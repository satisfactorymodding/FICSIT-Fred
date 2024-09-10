from re2 import search, RegexError

from ._baseclass import BaseCmds, commands, config, SearchFlags
from ._command_utils import get_search


class CrashCmds(BaseCmds):

    @BaseCmds.add.command(name="crash")
    async def add_crash(self, ctx: commands.Context, crash_name: str.lower, match: str = None, *, response: str = None):
        """Usage: `add crash (name) ["regex"] [response]`
        Purpose: Adds a crash to the list of known crashes.
        Notes:
            - If a regex and/or response is not supplied you will be prompted for them with a timeout.
            - Ensure the regex is surrounded by quotes BUT ONLY if you are doing it in one command.
            - `response` can be my command prefix and the name of a command, which will result in
            the response mirroring that of the command indicated."""

        if config.Crashes.fetch(crash_name) is not None:
            await self.bot.reply_to_msg(ctx.message, "A crash with this name already exists")
            return

        if not match:
            match, _ = await self.bot.reply_question(ctx.message, "What should the logs match (regex)?")
        try:
            search(match, "test")
        except RegexError:
            await self.bot.reply_to_msg(
                ctx.message,
                "The regex isn't valid. Please refer to "
                "https://docs.python.org/3/library/re.html for docs on Python's regex library",
            )
            return

        if not response:
            response, _ = await self.bot.reply_question(ctx.message, "What should the response be?")

        config.Crashes(name=crash_name, crash=match, response=response)
        await self.bot.reply_to_msg(ctx.message, "Known crash '" + crash_name + "' added!")

    @BaseCmds.remove.command(name="crash")
    async def remove_crash(self, ctx: commands.Context, crash_name: str.lower):
        """Usage: `remove crash (name)
        Purpose: Removes a crash from the list of known crashes.
        Notes: hi"""
        if config.Crashes.fetch(crash_name) is None:
            await self.bot.reply_to_msg(ctx.message, "Crash could not be found!")
            return

        config.Crashes.deleteBy(name=crash_name)

        await self.bot.reply_to_msg(ctx.message, "Crash removed!")

    @BaseCmds.modify.command(name="crash")
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
                match, _ = await self.bot.reply_question(
                    ctx.message, "What is the regular expression to match in the logs?"
                )
        except ValueError:
            return

        try:
            if change_response := await self.bot.reply_yes_or_no(ctx.message, "Do you want to change the response?"):
                response, _ = await self.bot.reply_question(
                    ctx.message,
                    f"What response do you want it to provide? Responding with `{self.bot.command_prefix}command_name`"
                    "will use the response of that command.",
                )
        except ValueError:
            return

        if change_crash:
            results[0].crash = match
        if change_response:
            results[0].response = response
        await self.bot.reply_to_msg(ctx.message, f"Crash '{name}' modified!")

    @BaseCmds.search.command(name="crashes")
    async def search_crashes(self, ctx: commands.Context, pattern: str, *, flags: SearchFlags) -> None:
        """Usage: `search crashes (name) [options]`
        Purpose: Searches crashes for the stuff requested.
        Optional args:
            -fuzzy=(true/false) Forces fuzzy matching. Defaults to false, but fuzzy happens if exact matches aren't found.
            -column=(name/crash/response) The column of the database to search along. Defaults to name
        Notes: Uses fuzzy matching!"""

        response = get_search(config.Commands, pattern, flags.column, flags.fuzzy)
        await self.bot.reply_to_msg(ctx.message, response)
