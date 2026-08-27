import re
from os import getenv
# ------------------------------------
# ------------------------------------
from dotenv import load_dotenv
from pyrogram import filters
import os
# ------------------------------------
# ------------------------------------
load_dotenv()
# ------------------------------------
# -----------------------------------------------------
API_ID = int(getenv("API_ID",23830188))
API_HASH = getenv("API_HASH")
# ------------------------------------------------------
BOT_TOKEN = getenv("BOT_TOKEN")
# -------------------------------------------------------
OWNER_USERNAME = getenv("OWNER_USERNAME","@Fake_SmileK")
# --------------------------------------------------------
BOT_USERNAME = getenv("BOT_USERNAME" , "@Fake_SmileK")
# --------------------------------------------------------
BOT_NAME = getenv("BOT_NAME" , "𝙁ǻķ𝐞 𝗦𝑚ᶦ𝑙𝐞")
# ---------------------------------------------------------
ASSUSERNAME = getenv("ASSUSERNAME" , "MREVO")
# ---------------------------------------------------------
# ---------- SHRUTI YOUTUBE API ----------
# These MUST be named exactly this way — CRAZYHUBBOT/platforms/Youtube.py
# reads these exact env var names directly. Get your own key from
# @SHRUTIAPIBOT on Telegram; without it, the bot falls back to a shared
# demo key that gets rate-limited fast since many bots share it.
SHRUTI_API_URL = getenv("SHRUTI_API_URL", "https://api01.shrutibots.site")
SHRUTI_API_KEY = getenv("SHRUTI_API_KEY", None)

# Set to "False" to skip the ShrutiAPI entirely and always download via
# cookie-free yt-dlp instead — no API key needed at all. Downloads will
# be a bit slower (yt-dlp extracts + downloads directly from YouTube)
# but won't depend on any external API being up or rate-limited.
USE_SHRUTI_API = getenv("USE_SHRUTI_API", "True").strip().lower() == "true"

#---------------------------------------------------------------
#---------------------------------------------------------------
MONGO_DB_URI = getenv("MONGO_DB_URI", None)
#---------------------------------------------------------------
#---------------------------------------------------------------

# ----------------------------------------------------------------
DURATION_LIMIT_MIN = int(getenv("DURATION_LIMIT", 17000))
# ----------------------------------------------------------------
# ----------------------------------------------------------------

# ----------------------------------------------------------------
LOGGER_ID = int(getenv("LOGGER_ID", -1002133369721))
# ----------------------------------------------------------------
# ----------------------------------------------------------------
OWNER_ID = int(getenv("OWNER_ID", 5948367761))
# -----------------------------------------------------------------
# -----------------------------------------------------------------
# ----------------------------------------------------------------
# ----------------------------------------------------------------
# ----------------------------------------------------------------
HEROKU_APP_NAME = getenv("HEROKU_APP_NAME")
# ----------------------------------------------------------------
HEROKU_API_KEY = getenv("HEROKU_API_KEY")
# ----------------------------------------------------------------
GPT_API = getenv("GPT_API")
# ----------------------------------------------------------------
DEEP_API = getenv("DEEP_API")
# ----------------------------------------------------------------
# OPTIONAL: Instagram cookies for /insta and /ig.
# Many Instagram reels now require a logged-in session to fetch at all
# ("Instagram sent an empty media response" in logs = this). Fully
# optional — without it, publicly-accessible posts still download
# fine, only login-gated ones fail. To enable: export your Instagram
# cookies (logged in, in a normal browser) as a cookies.txt file using
# a browser extension like "Get cookies.txt LOCALLY", then paste the
# ENTIRE file content here as one env var (multi-line values work
# fine in most host panels, e.g. Heroku config vars).
INSTAGRAM_COOKIES = getenv("INSTAGRAM_COOKIES", None)
# ----------------------------------------------------------------
# RapidAPI key for /story (Instagram Stories downloader by username).
# Defaults to the key you gave me so it works out of the box — but
# it's YOUR personal RapidAPI key, tied to your account's request
# quota. Move it into your own env var / secrets panel and rotate it
# if you ever share this repo publicly, since anyone with the code
# can otherwise use up your quota.
RAPIDAPI_INSTAGRAM_KEY = getenv(
    "RAPIDAPI_INSTAGRAM_KEY", "63a242b19dmsha3ab5f2eb03752ep1f97a8jsndb10651254cb"
)

