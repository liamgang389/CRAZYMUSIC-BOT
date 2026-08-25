import re

import httpx

from CRAZYHUBBOT import app
from pyrogram import filters


DOWNLOADING_STICKER_ID = (
    "CAACAgEAAx0CfD7LAgACO7xmZzb83lrLUVhxtmUaanKe0_ionAAC-gADUSkNORIJSVEUKRrhHgQ"
)
API_URL = "https://karma-api2.vercel.app/instadl"  # Replace with your actual API URL

# Matches instagram.com / instagr.am links, with or without http(s)://,
# with or without www. — used both to auto-detect a link in any message
# and to pull the link back out of that message's text.
INSTA_LINK_REGEX = re.compile(
    r"(?:https?://)?(?:www\.)?(?:instagram\.com|instagr\.am)/\S+",
    re.IGNORECASE,
)


async def _download_instagram(client, message, link: str):
    downloading_sticker = None
    try:
        # This sticker file_id may not resolve on every bot account/session
        # (Telegram file_ids aren't always portable between bots), so a
        # failure here must not abort the whole download or crash the
        # finally block below.
        try:
            downloading_sticker = await message.reply_sticker(DOWNLOADING_STICKER_ID)
        except Exception as sticker_err:
            print(f"[instadl] couldn't send status sticker: {sticker_err}")

        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(API_URL, params={"url": link})
            response.raise_for_status()
            data = response.json()

        if "content_url" in data:
            content_url = data["content_url"]
            content_type = "video" if "video" in content_url else "photo"

            if content_type == "photo":
                await message.reply_photo(content_url)
            elif content_type == "video":
                await message.reply_video(content_url)
            else:
                await message.reply_text("Unsupported content type.")
        else:
            await message.reply_text(
                "Unable to fetch content. Please check the Instagram URL or try with another Instagram link."
            )

    except Exception as e:
        print(e)
        await message.reply_text(
            "An error occurred while processing the request."
        )

    finally:
        if downloading_sticker:
            await downloading_sticker.delete()


@app.on_message(filters.command(["ig", "insta"]))
async def instadl_command_handler(client, message):
    if len(message.command) < 2:
        await message.reply_text("Usage: /insta [Instagram URL]")
        return
    await _download_instagram(client, message, message.command[1])


# No command needed — just sending/pasting an Instagram link (post, reel,
# IGTV, story, etc.) anywhere in the message text triggers the download
# automatically. Excludes /ig and /insta messages so the link inside
# those isn't processed twice by both handlers.
@app.on_message(
    filters.text
    & filters.regex(INSTA_LINK_REGEX)
    & ~filters.command(["ig", "insta"])
)
async def instadl_auto_handler(client, message):
    match = INSTA_LINK_REGEX.search(message.text)
    if not match:
        return
    await _download_instagram(client, message, match.group(0))
