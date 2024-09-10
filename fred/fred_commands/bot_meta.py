from ._baseclass import BaseCmds, commands, config, common


class BotCmds(BaseCmds):

    @commands.command()
    async def version(self, ctx: commands.Context):
        """Usage: `version`
        Response: Fred's current version
        Notes: Command is a useful is-alive check"""
        await self.bot.reply_to_msg(ctx.message, self.bot.version)

    @BaseCmds.set.command(name="welcome_message")
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

    @BaseCmds.set.command(name="latest_info")
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
    @BaseCmds.set.command(name="main_guild")
    async def set_main_guild(self, ctx: commands.Context, guild_id: int = None):
        """Usage: `set main_guild [guild_id: int]`
        Purpose: changes what counts as the main server
        Notes: unless you're testing me as a beta fork, don't use this"""
        if not guild_id:
            guild_id = ctx.guild.id
        config.Misc.change("main_guild_id", guild_id)
        await self.bot.reply_to_msg(ctx.message, "The main guild is now this one!")

    @commands.check(common.mod_only)
    @BaseCmds.set.command(name="prefix")
    async def prefix(self, ctx: commands.Context, *, prefix: str):
        """Usage: `set prefix (prefix: str)`
        Purpose: changes what prefix is used to call commands
        Notes: unless you're testing me as a beta fork, don't use this"""
        config.Misc.change("prefix", prefix)
        self.bot.command_prefix = prefix
        await self.bot.reply_to_msg(ctx.message, f"Prefix changed to {prefix}.")

    @BaseCmds.set.command(name="owo")
    async def owo(self, ctx: commands.Context):
        """Usage: `set owo`
        Purpose: toggle owo
        Notes: owo what's this? you need to be engineer or above to use this"""
        self.bot.owo = not self.bot.owo
        await ctx.reply("OwO" if self.bot.owo else "no owo :(")
