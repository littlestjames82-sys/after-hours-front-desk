# Compliance audit — DEV Hacktoberfest Week 2 "Side Hustle"

Audited: Oct 13, 2026. Final re-check: Oct 13, 2026 (round 3, see the
date-stamped entry at the bottom). Rules read fresh from the official
sources:

- Announcement: https://dev.to/devteam/join-the-hacktoberfest-open-source-ai-challenge-side-hustle-2550-in-prizes-across-18-winners-55ba
- Challenge page (template, FAQ, rules): https://dev.to/challenges/hacktoberfest-week2-2026-10-12
- Series overview: https://dev.to/devteam/hacktoberfest-2026-dev-challenges-five-challenges-one-prompt-a-new-theme-every-week-1e54
- Template structure cross-checked against a published, template-following
  Week 2 entry (Local Receipts, dev.to/ghalmeidadev).

## The rules, as stated

1. **Format:** Publish ONE post on DEV using the official submission
   template. One submission per person/team per challenge.
2. **Brand-new project:** the project AND its repository must be started
   and completed within the challenge window (Week 2: Oct 12–18, 2026).
   PRs to existing projects don't count. Commits made after the submission
   deadline must be noted in the project's README — failure to do so may
   result in disqualification.
3. **Core requirement:** open-weight models or open-source AI at the core
   — the open pieces must be what makes the project work (local inference
   qualifies).
4. **Theme (Side Hustle):** something someone would actually pay for; the
   post must say who would pay. Bonus points for landing a first user and
   reporting honestly how it went.
5. **Post content:** what you built + who pays, a demo, and why open
   innovation matters for the build.
6. **Required tags:** the template adds **#devchallenge** and
   **#hf26challenge**. DEV allows max 4 tags per post.
