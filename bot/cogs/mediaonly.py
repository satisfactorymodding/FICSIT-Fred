import discord.ext.commands as commands

class MediaOnly(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def process_message(self, message):
        if message.author.permissions_in(self.bot.get_channel(self.bot.config["filter channel"])).send_messages or message.author.id == 227473074616795137:
            return
        for automation in self.bot.config["media only channels"]:
            if message.channel.id == automation and len(message.embeds) == 0 and len(
                    message.attachments) == 0:
                if not message.author.dm_channel:
                    await message.author.create_dm()
                try:
                    await message.author.send(
                        "Hi " + message.author.name + ", the channel '" + self.bot.get_channel(automation).name
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
