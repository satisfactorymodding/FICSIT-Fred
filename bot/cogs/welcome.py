import discord.ext.commands as commands
import config


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        welcome = config.Misc.fetch("welcome_message")
        info = config.Misc.fetch("latest_info")
        if welcome:
            await self.bot.send_DM(member, welcome)
        if info:
            info = f"Here's the latest information :\n\n{info}"
            await self.bot.send_DM(member, info)
