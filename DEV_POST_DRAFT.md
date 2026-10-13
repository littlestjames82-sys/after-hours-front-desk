# DRAFT — DO NOT PUBLISH (Ryan approves all posts)
#
# Restructured Oct 13, 2026 to the OFFICIAL Week 2 submission template
# (audit: COMPLIANCE.md in this repo). Posting checklist for Ryan:
# 1. In DEV's editor, paste everything BELOW the marker line (front
#    matter included — DEV reads title + tags from it).
# 2. Tags: devchallenge + hf26challenge are the REQUIRED template tags;
#    hacktoberfest + opensource fill the other two slots DEV allows.
# 3. In the Demo section, upload the two screenshots from the repo
#    (demo-evidence/simulator-mid-call.png and
#    demo-evidence/simulator-summary-card.png) where marked.
# 4. If the editor offers an AI-assistance disclosure toggle, set it —
#    the challenge FAQ allows AI use, and this build was AI-assisted.
# 5. Publish before Oct 18, 2026, 11:59 PM PDT. One submission only.
#
# Categories: Overall (automatic) · Best Use of Gemma (entered in the
# Prize Categories section at the bottom, as the rules require)
# Repo: https://github.com/littlestjames82-sys/after-hours-front-desk

===== POST — COPY EVERYTHING BELOW THIS LINE =====

