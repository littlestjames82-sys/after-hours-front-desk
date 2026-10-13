#!/usr/bin/env python3
"""Round 2 screenshots, hybrid route (see ROUND2_CRITIQUE.md).

Why hybrid: two browser-driven attempts stalled mid-call when the
local model server died under sandbox load (the same failure the
eval documented). So the two full calls are run through the desk's
real API (same code path the page uses), and the browser renders the
page's own real state for the screenshots:

  demo-evidence/simulator-morning-list.png  page rendering the real
                                            call log of the two calls
  demo-evidence/simulator-riverbend.png     Riverbend selected in the
                                            real page
  demo-evidence/simulator-summary-card.png  a short real call driven
                                            through the page itself,
                                            ending on its real card

(simulator-mid-call.png was already re-shot by screenshot_v2.py.)

Usage: python3 scripts/screenshot_v2c.py  (starts its own desk server)
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

OAKDALE = [
    "Hi, our heat quit about an hour ago and it is getting cold "
    "fast. We have a four-month-old baby in the house.",
    "This is Sarah Daniels, my number is 423-555-0147. We are at "
    "418 Pine Street in Oakdale. Please, can someone come tonight, "
    "as soon as possible?",
]
RIVERBEND = [
    "Hi, a pipe just burst in our laundry room and water is "
    "pouring across the floor. I got the main shut off but we "
    "need a plumber tonight.",
    "This is Chris Novak, 423-555-0190, at 412 Willow Bend in "
    "Oakdale.",
]
PACKED = ("Hi, our heat quit and we have a four-month-old baby in "
          "the house. This is Sarah Daniels, 423-555-0147, at 418 "
          "Pine Street in Oakdale. Please come tonight.")


def api(path, payload, timeout=900):
    last = None
    for attempt in range(3):
        req = urllib.request.Request(
            BASE + path, method="POST",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload).encode())
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except Exception as e:
            last = e
            print(f"{path}: attempt {attempt + 1} failed "
                  f"({type(e).__name__}: {e}); retrying", flush=True)
            time.sleep(5)
    raise last


def api_call(shop, lines):
    d = api("/api/start", {"shop": shop})
    print(f"{shop}: greeting ok", flush=True)
    for line in lines:
        d = api("/api/say", {"text": line})
        print(f"{shop}: reply ok", flush=True)
    d = api("/api/end", {})
    c = d["card"]
    print(f"{shop}: card urgency={c['urgency']} job={c['job']!r} "
          f"logged={d.get('logged')}", flush=True)
    return c


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


def wait_enabled(m, timeout=1200):
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
    env["AHFD_CALL_LOG"] = LOG
    if os.path.exists(LOG):
        os.remove(LOG)
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
            raise RuntimeError("desk server / brain did not come up")
        print("stack up", flush=True)

        api_call("oakdale-heating-air", OAKDALE)
        api_call("riverbend-plumbing", RIVERBEND)

        fenv = {k: v for k, v in os.environ.items()
                if "proxy" not in k.lower()}
        profile = tempfile.mkdtemp(prefix="ahfd-ff-shots2-")
        proc = subprocess.Popen(
            [FIREFOX, "--headless", "--marionette", "-profile", profile,
             "--window-size", "1000,1500", "about:blank"],
            env=fenv, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
            m.cmd("WebDriver:Navigate", {"url": BASE + "/"})
            time.sleep(3)  # loadShops + refreshLog run on plain load

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

            # Short real call through the page itself, for the card.
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
            for _ in range(400):  # up to ~10 min for extraction
                shown = m.js("return document.getElementById('card')"
                             ".style.display;")
                if shown == "block":
                    break
                time.sleep(1.5)
            else:
                raise RuntimeError("summary card never appeared")
            time.sleep(1)
            m.js("document.getElementById('card')"
                 ".scrollIntoView({block:'center'});")
            time.sleep(1)
            m.shot(os.path.join(EV, "simulator-summary-card.png"))
            print("all hybrid screenshots done", flush=True)
        finally:
            proc.terminate()
    finally:
        server.terminate()
    return 0


if __name__ == "__main__":
    sys.exit(main())
