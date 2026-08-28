"""
/makesticker — reply to a photo, video, or GIF/animation with this
command (optionally with text) and the bot turns it into a proper
Telegram sticker.

- Photos → static WEBP sticker, resized to Telegram's format (512px
  on the long side), with an optional bold caption bar overlaid at
  the bottom.
- Videos/GIFs → animated WEBM video sticker (VP9, muted, trimmed to
  Telegram's 3-second sticker limit, resized to fit 512x512).

Usage: reply to a photo/video/GIF with  /makesticker Your text here
"""

import asyncio
import os
import uuid

from PIL import Image, ImageDraw, ImageFont
from pyrogram import filters
from pyrogram.types import Message

from CRAZYHUBBOT import app

STICKER_DIR = "downloads/stickers"
FONT_PATH = "CRAZYHUBBOT/assets/font.ttf"  # already bundled, used by welcome.py too
MAX_SIDE = 512  # Telegram sticker requirement: one side must be exactly 512px
MAX_VIDEO_SECONDS = 3  # Telegram's limit for video stickers


def _fit_to_sticker_canvas(photo: Image.Image) -> Image.Image:
    """Scales the photo so its longest side is 512px (Telegram sticker
    requirement), keeping aspect ratio — the short side ends up
    whatever it ends up being, which Telegram allows."""
    w, h = photo.size
    scale = MAX_SIDE / max(w, h)
    new_size = (max(1, round(w * scale)), max(1, round(h * scale)))
    return photo.resize(new_size, Image.LANCZOS)


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list:
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def _add_caption_bar(photo: Image.Image, text: str) -> Image.Image:
    """Overlays a semi-transparent dark bar with bold white text across
    the bottom of the image — the classic promo/poster-sticker look."""
    photo = photo.convert("RGBA")
    w, h = photo.size

    font_size = max(18, w // 12)
    font = ImageFont.truetype(FONT_PATH, font_size)

    draw_probe = ImageDraw.Draw(photo)
    padding = max(8, w // 40)
    lines = _wrap_text(draw_probe, text, font, w - 2 * padding)

    line_height = int(font_size * 1.25)
    bar_height = line_height * len(lines) + 2 * padding

    bar = Image.new("RGBA", (w, bar_height), (0, 0, 0, 160))
    draw = ImageDraw.Draw(bar)
    y = padding
    for line in lines:
        line_w = draw.textlength(line, font=font)
        x = (w - line_w) / 2
        # Thin black outline behind the white text for readability on
        # any background, since we can't know the photo's colors.
        for ox, oy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            draw.text((x + ox, y + oy), line, font=font, fill=(0, 0, 0, 255))
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
        y += line_height

    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    canvas.paste(photo, (0, 0))
    canvas.paste(bar, (0, h - bar_height), bar)
    return canvas


async def _video_to_animation(src_path: str, out_path: str):
    """Converts any video/GIF into an MP4 clip suitable for
    reply_animation() — H.264, no audio, trimmed to 3s, scaled to fit
    inside a 512x512 box. MP4 (not WEBM) because Telegram's
    sendAnimation only reliably renders inline for MP4/GIF; a WEBM
    here gets delivered as a plain downloadable document instead."""
    scale_filter = (
        f"scale='if(gt(iw,ih),{MAX_SIDE},-2)':'if(gt(iw,ih),-2,{MAX_SIDE})'"
    )
    cmd = [
        "ffmpeg",
        "-y",
        "-i", src_path,
        "-t", str(MAX_VIDEO_SECONDS),
        "-vf", scale_filter,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-an",
        out_path,
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {stderr.decode(errors='ignore')[-500:]}")


@app.on_message(filters.command(["makesticker", "mksticker", "stickergen"]))
async def makesticker_command(client, message: Message):
    replied = message.reply_to_message
    source = None
    kind = None  # "photo" or "video"
    for holder in (replied, message):
        if not holder:
            continue
        if holder.photo:
            source, kind = holder, "photo"
            break
        if holder.video or holder.animation:
            source, kind = holder, "video"
            break
    if not source:
        await message.reply_text(
            "Reply to a photo, video, or GIF with "
            "/makesticker [optional caption text]."
        )
        return

    caption_text = (
        message.text.split(None, 1)[1].strip() if len(message.command) > 1 else ""
    )

    status = await message.reply_text("🎨 Making your sticker...")
    os.makedirs(STICKER_DIR, exist_ok=True)
    file_id = uuid.uuid4().hex
    ext = "jpg" if kind == "photo" else "mp4"
    src_path = os.path.join(STICKER_DIR, f"src_{file_id}.{ext}")
    out_path = os.path.join(
        STICKER_DIR, f"sticker_{file_id}.{'webp' if kind == 'photo' else 'mp4'}"
    )

    try:
        await source.download(file_name=src_path)

        if kind == "photo":
            photo = Image.open(src_path).convert("RGBA")
            photo = _fit_to_sticker_canvas(photo)
            if caption_text:
                photo = _add_caption_bar(photo, caption_text)
            photo.save(out_path, "WEBP")
            await message.reply_sticker(out_path)
        else:
            # Text captions aren't overlaid on video stickers — doing
            # that per-frame reliably needs a heavier pipeline than
            # fits here; static photo stickers support captions.
            await _video_to_animation(src_path, out_path)
            # Sent via reply_animation (MP4), not reply_sticker
            # (WEBM) — Telegram's Bot API only renders inline/autoplay
            # for MP4/GIF through sendAnimation; a WEBM sent this way
            # (or via sendSticker on this Pyrogram version) ends up
            # delivered as a plain downloadable document instead.
            await message.reply_animation(out_path)
        await status.delete()
    except Exception as e:
        print(f"[makesticker] failed: {e}")
        await status.edit_text(
            "❌ Couldn't make that sticker — try a different file."
        )
    finally:
        for p in (src_path, out_path):
            try:
                os.remove(p)
            except OSError:
                pass
