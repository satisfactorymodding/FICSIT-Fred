from __future__ import annotations

from functools import lru_cache
import re
from typing import Coroutine

import attrs
import config
import logging
import nextcord
from nextcord.ext.commands import Cog

page_size: int = 30               # if you change this, make it a multiple of three
field_size: int = page_size // 3  # because inlined fields stack up to three horizontally


@lru_cache
def get_shift(index: int, field_number: int) -> int:
    return field_number + (index * page_size)


@lru_cache
def get_field_indices(index: int, field_number: int) -> str:
    return f"{1 + get_shift(index, field_number)}-{field_size + get_shift(index, field_number)}"


class FredHelpEmbed(nextcord.Embed):
    # these are placeholder values only, they will be set up when setup() is called post-DB connection
    help_colour: int = 0
    prefix: str = '>'

    def __init__(self: FredHelpEmbed, name: str, desc: str, fields: list[dict] = [], **kwargs) -> None:
        desc = re.sub(r"`(.+)`", rf"`{self.prefix}\1`", desc)
        desc = re.sub(r"^\s*(\w+:) ", r"**\1** ", desc, flags=re.MULTILINE)
        super().__init__(title=f"**{name}**", colour=self.help_colour, description=desc, **kwargs)
        for f in fields:
            self.add_field(**f)

    @classmethod
    def setup(cls: type(FredHelpEmbed)) -> None:
        """This is called after the DB has been set up"""
        cls.help_colour = config.ActionColours.fetch("Light Blue")
        cls.prefix = config.Misc.fetch("prefix")

    def __str__(self: FredHelpEmbed) -> str:
        return str(self.to_dict())


def name_is_index(category: str) -> FredHelpEmbed:
    return FredHelpEmbed("Bad input", f"help {category} expected a special command's name, not a number")


def index_is_name(category: str) -> FredHelpEmbed:
    return FredHelpEmbed("Bad input", f"help {category} expected a page number, not a specific name")


def git_webhooks() -> FredHelpEmbed:
    return FredHelpEmbed(
        "GitHub webhooks",
        'I am sent updates from GitHub about the most important modding repositories, '
        f'then publish updates to <#{config.Misc.fetch("githook_channel")}>!'
    )


@attrs.define
class SpecialCommand:
    name: str
    callback: Coroutine
    subcommands: list[SpecialCommand] = attrs.Factory(list)  # use this otherwise everyone gets the ptr to the same list


def _get_specials(commands_class: Cog) -> dict[str, SpecialCommand]:
    specials: dict[str, SpecialCommand] = {}
    for cmd in commands_class.walk_commands():
        name, *subcommand = cmd.qualified_name.split()
        if name in specials:
            specials[name].subcommands.append(SpecialCommand(subcommand[0], cmd.callback))
        else:
            specials[name] = SpecialCommand(name, cmd.callback)
    return specials


def all_special_commands(commands_class: Cog) -> FredHelpEmbed:
    desc = "*These are special commands doing something else than just replying with a predetermined answer.*"

    cmds = _get_specials(commands_class)
    embed = FredHelpEmbed("Special Commands", desc)
    solo_cmds = []
    for name, cmd in cmds.items():
        logging.debug(f"{name} {len(cmd.subcommands)}")
        if not cmd.subcommands:
            solo_cmds.append(cmd)
        else:
            embed.add_field(name=name, value='\n'.join(sorted(map(lambda s: s.name, cmd.subcommands))), inline=True)
    if solo_cmds:
        embed.add_field(name='other', value='\n'.join(sorted(map(lambda s: s.name, solo_cmds))), inline=True)
    logging.debug(embed.to_dict())

    return embed


def specific_special(commands_class: Cog, name: str) -> FredHelpEmbed:
    commands_by_name = _get_specials(commands_class)
    super_cmd, *sub_cmd = name.split()
    if cmd := commands_by_name.get(super_cmd):
        if sub_cmd and (cmd_child := next(filter(lambda s: s.name == sub_cmd[0], cmd.subcommands), None)):
            cmd = cmd_child
        desc = f"{cmd.callback.__doc__}"
        if cmd.subcommands:
            desc += "\nSubcommands: " + ",\t".join(sorted(map(lambda s: s.name, cmd.subcommands)))
    else:
        desc = f'Could not find the command "{name}"!' \
               '\nCheck your spelling, or use `help special` to see all special commands.' \
            + ('\nHint: no numbers!' if name.isnumeric() else '')

    return FredHelpEmbed(f'Help using special command "{name}"', desc)


def media_only() -> FredHelpEmbed:
    desc = '**These channels only allow users to post files (inc. images): **\n'
    for chan in config.MediaOnlyChannels.selectBy():
        desc += f"- <#{chan.channel_id}>\n"

    desc += "\n*All other messages will get deleted (if it doesn't, I might be down :( )*"

    return FredHelpEmbed("Media-Only Channels", desc)


def crashes(index: int = 0) -> FredHelpEmbed:
    title = "List of Known Crashes"
    desc = "*The bot responds when a common issues are present in a message, pastebin, debug file, or screenshot.*\n"
    all_crashes = list(config.Crashes.selectBy())
    logging.info(f"Fetched {len(all_crashes)} crashes from database.")

    global page_size, field_size
    # splits all crashes into groups of {page_size}
    pages = [all_crashes[i:i + page_size] for i in range(0, len(all_crashes), page_size)]
    try:
        page = pages[index]  # this is why try - user can provide index out of bounds
        # splits page into field groups of {field_size}

        fields: list[dict] = [
            {'name': f"{1 + get_shift(index, field)}-{field_size + get_shift(index, field)}",
             'value': "\n".join(f"`{crash.as_dict()['name']}`" for crash in page[field:field + field_size]),
             'inline': True}
            for field in range(0, len(page), field_size)
        ]
        return FredHelpEmbed(title, desc, fields=fields)

    except IndexError:
        desc = f"There aren't that many crashes! Try a number less than {index}."
        return FredHelpEmbed(title, desc)


def specific_crash(name: str) -> FredHelpEmbed:
    logging.debug(f"Specific crash requested: {name}")
    if answer := list(config.Crashes.selectBy(name=name.lower())):
        crash = answer[0].as_dict()
        logging.debug(f"Crash found!: {crash}")
    else:
        logging.debug("No crash found!")
        crash = None

    desc = "Crash could not be found!" if crash is None else \
        f"""
        **Regular expression:**
        `{crash['crash']}`
        **Response:**
        {crash['response']}
        """
    return FredHelpEmbed(f"Crash - {name}", desc)


def commands(index: int = 0) -> FredHelpEmbed:
    title = "List of Fred Commands"
    desc = "*These are normal commands that can be called by stating their name.*\n"

    all_commands = list(config.Commands.selectBy())
    logging.info(f"Fetched {len(all_commands)} commands from database.")
    global page_size, field_size
    # splits all commands into groups of {page_size}
    pages = [all_commands[page:page + page_size] for page in range(0, len(all_commands), page_size)]
    try:

        page = pages[index]  # this is why try - user can provide index out of bounds
        # splits page into field groups of {field_size}

        fields: list[dict] = [
            {'name': f"{1 + get_shift(index, field)}-{field_size + get_shift(index, field)}",
             'value': "\n".join(f"`{command.as_dict()['name']}`" for command in page[field:field + field_size]),
             'inline': True}
            for field in range(0, len(page), field_size)
        ]
        return FredHelpEmbed(title, desc, fields=fields)

    except IndexError:
        desc = f"There aren't that many commands! Try a number less than {index}."
        return FredHelpEmbed(title, desc)
