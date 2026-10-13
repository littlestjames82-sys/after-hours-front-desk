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
- 🏪 **Fictional shop:** "Oakdale Heating & Air" and every caller in the
  demo are invented. No real business or customer data appears anywhere.

## How it works

```
 caller (typed, simulator) ──► desk/server.py ──► llama.cpp + Gemma (local)
                                    │                    conversation brain
                                    ├──► Sopro service ──► spoken replies
                                    └──► end of call ──► model extracts
                                                         the summary card
```

- `desk/shop.json` — the shop card: services, area, prices, hours, and the
  shop's own definition of "emergency." The desk may only speak from this
  card; if it doesn't know, it says the owner will confirm.
- `desk/prompts.py` — builds the system prompt from the card, plus the
  extraction prompt that produces the summary card as JSON.
- `desk/brain.py` — talks to llama-server (OpenAI-compatible endpoint),
  with a one-shot `llama-cli` fallback.
- `desk/voice.py` — Sopro via its resident HTTP service, `soprotts` CLI
  fallback.
- `web/index.html` — the simulator page: Call button, three scripted
  scenario openers (burst pipe, no heat with a baby in the house, quote
  request), live transcript, and the owner summary card.
- `smoke_test.py` — headless end-to-end proof: a full scripted call,
  PASS/FAIL per stage.

## Why open is the business model

The first voice engine this studio adopted for client work turned out to
ship weights under a **non-commercial** license — fine for experiments,
illegal for a paid receptionist. Sopro is **Apache-2.0**: the license is
what makes this product sellable at all. And because both the brain
(Gemma open weights, llama.cpp under MIT) and the voice run on the shop's
own hardware, the marginal cost of a call is **zero** — no API keys, no
per-minute billing, no customer data leaving the building. Open isn't a
feature of this business; it's the reason the price works.

## Run it

Prerequisites: Python 3.10+, a llama.cpp build (`llama-server`), a Gemma
GGUF, and a Sopro install with its model files.

```bash
# 1. get a Gemma open-weight model (GGUF), e.g.:
#    https://huggingface.co/ggml-org/gemma-3-1b-it-GGUF
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
