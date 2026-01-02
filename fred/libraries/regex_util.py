import asyncio
import re2
import regex as regex_fallback
import re as std_re

REGEX_LIMIT: float = 6.9


async def regex_with_timeout(*args, **kwargs):
    try:
        return await asyncio.wait_for(asyncio.to_thread(re2.search, *args, **kwargs), REGEX_LIMIT)
    except asyncio.TimeoutError:
        raise TimeoutError(
            f"A regex timed out after {REGEX_LIMIT} seconds! \n"
            f"pattern: ({args[0]}) \n"
            f"flags: {kwargs['flags']} \n"
            f"on text of length {len(args[1])}"
        )
    except re2.RegexError as e:
        raise ValueError(args[0]) from e


def pattern_uses_lookaround(pattern: str) -> bool:
    return bool(std_re.search(r"\(\?=|\(\?!|\(\?<=|\(\?<!", pattern))


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
    # If the pattern contains lookaround constructs, go straight to fallback
    if pattern_uses_lookaround(pattern):
        return await asyncio.to_thread(regex_fallback.search, pattern, text, flags=flags)
    try:
        return await re2_search_with_timeout(pattern, text, flags=flags)
    except re2.RegexError:
        # fallback to the full-featured regex module
        return await asyncio.to_thread(regex_fallback.search, pattern, text, flags=flags)


def safe_search_sync(pattern: str, text: str, flags=0):
    if pattern_uses_lookaround(pattern):
        return regex_fallback.search(pattern, text, flags=flags)
    try:
        return re2.search(pattern, text, flags=flags)
    except re2.RegexError:
        return regex_fallback.search(pattern, text, flags=flags)


def safe_sub(pattern: str, repl, string: str, flags=0):
    if pattern_uses_lookaround(pattern):
        return regex_fallback.sub(pattern, repl, string, flags=flags)
    try:
        return re2.sub(pattern, repl, string, flags=flags)
    except re2.RegexError:
        return regex_fallback.sub(pattern, repl, string, flags=flags)


def safe_findall(pattern: str, string: str, flags=0):
    if pattern_uses_lookaround(pattern):
        return regex_fallback.findall(pattern, string, flags=flags)
    try:
        return re2.findall(pattern, string, flags=flags)
    except re2.RegexError:
        return regex_fallback.findall(pattern, string, flags=flags)
