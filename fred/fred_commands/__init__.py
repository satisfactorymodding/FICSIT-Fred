from __future__ import annotations

import asyncio
import inspect
import io
import logging
from os.path import split
from urllib.parse import urlparse

import nextcord
import re2
from algoliasearch.search.client import SearchClient
from nextcord.ext.commands.view import StringView

from ._baseclass import BaseCmds, common, config, commands
from .bot_meta import BotCmds
from .channels import ChannelCmds
from .crashes import CrashCmds
from .dbcommands import CommandCmds
from .experience import EXPCmds
from .help import HelpCmds, FredHelpEmbed
from ..libraries import createembed, ocr
from ..libraries.view.mod_picker import ModPicker


class Commands(BotCmds, ChannelCmds, CommandCmds, CrashCmds, EXPCmds, HelpCmds):
    @BaseCmds.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        # We get an error about commands being found when using "runtime" commands, so we have to ignore that
        self.logger.error(f"Caught {error!r}")
        if isinstance(error, commands.CommandNotFound):
            command = ctx.message.content.lower().lstrip(self.bot.command_prefix).split(" ")[0]
            if config.Commands.fetch(command) is not None:
                return
            self.logger.warning("Invalid command attempted")
            return
        elif isinstance(error, commands.MissingRequiredArgument):
            self.logger.info("Successfully deferred error of missing required argument")
            missing_argument_name, target_type = extract_target_type_from_converter_param(error.param)
            output = f"You are missing at least one parameter for this command: '{missing_argument_name}'"
            if target_type:
                output += f" of type '{target_type}'"
            await ctx.reply(output)
            return
        elif isinstance(error, commands.BadArgument):
            self.logger.info("Successfully deferred error of bad argument")
            # self.logger.debug(error)
            # _, target_type, _, missing_argument_name, *_ = str(error).split('"')
            # output = f"At least one parameter for this command was entered incorrectly: '{missing_argument_name}'"
            # if target_type:
            #     output += f" of type '{target_type}'"
            await ctx.reply(str(error))
            return
        elif isinstance(error, commands.CheckFailure):
            self.logger.info("Successfully deferred error af insufficient permissions")
            await ctx.reply("Sorry, but you do not have enough permissions to do this.")
            return
        elif isinstance(error, commands.errors.CommandInvokeError):
            self.logger.info("Deferring error of command invocation")
            # use error.original here because error is nextcord.ext.commands.errors.CommandInvokeError
            if isinstance(error.original, asyncio.exceptions.TimeoutError):
                self.logger.info("Handling command response timeout gracefully")
                # this is raised to escape a bunch of value passing if timed out, but should not raise big errors.
                return

        await ctx.send(
            "I encountered an error while trying to call this command. "
            "The error has been logged, sorry for the inconvenience."
        )
        raise (error.original if hasattr(error, "original") else error)

    @BaseCmds.listener()
    async def on_message(self, message: nextcord.Message):
        if message.author.bot or not self.bot.is_running():
            return

        prefix = self.bot.command_prefix
        self.logger.info("Processing a message", extra=common.message_info(message))
        command_pattern = re2.compile(rf"{re2.escape(prefix)}(\S+)\s*(.*)")
        if (match := re2.match(command_pattern, message.content)) is None:
            return

        (name, arguments) = match.groups()

        self.logger.info(f"Processing the command {name}", extra=common.message_info(message))

        if (command := config.Commands.fetch(name)) is None:
            return

        if (
            (content := command["content"])
            and content.startswith(prefix)  # for linked aliases of commands like ff->rp
            and (linked_command := config.Commands.fetch(content.lstrip(prefix)))
        ):
            command = linked_command
            content = linked_command["content"]

        if (attachment := command["attachment"]) is not None:
            async with self.bot.web_session.get(attachment) as resp:
                buff = io.BytesIO(await resp.read())
                _, filename = split(urlparse(attachment).path)
                attachment = nextcord.File(filename=filename, fp=buff, force_close=True)

        args = []
        view = StringView(arguments)
        while not view.eof:
            view.skip_ws()
            args.append(view.get_quoted_word())

        if content:
            text = str(content)
            substitutions = map(int, re2.findall(r"{(\d+)}", text))
            for substitution in substitutions:
                text = re2.sub(
                    rf"\{{{substitution}\}}",
                    args[substitution] if substitution < len(args) else "(missing argument)",
                    text,
                )
            text = text.replace("{...}", " ".join(args) if args else "(no arguments given)")
        else:
            text = None

        await self.bot.reply_to_msg(message, text, file=attachment)

    @commands.command()
    async def mod(self, ctx: commands.Context, *, mod_name: str) -> None:
        """Usage: `mod (name: str)`
        Response: If a near-exact match is found, gives you info about that mod.
        If close matches are found, up to 10 of those will be listed.
        If nothing even comes close, I'll let you know ;)"""

        mod_name = mod_name.split("\n")[0]

        if len(mod_name) < 3:
            await self.bot.reply_to_msg(ctx.message, "Searching needs at least three characters!")
            return

        embed, attachment, multiple_mods = await createembed.mod_embed(mod_name, self.bot)
        if embed is None:
            await self.bot.reply_to_msg(ctx.message, "No mods found!")
        else:
            if multiple_mods:
                view = ModPicker(multiple_mods)
            else:
                view = None
            msg = await self.bot.reply_to_msg(ctx.message, embed=embed, view=view, file=attachment)
            if view:

                async def callback(interaction: nextcord.Interaction):
                    if interaction.user == ctx.author:
                        logging.info(interaction.data.values)
                        new_embed, new_attachment, _ = await createembed.mod_embed(
                            interaction.data["values"][0], self.bot, using_id=True
                        )
                        # Two edits because the view doesn't go away with one... go figure why
                        await msg.edit(view=None)
                        await msg.edit(embed=new_embed, file=new_attachment)
                        view.stop()
                    else:
                        await interaction.send("Only the user who called this command can do this!", ephemeral=True)

                async def timeout():
                    await msg.edit(view=None)

                view.set_callback(callback)
                view.on_timeout = timeout

                await view.wait()

    @commands.command(aliases=["docssearch"])
    async def docsearch(self, ctx: commands.Context, *, search: str) -> None:
        """Usage: `docsearch (search: str)`
        Response: Equivalent to using the search function on the SMR docs page; links the first search result"""
        self.logger.info(f"Searching the documentation. {search =}")
        client: SearchClient = SearchClient("2FDCZBLZ1A", "28531804beda52a04275ecd964db429d")

        query = await client.search_single_index(
            index_name="ficsit",
            search_params={
                "query": search,
                "facetFilters": [
                    "component_name:satisfactory-modding",
                    "component_version:latest",
                ],
            },
        )

        for hit in query.hits:
            if hit.hierarchy["lvl0"].endswith("latest"):
                await self.bot.reply_to_msg(ctx.message, f"This is the best result I got from the SMD :\n{hit.url}")
                return

    @commands.command()
    async def ocr_test(self, ctx: commands.Context) -> None:
        """Usage: `ocr_test` {attach an image!}"""
        text = "OCR Debugging:\n\n"
        for n, att in enumerate(ctx.message.attachments):
            with io.BytesIO() as img:
                await att.save(img)
                read_text = await self.bot.loop.run_in_executor(self.bot.executor, ocr.read, img)
            text += f"**Image {n}:**\n ```\n{read_text}\n```\n"

        await self.bot.reply_to_msg(ctx.message, text)


def extract_target_type_from_converter_param(missing_argument: inspect.Parameter):
    s = str(missing_argument)

    if ":" not in s:
        return s, None

    split = s.split(": ")
    converter_type = split[1]
    missing_argument_name = split[0]

    target_type = converter_type.split(".")[-1].strip("Converter")
    return missing_argument_name, target_type
