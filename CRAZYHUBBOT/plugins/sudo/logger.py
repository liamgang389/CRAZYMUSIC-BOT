from pyrogram import filters

from CRAZYHUBBOT import app
from CRAZYHUBBOT.misc import SUDOERS
from CRAZYHUBBOT.utils.database import add_off, add_on
from CRAZYHUBBOT.utils.decorators.language import language


@app.on_message(filters.command(["logger"]) & SUDOERS)
@language
async def logger(client, message, _):
    usage = _["log_1"]
    if len(message.command) != 2:
        return await message.reply_text(usage)
    state = message.text.split(None, 1)[1].strip().lower()
    if state == "enable":
        await add_on(2)
        await message.reply_text(_["log_2"])
    elif state == "disable":
        await add_off(2)
        await message.reply_text(_["log_3"])
    else:
        await message.reply_text(usage)

@app.on_message(filters.command(["cookies"]) & SUDOERS)
@language
async def cookies_info(client, message, _):
    await message.reply_text(
        "ℹ️ This bot no longer uses cookies to fetch YouTube streams — it "
        "relies on yt-dlp's android/web client bypass instead. There is "
        "nothing to check here anymore."
    )
