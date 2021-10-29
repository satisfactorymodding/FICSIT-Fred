import logging
import re
import discord
import asyncio
import config
from cogs import levelling
from libraries import createembed, helper
import json
from algoliasearch.search_client import SearchClient
import io
import typing
import aiohttp

from discord.ext import commands
from discord.ext.commands.view import StringView


def extract_target_type_from_converter_param(missing_argument: commands.MissingRequiredArgument):
    s = str(missing_argument)

    if ":" not in s:
        return s, None

    split = s.split(": ")
    converter_type = split[1]
    missing_argument_name = split[0]

    target_type = converter_type.split(".")[-1].strip("Converter")
    return missing_argument_name, target_type


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
        elif isinstance(error, commands.MissingRequiredArgument):
            missing_argument_name, target_type = extract_target_type_from_converter_param(error.param)
            output = f"You are missing at least one parameter for this command: '{missing_argument_name}'"
            if target_type:
                output += f" of type '{target_type}'"
            await ctx.send(output)
        elif isinstance(error, commands.CheckFailure):
            await ctx.send("Sorry, but you do not have enough permissions to do this.")
        elif isinstance(error, commands.errors.CommandInvokeError):
            # use error.original here because error is discord.ext.commands.errors.CommandInvokeError
            if isinstance(error.original, asyncio.exceptions.TimeoutError):
                pass  # this is raised to escape a bunch of value passing if timed out, but should not raise big errors.
        else:
            await ctx.send("I encountered an error while trying to call this command. Feyko has been notified")
            raise error

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not self.bot.is_running():
            return
        self.bot.logger.info("Commands: Processing a message", extra=helper.messagedict(message))
        if message.content.startswith(self.bot.command_prefix):
            name = message.content.lower().lstrip(self.bot.command_prefix).split(" ")[0]
            self.bot.logger.info(f"Commands: Processing the command {name}", extra=helper.messagedict(message))
            if command := config.Commands.fetch(name):
                if content := command['content']:
                    if content.startswith(self.bot.command_prefix):  # for linked aliases of commands like rp<-ff
                        if (lnk_cmd := config.Commands.fetch(command['content'][1:])):
                            command = lnk_cmd

                attachment = None
                if command["attachment"]:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(command["attachment"]) as resp:
                            buff = io.BytesIO(await resp.read())
                            attachment = discord.File(filename=command["attachment"].split("/")[-1], fp=buff)
                args = []
                view = StringView(message.content.lstrip(self.bot.command_prefix))
                view.get_word()  # command name
                while not view.eof:
                    view.skip_ws()
                    args.append(view.get_quoted_word())
                if command["content"] is not None:
                    text = re.sub(
                        r'{(\d+)}',
                        lambda match: args[int(match.group(1))]
                        if int(match.group(1)) < len(args)
                        else '(missing argument)',
                        command["content"]
                    ).replace('{...}', ' '.join(args))
                else:
                    text = None

                await self.bot.reply_to_msg(message, text, file=attachment)
                return

    @commands.command()
    async def version(self, ctx):
        await self.bot.reply_to_msg(ctx.message, self.bot.version)

    @commands.command()
    async def help(self, ctx):
        await self.bot.reply_to_msg(ctx.message, "Sorry, this command is temporarily unavailable")

    @commands.command()
    async def mod(self, ctx, *, mod_name):
        result, desc = await createembed.mod(mod_name, self.bot)
        if result is None:
            await self.bot.reply_to_msg(ctx.message, "No mods found!")
        elif isinstance(result, str):
            await self.bot.reply_to_msg(ctx.message, "multiple mods found")
        else:
            new_message = await self.bot.reply_to_msg(ctx.message, content=None, embed=result)
            if desc:
                await new_message.add_reaction("📋")
                await asyncio.sleep(0.5)

                def check(reaction, user):
                    if reaction.emoji == "📋" and reaction.message.id == new_message.id:
                        return True

                while True:
                    try:
                        r = await self.bot.wait_for('reaction_add', timeout=240.0, check=check)
                        member = r[1]
                        sent = await self.bot.send_DM(member, content=None, embed=createembed.desc(desc))
                        if sent:
                            await new_message.add_reaction("✅")
                        else:
                            await ctx("I was unable to send you a direct message. "
                                      "Please check your discord settings regarding those!")
                    except asyncio.TimeoutError:
                        break

    @commands.command()
    async def docsearch(self, ctx, search):
        client = SearchClient.create('BH4D9OD16A', '53b3a8362ea7b391f63145996cfe8d82')
        index = client.init_index('ficsit')
        query = index.search(search, {'attributesToRetrieve': '*'})
        for hit in query["hits"]:
            if hit["hierarchy"]["lvl0"].endswith("latest"):
                await self.bot.reply_to_msg(ctx.message, f"This is the best result I got from the SMD :\n{hit['url']}")
                return

    @commands.command()
    async def leaderboard(self, ctx):
        query = config.Users.select().orderBy("-xp_count").limit(10)
        results = list(query)
        if not results:
            self.bot.reply_to_msg(ctx.message, "The database was empty. This should NEVER happen")
            return
        data = [dict(name=user.full_name, count_and_rank=dict(count=user.xp_count, rank=user.rank)) for user in results]
        embed = createembed.leaderboard(data)
        await self.bot.reply_to_msg(ctx.message, embed=embed)

    @commands.command()
    async def level(self, ctx, target_user: commands.UserConverter = None):
        if target_user:
            user_id = target_user.id
            user = self.bot.get_user(user_id)
            if not user:
                self.bot.reply_to_msg(ctx.message, f"Sorry, I was unable to find the user with id {user_id}")
                return
        else:
            user = ctx.author
        DB_user = config.Users.create_if_missing(user)
        await self.bot.reply_to_msg(ctx.message, f"{user.name} is level {DB_user.rank} with {DB_user.xp_count} xp")

    @commands.group()
    @commands.check(helper.t3_only)
    async def add(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.bot.reply_to_msg(ctx.message, 'Invalid sub command passed...')
            return

    @commands.group()
    @commands.check(helper.t3_only)
    async def remove(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.bot.reply_to_msg(ctx.message, 'Invalid sub command passed...')
            return

    @commands.group()
    @commands.check(helper.t3_only)
    async def set(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.bot.reply_to_msg(ctx.message, 'Invalid sub command passed...')
            return

    @commands.group()
    @commands.check(helper.t3_only)
    async def modify(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.bot.reply_to_msg(ctx.message, 'Invalid sub command passed...')
            return

    @commands.group()
    @commands.check(helper.mod_only)
    async def xp(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.bot.reply_to_msg(ctx.message, 'Invalid sub command passed...')
            return

    @add.command(name="mediaonly")
    async def add_mediaonly(self, ctx, channel: commands.TextChannelConverter):
        if config.MediaOnlyChannels.fetch(channel.id):
            await self.bot.reply_to_msg(ctx.message, "This channel is already a media only channel")
            return

        config.MediaOnlyChannels(channel_id=channel.id)
        await self.bot.reply_to_msg(ctx.message,
                                    f"Media Only channel {self.bot.get_channel(channel.id).mention} added!")

    @remove.command(name="mediaonly")
    async def remove_mediaonly(self, ctx, channel: commands.TextChannelConverter):
        if not config.MediaOnlyChannels.fetch(channel.id):
            await self.bot.reply_to_msg(ctx.message, "Media Only Channel could not be found!")
            return

        config.MediaOnlyChannels.deleteBy(channel_id=channel.id)
        await self.bot.reply_to_msg(ctx.message,
                                    f"Media Only channel {self.bot.get_channel(channel.id).mention} removed!")

    @add.command(name="command")
    async def add_command(self, ctx, command_name: str.lower, *, response: str = None):
        if config.Commands.fetch(command_name):
            await self.bot.reply_to_msg(ctx.message, "This command already exists!")
            return
        if config.ReservedCommands.fetch(command_name):
            await self.bot.reply_to_msg(ctx.message, "This command name is reserved")
            return

        attachment = ctx.message.attachments[0].url if ctx.message.attachments else None

        if not response and not attachment:
            response, attachment = await self.bot.reply_question(ctx.message,
                                                                 "What should the response be?")

        alias_check = response.partition(self.bot.command_prefix)
        if alias_check[1]:
            msg = f"This will attempt create an alias of `{alias_check[2]}`! Are you sure you want to proceed?"
            if not await self.bot.reply_yes_or_no(ctx.message, msg):
                return

        config.Commands(name=command_name, content=response, attachment=attachment)

        await self.bot.reply_to_msg(ctx.message, f"Command '{command_name}' added!")

    @remove.command(name="command")
    async def remove_command(self, ctx, command_name: str.lower):
        if not (cmd := config.Commands.fetch(command_name)):
            await self.bot.reply_to_msg(ctx.message, "Command could not be found!")
            return

        elif cmd['content'][0] == self.bot.command_prefix:
            delete = await self.bot.reply_yes_or_no(ctx.message,
                                                    f"This command is an alias of `{cmd['content'][1:]}` "
                                                    f"Delete?")
            if not delete:
                return
        config.Commands.deleteBy(name=command_name)

        await self.bot.reply_to_msg(ctx.message, "Command removed!")

    @modify.command(name="command")
    async def modify_command(self, ctx, command_name: str.lower, *, command_response: str = None):
        if config.ReservedCommands.fetch(command_name):
            await self.bot.reply_to_msg(ctx.message, "This command is special and cannot be modified")
            return

        results = list(config.Commands.selectBy(name=command_name))
        if not results:  # this command hasn't been created yet
            try:
                question = "Command could not be found! Do you want to create it?"
                if await self.bot.reply_yes_or_no(ctx.message, question):
                    await self.add_command(ctx, command_name, command_response)
                else:
                    await self.bot.reply_to_msg(ctx.message, "Understood. Aborting")
                return
            except ValueError:
                return

        elif (linked_command := results[0].content)[0] == self.bot.command_prefix:
            try:
                question = f"`{command_name}` is an alias of `{linked_command[1:]}`. Modify original?"
                if (choice := await self.bot.reply_yes_or_no(ctx.message, question)):
                    command_name = linked_command[1:]
                else:
                    await self.bot.reply_to_msg(ctx.message, f"Modifying {command_name}")
            except ValueError:
                return

        if not command_response:
            command_response, attachment = await self.bot.reply_question(ctx.message,
                                                                         "What should the response be?")
        else:
            attachment = ctx.message.attachments.url if ctx.message.attachments else None

        # this just works, don't touch it. trying to use config.Commands.fetch makes a duplicate command.
        results[0].content = command_response
        results[0].attachment = attachment

        await self.bot.reply_to_msg(ctx.message, f"Command '{command_name}' modified!")

    @add.command(name="alias")
    async def add_alias(self, ctx, cmd_to_alias: str.lower, *aliases: str):

        if not (cmd := config.Commands.fetch(cmd_to_alias)):
            await self.bot.reply_to_msg(ctx.message, f"`{cmd_to_alias}` doesn't exist!")
            return

        elif (link := cmd['content'])[0] == self.bot.command_prefix:
            try:
                confirm = await self.bot.reply_question(ctx.message,
                                                        f"`{cmd_to_alias}` is an alias for `{link[1:]}`. "
                                                        f"Add aliases to `{link[1:]}`?")
                if not confirm:
                    await self.bot.reply_to_msg(ctx.message, f"Aborting")
                    return

                else:
                    cmd_to_alias = link[1:]
            except ValueError:
                return

        if not aliases:
            response, _ = await self.bot.reply_question(ctx.message, "Please input aliases, separated by spaces.")
            aliases = response.split(' ')

        link = self.bot.command_prefix + cmd_to_alias
        skipped = set()  # this keeps track of all the aliases that couldn't be added
        for alias in aliases:
            if config.ReservedCommands.fetch(alias):
                await self.bot.reply_to_msg(ctx.message, f"`{alias}` is reserved. This alias will not be made.")
                skipped.add(alias)
                continue

            if cmd := config.Commands.fetch(name=alias):
                if cmd['content'] == link:
                    await self.bot.reply_to_msg(ctx.message, f"`{alias}` was already an alias for `{link}`")
                    skipped.add(alias)
                    continue
                else:
                    try:
                        if await self.bot.reply_yes_or_no(ctx.message, f"`{alias}` is another command! Replace?"):
                            config.Commands.deleteBy(name=alias)
                        else:
                            skipped.add(alias)
                            continue
                    except ValueError:
                        return

            config.Commands(name=alias, content=link, attachment=None)

        aliases_added = list(set(aliases) - skipped)  # aliases_added is aliases without all the skipped aliases
        if aliases_added:
            if (num_aliases := len(aliases_added)) > 1:
                user_info = f"{num_aliases} aliases added for {cmd_to_alias}: {', '.join(aliases_added)}"
            else:
                user_info = f"Alias added for {cmd_to_alias}: {aliases_added[0]}"
        else:
            user_info = "No aliases were added."
        self.bot.logger.info(user_info)
        await self.bot.reply_to_msg(ctx.message, user_info)

    @remove.command(name="alias")
    async def remove_alias(self, ctx, command_name: str.lower):
        if not (cmd := config.Commands.fetch(command_name)):
            await self.bot.reply_to_msg(ctx.message, "Alias could not be found!")
            return
        elif cmd['content'][0] != self.bot.command_prefix:
            await self.bot.reply_to_msg(ctx.message, "This command is not an alias!")
            return
        else:
            config.Commands.deleteBy(name=command_name)

        await self.bot.reply_to_msg(ctx.message, "Alias removed!")

    @add.command(name="crash")
    async def add_crash(self, ctx, crash_name: str.lower, match: str = None, *, response: str = None):
        if config.Crashes.fetch(crash_name):
            await self.bot.reply_to_msg(ctx.message, "A crash with this name already exists")
            return

        if not match:
            match, _ = await self.bot.reply_question(ctx.message, "What should the logs match (regex)?")
        try:
            re.search(match, "test")
        except:
            await self.bot.reply_to_msg(ctx.message,
                                        "The regex isn't valid. Please refer to "
                                        "https://docs.python.org/3/library/re.html for docs on Python's regex library")
            return

        if not response:
            response, _ = await self.bot.reply_question(ctx.message, "What should the response be?")

        config.Crashes(name=crash_name, crash=match, response=response)
        await self.bot.reply_to_msg(ctx.message, "Known crash '" + crash_name + "' added!")

    @remove.command(name="crash")
    async def remove_crash(self, ctx, crash_name: str.lower):
        if not config.Crashes.fetch(crash_name):
            await self.bot.reply_to_msg(ctx.message, "Crash could not be found!")
            return

        config.Crashes.deleteBy(name=crash_name)

        await self.bot.reply_to_msg(ctx.message, "Crash removed!")

    @modify.command(name="crash")
    async def modify_crash(self, ctx, crash_name: str.lower, match: str = None, *, response: str = None):
        query = config.Crashes.selectBy(name=crash_name)
        results = list(query)

        if not results:
            await ctx.send(f"Could not find a crash with name '{crash_name}'. Aborting")
            return

        try:
            if change_crash := await self.bot.reply_yes_or_no(ctx.message, "Do you want to change the crash to match?"):
                match, _ = await self.bot.reply_question(ctx.message,
                                                         "What is the regular expression to match in the logs?")
        except ValueError:
            return

        try:
            if change_response := await self.bot.reply_yes_or_no(ctx.message, "Do you want to change the response?"):
                response, _ = await self.bot.reply_question(ctx.message,
                                                            "What response do you want it to provide? Responding with "
                                                            "a command will make the response that command")
        except ValueError:
            return

        if change_crash:
            results[0].crash = match
        if change_response:
            results[0].response = response
        await self.bot.reply_to_msg(ctx.message, f"Crash '{crash_name}' modified!")

    @add.command(name="dialogflow")
    async def add_dialogflow(self, ctx, intent_id: str, response: typing.Union[bool, str], has_followup: bool, *args):
        if len(args) == 0:
            data = None
        else:
            data = {arg.split('=')[0]: arg.split('=')[1] for arg in args}

        if response is True:
            await self.bot.reply_to_msg(ctx.message,
                                        "Response should be a string or False (use the response from dialogflow)")
            return
        elif response is False:
            response = None

        if config.Dialogflow.fetch(intent_id, data):
            try:
                question = "Dialogflow response with this parameters already exists. Do you want to replace it?"
                if await self.bot.reply_yes_or_no(ctx.message, question):
                    await self.remove_dialogflow(ctx, intent_id, *args)
                else:
                    return
            except ValueError:
                return

        config.Dialogflow(intent_id=intent_id, data=data, response=response, has_followup=has_followup)
        await self.bot.reply_to_msg(ctx.message,
                                    f"Dialogflow response for '{intent_id}' "
                                    f"({json.dumps(data) if data else 'any data'}) added!")

    @remove.command(name="dialogflow")
    async def remove_dialogflow(self, ctx, intent_id: str, *args):
        if len(args) == 0:
            data = None
        else:
            data = {arg.split('=')[0]: arg.split('=')[1] for arg in args}

        if not config.Dialogflow.fetch(intent_id, data):
            await self.bot.reply_to_msg(ctx.message, "Couldn't find the dialogflow reply")
            return

        config.Dialogflow.deleteBy(intent_id=intent_id, data=data)
        await self.bot.reply_to_msg(ctx.message, "Dialogflow reply deleted")

    @add.command(name="dialogflowChannel")
    async def add_dialogflow_channel(self, ctx, channel: commands.TextChannelConverter):
        if config.DialogflowChannels.fetch(channel.id):
            await self.bot.reply_to_msg(ctx.message, "This channel is already a dialogflow channel!")
        else:
            config.DialogflowChannels(channel_id=channel.id)
            await self.bot.reply_to_msg(ctx.message,
                                        f"Dialogflow channel {self.bot.get_channel(channel.id).mention} added!")

    @remove.command(name="dialogflowChannel")
    async def remove_dialogflow_channel(self, ctx, channel: commands.TextChannelConverter):
        if config.DialogflowChannels.fetch(channel.id):
            config.DialogflowChannels.deleteBy(channel_id=channel.id)
            await self.bot.reply_to_msg(ctx.message,
                                        f"Dialogflow Channel {self.bot.get_channel(channel.id).mention} removed!")
        else:
            await self.bot.reply_to_msg(ctx.message, "Dialogflow channel could not be found!")

    @add.command(name="dialogflowRole")
    async def add_dialogflow_role(self, ctx, role: commands.RoleConverter):
        role_id = role.id

        if config.DialogflowExceptionRoles.fetch(role_id):
            await self.bot.reply_to_msg(ctx.message, "This role is already a dialogflow exception role")
            return

        config.DialogflowExceptionRoles(role_id=role_id)
        await self.bot.reply_to_msg(ctx.message, f"Dialogflow role {ctx.message.guild.get_role(role_id).name} added!")

    @remove.command(name="dialogflowRole")
    async def remove_dialogflow_role(self, ctx, role: commands.RoleConverter):
        role_id = role.id

        if config.DialogflowExceptionRoles.fetch(role_id):
            config.DialogflowExceptionRoles.deleteBy(role_id=role_id)
            await self.bot.reply_to_msg(ctx.message, "Dialogflow role removed!")
        else:
            await self.bot.reply_to_msg(ctx.message, "Dialogflow role could not be found!")

    @add.command(name="level_role")
    async def add_level_role(self, ctx, role: commands.RoleConverter, rank: int):
        role_id = role.id

        if config.DialogflowExceptionRoles.fetch(role_id):
            await self.bot.reply_to_msg(ctx.message, "This role is already a level role")
            return

        config.RankRoles(role_id=role_id, rank=rank)
        await self.bot.reply_to_msg(ctx.message, "level role " + ctx.message.guild.get_role(role_id).name + " added!")

    @remove.command(name="level_role")
    async def remove_level_role(self, ctx, role: commands.RoleConverter):
        role_id = role.id

        if config.RankRoles.fetch_by_role(role_id):
            config.RankRoles.deleteBy(role_id=role_id)
            await self.bot.reply_to_msg(ctx.message, "level role removed!")
        else:
            await self.bot.reply_to_msg(ctx.message, "level role could not be found!")

    @set.command(name="NLP_state")
    async def set_NLP_state(self, ctx, enabled: bool):
        if not enabled:
            config.Misc.change("dialogflow_state", False)
            await self.bot.reply_to_msg(ctx.message, "The NLP is now off!")
        else:
            config.Misc.change("dialogflow_state", True)
            await self.bot.reply_to_msg(ctx.message, "The NLP is now on!")

    @set.command(name="NLP_debug")
    async def set_NLP_debug(self, ctx, enabled: bool):
        if not enabled:
            config.Misc.change("dialogflow_debug_state", False)
            await self.bot.reply_to_msg(ctx.message, "The NLP debugging mode is now off!")
        else:
            config.Misc.change("dialogflow_debug_state", True)
            await self.bot.reply_to_msg(ctx.message, "The NLP debugging mode is now on!")

    @set.command(name="welcome_message")
    async def set_welcome_message(self, ctx, welcome_message: str):
        if len(welcome_message) < 10:
            config.Misc.change("welcome_message", "")
            await self.bot.reply_to_msg(ctx.message, "The welcome message is now disabled")
        else:
            config.Misc.change("welcome_message", welcome_message)
            await self.bot.reply_to_msg(ctx.message, "The welcome message has been changed")

    @set.command(name="latest_info")
    async def set_latest_info(self, ctx, latest_info: str):
        if len(latest_info) < 10:
            config.Misc.change("latest_info", "")
            await self.bot.reply_to_msg(ctx.message, "The latest info message is now disabled")
        else:
            config.Misc.change("latest_info", latest_info)
            await self.bot.reply_to_msg(ctx.message, "The latest info message has been changed!")

    @commands.check(helper.mod_only)
    @set.command(name="base_level_value")
    async def set_base_rank_value(self, ctx, base_level_value: int):
        config.Misc.change("base_level_value", base_level_value)
        await self.bot.reply_to_msg(ctx.message, "The base level value has been changed!")

    @commands.check(helper.mod_only)
    @set.command(name="level_value_multiplier")
    async def set_rank_value_multiplier(self, ctx, level_value_multiplier: float):
        config.Misc.change("level_value_multiplier", level_value_multiplier)
        await self.bot.reply_to_msg(ctx.message, "The level value multiplier has been changed!")

    @commands.check(helper.mod_only)
    @set.command(name="xp_gain_value")
    async def set_xp_gain_value(self, ctx, xp_gain_value: int):
        config.Misc.change("xp_gain_value", xp_gain_value)
        await self.bot.reply_to_msg(ctx.message, "The xp gain value has been changed!")

    @commands.check(helper.mod_only)
    @set.command(name="xp_gain_delay")
    async def set_xp_gain_delay(self, ctx, xp_gain_delay: int):
        config.Misc.change("xp_gain_delay", xp_gain_delay)
        await self.bot.reply_to_msg(ctx.message, "The xp gain delay has been changed!")

    @set.command(name="levelling_state")
    async def set_levelling_state(self, ctx, enabled: bool):
        if not enabled:
            config.Misc.change("levelling_state", False)
            await self.bot.reply_to_msg(ctx.message, "The levelling system is now inactive!")
        else:
            config.Misc.change("levelling_state", True)
            await self.bot.reply_to_msg(ctx.message, "The levelling system is now active!")

    @commands.check(helper.mod_only)
    @set.command(name="main_guild")
    async def set_main_guild(self, ctx, guild_id: int = None):
        if not guild_id:
            guild_id = ctx.guild.id
        config.Misc.change("main_guild_id", guild_id)
        await self.bot.reply_to_msg(ctx.message, "The main guild is now this one!")

    @xp.command(name="give")
    async def xp_give(self, ctx, target: commands.UserConverter, amount: float):
        profile = levelling.UserProfile(target.id, ctx.guild, self.bot)
        if amount < 0:
            await self.bot.reply_to_msg(ctx.message,
                                        f"<:thonk:836648850377801769> attempt to give a negative\n"
                                        f"Did you mean `{self.bot.command_prefix}xp take`?")
        else:
            await profile.give_xp(amount)
            await self.bot.reply_to_msg(ctx.message,
                                        f"Gave {amount} xp to {target.name}. "
                                        f"They are now rank {profile.rank} ({profile.xp_count} xp)")

    @xp.command(name="take")
    async def xp_take(self, ctx, target: commands.UserConverter, amount: float):
        profile = levelling.UserProfile(target.id, ctx.guild, self.bot)
        if amount < 0:
            await self.bot.reply_to_msg(ctx.message,
                                        f"<:thonk:836648850377801769> attempt to take away a negative\n"
                                        f"Did you mean `{self.bot.command_prefix}xp give`?")
            return

        if not await profile.take_xp(amount):
            await self.bot.reply_to_msg(ctx.message, "Cannot take more xp that this user has!")
        else:
            await self.bot.reply_to_msg(ctx.message,
                                        f"Took {amount} xp from {target.name}. "
                                        f"They are now rank {profile.rank} ({profile.xp_count} xp)")

    @xp.command(name="multiplier")
    async def xp_multiplier(self, ctx, target: commands.UserConverter, multiplier: float):
        DB_user = config.Users.create_if_missing(target)
        amount = 0 if multiplier < 0 else multiplier  # no negative gain, thank you
        DB_user.xp_multiplier = amount

        if amount == 0:
            await self.bot.reply_to_msg(ctx.message, f"{target.name} has been banned from xp gain")
        else:
            await self.bot.reply_to_msg(ctx.message, f"Set {target.name}'s xp multiplier to {amount}")

    @xp.command(name="set")
    async def xp_set(self, ctx, target: commands.UserConverter, amount: float):
        profile = levelling.UserProfile(target.id, ctx.guild, self.bot)

        if amount < 0:
            await self.bot.reply_to_msg(ctx.message, 'Negative numbers for xp are not allowed!')
        else:
            await profile.set_xp(amount)
            await self.bot.reply_to_msg(ctx.message,
                                        f"Set {target.name}'s xp count to {amount}. "
                                        f"They are now rank {profile.rank} ({profile.xp_count} xp)")

    @commands.command()
    @commands.check(helper.mod_only)
    async def set_git_hook_channel(self, ctx, channel: commands.TextChannelConverter):
        config.Misc.change("githook_channel", channel.id)
        await self.bot.reply_to_msg(ctx.message,
                                    f"The channel for the github hooks is now "
                                    f"{self.bot.get_channel(channel.id).mention}!")

    @commands.command()
    @commands.check(helper.mod_only)
    async def prefix(self, ctx, *, prefix: str):
        config.Misc.change("prefix", prefix)
        self.bot.command_prefix = prefix
        await self.bot.reply_to_msg(ctx.message, f"Prefix changed to {prefix}.")