# ----------------------------------------------------------------
# AI Chat (AgentRouter — OpenAI-compatible endpoint). Set your key
# after deploying; the feature just stays silently off until you do.
AGENTROUTER_API_KEY = getenv("AGENTROUTER_API_KEY", None)
AGENTROUTER_BASE_URL = getenv("AGENTROUTER_BASE_URL", "https://agentrouter.org/v1")
AGENTROUTER_MODEL = getenv("AGENTROUTER_MODEL", "deepseek-v4-flash")
# Kept small on purpose to control API credit usage: short replies,
# a short remembered history, and a per-user cooldown so one person
# spamming /chat can't burn through credits fast.
AI_CHAT_MAX_TOKENS = int(getenv("AI_CHAT_MAX_TOKENS", "220"))
AI_CHAT_HISTORY_TURNS = int(getenv("AI_CHAT_HISTORY_TURNS", "3"))
AI_CHAT_COOLDOWN_SECONDS = int(getenv("AI_CHAT_COOLDOWN_SECONDS", "8"))
# ----------------------------------------------------------------
UPSTREAM_REPO = getenv(
    "UPSTREAM_REPO",
    "https://github.com/liamgang389/CrazyMUSIC-BOT",
)
UPSTREAM_BRANCH = getenv("UPSTREAM_BRANCH", "Master")
GIT_TOKEN = getenv(
    "GIT_TOKEN", None
)  # ----------------------------------------------------------------
# -------------------------------------------------------------------
# --------------------------------------------------------------------
# --------------------------------------------------------------------



# ------------------------------------------------------------------------
# -------------------------------------------------------------------------
SUPPORT_CHANNEL = getenv("SUPPORT_CHANNEL", "https://t.me/Crazyhubxbot1")
SUPPORT_CHAT = getenv("SUPPORT_CHAT", "https://t.me/CrazyHubSupport")
# ------------------------------------------------------------------------------
# -------------------------------------------------------------------------------







# --------------------------------------------------------------------------------
# --------------------------------------------------------------------------------
# --------------------------------------------------------------------------------
# --------------------------------------------------------------------------------
AUTO_LEAVING_ASSISTANT = getenv("AUTO_LEAVING_ASSISTANT", "True")
AUTO_LEAVE_ASSISTANT_TIME = int(getenv("ASSISTANT_LEAVE_TIME", "5400"))

# Seconds to wait in an empty voice chat (no real listeners) before the
# assistant automatically stops the stream and leaves the VC.
AUTO_END_TIME = int(getenv("AUTO_END_TIME", "60"))
# How often (in seconds) the empty-VC watcher checks every active call.
AUTO_END_CHECK_INTERVAL = int(getenv("AUTO_END_CHECK_INTERVAL", "10"))
SONG_DOWNLOAD_DURATION = int(getenv("SONG_DOWNLOAD_DURATION", "9999999"))
SONG_DOWNLOAD_DURATION_LIMIT = int(getenv("SONG_DOWNLOAD_DURATION_LIMIT", "9999999"))
# --------------------------------------------------------------------------------
# --------------------------------------------------------------------------------
# --------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------
SPOTIFY_CLIENT_ID = getenv("SPOTIFY_CLIENT_ID", "1c21247d714244ddbb09925dac565aed")
SPOTIFY_CLIENT_SECRET = getenv("SPOTIFY_CLIENT_SECRET", "709e1a2969664491b58200860623ef19")
# ----------------------------------------------------------------------------------




