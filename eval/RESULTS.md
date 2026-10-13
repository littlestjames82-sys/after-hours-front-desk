# Eval results: triage accuracy + extraction, 20 scripted calls

**Run:** Oct 13, 2026, against the final v2 code (Gemma 3 4B-it Q4_K_M
via llama.cpp, Sopro V2 Turbo voice), through the desk's real HTTP API
(the same path the simulator uses). Raw per-scenario data, transcripts,
cards, and timings: `eval/results.json`. Harness: `eval/run_eval.py`;
scenarios: `eval/scenarios.json`.

The desk was not tuned against these scenarios first. They were written
from the two shops' own cards and demo scenarios, run once each, and
scored field by field: urgency must match the shop's own definition,
and the extracted name, phone, address, and job must match what the
caller actually said. Where a scenario withholds a field on purpose,
the correct extraction is "not given" - inventing one is a failure.

## Headline numbers

| Measure | Result |
|---|---|
| Urgency (triage) correct | **19 / 20 (95%)** |
| Emergencies correctly flagged | **8 / 8** |
| Urgent correctly judged | 4 / 5 (one over-triage, below) |
| Routine correctly judged | 7 / 7 |
| Extraction field checks correct | **79 / 80 (98.75%)** |
| Name | 20 / 20 |
| Phone | 20 / 20 |
| Address | 20 / 20 |
| Job | 19 / 20 |
| Scenarios fully correct (urgency + all 4 fields) | **18 / 20** |
| Fields invented that the caller never gave | **0** |
| Median desk turn, end to end (brain + voice) | 23.9 s |
| Median summary-card extraction after hang-up | 54.1 s |

Latency is sandbox latency: this build box has 2 CPU cores and is
shared with other work; the same stack on a normal shop laptop will
feel different. No latency claim is made for production hardware. The
speech itself is what a caller waits on: replies ran 1.0 to 12.0
seconds of audio per turn across the eval.

## Per-scenario results

| # | Scenario | Expected | Got | Fields |
|---|---|---|---|---|
| 1 | HVAC: no heat, baby in the house | emergency | emergency | 4/4 |
| 2 | HVAC: no heat, elderly mother on oxygen | emergency | emergency | 4/4 |
| 3 | HVAC: no heat, 12-degree night coming | emergency | emergency | 4/4 |
| 4 | HVAC: burst pipe under the sink | emergency | emergency | 4/4 |
| 5 | HVAC: smell of gas in the kitchen | emergency | emergency | 4/4 |
| 6 | HVAC: no heat, mild night, healthy adults | urgent | urgent | 4/4 |
| 7 | HVAC: AC out on a 95-degree day | urgent | urgent | 4/4 |
| 8 | HVAC: furnace banging, heat cutting out | urgent | urgent | 4/4 |
| 9 | HVAC: furnace replacement quote | routine | routine | 4/4 |
| 10 | HVAC: schedule a tune-up | routine | routine | 4/4 |
| 11 | Plumbing: burst pipe flooding laundry room | emergency | emergency | 4/4 |
| 12 | Plumbing: sewage backup into living room | emergency | emergency | 4/4 |
| 13 | Plumbing: no water at all, 79-year-old in house | emergency | emergency | 4/4 |
| 14 | Plumbing: water heater leaking in garage | urgent | **emergency** | 4/4 |
| 15 | Plumbing: slow kitchen drain, price question | routine | routine | 4/4 |
| 16 | Plumbing: faucet replacement quote | routine | routine | 4/4 |
| 17 | Edge: vague caller, funny-tasting water | routine | routine | 4/4 |
| 18 | Edge: prank call (refrigerator joke) | routine | routine | 3/4 |
| 19 | Edge: caller refuses phone and address | routine | routine | 4/4 |
| 20 | Edge: caller outside the service area | urgent | urgent | 4/4 |

## The failures, named

**1. Scenario 14: an over-triage (urgent judged emergency).**
The caller reported a water heater "leaking all over the garage floor
and the puddle keeps growing," and said tomorrow morning was fine. The
shop's card calls a burst pipe or an active leak *flooding the home*
an emergency; a contained garage leak the owner is watching is urgent
in the shop's own demo scenario. The extractor read "active leak" plus
"growing puddle" and flagged emergency. Every other field was exact.
This failure fails toward sending help faster, not toward missing a
real emergency - but it is a miss against the shop's definition, and
it is reported as one. A candidate fix is one more sentence of
extraction guidance (a contained leak outside living space is urgent
unless it is flooding living space). It is deliberately **not**
applied here: the eval was run once, on the shipping prompts, and
retuning after seeing the test would make the 19/20 number mean less.
The fix is listed as future work, and this paragraph is the receipt
that it was found in testing, not in production.

**2. Scenario 18: the prank call's "job."**
A caller opened with the refrigerator joke, then apologized and said
nobody needed anything. The extractor still had to fill the card, and
it wrote job: "Refrigerator" - with a summary claiming the caller
"inquired about a refrigerator issue," which is not what happened. The
urgency (routine) and the other fields (all correctly "not given") were
right. A front desk that files a joke call as no job at all would be
better; today it files the joke. Named, not hidden.

## What the edge cases proved

- **Nothing was invented.** Across the vague caller (scenario 17), the
  prank (18), and the refusal (19), withheld names, numbers, and
  addresses came back "not given" every time - the exact failure
  (an invented "123 Maple Street") that disqualified Gemma 3 1B during
  model selection. Scenario 17's card reads, in full: name "Sam",
  phone "not given", address "not given", job "funny tasting water".
- **The safety instruction fired in conversation, not just on paper.**
  On the gas call (scenario 5), the desk's first reply to the problem
  was: "Oh no – I’m sorry to hear that. Please leave the house
  immediately and call 911." - before it
  asked for a name. The summary card repeats the advice.
- **The out-of-area caller (20)** still got a complete, accurate card
  (name, Knoxville number, "500 Gay Street, Knoxville", AC out,
  urgent) - the desk takes the message; a human decides coverage.

## How the run actually went (infrastructure honesty)

The sandbox this was built in restarts and kills long-lived processes
without warning; during this eval the local model server died and was
restarted repeatedly, and two scenarios needed a retry of a failed HTTP
call after the desk returned a 500 caused by a dead backend (retries
are recorded per scenario in `results.json`; one scenario also ran on
the desk's built-in per-call fallback path). No scenario's *answers*
were touched by any of this - every reply and card is live model
output - but the wall-clock latencies carry that noise, which is one
more reason they are reported as sandbox numbers only. Final results
were assembled from the batch runs and a set of per-scenario
fresh-stack runs (`eval/run_singles.sh`); every partial file is kept
in `eval/` next to this report.

## Reproduce

```bash
source scripts/env-sandbox.sh
python3 eval/run_eval.py            # all 20 scenarios
python3 eval/run_eval.py --only edge-prank   # just one
```
