import discord
import datetime
import requests
import json
import Helper

with open("Config.json", "r") as file:
    Config = json.load(file)

# Github Update Embed Formats
def run(data):
    embed = "Debug"
    if "commits" in data:
        embed = push(data)
    elif "pull_request" in data:
        embed = pull_request(data)
    elif "action" in data:
        if data["action"] == "added":
            embed = contributer_added(data)
    else:
        print(data)

    return embed


def push(data):
    repo_name = data["repository"]["full_name"]
    repo_full_name = str(data["repository"]["name"] + "/" + data["ref"].lstrip("refs/heads"))

    embed = discord.Embed(title=str("Push created by __**" + data["sender"]["login"] + "**__"),
                          colour=Config["action colours"]["Push"], url=data["repository"]["url"],
                          description=data["head_commit"]["message"])

    embed.set_author(name=repo_full_name)

    commits = data["commits"]

    embed.add_field(name=commits[0]["message"],
                    value=str(
                        "[Link to commit](" + commits[0]["url"] + ")\n✅ " + str(len(commits[0]["added"])) + " ❌ " + str(
                            len(commits[0]["removed"])) + " 📝 " + str(len(commits[0]["modified"]))), inline=False)

    if len(commits) > 1:
        commits = commits[1:]

        for commit in commits:
            embed.add_field(name=commit["message"],
                            value=str(
                                "[Link to commit](" + commit["url"] + ")\n✅ " + str(len(commit["added"])) + " ❌ " + str(
                                    len(commit["removed"])) + " 📝 " + str(len(commit["modified"]))), inline=False)

    return embed


def contributer_added(data):
    repo_name = data["repository"]["full_name"]
    repo_full_name = str(data["repository"]["name"] + data["ref"].lstrip("refs/heads"))

    embed = discord.Embed(title=str("__**" + data["member"]["login"] + "**__ has been added to the Repository."),
                          colour=Config["action colours"]["Misc"], url=data["repository"]["url"], description=" ")

    embed.set_author(name=repo_full_name)
    return embed


def pull_request(data):
    repo_name = data["repository"]["full_name"]
    repo_full_name = str(data["repository"]["name"] + "/" + data["pull_request"]["head"]["ref"])

    embed = discord.Embed(title=str("Pull Request " + data["action"] + " by __**" + data["sender"]["login"] + "**__"),
                          colour=Config["action colours"]["PR"], url=data["repository"]["url"],
                          description=data["pull_request"]["title"])

    embed.set_author(name=repo_full_name)

    stats = str("[Link to PR](" + data["pull_request"]["url"] +
                ")\n📋 " + str(data["pull_request"]["commits"]) +
                "\n✅ " + str(data["pull_request"]["additions"]) +
                " ❌ " + str(data["pull_request"]["deletions"]) +
                " 📝 " + str(data["pull_request"]["changed_files"]))

    direction = str(data["pull_request"]["head"]["ref"] + " -> " + data["pull_request"]["base"]["ref"])
    embed.add_field(name=direction, value=stats)

    return embed


# SMR Lookup Embed Formats
def mod(name):
    # GraphQL Queries

    query = str('''{
      getMods(filter: { search: "''' + name + '''", order_by: last_version_date, order:desc}) {
        mods {
          name
          authors {
            user {
              username
            }
          }
          logo
          short_description
          full_description
          last_version_date
          id
        }
      }
    }''')
    data = requests.post("https://api.ficsit.app/v2/query", json={'query': query})
    data = json.loads(data.text)
    data = data["data"]["getMods"]["mods"]

    for mod in data:
        if mod["name"] == name:
            data = mod
            break
    if isinstance(data, list):
        if len(data) > 1:
            mod_list = ""
            for mod in data:
                mod_list = str(mod_list + mod["name"] + "\n")
            return mod_list, None
        elif len(data) == 0:
            return None, None
        else:
            data = data[0]
    date = str(data["last_version_date"][0:10] + " " + data["last_version_date"][11:19])

    embed = discord.Embed(title=data["name"],
                          colour=Config["action colours"]["Mod"], url=str("https://ficsit.app/mod/" + data["id"]),
                          description=str(data["short_description"] +
                                          "\n\n Last Updated: " + date +
                                          "\nCreated by: " + data["authors"][0]["user"]["username"]))

    embed.set_thumbnail(url=data["logo"])
    embed.set_author(name="ficsit.app Mod Lookup")
    return embed, data["full_description"]


