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
from pytesseract import pytesseract, image_to_string
import io

from urllib.request import urlopen
assert (os.environ.get("FRED_IP")), "The ENV variable 'FRED_IP' isn't set"
assert (os.environ.get("FRED_PORT")), "The ENV variable 'FRED_PORT' isn't set"
assert (os.environ.get("FRED_TOKEN")), "The ENV variable 'FRED_TOKEN' isn't set"
# server = 192.168.0.4:6969 | computer = 192.168.0.30:7000

class Bot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.git_listener = threading.Thread(target=WebhookListener.start_listener, args=[self])
        self.git_listener.daemon = True
        self.git_listener.start()
        self.queue_checker = self.loop.create_task(self.check_queue())

    async def on_ready(self):
        with open("Config.json", "r") as file:
            self.config = json.load(file)
        self.logchannel = self.get_channel(self.config["log channel"])
        print('We have logged in as {0.user}'.format(self))

    async def send_embed(self, embed_item):
        channel = self.get_channel(708420623310913628)
        await channel.send(content=None, embed=embed_item)

    async def check_queue(self):
        await self.wait_until_ready()
        while True:
            if os.path.exists("queue.txt"):
                with open("queue.txt", "r+") as file:
                    data = json.load(file)
                    try:
                        embed = CreateEmbed.run(data)
                    except:
                        print("Failed to create embed")
                    if embed == "Debug":
                        print("Unknown Payload received")
                    else:
                        await self.send_embed(embed)
                os.remove("queue.txt")
            else:
                await asyncio.sleep(1)

    async def on_message(self, message):
        time.sleep(0.1)
        if message.author.bot:
            return
        if message.author.permissions_in(self.get_channel(self.config["filter channel"])).send_messages:
            authorised = True
            if message.author.permissions_in(self.logchannel).send_messages:
                authorised = 2
        else:
            authorised = False

        # Media Only Channels
        for automation in self.config["media only channels"]:
            if message.channel.id == int(automation["id"]) and len(message.embeds) == 0 and len(
                    message.attachments) == 0:
                await message.author.send("Hi " + message.author.name + ", the channel '" + automation["name"]
                                          + "' you just tried to message in has been flagged as a 'Media Only' "
                                            "channel. This means you must post an embed or attach a file in order to "
                                            "post there. (we do not accept links)")
                await message.delete()
                return

        if message.content.startswith(self.config["prefix"]):
            await Commands.handleCommand(self, message, message.content.lower().lstrip(self.config["prefix"], "").split(" ")[0],message.content.lower().replace(self.config["prefix"], "").split(" ")[1:], authorised)

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
                                await message.channel.send(str(automation["response"].format(user=message.author.mention)))
                                return

        # Crash Responses

        #attachments
        if message.attachments:
            try:
                file = await message.attachments[0].to_file()
                file = file.fp
            except:
                file = io.BytesIO(b"")
            # .log or .txt Files
            if (".log" in message.attachments[0].filename or ".txt" in message.attachments[0].filename):
                for line in file:
                    for crash in self.config["known crashes"]:
                        if crash["crash"].lower() in line.decode().lower():
                            await message.channel.send(str(crash["response"].format(user=message.author.mention)))
                            return

            #images
            else:
                try:
                    image = Image.open(file)
                    image = image.convert(mode="L")
                    ratioTo8k = 4320 / image.height
                    if ratioTo8k > 1:
                        image = image.resize((round(image.width * ratioTo8k), round(image.height * ratioTo8k)),Image.LANCZOS)
                    result = image_to_string(image, lang="eng")[:2000]
                except:
                    result = ""
                for crash in self.config["known crashes"]:
                    if crash["crash"].lower() in result.lower():
                        await message.channel.send(str(crash["response"].format(user=message.author.mention)))
                        return

        #Pastebin links
        elif "https://pastebin.com/" in message.content:
            pastebincontent = urlopen("https://pastebin.com/raw/" + message.content.split("https://pastebin.com/")[1].split(" ")[0]).read()
            for crash in self.config["known crashes"]:
                if crash["crash"].lower() in pastebincontent.decode().lower():
                    await message.channel.send(str(crash["response"].format(user=message.author.mention)))
                    return
        else:
            for crash in self.config["known crashes"]:
                if crash["crash"].lower() in message.content.lower():
                    await message.channel.send(str(crash["response"].format(user=message.author.mention)))
                    return

client = Bot()
client.run(os.environ.get("FRED_TOKEN"))