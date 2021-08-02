import re
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


class Crashes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def extract_game_info_from_text(text):
        try:
            r = re.search(r"Satisfactory Mod Loader v\.(\d+\.\d+\.\d+)", text)
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

    @staticmethod
    def make_sml_version_message(game_version, sml_version):
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
            r = requests.post("https://api.ficsit.app/v2/query", json={"query": query})
            r_data = json.loads(r.text)
            sml_versions = r_data["data"]["getSMLVersions"]["sml_versions"]
            for i in range(0, len(sml_versions) - 1):
                if sml_versions[i]["satisfactory_version"] > game_version:
                    continue
                else:
                    latest = sml_versions[i]
                    break
            if latest["version"] != sml_version:
                return f"Your SML version is old. You should update to {latest['version']}."
        return None

    async def process_file(self, file, extension):
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

            with zipfile.ZipFile(file) as zip_f:
                for zip_file_name in zip_f.namelist():
                    with zip_f.open(zip_file_name) as zip_file:
                        zip_file_content = zip_file.read().decode("utf-8")
                        for message in self.process_text(zip_file_content):
                            messages.append(message)

                if 'metadata.json' in zip_f.namelist():
                    with zip_f.open("metadata.json") as metadataFile:
                        metadata = json.load(metadataFile)
                        if metadata["selectedInstall"]:
                            game_version = int(metadata["selectedInstall"]["version"])
                            path = metadata["selectedInstall"]["installLocation"]
                        if "smlVersion" in metadata:
                            sml_version = metadata["smlVersion"]
                        smm_version = metadata["smmVersion"]
                elif 'FactoryGame.log' in zip_f.namelist():
                    # Try to find CL and SML versions in FactoryGame.log
                    with zip_f.open("FactoryGame.log") as fg_log:
                        fg_log_content = fg_log.read().decode("utf-8")
                        sml_version, game_version, path, launcher_id, commandline = \
                            self.extract_game_info_from_text(fg_log_content[:200000])
            
            sml_outdated = self.make_sml_version_message(game_version, sml_version)
            if sml_outdated:
                messages.append(sml_outdated)

            version_info = self.make_version_info_message(smm_version, game_version, sml_version,
                                                          path, launcher_id, commandline)
            if version_info:
                messages.append(version_info)
            
            return messages
        elif extension == "log" or extension == "txt":
            text = file.read().decode("utf-8", errors="ignore")
            messages = self.process_text(text)

            sml_version, game_version, path, launcher_id, commandline = self.extract_game_info_from_text(text)
            
            sml_outdated = self.make_sml_version_message(game_version, sml_version)
            if sml_outdated:
                messages.append(sml_outdated)

            version_info = self.make_version_info_message(None, game_version, sml_version,
                                                          path, launcher_id, commandline)
            if version_info:
                messages.append(version_info)
            
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
                    self.bot.logger.info("OCR returned the following data:\n" + image_text)
                    return self.process_text(image_text)

            except Exception as e:
                self.bot.logger.error(f"OCR error:\n{e}")
                return []

    def process_text(self, text):
        messages = []
        for crash in config.Crashes.fetch_all():
            if match := re.search(crash["crash"], text, flags=re.IGNORECASE):
                if str(crash["response"]).startswith(self.bot.command_prefix):
                    if command := config.Commands.fetch(crash["response"][len(self.bot.command_prefix):]):
                        messages.append(command["content"])
                else:
                    text = re.sub("{(\d+)}", lambda m: match.group(int(m.group(1))), str(crash["response"]))
                    messages.append(text)
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
            
                sml_outdated = self.make_sml_version_message(game_version, sml_version)
                if sml_outdated:
                    responses.append(sml_outdated)

                version_info = self.make_version_info_message(None, game_version, sml_version,
                                                              path, launcher_id, commandline)
                if version_info:
                    responses.append(version_info)
            except:
                pass
        else:
            responses = self.process_text(message.content)
            sml_version, game_version, path, launcher_id, commandline = \
                self.extract_game_info_from_text(message.content)
            
            sml_outdated = self.make_sml_version_message(game_version, sml_version)
            if sml_outdated:
                responses.append(sml_outdated)

            version_info = self.make_version_info_message(None, game_version, sml_version,
                                                          path, launcher_id, commandline)
            if version_info:
                responses.append(version_info)

        for response in responses:
            await self.bot.reply_to_msg(message, response, propagate_reply=False)

        return len(responses) > 0
