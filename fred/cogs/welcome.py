from nextcord import Member
from nextcord.ext import commands

from .. import config
from ..libraries import common


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: Member):
        self.bot.logger.info("Processing a member joining", extra=common.user_info(member))
        if welcome := config.Misc.fetch("welcome_message"):
            self.bot.logger.info("Sending the welcome message to a new member", extra=common.user_info(member))
            await self.bot.send_DM(member, welcome)
        if info := config.Misc.fetch("latest_info"):
            self.bot.logger.info("Sending the latest information to a new member", extra=common.user_info(member))
            info = f"Here's the latest information :\n\n{info}"
            await self.bot.send_DM(member, info)
