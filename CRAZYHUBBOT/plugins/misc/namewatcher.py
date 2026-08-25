"""
Automatic Group User Name Change Detector.

No command exists for this feature by design. It is active automatically
in every group where the bot is an admin, and silently does nothing
everywhere else. See mongo/namechangedb.py for storage.
"""

import time

from pyrogram import filters
from pyrogram.enums import ChatMemberStatus, ChatType
from pyrogram.types import ChatMemberUpdated, Message

from CRAZYHUBBOT import app
from CRAZYHUBBOT.mongo.namechangedb import get_stored_name, save_name

# How long we trust a cached "is the bot admin here" result before
# re-checking via get_chat_member. Keeps this feature from calling the
# Telegram API on every single group message.
_ADMIN_CACHE_TTL = 300  # seconds

# chat_id -> (is_admin: bool, checked_at: float)
_bot_admin_cache = {}


async def _is_bot_admin(chat_id: int) -> bool:
    cached = _bot_admin_cache.get(chat_id)
    now = time.time()
    if cached and (now - cached[1]) < _ADMIN_CACHE_TTL:
        return cached[0]

    try:
        member = await app.get_chat_member(chat_id, app.id)
        is_admin = member.status in (
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        )
    except Exception:
        # Bot not in chat, no permission to check, API hiccup, etc.
        # Fail closed: treat as "not admin" rather than crashing.
        is_admin = False

    _bot_admin_cache[chat_id] = (is_admin, now)
    return is_admin


@app.on_chat_member_updated()
async def _namewatcher_track_own_status(_, update: ChatMemberUpdated):
    """Refresh the admin cache the instant the bot itself is promoted or
    demoted, so the feature turns on/off immediately instead of waiting
    for the TTL to expire."""
    try:
        member = update.new_chat_member
        if not member or not member.user or member.user.id != app.id:
            return
        is_admin = member.status in (
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        )
        _bot_admin_cache[update.chat.id] = (is_admin, time.time())
    except Exception:
        return


@app.on_message(filters.group & ~filters.bot & ~filters.via_bot, group=70)
async def _namewatcher_detect(_, message: Message):
    try:
        if message.chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
            return
        if not message.from_user or message.sender_chat:
            return

        if not await _is_bot_admin(message.chat.id):
            return

        user = message.from_user
        current_first = user.first_name or ""
        current_last = user.last_name or ""

        stored = await get_stored_name(message.chat.id, user.id)
        if not stored:
            # First time we've ever seen this user in this chat.
            # Save silently, no alert.
            await save_name(message.chat.id, user.id, current_first, current_last)
            return

        stored_first = stored.get("first_name") or ""
        stored_last = stored.get("last_name") or ""

        old_full = f"{stored_first} {stored_last}".strip() or "Unknown"
        new_full = f"{current_first} {current_last}".strip() or "Unknown"

        if old_full == new_full:
            # No change since last time -> no alert (duplicate prevention).
            return

        # Update the stored name immediately, before sending the alert,
        # so rapid consecutive messages can't trigger a second alert.
        await save_name(message.chat.id, user.id, current_first, current_last)

        mention = f"[{new_full}](tg://user?id={user.id})"
        await message.reply(
            f"🔔 **NAME CHANGED**\n\n"
            f"👤 {mention}\n\n"
            f"📝 {old_full} → {new_full}",
            quote=False,
        )
    except Exception:
        # This is a lightweight background feature; it must never take
        # down the bot or interfere with any other handler.
        return
