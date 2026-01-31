import nextcord
from nextcord.abc import GuildChannel
from nextcord import Interaction, SlashOption, TextChannel, ForumChannel
from nextcord.ext.commands import Cog

from ._baseclass import BaseCmds, commands, config, common


class ChannelCmds(BaseCmds, Cog):

    @BaseCmds.add.command(name="mediaonly")
    async def add_mediaonly(self, ctx: commands.Context, channel: commands.GuildChannelConverter):
        """Usage: `add mediaonly (channel)`
        Purpose: Adds channel to the list of channels that are managed to be media-only
        Notes: Limited to permission level 4 and above"""
        channel: GuildChannel

        if not can_enforce_mediaonly(channel):
            await self.bot.reply_to_msg(ctx.message, f"I don't know how to enforce mediaonly in {channel.mention}.")
            return

        if config.MediaOnlyChannels.check(channel.id):
            await self.bot.reply_to_msg(ctx.message, f"{channel.mention} is already a media only channel")
            return

        config.MediaOnlyChannels(channel_id=channel.id)
        await self.bot.reply_to_msg(ctx.message, f"Media-only channel {channel.mention} added!")

    @BaseCmds.remove.command(name="mediaonly")
    async def remove_mediaonly(self, ctx: commands.Context, channel: commands.GuildChannelConverter):
        """Usage: `add mediaonly (channel)`
        Purpose: Removes channel from the list of channels that are managed to be media-only
        Notes: Limited to permission level 4 and above"""
        channel: GuildChannel

        if not config.MediaOnlyChannels.check(channel.id):
            await self.bot.reply_to_msg(ctx.message, f"{channel.mention} is not marked as a media-only channel!")
            return

        config.MediaOnlyChannels.deleteBy(channel_id=channel.id)
        await self.bot.reply_to_msg(ctx.message, f"{channel.mention} is no longer a media-only channel.")

    @BaseCmds.set.command(name="webhook_channel")
    @commands.check(common.mod_only)
    async def set_webhook_channel(self, ctx: commands.Context, channel: commands.TextChannelConverter):
        """Usage: `set webhook_channel (channel: int | channel mention)`
        Purpose: changes where GitHub webhooks are sent
        Notes: unless you're testing me as a beta fork, don't use this"""
        channel: TextChannel
        config.Misc.change("githook_channel", channel.id)
        await self.bot.reply_to_msg(
            ctx.message, f"The channel for the github hooks is now " f"{self.bot.get_channel(channel.id).mention}!"
        )

    @commands.check(common.mod_only)
    @BaseCmds.set.command(name="error_channel")
    async def set_error_channel(self, ctx: commands.Context, error_channel_id: int):
        """Usage: `set error_channel [error_channel]`
        Purpose: changes what error channel is used to send errors to.
        Notes: no touchy please!
        """
        if (chan := self.bot.get_channel(int(error_channel_id))) is None:
            await self.bot.reply_to_msg(ctx.message, "I can't see that channel!")
        else:
            self.bot.error_channel = error_channel_id
            config.Misc.create_or_change("error_channel", error_channel_id)
            await self.bot.reply_to_msg(ctx.message, f"The error channel has been changed to {chan.mention}.")

    # @nextcord.slash_command(
    #     name="add_mediaonly",
    #     description="Adds a channel to the media-only list."
    # )
    # async def add_mediaonly_slash(
    #     self,
    #     interaction: Interaction,
    #     channel: TextChannel = SlashOption(description="The channel to add to media-only")
    # ):
    #     if not can_enforce_mediaonly(channel):
    #         await interaction.response.send_message(f"I don't know how to enforce mediaonly in {channel.mention}.")
    #         return

    #     if config.MediaOnlyChannels.check(channel.id):
    #         await interaction.response.send_message(f"{channel.mention} is already a media-only channel")
    #         return

    #     config.MediaOnlyChannels(channel_id=channel.id)
    #     await interaction.response.send_message(f"Media-only channel {channel.mention} added!")

    # @nextcord.slash_command(
    #     name="remove_mediaonly",
    #     description="Removes a channel from the media-only list."
    # )
    # async def remove_mediaonly_slash(
    #     self,
    #     interaction: Interaction,
    #     channel: TextChannel = SlashOption(description="The channel to remove from media-only")
    # ):
    #     if not config.MediaOnlyChannels.check(channel.id):
    #         await interaction.response.send_message(f"{channel.mention} is not marked as a media-only channel!")
    #         return

    #     config.MediaOnlyChannels.deleteBy(channel_id=channel.id)
    #     await interaction.response.send_message(f"{channel.mention} is no longer a media-only channel.")


def can_enforce_mediaonly(channel: GuildChannel) -> bool:
    return isinstance(channel, (TextChannel, ForumChannel))
