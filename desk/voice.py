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


def _service_speak(text: str) -> bytes:
    with open(SOPRO_REF, "rb") as f:
        ref_b64 = base64.b64encode(f.read()).decode()
    body = json.dumps({
        "referenceBase64": ref_b64,
        "referenceName": "front-desk-voice",
        "text": text,
        "lang": "en",
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
             "--out", out, "--lang", "en"],
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
