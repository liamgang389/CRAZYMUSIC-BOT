from pyrogram.types import KeyboardButtonStyle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram import Client, filters, enums 

class BUTTONS(object):
    MBUTTON = [[InlineKeyboardButton("CʜᴀᴛGPT", callback_data="mplus HELP_ChatGPT", style=KeyboardButtonStyle(bg_primary=True)),InlineKeyboardButton("ɢʀᴏᴜᴘs", callback_data="mplus HELP_Group", style=KeyboardButtonStyle(bg_primary=True)),InlineKeyboardButton("sᴛɪᴄᴋᴇʀs", callback_data="mplus HELP_Sticker", style=KeyboardButtonStyle(bg_primary=True))],
    [InlineKeyboardButton("Tᴀɢ-Aʟʟ", callback_data="mplus HELP_TagAll", style=KeyboardButtonStyle(bg_primary=True)),
    InlineKeyboardButton("Iɴꜰᴏ", callback_data="mplus HELP_Info", style=KeyboardButtonStyle(bg_primary=True)),InlineKeyboardButton("Exᴛʀᴀ", callback_data="mplus HELP_Extra", style=KeyboardButtonStyle(bg_primary=True))],
    [InlineKeyboardButton("Iᴍᴀɢᴇ", callback_data="mplus HELP_Image", style=KeyboardButtonStyle(bg_primary=True)),
    InlineKeyboardButton("Aᴄᴛɪᴏɴ", callback_data="mplus HELP_Action", style=KeyboardButtonStyle(bg_primary=True)),InlineKeyboardButton("Sᴇᴀʀᴄʜ", callback_data="mplus HELP_Search", style=KeyboardButtonStyle(bg_primary=True))],    
    [InlineKeyboardButton("ғᴏɴᴛ", callback_data="mplus HELP_Font", style=KeyboardButtonStyle(bg_primary=True)),
    InlineKeyboardButton("ɢᴀᴍᴇs", callback_data="mplus HELP_Game", style=KeyboardButtonStyle(bg_primary=True)),InlineKeyboardButton("Ⓣ-ɢʀᴀᴘʜ", callback_data="mplus HELP_TG", style=KeyboardButtonStyle(bg_primary=True))],
    [InlineKeyboardButton("ɪᴍᴘᴏsᴛᴇʀ", callback_data="mplus HELP_Imposter", style=KeyboardButtonStyle(bg_primary=True)),
    InlineKeyboardButton("Tʀᴜᴛʜ-ᗪᴀʀᴇ", callback_data="mplus HELP_TD", style=KeyboardButtonStyle(bg_primary=True)),InlineKeyboardButton("ʜᴀsᴛᴀɢ", callback_data="mplus HELP_HT", style=KeyboardButtonStyle(bg_primary=True))], 
    [InlineKeyboardButton("ᴛᴛs", callback_data="mplus HELP_TTS", style=KeyboardButtonStyle(bg_primary=True)),
    InlineKeyboardButton("ғᴜɴ", callback_data="mplus HELP_Fun", style=KeyboardButtonStyle(bg_primary=True)),InlineKeyboardButton("ǫᴜᴏᴛʟʏ", callback_data="mplus HELP_Q", style=KeyboardButtonStyle(bg_primary=True))],          
    [InlineKeyboardButton("<", callback_data=f"settings_back_helper", style=KeyboardButtonStyle(bg_primary=True)), 
    InlineKeyboardButton(">", callback_data=f"managebot123 settings_back_helper", style=KeyboardButtonStyle(bg_primary=True)),
    ]]