---
title: I built my clients an after-hours front desk that runs on their own laptop — in their own voice, with no cloud AI
published: true
tags: devchallenge, hf26challenge, hacktoberfest, opensource
---

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 2: Side Hustle](https://dev.to/challenges/hacktoberfest-week2-2026-10-12)*

## What I Built

**After-Hours Front Desk** — a voice receptionist for small trade shops
(HVAC, plumbing, excavation, tree work) that runs *entirely on the shop's
own computer*.

When a call comes in after hours, it answers in the shop's own voice
profile, holds a real conversation — what's the problem, your name,
callback number, address, how urgent is it — and hands the owner a clean
summary card:

> **Caller:** Sarah Daniels · **Phone:** 423-555-0147 · **Job:** Heat quit
> **Urgency: emergency** · **Address:** 418 Pine Street
> *"Heat failure with a four-month-old baby in the house."*

(That card is real output from the demo below, extracted by the model
from the actual call transcript — not a mock-up.)

**Demo, honestly labeled:** what's built today is a call *simulator* —
you type the caller's side in a browser page, and the front desk thinks
and speaks out loud for real. Wiring actual phone lines is the paid next
step, and I'm not going to pretend otherwise. The two shops in the
demo — an HVAC shop and a plumbing company, switchable in the
simulator — are fictional, and the voice is a demo profile standing in
for the owner's own consented voice clone.

**Who pays, and why.** Solo and two-truck trade shops lose real money to
missed evening calls — the job goes to the next name on Google. Cloud AI
receptionists run ~$30–$100/mo, human answering services $200–$500+/mo.
I'd sell this at **$49/mo**, and the reason that price works is the whole
point of this post: there are no per-minute API fees to pass on, because
nothing is billed per call. A shop that already sells the customer a
furnace can afford a front desk that costs less than the gas to drive
out and quote it.

## Demo

The demo is a local call simulator: a browser page where you type the
caller's side, and the desk answers out loud. Everything in the repo's
`demo-evidence/` folder is from real runs on my machine:

- `simulator-mid-call.png` — a call in progress: the desk holding the
  conversation and asking for the details it needs.
  [UPLOAD THIS SCREENSHOT HERE]
- `simulator-summary-card.png` — the same call at hang-up: the owner
  summary card the model extracted from the transcript.
  [UPLOAD THIS SCREENSHOT HERE]
- `sample-call.wav` + `sample-call-transcript.json` — a full spoken
  call and its transcript, and `voice-ab/` — the before/after voice
  clips from the tuning sweep described below.
- `smoke_test.py` — the headless proof: it plays a full scripted call
  (heat quit, baby in the house) and checks every field of the summary
  card against what the caller said. **8/8 passing.**

To run it yourself: clone the repo, point it at a Gemma GGUF, a
llama.cpp build, and a Sopro install (the README's Run section is a
worked example), start `desk/server.py`, and press Call. There is no
hosted demo — it runs on your machine for the same reason the product
does: nothing about a call should leave the building.

## Code

**Repo:** https://github.com/littlestjames82-sys/after-hours-front-desk
(MIT)

The pieces worth reading: `desk/prompts.py` (the system prompt is
generated from a one-page shop card), `desk/speech.py` (the speech-prep
pass), `desk/shops/` (each business is one JSON profile), and
`smoke_test.py` (the 8/8 end-to-end check).

## How I Built It

- **Brain:** Gemma 3 4B-it (Q4_K_M GGUF) served by llama.cpp on
  localhost. The system prompt is generated from a one-page "shop card"
  (services, area, prices, hours, the shop's own definition of
  *emergency*), and the desk is forbidden from speaking beyond it.
- **Voice:** Sopro V2 Turbo, cloned-voice TTS on CPU, resident as a local
  service so replies don't pay a model-load each time. Tuned sampling
  (warmer than the speed-first defaults), and every reply passes a
  speech-prep pass — numbers and prices become words before they're
  spoken; the transcript and summary card keep the original text.
- **Shops are data:** each business is one JSON profile (name, services,
  prices, emergency definition, demo scenarios). Two fictional shops
  ship in the demo; onboarding a new trade is editing a file, not
  retraining anything. Finished calls append to a local call log the
  owner reviews in the morning.
- **Summary:** at hang-up, the same local model extracts the owner card
  as structured JSON from the transcript. A headless smoke test plays a
  full scripted call and checks every field against what the caller
  said — 8/8 passing.
- **Cost of goods:** $0. Open weights, open engines, the shop's hardware.

## Why Does Open Innovation Matter?

Two stories from actually building this:

**The license that almost sank the product.** The first voice engine I
adopted for my studio's paid work turned out to ship its weights under a
*non-commercial* license. Great engine — and completely unusable for a
receptionist somebody pays for. I switched the studio to **Sopro**
(Apache-2.0), a 120M-parameter voice-cloning model that runs on a plain
CPU. That license line is the difference between a demo and a business.

**The brain had to earn its job.** I started with Gemma 3 1B to keep
things light. It failed my own test call: it rated a no-heat house with
a four-month-old baby as merely "urgent" instead of the shop-defined
**emergency**, and once it invented a street address the caller never
gave. So the desk runs **Gemma 3 4B** via llama.cpp (MIT) — same test
call, every field right: name, phone, address, job, and *emergency*,
called exactly the way the shop's own card defines it. Bigger model,
slower on my little 2-core build box, correct where it counts. A front
desk that occasionally invents an address isn't a product; it's a
liability with a phone number.

**The robot wasn't in the voice.** My first demo sounded like a
voicemail system from 2009, so I went looking for the "expressiveness"
knob — and Sopro doesn't have one. No rate, no pitch, no warmth slider;
just sampling controls and how many refinement steps each sound gets.
So I measured instead of guessing: a fixed-seed sweep over the
sampling settings (the write-up and before/after clips are in the repo,
`demo-evidence/voice-ab/`). More refinement steps made the same words
sound smoother at zero behavioral risk, and warmer sampling gave the
callback-number readback room to breathe. But the bigger fix was the
script: the brain was writing for a screen. Now it writes for a mouth —
contractions, short sentences, "Got it." and "Oh no — I'm sorry to hear
that.", and phone numbers spoken as grouped digits ("four two three,
five five five…") instead of a hyphenated string no human would say.
Same facts, same triage, same 8/8 test — it just sounds like a person
who works there.

And because both halves run locally, a customer's name, address, and
phone number never leave the shop's laptop. For a small business, "your
customers' details never go to a cloud AI" is not a compliance checkbox —
it's a sentence the owner can say out loud to the person across the
counter.

## What's Next

1. Consent-first voice setup: the owner records a 20-second script;
   that clip — and only that clip — becomes their front desk's voice.
2. The phone bridge: answer the real line after hours, local
   speech-to-text on the caller side, same brain, same voice, same card.
3. First real shop: one of the trade businesses I already build for gets
   a free first month; their missed calls are the test data.

The code's MIT and the demo runs on any machine with a few spare cores.
If you run a small shop: what does a missed 7 PM call cost you?

— Ryan Cotten, Ghost Developer Studio, Oakdale, TN

## Prize Categories

**Best Use of Gemma**: Gemma 3 4B-it runs locally via llama.cpp and is
the desk's entire brain — it holds the spoken conversation and extracts
the owner summary card from the transcript. Choosing it was empirical:
Gemma 3 1B failed the test call on emergency triage and invented an
address; the 4B passes every field, which is the difference between a
demo and something a shop could trust at 7 PM.
