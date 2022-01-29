from fred_core_imports import *

from functools import lru_cache

logger = logging.Logger("PERMISSIONS")


def is_bot_author(user_id: int):
    logger.info("Checking if someone is the author", extra={"user_id": user_id})
    return user_id == 227473074616795137


async def t3_only(ctx):
    logger.info("Checking if someone is a T3", extra=userdict(ctx.author))
    return is_bot_author(ctx.author.id) or permission_check(ctx, 4)


async def mod_only(ctx):
    logger.info("Checking if someone is a Moderator", extra=userdict(ctx.author))
    return is_bot_author(ctx.author.id) or permission_check(ctx, 6)


def permission_check(ctx, level: int):
    logpayload = userdict(ctx.author)
    logpayload['level'] = level
    logger.info("Checking permissions for someone", extra=logpayload)
    perms = config.PermissionRoles.fetch_by_lvl(level)
    main_guild = ctx.bot.get_guild(config.Misc.fetch("main_guild_id"))
    if (main_guild_member := main_guild.get_member(ctx.author.id)) is None:
        logger.warning("Checked permissions for someone but they weren't in the main guild", extra=logpayload)
        return False

    user_roles = [role.id for role in main_guild_member.roles]

    for clearance in perms:
        if clearance.perm_lvl >= level:
            if clearance.role_id in user_roles:
                logger.info(f"A permission check was positive with level {clearance.perm_lvl}", extra=logpayload)
                return True
        else:
            logger.info(f"A permission check was negative with level less than required ({clearance.perm_lvl}<",
                        extra=logpayload)
            break

    return False


@lru_cache(5)
def userdict(user):
    if user is None:
        return {}
    return {'user_full_name': str(user), 'user_id': user.id}


@lru_cache(5)
def messagedict(message):
    if message is None:
        return {}
    return {'message_id': message.id, 'channel_id': message.channel.id, 'user_id': message.author.id}


def reduce_str(string: str) -> str:
    # reduces a string into something that's more comparable
    return ''.join(string.split()).lower()


def mod_name_eq(name1: str, name2: str) -> bool:
    return reduce_str(name1) == reduce_str(name2)
