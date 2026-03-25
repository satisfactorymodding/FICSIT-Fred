from typing import Type

from regex import ENHANCEMATCH, escape, search as re_search

from ..config import Commands, Crashes, Misc
from ..libraries.common import new_logger

logger = new_logger("[Command/Crash Search]")


def search(
    table: Type[Commands | Crashes], pattern: str, column: str, force_fuzzy: bool
) -> tuple[str | list[str], bool]:
    """Returns the top three results based on the result"""

    if column not in dir(table):
        raise KeyError(f"`{column}` is not a column in the {table.__name__} table!")

    if not force_fuzzy and (exact_match := table.fetch_by(column, pattern)):
        return exact_match[column], True

    if len(pattern) < 2:
        raise KeyError("Search pattern must be at least 2 characters long for fuzzy searching!")

    # Set fuzzy range - (1/3 pattern length, max 6)
    max_edits = min(len(pattern) // 3, 6)
    substring_pattern = rf".*(?:{escape(pattern)}){{e<={max_edits}}}.*"

    scored_results: list[tuple[int, str]] = []
    for item in table.fetch_all():
        value = item.get(column)

        # Filter non matching strings
        if not isinstance(value, str):
            continue
        if not re_search(substring_pattern, value, flags=ENHANCEMATCH):
            continue

        # add levenshtein score
        score = levenshtein(pattern, value)
        scored_results.append((score, item["name"]))

    # Sort by score, then alphabetically
    scored_results.sort(key=lambda x: (x[0], x[1]))
    results = [name for _, name in scored_results]

    # Return all results fitting fuzzy range
    logger.info(results)
    return results, False


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


# Levenshtein distance algorithm
def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    la, lb = len(a), len(b)
    if la == 0:
        return lb
    if lb == 0:
        return la

    prev = list(range(lb + 1))
    for i, ca in enumerate(a, start=1):
        cur = [i] + [0] * lb
        for j, cb in enumerate(b, start=1):
            ins = cur[j - 1] + 1
            delete = prev[j] + 1
            sub = prev[j - 1] + (0 if ca == cb else 1)
            cur[j] = min(ins, delete, sub)
        prev = cur
    return prev[lb]
