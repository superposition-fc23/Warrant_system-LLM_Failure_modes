# Dyssonance case harness

A take-home enterprise AI challenge for Dyssonance, prepared over a week and presented live. This folder holds the report, the prototype shell, the slides, and the working code. Fill the templates in place.

## The assignment, as given

- **Problem.** Identify one or more failure modes or limitations of today's LLM-based enterprise systems and agentic workflows. Translate them into business problems: who is affected, why it matters, what the impact is. Define the target user and their jobs to be done.
- **Solution and prototype.** Design and build a working prototype. Third-party surfaces (Slack, Notion, etc.) are encouraged; web, mobile or voice also work. Use APIs, tools, open-source capabilities and integrations where relevant.
- **Show and tell.** A few slides and a live demo covering thinking, proposed solution, prototype, key decisions, trade-offs and conclusions.
- **Evaluated on:** product thinking, creativity, judgment, execution, communication. Weight every choice against those five, in that order.

## Dates

| Date | What |
|---|---|
| Wed 28 Oct | Harness built (this folder) |
| Thu 29 Oct | Dyssonance context in, failure mode chosen, sections 01 to 04 agreed |
| Fri 30 Oct to Sat 31 Oct | Working prototype in `ai-stack`, demo shell in `prototype.html`, sections 05 to 07 |
| Sun 1 Nov | Sections 08 to 11, slides filled from the report |
| Mon 2 Nov | Full rehearsal against the clock, backup demo recording, PDF export of the slides |
| **Tue 3 Nov** | **Share materials.** Send slides PDF plus links; nothing changes after this except rehearsal |
| Wed 4 Nov | Q&A rehearsal only |
| **Thu 5 Nov, 11:30 to 12:30 PT** | **Remote presentation, 30 min, then 15 min Q&A** |

## Company context

DYSSONANCE CONTEXT: what they build, who their customers are, which surfaces and agent patterns they use. To be added when shared. Until then, do not invent facts about Dyssonance; mark any guess as assumed.

## The rules of this folder

1. **Three files plus code.** The report lives in `index.html`; the prototype demo shell in `prototype.html`, full width for screen share; the deck in `slides.html`. All open from the filesystem. Tailwind (Play CDN, pinned 3.4.17) is already loaded; add no other frameworks or CDN links.
   - **Use Tailwind utilities for any new or reworked UI**, with the theme colors so it matches the existing styles and dark mode: `bg-surface`, `bg-surface-2`, `text-fg`, `text-fg-2`, `text-fg-3`, `border-rule`, `bg-accent`, `bg-accent-soft`, `text-ok`/`bg-ok-soft`, `text-warn`/`bg-warn-soft`, `text-stop`/`bg-stop-soft`, `font-mono`. Not raw Tailwind colors like `bg-blue-500`.
   - Preflight is off on purpose so the existing CSS stays intact; do not turn it on. Do not use `dark:` variants; the theme colors already switch.
2. **Working code goes in `ai-stack`** (Python 3.12: `llm.py` model calls, `router.py` XGBoost model router, `rag.py` LlamaIndex + Chroma, `agents.py` LangGraph belief-gated agent, `judge.py` LLM-as-judge, `rag_eval.py` retrieval eval; see its README; run scripts as `.venv/bin/python <file>` from inside `ai-stack`; `./setup.sh` if imports fail). Slack, Notion or other integrations also live there. Its `docs/` hold a synthetic corpus for every idea in the probable ideas list, with planted defects in `evals/planted_defects.json` so evals need no labels. Baseline and known misses are in its README.
3. **Edit, never regenerate.** Replace placeholder text in place. Keep the CSS, the section IDs, the tab script and the slide script untouched unless asked. `./reset.sh` restores all three blank templates and destroys work in progress, so never run it once real content exists.
4. **Placeholders are uppercase.** `TITLE`, `FAILURE MODE SENTENCE`, `DECISION 1`, `...`. Anything still uppercase or `...` on 3 Nov is unfinished.
5. **Never invent a number and present it as real.** Illustrative figures on the mock screens are fine and are labelled as such. A figure anywhere else needs a source or an "assumed" marker. Industry statistics about LLM failure rates are the most tempting thing to fabricate here; every one needs a link.
6. **No em dashes anywhere.** Commas, colons, semicolons or periods.
7. **Delete unused sections and slides** rather than leaving them empty. An empty one reads as unfinished; a missing one reads as scoped out.
8. **Report first, slides second.** The slides are a compression of `index.html`, never a separate argument. Fill a slide only after its section is settled.

