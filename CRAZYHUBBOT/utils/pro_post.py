"""
CRAZYHUBBOT/utils/pro_post.py

Buttons ko message ke BUBBLE ke ANDAR bhejta hai (Telegram <tg-button-row>).

Teen tareeke, ek ke baad ek:
  1. sendRichMessage + HTML  (<tg-button-row> / <tg-button>)   <- default
  2. sendRichMessage + JSON blocks (InputRichBlockButtons)
  3. sendMessage + neeche wala InlineKeyboard (sirf jab upar ke dono reject hon)

Do tarah se use hota hai:
  * send_pro_post(...)            -> seedha (ytsearch, /song group)
  * shim_send / shim_edit_*       -> core/bot.py me DAXX client ke
                                     send_message / edit_message_text /
                                     edit_message_reply_markup ke andar.
                                     Isse bot ke saare text+button messages
                                     automatically in-bubble ho jaate hain.

Env:  INBUBBLE_BUTTONS=false  -> shim band (purana behaviour)
      INBUBBLE_FORCE=true     -> kurigram detection skip karke shim chalu
"""
import html as _html
import os
import re
from collections import OrderedDict
from typing import List, Optional

import httpx

import config
from CRAZYHUBBOT.logging import LOGGER

API = "https://api.telegram.org/bot{token}/{method}"
_client: Optional[httpx.AsyncClient] = None


def _http() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=30)
    return _client


async def _call(method: str, payload: dict) -> dict:
    r = await _http().post(
        API.format(token=config.BOT_TOKEN, method=method), json=payload
    )
    data = r.json()
    if not data.get("ok"):
        raise RuntimeError(f"{method}: {data.get('description')}")
    return data["result"]


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def _nl2br(body: str) -> str:
    """Rich HTML me '\\n' collapse ho jaata hai, isliye <br> chahiye (<pre> ke bahar)."""
    parts = re.split(r"(<pre.*?</pre>)", body, flags=re.S | re.I)
    return "".join(
        p if i % 2 else p.replace("\r", "").replace("\n", "<br>")
        for i, p in enumerate(parts)
    )


def _clean(b: dict) -> dict:
    """JSON button (RichMessageButton / InlineKeyboardButton) ke liye."""
    out = {"text": b["text"]}
    if b.get("style"):
        out["style"] = b["style"]
    if b.get("url"):
        out["url"] = b["url"]
    elif b.get("callback_data") is not None:
        out["callback_data"] = b["callback_data"]
    return out


# ----------------------------------------------------------------------
# 1. HTML + <tg-button-row>
# ----------------------------------------------------------------------
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


def _rows_html(rows: List[List[dict]], align: Optional[str]) -> str:
    a = f' align="{align}"' if align else ""
    return "".join(
        f"<tg-button-row{a}>{''.join(_button_html(b) for b in row[:8])}</tg-button-row>"
        for row in rows
        if row
    )


async def _via_html(body, rows, align):
    return {"html": f"{_nl2br(body)}{_rows_html(rows, align)}"}


# ----------------------------------------------------------------------
# 2. JSON blocks (InputRichBlockButtons)
# ----------------------------------------------------------------------
async def _via_blocks(body, rows, align):
    blocks = []
    for row in rows:
        if not row:
            continue
        blk = {"type": "buttons", "buttons": [_clean(b) for b in row[:8]]}
        if align:
            blk["align"] = align
        blocks.append(blk)
    # NOTE: InputRichMessage me abhi sirf html/markdown documented hai; ye shape
    # andaza hai. Reject hua to agla tareeka / purana keyboard chalega.
    return {"html": _nl2br(body), "blocks": blocks}


_RICH_BUILDERS = (_via_html, _via_blocks)


# ----------------------------------------------------------------------
# Send / edit (Bot API)
# ----------------------------------------------------------------------
async def _send_rich(chat_id, body, rows, align, base) -> dict:
    last = None
    for build in _RICH_BUILDERS:
        try:
            rich = await build(body, rows, align)
            res = await _call("sendRichMessage", {**base, "chat_id": chat_id, "rich_message": rich})
            LOGGER(__name__).info(f"pro_post sent via {build.__name__}")
            return res
        except Exception as e:
            LOGGER(__name__).warning(f"pro_post {build.__name__} rejected: {e}")
            last = e
    raise RuntimeError(str(last))


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
        return await _send_rich(chat_id, body_html, rows, align, base)
    except Exception:
        # 3. neeche wala keyboard
        kb = {"inline_keyboard": [[_clean(b) for b in row] for row in rows if row]}
        res = await _call("sendMessage", {
            **base, "chat_id": chat_id, "text": body_html, "parse_mode": "HTML",
            "reply_markup": kb, "link_preview_options": {"is_disabled": True},
        })
        LOGGER(__name__).info("pro_post sent via keyboard fallback")
        return res


