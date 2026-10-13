# Build Report — After-Hours Front Desk

**Date:** Oct 13, 2026 · **Built for:** DEV Hacktoberfest Open-Source AI
Challenge, Week 2 "Side Hustle" (submissions due Oct 18, 2026, 11:59 PM PDT)
· **Status:** working simulator demo, verified end-to-end. DEV post is a
DRAFT — not published.

## What runs

| Piece | Actually used | Verified how |
|---|---|---|
| Brain | **Gemma 3 4B-it, Q4_K_M GGUF** (ggml-org), 2,489,757,856 B — byte-exact vs HF published size | Real inference round-trips via llama-cli and llama-server |
| Engine | **llama.cpp** (MIT), GhostOS spike build b11382 at `~/workspace/ghost-os/spike-llama/` + llama-server built from the same tree | Server health + chat completions |
| Voice out | **Sopro V2 Turbo** (Apache-2.0, rev 2610), standalone install `~/workspace/sopro-test/`, resident HTTP service + `soprotts` CLI | Real WAVs: greeting line 4.51 s, RMS/peak confirm speech energy |
| Voice in | **Not built** — caller side is typed in the simulator, labeled as such everywhere | — |
| UI | One local page (vanilla HTML/JS), desk server in Python stdlib | Live screenshots (below) |

## Model choice — decided by evidence, not preference

Gemma 3 1B-it was downloaded first (806,058,240 B, byte-exact) and run
through the full smoke test three times. It failed the job:

- Extraction judged a no-heat call with a 4-month-old baby **"urgent"**
  instead of the shop-defined **"emergency"** — twice, even after the
  extraction prompt spelled the rule out.
- It **invented an address** ("123 Maple Street") the caller never gave,
  and the extractor then faithfully copied the hallucination.
- First run extracted the job as **"customer"**.

Gemma 3 4B-it passed everything, repeatedly (below). The demo therefore
ships on the 4B. The 1B remains a documented dead end, not a hidden one.

## Smoke test — final run (Oct 13, 2026, final code)

Scripted call: heat quit, 4-month-old baby in the house; caller gives name
(Sarah Daniels), phone (423-555-0147), address (418 Pine Street, Oakdale),
wants someone tonight. **Exit code 0 — 8/8 PASS:**

```
[PASS] server+brain up (Gemma 3 4B via llama-server)
[PASS] greeting spoken ("Good evening, Oakdale Heating & Air, how can I help you?", 3.5s audio)
[PASS] conversation turns w/ audio (desk asked name, then address, then
       closed by reading the callback number back: "Your number is 423-555-0147")
[PASS] extract name ('Sarah Daniels')
[PASS] extract phone ('423-555-0147')
[PASS] extract address ('418 Pine Street in Oakdale')
[PASS] extract urgency=emergency ('emergency')
[PASS] extract job mentions heat ('Heat quit')
```

An identical independent run (scripts/make_evidence.py) produced the same
card: job "Heat quit", urgency "emergency", summary "Sarah Daniels
reported a heat failure at 418 Pine Street in Oakdale due to a
four-month-old baby in the house, requiring immediate service."

## Bugs found and fixed during the build

1. **llama-server context default (131,072)** made the 4B take minutes to
   load and blew the startup wait — the desk now starts it with
   `-c 8192`, plenty for a phone call.
2. **Query-string routing:** `/?demo=mid` 404'd because the server matched
   the raw path including the query. Fixed with proper URL parsing.
3. **Transcript bleed:** a new call reset the model history but not the
   displayed transcript, merging two calls into one screenshot. Fixed;
   screenshot retaken clean.

## Evidence (in `demo-evidence/`)

- `simulator-mid-call.png` — live call in progress (real page, real stack)
- `simulator-summary-card.png` — full call + extracted owner summary card
- `sample-call.wav` — the desk side of the evidence call, spoken by Sopro
- `call-0-greeting.wav` … `call-3-reply.wav` — per-line audio
- `sample-call-transcript.json`, `sample-summary-card.json`
- `sample-reply-greeting.wav` — Sopro CLI proof from early in the build

Screenshots were captured with headless Firefox driven over Marionette:
in this sandbox Chromium's network service cannot reach loopback at all
(verified against two different local servers), while Firefox can. The
page, server, and model in the shots are the real ones.

## Honest caveats

- **Speeds are sandbox speeds:** this build machine has 2 cores. Turns
  took ~10–30 s end-to-end here; the same stack on a normal shop laptop
  (and Sopro's company-reported 0.24 RTF on an M3) will feel very
  different. No latency claims are made in the post.
- **Simulator scope stands:** no phone line, no speech-to-text, demo voice
  profile (Sopro's bundled synthetic voice), fictional shop. All labeled
  in the UI, README, and post draft.
- **The desk is terse.** The 4B follows the shop card and the flow, but
  its small-talk is minimal — a fair trade for never inventing facts.
