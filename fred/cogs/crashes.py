from __future__ import annotations

import asyncio
import io
import json
from asyncio import Task, TaskGroup
from os.path import split
from pathlib import Path
from typing import AsyncIterator, IO, Type, Coroutine, Generator, Optional, Any, Final, TypedDict, AsyncGenerator
from urllib.parse import urlparse
from zipfile import ZipFile

import re2

re2.set_fallback_notification(re2.FALLBACK_WARNING)

from PIL import Image, ImageEnhance
from aiohttp import ClientResponseError
from attr import dataclass
from nextcord import Message, HTTPException, Forbidden, NotFound
from pytesseract import image_to_string, TesseractError
from semver import Version

from .. import config
from ..libraries import createembed
from ..libraries.common import FredCog, new_logger
from ..libraries.createembed import CrashResponse

REGEX_LIMIT: float = 6.9
DOWNLOAD_SIZE_LIMIT = 104857600  # 100 MiB
EMOJI_CRASHES_ANALYZING = "<:FredAnalyzingFile:1283182945019891712>"
EMOJI_CRASHES_TIMEOUT = "<:FredAnalyzingTimedOut:1283183010967195730>"

logger = new_logger(__name__)


async def regex_with_timeout(*args, **kwargs):
    try:
        return await asyncio.wait_for(asyncio.to_thread(re2.search, *args, **kwargs), REGEX_LIMIT)
    except asyncio.TimeoutError:
        raise TimeoutError(
            f"A regex timed out after {REGEX_LIMIT} seconds! \n"
            f"pattern: ({args[0]}) \n"
            f"flags: {kwargs['flags']} \n"
            f"on text of length {len(args[1])}"
        )
    except re2.RegexError as e:
        raise ValueError(args[0]) from e


