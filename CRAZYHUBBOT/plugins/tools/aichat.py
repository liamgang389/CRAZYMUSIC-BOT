"""
AI Chat — no command needed. Talk to the bot normally (private or
group) and it replies, using AgentRouter (OpenAI-compatible).

Since this now fires on every plain message instead of only on an
explicit /chat command, credit usage will be noticeably higher in
active groups. What's still in place to control that:
- Replies are capped short (config.AI_CHAT_MAX_TOKENS).
- Only the last few turns of a chat's history are sent back to the
  model (config.AI_CHAT_HISTORY_TURNS) — not the whole conversation.
- A short per-user cooldown (config.AI_CHAT_COOLDOWN_SECONDS) stops
  one person from spamming requests and burning credits fast.
- History is kept in memory only (resets on restart).
- Command messages, and messages containing an Instagram link (so it
  doesn't double-fire alongside the auto-download feature), are
  skipped entirely.
If a group turns out too chatty for this, raise
AI_CHAT_COOLDOWN_SECONDS or lower AI_CHAT_HISTORY_TURNS/MAX_TOKENS —
no code changes needed.
"""

import asyncio
import glob
import re
import time
from collections import deque

import httpx
from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.types import Message

import config
from CRAZYHUBBOT import app
from config import BANNED_USERS

# {chat_id: deque of {"role": "user"/"assistant", "content": str}}
_chat_history = {}
# {user_id: last_request_timestamp} — for the cooldown
_last_request = {}

SYSTEM_PROMPT = (
    "You are Music Genie X, a friendly, helpful assistant chatting "
    "inside a Telegram chat. If asked your name, say Music Genie X — "
    "never mention any underlying AI provider or model name. If asked "
    "who your owner/creator/developer is, say YTFARMAN. Keep replies "
    "natural, warm, and concise — a couple of sentences unless the "
    "person clearly wants more detail. Be polite and easy to talk "
    "to, never rude or dismissive. If asked about having a "
    "boyfriend/girlfriend/crush or being in a relationship, you can "
    "playfully tease that the person you're currently talking to is "
    "your crush/boyfriend/girlfriend, using their own name (given "
    "below) — keep it light and obviously joking, never a serious or "
    "literal claim. Never claim a real romantic relationship with "
    "anyone else by name."
)

