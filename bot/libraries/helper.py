import logging
import re
import asyncio
from html.parser import HTMLParser
import config


def is_bot_author(user_id: int):
    logging.info("Checking if someone is the author", extra={"user_id": user_id})
    return user_id == 227473074616795137


async def t3_only(ctx):
    logging.info("Checking if someone is a T3", extra=userdict(ctx.author))
    return is_bot_author(ctx.author.id) or permission_check(ctx, 4)


async def mod_only(ctx):
    logging.info("Checking if someone is a Moderator", extra=userdict(ctx.author))
    return is_bot_author(ctx.author.id) or permission_check(ctx, 6)


def permission_check(ctx, level: int):
    logpayload = userdict(ctx.author)
    logpayload['level'] = level
    logging.info("Checking permissions for someone", extra=logpayload)
    perms = config.PermissionRoles.fetch_by_lvl(level)
    main_guild = ctx.bot.get_guild(config.Misc.fetch("main_guild_id"))
    if (main_guild_member := main_guild.get_member(ctx.author.id)) is None:
        logging.warning("Checked permissions for someone but they weren't in the main guild", extra=logpayload)
        return False

    has_roles = [role.id for role in (main_guild_member.roles)]

    for role in perms:
        if role.perm_lvl >= level:
            if role.role_id in has_roles:
                logging.info("A permission check was negative", extra=logpayload)
                return True
        else:
            break
    logging.info("A permission check was positive", extra=logpayload)
    return False


async def waitResponse(client, message, question):
    logging.info(f"Waiting for a response", extra=userdict(message.author))
    await client.reply_to_msg(message, question)

    def check(message2):
        return message2.author == message.author

    timeout = 60
    try:
        response = await client.wait_for('message', timeout=timeout, check=check)
    except asyncio.TimeoutError:
        logging.warning(f"Stopped waiting for a response after {timeout} seconds", extra=userdict(message.author))
        await client.reply_to_msg(message, f"Timed out and aborted after {timeout} seconds.")
        raise asyncio.TimeoutError
    logging.info(f"Got a response", extra=userdict(message.author))
    return response.content, response.attachments[0] if response.attachments else None


class aTagParser(HTMLParser):
    link = ''
    view_text = ''

    def clear_output(self):
        self.link = ''
        self.view_text = ''

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for attr in attrs:
                if attr[0] == 'href':
                    self.link = f'({attr[1]})'

    def handle_endtag(self, tag):
        pass

    def handle_data(self, data):
        self.view_text = f'[{data}]'


def formatDesc(desc):
    logging.info("Formatting a mod description")
    revisions = {
        "<b>": "**",
        "</b>": "**",
        "<u>": "__",
        "</u>": "__",
        "<br>": "",
    }
    for old, new in revisions.items():
        desc = desc.replace(old, new)
    items = []
    embeds = dict()
    items.extend([i.groups() for i in re.finditer('(<a.+>.+</a>)', desc)])  # Finds all unhandled links
    for i in items:
        i = i[0]  # regex returns a one-element tuple :/
        parser = aTagParser()
        parser.feed(i)
        embeds.update({i: parser.view_text + parser.link})
    for old, new in embeds.items():
        desc = desc.replace(old, new)

    desc = re.sub('#+ ', "", desc)
    return desc


def fullname(user):
    return f"{user.name}#{user.discriminator}"


def userdict(user):
    if user is None:
        return {}
    return {'user_full_name': fullname(user), 'user_id': user.id}


def messagedict(message):
    if message is None:
        return {}
    return {'message_id': message.id, 'channel_id': message.channel.id, 'user_id': message.author.id}
