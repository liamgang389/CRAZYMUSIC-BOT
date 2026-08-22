"""
Automatic MCQ Quiz System.

No activation command exists. The quiz turns itself on for a group the
moment the bot is an admin there (checked continuously) and turns itself
off the moment the bot stops being admin or leaves. /quiz, /quizscore and
/quizrank below are VIEW-ONLY — they cannot turn anything on or off.
"""

import asyncio
import re
import time

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus, ChatType
from pyrogram.types import (
    CallbackQuery,
    ChatMemberUpdated,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from CRAZYHUBBOT import app
from CRAZYHUBBOT.misc import SUDOERS
from CRAZYHUBBOT.mongo.quizdb import (
    add_score,
    deactivate_group,
    end_active_quiz,
    get_active_groups,
    get_active_quiz,
    get_global_interval_default,
    get_leaderboard,
    get_recent_questions,
    get_settings,
    get_user_score,
    record_answer,
    register_group,
    save_used_question,
    set_global_interval_default,
    set_last_category,
    set_next_quiz_at,
    start_active_quiz,
)
from CRAZYHUBBOT.utils.quiz_bank import pick_question

QUIZ_DURATION = 600  # seconds each quiz stays open for answers (10 minutes)
TICK_INTERVAL = 30  # how often we check whether any group's quiz is due

# chat_id -> (is_admin: bool, checked_at: float) — separate, self-contained
# cache local to this plugin (kept isolated from any similar cache in
# other plugins so this feature never depends on / interferes with them).
_ADMIN_CACHE_TTL = 300
_admin_cache = {}
_seen_chats = set()  # lazy-registration de-dupe, see _quiz_lazy_register


async def _is_bot_admin(chat_id: int) -> bool:
    cached = _admin_cache.get(chat_id)
    now = time.time()
    if cached and (now - cached[1]) < _ADMIN_CACHE_TTL:
        return cached[0]
    try:
        member = await app.get_chat_member(chat_id, app.id)
        is_admin = member.status in (
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        )
    except Exception:
        is_admin = False
    _admin_cache[chat_id] = (is_admin, now)
    return is_admin


def _quiz_buttons(chat_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🅰️ A", callback_data=f"qz|{chat_id}|0"),
                InlineKeyboardButton("🅱️ B", callback_data=f"qz|{chat_id}|1"),
            ],
            [
                InlineKeyboardButton("🅲️ C", callback_data=f"qz|{chat_id}|2"),
                InlineKeyboardButton("🅳️ D", callback_data=f"qz|{chat_id}|3"),
            ],
        ]
    )


def _duration_display(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds} Seconds"
    minutes, rem = divmod(seconds, 60)
    if rem == 0:
        return f"{minutes} Minute{'s' if minutes != 1 else ''}"
    return f"{minutes}m {rem}s"


def _format_quiz_text(category: str, question: str, options: list) -> str:
    letters = ["A", "B", "C", "D"]
    option_lines = "\n".join(
        f"🔹 {letters[i]}) {opt}" for i, opt in enumerate(options)
    )
    return (
        f"🧠 **MUSIC GENIE X QUIZ**\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"📚 {category}\n\n"
        f"❓ Q. {question}\n\n"
        f"{option_lines}\n\n"
        f"⏳ {_duration_display(QUIZ_DURATION)}\n"
        f"━━━━━━━━━━━━━━━━━━"
    )


# ---------------------------------------------------------------------------
# Sending a quiz + ending it 30s later
# ---------------------------------------------------------------------------

async def _send_quiz(chat_id: int, settings: dict):
    # Never stack a second quiz on top of one still running.
    if await get_active_quiz(chat_id):
        return

    try:
        if not await app.get_chat(chat_id):
            return
    except Exception:
        return

    used = await get_recent_questions(chat_id)
    picked = pick_question(used, settings.get("last_category"))

    text = _format_quiz_text(picked["category"], picked["question"], picked["options"])

    try:
        sent = await app.send_message(
            chat_id, text, reply_markup=_quiz_buttons(chat_id)
        )
    except Exception:
        # Can't send messages here (permissions, bot removed, etc.) —
        # skip this round quietly and try again next interval.
        await set_next_quiz_at(
            chat_id, time.time() + settings.get("interval", 3600)
        )
        return

    await start_active_quiz(
        chat_id,
        sent.id,
        picked["question"],
        picked["options"],
        picked["correct_index"],
        picked["category"],
    )
    await save_used_question(chat_id, picked["question"])
    await set_last_category(chat_id, picked["category"])
    await set_next_quiz_at(chat_id, time.time() + settings.get("interval", 3600))

    asyncio.create_task(_end_quiz_after_delay(chat_id, sent.id))


