import WebhookListener
import discord
import os
import asyncio
import CreateEmbed
import json
import threading
import Commands
import time
import Helper
import datetime

from urllib.request import urlopen


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
        with open("Bans.json", "r") as file:
            self.bans = json.load(file)
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
        if message.content.startswith(self.config["prefix"]):
            await Commands.handleCommand(self, message, message.content.lower()[1:].split(" ")[0],message.content.lower()[1:].split(" ")[1:], authorised)

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
        for crash in self.config["known crashes"]:
            # .log or .txt Files
            if message.attachments and (
                    ".log" in message.attachments[0].filename or ".txt" in message.attachments[0].filename):
                crashlog = await message.attachments[0].to_file()
                crashlog = crashlog.fp
                for line in crashlog:
                    if crash["crash"].lower() in line.decode().lower():
                        await message.channel.send(str(crash["response"].format(user=message.author.mention)))
                        return

            # Pastebin links
            elif "https://pastebin.com/" in message.content:
                try:
                    pastebincontent
                except NameError:
                    pastebincontent = urlopen(
                        "https://pastebin.com/raw/" + message.content.split("https://pastebin.com/")[1].split(" ")[
                            0]).read()
                if crash["crash"].lower() in pastebincontent.decode().lower():
                    await message.channel.send(str(crash["response"].format(user=message.author.mention)))
                    return

            elif crash["crash"].lower() in message.content.lower():
                await message.channel.send(str(crash["response"].format(user=message.author.mention)))
                return

        # Media Only Channels
        time.sleep(0.5)
        for automation in self.config["media only channels"]:
            if message.channel.id == int(automation["id"]) and len(message.embeds) == 0 and len(
                    message.attachments) == 0:
                await message.author.send("Hi " + message.author.name + ", the channel '" + automation["name"]
                                          + "' you just tried to message in has been flagged as a 'Media Only' "
                                            "channel. This means you must post an embed or attach a file in order to "
                                            "post there. (we do not accept links)")
                await message.delete()

    async def on_message_delete(self, message):
        if message.author.bot:
            return
        await self.logchannel.send(content=None, embed=CreateEmbed.message_deleted(message))

    async def on_message_edit(self, before, after):
        if before.author.bot:
            return
        await self.logchannel.send(content=None, embed=CreateEmbed.message_edited(before, after))

    async def on_member_remove(self, member):
        if member.bot:
            return
        await self.logchannel.send(content=None, embed=CreateEmbed.user_left(member))

    async def on_member_update(self, before, after):
        if before.bot:
            return
        if before.nick != after.nick:
            await self.logchannel.send(content=None, embed=CreateEmbed.member_nicked(before, after))


with open("Secrets.json", "r") as Secrets:
    Secrets = json.load(Secrets)

client = Bot()
client.run(Secrets["token"])
