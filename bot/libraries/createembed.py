import discord
import config
import requests
import json
import libraries.helper as Helper
import os
import shutil

line_return = '\n'  # needed later for f-strings because finicky interpreter

if not os.path.exists("../config/config.json"):
    shutil.copyfile("../config/config_example.json", "../config/config.json")
with open("../config/config.json", "r") as file:
    Config = json.load(file)


# Github Update Embed Formats
async def run(data, client):
    embed = "Debug"
    try:
        global repo_name
        repo_name = data["repository"]["full_name"]
        global repo_full_name
        repo_full_name = f'{data["repository"]["name"]}/{data["ref"].split("/")[2]}'
    except:
        repo_name = "None"
        repo_full_name = "None"
    try:
        data_type = data["type"]
    except KeyError:
        print("data didn't have a type field")
        return
    if data_type == "push":
        embed = push(data)
    elif data_type == "pull_request":
        embed = pull_request(data)
    elif data_type == "member" and data["action"] == "added":
        embed = contributer_added(data)
    elif data_type == "release" and not data["release"]["draft"] and data["action"] in ["released", "prereleased"]:
        embed = release(data)
    elif data_type == "issue":
        embed = issue(data)
    else:
        print(data)
    return embed


def leaderboard(data: list):
    desc = f"Here are the {len(data)} people with the highest xp count"

    embed = discord.Embed(title="XP Leaderboard", colour=config.ActionColours.fetch("purple"), description=desc)

    for user in data:
        embed.add_field(name=user["name"],
                        value=f'XP: {user["count_and_rank"]["count"]} | Level: {user["count_and_rank"]["rank"]}')

    return embed


def DM(text):
    embed = discord.Embed(colour=config.ActionColours.fetch("purple"), description=text)

    embed.set_footer(text="To stop getting DM messages from me, type 'stop'. "
                          "If you ever want to reactivate it, type 'start'")
    return embed


def push(data):
    if data["forced"]:
        colour = config.ActionColours.fetch("Red")
        forced = "Forced "
    else:
        colour = config.ActionColours.fetch("Green")
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
        desc = f'{desc}[`{commit["id"][:7]}`]({commit["url"]}) ' \
               f'{commit["message"].split(line_return)[0]} - {commit["committer"]["name"]}\n' \
               f'✅ {len(commit["added"])} ❌ {len(commit["removed"])} 📝 {len(commit["modified"])}\n'

    commitLength = len(commits)
    while len(desc) > 2030:
        commitLength -= 1
        desc = ""
        for commit in commits[:commitLength]:
            desc = f'{desc}[`{commit["id"][:7]}`]({commit["url"]}) ' \
                   f'{commit["message"].split(line_return)[0]} - {commit["committer"]["name"]}\n' \
                   f'✅ {len(commit["added"])} ❌ {len(commit["removed"])} 📝 {len(commit["modified"])}\n'

    if commitLength != len(commits):
        desc = f'{desc}\n And {len(commits) - commitLength} more...'

    embed = discord.Embed(title=f'{forced} Pushed {len(data["commits"])} commit(s) to {repo_full_name}',
                          colour=colour,
                          url=data["compare"],
                          description=desc)

    embed.set_author(name=data["sender"]["login"], icon_url=data["sender"]["avatar_url"])

    return embed


def contributer_added(data):
    embed = discord.Embed(title=f'__**{data["member"]["login"]}**__ has been added to the Repository!',
                          colour=config.ActionColours.fetch("Green"),
                          url=data["repository"]["html_url"],
                          description=" ")

    embed.set_author(name=repo_full_name)
    return embed


def pull_request(data):
    action = data["action"]
    colour = config.ActionColours.fetch("Orange")
    if action == "opened":
        colour = config.ActionColours.fetch("Green")
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
            colour = config.ActionColours.fetch("Green")
        else:
            action = "closed without merging"
            colour = config.ActionColours.fetch("Red")
    embed = discord.Embed(title=f'Pull Request {action} in {data["repository"]["full_name"]}',
                          colour=colour,
                          url=data["pull_request"]["html_url"],
                          description=data["pull_request"]["title"])

    embed.set_author(name=data["sender"]["login"], icon_url=data["sender"]["avatar_url"])

    stats = f'\n📋 {data["pull_request"]["commits"]}' \
            f'\n✅ {data["pull_request"]["additions"]}' \
            f'\n❌ {data["pull_request"]["deletions"]}' \
            f'\n📝 {data["pull_request"]["changed_files"]}'

    direction = f'{data["pull_request"]["head"]["ref"]} -> {data["pull_request"]["base"]["ref"]}'
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
    embed = discord.Embed(title=f'{ref_type} "{ref_name}" created in {repo_name}',
                          colour=config.ActionColours.fetch("Green"),
                          url=data["repository"]["html_url"])

    embed.set_author(name=data["sender"]["login"], icon_url=data["sender"]["avatar_url"])

    return embed


