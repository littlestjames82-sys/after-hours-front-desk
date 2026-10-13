# Round 2 critique — round 1 outputs vs the win research

Critiqued Oct 13, 2026, against
`~/workspace/research_notes/dev-hacktoberfest-week2-winning-research-20261013-0639/report.md`
(the Weekend Challenge winner anatomy, the Week 2 field snapshot, and
the ranked improvement list), plus COMPLIANCE.md's template list.

## What round 1 already had right (no change)

- Held-out eval with both failures named and no retuning (research
  items #3/#7; the Gemma winner's exact pattern).
- Measured unit economics reframing $49 flat (research #6).
- Story opening, closing question, honest simulator disclosure,
  correct tags, Prize Categories with specifics for Gemma only,
  11-12 minute read (research #4/#9/#10).
- Demo video with real audio exists (research #2) — but see F6.

## Findings and fixes

**F1. No "My Agent Session" section.** The research's template
reconstruction (from published Week 2 entries) includes it, and the
announcement says showing your work helps judges understand the
process. The draft had only the closing disclosure line.
FIX: added a short, honest "My Agent Session" section before Prize
Categories. It states the build was AI-assisted and that no hosted
session replay is linked, because sessions in this environment stay
local — rather than dressing up an export as a DevRelay link.

**F2. Demo section said "There is no hosted demo."** True in round 1,
but the research's mitigation ladder for a local-only voice product is
explicit: (1) video with real audio, (2) a hosted page replaying
recorded real conversations, honestly labeled, (3) full hosted
inference (not needed). Round 2 builds step 2, so the sentence became
both stale and a missed rung.
FIX: built `docs/index.html` (demo video, fresh screenshots, eval
table, plainly labeled as recorded evidence, not a live desk) and
rewrote the paragraph to link it and say exactly what it is and is
not. OUTCOME: GitHub Pages was enabled via the API with the repo
root as source (no account action needed from Ryan), the build
completed, and the page, video, and images were verified serving:
https://littlestjames82-sys.github.io/after-hours-front-desk/docs/

**F3. The morning list and the second shop were described but never
shown.** Winners were screenshot-dense; the morning list is this
product's owner-facing surface, and Riverbend proves "shops are
data." The post had markers for only two screenshots.
FIX: re-shot the v2 UI (see F4) and added upload markers +
captions for `simulator-riverbend.png` and
`simulator-morning-list.png` in the Demo section.

**F4. The two existing screenshots predated v2.** File timestamps:
the shots are from 04:40/04:47 UTC, the current `web/index.html` is
05:45 UTC. They showed the v1 page (no shop switcher state, no
morning list).
FIX: re-shot against the current page: Oakdale mid-call, Oakdale
summary card, Riverbend selected, and the morning list after real
calls. Same filenames for the two originals so existing markers and
README references stay valid.

**F5. No architecture visual in the post.** The README has one; the
post asked judges to assemble the stack from prose.
FIX: added the compact flow diagram at the top of How I Built It.

**F6. Demo video covered one call, one shop (29 s vs the ~90 s
target).** Round 1 reported four failed Riverbend capture attempts
(sandbox load / VM restarts) and shipped the single complete call
rather than padding.
ROUND 2 OUTCOME: the attempt was made Oct 13, 2026 and the sandbox
killed it again. The capture (AHFD_CAPTURE_ONLY=plumb) recorded the
Riverbend greeting (frame + real audio, 4.3 s) and the first reply
(frame + real audio, 3.3 s; both in demo-evidence/video-capture/),
then the VM restarted mid-call (uptime 1 minute at the next check)
before the second reply and the summary card. Per the round's own
rule — one attempt, no padding, no looping — the shipped video stays
the 29 s single-call cut. The partial Riverbend frames/audio remain
in the capture folder as artifacts of the attempt, clearly not a
complete call, and are not assembled into anything.

**F7. README Run section pointed at the Gemma 3 1B GGUF** — the
model this project tested and rejected for mis-triaging an emergency
call and inventing an address. A judge following the README would
reproduce the failure mode the post describes.
FIX: points at the 4B GGUF, with the reason stated in one line.

**F8. README described the simulator's scenario openers with v1
wording** ("three scripted scenario openers (burst pipe, no heat
...)"). In v2 each shop card carries its own three openers.
FIX: wording updated to per-shop openers, and the bullet now names
the shop switcher and the morning list.

**F9. README had no pointer to the demo page.**
FIX: added a Demo page line after the intro (URL if Pages enabled;
otherwise the `docs/` path in the repo).

**F10. Draft header checklist said "the two screenshots."**
FIX: updated to four screenshots + video.

## Addendum — how the F4 re-shoot actually went (Oct 13, 2026)

Five attempts, all against the real stack; the sandbox fought every
one, the same way it fought the eval and the video capture:

1. `scripts/screenshot_v2.py` (browser-driven, both full calls):
   the fresh mid-call shot landed, then the summary card never
   appeared — the local model server had died mid-session (found
   dead afterward; the eval documented the same failure mode).
2. `scripts/screenshot_v2b.py` (API hybrid): turns fine, the
   end-of-call extraction returned HTTP 500 after minutes of
   generation.
3. `scripts/screenshot_v2c.py` (shorter calls + retries): killed
   after the extraction sat in one generation for 7+ minutes.
4. `scripts/screenshot_v2d.py` (packed one-line calls, the shape
   that had completed end to end in a manual check): Oakdale
   completed and logged (emergency, "Heat quit"); the Riverbend
   extraction timed out at 420 s and never logged; then Firefox's
   Marionette failed to start once (transient — a manual relaunch
   minutes later worked).
5. `scripts/screenshot_v2e.py` (rendering): morning list (rendering
   the real logged call) and Riverbend-selected shots landed fresh;
   the page-driven card call hung on a turn past its 600 s wait.

Net: mid-call, Riverbend, and morning-list shots are fresh v2
captures of real runs. The last card attempt (the v1-proven
`?demo=full` route) died when the VM restarted mid-call — the sixth
sandbox kill of the day — so the fallback was taken: the stale v1
summary-card shot's upload marker was pulled from the draft and its
figure removed from the demo page. The card itself is still quoted
verbatim in What I Built (from `demo-evidence/sample-summary-card
.json`, a real run artifact) and rendered as data on the demo page;
no image in the post or on the page claims to be a v2 capture of
something it is not. The stale PNG remains in `demo-evidence/` as a
v1-era artifact, unreferenced by the post. Nothing was composited
or staged: every landed frame is the real page, and the morning
list renders a call log written by a real call in this session.

## Deliberately NOT changed

- The `<!-- PILOT SLOT -->` stays reserved and empty. No user,
  quote, or reaction was invented (research #1 remains Ryan's
  outreach task, not a writing task).
- No Render, .tech, Sentry, or any other category was added. The
  project genuinely uses only Gemma among the categories
  (COMPLIANCE 8b stands).
- The two eval failures stay named in the post, verbatim in
  substance. The contained-leak prompt fix stays unapplied.
- Latency stays labeled as sandbox numbers everywhere.
