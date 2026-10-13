#!/usr/bin/env python3
"""Capture simulator screenshots with headless Firefox via Marionette.

Why Firefox: in this sandbox Chromium's network service cannot reach
loopback at all (verified against two local servers), while Firefox can.
The screenshots are of the real page talking to the real local stack.

Usage: python3 scripts/screenshot_ff.py <url> <out.png>
"""

import base64
import json
import os
import socket
import subprocess
import sys
import tempfile
import time

FIREFOX = os.environ.get(
    "FIREFOX_BIN",
    os.path.expanduser(
        "~/.cache/ms-playwright/firefox-1543/firefox/firefox"))
PORT = 2828


class Marionette:
    def __init__(self):
        self.sock = socket.create_connection(("127.0.0.1", PORT), timeout=30)
        self.buf = b""
        self.mid = 0
        self._read_packet()  # greeting

    def _read_packet(self):
        while b":" not in self.buf:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise ConnectionError("marionette closed")
            self.buf += chunk
        length, rest = self.buf.split(b":", 1)
        n = int(length)
        while len(rest) < n:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise ConnectionError("marionette closed")
            rest += chunk
        self.buf = rest[n:]
        return json.loads(rest[:n])

    def cmd(self, name, params=None):
        self.mid += 1
        payload = json.dumps([0, self.mid, name, params or {}]).encode()
        self.sock.sendall(str(len(payload)).encode() + b":" + payload)
        msg = self._read_packet()
        if msg[2] is not None:
            raise RuntimeError(f"{name}: {msg[2]}")
        return msg[3]


def main():
    url, out = sys.argv[1], sys.argv[2]
    env = {k: v for k, v in os.environ.items()
           if "proxy" not in k.lower()}
    with tempfile.TemporaryDirectory() as profile:
        proc = subprocess.Popen(
            [FIREFOX, "--headless", "--marionette", "-profile", profile,
             "--window-size", "900,1400", "about:blank"],
            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            for _ in range(60):
                try:
                    m = Marionette()
                    break
                except OSError:
                    time.sleep(1)
            else:
                raise RuntimeError("marionette did not come up")
            m.cmd("WebDriver:NewSession", {})
            m.cmd("WebDriver:Navigate", {"url": url})
            state = ""
            for _ in range(110):
                time.sleep(5)
                r = m.cmd("WebDriver:ExecuteScript",
                          {"script": "return window.__demoState || 'none';",
                           "args": []})
                state = (r or {}).get("value")
                print(f"\rstate: {state}      ", end="", flush=True)
                if state == "done" or str(state).startswith("error"):
                    break
            print()
            if state != "done":
                raise RuntimeError(f"demo did not finish: {state}")
            time.sleep(1.5)
            r = m.cmd("WebDriver:TakeScreenshot", {"full": True})
            data = base64.b64decode(r["value"])
            with open(out, "wb") as f:
                f.write(data)
            print("saved", out, len(data), "bytes")
        finally:
            proc.terminate()


if __name__ == "__main__":
    main()
