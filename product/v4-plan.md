# v4 plan: an uncertainty-aware decision layer

Status: steps 1 to 5 built on branch `v4`, with priors frozen in commit `764324f`. The paid runs in step 6 have not started. One pull request, results and misses in its description. The revert point is the tag `v3-final` (PR 8). Follow `CLAUDE.md` throughout (no em dashes, no invented numbers, report before slides, no new frameworks or CDN links).

## Hard deadline

`CLAUDE.md` says materials are shared Tue 3 Nov and nothing changes after that except rehearsal. So v4 either passes its bar and merges before materials go out, or it does not merge at all. **Cutoff: 21:30 PT Mon 2 Nov.** If the bar is not met by then, ship v3 materials unchanged and report the v4 attempt as a labelled experiment on its branch.

## Why v4

The report's section "Do we need a post-LLM architecture?" already sets out a replacement map and the test to run: give a belief store and this harness the same cases plus a stream of evidence updates, and compare missed defects, over-holds, cost per decision and explainability. v4 runs a small version of that test. Today it is a hypothesis; v4 turns it into a finding, whichever way it goes.

The v3 limits that map points at:

- **Uncertainty is binary.** A conflict is material or not; the gate acts or holds.
- **Decay is a step function.** Freshness windows of 6 h, 24 h and 30 d. A read 5 h 59 m old is as good as a fresh one; 6 h 01 m is worthless.
- **Silence means safe.** Every act rests on the model finding nothing (log row 18). The miss rate is unmeasured.
- **The model's own doubt is thrown away.** CT-08 flips between act and hold on 2 of 5 runs.
- **Every decision starts from zero.** Each case re-reads every source and calls the model, even when nothing relevant changed.

v3 already has two cases the harness cannot express:

1. **The Chargebee lag.** No freshness window can say "the credit list lags writes by over a minute". A belief whose confidence depends on time since the last write can.
2. **CT-08.** The harness discards sample disagreement. A belief layer treats it as evidence and gathers instead of flipping.

And v3 measured what a person costs. The human review took about an hour for 15 records, a mean of 4.2 minutes and a median of 2.75 per record, which is about $2.00 to $2.67 a record at $30 to $40 an hour (assumed), roughly 200 to 265 times the $0.0101 gate decision. Section 13's table scales that to 10,000 customers. The report's own conclusion is that review time alone does not pay for the product. v4 adds the missing link: a calibrated P(safe) turns the hold threshold into a dial, so the share of cases a person sees, and therefore review cost, can be traded against expected leakage with numbers rather than guesses.

## Decisions already made (do not reopen)

| Decision | Reason |
|---|---|
| Segment stays CRM customer service. Primary user: the engineer who owns the autonomy boundary. Buyer: VP of Support | Switching costs a day for no gain on what is judged. Fix the memo and report where the buyer is still "head of AI platform" |
| IT support (MSP) appears only as a generalization test, stretch goal S1 | Shows domain-agnostic design with proof, without widening scope |
| Code still decides. Hard checks (authority, currency, ledger, failed read, injection, one commit per record, the single guarded route through `warrant.commit_credit`) are vetoes the belief layer can never override toward act | Keeps the v3 guarantees; the belief layer only replaces the soft judgements |
| Keep the commit ledger | Belt and braces. The demo shows the belief layer would also have gathered on the lag case without it |
| No SageOx, no extra observability beyond belief attributes on existing spans, no PyMC or other new dependencies | None of it changes a decision on a slide. The maths is a few lines of stdlib Python |
| Priors and costs are set before any run, labelled assumed, and not tuned after seeing results. Any change is disclosed | Same rule as "I left the answer key alone" in v3 |
| Sample the model only when the belief state cannot settle a decision on its own | A stateful layer should need the model less, not more |

## The bar (set now, before building)

Read from the worst of 5 runs per case, v3 and v4 on the same cases. Thresholds marked (assumed) are starting points.

