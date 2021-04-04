import discord.ext.commands as commands
import config


class MediaOnly(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def process_message(self, message):
        if message.author.permissions_in(self.bot.get_channel(
                config.Misc.get_filter_channel())).send_messages or message.author.id == 227473074616795137:
            return
        if len(message.embeds) > 0 or len(message.attachments) > 0:
            return
        if config.MediaOnlyChannels.fetch(message.channel.id):
            if not message.author.dm_channel:
                await message.author.create_dm()
            try:
                await message.author.send(
                    "Hi " + message.author.name + ", the channel '" + self.bot.get_channel(message.channel.id).name
                    + "' you just tried to message in has been flagged as a 'Media Only' "
                      "channel. This means you must attach a file in order to "
                      "post there. Here is your "
                      "message if you want to paste it again after the adequate changes : "
                      "```\n" + message.content + "\n```")
            except:
                pass
            await message.delete()
            return True
        return False
