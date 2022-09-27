import asyncio
import logging
import os
import sys
import textwrap
import time
import traceback

import aiohttp
import nextcord
from nextcord.ext import commands
import sqlobject as sql

from . import config
from .fred_commands import Commands, FredHelpEmbed
from .cogs import crashes, dialogflow, mediaonly, webhooklistener, welcome, levelling
from .libraries import createembed, common


__version__ = "2.20.3"


class Bot(commands.Bot):
    async def isAlive(self):
        try:
            logging.info("getting from config")
            _ = config.Misc.get(1)
            logging.info("creating user fetch")
            coro = self.fetch_user(227473074616795137)
            logging.info("fetching user")
            await asyncio.wait_for(coro, timeout=5)
        except Exception as e:
            self.logger.error(f"Healthiness check failed: {e}")
            return False
        return True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.isReady = False
        self.setup_logger()
        self.setup_DB()
        self.command_prefix = config.Misc.fetch("prefix")
        self.setup_cogs()
        self.version = __version__
        FredHelpEmbed.setup()
        self.owo = False

        self.loop = asyncio.new_event_loop()
        self._error_channel = int(env_val) if (env_val := os.getenv("ERROR_CHANNEL")) else 748229790825185311

    async def start(self, *args, **kwargs):
        async with aiohttp.ClientSession() as session:
            self.web_session = session
            return await super().start(*args, **kwargs)

    @staticmethod
    def is_running():
        return config.Misc.fetch("is_running")

    async def on_ready(self):
        await self.change_presence(activity=nextcord.Game(f"v{self.version}"))
        self.isReady = True
        logging.info(f"We have logged in as {self.user} with prefix {self.command_prefix}")

    @staticmethod
    async def on_reaction_add(reaction: nextcord.Reaction, user: nextcord.User) -> None:
        if not user.bot and reaction.message.author.bot and reaction.emoji == "❌":
            await reaction.message.delete()

    def setup_DB(self):
        self.logger.info("Connecting to the database")
        user = os.environ.get("FRED_SQL_USER")
        password = os.environ.get("FRED_SQL_PASSWORD")
        host = os.environ.get("FRED_SQL_HOST")
        port = os.environ.get("FRED_SQL_PORT")
        dbname = os.environ.get("FRED_SQL_DB")
        uri = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
        attempt = 1
        while attempt < 6:
            try:
                connection = sql.connectionForURI(uri)
                sql.sqlhub.processConnection = connection
                break
            except sql.dberrors.OperationalError:
                self.logger.error(f"Could not connect to the DB on attempt {attempt}")
                attempt += 1
                time.sleep(5)
        else:  # this happens if the loop is not broken by a successful connection
            raise ConnectionError("Could not connect to the DB")

    def setup_logger(self):
        logging.root = logging.Logger("FRED")
        logging.root.setLevel(logging.DEBUG)

        self.logger = logging.root

        self.logger.info("Successfully set up the logger")
        self.logger.info(f"Prefix: {self.command_prefix}")

    def setup_cogs(self):
        logging.info("Setting up cogs")
        self.add_cog(Commands(self))
        self.add_cog(webhooklistener.Githook(self))
        self.add_cog(mediaonly.MediaOnly(self))
        self.add_cog(crashes.Crashes(self))
        self.add_cog(dialogflow.DialogFlow(self))
        self.add_cog(welcome.Welcome(self))
        self.add_cog(levelling.Levelling(self))
        self.MediaOnly = self.get_cog("MediaOnly")
        self.Crashes = self.get_cog("Crashes")
        self.DialogFlow = self.get_cog("DialogFlow")
        logging.info("Successfully set up cogs")

    async def on_error(self, event, *args, **kwargs):
        type, value, tb = sys.exc_info()
        if event == "on_message":
            channel: nextcord.TextChannel | nextcord.DMChannel = args[0].channel
            if isinstance(channel, nextcord.DMChannel):
                channel_str = f" in {channel.recipient}'s DMs"
            else:
                channel_str = f" in {channel.mention}"
        else:
            channel_str = ""

        fred_str = f"Fred v{self.version}"
        error_meta = f"{type.__name__} exception handled in {event}{channel_str}"
        full_error = f"\n{value}\n\n{''.join(traceback.format_tb(tb))}"
        logging.error(f"{fred_str}\n{error_meta}\n{full_error}")

        # error_embed = nextcord.Embed(colour=nextcord.Colour.red(), title=error_meta, description=full_error)
        # error_embed.set_author(name=fred_str)

        await self.get_channel(self._error_channel).send(f"**{fred_str}**\n{error_meta}\n```py\n{full_error}```")

    async def githook_send(self, data):
        self.logger.info("Handling GitHub payload", extra={"data": data})

        embed: nextcord.Embed | None = await createembed.run(data)
        if embed is None:
            self.logger.info("Non-supported Payload received")
        else:
            self.logger.info("GitHub payload was supported, sending an embed")
            channel = self.get_channel(config.Misc.fetch("githook_channel"))
            await channel.send(content=None, embed=embed)

    async def send_DM(
        self,
        user: nextcord.User,
        content: str = None,
        embed: nextcord.Embed = None,
        user_meta: config.Users = None,
        in_dm: bool = False,
        **kwargs,
    ) -> bool:
        if self.owo:
            if content is not None:
                content = common.owoize(content)

            if embed is not None:
                embed.title = common.owoize(embed.title)
                embed.description = common.owoize(embed.description)
                # don't do the fields because those are most often literal command names, like in help

        self.logger.info("Sending a DM", extra=common.user_info(user))
        if not user_meta:
            user_meta = config.Users.create_if_missing(user)

        if not user_meta.accepts_dms and not in_dm:
            self.logger.info("The user refuses to have DMs sent to them")
            return False

        if not user.dm_channel:
            await user.create_dm()

        try:
            if not embed:
                embed = createembed.DM(content)
                content = None
            await user.dm_channel.send(content=content, embed=embed, **kwargs)
            return True
        except Exception:
            self.logger.error(f"DMs: Failed to DM, reason: \n{traceback.format_exc()}")
        return False

    async def checked_DM(self, user: nextcord.User, **kwargs) -> bool:
        user_meta = config.Users.create_if_missing(user)
        try:
            return await self.send_DM(user, user_meta=user_meta, **kwargs)
        except (nextcord.HTTPException, nextcord.Forbidden):
            # user has blocked bot or does not take mutual-server DMs
            return False

    async def reply_to_msg(self, message: nextcord.Message, content=None, propagate_reply=True, **kwargs):
        self.logger.info("Replying to a message", extra=common.message_info(message))
        # use this line if you're trying to debug discord throwing code 400s
        # self.logger.debug(jsonpickle.dumps(dict(content=content, **kwargs), indent=2))
        reference = (message.reference if propagate_reply else None) or message
        if self.owo and content is not None:
            content = common.owoize(content)
        if isinstance(reference, nextcord.MessageReference):
            reference.fail_if_not_exists = False

        return await message.channel.send(content, reference=reference, **kwargs)

    async def reply_question(self, message, question, **kwargs):
        await self.reply_to_msg(message, question, **kwargs)

        def check(message2):
            return message2.author == message.author

        try:
            response = await self.wait_for("message", timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await self.reply_to_msg(message, "Timed out and aborted after 60 seconds.")
            raise asyncio.TimeoutError

        return response.content, response.attachments[0] if response.attachments else None

    async def reply_yes_or_no(self, message, question, **kwargs):
        response, _ = await self.reply_question(message, question, **kwargs)
        s = response.strip().lower()
        if s in ("1", "true", "yes", "y", "on", "oui"):
            return True
        elif s in ("0", "false", "no", "n", "off", "non"):
            return False
        else:
            await self.reply_to_msg(message, "Invalid bool string. Aborting")
            raise ValueError(f"Could not convert {s} to bool")

    async def on_message(self, message):
        self.logger.info("Processing a message", extra=common.message_info(message))
        if (is_bot := message.author.bot) or not self.is_running():
            self.logger.info(
                "OnMessage: Didn't read message because " f"{'the sender was a bot' if is_bot else 'I am dead'}."
            )
            return

        if isinstance(message.channel, nextcord.DMChannel):
            self.logger.info("Processing a DM", extra=common.message_info(message))
            if message.content.lower() == "start":
                config.Users.fetch(message.author.id).accepts_dms = True
                self.logger.info("A user now accepts to receive DMs", extra=common.message_info(message))
                await self.reply_to_msg(message, "You will now receive level changes notifications !")
                return
            elif message.content.lower() == "stop":
                config.Users.fetch(message.author.id).accepts_dms = False
                self.logger.info("A user now refuses to receive DMs", extra=common.message_info(message))
                await self.reply_to_msg(message, "You will no longer receive level changes notifications !")
                return

        removed = await self.MediaOnly.process_message(message)
        if not removed:
            if message.content.startswith(self.command_prefix):
                self.logger.info("Processing commands")
                await self.process_commands(message)
            else:
                reacted = await self.Crashes.process_message(message)
                if not reacted:
                    await self.DialogFlow.process_message(message)
        self.logger.info("Finished processing a message", extra=common.message_info(message))

    async def repository_query(self, query: str):
        self.logger.info(f"SMR query of length {len(query)} requested")

        async with await self.web_session.post("https://api.ficsit.app/v2/query", json={"query": query}) as response:
            self.logger.info(f"SMR query returned with response {response.status}")
            value = await response.json()
            self.logger.info("SMR response decoded")
            return value

    async def async_url_get(self, url: str, /, get: type = bytes) -> str | bytes | dict:
        async with self.web_session.get(url) as response:
            self.logger.info(f"Requested {get} from {url} with response {response.status}")

            if get == dict:
                rtn = await response.json()
            else:
                content = await response.read()
                rtn = content.decode("utf-8") if get == str else content

        self.logger.info(f"Data has length of {len(rtn)}")
        return rtn
