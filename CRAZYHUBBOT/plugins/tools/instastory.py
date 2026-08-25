import re

import httpx
from pyrogram import filters
from pyrogram.types import InputMediaPhoto, InputMediaVideo

import config
from CRAZYHUBBOT import app

STORY_API_URL = "https://instagram-video-downloader13.p.rapidapi.com/stories.php"
STORY_API_HOST = "instagram-video-downloader13.p.rapidapi.com"

_MEDIA_URL_RE = re.compile(r"\.(mp4|jpg|jpeg|png|webp|heic)(\?|$)", re.IGNORECASE)


def _find_media_urls(obj) -> list:
    """Recursively walks the API's JSON response and collects anything
    that looks like a direct media URL (video/image). This endpoint's
    exact response shape isn't documented here, so scanning for
    URL-shaped strings is more resilient than guessing fixed key
    names like "url"/"data"/"result" that may or may not exist."""
    urls = []
    if isinstance(obj, dict):
        for v in obj.values():
            urls.extend(_find_media_urls(v))
    elif isinstance(obj, list):
        for item in obj:
            urls.extend(_find_media_urls(item))
    elif isinstance(obj, str):
        if obj.startswith("http") and (
            _MEDIA_URL_RE.search(obj)
            or "cdninstagram" in obj
            or "fbcdn" in obj
        ):
            urls.append(obj)
    return urls


@app.on_message(filters.command(["story", "instastory"]))
async def instastory_command_handler(client, message):
    if len(message.command) < 2:
        await message.reply_text("Usage: /story <instagram_username>  (without the @)")
        return

    username = message.command[1].lstrip("@")
    status = await message.reply_text(f"⏳ Fetching stories for @{username}...")

    try:
        async with httpx.AsyncClient(timeout=30) as http_client:
            resp = await http_client.post(
                STORY_API_URL,
                data={"username": username},
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "x-rapidapi-host": STORY_API_HOST,
                    "x-rapidapi-key": config.RAPIDAPI_INSTAGRAM_KEY,
                },
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        print(f"[instastory] request failed: {e}")
        await status.edit_text(
            "❌ Couldn't reach the stories API right now. Try again in a bit."
        )
        return

    urls = _find_media_urls(data)
    if not urls:
        # Logged so the raw shape is visible if this API's response
        # format doesn't match what we're scanning for above.
        print(f"[instastory] no media urls recognized in response: {data}")
        await status.edit_text(
            f"❌ No active stories found for @{username} "
            "(or they don't currently have any up)."
        )
        return

    try:
        if len(urls) == 1:
            url = urls[0]
            if _MEDIA_URL_RE.search(url) and ".mp4" in url.lower():
                await message.reply_video(url)
            else:
                await message.reply_photo(url)
        else:
            media_group = []
            for url in urls:
                if ".mp4" in url.lower():
                    media_group.append(InputMediaVideo(url))
                else:
                    media_group.append(InputMediaPhoto(url))
            # Telegram allows at most 10 items per media group.
            for i in range(0, len(media_group), 10):
                await message.reply_media_group(media_group[i : i + 10])
        await status.delete()
    except Exception as e:
        print(f"[instastory] failed sending media: {e}")
        await status.edit_text(
            "❌ Found the stories but couldn't send them — the media "
            "link may have already expired."
        )
