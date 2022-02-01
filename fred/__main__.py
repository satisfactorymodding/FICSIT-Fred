from fred import Bot, nextcord, os


intents = nextcord.Intents.all()

client = Bot("?", help_command=None, intents=intents, chunk_guilds_at_startup=False)

client.run(os.environ.get("FRED_TOKEN"))
