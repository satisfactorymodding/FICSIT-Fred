from nextcord import Message

from .. import config
from ..libraries import common
from ..libraries.common import FredCog


class MediaOnly(FredCog):

    async def process_message(self, message: Message) -> bool:
        """Returns whether the message was removed."""
        self.logger.info("Processing a message", extra=common.message_info(message))

        if len(message.embeds) > 0 or len(message.attachments) > 0:
            self.logger.info("Message contains media", extra=common.message_info(message))
            return False

        ctx = await self.bot.get_context(message)

        if await common.l4_only(ctx):
            self.logger.info("Message doesn't contain media but the author is a T3", extra=common.message_info(message))
            return False

        if config.MediaOnlyChannels.check(message.channel.id):
            self.logger.info("Removing a message", extra=common.message_info(message))
            await message.delete()
            await self.bot.send_DM(
                message.author,
                f"Hi {message.author.name}, the channel you just tried to message in, "
                f"{self.bot.get_channel(message.channel.id).name} is a 'Media Only' channel. "
                f"This means you must attach a file in order to post there. "
                f"Here is your message if you want to paste it again after the adequate changes: "
                f"```\n{message.content}\n```",
            )
            return True

        return False
