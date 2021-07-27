import discord.ext.commands as commands
from discord import DMChannel
import config
from datetime import *


class UserProfile:
    def __init__(self, user_id, guild, bot):
        self.guild = guild
        self.bot = bot
        self.user_id = user_id
        self.member = guild.get_member(self.user_id)
        if DB_user := config.Users.fetch(self.user_id):
            self.DB_user = DB_user
        else:
            self.DB_user = config.Users(user_id=user_id,
                                        full_name=f"{self.member.name}#{self.member.discriminator}")

        self.rank = self.DB_user.rank
        self.xp_count = self.DB_user.xp_count
        self._xp_exp = 1.05
        self._xp_base = 200

    async def validate_role(self):
        if not self.member:
            self.bot.logger.warning("I was unable to validate a role because I could not get the member")
        if role_id := config.RankRoles.fetch_by_rank(self.rank):
            role = self.guild.get_role(role_id)
            if not role:
                self.bot.logger.warning("I was unable to validate a role because I could not get a role")
                return
            self.DB_user.rank_role_id = role_id
            # self.rank_role_id = role_id
            if not self.member.permissions_in(self.bot.modchannel).send_messages:
                for member_role in self.member.roles:
                    rank = config.RankRoles.fetch_by_role(member_role.id)
                    if rank:
                        await self.member.remove_roles(member_role)
                await self.member.add_roles(role)

    def _xp_cost(self, level: int) -> float:
        return 0 if level < 1 else self._xp_base * pow(self._xp_exp, level - 1)

    def xp_requirement(self, level: int) -> float:
        if level < 1:
            return 0
        else:
            return self.xp_requirement(level - 1) + \
                   self._xp_cost(level)

    async def validate_rank(self):
        expected_rank = self.rank
        print("Validating rank.")
        while True:
            if self.xp_count < self.xp_requirement(self.rank):
                expected_rank -= 1
                print(self.member.name, "will advance one rank!")
            elif self.xp_count >= self.xp_requirement(self.rank + 1):
                print(self.member.name, "will decrease one rank!")
                expected_rank += 1
            else:
                print(f"{self.member.name}'s rank remains unchanged.")
                break

        if expected_rank != self.rank:
            self.bot.logger.info(f"Correcting a mismatched rank from {self.rank} to {expected_rank}")
            self.DB_user.rank = expected_rank
            if self.DB_user.accepts_dms:
                if expected_rank > self.rank:
                    await self.bot.send_DM(self.member,
                                           f"You went up from rank {self.rank} to rank {expected_rank}! "
                                           f"Congratulations!")
                else:
                    await self.bot.send_DM(self.member,
                                           f"You went down from rank {self.rank} to rank {expected_rank}... "
                                           f"Sorry about that")
            self.rank = expected_rank
        await self.validate_role()

    async def increment_xp(self):
        await self.give_xp(
            config.Misc.fetch("xp_gain_value") * self.DB_user.xp_multiplier * self.DB_user.role_xp_multiplier
        )

    async def give_xp(self, xp: float):
        if xp <= 0:
            return
        self.DB_user.xp_count += xp
        self.xp_count += xp
        await self.validate_rank()

    async def take_xp(self, xp: float):
        if xp <= 0:
            return
        self.DB_user.xp_count -= xp
        self.xp_count -= xp
        await self.validate_rank()

    async def set_xp(self, xp: float):
        if xp <= 0:
            return False
        self.DB_user.xp_count = xp
        self.xp_count = xp
        await self.validate_rank()
        return True


class Levelling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.xp_timers = {}

    # TODO make xp roles
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.roles != after.roles:
            config.XpRoles

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or isinstance(message.channel, DMChannel) or \
                message.guild.id != config.Misc.fetch("main_guild_id") or not config.Misc.fetch("levelling_state"):
            return
        profile = UserProfile(message.author.id, message.guild, self.bot)
        profile.DB_user.message_count += 1
        if profile.user_id in self.bot.xp_timers:
            if datetime.now() >= self.bot.xp_timers[profile.user_id]:
                await profile.increment_xp()
        self.bot.xp_timers[profile.user_id] = datetime.now() + timedelta(seconds=config.Misc.fetch("xp_gain_delay"))
