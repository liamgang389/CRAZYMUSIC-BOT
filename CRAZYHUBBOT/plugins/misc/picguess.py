"""
Emoji/Word Picture-Guess mini-game.

Two manually-started rounds, one active per group at a time:
- /emojiguess — a card with one hidden emoji + 8 emoji buttons below.
  Tap the button matching the emoji shown in the card.
- /wordguess — a card with a scrambled word. Reply to that message with
  the unscrambled word (any case).

First correct guess wins the round and gets points via the same
add_score()/streak/leaderboard system as the MCQ quiz — /quizrank and
/quizweekly include these points too.
"""

import asyncio
import os

from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from CRAZYHUBBOT import app
from CRAZYHUBBOT.mongo.picguessdb import (
    claim_round,
    end_round_unsolved,
    get_active_round,
    start_round,
)
from CRAZYHUBBOT.mongo.quizdb import add_score, get_active_quiz
from CRAZYHUBBOT.utils.picguess_bank import pick_emoji_round, pick_word_round, scramble
from CRAZYHUBBOT.utils.picguess_image import generate_emoji_card_for, generate_word_card

ROUND_TIMEOUT = 300  # seconds a round stays open if nobody solves it


def _emoji_buttons(chat_id: int, options: list) -> InlineKeyboardMarkup:
    rows = []
    row = []
    for emoji in options:
        row.append(InlineKeyboardButton(emoji, callback_data=f"pgz|{chat_id}|{emoji}"))
        if len(row) == 4:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(rows)


async def _end_round_after_delay(chat_id: int, message_id: int):
    await asyncio.sleep(ROUND_TIMEOUT)
    try:
        ended = await end_round_unsolved(chat_id, message_id)
        if ended:
            try:
                await app.send_message(chat_id, "⌛ Nobody solved it in time — round closed.")
            except Exception:
                pass
    except Exception:
        return


async def start_emoji_round(chat_id: int) -> bool:
    """Starts an emoji-guess round in chat_id. Returns True if one was
    actually sent, False if a round/quiz is already active there or
    sending failed (permissions, etc.) — used by both the manual
    /emojiguess command and the automatic scheduler."""
    if await get_active_round(chat_id) or await get_active_quiz(chat_id):
        return False
    round_data = pick_emoji_round()
    path = generate_emoji_card_for(round_data["answer"])
    try:
        sent = await app.send_photo(
            chat_id,
            path,
            caption="🕵️ **Guess the hidden emoji!**\nTap to reveal, then tap the matching button below.",
            reply_markup=_emoji_buttons(chat_id, round_data["options"]),
            has_spoiler=True,
        )
    except Exception:
        return False
    finally:
        try:
            os.remove(path)
        except Exception:
            pass

    await start_round(chat_id, sent.id, "emoji", round_data["answer"], round_data["options"])
    asyncio.create_task(_end_round_after_delay(chat_id, sent.id))
    return True


async def start_word_round(chat_id: int) -> bool:
    """Starts a word-unscramble round in chat_id. Same return
    semantics as start_emoji_round()."""
    if await get_active_round(chat_id) or await get_active_quiz(chat_id):
        return False
    answer = pick_word_round()
    scrambled = scramble(answer)
    path = generate_word_card(scrambled)
    try:
        sent = await app.send_photo(
            chat_id,
            path,
            caption="🔤 **Unscramble this word!**\nTap to reveal, then reply to this message with your guess.",
            has_spoiler=True,
        )
    except Exception:
        return False
    finally:
        try:
            os.remove(path)
        except Exception:
            pass

    await start_round(chat_id, sent.id, "word", answer, None)
    asyncio.create_task(_end_round_after_delay(chat_id, sent.id))
    return True


@app.on_message(filters.command(["emojiguess"]) & filters.group)
async def _emojiguess_command(_, message):
    started = await start_emoji_round(message.chat.id)
    if not started:
        await message.reply(
            "⚠️ A guessing round (or quiz) is already active here — solve that one first!"
        )


@app.on_message(filters.command(["wordguess"]) & filters.group)
async def _wordguess_command(_, message):
    started = await start_word_round(message.chat.id)
    if not started:
        await message.reply(
            "⚠️ A guessing round (or quiz) is already active here — solve that one first!"
        )


@app.on_callback_query(filters.regex(r"^pgz\|"))
async def _emoji_guess_answer(_, cq):
    try:
        _, chat_id_str, emoji = cq.data.split("|", 2)
        chat_id = int(chat_id_str)

        round_ = await get_active_round(chat_id)
        if not round_ or round_.get("message_id") != cq.message.id:
            return await cq.answer("⌛ This round has already ended.")

        if emoji != round_["answer"]:
            return await cq.answer("❌ Not the right one — try again!")

        user = cq.from_user
        won = await claim_round(chat_id, user.id, user.first_name or "Player")
        if not won:
            return await cq.answer("😅 Someone already solved this one!", show_alert=True)

        points, streak = await add_score(
            chat_id, user.id, user.username or "", user.first_name or "", True, fast=True
        )
        streak_line = f"\n🔥 Streak: {streak}" if streak > 1 else ""
        try:
            await cq.message.edit_caption(
                f"✅ **Solved by {user.first_name}!**\n"
                f"The hidden emoji was {round_['answer']}\n"
                f"+{points} points{streak_line}"
            )
        except Exception:
            pass
        await cq.answer(f"🎉 Correct! +{points} points", show_alert=True)
    except Exception:
        try:
            await cq.answer("⚠️ Something went wrong.")
        except Exception:
            pass


@app.on_message(
    filters.group & filters.reply & filters.text & ~filters.bot & ~filters.via_bot,
    group=74,
)
async def _word_guess_answer(_, message):
    try:
        reply_to = message.reply_to_message
        if not reply_to or not message.from_user:
            return

        chat_id = message.chat.id
        round_ = await get_active_round(chat_id)
        if not round_ or round_.get("mode") != "word" or round_.get("message_id") != reply_to.id:
            return

        guess = (message.text or "").strip().lower()
        if guess != round_["answer"]:
            return  # wrong guesses are ignored quietly, no spam

        user = message.from_user
        won = await claim_round(chat_id, user.id, user.first_name or "Player")
        if not won:
            return  # someone else already solved it a moment earlier

        points, streak = await add_score(
            chat_id, user.id, user.username or "", user.first_name or "", True, fast=True
        )
        streak_line = f"\n🔥 Streak: {streak}" if streak > 1 else ""
        await message.reply(
            f"🎉 Correct, {user.first_name}! It was **{round_['answer'].title()}**\n"
            f"+{points} points{streak_line}",
            quote=True,
        )
    except Exception:
        return
