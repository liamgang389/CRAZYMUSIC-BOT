import asyncio
import os
import re

import httpx
import yt_dlp
from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    InputMediaVideo,
)

import config
from CRAZYHUBBOT import app

# Caption + "Group" button attached under every downloaded file.
CAPTION_TEXT = (
    '<blockquote>🐬 🅜🅐🅓🅔 🅑🅨  : '
    '<a href="https://t.me/MusicGenieXBot">Music Genie X &lt;/&gt;</a></blockquote>'
)
GROUP_BUTTON_URL = getattr(config, "SUPPORT_CHAT", None) or "https://t.me/CrazyHubSupport"
RESULT_MARKUP = InlineKeyboardMarkup(
    [[InlineKeyboardButton("👥 Group", url=GROUP_BUTTON_URL)]]
)

# Matches instagram.com / instagr.am links, with or without http(s)://,
# with or without www. — used both to auto-detect a link in any message
# and to pull the link back out of that message's text.
INSTA_LINK_REGEX = re.compile(
    r"(?:https?://)?(?:www\.)?(?:instagram\.com|instagr\.am)/\S+",
    re.IGNORECASE,
)

DOWNLOAD_DIR = "downloads"
DOWNLOADING_STICKER_ID = (
    "CAACAgUAAxkBAAEGXaBqjV15XG2pQat_t4egRhUvQMySFwAC7w8AArB52VZ0CWL6_wMMQj0E"
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


def _run_ytdlp(link: str, use_cookies: bool):
    ytdl_opts = {
        "quiet": True,
        "no_warnings": True,
        "outtmpl": os.path.join(DOWNLOAD_DIR, "insta_%(id)s_%(autonumber)s.%(ext)s"),
        "noplaylist": False,
        "format": "best",
        # A browser-like User-Agent avoids some 400s Instagram throws
        # at requests that look scripted/bare.
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        },
    }
    if use_cookies:
        cookies_path = _cookies_file_path()
        if cookies_path:
            ytdl_opts["cookiefile"] = cookies_path
    with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
        return ydl, ydl.extract_info(link, download=True)


def _extract_entries(link: str) -> list:
    """Blocking call — runs in a thread. Returns a list of yt-dlp info
    dicts: one per item for a carousel post, or a single-item list for
    a reel/photo/video post."""
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    try:
        ydl, info = _run_ytdlp(link, use_cookies=True)
    except Exception as e:
        # A 400/401/403 during info extraction can mean the configured
        # INSTAGRAM_COOKIES session has gone stale/invalid — Instagram
        # then rejects the request outright instead of just serving
        # public-only data. Retry once without cookies before giving
        # up, since anonymous access still works for public posts.
        msg = str(e).lower()
        if config.INSTAGRAM_COOKIES and any(
            code in msg for code in ("400", "401", "403")
        ):
            print(f"[instadl] extraction with cookies failed ({e}); retrying anonymously")
            ydl, info = _run_ytdlp(link, use_cookies=False)
        else:
            raise

    entries = info.get("entries") if info.get("entries") is not None else [info]
    results = []
    for entry in entries:
        if not entry:
            continue

        # yt-dlp's info dict "vcodec" field isn't reliable for deciding
        # photo vs video (it can be missing/stale after postprocessing
        # or format merging), and mismatching this is what causes
        # Telegram to reject the upload with PHOTO_EXT_INVALID. The
        # actual file extension on disk is the ground truth instead.
        requested = entry.get("requested_downloads") or []
        filepath = None
        for rd in requested:
            candidate = rd.get("filepath") or rd.get("_filename")
            if candidate and os.path.exists(candidate):
                filepath = candidate
                break
        if not filepath:
            candidate = ydl.prepare_filename(entry)
            if os.path.exists(candidate):
                filepath = candidate

        if not filepath:
            continue

        ext = os.path.splitext(filepath)[1].lower().lstrip(".")
        is_video = ext in ("mp4", "mov", "mkv", "webm", "m4v", "avi")
        results.append({"path": filepath, "is_video": is_video})
    return results


IG_APP_ID = "936619743392459"  # Instagram's public web-client app ID


def _cookie_jar_dict():
    """Reads the cookies file (if any) back into a plain name->value
    dict, for use as request cookies in the direct-scrape fallback."""
    cookies_path = _cookies_file_path()
    if not cookies_path:
        return {}
    try:
        import http.cookiejar

        jar = http.cookiejar.MozillaCookieJar(cookies_path)
        jar.load(ignore_discard=True, ignore_expires=True)
        return {c.name: c.value for c in jar if "instagram.com" in c.domain}
    except Exception:
        return {}


