from pyrogram.types import KeyboardButtonStyle
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def stats_buttons(_, status):
    not_sudo = [
        InlineKeyboardButton(
            text=_["SA_B_1"],
            callback_data="TopOverall", style=KeyboardButtonStyle(bg_primary=True)
        )
    ]
    sudo = [
        InlineKeyboardButton(
            text=_["SA_B_2"],
            callback_data="bot_stats_sudo", style=KeyboardButtonStyle(bg_primary=True)
        ),
        InlineKeyboardButton(
            text=_["SA_B_3"],
            callback_data="TopOverall", style=KeyboardButtonStyle(bg_primary=True)
        ),
    ]
    upl = InlineKeyboardMarkup(
        [
            sudo if status else not_sudo,
            [
                InlineKeyboardButton(
                    text=_["CLOSE_BUTTON"],
                    callback_data="close", style=KeyboardButtonStyle(bg_danger=True)
                ),
            ],
        ]
    )
    return upl


def back_stats_buttons(_):
    upl = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=_["BACK_BUTTON"],
                    callback_data="stats_back", style=KeyboardButtonStyle(bg_primary=True)
                ),
                InlineKeyboardButton(
                    text=_["CLOSE_BUTTON"],
                    callback_data="close", style=KeyboardButtonStyle(bg_danger=True)
                ),
            ],
        ]
    )
    return upl
