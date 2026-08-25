import asyncio

import pyrogram.utils
from pyrogram import Client, errors
from pyrogram.enums import ChatMemberStatus, ParseMode
from pyrogram.errors import FloodWait

import config

from ..logging import LOGGER

# Pyrogram's default MIN_CHANNEL_ID is too narrow for some newer/larger
# Telegram channel IDs, causing a spurious "ValueError: Peer id invalid"
# even when the bot is a valid admin there. Widen the accepted range.
pyrogram.utils.MIN_CHANNEL_ID = -1009147483647


class DAXX(Client):
    def __init__(self):
        LOGGER(__name__).info(f"Starting Bot...")
        super().__init__(
            name="CRAZYHUBBOT",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            in_memory=True,
            workers=4,  # lowered for low-resource ($5/mo Railway) hosting
            max_concurrent_transmissions=2,  # lowered for low-resource ($5/mo Railway) hosting
        )

    async def start(self):
        # Telegram sometimes rate-limits bot logins (FloodWait), especially
        # right after several quick restarts. If we let this exception
        # propagate, the process exits and Railway restarts the container,
        # which immediately retries the login and gets hit with FloodWait
        # again — a rapid crash-restart loop that only makes the wait time
        # grow. Instead, catch it here and sleep it out inside the SAME
        # process, logging it once, so the container never has to restart.
        while True:
            try:
                await super().start()
                break
            except FloodWait as e:
                wait_time = e.value + 5
                LOGGER(__name__).warning(
                    f"Telegram FloodWait hit while logging in. Waiting "
                    f"{wait_time} seconds before retrying (this is normal "
                    f"after repeated restarts, only needs to happen once)."
                )
                await asyncio.sleep(wait_time)

        self.id = self.me.id
        self.name = self.me.first_name + " " + (self.me.last_name or "")
        self.username = self.me.username
        self.mention = self.me.mention

        try:
            await self.send_message(
                chat_id=config.LOGGER_ID,
                text=f"<u><b>» {self.mention} ʙᴏᴛ sᴛᴀʀᴛᴇᴅ :</b><u>\n\nɪᴅ : <code>{self.id}</code>\nɴᴀᴍᴇ : {self.name}\nᴜsᴇʀɴᴀᴍᴇ : @{self.username}",
            )
        except (errors.ChannelInvalid, errors.PeerIdInvalid):
            LOGGER(__name__).error(
                "Bot has failed to access the log group/channel. Make sure that you have added your bot to your log group/channel."
            )
            exit()
        except Exception as ex:
            LOGGER(__name__).error(
                f"Bot has failed to access the log group/channel.\n  Reason : {type(ex).__name__}."
            )
            exit()

        a = await self.get_chat_member(config.LOGGER_ID, self.id)
        if a.status != ChatMemberStatus.ADMINISTRATOR:
            LOGGER(__name__).error(
                "Please promote your bot as an admin in your log group/channel."
            )
            exit()
        LOGGER(__name__).info(f"Music Bot Started as {self.name}")

    async def stop(self):
        await super().stop()
