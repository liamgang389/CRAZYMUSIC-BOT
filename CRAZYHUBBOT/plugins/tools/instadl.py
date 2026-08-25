import asyncio
import os
import re

import yt_dlp
from pyrogram import filters
from pyrogram.types import InputMediaPhoto, InputMediaVideo

import config
from CRAZYHUBBOT import app

# Matches instagram.com / instagr.am links, with or without http(s)://,
# with or without www. — used both to auto-detect a link in any message
# and to pull the link back out of that message's text.
INSTA_LINK_REGEX = re.compile(
    r"(?:https?://)?(?:www\.)?(?:instagram\.com|instagr\.am)/\S+",
    re.IGNORECASE,
)

DOWNLOAD_DIR = "downloads"
DOWNLOADING_STICKER_ID = (
    "CAACAgEAAx0CfD7LAgACO7xmZzb83lrLUVhxtmUaanKe0_ionAAC-gADUSkNORIJSVEUKRrhHgQ"
)
COOKIES_FILE = os.path.join(DOWNLOAD_DIR, "instagram_cookies.txt")


def _cookies_file_path():
    """Writes config.INSTAGRAM_COOKIES (if set) to disk and returns its
    path, so yt-dlp can log in as that account for gated posts. Returns
    None if no cookies were configured — yt-dlp then falls back to
    anonymous access, which still works for public posts.

    Defensive about how the value arrives: many hosting panels mangle
    multi-line env vars — either collapsing real newlines away or
    escaping them as literal backslash-n text — which otherwise breaks
    the Netscape cookies format yt-dlp expects (one cookie per line,
    tab-separated) and shows up as "does not look like a Netscape
    format cookies file". The file is rewritten fresh every time (not
    just when missing) so a fix to the env var takes effect on the
    next restart instead of a bad file lingering forever."""
    if not config.INSTAGRAM_COOKIES:
        return None

    raw = config.INSTAGRAM_COOKIES.strip()
    # Turn literal "\n"/"\r\n" escape sequences (two characters: a
    # backslash and a letter) into real newlines — happens when a
    # panel stores the value as a JSON/escaped string.
    raw = raw.replace("\\r\\n", "\n").replace("\\n", "\n")
    # Normalize real CRLF too, and drop any blank lines a paste added.
    lines = [ln.strip() for ln in raw.replace("\r\n", "\n").split("\n")]
    lines = [ln for ln in lines if ln]

    if not lines:
        print("[instadl] INSTAGRAM_COOKIES is set but empty after cleanup — ignoring it.")
        return None

    if not lines[0].startswith("#"):
        # Header missing (common when only the cookie rows got
        # copied) — MozillaCookieJar refuses to load without it.
        lines.insert(0, "# Netscape HTTP Cookie File")

    content = "\n".join(lines) + "\n"

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    with open(COOKIES_FILE, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)

    # Sanity-check it actually parses as a cookie jar before handing
    # it to yt-dlp, so a bad file fails with a clear message here
    # instead of a cryptic yt-dlp error deep in extraction.
    try:
        import http.cookiejar

        jar = http.cookiejar.MozillaCookieJar(COOKIES_FILE)
        jar.load(ignore_discard=True, ignore_expires=True)
        if len(jar) == 0:
            print(
                "[instadl] INSTAGRAM_COOKIES parsed but contains zero "
                "cookies — check the pasted content is the full "
                "cookies.txt file, not just a header or a snippet."
            )
    except Exception as e:
        print(
            f"[instadl] INSTAGRAM_COOKIES doesn't parse as a valid "
            f"Netscape cookies file even after cleanup ({e}). Falling "
            f"back to anonymous access — re-export cookies.txt with "
            f"'Get cookies.txt LOCALLY' and paste the ENTIRE file "
            f"content (including the '# Netscape HTTP Cookie File' "
            f"header line) into INSTAGRAM_COOKIES."
        )
        try:
            os.remove(COOKIES_FILE)
        except OSError:
            pass
        return None

    return COOKIES_FILE


def _extract_entries(link: str) -> list:
    """Blocking call — runs in a thread. Returns a list of yt-dlp info
    dicts: one per item for a carousel post, or a single-item list for
    a reel/photo/video post."""
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    ytdl_opts = {
        "quiet": True,
        "no_warnings": True,
        "outtmpl": os.path.join(DOWNLOAD_DIR, "insta_%(id)s_%(autonumber)s.%(ext)s"),
        "noplaylist": False,
        "format": "best",
    }
    cookies_path = _cookies_file_path()
    if cookies_path:
        ytdl_opts["cookiefile"] = cookies_path
    with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
        info = ydl.extract_info(link, download=True)

    entries = info.get("entries") if info.get("entries") is not None else [info]
    results = []
    for entry in entries:
        if not entry:
            continue
        filepath = ydl.prepare_filename(entry)
        if os.path.exists(filepath):
            is_video = entry.get("vcodec") not in (None, "none")
            results.append({"path": filepath, "is_video": is_video})
    return results


async def _download_instagram(client, message, link: str):
    downloading_sticker = None
    files = []
    try:
        # This sticker file_id may not resolve on every bot account/session
        # (Telegram file_ids aren't always portable between bots), so a
        # failure here must not abort the whole download.
        try:
            downloading_sticker = await message.reply_sticker(DOWNLOADING_STICKER_ID)
        except Exception as sticker_err:
            print(f"[instadl] couldn't send status sticker: {sticker_err}")

        loop = asyncio.get_event_loop()
        files = await loop.run_in_executor(None, _extract_entries, link)

        if not files:
            await message.reply_text(
                "Unable to fetch content. The link might be private, "
                "deleted, or unsupported."
            )
            return

        if len(files) == 1:
            f = files[0]
            if f["is_video"]:
                await message.reply_video(f["path"])
            else:
                await message.reply_photo(f["path"])
        else:
            # Carousel post — send everything together as an album.
            media_group = []
            for f in files:
                if f["is_video"]:
                    media_group.append(InputMediaVideo(f["path"]))
                else:
                    media_group.append(InputMediaPhoto(f["path"]))
            # Telegram allows at most 10 items per media group.
            for i in range(0, len(media_group), 10):
                await message.reply_media_group(media_group[i : i + 10])

    except Exception as e:
        print(f"[instadl] {e}")
        if "empty media response" in str(e).lower() or "logged-in" in str(e).lower():
            err_text = (
                "❌ Instagram is asking for a login to view this post. "
                "The bot owner needs to set the INSTAGRAM_COOKIES "
                "environment variable to download login-gated content."
            )
        else:
            err_text = (
                "❌ Couldn't download that — the link might be private, "
                "deleted, age-restricted, or Instagram is rate-limiting "
                "right now. Please try again in a bit."
            )
        await message.reply_text(err_text)

    finally:
        if downloading_sticker:
            await downloading_sticker.delete()
        for f in files:
            try:
                os.remove(f["path"])
            except OSError:
                pass


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
