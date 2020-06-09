import discord
import datetime
import requests
import json
import Helper

with open("config/config.json", "r") as file:
    Config = json.load(file)




# Github Update Embed Formats
def run(data):
    embed = "Debug"
    try:
        global repo_name
        repo_name = data["repository"]["full_name"]
        global repo_full_name
        repo_full_name = str(data["repository"]["name"] + "/" + data["ref"].lstrip("refs/heads"))
    except:
        repo_name = "None"
        repo_full_name = "None"
    type = data["type"]
    if type == "push":
        embed = push(data)
    elif type == "pull_request":
        embed = pull_request(data)
    elif type == "member" and data["action"] == "added":
        embed = contributer_added(data)
    elif type == "release" and data["action"] == "published" and not data["release"]["draft"]:
        embed = release(data)
    elif type == "issue":
        embed = issue(data)
    else:
        print(data)
    return embed


def push(data):
    if data["forced"]:
        colour = Config["action colours"]["Red"]
        forced = "Forced "
    else:
        colour = Config["action colours"]["Green"]
        forced = ""

    if data["created"]:
        embed = create(data)
        return embed
    elif data["deleted"]:
        embed = delete(data)
        return embed

    commits = data["commits"]
    desc = ""
    for commit in commits:
        desc = desc + "[`" + commit["id"][:7] + "`](" + commit["url"] + ") " + commit["message"].split("\n")[0] + " - " + commit["committer"]["name"] + "\n✅ " + str(len(commit["added"])) + " ❌ " + str(len(commit["removed"])) + " 📝 " + str(len(commit["modified"])) + "\n"
    embed = discord.Embed(title= forced + "Pushed " + str(len(data["commits"])) + " commit(s) to " + repo_full_name,
                          colour=colour, url=data["compare"],
                          description=desc)

    embed.set_author(name=data["sender"]["login"], icon_url=data["sender"]["avatar_url"])


    return embed


def contributer_added(data):

    embed = discord.Embed(title=str("__**" + data["member"]["login"] + "**__ has been added to the Repository !"),
                          colour=Config["action colours"]["Green"], url=data["repository"]["html_url"], description=" ")

    embed.set_author(name=repo_full_name)
    return embed


def pull_request(data):
    action = data["action"]
    colour = Config["action colours"]["Orange"]
    if action == "opened":
        colour = Config["action colours"]["Green"]
    elif action == "review_requested":
        action = "review requested"
    elif action == "review_request_removed":
        action = "review request removed"
    elif action == "ready_for_review":
        action = "is ready for review"
    elif action == "synchronize":
        action = "review synchronized"
    elif action == "closed":
        if data["pull_request"]["merged"]:
            action = "merged"
            colour = Config["action colours"]["Green"]
        else:
            action = "closed without merging"
            colour = Config["action colours"]["Red"]
    embed = discord.Embed(title=str("Pull Request " + action + " in " + data["repository"]["full_name"]),
                          colour=colour, url=data["pull_request"]["html_url"],
                          description=data["pull_request"]["title"])

    embed.set_author(name=data["sender"]["login"], icon_url=data["sender"]["avatar_url"])

    stats = str("\n📋 " + str(data["pull_request"]["commits"]) +
                "\n✅ " + str(data["pull_request"]["additions"]) +
                " ❌ " + str(data["pull_request"]["deletions"]) +
                " 📝 " + str(data["pull_request"]["changed_files"]))

    direction = str(data["pull_request"]["head"]["ref"] + " -> " + data["pull_request"]["base"]["ref"])
    embed.add_field(name=direction, value=stats)

    embed.set_footer(text=Config["prefix"] + "legend to understand the emojis")

    return embed


def create(data):
    ref_type = data["ref"].split("/")[1]
    ref_name = data["ref"].split("/")[2]
    if ref_type == "tags":
        ref_type = "Tag"
    elif ref_type == "heads":
        ref_type = "Branch"
    else:
        ref_type = data["ref"]
    embed = discord.Embed(title=str(ref_type + " \"" + ref_name + "\"" + " created in " + repo_name),
                          colour=Config["action colours"]["Green"], url=data["repository"]["html_url"])

    embed.set_author(name=data["sender"]["login"], icon_url=data["sender"]["avatar_url"])

    return embed

def delete(data):
    ref_type = data["ref"].split("/")[1]
    ref_name = data["ref"].split("/")[2]
    embed = discord.Embed(title=str(ref_type + " \"" + ref_name + "\"" + " deleted in " + repo_name),
                          colour=Config["action colours"]["Red"], url=data["repository"]["html_url"])

    embed.set_author(name=data["sender"]["login"], icon_url=data["sender"]["avatar_url"])

    return embed

def release(data):

    if data["release"]["prerelease"]:
        state = "pre-release"
    else:
        state = "release"
    embed = discord.Embed(title= "A new " + state + " for " + data["repository"]["name"] + " is available !",
                          colour=Config["action colours"]["Green"], url=data["release"]["html_url"])

    embed.set_author(name=data["sender"]["login"], icon_url=data["sender"]["avatar_url"])

    return embed

def issue(data):

    colour = Config["action colours"]["Orange"]
    action = data["action"]
    if action == "opened":
        colour = Config["action colours"]["Green"]
    elif action == "deleted":
        colour = Config["action colours"]["Red"]

    embed = discord.Embed(title=data["action"].capitalize() + " issue #" + str(data["issue"]["number"]) + " in " + data["repository"]["full_name"],
                          colour=colour, url=data["issue"]["html_url"])
    embed.set_author(name=data["sender"]["login"], icon_url=data["sender"]["avatar_url"])

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
                          colour=Config["action colours"]["Light Blue"], url=str("https://ficsit.app/mod/" + data["id"]),
                          description=str(data["short_description"] +
                                          "\n\n Last Updated: " + date +
                                          "\nCreated by: " + data["authors"][0]["user"]["username"]))

    embed.set_thumbnail(url=data["logo"])
    embed.set_author(name="ficsit.app Mod Lookup")
    embed.set_footer(text="React with the clipboard to have the full description be sent to you")
    return embed, data["full_description"]


def desc(full_desc):
    full_desc = Helper.formatDesc(full_desc[:1900])
    embed = discord.Embed(title="Description",
                          colour=Config["action colours"]["Light Blue"],
                          description=full_desc)
    embed.set_author(name="ficsit.app Mod Description")
    return embed


# Generic Bot Embed Formats
def command_list(client, full=False):
    with open("config/config.json", "r") as file:
        Config = json.load(file)

    embed = discord.Embed(title=str("What I do..."), colour=Config["action colours"]["Purple"])

    embed.add_field(name="**__GitHook__**",
                    value="*I fetch payloads from Github and show relevant info in* " + client.get_channel(Config["githook channel"]).mention,
                    inline=False)

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
        value = value + client.get_channel(id).mention + "\n"
    embed.add_field(name="**__Media Only Channels__**",value=value, inline=False)



    embed.add_field(name="**__Commands__**",
                    value="*These are normal commands that can be called by stating their name.*",
                    inline=False)

    for command in Config["commands"]:
        if command["byPM"]:
            byPM = " (By Direct Message)"
        else:
            byPM = ""
        embed.add_field(name=str("**" + Config["prefix"] + command["command"] + "**"), value=str("```" + command["response"]+ "```" + byPM),
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
                        value="*Two 'hidden' commands who didn't fit in the embed.*",
                        inline=False)

    return embed
