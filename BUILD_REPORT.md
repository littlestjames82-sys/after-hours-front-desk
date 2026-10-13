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

## v2 — voice humanization + product polish (Oct 13, 2026)

Ryan's direction: keep building it better, and give it a better voice —
more human, less robotic.

**Voice — what Sopro really offers.** Inspected the installed library
and CLI: synthesis controls are sampling (`temperature`, `top_p`,
`top_k`), acoustic `steps` (default 2), `seed`, `lang`, segment length.
There is **no** rate/pitch/expressiveness parameter — none was invented.
The resident service previously forwarded only text/lang/seed; it now
accepts and forwards the four sampling fields (backward-compatible —
clients that don't send them, e.g. GhostCut's bridge, get model
defaults exactly as before; verified live: same seed + text with and
without the params produces different audio of identical duration).

**Voice — measured sweep (seed 42, 3 project lines).** Steps 2→8 at the
same seed/sampling produced the *identical* token stream (durations
equal to 0.01 s): steps refine only the acoustic render, so raising
them is a pure quality win (sandbox cost ≈2× generation seconds).
Temperature 0.95 rushed the greeting (21.5 chars/s) and was rejected;
**temperature 0.85 / top-p 0.95 / top-k 40 / steps 8** kept natural pace
and doubled the readback pause fraction (0.08→0.17). Pitch stats were
measured but the F0 estimator saturated at its 300 Hz ceiling on this
voice in every config, so pitch was **not** used to rank — recorded
plainly in `demo-evidence/voice-ab/VOICE_NOTES.md`. No production seed:
identical-every-call greetings are their own tell.

**Voice — the words.** The system prompt gained a spoken-style block
(contractions, one thought per sentence, human acknowledgements, no
lists aloud, callback number written as spaced digit groups, warm
open/close); every factual/flow/extraction rule is unchanged. New
`desk/speech.py` prepares only the spoken copy: phone numbers →
grouped digit words, `$89` → "eighty-nine dollars", `&` → "and",
typographic punctuation → ASCII (Sopro's own model card warns its
text frontend is minimal and to spell things out). Transcript and
extractor always see the original text.

**A/B evidence** in `demo-evidence/voice-ab/`: greeting, empathy, and
number-readback lines rendered before (v1 defaults, raw text) and after
(v2 settings + speech prep); all six WAVs verified real speech (RMS
0.067–0.078, 89–99% active frames, `ab-metrics.json`). The readback
pair is the clearest: 8.90 s of a raw hyphenated number string vs
9.58 s of grouped spoken digits.

**Smoke test on final v2 code: 8/8 PASS, exit 0** — run twice. Extraction
identical to v1 (name/phone/address exact, urgency=emergency, job
"Heat quit"); the desk's new style is visible in the transcript
("Oh no – I'm sorry to hear that. What's your name, please?").

**Part B.**
- *Second shop:* profiles moved to `desk/shops/*.json`; added
  **Riverbend Plumbing & Drain** (own services/prices/emergency rules/
  scenarios). Simulator shop selector + `/api/shops`; `/api/start`
  takes `{"shop": id}`. Verified: shops API lists both, and the
  plumbing greeting answers in the plumbing shop's name. (A full
  plumbing extraction run was attempted twice but the sandbox VM —
  8 GB, llama-server resident at ~4.4 GB — thrashed and the client
  timed out; that's environment, not code: the call path is the same
  one the 8/8 HVAC smoke exercises.)
- *Call log + owner review:* `/api/end` appends each finished call
  (time, shop, caller card, transcript) to `call-log.jsonl` (gitignored;
  `AHFD_CALL_LOG` overrides). The simulator gained an "Owner review —
  the morning list" section fed by `/api/call-log`. Verified: entries
  from real smoke calls land in the log with correct shop + card.
- *UX fixes:* v1 left the page in a dead end after a call (Call button
  stayed disabled as "⏳ Thinking…" forever) — now it resets to
  "📞 Call again" and the shop selector re-enables. All dynamic text is
  now HTML-escaped (v1 injected model/caller text via raw innerHTML).

**Evidence note:** the simulator screenshots in `demo-evidence/` are
from v1 — the v2 page keeps the layout and adds the shop selector and
the owner-review section; re-shoot them before the DEV post goes out.

**v2 caveats, unchanged in kind:** still Sopro's bundled synthetic
stand-in voice (warmer settings, not a clone); no phone line, no STT;
sandbox turn latency got slower at steps 8 under memory pressure —
no latency claims made anywhere.