class Crashes(FredCog):

    type CrashJob = Coroutine[Any, Any, list[CrashResponse]]
    type CrashJobGenerator = Generator[Crashes.CrashJob, None, None]

    async def make_sml_version_message(self, game_version: int = 0, sml: str = "", **_) -> Optional[CrashResponse]:
        if game_version and sml:
            # Check the right SML for that CL
            query = """{
              getSMLVersions {
                sml_versions {
                  version
                  satisfactory_version
                }
              }
            }"""
            result = await self.bot.repository_query(query)
            sml_versions = result["data"]["getSMLVersions"]["sml_versions"]
            is_compatible = lambda s: s["satisfactory_version"] <= game_version
            latest_compatible_sml = next(filter(is_compatible, sml_versions))
            if (new_version := latest_compatible_sml["version"]) != sml:
                msg: str = (
                    "You are not using the most recent SML release for your game. " f"Please update to {new_version}."
                )
                if latest_compatible_sml != sml_versions[0]:
                    msg += "\nAlso, your game itself may need an update!"
                return CrashResponse("Outdated SML!", msg, inline=True)
            else:
                return None

    # fmt: off
    # we don't need id but a bug with the API means it must be requested to return versions
    # TODO remove this when the patched API is in prod
    _QUERY_TEMPLATE: Final[str] = """
    {
      getMods(filter: {references: %s, limit: 100}) {
        mods {
          id
          name
          mod_reference
          versions(filter: {limit: 1, order: desc}) {
            version
          }
          compatibility {
            %s {
              state
              note
            }
          }
        }
      }
    }
    """
    # fmt: on

    class _ModLookupGQLResponse(TypedDict):
        id: str
        name: str
        mod_reference: str
        versions: list[dict[str, str]]
        compatibility: dict[str, dict[str, str]]

    async def check_mods(
        self, input_mods: InstallInfo.InstalledMods, experimental: bool = False
    ) -> list[CrashResponse]:
        responses: list[CrashResponse] = []
        if not input_mods:
            return responses

        # This separates the mods into blocks of 100 because of API restrictions
        def formatted_chunks_of_100_mod_references() -> Generator[str, None, None]:
            mods = input_mods.copy()
            while mods:
                new_chunk = []
                while mods and len(new_chunk) < 100:
                    new_chunk.append(mods.popitem()[0])
                yield json.dumps(new_chunk)

        queried_mods: list[Crashes._ModLookupGQLResponse] = []
        for chunk in formatted_chunks_of_100_mod_references():
            # formats the list appropriately for GQL
            game_branch = "EXP" if experimental else "EA"
            query = self._QUERY_TEMPLATE % (chunk, game_branch)

            queried_mods.extend(
                # this guarantees this won't annoyingly KeyError and will only add nothing
                (await self.bot.repository_query(query))
                .get("data", {})
                .get("getMods", {})
                .get("mods", [])
            )

        broken_mods: list[tuple[str, str]] = []
        outdated_mods: list[tuple[str, str]] = []
        for mod in queried_mods:
            mod_name = mod["name"]
            mod_compat = mod["compatibility"]
            compat_info = mod_compat.get("EA") or mod_compat.get("EXP")
            mod_latest_version = Version.parse(mod["versions"][0]["version"])

            if compat_info["state"] == "Broken":
                broken_mods.append((mod_name, compat_info["note"]))

            if mod_latest_version > input_mods[mod["mod_reference"]]:
                outdated_mods.append((mod_name, str(mod_latest_version)))

        if broken_mods:
            string = "\n".join(f"{mod[0]}: {mod[1]}" for mod in broken_mods)
            if len(string) > 900:  # fields have a 1024 char value length limit
                string = "TOO MANY BROKEN MODS TO LIST!!"
            string += (
                "\nPlease attempt to remove/disable these mods so that they no longer force the old SML to be used "
                "(this is why your mods don't load)."
            )

            responses.append(CrashResponse("Incompatible mods found!", string))

        if outdated_mods:
            string = "\n".join(f"{mod[0]} can be updated to `{mod[1]}`" for mod in outdated_mods)
            if len(string) > 900:  # fields have a 1024 char value length limit
                string = "TOO MANY OUTDATED MODS TO LIST!!"
            string += "\nUpdate these mods, there may be fixes for your issue in doing so."
            responses.append(CrashResponse("Outdated mods found!", string))
        return responses

    async def mass_regex(self, text: str) -> AsyncIterator[CrashResponse]:
        for crash in config.Crashes.fetch_all():
            if match := await regex_with_timeout(crash["crash"], text, flags=re2.IGNORECASE | re2.S):
                if str(crash["response"]).startswith(self.bot.command_prefix):
                    if command := config.Commands.fetch(crash["response"].strip(self.bot.command_prefix)):
                        command_response = command["content"]
                        if command_response.startswith(self.bot.command_prefix):  # is alias
                            command = config.Commands.fetch(command_response.strip(self.bot.command_prefix))
                        yield CrashResponse(
                            name=command["name"],
                            value=command["content"],
                            attachment=command["attachment"],
                            inline=True,
                        )
                else:
                    response = re2.sub(r"{(\d+)}", lambda m: match.group(int(m.group(1))), str(crash["response"]))
                    yield CrashResponse(name=crash["name"], value=response, inline=True)

    async def detect_and_fetch_pastebin_content(self, text: str) -> str:
        if match := re2.search(r"(https://pastebin.com/\S+)", text):
            self.logger.info("Found a pastebin link! Fetching text.")
            url = re2.sub(r"(?<=bin.com)/", "/raw/", match.group(1))
            async with self.bot.web_session.get(url) as response:
                return await response.text()
        else:
            return ""

    async def process_text(self, text: str) -> list[CrashResponse]:
        if not text:
            return []
        self.logger.info("Processing text.")
        responses = [msg async for msg in self.mass_regex(text)]
        responses.extend(await self.process_text(await self.detect_and_fetch_pastebin_content(text)))
        return responses

    async def process_image(self, file: IO) -> list[CrashResponse]:
        try:
            image = Image.open(file)
            ratio = 2160 / image.height
            if ratio > 1:
                image = image.resize(
                    (round(image.width * ratio), round(image.height * ratio)), Image.Resampling.LANCZOS
                )

            enhancer_contrast = ImageEnhance.Contrast(image)

            image = enhancer_contrast.enhance(2)
            enhancer_sharpness = ImageEnhance.Sharpness(image)
            image = enhancer_sharpness.enhance(10)

            image_text = await self.bot.loop.run_in_executor(self.bot.executor, image_to_string, image)
            self.logger.info("OCR returned the following data:\n" + image_text)
            return await self.process_text(image_text)

        except TesseractError as oops:
            self.logger.error(f"OCR error!")
            self.logger.exception(oops)
            return []

    def _create_debug_messages(self, debug_zip: ZipFile, filename: str) -> Optional[CrashJob]:
        files = debug_zip.namelist()
        info: Optional[InstallInfo] = None
        if "metadata.json" in files:
            with debug_zip.open("metadata.json") as f:
                info = InstallInfo.from_metadata_json(f, filename)

        if info is None:
            return

        if "FactoryGame.log" in files:
            with debug_zip.open("FactoryGame.log") as f:
                info.update_from_fg_log(f)

        async def coro_rtn():
            return [info.format(), *await self.check_mods(info.installed_mods)]

        return coro_rtn()

    def _get_file_jobs(self, filename: str, file: IO) -> CrashJobGenerator:
        match self._file_extension(filename):
            case "zip":
                self.logger.info(f"Adding jobs from zip file {filename}")
                zip_file = ZipFile(file)
                if res := self._create_debug_messages(zip_file, filename):
                    yield res
                for zipped_item_filename in zip_file.namelist():
                    with zip_file.open(zipped_item_filename) as zip_item:
                        yield from self._get_file_jobs(f"{filename}/{zipped_item_filename}", zip_item)
            case "log" | "txt" | "json":
                self.logger.info(f"Adding job for log/text file {filename}")
                yield self.process_text(str(file.read()))
            case "png":
                self.logger.info(f"Adding job for png file {filename}")
                yield self.process_image(file)
            case _:
                self.logger.info(f"Not adding any job for {filename}")

    @staticmethod
    def _file_extension(filename: str) -> str:
        return filename.rpartition(".")[-1].lower()

    @staticmethod
    def _ext_filter(ext: str) -> bool:
        return ext in ("png", "log", "txt", "zip", "json")

    async def _obtain_attachments(self, message: Message) -> AsyncGenerator[tuple[str, IO | Exception], None, None]:
        cdn_links = re2.findall(r"(https://cdn.discordapp.com/attachments/\S+)", message.content)

        yield bool(cdn_links or message.attachments)

        for att_url in cdn_links:
            self.logger.info("Attempting to acquire linked file manually")
            url_path = urlparse(att_url).path
            _, name = split(url_path)

            if self._ext_filter(self._file_extension(name)):
                try:

                    async with self.bot.web_session.head(att_url) as response:
                        response.raise_for_status()
                        if int(response.headers.get("Content-Length", 0)) > DOWNLOAD_SIZE_LIMIT:
                            yield name, ResourceWarning(f"File unreasonably large!")

                    async with self.bot.web_session.get(att_url) as response:
                        response.raise_for_status()
                        yield name, io.BytesIO(await response.read())

                except ClientResponseError as e:
                    yield name, e

        for att in message.attachments:
            self.logger.info("Attempting to acquire file via Discord")
            name = att.filename
            if self._ext_filter(self._file_extension(name)):
                try:
                    file = await att.to_file()
                    yield name, file.fp
                except HTTPException | Forbidden | NotFound as e:
                    yield name, e

    async def process_message(self, message: Message) -> bool:
        """
        Responsibilities:
        - Get all attachments for a message by link or `message.attachments`
        - Determine whether we care to process any of them
        - Gather all the jobs (coroutines) to execute on the files
        - Execute all jobs, ignoring those that fail
        - Present any messages that arise from the jobs
        - Return whether there were any messages
        """
        self.logger.info("Processing message")
        file_getter = self._obtain_attachments(message)
        # get the first yield, which is just whether there's anything to do
        if there_were_files := await file_getter.asend(None):
            self.logger.info("Indicating interest in message")
            await message.add_reaction(EMOJI_CRASHES_ANALYZING)

        responses: list[CrashResponse] = []
        files: list[IO] = []
        try:
            self.logger.info("Creating message processing tasks")
            async with TaskGroup() as task_group:
                jobs: list[Task] = [task_group.create_task(self.process_text(message.content))]

                async for name, file_or_exc in file_getter:
                    if isinstance(file_or_exc, Exception):
                        self.logger.error(f"Unable to obtain file '{name}'")
                        self.logger.exception(file_or_exc)
                        responses.append(
                            CrashResponse(
                                name="Download failed", value=f"Could not obtain file '{name}' due to `{file_or_exc}`"
                            )
                        )
                        continue

                    file: IO = file_or_exc
                    files.append(file)
                    jobs.extend((task_group.create_task(job) for job in self._get_file_jobs(name, file)))
        except ExceptionGroup as eg:
            for ex in eg.exceptions:
                if isinstance(ex, TimeoutError):
                    self.logger.exception(ex)
                    await message.remove_reaction(EMOJI_CRASHES_ANALYZING, self.bot.user)
                    await message.add_reaction(EMOJI_CRASHES_TIMEOUT)
                    for j in jobs:
                        j.cancel()
                else:
                    raise ex

        self.logger.info("Collecting job results")
        for job in jobs:
            responses.extend(job.result())

        if files:
            self.logger.info("Closing files")
            for file in files:
                file.close()

        if there_were_files:
            self.logger.info("Removing reaction")
            await message.remove_reaction(EMOJI_CRASHES_ANALYZING, self.bot.user)

        if filtered_responses := list(set(responses)):  # remove dupes

            if len(filtered_responses) == 1:
                self.logger.info("Found only one response to message, sending.")
                await self.bot.reply_to_msg(
                    message,
                    f"{filtered_responses[0].value}\n-# Responding to `{filtered_responses[0].name}` triggered by {message.author.mention}",
                    propagate_reply=False,
                )

            else:

                self.logger.info("Found responses to message, sending.")
                embed = createembed.crashes(filtered_responses)
                embed.set_author(
                    name=f"Automated responses for {message.author.global_name or message.author.display_name} ({message.author.id})",
                    icon_url=message.author.avatar.url,
                )
                await self.bot.reply_to_msg(message, embed=embed, propagate_reply=False)
            return True

        else:
            self.logger.info("No responses to message, skipping.")
            return False


