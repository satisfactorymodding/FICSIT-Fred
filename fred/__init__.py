from os import getenv

from dotenv import load_dotenv

from .fred import __version__

ENVVARS = (
    "FRED_IP",
    "FRED_PORT",
    "FRED_TOKEN",
    "FRED_SQL_DB",
    "FRED_SQL_USER",
    "FRED_SQL_PASSWORD",
    "FRED_SQL_HOST",
    "FRED_SQL_PORT",
    # "DIALOGFLOW_AUTH",
)

load_dotenv()

for var in ENVVARS:
    if getenv(var) is None:
        raise EnvironmentError(f"The ENV variable '{var}' isn't set")
