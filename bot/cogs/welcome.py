import nextcord.ext.commands as commands

import config
from libraries import common


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        self.bot.logger.info("Processing a member joining", extra=common.user_info(member))
        welcome = config.Misc.fetch("welcome_message")
        info = config.Misc.fetch("latest_info")
        if welcome:
            self.bot.logger.info("Sending the welcome message to a new member", extra=common.user_info(member))
            await self.bot.send_DM(member, welcome)
        if info:
            self.bot.logger.info("Sending the latest information to a new member", extra=common.user_info(member))
            info = f"Here's the latest information :\n\n{info}"
            await self.bot.send_DM(member, info)
