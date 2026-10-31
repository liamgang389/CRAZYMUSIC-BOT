import asyncio
import html as _html
import json
import os
import re
import sys
from collections import OrderedDict
from typing import List, Optional

import httpx

import pyrogram.utils
from pyrogram import Client, errors
from pyrogram.enums import ChatMemberStatus, ParseMode
from pyrogram.errors import FloodWait

import config

from ..logging import LOGGER

# Pyrogram's default MIN_CHANNEL_ID is too narrow for some newer/larger
# Telegram channel IDs, causing a spurious "ValueError: Peer id invalid"
# even when the bot is a valid admin there. Widen the accepted range.
pyrogram.utils.MIN_CHANNEL_ID = -1009147483647


# ======================================================================
# IN-BUBBLE BUTTONS (single-file version)
# Buttons ko message ke bubble ke ANDAR bhejta hai (Telegram rich message,
# <tg-button-row>). Kuch bhi reject ho to purana (neeche wala keyboard) chalta hai.
#
# Env:
#   INBUBBLE_BUTTONS=false        -> band (purana behaviour)
#   INBUBBLE_FORCE=true           -> Kurigram detection skip karke chalu
#   INBUBBLE_MEDIA_CALLBACKS=a,b  -> in callback prefixes wale photo/video bhi
#                                    in-bubble (default: dash_cb,dash_back)
# ======================================================================
API = "https://api.telegram.org/bot{token}/{method}"
_client: Optional[httpx.AsyncClient] = None


def _http() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=60)
    return _client


async def _call(method: str, payload: dict, files: Optional[dict] = None) -> dict:
    url = API.format(token=config.BOT_TOKEN, method=method)
    if files:  # local file upload (attach://)
        data = {k: v if isinstance(v, str) else json.dumps(v) for k, v in payload.items()}
        r = await _http().post(url, data=data, files=files)
    else:
        r = await _http().post(url, json=payload)
    data = r.json()
    if not data.get("ok"):
        raise RuntimeError(f"{method}: {data.get('description')}")
    return data["result"]


# ----------------------------------------------------------------------
# HTML helpers
# ----------------------------------------------------------------------
def _nl2br(body: str) -> str:
    """Rich HTML me '\\n' collapse ho jaata hai, isliye <br> (<pre> ke bahar)."""
    parts = re.split(r"(<pre.*?</pre>)", body, flags=re.S | re.I)
    return "".join(
        p if i % 2 else p.replace("\r", "").replace("\n", "<br>")
        for i, p in enumerate(parts)
    )


def _button_html(b: dict) -> str:
    style = f' style="{b["style"]}"' if b.get("style") else ""
    if b.get("url"):
        attrs = f'type="url" url="{_html.escape(b["url"], quote=True)}"'
    else:
        attrs = (
            f'type="callback_data" '
            f'data="{_html.escape(str(b["callback_data"]), quote=True)}"'
        )
    return f"<tg-button {attrs}{style}>{_html.escape(b['text'])}</tg-button>"


def _rows_html(rows: List[List[dict]], align: Optional[str] = None) -> str:
    a = f' align="{align}"' if align else ""
    return "".join(
        f"<tg-button-row{a}>{''.join(_button_html(b) for b in row[:8])}</tg-button-row>"
        for row in rows
        if row
    )


def _clean(b: dict) -> dict:
    out = {"text": b["text"]}
    if b.get("style"):
        out["style"] = b["style"]
    if b.get("url"):
        out["url"] = b["url"]
    elif b.get("callback_data") is not None:
        out["callback_data"] = b["callback_data"]
    return out


# ----------------------------------------------------------------------
# Entry = ek message ka content (text ya media + caption). Edit ke liye yaad rakhte hain.
#   {"media": [{"id","type","src"}], "body": "<html>"}
# ----------------------------------------------------------------------
def _media_head(media: list) -> str:
    out = ""
    for m in media:
        if m["type"] == "photo":
            out += f'<img src="tg://photo?id={m["id"]}">'
        else:
            out += f'<video src="tg://video?id={m["id"]}"></video>'
    return out


def _payload(entry: dict, rows, align=None):
    """(rich_message dict, files dict|None)"""
    rich = {"html": _media_head(entry["media"]) + _nl2br(entry["body"]) + _rows_html(rows, align)}
    files = None
    if entry["media"]:
        rich["media"], files = [], {}
        for i, m in enumerate(entry["media"]):
            src = m["src"]
            if m.get("local"):
                name = f"f{i}"
                with open(src, "rb") as fh:
                    files[name] = (os.path.basename(src), fh.read())
                src = f"attach://{name}"
            rich["media"].append({"id": m["id"], "media": {"type": m["type"], "media": src}})
        files = files or None
    return rich, files


