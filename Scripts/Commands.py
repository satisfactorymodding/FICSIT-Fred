import discord
import asyncio
import CreateEmbed
import json
import Helper

async def handleCommand(client, message, command, args, authorised):
    # Normal Commands
    for automation in client.config["commands"]:
        if message.content.startswith(automation["command"]):
            if automation["media"]:
                await message.channel.send(content=None, file=discord.File(automation["response"]))
            else:
                await message.channel.send(automation["response"])

    if command == "help":
        await message.channel.send(content=None, embed=CreateEmbed.command_list())

    if command == "mod":
        if len(args) != 1:
            await message.channel.send("This command requires one argument")
            return
        if args[0] == "help":
            await message.channel.send("This command earches for the passed argument in the SMR database, returning the details of the mod if it is found. If multiple are found, it will state so. Same for if none are found. If the user that used the command reacts with the clipboard within a minute, I will extend the post to show the full description of said mod.")
            return
        result, desc = CreateEmbed.mod(args[0])
        if isinstance(result, str):
            await message.channel.send("Multiple mods found: ```" + result + "```")
        elif result is None:
            await message.channel.send("No mods found!")
        else:
            newmessage = await message.channel.send(content=None, embed=result)
            await newmessage.add_reaction("📋")
            await asyncio.sleep(2)

            def check(reaction, user):
                if reaction.emoji == "📋" and user == message.author and reaction.message.id == newmessage.id:
                    raise InterruptedError

            try:
                await client.wait_for('reaction_add', timeout=60.0, check=check)
            except asyncio.TimeoutError:
                print("User didnt react")
            except InterruptedError:
                await message.channel.send(content=None, embed=CreateEmbed.desc(desc))

    if not authorised:
        return

    elif command == "add":
        if len(args) == 0:
            await message.channel.send("This command requires at least one argument")
        if args[0] == "response":
            if args[1]:
                name = args[1]
            else:
                await Helper.waitResponse(client, message.channel, "")
                name = name.content

            keywords = await Helper.waitResponse(client, message.channel, "What keywords would you like to add? e.g. ``apple banana 110838934644211712`` (The last is a Discord User ID to grab pings)").split(" ")

            additional_words = await Helper.waitResponse(client, message.channel, "What additional words would you like to add? e.g. ``apple banana carrot 110838934644211712`` (The last is a Discord User ID to grab pings)")

            response = await Helper.waitResponse(client, message.channel, "What response do you want it to provide? e.g. ``Thanks for saying my keywords {user}`` (use {user} to ping the person saying the command (required))")

            ignore_members = await Helper.waitResponse(client, message.channel, "Do you want it to ignore members (and only target non-members)? e.g. ``True`` or ``False``")

            client.config["automated responses"].append(
                {"name": name, "keywords": keywords, "additional words": additional_words, "response": response,
                 "ignore members": ignore_members})
            json.dump(client.config, open("Config.json", "w"))
            await message.channel.send("Automated Response '" + name + "' added.")

        elif " ".join(args[0:2]) == "media only":
            try:
                name = message.channel_mentions[0].name
                id = message.channel_mentions[0].id
            except:
                try:
                    name = args[2]
                except:
                    name = await Helper.waitResponse(client, message.channel, "What is the name of the channel? e.g. ``Screenshots``")
                try:
                    id = args[3]
                except:
                    id = await Helper.waitResponse(client, message.channel, "What is the ID for the channel? e.g. ``709509235028918334``")

            client.config["media only channels"].append({"name": name, "id": id})
            json.dump(client.config, open("Config.json", "w"))
            await message.channel.send("Media Only Channel '" + name + "' added.")
            return

        elif args[0] == "command":
            try:
                command = args[1]
            except:
                command = await Helper.waitResponse(client, message.channel, "What is the command? e.g. ``>install``")

                response = await Helper.waitResponse(client, message.channel, "What is the response? e.g. ``Hello there`` or ``../Images/Install.png``")

                media = json.loads(await Helper.waitResponse(client, message.channel, "Is the response a file? e.g. ``True`` or ``False``").lower())

                client.config["commands"].append(
                    {"command": command, "response": response, "media": media})
                json.dump(client.config, open("Config.json", "w"))
                await message.channel.send("Command '" + command + "' added.")

        elif args[0] == "crash":
            try:
                name = args[1]
            except:
                name = await Helper.waitResponse(client, message.channel, "What would you like to name this known crash? e.g. ``CommandDave``")

                crash = await Helper.waitResponse(client, message.channel, "What is the string to search for in the crash logs ? e.g. \"Assertion failed: ObjectA == nullptr\"")

                response = await Helper.waitResponse(client, message.channel, "What response do you want it to provide? e.g. ``Thanks for saying my keywords {user}`` (use {user} to ping the user)")

                client.config["known crashes"].append({"name": name, "crash": crash, "response": response})
                json.dump(client.config, open("Config.json", "w"))
                await message.channel.send("Known crash '" + name + "' added.")

    elif command == "remove":
        if args[0] == "response":
            try:
                name = args[1]
            except:
                name = await Helper.waitResponse(client, message.channel, "Which Automated Response do you want to remove?")

                index = 0
                for response in client.config["automated responses"]:
                    if response["name"] == name:
                        del client.config["automated responses"][index]
                        json.dump(client.config, open("Config.json", "w"))
                        await message.channel.send("Response Removed!")
                        return
                    else:
                        index += 1
                await message.channel.send("Response could not be found!")

        elif " ".join(args[0:2]) == "media only":
            try:
                name = args[2]
            except:
                name = await Helper.waitResponse(client, message.channel, "Which Media Only Channel do you want to remove?")

                index = 0
                for response in client.config["media only channels"]:
                    if response["name"] == name:
                        del client.config["media only channels"][index]
                        json.dump(client.config, open("Config.json", "w"))
                        await message.channel.send("Media Only Channel Removed!")
                        return
                    else:
                        index += 1
                await message.channel.send("Media Only Channel could not be found!")

        elif args[0] == "command":
            try:
                command = args[1]
            except:
                command = await Helper.waitResponse(client, message.channel, "Which Command do you want to remove? e.g. ``>install``")

                index = 0
                for response in client.config["commands"]:
                    if response["command"] == command:
                        del client.config["commands"][index]
                        json.dump(client.config, open("Config.json", "w"))
                        await message.channel.send("Command Removed!")
                        return
                    else:
                        index += 1
                await message.channel.send("Command could not be found!")

        elif args[0] == "crash":
            try:
                name = args[0]
            except:
                name = await Helper.waitResponse(client, message.channel, "Which known crash do you want to remove?")

                index = 0
                for crash in client.config["known crashes"]:
                    if crash["name"] == name:
                        del client.config["known crashes"][index]
                        json.dump(client.config, open("Config.json", "w"))
                        await message.channel.send("Crash Removed!")
                        return
                    else:
                        index += 1
                await message.channel.send("Crash could not be found!")