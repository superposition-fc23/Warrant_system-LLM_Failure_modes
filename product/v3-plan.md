# v3 plan

Latency cause and fixes: [`v2-latency-rca.md`](v2-latency-rca.md). Status: in build. The list below is final and replaces section 4; sections 1 to 3 are kept as background.

## Final list

| # | Work | Done when |
|---|---|---|
| 1 | One model: Sonnet 5.5 per case, Opus 5.5 judge, every answer stored, served model logged, output capped. Fix the `swap` bug and the CT-08 over-hold | Bar below passes, or the miss is reported |
| 2 | Close known holes: redact the judge prompt, scope standing rules, re-read sources at commit. Add 5 injection cases, 3 cases from a practitioner conversation, five runs per case | Injection cases leave decisions unchanged, flip rate reported |
| 3 | Live sources: HubSpot and Chargebee behind the read-only MCP server, seeded accounts, injected timeouts and stale reads | A real cross-system conflict is held; a failed source never produces an act |
| 4 | Live agent: a Sonnet support agent proposes a credit; the credit tool only runs with a gate approval | A live proposal is held, and a clean one writes to the Chargebee test site |
| 5 | Slack card: a hold posts with buttons; the ruling returns and resumes the action | A click in Slack changes the decision record |
| 6 | Engineer view: a boundary file (per action type: shadow or enforce, amount limit) and one screen | Changing the boundary changes decisions, and the screen shows the effect |
| 7 | Shadow report: one page for the VP, from decision records | Shows held exposure, hold rate and over-hold rate, labelled as seeded data |
| 8 | Human review: about 15 records marked before the gate's answer is shown, exported as labels | Labels feed the improvement loop |
| 9 | Reddit: search API, capped at 100 URLs, storing URL, title and snippet only | Rows are in the corpus and reported per source |

**Primary user:** the support or applied AI engineer, who owns the autonomy boundary. The analyst answers the question on the card. The VP of Support is the buyer.

**Cut order if late:** 9, the Chargebee write in 4, then the screen in 6 (keep the file). Fixtures stay as the fallback if a live system fails on the call.

**Moved out of v3:** Web Awesome (`CLAUDE.md` rule 1 stays), Medium and other new evidence sources, field RBAC, real tickets, kill-switch enforcement, SageOx (v4). Contracts and risk stay local fixtures, labelled as mocked; authority stays a config file.

## Bar, set before building

Planted held 100%, fact named at least 90%, over-held at most 10% of controls, pairs 100%, injection cases 5 of 5 held, median at most 5 s and p95 at most 8 s on fixtures, cost at most \$0.017 per decision, a failed source never acts. Live-path latency is reported, not barred, since this is its first measurement. Each measure is read from five runs per case, taking the worst run.

**Measured before committing to Sonnet 5.5** (one run of the 27 v2 cases, Opus 5.5 judge): median 5.0 s, p95 7.3 s, \$0.0084 per decision, planted held 10 of 10, fact named 10 of 10, over-held 2 of 10.

## 1. Evidence: more data, and a better mix

**Decision: grow the corpus, without building an AI-content detector.**

Law of averages helps with variance only. Random noise cancels as n grows, but bias from one community, vendor marketing or AI-written posts does not, because it pushes in one direction.

- **The real weakness is the mix.** 378 of 396 items are from Hacker News. On the 18 Substack rows, O8 scores 14.7 against 9.0 on Hacker News (small n).
- **The sample that looked AI-generated was not the problem.** It dates from 2015, contains typos, and the relevance check already rejected it at importance 1. Off-topic is the issue, and that filter works.
- **A detector adds what you were worried about:** a new error surface, annotation work, and no reliable ground truth.

| Control | Cost | What it handles |
|---|---|---|
| Add sources through official channels | Low | Single-community bias |
| Report each outcome per source; flag any outcome that only ranks high in one | Low | Hidden skew |
| Date floor: 2023 onward | One line | Pre-LLM comments. Only 6 of 214 relevant rows, so it will not move much |
| Exact and near-duplicate removal; cap per author or thread | Low | Coordinated or repeated posts |
| One new field in the existing classifier prompt: `first_hand`, `commentary` or `vendor` | Very low | Marketing and opinion, with no new tool. Audit 30 by hand |
| Bootstrap each outcome's score for a confidence band | Low | Bias-variance check: stop adding volume when bands stop shrinking |

**Sources to add, in order:** Stack Exchange API, GitHub issues and discussions on agent frameworks, more Hacker News queries, then Reddit and Medium if access works out. Check each source's terms first. Same rule for all: full text in the local cache; committed rows keep link, classification and a short quote.

