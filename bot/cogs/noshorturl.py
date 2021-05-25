import discord.ext.commands as commands
import re
from config import Misc


class NoShortUrl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def process_message(self, message):
        if message.author.permissions_in(self.bot.get_channel(Misc.fetch("filter_channel"))).send_messages or \
                message.author.id == 227473074616795137:  # is Feyko?
            return
        found = re.search(r'https?://(bit\.ly|cutt\.ly|shorturl\.at)/\S+', message.content)
        if found:
            sent = self.bot.send_DM(message.author,
                                    f"Hi {message.author.name}. We do not accept shortened urls as we cannot moderate "
                                    f"and verify each and every one of them. Please send the full url. "
                                    f"Here is your message if you want to paste it again after the adequate changes: "
                                    f"```\n{message.content}\n```")
            if not sent:  # if you can't DM
                self.bot.reply_to_msg(message,
                                      f"Hi {message.author.name}. We do not accept shortened urls as we cannot "
                                      f"moderate and verify each and every one of them. Please send the full url.")
            await message.delete()
            return True
        return False
