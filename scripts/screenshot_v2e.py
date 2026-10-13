#!/usr/bin/env python3
"""Round 2 screenshots, rendering step (see ROUND2_CRITIQUE.md).

The call log already holds a real completed call (logged by
screenshot_v2d.py through the desk's real API). This script starts
the desk against that same log and renders the real page in headless
Firefox:

  demo-evidence/simulator-morning-list.png  the page's own morning
                                            list, rendering the log
  demo-evidence/simulator-riverbend.png     Riverbend selected
  demo-evidence/simulator-summary-card.png  one short real call
                                            driven through the page,
                                            ending on its real card

Usage: python3 scripts/screenshot_v2e.py  (starts its own desk server)
"""

import base64
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "demo-evidence")
PORT = os.environ.get("AHFD_PORT", "8890")
BASE = f"http://127.0.0.1:{PORT}"
LOG = os.path.join(EV, "screenshot-r2-call-log.jsonl")
FIREFOX = os.environ.get(
    "FIREFOX_BIN",
    os.path.expanduser(
        "~/.cache/ms-playwright/firefox-1543/firefox/firefox"))
MPORT = 2828
PACKED = ("Hi, our heat quit and we have a four-month-old baby in "
          "the house. This is Sarah Daniels, 423-555-0147, at 418 "
          "Pine Street in Oakdale. Please come tonight.")


class Marionette:
    def __init__(self):
        self.sock = socket.create_connection(("127.0.0.1", MPORT),
                                             timeout=180)
        self.buf = b""
        self.mid = 0
        self._read_packet()

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

    def js(self, script):
        r = self.cmd("WebDriver:ExecuteScript",
                     {"script": script, "args": []})
        return (r or {}).get("value")

    def shot(self, path):
        r = self.cmd("WebDriver:TakeScreenshot", {"full": False})
        with open(path, "wb") as f:
            f.write(base64.b64decode(r["value"]))
        print(f"saved {path}", flush=True)


def wait_enabled(m, timeout=600):
    t0 = time.time()
    while time.time() - t0 < 30:
        if m.js("return document.getElementById('callerText').disabled;"):
            break
        time.sleep(0.7)
    while time.time() - t0 < timeout:
        if m.js("return !document.getElementById('callerText').disabled;"):
            return True
        time.sleep(1.5)
    raise RuntimeError("page turn never finished")


def main():
    env = dict(os.environ)
    env["AHFD_CALL_LOG"] = LOG  # existing real log; do not clear
    server = subprocess.Popen(
        [sys.executable, os.path.join(ROOT, "desk", "server.py")],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    try:
        for _ in range(300):
            try:
                with urllib.request.urlopen(BASE + "/api/health",
                                            timeout=2) as r:
                    if json.loads(r.read()).get("brain_up"):
                        break
            except Exception:
                pass
            time.sleep(1)
        else:
            print("stack never came up", flush=True)
            return 0
        print("stack up", flush=True)

        fenv = {k: v for k, v in os.environ.items()
                if "proxy" not in k.lower()}
        profile = tempfile.mkdtemp(prefix="ahfd-ff-shots4-")
        proc = subprocess.Popen(
            [FIREFOX, "--headless", "--marionette", "-profile", profile,
             "--window-size", "1000,1500", "about:blank"],
            env=fenv, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            m = None
            for _ in range(90):
                try:
                    m = Marionette()
                    break
                except OSError:
                    time.sleep(1)
            if m is None:
                print("marionette never came up", flush=True)
                return 0
            m.cmd("WebDriver:NewSession", {})
            m.cmd("WebDriver:Navigate", {"url": BASE + "/"})
            time.sleep(3)  # loadShops + refreshLog on plain load

            entries = m.js("return document.querySelectorAll("
                           "'#callLog .logentry').length;")
            print(f"morning list entries rendered: {entries}",
                  flush=True)
            m.js("document.getElementById('review')"
                 ".scrollIntoView({block:'start'});")
            time.sleep(1)
            m.shot(os.path.join(EV, "simulator-morning-list.png"))

            m.js("window.scrollTo(0,0);")
            m.js("document.getElementById('shopSel').value="
                 "'riverbend-plumbing';"
                 "document.getElementById('shopSel')"
                 ".dispatchEvent(new Event('change'));")
            time.sleep(1)
            m.shot(os.path.join(EV, "simulator-riverbend.png"))

            try:
                m.js("document.getElementById('shopSel').value="
                     "'oakdale-heating-air';"
                     "document.getElementById('shopSel')"
                     ".dispatchEvent(new Event('change'));")
                time.sleep(0.5)
                m.js("document.getElementById('btnCall').click();")
                wait_enabled(m)
                m.js("document.getElementById('callerText').value="
                     + json.dumps(PACKED) + ";"
                     "document.getElementById('btnSay').click();")
                wait_enabled(m)
                m.js("document.getElementById('btnEnd').click();")
                shown = None
                for _ in range(400):  # up to ~10 min for extraction
                    shown = m.js("return document.getElementById('card')"
                                 ".style.display;")
                    if shown == "block":
                        break
                    time.sleep(1.5)
                if shown == "block":
                    time.sleep(1)
                    m.js("document.getElementById('card')"
                         ".scrollIntoView({block:'center'});")
                    time.sleep(1)
                    m.shot(os.path.join(EV,
                                        "simulator-summary-card.png"))
                else:
                    print("card never appeared in page call", flush=True)
            except Exception as e:
                print(f"page card call failed ({type(e).__name__}: "
                      f"{e})", flush=True)
            print("rendering screenshots done", flush=True)
        finally:
            proc.terminate()
    finally:
        server.terminate()
    return 0


if __name__ == "__main__":
    sys.exit(main())
