from dotenv import load_dotenv
from os import getenv

load_dotenv()

ENVVARS = [
    "FRED_IP",
    "FRED_PORT",
    "FRED_TOKEN",
    "FRED_SQL_DB",
    "FRED_SQL_USER",
    "FRED_SQL_PASSWORD",
    "FRED_SQL_HOST",
    "FRED_SQL_PORT",
    "DIALOGFLOW_AUTH",
]

for var in ENVVARS:
    if getenv(var) is None:
        raise EnvironmentError(f"The ENV variable '{var}' isn't set")

from .fred import Bot, nextcord, __version__


intents = nextcord.Intents.all()

client = Bot("?", help_command=None, intents=intents, chunk_guilds_at_startup=False)

client.run(getenv("FRED_TOKEN"))
