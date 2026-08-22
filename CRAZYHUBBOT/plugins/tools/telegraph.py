from telegraph import upload_file
from pyrogram import filters
from CRAZYHUBBOT import app
from pyrogram.types import InputMediaPhoto


@app.on_message(filters.command(["tgm", "telegraph"]))
def ul(_, message):
    reply = message.reply_to_message
    if not reply or not reply.media:
        return message.reply("𝐑𝙴𝙿𝙻𝚈 𝚃𝙾 𝙰 𝙼𝙴𝙳𝙸𝙰 𝙼𝙴𝚂𝚂𝙰𝙶𝙴...")
    i = message.reply("𝐌𝙰𝙺𝙴 𝐀 𝐋𝙸𝙽𝙺...")
    path = reply.download()
    try:
        fk = upload_file(path)
    except Exception:
        # telegra.ph's upload endpoint is unreliable and sometimes
        # returns a plain-text error instead of JSON, which crashes
        # the telegraph package internally. Fail gracefully instead
        # of taking the bot down.
        return i.edit("⚠️ Telegra.ph upload failed right now, try again later.")
    url = ""
    for x in fk:
        url = "https://telegra.ph" + x
    i.edit(f'Yᴏᴜʀ ʟɪɴᴋ sᴜᴄᴄᴇssғᴜʟ Gᴇɴ {url}')

########____________________________________________________________######

@app.on_message(filters.command(["graph", "grf"]))
def ulg(_, message):
    reply = message.reply_to_message
    if not reply or not reply.media:
        return message.reply("𝐑𝙴𝙿𝙻𝚈 𝚃𝙾 𝙰 𝙼𝙴𝙳𝙸𝙰 𝙼𝙴𝚂𝚂𝙰𝙶𝙴...")
    i = message.reply("𝐌𝙰𝙺𝙴 𝐀 𝐋𝙸𝙽𝙺...")
    path = reply.download()
    try:
        fk = upload_file(path)
    except Exception:
        return i.edit("⚠️ Telegra.ph upload failed right now, try again later.")
    url = ""
    for x in fk:
        url = "https://graph.org" + x
    i.edit(f'Yᴏᴜʀ ʟɪɴᴋ sᴜᴄᴄᴇssғᴜʟ Gᴇɴ {url}')
