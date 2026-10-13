#!/usr/bin/env python3
"""After-Hours Front Desk — simulator server.

One local web page, three local services, zero cloud:

  browser page  ->  this server (127.0.0.1:8890)
  conversation  ->  llama.cpp serving a local open-weight model
  voice         ->  Sopro V2 Turbo (Apache-2.0) on this machine

The caller side of the demo is typed (a call simulator - see README for
honest scope). Everything the desk says is generated live by the local
model from the shop card, spoken by Sopro, and shown in the transcript.
Ending the call asks the same model to extract the owner summary card.

Run:  python3 desk/server.py     (see setup.sh for first-time setup)
"""

import base64
import json
import os
import subprocess
import sys
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import brain          # noqa: E402
import prompts        # noqa: E402
import voice          # noqa: E402

PORT = int(os.environ.get("AHFD_PORT", "8890"))
SHOP_PATH = os.environ.get("AHFD_SHOP", os.path.join(HERE, "shop.json"))

with open(SHOP_PATH) as f:
    SHOP = json.load(f)
SYSTEM_PROMPT = prompts.build_system_prompt(SHOP)

# One demo call at a time. history = messages sent to the brain;
# transcript = what the page displays (kickoff line excluded).
STATE = {"history": [], "transcript": []}


def clean_for_speech(text: str) -> str:
    for ch in "*_#`>":
        text = text.replace(ch, "")
    return " ".join(text.split())


def desk_turn(user_text=None, kickoff=False):
    if kickoff:
        STATE["history"] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content":
             "(The phone just rang. Greet the caller as the front desk.)"},
        ]
        STATE["transcript"] = []
    elif user_text is not None:
        STATE["history"].append({"role": "user", "content": user_text})
        STATE["transcript"].append({"who": "Caller", "text": user_text})
    reply = brain.chat(STATE["history"], max_tokens=160, temperature=0.6)
    STATE["history"].append({"role": "assistant", "content": reply})
    STATE["transcript"].append({"who": SHOP["name"], "text": reply})
    audio = voice.speak(clean_for_speech(reply))
    return reply, audio


def autostart():
    """Start llama-server and the Sopro service if configured and down."""
    if not brain.server_up():
        srv = os.environ.get("AHFD_LLAMA_SERVER")
        model = os.environ.get("AHFD_MODEL")
        if srv and model:
            port = brain.BRAIN_URL.rsplit(":", 1)[-1]
            print(f"[desk] starting llama-server on :{port} ...", flush=True)
            subprocess.Popen(
                [srv, "-m", model, "--port", port, "-t",
                 os.environ.get("AHFD_THREADS", "2"),
                 "-c", os.environ.get("AHFD_CTX", "8192"),
                 "--host", "127.0.0.1"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            for _ in range(240):
                if brain.server_up():
                    break
                time.sleep(1)
    try:
        with urllib.request.urlopen(voice.SOPRO_URL + "/health",
                                    timeout=2) as r:
            ok = json.loads(r.read()).get("ok")
    except Exception:
        ok = False
    if not ok:
        py = os.environ.get("AHFD_SOPRO_PYTHON")
        server_py = os.environ.get("AHFD_SOPRO_SERVER")
        if py and server_py:
            port = voice.SOPRO_URL.rsplit(":", 1)[-1]
            print(f"[desk] starting Sopro service on :{port} ...", flush=True)
            env = dict(os.environ, SOPRO_PORT=port,
                       NO_PROXY="localhost,127.0.0.1")
            subprocess.Popen([py, server_py],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, env=env)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, code, body, ctype="application/json"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode()
        elif isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        from urllib.parse import urlparse
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            with open(os.path.join(ROOT, "web", "index.html"), "rb") as f:
                self._send(200, f.read(), "text/html; charset=utf-8")
        elif path == "/api/health":
            self._send(200, {
                "shop": SHOP["name"],
                "brain_up": brain.server_up(),
                "brain_url": brain.BRAIN_URL,
                "model": os.environ.get("AHFD_MODEL", ""),
            })
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length) or b"{}")
        try:
            if self.path == "/api/start":
                reply, audio = desk_turn(kickoff=True)
                self._send(200, {"reply": reply,
                                 "audio": base64.b64encode(audio).decode(),
                                 "transcript": STATE["transcript"]})
            elif self.path == "/api/say":
                reply, audio = desk_turn(user_text=payload["text"])
                self._send(200, {"reply": reply,
                                 "audio": base64.b64encode(audio).decode(),
                                 "transcript": STATE["transcript"]})
            elif self.path == "/api/end":
                lines = [f"{t['who']}: {t['text']}"
                         for t in STATE["transcript"]]
                prompt = prompts.build_extraction_prompt(
                    SHOP, "\n".join(lines))
                raw = brain.chat([{"role": "user", "content": prompt}],
                                 max_tokens=400, temperature=0.2)
                card = prompts.parse_extraction(raw)
                self._send(200, {"card": card})
            else:
                self._send(404, {"error": "not found"})
        except Exception as e:  # honest errors, never a faked reply
            self._send(500, {"error": f"{type(e).__name__}: {e}"})


if __name__ == "__main__":
    autostart()
    print(f"[desk] {SHOP['name']} front desk simulator on "
          f"http://127.0.0.1:{PORT}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