| Measure | Bar |
|---|---|
| Recall on planted cases plus the mutation set | At least v3's |
| Clean controls over-held | No worse than v3 (1 of 11) |
| Counterfactual pairs | At least 5 of 6 |
| CT-08 | Same decision on all 5 runs (gather or hold with a stated probability counts) |
| Calibration on the mutation set | In each probability bin with 20 or more cases, observed safe rate within 0.10 of predicted (assumed). This holds for this mix of cases only; it does not show calibration in production, where defects are rarer |
| Lag case, ledger and balance check disabled | Belief layer alone gathers, not acts. The balance check would catch it otherwise, which would prove nothing about the belief layer |
| Agreement with the 15 human labels | Reported against v3's 11 of 15. Not a bar: one reviewer, who is the author |
| Share of cases a person sees, at v3's recall | Reported on clean cases and defects separately, because the mutation set is about half defects by construction. Monthly review cost from section 13's middle row uses the clean-case share plus a stated, assumed defect rate |
| Cheap rules baseline | Reported beside v3 and v4: dedupe by incident, currency check, per-account cap from the order form, approval threshold. Stops 36 of 120 defects and 0 of 104 neutrals by code, with no model |
| Time-based gathers | Reported apart from holds: a re-read after a wait needs no person. Neutral `recent_change` cases are expected to gather, which is the honest cost of the lag fix |
| Decisions settled with no model call | Reported for v3 and v4 |
| Latency | p50 at most 7 s (assumed; v3 was 4.2 s) |
| Cost per decision | At most $0.035 (assumed; v3 was $0.0101, and k=3 samples roughly triples it on cases that need them) |

If any row misses, report it in the pull request, the report and the slides, as v2's latency miss was.

## Steps, in order

### 1. Mutation set first (`ai-stack/mutate.py`)

Generate about 200 cases **by code, not by a model**, from the clean controls and planted cases, with labels known by construction.

- **Defect mutations (expected not to act):** amount over the contract cap; a signed amendment's effective date moved so it supersedes; signature removed from the governing document; a prior credit present in the ledger but not yet in the billing list (lag of 5 to 120 s); risk flag aged across its old window; currency changed; amount above agent authority; injection text in the rationale or contract.
- **Neutral mutations (expected to act):** names and regions changed, source order shuffled, amount just under the cap, an unrelated closed risk flag.

Generating the cases costs nothing. Running them does. Built set: 224 cases, 120 defects and 104 neutrals. Estimate from a two-case smoke test ($0.024 to $0.034 a model case): about $24 for v4 at 5 runs, $10 for v3 on the same cases, $4 for the fixtures plus the judge, so **about $40, not $30**. The earlier figure left out the v3 baseline.

Reason: ground truth that does not come from the model that wrote the system fixes the self-grading weakness and gives enough volume to calibrate, which 36 fixtures and 15 human labels cannot.

### 2. Belief layer (`ai-stack/belief.py`, pure functions, no model calls)

- **Facts:** the ones the checks already test: no prior compensation, risk clear, within contract cap, entitlement matches, credit list complete.
- **Source reliability:** a Beta prior per source in `state/beliefs.json` (assumed values, listed in the report).
- **Decay instead of windows:** an observation's weight falls with age at a per-source half-life, set so it equals the old window at the point v3 would have called it stale. For the billing credit list, P(list includes a write made t seconds ago) = 1 − exp(−t/τ), with τ = 90 s (assumed, from the one observed lag of over a minute).
- **Model evidence, only when needed:** if the belief state already settles the decision, skip the model. Otherwise run the compare step k=3 times in parallel. For each conflict, the share of samples that raise it is a likelihood input, not a verdict.
- **Combine:** P(safe) as the product over facts, assuming independence. State that assumption on the slide.
- **Decide:** act if (1 − P(safe)) × amount at stake is below the cost of delay for that action type. Use section 13's measured review cost, $2.00 to $2.67 a record, as the person's share of that cost, and label the rest assumed. Otherwise gather the fact whose re-read most reduces expected loss, which is value of information and becomes the discriminating fact. Hold if no gather can bring the decision under the threshold.
- **Output:** P(safe), the top contributor to doubt, and the gather it recommends.

### 3. One held state with a question, and rulings that update beliefs

