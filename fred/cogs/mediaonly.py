from nextcord import Message, Thread, ForumChannel

from .. import config
from ..libraries import common
from ..libraries.common import FredCog


class MediaOnly(FredCog):

    async def process_message(self, message: Message) -> bool:
        """Returns whether the message was removed."""
        if isinstance(message.channel, Thread):
            if (
                isinstance(message.channel.parent, ForumChannel)
                and message.id == message.channel.id  # we only care if it's the initial post
                and config.MediaOnlyChannels.check(message.channel.parent_id)  # last because it's a DB call
            ):
                return await self._process_forum_message(message)
            else:
                return False
        elif config.MediaOnlyChannels.check(message.channel.id):
            return await self._process_regular_message(message)

        return False

    async def _process_regular_message(self, message: Message) -> bool:
        self.logger.info("Checking a message", extra=common.message_info(message))

        if len(message.embeds) > 0 or len(message.attachments) > 0:
            self.logger.info("Message contains media", extra=common.message_info(message))
            return False

        ctx = await self.bot.get_context(message)

        if await common.l4_only(ctx):
            self.logger.info("Message doesn't contain media but the author is a T3", extra=common.message_info(message))
            return False

        self.logger.info("Removing a message", extra=common.message_info(message))
        await message.delete()
        await self.bot.send_DM(
            message.author,
            f"Hi {message.author.mention}, "
            f"{message.channel.mention} is a 'media-only' channel. "
            f"This means posts there must have files or embedded links. "
            f"Here is your message if you want to paste it again after the adequate changes: "
            f"```\n{message.content}\n```",
        )
        return True

    async def _process_forum_message(self, message: Message) -> bool:

        self.logger.info("Checking a thread", extra=common.message_info(message))

        if len(message.embeds) > 0 or len(message.attachments) > 0:
            self.logger.info("Message contains media", extra=common.message_info(message))
            return False

        ctx = await self.bot.get_context(message)

        if await common.l4_only(ctx):
            self.logger.info("Message doesn't contain media but the author is a T3", extra=common.message_info(message))
            return False

        self.logger.info("Removing a thread", extra=common.message_info(message))
        await message.channel.delete()
        await self.bot.send_DM(
            message.author,
            f"Hi {message.author.mention}, "
            f"{message.channel.parent.mention} is a 'media-only' forum. "
            f"This means posts there must have files or embedded links. "
            f"Here is your message if you want to paste it again after the adequate changes: "
            f"\n\n**Title: **`{message.channel.name}`\n"
            f"```\n{message.content}\n```",
        )
        return True
