import time

from CRAZYHUBBOT.utils.mongo import db

quiz_settings_db = db.quiz_settings
quiz_questions_db = db.quiz_questions
quiz_scores_db = db.quiz_scores
quiz_answers_db = db.quiz_answers

DEFAULT_INTERVAL = 3600  # 1 hour, in seconds


# ---------------------------------------------------------------------------
# Per-group scheduling
# ---------------------------------------------------------------------------

async def register_group(chat_id: int, interval: int = None):
    """Called the moment the bot becomes admin in a group (or the first
    time we notice it already is). Turns the quiz on for that group with
    its own independent schedule, if it isn't already on."""
    existing = await quiz_settings_db.find_one({"chat_id": chat_id})
    use_interval = interval or DEFAULT_INTERVAL
    if existing:
        if not existing.get("active", False):
            await quiz_settings_db.update_one(
                {"chat_id": chat_id},
                {
                    "$set": {
                        "active": True,
                        "next_quiz_at": time.time()
                        + existing.get("interval", use_interval),
                    }
                },
            )
        return
    await quiz_settings_db.insert_one(
        {
            "chat_id": chat_id,
            "interval": use_interval,
            "active": True,
            "next_quiz_at": time.time() + use_interval,
            "last_category": None,
        }
    )


async def deactivate_group(chat_id: int):
    """Called when the bot loses admin / leaves. Stops future quizzes
    for this group without deleting its scores or history."""
    await quiz_settings_db.update_one(
        {"chat_id": chat_id}, {"$set": {"active": False}}
    )


async def get_active_groups() -> list:
    cursor = quiz_settings_db.find({"active": True})
    return [doc async for doc in cursor]


async def get_settings(chat_id: int):
    return await quiz_settings_db.find_one({"chat_id": chat_id})


async def set_next_quiz_at(chat_id: int, when: float):
    await quiz_settings_db.update_one(
        {"chat_id": chat_id}, {"$set": {"next_quiz_at": when}}
    )


async def set_last_category(chat_id: int, category: str):
    await quiz_settings_db.update_one(
        {"chat_id": chat_id}, {"$set": {"last_category": category}}
    )


async def set_global_interval_default(interval: int):
    """Bot-owner configurable default interval, used only when a NEW
    group is registered from then on. Existing groups keep whatever
    interval they already had."""
    await quiz_settings_db.update_one(
        {"is_global_config": True},
        {"$set": {"default_interval": interval, "is_global_config": True}},
        upsert=True,
    )


async def get_global_interval_default() -> int:
    doc = await quiz_settings_db.find_one({"is_global_config": True})
    if doc and doc.get("default_interval"):
        return doc["default_interval"]
    return DEFAULT_INTERVAL


# ---------------------------------------------------------------------------
# Duplicate-question prevention (per group)
# ---------------------------------------------------------------------------

_KEEP_RECENT = 200  # per-group question history kept for dedup


async def get_recent_questions(chat_id: int) -> set:
    cursor = quiz_questions_db.find({"chat_id": chat_id}, {"question": 1})
    return {doc["question"] async for doc in cursor}


async def save_used_question(chat_id: int, question_text: str):
    await quiz_questions_db.insert_one(
        {"chat_id": chat_id, "question": question_text, "used_at": time.time()}
    )
    count = await quiz_questions_db.count_documents({"chat_id": chat_id})
    if count > _KEEP_RECENT:
        excess = count - _KEEP_RECENT
        oldest = quiz_questions_db.find({"chat_id": chat_id}).sort(
            "used_at", 1
        ).limit(excess)
        ids = [doc["_id"] async for doc in oldest]
        if ids:
            await quiz_questions_db.delete_many({"_id": {"$in": ids}})


# ---------------------------------------------------------------------------
# Scores / leaderboard (per group, never mixed)
# ---------------------------------------------------------------------------

async def add_score(chat_id: int, user_id: int, username: str, first_name: str, correct: bool):
    inc = {"quiz_count": 1, "correct_answers": 1 if correct else 0,
           "wrong_answers": 0 if correct else 1}
    if correct:
        inc["total_points"] = 1
    await quiz_scores_db.update_one(
        {"chat_id": chat_id, "user_id": user_id},
        {"$inc": inc, "$set": {"username": username, "first_name": first_name}},
        upsert=True,
    )


async def get_user_score(chat_id: int, user_id: int):
    return await quiz_scores_db.find_one({"chat_id": chat_id, "user_id": user_id})


async def get_leaderboard(chat_id: int, limit: int = 10) -> list:
    cursor = quiz_scores_db.find({"chat_id": chat_id}).sort(
        "total_points", -1
    ).limit(limit)
    return [doc async for doc in cursor]


# ---------------------------------------------------------------------------
# Active quiz state (max one running quiz per group, enforced here)
# ---------------------------------------------------------------------------

async def start_active_quiz(chat_id, message_id, question, options, correct_index, category):
    await quiz_answers_db.update_one(
        {"chat_id": chat_id},
        {
            "$set": {
                "message_id": message_id,
                "question": question,
                "options": options,
                "correct_index": correct_index,
                "category": category,
                "started_at": time.time(),
                "ended": False,
                "answers": {},
            }
        },
        upsert=True,
    )


async def get_active_quiz(chat_id: int):
    """A quiz is 'active' (still accepting answers) only while ended=False."""
    return await quiz_answers_db.find_one({"chat_id": chat_id, "ended": False})


async def record_answer(chat_id: int, user_id: int, option_index: int,
                         correct_index: int, first_name: str, username: str) -> bool:
    """Atomically records a user's first (and only) answer. Returns True
    if this call recorded it, False if the user had already answered —
    the $exists:False guard in the filter makes this race-safe even if
    two taps land at nearly the same instant."""
    key = f"answers.{user_id}"
    result = await quiz_answers_db.update_one(
        {"chat_id": chat_id, "ended": False, key: {"$exists": False}},
        {
            "$set": {
                key: {
                    "idx": option_index,
                    "correct": option_index == correct_index,
                    "first_name": first_name,
                    "username": username,
                    "at": time.time(),
                }
            }
        },
    )
    return result.modified_count > 0


async def end_active_quiz(chat_id: int):
    """Marks the quiz as ended and returns its final document, or None
    if there was nothing active (e.g. already ended by another path)."""
    quiz = await quiz_answers_db.find_one({"chat_id": chat_id, "ended": False})
    if quiz:
        await quiz_answers_db.update_one(
            {"_id": quiz["_id"]}, {"$set": {"ended": True}}
        )
    return quiz
