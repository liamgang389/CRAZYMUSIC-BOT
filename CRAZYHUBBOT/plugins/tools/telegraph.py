import os
import requests

from pyrogram import filters
from CRAZYHUBBOT import app

# =========================
# ImgBB Configuration
# =========================

IMGBB_API_URL = "https://api.imgbb.com/1/upload"

# 👇 YAHAN APNI IMGBB API KEY PASTE KARO
IMGBB_API_KEY = "00116cf777819bd32894be3bb3433f2e"


# =========================
# ImgBB Upload Function
# =========================

def upload_to_imgbb(path: str) -> str:

    if not IMGBB_API_KEY or IMGBB_API_KEY == "YOUR_IMGBB_API_KEY":
        raise RuntimeError("ImgBB API key is not configured.")

    with open(path, "rb") as image:
        response = requests.post(
            IMGBB_API_URL,
            params={
                "key": IMGBB_API_KEY
            },
            files={
                "image": image
            },
            timeout=60
        )

    try:
        data = response.json()
    except ValueError:
        raise RuntimeError(
            f"ImgBB returned invalid response: HTTP {response.status_code}"
        )

    if response.status_code >= 400 or not data.get("success"):
        error = data.get("error", {})

        if isinstance(error, dict):
            error_message = (
                error.get("message")
                or error.get("code")
                or "Unknown ImgBB error"
            )
        else:
            error_message = str(error)

        raise RuntimeError(error_message)

    image_data = data.get("data") or {}

    url = image_data.get("url")

    if not url:
        raise RuntimeError(
            "ImgBB upload succeeded but no image URL was returned."
        )

    return url


# =========================
# /tgm & /telegraph
# =========================

@app.on_message(filters.command(["tgm", "telegraph"]))
def upload_image(_, message):

    reply = message.reply_to_message

    # Only photo/image
    if not reply or not reply.photo:
        return message.reply(
            "❌ **Reply to an image/photo to generate a CDN link.**"
        )

    status = message.reply(
        "⏳ **Uploading image to ImgBB...**"
    )

    path = None

    try:

        # Download Telegram photo
        path = reply.download()

        if not path:
            return status.edit(
                "❌ **Failed to download the image.**"
            )

        # Upload to ImgBB
        url = upload_to_imgbb(path)

        # Send result
        status.edit(
            "✅ **IMAGE UPLOADED SUCCESSFULLY**\n\n"
            f"🔗 **Direct URL:**\n`{url}`"
        )

    except Exception as e:

        print(f"[ImgBB Error] {e}")

        status.edit(
            "❌ **ImgBB upload failed.**\n"
            "Please try again later."
        )

    finally:

        # Delete downloaded file
        if path and os.path.exists(path):

            try:
                os.remove(path)

            except Exception:
                pass


# =========================
# /graph & /grf
# =========================

try:
    from telegraph import upload_file
except ImportError:
    upload_file = None


@app.on_message(filters.command(["graph", "grf"]))
def upload_graph(_, message):

    reply = message.reply_to_message

    if not reply or not reply.media:
        return message.reply(
            "𝐑𝙴𝙿𝙻𝚈 𝚃𝙾 𝙰 𝙼𝙴𝙳𝙸𝙰 𝙼𝙴𝚂𝚂𝙰𝙶𝙴..."
        )

    if upload_file is None:
        return message.reply(
            "❌ **Telegraph uploader is unavailable.**"
        )

    status = message.reply(
        "𝐌𝙰𝙺𝙴 𝐀 𝐋𝙸𝙽𝙺..."
    )

    path = None

    try:

        path = reply.download()

        result = upload_file(path)

        url = "https://graph.org" + result[0]

        status.edit(
            f"Yᴏᴜʀ ʟɪɴᴋ sᴜᴄᴄᴇssғᴜʟ Gᴇɴ {url}"
        )

    except Exception as e:

        print(f"[Graph Error] {e}")

        status.edit(
            "⚠️ **Graph upload failed. "
            "Please try again later.**"
        )

    finally:

        if path and os.path.exists(path):

            try:
                os.remove(path)

            except Exception:
                pass