def delete(data):
    ref_type = data["ref"].split("/")[1]
    ref_name = data["ref"].split("/")[2]
    embed = discord.Embed(title=f'{ref_type} "{ref_name}" deleted in {repo_name}',
                          colour=config.ActionColours.fetch("Red"),
                          url=data["repository"]["html_url"])

    embed.set_author(name=data["sender"]["login"], icon_url=data["sender"]["avatar_url"])

    return embed


def release(data):
    if data["release"]["prerelease"]:
        state = "pre-release"
    else:
        state = "release"
    embed = discord.Embed(title=f'A new {state} for {data["repository"]["name"]} is available!',
                          colour=config.ActionColours.fetch("Green"),
                          url=data["release"]["html_url"])

    embed.set_author(name=data["sender"]["login"], icon_url=data["sender"]["avatar_url"])

    return embed


def issue(data):
    colour = config.ActionColours.fetch("Orange")
    action = data["action"]
    if action == "opened":
        colour = config.ActionColours.fetch("Green")
    elif action == "deleted":
        colour = config.ActionColours.fetch("Red")

    embed = discord.Embed(
        title=f'{data["action"].capitalize()} issue #{data["issue"]["number"]} in {data["repository"]["full_name"]}',
        colour=colour,
        url=data["issue"]["html_url"])
    embed.set_author(name=data["sender"]["login"], icon_url=data["sender"]["avatar_url"])

    return embed


