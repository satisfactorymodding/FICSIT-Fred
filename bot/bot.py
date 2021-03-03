import asyncio
import inspect
import io
import json
import logging
import os
import sys
import textwrap
import time
import traceback
import cogs.commands as Commands
import cogs.webhooklistener as WebhookListener
import cogs.mediaonly
import cogs.crashes
import cogs.noshorturl
import cogs.dialogflow
import discord
import discord.ext.commands

import librairies.createembed as CreateEmbed
from logstash_async.handler import AsynchronousLogstashHandler

assert (os.environ.get("FRED_IP")), "The ENV variable 'FRED_IP' isn't set"
assert (os.environ.get("FRED_PORT")), "The ENV variable 'FRED_PORT' isn't set"
assert (os.environ.get("FRED_TOKEN")), "The ENV variable 'FRED_TOKEN' isn't set"
assert (os.environ.get("DIALOGFLOW_AUTH")), "The ENV variable 'DIALOGFLOW_AUTH' isn't set"


class Bot(discord.ext.commands.Bot):

    async def isAlive(self):
        try:
            user = await self.fetch_user(227473074616795137)
            queue = not self.queue_checker.done()
        except:
            return False
        if user and queue:
            return True
        else:
            return False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        with open("../config/config.json", "r") as file:
            self.config = json.load(file)
        self.command_prefix = self.config["prefix"]
        if os.environ.get("FRED_LOG_HOST") and os.environ.get("FRED_LOG_PORT"):
            self.logger = logging.getLogger("python-logstash-logger")
            self.logger.addHandler(
                AsynchronousLogstashHandler(os.environ.get("FRED_LOG_HOST"), int(os.environ.get("FRED_LOG_PORT")), ""))
            self.logger.addHandler(logging.StreamHandler())
        else:
            self.logger = logging.Logger("logger")
        self.logger.setLevel(logging.INFO)
        self.add_cog(Commands.Commands(self))
        self.add_cog(WebhookListener.Githook(self))
        self.add_cog(cogs.mediaonly.MediaOnly(self))
        self.add_cog(cogs.crashes.Crashes(self))
        self.add_cog(cogs.noshorturl.NoShortUrl(self))
        self.add_cog(cogs.dialogflow.DialogFlow(self))
        self.MediaOnly = self.get_cog("MediaOnly")
        self.Crashes = self.get_cog("Crashes")
        self.NoShortUrl = self.get_cog("NoShortUrl")
        self.DialogFlow = self.get_cog("DialogFlow")
        self.version = "2.4.2"
        self.running = True
        self.loop = asyncio.get_event_loop()
        source = inspect.getsource(discord.abc.Messageable.send)
        source = textwrap.dedent(source)
        assert ("content = str(content) if content is not None else None" in source)
        source = source.replace("def send", "def new_send")
        source = source.replace("isinstance(file, File)", "isinstance(file, discord.File)")
        r = """
    async def check_delete(ret=ret):
        def check(reaction, user):
            if reaction.message.id == ret.id and not user.bot and reaction.emoji == "❌":
                return True
        try:
            await client.wait_for("reaction_add", check=check, timeout=60.0)
            await ret.delete()
        except asyncio.TimeoutError:
            pass
    asyncio.create_task(check_delete(ret))
    return ret
                """
        source = source.replace("return ret", r)
        exec(source, globals())
        discord.abc.Messageable.send = new_send


    async def on_ready(self):
        self.logger.info(str(self.config))
        self.modchannel = self.get_channel(int(self.config["mod channel"]))
        assert self.modchannel, "I couldn't fetch the mod channel, please check the config"
        print('We have logged in as {0.user}'.format(self))


    async def on_error(self, event, *args, **kwargs):
        type, value, tb = sys.exc_info()
        if event == "on_message":
            channel = " in #" + args[0].channel.name
        else:
            channel = ""
        tbs = "```Fred v" + self.version + "\n\n" + type.__name__ + " exception handled in " + event + channel + " : " + str(
            value) + "\n\n"
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
            channel = self.get_channel(self.config["githook channel"])
            await channel.send(content=None, embed=embed)

    async def on_message(self, message):
        if message.author.bot or not self.running:
            return
        if isinstance(message.channel, discord.DMChannel):
            await message.channel.send("I do not allow commands to be used by direct message, please use an "
                                       "appropriate channel in the Modding Discord instead.")
            return

        removed = await self.MediaOnly.process_message(message)
        if not removed:
            removed = await self.NoShortUrl.process_message(message)
        if not removed:
            await self.process_commands(message)
            await self.Crashes.process_message(message)
            await self.DialogFlow.process_message(message)
    
    def save_config(self):
        json.dump(self.config, open("../config/config.json", "w"), indent=4)


client = Bot("?", help_command=None)
client.run(os.environ.get("FRED_TOKEN"))
