import asyncio
import logging
import os
import sys
import traceback
from cogs import commands, crashes, dialogflow, mediaonly, noshorturl, webhooklistener, welcome, levelling
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
    assert (os.environ.get(var)), "The ENV variable '{}' isn't set".format(var)


class Bot(discord.ext.commands.Bot):

    async def isAlive(self):
        try:
            user = await self.fetch_user(227473074616795137)
        except:
            return False
        return user

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_logger()
        self.setup_DB()
        self.command_prefix = config.Misc.fetch("prefix")
        self.setup_cogs()
        self.version = "2.13.0"

        self.running = True
        self.loop = asyncio.get_event_loop()

    async def on_ready(self):
        await self.change_presence(activity=discord.Game("v" + self.version))
        self.modchannel = self.get_channel(config.Misc.fetch("mod_channel"))
        assert self.modchannel, "I couldn't fetch the mod channel, please check the config"
        print('We have logged in as {0.user}'.format(self))

    async def on_reaction_add(self, reaction, user):
        if not user.bot and reaction.message.author.bot and reaction.emoji == "❌":
            await reaction.message.delete()

    def setup_DB(self):
        self.logger.info("Connecting to the database")
        user = os.environ.get("FRED_SQL_USER")
        password = os.environ.get("FRED_SQL_PASSWORD")
        host = os.environ.get("FRED_SQL_HOST")
        port = os.environ.get("FRED_SQL_PORT")
        dbname = os.environ.get("FRED_SQL_DB")
        uri = "postgresql://{}:{}@{}:{}/{}".format(user, password, host, port, dbname)
        try:
            connection = sql.connectionForURI(uri)
            sql.sqlhub.processConnection = connection
            config.create_missing_tables()
        except sql.dberrors.OperationalError:
            con = psycopg2.connect(dbname="postgres", user=user, password=password, host=host, port=port)
            autocommit = psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT
            con.set_isolation_level(autocommit)
            cursor = con.cursor()
            cursor.execute("CREATE DATABASE " + dbname)
            cursor.close()
            con.close()

            connection = sql.connectionForURI(uri)
            sql.sqlhub.processConnection = connection
            config.create_missing_tables()

        try:
            config.Commands.get(1)
        except:
            self.logger.warning("There is no registered command. Populating the database with the old config file")
            config.convert_old_config()

    def setup_logger(self):
        if os.environ.get("FRED_LOG_HOST") and os.environ.get("FRED_LOG_PORT"):
            self.logger = logging.getLogger("python-logstash-logger")
            self.logger.addHandler(
                AsynchronousLogstashHandler(os.environ.get("FRED_LOG_HOST"), int(os.environ.get("FRED_LOG_PORT")), ""))
            self.logger.addHandler(logging.StreamHandler())
        else:
            self.logger = logging.Logger("logger")
        self.logger.setLevel(logging.INFO)

    def setup_cogs(self):
        self.add_cog(commands.Commands(self))
        self.add_cog(webhooklistener.Githook(self))
        self.add_cog(mediaonly.MediaOnly(self))
        self.add_cog(crashes.Crashes(self))
        self.add_cog(noshorturl.NoShortUrl(self))
        self.add_cog(dialogflow.DialogFlow(self))
        self.add_cog(welcome.Welcome(self))
        self.add_cog(levelling.Levelling(self))
        self.MediaOnly = self.get_cog("MediaOnly")
        self.Crashes = self.get_cog("Crashes")
        self.NoShortUrl = self.get_cog("NoShortUrl")
        self.DialogFlow = self.get_cog("DialogFlow")

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
        print(tbs.replace("```", ""))

        await self.get_channel(748229790825185311).send(tbs)

    async def githook_send(self, data):
        embed = await CreateEmbed.run(data, self)
        if embed == "Debug":
            print("Non-supported Payload received")
        else:
            channel = self.get_channel(config.Misc.fetch("githook_channel"))
            await channel.send(content=None, embed=embed)

    async def send_DM(self, user, content, embed=None, file=None):
        DB_user = config.Users.create_if_missing(user)
        if not DB_user.accepts_dms:
            return None

        if not user.dm_channel:
            await user.create_dm()
        try:
            if not embed:
                embed = CreateEmbed.DM(content)
                content = None
            return await user.dm_channel.send(content=content, embed=embed, file=file)
        except Exception as e:
            print(e)
            return None

    async def reply_to_msg(self, message, content=None, propagate_reply=True, **kwargs):
        reference = (message.reference if propagate_reply else None) or message
        if isinstance(reference, discord.MessageReference):
            reference.fail_if_not_exists = False
        return await message.channel.send(content, reference=reference, **kwargs)

    async def on_message(self, message):
        if message.author.bot or not self.running:
            return
        if isinstance(message.channel, discord.DMChannel):
            if message.content.lower() == "start":
                config.Users.fetch(message.author.id).accepts_dms = True
                await self.reply_to_msg(message, "You will now receive rank changes notifications !")
                return
            elif message.content.lower() == "stop":
                config.Users.fetch(message.author.id).accepts_dms = False
                await self.reply_to_msg(message, "You will no longer receive rank changes notifications !")
                return

        removed = await self.MediaOnly.process_message(message)
        if not removed:
            removed = await self.NoShortUrl.process_message(message)
        if not removed:
            reacted = await self.Crashes.process_message(message)
            if not reacted:
                await self.process_commands(message)
                await self.DialogFlow.process_message(message)


intents = discord.Intents.default()
intents.members = True

client = Bot("?", help_command=None, intents=intents)
client.run(os.environ.get("FRED_TOKEN"))
