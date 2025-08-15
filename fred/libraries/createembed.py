from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import TYPE_CHECKING, Optional
from urllib.parse import quote as url_safe

import nextcord
from PIL import Image
from attr import dataclass
from nextcord.utils import format_dt

from .. import config

if TYPE_CHECKING:
    from ..fred import Bot
from ..libraries import common

logger = common.new_logger(__name__)


def timestamp(iso8601: str) -> str:
    return format_dt(datetime.fromisoformat(iso8601), "R")


repo_name, repo_full_name = "", ""


# GitHub Update Embed Formats
async def github_embed(data: dict) -> nextcord.Embed | None:
    embed = None

    global repo_name, repo_full_name
    try:
        repo_name = data["repository"]["full_name"]
        repo_full_name = f'{data["repository"]["name"]}/{data["ref"].split("/")[2]}'
    except (KeyError, IndexError):
        repo_name, repo_full_name = "", ""

    if (data_type := data.get("type")) is None:
        logger.error("data didn't have a type field")
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
            logger.warning("Unsupported GitHub payload", extra={"data": data})
    return embed


def leaderboard(data: list[dict]) -> nextcord.Embed:
    desc = f"Here are the {len(data)} people with the highest xp count"

    embed = nextcord.Embed(title="XP Leaderboard", colour=config.ActionColours.fetch("purple"), description=desc)

    for user in data:
        embed.add_field(name=user["name"], value=f'XP: {user["xp"]} | Level: {user["rank"]}')

    return embed


def DM(text: str) -> nextcord.Embed:
    embed = nextcord.Embed(colour=config.ActionColours.fetch("purple"), description=text)

    embed.set_footer(
        text="To stop getting DM messages from me, type 'stop'. " "If you ever want to reactivate it, type 'start'"
    )
    return embed


def format_commit(commit: dict) -> tuple[str, str]:
    hash_id = f'`{commit["id"][:8]}`'
    commit_message = commit["message"].split("\n")[0].replace("*", r"\*")
    author = commit["committer"]
    attribution = f'[{author["name"]}](https://github.com/{author["username"]})'
    ts = timestamp(commit["timestamp"])
    change_summary_icons = " ".join(
        [f"{em} {len(commit[k])}" for em, k in zip("✅❌📝", ["added", "removed", "modified"])]
    )
    return f"{commit_message}\n", f'{change_summary_icons} - by {attribution} {ts} [{hash_id}]({commit["url"]})\n'


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

    embed = nextcord.Embed(
        title=f"{forced}Pushed {len(commits)} commit(s) to {repo_full_name}",
        colour=colour,
        url=data["compare"],
        description="",
    )

    for commit in commits[:24]:
        title, details = format_commit(commit)
        embed.add_field(name=title, value=details, inline=False)

    if not_shown := len(commits[24:]):
        embed.add_field(name=f"{not_shown} commits not shown", value="See GitHub for more details!", inline=False)

    embed.set_author(name=data["sender"]["login"], icon_url=data["sender"]["avatar_url"])
    embed.set_footer(text="Use the `" + config.Misc.fetch("prefix") + "legend` to learn what the icons mean!")
    return embed


def contributor_added(data: dict) -> nextcord.Embed:
    embed = nextcord.Embed(
        title=f'__**{data["member"]["login"]}**__ has been added to the Repository!',
        colour=config.ActionColours.fetch("Green"),
        url=data["repository"]["html_url"],
        description=" ",
    )

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

    embed = nextcord.Embed(
        title=f'Pull Request {action} in {data["repository"]["full_name"]}',
        colour=colour,
        url=data["pull_request"]["html_url"],
        description=data["pull_request"]["title"],
    )

    embed.set_author(name=data["sender"]["login"], icon_url=data["sender"]["avatar_url"])

    stats = "\n".join(
        [
            f'📋 {data["pull_request"]["commits"]}',
            f'✅ {data["pull_request"]["additions"]}',
            f'❌ {data["pull_request"]["deletions"]}',
            f'📝 {data["pull_request"]["changed_files"]}',
        ]
    )

    direction = f'{data["pull_request"]["head"]["ref"]} -> {data["pull_request"]["base"]["ref"]}'
    embed.add_field(name=direction, value=stats)

    embed.set_footer(text="Use the `" + config.Misc.fetch("prefix") + "legend` to learn what the icons mean!")

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

    embed = nextcord.Embed(
        title=f'{ref_type} "{ref_name}" created in {repo_name}',
        colour=config.ActionColours.fetch("Green"),
        url=data["repository"]["html_url"],
    )

    embed.set_author(name=data["sender"]["login"], icon_url=data["sender"]["avatar_url"])

    return embed


