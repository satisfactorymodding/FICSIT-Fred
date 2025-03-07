import logging
from os import getenv

from dotenv import load_dotenv

load_dotenv()

logging.root = logging.getLogger("FRED")
logging.basicConfig(level=getenv("FRED_LOG_LEVEL", logging.DEBUG))

from .fred import __version__  # noqa

ENVVARS = (
    "FRED_IP",
    "FRED_PORT",
    "FRED_TOKEN",
    "FRED_SQL_DB",
    "FRED_SQL_USER",
    "FRED_SQL_PASSWORD",
    "FRED_SQL_HOST",
    "FRED_SQL_PORT",
)

for var in ENVVARS:
    if getenv(var) is None:
        raise EnvironmentError(f"The ENV variable '{var}' isn't set")
