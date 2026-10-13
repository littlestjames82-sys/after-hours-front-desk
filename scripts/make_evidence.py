#!/usr/bin/env python3
"""Record one real call against a running desk server and save the audio.

Saves every desk line as its own WAV plus one combined sample-call.wav
(desk side only - the caller side of the simulator is typed), the
transcript, and the extracted summary card into demo-evidence/.
The desk server must already be running (scripts/run-demo.sh).
"""

import base64
import io
import json
import os
import urllib.request
import wave

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "demo-evidence")
BASE = f"http://127.0.0.1:{os.environ.get('AHFD_PORT', '8890')}"

CALLER_LINES = [
    "Hi, our heat quit about an hour ago and it is getting cold fast. "
    "We have a four-month-old baby in the house.",
    "This is Sarah Daniels, my number is 423-555-0147.",
    "We are at 418 Pine Street in Oakdale. Please, can someone come "
    "tonight, as soon as possible?",
]


def post(path, payload=None):
    req = urllib.request.Request(
        BASE + path, data=json.dumps(payload or {}).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as resp:
        return json.loads(resp.read())


def main():
    os.makedirs(EV, exist_ok=True)
    segments = []  # (params, frames) for the combined file
    transcript = []

    def keep(tag, d):
        raw = base64.b64decode(d["audio"])
        with open(os.path.join(EV, f"call-{tag}.wav"), "wb") as f:
            f.write(raw)
        with wave.open(io.BytesIO(raw)) as w:
            segments.append((w.getparams(), w.readframes(w.getnframes())))
        transcript.append({"desk": d["reply"]})

    d = post("/api/start")
    keep("0-greeting", d)
    for i, line in enumerate(CALLER_LINES, 1):
        transcript.append({"caller": line})
        d = post("/api/say", {"text": line})
        keep(f"{i}-reply", d)
    card = post("/api/end")["card"]

    params = segments[0][0]
    pause = b"\x00" * int(params.framerate * params.sampwidth * 0.4)
    with wave.open(os.path.join(EV, "sample-call.wav"), "wb") as w:
        w.setparams(params)
        for _, frames in segments:
            w.writeframes(frames)
            w.writeframes(pause)
    with open(os.path.join(EV, "sample-call-transcript.json"), "w") as f:
        json.dump({"transcript": transcript, "summary_card": card},
                  f, indent=2)
    print("evidence saved:", sorted(os.listdir(EV)))
    print("card:", json.dumps(card))


if __name__ == "__main__":
    main()
