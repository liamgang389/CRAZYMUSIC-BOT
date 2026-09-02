"""
/makesticker — reply to a photo, video, or GIF/animation with this
command (optionally with text/emoji) and the bot adds it as a REAL
Telegram sticker — addable via long-press → "Add to Stickers", not
just an inline GIF/document.

Telegram requires every sticker to belong to a sticker SET (pack) —
there's no such thing as a standalone one-off sticker at the protocol
level. So this creates (or reuses) one personal pack per user,
named after them, and adds each new sticker to it. That's the same
approach basically every "kang"/sticker-maker bot uses.

- Photos → static WEBP sticker, resized to Telegram's format (512px
  on the long side), with an optional bold caption bar baked in.
- Videos/GIFs → WEBM (VP9) video sticker, trimmed to Telegram's
  3-second sticker limit, resized to fit 512x512, muted.

Usage: reply to a photo/video/GIF with  /makesticker [emoji or text]
"""

import asyncio
import os
import re
import uuid

from PIL import Image, ImageDraw, ImageFont
from pyrogram import filters, raw
from pyrogram.errors import StickersetInvalid
from pyrogram.types import Message

from CRAZYHUBBOT import app

STICKER_DIR = "downloads/stickers"
FONT_PATH = "CRAZYHUBBOT/assets/font.ttf"  # already bundled, used by welcome.py too
MAX_SIDE = 512  # Telegram sticker requirement: one side must be exactly 512px
MAX_VIDEO_SECONDS = 3  # Telegram's limit for video stickers
DEFAULT_EMOJI = "🎵"

# A single leading emoji (very common — "😂" etc.) is a good enough
# heuristic to check for.
_EMOJI_ONLY_RE = re.compile(
    r"^[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F]+$"
)


