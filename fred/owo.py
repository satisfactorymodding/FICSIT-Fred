import re

owo_table = {
    r"th([aeiou])": r"d\1",
    r"Th([aeiou])": r"D\1",
    r"oo": r"uwu",
    r"r": r"w",
    r"R": r"W",
    r"ove": r"uv",
    r"!": r"! OwO ",
    r"(?<![aeiou])n([aeiou])": r"ny\1",
    r"(?<![aeiou])N([aeiou])": r"Ny\1",
    r"you": "u",
    r"You": "U",
}


def owoize(string: str) -> str:
    new_string: list[str] = []
    for line in string.split('\n'):
        new_line: list[str] = []
        for word in line.split():
            if "http" not in word:
                for match, sub in owo_table.items():
                    word = re.sub(match, sub, word)
            new_line.append(word)
        new_string.append(" ".join(new_line))

    return "\n".join(new_string)