## 2. Reddit and Medium: your steps

**Plan the deck without them.** Materials go out on Tue 3 Nov, and Reddit's review may take longer than that. I could not read Reddit's or Medium's policy pages from here, so check them yourself in step 1 of each.

### Reddit

1. **Read the current rules in your browser:** the Responsible Builder Policy and Data API terms. Third-party guides say new public API requests stopped on 31 Oct 2026 and that reviews take 2 to 4 weeks. Neither claim is confirmed, so check this first.
2. **Create a dedicated account** for the automated reads, not your personal one.
3. **Register or request an app** on Reddit's developer page. Suggested wording: "Non-commercial product research. Read-only search of public posts about AI agents in business workflows. Stores links, classifications and quotes of at most 20 words. Not used to train models, and no full text is republished."
4. **Paste the keys into `ai-stack/.env` yourself:** `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET`. No Reddit password is needed; `voc.py` already uses app-only read access.
5. **Tell me "Reddit keys are in".** I will fix the empty date field, then run collect, classify and report, and re-check step 3d.

If it is closed or refused, stop there and keep Reddit as a named gap. No resellers, no scraping and no mirrors. A human-coded sample is the fallback: read 30 threads yourself and send links and a one-line note for each. Label it as hand-picked.

### Medium

The official API is archived and takes no new integrations, and it never documented reading others' articles. RSS is the one route `voc.py` uses.

1. **Read Medium's Terms of Service,** for what they say about automated access and RSS.
2. **Run the feed check from your own machine** and send me the output. It sends the script's honest user agent.
3. **Pick 5 to 10 tags and publications** where operators write, not just vendors. Vendor sources report a limit of about 10 items per feed, so Medium will not add much volume.
4. **If feeds are refused,** send 20 to 30 article links with a note each, as a labelled hand-picked sample.

## 3. UX: start from the action

**Audit of the current screens.** Screen 2 is the one that matters, and it has these problems:

- The action sits in the third column, below everything in the middle column's reading order.
- It serves four audiences at once: analyst (question), engineer (trace, record), evaluator (expected, pass, judge) and finance (cost).
- It repeats itself: banner, title, case ID, action table, two belief cards, why, explanation, other beliefs, then checks.
- Screen 1 gives a full page to a case our own rule says nobody needs to look at.

### Action, then decision, then information

Working backward. Only what appears here earns a place on the first view.

| Rank | Who | Key action | Decision | Must see | On demand | Delivery |
|---|---|---|---|---|---|---|
| **P0** | Analyst | Rule on a hold | Which evidence governs? | Amount and action; the two values with source and age; one question | Clause text, other beliefs, checks, earlier rulings | **Notification card with the buttons on it**; drawer for detail |
| **P0** | Analyst | Make it a standing rule | Does this apply next time? | Pattern, cases it would match, owner, expiry | Past matches | Inline right after the ruling |
| **P1** | CSM | Send a holding reply | What do I tell the customer? | Held, why in one line, owner, due time | Decision record | Notification on the account; suggested reply |
| **P1** | Agent owner or VP | Trigger the kill switch | Is this past the trigger? | Which metric crossed, by how much, action type affected | Trend | **Page**, the only interrupt of its kind |
| **P2** | VP | Widen, hold or narrow autonomy | Is the evidence enough? | One proposal per action type, with reversals, over-holds and leakage | Metric tree | **Weekly digest** linking to one page |
| **P2** | Engineer | Label a reversal's cause | Gate, data or policy? | Decision record with evidence timestamps | Trace | Pull only, from a link |
| **None** | Nobody | Nothing, on a clean commit | None | Nothing | Decision record | **No notification**; a count in the digest |

Latency, cost, trace IDs and eval pass or fail are for builders. They move to a separate **Proof** view that the demo uses and the analyst never sees.

### Severity and fatigue

| Severity | Trigger | Delivery | Who |
|---|---|---|---|
| **S1** | Kill-switch metric crossed | Page, interrupting | Agent owner, VP |
| **S2** | Customer is waiting, or the ruling is due within an hour | Direct message | Owner of the fact, with the CSM informed |
| **S3** | Ordinary hold | Batched into the queue channel | Owning team |
| **S4** | Gather resolves itself, rule settled it, or clean commit | None; digest count | Nobody |

Rules (the numbers are assumed starting points, to be tested in shadow mode):

