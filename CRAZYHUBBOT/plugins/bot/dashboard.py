from pyrogram.types import KeyboardButtonStyle
from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

import config
from CRAZYHUBBOT import app
from CRAZYHUBBOT.utils.database import get_lang
from CRAZYHUBBOT.utils.inline.start import private_panel
from config import BANNED_USERS
from strings import get_string

DASH_TEXT_KEYS = {
    "group": "DASH_GROUP_TEXT",
    "ai": "DASH_AI_TEXT",
    "about": "DASH_ABOUT_TEXT",
}


def _dash_back_markup(_):
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(text=_["DASH_BACK"], callback_data="dash_back", style=KeyboardButtonStyle(bg_primary=True))]]
    )


@app.on_callback_query(filters.regex("^dash_cb") & ~BANNED_USERS)
async def dashboard_section_cb(client, callback_query: CallbackQuery):
    try:
        await callback_query.answer()
    except Exception:
        pass

    section = callback_query.data.split(None, 1)[1]
    chat_id = callback_query.message.chat.id
    language = await get_lang(chat_id)
    _ = get_string(language)

    text_key = DASH_TEXT_KEYS.get(section)
    if not text_key:
        return

    text = _[text_key]
    if section == "about":
        text = text.format(app.mention)

    await callback_query.edit_message_caption(
        caption=text, parse_mode=ParseMode.HTML, reply_markup=_dash_back_markup(_)
    )


@app.on_callback_query(filters.regex("^dash_back$") & ~BANNED_USERS)
async def dashboard_back_cb(client, callback_query: CallbackQuery):
    try:
        await callback_query.answer()
    except Exception:
        pass

    chat_id = callback_query.message.chat.id
    language = await get_lang(chat_id)
    _ = get_string(language)

    caption = _["start_2"].format(
        callback_query.from_user.mention, app.mention
    )
    await callback_query.edit_message_caption(
        caption=caption, reply_markup=InlineKeyboardMarkup(private_panel(_))
    )
