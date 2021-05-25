import discord.ext.commands as commands
import config


class MediaOnly(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def process_message(self, message):
        if message.author.permissions_in(self.bot.get_channel(
                config.Misc.fetch("filter_channel"))).send_messages or message.author.id == 227473074616795137:
            return
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
