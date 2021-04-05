import discord.ext.commands as commands
import re
from config import Misc
class NoShortUrl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def process_message(self, message):
        if message.author.permissions_in(self.bot.get_channel(Misc.fetch("filter_channel"))).send_messages or message.author.id == 227473074616795137:
            return
        found = re.search(r'https?://(bit\.ly|cutt\.ly|shorturl\.at)/\S+', message.content)
        if found:
            if not message.author.dm_channel:
                await message.author.create_dm()
            try:
                await message.author.send(
                    "Hi " + message.author.name + ". We do not accept shortened urls as we cannot moderate and verify "
                                                  "each and every one of them. Please send the full url. Here is your "
                                                  "message if you want to paste it again after the adequate changes : "
                                                  "```\n" + message.content + "\n```")
            except:
                pass
            await message.delete()
            return True
        return False
