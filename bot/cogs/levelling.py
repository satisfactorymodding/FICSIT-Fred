import discord.ext.commands as commands
from discord import DMChannel

import config
from datetime import *
import math


class UserProfile:
    def __init__(self, user_id, guild, bot):
        self.guild = guild
        self.bot = bot
        self.user_id = user_id
        self.member = guild.get_member(self.user_id)
        if DB_user := config.Users.fetch(self.user_id):
            self.DB_user = DB_user
        else:
            self.DB_user = config.Users(user_id=user_id,
                                        full_name="{}#{}".format(self.member.name, self.member.discriminator))

        self.rank = self.DB_user.rank
        self.xp_count = self.DB_user.xp_count

    async def validate_role(self):
        if not self.member:
            self.bot.logger.warning("I was unable to validate a role because I could not get the member")
        if role_id := config.RankRoles.fetch_by_rank(self.rank):
            role = self.guild.get_role(role_id)
            if not role:
                self.bot.logger.warning("I was unable to validate a role because I could not get a role")
                return
            self.DB_user.rank_role_id = role_id
            # self.rank_role_id = role_id
            if not self.member.permissions_in(self.bot.modchannel).send_messages:
                for memberrole in self.member.roles:
                    rank = config.RankRoles.fetch_by_role(memberrole.id)
                    if rank:
                        await self.member.remove_roles(memberrole)
                await self.member.add_roles(role)

    async def validate_rank(self):
        expected_rank = math.log(self.xp_count / config.Misc.fetch("base_rank_value")) / math.log(
            config.Misc.fetch("rank_value_multiplier"))
        if expected_rank < 0:
            expected_rank = 0
        else:
            expected_rank += 1
        expected_rank = int(expected_rank)
        if expected_rank != self.rank:
            self.bot.logger.info("Correcting a mismatched rank from {} to {}".format(self.rank, expected_rank))
            self.DB_user.rank = expected_rank
            if self.DB_user.accepts_dms:
                if expected_rank > self.rank:
                    await self.bot.send_DM(self.member, "You went up from rank {} to rank {} ! Congratulations !".format(self.rank, expected_rank))
                else:
                    await self.bot.send_DM(self.member, "You went down from rank {} to rank {}.. Sorry about that".format(self.rank, expected_rank))
            self.rank = expected_rank
        await self.validate_role()

    async def give_xp(self, xp):
        self.DB_user.xp_count += xp
        self.xp_count += xp
        await self.validate_rank()

    async def take_xp(self, xp):
        self.DB_user.xp_count -= xp
        self.xp_count -= xp
        await self.validate_rank()

    async def set_xp(self, xp):
        self.DB_user.xp_count = xp
        self.xp_count = xp
        await self.validate_rank()


class Levelling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.xp_timers = {}

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or isinstance(message.channel, DMChannel) or \
                message.guild.id != config.Misc.fetch("main_guild_id") or not config.Misc.fetch("levelling_state"):
            return
        profile = UserProfile(message.author.id, message.guild, self.bot)
        profile.DB_user.message_count += 1
        if profile.user_id in self.bot.xp_timers:
            if datetime.now() >= self.bot.xp_timers[profile.user_id]:
                await profile.give_xp(config.Misc.fetch("xp_gain_value"))
        else:
            self.bot.xp_timers[profile.user_id] = datetime.now() + timedelta(seconds=config.Misc.fetch("xp_gain_delay"))
            await profile.give_xp(config.Misc.fetch("xp_gain_value"))
