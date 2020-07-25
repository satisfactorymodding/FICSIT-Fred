import WebhookListener
import discord
import os
import asyncio
import CreateEmbed
import json
import threading
import Commands
import time
from PIL import Image
from pytesseract import image_to_string
import io
from urllib.request import urlopen
import logging
import requests
import sys
import traceback
import inspect
import textwrap
import zipfile
from packaging import version

assert (os.environ.get("FRED_IP")), "The ENV variable 'FRED_IP' isn't set"
assert (os.environ.get("FRED_PORT")), "The ENV variable 'FRED_PORT' isn't set"
assert (os.environ.get("FRED_TOKEN")), "The ENV variable 'FRED_TOKEN' isn't set"

logging.basicConfig(level=logging.INFO)


class Bot(discord.Client):

    def isAlive(self):
        try:
            user = self.get_user(227473074616795137)
            queue = not self.queue_checker.done()
        except:
            return False
        if user and queue:
            return True
        else:
            return False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        with open("config/config.json", "r") as file:
            self.config = json.load(file)
        self.git_listener = threading.Thread(target=WebhookListener.start_listener, args=[self])
        self.git_listener.daemon = True
        self.git_listener.start()
        self.queue_checker = self.loop.create_task(self.check_queue())
        self.version = "1.2.2"
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
        await self.get_channel(720683767135469590).send(tbs)

    async def on_ready(self):
        logging.info(str(self.config))
        self.modchannel = self.get_channel(self.config["mod channel"])
        # with open("payload.txt", "r+") as file:
        #     data = json.load(file)
        # embed = await CreateEmbed.run(data, self)
        # if embed != "Debug":
        #     await self.modchannel.send(content=None, embed=embed)
        print('We have logged in as {0.user}'.format(self))

    async def send_embed(self, embed_item):
        channel = self.get_channel(self.config["githook channel"])
        await channel.send(content=None, embed=embed_item)

    async def check_queue(self):
        await self.wait_until_ready()
        while True:
            try:
                if os.path.exists("queue.txt"):
                    with open("queue.txt", "r+") as file:
                        data = json.load(file)
                        embed = await CreateEmbed.run(data, self)
                        if embed == "Debug":
                            print("Non-supported Payload received")
                        else:
                            await self.send_embed(embed)
                    os.remove("queue.txt")
                else:
                    await asyncio.sleep(1)
            except:
                await self.on_error("check_queue")
                break

    async def on_message(self, message):
        time.sleep(0.1)
        if message.author.bot:
            return
        if isinstance(message.channel, discord.DMChannel):
            await message.channel.send("I do not allow commands to be used by direct message, please use an "
                                       "appropriate channel in the Modding Discord instead.")
            return
        if message.author.permissions_in(self.get_channel(self.config["filter channel"])).send_messages:
            authorised = True
            if message.author.permissions_in(self.modchannel).send_messages:
                authorised = 2
        else:
            authorised = False

        # Media Only Channels
        for automation in self.config["media only channels"]:
            if message.channel.id == automation and len(message.embeds) == 0 and len(
                    message.attachments) == 0:
                await message.author.send(
                    "Hi " + message.author.name + ", the channel '" + self.get_channel(automation).name
                    + "' you just tried to message in has been flagged as a 'Media Only' "
                      "channel. This means you must attach a file in order to "
                      "post there.")
                await message.delete()
                return

        # Command handling
        if message.content.startswith(self.config["prefix"]):
            await Commands.handleCommand(self, message,
                                         message.content.lower().lstrip(self.config["prefix"]).split(" ")[0],
                                         message.content.lower().replace(self.config["prefix"], "").split(" ")[1:],
                                         authorised)

            if authorised:
                return

        # Run all automation tasks

        # Automated Responses
        for automation in self.config["automated responses"]:
            if len(message.author.roles) > 1 and automation["ignore members"] is False or len(
                    message.author.roles) == 1:
                for keyword in automation["keywords"]:
                    if keyword in message.content.lower():
                        for word in automation["additional words"]:
                            if word in message.content.lower():
                                await message.channel.send(
                                    str(automation["response"].format(user=message.author.mention)))
                                return

        # Crash Responses

        hasMetadata = False
        sml_version = ""
        CL = 0

        # attachments
        if message.attachments or "https://cdn.discordapp.com/attachments/" in message.content:
            try:
                file = await message.attachments[0].to_file()
                file = file.fp
                name = message.attachments[0].filename
            except:
                try:
                    id = message.content.split("https://cdn.discordapp.com/attachments/")[1].split(" ")[0]
                    name = id.split("/")[2]
                    file = io.BytesIO(requests.get("https://cdn.discordapp.com/attachments/" + id).content)
                except:
                    file = io.BytesIO(b"")
                    name = ""
            # .log or .txt Files
            if (".log" in name or ".txt" in name):
                data = file.read().decode("utf-8")

            # SMM Debug file
            elif ".zip" in name and "SMMDebug" in name:
                with zipfile.ZipFile(file) as zip:
                    try:
                        data = zip.open("FactoryGame.log").read().decode("utf-8")
                    except KeyError:
                        data = ""
                        pass
                    with zip.open("metadata.json") as metadataFile:
                        metadata = json.load(metadataFile)
                        CL = int(metadata["selectedInstall"]["version"])
                        sml_version = metadata["smlVersion"]
                        smb_version = metadata["bootstrapperVersion"]
                        hasMetadata = True

            # images
            else:
                try:
                    image = Image.open(file)
                    image = image.convert(mode="L")
                    ratioTo8k = 4320 / image.height
                    if ratioTo8k > 1:
                        image = image.resize((round(image.width * ratioTo8k), round(image.height * ratioTo8k)),
                                             Image.LANCZOS)
                    data = image_to_string(image, lang="eng")
                except:
                    data = ""

        # Pastebin links
        elif "https://pastebin.com/" in message.content:
            try:
                data = urlopen(
                    "https://pastebin.com/raw/" + message.content.split("https://pastebin.com/")[1].split(" ")[
                        0]).read().decode("utf-8")
            except:
                data = ""
        else:
            data = message.content

        # Try to find CL and SML versions in data
        if not hasMetadata:
            try:
                sml_version = data.find("SatisfactoryModLoader ", 0, 1000)
                assert sml_version != -1
                sml_version = data[sml_version:][23:].split("\r")[0]
            except:
                sml_version = ""
            try:
                CL = int(data[:200000].split("-CL-")[1].split("\n")[0])
            except:
                CL = 0

        if CL and sml_version:
            # Check the right SML for that CL
            query = """{
      getSMLVersions{
        sml_versions {
          version
          satisfactory_version
          bootstrap_version
        }
      }
    }"""
            r = requests.post("https://api.ficsit.app/v2/query", json={'query': query})
            rData = json.loads(r.text)
            sml_versions = rData["data"]["getSMLVersions"]["sml_versions"]
            for i in range(0, len(sml_versions) - 1):
                if hasMetadata:
                    if sml_versions[i]["version"] == sml_version:
                        if version.parse(sml_versions[i]["bootstrap_version"]) > version.parse(smb_version):
                            await message.channel.send(
                                "Your SMBootstrapper version is wrong. Please update it to " + sml_versions[i][
                                    "bootstrap_version"] + ". This can often be done by switch to the \"vanilla\" SMM profile and switching back to \"modded\", without launching the game in-between.")
                if sml_versions[i]["satisfactory_version"] > CL:
                    continue
                else:
                    latest = sml_versions[i]
                    break
            if latest["version"] != sml_version:
                await message.channel.send("Your SML version is wrong. Please update it to " + latest[
                    "version"] + ". This can often be done by switch to the \"vanilla\" SMM profile and switching back to \"modded\", without launching the game in-between.")

        data = data.lower()
        try:
            file.close()
        except:
            pass
        for crash in self.config["known crashes"]:
            if crash["crash"].lower() in data:
                await message.channel.send(str(crash["response"].format(user=message.author.mention)))
                return


client = Bot()
client.run(os.environ.get("FRED_TOKEN"))
