#!/usr/bin/env python3
"""Round 2 screenshots, fallback route (see ROUND2_CRITIQUE.md).

Three earlier attempts (browser-driven, then API hybrids) stalled or
500'd on the end-of-call extraction after multi-turn calls: the
turns complete, the extraction generation crawls on this loaded
2-core box. The one shape that completed end to end quickly in
testing was greeting + ONE packed caller line + end (~2.5 min
total), so this script uses exactly that shape for the logged calls,
takes the rendering-only screenshots first-class, and treats every
step as best-effort: whatever lands is real, whatever does not is
reported by the log, and the script exits 0 with partial results
rather than dying.

  demo-evidence/simulator-morning-list.png  page rendering the real
                                            call log of the calls run
  demo-evidence/simulator-riverbend.png     Riverbend selected
  demo-evidence/simulator-summary-card.png  the page-driven packed
                                            call's real card

Usage: python3 scripts/screenshot_v2d.py  (starts its own desk server)
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

PACKED = {
    "oakdale-heating-air":
        "Hi, our heat quit and we have a four-month-old baby in the "
        "house. This is Sarah Daniels, 423-555-0147, at 418 Pine "
        "Street in Oakdale. Please come tonight.",
    "riverbend-plumbing":
        "Hi, a pipe just burst in our laundry room and water is "
        "pouring across the floor; I shut the main off. This is "
        "Chris Novak, 423-555-0190, at 412 Willow Bend in Oakdale. "
        "We need a plumber tonight.",
}


def api(path, payload, timeout=420):
    req = urllib.request.Request(
        BASE + path, method="POST",
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload).encode())
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def api_call(shop):
    try:
        api("/api/start", {"shop": shop})
        api("/api/say", {"text": PACKED[shop]})
        d = api("/api/end", {})
        c = d["card"]
        print(f"{shop}: card urgency={c['urgency']} job={c['job']!r} "
              f"logged={d.get('logged')}", flush=True)
        return True
    except Exception as e:
        print(f"{shop}: call failed ({type(e).__name__}: {e})",
              flush=True)
        return False


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
            print("stack never came up", flush=True)
            return 0
        print("stack up", flush=True)

        ok_oak = api_call("oakdale-heating-air")
        ok_riv = api_call("riverbend-plumbing")
        print(f"logged calls: oakdale={ok_oak} riverbend={ok_riv}",
              flush=True)

        fenv = {k: v for k, v in os.environ.items()
                if "proxy" not in k.lower()}
        profile = tempfile.mkdtemp(prefix="ahfd-ff-shots3-")
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
                print("marionette never came up", flush=True)
                return 0
            m.cmd("WebDriver:NewSession", {})
            m.cmd("WebDriver:Navigate", {"url": BASE + "/"})
            time.sleep(3)

            if ok_oak or ok_riv:
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
                     + json.dumps(PACKED["oakdale-heating-air"]) + ";"
                     "document.getElementById('btnSay').click();")
                wait_enabled(m)
                m.js("document.getElementById('btnEnd').click();")
                shown = None
                for _ in range(280):  # up to ~7 min for extraction
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
                    m.shot(os.path.join(EV, "simulator-summary-card.png"))
                else:
                    print("card never appeared in page call", flush=True)
            except Exception as e:
                print(f"page card call failed ({type(e).__name__}: "
                      f"{e})", flush=True)
            print("fallback screenshots done", flush=True)
        finally:
            proc.terminate()
    finally:
        server.terminate()
    return 0


if __name__ == "__main__":
    sys.exit(main())
