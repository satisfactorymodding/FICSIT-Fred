import nextcord
from nextcord import Interaction, SlashOption, Role, User
from nextcord.ext.commands import Cog

from ._baseclass import BaseCmds, commands, common, config
from ..cogs import levelling
from ..libraries import createembed


class EXPCmds(BaseCmds, Cog):

    @commands.group()
    @commands.check(common.mod_only)
    async def xp(self, ctx: commands.Context):
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
        target: User
        profile = levelling.UserProfile(target.id, ctx.guild)
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
        target: User
        profile = levelling.UserProfile(target.id, ctx.guild)
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
        target: User
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
        target: User
        profile = levelling.UserProfile(target.id, ctx.guild)

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

    #      Leaderboard Command
    async def leaderboard(self, ctx_or_interaction, ephemeral: bool) -> None:
        query = config.Users.select().orderBy("-xp_count").limit(10)
        results = list(query)
        if not results:
            if isinstance(ctx_or_interaction, commands.Context):
                await self.bot.reply_to_msg(
                    ctx_or_interaction.message, "The database was empty. This should NEVER happen"
                )
            elif isinstance(ctx_or_interaction, nextcord.Interaction):
                await ctx_or_interaction.response.send_message(
                    "The database was empty. This should NEVER happen", ephemeral=ephemeral
                )
            return

        data = []
        for db_user in results:
            fetched_user = self.bot.get_user(db_user.user_id)
            if fetched_user is None:
                raise LookupError(f"Unable to find user with ID {db_user.user_id}")
            data.append({"name": fetched_user.global_name, "xp": db_user.xp_count, "rank": db_user.rank})

        embed = createembed.leaderboard(data)
        if isinstance(ctx_or_interaction, commands.Context):
            await self.bot.reply_to_msg(ctx_or_interaction.message, embed=embed)
        elif isinstance(ctx_or_interaction, nextcord.Interaction):
            await ctx_or_interaction.response.send_message(embed=embed, ephemeral=ephemeral)

    @commands.command()
    async def leaderboard(self, ctx: commands.Context):
        """Usage: `leaderboard`
        Response: Shows the top 10 most talkative members and their xp"""
        await self.leaderboard(ctx, ephemeral=False)

    @nextcord.slash_command(name="leaderboard", description="Shows the top 10 most talkative members and their xp.")
    async def leaderboard_slash(
        self,
        interaction: Interaction,
        private_command: bool = SlashOption(description="Only you can see the response", default=False),
    ):
        await self.leaderboard(interaction, ephemeral=private_command)

    #       Level Command
    async def handle_level(self, ctx_or_interaction, ephemeral: bool, target_user: User = None) -> None:
        target_user: User
        if target_user:
            user_id = target_user.id
            user = self.bot.get_user(user_id)
            if not user:
                if isinstance(ctx_or_interaction, commands.Context):
                    await self.bot.reply_to_msg(
                        ctx_or_interaction.message, f"Sorry, I was unable to find the user with id {user_id}"
                    )
                elif isinstance(ctx_or_interaction, nextcord.Interaction):
                    await ctx_or_interaction.response.send_message(
                        f"Sorry, I was unable to find the user with id {user_id}", ephemeral=ephemeral
                    )
                return
        else:
            user = ctx_or_interaction.author
            if isinstance(ctx_or_interaction, commands.Context):
                user = ctx_or_interaction.author
            elif isinstance(ctx_or_interaction, nextcord.Interaction):
                user = ctx_or_interaction.user
        user_meta = config.Users.create_if_missing(user)
        if isinstance(ctx_or_interaction, commands.Context):
            await self.bot.reply_to_msg(
                ctx_or_interaction.message, f"{user.name} is level {user_meta.rank} with {user_meta.xp_count} xp"
            )
        elif isinstance(ctx_or_interaction, nextcord.Interaction):
            await ctx_or_interaction.response.send_message(
                f"{user.name} is level {user_meta.rank} with {user_meta.xp_count} xp", ephemeral=False
            )

    @commands.command()
    async def level(self, ctx: commands.Context, target_user: commands.UserConverter = None):
        """Usage: `level` [user]
        Response: Either your level or the level of the user specified
        Notes: the user parameter can be the user's @ mention or their UID, like 506192269557366805"""
        await self.handle_level(ctx, target_user, ephemeral=False)

    @nextcord.slash_command(name="level", description="Shows either your level or the level of the user specified.")
    async def level_slash(
        self,
        interaction: Interaction,
        target_user: User = SlashOption(description="The user to get the level of", required=False),
        private_command: bool = SlashOption(description="Only you can see the response", default=True),
    ):
        await self.handle_level(interaction, target_user, ephemeral=private_command)

    @BaseCmds.add.command(name="level_role")
    async def add_level_role(self, ctx: commands.Context, role: commands.RoleConverter, rank: int):
        """Usage: `add level_role (role)`
        Purpose: adds a levelling role
        Notes: NOT IMPLEMENTED"""
        role: Role
        role_id = role.id

        if config.RankRoles.check(role_id):
            await self.bot.reply_to_msg(ctx.message, "This role is already a level role")
            return

        config.RankRoles(role_id=role_id, rank=rank)
        await self.bot.reply_to_msg(ctx.message, f"level role {ctx.guild.get_role(role_id).name} added!")

    @BaseCmds.remove.command(name="level_role")
    async def remove_level_role(self, ctx: commands.Context, role: commands.RoleConverter):
        """Usage: `remove level_role (role)`
        Purpose: removes a levelling role
        Notes: NOT IMPLEMENTED"""
        role: Role
        role_id = role.id

        if config.RankRoles.fetch_by_role(role_id):
            config.RankRoles.deleteBy(role_id=role_id)
            await self.bot.reply_to_msg(ctx.message, "level role removed!")
        else:
            await self.bot.reply_to_msg(ctx.message, "level role could not be found!")
