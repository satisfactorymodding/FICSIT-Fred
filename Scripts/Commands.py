import discord
import asyncio
import CreateEmbed
import json
import Helper
import matplotlib.pyplot as plt
import datetime
import logging
from algoliasearch.search_client import SearchClient
import requests
import io

logging.basicConfig(level=logging.INFO)

async def handleCommand(client, message, command, args, authorised):
    # Logging
    logging.info("Handling command:\nMessage: " + message.content + "\nCommand: " + command + "\nArguments: " + str(args) + "\nAuthorisation: " + str(authorised))
    # Normal Commands
    global full
    for automation in client.config["commands"]:
        if command == automation["command"]:
            if automation["byPM"]:
                try:
                    user = message.mentions[0]
                except:
                    user = message.author
                if not user.dm_channel:
                    await user.create_dm()
                try:
                    await user.dm_channel.send(automation["response"])
                    await message.add_reaction("✅")
                except:
                    await message.channel("I was unable to send the direct message. Please check your discord "
                                          "settings regarding those if you are the target !")
            else:
                await message.channel.send(automation["response"])
            return

    if command == "help":
        here = False
        full = False
        try:
            if args[0] == "here":
                here = True
            elif args[0] == "full":
                full = True
            try:
                if args[1] == "here":
                    here = True
                if args[1] == "full":
                    full = True
            except:
                pass
        except:
            pass
        embedList = CreateEmbed.command_list(client, full=full, here=here)
        if here:
            channel = message.channel
        else:
            if not message.author.dm_channel:
                await message.author.create_dm()
            channel = message.author.dm_channel
        try:
            helpMessage = await channel.send(content=None, embed=embedList[0])
            if not here:
                message.add_reaction("✅")
        except:
            if not here:
                await message.channel.send("I was unable to send you a direct message. Please check your discord "
                                          "settings regarding those !")
            return
        page = 0
        await helpMessage.add_reaction("➡️")
        ready = True
        def check(reaction, user):
            if ready and reaction.message.id == helpMessage.id and not user.bot and reaction.emoji in ["⬅", "➡️"]:
                return True
        try:
            while True:
                reaction = await client.wait_for("reaction_add", check=check, timeout=240.0)
                ready = False
                if here:
                    await helpMessage.remove_reaction(reaction[0].emoji, reaction[1])
                if reaction[0].emoji == "➡️":
                    page += 1
                    await helpMessage.edit(embed=embedList[page])
                    if here:
                        await helpMessage.remove_reaction("➡️", reaction[1])
                    if (embedList[2] and page == 3) or (not embedList[2] and page == 1):
                        await helpMessage.remove_reaction("➡️", client.user)
                        await helpMessage.add_reaction("⬅")
                    elif page == 1:
                        await helpMessage.remove_reaction("➡️", client.user)
                        await helpMessage.add_reaction("⬅")
                        await helpMessage.add_reaction("➡️")
                    ready = True
                elif reaction[0].emoji == "⬅":
                    page -= 1
                    await helpMessage.edit(embed=embedList[page])
                    if page == 0:
                        await helpMessage.remove_reaction("⬅", client.user)
                    if (embedList[2] and page < 3) or (not embedList[2] and page < 1):
                        await helpMessage.add_reaction("➡️")
                    ready = True
        except asyncio.TimeoutError:
            pass
        return


    if command == "mod":
        if len(args) < 1:
            await message.channel.send("This command requires at least one argument")
            return
        if args[0] == "help":
            await message.channel.send("I search for the provided mod name in the SMR database, returning the details "
                                       "of the mod if it is found. If multiple are found, it will state so. Same for "
                                       "if none are found. If someone reacts to the clipboard in 4m, I will send them "
                                       "the full description of the mod.")
            return
        args = [" ".join(args)]
        result, desc = CreateEmbed.mod(args[0])
        if isinstance(result, str):
            await message.channel.send("Multiple mods found: ```" + result + "```")
        elif result is None:
            await message.channel.send("No mods found!")
        else:
            newmessage = await message.channel.send(content=None, embed=result)
            await newmessage.add_reaction("📋")
            await asyncio.sleep(0.5)

            def check(reaction, user):
                if reaction.emoji == "📋" and reaction.message.id == newmessage.id:
                    return True

            try:
                r = await client.wait_for('reaction_add', timeout=240.0, check=check)
                member = r[1]
                if not member.dm_channel:
                    await member.create_dm()
                try:
                    await member.dm_channel.send(content=None, embed=CreateEmbed.desc(desc))
                    await newmessage.add_reaction("✅")
                except:
                    await message.channel("I was unable to send you a direct message. Please check your discord "
                                          "settings regarding those !")
            except asyncio.TimeoutError:
                pass
        return
    if command == "docsearch":
        yaml = requests.get("https://raw.githubusercontent.com/satisfactorymodding/Documentation/Dev/antora.yml")
        yamlf = io.BytesIO(yaml.content)
        version = str(yamlf.read()).split("version: ")[1].split("\\")[0]

        client = SearchClient.create('BH4D9OD16A', '53b3a8362ea7b391f63145996cfe8d82')
        index = client.init_index('ficsit')
        query = index.search(" ".join(args) + " " + version)
        await message.channel.send("This is the best result I got from the SMD :\n" + query["hits"][0]["url"])
        return

    if command == "version":
        await message.channel.send(client.version)
        return

    if not authorised:
        return

    elif command == "add":
        if len(args) == 0:
            await message.channel.send("This command requires at least one argument")
        if args[0] == "response":
            if args[1]:
                name = args[1]
            else:
                name = await Helper.waitResponse(client, message, "What is the response's name e.g. ``apple``")

            keywords = await Helper.waitResponse(client, message, "What keywords would you like to add? e.g. "
                                                                          "``apple banana 110838934644211712`` (The "
                                                                          "last is a Discord User ID to grab pings)")
            keywords = keywords.split(" ")

            additional_words = await Helper.waitResponse(client, message, "What additional words would you "
                                                                                  "like to add? e.g. ``apple banana "
                                                                                  "carrot 110838934644211712`` (The "
                                                                                  "last is a Discord User ID to grab "
                                                                                  "pings)")

            response = await Helper.waitResponse(client, message, "What response do you want it to provide? "
                                                                          "e.g. ``Thanks for saying my keywords {"
                                                                          "user}`` (use {user} to ping the person "
                                                                          "saying the command (required))")

            ignore_members = await Helper.waitResponse(client, message, "Do you want it to ignore members ("
                                                                                "and only target non-members)? e.g. "
                                                                                "``True`` or ``False``")

            client.config["automated responses"].append(
                {"name": name, "keywords": keywords, "additional words": additional_words, "response": response,
                 "ignore members": ignore_members})
            json.dump(client.config, open("config/config.json", "w"))
            await message.channel.send("Automated Response '" + name + "' added!")

        elif " ".join(args[0:2]) == "media only":
            try:
                id = message.channel_mentions[0].id
            except:
                try:
                    id = args[2]
                except:
                    id = await Helper.waitResponse(client, message, "What is the ID for the channel? e.g. "
                                                                            "``709509235028918334``")

            client.config["media only channels"].append(id)
            json.dump(client.config, open("config/config.json", "w"))
            await message.channel.send("Media only channel " + client.get_channel(int(id)).mention + " added!")
            return

        elif args[0] == "command":
            try:
                command = args[1]
            except:
                command = await Helper.waitResponse(client, message, "What is the command? e.g. ``install``")

            for scommand in (client.config["commands"] + client.config["special commands"] + client.config["management commands"] + client.config["miscellaneous commands"]):
                if command == scommand["command"]:
                    await message.channel.send("This command already exists !")
                    return

            response = await Helper.waitResponse(client, message, "What is the response? e.g. ``Hello there`` "
                                                                          "or an image or link to an image")

            byPM = await Helper.waitResponse(client, message, "Should the response be sent by dm ? (True or False)")

            try:
                byPM = json.loads(byPM.lower())
            except:
                await message.channel.send("You didn't respond with a valid boolean. Defaulting to False")
                byPM = False


            client.config["commands"].append(
                {"command": command, "response": response, "byPM": byPM})
            json.dump(client.config, open("config/config.json", "w"))
            await message.channel.send("Command '" + command + "' added!")

        elif args[0] == "crash":
            try:
                name = args[1]
            except:
                name = await Helper.waitResponse(client, message, "What would you like to name this known "
                                                                          "crash? e.g. ``CommandDave``")

            crash = await Helper.waitResponse(client, message,
                                              "What is the string to search for in the crash logs ? e.g. \"Assertion failed: ObjectA == nullptr\"")

            response = await Helper.waitResponse(client, message,
                                                 "What response do you want it to provide? e.g. ``Thanks for saying my keywords {user}`` (use {user} to ping the user)")

            client.config["known crashes"].append({"name": name, "crash": crash, "response": response})
            json.dump(client.config, open("config/config.json", "w"))
            await message.channel.send("Known crash '" + name + "' added!")
        return
    elif command == "remove":
        if args[0] == "response":
            try:
                name = args[1]
            except:
                name = await Helper.waitResponse(client, message,
                                                 "Which Automated Response do you want to remove?")

            index = 0
            for response in client.config["automated responses"]:
                if response["name"] == name:
                    del client.config["automated responses"][index]
                    json.dump(client.config, open("config/config.json", "w"))
                    await message.channel.send("Response Removed!")
                    return
                else:
                    index += 1
            await message.channel.send("Response could not be found!")

        elif " ".join(args[0:2]) == "media only":
            try:
                id = message.channel_mentions[0].id
            except:
                try:
                    id = args[2]
                except:
                    id = await Helper.waitResponse(client, message,
                                                   "What is the ID for the channel? e.g. ``709509235028918334``")

            index = 0
            for response in client.config["media only channels"]:
                if response == id:
                    del client.config["media only channels"][index]
                    json.dump(client.config, open("config/config.json", "w"))
                    await message.channel.send("Media Only Channel removed!")
                    return
                else:
                    index += 1
            await message.channel.send("Media Only Channel could not be found!")

        elif args[0] == "command":
            try:
                command = args[1]
            except:
                command = await Helper.waitResponse(client, message,
                                                    "Which Command do you want to remove? e.g. ``>install``")

            index = 0
            for response in client.config["commands"]:
                if response["command"] == command:
                    del client.config["commands"][index]
                    json.dump(client.config, open("config/config.json", "w"))
                    await message.channel.send("Command removed!")
                    return
                else:
                    index += 1
            await message.channel.send("Command could not be found!")

        elif args[0] == "crash":
            try:
                name = args[1]
            except:
                name = await Helper.waitResponse(client, message, "Which known crash do you want to remove?")

            index = 0
            for crash in client.config["known crashes"]:
                if crash["name"] == name.lower():
                    del client.config["known crashes"][index]
                    json.dump(client.config, open("config/config.json", "w"))
                    await message.channel.send("Crash removed!")
                    return
                else:
                    index += 1
            await message.channel.send("Crash could not be found!")
        return
    elif command == "members":
        list = []
        async for member in message.guild.fetch_members():
            list.append(member.joined_at)
        list.sort()
        first = list[0]
        last = list[len(list) - 1]
        count = 0
        countlist = []
        nb = 24
        for x in range(0, nb):
            for item in list:
                if item > first + datetime.timedelta(days=x*30):
                    break
                count += 1
            countlist.append(count)
            count = 0

        plt.plot(range(0, nb), countlist)
        with open("Countlist.png", "wb") as image:
            plt.savefig(image, format="PNG")
            plt.clf()
        with open("Countlist.png", "rb") as image:
            await message.channel.send(content=None, file=discord.File(image))
        return
    elif command == "growth":
        list = []
        async for member in message.guild.fetch_members():
            list.append(member.joined_at)
        list.sort()
        first = list[0]
        last = list[len(list) - 1]
        count = 0
        countlist = []
        nb = 24
        for x in range(0, nb):
            for item in list:
                if item > first + datetime.timedelta(days=x*30):
                    break
                count += 1
            countlist.append(count)
            count = 0

        growth = []
        for x in range(0, nb):
            try:
                ratio = (countlist[x] - countlist[x - 1]) / countlist[x - 1]
                growth.append(ratio * 100)
            except IndexError:
                growth.append(100)

        plt.plot(range(0, nb), growth)
        with open("Growth.png", "wb") as image:
            plt.savefig(image, format="PNG")
            plt.clf()
        with open("Growth.png", "rb") as image:
            await message.channel.send(content=None, file=discord.File(image))
        return
    if authorised != 2:
        return

    elif command == "engineers":
        try:
            id = message.channel_mentions[0].id
        except:
            try:
                id = args[0]
            except:
                id = await Helper.waitResponse(client, message,
                                               "What is the ID for the channel? e.g. ``709509235028918334``")
        client.config["filter channel"] = id
        json.dump(client.config, open("config/config.json", "w"))
        await message.channel.send(
            "The filter channel for the engineers is now " + client.get_channel(int(id)).mention + "!")

    elif command == "moderators":
        try:
            id = message.channel_mentions[0].id
        except:
            try:
                id = args[0]
            except:
                id = await Helper.waitResponse(client, message,
                                               "What is the ID for the channel? e.g. ``709509235028918334``")
        client.config["mod channel"] = id
        json.dump(client.config, open("config/config.json", "w"))
        await message.channel.send(
            "The filter channel for the moderators is now " + client.get_channel(int(id)).mention + "!")

    elif command == "githook":
        try:
            id = message.channel_mentions[0].id
        except:
            try:
                id = args[0]
            except:
                id = await Helper.waitResponse(client, message,"What is the ID for the channel? e.g. ``709509235028918334``")
        client.config["githook channel"] = id
        json.dump(client.config, open("config/config.json", "w"))
        await message.channel.send(
            "The channel for the github hooks is now " + client.get_channel(int(id)).mention + "!")

    elif command == "prefix":
        client.config["prefix"] = args[0]
        json.dump(client.config, open("config/config.json", "w"))
        await message.channel.send("Prefix changed to " + args[0] + " !")

    elif command == "saveconfig":
        if not message.author.dm_channel:
            await message.author.create_dm()
        try:
            await message.author.dm_channel.send(content=None,
                                       file=discord.File(open("config/config.json", "r"), filename="config.json"))
            await message.add_reaction("✅")
        except:
            await message.channel("I was unable to send you a direct message. Please check your discord "
                                  "settings regarding those !")