async def _send_entry(chat_id, entry, rows, align, base) -> dict:
    rich, files = _payload(entry, rows, align)
    res = await _call("sendRichMessage", {**base, "chat_id": chat_id, "rich_message": rich}, files)
    LOGGER(__name__).info("pro_post sent via _via_html")
    return res


async def _edit_entry(chat_id, mid, entry, rows):
    rich, files = _payload(entry, rows)
    try:
        return await _call("editMessageText", {
            "chat_id": chat_id, "message_id": mid, "rich_message": rich,
        }, files)
    except RuntimeError as e:
        if "not modified" in str(e).lower():
            return True
        raise


# ----------------------------------------------------------------------
# Direct use (ytsearch, /song group)
# ----------------------------------------------------------------------
async def send_pro_post(
    chat_id,
    body_html: str,
    rows: List[List[dict]],
    reply_to: Optional[int] = None,
    align: Optional[str] = None,
) -> dict:
    """rows = [[{"text","url"|"callback_data","style"}, ...], ...]
    style: success (green) / primary (blue) / danger (red)"""
    base = {}
    if reply_to:
        base["reply_parameters"] = {"message_id": reply_to}
    try:
        return await _send_entry(chat_id, {"media": [], "body": body_html}, rows, align, base)
    except Exception as e:
        LOGGER(__name__).warning(f"pro_post rich rejected, keyboard fallback: {e}")
        kb = {"inline_keyboard": [[_clean(b) for b in row] for row in rows if row]}
        res = await _call("sendMessage", {
            **base, "chat_id": chat_id, "text": body_html, "parse_mode": "HTML",
            "reply_markup": kb, "link_preview_options": {"is_disabled": True},
        })
        LOGGER(__name__).info("pro_post sent via keyboard fallback")
        return res


# ======================================================================
# SHIM: Kurigram client ke methods ke andar
# ======================================================================
def shim_status():
    """(enabled, reason)"""
    if os.getenv("INBUBBLE_BUTTONS", "true").lower() in ("0", "false", "no", "off"):
        return False, "INBUBBLE_BUTTONS=false set hai"
    if os.getenv("INBUBBLE_FORCE", "false").lower() in ("1", "true", "yes", "on"):
        return True, "INBUBBLE_FORCE=true"
    try:
        import pyrogram.types as t
        if hasattr(t, "InputRichMessage"):
            return True, "Kurigram me InputRichMessage mila"
        return False, "Kurigram me InputRichMessage NAHI mila (INBUBBLE_FORCE=true se chalu karo)"
    except Exception as e:
        return False, f"pyrogram import fail: {e}"


def shim_enabled() -> bool:
    return shim_status()[0]


def log_status():
    ok, why = shim_status()
    LOGGER(__name__).info(f"in-bubble buttons: {'ON' if ok else 'OFF'} - {why}")


_REG: "OrderedDict[tuple, dict]" = OrderedDict()  # (chat_id, mid) -> entry


def _remember(chat_id: int, mid: int, entry: dict):
    _REG[(chat_id, mid)] = entry
    while len(_REG) > 5000:
        _REG.popitem(last=False)


def markup_to_rows(markup) -> Optional[List[List[dict]]]:
    kb = getattr(markup, "inline_keyboard", None)
    if not kb:
        return None
    rows = []
    for row in kb:
        out = []
        for b in row:
            d = {"text": b.text}
            st = getattr(b, "style", None)
            if st is not None:
                d["style"] = (getattr(st, "name", None) or str(st)).lower()
            if getattr(b, "url", None):
                d["url"] = b.url
            elif getattr(b, "user_id", None):
                d["url"] = f"tg://user?id={b.user_id}"
            elif getattr(b, "callback_data", None) is not None:
                cd = b.callback_data
                d["callback_data"] = cd.decode() if isinstance(cd, bytes) else cd
            else:
                return None
            out.append(d)
        rows.append(out)
    return rows


def _media_buttons_ok(rows) -> bool:
    """Photo/video message tabhi in-bubble jab edit-safe ho: sirf URL buttons,
    ya callback prefixes allowlist me ho (default: dashboard)."""
    allow = tuple(
        p.strip() for p in os.getenv("INBUBBLE_MEDIA_CALLBACKS", "dash_cb,dash_back").split(",") if p.strip()
    )
    for row in rows:
        for b in row:
            if b.get("callback_data") is not None and not str(b["callback_data"]).startswith(allow):
                return False
    return True


