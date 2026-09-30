from pyrogram import  filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from CRAZYHUBBOT.utils.daxx_font import Fonts
from CRAZYHUBBOT import app

@app.on_message(filters.command(["font", "fonts"]))
async def style_buttons(c, m, cb=False):
    text = m.text.split(' ',1)[1]
    buttons = [
        [
            InlineKeyboardButton("𝚃𝚢𝚙𝚎𝚠𝚛𝚒𝚝𝚎𝚛", callback_data="style+typewriter", style="primary"),
            InlineKeyboardButton("𝕆𝕦𝕥𝕝𝕚𝕟𝕖", callback_data="style+outline", style="primary"),
            InlineKeyboardButton("𝐒𝐞𝐫𝐢𝐟", callback_data="style+serif", style="primary"),
        ],
        [
            InlineKeyboardButton("𝑺𝒆𝒓𝒊𝒇", callback_data="style+bold_cool", style="primary"),
            InlineKeyboardButton("𝑆𝑒𝑟𝑖𝑓", callback_data="style+cool", style="primary"),
            InlineKeyboardButton("Sᴍᴀʟʟ Cᴀᴘs", callback_data="style+small_cap", style="primary"),
        ],
        [
            InlineKeyboardButton("𝓈𝒸𝓇𝒾𝓅𝓉", callback_data="style+script", style="primary"),
            InlineKeyboardButton("𝓼𝓬𝓻𝓲𝓹𝓽", callback_data="style+script_bolt", style="primary"),
            InlineKeyboardButton("ᵗⁱⁿʸ", callback_data="style+tiny", style="primary"),
        ],
        [
            InlineKeyboardButton("ᑕOᗰIᑕ", callback_data="style+comic", style="primary"),
            InlineKeyboardButton("𝗦𝗮𝗻𝘀", callback_data="style+sans", style="primary"),
            InlineKeyboardButton("𝙎𝙖𝙣𝙨", callback_data="style+slant_sans", style="primary"),
        ],
        [
            InlineKeyboardButton("𝘚𝘢𝘯𝘴", callback_data="style+slant", style="primary"),
            InlineKeyboardButton("𝖲𝖺𝗇𝗌", callback_data="style+sim", style="primary"),
            InlineKeyboardButton("Ⓒ︎Ⓘ︎Ⓡ︎Ⓒ︎Ⓛ︎Ⓔ︎Ⓢ︎", callback_data="style+circles", style="primary"),
        ],
        [
            InlineKeyboardButton("🅒︎🅘︎🅡︎🅒︎🅛︎🅔︎🅢︎", callback_data="style+circle_dark", style="primary"),
            InlineKeyboardButton("𝔊𝔬𝔱𝔥𝔦𝔠", callback_data="style+gothic", style="primary"),
            InlineKeyboardButton("𝕲𝖔𝖙𝖍𝖎𝖈", callback_data="style+gothic_bolt", style="primary"),
        ],
        [
            InlineKeyboardButton("C͜͡l͜͡o͜͡u͜͡d͜͡s͜͡", callback_data="style+cloud", style="primary"),
            InlineKeyboardButton("H̆̈ă̈p̆̈p̆̈y̆̈", callback_data="style+happy", style="primary"),
            InlineKeyboardButton("S̑̈ȃ̈d̑̈", callback_data="style+sad", style="primary"),
        ],
        [InlineKeyboardButton ("ᴄʟᴏsᴇ",callback_data="close_reply", style="primary"),InlineKeyboardButton ("ɴᴇxᴛ ➻", callback_data="nxt", style="primary")],
    ]
    if not cb:
        await m.reply_text(
            f"`{text}`", reply_markup=InlineKeyboardMarkup(buttons), quote=True
        )
    else:
        await m.answer()
        await m.message.edit_reply_markup(InlineKeyboardMarkup(buttons))