- The human review found that hold and gather blur for a person: the reviewer used gather to mean "I need more context" on 2 records and named the same need on a third. In the Slack card, show one held state with the question the value-of-information step chose. Keep act, gather and hold distinct in the record.
- A ruling that keeps a hold applies a Beta update to the reliability of the source that turned out wrong. Standing rules stay as they are. Demo moment: one click visibly changes the next decision's P(safe).

### 4. Wire it in with minimal diffs (`warrant.py`)

- `compare`: skipped when the belief state settles it; otherwise k=3 samples in parallel, every answer stored.
- `decide`: hard vetoes first, then `belief.decide`.
- `record`: write P(safe), contributors and the recommended gather to the decision record.
- Telemetry: `belief.p_safe`, `belief.top_doubt`, `belief.gather` as span attributes on the existing spans.
- Name the invoice date field (invoice date versus paid date) in the sources and the prompt, since the refund window depends on it and the review found the ambiguity.
- Keep diffs minimal and add no new comments; update the module docstring only.

### 5. Tests (`test_warrant.py`, no model calls)

- A hard veto beats any P(safe).
- The lag case gathers with the ledger disabled.
- A ruling moves the right source's reliability in the right direction.
- Decay is monotonic, and at the old window boundary matches the old window.
- A failed read still gathers.
- A case the belief state settles makes no model call.

### 6. Runs

- `crm_eval.py v4 5` on the 36 fixtures, then the mutation set at 5 runs.
- Produce: a v3 versus v4 table; a calibration table (predicted bin, case count, observed safe rate); v4 against the 15 human labels; and a threshold sweep showing, for each P(safe) threshold, the share a person sees, the monthly review cost from section 13's middle row, and the defects that would have acted.
- Save under `runs/v4-*`, same contract as v3.

### 7. Live demo

Reuse `agent.py` and `slack_card.py`; no new integrations. The Slack card gains one line, for example: "P(safe) 0.71. Main doubt: the credit list may not yet show a write from 40 s ago. Re-read in 60 s."

Demo order: clean credit, then the lag case gathering on belief alone, then a ruling in Slack, then the same pattern settled with a changed P(safe).

### 8. Report, then slides (`CLAUDE.md` rule 8)

- **Report:** update "Do we need a post-LLM architecture?" from hypothesis to result, row by row, with what v4 showed and what it did not. Add "Where the harness hits its ceiling" (the two cases), the v4 design, the bar and its results, the calibration table and the threshold sweep. Fix the buyer text. Add v4 rows to the phase table, and new rows to `llm-failure-modes-log.md`, `build-learnings.md` and `future-plans.md`.
- **Diagrams:** update `product/diagrams/draw.py` for v4 and regenerate both SVGs: the belief layer between checks and decide, and the model call shown as conditional.
- **Slides, in this arc:** failure mode, then the business problem, then the harness (v1 to v3, one slide), then the two cases it cannot solve, then the belief layer, then the live demo, then calibrated results and the cost dial, then where this is weak, then what's next.
  - One headline number per slide.
  - Renumber the kickers; today 09, 11 and 13 each appear twice.
  - Bring the replacement map onto a slide; today it is only in the report.
  - Name the objection "isn't this just a guardrail?" and answer it with the belief layer.
  - Closing slide: where a stateful reasoning engine would replace `belief.py`, as the integration point.
- Re-export the slides PDF.

### Stretch S1 (cut first): generalization to IT support

Only if every bar row passes with time to spare. Run two cases from `docs/02-rmm-device-state` (restart on a stale monitoring alert during a change window) through `belief.py` with only a new source config and half-lives, and no change to the model prompt. If both decide correctly, add one line to the results slide: same layer, second domain, configuration only. If not, leave it out entirely.

## Not in v4

SageOx, new observability tooling, field-level RBAC, the kill switch build, a frontend library beyond the Tailwind already loaded, more forum evidence (Reddit snippets are done in v3), a second human labeler, and any change of segment.

## Folded in before execution

Checked against the code and the approach doc before building. Each was changed before any v4 run.

### Changes to the design