def _fit_to_sticker_canvas(photo: Image.Image) -> Image.Image:
    """Scales the photo so its longest side is 512px (Telegram sticker
    requirement), keeping aspect ratio."""
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
    the bottom of the image."""
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
        for ox, oy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            draw.text((x + ox, y + oy), line, font=font, fill=(0, 0, 0, 255))
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
        y += line_height

    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    canvas.paste(photo, (0, 0))
    canvas.paste(bar, (0, h - bar_height), bar)
    return canvas


async def _video_to_sticker_webm(src_path: str, out_path: str, start_seconds: float = 0):
    """Converts any video/GIF into Telegram's official video-sticker
    format: WEBM container, VP9 codec, muted, trimmed to 3s starting
    at start_seconds (so a specific moment in a longer video/reel can
    be picked instead of always the very start), scaled to fit inside
    a 512x512 box. CRF-based encoding to keep the file reasonably
    small (Telegram enforces a hard ~256KB ceiling for sticker-pack
    items)."""
    scale_filter = (
        f"scale='if(gt(iw,ih),{MAX_SIDE},-2)':'if(gt(iw,ih),-2,{MAX_SIDE})'"
    )
    # Telegram enforces a hard file-size ceiling for video stickers
    # (STICKER_VIDEO_BIG if exceeded) — how much a given source
    # compresses at a fixed CRF depends heavily on its content
    # (motion, detail), so a single fixed setting that worked on a
    # simple test clip can still come out too big on a busier real
    # video. Instead, encode and check the actual output size,
    # stepping up compression (higher CRF, then a hard bitrate cap as
    # a last resort) until it fits, rather than guessing one setting.
    MAX_STICKER_BYTES = 250 * 1024  # a little under Telegram's 256KB limit
    attempts = [
        {"crf": "34", "b:v": "0"},
        {"crf": "42", "b:v": "0"},
        {"crf": "50", "b:v": "0"},
        {"crf": "50", "b:v": "150k"},  # hard cap as a last resort
    ]

    last_stderr = b""
    for attempt in attempts:
        cmd = [
            "ffmpeg", "-y",
            "-i", src_path,
            "-ss", str(max(0, start_seconds)),
            "-t", str(MAX_VIDEO_SECONDS),
            "-vf", scale_filter,
            "-c:v", "libvpx-vp9",
            "-crf", attempt["crf"],
            "-b:v", attempt["b:v"],
            "-an",
            out_path,
        ]
        print(f"[makesticker] running: {' '.join(cmd)}")
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        last_stderr = stderr
        if proc.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {stderr.decode(errors='ignore')[-500:]}")

        if os.path.getsize(out_path) <= MAX_STICKER_BYTES:
            return

    raise RuntimeError(
        f"couldn't compress under Telegram's video-sticker size limit "
        f"even at max compression (last size: {os.path.getsize(out_path)} bytes)"
    )


def _short_name_for(user_id: int) -> str:
    # Telegram requires bot-created set short_names to end with
    # "_by_<BotUsername>", start with a letter, and be alnum/underscore
    # only. Prefixing "a" guarantees the letter-start rule regardless
    # of the user_id's digits.
    return f"a{user_id}_by_{app.username}"


async def _upload_as_document(
    client, user_id: int, file_path: str, mime_type: str, emoji: str,
    is_video: bool, short_name: str,
):
    """Uploads a local file and registers it as a proper Document on
    Telegram's servers, returning an InputDocument (with a valid
    file_reference) that stickers.CreateStickerSet/AddStickerToSet
    require.

    Crucially, this tags the document with DocumentAttributeSticker
    at upload time, pointing at the REAL pack (by short_name) it's
    about to join — without it (or with a placeholder
    InputStickerSetEmpty), the document doesn't show the native
    "Add to Stickers" prompt when tapped, even after
    AddStickerToSet/CreateStickerSet succeeds, since clients read
    this attribute to know which pack to offer. Video stickers also
    need DocumentAttributeVideo alongside it."""
    uploaded_file = await client.save_file(file_path)
    peer = await client.resolve_peer(user_id)
    attributes = [
        raw.types.DocumentAttributeFilename(file_name=os.path.basename(file_path)),
        raw.types.DocumentAttributeSticker(
            alt=emoji,
            stickerset=raw.types.InputStickerSetShortName(short_name=short_name),
        ),
    ]
    if is_video:
        attributes.append(
            raw.types.DocumentAttributeVideo(
                duration=MAX_VIDEO_SECONDS,
                w=MAX_SIDE,
                h=MAX_SIDE,
                supports_streaming=True,
            )
        )
    result = await client.invoke(
        raw.functions.messages.UploadMedia(
            peer=peer,
            media=raw.types.InputMediaUploadedDocument(
                file=uploaded_file,
                mime_type=mime_type,
                attributes=attributes,
            ),
        )
    )
    doc = result.document
    return raw.types.InputDocument(
        id=doc.id, access_hash=doc.access_hash, file_reference=doc.file_reference
    )


async def _add_to_personal_pack(
    client, user_id: int, user_name: str, input_document, emoji: str,
    is_video: bool, short_name: str,
):
    """Adds input_document to the user's personal sticker pack for
    this bot, creating that pack on their first-ever sticker if it
    doesn't exist yet. Returns the newly-added sticker's own
    InputDocument, as returned by Telegram's sticker-set endpoints —
    this is used (instead of the InputDocument from the earlier
    upload step) to actually display the sticker, since it's the
    canonical, fully-tagged reference Telegram considers part of the
    pack."""
    sticker_item = raw.types.InputStickerSetItem(document=input_document, emoji=emoji)

    try:
        result = await client.invoke(
            raw.functions.stickers.AddStickerToSet(
                stickerset=raw.types.InputStickerSetShortName(short_name=short_name),
                sticker=sticker_item,
            )
        )
    except StickersetInvalid:
        # Pack doesn't exist yet for this user — create it with this
        # sticker as the first item.
        peer = await client.resolve_peer(user_id)
        result = await client.invoke(
            raw.functions.stickers.CreateStickerSet(
                user_id=peer,
                title=f"{user_name}'s stickers",
                short_name=short_name,
                stickers=[sticker_item],
                videos=is_video,
            )
        )

    new_doc = result.documents[-1]
    return raw.types.InputDocument(
        id=new_doc.id, access_hash=new_doc.access_hash, file_reference=new_doc.file_reference
    )


# Detects a start-time argument for videos: "15", "15s", "0:15",
# "1:05" — so a specific moment in a longer video/reel can be picked
# instead of always taking the first 3 seconds.
_TIMESTAMP_RE = re.compile(r"^(?:(\d+):)?(\d+(?:\.\d+)?)s?$")


def _parse_timestamp(text: str):
    """Returns seconds (float) if text looks like a timestamp,
    otherwise None."""
    m = _TIMESTAMP_RE.match(text.strip())
    if not m:
        return None
    minutes, seconds = m.groups()
    total = float(seconds)
    if minutes:
        total += int(minutes) * 60
    return total


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
            "Reply to a photo, video, or GIF with /makesticker "
            "[optional emoji or caption text].\n\n"
            "For a video/reel, you can also pick where the 3-second "
            "clip starts: /makesticker 0:15 grabs from the 15s mark."
        )
        return

    arg = message.text.split(None, 1)[1].strip() if len(message.command) > 1 else ""
    start_seconds = 0.0
    if kind == "video" and arg:
        parsed = _parse_timestamp(arg)
        if parsed is not None:
            start_seconds = parsed
            arg = ""  # consumed as a timestamp, not emoji/caption
    print(f"[makesticker] raw arg={message.text!r}, parsed start_seconds={start_seconds}")

    emoji = arg if arg and _EMOJI_ONLY_RE.match(arg) else DEFAULT_EMOJI
    caption_text = arg if arg and not _EMOJI_ONLY_RE.match(arg) else ""

    status = await message.reply_text("🎨 Making your sticker...")
    os.makedirs(STICKER_DIR, exist_ok=True)
    file_id = uuid.uuid4().hex
    ext = "jpg" if kind == "photo" else "mp4"
    src_path = os.path.join(STICKER_DIR, f"src_{file_id}.{ext}")
    out_path = os.path.join(
        STICKER_DIR, f"sticker_{file_id}.{'webp' if kind == 'photo' else 'webm'}"
    )

    try:
        await source.download(file_name=src_path)

        if kind == "photo":
            photo = Image.open(src_path).convert("RGBA")
            photo = _fit_to_sticker_canvas(photo)
            if caption_text:
                photo = _add_caption_bar(photo, caption_text)
            photo.save(out_path, "WEBP")
            mime_type = "image/webp"
        else:
            await _video_to_sticker_webm(src_path, out_path, start_seconds)
            mime_type = "video/webm"

        user_id = message.from_user.id
        user_name = message.from_user.first_name or "User"
        short_name = _short_name_for(user_id)
        input_document = await _upload_as_document(
            client, user_id, out_path, mime_type, emoji,
            is_video=(kind == "video"), short_name=short_name,
        )
        pack_document = await _add_to_personal_pack(
            client, user_id, user_name, input_document, emoji,
            is_video=(kind == "video"), short_name=short_name,
        )

        # Send the actual sticker into the chat (not just a text link)
        # — using pack_document (the reference Telegram itself
        # returned for this sticker as part of the set), so it
        # renders as a proper tappable sticker bubble with the native
        # "Add to Stickers" option, same as any sticker someone sends
        # you.
        await client.invoke(
            raw.functions.messages.SendMedia(
                peer=await client.resolve_peer(message.chat.id),
                media=raw.types.InputMediaDocument(id=pack_document),
                message="",
                random_id=client.rnd_id(),
                reply_to_msg_id=message.id,
            )
        )
        await status.delete()
    except Exception as e:
        print(f"[makesticker] failed: {e}")
        await status.edit_text(
            "❌ Couldn't make that sticker — try a different file, or a "
            "shorter/smaller video."
        )
    finally:
        for p in (src_path, out_path):
            try:
                os.remove(p)
            except OSError:
                pass
