# How I got to the v4 plan

A record of the reasoning behind the v4 plan for Warrant, kept as input for build learnings and for future product work. I used an AI reviewer in devil's advocate mode and checked its claims against the repo. The sequence matters as much as the conclusions: each lens narrowed what the next iteration should be.

## The method in one line

Test the claim, then judge the product as a buyer, then as an investor, then judge the build against the brief, the team and the architecture. Only then plan, under a fixed budget, and verify the plan against the latest artifact before handing it to an agent.

## 1. Test the opening claim before anything else

**Question:** Is the opening line true, and what numbers sit behind it?

- Directionally true. Agents and support staff do commit money through credits, refunds and waivers, and goodwill concessions are often cited as 2% to 3% of revenue in enterprise subscriptions. That figure is an industry rule of thumb, not a study.
- The specific cause, acting on evidence that conflicts or is stale, has no public measurement.
- "Nobody finds out until finance closes the month" overclaims both ways: approval thresholds and QA sampling catch some errors immediately, while month-end close sees totals, not causes, so many errors are never traced at all.

**What I took from it:** the opener should claim only what a log pull could measure. A claim I cannot size is a hypothesis, and the slide should say so.

## 2. Judge it as a buyer

**Question:** Would I buy this?

- **No, not yet; a shadow pilot, yes.**
- The headline double-credit example is stopped by controls a buyer already has: dedupe by incident ID, per-account caps and an approval threshold, with no model involved. The product has to show what it catches that those rules miss.
- ROI depends on an unmeasured share: the part of concession leakage caused by conflicting or stale evidence, rather than by discretionary generosity.
- Misses are invisible: a missed conflict looks exactly like a clean case, so the buyer only learns at reconciliation, the same lag the product claims to remove.
- Platform risk: CRM vendors can ship the in-estate version.

**What I took from it:** state the buying conditions explicitly: a log pull sized in dollars, a 30-day shadow pilot confirmed by finance, an independently measured over-hold rate, and the kill switch built.

## 3. Judge it as an investor

**Question:** How believable are the numbers, and would I fund it?

- Every measured number answered an engineering question (works, fast, cheap). No measured number answered a discovery question (how often, at what cost, who pays).
- The sizing was arithmetic on assumed inputs, honestly labelled.
- The strongest signal was method: bars set before building, misses reported, a log of the system's own failures.

**What I took from it:** fund a milestone, not a company. The milestone is discovery evidence, not more engineering.

## 4. Separate the engineering from the AI

**Question:** Is the AI part novel, or is this strong software engineering?

- Roughly 80/20 engineering. The value came from fail-closed execution, an idempotent ledger, re-read before write, rules with owner and expiry, and separation of duties.
- The tell: the best bug in the story, the billing system's lagging credit list, was fixed with a ledger. A consistency fix, not a model fix.
- The AI part, reading contracts for meaning-level conflicts, is both the most valuable and the weakest: one case flips on 2 of 5 runs, and every act rests on the model finding nothing.

**What I took from it:** a moat here would be data and workflow (rulings becoming rules, conflict patterns across customers), not the model.

## 5. Grade the build against the brief

**Question:** Does it answer "identify failure modes, translate them to business problems, fix them"?

- Identify: strong, including a 28-row log of failures found while building.
- Fix: partial. The fixes that work are deterministic. The LLM-specific failure, failing open when the model is silent, is still open.
- The report promised a test of a belief-state alternative and held it as a hypothesis. That was the clearest unfinished promise.

## 6. Ask what ML should actually change

**Question:** What interventions would close the gap, and is a better model the answer?

- Not a bigger model; a different decomposition.
- Options considered:
  - extract contract terms once and compare in code;
  - treat disagreement between samples as uncertainty;
  - require the model to report what it checked, so "nothing found" is a positive claim;
  - generate labelled defects by code (mutation testing) to measure misses independently of the model that wrote the system;
  - calibrate the hold threshold.
- Better exhibits than the headline case already existed in the repo: a superseded contract clause, which is the failure the product claims to address, and the system's own escalation discarding dissent, which is the failure repeating inside the fix.

## 7. Weigh the teams

**Question:** Product discovery and craft versus AI and platform: who owes more?

- Platform execution was ahead of everything else. Product craft was strong. ML contribution was thin. Discovery was weakest: zero interviews, though interviews had been set as the gate before design.
- **Discovery comes first.** ML improvements on an unvalidated problem are wasted. But a cheap, credible ML step that also makes the problem measurable is worth doing in parallel.

