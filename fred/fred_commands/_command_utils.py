from typing import Type

from regex import E, match, escape

from ..config import Commands, Crashes, Misc


def search(table: Type[Commands | Crashes], pattern: str, force_fuzzy: bool) -> (str, bool):
    """Returns the top three results based on the result"""

    if not force_fuzzy and (exact_match := table.fetch(pattern)):
        return exact_match["name"], True

    fuzzy_pattern = rf"(?:{escape(pattern)}){{e<=2}}"
    fuzzies: list[str] = [item["name"] for item in table.fetch_all() if match(fuzzy_pattern, item["name"], flags=E)]

    return "`\n`".join(fuzzies[:5]), False


def get_search(table: Type[Commands | Crashes], pattern: str, force_fuzzy: bool) -> str:
    prefix = Misc.fetch("prefix") if table == Commands else ""
    searched, was_exact = search(table, pattern, force_fuzzy)
    response = f"Here's what I found: \n`{prefix}{searched}`"
    if was_exact:
        response += (
            f"\nIf this isn't what you are looking for, try " f"`{prefix}search {pattern} F`to attempt fuzzy matching!"
        )
    else:
        response += "\nThese were found by fuzzy matching. If it's not fuzzy enough, complain to Borketh#3347."

    return response
