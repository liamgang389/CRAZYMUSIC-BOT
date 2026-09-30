from pyrogram.types import KeyboardButtonStyle
from typing import Union
from CRAZYHUBBOT import app
from CRAZYHUBBOT.utils.formatters import time_to_seconds
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def queue_markup(
    _,
    DURATION,
    CPLAY,
    videoid,
    played: Union[bool, int] = None,
    dur: Union[bool, int] = None,
):
    not_dur = [
        [
            InlineKeyboardButton(
                text=_["QU_B_1"],
                callback_data=f"GetQueued {CPLAY}|{videoid}", style=KeyboardButtonStyle(bg_primary=True)
            ),
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data="close", style=KeyboardButtonStyle(bg_danger=True)
            ),
        ]
    ]
    dur = [
        [
            InlineKeyboardButton(
                text=_["QU_B_2"].format(played, dur),
                callback_data="GetTimer", style=KeyboardButtonStyle(bg_primary=True)
            )
        ],
        [
            InlineKeyboardButton(
                text=_["QU_B_1"],
                callback_data=f"GetQueued {CPLAY}|{videoid}", style=KeyboardButtonStyle(bg_primary=True)
            ),
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data="close", style=KeyboardButtonStyle(bg_danger=True)
            ),
        ],
    ]
    upl = InlineKeyboardMarkup(not_dur if DURATION == "Unknown" else dur)
    return upl


def queue_back_markup(_, CPLAY):
    upl = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=_["BACK_BUTTON"],
                    callback_data=f"queue_back_timer {CPLAY}", style=KeyboardButtonStyle(bg_primary=True)
                ),
                InlineKeyboardButton(
                    text=_["CLOSE_BUTTON"],
                    callback_data="close", style=KeyboardButtonStyle(bg_danger=True)
                ),
            ]
        ]
    )
    return upl


def aq_markup(_, chat_id):
    buttons = [
        [
            InlineKeyboardButton(text="▷", callback_data=f"ADMIN Resume|{chat_id}", style=KeyboardButtonStyle(bg_success=True)),
            InlineKeyboardButton(text="II", callback_data=f"ADMIN Pause|{chat_id}", style=KeyboardButtonStyle(bg_primary=True)),
            InlineKeyboardButton(text="‣‣I", callback_data=f"ADMIN Skip|{chat_id}", style=KeyboardButtonStyle(bg_primary=True)),
            InlineKeyboardButton(text="▢", callback_data=f"ADMIN Stop|{chat_id}", style=KeyboardButtonStyle(bg_danger=True)),
        ],
        [InlineKeyboardButton(text=_["CLOSE_BUTTON"], callback_data="close", style=KeyboardButtonStyle(bg_danger=True))],
    ]
    return buttons