def _text_to_html(client, text: str, parse_mode) -> Optional[str]:
    from pyrogram.enums import ParseMode
    pm = parse_mode if parse_mode is not None else getattr(client, "parse_mode", ParseMode.DEFAULT)
    if pm == ParseMode.DISABLED:
        return _html.escape(text)
    if pm == ParseMode.MARKDOWN:
        return None
    if pm == ParseMode.DEFAULT and re.search(r"\*\*|__|`|\|\|", text):
        return None
    return text


async def _as_message(client, chat_id, mid, body=None):
    try:
        return await client.get_messages(chat_id, mid)
    except Exception:
        try:
            from pyrogram.enums import ChatType
            from pyrogram.types import Chat, Message
            cid = chat_id if isinstance(chat_id, int) else 0
            ctype = ChatType.PRIVATE if cid > 0 else ChatType.SUPERGROUP
            return Message(id=mid, client=client, chat=Chat(id=cid, type=ctype), text=body)
        except Exception:
            return None


def _media_src(x):
    """-> (src, is_local) | None"""
    if isinstance(x, str):
        if x.startswith(("http://", "https://")):
            return x, False
        if os.path.isfile(x):
            return x, True
        if re.fullmatch(r"[A-Za-z0-9_\-]{20,}", x):
            return x, False  # file_id
    return None


_SEND_OK = {
    "parse_mode", "link_preview_options", "disable_web_page_preview",
    "disable_notification", "message_thread_id", "reply_to_message_id",
    "reply_parameters", "protect_content", "reply_markup",
}
_MEDIA_IGNORE = {  # media args jo bubble me farak nahi daalte
    "caption", "supports_streaming", "duration", "width", "height", "thumb",
    "file_name", "show_caption_above_media",
}


def _extra_args_block(kwargs, ok) -> bool:
    for k, v in kwargs.items():
        if k in ok or k in _MEDIA_IGNORE:
            continue
        if v not in (None, False):
            return True
    return False


def _base_params(kwargs) -> dict:
    base = {}
    rp = kwargs.get("reply_parameters")
    reply_to = kwargs.get("reply_to_message_id") or getattr(rp, "message_id", None)
    if reply_to:
        base["reply_parameters"] = {"message_id": reply_to}
    if kwargs.get("message_thread_id"):
        base["message_thread_id"] = kwargs["message_thread_id"]
    if kwargs.get("disable_notification"):
        base["disable_notification"] = True
    if kwargs.get("protect_content"):
        base["protect_content"] = True
    return base


async def _finish_send(client, res, entry, fallback_text):
    mid = res["message_id"]
    _remember(res["chat"]["id"], mid, entry)
    return await _as_message(client, res["chat"]["id"], mid, fallback_text)


async def shim_send(client, chat_id, text, args, kwargs):
    """send_message(text + InlineKeyboard) -> in-bubble. None = purana tareeka."""
    try:
        from pyrogram.types import InlineKeyboardMarkup
        markup = kwargs.get("reply_markup")
        if args or not text or not isinstance(markup, InlineKeyboardMarkup):
            return None
        if _extra_args_block(kwargs, _SEND_OK):
            return None
        rows = markup_to_rows(markup)
        body = _text_to_html(client, text, kwargs.get("parse_mode"))
        if not rows or body is None:
            return None
        entry = {"media": [], "body": body}
        res = await _send_entry(chat_id, entry, rows, None, _base_params(kwargs))
    except Exception as e:
        LOGGER(__name__).warning(f"in-bubble send skipped: {e}")
        return None
    return await _finish_send(client, res, entry, text)


