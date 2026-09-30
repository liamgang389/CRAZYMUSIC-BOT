from pyrogram.enums import ButtonStyle

from pyrogram.types import InlineKeyboardButton


def song_markup(_, vidid):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["SG_B_2"],
                callback_data=f"song_helper audio|{vidid}", style=ButtonStyle.PRIMARY
            ),
            InlineKeyboardButton(
                text=_["SG_B_3"],
                callback_data=f"song_helper video|{vidid}", style=ButtonStyle.PRIMARY
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"], callback_data="close"
            , style=ButtonStyle.DANGER),
        ],
    ]
    return buttons
