from ._baseclass import BaseCmds, commands
from .. import config


class CommandCmds(BaseCmds):

    @BaseCmds.add.command(name="command")
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

    @BaseCmds.remove.command(name="command")
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

    @BaseCmds.modify.command(name="command")
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
            attachment = ctx.message.attachments[0].url if ctx.message.attachments else None

        # this just works, don't touch it. trying to use config.Commands.fetch makes a duplicate command.
        results[0].content = command_response
        results[0].attachment = attachment

        await self.bot.reply_to_msg(ctx.message, f"Command '{command_name}' modified!")

    @BaseCmds.add.command(name="alias")
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

    @BaseCmds.remove.command(name="alias")
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
