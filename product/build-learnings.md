# Build learnings

What building this product changed about how I build products. Each entry records what happened, what changed, and the rule I keep. Rules that apply beyond this project are promoted to my reusable playbook.

Add an entry at the end of each iteration, and whenever a run or a review overturns something I believed.

## Evidence and research

| What happened | What changed | Rule |
|---|---|---|
| My assumed importance scores ran 2 to 3 points above the evidence check | Assumed scores are labelled, and evidence sits next to them | Treat your own scores as a hypothesis until something outside your head tests them |
| The first evidence report averaged the top 100 by importance, inflating importance by 0.6 to 1.0 per outcome | The report uses every relevant item | Never select on the field you are about to average |
| A severity outcome got 1 opinion. It looked like evidence against the idea, but 7 of 10 long queries had returned nothing | Queries were shortened with the bar unchanged | Check recall before you read a null result |
| Rerunning the same data moved a model-scored outcome by 1.9 points at the same n | Outcomes are ranked in bands, not decimals | Measure a model judge's noise before trusting its differences |
| I deferred severity (P3) on assumed scores, with no outcome able to capture it | Added O9 and set the pass rule before running | Write the decision rule before seeing the result; every deferral needs evidence |

| 95% of the 396 evidence items came from one source (378 from Hacker News). On the 18 Substack rows, scores differ from Hacker News by up to 5.7 points on a small n | Corpus growth now targets more sources, with outcomes reported per source | More data reduces noise, not bias. Add sources before adding volume |
| A comment that looked AI-generated was from 2015, had typos, and was already rejected by the relevance check at importance 1 | No AI-detector tool. Adding date, dedupe and source controls, plus one field in the existing classifier | Check what a bad sample actually is, and whether a filter already caught it, before building a tool for it |

## Evals

| What happened | What changed | Rule |
|---|---|---|
| v1 held 3 clean controls. The gate was right: my test data had invoices past the window, missing add-on lines and seats already granted | Added a model audit of the eval set that runs before evals | Audit the eval set. A failing case may be a wrong answer key |
| One clean control could not measure over-holding | Controls now match planted cases, 10 and 10 | Give the counter-metric enough clean cases to move |

| The first Reddit search returned 0 rows from 16 failed calls, and the report drew a clean table of zeros | Read the error before reading the table | A zero from a failed call is not a finding. Same rule as the severity outcome: check recall first |

## AI architecture and cost

| What happened | What changed | Rule |
|---|---|---|
| The model's named fact overrode a failed code check on 2 cases | A failed code check now names the fact | The model proposes; code decides. Deterministic facts outrank model output |
| A cheap first pass plus escalation cut cost 18% but more than doubled median latency, 6.7 s to 14.5 s | v3 targets output length and removes sequential calls | Measure before assuming a smaller model is faster. Output length drives latency, and tiers in series add up |
| v2 improved three measures and failed on the fourth | Reported as a failure against the bar set beforehand | Set the bar before building, across all the measures together, so one win cannot hide a regression |

| A trace review ruled out context, tools, reads and guardrails in minutes: non-model time was 36 ms of 14.5 s, and output tokens explained 93% to 100% of call time | The v3 fix targets the series calls and output length, not the harness | Check the usual suspects in traces before redesigning anything |
| Escalation overwrote the first pass, so nobody can say how often Opus changed Haiku's answer | v3 stores every model answer | Log what a tier produced, or you cannot judge whether the tier earns its cost |

| A system map showed all 11 acts rest on a model finding nothing, and that 2 "code" catches rest on a limit the model read | The dependence is now stated, and miss rate is proposed for v3 | "Model proposes, code decides" is only as strong as what code can see. Trace which decisions depend on model silence |
| v2 escalation overwrote the first answer: last write wins, in a gate built to stop that | Logged as a recursive failure | Check your own system against the failure you are selling |

| The first v3 eval held all 5 injection cases, but 1 held only because the reply could not be parsed. Failing closed hid a format bug behind a passing score | Output schema enforced; unreadable replies counted separately | Check why a case passed, not only that it passed. A safe default can hide a broken step |
| Five runs found 2 flipping cases that one run would have reported as simply passing or failing | Every measure in the bar now reads from the worst of five runs | Do not trust one run of a model step. Repeat before reading a result |
| All evals passed, then the first live agent run double-credited a customer. Chargebee's credit list lagged the write by over a minute, and an empty list looks exactly like a true "no prior credit" | The gate keeps its own commit ledger and cross-checks the balance against listed credits | A clean read is not a current read. Fixtures cannot show the failures only a real system has, so go live before trusting a score |
| Sonnet 5.5 in one call beat Haiku then Opus on latency and cost: median 14.5 s to 4.2 s, $0.0173 to $0.0098 per decision | One model for the gate, a stronger one for the judge | Try one good model before building a tier. Keep the stronger model for grading |

| Labelling 15 records took over an hour, and the reviewer made one selection error. At $30 to $40 an hour, that is at least $2 to $2.67 a record against $0.0101 a gate decision | Review cost now has its own table. At the middle volume it is below the assumed account price, so the case rests on avoided mistakes | Time your own evaluators. The cost of the human check is a product number, and it can weaken your pitch |

