import discord.ext.commands as commands

import fred.config as config
from fred.libraries.helper import t3_only


class MediaOnly(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def process_message(self, message):

        if len(message.embeds) > 0 or len(message.attachments) > 0:
            return
        ctx = await self.bot.get_context(message)
        if await t3_only(ctx):
            return False
        if config.MediaOnlyChannels.fetch(message.channel.id):
            await self.bot.send_dm(message.author,
                                   f"Hi {message.author.name}, the channel you just tried to message in, "
                                   f"{self.bot.get_channel(message.channel.id).name} is a 'Media Only' channel. "
                                   f"This means you must attach a file in order to post there. "
                                   f"Here is your message if you want to paste it again after the adequate changes: "
                                   f"```\n{message.content}\n```")
            await message.delete()
            return True
        return False
