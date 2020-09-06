import discord
import asyncio
import libraries.createembed as CreateEmbed
import json
import libraries.helper as Helper
import matplotlib.pyplot as plt
import datetime
import logging
from algoliasearch.search_client import SearchClient
import requests
import io
import os
import sys

from discord.ext import commands


async def t3_only(ctx):
    return (ctx.author.permissions_in(ctx.bot.get_channel(ctx.bot.config["filter channel"])).send_messages or
            ctx.author.id == 227473074616795137)


async def mod_only(ctx):
    return (ctx.author.permissions_in(ctx.bot.modchannel).send_messages or
            ctx.author.id == 227473074616795137)

class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot



    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not self.bot.running:
            return
        if message.content.startswith(self.bot.command_prefix):
            command = message.content.lower().lstrip(self.bot.command_prefix).split(" ")[0]
            args = message.content.lower().replace(self.bot.config["prefix"], "").split(" ")[1:]
            for automation in self.bot.config["commands"]:
                if command == automation["command"]:
                    await message.channel.send(automation["response"])
                    return

    @commands.command()
    async def version(self, ctx):
        await ctx.send(self.bot.version)

    @commands.command()
    async def mod(self, ctx, *args):
        if len(args) < 1:
            await ctx.send("This command requires at least one argument")
            return
        if args[0] == "help":
            await ctx.send("I search for the provided mod name in the SMR database, returning the details "
                           "of the mod if it is found. If multiple are found, it will state so. Same for "
                           "if none are found. If someone reacts to the clipboard in 4m, I will send them "
                           "the full description of the mod.")
            return
        args = " ".join(args)
        result, desc = CreateEmbed.mod(args)
        if result is None:
            await ctx.send("No mods found!")
        elif isinstance(result, str):
            await ctx.send("multiple mods found")
        else:
            newmessage = await ctx.send(content=None, embed=result)
            if desc:
                await newmessage.add_reaction("📋")
                await asyncio.sleep(0.5)

                def check(reaction, user):
                    if reaction.emoji == "📋" and reaction.message.id == newmessage.id:
                        return True

                while True:
                    try:
                        r = await self.bot.wait_for('reaction_add', timeout=240.0, check=check)
                        member = r[1]
                        if not member.dm_channel:
                            await member.create_dm()
                        try:
                            await member.dm_channel.send(content=None, embed=CreateEmbed.desc(desc))
                            await newmessage.add_reaction("✅")
                        except:
                            await ctx(
                                "I was unable to send you a direct message. Please check your discord "
                                "settings regarding those !")
                    except asyncio.TimeoutError:
                        break

    @commands.command()
    async def docsearch(self, ctx, *, args):
        yaml = requests.get("https://raw.githubusercontent.com/satisfactorymodding/Documentation/Dev/antora.yml")
        yamlf = io.BytesIO(yaml.content)
        version = str(yamlf.read()).split("version: ")[1].split("\\")[0]

        self.bot = SearchClient.create('BH4D9OD16A', '53b3a8362ea7b391f63145996cfe8d82')
        index = self.bot.init_index('ficsit')
        query = index.search(args + " " + version)
        await ctx.send("This is the best result I got from the SMD :\n" + query["hits"][0]["url"])

    @commands.group()
    @commands.check(t3_only)
    async def add(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid sub command passed...')
            return

    @commands.group()
    @commands.check(t3_only)
    async def remove(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid sub command passed...')
            return

    @add.command()
    async def mediaonly(self, ctx, *args):
        if ctx.message.channel_mentions:
            id = ctx.message.channel_mentions[0].id
        else:
            if len(args) > 1:
                id = args[0]
            else:
                id = await Helper.waitResponse(self.bot, ctx.ctx.message, "What is the ID for the channel? e.g. "
                                                                          "``709509235028918334``")

        self.bot.config["media only channels"].append(id)
        json.dump(self.bot.config, open("../config/config.json", "w"))
        await ctx.send("Media only channel " + self.bot.get_channel(int(id)).mention + " added!")

    @add.command()
    async def command(self, ctx, *args):
        if args:
            command = args[0]
        else:
            command = await Helper.waitResponse(self.bot, ctx.message, "What is the command? e.g. ``install``")

        for scommand in (self.bot.config["commands"] + self.bot.config["special commands"] + self.bot.config[
            "management commands"] + self.bot.config["miscellaneous commands"]):
            if command == scommand["command"]:
                await ctx.send("This command already exists !")
                return

        if len(args) == 2:
            response = args[1]
        elif len(args) > 1:
            response = " ".join(args[1:])
        else:
            response = await Helper.waitResponse(self.bot, ctx.message, "What is the response? e.g. ``Hello there`` "
                                                                        "or an image or link to an image")

        self.bot.config["commands"].append(
            {"command": command, "response": response})
        json.dump(self.bot.config, open("../config/config.json", "w"))
        await ctx.send("Command '" + command + "' added!")

    @add.command()
    async def crash(self, ctx, *args):
        if len(args) > 3:
            ctx.send("Please put your parameters between double quotes `\"`.")
            return
        if len(args) > 0:
            name = args[0]
        else:
            name = await Helper.waitResponse(self.bot, ctx.message, "What would you like to name this known "
                                                                    "crash? e.g. ``CommandDave``")
        name = name.lower()

        if len(args) > 1:
            crash = args[1]
        else:
            crash = await Helper.waitResponse(self.bot, ctx.message,
                                              "What is the string to search for in the crash logs ? e.g. \"Assertion "
                                              "failed: ObjectA == nullptr\"")
        if len(args) > 2:
            response = args[2]
        else:
            response = await Helper.waitResponse(self.bot, ctx.message,
                                                 "What response do you want it to provide? e.g. ``Thanks for saying my "
                                                 "keywords {user}`` (use {user} to ping the user)")

        self.bot.config["known crashes"].append({"name": name, "crash": crash, "response": response})
        json.dump(self.bot.config, open("../config/config.json", "w"))
        await ctx.send("Known crash '" + name + "' added!")

    @remove.command()
    async def mediaonly(self, ctx, *args):
        if ctx.message.channel_mentions:
            id = ctx.message.channel_mentions[0].id
        else:
            if len(args) > 1:
                id = args[0]
            else:
                id = await Helper.waitResponse(self.bot, ctx.ctx.message, "What is the ID for the channel? e.g. "
                                                                          "``709509235028918334``")

        index = 0
        for response in self.bot.config["media only channels"]:
            if response == id:
                del self.bot.config["media only channels"][index]
                json.dump(self.bot.config, open("../config/config.json", "w"))
                await ctx.send("Media Only Channel removed!")
                return
            else:
                index += 1
        await ctx.send("Media Only Channel could not be found!")

    @remove.command()
    async def command(self, ctx, *args):
        if args:
            command = args[0]
        else:
            command = await Helper.waitResponse(self.bot, ctx.message, "What is the command? e.g. ``install``")

        command = command.lower()
        index = 0
        for response in self.bot.config["commands"]:
            if response["command"].lower() == command:
                del self.bot.config["commands"][index]
                json.dump(self.bot.config, open("../config/config.json", "w"))
                await ctx.send("Command removed!")
                return
            else:
                index += 1
        await ctx.send("Command could not be found!")

    @remove.command()
    async def crash(self, ctx, *args):
        if args:
            name = args[0]
        else:
            name = await Helper.waitResponse(self.bot, ctx.message, "Which known crash do you want to remove?")

        index = 0
        for crash in self.bot.config["known crashes"]:
            if crash["name"].lower() == name.lower():
                del self.bot.config["known crashes"][index]
                json.dump(self.bot.config, open("../config/config.json", "w"))
                await ctx.send("Crash removed!")
                return
            else:
                index += 1
        await ctx.send("Crash could not be found!")

    @commands.command()
    @commands.check(t3_only)
    async def members(self, ctx):
        async with ctx.typing():
            list = []
            async for member in ctx.guild.fetch_members():
                list.append(member.joined_at)
            list.sort()
            first = list[0]
            last = list[len(list) - 1]
            count = 0
            countlist = []
            nb = 24
            for x in range(0, nb):
                for item in list:
                    if item > first + datetime.timedelta(days=x * 30):
                        break
                    count += 1
                countlist.append(count)
                count = 0

            plt.plot(range(0, nb), countlist)
            with open("Countlist.png", "wb") as image:
                plt.savefig(image, format="PNG")
                plt.clf()
            with open("Countlist.png", "rb") as image:
                await ctx.send(content=None, file=discord.File(image))

    @commands.command()
    @commands.check(t3_only)
    async def growth(self, ctx):
        async with ctx.typing():
            list = []
            async for member in ctx.guild.fetch_members():
                list.append(member.joined_at)
            list.sort()
            first = list[0]
            last = list[len(list) - 1]
            count = 0
            countlist = []
            nb = 24
            for x in range(0, nb):
                for item in list:
                    if item > first + datetime.timedelta(days=x * 30):
                        break
                    count += 1
                countlist.append(count)
                count = 0

            growth = []
            for x in range(0, nb):
                try:
                    ratio = (countlist[x] - countlist[x - 1]) / countlist[x - 1]
                    growth.append(ratio * 100)
                except IndexError:
                    growth.append(100)

            plt.plot(range(0, nb), growth)
            with open("Growth.png", "wb") as image:
                plt.savefig(image, format="PNG")
                plt.clf()
            with open("Growth.png", "rb") as image:
                await ctx.send(content=None, file=discord.File(image))

    @commands.command()
    @commands.check(t3_only)
    async def engineers(self, ctx, *args):
        if ctx.message.channel_mentions:
            id = ctx.message.channel_mentions[0].id
        else:
            if args:
                id = args[0]
            else:
                id = await Helper.waitResponse(self.bot, ctx.message,
                                               "What is the ID for the channel? e.g. ``709509235028918334``")
        self.bot.config["filter channel"] = id
        json.dump(self.bot.config, open("../config/config.json", "w"))
        await ctx.send(
            "The filter channel for the engineers is now " + self.bot.get_channel(int(id)).mention + "!")

    @commands.command()
    @commands.check(t3_only)
    async def moderators(self, ctx, *args):
        if ctx.message.channel_mentions:
            id = ctx.message.channel_mentions[0].id
        else:
            if args:
                id = args[0]
            else:
                id = await Helper.waitResponse(self.bot, ctx.message,
                                               "What is the ID for the channel? e.g. ``709509235028918334``")
        self.bot.config["mod channel"] = id
        json.dump(self.bot.config, open("../config/config.json", "w"))
        await ctx.send(
            "The filter channel for the moderators is now " + self.bot.get_channel(int(id)).mention + "!")

    @commands.command()
    @commands.check(t3_only)
    async def githook(self, ctx, *args):
        if ctx.message.channel_mentions:
            id = ctx.message.channel_mentions[0].id
        else:
            if args:
                id = args[0]
            else:
                id = await Helper.waitResponse(self.bot, ctx.message,
                                               "What is the ID for the channel? e.g. ``709509235028918334``")
        self.bot.config["githook channel"] = id
        json.dump(self.bot.config, open("../config/config.json", "w"))
        await ctx.send(
            "The channel for the github hooks is now " + self.bot.get_channel(int(id)).mention + "!")

    @commands.command()
    @commands.check(t3_only)
    async def prefix(self, ctx, *args):
        if not args:
            await ctx.send("Please specify a prefix")
            return
        self.bot.config["prefix"] = args[0]
        self.bot.command_prefix = args[0]
        json.dump(self.bot.config, open("../config/config.json", "w"))
        await ctx.send("Prefix changed to " + args[0])

    @commands.command()
    @commands.check(t3_only)
    async def saveconfig(self, ctx, *args):
        if not ctx.author.dm_channel:
            await ctx.author.create_dm()
        try:
            await ctx.author.dm_channel.send(content=None,
                                                 file=discord.File(open("../config/config.json", "r"),
                                                                   filename="config.json"))
            await ctx.message.add_reaction("✅")
        except:
            await ctx.send("I was unable to send you a direct message. Please check your discord "
                           "settings regarding those !")