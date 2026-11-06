import asyncio
import html
import os
import random
import time
from datetime import datetime, timedelta

from pyrogram import filters
from pyrogram.enums import ButtonStyle, ChatType, ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# BOT FILE NAME
from CRAZYHUBBOT import app as app
from CRAZYHUBBOT.utils.couples_card import make_couple_card

POLICE = [
    [
        InlineKeyboardButton(
            text="\U0001d641\u01fb\u0137\U0001d41e \U0001d5e6\U0001d45a\u1da6\U0001d459\U0001d41e",
            url="https://t.me/Fake_SmileK",
            style=ButtonStyle.PRIMARY,
        ),
    ],
]

DEFAULT_PFP = "CRAZYHUBBOT/assets/upic.png"


def _tomorrow() -> str:
    """Kal ki date (mahine/saal badalne par bhi sahi)."""
    return (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")


def _mention(user) -> str:
    name = html.escape((user.first_name or "User").strip() or "User")
    return f'<a href="tg://user?id={user.id}">{name}</a>'


async def _pfp(user_id: int, cid: int, tag: str) -> str:
    try:
        photo = (await app.get_chat(user_id)).photo
        return await app.download_media(
            photo.big_file_id, file_name=f"couple_{cid}_{tag}_{int(time.time())}.png"
        )
    except Exception:
        return DEFAULT_PFP


@app.on_message(filters.command("couples"))
async def ctest(_, message):
    cid = message.chat.id
    if message.chat.type == ChatType.PRIVATE:
        return await message.reply_text(
            "\u1d1b\u029c\u026as \u1d04\u1d0f\u1d0d\u1d0d\u1d00\u0274\u1d05 \u1d0f\u0274\u029f\u028f "
            "\u1d21\u1d0f\u0280\u1d0bs \u026a\u0274 \u0262\u0280\u1d0f\u1d1c\u1d18s."
        )

    made = []
    msg = None
    try:
        msg = await message.reply_text(
            "\u0262\u1d07\u0274\u1d07\u0280\u1d00\u1d1b\u026a\u0274\u0262 "
            "\u1d04\u1d0f\u1d1c\u1d18\u029f\u1d07s \u026a\u1d0d\u1d00\u0262\u1d07..."
        )

        # GET LIST OF USERS
        user_ids = []
        async for m in app.get_chat_members(cid, limit=50):
            if not m.user.is_bot:
                user_ids.append(m.user.id)
        if len(user_ids) < 2:
            return await msg.edit("Couple banane ke liye group me kam se kam 2 members chahiye.")

        c1_id, c2_id = random.sample(user_ids, 2)
        u1, u2 = await app.get_users([c1_id, c2_id])

        p1 = await _pfp(c1_id, cid, "a")
        p2 = await _pfp(c2_id, cid, "b")
        made += [p for p in (p1, p2) if p != DEFAULT_PFP]

        tomorrow = _tomorrow()
        out = f"couple_{cid}_{int(time.time())}.jpg"
        made.append(out)
        # Image banana CPU kaam hai: alag thread me, taaki bot na atke
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            make_couple_card,
            p1, p2, u1.first_name or "", u2.first_name or "", tomorrow, out,
        )

        TXT = (
            "<b>\u1d1b\u1d0f\u1d05\u1d00\u028f's \u1d04\u1d0f\u1d1c\u1d18\u029f\u1d07 "
            "\u1d0f\u0493 \u1d1b\u029c\u1d07 \u1d05\u1d00\u028f :</b>\n"
            f"{_mention(u1)} + {_mention(u2)} = \U0001f49a\n"
            "<b>\u0274\u1d07x\u1d1b \u1d04\u1d0f\u1d1c\u1d18\u029f\u1d07s \u1d21\u026a\u029f\u029f "
            f"\u0299\u1d07 s\u1d07\u029f\u1d07\u1d04\u1d1b\u1d07\u1d05 \u1d0f\u0274 {tomorrow} !!</b>"
        )
        await message.reply_photo(
            out,
            caption=TXT,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(POLICE),
        )
        await msg.delete()
    except Exception as e:
        print(f"[couples] error: {e!r}")
        if msg:
            try:
                await msg.edit("Couple image nahi ban payi, thodi der baad try karo.")
            except Exception:
                pass
    finally:
        for f in made:
            try:
                os.remove(f)
            except Exception:
                pass


__mod__ = "COUPLES"
__help__ = """
**\u00bb /couples** - Get Todays Couples Of The Group In Interactive View
"""
