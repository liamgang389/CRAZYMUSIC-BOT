from pyrogram import Client

import config

from ..logging import LOGGER

assistants = []
assistantids = []


class Userbot(Client):
    def __init__(self):
        self.one = Client(
            name="DAXXAss1",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING1),
            no_updates=True,
        )
        self.two = Client(
            name="DAXXAss2",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING2),
            no_updates=True,
        )
        self.three = Client(
            name="DAXXAss3",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING3),
            no_updates=True,
        )
        self.four = Client(
            name="DAXXAss4",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING4),
            no_updates=True,
        )
        self.five = Client(
            name="DAXXAss5",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING5),
            no_updates=True,
        )

    async def start(self):
        LOGGER(__name__).info(f"Starting Assistants...")
        if config.STRING1:
            try:
                await self.one.start()
            except Exception as e:
                LOGGER(__name__).error(
                    f"Assistant Account 1's STRING_SESSION is invalid/corrupted ({type(e).__name__}: {e}). "
                    "Generate a fresh session string using the SAME pyrogram version this bot uses "
                    "(pyrogram==2.0.106) — a Telethon or mismatched-version session string will NOT work."
                )
                exit()
            try:
                await self.one.join_chat("Music_logssss")
                await self.one.join_chat("About_EvoXpro_Owner")
            except:
                pass
            assistants.append(1)
            try:
                await self.one.send_message(config.LOGGER_ID, "Assistant Started")
            except:
                LOGGER(__name__).error(
                    "Assistant Account 1 has failed to access the log Group. Make sure that you have added your assistant to your log group and promoted as admin!"
                )
                exit()
            self.one.id = self.one.me.id
            self.one.name = self.one.me.mention
            self.one.username = self.one.me.username
            assistantids.append(self.one.id)
            LOGGER(__name__).info(f"Assistant Started as {self.one.name}")

        if config.STRING2:
            try:
                await self.two.start()
            except Exception as e:
                LOGGER(__name__).error(
                    f"Assistant Account 2's STRING_SESSION2 is invalid/corrupted ({type(e).__name__}: {e}). "
                    "Generate a fresh session string using the SAME pyrogram version this bot uses "
                    "(pyrogram==2.0.106) — a Telethon or mismatched-version session string will NOT work."
                )
                exit()
            try:
                await self.two.join_chat("Music_logssss")
                await self.one.join_chat("About_EvoXpro_Owner")
            except:
                pass
            assistants.append(2)
            try:
                await self.two.send_message(config.LOGGER_ID, "Assistant Started")
            except:
                LOGGER(__name__).error(
                    "Assistant Account 2 has failed to access the log Group. Make sure that you have added your assistant to your log group and promoted as admin!"
                )
                exit()
            self.two.id = self.two.me.id
            self.two.name = self.two.me.mention
            self.two.username = self.two.me.username
            assistantids.append(self.two.id)
            LOGGER(__name__).info(f"Assistant Two Started as {self.two.name}")

        if config.STRING3:
            try:
                await self.three.start()
            except Exception as e:
                LOGGER(__name__).error(
                    f"Assistant Account 3's STRING_SESSION3 is invalid/corrupted ({type(e).__name__}: {e}). "
                    "Generate a fresh session string using the SAME pyrogram version this bot uses "
                    "(pyrogram==2.0.106) — a Telethon or mismatched-version session string will NOT work."
                )
                exit()
            try:
                await self.three.join_chat("Music_logssss")
                await self.one.join_chat("About_EvoXpro_Owner")
            except:
                pass
            assistants.append(3)
            try:
                await self.three.send_message(config.LOGGER_ID, "Assistant Started")
            except:
                LOGGER(__name__).error(
                    "Assistant Account 3 has failed to access the log Group. Make sure that you have added your assistant to your log group and promoted as admin! "
                )
                exit()
            self.three.id = self.three.me.id
            self.three.name = self.three.me.mention
            self.three.username = self.three.me.username
            assistantids.append(self.three.id)
            LOGGER(__name__).info(f"Assistant Three Started as {self.three.name}")

        if config.STRING4:
            try:
                await self.four.start()
            except Exception as e:
                LOGGER(__name__).error(
                    f"Assistant Account 4's STRING_SESSION4 is invalid/corrupted ({type(e).__name__}: {e}). "
                    "Generate a fresh session string using the SAME pyrogram version this bot uses "
                    "(pyrogram==2.0.106) — a Telethon or mismatched-version session string will NOT work."
                )
                exit()
            try:
                await self.four.join_chat("Music_logssss")
                await self.one.join_chat("About_EvoXpro_Owner")
            except:
                pass
            assistants.append(4)
            try:
                await self.four.send_message(config.LOGGER_ID, "Assistant Started")
            except:
                LOGGER(__name__).error(
                    "Assistant Account 4 has failed to access the log Group. Make sure that you have added your assistant to your log group and promoted as admin! "
                )
                exit()
            self.four.id = self.four.me.id
            self.four.name = self.four.me.mention
            self.four.username = self.four.me.username
            assistantids.append(self.four.id)
            LOGGER(__name__).info(f"Assistant Four Started as {self.four.name}")

        if config.STRING5:
            try:
                await self.five.start()
            except Exception as e:
                LOGGER(__name__).error(
                    f"Assistant Account 5's STRING_SESSION5 is invalid/corrupted ({type(e).__name__}: {e}). "
                    "Generate a fresh session string using the SAME pyrogram version this bot uses "
                    "(pyrogram==2.0.106) — a Telethon or mismatched-version session string will NOT work."
                )
                exit()
            try:
                await self.five.join_chat("Music_logssss")
                await self.one.join_chat("About_EvoXpro_Owner")
            except:
                pass
            assistants.append(5)
            try:
                await self.five.send_message(config.LOGGER_ID, "Assistant Started")
            except:
                LOGGER(__name__).error(
                    "Assistant Account 5 has failed to access the log Group. Make sure that you have added your assistant to your log group and promoted as admin! "
                )
                exit()
            self.five.id = self.five.me.id
            self.five.name = self.five.me.mention
            self.five.username = self.five.me.username
            assistantids.append(self.five.id)
            LOGGER(__name__).info(f"Assistant Five Started as {self.five.name}")

    async def stop(self):
        LOGGER(__name__).info(f"Stopping Assistants...")
        try:
            if config.STRING1:
                await self.one.stop()
            if config.STRING2:
                await self.two.stop()
            if config.STRING3:
                await self.three.stop()
            if config.STRING4:
                await self.four.stop()
            if config.STRING5:
                await self.five.stop()
        except:
            pass
