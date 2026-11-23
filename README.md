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

## Results so far

### v5: the same gate on an open-weight model (224 generated cases)

The Claude API became unavailable, so v5 asked whether the safety result belongs to the model or to the mechanism. The gate ran on DeepSeek-V4.1-Flash through Together AI, every model call passed a guard (visible retries, rate caps, a circuit breaker, budgets, loop detection), and every arm had its bar written before it ran. Runs, traces and two open-weight judges' scores are compared in Arize Phoenix.

| System | Defects acted on (of 120) | Clean cases stopped (of 104) | Cost per decision | Median latency |
|---|---|---|---|---|
| Plain rules a buyer already has | 84 | 0 | 0 | 0 |
| v3 on Claude, run 1 | 17 | 5 | $0.0086 | 3.1 s |
| v4 on Claude, run 1 | 0 | 21 | $0.0245 | 4.3 s |
| Open model, reasoning off | 0 | 48 | $0.0024 | 2.1 s |
| + its arithmetic rechecked in code | 0 | 32 | $0.0025 | 2.1 s |
| + reasoning high | 0 | 24 | $0.0094 | 7.8 s |

Safety held on the open model in every arm, at a tenth of the cost. Over-caution failed the bar (21) in every arm; the best missed by 3, and the open arms ran once each. What changed and why: [`product/build-learnings.md`](product/build-learnings.md); full table: [`ai-stack/README.md`](ai-stack/README.md).

### v1 and v2 (26 fixtures)

10 planted failures, 10 clean controls and 6 counterfactual pairs. The bar for v2, set before building, was to beat v1 on catch rate, over-holds, cost and latency together.

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
