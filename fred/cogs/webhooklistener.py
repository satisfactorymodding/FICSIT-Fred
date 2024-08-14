from __future__ import annotations

import asyncio
import json
import socket
import sys
import threading
import traceback
from http.server import BaseHTTPRequestHandler, HTTPServer
from os import getenv
from typing import TYPE_CHECKING

from fred.libraries import common

if TYPE_CHECKING:
    from fred.fred import Bot

logger = common.new_logger(__name__)


def runServer(self, bot):
    logger.info("Running the webserver for the Githook")
    ip = getenv("FRED_IP")
    port = int(getenv("FRED_PORT"))
    try:
        server = HTTPServerV6((ip, port), MakeGithookHandler(bot))
        server.serve_forever()
    except PermissionError as pe:
        logger.error(f"Cannot handle githooks! Permission denied to listen to {ip=} {port=}.")
        logger.exception(pe)


class Githook(common.FredCog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Run GitHub webhook handling server
        try:
            daemon = threading.Thread(target=runServer, args=[self.bot, self.bot])
            daemon.daemon = True
            daemon.start()
        except Exception:  # noqa
            exc_type, value, tb = sys.exc_info()
            tbs = "".join(traceback.format_tb(tb))
            self.logger.error(f"Failed to run the webserver:\n{tbs}")


# handle POST events from GitHub server
# We should also make sure to ignore requests from the IRC, which can clutter
# the output with errors
CONTENT_TYPE = "content-type"
CONTENT_LEN = "content-length"
EVENT_TYPE = "x-github-event"


def MakeGithookHandler(bot: Bot):
    class MyGithookHandler(BaseHTTPRequestHandler):
        def respond(self, code: int, message: str | None = None):
            self.send_response(code, message)
            self.end_headers()

        def handle_check(self):
            try:
                match self.path:
                    case "/ready":
                        self.respond(200 if bot.isReady else 503)
                    case "/healthy":
                        logger.info("handling /healthy")
                        fut = asyncio.run_coroutine_threadsafe(bot.isAlive(), bot.loop)
                        logger.info("waiting for result from healthcheck")
                        healthy = fut.result(5)
                        logger.info("responding")
                        self.respond(200 if healthy else 503)
                    case _:
                        self.respond(200)
            except Exception as e:
                logger.error(f"Errored during check")
                logger.exception(e)

        def do_HEAD(self):
            self.handle_check()

        def do_GET(self):
            self.handle_check()

        def do_CONNECT(self):
            self.respond(200)

        def do_POST(self):
            logger.info("Handling a POST request")
            if not all(x in self.headers for x in [CONTENT_TYPE, CONTENT_LEN, EVENT_TYPE]):
                logger.error("Invalid POST request")
                self.send_response(417)
                return
            content_type = self.headers["content-type"]
            content_len = int(self.headers["content-length"])
            event_type = self.headers["x-github-event"]

            # Return error if the payload type is that other weird format instead of a normal json
            if content_type != "application/json":
                logger.error("POST request has invalid content_type", extra={"content_type": content_type})
                self.send_error(400, "Bad Request", "Expected a JSON request")
                return

            # Decrypt it into a json
            data = self.rfile.read(content_len)
            if sys.version_info < (3, 6):
                data = data.decode()
            data = json.loads(data)
            data["type"] = event_type

            # Respond to GitHub saying the payload arrived
            self.send_response(200)
            self.send_header("content-type", "text/html")
            self.end_headers()
            self.wfile.write(bytes("FICSIT-Fred received the payload", "utf-8"))
            # Send it!
            asyncio.run_coroutine_threadsafe(bot.githook_send(data), bot.loop)
            return

    return MyGithookHandler


class HTTPServerV6(HTTPServer):
    address_family = socket.AF_INET6
