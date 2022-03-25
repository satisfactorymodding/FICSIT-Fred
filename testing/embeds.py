# IMPORTANT! Must be run with a temp environment variable like this
# ~/FICSIT-Fred$ TESTWEBHOOKURL="https://webhook.com/url_things" python3 tests/embeds.py
# also, first comment out calls to config and provide approximate info, as the config connection isn't there

from os.path import abspath
import sys

sys.path.insert(0, abspath("./bot"))
from libraries.createembed import run
from asyncio import run as nonawait
from json import load
from os import getenv
from requests import post


with open(abspath("./tests/push.json")) as j:
    test_data = load(j)

test_data["type"] = "push"
embed = nonawait(run(test_data))
url = getenv("TESTWEBHOOKURL")
response = post(url, json={"embeds": [embed.to_dict()]})
print(response)
