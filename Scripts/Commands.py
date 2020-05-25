import discord
import asyncio
import CreateEmbed
import json
import Helper
import datetime


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
            await message.channel.send(
                "This command earches for the passed argument in the SMR database, returning the details of the mod if it is found. If multiple are found, it will state so. Same for if none are found. If the user that used the command reacts with the clipboard within a minute, I will extend the post to show the full description of said mod.")
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
                await message.channel.send("What would you like to name this automation? e.g. ``CommandDave``")
                name = await client.wait_for('message', timeout=30.0)
                name = name.content

            await message.channel.send(
                "What keywords would you like to add? e.g. ``apple banana 110838934644211712`` (The last is a Discord User ID to grab pings)")
            keywords = await client.wait_for('message', timeout=60.0)
            keywords = keywords.content.split(" ")

            await message.channel.send(
                "What additional words would you like to add? e.g. ``apple banana carrot 110838934644211712`` (The last is a Discord User ID to grab pings)")
            additional_words = await client.wait_for('message', timeout=60.0)
            additional_words = additional_words.content.split(" ")

            await message.channel.send(
                "What response do you want it to provide? e.g. ``Thanks for saying my keywords {user}`` (use {user} to ping the person saying the command (required))")
            response = await client.wait_for('message', timeout=60.0)
            response = response.content

            await message.channel.send(
                "Do you want it to ignore members (and only target non-members)? e.g. ``True`` or ``False``")
            ignore_members = await client.wait_for('message', timeout=10.0)
            ignore_members = ignore_members.content

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
                    await message.channel.send("What is the name of the channel? e.g. ``Screenshots``")
                    name = await client.wait_for('message', timeout=30.0)
                    name = name.content
                try:
                    id = args[3]
                except:
                    await message.channel.send("What is the ID for the channel? e.g. ``709509235028918334``")
                    id = await client.wait_for('message', timeout=60.0)
                    id = id.content

            client.config["media only channels"].append(
                {"name": name, "id": id})
            json.dump(client.config, open("Config.json", "w"))
            await message.channel.send("Media Only Channel '" + name + "' added.")
            return

        elif args[0] == "command":
            try:
                command = args[1]
            except:
                await message.channel.send("What is the command? e.g. ``>install``")
                command = await client.wait_for('message', timeout=30.0)
                command = command.content

                await message.channel.send("What is the response? e.g. ``Hello there`` or ``../Images/Install.png``")
                response = await client.wait_for('message', timeout=60.0)
                response = response.content

                await message.channel.send("Is the response a file? e.g. ``True`` or ``False``")
                media = await client.wait_for('message', timeout=60.0)
                media = json.loads(media.content.lower())

                client.config["commands"].append(
                    {"command": command, "response": response, "media": media})
                json.dump(client.config, open("Config.json", "w"))
                await message.channel.send("Command '" + command + "' added.")

        elif args[0] == "crash":
            try:
                name = args[1]
            except:
                await message.channel.send("What would you like to name this known crash? e.g. ``CommandDave``")
                name = await client.wait_for('message', timeout=30.0)
                name = name.content

                await message.channel.send(
                    "What is the string to search for in the crash logs ? e.g. \"Assertion failed: ObjectA == nullptr\"")
                crash = await client.wait_for('message', timeout=60.0)
                crash = crash.content

                await message.channel.send(
                    "What response do you want it to provide? e.g. ``Thanks for saying my keywords {user}`` (use {user} to ping the user)")
                response = await client.wait_for('message', timeout=60.0)
                response = response.content

                client.config["known crashes"].append({"name": name, "crash": crash, "response": response})
                json.dump(client.config, open("Config.json", "w"))
                await message.channel.send("Known crash '" + name + "' added.")

    elif command == "remove":
        if args[0] == "response":
            try:
                name = args[1]
            except:
                await message.channel.send("Which Automated Response do you want to remove?")
                name = await client.wait_for('message', timeout=30.0)
                name = name.content

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
                await message.channel.send("Which Media Only Channel do you want to remove?")
                name = await client.wait_for('message', timeout=30.0)
                name = name.content

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
                await message.channel.send("Which Command do you want to remove? e.g. ``>install``")
                command = await client.wait_for('message', timeout=30.0)
                command = command.content

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
                await message.channel.send("Which known crash do you want to remove?")
                name = await client.wait_for('message', timeout=30.0)
                name = name.content

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

    if authorised != 2:
        print(authorised)
        return

    if command == "hardban":
        deletemessages = 7
        command = "ban"
    else:
        deletemessages = 0
    if command == "ban":
        if len(args) < 1:
            await message.channel.send("This command needs a user")
            return
        try:
            user = message.mentions[0]
        except:
            try:
                user = await client.fetch_user(int(args[0]))
            except:
                await message.channel.send("User cannot be found")
                return
        if user == message.author:
            await message.channel.send("You cannot ban yourself, dummy !")
            return
        for x in client.bans:
            if client.bans[x]["userid"] == user.id:
                await message.channel.send("User is already banned")
                return
        try:
            time = str(Helper.strToTime("".join(args).split("|")[1]))
        except:
            time = "Indefinitely"
        try:
            reason = args[1]
            reason = " ".join(args[1:]).split("|")[0].strip()
        except:
            reason = "Unspecified"
        try:
            await message.guild.ban(user=user, delete_message_days=deletemessages, reason=reason)
        except discord.Forbidden:
            await message.channel.send("You do not have the necessary permissions to ban this specific user")
            return
        ban = {
            "user": str(user),
            "userid": user.id,
            "reason": reason,
            "moderator": str(message.author),
            "moderatorid": message.author.id,
            "until": time
        }
        client.bans[len(client.bans)] = ban
        json.dump(client.bans, open("Bans.json", "w"))
        if not user.dm_channel:
            await user.create_dm()
        try:
            await user.dm_channel.send("You got banned by " + str(message.author) + " Until: " + time + " Reason: " + reason)#embed
        except:
            await message.channel.send("Banned " + str(user) + " (" + str(user.id) + ") Until: " + time + " Reason: " + reason + " (was unable to send a PM to the user)")#embed ? not sure if the precision is needed
            return
        await message.channel.send("Banned " + str(user) + " (" + str(user.id) + ") Until: " + time + " Reason: " + reason)#embed
        return

    if command == "unban":
        if len(args) < 1:
            await message.channel.send("This command needs a user")
            return
        try:
            reason = args[1]
            reason = " ".join(args[1:])
        except:
            reason = "Unspecified"
        try:
            user = message.mentions[0]
        except:
            user = await client.fetch_user(int(args[0]))
            if not user:
                await message.channel.send("User cannot be found")
                return
        for x in client.bans:
            if client.bans[x]["userid"] == user.id:
                print("Found")
                try:
                    await message.guild.unban(user=user, reason=reason)
                except discord.Forbidden:
                    await message.channel.send("Cannot ban this user")
                    return
                except:
                    await message.channel.send("Something went wrong, sorry about that")
                    return
                print(client.bans[x])
                del client.bans[x]
                json.dump(client.bans, open("Bans.json", "w"))
                await message.channel.send("Unbanned " + str(user) + "(" + str(user.id) + ") Reason: " + reason) #embed
                return
        await message.channel.send("User isn't banned")
        return
