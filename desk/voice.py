"""The voice: Sopro V2 Turbo (Apache-2.0) text-to-speech.

Preferred route is a resident Sopro HTTP service (the model is ~634 MB;
keeping it loaded makes replies take seconds instead of a cold load each
time). Fallback route shells out to the `soprotts` CLI from a local Sopro
install. Either way synthesis happens on this machine.

Environment:
  AHFD_SOPRO_URL   Sopro service base URL (default http://127.0.0.1:8766)
  AHFD_SOPRO_CLI   path to the soprotts executable (fallback)
  AHFD_SOPRO_MODEL local Sopro model dir (fallback)
  AHFD_SOPRO_REF   reference clip for the voice profile (5-20 s)
  AHFD_VOICE_TEMPERATURE / _TOP_P / _TOP_K / _STEPS
                   synthesis sampling (v2 "human voice" defaults below)

Voice settings (v2): Sopro's shipping defaults (temperature 0.8, top-p
0.9, top-k 25, steps 2) are tuned for speed - the "Turbo" in the name.
A settings sweep on this project's lines (see
demo-evidence/voice-ab/VOICE_NOTES.md) picked warmer sampling plus the
maximum acoustic refinement that costs nothing behaviorally: steps only
refine the acoustic render of the same token stream, so 2 -> 8 smooths
the sound without changing a word or a pause. No seed is pinned: a fixed
seed makes the greeting byte-identical on every call, which is its own
kind of robotic.
"""

import base64
import json
import os
import subprocess
import tempfile
import urllib.request

SOPRO_URL = os.environ.get("AHFD_SOPRO_URL", "http://127.0.0.1:8766")
SOPRO_CLI = os.environ.get("AHFD_SOPRO_CLI", "")
SOPRO_MODEL = os.environ.get("AHFD_SOPRO_MODEL", "")
SOPRO_REF = os.environ.get("AHFD_SOPRO_REF", "")

TEMPERATURE = float(os.environ.get("AHFD_VOICE_TEMPERATURE", "0.85"))
TOP_P = float(os.environ.get("AHFD_VOICE_TOP_P", "0.95"))
TOP_K = int(os.environ.get("AHFD_VOICE_TOP_K", "40"))
STEPS = int(os.environ.get("AHFD_VOICE_STEPS", "8"))


def _service_speak(text: str) -> bytes:
    with open(SOPRO_REF, "rb") as f:
        ref_b64 = base64.b64encode(f.read()).decode()
    body = json.dumps({
        "referenceBase64": ref_b64,
        "referenceName": "front-desk-voice",
        "text": text,
        "lang": "en",
        "temperature": TEMPERATURE,
        "top_p": TOP_P,
        "top_k": TOP_K,
        "steps": STEPS,
    }).encode()
    req = urllib.request.Request(
        SOPRO_URL + "/generate", data=body,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as resp:
        data = json.loads(resp.read())
    if not data.get("ok"):
        raise RuntimeError("Sopro service error: %s" % data.get("error"))
    return base64.b64decode(data["wavBase64"])


def _cli_speak(text: str) -> bytes:
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "reply.wav")
        env = dict(os.environ, NO_PROXY="localhost,127.0.0.1")
        subprocess.run(
            [SOPRO_CLI, text, "--ref", SOPRO_REF, "--model", SOPRO_MODEL,
             "--out", out, "--lang", "en",
             "--temperature", str(TEMPERATURE), "--top-p", str(TOP_P),
             "--top-k", str(TOP_K), "--steps", str(STEPS)],
            check=True, capture_output=True, text=True, timeout=900, env=env)
        with open(out, "rb") as f:
            return f.read()


def speak(text: str) -> bytes:
    """Return WAV bytes for one spoken reply line."""
    try:
        return _service_speak(text)
    except Exception:
        if SOPRO_CLI and SOPRO_MODEL:
            return _cli_speak(text)
        raise
