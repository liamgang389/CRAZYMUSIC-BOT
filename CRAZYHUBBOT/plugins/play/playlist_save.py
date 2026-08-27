from pyrogram import filters
from pyrogram.types import Message

import config
from CRAZYHUBBOT import YouTube, app
from CRAZYHUBBOT.core.mongo import mongodb
from CRAZYHUBBOT.misc import db
from CRAZYHUBBOT.utils.database import is_active_chat
from CRAZYHUBBOT.utils.decorators.language import language
from CRAZYHUBBOT.utils.stream.stream import stream
from config import BANNED_USERS

playlistsdb = mongodb.saved_playlists
MAX_PLAYLIST_SIZE = 25  # keeps /loadplaylist reasonably fast and avoids abuse


@app.on_message(filters.command(["saveplaylist"]) & filters.group & ~BANNED_USERS)
@language
async def save_playlist_command(client, message: Message, _):
    if len(message.command) < 2:
        await message.reply_text(
            "Usage: /saveplaylist <name>\n\n"
            "Saves the songs currently in this chat's queue under that name, "
            "so you can bring them back anytime with /loadplaylist <name>."
        )
        return

    name = message.text.split(None, 1)[1].strip().lower()
    chat_id = message.chat.id
    queue = db.get(chat_id)
    if not queue:
        await message.reply_text("Nothing is playing/queued in this chat right now.")
        return

    songs = []
    for track in queue:
        vidid = track.get("vidid")
        title = track.get("title")
        if not vidid or not title:
            # Skip entries without a re-fetchable video id (e.g. a raw
            # uploaded audio file) — those can't be looked up again later.
            continue
        songs.append({"vidid": vidid, "title": title})
        if len(songs) >= MAX_PLAYLIST_SIZE:
            break

    if not songs:
        await message.reply_text(
            "Couldn't save this queue — none of the current tracks have a "
            "re-downloadable source (e.g. they were uploaded files, not "
            "YouTube/Spotify searches)."
        )
        return

    await playlistsdb.update_one(
        {"user_id": message.from_user.id, "name": name},
        {"$set": {"user_id": message.from_user.id, "name": name, "songs": songs}},
        upsert=True,
    )
    await message.reply_text(
        f"✅ Saved **{len(songs)}** song(s) as playlist **{name}**.\n"
        f"Load it anytime with `/loadplaylist {name}`."
    )


@app.on_message(filters.command(["loadplaylist"]) & filters.group & ~BANNED_USERS)
@language
async def load_playlist_command(client, message: Message, _):
    if len(message.command) < 2:
        await message.reply_text("Usage: /loadplaylist <name>")
        return

    name = message.text.split(None, 1)[1].strip().lower()
    chat_id = message.chat.id

    saved = await playlistsdb.find_one(
        {"user_id": message.from_user.id, "name": name}
    )
    if not saved or not saved.get("songs"):
        await message.reply_text(
            f"❌ No saved playlist named **{name}** found for you. "
            f"Save one first with `/saveplaylist {name}` while something "
            f"is queued."
        )
        return

    if not await is_active_chat(chat_id) and chat_id not in db:
        # No voice chat session yet — the normal /play flow is what
        # actually joins the VC, so ask for that first rather than
        # silently failing deep inside stream().
        await message.reply_text(
            "▶️ Play any song first with /play to join the voice chat, "
            "then run /loadplaylist again to queue the rest."
        )
        return

    mystic = await message.reply_text(
        f"⏳ Loading playlist **{name}** ({len(saved['songs'])} song(s))..."
    )
    vidids = [song["vidid"] for song in saved["songs"]]

    await stream(
        _,
        mystic,
        message.from_user.id,
        vidids,
        chat_id,
        message.from_user.first_name,
        chat_id,
        streamtype="playlist",
    )


@app.on_message(filters.command(["myplaylists"]) & ~BANNED_USERS)
@language
async def list_playlists_command(client, message: Message, _):
    cursor = playlistsdb.find({"user_id": message.from_user.id})
    names = [doc["name"] async for doc in cursor]
    if not names:
        await message.reply_text(
            "You haven't saved any playlists yet. Use /saveplaylist <name> "
            "while a queue is active in a group."
        )
        return
    listing = "\n".join(f"◆ {n}" for n in names)
    await message.reply_text(f"📋 **Your saved playlists:**\n\n{listing}")


@app.on_message(filters.command(["delplaylist"]) & ~BANNED_USERS)
@language
async def delete_playlist_command(client, message: Message, _):
    if len(message.command) < 2:
        await message.reply_text("Usage: /delplaylist <name>")
        return
    name = message.text.split(None, 1)[1].strip().lower()
    result = await playlistsdb.delete_one(
        {"user_id": message.from_user.id, "name": name}
    )
    if result.deleted_count:
        await message.reply_text(f"🗑 Deleted playlist **{name}**.")
    else:
        await message.reply_text(f"❌ No saved playlist named **{name}** found.")
