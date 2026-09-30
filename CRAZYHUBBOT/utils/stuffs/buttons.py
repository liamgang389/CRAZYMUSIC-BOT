from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram import Client, filters, enums 

class BUTTONS(object):
    MBUTTON = [[InlineKeyboardButton("CʜᴀᴛGPT", callback_data="mplus HELP_ChatGPT", style=ButtonStyle.PRIMARY),InlineKeyboardButton("ɢʀᴏᴜᴘs", callback_data="mplus HELP_Group", style=ButtonStyle.PRIMARY),InlineKeyboardButton("sᴛɪᴄᴋᴇʀs", callback_data="mplus HELP_Sticker", style=ButtonStyle.PRIMARY)],
    [InlineKeyboardButton("Tᴀɢ-Aʟʟ", callback_data="mplus HELP_TagAll", style=ButtonStyle.PRIMARY),
    InlineKeyboardButton("Iɴꜰᴏ", callback_data="mplus HELP_Info", style=ButtonStyle.PRIMARY),InlineKeyboardButton("Exᴛʀᴀ", callback_data="mplus HELP_Extra", style=ButtonStyle.PRIMARY)],
    [InlineKeyboardButton("Iᴍᴀɢᴇ", callback_data="mplus HELP_Image", style=ButtonStyle.PRIMARY),
    InlineKeyboardButton("Aᴄᴛɪᴏɴ", callback_data="mplus HELP_Action", style=ButtonStyle.PRIMARY),InlineKeyboardButton("Sᴇᴀʀᴄʜ", callback_data="mplus HELP_Search", style=ButtonStyle.PRIMARY)],    
    [InlineKeyboardButton("ғᴏɴᴛ", callback_data="mplus HELP_Font", style=ButtonStyle.PRIMARY),
    InlineKeyboardButton("ɢᴀᴍᴇs", callback_data="mplus HELP_Game", style=ButtonStyle.PRIMARY),InlineKeyboardButton("Ⓣ-ɢʀᴀᴘʜ", callback_data="mplus HELP_TG", style=ButtonStyle.PRIMARY)],
    [InlineKeyboardButton("ɪᴍᴘᴏsᴛᴇʀ", callback_data="mplus HELP_Imposter", style=ButtonStyle.PRIMARY),
    InlineKeyboardButton("Tʀᴜᴛʜ-ᗪᴀʀᴇ", callback_data="mplus HELP_TD", style=ButtonStyle.PRIMARY),InlineKeyboardButton("ʜᴀsᴛᴀɢ", callback_data="mplus HELP_HT", style=ButtonStyle.PRIMARY)], 
    [InlineKeyboardButton("ᴛᴛs", callback_data="mplus HELP_TTS", style=ButtonStyle.PRIMARY),
    InlineKeyboardButton("ғᴜɴ", callback_data="mplus HELP_Fun", style=ButtonStyle.PRIMARY),InlineKeyboardButton("ǫᴜᴏᴛʟʏ", callback_data="mplus HELP_Q", style=ButtonStyle.PRIMARY)],          
    [InlineKeyboardButton("<", callback_data=f"settings_back_helper", style=ButtonStyle.PRIMARY), 
    InlineKeyboardButton(">", callback_data=f"managebot123 settings_back_helper", style=ButtonStyle.PRIMARY),
    ]]