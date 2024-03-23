from ._baseclass import BaseCmds, commands, common, config
from cogs import levelling
from libraries import createembed


class EXPCmds(BaseCmds):
    @commands.group()
    @commands.check(common.mod_only)
    async def xp(self, ctx):
        """Usage: `set (subcommand) [args]`
        Purpose: Xp stuff. Check individual subcommands for specifics.
        Notes: Limited to moderators and above"""
        if ctx.invoked_subcommand is None:
            await self.bot.reply_to_msg(ctx.message, "Invalid sub command passed...")
            return

    @xp.command(name="give")
    async def xp_give(self, ctx: commands.Context, target: commands.UserConverter, amount: float):
        """Usage: `xp give (user) (amount)`
        Purpose: gives the indicated user the specified xp
        Notes: don't give negative xp, use take"""
        profile = levelling.UserProfile(target.id, ctx.guild, self.bot)
        if amount < 0:
            await self.bot.reply_to_msg(
                ctx.message,
                f"<:thonk:836648850377801769> attempt to give a negative\n"
                f"Did you mean `{self.bot.command_prefix}xp take`?",
            )
        else:
            await profile.give_xp(amount)
            await self.bot.reply_to_msg(
                ctx.message,
                f"Gave {amount} xp to {target.name}. " f"They are now rank {profile.rank} ({profile.xp_count} xp)",
            )

    @xp.command(name="take")
    async def xp_take(self, ctx: commands.Context, target: commands.UserConverter, amount: float):
        """Usage: `xp give (user) (amount)`
        Purpose: takes the specified xp from the indicated user
        Notes: don't take negative xp, use give"""
        profile = levelling.UserProfile(target.id, ctx.guild, self.bot)
        if amount < 0:
            await self.bot.reply_to_msg(
                ctx.message,
                f"<:thonk:836648850377801769> attempt to take away a negative\n"
                f"Did you mean `{self.bot.command_prefix}xp give`?",
            )
            return

        if not await profile.take_xp(amount):
            await self.bot.reply_to_msg(ctx.message, "Cannot take more xp that this user has!")
        else:
            await self.bot.reply_to_msg(
                ctx.message,
                f"Took {amount} xp from {target.name}. " f"They are now rank {profile.rank} ({profile.xp_count} xp)",
            )

    @xp.command(name="multiplier")
    async def xp_multiplier(self, ctx: commands.Context, target: commands.UserConverter, multiplier: float):
        """Usage: `xp multiplier (user) (multiplier)`
        Purpose: sets the user's personalised xp gain multiplier from the base value
        Notes: a negative value will be converted to 0"""
        user_meta = config.Users.create_if_missing(target)
        amount = max(multiplier, 0)  # no negative gain allowed
        user_meta.xp_multiplier = amount

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
            await self.bot.reply_to_msg(ctx.message, "Negative numbers for xp are not allowed!")
        else:
            await profile.set_xp(amount)
            await self.bot.reply_to_msg(
                ctx.message,
                f"Set {target.name}'s xp count to {amount}. "
                f"They are now rank {profile.rank} ({profile.xp_count} xp)",
            )

    @commands.check(common.mod_only)
    @BaseCmds.set.command(name="base_level_value")
    async def set_base_level_value(self, ctx: commands.Context, base_level_value: int):
        """Usage: `set base_level_value (value: int)`
        Purpose: Sets base value for levelling calculations
        Notes: moderator and above only"""
        config.Misc.change("base_level_value", base_level_value)
        await self.bot.reply_to_msg(ctx.message, "The base level value has been changed!")

    @commands.check(common.mod_only)
    @BaseCmds.set.command(name="level_value_multiplier")
    async def set_level_value_multiplier(self, ctx: commands.Context, level_value_multiplier: float):
        """Usage: `set level_value_multiplier (value: int)`
        Purpose: Sets coefficient for levelling calculations
        Notes: moderator and above only"""
        config.Misc.change("level_value_multiplier", level_value_multiplier)
        await self.bot.reply_to_msg(ctx.message, "The level value multiplier has been changed!")

    @commands.check(common.mod_only)
    @BaseCmds.set.command(name="xp_gain_value")
    async def set_xp_gain_value(self, ctx: commands.Context, xp_gain_value: int):
        """Usage: `set xp_gain_value (value: int)`
        Purpose: Sets amount gained per valid message (see xp_gain_delay)
        Notes: moderator and above only"""
        config.Misc.change("xp_gain_value", xp_gain_value)
        await self.bot.reply_to_msg(ctx.message, "The xp gain value has been changed!")

    @commands.check(common.mod_only)
    @BaseCmds.set.command(name="xp_gain_delay")
    async def set_xp_gain_delay(self, ctx: commands.Context, xp_gain_delay: int):
        """Usage: `set xp_gain_delay (value: int)`
        Purpose: Sets duration before another message sent can trigger another xp increment
        Notes: moderator and above only"""
        config.Misc.change("xp_gain_delay", xp_gain_delay)
        await self.bot.reply_to_msg(ctx.message, "The xp gain delay has been changed!")

    @commands.check(common.mod_only)
    @BaseCmds.set.command(name="levelling_state")
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
        user_meta = config.Users.create_if_missing(user)
        await self.bot.reply_to_msg(ctx.message, f"{user.name} is level {user_meta.rank} with {user_meta.xp_count} xp")

    @BaseCmds.add.command(name="level_role")
    async def add_level_role(self, ctx: commands.Context, role: commands.RoleConverter, rank: int):
        """Usage: `add level_role (role)`
        Purpose: adds a levelling role
        Notes: NOT IMPLEMENTED"""
        role_id = role.id

        if config.DialogflowExceptionRoles.fetch(role_id):
            await self.bot.reply_to_msg(ctx.message, "This role is already a level role")
            return

        config.RankRoles(role_id=role_id, rank=rank)
        await self.bot.reply_to_msg(ctx.message, f"level role {ctx.guild.get_role(role_id).name} added!")

    @BaseCmds.remove.command(name="level_role")
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