| Finding | Change |
|---|---|
| An exponential half-life over-holds. At a $20 cost of delay and $300 at stake, the tolerance is 6.7% total doubt, and a 6 h half-life already costs 11% after an hour | Weight is 1 / (1 + (age / window)^4). It is flat while fresh, exactly 0.5 at the old window, and falls after it. The plan's boundary test still holds |
| Silence still meant safe: three samples that find nothing could also mean three samples that did not look | The compare step reports what it checked. A sample counts as clean only if it checked the contract terms; otherwise the fact stays at its prior and the action does not act. This is the direct fix for log row 18, from section 6 of the approach doc |
| Independent samples would let two silent answers outweigh a real conflict, which risks the recall bar | The share raising a conflict maps to a stated table, not a product of likelihoods: 0 of 3 uses the contract reliability, 1 of 3 is 0.70, 2 of 3 is 0.30, 3 of 3 is 0.05. The calibration table tests it |
| A credit-list wait has no fixed length | The layer solves for the wait, so the card says "Re-read in N s". An age-based re-read comes before any model call |
| When no answer could clear the action, skipping the model would leave nothing to name | One sample runs in that case, to name the fact |
| Fixtures had no contract-age effect | Added a contract-current fact, so a stale contract still gathers |
| Evals must not change state the demo uses | Priors live in `belief_priors.json`, rulings in `state/beliefs.json` (gitignored), and each eval run has its own copy |

### Proposed priors and costs, all assumed

| Value | Setting | Effect, by arithmetic alone |
|---|---|---|
| Source reliability | CRM, billing, risk 0.995 (Beta 199, 1); contracts 0.99 (Beta 99, 1) | A clean, fresh case has P(safe) of about 0.975. One kept hold moves a source to 0.990 |
| Unread or fully aged fact | 0.8 | A stale source or unread contract adds about 20% doubt |
| Cost of delay | $20: review $2.67 (upper end of section 13), other delay cost $17.33 | The dial. The sweep reports other values |
| Credit list τ | 90 s | Complete with P = 0.36 at 40 s, 0.74 at 2 min, 0.96 at 5 min |
| k | 3, or 1 when no answer could clear the action | |

Consequences to state in the report:

- **Nothing above about $800 acts.** At 2.5% doubt, $20 buys $800 of stake, below the agents' $1,000 authority. This is a real limit of these values, and the dial moves it.
- **Below about $94, nothing reads the contract.** Expected loss is under the cost of delay even unread. A low-stakes defect would act, by design.
- **CT-08 may still miss its bar.** If a sample raises the conflict about 40% of the time (2 of 5 v3 runs), k=3 stays clean 22% of the time, so all 5 runs agree only about 30% of the time. Moving to k=5 raises that to about 67% at higher cost. Report the result either way.

### Additions from the improvement list and the approach doc

| Addition | Where |
|---|---|
| Cheap rules baseline: what the product catches that buyer controls miss | Step 6 and the results slide |
| Time to ruling logged per click, to measure a ruling and not only a blind label | Built in `slack_card.py`; reported in step 7 |
| Correct a review mark without erasing it, because the first mark must stay blind | Step 3, Review screen. Not yet built |
| Post a real Slack card before recording, since the role-only cards have never reached a channel | Step 7 |
| Replace the stale section 09 tables, not just the note about them; fix P2 in section 15, which still names SageOx for v4 | Step 8 |
| Name the buying conditions: a log pull sized in dollars, a 30-day shadow pilot confirmed by finance, an independently measured over-hold rate, a built kill switch | Step 8, report and closing slide |
| Open with what a log pull could measure; lead with the superseded clause, not the double credit, which cheap rules stop | Step 8, slides |
| Position the moat as data and workflow | Step 8, report and slides |
| The 2% to 3% goodwill figure is a rule of thumb with no link, so it stays out unless a source is found (`CLAUDE.md` rule 5) | Step 8 |

### Considered and left out

Catching names outside the roster and minimising contract text (privacy, no decision on a slide changes; stated as limits), and caching contract extraction per document version (it would hide sample noise in repeat runs, which the bar reads).
