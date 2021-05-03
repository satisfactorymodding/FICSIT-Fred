import re
import discord.ext.commands as commands
import requests
from PIL import Image, ImageEnhance
from packaging import version
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

    async def process_message(self, message):
        hasMetadata = False
        sml_version = ""
        smb_version = ""
        CL = 0
        path = ""

        sent = None

        # attachments
        if message.attachments or "https://cdn.discordapp.com/attachments/" in message.content:
            try:
                file = await message.attachments[0].to_file()
                file = file.fp
                name = message.attachments[0].filename
            except:
                try:
                    id = message.content.split("https://cdn.discordapp.com/attachments/")[1].split(" ")[0]
                    name = id.split("/")[2]
                    file = io.BytesIO(requests.get("https://cdn.discordapp.com/attachments/" + id).content)
                except:
                    file = io.BytesIO(b"")
                    name = ""
            # .log or .txt Files
            if ".log" in name or ".txt" in name:
                data = file.read().decode("utf-8", errors="ignore")

            # SMM Debug file
            elif name.endswith(".zip"):
                with zipfile.ZipFile(file) as file:
                    data = file.open("FactoryGame.log").read().decode(
                        "utf-8") if "FactoryGame.log" in file.namelist() else ""
                    with file.open("metadata.json") as metadataFile:
                        metadata = json.load(metadataFile)
                        if metadata["selectedInstall"]:
                            CL = int(metadata["selectedInstall"]["version"])
                        if "installedMods" in metadata and len(metadata["installedMods"]) > 0:
                            sml_version = metadata["smlVersion"]
                            path = metadata["selectedInstall"]["installLocation"]
                            hasMetadata = True
                            "Resolved imports successfully; Calling DllMain"

            # images
            else:
                try:
                    image = Image.open(file)
                    ratio = 2160 / image.height
                    if ratio > 1:
                        image = image.resize((round(image.width * ratio), round(image.height * ratio)),
                                             Image.LANCZOS)

                    enhancerContrast = ImageEnhance.Contrast(image)

                    image = enhancerContrast.enhance(2)
                    enhancerSharpness = ImageEnhance.Sharpness(image)
                    image = enhancerSharpness.enhance(10)
                    with ThreadPoolExecutor() as pool:
                        data = await self.bot.loop.run_in_executor(pool, image_to_string, image)
                        self.bot.logger.info("OCR returned the following data :\n" + data)


                except Exception as e:
                    print(e)
                    data = ""


        # Pastebin links
        elif "https://pastebin.com/" in message.content:
            try:
                data = urlopen(
                    "https://pastebin.com/raw/" + message.content.split("https://pastebin.com/")[1].split(" ")[
                        0]).read().decode("utf-8")
            except:
                data = ""
        else:
            data = message.content

        # Try to find CL and SML versions in data
        if not hasMetadata:
            try:
                r = re.search(r"Satisfactory Mod Loader v\.(\d+\.\d+\.\d+)", data)
                sml_version = r[1]
            except TypeError:
                sml_version = None
            try:
                CL = int(data[:200000].split("-CL-")[1].split("\n")[0])
            except:
                CL = 0
            try:
                path = data[:100000].split("LogInit: Base Directory: ")[1].split("\n")[0]
            except:
                path = ""
        try:
            launcherid = data[:100000].split("LogInit: Launcher ID: ")[1].split("\n")[0]
        except:
            launcherid = ""
        try:
            commandline = data[:100000].split("LogInit: Command Line: ")[1].split("\n")[0]
        except:
            commandline = ""

        versionInfo = ""
        if CL:
            versionInfo += "CL : " + str(CL) + "\n"
        if sml_version:
            versionInfo += "SML : " + sml_version + "\n"
        if path:
            versionInfo += "Path : " + path + "\n"
        if launcherid:
            versionInfo += "Launcher ID : " + launcherid + "\n"
        if commandline:
            versionInfo += "Command Line : " + commandline + "\n"
        if versionInfo:
            sent = await self.bot.reply_to_msg(message, versionInfo)
        if CL and sml_version:
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
            r = requests.post("https://api.ficsit.app/v2/query", json={'query': query})
            rData = json.loads(r.text)
            sml_versions = rData["data"]["getSMLVersions"]["sml_versions"]
            for i in range(0, len(sml_versions) - 1):
                if sml_versions[i]["satisfactory_version"] > CL:
                    continue
                else:
                    latest = sml_versions[i]
                    break
            if latest["version"] != sml_version:
                sent = await self.bot.reply_to_msg(message,
                                                   "Hi " + message.author.mention + " ! Your SML version is wrong. Please update it to " +
                                                   latest[
                                                       "version"] + ". This can often be done by switching to the \"vanilla\" SMM profile and switching back to \"modded\", without launching the game in-between.")

        data = data.lower()
        try:
            file.close()
        except:
            pass
        data = data[len(data) - 100000:]
        for crash in config.Crashes.fetch_all():
            if re.search(crash["crash"].lower(), data.lower()):
                if str(crash["response"]).startswith(self.bot.command_prefix):
                    if command := config.Commands.fetch(crash["response"][len(self.bot.command_prefix):]):
                        await self.bot.reply_to_msg(message, command["content"])
                else:
                    await self.bot.reply_to_msg(message, str(crash["response"]))


        return sent
