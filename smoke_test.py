#!/usr/bin/env python3
"""Headless end-to-end smoke test for the After-Hours Front Desk.

Starts the desk server (which autostarts llama-server + the Sopro service
when AHFD_* env is set - see scripts/run-demo.sh), plays one full scripted
call - the "no heat, baby in the house" scenario, giving every detail -
ends the call, and checks each stage:

  1. greeting     desk answers with a spoken line
  2. conversation desk replies to each caller line, audio is real WAV
  3. extraction   owner summary card fields match what the caller said
  4. honesty      urgency is judged "emergency" (baby + no heat)

Prints PASS/FAIL per stage; exit code 0 only if all pass.
"""

import base64
import io
import json
import os
import subprocess
import sys
import time
import urllib.request
import wave

ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = os.environ.get("AHFD_PORT", "8890")
BASE = f"http://127.0.0.1:{PORT}"

CALLER_LINES = [
    "Hi, our heat quit about an hour ago and it is getting cold fast. "
    "We have a four-month-old baby in the house.",
    "This is Sarah Daniels, my number is 423-555-0147.",
    "We are at 418 Pine Street in Oakdale. Please, can someone come "
    "tonight, as soon as possible?",
]

results = []


def check(stage, ok, detail=""):
    results.append((stage, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {stage} {detail}", flush=True)


def post(path, payload=None):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(payload or {}).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as resp:
        return json.loads(resp.read())


def wav_seconds(b64):
    raw = base64.b64decode(b64)
    with wave.open(io.BytesIO(raw)) as w:
        return w.getnframes() / w.getframerate()


def main():
    env = dict(os.environ)
    proc = subprocess.Popen(
        [sys.executable, os.path.join(ROOT, "desk", "server.py")],
        env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True)
    try:
        up = False
        for _ in range(240):
            try:
                with urllib.request.urlopen(BASE + "/api/health",
                                            timeout=2) as r:
                    health = json.loads(r.read())
                up = health.get("brain_up", False)
                if up:
                    break
            except Exception:
                pass
            time.sleep(1)
        check("server+brain up", up, f"(health={health if up else 'n/a'})")
        if not up:
            return 1

        d = post("/api/start")
        secs = wav_seconds(d["audio"])
        check("greeting spoken", bool(d["reply"]) and secs > 0.5,
              f"(reply={d['reply'][:60]!r}, audio={secs:.1f}s)")

        all_audio_ok = True
        for line in CALLER_LINES:
            d = post("/api/say", {"text": line})
            secs = wav_seconds(d["audio"])
            if not d["reply"] or secs <= 0.5:
                all_audio_ok = False
            print(f"       desk: {d['reply'][:90]!r} (audio {secs:.1f}s)",
                  flush=True)
        check("conversation turns w/ audio", all_audio_ok)

        card = post("/api/end")["card"]
        print("       card:", json.dumps(card), flush=True)
        digits = "".join(c for c in card["phone"] if c.isdigit())
        check("extract name", "daniels" in card["caller_name"].lower(),
              f"({card['caller_name']!r})")
        check("extract phone", digits == "4235550147", f"({card['phone']!r})")
        check("extract address", "pine" in card["address"].lower(),
              f"({card['address']!r})")
        check("extract urgency=emergency",
              card["urgency"].strip().lower() == "emergency",
              f"({card['urgency']!r})")
        check("extract job mentions heat",
              "heat" in card["job"].lower() or "furnace" in card["job"].lower()
              or "heating" in card["job"].lower(), f"({card['job']!r})")
        with open(os.path.join(ROOT, "demo-evidence",
                               "sample-summary-card.json"), "w") as f:
            json.dump(card, f, indent=2)
        return 0 if all(ok for _, ok, _ in results) else 1
    finally:
        proc.terminate()
        try:
            out, _ = proc.communicate(timeout=10)
        except Exception:
            proc.kill()
            out = ""


if __name__ == "__main__":
    sys.exit(main())
