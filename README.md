# Warrant

A checkpoint for AI agents in customer service. When an agent is about to take a money action, such as a credit or a refund, Warrant reads the source systems. If they disagree, it holds the action and names the exact fact in conflict, so a person can rule on it. Each ruling becomes a standing rule and an eval case.

An independent, self-built project, developed in public. The commits and pull requests are kept as a public record of how it developed.

## Where to look

Open it in a browser, no setup: [report](https://superposition-fc23.github.io/Warrant_system-LLM_Failure_modes/), [prototype](https://superposition-fc23.github.io/Warrant_system-LLM_Failure_modes/prototype.html), [slides](https://superposition-fc23.github.io/Warrant_system-LLM_Failure_modes/slides.html). Tab 8 of the prototype replays a recorded run; a live run needs the project's keys and test accounts.

| What | Where |
|---|---|
| The product report, from failure mode to requirements | [`index.html`](index.html) |
| The demo, rendered from real run data | [`prototype.html`](prototype.html) |
| The gate, MCP tools and evals | [`ai-stack/`](ai-stack/): `warrant.py`, `crm_mcp.py`, `crm_eval.py`, `mutation_eval.py` |
| Architecture and data flow, as of v5 | [`warrant-v5-architecture.svg`](product/diagrams/warrant-v5-architecture.svg), [`warrant-v5-data-flow.svg`](product/diagrams/warrant-v5-data-flow.svg) |
| v5: model-call guard, open-weight gate, Phoenix loaders, judges, bars written before each run | [`ai-stack/callguard.py`](ai-stack/callguard.py), [`ai-stack/v5/`](ai-stack/v5/) |
| Run logs: traces, decision records, summaries | [`ai-stack/runs/`](ai-stack/runs/) |
| What building this changed about how I build | [`product/build-learnings.md`](product/build-learnings.md) |
| How data is classified and protected | [`DATA_GOVERNANCE.md`](DATA_GOVERNANCE.md) |

## The evals at a glance

Every label is known by construction, not judged by a model. Everything is synthetic.

| Eval set | Size | What it tests |
|---|---|---|
| Generated cases ([`mutations.json`](ai-stack/evals/mutations.json), made by `mutate.py`) | 224: 120 planted defects, 104 clean | 10 base cases times 16 mutations: caps, amendments, unsigned contracts, ledger and list lag, stale feeds, currency, authority, prompt injection, chargebacks, plus clean renames, shuffles, closed flags, recent changes and amounts under the cap that must not be stopped |
| Fixture cases ([`crm_cases.json`](ai-stack/evals/crm_cases.json)) | 36: 13 planted, 11 clean controls, 6 counterfactual pairs, 5 prompt injections, 1 replay | Named failures end to end, including standing rules and their expiry |

- **3,360 stored decisions** on the generated set across seven systems: plain rules, v3 and v4 (five runs each), and four open-weight arms.
- **703 holds** scored by two open-weight judges on whether the gate named the planted fact.
- **61 tests** run with no model calls and no keys.
- Every version's bar was written before its run, and a miss is reported as a miss.

The [report](https://superposition-fc23.github.io/Warrant_system-LLM_Failure_modes/) and [slides](https://superposition-fc23.github.io/Warrant_system-LLM_Failure_modes/slides.html) cover v1 to v4; v5 is below and in [`product/build-learnings.md`](product/build-learnings.md).

## Results so far

### On the 224 generated cases: v3, v4 and v5

v3 and v4 ran on Claude Sonnet 5.5, five runs per case. When the Claude API became unavailable, v5 asked whether the safety result belongs to the model or to the mechanism: the same gate ran on DeepSeek-V4.1-Flash through Together AI, every model call passed a guard (visible retries, rate caps, a circuit breaker, budgets, loop detection), and every arm had its bar written before it ran. Runs, traces and the judges' scores are compared in Arize Phoenix.

| System | Defects acted on (of 120) | Clean cases stopped (of 104) | Cost per decision | Median latency |
|---|---|---|---|---|
| Plain rules a buyer already has | 84 | 0 | 0 | 0 |
| v3 on Claude, 5 runs | 16 to 19 | 5 to 7 | $0.0087 | 3.9 s |
| v4 on Claude, 5 runs | 0 in every run | 18 to 21 | $0.0245 | 3.4 s |
| v5, open model, reasoning off, 1 run | 0 | 48 | $0.0024 | 2.1 s |
| + its arithmetic rechecked in code | 0 | 32 | $0.0025 | 2.1 s |
| + computed facts in the prompt | 0 | 35 | $0.0024 | 1.9 s |
| + reasoning high, arithmetic rechecked | 0 | 24 | $0.0094 | 7.8 s |

Safety held on the open model in every arm, at a tenth of v4's cost. Over-caution failed the bar in every arm: at most 21 clean cases stopped, v4's worst run. The best arm missed by 3, and the open arms ran once each, so repeats come next. Full table: [`ai-stack/README.md`](ai-stack/README.md).

### On the 36 fixture cases: v3 and v4

| Version | Planted held | Fact named | Clean over-held, worst of 5 runs | Prompt injections held | Median latency | Cost per decision |
|---|---|---|---|---|---|---|
| v3 | 13 of 13 | 13 of 13 | 1 of 11 | 5 of 5 | 4.2 s | $0.0101 |
| v4 | 13 of 13 | 12 of 13 | 1 of 11 | 5 of 5 | 4.5 s | $0.0266 |

v4's latency comes from a separate pass run alone, because the first reading came from runs competing for capacity. 13 of 13 has a 95% lower bound of 75% (Clopper-Pearson), so the catch rate is thin evidence on its own; the generated set above is the larger test.

### v1 and v2 (the first 27 fixtures)

10 planted failures, 10 clean controls, 6 counterfactual pairs and 1 replay case; the set grew to the 36 above. The bar for v2, set before building, was to beat v1 on catch rate, over-holds, cost and latency together.

| Version | Planted failures held | Conflict named | Clean controls over-held | Median latency | Cost per decision |
|---|---|---|---|---|---|
| v1 | 10 of 10 | 8 of 10 | 3 of 10 | 6.7 s | $0.021 |
| v2 | 10 of 10 | 9 of 10 | 1 of 10 | 14.5 s | $0.017 |

v2 was more precise and cheaper, but it failed on latency. The [v2 pull request](https://github.com/superposition-fc23/Warrant_system-LLM_Failure_modes/pull/2) records that miss.

## Run it

```bash
cd ai-stack && ./setup.sh
cp .env.example .env
.venv/bin/python crm_eval.py v2
```

The fixture eval needs an Anthropic API key in `.env`. The open-weight runs need Together keys instead; the commands are in [`ai-stack/README.md`](ai-stack/README.md). Every test runs without keys:

```bash
cd ai-stack && .venv/bin/python test_warrant.py && .venv/bin/python test_callguard.py
```

Full forum text is not in this repo, so the evidence classification cannot be rerun from here; each row keeps its source link. A local cache holds the text.
