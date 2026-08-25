from pyrogram import filters
from pyrogram.types import Message

from CRAZYHUBBOT import app
from CRAZYHUBBOT.misc import SUDOERS
from CRAZYHUBBOT.utils.database import autoend_off, autoend_on


@app.on_message(filters.command("autoend") & SUDOERS)
async def auto_end_stream(_, message: Message):
    usage = (
        "<b>ᴀᴜᴛᴏ ᴇɴᴅ ɪs ᴏɴ ʙʏ ᴅᴇғᴀᴜʟᴛ — ɴᴏ ᴄᴏᴍᴍᴀɴᴅ ɴᴇᴇᴅᴇᴅ.</b>\n"
        "ᴜsᴇ ᴛʜɪs ᴏɴʟʏ ɪғ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴛᴜʀɴ ɪᴛ ᴏғғ/ᴏɴ ᴍᴀɴᴜᴀʟʟʏ:\n\n"
        "<b>ᴇxᴀᴍᴘʟᴇ :</b>\n\n/autoend [ᴇɴᴀʙʟᴇ | ᴅɪsᴀʙʟᴇ]"
    )
    if len(message.command) != 2:
        return await message.reply_text(usage)
    state = message.text.split(None, 1)[1].strip().lower()
    if state == "enable":
        await autoend_on()
        await message.reply_text(
            "» ᴀᴜᴛᴏ ᴇɴᴅ sᴛʀᴇᴀᴍ ᴇɴᴀʙʟᴇᴅ.\n\nᴀssɪsᴛᴀɴᴛ ᴡɪʟʟ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ʟᴇᴀᴠᴇ ᴛʜᴇ ᴠɪᴅᴇᴏᴄʜᴀᴛ ᴡʜᴇɴ ɴᴏ ʀᴇᴀʟ ᴜsᴇʀ ɪs ʟɪsᴛᴇɴɪɴɢ."
        )
    elif state == "disable":
        await autoend_off()
        await message.reply_text("» ᴀᴜᴛᴏ ᴇɴᴅ sᴛʀᴇᴀᴍ ᴅɪsᴀʙʟᴇᴅ.")
    else:
        await message.reply_text(usage)
