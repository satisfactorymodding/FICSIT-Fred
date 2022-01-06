from fred_core_imports import *

from http.server import BaseHTTPRequestHandler, HTTPServer
import socket
import threading
import nextcord.ext.commands as commands


def runServer(self, bot):
    logging.info("Running the webserver for the Githook")
    server = HTTPServerV6((os.environ.get("FRED_IP"), int(os.environ.get("FRED_PORT"))), MakeGithookHandler(bot))
    server.serve_forever()


class Githook(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        # Run GitHub webhook handling server
        try:
            botargs = [bot, bot]
            daemon = threading.Thread(target=runServer, args=botargs)
            daemon.daemon = True
            daemon.start()
        except Exception as e:
            type, value, tb = sys.exc_info()
            tbs = ""
            for string in traceback.format_tb(tb):
                tbs = tbs + string
            logging.error(f'Failed to run the webserver:\n{tbs}')


# handle POST events from GitHub server
# We should also make sure to ignore requests from the IRC, which can clutter
# the output with errors
CONTENT_TYPE = 'content-type'
CONTENT_LEN = 'content-length'
EVENT_TYPE = 'x-github-event'


def MakeGithookHandler(bot):
    class MyGithookHandler(BaseHTTPRequestHandler):

        def do_HEAD(self):
            logging.info("Handling a HEAD request")
            match self.path:
                case "/ready":
                    self.send_response(200 if bot.isReady else 503)
                case "/healthy":
                    self.send_response(200 if bot.isAlive() else 503)
                case _:
                    self.send_response(200)

        def do_GET(self):
            logging.info("Handling a GET request")
            match self.path:
                case "/ready":
                    self.send_response(200 if bot.isReady else 503)
                case "/healthy":
                    self.send_response(200 if bot.isAlive() else 503)
                case _:
                    self.send_response(200)

        def do_CONNECT(self):
            logging.info("Handling a CONNECT request")
            self.send_response(200)

        def do_POST(self):
            logging.info("Handling a POST request")
            if not all(x in self.headers for x in [CONTENT_TYPE, CONTENT_LEN, EVENT_TYPE]):
                logging.error("Invalid POST request")
                self.send_response(417)
                return
            content_type = self.headers['content-type']
            content_len = int(self.headers['content-length'])
            event_type = self.headers['x-github-event']

            # Return error if the payload type is that other weird format instead of a normal json
            if content_type != "application/json":
                logging.error("POST request has invalid content_type", extra={'content_type': content_type})
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
            self.send_header('content-type', 'text/html')
            self.end_headers()
            self.wfile.write(bytes('FICSIT-Fred received the payload', 'utf-8'))
            # Send it!
            asyncio.run_coroutine_threadsafe(bot.githook_send(data), bot.loop)
            return

    return MyGithookHandler


class HTTPServerV6(HTTPServer):
    address_family = socket.AF_INET6
