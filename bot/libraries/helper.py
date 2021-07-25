import re
import asyncio
from html.parser import HTMLParser
import config

async def t3_only(ctx):
    return ctx.author.id == 227473074616795137 or permission_check(ctx.author, 2)


def permission_check(member, level:int):
    perms = config.PermissionRoles.fetch_by_lvl(level)
    has_roles = [role.id for role in member.roles]
    for role in perms:
        if role.perm_lvl >= level:
            if role.role_id in has_roles:
                return True
        else:
            break
    return False


async def mod_only(ctx):
    return ctx.author.id == 227473074616795137 or permission_check(ctx.author, 3)


async def waitResponse(client, message, question):
    await client.reply_to_msg(message, question)

    def check(message2):
        return message2.author == message.author

    try:
        response = await client.wait_for('message', timeout=60.0, check=check)
    except asyncio.TimeoutError:
        await client.reply_to_msg(message, "Timed out and aborted after 30 seconds.")
        raise asyncio.TimeoutError

    return response.content, response.attachments[0] if response.attachments else None


class aTagParser(HTMLParser):
    link = ''
    viewtext = ''

    def clear_output(self):
        self.link = ''
        self.viewtext = ''

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for attr in attrs:
                if attr[0] == 'href':
                    self.link = f'({attr[1]})'

    def handle_endtag(self, tag):
        pass

    def handle_data(self, data):
        self.viewtext = f'[{data}]'


def formatDesc(desc):
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
        embeds.update({i: parser.viewtext + parser.link})
    for old, new in embeds.items():
        desc = desc.replace(old, new)

    desc = re.sub('#+ ', "", desc)
    return desc