def delete(data: dict) -> nextcord.Embed:
    _, ref_type, ref_name = data["ref"].split("/")
    embed = nextcord.Embed(
        title=f'{ref_type} "{ref_name}" deleted in {repo_name}',
        colour=config.ActionColours.fetch("Red"),
        url=data["repository"]["html_url"],
    )

    embed.set_author(name=data["sender"]["login"], icon_url=data["sender"]["avatar_url"])

    return embed


def release(data: dict) -> nextcord.Embed:
    state = "pre-release" if data["release"]["prerelease"] else "release"
    embed = nextcord.Embed(
        title=f'A new {state} for {data["repository"]["name"]} is available!',
        colour=config.ActionColours.fetch("Green"),
        url=data["release"]["html_url"],
    )

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
        url=data["issue"]["html_url"],
    )

    author = data["sender"]
    embed.set_author(name=author["login"], icon_url=author["avatar_url"])

    return embed


def issue_comment(data: dict) -> nextcord.Embed:
    author = data["comment"]["user"]
    embed = nextcord.Embed(
        title=f'{author["login"]} commented on issue #{data["issue"]["number"]}',
        description=f'{data["comment"]["body"]}',
        url=data["comment"]["url"],
        colour=config.ActionColours.fetch("yellow"),
    )

    embed.set_thumbnail(author["avatar_url"])
    return embed


def _single_mod_embed(mod: dict) -> nextcord.Embed:
    if (zulu_time := mod.get("last_version_date")) and len(mod.get("versions")) > 0:
        ts = timestamp(f"{zulu_time[:19]}+00:00")
    else:
        ts = ""

    *preceding, last = map(lambda a: a["user"]["username"], mod["authors"])

    if preceding:
        # gotta get that proper grammar
        joiner = ", and " if len(preceding) > 1 else " and "
        authors = ", ".join(preceding) + joiner + last
    else:
        authors = last

    desc = mod["short_description"] + "\n"

    if compatibility := mod["compatibility"]:
        ea = compatibility["EA"]
        exp = compatibility["EXP"]
        desc += f"\nEA: {compatibility_to_emoji(ea['state'])}\n"
        if note := ea["note"]:
            desc += f"Note: {note}\n"
        desc += f"EXP: {compatibility_to_emoji(exp['state'])}\n"
        if note := exp["note"]:
            desc += f"Note: {note}\n"

    desc += f"\nLast Updated {ts}" if ts else "\n(No versions available!)"
    desc += f"\nCreated by {authors}"

    return nextcord.Embed(
        title=mod["name"],
        description=desc,
        url=f'https://ficsit.app/mod/{mod["id"]}',
    )


def compatibility_to_emoji(compatibility_state: str) -> str:
    match compatibility_state:
        case "Works":
            return ":white_check_mark:"
        case "Damaged":
            return ":warning:"
        case "Broken":
            return ":no_entry_sign:"


def _multiple_mod_embed(original_query_name: str, mods: list[dict]) -> nextcord.Embed:
    desc = "\n".join([f'{mod["name"]}[™](https://ficsit.app/mod/{mod["id"]})' for mod in mods[:10]]) + (
        f"\n*And {cut} more...*" if (cut := len(mods[10:])) else ""
    )
    return nextcord.Embed(
        title="Multiple mods found:", description=desc, url=f"https://ficsit.app/mods?q={url_safe(original_query_name)}"
    )


