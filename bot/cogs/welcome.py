import discord.ext.commands as commands
import config


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if not member.dm_channel:
            await member.create_dm()
        try:
            welcome = config.Misc.get_welcome_message()
            info = config.Misc.get_latest_info()
            if welcome:
                await member.send(welcome)
            if info:
                info = "Here's the latest information :\n\n" + info
                await member.send(info)
        except:
            pass
