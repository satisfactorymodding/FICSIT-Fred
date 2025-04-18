from __future__ import annotations

import json
from asyncio import Task, TaskGroup
from asyncio import wait_for, to_thread, TimeoutError
from contextlib import suppress
from io import StringIO
from itertools import batched
from os import path
from os.path import split, splitext
from pathlib import Path
from typing import AsyncIterator, IO, Type, Coroutine, Generator, Optional, Any, Final, TypedDict
from zipfile import ZipFile

import re2
from attr import dataclass
from nextcord import Message, File
from semver import Version

from fred import config
from fred.libraries import createembed, ocr
from fred.libraries.common import FredCog, new_logger
from fred.libraries.content_manager import ContentManager

re2.set_fallback_notification(re2.FALLBACK_WARNING)

REGEX_LIMIT: float = 6.9
DOWNLOAD_SIZE_LIMIT = 104857600  # 100 MiB
EMOJI_CRASHES_ANALYZING = "<:FredAnalyzingFile:1283182945019891712>"
EMOJI_CRASHES_TIMEOUT = "<:FredAnalyzingTimedOut:1283183010967195730>"

logger = new_logger(__name__)


async def regex_with_timeout(*args, **kwargs):
    try:
        return await wait_for(to_thread(re2.search, *args, **kwargs), REGEX_LIMIT)
    except TimeoutError:
        raise TimeoutError(
            f"A regex timed out after {REGEX_LIMIT} seconds! \n"
            f"pattern: ({args[0]}) \n"
            f"flags: {kwargs['flags']} \n"
            f"on text of length {len(args[1])}"
        )
    except re2.RegexError as e:
        raise ValueError(args[0]) from e


