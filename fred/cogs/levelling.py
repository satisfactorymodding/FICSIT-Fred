from __future__ import annotations

import logging
import math
from datetime import *

from nextcord import DMChannel, Message, Guild
from nextcord.ext.commands import MemberNotFound

from .. import config
from ..libraries import common

logger = common.new_logger(__name__)


class UserProfile:
    def __init__(self, user_id: int, guild: Guild):
        self.guild = guild
        self.user_id = user_id

        self.member = guild.get_member(user_id)
        if self.member is None:
            logger.warning(f"Unable to retrieve information about user {user_id}")
            raise MemberNotFound(f"Unable to retrieve information about user {user_id}")

        logger.info(f"Found member id {self.member}")

        if DB_user := config.Users.fetch(user_id):
            self.DB_user = DB_user
        else:
            self.DB_user = config.Users(user_id=user_id)

        self._rank: int = DB_user.rank
        self._xp_count: int = DB_user.xp_count

    @property
    def rank(self):
        return self._rank

    @rank.setter
    def rank(self, value: int):
        self._rank = value
        self.DB_user.rank = value

    @property
    def xp_count(self):
        return self._xp_count

    @xp_count.setter
    def xp_count(self, value: int):
        self._xp_count = value
        self.DB_user.xp_count = value

    async def validate_role(self):
        if not self.member:
            logger.info(
                "Could not validate someone's level role because they aren't in the main guild",
                extra={"user_id": self.user_id},
            )
            return
        logpayload = common.user_info(self.member)
        if role_id := config.RankRoles.fetch_by_rank(self.rank):
            role = self.guild.get_role(role_id)
            if not role:
                logpayload["role_id"] = role_id
                logger.warning(
                    "Could not validate someone's level role because the role isn't in the main guild", extra=logpayload
                )
                return
            self.DB_user.rank_role_id = role_id

            # if not self.guild.get_channel(config.Misc.fetch("mod_channel")).permissions_for(self.member).send_messages:
            if not common.permission_check(self.member, level=6):
                for member_role in self.member.roles:
                    if config.RankRoles.fetch_by_role(member_role.id) is not None:  # i.e. member_role is a rank role
                        logpayload["role_id"] = member_role.id
                        logger.info("Removing a mismatched level role from someone", extra=logpayload)
                        await self.member.remove_roles(member_role)
                logpayload["role_id"] = role.id
                logger.info("Removing a mismatched level role from someone", logpayload)
                await self.member.add_roles(role)

    async def validate_level(self):
        if not self.member:
            logger.info(
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
            logger.info("Correcting a mismatched level", extra=logpayload)
            if self.DB_user.accepts_dms:
                if expected_level > self.rank:
                    await Levelling.bot.send_DM(
                        self.member,
                        f"You went up from level {self.rank} to level {expected_level}! " f"Congratulations!",
                    )
                else:
                    await Levelling.bot.send_DM(
                        self.member,
                        f"You went down from level {self.rank} to level {expected_level}... " f"Sorry about that",
                    )
            self.rank = expected_level
        await self.validate_role()

    async def increment_xp(self):
        xp_gain = config.Misc.fetch("xp_gain_value") * self.DB_user.xp_multiplier * self.DB_user.role_xp_multiplier
        logpayload = common.user_info(self.member)
        logpayload["xp_increment"] = xp_gain
        logger.info("Incrementing someone's xp", logpayload)
        await self.give_xp(xp_gain)

    async def give_xp(self, xp):
        if xp <= 0:
            return
        logpayload = common.user_info(self.member)
        logpayload["xp_gain"] = xp
        logger.info("Giving someone xp", logpayload)
        self.xp_count += xp
        await self.validate_level()
        return True

    async def take_xp(self, xp):
        if xp > self.xp_count:
            return False  # can't take more than a user has

        logpayload = common.user_info(self.member)
        logpayload["xp_loss"] = xp
        logger.info("Taking xp from someone", logpayload)
        self.xp_count -= xp
        await self.validate_level()
        return True

    async def set_xp(self, xp):
        logpayload = common.user_info(self.member)
        logpayload["new_xp"] = xp
        logger.info("Setting someone's xp", logpayload)
        self.xp_count = xp
        await self.validate_level()
        return True


class Levelling(common.FredCog):
    xp_timers = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.xp_timers = {}

    # TODO make xp roles
    # @commonn.FredCog.listener()
    # async def on_member_update(self, before, after):
    #     if before.roles != after.roles:
    #         config.XpRoles

    @common.FredCog.listener()
    async def on_message(self, message: Message):
        self.logger.info("Levelling: Processing message", extra=common.message_info(message))
        if (
            message.author.bot
            or isinstance(message.channel, DMChannel)
            or message.guild.id != config.Misc.fetch("main_guild_id")
            or not config.Misc.fetch("levelling_state")
        ):
            return

        profile = UserProfile(message.author.id, message.guild)
        profile.DB_user.message_count += 1
        if profile.user_id in self.xp_timers:
            if datetime.now() >= self.xp_timers[profile.user_id]:
                await profile.increment_xp()
            else:
                self.logger.info(
                    "Levelling: Someone sent a message too fast and will not be awarded xp",
                    extra=common.message_info(message),
                )
        self.xp_timers[profile.user_id] = datetime.now() + timedelta(seconds=config.Misc.fetch("xp_gain_delay"))
