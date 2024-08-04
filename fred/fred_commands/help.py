from __future__ import annotations

import logging
from functools import lru_cache
from typing import Coroutine

import attrs
import nextcord
import re

from ._baseclass import BaseCmds, commands, config


class HelpCmds(BaseCmds):
    @commands.group()
    async def help(self, ctx: commands.Context) -> None:
        """[Help Commands!](https://www.youtube.com/watch?v=2Q_ZzBGPdqE)
        Usage: `help [commands/crash(es)/special/media_only/webhooks] [page: int/name: str]`
        Response: Information about what you requested"""
        if ctx.invoked_subcommand is None:
            await self.help_special(ctx, name="help")
            return

    async def _send_help(self, ctx: commands.Context, **kwargs):
        if not ctx.author.dm_channel:
            await ctx.author.create_dm()
        if not await self.bot.checked_DM(ctx.author, in_dm=ctx.channel == ctx.author.dm_channel, **kwargs):
            await ctx.reply(
                "Help commands only work in DMs to avoid clutter. "
                "You have either disabled server DMs or indicated that you do not wish for Fred to DM you. "
                "Please enable both of these if you want to receive messages."
            )
        else:
            try:
                await ctx.message.delete()
            except nextcord.Forbidden:
                pass  # doesn't have delete perms, f.e. in a DM channel

    @help.command(name="commands")
    async def help_commands(self, ctx: commands.Context, page: int = None) -> None:
        """[Help Commands!](https://www.youtube.com/watch?v=2Q_ZzBGPdqE)
        Usage: `help commands [page: int]`
        Response: Shows a table of all commands at the page specified"""
        if page is None:
            response = FredHelpEmbed.commands()
        elif page < 1:
            response = FredHelpEmbed("Bad input", "No negative/zero indices! >:(", "commands")
            response.set_footer(text="y r u like dis")
        else:
            response = FredHelpEmbed.commands(index=page - 1)
        await self._send_help(ctx, embed=response)

    @help.command(name="webhooks")
    async def help_webhooks(self, ctx: commands.Context) -> None:
        """[Help Commands!](https://www.youtube.com/watch?v=2Q_ZzBGPdqE)
        Usage: `help webhooks`
        Response: Info about webhooks"""
        response = FredHelpEmbed.git_webhooks()
        await self._send_help(ctx, embed=response)

    @help.command(name="crashes")
    async def help_crashes(self, ctx: commands.Context, page: int = None) -> None:
        """[Help Commands!](https://www.youtube.com/watch?v=2Q_ZzBGPdqE)
        Usage: `help crashes [page: int]`
        Response: Shows a table of all crashes at the page specified"""
        if page is None:
            response = FredHelpEmbed.crashes()
        elif page < 1:
            response = FredHelpEmbed("Bad input", "No negative/zero indices! >:(", "crashes [page]")
            response.set_footer(text="y r u like dis")
        else:
            response = FredHelpEmbed.crashes(index=page - 1)
        await self._send_help(ctx, embed=response)

    @help.command(name="crash")
    async def help_crash(self, ctx: commands.Context, *, name: str = None) -> None:
        """[Help Commands!](https://www.youtube.com/watch?v=2Q_ZzBGPdqE)
        Usage: `help crash [name: str]`
        Response: Shows info about the crash specified"""
        if name is None:
            response = FredHelpEmbed.crashes()
        elif name.isnumeric():
            response = FredHelpEmbed("Bad input", f"Did you mean `help crashes {name}`?", "crash [name]")
        else:
            response = FredHelpEmbed.specific_crash(name=name)
        await self._send_help(ctx, embed=response)

    @help.command(name="special")
    async def help_special(self, ctx: commands.Context, *, name: str = None) -> None:
        """[Help Commands!](https://www.youtube.com/watch?v=2Q_ZzBGPdqE)
        Usage: `help special [name: str]`
        Response: Shows info about the special command specified, or all special commands if none is given"""
        if name:
            response = FredHelpEmbed.specific_special(self, name)
        else:
            response = FredHelpEmbed.all_special_commands(self)

        await self._send_help(ctx, embed=response)

    @help.command(name="media_only")
    async def help_media_only(self, ctx: commands.Context) -> None:
        """[Help Commands!](https://www.youtube.com/watch?v=2Q_ZzBGPdqE)
        Usage: `help media_only`
        Response: Shows info about media only channels"""
        response = FredHelpEmbed.media_only()
        await self._send_help(ctx, embed=response)


