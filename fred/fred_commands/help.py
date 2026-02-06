from __future__ import annotations

from functools import lru_cache
from typing import Coroutine, Type
from typing import Optional

import attrs
import nextcord
import regex
from nextcord import Interaction, SlashOption
from nextcord.ext.commands import Cog

from ._baseclass import BaseCmds, commands, config
from ..libraries import common

logger = common.new_logger(__name__)


class HelpCmds(BaseCmds, Cog):

    @commands.group()
    async def help(self, ctx: commands.Context) -> None:
        """[Help Commands!](https://www.youtube.com/watch?v=2Q_ZzBGPdqE)
        Usage: `help [commands/crash(es)/special/media_only/webhooks] [page: int/name: str]`
        Response: Information about what you requested"""
        if ctx.invoked_subcommand is None:
            await self.help_special(ctx, name="help")
            return

    async def _send_help(self, ctx_or_interaction, **kwargs):

        if isinstance(ctx_or_interaction, Interaction):
            if not ctx_or_interaction.user.dm_channel:
                await ctx_or_interaction.user.create_dm()
            if not await self.bot.send_safe_direct_message(
                ctx_or_interaction.user,
                in_dm=ctx_or_interaction.channel == ctx_or_interaction.user.dm_channel,
                **kwargs,
            ):
                await ctx_or_interaction.response.send_message(
                    "Help commands only work in DMs to avoid clutter. "
                    "You have either disabled server DMs or indicated that you do not wish for Fred to DM you. "
                    "Please enable both of these if you want to receive messages.",
                    ephemeral=True,
                )
            else:
                if not ctx_or_interaction.response.is_done():
                    await ctx_or_interaction.response.defer(ephemeral=True)
                await ctx_or_interaction.followup.send("Help message sent to your DMs!", ephemeral=True)
        else:
            if not ctx_or_interaction.author.dm_channel:
                await ctx_or_interaction.author.create_dm()
            if not await self.bot.send_safe_direct_message(
                ctx_or_interaction.author,
                in_dm=ctx_or_interaction.channel == ctx_or_interaction.author.dm_channel,
                **kwargs,
            ):
                await ctx_or_interaction.reply(
                    "Help commands only work in DMs to avoid clutter. "
                    "You have either disabled server DMs or indicated that you do not wish for Fred to DM you. "
                    "Please enable both of these if you want to receive messages."
                )
            else:
                try:
                    await ctx_or_interaction.message.delete()
                except nextcord.Forbidden:
                    pass

    #       Commands Help Command
    async def help_commands_handler(self, ctxorctx_or_interaction, page: Optional[int] = None) -> None:
        if page is None:
            response = FredHelpEmbed.commands()
        elif page < 1:
            response = FredHelpEmbed("Bad input", "No negative/zero indices! >:(", "commands")
            response.set_footer(text="y r u like dis")
        else:
            response = FredHelpEmbed.commands(index=page - 1)
        await self._send_help(ctxorctx_or_interaction, embed=response)

    @help.command(name="commands")
    async def help_commands(self, ctx: commands.Context, page: int = None) -> None:
        """[Help Commands!](https://www.youtube.com/watch?v=2Q_ZzBGPdqE)
        Usage: `help commands [page: int]`
        Response: Shows a table of all commands at the page specified"""
        await self.help_commands_handler(ctx, page)

    @nextcord.slash_command(name="help_commands", description="Shows a list of all commands, paginated")
    async def help_commands_slash(
        self,
        interaction: Interaction,
        page: Optional[int] = SlashOption(description="The page number to view, starting at 1", required=False),
    ) -> None:
        await self.help_commands_handler(interaction, page)

    #    Crashes Help Command
    async def help_crashes_handler(self, ctxorctx_or_interaction, page: Optional[int] = None) -> None:
        if page is None:
            response = FredHelpEmbed.crashes()
        elif page < 1:
            response = FredHelpEmbed("Bad input", "No negative/zero indices! >:(", "crashes [page]")
            response.set_footer(text="y r u like dis")
        else:
            response = FredHelpEmbed.crashes(index=page - 1)
        await self._send_help(ctxorctx_or_interaction, embed=response)

    @help.command(name="crashes")
    async def help_crashes(self, ctx: commands.Context, page: int = None) -> None:
        """[Help Commands!](https://www.youtube.com/watch?v=2Q_ZzBGPdqE)
        Usage: `help crashes [page: int]`
        Response: Shows a table of all crashes at the page specified"""
        await self.help_crashes_handler(ctx, page)

    @nextcord.slash_command(name="help_crashes", description="Shows a list of all crashes, paginated")
    async def help_crashes_slash(
        self,
        interaction: Interaction,
        page: Optional[int] = SlashOption(description="The page number to view, starting at 1", required=False),
    ) -> None:
        await self.help_crashes_handler(interaction, page)

    #     Webhooks Help Command
    @help.command(name="webhooks")
    async def help_webhooks(self, ctx: commands.Context) -> None:
        """[Help Commands!](https://www.youtube.com/watch?v=2Q_ZzBGPdqE)
        Usage: `help webhooks`
        Response: Info about webhooks"""
        response = FredHelpEmbed.git_webhooks()
        await self._send_help(ctx, embed=response)

    @nextcord.slash_command(name="help_webhooks", description="Shows info about GitHub webhooks")
    async def help_webhooks_slash(self, interaction: Interaction) -> None:
        response = FredHelpEmbed.git_webhooks()
        await self._send_help(interaction, embed=response)

    #       Specific Crash Help Command
    async def help_specific_crash_handler(self, ctx_or_interaction, name: Optional[str] = None) -> None:
        if name is None:
            response = FredHelpEmbed.crashes()
        elif name.isnumeric():
            response = FredHelpEmbed("Bad input", f"Did you mean `help crashes {name}`?", "crash [name]")
        else:
            response = FredHelpEmbed.specific_crash(name=name)
        await self._send_help(ctx_or_interaction, embed=response)

    @help.command(name="crash")
    async def help_crash(self, ctx: commands.Context, *, name: str = None) -> None:
        """[Help Commands!](https://www.youtube.com/watch?v=2Q_ZzBGPdqE)
        Usage: `help crash [name: str]`
        Response: Shows info about the crash specified"""
        await self.help_specific_crash_handler(ctx, name)

    @nextcord.slash_command(name="help_crash", description="Shows info about a specific crash")
    async def help_crash_slash(
        self, interaction: Interaction, name: str = SlashOption(description="The name of the crash to get info about")
    ) -> None:
        await self.help_specific_crash_handler(interaction, name)

    #       Special Commands Help Command
    async def help_special_handler(self, ctx_or_interaction, name: Optional[str] = None) -> None:
        if name is None:
            response = FredHelpEmbed.all_special_commands(self)
        else:
            response = FredHelpEmbed.specific_special(self, name)
        await self._send_help(ctx_or_interaction, embed=response)

    @help.command(name="special")
    async def help_special(self, ctx: commands.Context, *, name: str = None) -> None:
        """[Help Commands!](https://www.youtube.com/watch?v=2Q_ZzBGPdqE)
        Usage: `help special [name: str]`
        Response: Shows info about the special command specified, or all special commands if none is given"""
        await self.help_special_handler(ctx, name)

    @nextcord.slash_command(
        name="help_special", description="Shows info about special commands, or a specific one if a name is provided"
    )
    async def help_special_slash(
        self,
        interaction: Interaction,
        name: Optional[str] = SlashOption(
            description="The name of the special command to get info about", required=False
        ),
    ) -> None:
        await self.help_special_handler(interaction, name)

    #      Media-Only Channels Help Command
    @help.command(name="media_only")
    async def help_media_only(self, ctx: commands.Context) -> None:
        """[Help Commands!](https://www.youtube.com/watch?v=2Q_ZzBGPdqE)
        Usage: `help media_only`
        Response: Shows info about media only channels"""
        response = FredHelpEmbed.media_only()
        await self._send_help(ctx, embed=response)

    @nextcord.slash_command(name="help_media_only", description="Shows info about media-only channels")
    async def help_media_only_slash(self, interaction: Interaction) -> None:
        response = FredHelpEmbed.media_only()
        await self._send_help(interaction, embed=response)


