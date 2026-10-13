#!/usr/bin/env python3
"""Quantified triage + extraction eval for the After-Hours Front Desk.

Runs the scripted caller scenarios in eval/scenarios.json against the
real desk (desk/server.py, Gemma 3 4B via llama.cpp, Sopro voice) over
the same HTTP API the simulator uses, one call at a time. For each
scenario it records:

  - every desk reply and the wall-clock time of every turn
    (brain generation + voice synthesis, end to end)
  - the extracted owner summary card from /api/end
  - the expected urgency and fields, scored field by field

Scoring: urgency must match exactly. Name/phone/address/job are scored
against what the caller actually said in the script; where a scenario
withholds a field on purpose, the correct extraction is "not given"
(inventing one is scored as a failure, and flagged).

Results are written incrementally to eval/results.json (or
eval/results-<tag>.json) so a crashed run still leaves its evidence.

Usage:
  python3 eval/run_eval.py [--only id1,id2] [--tag before]

Environment: same AHFD_* variables as smoke_test.py
(see scripts/env-sandbox.sh). The desk's call log is redirected into
this folder so eval calls never touch the owner's morning list.
"""

import argparse
import base64
import io
import json
import os
import statistics
import subprocess
import sys
import time
import urllib.request
import wave
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVAL_DIR = os.path.dirname(os.path.abspath(__file__))
PORT = os.environ.get("AHFD_PORT", "8890")
BASE = f"http://127.0.0.1:{PORT}"


def post(path, payload=None, timeout=480):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(payload or {}).encode(),
        headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read())
    return data, time.time() - t0


BRAIN_URL = os.environ.get("AHFD_BRAIN_URL", "http://127.0.0.1:8771")


def brain_up():
    try:
        with urllib.request.urlopen(BRAIN_URL + "/health", timeout=3) as r:
            return r.status == 200
    except Exception:
        return False


def ensure_brain():
    """Report brain state at scenario start - and otherwise stay out
    of the way. The desk has its own designed fallback (boot a
    throwaway llama-server per call) for exactly the case where the
    resident server has died; respawning a resident server from here
    raced that fallback, put two 2.5 GB model loads in flight at once
    on an 8 GB box, and made things worse. Logged, not hidden."""
    up = brain_up()
    if not up:
        print("    [eval] resident brain is down; the desk's per-call "
              "fallback path will serve this scenario", flush=True)
    return up


def post_resilient(path, payload, rec):
    """Retry a failed call up to twice, with the error body logged.

    In this sandbox, resident model servers have died mid-request;
    the desk surfaces that as a 500. That is infrastructure, not a
    desk answer - the retry lands on the desk's fallback path and the
    reply is still live model output. RESULTS.md discloses this
    policy and every retry is recorded in the results file."""
    last = None
    for attempt in range(3):
        try:
            return post(path, payload)
        except Exception as e:
            body = ""
            if hasattr(e, "read"):
                try:
                    body = e.read().decode("utf-8", "replace")[:200]
                except Exception:
                    pass
            last = e
            rec.setdefault("call_errors", []).append(
                f"{path}: {type(e).__name__}: {e} {body}".strip())
            if attempt < 2:
                rec["retries"] = rec.get("retries", 0) + 1
                print(f"    [eval] call failed ({e} {body}); "
                      f"retry {attempt + 1} in 20s", flush=True)
                time.sleep(20)
    raise last


def wav_seconds(b64):
    raw = base64.b64decode(b64)
    with wave.open(io.BytesIO(raw)) as w:
        return w.getnframes() / w.getframerate()


def digits(s):
    return "".join(c for c in (s or "") if c.isdigit())


def is_not_given(s):
    return (s or "").strip().lower() in ("not given", "", "none", "n/a")


def score(scenario, card):
    exp = scenario["expect"]
    out = {}

    got_urg = (card.get("urgency") or "").strip().lower()
    out["urgency"] = {
        "expected": exp["urgency"], "got": got_urg,
        "ok": got_urg == exp["urgency"]}

    def field(name, ok):
        out[name] = {"ok": bool(ok)}

    if exp["name"] is None:
        field("name", is_not_given(card.get("caller_name")))
    else:
        field("name", exp["name"] in (card.get("caller_name") or "").lower())
    out["name"]["got"] = card.get("caller_name")

    if exp["phone"] is None:
        field("phone", is_not_given(card.get("phone")))
    else:
        field("phone", digits(card.get("phone")) == exp["phone"])
    out["phone"]["got"] = card.get("phone")

    if exp["address"] is None:
        field("address", is_not_given(card.get("address")))
    else:
        field("address",
              exp["address"] in (card.get("address") or "").lower())
    out["address"]["got"] = card.get("address")

    if exp["job"] is None:
        field("job", is_not_given(card.get("job")))
    else:
        job = (card.get("job") or "").lower()
        field("job", any(k in job for k in exp["job"]))
    out["job"]["got"] = card.get("job")

    out["fields_ok"] = sum(out[f]["ok"] for f in
                            ("name", "phone", "address", "job"))
    out["all_ok"] = out["urgency"]["ok"] and out["fields_ok"] == 4
    return out


