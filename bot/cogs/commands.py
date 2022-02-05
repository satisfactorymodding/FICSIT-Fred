from __future__ import annotations

import asyncio
import io
import json
import logging
import re

import nextcord
from algoliasearch.search_client import SearchClient
from nextcord.ext import commands
from nextcord.ext.commands.view import StringView

import config
from cogs import levelling
from libraries import createembed, common, fred_help


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
        self.logger = logging.Logger("COMMANDS")

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        # We get an error about commands being found when using "runtime" commands, so we have to ignore that
        self.logger.error(f"Caught {error!r}, {dir(error)}")
        if isinstance(error, commands.CommandNotFound):
            command = ctx.message.content.lower().lstrip(self.bot.command_prefix).split(" ")[0]
            if config.Commands.fetch(command):
                return
            self.logger.warning("Invalid command attempted")
            return
        elif isinstance(error, commands.MissingRequiredArgument):
            self.logger.info("Successfully deferred error of missing required argument")
            missing_argument_name, target_type = extract_target_type_from_converter_param(error.param)
            output = f"You are missing at least one parameter for this command: '{missing_argument_name}'"
            if target_type:
                output += f" of type '{target_type}'"
            await ctx.reply(output)
            return
        elif isinstance(error, commands.BadArgument):
            self.logger.info("Successfully deferred error of bad argument")
            _, target_type, _, missing_argument_name, *_ = str(error).split('"')
            output = f"At least one parameter for this command was entered incorrectly: '{missing_argument_name}'"
            if target_type:
                output += f" of type '{target_type}'"
            await ctx.reply(output)
            return
        elif isinstance(error, commands.CheckFailure):
            self.logger.info("Successfully deferred error af insufficient permissions")
            await ctx.reply("Sorry, but you do not have enough permissions to do this.")
            return
        elif isinstance(error, commands.errors.CommandInvokeError):
            self.logger.info("Deferring error of command invocation")
            # use error.original here because error is nextcord.ext.commands.errors.CommandInvokeError
            if isinstance(error.original, asyncio.exceptions.TimeoutError):
                self.logger.info("Handling command response timeout gracefully")
                # this is raised to escape a bunch of value passing if timed out, but should not raise big errors.
                return

        await ctx.send("I encountered an error while trying to call this command. Feyko has been notified")
        raise (error.original if hasattr(error, 'original') else error)

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if message.author.bot or not self.bot.is_running():
            return

        prefix = self.bot.command_prefix
        self.logger.info("Processing a message", extra=common.message_info(message))
        if message.content.startswith(prefix):
            name = message.content.lower().lstrip(prefix).split(" ")[0]
            self.logger.info(f"Processing the command {name}", extra=common.message_info(message))
            if command := config.Commands.fetch(name):
                if (
                        (content := command['content'])
                        and content.startswith(prefix)  # for linked aliases of commands like ff->rp
                        and (linked_command := config.Commands.fetch(command['content'].lstrip(prefix)))
                ):
                    command = linked_command

                attachment = None
                if command["attachment"]:
                    async with self.bot.web_session.get(command["attachment"]) as resp:
                        buff = io.BytesIO(await resp.read())
                        attachment = nextcord.File(filename=command["attachment"].split("/")[-1], fp=buff)
                args = []
                view = StringView(message.content.lstrip(prefix))
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
    async def version(self, ctx: commands.Context):
        """Usage: `version`
        Response: Fred's current version
        Notes: Command is a useful is-alive check"""
        await self.bot.reply_to_msg(ctx.message, self.bot.version)

    @commands.group()
    async def help(self, ctx: commands.Context) -> None:
        """[Help Commands!](https://www.youtube.com/watch?v=2Q_ZzBGPdqE)
        Usage: `help [commands/crash(es)/special/media_only/webhooks] [page: int/name: str]`
        Response: Information about what you requested"""
        if ctx.invoked_subcommand is None:
            await self.help_special(ctx, name='help')
            return

    async def _send_help(self, ctx: commands.Context, **kwargs):
        if not await self.bot.checked_DM(ctx.author, **kwargs):
            await ctx.reply("Help commands only work in DMs to avoid clutter. "
                            "You have either disabled server DMs or indicated that you do not wish for Fred to DM you."
                            "Please enable both of these if you want to receive messages.")

    @help.command(name='commands')
    async def help_commands(self, ctx: commands.Context, page: int = None) -> None:
        """[Help Commands!](https://www.youtube.com/watch?v=2Q_ZzBGPdqE)
        Usage: `help commands [page: int]`
        Response: Shows a table of all commands at the page specified"""
        if page is None:
            response = fred_help.commands()
        elif page < 1:
            response = fred_help.FredHelpEmbed("Bad input", "No negative/zero indices! >:(")
            response.set_footer(text="y r u like dis")
        else:
            response = fred_help.commands(index=page - 1)
        await self._send_help(ctx, embed=response)

    @help.command(name='webhooks')
    async def help_webhooks(self, ctx: commands.Context) -> None:
        """[Help Commands!](https://www.youtube.com/watch?v=2Q_ZzBGPdqE)
        Usage: `help webhooks`
        Response: Info about webhooks"""
        response = fred_help.git_webhooks()
        await self._send_help(ctx, embed=response)

    @help.command(name='crashes')
    async def help_crashes(self, ctx: commands.Context, page: int = None) -> None:
        """[Help Commands!](https://www.youtube.com/watch?v=2Q_ZzBGPdqE)
        Usage: `help crashes [page: int]`
        Response: Shows a table of all crashes at the page specified"""
        if page is None:
            response = fred_help.crashes()
        elif page < 1:
            response = fred_help.FredHelpEmbed("Bad input", "No negative/zero indices! >:(")
            response.set_footer(text="y r u like dis")
        else:
            response = fred_help.crashes(index=page - 1)
        await self._send_help(ctx, embed=response)

    @help.command(name='crash')
    async def help_crash(self, ctx: commands.Context, *, name: str = None) -> None:
        """[Help Commands!](https://www.youtube.com/watch?v=2Q_ZzBGPdqE)
        Usage: `help crash [name: str]`
        Response: Shows info about the crash specified"""
        if name is None:
            response = fred_help.crashes()
        elif name.isnumeric():
            response = fred_help.FredHelpEmbed("Bad input", f"Did you mean `help crashes {name}`?")
        else:
            response = fred_help.specific_crash(name=name)
        await self._send_help(ctx, embed=response)

    @help.command(name='special')
    async def help_special(self, ctx: commands.Context, *, name: str = None) -> None:
        """[Help Commands!](https://www.youtube.com/watch?v=2Q_ZzBGPdqE)
        Usage: `help special [name: str]`
        Response: Shows info about the special command specified, or all special commands if none is given"""
        if name:
            response = fred_help.specific_special(self, name)
        else:
            response = fred_help.all_special_commands(self)

        await self._send_help(ctx, embed=response)

    @help.command(name='media_only')
    async def help_media_only(self, ctx: commands.Context) -> None:
        """[Help Commands!](https://www.youtube.com/watch?v=2Q_ZzBGPdqE)
        Usage: `help media_only`
        Response: Shows info about media only channels"""
        response = fred_help.media_only()
        await self._send_help(ctx, embed=response)

    @commands.command()
    async def mod(self, ctx: commands.Context, *, mod_name: str) -> None:
        """Usage: `mod (name: str)`
        Response: If a near-exact match is found, gives you info about that mod.
        If close matches are found, up to 10 of those will be listed.
        If nothing even comes close, I'll let you know ;)"""
        embed, attachment = await createembed.mod_embed(mod_name, self.bot)
        if embed is None:
            await self.bot.reply_to_msg(ctx.message, "No mods found!")
        else:
            await self.bot.reply_to_msg(ctx.message, embed=embed, file=attachment)

    @commands.command()
    async def docsearch(self, ctx: commands.Context, *, search: str) -> None:
        """Usage: `docsearch (search: str)`
        Response: Equivalent to using the search function on the SMR docs page; links the first search result"""
        client = SearchClient.create('BH4D9OD16A', '53b3a8362ea7b391f63145996cfe8d82')
        index = client.init_index('ficsit')
        query = index.search(search, {'attributesToRetrieve': '*'})
        for hit in query["hits"]:
            if hit["hierarchy"]["lvl0"].endswith("latest"):
                await self.bot.reply_to_msg(ctx.message, f"This is the best result I got from the SMD :\n{hit['url']}")
                return

    @commands.command()
    async def leaderboard(self, ctx):
        """Usage: `leaderboard`
        Response: Shows the top 10 most talkative members and their xp"""
        query = config.Users.select().orderBy("-xp_count").limit(10)
        results = list(query)
        if not results:
            self.bot.reply_to_msg(ctx.message, "The database was empty. This should NEVER happen")
            return
        data = [dict(name=user.full_name, count_and_rank=dict(count=user.xp_count, rank=user.rank)) for user in results]
        embed = createembed.leaderboard(data)
        await self.bot.reply_to_msg(ctx.message, embed=embed)

    @commands.command()
    async def level(self, ctx: commands.Context, target_user: commands.UserConverter = None):
        """Usage: `level` [user]
        Response: Either your level or the level of the user specified
        Notes: the user parameter can be the user's @ mention or their UID, like 506192269557366805"""
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
    @commands.check(common.l4_only)
    async def add(self, ctx):
        """Usage: `add (subcommand) [args]`
        Purpose: Adds something (duh). Check individual subcommands for specifics.
        Notes: Limited to permission level 4 and above"""
        if ctx.invoked_subcommand is None:
            await self.bot.reply_to_msg(ctx.message, 'Invalid sub command passed...')
            return

    @commands.group()
    @commands.check(common.l4_only)
    async def remove(self, ctx):
        """Usage: `remove (subcommand) [args]`
        Purpose: Removes something (duh). Check individual subcommands for specifics.
        Notes: Limited to permission level 4 and above"""
        if ctx.invoked_subcommand is None:
            await self.bot.reply_to_msg(ctx.message, 'Invalid sub command passed...')
            return

    @commands.group()
    @commands.check(common.l4_only)
    async def set(self, ctx):
        """Usage: `set (subcommand) [args]`
        Purpose: Sets something (duh). Check individual subcommands for specifics.
        Notes: Limited to permission level 4 and above"""
        if ctx.invoked_subcommand is None:
            await self.bot.reply_to_msg(ctx.message, 'Invalid sub command passed...')
            return

    @commands.group()
    @commands.check(common.l4_only)
    async def modify(self, ctx):
        """Usage: `modify (subcommand) [args]`
        Purpose: Modifies something (duh). Check individual subcommands for specifics.
        Notes: Limited to permission level 4 and above"""
        if ctx.invoked_subcommand is None:
            await self.bot.reply_to_msg(ctx.message, 'Invalid sub command passed...')
            return

    @commands.group()
    @commands.check(common.mod_only)
    async def xp(self, ctx):
        """Usage: `set (subcommand) [args]`
        Purpose: Xp stuff. Check individual subcommands for specifics.
        Notes: Limited to moderators and above"""
        if ctx.invoked_subcommand is None:
            await self.bot.reply_to_msg(ctx.message, 'Invalid sub command passed...')
            return

    @add.command(name="mediaonly")
    async def add_mediaonly(self, ctx: commands.Context, channel: commands.TextChannelConverter):
        """Usage: `add mediaonly (channel)`
        Purpose: Adds channel to the list of channels that are managed to be media-only
        Notes: Limited to permission level 4 and above"""
        if config.MediaOnlyChannels.fetch(channel.id):
            await self.bot.reply_to_msg(ctx.message, "This channel is already a media only channel")
            return

        config.MediaOnlyChannels(channel_id=channel.id)
        await self.bot.reply_to_msg(ctx.message,
                                    f"Media Only channel {self.bot.get_channel(channel.id).mention} added!")

    @remove.command(name="mediaonly")
    async def remove_mediaonly(self, ctx: commands.Context, channel: commands.TextChannelConverter):
        """Usage: `add mediaonly (channel)`
        Purpose: Removes channel from the list of channels that are managed to be media-only
        Notes: Limited to permission level 4 and above"""
        if not config.MediaOnlyChannels.fetch(channel.id):
            await self.bot.reply_to_msg(ctx.message, "Media Only Channel could not be found!")
            return

        config.MediaOnlyChannels.deleteBy(channel_id=channel.id)
        await self.bot.reply_to_msg(ctx.message,
                                    f"Media Only channel {self.bot.get_channel(channel.id).mention} removed!")

    @add.command(name="command")
    async def add_command(self, ctx: commands.Context, command_name: str.lower, *, response: str = None):
        """Usage: `add command (name) [response]`
        Purpose: Adds a simple command to the list of commands
        Notes: If response is not supplied you will be prompted for one with a timeout"""
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
    async def remove_command(self, ctx: commands.Context, command_name: str.lower):
        """Usage: `remove command (name)`
        Purpose: Removes a simple command from the list of commands
        Notes: Probably best to ask first"""
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
    async def modify_command(self, ctx: commands.Context, command_name: str.lower, *, command_response: str = None):
        """Usage: `modify command (name) [response]`
        Purpose: Modifies a command
        Notes: If response is not supplied you will be prompted for one with a timeout"""
        if config.ReservedCommands.fetch(command_name):
            await self.bot.reply_to_msg(ctx.message, "This command is special and cannot be modified")
            return

        results = list(config.Commands.selectBy(name=command_name))
        if not results:  # this command hasn't been created yet
            try:
                question = "Command could not be found! Do you want to create it?"
                if await self.bot.reply_yes_or_no(ctx.message, question):
                    await self.add_command(ctx, command_name, response=command_response)
                else:
                    await self.bot.reply_to_msg(ctx.message, "Understood. Aborting")
                return
            except ValueError:
                return

        elif (linked_command := results[0].content)[0] == self.bot.command_prefix:
            try:
                question = f"`{command_name}` is an alias of `{linked_command[1:]}`. Modify original?"
                if await self.bot.reply_yes_or_no(ctx.message, question):
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
    async def add_alias(self, ctx: commands.Context, cmd_to_alias: str.lower, *aliases: str):
        """Usage: `add alias (command) [aliases...]`
        Purpose: Adds one or more aliases to a command, checking first for overwriting stuff
        Notes: If an alias is not supplied you will be prompted for one with a timeout"""

        # god this needs a refactor badly
        if not (cmd := config.Commands.fetch(cmd_to_alias)):
            await self.bot.reply_to_msg(ctx.message, f"`{cmd_to_alias}` doesn't exist!")
            return

        elif (link := cmd['content'])[0] == self.bot.command_prefix:
            try:
                confirm = await self.bot.reply_question(ctx.message,
                                                        f"`{cmd_to_alias}` is an alias for `{link[1:]}`. "
                                                        f"Add aliases to `{link[1:]}`?")
                if not confirm:
                    await self.bot.reply_to_msg(ctx.message, "Aborting")
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

        if aliases_added := list(set(aliases) - skipped):  # aliases_added is aliases without all the skipped aliases
            if (num_aliases := len(aliases_added)) > 1:
                user_info = f"{num_aliases} aliases added for {cmd_to_alias}: {', '.join(aliases_added)}"
            else:
                user_info = f"Alias added for {cmd_to_alias}: {aliases_added[0]}"
        else:
            user_info = "No aliases were added."
        self.logger.info(user_info)
        await self.bot.reply_to_msg(ctx.message, user_info)

    @remove.command(name="alias")
    async def remove_alias(self, ctx: commands.Context, command_name: str.lower):
        """Usage: `remove alias (alias)`
        Purpose: Removes an alias to a command, checking first to ensure it is one
        Notes: If an alias is not supplied you will be prompted for one with a timeout"""
        if not (cmd := config.Commands.fetch(command_name)):
            await self.bot.reply_to_msg(ctx.message, "Alias could not be found!")
            return
        elif not cmd['content'].startswith(self.bot.command_prefix):
            await self.bot.reply_to_msg(ctx.message, "This command is not an alias!")
            return
        else:
            config.Commands.deleteBy(name=command_name)

        await self.bot.reply_to_msg(ctx.message, "Alias removed!")

    @add.command(name="crash")
    async def add_crash(self, ctx: commands.Context, crash_name: str.lower, match: str = None, *, response: str = None):
        """Usage: `add crash (name) ["regex"] [response]`
        Purpose: Adds a crash to the list of known crashes.
        Notes:
            - If a regex and/or response is not supplied you will be prompted for them with a timeout.
            - Ensure the regex is surrounded by quotes BUT ONLY if you are doing it in one command.
            - `response` can be my command prefix and the name of a command, which will result in
            the response mirroring that of the command indicated."""
        if config.Crashes.fetch(crash_name):
            await self.bot.reply_to_msg(ctx.message, "A crash with this name already exists")
            return

        if not match:
            match, _ = await self.bot.reply_question(ctx.message, "What should the logs match (regex)?")
        try:
            re.search(match, "test")
        except re.error:
            await self.bot.reply_to_msg(ctx.message,
                                        "The regex isn't valid. Please refer to "
                                        "https://docs.python.org/3/library/re.html for docs on Python's regex library")
            return

        if not response:
            response, _ = await self.bot.reply_question(ctx.message, "What should the response be?")

        config.Crashes(name=crash_name, crash=match, response=response)
        await self.bot.reply_to_msg(ctx.message, "Known crash '" + crash_name + "' added!")

    @remove.command(name="crash")
    async def remove_crash(self, ctx: commands.Context, crash_name: str.lower):
        """Usage: `remove crash (name)
        Purpose: Removes a crash from the list of known crashes.
        Notes: hi"""
        if not config.Crashes.fetch(crash_name):
            await self.bot.reply_to_msg(ctx.message, "Crash could not be found!")
            return

        config.Crashes.deleteBy(name=crash_name)

        await self.bot.reply_to_msg(ctx.message, "Crash removed!")

    @modify.command(name="crash")
    async def modify_crash(self, ctx: commands.Context, name: str.lower, match: str = None, *, response: str = None):
        """Usage: `modify crash (name) ["regex"] [response]`
        Purpose: Adds a crash to the list of known crashes.
        Notes:
            - If a regex and/or response is not supplied you will be prompted to answer whether you want to modify each
            trait, then the desired new value for that trait, all with a timeout.
            - Ensure the regex is surrounded by quotes BUT ONLY if you are doing it in one command.
            - `response` can be my command prefix and the name of a command, which will result in
            the response mirroring that of the command indicated."""
        query = config.Crashes.selectBy(name=name)
        results = list(query)

        if not results:
            await ctx.send(f"Could not find a crash with name '{name}'. Aborting")
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
        await self.bot.reply_to_msg(ctx.message, f"Crash '{name}' modified!")

    @add.command(name="dialogflow")
    async def add_dialogflow(self, ctx: commands.Context, intent_id: str, response: bool | str, followup: bool, *args):
        """Usage: `add dialogflow (intent_id: str) (response: bool/str) (has_followup: bool)`
        Purpose: Adds a natural language processing trigger
        Notes: probably don't mess around with this, Mircea is the only wizard that knows how these works"""
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

        config.Dialogflow(intent_id=intent_id, data=data, response=response, has_followup=followup)
        await self.bot.reply_to_msg(ctx.message,
                                    f"Dialogflow response for '{intent_id}' "
                                    f"({json.dumps(data) if data else 'any data'}) added!")

    @remove.command(name="dialogflow")
    async def remove_dialogflow(self, ctx: commands.Context, intent_id: str, *args):
        """Usage: `add dialogflow (intent_id: str)`
        Purpose: Removes a natural language processing trigger
        Notes: probably don't mess around with this, Mircea is the only wizard that knows how these works"""
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
    async def add_dialogflow_channel(self, ctx: commands.Context, channel: commands.TextChannelConverter):
        """Usage: `add dialogflowChannel (channel)`
        Purpose: Adds channel to the list of channels that natural language processing is applied to"""
        if config.DialogflowChannels.fetch(channel.id):
            await self.bot.reply_to_msg(ctx.message, "This channel is already a dialogflow channel!")
        else:
            config.DialogflowChannels(channel_id=channel.id)
            await self.bot.reply_to_msg(ctx.message,
                                        f"Dialogflow channel {self.bot.get_channel(channel.id).mention} added!")

    @remove.command(name="dialogflowChannel")
    async def remove_dialogflow_channel(self, ctx: commands.Context, channel: commands.TextChannelConverter):
        """Usage: `remove dialogflowChannel (channel)`
        Purpose: Removes channel from the list of channels that natural language processing is applied to"""
        if config.DialogflowChannels.fetch(channel.id):
            config.DialogflowChannels.deleteBy(channel_id=channel.id)
            await self.bot.reply_to_msg(ctx.message,
                                        f"Dialogflow Channel {self.bot.get_channel(channel.id).mention} removed!")
        else:
            await self.bot.reply_to_msg(ctx.message, "Dialogflow channel could not be found!")

    @add.command(name="dialogflowRole")
    async def add_dialogflow_role(self, ctx: commands.Context, role: commands.RoleConverter):
        """Usage: `add dialogflowRole (role)`
        Purpose: Adds role to the list of roles that natural language processing is not applied to"""
        role_id = role.id

        if config.DialogflowExceptionRoles.fetch(role_id):
            await self.bot.reply_to_msg(ctx.message, "This role is already a dialogflow exception role")
            return

        config.DialogflowExceptionRoles(role_id=role_id)
        await self.bot.reply_to_msg(ctx.message, f"Dialogflow role {ctx.message.guild.get_role(role_id).name} added!")

    @remove.command(name="dialogflowRole")
    async def remove_dialogflow_role(self, ctx: commands.Context, role: commands.RoleConverter):
        """Usage: `remove dialogflowRole (role)`
        Purpose: Removes role from the list of roles that natural language processing is not applied to"""
        role_id = role.id

        if config.DialogflowExceptionRoles.fetch(role_id):
            config.DialogflowExceptionRoles.deleteBy(role_id=role_id)
            await self.bot.reply_to_msg(ctx.message, "Dialogflow role removed!")
        else:
            await self.bot.reply_to_msg(ctx.message, "Dialogflow role could not be found!")

    @add.command(name="level_role")
    async def add_level_role(self, ctx: commands.Context, role: commands.RoleConverter, rank: int):
        """Usage: `add level_role (role)`
        Purpose: adds a levelling role
        Notes: NOT IMPLEMENTED"""
        role_id = role.id

        if config.DialogflowExceptionRoles.fetch(role_id):
            await self.bot.reply_to_msg(ctx.message, "This role is already a level role")
            return

        config.RankRoles(role_id=role_id, rank=rank)
        await self.bot.reply_to_msg(ctx.message, "level role " + ctx.message.guild.get_role(role_id).name + " added!")

    @remove.command(name="level_role")
    async def remove_level_role(self, ctx: commands.Context, role: commands.RoleConverter):
        """Usage: `remove level_role (role)`
        Purpose: removes a levelling role
        Notes: NOT IMPLEMENTED"""
        role_id = role.id

        if config.RankRoles.fetch_by_role(role_id):
            config.RankRoles.deleteBy(role_id=role_id)
            await self.bot.reply_to_msg(ctx.message, "level role removed!")
        else:
            await self.bot.reply_to_msg(ctx.message, "level role could not be found!")

    @set.command(name="NLP_state")
    async def set_NLP_state(self, ctx: commands.Context, enabled: bool):
        """Usage: `set NLP_state (true/false)`
        Purpose: turns NLP on or off
        Notes: no touchy"""
        if not enabled:
            config.Misc.change("dialogflow_state", False)
            await self.bot.reply_to_msg(ctx.message, "The NLP is now off!")
        else:
            config.Misc.change("dialogflow_state", True)
            await self.bot.reply_to_msg(ctx.message, "The NLP is now on!")

    @set.command(name="NLP_debug")
    async def set_NLP_debug(self, ctx: commands.Context, enabled: bool):
        """Usage: `set NLP_debug (true/false)`
        Purpose: turns NLP debug (ignores all ignore rules) on or off
        Notes: no touchy, can get very spammy"""
        if not enabled:
            config.Misc.change("dialogflow_debug_state", False)
            await self.bot.reply_to_msg(ctx.message, "The NLP debugging mode is now off!")
        else:
            config.Misc.change("dialogflow_debug_state", True)
            await self.bot.reply_to_msg(ctx.message, "The NLP debugging mode is now on!")

    @set.command(name="welcome_message")
    async def set_welcome_message(self, ctx: commands.Context, *, welcome_message: str):
        """Usage: `set welcome_message (message)`
        Purpose: Sets the message that will be DMed to people who join the server
        Notes: messages under 10 characters will result in the welcome message being disabled"""
        if len(welcome_message) < 10:
            config.Misc.change("welcome_message", "")
            await self.bot.reply_to_msg(ctx.message, "The welcome message is now disabled")
        else:
            config.Misc.change("welcome_message", welcome_message)
            await self.bot.reply_to_msg(ctx.message, "The welcome message has been changed")

    @set.command(name="latest_info")
    async def set_latest_info(self, ctx: commands.Context, latest_info: str):
        """Usage: `set latest_info (message)`
        Purpose: Sets the other message that will be DMed to people who join the server
        Notes: messages under 10 characters will result in the message being disabled"""
        if len(latest_info) < 10:
            config.Misc.change("latest_info", "")
            await self.bot.reply_to_msg(ctx.message, "The latest info message is now disabled")
        else:
            config.Misc.change("latest_info", latest_info)
            await self.bot.reply_to_msg(ctx.message, "The latest info message has been changed!")

    @commands.check(common.mod_only)
    @set.command(name="base_level_value")
    async def set_base_level_value(self, ctx: commands.Context, base_level_value: int):
        """Usage: `set base_level_value (value: int)`
        Purpose: Sets base value for levelling calculations
        Notes: moderator and above only"""
        config.Misc.change("base_level_value", base_level_value)
        await self.bot.reply_to_msg(ctx.message, "The base level value has been changed!")

    @commands.check(common.mod_only)
    @set.command(name="level_value_multiplier")
    async def set_level_value_multiplier(self, ctx: commands.Context, level_value_multiplier: float):
        """Usage: `set level_value_multiplier (value: int)`
        Purpose: Sets coefficient for levelling calculations
        Notes: moderator and above only"""
        config.Misc.change("level_value_multiplier", level_value_multiplier)
        await self.bot.reply_to_msg(ctx.message, "The level value multiplier has been changed!")

    @commands.check(common.mod_only)
    @set.command(name="xp_gain_value")
    async def set_xp_gain_value(self, ctx: commands.Context, xp_gain_value: int):
        """Usage: `set xp_gain_value (value: int)`
        Purpose: Sets amount gained per valid message (see xp_gain_delay)
        Notes: moderator and above only"""
        config.Misc.change("xp_gain_value", xp_gain_value)
        await self.bot.reply_to_msg(ctx.message, "The xp gain value has been changed!")

    @commands.check(common.mod_only)
    @set.command(name="xp_gain_delay")
    async def set_xp_gain_delay(self, ctx: commands.Context, xp_gain_delay: int):
        """Usage: `set xp_gain_delay (value: int)`
        Purpose: Sets duration before another message sent can trigger another xp increment
        Notes: moderator and above only"""
        config.Misc.change("xp_gain_delay", xp_gain_delay)
        await self.bot.reply_to_msg(ctx.message, "The xp gain delay has been changed!")

    @commands.check(common.mod_only)
    @set.command(name="levelling_state")
    async def set_levelling_state(self, ctx: commands.Context, enabled: bool):
        """Usage: `set levelling_state (enabled: bool)`
        Purpose: turns levelling on or off
        Notes: moderator and above only"""
        if not enabled:
            config.Misc.change("levelling_state", False)
            await self.bot.reply_to_msg(ctx.message, "The levelling system is now inactive!")
        else:
            config.Misc.change("levelling_state", True)
            await self.bot.reply_to_msg(ctx.message, "The levelling system is now active!")

    @commands.check(common.mod_only)
    @set.command(name="main_guild")
    async def set_main_guild(self, ctx: commands.Context, guild_id: int = None):
        """Usage: `set main_guild (guild_id: int)`
        Purpose: changes what counts as the main server
        Notes: unless you're testing me as a beta fork, don't use this"""
        if not guild_id:
            guild_id = ctx.guild.id
        config.Misc.change("main_guild_id", guild_id)
        await self.bot.reply_to_msg(ctx.message, "The main guild is now this one!")

    @xp.command(name="give")
    async def xp_give(self, ctx: commands.Context, target: commands.UserConverter, amount: float):
        """Usage: `xp give (user) (amount)`
        Purpose: gives the indicated user the specified xp
        Notes: don't give negative xp, use take"""
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
    async def xp_take(self, ctx: commands.Context, target: commands.UserConverter, amount: float):
        """Usage: `xp give (user) (amount)`
        Purpose: takes the specified xp from the indicated user
        Notes: don't take negative xp, use give"""
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
    async def xp_multiplier(self, ctx: commands.Context, target: commands.UserConverter, multiplier: float):
        """Usage: `xp multiplier (user) (multiplier)`
        Purpose: sets the user's personalised xp gain multiplier from the base value
        Notes: a negative value will be converted to 0"""
        DB_user = config.Users.create_if_missing(target)
        amount = max(multiplier, 0)  # no negative gain allowed
        DB_user.xp_multiplier = amount

        if amount == 0:
            await self.bot.reply_to_msg(ctx.message, f"{target.name} has been banned from xp gain")
        else:
            await self.bot.reply_to_msg(ctx.message, f"Set {target.name}'s xp multiplier to {amount}")

    @xp.command(name="set")
    async def xp_set(self, ctx: commands.Context, target: commands.UserConverter, amount: float):
        """Usage: `xp set (user) (amount)`
        Purpose: sets the user's xp amount to the specified amount
        Notes: don't try negative values, it won't work"""
        profile = levelling.UserProfile(target.id, ctx.guild, self.bot)

        if amount < 0:
            await self.bot.reply_to_msg(ctx.message, 'Negative numbers for xp are not allowed!')
        else:
            await profile.set_xp(amount)
            await self.bot.reply_to_msg(ctx.message,
                                        f"Set {target.name}'s xp count to {amount}. "
                                        f"They are now rank {profile.rank} ({profile.xp_count} xp)")

    @set.command(name="webhook_channel")
    @commands.check(common.mod_only)
    async def set_webhook_channel(self, ctx: commands.Context, channel: commands.TextChannelConverter):
        """Usage: `set webhook_channel (channel: int | channel mention)`
        Purpose: changes where GitHub webhooks are sent
        Notes: unless you're testing me as a beta fork, don't use this"""
        config.Misc.change("githook_channel", channel.id)
        await self.bot.reply_to_msg(ctx.message,
                                    f"The channel for the github hooks is now "
                                    f"{self.bot.get_channel(channel.id).mention}!")

    @set.command(name='prefix')
    @commands.check(common.mod_only)
    async def prefix(self, ctx: commands.Context, *, prefix: str):
        """Usage: `set prefix (prefix: str)`
        Purpose: changes what prefix is used to call commands
        Notes: unless you're testing me as a beta fork, don't use this"""
        config.Misc.change("prefix", prefix)
        self.bot.command_prefix = prefix
        await self.bot.reply_to_msg(ctx.message, f"Prefix changed to {prefix}.")