# ======================================================================
# SHIM: Kurigram client ke methods ke andar (saare buttons ke liye)
# ======================================================================
def shim_enabled() -> bool:
    if os.getenv("INBUBBLE_BUTTONS", "true").lower() in ("0", "false", "no", "off"):
        return False
    if os.getenv("INBUBBLE_FORCE", "false").lower() in ("1", "true", "yes", "on"):
        return True
    try:  # Rich message support wala Kurigram chahiye (Bot API 10.3)
        import pyrogram.types as t
        return hasattr(t, "InputRichMessage")
    except Exception:
        return False


# (chat_id, message_id) -> body html. Edit ke time body wapas chahiye hota hai.
_REG: "OrderedDict[tuple, str]" = OrderedDict()


def _remember(chat_id: int, mid: int, body: str):
    _REG[(chat_id, mid)] = body
    while len(_REG) > 5000:
        _REG.popitem(last=False)


def markup_to_rows(markup) -> Optional[List[List[dict]]]:
    """Kurigram InlineKeyboardMarkup -> rows. Unsupported button ho to None."""
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
                return None  # web_app / switch_inline / login etc. -> purana tareeka
            out.append(d)
        rows.append(out)
    return rows


def _text_to_html(client, text: str, parse_mode) -> Optional[str]:
    from pyrogram.enums import ParseMode
    pm = parse_mode if parse_mode is not None else getattr(client, "parse_mode", ParseMode.DEFAULT)
    if pm == ParseMode.DISABLED:
        return _html.escape(text)
    if pm == ParseMode.MARKDOWN:
        return None
    if pm == ParseMode.DEFAULT and re.search(r"\*\*|__|`|\|\|", text):
        return None  # markdown mila-jula hai, safe nahi
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


_SEND_OK = {
    "parse_mode", "link_preview_options", "disable_web_page_preview",
    "disable_notification", "message_thread_id", "reply_to_message_id",
    "reply_parameters", "protect_content", "reply_markup",
}


async def shim_send(client, chat_id, text, args, kwargs):
    """Kurigram send_message(text + InlineKeyboardMarkup) -> in-bubble.
    None return = ye message convert nahi ho sakta, purana tareeka chalao."""
    try:
        from pyrogram.types import InlineKeyboardMarkup
        markup = kwargs.get("reply_markup")
        if args or not text or not isinstance(markup, InlineKeyboardMarkup):
            return None
        if any(v not in (None, False) for k, v in kwargs.items() if k not in _SEND_OK):
            return None
        rows = markup_to_rows(markup)
        body = _text_to_html(client, text, kwargs.get("parse_mode"))
        if not rows or body is None:
            return None

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

        res = await _send_rich(chat_id, body, rows, None, base)
    except Exception as e:
        LOGGER(__name__).warning(f"in-bubble send skipped: {e}")
        return None

    mid = res["message_id"]
    _remember(res["chat"]["id"], mid, body)
    return await _as_message(client, res["chat"]["id"], mid, text)


_EDIT_OK = {
    "parse_mode", "link_preview_options", "disable_web_page_preview",
    "reply_markup", "business_connection_id",
}


async def _rich_edit(chat_id, mid, body, rows):
    last = None
    for build in _RICH_BUILDERS:
        try:
            rich = await build(body, rows, None)
            return await _call("editMessageText", {
                "chat_id": chat_id, "message_id": mid, "rich_message": rich,
            })
        except Exception as e:
            if "not modified" in str(e).lower():
                return True
            last = e
    raise RuntimeError(str(last))


async def shim_edit_text(client, chat_id, message_id, text, args, kwargs):
    try:
        from pyrogram.types import InlineKeyboardMarkup
        if args or not isinstance(chat_id, int) or not text:
            return None
        if any(v not in (None, False) for k, v in kwargs.items() if k not in _EDIT_OK):
            return None
        markup = kwargs.get("reply_markup")
        known = (chat_id, message_id) in _REG
        if isinstance(markup, InlineKeyboardMarkup):
            rows = markup_to_rows(markup)
            if not rows:
                return None
        elif known:
            rows = []
        else:
            return None
        body = _text_to_html(client, text, kwargs.get("parse_mode"))
        if body is None:
            return None
        await _rich_edit(chat_id, message_id, body, rows)
    except Exception as e:
        LOGGER(__name__).warning(f"in-bubble edit skipped: {e}")
        return None
    _remember(chat_id, message_id, body)
    return await _as_message(client, chat_id, message_id, text)


async def shim_edit_markup(client, chat_id, message_id, reply_markup, kwargs):
    try:
        key = (chat_id, message_id)
        if key not in _REG or kwargs:
            return None
        rows = markup_to_rows(reply_markup) if reply_markup else []
        if reply_markup and not rows:
            return None
        await _rich_edit(chat_id, message_id, _REG[key], rows)
    except Exception as e:
        LOGGER(__name__).warning(f"in-bubble markup edit skipped: {e}")
        return None
    return await _as_message(client, chat_id, message_id)