- **Budget:** at most 5 S2 interrupts per analyst per day. Past that, batch and alert the team lead, since a breach means a policy or data problem.
- **Group by cause:** the same conflict pattern across accounts is one card, "3 credits, same amendment". Rule once.
- **Withdraw:** if a gather resolves the fact, remove the card.
- **Dedupe:** one case gets one card, updated in place.
- **Track fatigue:** notifications per analyst per day by severity, time to ruling, share acted on, and rubber-stamp rate. The severity ladder follows common incident-management practice; that source is vendor guidance, not controlled studies.

### Screens after the change

1. **Notification card** (new, and the lead of the demo): action, amount, two values with sources, one question, buttons.
2. **Hold detail:** one column, question and buttons first. Evidence stays in a drawer.
3. **After the ruling:** the standing-rule offer inline, then the replay showing the same pattern settled with no notification.
4. **Weekly digest:** counts, one proposal, nothing clean itemised.
5. **Proof** (for the panel): eval table, latency, cost, trace.

Screen 1 goes away as a page. The clean commit becomes a digest count and a line in the demo.

### Frontend

| Option | Fit for this repo | Verdict |
|---|---|---|
| **Web Awesome 3 plus Tailwind** | CDN, no build, framework-free web components. Free tier has dialog, drawer, badge, callout, tab group and details | **Use for v3** |
| shadcn/ui with TanStack Table | Needs React and a build, and files would no longer open from disk | Best for a real product, later |
| Ant Design or MUI | Strong data tables; heavy, and a build | Only if the product becomes table-led |
| Carbon | Accessible and thorough; its web components tutorial uses a build, and I found no CDN route | Skip |
| Semantic UI | | Skip: nothing here needs it, and it adds a second styling system |

The data grid in Web Awesome is Pro, but the eval table has 27 rows, so a plain table is enough. **This needs your approval:** `CLAUDE.md` rule 1 currently says to add no other frameworks or CDN links, and this changes that rule.

**The surface matters more than the library.** UX rule 4 says to go where people already work, and the brief encourages third-party surfaces, so the card should be a real Slack message if you will create a test workspace and paste a webhook or bot token into `.env`. The Slack mock stays as the fallback on the call.

## 4. Earlier scope, superseded by the final list

| # | Work | Done when | Priority |
|---|---|---|---|
| A | Latency fixes: one model, compact output, store all answers, bar in the run | The bar in the RCA passes, or the miss is reported | Must |
| B | Fix the `swap` bug, add the incident system | Test with 10+ names passes; "unverifiable" no longer fires on covered cases | Must |
| C | "Proposal agrees with governing source" code rule | Controls clear with no model, planted stay 10 of 10 | Must |
| D | UX rework: card, one-column hold, Proof view, severity policy | Each P0 action works in one view; real vs mocked labelled | Must |
| E | Evidence: new official sources and the controls above | Per-source table in step 3d; rule re-run | Should |
| F | Real Slack card | Hold posts to a test workspace; ruling returns | Should, needs your workspace |
| G | Field RBAC and scopes; MCP over stdio; gate as a tool | Agent can see only permitted fields, tested | Move to v4 |
| H | Shadow report screen | One page from a shadow run | Move to v4; on a slide for now |
| I | SageOx as the decision-record store; Reddit, Medium evidence | Rows in the corpus or records in SageOx, or a named gap | v4; Reddit and Medium sooner if your keys arrive |

### Added after the system map (report sections 09 and 14), proposed

| # | Work | Why | Done when | Priority |
|---|---|---|---|---|
| J | Five runs per case; report flips and bands | One run cannot separate a result from noise; 10 of 10 has a 95% lower bound of 69% | Flip rate in the run summary | Must |
| K | 5 prompt-injection cases in rationale and contract text | 0 adversarial cases today | Decisions unchanged, or the miss is reported | Must |
| L | Redact the judge prompt; add scope to standing rules; log the model that served | Known holes in privacy, R6 and the record | Tests pass | Must |
| M | 10 blind cases written and labelled by you, not by the model | The same model wrote the system and its tests | Results reported separately from the 27 | Must, needs about an hour of your time |
| N | Gate as an MCP tool that one live agent must call (moves up from G) | Today the gate stands in front of nothing | A real agent proposal gets held in the demo | Should; first to cut |
| O | A boundary and reversal view for the engineer | Section 07's primary user has no screen | Depends on the primary-user decision | Should |

Report sections 09, 10, 11, 14, 15 and the slides come after A to D, with the report first as usual.

**Why move G and H:** they were in the v3 scope, but materials are due Tue 3 Nov. RBAC is a strong enterprise point and can be stated on a slide with its design until v4 proves it. Say in the room that it is not built.
