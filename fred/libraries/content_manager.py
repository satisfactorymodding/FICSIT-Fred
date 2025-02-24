from __future__ import annotations

from asyncio import Event, as_completed
from io import BytesIO
from os.path import splitext, split
from typing import Any, Coroutine, Optional, Generator
from urllib.parse import urlparse

from re2 import findall as re2findall
from aiohttp import ClientSession as HTTPClientSession, ClientResponseError
from nextcord import Message, File as NCFile

from fred.libraries.common import new_logger

DOWNLOAD_SIZE_LIMIT = 104857600  # 100 MiB


class ContentManager:

    logger = new_logger(__name__)

    class ManagedFile(BytesIO):

        class NotDoneWithFile(Exception):
            pass

        def __init__(self, *args, filename: str = "", text=False, **kwargs):
            super().__init__(*args, **kwargs)
            self.filename = filename
            self._done: Event = Event()
            self.text = text

        def close(self):
            if not self.done:
                raise self.NotDoneWithFile
            super().close()

        def mark_done(self):
            self._done.set()

        @property
        def done(self):
            return self._done.is_set()

        async def wait_done(self):
            await self._done.wait()

        def to_nc_file(self) -> NCFile:
            return NCFile(self, filename=self.filename, force_close=False)

    # spacer here for ease of reading where ManagedFile ends and the ContentManager methods begin

    def __init__(self):
        self.files: list[ContentManager.ManagedFile] = []

    async def __aenter__(self):
        self.logger.info("Entering content manager context")

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.logger.info("Content manager context exit requested, ensuring files are closed.")
        while self.files:
            file = self.files.pop()
            await file.wait_done()
            file.close()
            del file
        self.logger.info("Exiting content manager context.")
        return True

    def all_done(self):
        for file in self.files:
            file.mark_done()

    def add_file(self, file: ContentManager.ManagedFile):
        self.files.append(file)

    def add_files(self, files: list[ContentManager.ManagedFile]):
        self.files.extend(files)

    def to_nc_files(self) -> list[NCFile]:
        return [*map(lambda file: file.to_nc_file(), self.files)]

    @classmethod
    async def from_message(cls, message: Message, web_session: HTTPClientSession) -> ContentManager:

        cm = ContentManager()

        for att in message.attachments:
            mf = ContentManager.ManagedFile(filename=att.filename, text=cls.is_text(att.content_type))
            await att.save(fp=mf)
            cm.add_file(mf)

        for fut_maybe_file in as_completed(ContentManager.yoink_cdn_link_files(message.content, web_session)):
            if (file := await fut_maybe_file) is not None:
                cm.add_file(file)

        return cm

    @staticmethod
    def is_text(mime: str) -> bool:
        return mime in ("text/plain", "application/json")

    @classmethod
    def yoink_cdn_link_files(
        cls, message_content: str, web_session: HTTPClientSession
    ) -> Generator[Coroutine[Any, Any, ManagedFile | None], None, None]:
        cdn_links = re2findall(
            r"(https://(?:cdn.discordapp.com|media.discordapp.net)/attachments/\S+)", message_content
        )

        cls.logger.info(f"Found {len(cdn_links)} files via link to CDN. Attempting to acquire them.")


        async def obtain_file(att_url: str) -> Optional[ContentManager.ManagedFile]:

            url_path = urlparse(att_url).path
            _, filename = split(url_path)
            _, file_ext = splitext(filename)

            if file_ext[1:] in ("png", "log", "txt", "zip", "json"):
                try:
                    async with web_session.head(att_url, raise_for_status=True) as response:
                        if (size := response.content_length) > DOWNLOAD_SIZE_LIMIT:
                            cls.logger.warning(f"File {filename} unreasonably large! ({size} bytes)")
                            return None

                    async with web_session.get(att_url, raise_for_status=True) as response:

                        return ContentManager.ManagedFile(
                            await response.content.read(), filename=filename, text=cls.is_text(response.content_type)
                        )

                except ClientResponseError as e:
                    cls.logger.error(e)
                    return None
            return None

        for cdn_link in cdn_links:
            yield obtain_file(cdn_link)
