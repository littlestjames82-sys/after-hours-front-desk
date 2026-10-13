"""The brain: a local open-weight model served by llama.cpp.

Uses llama-server's OpenAI-compatible chat endpoint when it is running
(fast, model stays loaded). If no server is up but a model path is set,
it boots a throwaway llama-server for the call. Either way the model
runs entirely on this machine - no call leaves the shop's computer.

Environment:
  AHFD_BRAIN_URL   llama-server base URL (default http://127.0.0.1:8771)
  AHFD_LLAMA_SERVER path to the llama-server binary (autostart/fallback)
  AHFD_MODEL       path to the .gguf model (autostart/fallback)
"""

import json
import os
import subprocess
import urllib.request

BRAIN_URL = os.environ.get("AHFD_BRAIN_URL", "http://127.0.0.1:8771")
LLAMA_CLI = os.environ.get("AHFD_LLAMA_CLI", "llama-cli")
MODEL = os.environ.get("AHFD_MODEL", "")


def _server_chat(messages, max_tokens=200, temperature=0.6):
    body = json.dumps({
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }).encode()
    req = urllib.request.Request(
        BRAIN_URL + "/v1/chat/completions",
        data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"].strip()


def server_up() -> bool:
    try:
        with urllib.request.urlopen(BRAIN_URL + "/health", timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False


def _spawned_server_chat(messages, max_tokens=200, temperature=0.6):
    """Fallback: boot a throwaway llama-server on a spare port, chat, kill.

    Slower (model loads per call) but uses the exact same HTTP path as the
    resident server - no fragile CLI output parsing.
    """
    server_bin = os.environ.get("AHFD_LLAMA_SERVER", "llama-server")
    port = int(os.environ.get("AHFD_FALLBACK_PORT", "8772"))
    url = f"http://127.0.0.1:{port}"
    proc = subprocess.Popen(
        [server_bin, "-m", MODEL, "--port", str(port),
         "--host", "127.0.0.1", "-t", os.environ.get("AHFD_THREADS", "2"),
         "-c", os.environ.get("AHFD_CTX", "8192")],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        import time
        for _ in range(180):
            try:
                with urllib.request.urlopen(url + "/health", timeout=2):
                    break
            except Exception:
                time.sleep(1)
        else:
            raise RuntimeError("fallback llama-server did not come up")
        body = json.dumps({
            "messages": messages, "max_tokens": max_tokens,
            "temperature": temperature}).encode()
        req = urllib.request.Request(
            url + "/v1/chat/completions", data=body,
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=900) as resp:
            data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"].strip()
    finally:
        proc.terminate()


def chat(messages, max_tokens=200, temperature=0.6):
    if server_up():
        return _server_chat(messages, max_tokens, temperature)
    if MODEL:
        return _spawned_server_chat(messages, max_tokens, temperature)
    raise RuntimeError(
        "No brain available: start llama-server or set AHFD_MODEL")
