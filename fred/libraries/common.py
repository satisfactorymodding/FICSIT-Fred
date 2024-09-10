from __future__ import annotations

import logging
import re
from functools import lru_cache, singledispatch
from typing import TYPE_CHECKING, Optional

from nextcord import User, Message, Member
from nextcord.ext import commands
from nextcord.ext.commands import Context

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


def is_bot_author(user_id: int) -> bool:
    logger.info("Checking if someone is the author", extra={"user_id": user_id})
    return user_id == 227473074616795137


async def l4_only(ctx: Context) -> bool:
    logger.info("Checking if someone is a T3", extra=user_info(ctx.author))
    return is_bot_author(ctx.author.id) or permission_check(ctx, level=4)


async def mod_only(ctx: Context) -> bool:
    logger.info("Checking if someone is a Moderator", extra=user_info(ctx.author))
    return is_bot_author(ctx.author.id) or permission_check(ctx, level=6)


@singledispatch
def permission_check(_, *, level: int) -> bool:
    pass


@permission_check.register
def _permission_check_ctx(ctx: Context, *, level: int) -> bool:
    main_guild_id = config.Misc.fetch("main_guild_id")
    main_guild = ctx.bot.get_guild(main_guild_id)

    if main_guild is None:
        raise LookupError(f"Unable to retrieve the guild {main_guild_id}. Is this the guild you meant?")

    if (main_guild_member := main_guild.get_member(ctx.author.id)) is None:
        logger.warning(
            "Checked permissions for someone but they weren't in the main guild", extra=user_info(ctx.author)
        )
        return False

    return _permission_check_member(main_guild_member, level=level)


@permission_check.register
def _permission_check_member(member: Member, *, level: int) -> bool:
    """Checks permissions for a member assuming they are in the main guild."""
    logpayload = user_info(member)
    logpayload["level"] = level

    if member.guild.id != config.Misc.fetch("main_guild_id"):
        logger.warning("Checked permissions for a member of the wrong guild", extra=logpayload)
        return False

    logger.info("Checking permissions for someone", extra=logpayload)
    perms = config.PermissionRoles.fetch_by_lvl(level)

    user_roles = [role.id for role in member.roles]
    if (
        # it shouldn't be possible to request a level above the defined levels but check anyway
        role := next(
            (permission for permission in perms if permission.perm_lvl >= level and permission.role_id in user_roles),
            False,
        )  # checks for the first occurring, if any
    ):
        logger.info(f"A permission check was positive with level {role.perm_lvl}", extra=logpayload)
        return True  # user has a role that is above the requested level

    logger.info(f"A permission check was negative with level less than required ({level})", extra=logpayload)
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
    return {"message_id": message.id, "channel_id": message.channel.id, **user_info(message.author)}


def reduce_str(string: str) -> str:
    # reduces a string into something that's more comparable
    return "".join(string.split()).lower()


def mod_name_eq(name1: str, name2: str) -> bool:
    return reduce_str(name1) == reduce_str(name2)


owo_table = {
    r"\bth([aeiou])": r"d\1",
    r"\bTh([aeiou])": r"D\1",
    r"oo": r"uwu",
    r"r": r"w",
    r"R": r"W",
    r"ove": r"uv",
    r"!": r"! OwO ",
    r"(?<![aeiou])n([aeiou])": r"ny\1",
    r"(?<![aeiou])N([aeiou])": r"Ny\1",
    r"you": "u",
    r"You": "U",
    r"fuzzy": r"fuzzy-wuzzy",
}


def owoize(string: str) -> str:
    new_string: list[str] = []
    for line in string.split("\n"):
        new_line: list[str] = []
        for word in line.split():
            if re.match(r"://|`", word) is None:
                for match, sub in owo_table.items():
                    word = re.sub(match, sub, word)
            new_line.append(word)
        new_string.append(" ".join(new_line))

    return "\n".join(new_string)