async def _fallback_scrape_extract(link: str) -> list:
    """Used only when yt-dlp fails outright (e.g. Instagram API 400s
    it's hitting internally). Doesn't reimplement Instagram's private
    GraphQL app — those query hashes rotate often and are themselves
    fragile. Instead this scrapes the same og:video / og:image meta
    tags Instagram serves on every post's embed page so it unfurls
    correctly in WhatsApp/Telegram/Twitter link previews — Instagram
    has strong incentive to keep those stable since the entire web's
    link-preview tooling depends on them.

    Only covers single-item posts/reels (carousels only expose their
    first item this way) — yt-dlp stays the primary path, this is
    strictly a backup for when that path is broken."""
    match = re.search(r"/(?:p|reel|tv)/([A-Za-z0-9_-]+)", link)
    if not match:
        return []
    shortcode = match.group(1)
    embed_url = f"https://www.instagram.com/p/{shortcode}/embed/captioned/"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "X-IG-App-ID": IG_APP_ID,
        "Accept": "text/html,application/xhtml+xml",
    }
    cookies = _cookie_jar_dict()

    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as http_client:
        resp = await http_client.get(embed_url, headers=headers, cookies=cookies)
        resp.raise_for_status()
        html = resp.text

    video_match = re.search(r'<meta property="og:video" content="([^"]+)"', html)
    image_match = re.search(r'<meta property="og:image" content="([^"]+)"', html)

    if video_match:
        media_url = video_match.group(1).replace("&amp;", "&")
        is_video = True
    elif image_match:
        media_url = image_match.group(1).replace("&amp;", "&")
        is_video = False
    else:
        return []

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    ext = "mp4" if is_video else "jpg"
    filepath = os.path.join(DOWNLOAD_DIR, f"insta_fallback_{shortcode}.{ext}")

    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as http_client:
        media_resp = await http_client.get(media_url, headers=headers)
        media_resp.raise_for_status()
        with open(filepath, "wb") as f:
            f.write(media_resp.content)

    return [{"path": filepath, "is_video": is_video}]


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
        try:
            files = await loop.run_in_executor(None, _extract_entries, link)
        except Exception as ytdlp_err:
            print(f"[instadl] yt-dlp failed ({ytdlp_err}); trying direct-scrape fallback")
            files = await _fallback_scrape_extract(link)
            if not files:
                # Nothing recovered — re-raise the original yt-dlp
                # error so the existing error-message logic below
                # picks the right explanation (login-gated, 400, etc).
                raise ytdlp_err

        if not files:
            await message.reply_text(
                "Unable to fetch content. The link might be private, "
                "deleted, or unsupported."
            )
            return

        if len(files) == 1:
            f = files[0]
            try:
                if f["is_video"]:
                    await message.reply_video(
                        f["path"],
                        caption=CAPTION_TEXT,
                        parse_mode=ParseMode.HTML,
                        reply_markup=RESULT_MARKUP,
                    )
                else:
                    await message.reply_photo(
                        f["path"],
                        caption=CAPTION_TEXT,
                        parse_mode=ParseMode.HTML,
                        reply_markup=RESULT_MARKUP,
                    )
            except Exception as send_err:
                # Belt-and-braces: if Telegram still rejects it as the
                # detected type (e.g. an odd container/codec it's
                # picky about), try the other type before giving up,
                # instead of failing the whole download.
                print(f"[instadl] send as {'video' if f['is_video'] else 'photo'} failed ({send_err}), trying document")
                await message.reply_document(
                    f["path"],
                    caption=CAPTION_TEXT,
                    parse_mode=ParseMode.HTML,
                    reply_markup=RESULT_MARKUP,
                )
        else:
            # Carousel post — send everything together as an album.
            # Media groups can't carry an inline keyboard, so the
            # caption + Group button go on the first item's own
            # message, sent as a normal follow-up right after.
            media_group = []
            for f in files:
                if f["is_video"]:
                    media_group.append(InputMediaVideo(f["path"]))
                else:
                    media_group.append(InputMediaPhoto(f["path"]))
            # Telegram allows at most 10 items per media group.
            for i in range(0, len(media_group), 10):
                await message.reply_media_group(media_group[i : i + 10])
            await message.reply_text(
                CAPTION_TEXT, parse_mode=ParseMode.HTML, reply_markup=RESULT_MARKUP
            )

    except Exception as e:
        print(f"[instadl] {e}")
        err_msg = str(e).lower()
        if "empty media response" in err_msg or "logged-in" in err_msg:
            err_text = (
                "❌ Instagram is asking for a login to view this post. "
                "The bot owner needs to set the INSTAGRAM_COOKIES "
                "environment variable to download login-gated content."
            )
        elif "400" in err_msg or "401" in err_msg or "403" in err_msg:
            err_text = (
                "❌ Instagram rejected this request. This usually means "
                "either the bot's INSTAGRAM_COOKIES session has expired "
                "(re-export fresh cookies from a logged-in browser), or "
                "yt-dlp needs updating since Instagram changes its API "
                "often. Please try again in a bit."
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
