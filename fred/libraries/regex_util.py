import asyncio
import re as regex_fallback

import re2

REGEX_LIMIT: float = 6.9

re2.set_fallback_module(regex_fallback)


def pattern_uses_lookaround(pattern: str) -> bool:
    return bool(regex_fallback.search(r"\(\?=|\(\?!|\(\?<=|\(\?<!", pattern))


async def safe_search(pattern: str, text: str, flags=0):
    try:
        return await asyncio.wait_for(asyncio.to_thread(re2.search, pattern, text, flags=flags), REGEX_LIMIT)
    except asyncio.TimeoutError:
        raise TimeoutError(
            f"A regex timed out after {REGEX_LIMIT} seconds! \n"
            f"pattern: ({pattern}) \n"
            f"flags: {flags} \n"
            f"on text of length {len(text)}"
        )