page_size: int = 30  # if you change this, make it a multiple of three
field_size: int = page_size // 3  # because inlined fields stack up to three horizontally


@attrs.define
class SpecialCommand:
    name: str
    callback: Coroutine
    subcommands: list[SpecialCommand] = attrs.Factory(list)  # use this otherwise everyone gets the ptr to the same list


class FredHelpEmbed(nextcord.Embed):
    # these are placeholder values only, they will be set up when setup() is called post-DB connection
    help_colour: int = 0
    prefix: str = ">"
    logger = logging.Logger("HELP-EMBEDS")

    def __init__(
        self: FredHelpEmbed, name: str, desc: str, /, usage: str = "", fields: list[dict] = (), **kwargs
    ) -> None:

        desc = re.sub(r"^\s*(\S.*)$", r"\1", desc, flags=re.MULTILINE)
        desc = re.sub(r"(?<=Usage: )`(.+)`", rf"`{self.prefix}\1`", desc)
        desc = re.sub(r"^(\w+:) ", r"**\1** ", desc, flags=re.MULTILINE)
        super().__init__(title=f"**{name}**", colour=self.help_colour, description=desc, **kwargs)
        for f in fields:
            self.add_field(**f)
        self.set_footer(text=f"Usage: `{self.prefix}help {usage}`")

    @classmethod
    def setup(cls: type(FredHelpEmbed)) -> None:
        """This is called after the DB has been set up"""
        cls.help_colour = config.ActionColours.fetch("Light Blue")
        cls.prefix = config.Misc.fetch("prefix")

    def __str__(self: FredHelpEmbed) -> str:
        return str(self.to_dict())

    @staticmethod
    @lru_cache
    def get_shift(index: int, field_number: int) -> int:
        return field_number + (index * page_size)

    @staticmethod
    @lru_cache
    def get_field_indices(index: int, field_number: int) -> str:
        start = 1 + FredHelpEmbed.get_shift(index, field_number)
        end = field_size + FredHelpEmbed.get_shift(index, field_number)
        return f"{start}-{end}"

    @classmethod
    def git_webhooks(cls) -> FredHelpEmbed:
        return cls(
            "GitHub webhooks",
            "I am sent updates from GitHub about the most important modding repositories, "
            f'then publish updates to <#{config.Misc.fetch("githook_channel")}>!',
            usage="webhooks",
        )

    @staticmethod
    def _get_specials(commands_class: commands.Cog) -> dict[str, SpecialCommand]:
        specials: dict[str, SpecialCommand] = {}
        for cmd in commands_class.walk_commands():
            name, *subcommand = cmd.qualified_name.split()
            if name in specials:
                specials[name].subcommands.append(SpecialCommand(subcommand[0], cmd.callback))
            else:
                specials[name] = SpecialCommand(name, cmd.callback)
        return specials

    @classmethod
    def all_special_commands(cls, commands_class: commands.Cog) -> FredHelpEmbed:
        desc = "*These are special commands doing something else than just replying with a predetermined answer.*"

        cmds = cls._get_specials(commands_class)
        embed = cls("Special Commands", desc, usage="special [name]")
        solo_cmds = []
        for name, cmd in cmds.items():
            if not cmd.subcommands:
                solo_cmds.append(cmd)
            else:
                embed.add_field(name=name, value="\n".join(sorted(map(lambda s: s.name, cmd.subcommands))), inline=True)
        if solo_cmds:
            embed.add_field(name="other", value="\n".join(sorted(map(lambda s: s.name, solo_cmds))), inline=True)

        return embed

    @classmethod
    def specific_special(cls, commands_class: commands.Cog, name: str) -> FredHelpEmbed:
        commands_by_name = cls._get_specials(commands_class)
        super_cmd, *sub_cmd = name.split()
        if cmd := commands_by_name.get(super_cmd):
            if sub_cmd and (cmd_child := next(filter(lambda s: s.name == sub_cmd[0], cmd.subcommands), None)):
                cmd = cmd_child
            desc = f"{cmd.callback.__doc__}"
            if cmd.subcommands:
                desc += "\nSubcommands: " + ",\t".join(sorted(map(lambda s: s.name, cmd.subcommands)))
        else:
            desc = (
                f'Could not find the command "{name}"!'
                "\nCheck your spelling, or use `help special` to see all special commands."
                + ("\nHint: no numbers!" if name.isnumeric() else "")
            )

        return cls(f'Help using special command "{name}"', desc, usage="special [name]")

    @classmethod
    def media_only(cls) -> FredHelpEmbed:
        desc = "**These channels only allow users to post files (inc. images): **\n"
        for chan in config.MediaOnlyChannels.selectBy():
            desc += f"- <#{chan.channel_id}>\n"

        desc += "\n*All other messages will get deleted (if it doesn't, I might be down :( )*"

        return cls("Media-Only Channels", desc, usage="media_only")

    @classmethod
    def crashes(cls, index: int = 0) -> FredHelpEmbed:
        title = "List of Known Crashes"
        desc = (
            "*The bot responds when a common issues are present "
            "in a message, pastebin, debug file, or screenshot.*\n"
        )
        all_crashes = list(config.Crashes.selectBy())
        cls.logger.info(f"Fetched {len(all_crashes)} crashes from database.")

        global page_size, field_size
        # splits all crashes into groups of {page_size}
        pages = [all_crashes[i : i + page_size] for i in range(0, len(all_crashes), page_size)]
        try:
            page = pages[index]  # this is why try - user can provide index out of bounds
            # splits page into field groups of {field_size}

            fields: list[dict] = [
                {
                    "name": cls.get_field_indices(index, field),
                    "value": "\n".join(f"`{crash.as_dict()['name']}`" for crash in page[field : field + field_size]),
                    "inline": True,
                }
                for field in range(0, len(page), field_size)
            ]
            return FredHelpEmbed(title, desc, fields=fields, usage="crashes [page]")

        except IndexError:
            desc = f"There aren't that many crashes! Try a number less than {index}."
            return FredHelpEmbed(title, desc, usage="crashes [page]")

    @classmethod
    def specific_crash(cls, name: str) -> FredHelpEmbed:
        if answer := list(config.Crashes.selectBy(name=name.lower())):
            crash = answer[0].as_dict()
        else:
            crash = None

        desc = (
            "Crash could not be found!"
            if crash is None
            else f"""
            **Regular expression:**
            `{crash['crash']}`
            **Response:**
            {crash['response']}
            """
        )
        return cls(f"Crash - {name}", desc, usage="crash [name]")

    @classmethod
    def commands(cls, index: int = 0) -> FredHelpEmbed:
        title = "List of Fred Commands"
        desc = "*These are normal commands that can be called by stating their name.*\n"

        all_commands = list(config.Commands.selectBy())
        cls.logger.info(f"Fetched {len(all_commands)} commands from database.")
        global page_size, field_size
        # splits all commands into groups of {page_size}
        pages = [all_commands[page : page + page_size] for page in range(0, len(all_commands), page_size)]
        try:

            page = pages[index]  # this is why try - user can provide index out of bounds
            # splits page into field groups of {field_size}

            fields: list[dict] = [
                {
                    "name": cls.get_field_indices(index, field),
                    "value": "\n".join(
                        f"`{command.as_dict()['name']}`" for command in page[field : field + field_size]
                    ),
                    "inline": True,
                }
                for field in range(0, len(page), field_size)
            ]
            return cls(title, desc, fields=fields, usage="commands [page]")

        except IndexError:
            desc = f"There aren't that many commands! Try a number less than {index}."
            return cls(title, desc, usage="commands [page]")
