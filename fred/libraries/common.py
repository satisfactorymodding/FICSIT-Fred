from __future__ import annotations

import logging
from functools import lru_cache, singledispatch
from io import BytesIO
from typing import TYPE_CHECKING, Optional

from nextcord import User, Message, Member, Guild, NotFound, File, Interaction
from nextcord.ext import commands
from nextcord.ext.commands import Context
from uwuipy import Uwuipy

from .. import config

if TYPE_CHECKING:
    from ..fred import Bot


def new_logger(name: str) -> logging.Logger:
    logging.root.debug("Creating new logger for %s", name)
    new_logger_ = logging.root.getChild(name)
    new_logger_.setLevel(new_logger_.parent.level)
    return new_logger_


logger = new_logger(__name__)


class FredCog(commands.Cog):
    bot: Bot = ...  # we can assume any cog will have a bot by the time it needs to be accessed

    def __init__(self, bot: Bot):
        self.__class__.bot = bot
        self.bot = bot
        self.logger = new_logger(self.__class__.__name__)
        self.logger.debug("Cog loaded.")


async def get_guild_member(guild: Guild, user_id: int) -> Optional[Member]:
    try:
        return guild.get_member(user_id) or await guild.fetch_member(user_id)
    except NotFound:
        return None


async def l4_only(ctx: Context | Interaction) -> bool:
    return await permission_check(ctx, level=4)


async def mod_only(ctx: Context | Interaction) -> bool:
    return await permission_check(ctx, level=6)


@singledispatch
async def permission_check(_ctx_or_member, *, level: int) -> bool: ...


@permission_check.register
async def _permission_check_itr(itr: Interaction, *, level: int) -> bool:
    logger.info(f"Checking if a user (from an Interaction) has permission level {level}", extra=user_info(itr.user))
    main_guild_id = config.Misc.fetch("main_guild_id")
    main_guild = await itr.client.fetch_guild(main_guild_id)

    if main_guild is None:
        raise LookupError(f"Unable to retrieve the guild {main_guild_id}. Is this the guild you meant?")

    if (main_guild_member := await get_guild_member(main_guild, itr.user.id)) is None:
        logger.warning(
            "Checked permissions for someone but they weren't in the main guild",
            extra=user_info(itr.user),
        )
        return False

    return await _permission_check_member(main_guild_member, threshold_level=level)


@permission_check.register
async def _permission_check_ctx(ctx: Context, *, level: int) -> bool:

    logger.info(f"Checking if a user (from a Context) has permission level {level}", extra=user_info(ctx.author))

    main_guild_id = config.Misc.fetch("main_guild_id")
    main_guild = await ctx.bot.fetch_guild(main_guild_id)

    if main_guild is None:
        raise LookupError(f"Unable to retrieve the guild {main_guild_id}. Is this the guild you meant?")

    if (main_guild_member := await get_guild_member(main_guild, ctx.author.id)) is None:
        logger.warning(
            "Checked permissions for someone but they weren't in the main guild",
            extra=user_info(ctx.author),
        )
        return False

    return await _permission_check_member(main_guild_member, threshold_level=level)


@permission_check.register
async def _permission_check_member(member: Member, *, threshold_level: int) -> bool:
    """Checks permissions for a member assuming they are in the main guild."""

    logger.info(f"Checking if a user (from a Member) has permission level {threshold_level}", extra=user_info(member))

    logpayload = user_info(member)
    logpayload["level"] = threshold_level

    if member.guild.id != config.Misc.fetch("main_guild_id"):
        logger.warning("Checked permissions for a member of the wrong guild", extra=logpayload)
        return False

    logger.info(
        f"Checking permissions for {member.display_name} ({member.id})",
        extra=logpayload,
    )

    user_roles = {role.id for role in member.roles}
    perm_roles = config.PermissionRoles.fetch_ge_lvl(threshold_level)
    user_roles_above_threshold = {role for role in perm_roles if role.role_id in user_roles}

    if user_roles_above_threshold:
        user_max_perm = max(user_roles_above_threshold, key=lambda role: role.perm_lvl)
        logger.info(
            f"Permission granted for {member.display_name} (lvl {user_max_perm.perm_lvl}, threshold {threshold_level})",
            extra=logpayload,
        )
        return True  # user has a role that is above the requested level
    else:
        logger.info(
            f"Permission denied for {member.display_name} - does not have any permission roles above the required level.",
            extra=logpayload,
        )
        return False


@lru_cache(15)
def user_info(user: Optional[User | Member]) -> dict:
    if user is None:
        return {}
    return {"user_full_name": user.global_name, "user_id": user.id}


@lru_cache(15)
def message_info(message: Optional[Message]) -> dict:
    if message is None:
        return {}
    return {
        "message_id": message.id,
        "channel_id": message.channel.id,
        **user_info(message.author),
    }


def reduce_str(string: str) -> str:
    # reduces a string into something that's more comparable
    return "".join(string.split()).lower()


def mod_name_eq(name1: str, name2: str) -> bool:
    return reduce_str(name1) == reduce_str(name2)


_owoizer = Uwuipy(stutter_chance=0.05, face_chance=0.05, action_chance=0, power=4)


def owoize(string: Optional[str]) -> Optional[str]:
    return (
        _owoizer.uwuify(
            string,
            skip_urls=True,
        )
        if string is not None
        else None
    )


def text2file(content: str, filename="file") -> File:
    return File(BytesIO(content.encode()), filename=filename)