async def _end_quiz_after_delay(chat_id: int, message_id: int):
    await asyncio.sleep(QUIZ_DURATION)
    try:
        quiz = await end_active_quiz(chat_id)
        if not quiz or quiz.get("message_id") != message_id:
            return

        try:
            await app.edit_message_reply_markup(chat_id, message_id, reply_markup=None)
        except Exception:
            pass

        answers = quiz.get("answers", {})

        correct_entries = sorted(
            (a for a in answers.values() if a.get("correct")),
            key=lambda a: a.get("at", 0),
        )
        medals = ["🥇", "🥈", "🥉"]
        result_lines = [
            f"{medals[i]} {entry.get('first_name') or 'Player'} — 1 point"
            for i, entry in enumerate(correct_entries[:3])
        ]
        if not result_lines:
            result_lines = ["No one answered correctly this time. 😅"]

        # No automatic "Correct Answer: X" line here on purpose — only
        # real users' own answers decide the result, the bot itself
        # never announces the answer.
        result_text = (
            f"🏁 **QUIZ ENDED**\n\n"
            f"🏆 **QUIZ RESULT**\n" + "\n".join(result_lines)
        )
        await app.send_message(chat_id, result_text)
    except Exception:
        return


# ---------------------------------------------------------------------------
# Scheduler tick — checks every group's own independent due-time
# ---------------------------------------------------------------------------

async def _quiz_tick():
    try:
        groups = await get_active_groups()
    except Exception:
        return

    now = time.time()
    for g in groups:
        chat_id = g.get("chat_id")
        try:
            if not await _is_bot_admin(chat_id):
                await deactivate_group(chat_id)
                continue
            if g.get("next_quiz_at", 0) > now:
                continue
            await _send_quiz(chat_id, g)
        except Exception:
            continue


_scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")
_scheduler.add_job(_quiz_tick, trigger="interval", seconds=TICK_INTERVAL, max_instances=1)
_scheduler.start()


# ---------------------------------------------------------------------------
# Automatic group discovery
# ---------------------------------------------------------------------------

@app.on_chat_member_updated()
async def _quiz_track_own_status(_, update: ChatMemberUpdated):
    """Instant reaction the moment the bot itself is promoted, demoted,
    or removed — no need to wait for the next scheduler tick."""
    try:
        member = update.new_chat_member
        if not member or not member.user or member.user.id != app.id:
            return
        is_admin = member.status in (
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        )
        _admin_cache[update.chat.id] = (is_admin, time.time())
        if is_admin:
            interval = await get_global_interval_default()
            await register_group(update.chat.id, interval)
        else:
            await deactivate_group(update.chat.id)
    except Exception:
        return


@app.on_message(filters.group & ~filters.bot & ~filters.via_bot, group=71)
async def _quiz_lazy_register(_, message):
    """Covers groups where the bot was ALREADY an admin before this
    feature was added — picked up the first time any message arrives,
    without needing a fresh promotion event."""
    try:
        chat_id = message.chat.id
        if chat_id in _seen_chats:
            return
        _seen_chats.add(chat_id)
        if message.chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
            return
        if await _is_bot_admin(chat_id):
            interval = await get_global_interval_default()
            await register_group(chat_id, interval)
    except Exception:
        return


# ---------------------------------------------------------------------------
# Answer handling
# ---------------------------------------------------------------------------

@app.on_callback_query(filters.regex(r"^qz\|"))
async def _quiz_answer_cb(_, cq: CallbackQuery):
    try:
        _, chat_id_str, idx_str = cq.data.split("|")
        chat_id = int(chat_id_str)
        idx = int(idx_str)

        quiz = await get_active_quiz(chat_id)
        if not quiz or quiz.get("message_id") != cq.message.id:
            return await cq.answer("⌛ This quiz has already ended.")

        user = cq.from_user
        newly_recorded = await record_answer(
            chat_id,
            user.id,
            idx,
            quiz["correct_index"],
            user.first_name or "",
            user.username or "",
        )
        if not newly_recorded:
            return await cq.answer(
                "⚠️ You already answered this question.", show_alert=True
            )

        is_correct = idx == quiz["correct_index"]
        await add_score(chat_id, user.id, user.username or "", user.first_name or "", is_correct)

        letters = ["A", "B", "C", "D"]
        chosen_text = quiz["options"][idx]
        if is_correct:
            await cq.answer(
                f"🎉 Correct!\n✅ {letters[idx]}) {chosen_text}", show_alert=True
            )
        else:
            await cq.answer(
                f"❌ Wrong Answer\n❌ Your answer: {letters[idx]}) {chosen_text}",
                show_alert=True,
            )
    except Exception:
        try:
            await cq.answer("⚠️ Something went wrong.")
        except Exception:
            pass


