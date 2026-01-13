import asyncio
import re2
import re as regex_fallback

REGEX_LIMIT: float = 6.9

re2.set_fallback_module(regex_fallback)

def pattern_uses_lookaround(pattern: str) -> bool:
    return bool(regex_fallback.search(r"\(\?=|\(\?!|\(\?<=|\(\?<!", pattern))


async def re2_search_with_timeout(pattern: str, text: str, flags=0):
    try:
        return await asyncio.wait_for(asyncio.to_thread(re2.search, pattern, text, flags=flags), REGEX_LIMIT)
    except asyncio.TimeoutError:
        raise TimeoutError(
            f"A regex timed out after {REGEX_LIMIT} seconds! \n"
            f"pattern: ({pattern}) \n"
            f"flags: {flags} \n"
            f"on text of length {len(text)}"
        )


async def safe_search(pattern: str, text: str, flags=0):

    return await re2_search_with_timeout(pattern, text, flags=flags)

    # if pattern_uses_lookaround(pattern):
    #     return await asyncio.to_thread(regex_fallback.search, pattern, text, flags=flags)
    # try:
    #     return await re2_search_with_timeout(pattern, text, flags=flags)
    # except re2.RegexError:
    #     # fallback to the full-featured regex module
    #     return await asyncio.to_thread(regex_fallback.search, pattern, text, flags=flags)


def safe_search_sync(pattern: str, text: str, flags=0):

    return re2.search(pattern, text, flags=flags)

    # if pattern_uses_lookaround(pattern):
    #     return regex_fallback.search(pattern, text, flags=flags)
    # try:
    #     return re2.search(pattern, text, flags=flags)
    # except re2.RegexError:
    #     return regex_fallback.search(pattern, text, flags=flags)


def safe_sub(pattern: str, repl, string: str, flags=0):

    return re2.sub(pattern, repl, string, flags=flags)

    # if pattern_uses_lookaround(pattern):
    #     return regex_fallback.sub(pattern, repl, string, flags=flags)
    # try:
    #     return re2.sub(pattern, repl, string, flags=flags)
    # except re2.RegexError:
    #     return regex_fallback.sub(pattern, repl, string, flags=flags)


def safe_findall(pattern: str, string: str, flags=0):

    return re2.findall(pattern, string, flags=flags)

    # if pattern_uses_lookaround(pattern):
    #     return regex_fallback.findall(pattern, string, flags=flags)
    # try:
    #     return re2.findall(pattern, string, flags=flags)
    # except re2.RegexError:
    #     return regex_fallback.findall(pattern, string, flags=flags)