def filter_epic_commandline(cli: str) -> str:
    return " ".join(filter(lambda opt: "auth" not in opt.lower(), cli.split()))


@dataclass
class InstallInfo:

    type InstalledMods = dict[str, str]  # key: mod reference, value: mod version

    filename: str
    game_version: str = ""
    game_type: str = ""
    smm_version: str = ""
    sml_version: str = ""
    game_path: str = ""
    game_launcher_id: str = ""
    game_command_line: str = ""
    installed_mods: InstalledMods = {}
    mismatches: list[str] = []

    @classmethod
    def from_metadata_json(cls: Type[InstallInfo], file: IO[bytes], filename: str) -> Optional[InstallInfo]:
        metadata: dict = json.load(file)
        match metadata:
            case {
                # SMM 3 format
                "installations": _installations,
                "selectedInstallation": selected_installation,
                "profiles": _profiles,
                "selectedProfile": _selected_profile,
                "installedMods": installed_mods,
                "smlVersion": sml_version,
                "smmVersion": smm_version,
                "modsEnabled": _mods_enabled,
            }:
                # if there is no install everything can default to None
                selected_installation = selected_installation or {}
                return cls(
                    filename,
                    smm_version=smm_version,
                    sml_version=sml_version or "",
                    game_version=selected_installation.get("version", ""),
                    game_type=selected_installation.get("type", ""),
                    game_path=selected_installation.get("path", ""),
                    game_launcher_id=selected_installation.get("launcher", ""),
                    game_command_line=selected_installation.get("launchPath", ""),
                    installed_mods=installed_mods,
                )
            case {
                # SMM 2 format
                "installsFound": _installations,
                "selectedInstall": selected_installation,
                "profiles": _profiles,
                "selectedProfile": _selected_profile,
                "installedMods": installed_mods,
                "smlVersion": sml_version,
                "smmVersion": smm_version,
                "modsEnabled": _mods_enabled,
            }:
                # if there is no install everything can default to None
                selected_installation = selected_installation or {}
                return cls(
                    filename,
                    smm_version=smm_version,
                    sml_version=sml_version or "",
                    game_version=selected_installation.get("version", ""),
                    game_type="WindowsClient",  # SMM 2 only supports this one and therefore doesn't specify otherwise
                    game_path=selected_installation.get("installLocation", ""),
                    game_command_line=selected_installation.get("launchPath", ""),
                    installed_mods=installed_mods,
                )

            case {
                # SMM 2 format - keys missing when generated when no installs found
                "installsFound": _installations,
                "selectedInstall": selected_installation,
                "profiles": _profiles,
                "selectedProfile": _selected_profile,
                "smmVersion": smm_version,
                "modsEnabled": _mods_enabled,
            }:
                # if there is no install everything can default to None
                selected_installation = selected_installation or {}
                return cls(
                    filename,
                    smm_version=smm_version,
                    sml_version="",
                    game_version=selected_installation.get("version", ""),
                    game_type="WindowsClient",  # SMM 2 only supports this one and therefore doesn't specify otherwise
                    game_path=selected_installation.get("installLocation", ""),
                    game_command_line=selected_installation.get("launchPath", ""),
                    installed_mods={},
                )

            case _:
                logger.exception(ValueError("Invalid SMM metadata json"))
                return None

    def update_from_fg_log(self, log_file: IO[bytes]):

        info = self._get_fg_log_details(log_file)

        if sml_version := info.get("sml"):
            if self.sml_version and self.sml_version != sml_version:
                self.mismatches.append(f"SML Version ({sml_version})")
            else:
                self.sml_version = sml_version

        if game_version := info.get("game_version"):
            if self.game_version and int(float(self.game_version)) != int(float(game_version)):
                self.mismatches.append(f"Game Version ({game_version})")
            else:
                self.game_version = game_version

        if path := info.get("path"):
            if self.game_path:
                p1 = path.replace("\\", "/")
                p2 = self.game_path.replace("\\", "/")
                if "Windows" in self.game_type:  # windows is case-insensitive
                    p1 = p1.lower()
                    p2 = p2.lower()
                if Path(p1) != Path(p2):
                    self.mismatches.append(f"Game Path: ({path})")
            else:
                self.game_path = path

        if launcher := info.get("launcher"):
            if self.game_launcher_id and self.game_launcher_id.lower() != launcher.lower():
                self.mismatches.append(f"Launcher ID: {launcher}")
            else:
                self.game_launcher_id = launcher

        if cli := info.get("cli"):
            if self.game_command_line:
                self.game_command_line += cli

    @staticmethod
    def _get_fg_log_details(log_file: IO[bytes]):
        # This function uses lazy evaluation to get the info we need without performing regex on the whole log
        # It used to matter more when we were using slower regex libraries. - Borketh

        lines: list[bytes] = log_file.readlines()
        vanilla_info_search_area = filter(lambda l: re2.match("^LogInit", l), map(bytes.decode, lines))

        info = {}
        patterns = [
            re2.compile(r"Net CL: (?P<game_version>\d+)"),
            re2.compile(r"Command Line:(?P<cli>.*)"),
            re2.compile(r"Base Directory:(?P<path>.+)"),
            re2.compile(r"Launcher ID: (?P<launcher>\w+)"),
        ]

        # This loop sequentially finds information,
        # dropping patterns to look for as they are found (until it runs out of patterns).
        # The patterns have named regex captures which the rest of the code knows the names of.
        # - Borketh

        for line in vanilla_info_search_area:
            if not patterns:
                break
            elif match := re2.search(patterns[0], line):
                info |= match.groupdict()
                patterns.pop(0)
        else:
            logger.info("Didn't find all four pieces of information normally found in a log!")
            logger.debug(json.dumps(info, indent=2))

        mod_loader_logs = filter(lambda l: re2.match("LogSatisfactoryModLoader", l), map(bytes.decode, lines))
        for line in mod_loader_logs:
            if match := re2.search(r"(?<=v\.)(?P<sml>[\d.]+)", line):
                info |= match.groupdict()
                break

        if cl := info.get("game_version"):
            info["game_version"] = int(cl)

        if cli := info.get("cli"):
            info["cli"] = filter_epic_commandline(cli)

        return info

    def _version_info(self) -> str:
        # note: `(str that defaults to "") and (f-string)` is shorthand for if str: f-string
        version_info = (
            "```\n"
            + (self.smm_version and f"SMM Version: {self.smm_version}\n")
            + (self.sml_version and f"SML Version: {self.sml_version}\n")
        )

        if self.installed_mods:
            version_info += f"Installed Mods: {len(self.installed_mods)}\n"

        if self.game_version:

            version_info += (
                "Game: "
                + self.game_type
                + f" CL {self.game_version}"
                + (self.game_launcher_id and f" from {self.game_launcher_id}")
                + (self.game_path and f"\nPath: `{self.game_path.strip()}`")
                + "\n"
            )

        if cli := self.game_command_line.strip():
            version_info += f"Command Line: {cli}\n"

        return version_info + "\n```"

    def format(self) -> CrashResponse:
        return CrashResponse(
            name=f"Key Details for {self.filename}",
            value=self._version_info(),
        )
