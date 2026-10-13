# After-Hours Front Desk

**A voice receptionist that runs entirely on the shop's own computer.**

When a small trade shop misses a call at 7 PM, that job usually goes to the
next name on Google. After-Hours Front Desk answers instead: a local
open-weight model holds the conversation, takes the job details, judges the
urgency, and hands the owner a clean summary card — spoken in the shop's own
voice profile, with **nothing leaving the machine**. No cloud AI sees the
customer's name, address, or phone number, and there are no per-minute fees,
which is exactly what makes a **$49/month** price possible (basic cloud AI
receptionists run ~$30–$100/mo and human answering services $200–$500+/mo).

Built by [Ghost Developer Studio](https://github.com/littlestjames82-sys)
for the DEV Hacktoberfest Open-Source AI Challenge, Week 2: "Side Hustle."

**Demo page:** https://littlestjames82-sys.github.io/after-hours-front-desk/docs/
— the recorded demo video, the simulator screenshots, and the eval
table on one page. It is recorded evidence, not a live demo: the desk
itself runs locally (see Run it, below).

## What this is — honest scope

This is a **working call-simulator demo**, not a shipped phone product:

- ✅ **Real:** the conversation brain is a real open-weight model
  (Gemma 3, via llama.cpp) running locally; every desk reply is generated
  live from the shop card, never scripted.
- ✅ **Real:** the voice is Sopro V2 Turbo (Apache-2.0) synthesizing each
  reply on this machine.
- ✅ **Real:** the end-of-call summary card is extracted by the model from
  the actual transcript (see `smoke_test.py` — it plays a full call and
  checks the card against what the "caller" said).
- 🎭 **Simulator:** the caller side is typed lines in a web page, standing
  in for a phone line. **Wiring real phone lines is the paid next step**
  and is deliberately not faked here.
- 🎭 **Demo voice profile:** the demo speaks in Sopro's bundled synthetic
  demo voice. In production the voice profile is the shop owner's own
  voice, cloned from a 5–20 second reference clip recorded **with the
  owner's consent** — that consent-first clone flow is designed (below),
  not faked: no real person's voice is used in this demo.
- 🏪 **Fictional shops:** "Oakdale Heating & Air" and "Riverbend
  Plumbing & Drain" and every caller in the demo are invented. No real
  business or customer data appears anywhere.

## v2 — a more human voice, and a second shop

The v1 voice worked but sounded robotic, so v2 worked on both layers
that make a voice feel human — and measured instead of guessing:

- **Synthesis:** a settings sweep (fixed seed, same lines) picked
  warmer Sopro sampling — temperature 0.85, top-p 0.95, top-k 40,
  **steps 8 instead of the speed-first default 2**. Steps turned out
  to refine the acoustic render of the *same* words at zero behavioral
  risk. No seed is pinned, so the greeting isn't byte-identical on
  every call. Sopro has no rate/pitch knobs; everything used is a real
  control it exposes. Full method + measurements:
  `demo-evidence/voice-ab/VOICE_NOTES.md`, with before/after WAVs.
- **The words:** the brain now writes for a mouth, not a screen —
  contractions, one thought per sentence, short acknowledgements
  ("Got it.", "Oh no — I'm sorry to hear that."), no lists read aloud.
  A speech-prep layer (`desk/speech.py`) speaks phone numbers as
  grouped digits ("four two three, five five five, …") and prices as
  words — the transcript and the summary card keep the original text.
  Extraction and emergency triage are unchanged: **smoke test still
  8/8**.
- **Second shop:** shop profiles are data (`desk/shops/*.json`), and
  the simulator now offers two — the HVAC shop and a plumbing company
  with its own services, prices, emergency rules, and scenarios.
  Retraining a desk for a new trade is editing one JSON file.
- **Owner review:** every finished call appends to a local call log
  (`call-log.jsonl`), and the simulator shows the morning list — time,
  shop, caller, urgency, summary — the thing an owner actually reads
  over coffee.

Still honest: the voice is Sopro's bundled **synthetic stand-in**,
warmer-tuned — it is not a clone of anyone, and the clone flow remains
a designed, consent-first step, not a faked one.

## How it works

```
 caller (typed, simulator) ──► desk/server.py ──► llama.cpp + Gemma (local)
                                    │                    conversation brain
                                    ├──► Sopro service ──► spoken replies
                                    └──► end of call ──► model extracts
                                                         the summary card
```

- `desk/shops/*.json` — the shop cards: services, area, prices, hours,
  and each shop's own definition of "emergency." The desk may only speak
  from its shop's card; if it doesn't know, it says the owner will confirm.
- `desk/prompts.py` — builds the system prompt from the card, plus the
  extraction prompt that produces the summary card as JSON.
- `desk/brain.py` — talks to llama-server (OpenAI-compatible endpoint),
  with a one-shot `llama-cli` fallback.
- `desk/voice.py` — Sopro via its resident HTTP service, `soprotts` CLI
  fallback.
- `web/index.html` — the simulator page: shop switcher, Call button,
  three scripted scenario openers per shop card (each shop's own:
  burst pipe, no heat with a baby in the house, water heater leaking,
  quote requests), live transcript, the owner summary card, and the
  owner morning list.
- `smoke_test.py` — headless end-to-end proof: a full scripted call,
  PASS/FAIL per stage.

## The eval — 20 scripted calls, scored field by field

A demo call proves a demo works, so the finished desk was also run
against **20 scripted caller scenarios it had never seen** (both shops;
emergencies, urgent, routine, plus vague/prank/refusal/out-of-area edge
cases), scored on urgency (by each shop's own definition) and on the
extracted name, phone, address, and job. Full write-up, per-scenario
table, and raw data: [`eval/RESULTS.md`](eval/RESULTS.md) and
`eval/results.json`; harness: `eval/run_eval.py`.

- **Urgency: 19/20 (95%)** — emergencies **8/8**
- **Extraction fields: 79/80** (name 20/20, phone 20/20, address 20/20,
  job 19/20); scenarios fully correct: 18/20
- **Zero invented details**: withheld names/numbers/addresses came back
  "not given" every time
- The two failures are named in the report, not hidden: one over-triage
  (a contained garage leak flagged emergency instead of urgent — the
  candidate fix is documented but was deliberately not applied after
  seeing the test), and the prank call whose "job" was extracted as
  "Refrigerator."
- Latency (2-core sandbox, shared box — not a production claim):
  median desk turn ≈ 24 s end to end; median summary extraction ≈ 54 s.

A short demo video of a live call (`demo-evidence/demo-video.mp4`,
29 s, with burned-in captions and a sidecar
`demo-evidence/demo-video.srt`) was captured from the real simulator
page; its frames are live viewport captures and its audio is the exact
speech the desk generated for those replies.

The simulator screenshots in `demo-evidence/`
(`simulator-mid-call.png`, `simulator-riverbend.png`,
`simulator-morning-list.png`) were re-shot against the current v2
page on Oct 13, 2026. A round-2 attempt to extend the video with the
Riverbend call captured that call's greeting and first reply (kept in
`demo-evidence/video-capture/`) before the sandbox restarted
mid-call; the shipped video stays the one complete call rather than
a padded cut. The round-1 summary-card screenshot was not re-shot
(the extraction step kept stalling under sandbox load; attempts are
logged in `demo-evidence/screenshot-*.log` and written up in
`ROUND2_CRITIQUE.md`), so the post no longer presents it as current —
the card is quoted verbatim in the post and rendered as data on the
demo page.

## Why open is the business model

The first voice engine this studio adopted for client work turned out to
ship weights under a **non-commercial** license — fine for experiments,
illegal for a paid receptionist. Sopro is **Apache-2.0**: the license is
what makes this product sellable at all. And because both the brain
(Gemma open weights, llama.cpp under MIT) and the voice run on the shop's
own hardware, the marginal cost of a call is **zero** — no API keys, no
per-minute billing, no customer data leaving the building. Open isn't a
feature of this business; it's the reason the price works.

**The arithmetic, measured on this machine:** a desk turn processes
~800–900 tokens, nearly all of it the shop-card system prompt, which
llama.cpp serves from its prefix cache after the first turn (measured:
768 of 831 prompt tokens were cache hits on turn two); the model
generates ~20 tokens per spoken reply. A full call (greeting + 3 turns
+ summary extraction) is roughly 4,500 tokens. The API bill is $0 —
there is no API. The only meter is electricity: a 65 W laptop for a
3-minute call at $0.15/kWh is about a twentieth of a cent. That is why
$49/month can be flat while per-minute cloud pricing cannot.

## Run it

Prerequisites: Python 3.10+, a llama.cpp build (`llama-server`), a Gemma
GGUF, and a Sopro install with its model files.

```bash
# 1. get the Gemma 3 4B-it open-weight model (GGUF), e.g.:
#    https://huggingface.co/ggml-org/gemma-3-4b-it-GGUF
#    (the 4B is deliberate: the 1B was tested first and rejected -
#    it mis-triaged the emergency test call and invented an address
#    the caller never gave)
# 2. point the environment at your installs (see scripts/run-demo.sh
#    for a complete worked example) and start:
AHFD_MODEL=/path/to/gemma.gguf \
AHFD_LLAMA_SERVER=/path/to/llama-server \
AHFD_SOPRO_SERVER=/path/to/sopro/server.py \
AHFD_SOPRO_PYTHON=/path/to/sopro-venv/bin/python \
AHFD_SOPRO_REF=/path/to/voice-reference.wav \
python3 desk/server.py
# 3. open http://127.0.0.1:8890 and press Call
```

Smoke test (same environment): `python3 smoke_test.py`

## The production path (designed, not built)

1. **Consent-first voice clone:** the owner records a 20-second script in
   the setup page; the clip is stored locally, used only as the Sopro
   reference, and the owner can delete it at any time. No voice is ever
   cloned without its owner's recorded consent.
2. **Phone wiring:** a telephony bridge answers the shop's real line after
   hours and streams caller audio to a local speech-to-text engine; the
   brain, voice, and summary flow are the ones demoed here.
3. **Owner delivery:** the summary card is texted to the owner; emergencies
   (per the shop's own definition on its card) are flagged for immediate
   alert.

## License

MIT — see [LICENSE](LICENSE). Gemma is provided under the Gemma Terms of
Use; llama.cpp is MIT; Sopro V2 Turbo is Apache-2.0.
