import asyncio
from os import getenv

from .fred import Bot, nextcord


async def main():  # this is so poetry can run a function from here properly
    intents = nextcord.Intents.all()

    client = Bot("?", help_command=None, intents=intents, chunk_guilds_at_startup=False)
    await client.start(getenv("FRED_TOKEN"), reconnect=True)


if __name__ == "__main__":
    asyncio.run(main())
