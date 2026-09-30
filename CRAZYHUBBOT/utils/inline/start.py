from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardButton

import config
from CRAZYHUBBOT import app


def start_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_1"], url=f"https://t.me/{app.username}?startgroup=true"
            , style=ButtonStyle.PRIMARY),
            InlineKeyboardButton(text=_["S_B_2"], url=config.SUPPORT_CHAT, style=ButtonStyle.PRIMARY),
        ],
    ]
    return buttons


def private_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["DASH_B_1"],
                url=f"https://t.me/{app.username}?startgroup=true", style=ButtonStyle.PRIMARY
            )
        ],
        [
            InlineKeyboardButton(text=_["DASH_B_2"], callback_data="dash_cb group", style=ButtonStyle.PRIMARY),
            InlineKeyboardButton(text=_["DASH_B_3"], callback_data="dash_cb ai", style=ButtonStyle.PRIMARY),
        ],
        [
            InlineKeyboardButton(
                text=_["DASH_B_4"],
                url=f"https://t.me/{app.username}?start=help", style=ButtonStyle.SUCCESS
            ),
            InlineKeyboardButton(text=_["DASH_B_5"], callback_data="dash_cb about", style=ButtonStyle.PRIMARY),
        ],
        [
            InlineKeyboardButton(text=_["DASH_B_6"], url=config.SUPPORT_CHAT, style=ButtonStyle.PRIMARY),
        ],
    ]
    return buttons
