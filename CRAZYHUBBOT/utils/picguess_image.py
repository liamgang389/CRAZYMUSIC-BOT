"""
Generates the card images for the Emoji/Word picture-guess game.

The bundled emoji font (CRAZYHUBBOT/assets/emoji_font.ttf, Noto Color
Emoji) is a bitmap-strike font — it only renders at its native pixel
size (109px), not at arbitrary sizes. So emoji are rendered small at
that native size, cropped tight, then upscaled with PIL to whatever
display size we actually want. Word cards use the project's existing
text font instead, which scales normally.
"""

import os
import uuid

from PIL import Image, ImageDraw, ImageFont

EMOJI_FONT_PATH = "CRAZYHUBBOT/assets/emoji_font.ttf"
WORD_FONT_PATH = "CRAZYHUBBOT/assets/font.ttf"
_EMOJI_NATIVE_SIZE = 109  # the only pixel size this bitmap font supports

TMP_DIR = "downloads"


def _render_emoji(emoji: str, display_size: int) -> Image.Image:
    font = ImageFont.truetype(EMOJI_FONT_PATH, _EMOJI_NATIVE_SIZE)
    tmp = Image.new("RGBA", (140, 140), (0, 0, 0, 0))
    draw = ImageDraw.Draw(tmp)
    bbox = draw.textbbox((0, 0), emoji, font=font, embedded_color=True)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((-bbox[0] + 2, -bbox[1] + 2), emoji, font=font, embedded_color=True)
    cropped = tmp.crop((0, 0, w + 4, h + 4))
    return cropped.resize((display_size, display_size), Image.LANCZOS)


def generate_emoji_card_for(emoji: str) -> str:
    size = (720, 720)
    card = Image.new("RGB", size, (22, 20, 38))
    draw = ImageDraw.Draw(card)
    for y in range(size[1]):
        shade = 22 + int(18 * (y / size[1]))
        draw.line([(0, y), (size[0], y)], fill=(shade, shade - 4, shade + 16))

    emoji_img = _render_emoji(emoji, 360)
    pos = ((size[0] - emoji_img.width) // 2, (size[1] - emoji_img.height) // 2 - 30)
    card.paste(emoji_img, pos, emoji_img)

    try:
        label_font = ImageFont.truetype(WORD_FONT_PATH, 40)
    except Exception:
        label_font = ImageFont.load_default()
    label = "🕵️ GUESS THE EMOJI"
    bbox = draw.textbbox((0, 0), label, font=label_font)
    lw = bbox[2] - bbox[0]
    draw.text(((size[0] - lw) / 2, size[1] - 90), label, font=label_font, fill=(230, 230, 245))

    os.makedirs(TMP_DIR, exist_ok=True)
    path = os.path.join(TMP_DIR, f"emojiguess_{uuid.uuid4().hex}.png")
    card.save(path)
    return path


def generate_word_card(word: str) -> str:
    size = (900, 420)
    card = Image.new("RGB", size, (18, 20, 32))
    draw = ImageDraw.Draw(card)
    for y in range(size[1]):
        shade = 18 + int(20 * (y / size[1]))
        draw.line([(0, y), (size[0], y)], fill=(shade, shade, shade + 18))

    display_text = word.upper()
    font_size = 110
    try:
        font = ImageFont.truetype(WORD_FONT_PATH, font_size)
        bbox = draw.textbbox((0, 0), display_text, font=font)
        while (bbox[2] - bbox[0]) > size[0] - 80 and font_size > 30:
            font_size -= 5
            font = ImageFont.truetype(WORD_FONT_PATH, font_size)
            bbox = draw.textbbox((0, 0), display_text, font=font)
    except Exception:
        font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), display_text, font=font)

    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(
        ((size[0] - tw) / 2 - bbox[0], (size[1] - th) / 2 - bbox[1] - 20),
        display_text,
        font=font,
        fill=(255, 210, 90),
    )

    try:
        label_font = ImageFont.truetype(WORD_FONT_PATH, 34)
    except Exception:
        label_font = ImageFont.load_default()
    label = "🔤 GUESS THIS — REPLY WITH THE WORD"
    lbbox = draw.textbbox((0, 0), label, font=label_font)
    lw = lbbox[2] - lbbox[0]
    draw.text(((size[0] - lw) / 2, size[1] - 70), label, font=label_font, fill=(210, 210, 225))

    os.makedirs(TMP_DIR, exist_ok=True)
    path = os.path.join(TMP_DIR, f"wordguess_{uuid.uuid4().hex}.png")
    card.save(path)
    return path
