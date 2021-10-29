import errno
import logging
import os
import re
import signal
from functools import wraps

import discord.ext.commands as commands
import requests
from PIL import Image, ImageEnhance
from pytesseract import image_to_string
import zipfile
from urllib.request import urlopen
import io
import json
import config
from concurrent.futures import ThreadPoolExecutor
from time import strptime

from libraries import helper
from libraries import createembed


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
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def extract_game_info_from_text(text):
        try:
            r = timedregexsearch(r"Satisfactory Mod Loader v\.(\d+\.\d+\.\d+)", text)
            sml_version = r[1]
        except TypeError:
            sml_version = None
        try:
            game_version = int(text.split("-CL-")[1].split("\n")[0])
        except IndexError:
            game_version = 0
        try:
            path = text.split("LogInit: Base Directory: ")[1].split("\n")[0]
        except IndexError:
            path = ""
        try:
            launcher_id = text.split("LogInit: Launcher ID: ")[1].split("\n")[0]
        except IndexError:
            launcher_id = ""
        try:
            commandline = text.split("LogInit: Command Line: ")[1].split("\n")[0]
        except IndexError:
            commandline = ""
        return sml_version, game_version, path, launcher_id, commandline

    @staticmethod
    def make_version_info_message(smm_version, game_version, sml_version, path, launcher_id, commandline) -> str:
        version_info = ""

        if smm_version:
            version_info += f"SMM: {smm_version}\n"
        if game_version:
            version_info += f"CL: {game_version}\n"
        if sml_version:
            version_info += f"SML: {sml_version}\n"
        if path:
            version_info += f"Path: {path}\n"
        if launcher_id:
            version_info += f"Launcher ID: {launcher_id}\n"
        if commandline:
            version_info += f"Command Line: {commandline}\n"

        return version_info

    async def make_sml_version_message(self, game_version, sml_version):
        if game_version and sml_version:
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
            result = await helper.repository_query(query, self.bot)
            sml_versions = result["data"]["getSMLVersions"]["sml_versions"]
            for i in range(0, len(sml_versions) - 1):
                if sml_versions[i]["satisfactory_version"] > game_version:
                    continue
                else:
                    latest = sml_versions[i]
                    break
            if latest["version"] != sml_version:
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
        enabled = []
        for item in mod_list:
            if item["enabled"]:
                enabled += [item["id"]]

        return enabled

    async def check_for_outdated_mods(self, mod_list: list):

        enabled_mods: list = self.filter_enabled(mod_list)
        if not enabled_mods:
            return enabled_mods

        # This block separates the mods into blocks of 100 because that's
        results = dict()
        for slice in [enabled_mods[i:i + 100] for i in range(0, len(enabled_mods), 100)]:
            query_mods, length = str(slice).replace("'", '"'), str(len(slice))

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
            result = await helper.repository_query(query, self.bot)
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
        if extension == "":
            return []
        elif extension == "zip":
            messages = []

            smm_version = ""
            sml_version = ""
            game_version = 0
            path = ""
            launcher_id = ""
            commandline = ""
            outdated_mods = []

            with zipfile.ZipFile(file) as zip_f:
                for zip_file_name in zip_f.namelist():
                    with zip_f.open(zip_file_name) as zip_file:
                        try:
                            zip_file_content = zip_file.read().decode("utf-8")
                        except zipfile.BadZipFile:
                            return ["This zipfile is invalid! Its contents may have been changed after zipping."]

                        messages += self.process_text(zip_file_content)

                if 'metadata.json' in zip_f.namelist():
                    with zip_f.open("metadata.json") as metadataFile:
                        metadata = json.load(metadataFile)
                        if metadata["selectedInstall"]:
                            game_version = int(metadata["selectedInstall"]["version"])
                            path = metadata["selectedInstall"]["installLocation"]
                        if metadata["selectedProfile"]:
                            if metadata["selectedProfile"]["name"] != "development":
                                outdated_mods = await self.check_for_outdated_mods(metadata["selectedProfile"]["items"])

                        if "smlVersion" in metadata:
                            sml_version = metadata["smlVersion"]
                        smm_version = metadata["smmVersion"]

                if 'FactoryGame.log' in zip_f.namelist():
                    # Try to find CL and SML versions in FactoryGame.log
                    with zip_f.open("FactoryGame.log") as fg_log:
                        fg_log_content = fg_log.read().decode("utf-8")
                        fg_sml_version, fg_game_version, fg_path, fg_launcher_id, fg_commandline = \
                            self.extract_game_info_from_text(fg_log_content[:200000])

                        # If a property was not found before, use the one from the log
                        if not sml_version and fg_sml_version:
                            sml_version = fg_sml_version
                        if not game_version and fg_game_version:
                            game_version = fg_game_version
                        if not path and fg_path:
                            path = fg_path
                        if not launcher_id and fg_launcher_id:
                            launcher_id = fg_launcher_id
                        if not commandline and fg_commandline:
                            commandline = fg_commandline

            sml_outdated = await self.make_sml_version_message(game_version, sml_version)
            if sml_outdated:
                messages += [("Outdated SML!", sml_outdated)]

            if outdated_mods:
                messages += [("Outdated Mods!", self.make_outdated_mods_message(outdated_mods))]

            version_info = self.make_version_info_message(smm_version, game_version, sml_version,
                                                          path, launcher_id, commandline)
            if version_info:
                messages += [("Version Info (ignore this)", version_info)]

            return messages
        elif extension == "log" or extension == "txt":
            text = file.read().decode("utf-8", errors="ignore")
            messages = self.process_text(text)

            sml_version, game_version, path, launcher_id, commandline = self.extract_game_info_from_text(text)

            sml_outdated = await self.make_sml_version_message(game_version, sml_version)
            if sml_outdated:
                messages += [("Outdated SML!", sml_outdated)]

            version_info = self.make_version_info_message(None, game_version, sml_version,
                                                          path, launcher_id, commandline)
            if version_info:
                messages += [("Version Info (ignore this)", version_info)]

            return messages
        else:
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
                    return self.process_text(image_text)

            except Exception as e:
                logging.error(f"OCR error:\n{e}")
                return []

    def process_text(self, text) -> list[tuple[str, str]]():
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
            try:
                file = await message.attachments[0].to_file()
                file = file.fp
                name = message.attachments[0].filename
            except:
                try:
                    file_id = message.content.split("https://cdn.discordapp.com/attachments/")[1].split(" ")[0]
                    name = file_id.split("/")[2]
                    file = io.BytesIO(requests.get("https://cdn.discordapp.com/attachments/" + file_id).content)
                except IndexError:
                    file = io.BytesIO(b"")
                    name = ""
            extension = name.split(".")[-1]
            if extension == name:
                extension = ""
            responses = await self.process_file(file, extension)

            file.close()

        # Pastebin links
        elif "https://pastebin.com/" in message.content:
            try:
                text = urlopen(
                    f"https://pastebin.com/raw/"
                    f"{message.content.split('https://pastebin.com/')[1].split(' ')[0].read().decode('utf-8')}"
                )
                responses = self.process_text(text)
                sml_version, game_version, path, launcher_id, commandline = \
                    self.extract_game_info_from_text(message.content)

                sml_outdated = await self.make_sml_version_message(game_version, sml_version)
                if sml_outdated:
                    responses += [("Outdated SML!", sml_outdated)]

                version_info = self.make_version_info_message(None, game_version, sml_version,
                                                              path, launcher_id, commandline)
                if version_info:
                    responses += [("Version Info (ignore this)", version_info)]
            except:
                pass
        else:
            responses = self.process_text(message.content)
            sml_version, game_version, path, launcher_id, commandline = \
                self.extract_game_info_from_text(message.content)

            sml_outdated = await self.make_sml_version_message(game_version, sml_version)
            if sml_outdated:
                responses += [("Outdated SML!", sml_outdated)]

            version_info = self.make_version_info_message(None, game_version, sml_version,
                                                          path, launcher_id, commandline)
            if version_info:
                responses += [("Version Info (ignore this)", version_info)]

        if len(responses) > 2:
            await self.bot.reply_to_msg(message, embed=createembed.crashes(responses))
        else:
            for response in responses:
                await self.bot.reply_to_msg(message, response[1], propagate_reply=False)

        return len(responses) > 0
