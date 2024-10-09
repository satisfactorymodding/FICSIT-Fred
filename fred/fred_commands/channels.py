from nextcord import TextChannel, ForumChannel
from nextcord.abc import GuildChannel

from ._baseclass import BaseCmds, commands, config, common


class ChannelCmds(BaseCmds):

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

    @BaseCmds.add.command(name="dialogflowChannel")
    async def add_dialogflow_channel(self, ctx: commands.Context, channel: commands.TextChannelConverter):
        """Usage: `add dialogflowChannel (channel)`
        Purpose: Adds channel to the list of channels that natural language processing is applied to
        Notes: probably don't mess around with this, Mircea is the only wizard that knows how these works"""
        channel: TextChannel

        if config.DialogflowChannels.check(channel.id):
            await self.bot.reply_to_msg(ctx.message, "This channel is already a dialogflow channel!")
        else:
            config.DialogflowChannels(channel_id=channel.id)
            await self.bot.reply_to_msg(
                ctx.message, f"Dialogflow channel {self.bot.get_channel(channel.id).mention} added!"
            )

    @BaseCmds.remove.command(name="dialogflowChannel")
    async def remove_dialogflow_channel(self, ctx: commands.Context, channel: commands.TextChannelConverter):
        """Usage: `remove dialogflowChannel (channel)`
        Purpose: Removes channel from the list of channels that natural language processing is applied to
        Notes: probably don't mess around with this, Mircea is the only wizard that knows how these works"""
        channel: TextChannel

        if config.DialogflowChannels.check(channel.id):
            config.DialogflowChannels.deleteBy(channel_id=channel.id)
            await self.bot.reply_to_msg(
                ctx.message, f"Dialogflow Channel {self.bot.get_channel(channel.id).mention} removed!"
            )
        else:
            await self.bot.reply_to_msg(ctx.message, "Dialogflow channel could not be found!")

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


def can_enforce_mediaonly(channel: GuildChannel) -> bool:
    return isinstance(channel, (TextChannel, ForumChannel))