def summarize(results):
    done = [r for r in results if "score" in r]
    if not done:
        return {}
    n = len(done)
    urg_ok = sum(r["score"]["urgency"]["ok"] for r in done)
    fields = {f: sum(r["score"][f]["ok"] for r in done)
              for f in ("name", "phone", "address", "job")}
    turn_secs = [t for r in done for t in r["turn_seconds"]]
    return {
        "scenarios": n,
        "urgency_correct": urg_ok,
        "urgency_accuracy": round(urg_ok / n, 4),
        "fields_correct": fields,
        "fields_total": {f: n for f in fields},
        "field_checks_correct": sum(fields.values()),
        "field_checks_total": 4 * n,
        "fully_correct_scenarios": sum(r["score"]["all_ok"] for r in done),
        "turn_seconds": {
            "count": len(turn_secs),
            "mean": round(statistics.mean(turn_secs), 2),
            "median": round(statistics.median(turn_secs), 2),
            "min": round(min(turn_secs), 2),
            "max": round(max(turn_secs), 2),
        },
        "extraction_seconds": {
            "mean": round(statistics.mean(
                r["extraction_seconds"] for r in done), 2),
            "median": round(statistics.median(
                r["extraction_seconds"] for r in done), 2),
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="",
                    help="comma-separated scenario ids to run")
    ap.add_argument("--tag", default="",
                    help="suffix for the results file (results-<tag>.json)")
    args = ap.parse_args()

    with open(os.path.join(EVAL_DIR, "scenarios.json")) as f:
        scenarios = json.load(f)
    if args.only:
        wanted = {s.strip() for s in args.only.split(",") if s.strip()}
        scenarios = [s for s in scenarios if s["id"] in wanted]
    out_name = f"results-{args.tag}.json" if args.tag else "results.json"
    out_path = os.path.join(EVAL_DIR, out_name)

    env = dict(os.environ)
    env["AHFD_CALL_LOG"] = os.path.join(EVAL_DIR, "call-log-eval.jsonl")
    proc = subprocess.Popen(
        [sys.executable, os.path.join(ROOT, "desk", "server.py")],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    results = []
    doc = {
        "eval": "After-Hours Front Desk triage + extraction eval",
        "started_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "model_file": os.path.basename(os.environ.get("AHFD_MODEL", "")),
        "brain_url": os.environ.get("AHFD_BRAIN_URL", "http://127.0.0.1:8771"),
        "note": "Turn seconds are end-to-end wall time per desk reply "
                "(brain generation + Sopro voice synthesis) on the "
                "2-core sandbox build box. Scenarios are scripted; the "
                "desk replies and the summary card are live model output.",
        "results": results,
    }

    def save():
        doc["summary"] = summarize(results)
        with open(out_path, "w") as f:
            json.dump(doc, f, indent=2)

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
        if not up:
            print("desk server / brain did not come up", flush=True)
            return 1

        for sc in scenarios:
            print(f"=== {sc['id']} ({sc['shop']}) ===", flush=True)
            rec = {"id": sc["id"], "shop": sc["shop"], "class": sc["class"],
                   "note": sc["note"], "expected": sc["expect"],
                   "caller_lines": sc["lines"], "desk_replies": [],
                   "turn_seconds": [], "audio_seconds": []}
            try:
                ensure_brain()
                d, secs = post_resilient("/api/start",
                                         {"shop": sc["shop"]}, rec)
                rec["desk_replies"].append(d["reply"])
                rec["turn_seconds"].append(round(secs, 2))
                rec["audio_seconds"].append(round(wav_seconds(d["audio"]), 2))
                for line in sc["lines"]:
                    d, secs = post_resilient("/api/say", {"text": line}, rec)
                    rec["desk_replies"].append(d["reply"])
                    rec["turn_seconds"].append(round(secs, 2))
                    rec["audio_seconds"].append(
                        round(wav_seconds(d["audio"]), 2))
                d, secs = post_resilient("/api/end", None, rec)
                rec["extraction_seconds"] = round(secs, 2)
                rec["card"] = d["card"]
                rec["score"] = score(sc, d["card"])
                s = rec["score"]
                print(f"    urgency: expected {s['urgency']['expected']}, "
                      f"got {s['urgency']['got']!r} "
                      f"({'OK' if s['urgency']['ok'] else 'MISS'}) · "
                      f"fields {s['fields_ok']}/4 · "
                      f"turns {rec['turn_seconds']}", flush=True)
            except Exception as e:
                rec["error"] = f"{type(e).__name__}: {e}"
                print(f"    ERROR: {rec['error']}", flush=True)
            results.append(rec)
            save()
        print(json.dumps(doc["summary"], indent=2), flush=True)
        return 0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    sys.exit(main())
