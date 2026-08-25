import logging
from pyrogram.types import Message
from youtube_search import YoutubeSearch
from CRAZYHUBBOT import app
from pyrogram import filters
from config import BOT_USERNAME





@app.on_message(filters.command("search"))
async def ytsearch(_, message: Message):
    try:
        if len(message.command) < 2:
            await message.reply_text("/search needs an argument!")
            return
        query = message.text.split(None, 1)[1]
        m = await message.reply_text(" searching")
        results = YoutubeSearch(query, max_results=5).to_dict()
        i = 0
        text = ""
        while i < 5:
            text += f"Qᴜᴇʀʏ: {results[i]['title']}\n"
            text += f"Dᴜʀᴀᴛɪᴏɴ: {results[i]['duration']}\n"
            text += f"Vɪᴇᴡs: {results[i]['views']}\n"
            text += f"Cʜᴀɴɴᴇʟ: {results[i]['channel']}\n"
            text += f"https://www.youtube.com{results[i]['url_suffix']}\n\n"
            i += 1
        await m.edit(text, disable_web_page_preview=True)
    except Exception as e:
        await m.edit(str(e))
