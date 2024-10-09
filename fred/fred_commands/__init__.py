from __future__ import annotations

import asyncio
import inspect
import io
import logging
import re
from os.path import split
from urllib.parse import urlparse

import nextcord
from algoliasearch.search_client import SearchClient
from nextcord.ext.commands.view import StringView

from ._baseclass import BaseCmds, common, config, commands
from .bot_meta import BotCmds
from .channels import ChannelCmds
from .crashes import CrashCmds
from .dbcommands import CommandCmds
from .dialogflow import DialogflowCmds
from .experience import EXPCmds
from .help import HelpCmds, FredHelpEmbed
from ..libraries import createembed
from ..libraries.view.mod_picker import ModPicker


class Commands(BotCmds, ChannelCmds, CommandCmds, CrashCmds, DialogflowCmds, EXPCmds, HelpCmds):
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
        if message.content.startswith(prefix):
            name = message.content.lower().lstrip(prefix).split(" ")[0]
            self.logger.info(f"Processing the command {name}", extra=common.message_info(message))
            if (command := config.Commands.fetch(name)) is not None:
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
                        attachment = nextcord.File(filename=filename, fp=buff)
                args = []
                view = StringView(message.content.lstrip(prefix))
                view.get_word()  # command name
                while not view.eof:
                    view.skip_ws()
                    args.append(view.get_quoted_word())
                if content:
                    # ok who wrote this unreadable garbage? oh wait, it was me - Borketh
                    # this should probably be simplified...
                    text = re.sub(
                        r"{(\d+)}",
                        lambda match: (
                            args[int(match.group(1))] if int(match.group(1)) < len(args) else "(missing argument)"
                        ),
                        content,
                    ).replace("{...}", " ".join(args))
                else:
                    text = None

                await self.bot.reply_to_msg(message, text, file=attachment)
                return

    @commands.command()
    async def mod(self, ctx: commands.Context, *, mod_name: str) -> None:
        """Usage: `mod (name: str)`
        Response: If a near-exact match is found, gives you info about that mod.
        If close matches are found, up to 10 of those will be listed.
        If nothing even comes close, I'll let you know ;)"""
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
                    logging.info(interaction.data.values)
                    new_embed, new_attachment, _ = await createembed.mod_embed(interaction.data["values"][0], self.bot)
                    # Two edits because the view doesn't go away with one... go figure why
                    await msg.edit(view=None)
                    await msg.edit(embed=new_embed, file=new_attachment)
                    view.stop()

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
        client: SearchClient = SearchClient.create("BH4D9OD16A", "53b3a8362ea7b391f63145996cfe8d82")
        index = client.init_index("ficsit")
        index.set_settings({"searchableAttributes": ["url"]})
        query = index.search(search, {"attributesToRetrieve": "*"})
        import json

        self.logger.debug(json.dumps(query, indent=2))
        for hit in query["hits"]:
            if hit["hierarchy"]["lvl0"].endswith("latest"):
                await self.bot.reply_to_msg(ctx.message, f"This is the best result I got from the SMD :\n{hit['url']}")
                return


def extract_target_type_from_converter_param(missing_argument: inspect.Parameter):
    s = str(missing_argument)

    if ":" not in s:
        return s, None

    split = s.split(": ")
    converter_type = split[1]
    missing_argument_name = split[0]

    target_type = converter_type.split(".")[-1].strip("Converter")
    return missing_argument_name, target_type
