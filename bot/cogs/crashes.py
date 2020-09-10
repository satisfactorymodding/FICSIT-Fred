import discord.ext.commands as commands
import requests
from PIL import Image, ImageEnhance
from packaging import version
from pytesseract import image_to_string
import jellyfish
import zipfile
from urllib.request import urlopen
import io
import json


class Crashes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def process_message(self, message):
        hasMetadata = False
        sml_version = ""
        CL = 0

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
                data = file.read().decode("utf-8")

            # SMM Debug file
            elif ".zip" in name and "SMMDebug" in name:
                with zipfile.ZipFile(file) as zip:
                    try:
                        data = zip.open("FactoryGame.log").read().decode("utf-8")
                    except KeyError:
                        data = ""
                        pass
                    with zip.open("metadata.json") as metadataFile:
                        metadata = json.load(metadataFile)
                        CL = int(metadata["selectedInstall"]["version"])
                        if len(metadata["installedMods"]) > 0:
                            sml_version = metadata["smlVersion"]
                            smb_version = metadata["bootstrapperVersion"]
                            hasMetadata = True

            # images
            else:
                try:
                    image = Image.open(file)
                    ratio = 4320 / image.height
                    if ratio > 1:
                        image = image.resize((round(image.width * ratio), round(image.height * ratio)),
                                             Image.LANCZOS)

                    enhancerContrast = ImageEnhance.Contrast(image)

                    image = enhancerContrast.enhance(2)
                    enhancerSharpness = ImageEnhance.Sharpness(image)
                    image = enhancerSharpness.enhance(10)

                    data = image_to_string(image, lang="eng")

                except:
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
                sml_version = data.find("SatisfactoryModLoader ", 0, 1000)
                assert sml_version != -1
                sml_version = data[sml_version:][23:].split("\r")[0]
            except:
                sml_version = ""
            try:
                CL = int(data[:200000].split("-CL-")[1].split("\n")[0])
            except:
                CL = 0

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
                if hasMetadata:
                    if sml_versions[i]["version"] == sml_version:
                        if version.parse(sml_versions[i]["bootstrap_version"]) > version.parse(smb_version):
                            await message.channel.send(
                                "Hi " + message.author.mention + " ! Your SMBootstrapper version is wrong. Please update it to " +
                                sml_versions[i][
                                    "bootstrap_version"] + ". This can often be done by switching to the \"vanilla\" SMM profile and switching back to \"modded\", without launching the game in-between.")
                if sml_versions[i]["satisfactory_version"] > CL:
                    continue
                else:
                    latest = sml_versions[i]
                    break
            if latest["version"] != sml_version:
                await message.channel.send(
                    "Hi " + message.author.mention + " ! Your SML version is wrong. Please update it to " + latest[
                        "version"] + ". This can often be done by switching to the \"vanilla\" SMM profile and switching back to \"modded\", without launching the game in-between.")

        data = data.lower()
        try:
            file.close()
        except:
            pass
        for crash in self.bot.config["known crashes"]:
            for line in data.split("\n"):
                if jellyfish.levenshtein_distance(line, crash["crash"].lower()) < len(crash["crash"]) * 0.1:
                    await message.channel.send(str(crash["response"].format(user=message.author.mention)))
                    return
