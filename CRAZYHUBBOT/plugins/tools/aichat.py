"""
AI Chat — lets people talk to the bot naturally via /chat, or by
replying to one of the bot's own AI replies (so it feels like an
ongoing conversation, not just one-off commands).

Built to keep API credit usage low:
- Replies are capped short (config.AI_CHAT_MAX_TOKENS).
- Only the last few turns of a chat's history are sent back to the
  model (config.AI_CHAT_HISTORY_TURNS) — not the whole conversation.
- A short per-user cooldown (config.AI_CHAT_COOLDOWN_SECONDS) stops
  one person from spamming requests and burning credits fast.
- History is kept in memory only (resets on restart) — no growing
  database of every message ever sent.
"""

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
    "group. Keep replies natural, warm, and concise — a couple of "
    "sentences unless the person clearly wants more detail. Be polite "
    "and easy to talk to, never rude or dismissive."
)


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

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{config.AGENTROUTER_BASE_URL.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {config.AGENTROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": config.AGENTROUTER_MODEL,
                "messages": messages,
                "max_tokens": config.AI_CHAT_MAX_TOKENS,
                "temperature": 0.7,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    reply = data["choices"][0]["message"]["content"].strip()

    history.append({"role": "user", "content": user_text})
    history.append({"role": "assistant", "content": reply})
    return reply


async def _handle_chat(message: Message, user_text: str):
    if not config.AGENTROUTER_API_KEY:
        # Feature not configured yet — stay quiet rather than error
        # out on every message once auto-reply-to-bot is wired in.
        return

    user_id = message.from_user.id
    now = time.time()
    last = _last_request.get(user_id, 0)
    if now - last < config.AI_CHAT_COOLDOWN_SECONDS:
        return
    _last_request[user_id] = now

    if not user_text.strip():
        await message.reply_text("Usage: /chat <your message>")
        return

    status = await message.reply_text("💬 ...")
    try:
        reply = await _ask_agentrouter(message.chat.id, user_text.strip())
        await status.edit_text(reply)
    except Exception as e:
        print(f"[aichat] request failed: {e}")
        await status.edit_text(
            "❌ Couldn't reach the AI right now. Try again in a bit."
        )


@app.on_message(filters.command(["chat", "ai"]) & ~BANNED_USERS)
async def ai_chat_command(client, message: Message):
    user_text = message.text.split(None, 1)[1] if len(message.command) > 1 else ""
    await _handle_chat(message, user_text)


# This bot uses several different command-prefix sets across its
# plugins (/, !, ., %, ,, @) — matching any of them here keeps this
# broad reply-listener from ever swallowing an actual command message
# (e.g. "/mute" sent as a reply) ahead of that command's own handler.
_COMMAND_PREFIX_RE = re.compile(r"^[/!.%,@]")


@app.on_message(
    filters.reply
    & filters.text
    & ~filters.via_bot
    & ~filters.regex(_COMMAND_PREFIX_RE)
    & ~BANNED_USERS
)
async def ai_chat_reply(client, message: Message):
    # Only continue the conversation if they're replying to one of
    # THIS bot's own /chat replies — never auto-triggers on unrelated
    # replies, so it doesn't fire (and spend credits) on every message.
    replied = message.reply_to_message
    if not replied or not replied.from_user or not replied.from_user.is_self:
        return
    await _handle_chat(message, message.text)
