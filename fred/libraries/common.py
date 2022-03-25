import logging
from functools import lru_cache

from nextcord import User, Message
from nextcord.ext.commands import Context

from .. import config

logger = logging.Logger("PERMISSIONS")


def is_bot_author(user_id: int) -> bool:
    logger.info("Checking if someone is the author", extra={"user_id": user_id})
    return user_id == 227473074616795137


async def l4_only(ctx: Context) -> bool:
    logger.info("Checking if someone is a T3", extra=user_info(ctx.author))
    return is_bot_author(ctx.author.id) or permission_check(ctx, 4)


async def mod_only(ctx: Context) -> bool:
    logger.info("Checking if someone is a Moderator", extra=user_info(ctx.author))
    return is_bot_author(ctx.author.id) or permission_check(ctx, 6)


def permission_check(ctx: Context, level: int) -> bool:
    logpayload = user_info(ctx.author)
    logpayload["level"] = level
    logger.info("Checking permissions for someone", extra=logpayload)
    perms = config.PermissionRoles.fetch_by_lvl(level)
    main_guild = ctx.bot.get_guild(config.Misc.fetch("main_guild_id"))
    if (main_guild_member := main_guild.get_member(ctx.author.id)) is None:
        logger.warning("Checked permissions for someone but they weren't in the main guild", extra=logpayload)
        return False

    user_roles = [role.id for role in main_guild_member.roles]
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


@lru_cache(5)
def user_info(user: User | config.Users) -> dict:
    if isinstance(user, User):
        return {"user_full_name": str(user), "user_id": user.id}
    elif isinstance(user, config.Users):
        return {"user_full_name": user.full_name, "user_id": user.id}
    return {}


@lru_cache(5)
def message_info(message: Message) -> dict:
    if message is None:
        return {}
    return {"message_id": message.id, "channel_id": message.channel.id, "user_id": message.author.id}


def reduce_str(string: str) -> str:
    # reduces a string into something that's more comparable
    return "".join(string.split()).lower()


def mod_name_eq(name1: str, name2: str) -> bool:
    return reduce_str(name1) == reduce_str(name2)
