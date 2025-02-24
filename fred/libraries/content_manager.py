from __future__ import annotations

from asyncio import as_completed, Condition
from io import BytesIO
from os.path import splitext, split
from threading import Lock
from typing import Any, Coroutine, Optional, Generator
from urllib.parse import urlparse
from zipfile import ZipFile

from aiohttp import ClientSession as HTTPClientSession, ClientResponseError
from nextcord import Message, File as NCFile
from re2 import findall as re2findall

from fred.libraries.common import new_logger

DOWNLOAD_SIZE_LIMIT = 104857600  # 100 MiB


class ContentManager:

    logger = new_logger(__name__)

    class SyncKeeper:
        def __init__(self, name: str = "<anonymous sync object>") -> None:
            self.name = name
            self.users = 0
            self._done = Condition()
            self.lock = Lock()

        def mark_using(self):
            ContentManager.logger.debug(f"Something wants to use <{self.name}>")
            with self.lock:
                self.users += 1

        def mark_done(self):
            ContentManager.logger.debug(f"Something is done with <{self.name}>")
            with self.lock:
                self.users -= 1

        @property
        def done(self):
            return self.users == 0

        async def wait_done(self):
            async with self._done:
                await self._done.wait_for(lambda: self.users == 0)

    class ManagedFile(BytesIO):
        """
        A file managed by a ContentManager. Access must be conducted with the Lock provided.
        It must have no one using it to be closed by the ContentManager.
        """

        class NotDoneWithFile(Exception):
            pass

        def __init__(self, *args, filename: str = "", text=False, **kwargs):
            super().__init__(*args, **kwargs)
            self.filename = filename
            self._sync = ContentManager.SyncKeeper(filename)
            self.text = text

        def close(self):
            if not self.sync.done:
                raise self.NotDoneWithFile
            super().close()

        @property
        def sync(self):
            return self._sync

        def to_nc_file(self) -> NCFile:
            return NCFile(self, filename=self.filename, force_close=False)

        def __repr__(self) -> str:
            return f"<ManagedFile: {self.filename}>"

    # spacer here for ease of reading where ManagedFile ends and the ContentManager methods begin

    def __init__(self, name: str = "<anonymous context manager>") -> None:
        self.name = name
        self._files: list[ContentManager.ManagedFile] = []
        self._children: list[ContentManager] = []
        self._sync = ContentManager.SyncKeeper(name)

    @property
    def sync(self):
        return self._sync

    async def __aenter__(self):
        self.logger.info("Entering content manager context")
        return self

    async def _close_all_when_done(self):
        for child in self._children:
            self.logger.info("Closing child content manager")
            await child.sync.wait_done()
            await child._close_all_when_done()
        while self._files:
            file = self._files.pop()
            self.logger.debug(f"Waiting for {file.filename} to be done")
            await file.sync.wait_done()
            self.logger.debug(f"Closing {file.filename}")
            file.close()
            del file

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool | None:
        if exc_type is None:
            self.logger.info("Content manager context exit requested, ensuring files are closed.")
            await self._close_all_when_done()
            self.logger.info("Exiting content manager context.")
            return True

        self.logger.warning("Content manager exiting due to an error. Attempting to close everything.")
        self.logger.exception(exc_val)
        self.mark_all_done()
        self.mark_children_done()
        await self._close_all_when_done()
        self.logger.warning("Successfully closed everything, exception will now be raised.")

    def mark_all_done(self):
        for file in self._files:
            file.sync.mark_done()

    def mark_children_done(self):
        for child in self._children:
            child.mark_all_done()
            child.sync.mark_done()

    def add_file(self, file: ContentManager.ManagedFile):
        self._files.append(file)

    def add_files(self, files: list[ContentManager.ManagedFile]):
        self._files.extend(files)

    def add_child(self, child: ContentManager):
        self._children.append(child)

    def to_nc_files(self) -> list[NCFile]:
        return [*map(lambda file: file.to_nc_file(), self._files)]

    def has_files(self) -> bool:
        return len(self._files) > 0

    def are_all_done(self) -> bool:
        return all(map(lambda file: file.done, self._files))

    def get_files(self) -> list[ManagedFile]:
        return self._files.copy()  # so we don't allow modification of the internal list, which can leak unclosed files

    def searchable(self) -> dict[str, list[ManagedFile]]:
        d = {}
        for file in self._files:
            files_by_this_name = d.setdefault(file.filename, [])
            files_by_this_name.append(file)

        return d

    @classmethod
    async def from_message(cls, message: Message, web_session: HTTPClientSession) -> ContentManager:

        cm = ContentManager(f"Context Manager for message {message.id}")

        if message.attachments:
            cls.logger.info(f"Found {len(message.attachments)} direct attachments. Attempting to acquire them.")

        for att in message.attachments:
            mf = ContentManager.ManagedFile(filename=att.filename, text=cls.is_text(att.content_type))
            await att.save(fp=mf)
            cm.add_file(mf)

        for fut_maybe_file in as_completed(ContentManager._yoink_cdn_link_files(message.content, web_session)):
            if (file := await fut_maybe_file) is not None:
                cm.add_file(file)

        cls.logger.info(f"ContentManager made with {cm.get_files()}")

        return cm

    @classmethod
    def from_zipfile(cls, zip_file: ZipFile, filename: str) -> ContentManager:
        cm = ContentManager(f"Content Manager for {filename}")

        for zip_filename in zip_file.namelist():
            with zip_file.open(zip_filename) as file:
                cm.add_file(ContentManager.ManagedFile(file.read(), filename=f"{filename}/{zip_filename}"))

        cls.logger.info(f"ContentManager made with {cm.get_files()}")

        return cm

    @staticmethod
    def is_text(mime: str) -> bool:
        return mime in ("text/plain", "application/json")

    @classmethod
    def _yoink_cdn_link_files(
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
            cls.logger.debug(f"Queue fetch {cdn_link}")
            yield obtain_file(cdn_link)
