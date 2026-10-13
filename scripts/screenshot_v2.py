#!/usr/bin/env python3
"""Re-shoot the simulator screenshots against the current v2 UI.

Round 2 (Oct 13, 2026): the previous simulator-*.png shots predated
v2 (no shop switcher state, no morning list). This script drives the
real page in headless Firefox (Marionette, same route as
capture_demo.py) through two complete real calls - the Oakdale
no-heat emergency and the Riverbend burst pipe - and saves:

  demo-evidence/simulator-mid-call.png      Oakdale call in progress
  demo-evidence/simulator-summary-card.png  Oakdale card at hang-up
  demo-evidence/simulator-riverbend.png     Riverbend shop selected
  demo-evidence/simulator-morning-list.png  owner review, both calls

Nothing is staged: replies are live model output, the call log is
this session's own (AHFD_CALL_LOG points at a dedicated file so the
morning list shows exactly these two calls).

Usage: python3 scripts/screenshot_v2.py  (starts its own desk server)
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
FIREFOX = os.environ.get(
    "FIREFOX_BIN",
    os.path.expanduser(
        "~/.cache/ms-playwright/firefox-1543/firefox/firefox"))
MPORT = 2828

OAKDALE = [
    "Hi, our heat quit about an hour ago and it is getting cold "
    "fast. We have a four-month-old baby in the house.",
    "This is Sarah Daniels, my number is 423-555-0147.",
    "We are at 418 Pine Street in Oakdale. Please, can someone "
    "come tonight, as soon as possible?",
]
RIVERBEND = [
    "Hi, a pipe just burst in our laundry room and water is "
    "pouring across the floor. I got the main shut off but we "
    "need a plumber tonight.",
    "This is Chris Novak, 423-555-0190, at 412 Willow Bend in "
    "Oakdale.",
]


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


def wait_enabled(m, timeout=1500):
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


def env_log_path():
    return os.path.join(EV, "screenshot-r2-call-log.jsonl")


def run_call(m, shop, lines):
    m.js(f"document.getElementById('shopSel').value='{shop}';"
         "document.getElementById('shopSel')"
         ".dispatchEvent(new Event('change'));")
    time.sleep(0.5)
    m.js("document.getElementById('btnCall').click();")
    wait_enabled(m)
    for i, line in enumerate(lines):
        m.js("document.getElementById('callerText').value="
             + json.dumps(line) + ";"
             "document.getElementById('btnSay').click();")
        wait_enabled(m)
        if shop == "oakdale-heating-air" and i == 0:
            m.js("document.getElementById('transcript')"
                 ".scrollIntoView({block:'center'});")
            time.sleep(1)
            m.shot(os.path.join(EV, "simulator-mid-call.png"))
    m.js("document.getElementById('btnEnd').click();")
    log = env_log_path()
    for _ in range(600):  # up to ~15 min: extraction is slow on a cold box
        shown = m.js("return document.getElementById('card')"
                     ".style.display;")
        if shown == "block":
            break
        if log and os.path.exists(log) and os.path.getsize(log) > 0:
            # the server logged the call; give the page a moment to
            # render the card it already received
            time.sleep(3)
            shown = m.js("return document.getElementById('card')"
                         ".style.display;")
            if shown == "block":
                break
        time.sleep(1.5)
    else:
        raise RuntimeError("summary card never appeared")
    time.sleep(1)


def main():
    env = dict(os.environ)
    env["AHFD_CALL_LOG"] = os.path.join(EV, "screenshot-r2-call-log.jsonl")
    if os.path.exists(env["AHFD_CALL_LOG"]):
        os.remove(env["AHFD_CALL_LOG"])
    server = subprocess.Popen(
        [sys.executable, os.path.join(ROOT, "desk", "server.py")],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    try:
        for _ in range(240):
            try:
                with urllib.request.urlopen(BASE + "/api/health",
                                            timeout=2) as r:
                    if json.loads(r.read()).get("brain_up"):
                        break
            except Exception:
                pass
            time.sleep(1)
        else:
            raise RuntimeError("desk server did not come up")

        fenv = {k: v for k, v in os.environ.items()
                if "proxy" not in k.lower()}
        profile = tempfile.mkdtemp(prefix="ahfd-ff-shots-")
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
            time.sleep(2)
            m.js("return (async()=>{ await loadShops(); })();")
            time.sleep(1)

            run_call(m, "oakdale-heating-air", OAKDALE)
            m.js("document.getElementById('card')"
                 ".scrollIntoView({block:'center'});")
            time.sleep(1)
            m.shot(os.path.join(EV, "simulator-summary-card.png"))

            # Riverbend selected, page top: the shop switcher state.
            m.js("window.scrollTo(0,0);")
            m.js("document.getElementById('shopSel').value="
                 "'riverbend-plumbing';"
                 "document.getElementById('shopSel')"
                 ".dispatchEvent(new Event('change'));")
            time.sleep(1)
            m.shot(os.path.join(EV, "simulator-riverbend.png"))

            run_call(m, "riverbend-plumbing", RIVERBEND)
            m.js("return (async()=>{ await refreshLog(); })();")
            time.sleep(1)
            m.js("document.getElementById('review')"
                 ".scrollIntoView({block:'start'});")
            time.sleep(1)
            m.shot(os.path.join(EV, "simulator-morning-list.png"))
            print("all screenshots done", flush=True)
        finally:
            proc.terminate()
    finally:
        server.terminate()
    return 0


if __name__ == "__main__":
    sys.exit(main())
