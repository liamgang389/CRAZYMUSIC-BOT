import asyncio
import json
import os
import re
from typing import Union
from pytgcalls.types.input_stream import InputStream
from pytgcalls.types.input_stream import InputAudioStream

import aiohttp
import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch

from CRAZYHUBBOT.utils.database import is_on_off
from CRAZYHUBBOT.utils.formatters import time_to_seconds

try:
    from config import USE_CRAZYHUB_API
except ImportError:
    # config.py on the deployed server hasn't been updated with this
    # variable yet — default to the old behavior (API first, yt-dlp
    # fallback) instead of crashing the whole bot on import.
    USE_CRAZYHUB_API = True


import os
import glob
import random
import logging

def cookie_txt_file():
    """Deprecated: this bot no longer uses cookies. Kept as a no-op so any
    stray reference elsewhere doesn't crash; returns None."""
    return None


# ---------------------------------------------------------------------------
# API-based download — two APIs are tried in order before falling back to
# cookie-free yt-dlp:
#   1. CRAZYHUB_API (your own deployment)
#   2. Shruti API (shrutibots) — used only if CRAZYHUB_API fails/unreachable
# ---------------------------------------------------------------------------
CRAZYHUB_API_URL = os.environ.get("CRAZYHUB_API_URL", "http://localhost:8000")
CRAZYHUB_API_KEY = os.environ.get("CRAZYHUB_API_KEY", None)  ## Must match the API_KEY set on your CRAZYHUB_API server

SHRUTI_API_URL = os.environ.get("SHRUTI_API_URL", "https://api01.shrutibots.site")
_DEFAULT_SHRUTI_KEY = "ShrutiBots3OYSuzKa7u0PyQi3ifqT"
SHRUTI_API_KEY = os.environ.get("SHRUTI_API_KEY", _DEFAULT_SHRUTI_KEY)  ## Get this from Telegram bot: @SHRUTIAPIBOT

if not CRAZYHUB_API_KEY:
    print(
        "[CrazyHubAPI] WARNING: CRAZYHUB_API_KEY env var is not set — "
        "API downloads will fail (the server always requires an api_key). "
        "Set CRAZYHUB_API_URL/CRAZYHUB_API_KEY to match your CRAZYHUB_API deployment. "
        "Shruti API will be used as fallback instead.",
        flush=True,
    )
else:
    print("[CrazyHubAPI] Using CRAZYHUB_API_KEY from the environment.", flush=True)

if SHRUTI_API_KEY == _DEFAULT_SHRUTI_KEY:
    print(
        "[ShrutiAPI] WARNING: SHRUTI_API_KEY env var is not set — "
        "using the shared default demo key, which is likely rate-limited/unreliable. "
        "Get your own key from @SHRUTIAPIBOT on Telegram and set SHRUTI_API_KEY.",
        flush=True,
    )
else:
    print("[ShrutiAPI] Using your own SHRUTI_API_KEY from the environment.", flush=True)


def _extract_video_id(link: str) -> str:
    if "v=" in link:
        return link.split("v=")[-1].split("&")[0]
    if "youtu.be/" in link:
        return link.split("youtu.be/")[-1].split("?")[0]
    return link


def _watch_url_from_id(video_id: str) -> str:
    # CRAZYHUB_API validates its "url" param as an absolute http(s) URL
    # (scheme + host), so a bare video id is rejected — always send a
    # full YouTube watch URL, never just the id. (Shruti's API accepts
    # the bare video id directly, so it doesn't need this.)
    return f"https://www.youtube.com/watch?v={video_id}"


