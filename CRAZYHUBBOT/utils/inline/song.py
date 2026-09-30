from pyrogram.types import KeyboardButtonStyle

from pyrogram.types import InlineKeyboardButton


def song_markup(_, vidid):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["SG_B_2"],
                callback_data=f"song_helper audio|{vidid}", style=KeyboardButtonStyle(bg_primary=True)
            ),
            InlineKeyboardButton(
                text=_["SG_B_3"],
                callback_data=f"song_helper video|{vidid}", style=KeyboardButtonStyle(bg_primary=True)
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"], callback_data="close"
            , style=KeyboardButtonStyle(bg_danger=True)),
        ],
    ]
    return buttons
