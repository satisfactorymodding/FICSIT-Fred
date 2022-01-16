from fred_core_imports import *

from html.parser import HTMLParser


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

    user_roles = [role.id for role in main_guild_member.roles]

    for clearance in perms:
        if clearance.perm_lvl >= level:
            if clearance.role_id in user_roles:
                logging.info(f"A permission check was positive with level {clearance.perm_lvl}", extra=logpayload)
                return True
        else:
            logging.info(f"A permission check was negative with level less than required ({clearance.perm_lvl}<",
                         extra=logpayload)
            break

    return False


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