page_size: int = 30  # if you change this, make it a multiple of three
field_size: int = 10  # Define 'field_size' if it is missing


@attrs.define
class SpecialCommand:
    name: str
    callback: Coroutine
    subcommands: list[SpecialCommand] = attrs.Factory(list)  # use this otherwise everyone gets the ptr to the same list


class FredHelpEmbed(nextcord.Embed):
    # these are placeholder values only, they will be set up when setup() is called post-DB connection
    help_colour: int = 0
    prefix: str = ">"

    def __init__(
        self: FredHelpEmbed, name: str, desc: str, /, usage: str = "", fields: list[dict] = (), **kwargs
    ) -> None:

        desc = regex.sub(r"^\s*(\S.*)$", r"\1", desc, flags=regex.MULTILINE)
        desc = regex.sub(r"(?<=Usage: )`(.+)`", rf"`{self.prefix}\1`", desc)
        desc = regex.sub(r"^(\w+:) ", r"**\1** ", desc, flags=regex.MULTILINE)
        super().__init__(title=f"**{name}**", colour=self.help_colour, description=desc, **kwargs)
        for f in fields:
            self.add_field(**f)
        self.set_footer(text=f"Usage: `{self.prefix}help {usage}`")

    @classmethod
    def setup(cls: Type[FredHelpEmbed]) -> None:
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
    def git_webhooks(cls: Type[FredHelpEmbed]) -> FredHelpEmbed:
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
    def all_special_commands(cls: Type[FredHelpEmbed], commands_class: commands.Cog) -> FredHelpEmbed:
        desc = "*These are special commands doing something else than just replying with a predetermined answer.*"

        cmds = cls._get_specials(commands_class)
        embed = cls("Special Commands", desc, usage="special [name]")
        solo_cmds = []
        for name, cmd in cmds.items():
            if not cmd.subcommands:
                solo_cmds.append(cmd)
            else:
                embed.add_field(name=name, value="\n".join(sorted(map(lambda s: s.name, cmd.subcommands))))
        if solo_cmds:
            embed.add_field(name="other", value="\n".join(sorted(map(lambda s: s.name, solo_cmds))))

        return embed

    @classmethod
    def specific_special(cls: Type[FredHelpEmbed], commands_class: commands.Cog, name: str) -> FredHelpEmbed:
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
    def media_only(cls: Type[FredHelpEmbed]) -> FredHelpEmbed:
        desc = "**These channels only allow users to post files (inc. images): **\n"
        for chan in config.MediaOnlyChannels.selectBy():
            desc += f"- <#{chan.channel_id}>\n"

        desc += "\n*All other messages will get deleted (if it doesn't, I might be down :( )*"

        return cls("Media-Only Channels", desc, usage="media_only")

    @classmethod
    def crashes(cls: Type[FredHelpEmbed], index: int = 0) -> FredHelpEmbed:
        title = "List of Known Crashes"
        desc = (
            "*The bot responds when a common issues are present "
            "in a message, pastebin, debug file, or screenshot.*\n"
        )
        all_crashes = list(config.Crashes.selectBy().orderBy("name"))
        logger.info(f"Fetched {len(all_crashes)} crashes from database.")

        global page_size
        # splits all crashes into groups of {page_size}
        pages = [all_crashes[i : i + page_size] for i in range(0, len(all_crashes), page_size)]
        try:
            page = pages[index]  # this is why try - user can provide index out of bounds
            # splits page into field groups of {field_size}

            desc += "```\n" + ("\n".join(crash.name for crash in page)) + "\n```"
            return FredHelpEmbed(title, desc, usage="crashes [page]")

        except IndexError:
            desc = f"There aren't that many crashes! Try a number less than {index}."
            return FredHelpEmbed(title, desc, usage="crashes [page]")

    @classmethod
    def specific_crash(cls: Type[FredHelpEmbed], name: str) -> FredHelpEmbed:

        crash: Optional[config.Crashes] = config.Crashes.selectBy(name=name.lower()).getOne(None)

        desc = (
            f"""
            **Regular expression:**
            `{crash.crash}`
            **Response:**
            {crash.response}
            """
            if crash is not None
            else "Crash could not be found!"
        )
        return cls(f"Crash - {name}", desc, usage="crash [name]")

    @classmethod
    def commands(cls: Type[FredHelpEmbed], index: int = 0) -> FredHelpEmbed:
        title = "List of Fred Commands"
        desc = "*These are normal commands that can be called by stating their name.*\n"

        all_commands = list(config.Commands.selectBy().orderBy("name"))
        logger.info(f"Fetched {len(all_commands)} commands from database.")
        global page_size
        # splits all commands into groups of {page_size}
        pages = [all_commands[page : page + page_size] for page in range(0, len(all_commands), page_size)]
        try:

            page = pages[index]  # this is why try - user can provide index out of bounds
            # splits page into field groups of {field_size}

            desc += "```\n" + ("\n".join(command.name for command in page)) + "\n```"
            return cls(title, desc, usage="commands [page]")

        except IndexError:
            desc = f"There aren't that many commands! Try a number less than {index}."
            return cls(title, desc, usage="commands [page]")