## Fill order

Work top down. Discovery (01 to 06) is drafted. Next: 07 user and JTBD and 08 scope (design stage), then 09 the model, 10 the solution and prototype, then 11 to 15. Then the slides.

If time runs short, the sections that must exist are **02 failure mode, 06 judgement, 07 user and JTBD, 10 solution and prototype, 11 decisions and trade-offs, 15 conclusions**. They map one to one onto what the assignment says is evaluated.

## Section notes

**Product discovery, 01 to 06.** Done 31 Oct from `product/01-discovery-memo.md` (rev 3, after a devil's advocate review): 01 vision, 02 failure mode, 03 business problem, 04 market landscape and sizing, 05 competition, 06 judgement calls. The memo is the source; change it first, then the report.

**02 Failure mode.** One sentence describing an observable behaviour of LLM systems or agents, with no solution in it. Then evidence it is real, sourced. The candidates table shows the alternatives considered and why one won: that table is where judgment is visible. Selection test: frequent, expensive, invisible to the victim until late, and containable by a product rather than only by a better model. If the next model release fixes it, it is not a product.

**03 Business problem.** The same failure in the language of the person who pays for it. Who is affected (often more than one party: the operator, their customer, compliance), why it matters, the impact. Add the "why now".

**07 User and JTBD.** One primary user. Jobs in the form *When [situation], I want to [motivation], so I can [outcome].* Plus what they do today. Name the decision this changes.

**08 Goal and non-goals.** Three non-goals, each with half a line of reason. "Not fixing the model itself" is almost always one of them. The assumptions note underneath is not optional.

**09 The model.** Edit the SVG labels, keep the shape. Top row: the actors in the agentic workflow and where trust is handed off. Bottom row: the state flow with one exception branch where the failure is caught. The caption must name the trap, for example that the agent reports success at a state the user does not care about.

**10 Solution and prototype.** One paragraph on the solution, one line on the surface and why it fits where the user already works. The "real vs mocked" table is mandatory: a live demo that hides what is staged loses trust the moment someone asks. Build the demo shell in `prototype.html`, inside its `<main>`, and set its `<h1>`. The report links to it; add one line per screen there once built. Default three screens behind the existing tabs (`.tabs` > `button.tab[data-screen]`, each screen a `div.screen` with an id, the first with class `on`):
- **Screen 1, normal.** The agent completes the task and the check passes. Nobody needs to look.
- **Screen 2, caught.** The failure that would have been silent, held, with the system naming the exact step and field it does not trust. This is the screen that proves the thesis; demo it slowly.
- **Screen 3, correction and audit.** A person fixes it, the trail records it, and the correction becomes an eval case.

If the prototype lives in Slack or Notion, the screens in `prototype.html` are the storyboard and the fallback if the live integration fails on the call. The stylesheet defines a list plus detail plus action shell (`.mock`, `.mock-bar`, `.mock-top`, `.mock-body`, `.side`, `.main`, `.panel`, `table.grid`, `.pill`, `.banner`, `.conf`, `.trail`). Use Tailwind for anything else.

**Building it in parallel.** When asked to build the prototype in the background, launch a background agent with a self-contained brief: read `index.html` sections 01 to 09 and this file's section 10 note, edit only `prototype.html` (or only its named files in `ai-stack`), use only data the report states or mark fields assumed, and report back the screen names. Do not edit those files from the main conversation while it runs.

**11 Decisions and trade-offs.** Four rows. Each: what I chose, what I gave up, and what would make me switch. Typical forks: surface, autonomy level, which model and why, build vs integrate, where verification runs.

**12 Requirements and guardrails.** Grammar: *When [condition], the system must [observable behaviour]. Test: [method and data].* The must-not table is where risk awareness becomes visible. N3, the kill switch with a defined trigger, is the single most credible control.

**13 Metrics and evals.** Always three: leading, lagging, counter. Plus the eval set: size, source, share of known failures, pass definition. An agent product without an eval set is measuring itself with its own judgment.

**14 Risks.** Each row needs a mitigation or an owner, not a worry. The "where this plan is weak" note is said out loud before Q&A.

**15 Conclusions and phasing.** De-risking sequence; P1 is the smallest build that tests the riskiest assumption. Then the three-part close.

## Slides

`slides.html` is a keyboard deck: arrow keys or click to move, `N` toggles speaker notes, the URL hash keeps the slide number, and Print to PDF exports one 16:9 slide per page (that PDF is what gets shared on 3 Nov). Each slide maps to a report section and carries the section number in its kicker. Copy figures and tables from the report rather than rewriting them. Target about one slide per two and a half minutes of talk, excluding the demo.

## The presentation clock, 30 minutes plus 15 Q&A

| Minutes | What | Slides |
|---|---|---|
| 0 to 2 | Hook: the failure mode as one concrete story | 1, 2 |
| 2 to 7 | Business problem, user, JTBD, scope | 3, 4, 5 |
| 7 to 9 | How it works, the model | 6 |
| 9 to 19 | **Live demo**, real vs mocked stated first, screen 2 slowest | 7 |
| 19 to 24 | Decisions, trade-offs, guardrails | 8, 9 |
| 24 to 27 | Metrics and three ways this is wrong | 10, 11 |
| 27 to 30 | Conclusions, then stop talking | 12 |
| 30 to 45 | Q&A | |

**The clock is the thing that fails, not the content.** Rehearse with a timer at least twice. If the demo runs long, cut decisions to two rows, never cut "three ways this is wrong".

## Demo rules

- **Say what is real and what is mocked before the demo starts.**
- **Keep a backup recording** of the full demo path, made on 2 Nov, one click away.
- **Seeded data only.** No live customer data, no keys on screen, close notifications.
- **Show the failure being caught, not only the happy path.** Screen 2 is the argument.
- **Show one place the AI was wrong while building it** and how it was caught. Catching one hallucination is worth more than three extra features.

## Questions to ask before 3 Nov

1. Who is the panel, and is there a Dyssonance product or customer type they would like the case anchored to?
2. Is it fine to use Dyssonance's own product or APIs, or should the prototype be independent?
3. What should the shared materials be: slides only, or slides plus a link to the working prototype?

## Four sentences for Q&A

- "My assumption is the user already works in SURFACE. Correct me."
- "What would change your view of the size of this problem by an order of magnitude?"
- "I deliberately left Y out of v1. Is that the right cut for your customers?"
- "Where would this break first in production: volume, a bad input, or a system we do not control?"

**If the panel pushes back on something, change it in the artifact afterward and say in the follow-up that you did.**

## The close

Three things, in order, every time:

1. What I would cut with half the time, and what it would cost.
2. What I would want to know before anyone builds this.
3. How I would know in 90 days whether it worked, including the counter-metric.

## Do not

- Write a requirement containing "accurate", "fast", "reliable" or "intuitive" without a number and a test.
- Draw a data field on a screen without either labelling it assumed or saying out loud that it is.
- Claim the prototype does something live that is mocked.
- Present an industry statistic without a source.
