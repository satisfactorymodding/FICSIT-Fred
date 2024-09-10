from ._baseclass import BaseCmds, commands, SearchFlags
from ._command_utils import get_search
from .. import config


def _extract_prefix(string: str, prefix: str):
    if not string:
        return False, ""
    a, prefix, b = string.partition(prefix)
    if prefix and not a and not (words := b.split())[1:]:
        return True, words[0]
    else:
        return False, string


class CommandCmds(BaseCmds):

    @BaseCmds.add.command(name="command")
    async def add_command(self, ctx: commands.Context, command_name: str.lower, *, response: str = None):
        """Usage: `add command (name) [response]`
        Purpose: Adds a simple command to the list of commands
        Notes: If response is not supplied you will be prompted for one with a timeout"""
        if config.Commands.fetch(command_name) is not None:
            await self.bot.reply_to_msg(ctx.message, "This command already exists!")
            return
        if config.ReservedCommands.check(command_name):
            await self.bot.reply_to_msg(ctx.message, "This command name is reserved")
            return

        attachment = ctx.message.attachments[0].url if ctx.message.attachments else None

        if not response and not attachment:
            response, attachment = await self.bot.reply_question(ctx.message, "What should the response be?")

        is_alias, name = _extract_prefix(response, self.bot.command_prefix)
        if is_alias:
            msg = f"This creates an unchecked alias for `{name}`! Are you sure you want to proceed?"
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

        is_alias, name = _extract_prefix(cmd["content"], self.bot.command_prefix)

        if is_alias:
            delete = await self.bot.reply_yes_or_no(ctx.message, f"This command is an alias of `{name}`! Delete?")
            if not delete:
                return
        config.Commands.deleteBy(name=command_name)

        await self.bot.reply_to_msg(ctx.message, "Command removed!")

    @BaseCmds.modify.command(name="command")
    async def modify_command(self, ctx: commands.Context, command_name: str.lower, *, new_response: str = None):
        """Usage: `modify command (name) [response]`
        Purpose: Modifies a command
        Notes: If response is not supplied you will be prompted for one with a timeout"""
        if config.ReservedCommands.check(command_name):
            await self.bot.reply_to_msg(ctx.message, "This command is special and cannot be modified.")
            return

        if not (results := list(config.Commands.selectBy(name=command_name))):  # this command hasn't been created yet
            try:
                question = "Command could not be found! Do you want to create it?"
                if await self.bot.reply_yes_or_no(ctx.message, question):
                    await self.add_command(ctx, command_name, response=new_response)
                else:
                    await self.bot.reply_to_msg(ctx.message, "Command modification cancelled.")
                return
            except ValueError:
                return

        is_alias, name = _extract_prefix(results[0].content, self.bot.command_prefix)
        if is_alias:
            try:
                question = f"`{command_name}` is an alias of `{name}`. Modify original?"
                if await self.bot.reply_yes_or_no(ctx.message, question):
                    command_name = name
                await self.bot.reply_to_msg(ctx.message, f"Modifying {command_name}")
            except ValueError:
                return

        if not new_response and not ctx.message.attachments:
            new_response, attachment = await self.bot.reply_question(ctx.message, "What should the response be?")
        else:
            attachment = ctx.message.attachments[0] if ctx.message.attachments else None

        # this just works, don't touch it. trying to use config.Commands.fetch makes a duplicate command.
        results[0].content = new_response
        results[0].attachment = attachment.url if attachment else None

        await self.bot.reply_to_msg(ctx.message, f"Command '{command_name}' modified!")

    @staticmethod
    def _valid_aliases(target: str, aliases: list[str]) -> dict[str, list[str | tuple[str, str]]]:
        rtn = {"valid": [], "overwrite": [], "failure": []}
        for alias in aliases:
            if config.ReservedCommands.check(alias):
                rtn["failure"] += (alias, "reserved")

            elif cmd := config.Commands.fetch(name=alias):
                if cmd["content"] == target:  # contents are identical
                    rtn["failure"].append((alias, "exists"))
                else:
                    rtn["overwrite"].append(alias)
            else:
                rtn["valid"].append(alias)
        return rtn

    async def _add_alias(self, ctx: commands.Context, target: str, aliases: list[str]) -> str:
        link = self.bot.command_prefix + target
        alias_checks = self._valid_aliases(link, aliases)

        for alias in alias_checks["overwrite"]:
            if await self.bot.reply_yes_or_no(ctx.message, f"`{alias}` is already something else. Replace definition?"):
                config.Commands.deleteBy(name=alias)
                alias_checks["valid"].append(alias)
            else:
                alias_checks["failure"].append((alias, "overwrite"))

        for alias in alias_checks["valid"]:
            config.Commands(name=alias, content=link, attachment=None)

        if (num_aliases := len(alias_checks["valid"])) > 1:
            user_info = f"{num_aliases} aliases added for {target}: `{'`, `'.join(alias_checks['valid'])}`"
        elif num_aliases == 1:
            user_info = f"Alias added for `{target}`: `{alias_checks['valid'][0]}`"
        else:
            user_info = "No aliases could be added"

        if unable := alias_checks["failure"]:
            user_info += "\nUnable to add the following aliases: \n"
            for name, reason in unable:
                match reason:
                    case "exists":
                        verbose_reason = f"already an alias for `{target}`"
                    case "reserved":
                        verbose_reason = "is a reserved name"
                    case "overwrite":
                        verbose_reason = "would overwrite - cancelled by user"
                    case _:
                        verbose_reason = "uhh"

                user_info += f"`{name}`\t-\t{verbose_reason}\n"

        return user_info

    @BaseCmds.add.command(name="alias")
    async def add_alias(self, ctx: commands.Context, target: str.lower, *aliases: str.lower):
        """Usage: `add alias (command) [aliases...]`
        Purpose: Adds one or more aliases to a command, checking first for overwriting stuff
        Notes: If an alias is not supplied you will be prompted for one with a timeout"""

        # god this needs a refactor badly
        if not (cmd := config.Commands.fetch(target)):
            await self.bot.reply_to_msg(ctx.message, f"`{target}` doesn't exist!")
            return

        is_alias, name = _extract_prefix(cmd["content"], self.bot.command_prefix)
        if is_alias:
            try:
                msg = (
                    f"`{target}` is an alias for `{name}`. Links to links are not supported. \n"
                    f"Do you want to redirect your alias target to `{name}`?"
                )
                if not await self.bot.reply_question(ctx.message, msg):
                    await self.bot.reply_to_msg(ctx.message, "Aborting alias addition.")
                    return
                target = name
            except ValueError:
                return

        if not aliases:
            response, _ = await self.bot.reply_question(ctx.message, "Please input aliases, separated by spaces.")
            aliases = response.lower().split(" ")

        response = await self._add_alias(ctx, target, aliases)

        self.logger.info(response)
        await self.bot.reply_to_msg(ctx.message, response)

    @BaseCmds.remove.command(name="alias")
    async def remove_alias(self, ctx: commands.Context, command_name: str.lower):
        """Usage: `remove alias (alias)`
        Purpose: Removes an alias to a command, checking first to ensure it is one
        Notes: If an alias is not supplied you will be prompted for one with a timeout"""
        if not (cmd := config.Commands.fetch(command_name)):
            await self.bot.reply_to_msg(ctx.message, "Alias could not be found!")
            return
        elif not cmd["content"].startswith(self.bot.command_prefix):
            await self.bot.reply_to_msg(ctx.message, "This command is not an alias!")
            return
        else:
            config.Commands.deleteBy(name=command_name)

        await self.bot.reply_to_msg(ctx.message, "Alias removed!")

    @BaseCmds.rename.command(name="command")
    async def rename_command(self, ctx: commands.Context, name: str.lower, *, new_name: str.lower = None) -> None:
        """Usage: `rename command (name) (new_name)`
        Purpose: Renames a command.
        Notes: If response is not supplied you will be prompted for one with a timeout"""
        if config.ReservedCommands.check(name):
            await self.bot.reply_to_msg(ctx.message, "This command is special and cannot be modified.")
            return

        results: list[config.Commands]
        if not (results := list(config.Commands.selectBy(name=name))):  # this command hasn't been created yet
            await self.bot.reply_to_msg(ctx.message, "Command could not be found!")
            return

        if new_name is None:
            new_name, _ = await self.bot.reply_question(ctx.message, "What should the new name be?")

        # this just works, don't touch it. trying to use config.Commands.fetch makes a duplicate command.
        results[0].name = new_name

        await self.bot.reply_to_msg(ctx.message, f"Command `{name}` is now `{new_name}`!")

    @BaseCmds.rename.command(name="alias")
    async def rename_alias(self, ctx: commands.Context, name: str.lower, *, new_name: str.lower = None) -> None:
        """Usage: `rename alias (name) (new name)`
        Purpose: Renames an alias.
        Notes: If response is not supplied you will be prompted for one with a timeout"""
        await self.rename_command(ctx, name, new_name)

    @BaseCmds.search.command(name="commands")
    async def search_commands(self, ctx: commands.Context, pattern: str, *, flags: SearchFlags) -> None:
        """Usage: `search commands (pattern) [options]`
        Purpose: Searches commands for the stuff requested.
        Optional args:
            -fuzzy=(true/false) Forces fuzzy matching. Defaults to false, but fuzzy happens if exact matches aren't found.
            -column=(name/content/attachment) The column of the database to search along. Defaults to name
        Notes: Uses fuzzy matching!"""

        response = get_search(config.Commands, pattern, flags.column, flags.fuzzy)
        await self.bot.reply_to_msg(ctx.message, response)
