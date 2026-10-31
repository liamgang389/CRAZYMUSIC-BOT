import html

from pyrogram import filters
from pyrogram.types import Message
from youtube_search import YoutubeSearch

from CRAZYHUBBOT import app
from CRAZYHUBBOT.utils.pro_post import send_pro_post


@app.on_message(filters.command("search"))
async def ytsearch(_, message: Message):
    m = None
    try:
        if len(message.command) < 2:
            await message.reply_text("/search needs an argument!")
            return
        query = message.text.split(None, 1)[1]
        m = await message.reply_text(" searching")
        results = YoutubeSearch(query, max_results=5).to_dict()
        if not results:
            return await m.edit("No results found.")
        text, buttons = "", []
        for i, r in enumerate(results[:5], 1):
            url = f"https://www.youtube.com{r['url_suffix']}"
            text += (
                f"<b>{i}. {html.escape(r['title'])}</b>\n"
                f"Dᴜʀᴀᴛɪᴏɴ: {html.escape(str(r['duration']))}\n"
                f"Vɪᴇᴡs: {html.escape(str(r['views']))}\n"
                f"Cʜᴀɴɴᴇʟ: {html.escape(r['channel'])}\n\n"
            )
            buttons.append({"text": f"▶️ {i}", "url": url, "style": "success"})
        # buttons post ke andar (bubble ke bheetar) aayenge
        await send_pro_post(
            message.chat.id, text, rows=[buttons], reply_to=message.id
        )
        await m.delete()
    except Exception as e:
        if m:
            await m.edit(str(e))
        else:
            await message.reply_text(str(e))
