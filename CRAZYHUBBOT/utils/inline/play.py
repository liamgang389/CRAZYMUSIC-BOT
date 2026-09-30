from pyrogram.types import KeyboardButtonStyle
import math
from config import SUPPORT_CHAT, OWNER_USERNAME
from pyrogram.types import InlineKeyboardButton
from CRAZYHUBBOT import app
import config
from CRAZYHUBBOT.utils.formatters import time_to_seconds


def track_markup(_, videoid, user_id, channel, fplay):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}", style=KeyboardButtonStyle(bg_success=True)
            ),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}", style=KeyboardButtonStyle(bg_success=True)
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}", style=KeyboardButtonStyle(bg_primary=True)
            )
        ],
    ]
    return buttons


def stream_markup_timer(_, chat_id, played, dur):
    played_sec = time_to_seconds(played)
    duration_sec = time_to_seconds(dur)
    percentage = (played_sec / duration_sec) * 100
    umm = math.floor(percentage)
    if 0 < umm <= 10:
        bar = "◉—————————"
    elif 10 < umm < 20:
        bar = "—◉————————"
    elif 20 <= umm < 30:
        bar = "——◉———————"
    elif 30 <= umm < 40:
        bar = "———◉——————"
    elif 40 <= umm < 50:
        bar = "————◉—————"
    elif 50 <= umm < 60:
        bar = "—————◉————"
    elif 60 <= umm < 70:
        bar = "——————◉———"
    elif 70 <= umm < 80:
        bar = "———————◉——"
    elif 80 <= umm < 95:
        bar = "————————◉—"
    else:
        bar = "—————————◉"
    buttons = [
                [
            InlineKeyboardButton(
                text=f"{played} {bar} {dur}",
                callback_data="GetTimer", style=KeyboardButtonStyle(bg_primary=True)
            )
        ],
        [
            InlineKeyboardButton(text="▷", callback_data=f"ADMIN Resume|{chat_id}", style=KeyboardButtonStyle(bg_success=True)),
            InlineKeyboardButton(text="II", callback_data=f"ADMIN Pause|{chat_id}", style=KeyboardButtonStyle(bg_primary=True)),
            InlineKeyboardButton(text="‣‣I", callback_data=f"ADMIN Skip|{chat_id}", style=KeyboardButtonStyle(bg_primary=True)),
            InlineKeyboardButton(text="▢", callback_data=f"ADMIN Stop|{chat_id}", style=KeyboardButtonStyle(bg_danger=True)),
        ],
        [
            InlineKeyboardButton(text="🔁 Autoplay", callback_data=f"ADMIN Autoplay|{chat_id}", style=KeyboardButtonStyle(bg_primary=True)),
        ],
        [
         InlineKeyboardButton(text="Oᴡɴᴇʀ 💕", user_id=config.OWNER_ID, style=KeyboardButtonStyle(bg_primary=True)),
         InlineKeyboardButton(text="💌 ɢʀᴏᴜᴘ", url=f"{SUPPORT_CHAT}", style=KeyboardButtonStyle(bg_primary=True)),
        ],
        [InlineKeyboardButton(text=_["CLOSE_BUTTON"], callback_data="close", style=KeyboardButtonStyle(bg_danger=True))],
    ]
    return buttons


def stream_markup(_, chat_id):
    buttons = [
        [
            InlineKeyboardButton(text="▷", callback_data=f"ADMIN Resume|{chat_id}", style=KeyboardButtonStyle(bg_success=True)),
            InlineKeyboardButton(text="II", callback_data=f"ADMIN Pause|{chat_id}", style=KeyboardButtonStyle(bg_primary=True)),
            InlineKeyboardButton(text="‣‣I", callback_data=f"ADMIN Skip|{chat_id}", style=KeyboardButtonStyle(bg_primary=True)),
            InlineKeyboardButton(text="▢", callback_data=f"ADMIN Stop|{chat_id}", style=KeyboardButtonStyle(bg_danger=True)),
        ],
        [
            InlineKeyboardButton(text="🔁 Autoplay", callback_data=f"ADMIN Autoplay|{chat_id}", style=KeyboardButtonStyle(bg_primary=True)),
        ],
        [
         InlineKeyboardButton(text="Oᴡɴᴇʀ 💕", user_id=config.OWNER_ID, style=KeyboardButtonStyle(bg_primary=True)),
         InlineKeyboardButton(text="💌 ɢʀᴏᴜᴘ", url=f"{SUPPORT_CHAT}", style=KeyboardButtonStyle(bg_primary=True)),
        ],
        [InlineKeyboardButton(text=_["CLOSE_BUTTON"], callback_data="close", style=KeyboardButtonStyle(bg_danger=True))],
    ]
    return buttons


def playlist_markup(_, videoid, user_id, ptype, channel, fplay):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=f"DAXXPlaylists {videoid}|{user_id}|{ptype}|a|{channel}|{fplay}", style=KeyboardButtonStyle(bg_primary=True)
            ),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=f"DAXXPlaylists {videoid}|{user_id}|{ptype}|v|{channel}|{fplay}", style=KeyboardButtonStyle(bg_primary=True)
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}", style=KeyboardButtonStyle(bg_primary=True)
            ),
        ],
    ]
    return buttons


def livestream_markup(_, videoid, user_id, mode, channel, fplay):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["P_B_3"],
                callback_data=f"LiveStream {videoid}|{user_id}|{mode}|{channel}|{fplay}", style=KeyboardButtonStyle(bg_primary=True)
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}", style=KeyboardButtonStyle(bg_primary=True)
            ),
        ],
    ]
    return buttons


def slider_markup(_, videoid, user_id, query, query_type, channel, fplay):
    query = f"{query[:20]}"
    buttons = [
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}", style=KeyboardButtonStyle(bg_success=True)
            ),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}", style=KeyboardButtonStyle(bg_success=True)
            ),
        ],
        [
            InlineKeyboardButton(
                text="◁",
                callback_data=f"slider B|{query_type}|{query}|{user_id}|{channel}|{fplay}", style=KeyboardButtonStyle(bg_primary=True)
            ),
            InlineKeyboardButton(
                text="▷",
                callback_data=f"slider F|{query_type}|{query}|{user_id}|{channel}|{fplay}", style=KeyboardButtonStyle(bg_primary=True)
            ),
        ],
    ]
    return buttons
