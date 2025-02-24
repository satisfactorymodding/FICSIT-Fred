from __future__ import annotations

import regex as re

owo_table = {
    r"\bth([aeiou])": r"d\1",
    r"\bTh([aeiou])": r"D\1",
    r"oo": r"uwu",
    r"r": r"w",
    r"R": r"W",
    r"ove": r"uv",
    r"!": r":3",
    r"(?<![aeiou])([Nn])([aeiou])": r"\1y\2",
    r"you": "u",
    r"You": "U",
    r"fuzzy": r"fuzzy-wuzzy",
}


def owoize(string: str) -> str:
    new_string: list[str] = []
    for line in string.split("\n"):
        new_line: list[str] = []
        for word in line.split():
            if re.match(r"://|`", word) is None:
                for match, sub in owo_table.items():
                    word = re.sub(match, sub, word)
            new_line.append(word)
        new_string.append(" ".join(new_line))

    return "\n".join(new_string)
