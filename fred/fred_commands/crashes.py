import nextcord
import re2
from nextcord import Interaction, SlashOption

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

        if not response:
            response, _ = await self.bot.reply_question(ctx.message, "What should the response be?")

        issue = validate_crash(match, response)
        if issue:
            await self.bot.reply_to_msg(ctx.message, issue)
            return

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
    async def modify_crash(
        self, ctx: commands.Context, name: str.lower, new_crash: str = None, *, new_response: str = None
    ):
        """Usage: `modify crash (name) ["regex"] [response]`
        Purpose: Adds a crash to the list of known crashes.
        Notes:
            - If a regex and/or response is not supplied you will be prompted to answer whether you want to modify each
            trait, then the desired new value for that trait, all with a timeout.
            - Ensure the regex is surrounded by quotes BUT ONLY if you are doing it in one command.
            - `response` can be my command prefix and the name of a command, which will result in
            the response mirroring that of the command indicated."""
        crash = config.Crashes.selectBy(name=name).getOne(None)

        if crash is None:
            await ctx.send(f"Could not find a crash with name '{name}'. Aborting")
            return

        try:
            if change_crash := await self.bot.reply_yes_or_no(ctx.message, "Do you want to change the crash to match?"):
                new_crash, _ = await self.bot.reply_question(
                    ctx.message, "What is the regular expression to match in the logs?"
                )

            if change_response := await self.bot.reply_yes_or_no(ctx.message, "Do you want to change the response?"):
                new_response, _ = await self.bot.reply_question(
                    ctx.message,
                    f"What response do you want it to provide? Responding with `{self.bot.command_prefix}command_name`"
                    "will use the response of that command.",
                )
        except ValueError:
            return

        checked_crash = new_crash if change_crash else crash.crash
        checked_response = new_response if change_response else crash.response

        issue = validate_crash(checked_crash, checked_response)
        if issue:
            await self.bot.reply_to_msg(ctx.message, issue)
            return

        crash.crash = checked_crash
        crash.response = checked_response

        await self.bot.reply_to_msg(ctx.message, f"Crash '{name}' modified!")

    #       Search Crashes Command
    @BaseCmds.search.command(name="crashes")
    async def search_crashes(self, ctx: commands.Context, pattern: str, *, flags: SearchFlags) -> None:
        """Usage: `search crashes (name) [options]`
        Purpose: Searches crashes for the stuff requested.
        Optional args:
            -fuzzy=(true/false) Forces fuzzy matching. Defaults to false, but fuzzy happens if exact matches aren't found.
            -column=(name/crash/response) The column of the database to search along. Defaults to name
        Notes: Uses fuzzy matching!"""

        response = get_search(config.Crashes, pattern, flags.column, flags.fuzzy)
        await self.bot.reply_to_msg(ctx.message, response)

    @nextcord.slash_command(name="search_crashes", description="Searches crashes for the stuff requested.")
    async def search_crashes_slash(
        self,
        interaction: Interaction,
        pattern: str = SlashOption(description="The pattern to search for"),
        fuzzy: bool = SlashOption(description="Whether to use fuzzy matching", default=False),
        column: str = SlashOption(
            description="The column of the database to search along",
            choices={"name": "name", "crash": "crash", "response": "response"},
            default="name",
        ),
        private_command: bool = SlashOption(description="Only you can see the response", default=True),
    ):
        flags = SearchFlags()
        flags.fuzzy = fuzzy
        flags.column = column

        response = get_search(config.Commands, pattern, flags.column, flags.fuzzy)
        await interaction.response.send_message(response, ephemeral=private_command)


def validate_crash(expression: str, response: str) -> str:
    """Returns a string describing an issue with the crash or empty string if it's fine."""
    try:
        print(f"Debug: Compiling expression: {expression}")
        compiled = re2.compile(expression)
        print("Debug: Performing test search with re2")
        re2.search(expression, "test")

        replace_groups = re2.findall(r"{(\d+)}", response)
        replace_groups_count = max(map(int, replace_groups), default=0)

        if replace_groups_count > compiled.groups:
            return f"There are replacement groups the regex does not capture!"

    except (re2.error, re2.RegexError) as e:
        print(f"Debug: re2 error encountered: {e}")
        return f"The expression isn't valid: {e}"

    except Exception as fallback_error:
        print(f"Debug: Fallback module error: {fallback_error}")
        return f"An error occurred in the fallback module: {fallback_error}"

    return ""  # all good
