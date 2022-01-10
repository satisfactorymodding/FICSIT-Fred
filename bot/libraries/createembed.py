from fred_core_imports import *
from libraries import common

from datetime import datetime


def timestamp(iso8601: str) -> str:
    unix_time: int = int(datetime.fromisoformat(iso8601).timestamp())
    return f"<t:{unix_time}:R>"


# GitHub Update Embed Formats
async def run(data: dict) -> nextcord.Embed | None:
    embed = None

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
        logging.error("data didn't have a type field")
        return

    match data_type:
        case "push":
            embed = push(data)
        case "pull_request":
            embed = pull_request(data)
        case "member":
            if data["action"] == "added":
                embed = contributor_added(data)
        case "release":
            if not data["release"]["draft"] and data["action"] in ["released", "prereleased"]:
                embed = release(data)
        case "issue":
            embed = issue(data)
        case _:
            logging.warning("Unsupported GitHub payload", extra={'data': data})
    return embed


def leaderboard(data: list[dict]) -> nextcord.Embed:
    desc = f"Here are the {len(data)} people with the highest xp count"

    embed = nextcord.Embed(title="XP Leaderboard", colour=config.ActionColours.fetch("purple"), description=desc)

    for user in data:
        embed.add_field(name=user["name"],
                        value=f'XP: {user["count_and_rank"]["count"]} | Level: {user["count_and_rank"]["rank"]}')

    return embed


def DM(text: str) -> nextcord.Embed:
    embed = nextcord.Embed(colour=config.ActionColours.fetch("purple"), description=text)

    embed.set_footer(text="To stop getting DM messages from me, type 'stop'. "
                          "If you ever want to reactivate it, type 'start'")
    return embed


def format_commit(commit: dict) -> tuple[str, str]:
    hash_id = f'`{commit["id"][:8]}`'
    commit_message = commit['message'].split('\n')[0].replace("*", "\*")
    author = commit["committer"]
    attribution = f'[{author["name"]}](https://github.com/{author["username"]})'
    ts = timestamp(commit["timestamp"])
    change_summary_icons = ' '.join([f'{em} {len(commit[k])}' for em, k in zip("✅❌📝", ["added", "removed", "modified"])])
    return (f'{commit_message}\n',
            f'{change_summary_icons} - by {attribution} {ts} [{hash_id}]({commit["url"]})\n')


def push(data: dict) -> nextcord.Embed:
    if data["forced"]:
        colour = config.ActionColours.fetch("Red")
        forced = "Force "
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

    embed = nextcord.Embed(title=f'{forced}Pushed {len(commits)} commit(s) to {repo_full_name}',
                          colour=colour,
                          url=data["compare"],
                          description='')

    for commit in commits[:24]:
        title, details = format_commit(commit)
        embed.add_field(name=title, value=details, inline=False)

    if not_shown := len(commits[24:]):
        embed.add_field(name=f"{not_shown} commits not shown", 
                        value="See GitHub for more details!",
                        inline=False)

    embed.set_author(name=data["sender"]["login"], icon_url=data["sender"]["avatar_url"])
    embed.set_footer(text=config.Misc.fetch("prefix") + "legend to understand the emojis")
    return embed


def contributor_added(data: dict) -> nextcord.Embed:
    embed = nextcord.Embed(title=f'__**{data["member"]["login"]}**__ has been added to the Repository!',
                          colour=config.ActionColours.fetch("Green"),
                          url=data["repository"]["html_url"],
                          description=" ")

    embed.set_author(name=repo_full_name)
    return embed


def pull_request(data: dict) -> nextcord.Embed:
    action = data["action"]
    colour = config.ActionColours.fetch("Orange")
    match action:
        case "opened":
            colour = config.ActionColours.fetch("Green")
        case "review_requested":
            action = "review requested"
        case "review_request_removed":
            action = "review request removed"
        case "ready_for_review":
            action = "is ready for review"
        case "synchronize":
            action = "review synchronized"
        case "closed":
            if data["pull_request"]["merged"]:
                action = "merged"
                colour = config.ActionColours.fetch("Green")
            else:
                action = "closed without merging"
                colour = config.ActionColours.fetch("Red")
        case _:
            raise ValueError("Pull request has invalid action!")

    embed = nextcord.Embed(title=f'Pull Request {action} in {data["repository"]["full_name"]}',
                          colour=colour,
                          url=data["pull_request"]["html_url"],
                          description=data["pull_request"]["title"])

    embed.set_author(name=data["sender"]["login"], icon_url=data["sender"]["avatar_url"])

    stats = f'''
            📋 {data["pull_request"]["commits"]}
            ✅ {data["pull_request"]["additions"]}
            ❌ {data["pull_request"]["deletions"]}
            📝 {data["pull_request"]["changed_files"]}
            '''

    direction = f'{data["pull_request"]["head"]["ref"]} -> {data["pull_request"]["base"]["ref"]}'
    embed.add_field(name=direction, value=stats)

    embed.set_footer(text=config.Misc.fetch("prefix") + "legend to understand the emojis")

    return embed


