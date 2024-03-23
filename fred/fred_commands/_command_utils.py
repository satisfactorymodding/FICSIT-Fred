from typing import Type
import logging

from regex import E, match, escape

from ._baseclass import BaseCmds
from config import Commands, Crashes, Misc


def search(table: Type[Commands | Crashes], pattern: str, column: str, force_fuzzy: bool) -> (str | list[str], bool):
    """Returns the top three results based on the result"""

    if column not in dir(table):
        raise KeyError(f"`{column}` is not a column in the {table.__name__} table!")

    if not force_fuzzy and (exact_match := table.fetch_by(column, pattern)):
        return exact_match[column], True

    fuzzy_pattern = rf".*(?:{escape(pattern)}){{e<={min(len(pattern) // 3, 6)}}}.*"
    fuzzies: list[str] = [
        item["name"]
        for item in table.fetch_all()
        if (item.get(column, None) is not None) and match(fuzzy_pattern, item[column], flags=E)
    ]
    BaseCmds.logger.info(fuzzies)
    return fuzzies[:5], False


def get_search(table: Type[Commands | Crashes], pattern: str, column: str, force_fuzzy: bool) -> str:
    prefix = Misc.fetch("prefix") if table == Commands else ""

    try:
        searched, was_exact = search(table, pattern, column, force_fuzzy)
        response = f"Here's what I found: "

        if searched:
            if was_exact:
                response += (
                    f"\n`{prefix}{searched}`\n "
                    "If this isn't what you are looking for, try "
                    f"`{prefix}search {table.__name__.lower()} {pattern} -fuzzy=true` to force fuzzy matching!"
                )
            else:
                response += (
                    f"\n`{prefix}"
                    + (f"`\n`{prefix}".join(searched))
                    + "\n` These were found by fuzzy matching. If it's not fuzzy enough, complain to Borketh#3347."
                )
        else:
            response = "Nothing could be found!"

    except KeyError as e:
        response = e.args[0]

    return response