# This bot uses several different command-prefix sets across its
# plugins (/, !, ., %, ,, @, #), and quite a few commands — including
# /play itself — are also registered with a BLANK prefix, meaning
# they trigger on the bare word with no leading symbol at all (e.g.
# typing "play believer" works exactly like "/play believer"). A
# prefix-character check alone can't catch those, so this scans every
# plugin file at import time for every command name actually
# registered anywhere in the bot, and skips this handler if the
# message's first word matches one — keeping this self-maintaining as
# commands get added/removed elsewhere, instead of a hardcoded list
# that would silently go stale.
def _collect_all_command_names() -> set:
    names = set()
    plugins_dir = __file__.rsplit("plugins", 1)[0] + "plugins"
    for path in glob.glob(f"{plugins_dir}/**/*.py", recursive=True):
        try:
            text = open(path, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        for m in re.finditer(r"filters\.command\((\[[^\]]*\]|\"[^\"]*\"|'[^']*')", text):
            for cmd in re.findall(r"[\"']([a-zA-Z0-9_]+)[\"']", m.group(1)):
                names.add(cmd.lower())
    return names


BOT_DISPLAY_NAME = "Music Genie X"
OWNER_NAME = "YTFARMAN"

# LLMs don't reliably reproduce an exact fixed string every time (it
# can get shortened/garbled turn to turn, as seen in testing — asked
# for "YTFARMAN" and got "YTFAR", then "YTF"). Names/ownership are
# simple facts, not something that benefits from being generated, so
# these are answered directly in code — guaranteed correct every
# time, and skips an API call too.
_OWNER_QUESTION_RE = re.compile(
    r"\b(owner|malik|maalik|developer|creator|kisne\s*banaya|who\s*made\s*you|"
    r"who\s*created\s*you|who\s*owns\s*you|banaya\s*kisne|tumhe\s*kisne\s*banaya)\b",
    re.IGNORECASE,
)
_NAME_QUESTION_RE = re.compile(
    r"\b(tumhara\s*naam|tera\s*naam|your\s*name|what.?s\s*your\s*name)\b",
    re.IGNORECASE,
)


def _deterministic_reply(text: str) -> str:
    """Returns a fixed answer for questions with one guaranteed-right
    answer (owner, name), or None to fall through to the AI."""
    if _OWNER_QUESTION_RE.search(text):
        return f"Mera owner {OWNER_NAME} hai! 🎵"
    if _NAME_QUESTION_RE.search(text):
        return f"Mera naam {BOT_DISPLAY_NAME} hai! 🎧"
    return None


_KNOWN_COMMAND_NAMES = _collect_all_command_names()
_COMMAND_PREFIX_RE = re.compile(r"^[/!.%,@#]")
# Skip Instagram links so this doesn't fire an extra AI reply
# alongside the auto-download feature on the same message.
_INSTA_LINK_RE = re.compile(
    r"(?:https?://)?(?:www\.)?(?:instagram\.com|instagr\.am)/\S+", re.IGNORECASE
)


def _looks_like_a_command(text: str) -> bool:
    if _COMMAND_PREFIX_RE.match(text):
        return True
    first_word = text.strip().split(None, 1)[0].lower() if text.strip() else ""
    # Strip a possible @BotUsername suffix ("play@MyBot").
    first_word = first_word.split("@", 1)[0]
    return first_word in _KNOWN_COMMAND_NAMES


def _history_for(chat_id: int) -> deque:
    if chat_id not in _chat_history:
        # maxlen keeps this self-trimming — oldest turns fall off
        # automatically, no manual cleanup needed.
        _chat_history[chat_id] = deque(maxlen=config.AI_CHAT_HISTORY_TURNS * 2)
    return _chat_history[chat_id]


async def _ask_agentrouter(chat_id: int, user_text: str, user_name: str = "") -> str:
    history = _history_for(chat_id)
    system_prompt = SYSTEM_PROMPT
    if user_name:
        system_prompt += (
            f" The person you're talking to right now is named "
            f"{user_name} — if you refer to them by name, always use "
            f"it exactly as written here, in full, never shortened, "
            f"abbreviated, or altered."
        )
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_text})

    url = f"{config.AGENTROUTER_BASE_URL.rstrip('/')}/chat/completions"
    payload = {
        "model": config.AGENTROUTER_MODEL,
        "messages": messages,
        "max_tokens": config.AI_CHAT_MAX_TOKENS,
        "temperature": 0.7,
    }
    headers = {
        "Authorization": f"Bearer {config.AGENTROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    # AgentRouter has been observed intermittently returning a 401
    # "unauthorized_client_error" that isn't a real auth failure —
    # the exact same key/model has also gone through fine and reached
    # real API-level responses (e.g. content moderation errors), so
    # this looks like flaky/rate-limited behaviour on their end
    # rather than a genuine rejection. Retrying a couple of times
    # with a short backoff papers over that instead of failing a
    # request that would likely have worked on the next attempt.
    max_attempts = 3
    last_error_body = None
    async with httpx.AsyncClient(timeout=30) as client:
        for attempt in range(1, max_attempts + 1):
            resp = await client.post(url, headers=headers, json=payload)

            if resp.status_code >= 400:
                last_error_body = resp.text[:500]
                is_flaky_unauthorized = (
                    resp.status_code == 401
                    and "unauthorized_client_error" in resp.text
                )
                if is_flaky_unauthorized and attempt < max_attempts:
                    print(
                        f"[aichat] attempt {attempt}/{max_attempts}: transient "
                        f"401 unauthorized_client_error, retrying..."
                    )
                    await asyncio.sleep(1.5 * attempt)
                    continue

                key = config.AGENTROUTER_API_KEY or ""
                masked = (
                    f"{key[:4]}...{key[-4:]} (len={len(key)})"
                    if len(key) > 8
                    else "(too short / empty)"
                )
                print(
                    f"[aichat] {resp.status_code} from {url} "
                    f"(model={config.AGENTROUTER_MODEL}, attempt={attempt}) "
                    f"— key seen by the bot: {masked}. Response body: {last_error_body}"
                )
            resp.raise_for_status()
            data = resp.json()
            break

    reply = data["choices"][0]["message"]["content"].strip()

    history.append({"role": "user", "content": user_text})
    history.append({"role": "assistant", "content": reply})
    return reply


async def _reply_with_ai(message: Message, user_text: str, is_triggered: bool = True):
    if not config.AGENTROUTER_API_KEY:
        return
    if not user_text.strip():
        return

    fixed = _deterministic_reply(user_text)
    if fixed:
        await message.reply_text(fixed)
        return

    # Gemini's free tier only allows 20 requests/minute for the whole
    # bot (shared across every chat, not per-user). Auto-replying to
    # every single group message burns through that fast — so in
    # groups, an explicit trigger (mention or reply to the bot) is
    # required to actually call the AI. Private chats stay
    # command-free since they're naturally low-volume. is_triggered
    # is always True for the explicit /chat command and /ai command.
    if message.chat.type != ChatType.PRIVATE and not is_triggered:
        return

    user_id = message.from_user.id
    now = time.time()
    last = _last_request.get(user_id, 0)
    if now - last < config.AI_CHAT_COOLDOWN_SECONDS:
        return
    _last_request[user_id] = now

    try:
        user_name = message.from_user.first_name if message.from_user else ""
        reply = await _ask_agentrouter(message.chat.id, user_text.strip(), user_name)
        await message.reply_text(reply)
    except Exception as e:
        print(f"[aichat] request failed: {e}")


@app.on_message(filters.command(["chat", "ai"]) & ~BANNED_USERS)
async def ai_chat_command(client, message: Message):
    if not config.AGENTROUTER_API_KEY:
        await message.reply_text(
            "❌ AI chat isn't configured yet — the bot owner needs to set "
            "AGENTROUTER_API_KEY."
        )
        return
    user_text = message.text.split(None, 1)[1] if len(message.command) > 1 else ""
    if not user_text.strip():
        await message.reply_text("Usage: /chat <your message>")
        return
    await _reply_with_ai(message, user_text)


@app.on_message(
    filters.text
    & ~filters.via_bot
    & ~filters.regex(_INSTA_LINK_RE)
    & ~BANNED_USERS,
    # Registered in a non-default group so this NEVER blocks any
    # other command/handler in the bot. Pyrogram only checks the
    # first matching handler within a group and then stops for that
    # group (unless it explicitly calls continue_propagation()) — so
    # a broad "matches any text" filter like this one, if left in the
    # default group 0, would silently swallow every command handled
    # by a plugin that happens to load after this file alphabetically
    # (this is exactly what broke /makesticker, /stickergen, etc.).
    # A separate group runs independently, so group 0's commands are
    # always checked first and normally, with zero interference.
    group=10,
)
async def ai_chat_auto(client, message: Message):
    if not config.AGENTROUTER_API_KEY:
        # Feature not configured yet — stay quiet on every message
        # rather than error out.
        return
    if not message.from_user or message.from_user.is_bot:
        return
    if _looks_like_a_command(message.text):
        return

    # A group message "triggers" the AI if it's a reply to one of the
    # bot's own messages, or @mentions the bot by username.
    is_triggered = True
    if message.chat.type != ChatType.PRIVATE:
        replied = message.reply_to_message
        is_reply_to_bot = bool(
            replied and replied.from_user and replied.from_user.is_self
        )
        is_mentioned = bool(app.username) and f"@{app.username.lower()}" in message.text.lower()
        is_triggered = is_reply_to_bot or is_mentioned

    await _reply_with_ai(message, message.text, is_triggered)
