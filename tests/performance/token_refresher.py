#!/usr/bin/env python3
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from time import ctime, sleep, time

from get_test_config import get_public_mode_config

current_config = None

env_name = os.environ.get("ENV", "perftest")
port = int(os.environ.get("TOKEN_REFRESH_PORT", 8765))


class TokenHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(current_config or {}).encode())

    def log_message(self, format, *args):
        pass  # Suppress logging


def refresh_token_loop():
    global current_config
    while True:
        current_config = get_public_mode_config(env_name)

        print(f"Token refreshed at {ctime()}")  # noqa
        expires_in = current_config.get("bearer_token_expires") - time()  # 5 mins

        sleep(max(expires_in - 30, 30))


def main():
    # Start thread to regularly fetch a fresh token
    thread = threading.Thread(target=refresh_token_loop, daemon=True)
    thread.start()
    sleep(1)  # Get initial token

    # Start HTTP server to serve the latest token
    server = HTTPServer(("localhost", port), TokenHandler)
    print(f"Token server running on http://localhost:{port}")  # noqa
    server.serve_forever()


if __name__ == "__main__":
    main()