async def webp_icon_as_png(url: str, bot: Bot) -> tuple[nextcord.File, str]:
    with BytesIO(await bot.async_url_get(url)) as virtual_webp, BytesIO() as virtual_png:
        webp_dat = Image.open(virtual_webp).convert("RGB")
        webp_dat.save(virtual_png, "png")
        virtual_png.seek(0)
        filename = f"{url.split('/')[-2]}.png".strip()
        file = nextcord.File(virtual_png, filename=filename)
    return file, filename  # this is out of the ctx manager to ensure the buffers are closed


# SMR Lookup Embed Formats
async def mod_embed(
    name: str, bot: Bot, using_id=False
) -> tuple[nextcord.Embed | None, nextcord.File | None, list[dict] | None]:
    # GraphQL Queries
    # fmt: off
    query_values = '''
    name
    authors {
        user {
          username
        }
    }
    logo
    short_description
    versions(filter: {limit: 1, order: desc}) {
        version
    }
    last_version_date
    id
    compatibility {
        EA {
          state
          note
        }
        EXP {
          state
          note
        }
    }
    '''
    if using_id:
        query = '''{
        getModByIdOrReference(modIdOrReference: "%s") {
            %s
        }
        }''' % (name, query_values)
    else:
        query = '''{
        getMods(filter: { search: "%s", order_by: search, order:desc, limit:100}) {
            mods {
                %s
            }
        }
        }''' % (name, query_values)
    # fmt: on
    result = await bot.repository_query(query)
    mods: list[dict] = [result["data"]["getModByIdOrReference"]] if using_id else result["data"]["getMods"]["mods"]
    # logger.debug(mods)
    if not mods:
        return None, None, None

    single_mod = len(mods) == 1 or (
        common.mod_name_eq(mods[0]["name"], name) and not common.mod_name_eq(mods[1]["name"], name)
    )
    if single_mod:
        # we have only one result, or only one near-exact match
        mod = mods[0]
        embed = _single_mod_embed(mod)
        logo = l if (l := mod["logo"]) else "https://ficsit.app/images/no_image.webp"
        file, filename = await webp_icon_as_png(logo, bot)
        thumb_url = f"attachment://{filename}"
        # thumb_url = logo
        footer = "If this isn't the mod you were looking for, try a different spelling."
    else:
        # we have a bunch of almost matches
        embed = _multiple_mod_embed(name, mods)
        thumb_url = "https://ficsit.app/static/assets/images/no_image.png"
        file = None
        footer = "Click™ on the TM™ to open the link™ to the mod™ page on SMR™"

    embed.set_thumbnail(url=thumb_url)
    embed.set_footer(text=footer)
    embed.set_author(name="Fred Mod Search™")
    multiple_mods = mods[:10] if not single_mod else None
    return embed, file, multiple_mods


@dataclass(unsafe_hash=True)
class CrashResponse:

    name: str
    value: str
    attachment: Optional[str | nextcord.File] = None
    inline: bool = False

    def add_self_as_field(self, embed: nextcord.Embed):
        logger.debug(self.value)
        embed.add_field(name=self.name, value=self.value, inline=self.inline)

    def __hash__(self):
        return hash(self.name)


def crashes(responses: list[CrashResponse]) -> nextcord.Embed:
    embed = nextcord.Embed(colour=config.ActionColours.fetch("Purple"))
    # sort the responses by size, so they display in a more efficient order
    responses = sorted(responses, key=lambda r: len(r.value), reverse=True)  # smaller = less important, can be cut

    for response in responses[:24]:
        response.add_self_as_field(embed)

    if unsaid := responses[24:]:
        embed.add_field(
            name=f"And {len(unsaid)} more that don't fit here...",
            value=", ".join(r.name for r in unsaid) + "\nuse `help crash [name]` to see what they are",
        )

    return embed
