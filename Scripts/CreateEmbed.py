import discord
import datetime
import requests
import json
import Helper
import os
import shutil

if not os.path.exists("config/config.json"):
    shutil.copyfile("../config_example.json", "config/config.json")
with open("config/config.json", "r") as file:
    Config = json.load(file)




# Github Update Embed Formats
async def run(data, client):
    embed = "Debug"
    try:
        global repo_name
        repo_name = data["repository"]["full_name"]
        global repo_full_name
        repo_full_name = str(data["repository"]["name"] + "/" + data["ref"].lstrip("refs/heads"))
    except:
        repo_name = "None"
        repo_full_name = "None"
    try:
        type = data["type"]
    except KeyError:
        print("data didn't have a type field")
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
                          colour=Config["action colours"]["Light Blue"],
                          url=str("https://ficsit.app/mod/" + data["id"]),
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
def command_list(client, full=False, here=False):

    desc = "**__GitHook__**\n*I fetch payloads from Github and show relevant info in* " + client.get_channel(
                        client.config["githook channel"]).mention + "\n\n"

    desc = desc + "**__Special Commands__**\n*These are special commands doing something else than just replying with a predetermined answer.*\n\n"

    for command in client.config["special commands"]:
        desc = desc + "**" + client.config["prefix"] + command["command"] + "**\n```" + command["response"] + "```"

    desc = desc + "**__Known Crashes__**\n*The bot respond to a post when a string is present in a message, pastebin, .txt/.log file or image.*\n\n"

    for command in client.config["known crashes"]:
        desc = desc + "**" + command["name"] + "**\nError:\n```" + command["crash"] + "```Response:\n```" + command["response"] + "```"


    desc = desc + "\n**__Media Only Channels__**\n*These channels only allow users to post files (inc. images).*\n"
    for id in client.config["media only channels"]:
        desc = desc + client.get_channel(id).mention + "\n"

    specialities = discord.Embed(title=str("What I do..."), colour=client.config["action colours"]["Purple"],
                                 description=desc)

    if here:
        specialities.set_footer(text="Please do not spam the reactions for this embed to work properly.")
    else:
        specialities.set_footer(text="Please do not spam the reactions for this embed to work properly. Also, since I "
                             "cannot remove your reactions in direct messages, navigation in here could be a "
                             "little weird")

    desc = "**__Commands__**\n*These are normal commands that can be called by stating their name.*\n\n"

    for command in client.config["commands"]:
        if command["byPM"]:
            byPM = " (By Direct Message)"
        else:
            byPM = ""
        desc = desc + "**" + client.config["prefix"] + command["command"] + "**\n```" + command["response"]+ "```" + byPM + "\n"

    commands = discord.Embed(title=str("What I do..."), colour=client.config["action colours"]["Purple"],
                                 description=desc)

    if here:
        commands.set_footer(text="Please do not spam the reactions for this embed to work properly.")
    else:
        commands.set_footer(text="Please do not spam the reactions for this embed to work properly. Also, since I "
                             "cannot remove your reactions in direct messages, navigation in here could be a "
                             "little weird")

    if full:
        desc = "**__Management Commands__**\n*These are commands to manage the bot and its automations.*\n\n"

        for command in client.config["management commands"]:
            desc = desc + "**" + client.config["prefix"] + command["command"] + "**\n```" + command["response"] + "```\n"

        management = discord.Embed(title=str("What I do..."), colour=client.config["action colours"]["Purple"],
                                 description=desc)

        if here:
            management.set_footer(text="Please do not spam the reactions for this embed to work properly.")
        else:
            management.set_footer(text="Please do not spam the reactions for this embed to work properly. Also, since I "
                                 "cannot remove your reactions in direct messages, navigation in here could be a "
                                 "little weird")

        desc = "**__Miscellaneous commands__**\n*It's all in the title*\n\n"

        for command in client.config["miscellaneous commands"]:
            desc = desc + "**" + client.config["prefix"] + command["command"] + "**\n```" + command["response"] + "```"

        desc = desc + "\n**__Additional information__**\nThis info is relevant if you are an engineer or above, which you should be if you are seeing this page.\n\n```*You can react to any of the bot's message with ❌ to remove it\n*You can add 'here' after the help command to send the embed in the channel you typed the command in. This will make the embed not be full by default, but you can override that by adding another argument, 'full'```"

        misc = discord.Embed(title=str("What I do..."), colour=client.config["action colours"]["Purple"],
                                 description=desc)
        if here:
            misc.set_footer(text="Please do not spam the reactions for this embed to work properly.")
        else:
            misc.set_footer(text="Please do not spam the reactions for this embed to work properly. Also, since I "
                                 "cannot remove your reactions in direct messages, navigation in here could be a "
                                 "little weird")
    else:
        management = False
        misc = False

    return [specialities, commands, management, misc]