# SMR Lookup Embed Formats
async def mod(name, session):
    # GraphQL Queries
    query = str('''{
          getMods(filter: { search: "''' + name + '''", order_by: search, order:desc, limit:100}) {
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
    result = await Helper.repository_query(query, session)
    data = result["data"]["getMods"]["mods"]

    for mod in data:
        if mod["name"].lower() == name.lower():
            data = mod
            break
    if isinstance(data, list):
        if len(data) > 1:
            cut = False
            if len(data) > 10:
                cut = len(data) - 10
                data = data[:10]
            desc = ""
            for mod in data:
                desc = f'{desc}{mod["name"]}[™](https://ficsit.app/mod/{mod["id"]})\n'
            if cut:
                desc += f"\n*And {cut} more...*"
            embed = discord.Embed(title="Multiple mods found:",
                                  colour=config.ActionColours.fetch("Light Blue"),
                                  description=desc)
            embed.set_author(name="ficsit.app Mod Lookup")
            embed.set_thumbnail(url="https://ficsit.app/static/assets/images/no_image.png")
            embed.set_footer(text="Click™ on the TM™ to open the link™ to the mod™ page on SMR™")
            return embed, None
        elif len(data) == 0:
            return None, None
        else:
            data = data[0]
    date = f'{data["last_version_date"][0:10]} {data["last_version_date"][11:19]}'

    embed = discord.Embed(title=data["name"],
                          colour=config.ActionColours.fetch("Light Blue"),
                          url=str("https://ficsit.app/mod/" + data["id"]),
                          description=f'{data["short_description"]}\n\n Last Updated: {date}\n'
                                      f'Created by: {data["authors"][0]["user"]["username"]}')

    embed.set_thumbnail(url=data["logo"])
    embed.set_author(name="ficsit.app Mod Lookup")
    embed.set_footer(text="React with the clipboard to have the full description be sent to you")
    return embed, data["full_description"]


def desc(full_desc):
    full_desc = Helper.formatDesc(full_desc[:1900])
    embed = discord.Embed(title="Description",
                          colour=config.ActionColours.fetch("Light Blue"),
                          description=full_desc)
    embed.set_author(name="ficsit.app Mod Description")
    return embed


# Generic Bot Embed Formats
def command_list(client, full=False, here=False):
    desc = f'**__GitHook__**\n*I fetch payloads from Github and show relevant info in* ' \
           f'{client.get_channel(client.config["githook channel"]).mention}\n\n'

    desc = desc + """**__Special Commands__**
    *These are special commands doing something else than just replying with a predetermined answer.*

    """

    for command in client.config["special commands"]:
        desc = f'{desc}**{client.config["prefix"]}{command["command"]}**\n```{command["response"]}```\n'

    desc = f'{desc}\n**__Media Only Channels__**\n*These channels only allow users to post files (inc. images).*\n'
    for id in client.config["media only channels"]:
        desc = f'{desc}{client.get_channel(id).mention}\n'

    specialities = discord.Embed(title=str("What I do..."),
                                 colour=client.config.ActionColours.fetch("Purple"),
                                 description=desc)

    if here:
        specialities.set_footer(text="Please do not spam the reactions for this embed to work properly.")
    else:
        specialities.set_footer(text="Please do not spam the reactions for this embed to work properly. Also, since I "
                                     "cannot remove your reactions in direct messages, "
                                     "navigation in here could be a little weird")

    desc = """**__Known Crashes__**
    *The bot respond to a post when a string is present in a message, pastebin, .txt/.log file or image.*

    """

    for command in client.config["known crashes"]:
        desc = f'{desc}**{command["name"]}**\nError:\n{command["crash"]}```Response:\n{command["response"]}```'

    crashes = discord.Embed(title=str("What I do..."),
                            colour=client.config.ActionColours.fetch("Purple"),
                            description=desc)

    if here:
        crashes.set_footer(text="Please do not spam the reactions for this embed to work properly.")
    else:
        crashes.set_footer(text="Please do not spam the reactions for this embed to work properly. Also, since I "
                                "cannot remove your reactions in direct messages, navigation in here could be a "
                                "little weird")

    commands = []
    desc = ""
    half = int(len(client.config["commands"]) / 2)
    for command in client.config["commands"][:half]:
        if command["byPM"]:
            byPM = " (By Direct Message)"
        else:
            byPM = ""
        desc = f'{desc}**{client.config["prefix"]}{command["command"]}**\n```{command["response"]}```{byPM}\n'

    commands.append(discord.Embed(title=str("What I do..."),
                                  colour=client.config.ActionColours.fetch("Purple"),
                                  description=desc))
    desc = ""
    for command in client.config["commands"][half:]:
        if command["byPM"]:
            byPM = " (By Direct Message)"
        else:
            byPM = ""
        desc = f'{desc}**{client.config["prefix"]}{command["command"]}**\n```{command["response"]}```{byPM}\n'

    commands.append(discord.Embed(title=str("What I do..."),
                                  colour=client.config.ActionColours.fetch("Purple"),
                                  description=desc))

    for command in commands:
        command.description = f"**__Commands__**\n*These are normal commands that can be called " \
                              f"by stating their name.*\n\n{command.description}"
        if here:
            command.set_footer(text="Please do not spam the reactions for this embed to work properly.")
        else:
            command.set_footer(text="Please do not spam the reactions for this embed to work properly. "
                                    "Also, since I cannot remove your reactions in direct messages, "
                                    "navigation in here could be a little weird")

    if full:
        desc = "**__Management Commands__**\n*These are commands to manage the bot and its automations.*\n\n"

        for command in client.config["management commands"]:
            desc = f'{desc}**{client.config["prefix"]}{command["command"]}**\n```{command["response"]}```\n'

        management = discord.Embed(title=str("What I do..."),
                                   colour=client.config.ActionColours.fetch("Purple"),
                                   description=desc)

        if here:
            management.set_footer(text="Please do not spam the reactions for this embed to work properly.")
        else:
            management.set_footer(text="Please do not spam the reactions for this embed to work properly. "
                                       "Also, since I cannot remove your reactions in direct messages, "
                                       "navigation in here could be a little weird")

        desc = "**__Miscellaneous commands__**\n*It's all in the title*\n\n"

        for command in client.config["miscellaneous commands"]:
            desc = f'{desc}**{client.config["prefix"]}{command["command"]}**\n```{command["response"]}```'

        desc = desc + "**__Additional information__**\n" \
                      "This info is relevant if you are an engineer or above, " \
                      "which you should be if you are seeing this page.\n\n" \
                      "```*You can react to any of the bot's message with ❌ to remove it\n" \
                      " *You can add 'here' after the help command " \
                      "to send the embed in the channel you typed the command in. " \
                      "This will make the embed not be full by default, " \
                      "but you can override that by adding another argument, 'full'```"

        misc = discord.Embed(title=str("What I do..."),
                             colour=client.config.ActionColours.fetch("Purple"),
                             description=desc)
        if here:
            misc.set_footer(text="Please do not spam the reactions for this embed to work properly.")
        else:
            misc.set_footer(text="Please do not spam the reactions for this embed to work properly. "
                                 "Also, since I cannot remove your reactions in direct messages, "
                                 "navigation in here could be a little weird")
    else:
        management = False
        misc = False

    return [specialities, crashes, commands[0], commands[1], management, misc]


def crashes(responses: list[tuple[str, str]]) -> discord.Embed:
    embed = discord.Embed(
        title=f"{len(responses)} automated responses found: ",
        colour=config.ActionColours.fetch("Purple")
    )
    for title, response in responses:
        embed.add_field(name=title, value=response)
    return embed