def create(data: dict) -> nextcord.Embed:
    _, ref_type, ref_name = data["ref"].split("/")
    match ref_type:
        case "tags":
            ref_type = "Tag"
        case "heads":
            ref_type = "Branch"
        case _:
            ref_type = data["ref"]

    embed = nextcord.Embed(title=f'{ref_type} "{ref_name}" created in {repo_name}',
                          colour=config.ActionColours.fetch("Green"),
                          url=data["repository"]["html_url"])

    embed.set_author(name=data["sender"]["login"], icon_url=data["sender"]["avatar_url"])

    return embed


def delete(data: dict) -> nextcord.Embed:
    _, ref_type, ref_name = data["ref"].split("/")
    embed = nextcord.Embed(title=f'{ref_type} "{ref_name}" deleted in {repo_name}',
                          colour=config.ActionColours.fetch("Red"),
                          url=data["repository"]["html_url"])

    embed.set_author(name=data["sender"]["login"], icon_url=data["sender"]["avatar_url"])

    return embed


def release(data: dict) -> nextcord.Embed:
    state = "pre-release" if data['release']['prerelease'] else "release"
    embed = nextcord.Embed(title=f'A new {state} for {data["repository"]["name"]} is available!',
                          colour=config.ActionColours.fetch("Green"),
                          url=data["release"]["html_url"])

    embed.set_author(name=data["sender"]["login"], icon_url=data["sender"]["avatar_url"])

    return embed


def issue(data: dict) -> nextcord.Embed:
    match action := data["action"]:
        case "opened":
            colour = config.ActionColours.fetch("Green")
        case "deleted":
            colour = config.ActionColours.fetch("Red")
        case _:
            colour = config.ActionColours.fetch("Orange")

    embed = nextcord.Embed(
        title=f'{action.capitalize()} issue #{data["issue"]["number"]} in {data["repository"]["full_name"]}',
        colour=colour,
        url=data["issue"]["html_url"])

    embed.set_author(name=data["sender"]["login"], icon_url=data["sender"]["avatar_url"])

    return embed


# SMR Lookup Embed Formats
async def mod(name: str, bot) -> (nextcord.Embed, str):
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
    result = await common.repository_query(query, bot)
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

            embed = nextcord.Embed(title="Multiple mods found:",
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

    embed = nextcord.Embed(title=data["name"],
                          colour=config.ActionColours.fetch("Light Blue"),
                          url=str("https://ficsit.app/mod/" + data["id"]),
                          description=f'{data["short_description"]}\n\n Last Updated: {date}\n'
                                      f'Created by: {data["authors"][0]["user"]["username"]}')

    embed.set_thumbnail(url=data["logo"])
    embed.set_author(name="ficsit.app Mod Lookup")
    embed.set_footer(text="React with the clipboard to have the full description be sent to you")
    return embed, data["full_description"]


def desc(full_desc: str) -> nextcord.Embed:
    full_desc = common.formatDesc(full_desc[:1900])
    embed = nextcord.Embed(title="Description",
                          colour=config.ActionColours.fetch("Light Blue"),
                          description=full_desc)
    embed.set_author(name="ficsit.app Mod Description")
    return embed


def crashes(responses: list[dict]) -> nextcord.Embed:
    embed = nextcord.Embed(
        title=f"{len(responses)} automated responses found: ",
        colour=config.ActionColours.fetch("Purple")
    )
    # sort the responses by size, so they display in a more efficient order
    responses = sorted(responses, key=lambda r: len(r['value']), reverse=True)  # smaller = less important, can be cut

    for response in responses[:24]:
        embed.add_field(**response)
        
    if unsaid := responses[24:]:
        embed.add_field(name=f"And {len(unsaid)} more that don't fit here...",
                        value=", ".join(r['name'] for r in unsaid) + "\nuse `help crash [name]` to see what they are")
    
    return embed
