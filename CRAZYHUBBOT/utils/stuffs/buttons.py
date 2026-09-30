from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram import Client, filters, enums 

class BUTTONS(object):
    MBUTTON = [[InlineKeyboardButton("CʜᴀᴛGPT", callback_data="mplus HELP_ChatGPT", style="primary"),InlineKeyboardButton("ɢʀᴏᴜᴘs", callback_data="mplus HELP_Group", style="primary"),InlineKeyboardButton("sᴛɪᴄᴋᴇʀs", callback_data="mplus HELP_Sticker", style="primary")],
    [InlineKeyboardButton("Tᴀɢ-Aʟʟ", callback_data="mplus HELP_TagAll", style="primary"),
    InlineKeyboardButton("Iɴꜰᴏ", callback_data="mplus HELP_Info", style="primary"),InlineKeyboardButton("Exᴛʀᴀ", callback_data="mplus HELP_Extra", style="primary")],
    [InlineKeyboardButton("Iᴍᴀɢᴇ", callback_data="mplus HELP_Image", style="primary"),
    InlineKeyboardButton("Aᴄᴛɪᴏɴ", callback_data="mplus HELP_Action", style="primary"),InlineKeyboardButton("Sᴇᴀʀᴄʜ", callback_data="mplus HELP_Search", style="primary")],    
    [InlineKeyboardButton("ғᴏɴᴛ", callback_data="mplus HELP_Font", style="primary"),
    InlineKeyboardButton("ɢᴀᴍᴇs", callback_data="mplus HELP_Game", style="primary"),InlineKeyboardButton("Ⓣ-ɢʀᴀᴘʜ", callback_data="mplus HELP_TG", style="primary")],
    [InlineKeyboardButton("ɪᴍᴘᴏsᴛᴇʀ", callback_data="mplus HELP_Imposter", style="primary"),
    InlineKeyboardButton("Tʀᴜᴛʜ-ᗪᴀʀᴇ", callback_data="mplus HELP_TD", style="primary"),InlineKeyboardButton("ʜᴀsᴛᴀɢ", callback_data="mplus HELP_HT", style="primary")], 
    [InlineKeyboardButton("ᴛᴛs", callback_data="mplus HELP_TTS", style="primary"),
    InlineKeyboardButton("ғᴜɴ", callback_data="mplus HELP_Fun", style="primary"),InlineKeyboardButton("ǫᴜᴏᴛʟʏ", callback_data="mplus HELP_Q", style="primary")],          
    [InlineKeyboardButton("<", callback_data=f"settings_back_helper", style="primary"), 
    InlineKeyboardButton(">", callback_data=f"managebot123 settings_back_helper", style="primary"),
    ]]