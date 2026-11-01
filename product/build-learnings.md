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

## Evals

| What happened | What changed | Rule |
|---|---|---|
| v1 held 3 clean controls. The gate was right: my test data had invoices past the window, missing add-on lines and seats already granted | Added a model audit of the eval set that runs before evals | Audit the eval set. A failing case may be a wrong answer key |
| One clean control could not measure over-holding | Controls now match planted cases, 10 and 10 | Give the counter-metric enough clean cases to move |

## AI architecture and cost

| What happened | What changed | Rule |
|---|---|---|
| The model's named fact overrode a failed code check on 2 cases | A failed code check now names the fact | The model proposes; code decides. Deterministic facts outrank model output |
| A cheap first pass plus escalation cut cost 18% but more than doubled median latency, 6.7 s to 14.5 s | v3 targets output length and removes sequential calls | Measure before assuming a smaller model is faster. Output length drives latency, and tiers in series add up |
| v2 improved three measures and failed on the fourth | Reported as a failure against the bar set beforehand | Set the bar before building, across all the measures together, so one win cannot hide a regression |

## Privacy and governance

| What happened | What changed | Rule |
|---|---|---|
| Scraped forum text put 28 third-party email addresses in git history, found only when preparing to go public | Added scrubbing on collection, a pre-commit scan, a CI scan and a governance doc | Build as if public from the first commit. Scrub at ingestion, not at release |
| Scrubbing history is not enough on GitHub: pull request refs keep old commits reachable | History is scrubbed before publishing, and the limit is documented | Treat a commit as permanent. Prevention is far cheaper than cleanup |
| Reddit and Medium refused automated reads, and browser spoofing was blocked | Used official APIs only; the gap is named in the evidence | Use official channels, and record the gap instead of working around it |

## Process

| What happened | What changed | Rule |
|---|---|---|
| I pushed straight to main, so the pull requests tab stayed empty and the iterations were hard to see | One branch and one pull request per iteration, with results and failures in the description | Make the iteration visible as it happens: small commits, one pull request per version |
| The demo shell and backend were built in parallel without collisions | The data contract was written first | Fix the interface before splitting work between agents |
| My first reason for sitting beside the CRM was "habit". Challenged, the real reason was separation of duties, and it exposed where we lose | The non-goal was rewritten with its losing case | Ask why a buyer would pay for two tools. A non-goal needs a reason that survives that |
