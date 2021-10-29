import asyncio
import logging
import os
import sys
import traceback
import aiohttp
from cogs import commands, crashes, dialogflow, mediaonly, webhooklistener, welcome, levelling
import discord
import discord.ext.commands
import sqlobject as sql
import psycopg2
import psycopg2.extensions
import config
import libraries.createembed as CreateEmbed
from logstash_async.handler import AsynchronousLogstashHandler

ENVVARS = ["FRED_IP", "FRED_PORT", "FRED_TOKEN", "DIALOGFLOW_AUTH",
           "FRED_SQL_DB", "FRED_SQL_USER", "FRED_SQL_PASSWORD",
           "FRED_SQL_HOST", "FRED_SQL_PORT"]

for var in ENVVARS:
    assert (os.environ.get(var)), f"The ENV variable '{var}' isn't set"


class Bot(discord.ext.commands.Bot):

    async def isAlive(self):
        try:
            cursor = self.dbcon.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
        except:
            return False
        return True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.isReady = False
        self.setup_logger()
        self.setup_DB()
        self.command_prefix = config.Misc.fetch("prefix")
        self.setup_cogs()
        self.version = "2.17.4"

        self.loop = asyncio.get_event_loop()

    async def start(self, *args, **kwargs):
        async with aiohttp.ClientSession() as session:
            self.web_session = session
            return await super().start(*args, **kwargs)

    @staticmethod
    def is_running():
        return config.Misc.fetch("is_running")

    async def on_ready(self):
        await self.change_presence(activity=discord.Game("v" + self.version))
        self.isReady = True
        logging.info(f'We have logged in as {self.user}')

    @staticmethod
    async def on_reaction_add(reaction, user):
        if not user.bot and reaction.message.author.bot and reaction.emoji == "❌":
            await reaction.message.delete()

    def setup_DB(self):
        logging.info("Connecting to the database")
        user = os.environ.get("FRED_SQL_USER")
        password = os.environ.get("FRED_SQL_PASSWORD")
        host = os.environ.get("FRED_SQL_HOST")
        port = os.environ.get("FRED_SQL_PORT")
        dbname = os.environ.get("FRED_SQL_DB")
        uri = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
        try:
            connection = sql.connectionForURI(uri)
            sql.sqlhub.processConnection = connection
            config.create_missing_tables()
        except sql.dberrors.OperationalError:
            logging.warning("DB is either empty of not running")
            try:
                con = psycopg2.connect(dbname="postgres", user=user, password=password, host=host, port=port)
            except psycopg2.OperationalError:
                logging.error("The DB isn't running")
                raise EnvironmentError("The DB isn't running")
            autocommit = psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT
            con.set_isolation_level(autocommit)
            cursor = con.cursor()
            cursor.execute("CREATE DATABASE " + dbname)
            cursor.close()
            self.dbcon = con

            connection = sql.connectionForURI(uri)
            sql.sqlhub.processConnection = connection
            config.create_missing_tables()

        try:
            config.Commands.get(1)
        except:
            logging.warning("There is no registered command. Populating the database with the old config file")
            config.convert_old_config()

    def setup_logger(self):
        if os.environ.get("FRED_LOG_HOST") and os.environ.get("FRED_LOG_PORT"):
            logging.root = logging.getLogger("python-logstash-logger")
            logging.root.addHandler(
                AsynchronousLogstashHandler(os.environ.get("FRED_LOG_HOST"), int(os.environ.get("FRED_LOG_PORT")), ""))
            logging.root.addHandler(logging.StreamHandler())
        else:
            logging.root = logging.Logger("logger")
        logging.root.setLevel(logging.DEBUG)

        self.logger = logging.root

        logging.info("Successfully set up the logger")

    def setup_cogs(self):
        logging.info("Setting up cogs")
        self.add_cog(commands.Commands(self))
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
            channel = args[0].channel
            if isinstance(channel, discord.DMChannel):
                channelstr = f" in {channel.recipient.name}#{channel.recipient.discriminator}'s DMs"
            else:
                channelstr = f" in #{args[0].channel.name}"
        else:
            channelstr = ""
        tbs = f"```Fred v{self.version}\n\n{type.__name__} exception handled in {event}{channelstr}: {value}\n\n"
        for string in traceback.format_tb(tb):
            tbs = tbs + string
        tbs = tbs + "```"
        logging.error(tbs.replace("```", ""))
        await self.get_channel(748229790825185311).send(tbs)

    async def githook_send(self, data):
        logging.info("Handling GitHub payload", extra={'data': data})
        embed = await CreateEmbed.run(data, self)
        if embed == "Debug":
            self.logger.info("Non-supported Payload received")
        else:
            logging.info("GitHub payload was supported, sending an embed")
            channel = self.get_channel(config.Misc.fetch("githook_channel"))
            await channel.send(content=None, embed=embed)

    @staticmethod
    async def send_DM(user, content, embed=None, file=None):
        logging.info("Sending a DM", extra=helper.userdict(user))
        DB_user = config.Users.create_if_missing(user)
        if not DB_user.accepts_dms:
            logging.info("The user refuses to have DMs sent to them")
            return None

        if not user.dm_channel:
            logging.info(f"We did not have a DM channel with someone, creating one", extra=helper.userdict(user))
            await user.create_dm()
        try:
            if not embed:
                embed = CreateEmbed.DM(content)
                content = None
            return await user.dm_channel.send(content=content, embed=embed, file=file)
        except Exception as e:
            print(e)
            return None

    @staticmethod
    async def reply_to_msg(message, content=None, propagate_reply=True, **kwargs):
        reference = (message.reference if propagate_reply else None) or message
        if isinstance(reference, discord.MessageReference):
            reference.fail_if_not_exists = False
        logpayload = helper.messagedict(message)
        logpayload['reference'] = reference.message_id if 'message_id' in reference else reference.id
        logging.info(f"Replying to a message", extra=logpayload)
        return await message.channel.send(content, reference=reference, **kwargs)

    async def reply_question(self, message, question):
        await self.reply_to_msg(message, question)

        def check(message2):
            return message2.author == message.author

        try:
            response = await self.wait_for('message', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await self.reply_to_msg(message, "Timed out and aborted after 60 seconds.")
            raise asyncio.TimeoutError

        return response.content, response.attachments[0] if response.attachments else None

    async def reply_yes_or_no(self, message, question):
        response, _ = await self.reply_question(message, question)
        s = response.strip().lower()
        if s in ("1", "true", "yes", "y", "on", "oui"):
            return True
        elif s in ("0", "false", "no", "n", "off", "non"):
            return False
        else:
            await self.reply_to_msg(message, "Invalid bool string. Aborting")
            raise ValueError(f"Could not convert {s} to bool")

    async def on_message(self, message):
        if message.author.bot or not self.is_running():
            return
        logging.info("Processing a message", extra=helper.messagedict(message))
        if isinstance(message.channel, discord.DMChannel):
            logging.info("Processing a DM", extra=helper.messagedict(message))
            if message.content.lower() == "start":
                config.Users.fetch(message.author.id).accepts_dms = True
                logging.info("A user now accepts to receive DMs", extra=helper.messagedict(message))
                await self.reply_to_msg(message, "You will now receive level changes notifications !")
                return
            elif message.content.lower() == "stop":
                config.Users.fetch(message.author.id).accepts_dms = False
                logging.info("A user now refuses to receive DMs", extra=helper.messagedict(message))
                await self.reply_to_msg(message, "You will no longer receive level changes notifications !")
                return

        removed = await self.MediaOnly.process_message(message)
        if not removed:
            if message.content.startswith(self.command_prefix):
                await self.process_commands(message)
            else:
                reacted = await self.Crashes.process_message(message)
                if not reacted:
                    await self.DialogFlow.process_message(message)
        logging.info("Finished processing a message", extra=helper.messagedict(message))


intents = discord.Intents.default()
intents.members = True

client = Bot("?", help_command=None, intents=intents)
client.run(os.environ.get("FRED_TOKEN"))
