# DRAFT — DO NOT PUBLISH (Ryan approves all posts)
#
# Rewritten Oct 13, 2026 to the winning shape (held-out eval, honest
# failures, hard numbers, video up top) per the Week 2 win research.
# Posting checklist for Ryan:
# 1. In DEV's editor, paste everything BELOW the marker line (front
#    matter included — DEV reads title + tags from it).
# 2. Tags: devchallenge + hf26challenge are the REQUIRED template tags;
#    hacktoberfest + opensource fill the other two slots DEV allows.
# 3. In the Demo section, upload the demo video (repo file
#    demo-evidence/demo-video.mp4) and the four screenshots where the
#    HTML comments mark the spots. DEV does not render GitHub-relative
#    paths, so every one of these assets must be uploaded into DEV's
#    editor directly; the repo paths in the comments are just labels
#    for which file goes where. HTML comments do not render, so a
#    missed one will not show in the published post.
# 4. If the editor offers an AI-assistance disclosure toggle, set it.
#    The challenge FAQ allows AI use; this build was AI-assisted, and
#    the post says so in plain text as well.
# 5. Publish before Oct 18, 2026, 11:59 PM PDT. One submission only.
#
# Categories: Overall (automatic) · Best Use of Gemma (entered in the
# Prize Categories section at the bottom, as the rules require)
# Repo: https://github.com/littlestjames82-sys/after-hours-front-desk

===== POST — COPY EVERYTHING BELOW THIS LINE =====