## Privacy and governance

| What happened | What changed | Rule |
|---|---|---|
| Scraped forum text put 28 third-party email addresses in git history, found only when preparing to go public | Added scrubbing on collection, a pre-commit scan, a CI scan and a governance doc | Build as if public from the first commit. Scrub at ingestion, not at release |
| Scrubbing history is not enough on GitHub: pull request refs keep old commits reachable | History is scrubbed before publishing, and the limit is documented | Treat a commit as permanent. Prevention is far cheaper than cleanup |
| Reddit and Medium refused automated reads, and browser spoofing was blocked | Used official APIs only; the gap is named in the evidence | Use official channels, and record the gap instead of working around it |
| A search API gave Reddit coverage without touching Reddit, but pulling thread text would have repeated the block we had accepted | Rows hold URL, classification and a short quote, labelled as snippets | Take the coverage the channel allows, and label how thin it is |

| Removing emails was not enough: 100 of 407 items still held personal details such as names and employers | Full forum text left the repo. Committed rows keep the link, classification and a short quote | Minimise before masking. Do not publish what the analysis does not need |
| A rewrite was tested on a copy, then pushed to a private repo and scanned from a fresh clone of every ref before the visibility changed | Went public with 0 addresses, secrets or forum text in 139 blobs | Verify the published artifact, not the local one, and flip visibility last |
| A commit address swap could have looked like losing the activity graph | Checked commit attribution before, and the logged-out graph after | Test what the audience will see, from their position |

| A new drawing of all data exits found the agent path unredacted and real names on Slack cards. The old drawing and the guardrail text had claimed less exposure than the code had | Same tokens on every model path, roles on Slack, three new tests | Draw every exit from the code, not from the design. Fix the guard everywhere the data goes |

## Working with AI agents

Full evidence: [`llm-failure-modes-log.md`](llm-failure-modes-log.md).

| What happened | What changed | Rule |
|---|---|---|
| An instruction about public text became a ban on naming a tool, then hardened through agent memory and a context summary | Corrected the rule and its memory entry | State scope when instructing an agent. Treat its saved beliefs as claims to re-check, especially after a summary |
| The same model wrote the cases, prompts, audit and judge | Blind cases and human labels proposed | An agent's tests share its blind spots. Keep one evaluator outside the writer |
| Most catches came from traces, recounts, scans and people, rarely from rereading | The log records who caught each failure | Build checks that do not depend on the author's reasoning |

| A code comment called one function "the only route to the money" while a second path wrote credits directly, and that path had no shadow-mode check | One guarded function now holds both routes, with tests | A comment that claims a guarantee needs a test that would fail if it stopped being true |

## Process

| What happened | What changed | Rule |
|---|---|---|
| I pushed straight to main, so the pull requests tab stayed empty and the iterations were hard to see | One branch and one pull request per iteration, with results and failures in the description | Make the iteration visible as it happens: small commits, one pull request per version |
| The demo shell and backend were built in parallel without collisions | The data contract was written first | Fix the interface before splitting work between agents |
| My first reason for sitting beside the CRM was "habit". Challenged, the real reason was separation of duties, and it exposed where we lose | The non-goal was rewritten with its losing case | Ask why a buyer would pay for two tools. A non-goal needs a reason that survives that |

## Product judgement

| What happened | What changed | Rule |
|---|---|---|
| Three verticals kept the user vague; narrowing to CRM service sharpened the design | Designed for one user and one buyer, with each element labelled general or vertical | Narrow first. Abstraction is easier from something concrete |
| Interviews were set as the gate before design, then design went ahead on public opinions | The gap is now stated as the first weakness | A gate nobody enforces is a wish. Name who stops the work if it is not met |
| The UX plan ranked the analyst first while the report names the engineer as primary | Flagged as an open decision | Check each plan against the stated user, since local optimising drifts from the goal |
| Mapping the whole system showed a strong gate that stands in front of no live agent or person | The canvas now separates built from scripted | Draw built and staged links differently. Component progress can hide that the job is not done |
| A 35-minute design sprint took about five hours by commit times | Noted, with the depth kept | Time-box the plan, and record the actual |

## For the final presentation

These come from the log above and [`llm-failure-modes-log.md`](llm-failure-modes-log.md).

0. **The best moment of the build.** Evals were perfect, then the first live agent double-credited a customer because the billing list lagged. Show this one.
1. **Reported misses are the proof of method.** v2 improved three measures and failed the bar on latency, and we said so.
2. **The best catch was in our own test data.** v1's over-holds were wrong answer keys; the gate was right.
3. **Traces beat intuition.** "Smaller is faster" was false, and non-model time was about 36 ms of 14.5 s.
4. **The system repeats the failure it targets.** v2's escalation discarded dissent, in a gate built to keep it.
5. **Say the weak points first:** no customer validation, results that partly grade themselves, and a gate not yet in a live path.

## Knowledge bank

This log is one file for now. When it outgrows a quick read, or several projects need searching together, turn these logs into a corpus with a small RAG over it and an eval on retrieval. Build that when retrieval is the actual pain, not before.
