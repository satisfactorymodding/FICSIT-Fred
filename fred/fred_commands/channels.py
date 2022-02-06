from ._baseclass import BaseCmds, commands, config, common


class ChannelCmds(BaseCmds):

    @BaseCmds.add.command(name="mediaonly")
    async def add_mediaonly(self, ctx: commands.Context, channel: commands.TextChannelConverter):
        """Usage: `add mediaonly (channel)`
        Purpose: Adds channel to the list of channels that are managed to be media-only
        Notes: Limited to permission level 4 and above"""
        if config.MediaOnlyChannels.fetch(channel.id):
            await self.bot.reply_to_msg(ctx.message, "This channel is already a media only channel")
            return

        config.MediaOnlyChannels(channel_id=channel.id)
        await self.bot.reply_to_msg(ctx.message,
                                    f"Media Only channel {self.bot.get_channel(channel.id).mention} added!")

    @BaseCmds.remove.command(name="mediaonly")
    async def remove_mediaonly(self, ctx: commands.Context, channel: commands.TextChannelConverter):
        """Usage: `add mediaonly (channel)`
        Purpose: Removes channel from the list of channels that are managed to be media-only
        Notes: Limited to permission level 4 and above"""
        if not config.MediaOnlyChannels.fetch(channel.id):
            await self.bot.reply_to_msg(ctx.message, "Media Only Channel could not be found!")
            return

        config.MediaOnlyChannels.deleteBy(channel_id=channel.id)
        await self.bot.reply_to_msg(ctx.message,
                                    f"Media Only channel {self.bot.get_channel(channel.id).mention} removed!")

    @BaseCmds.add.command(name="dialogflowChannel")
    async def add_dialogflow_channel(self, ctx: commands.Context, channel: commands.TextChannelConverter):
        """Usage: `add dialogflowChannel (channel)`
        Purpose: Adds channel to the list of channels that natural language processing is applied to
        Notes: probably don't mess around with this, Mircea is the only wizard that knows how these works"""
        if config.DialogflowChannels.fetch(channel.id):
            await self.bot.reply_to_msg(ctx.message, "This channel is already a dialogflow channel!")
        else:
            config.DialogflowChannels(channel_id=channel.id)
            await self.bot.reply_to_msg(ctx.message,
                                        f"Dialogflow channel {self.bot.get_channel(channel.id).mention} added!")

    @BaseCmds.remove.command(name="dialogflowChannel")
    async def remove_dialogflow_channel(self, ctx: commands.Context, channel: commands.TextChannelConverter):
        """Usage: `remove dialogflowChannel (channel)`
        Purpose: Removes channel from the list of channels that natural language processing is applied to
        Notes: probably don't mess around with this, Mircea is the only wizard that knows how these works"""
        if config.DialogflowChannels.fetch(channel.id):
            config.DialogflowChannels.deleteBy(channel_id=channel.id)
            await self.bot.reply_to_msg(ctx.message,
                                        f"Dialogflow Channel {self.bot.get_channel(channel.id).mention} removed!")
        else:
            await self.bot.reply_to_msg(ctx.message, "Dialogflow channel could not be found!")

    @BaseCmds.set.command(name="webhook_channel")
    @commands.check(common.mod_only)
    async def set_webhook_channel(self, ctx: commands.Context, channel: commands.TextChannelConverter):
        """Usage: `set webhook_channel (channel: int | channel mention)`
        Purpose: changes where GitHub webhooks are sent
        Notes: unless you're testing me as a beta fork, don't use this"""
        config.Misc.change("githook_channel", channel.id)
        await self.bot.reply_to_msg(ctx.message,
                                    f"The channel for the github hooks is now "
                                    f"{self.bot.get_channel(channel.id).mention}!")