class Crashes(FredCog):

    type CrashJob = Coroutine[Any, Any, list[createembed.CrashResponse]]
    type CrashJobGenerator = Generator[Crashes.CrashJob, None, None]

    async def make_sml_version_message(
        self, game_version: int = 0, sml: str = "", **_
    ) -> Optional[createembed.CrashResponse]:
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
                return createembed.CrashResponse("Outdated SML!", msg, inline=True)
            else:
                return None

    # fmt: off
    _QUERY_TEMPLATE: Final[str] = """
    {
      getMods(filter: {references: %s, limit: 100}) {
        mods {
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
    ) -> list[createembed.CrashResponse]:
        responses: list[createembed.CrashResponse] = []
        if not input_mods:
            return responses

        queried_mods: list[Crashes._ModLookupGQLResponse] = []

        # This separates the mods into blocks of 100 because of API restrictions
        for chunk in batched(input_mods, 100):
            # formats the list appropriately for GQL
            game_branch = "EXP" if experimental else "EA"
            query = self._QUERY_TEMPLATE % (json.dumps(chunk), game_branch)

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
            if mod_compat is None:
                continue  # we have no way of knowing
            compat_info = mod_compat.get("EA") or mod_compat.get("EXP")
            mod_latest_version = Version.parse(mod["versions"][0]["version"])
            using_mod_version = Version.parse(input_mods[mod["mod_reference"]])

            if compat_info["state"] == "Broken":
                broken_mods.append((mod_name, compat_info["note"]))

            if mod_latest_version > using_mod_version and not mod_latest_version.prerelease:
                outdated_mods.append((mod_name, str(mod_latest_version)))

        if broken_mods:
            string = "\n".join(f"{mod[0]}: {mod[1]}" for mod in broken_mods)
            if len(string) > 900:  # fields have a 1024 char value length limit
                string = "TOO MANY BROKEN MODS TO LIST!!"
            string += (
                "\nPlease attempt to remove/disable these mods so that they no longer force the old SML to be used "
                "(this is why your mods don't load)."
            )

            responses.append(createembed.CrashResponse("Incompatible mods found!", string))

        if outdated_mods:
            string = "\n".join(f"{mod[0]} can be updated to `{mod[1]}`" for mod in outdated_mods)
            if len(string) > 900:  # fields have a 1024 char value length limit
                string = "TOO MANY OUTDATED MODS TO LIST!!"
            string += "\nUpdate these mods, there may be fixes for your issue in doing so."
            responses.append(createembed.CrashResponse("Outdated mods found!", string))
        return responses

    async def mass_regex(self, text: str) -> AsyncIterator[createembed.CrashResponse]:

        all_crashes = config.Crashes.fetch_all()

        for crash in all_crashes:
            if match := await regex_with_timeout(crash["crash"], text, flags=re2.IGNORECASE | re2.S):
                if str(crash["response"]).startswith(self.bot.command_prefix):
                    if command := config.Commands.fetch(crash["response"].strip(self.bot.command_prefix)):
                        command_response = command["content"]
                        if command_response.startswith(self.bot.command_prefix):  # is alias
                            command = config.Commands.fetch(command_response.strip(self.bot.command_prefix))
                        yield createembed.CrashResponse(
                            name=crash["name"],
                            value=command["content"],
                            attachment=command["attachment"],
                            inline=True,
                        )
                else:

                    def replace_response_value_with_captured(m: re2.Match) -> str:
                        group = int(m.group(1))
                        if group > len(match.groups()):
                            return f"{{Group {group} not captured in crash regex!}}"
                        return match.group(group)

                    response = re2.sub(r"{(\d+)}", replace_response_value_with_captured, str(crash["response"]))
                    yield createembed.CrashResponse(name=crash["name"], value=response, inline=True)

    async def detect_and_fetch_pastebin_content(self, text: str) -> str:
        if match := re2.search(r"(https://pastebin.com/\S+)", text):
            self.logger.info("Found a pastebin link! Fetching text.")
            url = re2.sub(r"(?<=bin.com)/", "/raw/", match.group(1))
            async with self.bot.web_session.get(url) as response:
                return await response.text()
        else:
            return ""

    async def process_text(self, text: str, filename="") -> list[createembed.CrashResponse]:
        if not text:
            return []

        self.logger.info("Processing text.")
        import time

        start = time.time()
        responses = [msg async for msg in self.mass_regex(text)]
        done = time.time()
        self.logger.info(f"Fetch took {done - start} seconds")

        responses.extend(await self.process_text(await self.detect_and_fetch_pastebin_content(text)))

        if match := re2.search(r"([^\n]*Critical error:.*Engine exit[^\n]*\))", text, flags=re2.I | re2.M | re2.S):
            filename = path.basename(filename)
            crash = match.group(1)
            responses.append(
                createembed.CrashResponse(
                    name=f"Crash found in {filename}",
                    value="It has been attached to this message.",
                    attachment=File(StringIO(crash), filename="Abridged " + filename, force_close=True),
                )
            )

        return responses

    async def process_text_file(self, file: ContentManager.ManagedFile) -> list[createembed.CrashResponse]:
        self.logger.info("Processing text file.")
        with file.sync.lock:
            res = await self.process_text(file.read().decode(), file.filename)
        file.sync.mark_done()
        return res

    async def process_image(self, file: ContentManager.ManagedFile) -> list[createembed.CrashResponse]:
        self.logger.info("Processing image.")
        with file.sync.lock:
            res = await self.process_text(await self.bot.loop.run_in_executor(self.bot.executor, ocr.read, file))
        file.sync.mark_done()
        return res

    async def process_zip(self, managed_zip_content: ContentManager, filename: str) -> list[createembed.CrashResponse]:
        self.logger.info(f"Processing zip {filename}")

        res = []

        with managed_zip_content.sync.lock, suppress(IndexError):
            info: Optional[InstallInfo] = None

            searchable_files = managed_zip_content.searchable()

            files = searchable_files.get(f"{filename}/metadata.json", [])
            metadata = files.pop(0)  # shortcuts to return [] if there is no metadata file
            if files:
                self.logger.warn("Multiple metadata.json found! Using 1st.")

            with metadata.sync.lock:
                metadata.seek(0)
                info = InstallInfo.from_metadata_json(metadata, filename)

            with suppress(IndexError):
                files = searchable_files.get(f"{filename}/FactoryGame.log", [])
                fg_log = files.pop(0)  # shortcuts to return without using fg.log if there isn't one
                if files:
                    self.logger.warn("Multiple FactoryGame.log found! Using 1st.")

                with fg_log.sync.lock:
                    fg_log.seek(0)
                    info.update_from_fg_log(fg_log)

            if info is not None:
                res.append(info.format())
                res.extend(await self.check_mods(info.installed_mods))

        managed_zip_content.sync.mark_done()
        return res

    def _get_file_jobs(self, cm: ContentManager) -> CrashJobGenerator:
        cm.sync.mark_using()

        for file in cm.get_files():
            self.logger.debug(f"Getting jobs for file {file.filename}")
            match self._file_extension(file.filename):
                case "zip":
                    self.logger.info(f"Adding jobs from zip file {file.filename}")
                    file.sync.mark_using()
                    with file.sync.lock:
                        zip_file = ZipFile(file)
                        zcm = ContentManager.from_zipfile(zip_file, file.filename)
                    file.sync.mark_done()
                    cm.add_child(zcm)
                    zcm.sync.mark_using()
                    self.logger.info(f"Adding job from zip file {file.filename}")
                    yield self.process_zip(zcm, file.filename)
                    self.logger.info(f"Recursing job creation over zip file {file.filename}")
                    yield from self._get_file_jobs(zcm)

                case "log" | "txt" | "json":
                    self.logger.info(f"Adding job for log/text file {file.filename}")
                    yield self.process_text_file(file)
                    file.sync.mark_using()
                case "png":
                    self.logger.info(f"Adding job for png file {file.filename}")
                    file.sync.mark_using()
                    yield self.process_image(file)
                case _:
                    self.logger.info(f"Not adding any job for {file.filename}")

        # this guarantees the mark done runs
        cm.sync.mark_done()

        async def nothing():
            return []

        yield nothing()

    @staticmethod
    def _file_extension(filename: str) -> str:
        return splitext(split(filename)[1])[1][1:].lower()

    @staticmethod
    def _ext_filter(ext: str) -> bool:
        return ext in ("png", "log", "txt", "zip", "json")

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
        async with await ContentManager.from_message(message, self.bot.web_session) as content_manager:

            if there_were_files := content_manager.has_files():
                self.logger.info("Indicating interest in message")
                await message.add_reaction(EMOJI_CRASHES_ANALYZING)

            responses: list[createembed.CrashResponse] = []
            jobs: list[Task] = []
            try:
                self.logger.info("Creating message processing tasks")
                async with TaskGroup() as task_group:
                    jobs.append(task_group.create_task(self.process_text(message.content)))
                    jobs.extend((task_group.create_task(job) for job in self._get_file_jobs(content_manager)))

            except ExceptionGroup as eg:
                self.logger.error(f"Exceptions raised in jobs: {eg.exceptions}")
                for ex in eg.exceptions:
                    if isinstance(ex, TimeoutError):
                        self.logger.exception(ex)
                        await message.remove_reaction(EMOJI_CRASHES_ANALYZING, self.bot.user)
                        await message.add_reaction(EMOJI_CRASHES_TIMEOUT)
                        for j in jobs:
                            j.cancel()
                    else:
                        await message.remove_reaction(EMOJI_CRASHES_ANALYZING, self.bot.user)
                        raise ex

            self.logger.info("Collecting job results")
            for job in jobs:
                responses.extend(job.result())

        # all files should be closed at this point
        self.logger.debug("Do we get past the context manager?")

        if there_were_files:
            self.logger.info("Removing reaction")
            await message.remove_reaction(EMOJI_CRASHES_ANALYZING, self.bot.user)

        if filtered_responses := list(set(responses)):  # remove dupes

            resp_files = [
                await self.bot.obtain_attachment(att) if isinstance(att, str) else att
                for resp in filtered_responses
                if (att := resp.attachment) is not None
            ]

            if len(filtered_responses) == 1:
                self.logger.info("Found only one response to message, sending.")
                await self.bot.reply_to_msg(
                    message,
                    f"{filtered_responses[0].value}\n-# Responding to `{filtered_responses[0].name}` triggered by {message.author.mention}",
                    propagate_reply=False,
                    files=resp_files,
                )

            else:

                self.logger.info("Found responses to message, sending.")
                embed = createembed.crashes(filtered_responses)
                embed.set_author(
                    name=f"Automated responses for {message.author.global_name or message.author.display_name} ({message.author.id})",
                    icon_url=message.author.avatar and message.author.avatar.url,
                    # defaults to None if no avatar, like mircea
                )
                await self.bot.reply_to_msg(message, embed=embed, propagate_reply=False, files=resp_files)
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

        if game_path := info.get("path"):
            if self.game_path:
                p1 = game_path.replace("\\", "/")
                p2 = self.game_path.replace("\\", "/")
                if "Windows" in self.game_type:  # windows is case-insensitive
                    p1 = p1.lower()
                    p2 = p2.lower()
                if Path(p1) != Path(p2):
                    self.mismatches.append(f"Game Path: ({game_path})")
            else:
                self.game_path = game_path

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
        vanilla_info_search_area = filter(lambda l: re2.match("^LogInit", l), map(lambda b: b.decode(), lines))

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

        mod_loader_logs = filter(lambda l: re2.match("LogSatisfactoryModLoader", l), map(lambda b: b.decode(), lines))

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

    def format(self) -> createembed.CrashResponse:
        return createembed.CrashResponse(
            name=f"Key Details for {self.filename}",
            value=self._version_info(),
        )