7. **Template sections** (from the official template, as used by published
   entries): the italic submission line ("This is a submission for the
   Hacktoberfest Open-Source AI Challenge Week 2: Side Hustle"), then
   *What I Built / Demo / Code / How I Built It / Why Does Open Innovation
   Matter? / Prize Categories*.
8. **Prize Categories section:** partner categories are opt-in — enter by
   (a) genuinely using the technology and (b) listing each entered
   category in the post's Prize Categories section. One win max per
   challenge. No partner tech is required for the overall prize.
   - *Best Use of Gemma* (featured, $200): use Gemma in the project —
     run it locally, fine-tune it, or serve it via a provider.
   - *Best Use of Render* (featured, $200): Render must be the project's
     AI runtime / host an agent's front end / run Hermes or OpenClaw.
9. **Deadline:** Oct 18, 2026, 11:59 PM PDT. All entries submitted during
   the contest period.
10. **Eligibility:** 18+, no purchase necessary, void where prohibited;
    full terms in the linked Week 2 Contest Rules + General Contest
    Rules. Winners may need an eligibility affidavit + tax info (e.g.
    W-9) within 7 business days of notification.
11. **Language:** non-English submissions get a completion badge but are
    NOT prize-eligible. English required for prizes.
12. **AI use:** allowed, as long as all other rules are followed.
13. **Credit:** any non-generic, non-trivial use of prior/open-source work
    must be credited in the submission. Plagiarism = disqualification.
14. **Teams:** up to 4 people; collaborators' DEV handles must be listed
    in the post; one submission per team.
15. **Judging:** Writing Quality (weighted most heavily), Relevance to
    Prompt & Theme, Creativity, Technical Execution, Use of Partner
    Technology (only for entered categories). Ties broken by positive
    reactions on the post.
16. **Optional:** "Show your work" — a DevRelay agent session embed/link
    is optional and helps judges; not required.
17. **Prizes:** Overall $250 + DEV++ + badge; 6 featured categories $200
    each; 11 partner categories $100 each; every valid submission gets a
    completion badge. Winners announced week of Oct 19.

## Audit of this entry

| # | Requirement | Verdict | Evidence |
|---|---|---|---|
| 1 | One DEV post via template | GAP-RYAN | Draft restructured to the template (see fixes); publishing is Ryan's action on his DEV account |
| 2 | New project + repo in window | **MET** | GitHub API: repo created 2026-10-13T04:50:17Z, all commits Oct 13, 2026 — inside Oct 12–18. Project conceived Oct 12 (idea shortlist) and built Oct 13 |
| 2b | Post-deadline commits noted in README | WATCH | No post-deadline commits exist yet (deadline is Oct 18). Standing rule: any commit after Oct 18, 2026 must be noted in README.md or the entry risks disqualification |
| 3 | Open AI at the core | **MET** | Gemma 3 4B via llama.cpp runs the conversation + extraction locally; Sopro (Apache-2.0) voice; no closed API anywhere in the call path |
| 4 | Someone would pay + who | **MET** | Draft names the buyer (solo/two-truck trade shops), the price ($49/mo), and market grounding ($30–$100 cloud, $200–$500+ human answering). No first user yet — stated as a next step, never claimed |
| 5 | Post: built + demo + why open | FIXED | Demo and Code sections were missing as template sections; added from real repo evidence |
| 6 | Required tags | FIXED | Draft now carries front matter with devchallenge, hf26challenge (+2 free slots noted) |
| 7 | Template sections + submission line | FIXED | Draft restructured: submission line, What I Built, Demo, Code, How I Built It, Why Does Open Innovation Matter?, What's Next, Prize Categories — all original claims preserved verbatim in substance |
| 8 | Prize Categories in post | FIXED | Was only a note in the draft header; now a real section entering **Best Use of Gemma** (Gemma 3 run locally — exactly the category definition) |
| 8b | Best Use of Render | NOT ENTERED (correct) | The project is not hosted on Render and does not use it as a runtime. Entering would be a false claim. Only enter if a Render deployment is actually built before the deadline |
| 9 | Deadline Oct 18, 11:59 PM PDT | GAP-RYAN | Everything is staged; Ryan must publish before the deadline |
| 10 | Eligibility 18+ / rules | GAP-RYAN | Ryan's own attestation territory; no purchase made or needed |
| 11 | English | **MET** | Post and repo are in English |
| 12 | AI use allowed | **MET** | Expressly permitted by the FAQ. Note: DEV's post editor offers an AI-assistance disclosure — set it honestly when publishing (the build and draft were AI-assisted; the FAQ allows AI use, disclosure keeps it clean) |
| 13 | Credit prior work | **MET** | Post + README credit Gemma (Gemma Terms), llama.cpp (MIT), Sopro V2 Turbo (Apache-2.0). The earlier non-commercial voice engine is described but not named or used |
| 14 | Team rules | **MET** | Solo entry (Ghost Developer Studio is Ryan); no collaborators to list |
| 15 | Judging alignment | **MET** (as far as a draft can) | Write-up leads with story + evidence (model rejection on test results, license catch, measured voice sweep, 8/8 smoke test) — aimed squarely at the heaviest-weighted criterion |
| 16 | DevRelay session (optional) | GAP-RYAN (optional) | Not required. Would require Ryan to save/share a session via DevRelay; skipped sessions in this environment contain local file paths — scrub before sharing if he chooses to |
| — | Repo public + licensed | **MET** | GitHub API: visibility public, license MIT detected; LICENSE file present |
| — | Fictional-data honesty | **MET** | Demo shops/callers are invented and labeled fictional in README, post, and simulator; no claim of real customers, calls, or revenue anywhere |

## Fixes made in this audit (Oct 13, 2026)

1. `DEV_POST_DRAFT.md` + `~/workspace/your_files/after-hours-front-desk-dev-post-draft.md`
   restructured to the official template (kept byte-identical to each
   other): added DEV front matter (title/tags), the italic submission
   line, `## Demo` and `## Code` sections built from real repo evidence,
   template section titles, and a `## Prize Categories` section entering
   Best Use of Gemma. No factual claim was changed.
2. README: corrected the stale `desk/shop.json` reference (v2 moved shop
   profiles to `desk/shops/*.json`).
3. This file.

## Risks / watch items

- **Publishing is the whole ballgame:** no valid submission exists until
  Ryan posts on DEV before Oct 18, 2026, 11:59 PM PDT. Everything else
  is ready.
- **Post-deadline commits:** if the repo is touched after Oct 18, add a
  dated note to README.md the same day (rule 2b).
- **Demo weight:** the demo runs locally (llama.cpp + GGUF + Sopro), not
  as a hosted one-click demo. Not a rule violation — the post shows
  screenshots, the real summary card, the transcript, and the smoke
  test — but it's the entry's softest judging surface. A Render-hosted
  front end would also open the Best Use of Render category; that is a
  build decision for Ryan, not a compliance gap.
- **No first user yet:** bonus points unclaimed; the draft says so
  honestly ("first real shop" is step 3 of What's Next). Do not let any
  edit imply otherwise.

---

**Update Oct 13, 2026 (v3, win-research pass):** the draft was rewritten
to the winning shape and the demo gap is closed with real artifacts:
- **Demo video EXISTS:** `demo-evidence/demo-video.mp4` (29 s, real live
  call in the simulator, real desk audio, burned-in captions + sidecar
  .srt). The Demo section leads with it (upload marker is an HTML
  comment, invisible if missed).
- **Held-out eval EXISTS:** 20 scripted scenarios, urgency 19/20,
  fields 79/80, both failures named in `eval/RESULTS.md` and in the
  post itself. No retuning after seeing the test.
- **Unit economics measured** (tokens per turn/call, $0 API cost,
  ~$0.0005 electricity per call) and cited in README + post. Market
  price ranges unchanged from the originally sourced ones.
- **Read time:** ~2,620 words (about 11-12 min), up from ~1,150.
- **No em dashes** anywhere in the post body (Ryan's Oct 13 rule).
- Prize Categories still Best Use of Gemma only; Render not claimed.
- Remaining GAP-RYAN is unchanged: Ryan publishes on DEV before
  Oct 18, 2026, 11:59 PM PDT and sets the editor's AI disclosure.

---

**Update Oct 13, 2026 (round 2, critique pass vs the win research):**
- **Critique written up** in `ROUND2_CRITIQUE.md` (findings F1-F10).
  Post fixes: a "My Agent Session" section (honest: AI-assisted
  build, no hosted session replay linked because sessions here stay
  local), an architecture diagram in How I Built It, and two new
  screenshot markers (Riverbend, morning list).
- **Screenshots re-shot against the v2 UI:** mid-call, Riverbend
  selected, and the morning list are fresh captures of real runs
  (the morning list renders a call this session actually logged).
  The summary-card screenshot could NOT be re-shot despite six
  attempts (model server deaths, an extraction 500, multi-minute
  generations, two VM restarts — all logged in `demo-evidence/`).
  Its upload marker was pulled from the draft and its figure removed
  from the demo page rather than present a v1 shot as current; the
  card is quoted verbatim in the post and rendered as data on the
  demo page.
- **Video retry:** one more Riverbend capture attempt; the VM
  restarted mid-call after the greeting and first reply (real frames
  + audio kept in `demo-evidence/video-capture/`). The shipped video
  stays the 29 s single complete call. Nothing padded or looped.
- **Judge-clickable demo page LIVE:** `docs/index.html`, served by
  GitHub Pages (enabled via the API, repo root as source, build
  verified): https://littlestjames82-sys.github.io/after-hours-front-desk/docs/
  It presents the recorded video, screenshots, and eval table, and
  states plainly that it is recorded evidence, not the live desk.
  This is GitHub Pages, not Render — the Best Use of Render category
  remains NOT entered, and no Render claim appears anywhere.
- **Week 1 (Touch Grass) winners:** re-checked Oct 13, 2026 — still
  not announced (the newest DEV Team winners post is the Oct 9
  Weekend Challenge one). No new lessons to fold in.
- **DEV profile text staged** for Ryan at
  `~/workspace/your_files/dev-profile-draft.md` (draft only).
- Prize Categories still Best Use of Gemma only. GAP-RYAN unchanged:
  Ryan publishes on DEV before Oct 18, 2026, 11:59 PM PDT, finishes
  his DEV profile onboarding, and sets the editor's AI disclosure.

---

**Final re-check Oct 13, 2026 (round 3) — date-stamped.**
Rules re-read fresh today from the official challenge page
(https://dev.to/challenges/hacktoberfest-week2-2026-10-12): no rule
changes. Confirmed again, point by point: brand-new project in the
Oct 12–18 window; one submission per challenge; required tags
**devchallenge + hf26challenge** carried in the draft's front matter
(hacktoberfest + opensource fill the remaining two of DEV's four);
Best Use of Gemma = "run it locally" qualifies, and the draft's Prize
Categories section enters that category ONLY (Render still not used,
still not claimed); post-deadline commits must be noted in the README
(rule 2b — no such commits yet, watch item stands); AI use expressly
allowed (disclosure line is in the post and the editor toggle is on
Ryan's checklist); English; 18+; deadline Oct 18, 2026, 11:59 PM PDT;
prior/open work credited (Gemma Terms, llama.cpp MIT, Sopro
Apache-2.0). Verdict: the audit table above stands unchanged.
Round-3 evidence changes: the summary-card screenshot is now a real
v2 capture (marker restored in the draft, figure restored on the
demo page) and the demo video is the 50.3 s two-call cut; the draft
header now instructs Ryan to upload the video + all four screenshots
into DEV's editor directly, because DEV does not render
GitHub-relative paths. Pre-publish link pass: every URL in the post
fetched 200 on Oct 13, 2026. Final smoke-test note: two round-3
attempts died on sandbox-load 500s (brain-call 600 s timeout
exceeded; see BUILD_REPORT round 3) — an environment limit, not a
compliance item; the same final code completed two full page-driven
calls the same day. GAP-RYAN is the only remaining item and is
unchanged: publish on DEV before Oct 18, 2026, 11:59 PM PDT, finish
profile onboarding, set the AI disclosure toggle.
