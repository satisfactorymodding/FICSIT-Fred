from fred_core_imports import *
from libraries import common

import nextcord.ext.commands as commands


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        logging.info("Processing a member joining", extra=common.userdict(member))
        welcome = config.Misc.fetch("welcome_message")
        info = config.Misc.fetch("latest_info")
        if welcome:
            logging.info("Sending the welcome message to a new member", extra=common.userdict(member))
            await self.bot.send_DM(member, welcome)
        if info:
            logging.info("Sending the latest information to a new member", extra=common.userdict(member))
            info = f"Here's the latest information :\n\n{info}"
            await self.bot.send_DM(member, info)
