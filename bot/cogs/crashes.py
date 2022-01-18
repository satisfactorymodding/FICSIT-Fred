from fred_core_imports import *
from libraries import common, createembed

import nextcord.ext.commands as commands
from PIL import Image, ImageEnhance, UnidentifiedImageError
from pytesseract import image_to_string, TesseractError
import zipfile
from concurrent.futures import ThreadPoolExecutor
from time import strptime
from typing import AsyncIterator


REGEX_LIMIT: float = 2


async def regex_with_timeout(*args, **kwargs):
    try:
        return await asyncio.wait_for(asyncio.to_thread(re.search, *args, **kwargs), REGEX_LIMIT)
    except asyncio.TimeoutError:
        raise TimeoutError(f"A regex timed out after {REGEX_LIMIT} seconds! \n"
                           f"pattern: ({args[0]}) \n"
                           f"flags: {kwargs['flags']} \n"
                           f"on text of length {len(args[1])}")


class Crashes(commands.Cog):
    vanilla_info_patterns = [
        re.compile(r"Net CL: (?P<game_version>\d+)"),
        re.compile(r"Command Line: (?P<cli>.*)"),
        re.compile(r"Base Directory: (?P<path>.+)"),
        re.compile(r"Launcher ID: (?P<launcher>\w+)")
    ]

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.Logger("CRASH_PARSING")

    @staticmethod
    def filter_epic_commandline(cli: str) -> str:
        return ' '.join(filter(lambda opt: "auth" not in opt.lower(), cli.split()))

    async def parse_factory_game_log(self, text: str) -> dict[str, str | int]:
        self.logger.info("Extracting game info")
        lines = text.splitlines()
        vanilla_info_search_area = filter(lambda l: re.match("^LogInit", l), lines)

        info = dict()
        patterns = self.vanilla_info_patterns[:]
        for line in vanilla_info_search_area:
            if not patterns:
                break
            elif match := await regex_with_timeout(patterns[0], line):
                info |= match.groupdict()
                patterns.pop(0)
        else:
            self.logger.info("Didn't find all four pieces of information normally found in a log")

        mod_loader_logs = filter(lambda l: re.match("LogSatisfactoryModLoader", l), lines)
        for line in mod_loader_logs:
            if match := await regex_with_timeout(r"(?<=v\.)(?P<sml>[\d.]+)", line):
                info |= match.groupdict()
                break

        if cl := info.get("game_version"):
            info["game_version"] = int(cl)

        if cli := info.get("cli"):
            info["cli"] = self.filter_epic_commandline(cli)

        return info

    @staticmethod
    def make_version_info_message(smm: str = '', game_version: int = 0,
                                  sml: str = '', path: str = '',
                                  cli: str = '', launcher: str = '', **_) -> str:
        version_info = ""

        if smm:
            version_info += f"SMM: {smm}\n"
        if game_version:
            version_info += f"CL: {game_version}\n"
        if sml:
            version_info += f"SML: {sml}\n"
        if path:
            version_info += f"Path: {path}\n"
        if launcher:
            version_info += f"Launcher ID: {launcher}\n"
        if cli.strip():
            version_info += f"Command Line: {cli}\n"

        return version_info

    async def make_sml_version_message(self, game_version: int = 0, sml: str = '', **_) -> str:
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
            if (new_version := latest_compatible_sml['version']) != sml:
                msg: str = "You are not using the most recent SML release for your game. " \
                           f"Please update to {new_version}."
                if latest_compatible_sml != sml_versions[0]:
                    msg += "\nAlso, your game itself may need an update!"
                return msg
            else:
                return ""

    @staticmethod
    def make_outdated_mods_message(mods: list) -> str:
        if len(mods) == 1:
            header = f"You are attempting to use a mod that no longer works! \n```"
            mod_list = "\n".join(mods)
            footer = "```Please attempt to remove/disable that mod, " \
                     "so that it no longer forces the old SML to be used (this is why your mods don't load)"
        else:
            header = f"You are attempting to use {len(mods)} mods that no longer work! \n```"
            mod_list = "\n".join(mods)
            footer = "```Please attempt to remove/disable these mods, " \
                     "so that they no longer force the old SML to be used (this is why your mods don't load)"
        return header + mod_list + footer

    @staticmethod
    def filter_enabled(mod_list: list) -> list:
        return [mod["id"] for mod in mod_list if mod["enabled"]]

    async def check_for_outdated_mods(self, mod_list: list) -> list[str]:

        enabled_mods: list = self.filter_enabled(mod_list)
        if not enabled_mods:
            return []

        # This block separates the mods into blocks of 100 because that's
        results = dict()
        for chunk in [enabled_mods[i:i + 100] for i in range(0, len(enabled_mods), 100)]:
            query_mods, length = str(chunk).replace("'", '"'), str(len(chunk))

            # Replace argument smlVersionID with the ID of the release of a breaking SML (such as 3.0.0) when another comes
            query = """
            {
                getMods(
                    filter: {
                        references: """ + query_mods + """
                        limit: """ + length + """
                    }
                ) {
                    mods {
                        name
                        last_version_date
                    }
                }
                getSMLVersion(smlVersionID: "9DgqKh9KVL2cuu") {
                    date
                }
            }"""
            result = await self.bot.repository_query(query)
            results.update(result)

        mods_with_dates: list[dict[str, str]] = results["data"]["getMods"]["mods"]
        latest_compatible_loader = strptime(results["data"]["getSMLVersion"]["date"], "%Y-%m-%dT%H:%M:%SZ")

        # Checking mods against SML date
        incompatible_mods: list[str] = [
            mod['name']
            for mod in mods_with_dates
            if latest_compatible_loader > strptime(mod["last_version_date"], "%Y-%m-%dT%H:%M:%S.%fZ")
        ]

        return incompatible_mods

    async def process_file(self, file, extension) -> list[dict]():
        self.logger.info(f"Processing {extension} file")
        match extension:
            case "":
                return []
            case "zip":
                messages: list[dict] = []

                info = dict(
                    smm="",
                    sml="",
                    game_version=0,
                    path="",
                    launcher="",
                    cli="",
                    outdated_mods=[]
                )

                with zipfile.ZipFile(file) as zip_f:
                    zf_contents: list[str] = zip_f.namelist()
                    self.logger.info("Zip contents: " + ' '.join(zf_contents))
                    for zip_file_name in zf_contents:
                        with zip_f.open(zip_file_name) as zip_file:
                            try:
                                zip_file_content: str = zip_file.read().decode("utf-8")
                            except zipfile.BadZipFile as e:
                                self.logger.error(str(e))
                                return messages + [dict(
                                    name="Bad Zip File!",
                                    value="This zipfile is invalid! Its contents may have been changed after zipping.",
                                    inline=False)]

                            self.logger.info(f"Entering mass-regex of {zip_file_name}")
                            results = await self.process_text(zip_file_content)
                            self.logger.info(f"Finished mass-regex of {zip_file_name} - {len(results)} results")
                            messages += results

                    if 'metadata.json' in zf_contents:
                        self.logger.info("found SMM metadata file")
                        with zip_f.open("metadata.json") as metadataFile:
                            metadata: dict = json.load(metadataFile)
                            if metadata["selectedInstall"]:
                                info['game_version'] = int(float(metadata["selectedInstall"]["version"]))
                                info['path'] = metadata["selectedInstall"]["installLocation"]
                            if metadata["selectedProfile"]:
                                if metadata["selectedProfile"]["name"] != "development":
                                    info['outdated_mods'] = \
                                        await self.check_for_outdated_mods(metadata["selectedProfile"]["items"])

                            if sml := metadata.get("smlVersion"):
                                info['sml'] = sml

                            info['smm'] = metadata["smmVersion"]

                    if 'FactoryGame.log' in zf_contents:
                        self.logger.info("found FactoryGame.log file")
                        # Try to find CL and SML versions in FactoryGame.log
                        with zip_f.open("FactoryGame.log") as fg_log:
                            fg_log_content = fg_log.read().decode("utf-8")
                            fg_log_info = await self.parse_factory_game_log(fg_log_content)
                            # merge log info into current info
                            # with log as priority because it is more likely to be correct
                            info = {k: x if (x := fg_log_info.get(k)) else info.get(k) for k in fg_log_info | info}

                if sml_outdated := await self.make_sml_version_message(**info):
                    messages += [dict(name="Outdated SML!", value=sml_outdated, inline=True)]

                if info['outdated_mods']:
                    messages += [dict(name="Outdated Mods!",
                                      value=self.make_outdated_mods_message(info['outdated_mods']),
                                      inline=True)]

                if version_info := self.make_version_info_message(**info):
                    messages += [dict(name="Quick debug summary", value=version_info, inline=False)]

                return messages

            case "log" | "txt":
                text = file.read().decode("utf-8", errors="ignore")
                self.logger.info("Entering mass-regex for standalone text file")
                messages = await self.process_text(text)
                self.logger.info(f"Completed mass-regex for standalone text file - {len(messages)} results")

                self.logger.info("Attempting to find game info for standalone text file")
                log_file_info = await self.parse_factory_game_log(text)

                if sml_outdated := await self.make_sml_version_message(**log_file_info):
                    messages += [dict(name="Outdated SML!", value=sml_outdated, inline=True)]

                if version_info := self.make_version_info_message(**log_file_info):
                    messages += [dict(name="Quick log summary", value=version_info, inline=False)]

                return messages

            case _:
                try:
                    image = Image.open(file)
                    ratio = 2160 / image.height
                    if ratio > 1:
                        image = image.resize((round(image.width * ratio), round(image.height * ratio)), Image.LANCZOS)

                    enhancer_contrast = ImageEnhance.Contrast(image)

                    image = enhancer_contrast.enhance(2)
                    enhancer_sharpness = ImageEnhance.Sharpness(image)
                    image = enhancer_sharpness.enhance(10)
                    with ThreadPoolExecutor() as pool:
                        image_text = await self.bot.loop.run_in_executor(pool, image_to_string, image)
                        self.logger.info("OCR returned the following data:\n" + image_text)
                        return await self.process_text(image_text)

                except TesseractError:
                    self.logger.error(f"OCR error:\n{traceback.format_exc()}")
                    return []
                except UnidentifiedImageError:
                    self.logger.warning("Tried OCR-ing file but it was not an image")
                    return []

    async def mass_regex(self, text: str) -> AsyncIterator[dict]:
        for crash in config.Crashes.fetch_all():
            if match := await regex_with_timeout(crash["crash"], text, flags=re.IGNORECASE):
                if str(crash["response"]).startswith(self.bot.command_prefix):
                    if command := config.Commands.fetch(crash["response"].strip(self.bot.command_prefix)):
                        command_response = command['content']
                        if command_response.startswith(self.bot.command_prefix):  # is alias
                            command_response = config.Commands.fetch(command_response.strip(self.bot.command_prefix))
                        yield dict(name=command["name"], value=command_response, inline=True)
                else:
                    response = re.sub(r"{(\d+)}", lambda m: match.group(int(m.group(1))), str(crash["response"]))
                    yield dict(name=crash["name"], value=response, inline=True)

    async def process_text(self, text: str) -> list[dict]:
        messages = [msg async for msg in self.mass_regex(text)]
        return messages

    async def process_message(self, message) -> bool:
        responses: list[dict] = []
        # attachments
        cdn_link = re.search(r"(https://cdn.discordapp.com/attachments/\S+)", message.content)
        if cdn_link or message.attachments:
            self.logger.info("Found file in message")

            try:
                file = await message.attachments[0].to_file()
                file = file.fp
                name = message.attachments[0].filename
                self.logger.info("Acquired file from discord API")
            except IndexError:
                self.logger.info("Couldn't acquire file from discord API")
                try:
                    self.logger.info("Attempting to acquire linked file manually")
                    url = cdn_link.group(1)
                    name = url.split("/")[-1]
                    async with self.bot.web_session.get(url) as response:
                        assert response.status == 200, f"the web request failed with status {response.status}"
                        file = io.BytesIO(await response.read())
                except (AttributeError, AssertionError) as e:
                    if isinstance(e, AttributeError):
                        e = "there was no CDN url"
                    self.logger.warning(f"Couldn't acquire file manually because {e}.")
                    return False  # did not have any responses

            extension = name.rpartition(".")[-1]

            if name.startswith("SMMDebug") or extension == 'log':
                async with message.channel.typing():
                    responses += await self.process_file(file, extension)
            else:
                responses += await self.process_file(file, extension)

            file.close()

        # Pastebin links
        elif match := re.search(r"(https://pastebin.com/\S+)", message.content):
            url = re.sub(r"(?<=bin.com)/", "/raw/", match.group(1))
            async with self.bot.web_session.get(url) as response:
                text: str = await response.text()

            responses += await self.process_text(text)

            maybe_log_info = await self.parse_factory_game_log(message.content)

            sml_outdated = await self.make_sml_version_message(**maybe_log_info)
            if sml_outdated:
                responses += [dict(name="Outdated SML!", value=sml_outdated, inline=True)]

            version_info = self.make_version_info_message(**maybe_log_info)
            if version_info:
                responses += [dict(name="Quick log summary", value=version_info, inline=True)]

        else:
            responses += await self.process_text(message.content)

        if len(responses) > 2:
            await self.bot.reply_to_msg(message, embed=createembed.crashes(responses))
        else:
            for response in responses:
                await self.bot.reply_to_msg(message, response["value"], propagate_reply=False)
        return len(responses) > 0
