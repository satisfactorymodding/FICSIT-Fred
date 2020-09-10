import socketserver
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import sys
import socket
import os
from typing import Tuple

import discord.ext.commands as commands


class Githook(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Run Github webhook handling server
        try:
            server = HTTPServerV6((os.environ.get("FRED_IP"), int(os.environ.get("FRED_PORT"))), MakeGithookHandler(bot))
            server.serve_forever()
        except Exception as e:
            print("Failed to run the githook server")
            type, value, tb = sys.exc_info()
            tbs = ""
            for string in traceback.format_tb(tb):
                tbs = tbs + string
            self.bot.logger.error(tbs)


# handle POST events from github server
# We should also make sure to ignore requests from the IRC, which can clutter
# the output with errors
CONTENT_TYPE = 'content-type'
CONTENT_LEN = 'content-length'
EVENT_TYPE = 'x-github-event'

def MakeGithookHandler(bot):
    class GithookHandler(BaseHTTPRequestHandler):
        def __init__(self, bot, request: bytes, client_address: Tuple[str, int], server: socketserver.BaseServer):
            super().__init__(request, client_address, server)
            self.bot = bot

        async def do_GET(self):
            if self.path == "/readiness":
                self.send_response(200)
            elif self.path == "/liveness":
                if self.bot.isAlive():
                    self.send_response(200)
                else:
                    self.send_response(503)
            else:
                self.send_response(200)

        async def do_CONNECT(self):
            self.send_response(200)

        def do_POST(self):
            if not all(x in self.headers for x in [CONTENT_TYPE, CONTENT_LEN, EVENT_TYPE]):
                self.send_response(417)
                return
            content_type = self.headers['content-type']
            content_len = int(self.headers['content-length'])
            event_type = self.headers['x-github-event']

            # Return error if some moron set the payload type to be that other weird format instead of a normal fucking json!
            if content_type != "application/json":
                self.send_error(400, "Bad Request", "Expected a JSON request")
                return

            # Decrypt that shit into a json, idk wtf it means otherwise!
            data = self.rfile.read(content_len)
            if sys.version_info < (3, 6):
                data = data.decode()
            data = json.loads(data)
            data["type"] = event_type

            # Respond to GitHub saying the payload arrived, as it fucking should!
            self.send_response(200)
            self.send_header('content-type', 'text/html')
            self.end_headers()
            self.wfile.write(bytes('FICSIT-Fred received the payload', 'utf-8'))
            print("Got a POST with good data")
            # Send that shit !
            bot.githook_send(data)
            return
    return GithookHandler

class HTTPServerV6(ThreadingHTTPServer):
    address_family = socket.AF_INET6



