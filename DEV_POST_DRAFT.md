# DRAFT — DO NOT PUBLISH (Ryan approves all posts)

**Title:** I built my clients an after-hours front desk that runs on their
own laptop — in their own voice, with no cloud AI

**Categories:** Overall · Best Use of Gemma
**Repo:** https://github.com/littlestjames82-sys/after-hours-front-desk

---

## What I built

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
step, and I'm not going to pretend otherwise. The shop in the demo is
fictional, and the voice is a demo profile standing in for the owner's
own consented voice clone.

## Who pays, and why

Solo and two-truck trade shops lose real money to missed evening calls —
the job goes to the next name on Google. Cloud AI receptionists run
~$30–$100/mo, human answering services $200–$500+/mo. I'd sell this at
**$49/mo**, and the reason that price works is the whole point of this
post: there are no per-minute API fees to pass on, because nothing is
billed per call. A shop that already sells the customer a furnace can
afford a front desk that costs less than the gas to drive out and quote it.

## Why open isn't a feature here — it's the business model

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

And because both halves run locally, a customer's name, address, and
phone number never leave the shop's laptop. For a small business, "your
customers' details never go to a cloud AI" is not a compliance checkbox —
it's a sentence the owner can say out loud to the person across the
counter.

## How it's built

- **Brain:** Gemma 3 4B-it (Q4_K_M GGUF) served by llama.cpp on
  localhost. The system prompt is generated from a one-page "shop card"
  (services, area, prices, hours, the shop's own definition of
  *emergency*), and the desk is forbidden from speaking beyond it.
- **Voice:** Sopro V2 Turbo, cloned-voice TTS on CPU, resident as a local
  service so replies don't pay a model-load each time.
- **Summary:** at hang-up, the same local model extracts the owner card
  as structured JSON from the transcript. A headless smoke test plays a
  full scripted call and checks every field against what the caller
  said — 8/8 passing.
- **Cost of goods:** $0. Open weights, open engines, the shop's hardware.

## What's next

1. Consent-first voice setup: the owner records a 20-second script;
   that clip — and only that clip — becomes their front desk's voice.
2. The phone bridge: answer the real line after hours, local
   speech-to-text on the caller side, same brain, same voice, same card.
3. First real shop: one of the trade businesses I already build for gets
   a free first month; their missed calls are the test data.

The code's MIT and the demo runs on any machine with a few spare cores.
If you run a small shop: what does a missed 7 PM call cost you?

— Ryan Cotten, Ghost Developer Studio, Oakdale, TN
