from pyrogram.types import KeyboardButtonStyle
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import SUPPORT_CHAT


def botplaylist_markup(_):
    buttons = [
        [
            InlineKeyboardButton(text=_["S_B_9"], url=SUPPORT_CHAT, style=KeyboardButtonStyle(bg_primary=True)),
            InlineKeyboardButton(text=_["CLOSE_BUTTON"], callback_data="close", style=KeyboardButtonStyle(bg_danger=True)),
        ],
    ]
    return buttons


def close_markup(_):
    upl = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=_["CLOSE_BUTTON"],
                    callback_data="close", style=KeyboardButtonStyle(bg_danger=True)
                ),
            ]
        ]
    )
    return upl


def supp_markup(_):
    upl = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=_["S_B_9"],
                    url=SUPPORT_CHAT, style=KeyboardButtonStyle(bg_primary=True)
                ),
            ]
        ]
    )
    return upl
