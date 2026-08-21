from pyrogram import filters
from pyrogram.types import Message

from CRAZYHUBBOT import app
from CRAZYHUBBOT.utils.database import get_autoplay, set_autoplay
from CRAZYHUBBOT.utils.decorators import AdminRightsCheck
from CRAZYHUBBOT.utils.inline import close_markup
from config import BANNED_USERS


@app.on_message(filters.command(["autoplay"]) & filters.group & ~BANNED_USERS)
@AdminRightsCheck
async def autoplay_command(cli, message: Message, _, chat_id):
    if len(message.command) != 2:
        current = await get_autoplay(chat_id)
        state_text = "ON ✅" if current else "OFF ❌"
        return await message.reply_text(
            f"🎧 **Autoplay** is currently **{state_text}** in this chat.\n\n"
            f"When the queue runs out, autoplay automatically keeps a related "
            f"song playing instead of stopping.\n\n"
            f"Usage: `/autoplay on` or `/autoplay off`",
            reply_markup=close_markup(_),
        )

    state = message.command[1].strip().lower()
    if state in ("on", "enable"):
        await set_autoplay(chat_id, True)
        return await message.reply_text(
            "🎧 Autoplay turned **ON** — I'll keep playing related songs "
            "automatically once the queue runs out.",
            reply_markup=close_markup(_),
        )
    elif state in ("off", "disable"):
        await set_autoplay(chat_id, False)
        return await message.reply_text(
            "🎧 Autoplay turned **OFF** — I'll stop and leave the voice "
            "chat once the queue runs out, like before.",
            reply_markup=close_markup(_),
        )
    else:
        return await message.reply_text("Usage: `/autoplay on` or `/autoplay off`")
