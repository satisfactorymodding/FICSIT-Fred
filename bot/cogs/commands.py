import re
from datetime import datetime, timedelta

import discord
import asyncio
import config
from cogs import levelling
import libraries.createembed as CreateEmbed
import json
import libraries.helper as Helper
from algoliasearch.search_client import SearchClient
import requests
import io
import typing
import aiohttp

from discord.ext import commands
from discord.ext.commands.view import StringView


def convert_to_bool(s: str):
    if s.lower() in ["1", "true", "yes", "y", "on"]:
        return True
    if s.lower() in ["0", "false", "no", "n", "off"]:
        return False
    raise ValueError(f"Could not convert {s} to bool")

async def t3_only(ctx):
    return (ctx.author.id == 227473074616795137 or
            ctx.author.permissions_in(ctx.bot.get_channel(config.Misc.fetch("filter_channel"))).send_messages)


async def mod_only(ctx):
    return (ctx.author.id == 227473074616795137 or
            ctx.author.permissions_in(ctx.bot.modchannel).send_messages)


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        # We get an error about commands being found when using "runtime" commands, so we have to ignore that
        if isinstance(error, commands.CommandNotFound):
            command = ctx.message.content.lower().lstrip(self.bot.command_prefix).split(" ")[0]
            if config.Commands.fetch(command):
                return
        elif isinstance(error, commands.CheckFailure):
            await ctx.send("Sorry, but you do not have enough permissions to do this")
        else:
            await ctx.send("I encountered an error while trying to call this command. Feyko has been notified")
            raise error

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not self.bot.running:
            return
        if message.content.startswith(self.bot.command_prefix):
            name = message.content.lower().lstrip(self.bot.command_prefix).split(" ")[0]
            if command := config.Commands.fetch(name):
                attachment = None
                if command["attachment"]:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(command["attachment"]) as resp:
                            buff = io.BytesIO(await resp.read())
                            attachment = discord.File(filename= command["attachment"].split("/")[-1], fp=buff)
                args = []
                view = StringView(message.content.lstrip(self.bot.command_prefix))
                view.get_word() # command name
                while not view.eof:
                    view.skip_ws()
                    args.append(view.get_quoted_word())
                
                text = re.sub('{(\d+)}', lambda match: args[int(match.group(1))] if int(match.group(1)) < len(args) else '(missing argument)', command["content"]).replace('{...}', ' '.join(args))
                await self.bot.reply_to_msg(message, text, file=attachment)
                return

    @commands.command()
    async def version(self, ctx):
        await self.bot.reply_to_msg(ctx.message, self.bot.version)

    @commands.command()
    async def help(self, ctx):
        await self.bot.reply_to_msg(ctx.message, "Sorry, this command is temporarily unavailable")

    @commands.command()
    async def mod(self, ctx, *args):
        if len(args) < 1:
            await self.bot.reply_to_msg(ctx.message, "This command requires at least one argument")
            return
        if args[0] == "help":
            await self.bot.reply_to_msg(ctx.message,
                                        "I search for the provided mod name in the SMR database, returning the details "
                                        "of the mod if it is found. If multiple are found, it will state so. Same for "
                                        "if none are found. If someone reacts to the clipboard in 4m, I will send them "
                                        "the full description of the mod.")
            return
        args = " ".join(args)
        result, desc = CreateEmbed.mod(args)
        if result is None:
            await self.bot.reply_to_msg(ctx.message, "No mods found!")
        elif isinstance(result, str):
            await self.bot.reply_to_msg(ctx.message, "multiple mods found")
        else:
            newmessage = await self.bot.reply_to_msg(ctx.message, content=None, embed=result)
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
                        sent = await self.bot.send_DM(member, content=None, embed=CreateEmbed.desc(desc))
                        if sent:
                            await newmessage.add_reaction("✅")
                        else:
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
        query = index.search(args, {
            'attributesToRetrieve': '*'
        })
        for hit in query["hits"]:
            if hit["hierarchy"]["lvl0"].endswith("latest"):
                await self.bot.reply_to_msg(ctx.message,
                                            "This is the best result I got from the SMD :\n" + hit["url"])
                return

    @commands.command()
    async def leaderboard(self, ctx):
        query = config.Users.select().orderBy("-xp_count").limit(10)
        results = list(query)
        if not results:
            self.bot.reply_to_msg(ctx.message, "The database was empty. This should NEVER happen")
            return
        data = [dict(name=user.full_name, count_and_rank=dict(count=user.xp_count, rank=user.rank)) for user in results]
        embed = CreateEmbed.leaderboard(data)
        await self.bot.reply_to_msg(ctx.message, embed=embed)

    @commands.command()
    async def rank(self, ctx, *, args=None):
        if ctx.message.mentions:
            user = ctx.message.mentions[0]
        else:
            if args:
                id = int(args[0])
                user = self.bot.get_user(id)
                if not user:
                    self.bot.reply_to_msg(ctx.message, "Sorry, I was unable to find the user with id {}".format(id))
                    return
            else:
                user = ctx.author
        DB_user = config.Users.create_if_missing(user)
        await self.bot.reply_to_msg(ctx.message,
                                    "{} is rank {} with {} xp".format(user.name, DB_user.rank, DB_user.xp_count))

    @commands.group()
    @commands.check(t3_only)
    async def add(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.bot.reply_to_msg(ctx.message, 'Invalid sub command passed...')
            return

    @commands.group()
    @commands.check(t3_only)
    async def remove(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.bot.reply_to_msg(ctx.message, 'Invalid sub command passed...')
            return

    @commands.group()
    @commands.check(t3_only)
    async def set(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.bot.reply_to_msg(ctx.message, 'Invalid sub command passed...')
            return

    @commands.group()
    @commands.check(t3_only)
    async def modify(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.bot.reply_to_msg(ctx.message, 'Invalid sub command passed...')
            return

    @commands.group()
    @commands.check(mod_only)
    async def xp(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.bot.reply_to_msg(ctx.message, 'Invalid sub command passed...')
            return

    @add.command(name="mediaonly")
    async def addmediaonly(self, ctx, *args):
        if ctx.message.channel_mentions:
            id = int(ctx.message.channel_mentions[0].id)
        else:
            if len(args) > 0:
                id = int(args[0])
            else:
                id, attachment = await Helper.waitResponse(self.bot, ctx.message, "What is the ID for the channel? e.g. "
                                                                          "``709509235028918334``")
                id = int(id)

        if config.MediaOnlyChannels.fetch(id):
            await self.bot.reply_to_msg(ctx.message, "This channel is already a media only channel")
            return

        config.MediaOnlyChannels(channel_id=id)
        await self.bot.reply_to_msg(ctx.message, "Media only channel " + self.bot.get_channel(id).mention + " added !")

    @remove.command(name="mediaonly")
    async def removemediaonly(self, ctx, *args):
        if ctx.message.channel_mentions:
            id = int(ctx.message.channel_mentions[0].id)
        else:
            if len(args) > 0:
                id = int(args[0])
            else:
                id, attachment = await Helper.waitResponse(self.bot, ctx.message, "What is the ID for the channel? e.g. "
                                                                          "``709509235028918334``")
                id = int(id)

        if not config.MediaOnlyChannels.fetch(id):
            await self.bot.reply_to_msg(ctx.message, "Media Only Channel could not be found !")
            return

        config.MediaOnlyChannels.deleteBy(channel_id=id)
        await self.bot.reply_to_msg(ctx.message, "Media Only Channel removed !")

    @add.command(name="command")
    async def addcommand(self, ctx, *args):
        if args:
            command = args[0]
        else:
            command, attachment = await Helper.waitResponse(self.bot, ctx.message, "What is the command? e.g. ``install``")
        command = command.lower()
        if config.Commands.fetch(command):
            await self.bot.reply_to_msg(ctx.message, "This command already exists !")
            return
        if config.ReservedCommands.fetch(command):
            await self.bot.reply_to_msg(ctx.message, "This command name is reserved")
            return
        attachment = None
        if len(args) == 2:
            response = args[1]
        elif len(args) > 1:
            response = " ".join(args[1:])
        else:
            response, attachment = await Helper.waitResponse(self.bot, ctx.message, "What is the response? e.g. ``Hello there`` "
                                                                        "or an image or link to an image")
        attachment = attachment.url if attachment else None
        config.Commands(name=command, content=response, attachment=attachment)
        await self.bot.reply_to_msg(ctx.message, "Command '" + command + "' added !")

    @remove.command(name="command")
    async def removecommand(self, ctx, *args):
        if args:
            commandname = args[0]
        else:
            commandname, attachment, attachment = await Helper.waitResponse(self.bot, ctx.message, "What is the command? e.g. ``install``")

        if not config.Commands.fetch(commandname):
            await self.bot.reply_to_msg(ctx.message, "Command could not be found !")
            return
        commandname = commandname.lower()
        config.Commands.deleteBy(name=commandname)
        await self.bot.reply_to_msg(ctx.message, "Command removed !")

    @modify.command(name="command")
    async def modifycommand(self, ctx, *args):
        if args:
            commandname = args[0]
        else:
            commandname, attachment = await Helper.waitResponse(self.bot, ctx.message,
                                                    "What is the command to modify ? e.g. ``install``")
        if config.ReservedCommands.fetch(commandname):
            await self.bot.reply_to_msg(ctx.message, "This command is special and cannot be modified")
            return

        commandname = commandname.lower()
        query = config.Commands.selectBy(name=commandname)
        results = list(query)
        if not results:
            createcommand, attachment = await Helper.waitResponse(self.bot, ctx.message,
                                                      "Command could not be found ! Do you want to create it ?")
            try:
                createcommand = convert_to_bool(createcommand)
            except ValueError:
                await self.bot.reply_to_msg(ctx.message, "Invalid bool string")
                return

            if not createcommand:
                await self.bot.reply_to_msg(ctx.message, "Understood. Aborting")
                return
            
            await self.addcommand(ctx, *args if args else commandname)
            return
            
        attachment = None
        if len(args) == 2:
            response = args[1]
        elif len(args) > 1:
            response = " ".join(args[1:])
        else:
            response, attachment = await Helper.waitResponse(self.bot, ctx.message, "What is the response? e.g. ``Hello there`` "
                                                                        "and/or an image")
        attachment = attachment.url if attachment else None
        results[0].content = response
        results[0].attachment = attachment
        await self.bot.reply_to_msg(ctx.message, "Command '" + commandname + "' modified !")

    @add.command(name="crash")
    async def addcrash(self, ctx, *args):
        if len(args) > 3:
            self.bot.reply_to_msg(ctx.message, "Please put your parameters between double quotes `\"`.")
            return
        if len(args) > 0:
            name = args[0]
        else:
            name, attachment = await Helper.waitResponse(self.bot, ctx.message, "What would you like to name this known "
                                                                    "crash? e.g. ``CommandDave``")
        name = name.lower()

        if config.Crashes.fetch(name):
            await self.bot.reply_to_msg(ctx.message, "A crash with this name already exists")
            return

        if len(args) > 1:
            crash = args[1]
        else:
            crash, attachment = await Helper.waitResponse(self.bot, ctx.message, "What is the regular expression to match in the logs ?")

        try:
            re.search(crash, "test")
        except:
            await self.bot.reply_to_msg(ctx.message, "The regex isn't valid. Please refer to "
                                               "https://docs.python.org/3/library/re.html for docs on Python's regex "
                                               "library")
            return

        if len(args) > 2:
            response = args[2]
        else:
            response, attachment = await Helper.waitResponse(self.bot, ctx.message,
                                                 "What response do you want it to provide? Responding with a command will make the response that command")

        config.Crashes(name=name, crash=crash, response=response)
        await self.bot.reply_to_msg(ctx.message, "Known crash '" + name + "' added!")

    @remove.command(name="crash")
    async def removecrash(self, ctx, *args):
        if args:
            name = args[0]
        else:
            name, attachment = await Helper.waitResponse(self.bot, ctx.message, "Which known crash do you want to remove ?")

        if not config.Crashes.fetch(name):
            await self.bot.reply_to_msg(ctx.message, "Crash could not be found!")
            return
        name = name.lower()
        config.Crashes.deleteBy(name=name)
        await self.bot.reply_to_msg(ctx.message, "Crash removed!")

    @modify.command(name="crash")
    async def modifycrash(self, ctx, *args):
        if args:
            crashname = args[0]
        else:
            crashname, _ = await Helper.waitResponse(self.bot, ctx.message,
                                                    "What is the crash to modify ? e.g. ``install``")

        crashname = crashname.lower()
        query = config.Crashes.selectBy(name=crashname)
        results = list(query)
        if not results:
            createcrash, _ = await Helper.waitResponse(self.bot, ctx.message,
                                                      "Command could not be found ! Do you want to create it ?")
            try:
                createcrash = convert_to_bool(createcrash)
            except ValueError:
                await self.bot.reply_to_msg(ctx.message, "Invalid bool string")
                return

            if not createcrash:
                await self.bot.reply_to_msg(ctx.message, "Understood. Aborting")
                return
            
            await self.addcrash(ctx, *args if args else crashname)
            return
            
        change_crash, _ = await Helper.waitResponse(self.bot, ctx.message, "Do you want to change the crash to match ?")
        try:
            change_crash = convert_to_bool(change_crash)
        except ValueError:
            await self.bot.reply_to_msg(ctx.message, "Invalid bool string")
            return
        
        if change_crash:
            crash, _ = await Helper.waitResponse(self.bot, ctx.message, "What is the regular expression to match in the logs ?")
        
        change_response, _ = await Helper.waitResponse(self.bot, ctx.message,"Do you want to change the response ?")
        try:
            change_response = convert_to_bool(change_response)
        except ValueError:
            await self.bot.reply_to_msg(ctx.message, "Invalid bool string")
            return
        
        if change_response:
            response, _ = await Helper.waitResponse(self.bot, ctx.message, "What response do you want it to provide? Responding with a command will make the response that command")
        
        if change_crash:
            results[0].crash = crash
        if change_response:
            results[0].response = response
        await self.bot.reply_to_msg(ctx.message, "Crash '" + crashname + "' modified !")

    @add.command(name="dialogflow")
    async def adddialogflow(self, ctx, id: str, response: typing.Union[bool, str], has_followup: bool, *args):
        if len(args) == 0:
            data = False
        else:
            data = {arg.split('=')[0]: arg.split('=')[1] for arg in args}

        if response == True:
            await self.bot.reply_to_msg(ctx.message,
                                        "Response should be a string or False (use the response from dialogflow)")
            return

        if config.Dialogflow.fetch(id, data):
            should_delete, attachment = await Helper.waitResponse(self.bot, ctx.message,
                                                      "Dialogflow response with this parameters already exists. Do you want to replace it? (Yes/No)")
            should_delete = should_delete.lower()
            if should_delete == 'no' or should_delete == 'n' or should_delete == 'false':
                return
            await self.removedialogflow(ctx, id, *args)

        config.Dialogflow(intent_id=id, data=data, response=response, has_followup=has_followup)
        await self.bot.reply_to_msg(ctx.message,
                                    "Dialogflow response for '" + id + "' (" + (
                                        json.dumps(data) if data else 'any data') + ") added!")

    @remove.command(name="dialogflow")
    async def removedialogflow(self, ctx, id: str, *args):
        if len(args) == 0:
            data = False
        else:
            data = {arg.split('=')[0]: arg.split('=')[1] for arg in args}

        if not config.Dialogflow.fetch(id, data):
            await self.bot.reply_to_msg(ctx.message, "Couldn't find the dialogflow reply")
            return

        config.Dialogflow.deleteBy(intent_id=id, data=data)
        await self.bot.reply_to_msg(ctx.message, "Dialogflow reply deleted")

    @add.command(name="dialogflowChannel")
    async def adddialogflowchannel(self, ctx, *args):
        if ctx.message.channel_mentions:
            id = int(ctx.message.channel_mentions[0].id)
        else:
            if len(args) > 0:
                id = int(args[0])
            else:
                id, attachment = await Helper.waitResponse(self.bot, ctx.message, "What is the ID for the channel? e.g. "
                                                                          "``709509235028918334``")
                id = int(id)
        if config.DialogflowChannels.fetch(id):
            await self.bot.reply_to_msg(ctx.message, "This channel is already a dialogflow channel")
            return

        config.DialogflowChannels(channel_id=id)
        await self.bot.reply_to_msg(ctx.message, "Dialogflow channel " + self.bot.get_channel(id).mention + " added!")

    @remove.command(name="dialogflowChannel")
    async def removedialogflowchannel(self, ctx, *args):
        if ctx.message.channel_mentions:
            id = int(ctx.message.channel_mentions[0].id)
        else:
            if len(args) > 0:
                id = int(args[0])
            else:
                id, attachment = await Helper.waitResponse(self.bot, ctx.message, "What is the ID for the channel? e.g. "
                                                                          "``709509235028918334``")
                id = int(id)
        index = 0
        if config.DialogflowChannels.fetch(id):
            config.DialogflowChannels.deleteBy(channel_id=id)
            await self.bot.reply_to_msg(ctx.message, "Dialogflow Channel removed!")
        else:
            await self.bot.reply_to_msg(ctx.message, "Dialogflow channel could not be found!")

    @add.command(name="dialogflowRole")
    async def adddialogflowrole(self, ctx, *args):
        if ctx.message.role_mentions:
            id = int(ctx.message.role_mentions[0].id)
        else:
            if len(args) > 0:
                id = int(args[0])
            else:
                id, attachment = await Helper.waitResponse(self.bot, ctx.message, "What is the ID for the role? e.g. "
                                                                          "``809710343533232129``")
                id = int(id)

        if config.DialogflowExceptionRoles.fetch(id):
            await self.bot.reply_to_msg(ctx.message, "This role is already a dialogflow exception role")
            return

        config.DialogflowExceptionRoles(role_id=id)
        await self.bot.reply_to_msg(ctx.message, "Dialogflow role " + ctx.message.guild.get_role(id).name + " added!")

    @remove.command(name="dialogflowRole")
    async def removedialogflowrole(self, ctx, *args):
        if ctx.message.role_mentions:
            id = int(ctx.message.role_mentions[0].id)
        else:
            if len(args) > 0:
                id = int(args[0])
            else:
                id, attachment = await Helper.waitResponse(self.bot, ctx.message, "What is the ID for the role? e.g. "
                                                                          "``809710343533232129``")
                id = int(id)
        index = 0
        if config.DialogflowExceptionRoles.fetch(id):
            config.DialogflowExceptionRoles.deleteBy(role_id=id)
            await self.bot.reply_to_msg(ctx.message, "Dialogflow role removed!")
        else:
            await self.bot.reply_to_msg(ctx.message, "Dialogflow role could not be found!")

    @add.command(name="rank_role")
    async def adddrankrole(self, ctx, *args):
        if ctx.message.role_mentions:
            id = int(ctx.message.role_mentions[0].id)
            if args:
                rank = int(args[0])
        else:
            if len(args) > 0:
                id = int(args[0])
                if len(args) > 1:
                    rank = int(args[1])
                else:
                    rank = int(
                        await Helper.waitResponse(self.bot, ctx.message, "What is the rank for the role ? e.g. 5"))
            else:
                id, attachment = await Helper.waitResponse(self.bot, ctx.message, "What is the ID for the role? e.g. "
                                                                          "``809710343533232129``")
                id = int(id)
                rank, attachment = await Helper.waitResponse(self.bot, ctx.message, "What is the rank for the role ? e.g. 5")
                rank = int(rank)

        if config.DialogflowExceptionRoles.fetch(id):
            await self.bot.reply_to_msg(ctx.message, "This role is already a rank role")
            return

        config.RankRoles(role_id=id, rank=rank)
        await self.bot.reply_to_msg(ctx.message, "Rank role " + ctx.message.guild.get_role(id).name + " added!")

    @remove.command(name="rank_role")
    async def removerankrole(self, ctx, *args):
        if ctx.message.role_mentions:
            id = int(ctx.message.role_mentions[0].id)
        else:
            if len(args) > 0:
                id = int(args[0])
            else:
                id, attachment = await Helper.waitResponse(self.bot, ctx.message, "What is the ID for the role? e.g. "
                                                                          "``809710343533232129``")
                id = int(id)

        if config.RankRoles.fetch_by_role(id):
            config.RankRoles.deleteBy(role_id=id)
            await self.bot.reply_to_msg(ctx.message, "Rank role removed!")
        else:
            await self.bot.reply_to_msg(ctx.message, "Rank role could not be found!")

    @set.command(name="NLP_state")
    async def setNLPstate(self, ctx, *args):
        if len(args) > 0:
            data = args[0]
            try:
                enabled = convert_to_bool(data)
            except ValueError:
                await self.bot.reply_to_msg(ctx.message, "Invalid bool string")
                return
            if not enabled:
                config.Misc.change("dialogflow_state", False)
                await self.bot.reply_to_msg(ctx.message, "The NLP is now off !")
            else:
                config.Misc.change("dialogflow_state", True)
                await self.bot.reply_to_msg(ctx.message, "The NLP is now on !")
        else:
            config.Misc.change("dialogflow_state", config.Misc.fetch("dialogflow_state"))

    @set.command(name="NLP_debug")
    async def setNLPdebug(self, ctx, *args):
        if len(args) > 0:
            data = args[0]
            try:
                enabled = convert_to_bool(data)
            except ValueError:
                await self.bot.reply_to_msg(ctx.message, "Invalid bool string")
                return
            if not enabled:
                config.Misc.change("dialogflow_debug_state", False)
                await self.bot.reply_to_msg(ctx.message, "The NLP debugging mode is now off !")
            else:
                config.Misc.change("dialogflow_debug_state", True)
                await self.bot.reply_to_msg(ctx.message, "The NLP debugging mode is now on !")
        else:
            config.Misc.change("dialogflow_debug_state", not config.Misc.fetch("dialogflow_debug_state"))

    @set.command(name="welcome_message")
    async def setwelcomemessage(self, ctx, *args):
        if len(args) > 0:
            data = " ".join(args)
        else:
            data, attachment = await Helper.waitResponse(self.bot, ctx.message, "What should the welcome message be ? (Anything "
                                                                    "under 10 characters will completely disable the "
                                                                    "mesage)")
        if len(data) < 10:
            config.Misc.change("welcome_message", "")
            await self.bot.reply_to_msg(ctx.message, "The welcome message is now disabled")
        else:
            config.Misc.change("welcome_message", data)
            await self.bot.reply_to_msg(ctx.message, "The welcome message has been changed !")

    @set.command(name="latest_info")
    async def setlatestinfo(self, ctx, *args):
        if len(args) > 0:
            data = " ".join(args)
        else:
            data, attachment = await Helper.waitResponse(self.bot, ctx.message, "What should the welcome message be ? (Anything "
                                                                    "under 10 characters will completely disable the "
                                                                    "mesage)")
        if len(data) < 10:
            config.Misc.change("latest_info", "")
            await self.bot.reply_to_msg(ctx.message, "The latest info message is now disabled")
        else:
            config.Misc.change("latest_info", data)
            await self.bot.reply_to_msg(ctx.message, "The latest info message has been changed !")

    @commands.check(mod_only)
    @set.command(name="base_rank_value")
    async def setbaserankvalue(self, ctx, *args):
        if len(args) > 0:
            data = args[0]
        else:
            data, attachment = await Helper.waitResponse(self.bot, ctx.message,
                                             "What should be the rank value of the first rank ? e.g. '300'")
        data = int(data)

        config.Misc.change("base_rank_value", data)
        await self.bot.reply_to_msg(ctx.message, "The base rank value has been changed !")

    @commands.check(mod_only)
    @set.command(name="rank_value_multiplier")
    async def setrankvaluemultiplier(self, ctx, *args):
        if len(args) > 0:
            data = args[0]
        else:
            data, attachment = await Helper.waitResponse(self.bot, ctx.message,
                                             "By how much should the rank value be multiplied from one rank to the "
                                             "next ? e.g. '1.2'")
        data = float(data)

        config.Misc.change("rank_value_multiplier", data)
        await self.bot.reply_to_msg(ctx.message, "The rank value multiplier has been changed !")

    @commands.check(mod_only)
    @set.command(name="xp_gain_value")
    async def setxpgainvalue(self, ctx, *args):
        if len(args) > 0:
            data = args[0]
        else:
            data, attachment = await Helper.waitResponse(self.bot, ctx.message,
                                             "How much xp should someone get for each message ? e.g '1'")
        data = int(data)

        config.Misc.change("xp_gain_value", data)
        await self.bot.reply_to_msg(ctx.message, "The xp gain value has been changed !")

    @commands.check(mod_only)
    @set.command(name="xp_gain_delay")
    async def setxpgaindelay(self, ctx, *args):
        if len(args) > 0:
            data = args[0]
        else:
            data, attachment = await Helper.waitResponse(self.bot, ctx.message,
                                             "How long should the xp gain delay be ? e.g '5' will mean that if "
                                             "someone sends a message and one again 4 seconds later, the second one "
                                             "will not give any xp")
        data = int(data)

        config.Misc.change("xp_gain_delay", data)
        await self.bot.reply_to_msg(ctx.message, "The xp gain delay has been changed !")

    @set.command(name="levelling_state")
    async def setlevellingstate(self, ctx, *args):
        if len(args) > 0:
            data = args[0]
            try:
                enabled = convert_to_bool(data)
            except ValueError:
                await self.bot.reply_to_msg(ctx.message, "Invalid bool string")
                return
            if not enabled:
                config.Misc.change("levelling_state", False)
                await self.bot.reply_to_msg(ctx.message, "The levelling system is now inactive !")
            else:
                config.Misc.change("levelling_state", True)
                await self.bot.reply_to_msg(ctx.message, "The levelling system is now active !")
        else:
            config.Misc.change("levelling_state", not config.Misc.fetch("levelling_state"))

    @commands.check(mod_only)
    @set.command(name="main_guild")
    async def setmainguild(self, ctx, *args):
        config.Misc.change("main_guild_id", ctx.guild.id)
        await self.bot.reply_to_msg(ctx.message, "The main guild is now this one !")

    @xp.command(name="give")
    async def xpgive(self, ctx, *args):
        if ctx.message.mentions:
            id = int(ctx.message.mentions[0].id)
        else:
            if len(args) > 0:
                id = int(args[0])
            else:
                id, attachment = await Helper.waitResponse(self.bot, ctx.message,
                                                   "What is the ID of the person you want to give xp to ? e.g. "
                                                   "``809710343533232129``")
                id = int(id)
        if len(args) > 1:
            amount = int(args[1])
        else:
            amount, attachment = await Helper.waitResponse(self.bot, ctx.message,
                                                   "How much xp do you want to give ? e.g. "
                                                   "``809710343533232129``")
            amount = int(amount)
        user = ctx.guild.get_member(id)
        if not user:
            self.bot.reply_to_msg(ctx.message, "Sorry, I was unable to get the member with ID {}".format(id))
            return
        profile = levelling.UserProfile(id, ctx.guild, self.bot)
        await profile.give_xp(amount)
        await self.bot.reply_to_msg(ctx.message,
                                    "Gave {} xp to {}. They are now rank {} ({} xp)".format(amount, user.name,
                                                                                            profile.rank,
                                                                                            profile.xp_count))

    @xp.command(name="take")
    async def xptake(self, ctx, *args):
        if ctx.message.mentions:
            id = int(ctx.message.mentions[0].id)
        else:
            if len(args) > 0:
                id = int(args[0])
            else:
                id, attachment = await Helper.waitResponse(self.bot, ctx.message,
                                                   "What is the ID of the person you want to take xp from ? e.g. "
                                                   "``809710343533232129``")
                id = int(id)
        if len(args) > 1:
            amount = int(args[1])
        else:
            amount, attachment = await Helper.waitResponse(self.bot, ctx.message,
                                                   "How much xp do you want to take ? e.g. "
                                                   "``809710343533232129``")
            amount = int(amount)
        user = ctx.guild.get_member(id)
        if not user:
            self.bot.reply_to_msg(ctx.message, "Sorry, I was unable to get the member with ID {}".format(id))
            return
        profile = levelling.UserProfile(id, ctx.guild, self.bot)
        await profile.take_xp(amount)
        await self.bot.reply_to_msg(ctx.message,
                                    "Took {} xp from {}. They are now rank {} ({} xp)".format(amount, user.name,
                                                                                              profile.rank,
                                                                                              profile.xp_count))

    @xp.command(name="multiplier")
    async def xpmultiplier(self, ctx, *args):
        if ctx.message.mentions:
            id = int(ctx.message.mentions[0].id)
        else:
            if len(args) > 0:
                id = int(args[0])
            else:
                id, attachment = await Helper.waitResponse(self.bot, ctx.message,
                                                   "What is the ID of the person for which you want to set their xp "
                                                   "multiplier e.g. ``809710343533232129``")
                id = int(id)

        if len(args) > 1:
            amount = int(args[1])
        else:
            amount, attachment = await Helper.waitResponse(self.bot, ctx.message,
                                                   "At how much should the xp multiplier be set ? e.g. "
                                                   "``809710343533232129``")
            amount = int(amount)

        user = ctx.guild.get_member(id)
        if not user:
            self.bot.reply_to_msg(ctx.message, "Sorry, I was unable to get the member with ID {}".format(id))
            return
        DB_user = config.Users.create_if_missing(user)
        if amount < 0:
            amount = 0
        DB_user.xp_multiplier = amount

        if amount == 0:
            await self.bot.reply_to_msg(ctx.message, "{} has been banned from xp gain".format(user.name))
        else:
            await self.bot.reply_to_msg(ctx.message, "Set {}'s xp multiplier to {}".format(user.name, amount))

    @xp.command(name="set")
    async def xpset(self, ctx, *args):
        if ctx.message.mentions:
            id = int(ctx.message.mentions[0].id)
        else:
            if len(args) > 0:
                id = int(args[0])
            else:
                id, attachment = await Helper.waitResponse(self.bot, ctx.message,
                                                   "What is the ID of the person for which you want to set their xp "
                                                   "count e.g. ``809710343533232129``")
                id = int(id)

        if len(args) > 1:
            amount = int(args[1])
        else:
            amount, attachment = await Helper.waitResponse(self.bot, ctx.message,
                                                   "At how much should the xp count be set ? e.g. "
                                                   "``809710343533232129``")
            amount = int(amount)
        user = ctx.guild.get_member(id)
        if not user:
            self.bot.reply_to_msg(ctx.message, "Sorry, I was unable to get the member with ID {}".format(id))
            return
        profile = levelling.UserProfile(id, ctx.guild, self.bot)
        await profile.set_xp(amount)
        await self.bot.reply_to_msg(ctx.message,
                                    "Set {}'s xp count to {}. They are now rank {}".format(user.name, amount,
                                                                                           profile.rank,
                                                                                           profile.xp_count))

    @commands.command()
    @commands.check(t3_only)
    async def saveconfig(self, ctx, *args):
        sent = self.bot.send_DM(ctx.author, content="WARNING : THIS IS OUTDATED, config is now managed via the DB",
                                file=discord.File(open("../config/config.json", "r"),
                                                  filename="config.json"))
        if sent:
            await ctx.message.add_reaction("✅")
        else:
            await self.bot.reply_to_msg(ctx.message,
                                        "I was unable to send you a direct message. Please check your discord "
                                        "settings regarding those !")

    @commands.command()
    @commands.check(mod_only)
    async def engineers(self, ctx, *args):
        if ctx.message.channel_mentions:
            id = int(ctx.message.channel_mentions[0].id)
        else:
            if args:
                id = int(args[0])
            else:
                id, attachment = await Helper.waitResponse(self.bot, ctx.message,
                                                   "What is the ID for the channel? e.g. ``709509235028918334``")
                id = int(id)
        config.Misc.change("filter_channel", id)
        await self.bot.reply_to_msg(ctx.message,
                                    "The filter channel for the engineers is now " + self.bot.get_channel(
                                        int(id)).mention + "!")

    @commands.command()
    @commands.check(mod_only)
    async def moderators(self, ctx, *args):
        if ctx.message.channel_mentions:
            id = int(ctx.message.channel_mentions[0].id)
        else:
            if args:
                id = int(args[0])
            else:
                id, attachment = await Helper.waitResponse(self.bot, ctx.message,
                                                   "What is the ID for the channel? e.g. ``709509235028918334``")
                id = int(id)
        config.Misc.change("mod_channel", id)
        await self.bot.reply_to_msg(ctx.message,
                                    "The filter channel for the moderators is now " + self.bot.get_channel(
                                        int(id)).mention + "!")

    @commands.command()
    @commands.check(mod_only)
    async def githook(self, ctx, *args):
        if ctx.message.channel_mentions:
            id = int(ctx.message.channel_mentions[0].id)
        else:
            if args:
                id = int(args[0])
            else:
                id, attachment = await Helper.waitResponse(self.bot, ctx.message,
                                                   "What is the ID for the channel? e.g. ``709509235028918334``")
                id = int(id)
        config.Misc.change("githook_channel", id)
        await self.bot.reply_to_msg(ctx.message,
                                    "The channel for the github hooks is now " + self.bot.get_channel(
                                        int(id)).mention + "!")

    @commands.command()
    @commands.check(mod_only)
    async def prefix(self, ctx, *args):
        if not args:
            await self.bot.reply_to_msg(ctx.message, "Please specify a prefix")
            return
        config.Misc.change("prefix", args[0])
        self.bot.command_prefix = args[0]
        await self.bot.reply_to_msg(ctx.message, "Prefix changed to " + args[0])
