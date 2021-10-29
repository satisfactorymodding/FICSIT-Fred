import logging

import discord.ext.commands as commands
import config
from libraries.helper import t3_only

from libraries import helper


class MediaOnly(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def process_message(self, message):
        logging.info("MediaOnly: Processing a message", extra=helper.messagedict(message))
        if len(message.embeds) > 0 or len(message.attachments) > 0:
            logging.info("MediaOnly: message contains media", extra=helper.messagedict(message))
            return
        ctx = await self.bot.get_context(message)
        if await t3_only(ctx):
            logging.info("MediaOnly: message doesn't contain media but the author is a T3", extra=helper.messagedict(message))
            return False
        if config.MediaOnlyChannels.fetch(message.channel.id):
            logging.info("MediaOnly: removing a message", extra=helper.messagedict(message))
            await message.delete()
            await self.bot.send_DM(message.author,
                                   f"Hi {message.author.name}, the channel you just tried to message in, "
                                   f"{self.bot.get_channel(message.channel.id).name} is a 'Media Only' channel. "
                                   f"This means you must attach a file in order to post there. "
                                   f"Here is your message if you want to paste it again after the adequate changes: "
                                   f"```\n{message.content}\n```")
            return True
        return False
