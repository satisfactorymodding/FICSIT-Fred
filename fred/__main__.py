import asyncio
from os import getenv

from .fred import Bot, nextcord


async def a_main():
    intents = nextcord.Intents.all()

    client = Bot("?", help_command=None, intents=intents, chunk_guilds_at_startup=False)
    await client.start(getenv("FRED_TOKEN"), reconnect=True)


def main():  # this is so poetry can run a function from here properly
    asyncio.run(a_main())


if __name__ == "__main__":
    main()
