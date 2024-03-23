from __future__ import annotations

import logging
import math
from datetime import *

import nextcord.ext.commands as commands
from nextcord import DMChannel

import config
from libraries import common


class UserProfile:
    def __init__(self, user_id, guild, bot):
        self.guild = guild
        self.bot = bot
        self.user_id = user_id
        self.logger = logging.Logger("USERPROFILE")

        assert bot.intents.members, "The bot has no member intents, so it cannot do levelling!!"
        self.member = bot.get_user(user_id)
        assert self.member is not None, "This member does not exist o.0"
        self.logger.info(f"Found member id {self.member}")

        if DB_user := config.Users.fetch(user_id):
            self.DB_user = DB_user
        else:
            self.DB_user = config.Users(user_id=user_id, full_name=f"{self.member.name}#{self.member.discriminator}")

        self.rank = self.DB_user.rank
        self.xp_count = self.DB_user.xp_count

    async def validate_role(self):
        if not self.member:
            self.logger.info(
                "Could not validate someone's level role because they aren't in the main guild",
                extra={"user_id": self.user_id},
            )
            return
        logpayload = common.user_info(self.member)
        if role_id := config.RankRoles.fetch_by_rank(self.rank):
            role = self.guild.get_role(role_id)
            if not role:
                logpayload["role_id"] = role_id
                self.logger.warning(
                    "Could not validate someone's level role because the role isn't in the main guild", extra=logpayload
                )
                return
            self.DB_user.rank_role_id = role_id
            # self.rank_role_id = role_id
            if not self.member.permissions_in(self.bot.modchannel).send_messages:
                for member_role in self.member.roles:
                    if rank := config.RankRoles.fetch_by_role(member_role.id):
                        logpayload["role_id"] = member_role.id
                        self.logger.info("Removing a mismatched level role from someone", extra=logpayload)
                        await self.member.remove_roles(member_role)
                logpayload["role_id"] = role.id
                self.logger.info("Removing a mismatched level role from someone", logpayload)
                await self.member.add_roles(role)

    async def validate_level(self):
        if not self.member:
            self.logger.info(
                "Could not validate someone's level because they aren't in the main guild",
                extra={"user_id": self.user_id},
            )
            return
        logpayload = common.user_info(self.member)
        expected_level = math.log(self.xp_count / config.Misc.fetch("base_level_value")) / math.log(
            config.Misc.fetch("level_value_multiplier")
        )
        if expected_level < 0:
            expected_level = 0
        else:
            expected_level += 1
        expected_level = int(expected_level)
        logpayload["expected_level"] = expected_level
        logpayload["current_level"] = self.rank
        if expected_level != self.rank:
            self.logger.info("Correcting a mismatched level", extra=logpayload)
            self.DB_user.rank = expected_level
            if self.DB_user.accepts_dms:
                if expected_level > self.rank:
                    await self.bot.send_DM(
                        self.member,
                        f"You went up from level {self.rank} to level {expected_level}! " f"Congratulations!",
                    )
                else:
                    await self.bot.send_DM(
                        self.member,
                        f"You went down from level {self.rank} to level {expected_level}... " f"Sorry about that",
                    )
        await self.validate_role()

    async def increment_xp(self):
        xp_gain = config.Misc.fetch("xp_gain_value") * self.DB_user.xp_multiplier * self.DB_user.role_xp_multiplier
        logpayload = common.user_info(self.member)
        logpayload["xp_increment"] = xp_gain
        self.logger.info("Incrementing someone's xp", logpayload)
        await self.give_xp(xp_gain)

    async def give_xp(self, xp):
        if xp <= 0:
            return
        logpayload = common.user_info(self.member)
        logpayload["xp_gain"] = xp
        self.logger.info("Giving someone xp", logpayload)
        self.DB_user.xp_count += xp
        self.xp_count += xp
        await self.validate_level()
        return True

    async def take_xp(self, xp):
        if xp > self.DB_user.xp_count:
            return False  # can't take more than a user has

        logpayload = common.user_info(self.member)
        logpayload["xp_loss"] = xp
        self.logger.info("Taking xp from someone", logpayload)
        self.DB_user.xp_count -= xp
        self.xp_count -= xp
        await self.validate_level()
        return True

    async def set_xp(self, xp):
        logpayload = common.user_info(self.member)
        logpayload["new_xp"] = xp
        self.logger.info("Setting someone's xp", logpayload)
        self.DB_user.xp_count = xp
        self.xp_count = xp
        await self.validate_level()
        return True


class Levelling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.xp_timers = {}
        self.logger = logging.Logger("LEVELLING")

    # TODO make xp roles
    # @commands.Cog.listener()
    # async def on_member_update(self, before, after):
    #     if before.roles != after.roles:
    #         config.XpRoles

    @commands.Cog.listener()
    async def on_message(self, message):
        self.logger.info("Levelling: Processing message", extra=common.message_info(message))
        if (
            message.author.bot
            or isinstance(message.channel, DMChannel)
            or message.guild.id != config.Misc.fetch("main_guild_id")
            or not config.Misc.fetch("levelling_state")
        ):
            return

        profile = UserProfile(message.author.id, message.guild, self.bot)
        profile.DB_user.message_count += 1
        if profile.user_id in self.bot.xp_timers:
            if datetime.now() >= self.bot.xp_timers[profile.user_id]:
                await profile.increment_xp()
            else:
                self.logger.info(
                    "Levelling: Someone sent a message too fast and will not be awarded xp",
                    extra=common.message_info(message),
                )
        self.bot.xp_timers[profile.user_id] = datetime.now() + timedelta(seconds=config.Misc.fetch("xp_gain_delay"))