def desc(full_desc):
    full_desc = Helper.formatDesc(full_desc[:1900])
    embed = discord.Embed(title="Description",
                          colour=Config["action colours"]["Mod"],
                          description=full_desc)
    embed.set_author(name="ficsit.app Mod Description")
    return embed


# Generic Bot Embed Formats
def command_list(guild, full=False):
    with open("Config.json", "r") as file:
        Config = json.load(file)

    embed = discord.Embed(title=str("What I do..."), colour=Config["action colours"]["Misc"])

    embed.add_field(name="**__Automated Responses__**",
                    value="*These commands trigger when one Keyword and one Additional Word are sent in a message.*",
                    inline=False)

    for command in Config["automated responses"]:
        keywords = ""
        words = "\n" + command["additional words"][0]
        del command["additional words"][0]

        for keyword in command["keywords"]:
            keywords = keywords + "\n" + keyword

        for word in command["additional words"]:
            words = words + ", " + word

        if command["ignore members"]:
            embed.add_field(name=str("**" + command["name"] + "**"), value=str(
                "Keywords:\n```" + keywords + "```Additional Words:\n```" + words + "```Response:\n```" + command[
                    "response"] + "```This response **ignores** anyone with T1+."), inline=False)
        else:
            embed.add_field(name=str("**" + command["name"] + "**"), value=str(
                "Keywords:\n```" + keywords + "```Additional Words:\n```" + words + "```Response:\n```" + command[
                    "response"] + "```This response applies to **everyone**."), inline=False)

    embed.add_field(name="**__Known Crashes__**",
                    value="*The bot respond to a post when a string is present in a message, pastebin, .txt/.log file or image.*",
                    inline=False)

    for command in Config["known crashes"]:
        embed.add_field(name=str("**" + command["name"] + "**"), value=str("Error:\n```" + command["crash"] + "```Response:\n```" + command["response"] + "```"),
                        inline=False)


    value = "*These channels only allow users to post files (inc. images).*\n"
    for id in Config["media only channels"]:
        value = value + guild.get_channel(id).mention + "\n"
    embed.add_field(name="**__Media Only Channels__**",value=value, inline=False)



    embed.add_field(name="**__Commands__**",
                    value="*These are normal commands that can be called by stating their name.*",
                    inline=False)

    for command in Config["commands"]:
        if command["media"]:
            embed.add_field(name=str("**" + Config["prefix"] + command["command"] + "**"), value="```An image is posted.```", inline=False)
        else:
            embed.add_field(name=str("**" + Config["prefix"] + command["command"] + "**"), value=str("```" + command["response"] + "```"),
                            inline=False)

    embed.add_field(name="**__Special Commands__**",
                    value="*These are special commands doing something else than just replying with a predetermined answer.*",
                    inline=False)


    for command in Config["special commands"]:
        embed.add_field(name=str("**" + Config["prefix"] + command["command"] + "**"), value=str("```" + command["response"] + "```"),
                        inline=False)

    if full:
        embed.add_field(name="**__Management Commands__**",
                        value="*These are commands to manage the bot and its automations.*",
                        inline=False)

        for command in Config["management commands"]:
            embed.add_field(name=str("**" + Config["prefix"] + command["command"] + "**"), value=str("```" + command["response"] + "```"),
                            inline=False)

        embed.add_field(name="**__Miscellaneous commands__**",
                        value="*It's all in the title.*",
                        inline=False)

        for command in Config["miscellaneous commands"]:
            embed.add_field(name=str("**" + Config["prefix"] + command["command"] + "**"), value=str("```" + command["response"] + "```"),
                            inline=False)

    return embed