@app.on_message(
    filters.group & filters.reply & filters.text & ~filters.bot & ~filters.via_bot,
    group=73,
)
async def _quiz_text_answer(_, message):
    """Lets people answer by replying 'A' / 'B' / 'C' / 'D' (any case,
    with or without a trailing ')' or '.') directly to the quiz message,
    instead of only via the inline buttons."""
    try:
        reply_to = message.reply_to_message
        if not reply_to or not message.from_user:
            return

        match = re.match(r"^\s*([ABCD])[).]?\s*$", (message.text or "").upper())
        if not match:
            return
        idx = "ABCD".index(match.group(1))

        chat_id = message.chat.id
        quiz = await get_active_quiz(chat_id)
        if not quiz or quiz.get("message_id") != reply_to.id:
            return

        user = message.from_user
        newly_recorded = await record_answer(
            chat_id,
            user.id,
            idx,
            quiz["correct_index"],
            user.first_name or "",
            user.username or "",
        )
        if not newly_recorded:
            return await message.reply(
                "⚠️ You already answered this question.", quote=True
            )

        is_correct = idx == quiz["correct_index"]
        await add_score(chat_id, user.id, user.username or "", user.first_name or "", is_correct)

        letters = ["A", "B", "C", "D"]
        chosen_text = quiz["options"][idx]
        if is_correct:
            await message.reply(f"🎉 Correct!\n✅ {letters[idx]}) {chosen_text}", quote=True)
        else:
            await message.reply(
                f"❌ Wrong Answer\n❌ Your answer: {letters[idx]}) {chosen_text}",
                quote=True,
            )
    except Exception:
        return


# ---------------------------------------------------------------------------
# View-only commands (cannot activate/deactivate anything)
# ---------------------------------------------------------------------------

@app.on_message(filters.command("quiz") & filters.group)
async def _quiz_info(_, message):
    try:
        settings = await get_settings(message.chat.id)
        if not settings or not settings.get("active"):
            return await message.reply(
                "🧠 The automatic quiz isn't active here — make me an "
                "**admin** in this group and it turns on by itself."
            )
        if await get_active_quiz(message.chat.id):
            return await message.reply(
                "🧠 A quiz is running right now in this group — answer it above! ⏳"
            )
        remaining = max(0, int(settings.get("next_quiz_at", 0) - time.time()))
        mins, secs = divmod(remaining, 60)
        await message.reply(f"🧠 Next automatic quiz in **{mins}m {secs}s**.")
    except Exception:
        await message.reply("⚠️ Couldn't fetch quiz info right now.")


@app.on_message(filters.command("quizscore") & filters.group)
async def _quiz_score(_, message):
    try:
        score = await get_user_score(message.chat.id, message.from_user.id)
        if not score:
            return await message.reply("You haven't played a quiz in this group yet.")
        await message.reply(
            f"📊 **Your Quiz Score**\n\n"
            f"🏆 Points: {score.get('total_points', 0)}\n"
            f"✅ Correct: {score.get('correct_answers', 0)}\n"
            f"❌ Wrong: {score.get('wrong_answers', 0)}\n"
            f"🧠 Quizzes played: {score.get('quiz_count', 0)}"
        )
    except Exception:
        await message.reply("⚠️ Couldn't fetch your score right now.")


@app.on_message(filters.command("quizrank") & filters.group)
async def _quiz_rank(_, message):
    try:
        top = await get_leaderboard(message.chat.id, limit=10)
        if not top:
            return await message.reply("No quiz scores yet in this group.")
        medals = ["🥇", "🥈", "🥉"]
        lines = []
        for i, entry in enumerate(top):
            medal = medals[i] if i < 3 else f"{i + 1}."
            name = entry.get("first_name") or entry.get("username") or "Player"
            lines.append(f"{medal} {name} — {entry.get('total_points', 0)} points")
        await message.reply("🏆 **Group Quiz Leaderboard**\n\n" + "\n".join(lines))
    except Exception:
        await message.reply("⚠️ Couldn't fetch the leaderboard right now.")


# ---------------------------------------------------------------------------
# Owner-only: configure the DEFAULT interval for newly-registered groups
# ---------------------------------------------------------------------------

_VALID_INTERVALS = {
    "30m": 1800, "1h": 3600, "3h": 10800,
    "6h": 21600, "12h": 43200, "24h": 86400,
}


@app.on_message(filters.command("quizinterval") & SUDOERS)
async def _quiz_set_interval(_, message):
    try:
        if len(message.command) == 1:
            current = await get_global_interval_default()
            return await message.reply(
                f"⚙️ Current default quiz interval: **{current // 60} minutes**.\n"
                f"Usage: `/quizinterval 30m|1h|3h|6h|12h|24h`\n"
                f"(Applies to newly-registered groups only; existing groups "
                f"keep their current interval.)"
            )
        arg = message.command[1].lower()
        if arg not in _VALID_INTERVALS:
            return await message.reply("⚠️ Valid options: 30m, 1h, 3h, 6h, 12h, 24h")
        await set_global_interval_default(_VALID_INTERVALS[arg])
        await message.reply(f"✅ Default quiz interval set to **{arg}** for newly-registered groups.")
    except Exception:
        await message.reply("⚠️ Couldn't update the interval right now.")