# -----------------------------------------------------------------------------------
PLAYLIST_FETCH_LIMIT = int(getenv("PLAYLIST_FETCH_LIMIT", 30))
# ------------------------------------------------------------------------------------

# ------------------------------------------------------------------------------------
TG_AUDIO_FILESIZE_LIMIT = int(getenv("TG_AUDIO_FILESIZE_LIMIT", "5242880000"))
TG_VIDEO_FILESIZE_LIMIT = int(getenv("TG_VIDEO_FILESIZE_LIMIT", "5242880000"))
# --------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------



# ------------------------------------
# ------------------------------------
# ------------------------------------
# ------------------------------------
STRING1 = getenv("STRING_SESSION", None)
STRING2 = getenv("STRING_SESSION2", None)
STRING3 = getenv("STRING_SESSION3", None)
STRING4 = getenv("STRING_SESSION4", None)
STRING5 = getenv("STRING_SESSION5", None)
STRING6 = getenv("STRING_SESSION6", None)
STRING7 = getenv("STRING_SESSION7", None)
BANNED_USERS = filters.user()
adminlist = {}
lyrical = {}
votemode = {}
autoclean = []
confirmer = {}

# ------------------------------------
# ------------------------------------
# ------------------------------------
# ------------------------------------

# ------------------------------------------------------------------------
# ------------------------------------------------------------------------
# ------------------------------------------------------------------------
# ------------------------------------------------------------------------
# ------------------------------------------------------------------------
# ------------------------------------------------------------------------
# ------------------------------------------------------------------------
START_IMG_URL = getenv(
    "START_IMG_URL", "https://telegra.ph/file/cfbdee8103102bcb2e5da.jpg"
)
PING_IMG_URL = getenv(
    "PING_IMG_URL", "https://telegra.ph/file/00360393a15daf7fc4e9d.jpg"
)
PLAYLIST_IMG_URL = "https://telegra.ph/file/d723f4c80da157fca1678.jpg"
STATS_IMG_URL = "https://telegra.ph/file/d30d11c4365c025c25e3e.jpg"
TELEGRAM_AUDIO_URL = "https://telegra.ph/file/3f0fbea0276a739ee07ce.jpg"
TELEGRAM_VIDEO_URL = "https://telegra.ph/file/e575ae40d6635250974e1.jpg"
STREAM_IMG_URL = "https://telegra.ph/file/03efec694e41e891b29dc.jpg"
SOUNCLOUD_IMG_URL = "https://telegra.ph/file/d723f4c80da157fca1678.jpg"
YOUTUBE_IMG_URL = "https://telegra.ph/file/4dc854f961cd3ce46899b.jpg"
SPOTIFY_ARTIST_IMG_URL = "https://telegra.ph/file/d723f4c80da157fca1678.jpg"
SPOTIFY_ALBUM_IMG_URL = "https://telegra.ph/file/6c741a6bc1e1663ac96fc.jpg"
SPOTIFY_PLAYLIST_IMG_URL = "https://telegra.ph/file/6c741a6bc1e1663ac96fc.jpg"

# ------------------------------------------------------------------------
# ------------------------------------------------------------------------
# ------------------------------------------------------------------------
# ------------------------------------------------------------------------
def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60**i for i, x in enumerate(reversed(stringt.split(":"))))


DURATION_LIMIT = int(time_to_seconds(f"{DURATION_LIMIT_MIN}:00"))

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# ------------------------------------------------------------------------------
if SUPPORT_CHANNEL:
    if not re.match("(?:http|https)://", SUPPORT_CHANNEL):
        raise SystemExit(
            "[ERROR] - Your SUPPORT_CHANNEL url is wrong. Please ensure that it starts with https://"
        )

if SUPPORT_CHAT:
    if not re.match("(?:http|https)://", SUPPORT_CHAT):
        raise SystemExit(
            "[ERROR] - Your SUPPORT_CHAT url is wrong. Please ensure that it starts with https://"
        )
# ---------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
