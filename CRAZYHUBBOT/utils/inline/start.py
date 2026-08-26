from pyrogram.types import InlineKeyboardButton

import config
from CRAZYHUBBOT import app


def start_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_1"], url=f"https://t.me/{app.username}?startgroup=true"
            ),
            InlineKeyboardButton(text=_["S_B_2"], url=config.SUPPORT_CHAT),
        ],
    ]
    return buttons


def private_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["DASH_B_1"],
                callback_data="dash_cb music",
            )
        ],
        [
            InlineKeyboardButton(text=_["DASH_B_2"], callback_data="dash_cb group"),
            InlineKeyboardButton(text=_["DASH_B_3"], callback_data="dash_cb ai"),
        ],
        [
            InlineKeyboardButton(
                text=_["DASH_B_4"],
                url=f"https://t.me/{app.username}?start=help",
            ),
            InlineKeyboardButton(text=_["DASH_B_5"], callback_data="dash_cb about"),
        ],
        [
            InlineKeyboardButton(text=_["DASH_B_6"], url=config.SUPPORT_CHAT),
        ],
    ]
    return buttons
