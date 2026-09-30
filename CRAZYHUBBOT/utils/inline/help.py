from pyrogram.types import KeyboardButtonStyle
from typing import Union

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from CRAZYHUBBOT import app


def help_pannel(_, START: Union[bool, int] = None):
    first = [InlineKeyboardButton(text=_["CLOSE_BUTTON"], callback_data=f"close", style=KeyboardButtonStyle(bg_danger=True))]
    second = [
        InlineKeyboardButton(
            text=_["BACK_PAGE"],
            callback_data=f"mbot_cb", style=KeyboardButtonStyle(bg_primary=True)
        ),
        InlineKeyboardButton(
            text=_["BACK_BUTTON"],
            callback_data=f"settingsback_helper", style=KeyboardButtonStyle(bg_primary=True)
        ),
        InlineKeyboardButton(
            text=_["NEXT_PAGE"],
            callback_data=f"mbot_cb", style=KeyboardButtonStyle(bg_primary=True)
        ),
    ]
    mark = second if START else first
    upl = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=_["H_B_1"],
                    callback_data="help_callback hb1", style=KeyboardButtonStyle(bg_primary=True)
                ),
                InlineKeyboardButton(
                    text=_["H_B_2"],
                    callback_data="help_callback hb2", style=KeyboardButtonStyle(bg_primary=True)
                ),
                InlineKeyboardButton(
                    text=_["H_B_3"],
                    callback_data="help_callback hb3", style=KeyboardButtonStyle(bg_primary=True)
                ),
            ],
            [
                InlineKeyboardButton(
                    text=_["H_B_4"],
                    callback_data="help_callback hb4", style=KeyboardButtonStyle(bg_primary=True)
                ),
                InlineKeyboardButton(
                    text=_["H_B_5"],
                    callback_data="help_callback hb5", style=KeyboardButtonStyle(bg_primary=True)
                ),
                InlineKeyboardButton(
                    text=_["H_B_6"],
                    callback_data="help_callback hb6", style=KeyboardButtonStyle(bg_primary=True)
                ),
            ],
            [
                InlineKeyboardButton(
                    text=_["H_B_7"],
                    callback_data="help_callback hb7", style=KeyboardButtonStyle(bg_primary=True)
                ),
                InlineKeyboardButton(
                    text=_["H_B_8"],
                    callback_data="help_callback hb8", style=KeyboardButtonStyle(bg_primary=True)
                ),
                InlineKeyboardButton(
                    text=_["H_B_9"],
                    callback_data="help_callback hb9", style=KeyboardButtonStyle(bg_primary=True)
                ),
            ],
            [
                InlineKeyboardButton(
                    text=_["H_B_10"],
                    callback_data="help_callback hb10", style=KeyboardButtonStyle(bg_primary=True)
                ),
                InlineKeyboardButton(
                    text=_["H_B_11"],
                    callback_data="help_callback hb11", style=KeyboardButtonStyle(bg_primary=True)
                ),
                InlineKeyboardButton(
                    text=_["H_B_12"],
                    callback_data="help_callback hb12", style=KeyboardButtonStyle(bg_primary=True)
                ),
            ],
            [
                InlineKeyboardButton(
                    text=_["H_B_13"],
                    callback_data="help_callback hb13", style=KeyboardButtonStyle(bg_primary=True)
                ),
                InlineKeyboardButton(
                    text=_["H_B_14"],
                    callback_data="help_callback hb14", style=KeyboardButtonStyle(bg_primary=True)
                ),
                InlineKeyboardButton(
                    text=_["H_B_15"],
                    callback_data="help_callback hb15", style=KeyboardButtonStyle(bg_primary=True)
                ),
            ],
            mark,
        ]
    )
    return upl


def help_back_markup(_):
    upl = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=_["BACK_BUTTON"],
                    callback_data=f"settings_back_helper", style=KeyboardButtonStyle(bg_primary=True)
                ),
            ]
        ]
    )
    return upl


def private_help_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_4"],
                url=f"https://t.me/{app.username}?start=help", style=KeyboardButtonStyle(bg_success=True)
            ),
        ],
    ]
    return buttons
