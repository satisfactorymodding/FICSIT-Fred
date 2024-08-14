from os import getenv

from .fred import Bot, nextcord

intents = nextcord.Intents.all()

client = Bot("?", help_command=None, intents=intents, chunk_guilds_at_startup=False)

client.run(getenv("FRED_TOKEN"))