## 8. Choose the architecture, not the buzzword

**Question:** Is a Bayesian cognitive architecture the right fit?

- A Bayesian decision layer fits the shape of the problem: sources are noisy, aging observations of hidden facts; freshness windows are a crude step function; act, gather or hold is an expected-value decision; human rulings are evidence about source reliability.
- A full cognitive architecture is overkill for one iteration.
- The model stays as an extractor, not as the posterior, because model outputs are not calibrated probabilities.

## 9. Decide under a fixed budget

**Constraints:** one execution iteration, 45 minutes for discovery and design, 1 hour for the presentation, 2 hours available for video.

| Choice | Decision | Why |
|---|---|---|
| Better reasoning, or better evals? | Both, as one change: the belief layer, proven by calibration on a generated mutation set | Each without the other is unconvincing: a new layer without independent evidence, or new evidence about the old layer |
| Add new tools (a decision-record store, more observability) | No | Neither changes a decision on a slide; adding tools late reads as collecting tools |
| Change the user segment | No; I pushed back on the reviewer here | Switching costs a day for no gain. I kept the segment and added a second domain only as a configuration-only generalization test, cut first if time runs short |
| Explainer video | Mostly cut, to a 3-minute narrated demo recording that doubles as the backup | Rehearsal and Q&A prep are worth more than polish |
| Discovery time | Two or three practitioner conversations with one question each | Two real quotes beat dozens of forum snippets |

## 10. Verify the plan against the latest artifact

Before handing the plan to an agent, I checked it against the latest merged pull requests. Several of the reviewer's earlier claims were outdated or wrong:

- **Outdated:** it said the architecture diagram showed the previous version. The current diagrams had been regenerated.
- **Missed:** it said the belief-state replacement map was missing. It was in the report, just not on the slides.
- **Already done:** forum evidence from Reddit had been completed through search snippets.
- **My own error, caught by the check:** I had believed a new frontend library was in place. The pages still load only Tailwind.
- **Arithmetic error:** the reviewer priced the mutation set at one run when the bar needs five: about $6 a pass, so about $30, not $6.

I also folded in a number measured since the first draft. A human review of 15 records took about an hour, a median of 2.75 minutes a record. At an assumed $30 to $40 an hour for an expert labeler, that is about $2.00 to $2.67 a record, roughly 200 to 265 times the cost of an automated decision.

Scaled to 10,000 customers, review time alone does not justify the product's assumed price. So the value has to come from what review time leaves out: clawbacks, lost trust and relationship overhead. That reframed v4's business metric: a calibrated confidence turns the hold threshold into a dial that trades the share of cases a person sees against expected leakage.

## Rules to promote to build learnings

| What happened | What changed | Rule |
|---|---|---|
| The opening claim was directionally right but unmeasured, and overclaimed when errors surface | Opener limited to what a log pull could measure | Never open with a claim you cannot size. Label it a hypothesis |
| As a buyer, the headline example was stopped by controls buyers already have | Planned to show what the product catches that cheap rules miss | Compare against the cheapest existing control, not against nothing |
| Every measured number answered an engineering question; none answered a discovery question | Discovery named as the milestone | Ask which of your numbers a customer could have given you. If none, you have not done discovery |
| The best fix in the story was engineering, not AI | Positioned the moat as data and workflow | Name where the value actually comes from before claiming it is AI |
| The LLM-specific failure stayed open while deterministic fixes landed | v4 targets failing open on model silence | Grade the fix against the failure you named, not against the failures you happened to fix |
| A bigger model was the obvious lever | Chose a different decomposition: extraction, sample disagreement, a calibrated decision | Change the shape of the problem before changing the model |
| The reviewer suggested changing the user segment | Kept it, and added a configuration-only generalization test | Weigh every suggestion against effort and what is being judged. Broaden with a cheap proof, not a rewrite |
| More tools were tempting for the last iteration | Rejected any tool that changes no decision on a slide | A tool earns a place only if it changes a decision |
| Several reviewer claims were stale by the time of planning | Verified against the latest merged pull requests first | Verify a review against the latest artifact before acting on it; reviews age within hours |
| Measured review cost showed that saved review time alone does not pay for the product | Business metric reframed as a threshold dial between review share and leakage | When the obvious value does not cover the price, find the trade-off the product lets the buyer control |
