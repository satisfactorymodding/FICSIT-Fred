from __future__ import annotations

import asyncio
import io
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from importlib.metadata import version
from os import getenv
from os.path import split
from typing import Optional
from urllib.parse import urlparse

import aiohttp
import nextcord
import sqlobject as sql
from nextcord.ext import commands

from . import config
from .cogs import crashes, mediaonly, webhooklistener, welcome, levelling
from .fred_commands import Commands, FredHelpEmbed
from .libraries import createembed, common

__version__ = version("fred")

from .libraries.common import text2file


class Bot(commands.Bot):

    async def isAlive(self: Bot):
        try:
            self.logger.info("Healthcheck: Attempting DB fetch")
            _ = config.Misc.get(1)
            self.logger.info("Healthcheck: Creating user fetch")
            coro = self.fetch_user(227473074616795137)
            self.logger.info("Healthcheck: Executing user fetch")
            await asyncio.wait_for(coro, timeout=5)
        except Exception as e:
            self.logger.error(f"Healthcheck failed: {e}")
            return False
        return True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.isReady = False
        self.logger = common.new_logger(self.__class__.__name__)
        self.version = __version__
        self.logger.info(f"Starting Fred v{self.version}")
        self.setup_DB()
        self.command_prefix = config.Misc.fetch("prefix")
        self.setup_cogs()
        FredHelpEmbed.setup()
        self.owo = False
        self.web_session: aiohttp.ClientSession = ...
        self.loop = asyncio.get_event_loop()
        self.executor = ThreadPoolExecutor()
        self.error_channel = int(chan) if (chan := config.Misc.fetch("error_channel")) else 748229790825185311

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
        self.logger.info(f"We have logged in as {self.user} with prefix {self.command_prefix}")

    async def on_reaction_add(self, reaction: nextcord.Reaction, user: nextcord.User) -> None:
        if not user.bot and reaction.message.author.bot and reaction.emoji == "❌":
            self.logger.info(f"Removing my own message because {user.display_name} reacted with ❌.")
            await reaction.message.delete()

    def setup_DB(self):
        self.logger.info("Connecting to the database")
        user = getenv("FRED_SQL_USER")
        password = getenv("FRED_SQL_PASSWORD")
        host = getenv("FRED_SQL_HOST")
        port = getenv("FRED_SQL_PORT")
        dbname = getenv("FRED_SQL_DB")
        uri = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
        attempt = 1
        while attempt < 6:
            try:
                connection = sql.connectionForURI(uri)
                sql.sqlhub.processConnection = connection
                config.migrate()
                self.logger.debug("Applied migration.")
                break
            except sql.dberrors.OperationalError:
                self.logger.error(f"Could not connect to the DB on attempt {attempt}")
                attempt += 1
                time.sleep(5)
        else:  # this happens if the loop is not broken by a successful connection
            raise ConnectionError("Could not connect to the DB")
        self.logger.info(f"Connected to the DB. Took {attempt} tries.")

    def setup_cogs(self):
        self.logger.info("Setting up cogs")
        self.add_cog(Commands(self))
        self.add_cog(webhooklistener.Githook(self))
        self.add_cog(mediaonly.MediaOnly(self))
        self.add_cog(crashes.Crashes(self))
        self.add_cog(welcome.Welcome(self))
        self.add_cog(levelling.Levelling(self))

        self.logger.info("Successfully set up cogs")

    @property
    def MediaOnly(self) -> mediaonly.MediaOnly:
        return self.get_cog("MediaOnly")  # noqa

    @property
    def Crashes(self) -> crashes.Crashes:
        return self.get_cog("Crashes")  # noqa

    @property
    def Welcome(self) -> welcome.Welcome:
        return self.get_cog("Welcome")  # noqa

    async def on_error(self, event_method: str, *args, **kwargs):
        exc_type, value, tb = sys.exc_info()
        if event_method == "on_message":
            channel: nextcord.abc.GuildChannel | nextcord.DMChannel = args[0].channel
            if isinstance(channel, nextcord.DMChannel):
                if channel.recipient is not None:
                    channel_str = f"{channel.recipient}'s DMs"
                else:
                    channel_str = "a DM"
            else:
                channel_str = f"{channel.guild.name}: `#{channel.name}` ({channel.mention})"
        else:
            channel_str = ""

        fred_str = f"Fred v{self.version}"
        error_meta = f"{exc_type.__name__} exception handled in `{event_method}` in {channel_str}"
        full_error = f"\n{value}\n\n{''.join(traceback.format_tb(tb))}"
        self.logger.error(f"{fred_str}\n{error_meta}\n{full_error}")

        # error_embed = nextcord.Embed(colour=nextcord.Colour.red(), title=error_meta, description=full_error)
        # error_embed.set_author(name=fred_str)

        await self.get_channel(self.error_channel).send(f"**{fred_str}**\n{error_meta}\n```py\n{full_error}```")

    async def githook_send(self, data: dict):
        self.logger.info("Handling GitHub payload", extra={"data": data})

        embed: nextcord.Embed | None = await createembed.github_embed(data)
        if embed is None:
            self.logger.info("Non-supported Payload received")
        else:
            self.logger.info("GitHub payload was supported, sending an embed")
            channel = self.get_channel(config.Misc.fetch("githook_channel"))
            await channel.send(content=None, embed=embed)

    async def _send_safe_direct_message_internal(
        self,
        user: nextcord.User | nextcord.Member,
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

        try:

            if not user.dm_channel:
                await user.create_dm()

            if not embed:
                embed = createembed.DM(content)
                content = None

            await self.safe_send(user.dm_channel, content=content, embed=embed, **kwargs)
            return True
        except Exception:  # noqa
            self.logger.error(f"DMs: Failed to DM, reason: \n{traceback.format_exc()}")
            return False

    async def send_safe_direct_message(self, user: nextcord.User, **kwargs) -> bool:
        user_meta = config.Users.create_if_missing(user)
        try:
            return await self._send_safe_direct_message_internal(user, user_meta=user_meta, **kwargs)
        except (nextcord.HTTPException, nextcord.Forbidden):
            # user has blocked bot or does not take mutual-server DMs
            return False

    @staticmethod
    async def safe_send(
        chan: nextcord.TextChannel | nextcord.DMChannel,
        content: Optional[str],
        /,
        files: Optional[list[nextcord.File]] = None,
        **kwargs,
    ) -> nextcord.Message:
        if content is not None and len(content) > 2000:
            files = files or []
            files.append(text2file(content, filename="long-message.txt"))
            content = "Message too long, converted to text file!"

        return await chan.send(content, files=files, **kwargs)

    async def reply_to_msg(
        self,
        message: nextcord.Message,
        content: Optional[str] = None,
        propagate_reply: bool = True,
        **kwargs,
    ) -> nextcord.Message:
        self.logger.info("Replying to a message", extra=common.message_info(message))
        # use this line if you're trying to debug discord throwing code 400s
        # self.logger.debug(jsonpickle.dumps(dict(content=content, **kwargs), indent=2))
        pingee = message.author
        if propagate_reply and message.reference is not None:
            reference = message.reference
            if (referenced_message := message.reference.cached_message) is not None:
                pingee = referenced_message.author
                if referenced_message.author == self.user:
                    reference = message
        else:
            reference = message

        if self.owo and content is not None:
            content = common.owoize(content)
        if isinstance(reference, nextcord.MessageReference):
            reference.fail_if_not_exists = False

        try:
            return await self.safe_send(message.channel, content, reference=reference, **kwargs)
        except (nextcord.HTTPException, nextcord.Forbidden):
            if content and pingee.mention not in content:
                content += f"\n-# {pingee.mention} ↩️"
            return await self.safe_send(message.channel, content, **kwargs)

    async def reply_question(
        self, message: nextcord.Message, question: Optional[str] = None, **kwargs
    ) -> tuple[str, Optional[nextcord.Attachment]]:
        await self.reply_to_msg(message, question, **kwargs)

        def check(message2: nextcord.Message):
            nonlocal message
            return message2.author == message.author

        try:
            response: nextcord.Message = await self.wait_for("message", timeout=120.0, check=check)
        except asyncio.TimeoutError:
            await self.reply_to_msg(message, "Timed out and aborted after 120 seconds.")
            raise asyncio.TimeoutError

        return response.content, response.attachments[0] if response.attachments else None

    async def reply_yes_or_no(self, message: nextcord.Message, question: Optional[str] = None, **kwargs) -> bool:
        response, _ = await self.reply_question(message, question, **kwargs)
        s = response.strip().lower()
        if s in ("1", "true", "yes", "y", "on", "oui"):
            return True
        elif s in ("0", "false", "no", "n", "off", "non"):
            return False
        else:
            await self.reply_to_msg(message, "Invalid bool string. Aborting")
            raise ValueError(f"Could not convert {s} to bool")

    async def on_message(self, message: nextcord.Message):
        self.logger.info("Processing a message", extra=common.message_info(message))
        if (is_bot := message.author.bot) or not self.is_running():
            self.logger.info(
                f"OnMessage: Didn't read message because {'the sender was a bot' if is_bot else 'I am dead'}."
            )
            return

        if isinstance(message.channel, nextcord.DMChannel):
            self.logger.info("Processing a DM", extra=common.message_info(message))
            if message.content.lower() == "start":
                config.Users.fetch(message.author.id).accepts_dms = True
                self.logger.info("A user now accepts to receive DMs", extra=common.message_info(message))
                await self.reply_to_msg(
                    message,
                    "You will now receive direct messages from me again! If you change your mind, send a message that says `stop`.",
                )
                return
            elif message.content.lower() == "stop":
                config.Users.fetch(message.author.id).accepts_dms = False
                self.logger.info("A user now refuses to receive DMs", extra=common.message_info(message))
                await self.reply_to_msg(
                    message,
                    "You will no longer receive direct messages from me! To resume, send a message that says `start`.",
                )
                return

        removed = await self.MediaOnly.process_message(message)
        if not removed:
            before, space, after = message.content.partition(" ")
            # if the prefix is the only thing before the space then this isn't a command
            if before.startswith(self.command_prefix) and len(before) > 1:
                self.logger.info("Processing commands")
                await self.process_commands(message)
            else:
                _reacted = await self.Crashes.process_message(message)
        self.logger.info("Finished processing a message", extra=common.message_info(message))

    async def repository_query(self, query: str):
        self.logger.info(f"SMR query of length {len(query)} requested")

        async with await self.web_session.post("https://api.ficsit.app/v2/query", json={"query": query}) as response:
            response.raise_for_status()
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
                rtn = content.decode() if get == str else content

        self.logger.info(f"Data has length of {len(rtn)}")
        return rtn

    async def obtain_attachment(self, url: str) -> nextcord.File:
        async with self.web_session.get(url) as resp:
            buff = io.BytesIO(await resp.read())
            _, filename = split(urlparse(url).path)
            return nextcord.File(filename=filename, fp=buff, force_close=True)
