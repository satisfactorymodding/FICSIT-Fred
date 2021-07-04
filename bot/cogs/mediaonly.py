import discord.ext.commands as commands
import config
from libraries.helper import t3_only


class MediaOnly(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def process_message(self, message):
        if t3_only(message):
            return False
        if len(message.embeds) > 0 or len(message.attachments) > 0:
            return
        if config.MediaOnlyChannels.fetch(message.channel.id):
            self.bot.send_DM(message.author,
                             f"Hi {message.author.name}, the channel you just tried to message in, "
                             f"{self.bot.get_channel(message.channel.id).name} is a 'Media Only' channel. "
                             f"This means you must attach a file in order to post there. "
                             f"Here is your message if you want to paste it again after the adequate changes: "
                             f"```\n{message.content}\n```")
            await message.delete()
            return True
        return False
