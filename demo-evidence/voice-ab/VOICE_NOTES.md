# Voice notes — v2 "more human" pass (Oct 13, 2026)

Ryan's note on v1: the voice works but sounds robotic. This pass attacks
that on the only two layers Sopro actually gives us — there is **no**
rate/pitch/expressiveness knob in Sopro V2 Turbo. What the library
(`SoproTTS.synthesize`) and the `soprotts` CLI really expose is:

- sampling: `temperature`, `top_p`, `top_k`
- acoustic refinement: `steps` (DiT sampling steps; default **2**)
- `seed`, `lang`, `max_seconds`/`min_seconds`
- sentence-aware text splitting (segments joined with prompt-token
  carry-over, so one reply stays one continuous voice)

Everything below uses only those, plus the words themselves.

## What v1 did

- Resident service called `synthesize(text)` with **all defaults**:
  temperature 0.8, top-p 0.9, top-k 25, **steps 2** — the
  speed-optimized "Turbo" settings.
- The brain wrote replies for a screen (stiff forms, hyphenated phone
  number) and the raw text went straight to the synthesizer. Sopro's own
  model card warns: *"Text frontend is minimal — numbers / abbreviations
  / symbols may mispronounce (spell them out)."*

## The settings sweep (fixed seed 42, same lines, this 2-core box)

| config | temp / top-p / top-k / steps | greeting pace | empathy pace | readback pace | readback pause fraction |
|---|---|---|---|---|---|
| v1 defaults | 0.8 / 0.9 / 25 / **2** | 16.8 ch/s | 15.9 ch/s | 12.1 ch/s | 0.08 |
| **warm (picked)** | 0.85 / 0.95 / 40 / **8** | 17.1 ch/s | 18.9 ch/s | 10.9 ch/s | **0.17** |
| expressive | 0.95 / 0.97 / 60 / 8 | 21.5 ch/s | 19.2 ch/s | 11.0 ch/s | 0.19 |
| steps-only | 0.8 / 0.9 / 25 / **8** | 16.6 ch/s | 15.9 ch/s | 12.1 ch/s | 0.08 |

What decided it:

- **Steps is a free win.** At the same seed and sampling, steps 2 vs 8
  produced the *identical* token stream (same durations to the
  hundredth) — steps only refine the acoustic render of the same words.
  Smoother sound, zero behavioral risk. The cost is generation time
  (~2× on this sandbox CPU; Sopro reports 0.24 RTF on an M3, so a real
  shop laptop barely notices).
- **"Expressive" (temp 0.95) rushed the greeting** to 21.5 chars/s —
  that's not warmth, that's hurry. Rejected.
- **"Warm" (temp 0.85 / top-p 0.95 / top-k 40)** kept the greeting at a
  natural pace and gave the phone-number readback real breathing room
  (pause fraction 0.08 → 0.17) — the moment a human slows down most.
- **No seed is pinned in production.** A fixed seed makes the greeting
  byte-identical on every call, which is its own kind of robotic. v1
  already varied per call; v2 keeps that.
- Pitch (F0) stats were measured too, but the estimator saturated on
  this bright demo voice (p90 pinned at the 300 Hz search ceiling in
  every config), so they could not separate the configs and were **not**
  used to pick. Saying so beats dressing the choice up in numbers that
  don't discriminate.

## The words changed too (the bigger half)

Synthesis settings polish the sound; the *script* was the robotic part.

1. **Brain prompt (desk/prompts.py)** — the desk is now told to talk
   like a person: contractions always, one thought per sentence, short
   human acknowledgements first ("Got it.", "Oh no — I'm sorry to hear
   that."), never read a list aloud, write the callback number as three
   spaced digit groups, warm open and close. All factual rules (what to
   ask, in what order, the emergency definition, never invent, never
   dispatch) are unchanged, and the smoke test still passes 8/8.
2. **Speech prep (desk/speech.py)** — only the copy handed to the voice
   is rewritten (the transcript and the extractor keep the original):
   - phone numbers → spoken digit groups:
     `423-555-0147` → "four two three, five five five, zero one four seven"
   - prices → words: `$89` → "eighty-nine dollars"
   - `&` → "and", curly quotes/dashes → plain ASCII (Sopro's frontend
     is minimal; give it nothing to trip on)

## A/B files in this folder

Same voice (Sopro's bundled synthetic demo voice — still a stand-in
for a consented owner clone, not a clone), same seed, rendered through
the exact pipelines:

| pair | before (v1) | after (v2) | what differs |
|---|---|---|---|
| `greeting-*.wav` | 3.34 s | 2.94 s | sampling only ("&" → "and") |
| `empathy-*.wav` | 7.99 s | 6.74 s | sampling only, identical text |
| `readback-*.wav` | 8.90 s | 9.58 s | sampling **and** spoken digit groups |

All six files verified as real speech (RMS 0.067–0.078, 89–99% active
frames; see `ab-metrics.json`). The readback pair is the one to listen
to first: v1 gets a raw hyphenated number string to chew on, v2 gets
the number the way a person would say it.

## Wiring

- Project defaults live in `desk/voice.py` (env-overridable:
  `AHFD_VOICE_TEMPERATURE/_TOP_P/_TOP_K/_STEPS`) and are sent on both
  routes — the resident service and the `soprotts` CLI fallback.
- The resident service (`sopro-test/server.py`) learned to forward the
  four optional sampling fields to `synthesize`; clients that don't
  send them (e.g. GhostCut's bridge) get model defaults exactly as
  before. Verified live: same seed + text, params change the audio.
