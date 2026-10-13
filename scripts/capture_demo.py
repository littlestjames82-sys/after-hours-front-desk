#!/usr/bin/env python3
"""Capture a real simulator call for the demo video.

Drives the actual simulator page in headless Firefox (Marionette, the
same route as scripts/screenshot_ff.py) through two complete scripted
calls - the Oakdale no-heat emergency and the Riverbend burst pipe -
and, at every step, saves:

  - a viewport screenshot of the page exactly as a user would see it
  - the exact WAV bytes the desk server generated for that reply
    (intercepted from the page's own /api/start and /api/say fetch
    responses - the same base64 audio the browser played)
  - the desk's reply text from the page transcript

Output: demo-evidence/video-capture/manifest.json + frames/ + audio/.
scripts/make_video.py assembles those pieces into the demo video.
Nothing here is staged: the page, the model, and the voice are the
real local stack, and the calls are the shops' own demo scenarios.

Usage: python3 scripts/capture_demo.py
(Starts its own desk server, like smoke_test.py does.)
"""

import base64
import io
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
import wave

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "demo-evidence", "video-capture")
PORT = os.environ.get("AHFD_PORT", "8890")
BASE = f"http://127.0.0.1:{PORT}"
FIREFOX = os.environ.get(
    "FIREFOX_BIN",
    os.path.expanduser(
        "~/.cache/ms-playwright/firefox-1543/firefox/firefox"))
MPORT = 2828

CALLS = [
    {
        "shop": "oakdale-heating-air",
        "tag": "hvac",
        "lines": [
            "Hi, our heat quit about an hour ago and it is getting cold "
            "fast. We have a four-month-old baby in the house.",
            "This is Sarah Daniels, my number is 423-555-0147.",
            "We are at 418 Pine Street in Oakdale. Please, can someone "
            "come tonight, as soon as possible?",
        ],
    },
    {
        "shop": "riverbend-plumbing",
        "tag": "plumb",
        "lines": [
            "Hi, a pipe just burst in our laundry room and water is "
            "pouring across the floor. I got the main shut off but we "
            "need a plumber tonight.",
            "This is Chris Novak, 423-555-0190, at 412 Willow Bend in "
            "Oakdale.",
        ],
    },
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


def wait_enabled(m, timeout=1500):
    """Wait for a full turn: input disables (turn starts), then
    re-enables (reply arrived and was handed to the page)."""
    t0 = time.time()
    while time.time() - t0 < 30:  # turn should begin promptly
        if m.js("return document.getElementById('callerText').disabled;"):
            break
        time.sleep(0.7)
    while time.time() - t0 < timeout:
        if m.js("return !document.getElementById('callerText').disabled;"):
            return True
        time.sleep(1.5)
    raise RuntimeError("page turn never finished")


def wav_seconds(raw):
    with wave.open(io.BytesIO(raw)) as w:
        return w.getnframes() / w.getframerate()


def main():
    only = os.environ.get("AHFD_CAPTURE_ONLY", "")
    if only:
        CALLS[:] = [c for c in CALLS if c["tag"] == only]
    os.makedirs(os.path.join(OUT, "frames"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "audio"), exist_ok=True)
    env = dict(os.environ)
    env["AHFD_CALL_LOG"] = os.path.join(OUT, "call-log-video.jsonl")
    server = subprocess.Popen(
        [sys.executable, os.path.join(ROOT, "desk", "server.py")],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    segments = []
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
        import tempfile
        profile = tempfile.mkdtemp(prefix="ahfd-ff-")
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

            def grab(tag, kind, caption_hint=None):
                """Save frame + the exact audio the desk returned for
                this step (intercepted from the page's own fetch of
                /api/start and /api/say - the same base64 WAV the
                browser played)."""
                frame = os.path.join("frames", f"{tag}.png")
                m.shot(os.path.join(OUT, frame))
                seg = {"tag": tag, "kind": kind, "frame": frame}
                if kind in ("greeting", "reply"):
                    idx = grab.audio_idx
                    n = m.js("return window.__caps ? "
                             "window.__caps.length : -1;")
                    if n is not None and n > idx:
                        b64 = m.js(f"return window.__caps[{idx}];")
                        grab.audio_idx = idx + 1
                        if b64:
                            raw = base64.b64decode(b64)
                            rel = os.path.join("audio", f"{tag}.wav")
                            with open(os.path.join(OUT, rel), "wb") as f:
                                f.write(raw)
                            seg["audio"] = rel
                            seg["audio_seconds"] = round(
                                wav_seconds(raw), 2)
                text = m.js(
                    "const t=[...document.querySelectorAll("
                    "'#transcript .line')];"
                    "const last=t[t.length-1];"
                    "return last ? last.textContent.trim() : '';")
                seg["page_line"] = text
                if caption_hint:
                    seg["caption"] = caption_hint
                segments.append(seg)
                print(f"captured {tag}: audio="
                      f"{seg.get('audio_seconds')} line={text[:60]!r}",
                      flush=True)
                return seg
            grab.audio_idx = 0

            # Hook: record the audio payload of every /api/start and
            # /api/say response the page receives, in order.
            hook = (
                "window.__caps=[];"
                "const _f=window.fetch;"
                "window.fetch=async(...a)=>{"
                "  const r=await _f(...a);"
                "  try{ const u=String(a[0]);"
                "    if(u.includes('/api/start')||u.includes('/api/say')){"
                "      const d=await r.clone().json();"
                "      if(d&&d.audio) window.__caps.push(d.audio); }"
                "  }catch(e){}"
                "  return r; };")

            for ci, call in enumerate(CALLS):
              try:
                m.cmd("WebDriver:Navigate", {"url": BASE + "/"})
                time.sleep(2)
                m.js(hook)
                grab.audio_idx = 0
                m.js("return (async()=>{ await loadShops(); })();")
                time.sleep(1)
                if ci == 0:
                    grab("intro", "title",
                         "A real call, recorded live in the simulator. "
                         "The desk is a local model; the caller side "
                         "is typed.")
                m.js(f"document.getElementById('shopSel').value="
                     f"'{call['shop']}';"
                     "document.getElementById('shopSel')"
                     ".dispatchEvent(new Event('change'));")
                time.sleep(0.5)
                m.js("document.getElementById('btnCall').click();")
                wait_enabled(m)
                grab(f"{call['tag']}-0-greeting", "greeting")
                for i, line in enumerate(call["lines"], 1):
                    m.js("document.getElementById('callerText').value="
                         + json.dumps(line) + ";"
                         "document.getElementById('btnSay').click();")
                    wait_enabled(m)
                    grab(f"{call['tag']}-{i}-reply", "reply")
                m.js("document.getElementById('btnEnd').click();")
                for _ in range(120):
                    shown = m.js(
                        "return document.getElementById('card')"
                        ".style.display;")
                    if shown == "block":
                        break
                    time.sleep(1.5)
                time.sleep(1)
                m.js("document.getElementById('card')"
                     ".scrollIntoView({block:'center'});")
                time.sleep(1)
                grab(f"{call['tag']}-9-card", "card",
                     "The owner summary card: extracted from the "
                     "transcript by the same local model.")
              except Exception as e:
                print(f"call {call['tag']} stopped partway: "
                      f"{type(e).__name__}: {e}", flush=True)
            manifest = {"segments": segments}
            with open(os.path.join(OUT, "manifest.json"), "w") as f:
                json.dump(manifest, f, indent=2)
            print(f"manifest: {len(segments)} segments", flush=True)
        finally:
            proc.terminate()
    finally:
        server.terminate()
    return 0


if __name__ == "__main__":
    sys.exit(main())
