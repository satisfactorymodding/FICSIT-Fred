from fred_core_imports import *
from libraries import common, createembed

import errno
from functools import wraps
import nextcord.ext.commands as commands
from PIL import Image, ImageEnhance
from pytesseract import image_to_string, TesseractError
import zipfile
from urllib.request import urlopen
from concurrent.futures import ThreadPoolExecutor
from time import strptime



def timeout(seconds=2, error_message=os.strerror(errno.ETIME)):
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutError(error_message)

        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.setitimer(signal.ITIMER_REAL, seconds)  # used timer instead of alarm
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result

        return wraps(func)(wrapper)

    return decorator


@timeout(5)
def timedregexsearch(*args, **kwargs):
    try:
        return re.search(*args, **kwargs)
    except TimeoutError:
        raise TimeoutError(f"The following regexp timed out: '{args[0]}'")


class Crashes(commands.Cog):
    game_info_pattern = re.compile(r'''
        ^LogInit:\s(?=[NCBL])
        (?:
            Net\sCL:\s(?P<game_version>\d+)
        |   Command\sLine:\s(?P<cli>.*)
        |   Base\sDirectory:\s(?P<path>.+)
        |   Launcher\sID:\s(?P<launcher>\w+)
        )''', flags=re.X | re.M)
    sml_version_pattern = re.compile(r"ModLoader[\w\s.:]+(?<=v\.)(?P<sml>[\d.]+)", flags=re.M)

    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def filter_epic_commandline(cli: str) -> str:
        return ' '.join(filter(lambda opt: "auth" not in opt.lower(), cli.split()))

    def parse_factory_game_log(self, text: str) -> dict[str, str | int]:  # -> tuple[str, int, str, str, str]:
        logging.info("ContentParse: Extracting game info")

        info = {
            name: capture
            for match in re.finditer(self.game_info_pattern, text)
            for name, capture in match.groupdict().items()
            if capture
        }

        if sml_detected := re.search(self.sml_version_pattern, text):
            info.update(sml_detected.groupdict())

        return info

    @staticmethod
    def make_version_info_message(smm=None, game_version=0, sml=None, path='', launcher=None, cli='', **_) -> str:
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

    async def make_sml_version_message(self, game_version=0, sml='', **_):
        if game_version and sml:
            # Check the right SML for that CL
            query = """{
            getSMLVersions{
                sml_versions {
                version
                satisfactory_version
                bootstrap_version
                }
            }
            }"""
            result = await common.repository_query(query, self.bot)
            sml_versions = result["data"]["getSMLVersions"]["sml_versions"]
            for i in range(0, len(sml_versions) - 1):
                if sml_versions[i]["satisfactory_version"] > game_version:
                    continue
                else:
                    latest = sml_versions[i]
                    break
            if latest["version"] != sml:
                return f"Your SML version is old. You should update to {latest['version']}."
        return None

    @staticmethod
    def make_outdated_mods_message(mods):
        singular = len(mods) == 1
        if singular:
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
    def filter_enabled(mod_list):
        return [item["id"] for item in mod_list if item["enabled"]]

    async def check_for_outdated_mods(self, mod_list: list):

        enabled_mods: list = self.filter_enabled(mod_list)
        if not enabled_mods:
            return enabled_mods

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
            result = await common.repository_query(query, self.bot)
            results.update(result)

        mods_with_dates = results["data"]["getMods"]["mods"]
        latest_compatible_loader = strptime(results["data"]["getSMLVersion"]["date"], "%Y-%m-%dT%H:%M:%SZ")
        names_with_dates = {mod["name"]: mod["last_version_date"] for mod in mods_with_dates}

        incompatible_mods = []
        # Checking mods against SML date
        for mod in names_with_dates:
            if latest_compatible_loader > strptime(names_with_dates[mod], "%Y-%m-%dT%H:%M:%S.%fZ"):
                incompatible_mods += [mod]

        return incompatible_mods

    async def process_file(self, file, extension) -> list[tuple[str, str]]():
        logging.info(f"ContentParse: processing {extension} file")
        match extension:
            case "":
                return []
            case "zip":
                messages = []

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
                    logging.info("ContentParse: Zip contents: " + ' '.join(zf_contents))
                    for zip_file_name in zf_contents:
                        with zip_f.open(zip_file_name) as zip_file:
                            try:
                                zip_file_content: str = zip_file.read().decode("utf-8")
                            except zipfile.BadZipFile as e:
                                logging.error(str(e))
                                return messages + [("Bad Zip File!",
                                                    "This zipfile is invalid! "
                                                    "Its contents may have been changed after zipping.")]

                            logging.info(f"Entering mass-regex of {zip_file_name}")
                            results = await self.process_text(zip_file_content)
                            logging.info(f"Finished mass-regex of {zip_file_name} - {len(results)} results")
                            messages += results

                    if 'metadata.json' in zf_contents:
                        logging.info("ContentParse: found SMM metadata file")
                        with zip_f.open("metadata.json") as metadataFile:
                            metadata = json.load(metadataFile)
                            if metadata["selectedInstall"]:
                                info['game_version'] = int(float(metadata["selectedInstall"]["version"]))
                                info['path'] = metadata["selectedInstall"]["installLocation"]
                            if metadata["selectedProfile"]:
                                if metadata["selectedProfile"]["name"] != "development":
                                    info['outdated_mods'] = \
                                        await self.check_for_outdated_mods(metadata["selectedProfile"]["items"])

                            if "smlVersion" in metadata:
                                info['sml'] = metadata["smlVersion"]
                            info['smm'] = metadata["smmVersion"]

                    if 'FactoryGame.log' in zf_contents:
                        logging.info("ContentParse: found FactoryGame.log file")
                        # Try to find CL and SML versions in FactoryGame.log
                        with zip_f.open("FactoryGame.log") as fg_log:
                            fg_log_content = fg_log.read().decode("utf-8")
                            fg_log_info = self.parse_factory_game_log(fg_log_content[:200000])

                            # merge log info into current info
                            # with log as priority because it is more likely to be correct
                            info = {k: x if (x := fg_log_info.get(k)) else info.get(k) for k in fg_log_info | info}

                if sml_outdated := await self.make_sml_version_message(**info):
                    messages += [("Outdated SML!", sml_outdated)]

                if info['outdated_mods']:
                    messages += [("Outdated Mods!", self.make_outdated_mods_message(info['outdated_mods']))]

                if version_info := self.make_version_info_message(**info):
                    messages += [("Quick debug summary", version_info)]

                return messages

            case "log" | "txt":
                text = file.read().decode("utf-8", errors="ignore")
                logging.info("Entering mass-regex for standalone text file")
                messages = await self.process_text(text)
                logging.info(f"Completed mass-regex for standalone text file - {len(messages)} results")

                logging.info("Attempting to find game into for standalone text file")
                log_file_info = self.parse_factory_game_log(text)

                if sml_outdated := await self.make_sml_version_message(**log_file_info):
                    messages += [("Outdated SML!", sml_outdated)]

                if version_info := self.make_version_info_message(**log_file_info):
                    messages += [("Quick log summary", version_info)]

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
                        logging.info("OCR returned the following data:\n" + image_text)
                        return await self.process_text(image_text)

                except TesseractError as e:
                    logging.error(f"OCR error:\n{e}")
                    return []

    async def process_text(self, text) -> list[tuple[str, str]]:
        messages = []
        for crash in config.Crashes.fetch_all():
            if match := timedregexsearch(crash["crash"], text, flags=re.IGNORECASE):
                if str(crash["response"]).startswith(self.bot.command_prefix):
                    if command := config.Commands.fetch(crash["response"][len(self.bot.command_prefix):]):
                        if command['content'].startswith(self.bot.command_prefix):  # is alias
                            command = config.Commands.fetch(command['content'][len(self.bot.command_prefix):])
                        messages += [(command["name"], command["content"])]
                else:
                    response = re.sub(r"{(\d+)}", lambda m: match.group(int(m.group(1))), str(crash["response"]))
                    messages += [(crash["name"], response)]
        return messages

    async def process_message(self, message):
        responses = []

        # attachments
        if message.attachments or "https://cdn.discordapp.com/attachments/" in message.content:
            logging.info("ContentParse: Found file in message")
            try:
                file = await message.attachments[0].to_file()
                file = file.fp
                name = message.attachments[0].filename
                logging.info("ContentParse: Acquired file from discord API")
            except IndexError:
                logging.info("ContentParse: Couldn't acquire file from discord API")
                try:
                    logging.info("ContentParse: Attempting to acquire linked file manually")
                    file_id = message.content.split("https://cdn.discordapp.com/attachments/")[1].split(" ")[0]
                    name = file_id.split("/")[2]
                    file = io.BytesIO(requests.get("https://cdn.discordapp.com/attachments/" + file_id).content)
                except IndexError:
                    logging.info("ContentParse: Couldn't acquire file manually either")
                    file = io.BytesIO(b"")
                    name = ""
            extension = name.rpartition(".")[-1]

            if name.startswith("SMMDebug") or extension == 'log':
                async with message.channel.typing():
                    responses = await self.process_file(file, extension)
            else:
                responses = await self.process_file(file, extension)

            file.close()

        # Pastebin links
        elif "https://pastebin.com/" in message.content:

            text = urlopen(
                f"https://pastebin.com/raw/"
                f"{message.content.split('https://pastebin.com/')[1].split(' ')[0].read().decode('utf-8')}"
            )
            responses = await self.process_text(text)
            maybe_log_info = self.parse_factory_game_log(message.content)

            sml_outdated = await self.make_sml_version_message(**maybe_log_info)
            if sml_outdated:
                responses += [("Outdated SML!", sml_outdated)]

            version_info = self.make_version_info_message(**maybe_log_info)
            if version_info:
                responses += [("Quick log summary", version_info)]

        else:
            responses = await self.process_text(message.content)

        if len(responses) > 2:
            await self.bot.reply_to_msg(message, embed=createembed.crashes(responses))
        else:
            for response in responses:
                await self.bot.reply_to_msg(message, response[1], propagate_reply=False)

        return len(responses) > 0
