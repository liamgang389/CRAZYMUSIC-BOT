from pyrogram.types import InlineKeyboardButton

import config
from CRAZYHUBBOT import app


def start_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_1"], url=f"https://t.me/{app.username}?startgroup=true"
            , style="primary"),
            InlineKeyboardButton(text=_["S_B_2"], url=config.SUPPORT_CHAT, style="primary"),
        ],
    ]
    return buttons


def private_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["DASH_B_1"],
                url=f"https://t.me/{app.username}?startgroup=true", style="primary"
            )
        ],
        [
            InlineKeyboardButton(text=_["DASH_B_2"], callback_data="dash_cb group", style="primary"),
            InlineKeyboardButton(text=_["DASH_B_3"], callback_data="dash_cb ai", style="primary"),
        ],
        [
            InlineKeyboardButton(
                text=_["DASH_B_4"],
                url=f"https://t.me/{app.username}?start=help", style="success"
            ),
            InlineKeyboardButton(text=_["DASH_B_5"], callback_data="dash_cb about", style="primary"),
        ],
        [
            InlineKeyboardButton(text=_["DASH_B_6"], url=config.SUPPORT_CHAT, style="primary"),
        ],
    ]
    return buttons
