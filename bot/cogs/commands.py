import discord
import asyncio
import librairies.createembed as CreateEmbed
import json
import librairies.helper as Helper
import matplotlib.pyplot as plt
import datetime
import logging
from algoliasearch.search_client import SearchClient
import requests
import io
import os
import sys
import typing


from discord.ext import commands


async def t3_only(ctx):
    return (ctx.author.id == 227473074616795137 or
            ctx.author.permissions_in(ctx.bot.get_channel(int(ctx.bot.config["filter channel"]))).send_messages)


async def mod_only(ctx):
    return (ctx.author.id == 227473074616795137 or
            ctx.author.permissions_in(ctx.bot.modchannel).send_messages)

class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            command = ctx.message.content.lower().lstrip(self.bot.command_prefix).split(" ")[0]
            for automation in self.bot.config["commands"]:
                if command == automation["command"]:
                    return
        await ctx.send(error)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not self.bot.running:
            return
        if message.content.startswith(self.bot.command_prefix):
            command = message.content.lower().lstrip(self.bot.command_prefix).split(" ")[0]
            for automation in self.bot.config["commands"]:
                if command.lower() == automation["command"].lower():
                    await message.channel.send(automation["response"])
                    return

    @commands.command()
    async def version(self, ctx):
        await ctx.send(self.bot.version)

    @commands.command()
    async def help(self, ctx):
        await ctx.send("Sorry, this command is temporarily unavailable")

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

        search = SearchClient.create('BH4D9OD16A', '53b3a8362ea7b391f63145996cfe8d82')
        index = search.init_index('ficsit')
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

    @add.command(name="mediaonly")
    async def addmediaonly(self, ctx, *args):
        if ctx.message.channel_mentions:
            id = ctx.message.channel_mentions[0].id
        else:
            if len(args) > 1:
                id = args[0]
            else:
                id = await Helper.waitResponse(self.bot, ctx.ctx.message, "What is the ID for the channel? e.g. "
                                                                          "``709509235028918334``")

        self.bot.config["media only channels"].append(id)
        self.bot.save_config()
        await ctx.send("Media only channel " + self.bot.get_channel(int(id)).mention + " added!")

    @add.command(name="command")
    async def addcommand(self, ctx, *args):
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

        self.bot.config["commands"].append({"command": command, "response": response})
        self.bot.save_config()
        await ctx.send("Command '" + command + "' added!")

    @add.command(name="crash")
    async def addcrash(self, ctx, *args):
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
        self.bot.save_config()
        await ctx.send("Known crash '" + name + "' added!")

    @add.command(name="dialogflow")
    async def dialogflow(self, ctx, id: str, response: typing.Union[str, bool], has_followup: bool, *args):
        if len(args) == 0:
            data = False
        else:
            data = {arg.split('=')[0]: arg.split('=')[1] for arg in args}
                
        if response == True:
            await ctx.send("Response should be a string or False (use the response from dialogflow)")
            return
        
        for dialogflowReply in self.bot.config["dialogflow"]:
            if dialogflowReply["id"] == id and (dialogflowReply["data"] == data):                
                should_delete = await Helper.waitResponse(self.bot, ctx.message, "Dialogflow response with this parameters already exists. Do you want to replace it? (Yes/No)")
                should_delete = should_delete.lower()
                if should_delete == 'no' or should_delete == 'n' or should_delete == 'false':
                    return
                await self.removedialogflow(ctx, id, *args)
        
        self.bot.config["dialogflow"].append({"id": id, "data": data, "response": response, "has_followup": has_followup})
        self.bot.save_config()
        await ctx.send("Dialogflow response for '" + id + "' (" + (json.dumps(data) if data else 'any data') + ") added!")

    @remove.command(name="mediaonly")
    async def removemediaonly(self, ctx, *args):
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
                self.bot.save_config()
                await ctx.send("Media Only Channel removed!")
                return
            else:
                index += 1
        await ctx.send("Media Only Channel could not be found!")

    @remove.command(name="command")
    async def removecommand(self, ctx, *args):
        if args:
            command = args[0]
        else:
            command = await Helper.waitResponse(self.bot, ctx.message, "What is the command? e.g. ``install``")

        command = command.lower()
        index = 0
        for response in self.bot.config["commands"]:
            if response["command"].lower() == command:
                del self.bot.config["commands"][index]
                self.bot.save_config()
                await ctx.send("Command removed!")
                return
            else:
                index += 1
        await ctx.send("Command could not be found!")

    @remove.command(name="crash")
    async def removecrash(self, ctx, *args):
        if args:
            name = args[0]
        else:
            name = await Helper.waitResponse(self.bot, ctx.message, "Which known crash do you want to remove?")

        index = 0
        for crash in self.bot.config["known crashes"]:
            if crash["name"].lower() == name.lower():
                del self.bot.config["known crashes"][index]
                self.bot.save_config()
                await ctx.send("Crash removed!")
                return
            index += 1
        await ctx.send("Crash could not be found!")

    @remove.command(name="dialogflow")
    async def removedialogflow(self, ctx, id: str, *args):
        if len(args) == 0:
            data = False
        else:
            data = {arg.split('=')[0]: arg.split('=')[1] for arg in args}

        index = 0
        for dialogflowReply in self.bot.config["dialogflow"]:
            if dialogflowReply["id"] == id and (dialogflowReply["data"] == data):
                del self.bot.config["dialogflow"][index]
                self.bot.save_config()
                await ctx.send("Dialogflow reply deleted")
                return
            index += 1

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

    @commands.command()
    @commands.check(mod_only)
    async def engineers(self, ctx, *args):
        if ctx.message.channel_mentions:
            id = ctx.message.channel_mentions[0].id
        else:
            if args:
                id = args[0]
            else:
                id = await Helper.waitResponse(self.bot, ctx.message,
                                               "What is the ID for the channel? e.g. ``709509235028918334``")
        self.bot.config["filter channel"] = int(id)
        self.bot.save_config()
        await ctx.send(
            "The filter channel for the engineers is now " + self.bot.get_channel(int(id)).mention + "!")

    @commands.command()
    @commands.check(mod_only)
    async def moderators(self, ctx, *args):
        if ctx.message.channel_mentions:
            id = ctx.message.channel_mentions[0].id
        else:
            if args:
                id = args[0]
            else:
                id = await Helper.waitResponse(self.bot, ctx.message,
                                               "What is the ID for the channel? e.g. ``709509235028918334``")
        self.bot.config["mod channel"] = int(id)
        self.bot.save_config()
        await ctx.send(
            "The filter channel for the moderators is now " + self.bot.get_channel(int(id)).mention + "!")

    @commands.command()
    @commands.check(mod_only)
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
        self.bot.save_config()
        await ctx.send(
            "The channel for the github hooks is now " + self.bot.get_channel(int(id)).mention + "!")

    @commands.command()
    @commands.check(mod_only)
    async def prefix(self, ctx, *args):
        if not args:
            await ctx.send("Please specify a prefix")
            return
        self.bot.config["prefix"] = args[0]
        self.bot.command_prefix = args[0]
        self.bot.save_config()
        await ctx.send("Prefix changed to " + args[0])


