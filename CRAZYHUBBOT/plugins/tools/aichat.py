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
from pyrogram.types import Message

import config
from CRAZYHUBBOT import app
from config import BANNED_USERS

# {chat_id: deque of {"role": "user"/"assistant", "content": str}}
_chat_history = {}
# {user_id: last_request_timestamp} — for the cooldown
_last_request = {}

SYSTEM_PROMPT = (
    "You are a friendly, helpful assistant chatting inside a Telegram "
    "chat. Keep replies natural, warm, and concise — a couple of "
    "sentences unless the person clearly wants more detail. Be polite "
    "and easy to talk to, never rude or dismissive."
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


async def _ask_agentrouter(chat_id: int, user_text: str) -> str:
    history = _history_for(chat_id)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
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


async def _reply_with_ai(message: Message, user_text: str):
    if not config.AGENTROUTER_API_KEY:
        return
    if not user_text.strip():
        return

    user_id = message.from_user.id
    now = time.time()
    last = _last_request.get(user_id, 0)
    if now - last < config.AI_CHAT_COOLDOWN_SECONDS:
        return
    _last_request[user_id] = now

    try:
        reply = await _ask_agentrouter(message.chat.id, user_text.strip())
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
    & ~BANNED_USERS
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

    await _reply_with_ai(message, message.text)