---
title: I built an after-hours front desk that runs on the shop's own laptop, in the owner's voice, with no cloud AI
published: true
tags: devchallenge, hf26challenge, hacktoberfest, opensource
---

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 2: Side Hustle](https://dev.to/challenges/hacktoberfest-week2-2026-10-12)*

## The call every small shop misses

It is 7:04 PM in East Tennessee. The shop is dark, the trucks are
parked, and the owner is at the kitchen table. The office phone rings
four times and goes to voicemail. On the other end is a homeowner whose
heat just quit, with a baby in the house, deciding which name on Google
to try next. She does not leave a message. Almost nobody does. She
calls the next shop.

I build software for small trade businesses out here: HVAC companies,
plumbers, excavators, tree crews. Most of them are one or two trucks.
They cannot staff a phone at night, and the answering services they can
afford sound like answering services. So I built them a front desk that
answers after hours, in the shop's own voice, from a computer the shop
already owns. It holds a real conversation, figures out how urgent the
problem is by the shop's own definition of urgent, and leaves the owner
a clean summary card to work from in the morning.

One honest note before the demo: the first voice engine I picked for
this carried a non-commercial license, which would have made the whole
product illegal to sell. Catching that line is part of the story below,
because a side hustle lives or dies on exactly that kind of fine print.

## What I Built

**After-Hours Front Desk**: a voice receptionist for small trade shops
that runs entirely on the shop's own computer. No cloud AI bills per
call, no customer data leaving the building.

When a call comes in, the desk answers out loud, asks what the problem
is, takes a name, a callback number, an address, and a requested time,
judges the urgency against the shop's own written rules, and at hang-up
extracts a summary card like this one (real output from a real demo run,
not a mock-up):

> **Caller:** Sarah Daniels · **Phone:** 423-555-0147 · **Job:** Heat quit
> **Urgency: emergency** · **Address:** 418 Pine Street, Oakdale
> *"Heat failure with a four-month-old baby in the house."*

Finished calls also land in an owner review list, the "morning list,"
so the day starts with every after-hours call already sorted.

**What is built today, labeled plainly:** a call simulator. You type
the caller's side into a browser page; the desk thinks and speaks out
loud for real. Wiring it to an actual phone line, with local
speech-to-text for the caller's voice, is the paid next step, and I am
not going to pretend it is done. The two shops in the demo, an HVAC
company and a plumbing company you can switch between, are fictional.
The voice is a bundled demo profile standing in for the shop owner's
own consented voice clone, which is how the paid version works.

**Who pays and why:** the buyer is the owner of a one or two-truck
shop who loses evening jobs to the next name on Google. Cloud AI
receptionists run about $30 to $100 a month; human answering services
run $200 to $500 or more. I would sell this at **$49 a month**, flat.
The math section below explains why flat is even possible: when the
brain and the voice run on hardware the shop already owns, there is no
per-minute meter running to pass along.

## Demo

<!-- RYAN: upload demo-evidence/demo-video.mp4 here, at the top of this section. -->

The video above is two real calls, recorded live in the simulator: a
no-heat call with a baby in the house at the HVAC shop, and a burst
pipe at the plumbing shop. Both are answered by the local model and
spoken by the local voice, and each ends on its owner summary card.
Nothing in it is a mock-up: the frames are the actual page during the
calls, and the audio is the exact speech the desk generated for those
replies.

<!-- RYAN: upload demo-evidence/simulator-mid-call.png here. -->

A call in progress: the desk holding the conversation and asking for
the details it needs.

<!-- RYAN: upload demo-evidence/simulator-riverbend.png here. -->

The second demo shop, Riverbend Plumbing & Drain, in the same
simulator. A shop is one JSON profile: its own services, prices,
service area, and definition of emergency. Retooling the desk for a
different trade is editing that file, not retraining anything.

<!-- RYAN: upload demo-evidence/simulator-morning-list.png here. -->

Owner review, the morning list: every finished call lands here,
flagged by urgency, before the owner's first coffee. This list is
the surface the whole product exists to produce.

<!-- RYAN: upload demo-evidence/simulator-summary-card.png here. -->

And the card itself, from a real call driven through this same page:
name, callback number, job, urgency, address, and what the caller
asked for, extracted by the same local model at hang-up. The desk's
closing readback sits above it, and the call is already filed in the
morning list below it.

Everything in the repo's `demo-evidence/` folder is from real runs:
the video and its caption file, the screenshots, a full recorded call
(`sample-call.wav`) with its transcript, the before and after voice
clips from the tuning sweep described below, and the eval outputs in
`eval/`.

I also put up a [demo page](https://littlestjames82-sys.github.io/after-hours-front-desk/docs/)
that gathers the video, the screenshots, and the eval table in one
place. Be clear about what it is: a page of recorded evidence, not
the desk running live. The desk itself only runs locally, on purpose:
a customer's details should not have to leave the building to get a
call answered. To run the real thing, follow the README's Run section
(a worked example, with the exact paths from my machine), start
`desk/server.py`, and press Call.

## The eval: 20 scripted calls the desk had never seen

A demo call proves a demo works. So after the build, I wrote 20
scripted caller scenarios and ran them against the finished desk
through its real API, scoring what came back field by field:
emergencies, urgent jobs, and routine work across both demo shops,
each judged by that shop's own written definition of emergency, plus
edge cases (a vague caller, a prank call, a caller who refuses to give
a number or an address, a caller outside the service area).

The desk was not tuned against these scenarios first. They were run
once each, as written. Full data, transcripts, and timings are in
`eval/RESULTS.md` and `eval/results.json` in the repo.

| Measure | Result |
|---|---|
| Urgency judged right | **19 of 20 (95%)** |
| Emergencies flagged as emergencies | **8 of 8** |
| Extraction fields right (name, phone, address, job) | **79 of 80** |
| Scenarios completely right | 18 of 20 |
| Details invented that the caller never gave | **0** |

The two failures, named on purpose:

1. **An over-triage.** A caller reported a water heater leaking across
   a garage floor, puddle growing, and said tomorrow morning was fine.
   The shop's card reserves "emergency" for a leak flooding the home,
   so the expected answer was urgent. The extractor read "active leak,
   growing puddle" and flagged emergency. Every other field was exact.
   It fails toward sending help faster, but it is a miss, and it is
   reported as one. The likely fix is one sentence of extraction
   guidance about contained leaks. I have deliberately not applied it:
   retuning after seeing the test would make the 19 of 20 mean less.
   The fix is written down in the eval report as future work, with
   this failure next to it.
2. **The prank call.** A caller opened with the "is your refrigerator
   running" joke, then apologized and said nobody needed anything. The
   extractor still had to fill the card, and it wrote job:
   "Refrigerator." Urgency (routine) and the withheld fields (correctly
   "not given") were right. A better desk files a joke call as no job
   at all. Today it files the joke.

What the edge cases proved matters more to me than the headline
number. Across the vague caller, the refusal, and the prank, withheld
names, numbers, and addresses came back "not given" every single time.
Nothing was invented. That specific failure, a model making up an
address, is what got the smaller model fired from this project (see
the Gemma comparison below). And on the call where the caller smelled
gas, the desk's first reply was: "Oh no, I'm sorry to hear that.
Please leave the house immediately and call 911." Safety advice first,
intake questions second. That ordering is in the shop card, and the
eval caught it working in conversation, not just written in a prompt.

On speed, I will only claim what I measured: on my 2-core build box, a
desk turn end to end (brain plus voice) took a median of about 24
seconds, and the summary card about 54 seconds after hang-up. Sandbox
numbers, not a production promise. The speech ran 1 to 12 seconds per
reply.

## The math: why $49 flat is not a fantasy price

I measured what one call actually costs this system, on the record,
with the real shop prompt loaded:

- Each desk turn processes roughly 800 to 900 tokens, and nearly all of
  it is the shop card system prompt. llama.cpp caches that prefix, so
  after the first turn of a call, most of it is served from cache (on
  the second turn I measured, 768 of 831 prompt tokens were cache
  hits). The model only generates about 20 tokens per spoken reply.
- A full call, greeting plus three turns plus the summary extraction,
  comes to roughly 4,500 tokens total.
- The API bill for those tokens is $0. There is no API.
- The electricity is the only meter running: even charging a 65-watt
  laptop for a whole 3-minute call at $0.15 per kilowatt-hour works out
  to about a twentieth of a cent.

So the marginal cost of call number 500 is the same as call number 1:
effectively nothing. That is what makes a flat $49 a month honest.
Per-minute cloud pricing has to charge for the meter; this design does
not have one. And the privacy story (customer details never leave the
building) falls out of the same architecture instead of being a policy
someone has to trust.

## Code

**Repo:** https://github.com/littlestjames82-sys/after-hours-front-desk
(MIT)

The pieces worth reading: `desk/prompts.py` (the system prompt is
generated from a one-page shop card, including the shop's own
definition of emergency and its safety rules), `desk/speech.py` (the
speech-prep pass every reply goes through), `desk/shops/` (each
business is one JSON profile), `eval/` (the 20-scenario harness and
its full results), and `smoke_test.py` (a headless end-to-end check
that plays a scripted call and verifies every field of the summary
card; 8 of 8 on the final code).

## How I Built It

The whole call path, on one machine:

```
caller (typed, simulator) --> desk/server.py --> llama.cpp + Gemma 3 4B
                                    |              conversation, triage,
                                    |              safety rules
                                    +----------> Sopro V2 Turbo
                                    |              spoken replies
                                    '--> at hang-up: Gemma extracts
                                         the owner summary card
```

**Brain:** Gemma 3 4B-it (Q4_K_M GGUF) served by llama.cpp on
localhost. The desk may only speak from the shop card: services, area,
prices, hours, and the emergency definition. If a caller asks for
something outside the card, the desk takes a message instead of
improvising.

**The Gemma choice was empirical.** I started with the 1B to keep
things light. It did not survive contact with the test call:

| Same test call, two models | Gemma 3 1B | Gemma 3 4B |
|---|---|---|
| No heat + baby, shop defines it as emergency | Judged "urgent" in 2 of 3 runs | Judged emergency, every run |
| Address the caller never gave | Invented "123 Maple Street" | "not given" |
| Job extraction on an early run | Wrote "customer" | "Heat quit" |
| 20-scenario held-out eval | Not run; it had already failed selection | 19/20 urgency, 79/80 fields |

The 4B is slower on my little build box. It is also the difference
between a demo and something a shop could trust at 7 PM. A front desk
that occasionally invents an address is a liability with a phone
number.

**Voice:** Sopro V2 Turbo, open-weights voice cloning that runs on CPU,
kept resident as a local service so replies do not pay a model load
each time. The demo voice is a bundled synthetic profile, labeled as
such everywhere it appears.

**The robot was not in the voice.** My first demo sounded like a
voicemail system from 2009, so I went looking for an expressiveness
knob, and Sopro does not have one: no rate, no pitch, just sampling
controls and a step count for how much each sound gets refined. So I
measured instead of guessing. A fixed-seed sweep (write-up and before
and after clips in `demo-evidence/voice-ab/`) showed more refinement
steps made the same words smoother with zero behavioral risk, and
warmer sampling gave the readbacks room to breathe. But the bigger fix
was the script: the brain was writing for a screen. Now it writes for
a mouth: contractions, short sentences, "Got it." and "Oh no, I'm
sorry to hear that.", and a speech-prep pass that turns phone numbers
into grouped spoken digits and prices into words before anything is
spoken. The transcript and the summary card keep the original text;
only the spoken form is shaped.

**Shops are data.** Each business is one JSON profile: name, services,
prices, area, emergency definition, demo scenarios. Onboarding a real
trade is editing a file, not retraining anything. Finished calls
append to a local call log behind the morning list.

## Why Does Open Innovation Matter?

Because this product exists only where open licenses let it.

The first voice engine I adopted for paid studio work shipped its
weights under a non-commercial license. Good engine, and completely
unusable for a receptionist somebody pays for. That is the kind of
detail that kills a side hustle quietly, after the demo already works.
I switched to **Sopro** (Apache-2.0), a small voice-cloning model that
runs on a plain CPU, and the $49 price became legal to charge. Gemma's
weights, llama.cpp (MIT), Sopro (Apache-2.0): every layer of this stack
is something a one-person studio can build a business on without
asking permission or paying a toll per call. The openness is not a
philosophy section in this post. It is the bill of materials.

It also changes who gets to have this. A per-minute cloud receptionist
is priced for businesses that already have margin. A local one, on a
laptop the shop owns, is priced for a two-truck shop in rural
Tennessee. Open weights are why that second product can exist at all.

## What's Next

1. **A first real pilot shop.** The honest status is that no shop is
   using this yet, and the next step is not more features. It is
   finding one trade business I already work with to run it as a pilot
   and tell me what the morning list gets wrong. That search is the
   work now, and I would rather say so than dress up a demo as
   traction.
2. **Consent-first voice setup:** the owner records a short script;
   that clip, and only that clip, becomes their front desk's voice.
3. **The phone bridge:** answer the real line after hours, local
   speech-to-text on the caller side, same brain, same voice, same
   card. Plus the contained-leak extraction fix the eval found,
   verified against fresh scenarios rather than the ones that exposed
   it.

<!-- PILOT SLOT: if a pilot shop signs on before the deadline, write the debrief here: who they are (with permission), what they said after the first morning list, and one thing they asked to change. Do not publish this comment. -->

The code is MIT and the demo runs on any machine with a few spare
cores. If you run a small shop: what does a missed 7 PM call cost you?

Ryan Cotten, Ghost Developer Studio, Oakdale, TN

*Disclosure: this project and this post were built with an AI coding
assistant, which the challenge FAQ expressly allows. Every result
quoted above is from runs on my machine, and the failures are reported
the same way as the passes.*

## My Agent Session

This project was designed, built, and tested with an AI coding
assistant working in my studio environment. The shop-card prompt
system, the speech-prep pass, the measured voice tuning sweep, the
20-scenario eval harness, and this post all came out of that
workflow, and the two eval failures above were caught and written
down inside it. I am not linking a hosted session replay: the
environment I build in keeps its sessions local, and I would rather
say that plainly than dress up a transcript export as one. The repo
is the record instead: the eval harness and its raw results, the
voice A/B notes, and the build reports are all in it, in the open.

## Prize Categories

**Best Use of Gemma**: Gemma 3 4B-it, running locally via llama.cpp, is
the desk's entire brain. It holds the spoken conversation, follows the
shop card's triage and safety rules, and extracts the owner summary
card. The choice was measured, not assumed: the 1B mis-triaged the
emergency test call and invented an address; the 4B passed the same
call, then scored 19 of 20 on urgency and 79 of 80 on extraction
across 20 held-out scripted scenarios. Gemma is not a component in
this build. It is the employee.