async def shim_send_media(client, kind, chat_id, media, args, kwargs):
    """send_photo / send_video (caption + InlineKeyboard) -> in-bubble."""
    try:
        from pyrogram.types import InlineKeyboardMarkup
        markup = kwargs.get("reply_markup")
        if args or not isinstance(markup, InlineKeyboardMarkup):
            return None
        if kwargs.get("has_spoiler") or kwargs.get("ttl_seconds"):
            return None
        extra = [k for k, v in kwargs.items()
                 if k not in _SEND_OK and k not in _MEDIA_IGNORE
                 and k not in ("has_spoiler", "ttl_seconds") and v not in (None, False)]
        if extra:
            LOGGER(__name__).info(f"in-bubble {kind} skip: extra args {extra}")
            return None
        rows = markup_to_rows(markup)
        src = _media_src(media)
        if not rows:
            LOGGER(__name__).info(f"in-bubble {kind} skip: unsupported button type")
            return None
        if src is None:
            LOGGER(__name__).info(f"in-bubble {kind} skip: media source not url/file/file_id: {type(media).__name__}")
            return None
        if not _media_buttons_ok(rows):
            LOGGER(__name__).info(f"in-bubble {kind} skip: callback buttons not allowlisted (player/edit-safe)")
            return None
        caption = kwargs.get("caption") or ""
        body = _text_to_html(client, caption, kwargs.get("parse_mode")) if caption else ""
        if body is None:
            return None
        entry = {"media": [{"id": "m1", "type": kind, "src": src[0], "local": src[1]}], "body": body}
        res = await _send_entry(chat_id, entry, rows, None, _base_params(kwargs))
    except Exception as e:
        LOGGER(__name__).warning(f"in-bubble {kind} send skipped: {e}")
        return None
    return await _finish_send(client, res, entry, caption)


_EDIT_OK = {
    "parse_mode", "link_preview_options", "disable_web_page_preview",
    "reply_markup", "business_connection_id", "caption_entities", "entities",
}


async def shim_edit_text(client, chat_id, message_id, text, args, kwargs):
    try:
        from pyrogram.types import InlineKeyboardMarkup
        if args or not isinstance(chat_id, int) or not text:
            return None
        if any(v not in (None, False) for k, v in kwargs.items() if k not in _EDIT_OK):
            return None
        if kwargs.get("entities"):
            return None
        old = _REG.get((chat_id, message_id))
        if old is not None and old["media"]:
            return None  # media message ka text edit = caption edit; alag handler
        markup = kwargs.get("reply_markup")
        if isinstance(markup, InlineKeyboardMarkup):
            rows = markup_to_rows(markup)
            if not rows:
                return None
        elif old is not None:
            rows = []
        else:
            return None
        body = _text_to_html(client, text, kwargs.get("parse_mode"))
        if body is None:
            return None
        entry = {"media": [], "body": body}
        await _edit_entry(chat_id, message_id, entry, rows)
    except Exception as e:
        LOGGER(__name__).warning(f"in-bubble edit skipped: {e}")
        return None
    _remember(chat_id, message_id, entry)
    return await _as_message(client, chat_id, message_id, text)


async def shim_edit_caption(client, chat_id, message_id, caption, args, kwargs):
    """Sirf un media messages ke liye jo humne in-bubble bheje (registry me hain)."""
    try:
        from pyrogram.types import InlineKeyboardMarkup
        old = _REG.get((chat_id, message_id)) if isinstance(chat_id, int) else None
        if old is None or not old["media"] or args:
            return None
        if kwargs.get("caption_entities"):
            return None
        markup = kwargs.get("reply_markup")
        rows = markup_to_rows(markup) if isinstance(markup, InlineKeyboardMarkup) else []
        if markup is not None and not rows:
            return None
        body = _text_to_html(client, caption or "", kwargs.get("parse_mode")) if caption else ""
        if body is None:
            return None
        entry = {"media": old["media"], "body": body}
        await _edit_entry(chat_id, message_id, entry, rows)
    except Exception as e:
        LOGGER(__name__).warning(f"in-bubble caption edit skipped: {e}")
        return None
    _remember(chat_id, message_id, entry)
    return await _as_message(client, chat_id, message_id, caption)


async def shim_edit_markup(client, chat_id, message_id, reply_markup, kwargs):
    try:
        key = (chat_id, message_id)
        if key not in _REG or kwargs:
            return None
        rows = markup_to_rows(reply_markup) if reply_markup else []
        if reply_markup and not rows:
            return None
        await _edit_entry(chat_id, message_id, _REG[key], rows)
    except Exception as e:
        LOGGER(__name__).warning(f"in-bubble markup edit skipped: {e}")
        return None
    return await _as_message(client, chat_id, message_id)


def _pp():
    """DAXX ke methods isse shim_* functions lete hain (isi file ke functions)."""
    return sys.modules[__name__]


