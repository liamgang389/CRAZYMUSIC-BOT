import time

from CRAZYHUBBOT.utils.mongo import db

picguess_db = db.picguess_rounds


async def start_round(chat_id: int, message_id: int, mode: str, answer: str, options: list = None):
    """mode is 'emoji' or 'word'. answer is the correct emoji, or the
    correct word in lowercase. options is the shuffled list of 8
    emoji buttons for 'emoji' mode (None for 'word' mode)."""
    await picguess_db.update_one(
        {"chat_id": chat_id},
        {
            "$set": {
                "message_id": message_id,
                "mode": mode,
                "answer": answer,
                "options": options,
                "started_at": time.time(),
                "ended": False,
                "winner": None,
            }
        },
        upsert=True,
    )


async def get_active_round(chat_id: int):
    return await picguess_db.find_one({"chat_id": chat_id, "ended": False})


async def claim_round(chat_id: int, user_id: int, first_name: str) -> bool:
    """Atomically marks the round as solved by this user. The
    ended:False guard in the filter makes this race-safe — if two
    people answer correctly at nearly the same instant, only the first
    write wins; the second gets modified_count == 0."""
    result = await picguess_db.update_one(
        {"chat_id": chat_id, "ended": False},
        {
            "$set": {
                "ended": True,
                "winner": {"user_id": user_id, "first_name": first_name},
                "won_at": time.time(),
            }
        },
    )
    return result.modified_count > 0


async def end_round_unsolved(chat_id: int, message_id: int) -> bool:
    """Used by the round timeout — only ends it if it's still the same
    unsolved round (not already claimed or replaced)."""
    result = await picguess_db.update_one(
        {"chat_id": chat_id, "message_id": message_id, "ended": False},
        {"$set": {"ended": True, "winner": None}},
    )
    return result.modified_count > 0
