import logging

from nextcord.ext import commands
from .. import config
from ..libraries import common

assert config  # shut up linter, things that import this need this for convenience


class BaseCmds(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.Logger("COMMANDS")

    @commands.group()
    @commands.check(common.l4_only)
    async def add(self, ctx):
        """Usage: `add (subcommand) [args]`
        Purpose: Adds something (duh). Check individual subcommands for specifics.
        Notes: Limited to permission level 4 and above"""
        if ctx.invoked_subcommand is None:
            await self.bot.reply_to_msg(ctx.message, "Invalid sub command passed...")
            return

    @commands.group()
    @commands.check(common.l4_only)
    async def remove(self, ctx):
        """Usage: `remove (subcommand) [args]`
        Purpose: Removes something (duh). Check individual subcommands for specifics.
        Notes: Limited to permission level 4 and above"""
        if ctx.invoked_subcommand is None:
            await self.bot.reply_to_msg(ctx.message, "Invalid sub command passed...")
            return

    @commands.group()
    @commands.check(common.l4_only)
    async def set(self, ctx):
        """Usage: `set (subcommand) [args]`
        Purpose: Sets something (duh). Check individual subcommands for specifics.
        Notes: Limited to permission level 4 and above"""
        if ctx.invoked_subcommand is None:
            await self.bot.reply_to_msg(ctx.message, "Invalid sub command passed...")
            return

    @commands.group()
    @commands.check(common.l4_only)
    async def modify(self, ctx):
        """Usage: `modify (subcommand) [args]`
        Purpose: Modifies something (duh). Check individual subcommands for specifics.
        Notes: Limited to permission level 4 and above"""
        if ctx.invoked_subcommand is None:
            await self.bot.reply_to_msg(ctx.message, "Invalid sub command passed...")
            return
