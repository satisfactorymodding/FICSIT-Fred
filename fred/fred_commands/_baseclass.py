from nextcord.ext import commands

from .. import config
from ..libraries import common

assert config  # noqa


class BaseCmds(common.FredCog):

    @commands.group()
    @commands.check(common.l4_only)
    async def add(self, ctx: commands.Context):
        """Usage: `add (subcommand) [args]`
        Purpose: Adds something (duh). Check individual subcommands for specifics.
        Notes: Limited to permission level 4 and above"""
        if ctx.invoked_subcommand is None:
            await self.bot.reply_to_msg(ctx.message, "Invalid sub command passed...")
            return

    @commands.group()
    @commands.check(common.l4_only)
    async def remove(self, ctx: commands.Context):
        """Usage: `remove (subcommand) [args]`
        Purpose: Removes something (duh). Check individual subcommands for specifics.
        Notes: Limited to permission level 4 and above"""
        if ctx.invoked_subcommand is None:
            await self.bot.reply_to_msg(ctx.message, "Invalid sub command passed...")
            return

    @commands.group()
    @commands.check(common.l4_only)
    async def rename(self, ctx: commands.Context):
        """Usage: `rename (subcommand) (name) (new name)`
        Purpose: Renames a configurable interaction. Check individual subcommands for specifics.
        Notes: Limited to permission level 4 and above"""
        if ctx.invoked_subcommand is None:
            await self.bot.reply_to_msg(ctx.message, "Invalid sub command passed...")
            return

    @commands.group()  # no checks needed because it doesn't change anything
    async def search(self, ctx: commands.Context):
        """Usage: `search (category) (pattern) [options]`
        Purpose: Searches things like crashes and commands for the stuff requested.
        Notes: Uses fuzzy matching!"""
        if ctx.invoked_subcommand is None:
            await self.bot.reply_to_msg(ctx.message, "Cannot search this category! Are you sure it exists?")
            return

    @commands.group()
    @commands.check(common.l4_only)
    async def set(self, ctx: commands.Context):
        """Usage: `set (subcommand) [args]`
        Purpose: Sets something (duh). Check individual subcommands for specifics.
        Notes: Limited to permission level 4 and above"""
        if ctx.invoked_subcommand is None:
            await self.bot.reply_to_msg(ctx.message, "Invalid sub command passed...")
            return

    @commands.group()
    @commands.check(common.l4_only)
    async def modify(self, ctx: commands.Context):
        """Usage: `modify (subcommand) [args]`
        Purpose: Modifies something (duh). Check individual subcommands for specifics.
        Notes: Limited to permission level 4 and above"""
        if ctx.invoked_subcommand is None:
            await self.bot.reply_to_msg(ctx.message, "Invalid sub command passed...")
            return

    @commands.group()
    @commands.check(common.l4_only)
    async def get(self, ctx: commands.Context):
        """Usage: `get (subcommand) [args]`
        Purpose: Gets something (duh). Check individual subcommands for specifics.
        Notes: Limited to permission level 4 and above."""
        if ctx.invoked_subcommand is None:
            await self.bot.reply_to_msg(ctx.message, "Invalid sub command passed...")
            return


class SearchFlags(commands.FlagConverter, delimiter="=", prefix="-"):
    column: str = "name"
    fuzzy: bool = False