async def _fetch_to_file(url: str, params: dict, file_path: str, timeout_s: int, tag: str) -> str:
    """Shared GET-and-stream-to-disk helper used by both APIs. Returns
    file_path on success, None on any failure (never raises)."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, params=params, timeout=aiohttp.ClientTimeout(total=timeout_s)
            ) as resp:
                if resp.status != 200:
                    body_preview = (await resp.text())[:300]
                    logging.warning(f"[{tag}] request failed: HTTP {resp.status} — {body_preview}")
                    return None
                with open(file_path, "wb") as f:
                    async for chunk in resp.content.iter_chunked(131072):
                        f.write(chunk)
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            return file_path
        return None
    except Exception as e:
        logging.warning(f"[{tag}] download failed: {e}")
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
        return None


async def crazyhub_download_song(video_id: str, file_path: str) -> str:
    return await _fetch_to_file(
        f"{CRAZYHUB_API_URL}/download",
        {"url": _watch_url_from_id(video_id), "type": "audio", "api_key": CRAZYHUB_API_KEY},
        file_path, 300, "CrazyHubAPI",
    )


async def crazyhub_download_video(video_id: str, file_path: str) -> str:
    return await _fetch_to_file(
        f"{CRAZYHUB_API_URL}/download",
        {"url": _watch_url_from_id(video_id), "type": "video", "api_key": CRAZYHUB_API_KEY},
        file_path, 600, "CrazyHubAPI",
    )


async def shruti_download_song(video_id: str, file_path: str) -> str:
    return await _fetch_to_file(
        f"{SHRUTI_API_URL}/download",
        {"url": video_id, "type": "audio", "api_key": SHRUTI_API_KEY},
        file_path, 300, "ShrutiAPI",
    )


async def shruti_download_video(video_id: str, file_path: str) -> str:
    return await _fetch_to_file(
        f"{SHRUTI_API_URL}/download",
        {"url": video_id, "type": "video", "api_key": SHRUTI_API_KEY},
        file_path, 600, "ShrutiAPI",
    )


async def api_download_song(link: str) -> str:
    """Try CRAZYHUB_API first, then Shruti API. Returns file path or None
    if both fail (caller then falls back to yt-dlp)."""
    video_id = _extract_video_id(link)
    if not video_id or len(video_id) < 3:
        return None

    os.makedirs("downloads", exist_ok=True)
    file_path = os.path.join("downloads", f"{video_id}.mp3")
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return file_path

    result = await crazyhub_download_song(video_id, file_path)
    if result:
        return result

    logging.warning("[CrazyHubAPI] audio failed, trying Shruti API")
    return await shruti_download_song(video_id, file_path)


async def api_download_video(link: str) -> str:
    """Try CRAZYHUB_API first, then Shruti API. Returns file path or None
    if both fail (caller then falls back to yt-dlp)."""
    video_id = _extract_video_id(link)
    if not video_id or len(video_id) < 3:
        return None

    os.makedirs("downloads", exist_ok=True)
    file_path = os.path.join("downloads", f"{video_id}.mp4")
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return file_path

    result = await crazyhub_download_video(video_id, file_path)
    if result:
        return result

    logging.warning("[CrazyHubAPI] video failed, trying Shruti API")
    return await shruti_download_video(video_id, file_path)


# ---------------------------------------------------------------------------
# Cookie-free YouTube access (fallback path).
# We avoid --cookies / cookiefile entirely and instead ask yt-dlp to use the
# "android" / "web" InnerTube player clients, which (unlike the default web
# client) do not require a signed-in session to fetch playback URLs. If
# YouTube tightens this further in the future, keep yt-dlp itself updated
# (`pip install -U yt-dlp`) — this trick relies on yt-dlp's extractor, not on
# this bot's code.
# ---------------------------------------------------------------------------
NO_COOKIE_YTDL_OPTS = {
    "geo_bypass": True,
    "nocheckcertificate": True,
    "extractor_args": {"youtube": {"player_client": ["android", "ios", "tv_embedded", "web"]}},
}
NO_COOKIE_CLI_ARGS = ["--extractor-args", "youtube:player_client=android,ios,tv_embedded,web"]


def _ytdlp_video_metadata(link: str) -> dict:
    """Fallback metadata fetch used when youtubesearchpython fails/crashes
    (it has a known bug where some videos have no channel id and it raises
    a TypeError instead of returning results). Since every caller of this
    already knows the exact video URL, we can just ask yt-dlp for the same
    info directly instead of searching for it."""
    ytdl_opts = {"quiet": True, "skip_download": True, **NO_COOKIE_YTDL_OPTS}
    with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
        info = ydl.extract_info(link, download=False)
    duration_sec = info.get("duration") or 0
    minutes, seconds = divmod(int(duration_sec), 60)
    hours, minutes = divmod(minutes, 60)
    duration_min = f"{hours}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes}:{seconds:02d}"
    thumbnails = info.get("thumbnails") or []
    thumbnail = thumbnails[-1]["url"].split("?")[0] if thumbnails else ""
    return {
        "title": info.get("title") or "Unknown",
        "duration_min": duration_min,
        "duration_sec": int(duration_sec),
        "thumbnail": thumbnail,
        "vidid": info.get("id") or "",
        "link": info.get("webpage_url") or link,
    }


def _ytdlp_search_metadata(query: str, limit: int = 10) -> list:
    """Same fallback idea as _ytdlp_video_metadata, but for an actual text
    search (used by slider()) rather than a single known video URL."""
    ytdl_opts = {"quiet": True, "skip_download": True, "extract_flat": "in_playlist", **NO_COOKIE_YTDL_OPTS}
    with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
    entries = info.get("entries") or []
    results = []
    for entry in entries:
        duration_sec = entry.get("duration") or 0
        minutes, seconds = divmod(int(duration_sec), 60)
        hours, minutes = divmod(minutes, 60)
        duration_min = f"{hours}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes}:{seconds:02d}"
        thumbnails = entry.get("thumbnails") or []
        thumbnail = thumbnails[-1]["url"].split("?")[0] if thumbnails else ""
        results.append(
            {
                "title": entry.get("title") or "Unknown",
                "duration_min": duration_min,
                "thumbnail": thumbnail,
                "vidid": entry.get("id") or "",
            }
        )
    return results


def _ytdlp_mix_related(vidid: str, exclude_vidid: str = None, limit: int = 8) -> list:
    """Uses YouTube's own auto-generated 'Mix' playlist for a video —
    this is literally the same thing YouTube's native autoplay follows
    on youtube.com, so it gives genuinely varied but related songs
    (different tracks by the same artist/genre/era) instead of just
    other uploads of the exact same song, which is what a plain title
    search mostly turns up."""
    url = f"https://www.youtube.com/watch?v={vidid}&list=RD{vidid}"
    ytdl_opts = {
        "quiet": True,
        "skip_download": True,
        "extract_flat": "in_playlist",
        **NO_COOKIE_YTDL_OPTS,
    }
    with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    entries = info.get("entries") or []
    results = []
    for entry in entries:
        entry_vidid = entry.get("id") or ""
        if not entry_vidid or entry_vidid in (vidid, exclude_vidid):
            continue
        duration_sec = entry.get("duration") or 0
        minutes, seconds = divmod(int(duration_sec), 60)
        hours, minutes = divmod(minutes, 60)
        duration_min = f"{hours}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes}:{seconds:02d}"
        results.append(
            {
                "title": entry.get("title") or "Unknown",
                "duration_min": duration_min,
                "vidid": entry_vidid,
                "link": f"https://www.youtube.com/watch?v={entry_vidid}",
            }
        )
        if len(results) >= limit:
            break
    return results


async def check_file_size(link):
    async def get_format_info(link):
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            *NO_COOKIE_CLI_ARGS,
            "-J",
            link,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            print(f'Error:\n{stderr.decode()}')
            return None
        return json.loads(stdout.decode())

    def parse_size(formats):
        total_size = 0
        for format in formats:
            if 'filesize' in format:
                total_size += format['filesize']
        return total_size

    info = await get_format_info(link)
    if info is None:
        return None
    
    formats = info.get('formats', [])
    if not formats:
        print("No formats found.")
        return None
    
    total_size = parse_size(formats)
    return total_size

async def shell_cmd(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, errorz = await proc.communicate()
    if errorz:
        if "unavailable videos are hidden" in (errorz.decode("utf-8")).lower():
            return out.decode("utf-8")
        else:
            return errorz.decode("utf-8")
    return out.decode("utf-8")


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if re.search(self.regex, link):
            return True
        else:
            return False

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        text = ""
        offset = None
        length = None
        for message in messages:
            if offset:
                break
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        offset, length = entity.offset, entity.length
                        break
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        if offset in (None,):
            return None
        return text[offset : offset + length]

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        try:
            results = VideosSearch(link, limit=1)
            for result in (await results.next())["result"]:
                title = result["title"]
                duration_min = result["duration"]
                thumbnail = result["thumbnails"][0]["url"].split("?")[0]
                vidid = result["id"]
                if str(duration_min) == "None":
                    duration_sec = 0
                else:
                    duration_sec = int(time_to_seconds(duration_min))
        except Exception:
            meta = _ytdlp_video_metadata(link)
            title = meta["title"]
            duration_min = meta["duration_min"]
            duration_sec = meta["duration_sec"]
            thumbnail = meta["thumbnail"]
            vidid = meta["vidid"]
        return title, duration_min, duration_sec, thumbnail, vidid

    async def title(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        try:
            results = VideosSearch(link, limit=1)
            for result in (await results.next())["result"]:
                title = result["title"]
        except Exception:
            title = _ytdlp_video_metadata(link)["title"]
        return title

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        try:
            results = VideosSearch(link, limit=1)
            for result in (await results.next())["result"]:
                duration = result["duration"]
        except Exception:
            duration = _ytdlp_video_metadata(link)["duration_min"]
        return duration

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        try:
            results = VideosSearch(link, limit=1)
            for result in (await results.next())["result"]:
                thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        except Exception:
            thumbnail = _ytdlp_video_metadata(link)["thumbnail"]
        return thumbnail

    async def video(self, link: str, videoid: Union[bool, str] = None):
        """
        Returns a direct streamable URL (used by pytgcalls InputStream).
        This stays on yt-dlp's -g flag since the API only returns downloadable
        files, not a direct stream URL.
        """
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            *NO_COOKIE_CLI_ARGS,
            "-g",
            "-f",
            "best[height<=?720][width<=?1280]",
            f"{link}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if stdout:
            return 1, stdout.decode().split("\n")[0]
        else:
            return 0, stderr.decode()

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        if "&" in link:
            link = link.split("&")[0]
        playlist = await shell_cmd(
            f"yt-dlp -i --get-id --flat-playlist --extractor-args \"youtube:player_client=android,ios,tv_embedded,web\" --playlist-end {limit} --skip-download {link}"
        )
        try:
            result = playlist.split("\n")
            for key in result:
                if key == "":
                    result.remove(key)
        except:
            result = []
        return result

    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        try:
            results = VideosSearch(link, limit=1)
            for result in (await results.next())["result"]:
                title = result["title"]
                duration_min = result["duration"]
                vidid = result["id"]
                yturl = result["link"]
                thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            track_details = {
                "title": title,
                "link": yturl,
                "vidid": vidid,
                "duration_min": duration_min,
                "thumb": thumbnail,
            }
        except Exception:
            meta = _ytdlp_video_metadata(link)
            track_details = {
                "title": meta["title"],
                "link": meta["link"],
                "vidid": meta["vidid"],
                "duration_min": meta["duration_min"],
                "thumb": meta["thumbnail"],
            }
        return track_details, track_details["vidid"]

    async def related(self, title: str, exclude_vidid: str = None, limit: int = 6):
        """Autoplay support: prefers YouTube's own auto-generated Mix
        playlist for exclude_vidid — the same mechanism youtube.com's
        native autoplay uses, so results are genuinely varied songs
        rather than reuploads of the same track. Falls back to a plain
        title search only if the Mix playlist can't be fetched (e.g.
        very obscure video, or extraction blocked). Returns a list of
        track dicts (most-relevant first), possibly empty."""
        candidates = []
        if exclude_vidid:
            try:
                candidates = _ytdlp_mix_related(exclude_vidid, exclude_vidid, limit=limit)
            except Exception:
                candidates = []
        if candidates:
            return candidates

        try:
            results = VideosSearch(title, limit=limit + 2)
            for result in (await results.next())["result"]:
                vidid = result["id"]
                if exclude_vidid and vidid == exclude_vidid:
                    continue
                candidates.append(
                    {
                        "title": result["title"],
                        "link": result["link"],
                        "vidid": vidid,
                        "duration_min": result["duration"],
                        "thumb": result["thumbnails"][0]["url"].split("?")[0],
                    }
                )
                if len(candidates) >= limit:
                    break
        except Exception:
            pass
        return candidates

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        ytdl_opts = {"quiet": True, **NO_COOKIE_YTDL_OPTS}
        ydl = yt_dlp.YoutubeDL(ytdl_opts)
        with ydl:
            formats_available = []
            r = ydl.extract_info(link, download=False)
            for format in r["formats"]:
                try:
                    str(format["format"])
                except:
                    continue
                if not "dash" in str(format["format"]).lower():
                    try:
                        format["format"]
                        format["filesize"]
                        format["format_id"]
                        format["ext"]
                        format["format_note"]
                    except:
                        continue
                    formats_available.append(
                        {
                            "format": format["format"],
                            "filesize": format["filesize"],
                            "format_id": format["format_id"],
                            "ext": format["ext"],
                            "format_note": format["format_note"],
                            "yturl": link,
                        }
                    )
        return formats_available, link

    async def slider(
        self,
        link: str,
        query_type: int,
        videoid: Union[bool, str] = None,
    ):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        a = VideosSearch(link, limit=10)
        try:
            result = (await a.next()).get("result")
            title = result[query_type]["title"]
            duration_min = result[query_type]["duration"]
            vidid = result[query_type]["id"]
            thumbnail = result[query_type]["thumbnails"][0]["url"].split("?")[0]
        except Exception:
            results = _ytdlp_search_metadata(link, limit=10)
            picked = results[query_type]
            title = picked["title"]
            duration_min = picked["duration_min"]
            vidid = picked["vidid"]
            thumbnail = picked["thumbnail"]
        return title, duration_min, thumbnail, vidid

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> str:
        if videoid:
            link = self.base + link
        loop = asyncio.get_running_loop()

        def audio_dl_ytdlp():
            ydl_optssx = {
                "format": "bestaudio/best",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "extractor_args": {"youtube": {"player_client": ["android", "ios", "tv_embedded", "web"]}},
                "no_warnings": True,
            }
            x = yt_dlp.YoutubeDL(ydl_optssx)
            info = x.extract_info(link, False)
            xyz = os.path.join("downloads", f"{info['id']}.{info['ext']}")
            if os.path.exists(xyz):
                return xyz
            x.download([link])
            return xyz

        def video_dl_ytdlp():
            ydl_optssx = {
                "format": "(bestvideo[height<=?720][width<=?1280][ext=mp4])+(bestaudio[ext=m4a])",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "extractor_args": {"youtube": {"player_client": ["android", "ios", "tv_embedded", "web"]}},
                "no_warnings": True,
            }
            x = yt_dlp.YoutubeDL(ydl_optssx)
            info = x.extract_info(link, False)
            xyz = os.path.join("downloads", f"{info['id']}.{info['ext']}")
            if os.path.exists(xyz):
                return xyz
            x.download([link])
            return xyz

        def song_video_dl():
            formats = f"{format_id}+140"
            fpath = f"downloads/{title}"
            ydl_optssx = {
                "format": formats,
                "outtmpl": fpath,
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "extractor_args": {"youtube": {"player_client": ["android", "ios", "tv_embedded", "web"]}},
                "prefer_ffmpeg": True,
                "merge_output_format": "mp4",
            }
            x = yt_dlp.YoutubeDL(ydl_optssx)
            x.download([link])

        def song_audio_dl():
            fpath = f"downloads/{title}.%(ext)s"
            ydl_optssx = {
                "format": format_id,
                "outtmpl": fpath,
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "extractor_args": {"youtube": {"player_client": ["android", "ios", "tv_embedded", "web"]}},
                "prefer_ffmpeg": True,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
            }
            x = yt_dlp.YoutubeDL(ydl_optssx)
            x.download([link])

        # format_id-specific downloads (used by /songvideo and /songaudio) stay
        # on yt-dlp since the API doesn't support arbitrary format selection.
        if songvideo:
            await loop.run_in_executor(None, song_video_dl)
            fpath = f"downloads/{title}.mp4"
            return fpath
        elif songaudio:
            await loop.run_in_executor(None, song_audio_dl)
            fpath = f"downloads/{title}.mp3"
            return fpath
        elif video:
            if await is_on_off(1):
                # API first (unless disabled via USE_CRAZYHUB_API), yt-dlp fallback
                direct = True
                downloaded_file = await api_download_video(link) if USE_CRAZYHUB_API else None
                if not downloaded_file:
                    if USE_CRAZYHUB_API:
                        logging.warning("[CrazyHubAPI] video download failed, falling back to yt-dlp")
                    downloaded_file = await loop.run_in_executor(None, video_dl_ytdlp)
            else:
                proc = await asyncio.create_subprocess_exec(
                    "yt-dlp",
                    *NO_COOKIE_CLI_ARGS,
                    "-g",
                    "-f",
                    "best[height<=?720][width<=?1280]",
                    f"{link}",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await proc.communicate()
                if stdout:
                    downloaded_file = stdout.decode().split("\n")[0]
                    direct = False
                else:
                   file_size = await check_file_size(link)
                   if not file_size:
                     print("None file Size")
                     return
                   total_size_mb = file_size / (1024 * 1024)
                   if total_size_mb > 250:
                     print(f"File size {total_size_mb:.2f} MB exceeds the 100MB limit.")
                     return None
                   direct = True
                   downloaded_file = await api_download_video(link) if USE_CRAZYHUB_API else None
                   if not downloaded_file:
                       downloaded_file = await loop.run_in_executor(None, video_dl_ytdlp)
        else:
            # Plain audio download — API first (unless disabled via
            # USE_CRAZYHUB_API), yt-dlp fallback
            direct = True
            downloaded_file = await api_download_song(link) if USE_CRAZYHUB_API else None
            if not downloaded_file:
                if USE_CRAZYHUB_API:
                    logging.warning("[CrazyHubAPI] audio download failed, falling back to yt-dlp")
                downloaded_file = await loop.run_in_executor(None, audio_dl_ytdlp)
        return downloaded_file, direct
