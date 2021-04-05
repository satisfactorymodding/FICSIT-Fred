import discord.ext.commands as commands
from discord import DMChannel

import config
from datetime import *
import math


class UserProfile:
    def __init__(self, DB_user, guild, bot):
        self.guild = guild
        self.bot = bot
        self.DB_user = DB_user
        self.user_id = DB_user.user_id
        self.message_count = DB_user.message_count
        self.xp_count = DB_user.xp_count
        self.rank_role_id = DB_user.rank_role_id
        self.rank = DB_user.rank
        self.rankup_notifications = DB_user.rankup_notifications

        self.member = guild.get_member(self.user_id)

    async def validate_role(self):
        if not self.member:
            self.bot.logger.warning("I was unable to validate a role because I could not get the member")
        if role_id := config.RankRoles.fetch_by_rank(self.rank):
            role = self.guild.get_role(role_id)
            if not role:
                self.bot.logger.warning("I was unable to validate a role because I could not get a role")
                return
            self.DB_user.rank_role_id = role_id
            self.rank_role_id = role_id
            if not self.member.permissions_in(self.bot.modchannel).send_messages:
                for memberrole in self.member.roles:
                    rank = config.RankRoles.fetch_by_role(memberrole.id)
                    if rank:
                        await self.member.remove_roles(memberrole)
                await self.member.add_roles(role)

        elif self.rank > 0:
            self.bot.logger.warning("There was no valid role for the rank " + str(self.rank))

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
            old_rank = self.rank
            self.rank = expected_rank
            self.DB_user.rank = expected_rank
            if self.rankup_notifications:
                if not self.member.dm_channel:
                    await self.member.create_dm()
                if expected_rank > old_rank:
                    try:
                        await self.member.dm_channel.send("You went up in rank ! Congratulations ! Look at you and "
                                                          "your shiny new role and colour\n(If you wish that I do not "
                                                          "send you a DM next time, simply say 'stop'. You can "
                                                          "reactivate it with 'start')")
                    except:
                        pass
                else:
                    try:
                        await self.member.dm_channel.send("You went down in rank.. This is weird. Maybe the admins "
                                                          "changed some experience values. Sorry about that ! But "
                                                          "maybe it's normal\n(If you wish that I do not send you a "
                                                          "DM next time, simply say 'stop'. You can reactivate it "
                                                          "with 'start')")
                    except:
                        pass
        await self.validate_role()

    async def give_xp(self, xp):
        self.xp_count += xp
        self.DB_user.xp_count += xp
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
        if DBUser := config.Users.fetch(message.author.id):
            DBUser.message_count += 1
            profile = UserProfile(DBUser, message.guild, self.bot)
            if profile.user_id in self.bot.xp_timers:
                if datetime.now() >= self.bot.xp_timers[profile.user_id]:
                    await profile.give_xp(config.Misc.fetch("xp_gain_value"))
            else:
                self.bot.xp_timers[profile.user_id] = datetime.now() + timedelta(
                    seconds=config.Misc.fetch("xp_gain_delay"))
                await profile.give_xp(config.Misc.fetch("xp_gain_value"))
        else:
            config.Users(user_id=message.author.id, message_count=1, xp_count=config.Misc.fetch("xp_gain_value"),
                         rank_role_id=None, rank=0,
                         full_name="{}#{}".format(message.author.name, message.author.discriminator))
            self.bot.xp_timers[message.author.id] = datetime.now() + timedelta(
                seconds=config.Misc.fetch("xp_gain_delay"))