class DAXX(Client):
    def __init__(self):
        LOGGER(__name__).info(f"Starting Bot...")
        super().__init__(
            name="CRAZYHUBBOT",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            in_memory=True,
            workers=4,  # lowered for low-resource ($5/mo Railway) hosting
            max_concurrent_transmissions=2,  # lowered for low-resource ($5/mo Railway) hosting
        )

    async def start(self):
        # Telegram sometimes rate-limits bot logins (FloodWait), especially
        # right after several quick restarts. If we let this exception
        # propagate, the process exits and Railway restarts the container,
        # which immediately retries the login and gets hit with FloodWait
        # again — a rapid crash-restart loop that only makes the wait time
        # grow. Instead, catch it here and sleep it out inside the SAME
        # process, logging it once, so the container never has to restart.
        while True:
            try:
                await super().start()
                break
            except FloodWait as e:
                wait_time = e.value + 5
                LOGGER(__name__).warning(
                    f"Telegram FloodWait hit while logging in. Waiting "
                    f"{wait_time} seconds before retrying (this is normal "
                    f"after repeated restarts, only needs to happen once)."
                )
                await asyncio.sleep(wait_time)

        _pp().log_status()
        self.id = self.me.id
        self.name = self.me.first_name + " " + (self.me.last_name or "")
        self.username = self.me.username
        self.mention = self.me.mention

        try:
            await self.send_message(
                chat_id=config.LOGGER_ID,
                text=f"<u><b>» {self.mention} ʙᴏᴛ sᴛᴀʀᴛᴇᴅ :</b><u>\n\nɪᴅ : <code>{self.id}</code>\nɴᴀᴍᴇ : {self.name}\nᴜsᴇʀɴᴀᴍᴇ : @{self.username}",
            )
        except (errors.ChannelInvalid, errors.PeerIdInvalid):
            LOGGER(__name__).error(
                "Bot has failed to access the log group/channel. Make sure that you have added your bot to your log group/channel."
            )
            exit()
        except Exception as ex:
            LOGGER(__name__).error(
                f"Bot has failed to access the log group/channel.\n  Reason : {type(ex).__name__}."
            )
            exit()

        a = await self.get_chat_member(config.LOGGER_ID, self.id)
        if a.status != ChatMemberStatus.ADMINISTRATOR:
            LOGGER(__name__).error(
                "Please promote your bot as an admin in your log group/channel."
            )
            exit()
        LOGGER(__name__).info(f"Music Bot Started as {self.name}")

    # ------------------------------------------------------------------
    # In-bubble buttons: text + InlineKeyboard wale saare messages ke buttons
    # ab message ke andar (<tg-button-row>) jaate hain. Kuch bhi reject ho to
    # purana (neeche wala keyboard) tareeka apne aap chalta hai.
    # ------------------------------------------------------------------
    async def send_message(self, chat_id, text, *args, **kwargs):
        pro_post = _pp()
        if pro_post.shim_enabled():
            sent = await pro_post.shim_send(self, chat_id, text, args, kwargs)
            if sent is not None:
                return sent
        return await super().send_message(chat_id, text, *args, **kwargs)

    async def edit_message_text(self, chat_id, message_id, text, *args, **kwargs):
        pro_post = _pp()
        if pro_post.shim_enabled():
            done = await pro_post.shim_edit_text(
                self, chat_id, message_id, text, args, kwargs
            )
            if done is not None:
                return done
        return await super().edit_message_text(
            chat_id, message_id, text, *args, **kwargs
        )

    async def send_photo(self, chat_id, photo, *args, **kwargs):
        pro_post = _pp()
        if pro_post.shim_enabled():
            sent = await pro_post.shim_send_media(
                self, "photo", chat_id, photo, args, kwargs
            )
            if sent is not None:
                return sent
        return await super().send_photo(chat_id, photo, *args, **kwargs)

    async def send_video(self, chat_id, video, *args, **kwargs):
        pro_post = _pp()
        if pro_post.shim_enabled():
            sent = await pro_post.shim_send_media(
                self, "video", chat_id, video, args, kwargs
            )
            if sent is not None:
                return sent
        return await super().send_video(chat_id, video, *args, **kwargs)

    async def edit_message_caption(self, chat_id, message_id, caption, *args, **kwargs):
        pro_post = _pp()
        if pro_post.shim_enabled():
            done = await pro_post.shim_edit_caption(
                self, chat_id, message_id, caption, args, kwargs
            )
            if done is not None:
                return done
        return await super().edit_message_caption(
            chat_id, message_id, caption, *args, **kwargs
        )

    async def edit_message_reply_markup(
        self, chat_id, message_id, reply_markup=None, **kwargs
    ):
        pro_post = _pp()
        if pro_post.shim_enabled():
            done = await pro_post.shim_edit_markup(
                self, chat_id, message_id, reply_markup, kwargs
            )
            if done is not None:
                return done
        return await super().edit_message_reply_markup(
            chat_id, message_id, reply_markup, **kwargs
        )

    async def stop(self):
        await super().stop()
