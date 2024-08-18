from os import getenv

from .fred import Bot, nextcord


def main():  # this is so poetry can run a function from here properly
    intents = nextcord.Intents.all()

    client = Bot("?", help_command=None, intents=intents, chunk_guilds_at_startup=False)

    client.run(getenv("FRED_TOKEN"))


if __name__ == "__main__":
    main()