@app.on_callback_query(filters.regex("^nxt"))
async def nxt(c, m):
    if m.data == "nxt":
        buttons = [
            [
                InlineKeyboardButton("🇸 🇵 🇪 🇨 🇮 🇦 🇱 ", callback_data="style+special", style="primary"),
                InlineKeyboardButton("🅂🅀🅄🄰🅁🄴🅂", callback_data="style+squares", style="primary"),
                InlineKeyboardButton(
                    "🆂︎🆀︎🆄︎🅰︎🆁︎🅴︎🆂︎", callback_data="style+squares_bold"
                , style="primary"),
            ],
            [
                InlineKeyboardButton("ꪖꪀᦔꪖꪶꪊᥴ𝓲ꪖ", callback_data="style+andalucia", style="primary"),
                InlineKeyboardButton("爪卂几ᘜ卂", callback_data="style+manga", style="primary"),
                InlineKeyboardButton("S̾t̾i̾n̾k̾y̾", callback_data="style+stinky", style="primary"),
            ],
            [
                InlineKeyboardButton(
                    "B̥ͦu̥ͦb̥ͦb̥ͦl̥ͦe̥ͦs̥ͦ", callback_data="style+bubbles"
                , style="primary"),
                InlineKeyboardButton(
                    "U͟n͟d͟e͟r͟l͟i͟n͟e͟", callback_data="style+underline"
                , style="primary"),
                InlineKeyboardButton("꒒ꍏꀷꌩꌃꀎꁅ", callback_data="style+ladybug", style="primary"),
            ],
            [
                InlineKeyboardButton("R҉a҉y҉s҉", callback_data="style+rays", style="primary"),
                InlineKeyboardButton("B҈i҈r҈d҈s҈", callback_data="style+birds", style="primary"),
                InlineKeyboardButton("S̸l̸a̸s̸h̸", callback_data="style+slash", style="primary"),
            ],
            [
                InlineKeyboardButton("s⃠t⃠o⃠p⃠", callback_data="style+stop", style="danger"),
                InlineKeyboardButton(
                    "S̺͆k̺͆y̺͆l̺͆i̺͆n̺͆e̺͆", callback_data="style+skyline"
                , style="primary"),
                InlineKeyboardButton("A͎r͎r͎o͎w͎s͎", callback_data="style+arrows", style="primary"),
            ],
            [
                InlineKeyboardButton("ዪሀክቿነ", callback_data="style+qvnes", style="primary"),
                InlineKeyboardButton("S̶t̶r̶i̶k̶e̶", callback_data="style+strike", style="primary"),
                InlineKeyboardButton("F༙r༙o༙z༙e༙n༙", callback_data="style+frozen", style="primary"),
            ],
            [InlineKeyboardButton ("ᴄʟᴏsᴇ",callback_data="close_reply", style="primary"),InlineKeyboardButton ("ʙᴀᴄᴋ", callback_data="nxt+0", style="primary")],
        ]
        await m.answer()
        await m.message.edit_reply_markup(InlineKeyboardMarkup(buttons))
    else:
        await style_buttons(c, m, cb=True)


@app.on_callback_query(filters.regex("^style"))
async def style(c, m):
    await m.answer()
    cmd,style = m.data.split('+')
    if style == "typewriter":
        cls = Fonts.typewriter
    if style == "outline":
        cls = Fonts.outline
    if style == "serif":
        cls = Fonts.serief
    if style == "bold_cool":
        cls = Fonts.bold_cool
    if style == "cool":
        cls = Fonts.cool
    if style == "small_cap":
        cls = Fonts.smallcap
    if style == "script":
        cls = Fonts.script
    if style == "script_bolt":
        cls = Fonts.bold_script
    if style == "tiny":
        cls = Fonts.tiny
    if style == "comic":
        cls = Fonts.comic
    if style == "sans":
        cls = Fonts.san
    if style == "slant_sans":
        cls = Fonts.slant_san
    if style == "slant":
        cls = Fonts.slant
    if style == "sim":
        cls = Fonts.sim
    if style == "circles":
        cls = Fonts.circles
    if style == "circle_dark":
        cls = Fonts.dark_circle
    if style == "gothic":
        cls = Fonts.gothic
    if style == "gothic_bolt":
        cls = Fonts.bold_gothic
    if style == "cloud":
        cls = Fonts.cloud
    if style == "happy":
        cls = Fonts.happy
    if style == "sad":
        cls = Fonts.sad
    if style == "special":
        cls = Fonts.special
    if style == "squares":
        cls = Fonts.square
    if style == "squares_bold":
        cls = Fonts.dark_square
    if style == "andalucia":
        cls = Fonts.andalucia
    if style == "manga":
        cls = Fonts.manga
    if style == "stinky":
        cls = Fonts.stinky
    if style == "bubbles":
        cls = Fonts.bubbles
    if style == "underline":
        cls = Fonts.underline
    if style == "ladybug":
        cls = Fonts.ladybug
    if style == "rays":
        cls = Fonts.rays
    if style == "birds":
        cls = Fonts.birds
    if style == "slash":
        cls = Fonts.slash
    if style == "stop":
        cls = Fonts.stop
    if style == "skyline":
        cls = Fonts.skyline
    if style == "arrows":
        cls = Fonts.arrows
    if style == "qvnes":
        cls = Fonts.rvnes
    if style == "strike":
        cls = Fonts.strike
    if style == "frozen":
        cls = Fonts.frozen
    #text = m.text.split(' ',1)[1]    
    new_text = cls(m.message.reply_to_message.text.split(" ",1)[1])
    try:
        await m.message.edit_text(new_text, reply_markup=m.message.reply_markup)
    except:
        pass


__help__ = """

 ❍ /fonts <text> *:* ᴄᴏɴᴠᴇʀᴛs sɪᴍᴩʟᴇ ᴛᴇxᴛ ᴛᴏ ʙᴇᴀᴜᴛɪғᴜʟ ᴛᴇxᴛ ʙʏ ᴄʜᴀɴɢɪɴɢ ɪᴛ's ғᴏɴᴛ.
 """

__mod_name__ = "Fᴏɴᴛ"