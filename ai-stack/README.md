# AI stack for Warrant

Python 3.12, managed by uv. Every script runs from this folder. Everything in `docs/` and `evals/` is synthetic.

Architecture: [`v5`](../product/diagrams/warrant-v5-architecture.svg) and its [data flow](../product/diagrams/warrant-v5-data-flow.svg); the [`v4`](../product/diagrams/warrant-architecture.svg) figures match the report.

## The gate

| File | What it is | Try it |
|---|---|---|
| `warrant.py` | The gate: a fixed LangGraph pipeline with no cycles (read sources, freshness, checks, rules, compare, decide, re-read, commit or route, record) | `.venv/bin/python warrant.py PL-01` |
| `belief.py` | The belief layer: P(safe) from ageing evidence, expected loss against the cost of delay. Priors frozen in `belief_priors.json` | |
| `crm_mcp.py` | Read-only MCP server over CRM, billing, contracts, risk and authority limits | |
| `callguard.py` | Every model call passes one guard: a span per attempt, rate and concurrency caps, a circuit breaker (immediate on 401, 402, 403), run budgets in calls and dollars, loop detection per trace. SDK retries are off | `.venv/bin/python test_callguard.py` |
| `llm.py` | `ask()` across Claude, GPT, Gemini and Together AI open-weight models, plus a scripted fake provider. Prompts, replies, tokens and reasoning tokens go on OpenInference spans | `.venv/bin/python llm.py` |
| `verify.py` | Optional (`WARRANT_VERIFY_CLAIMS=1`): the model states the arithmetic behind a conflict as a claim, code recomputes it, and a false claim drops the conflict | `.venv/bin/python test_verify.py` |
| `facts.py` | Optional (`WARRANT_COMPUTED_FACTS=1`): neutral numbers computed by code go into the prompt. No gain in v5; kept for the record | `.venv/bin/python test_facts.py` |
| `telemetry.py` | OpenTelemetry spans to JSON lines per run; with `WARRANT_OTLP_ENDPOINT` set, also to Arize Phoenix | |
| `test_warrant.py` | 36 gate tests, no model calls | `.venv/bin/python test_warrant.py` |

v4's defaults are unchanged: compare model Sonnet 5.5, a 2,000-token output cap, verification and facts off. Open-model runs set them by env vars and are labelled apart.

## Evals

| File | What it is |
|---|---|
| `crm_eval.py` | The 36 fixtures (planted, controls, injections, pairs, replay), five runs, LLM judge on the named fact |
| `mutation_eval.py` | The 224 generated cases (120 planted defects, 104 clean), plain-rules baseline, sharded runs, per-run scores |
| `v5/bars/` | One bar per arm, written before its run |
| `v5/check_bar.py` | Scores a run against its bar: defects acted on by tier, clean cases stopped, unreadable replies, cost, latency |
| `v5/live_run.py` | Fixture cases through the real gate on a Together model, traced to Phoenix |
| `v5/judge_holds.py` | Two open-weight judges (MiniMax-M3.1-Flash, gpt-oss-120b) score whether each hold named the planted fact, 0 to 2 |
| `v5/push_phoenix.py`, `push_experiment.py`, `push_judgements.py`, `import_traces.py` | Load datasets, experiments, judge annotations and stored traces into a local Phoenix. No model calls |

## v5 baseline, Nov 21 (224 generated cases)

Bar for every open arm, written first: 0 defects acted on, at most 5% unreadable replies, at most 21 clean cases stopped (v4's worst run on Claude).

| System | Defects acted on (of 120) | Clean cases stopped (of 104) | Cost per decision | Median latency |
|---|---|---|---|---|
| Plain rules | 84 | 0 | 0 | 0 |
| v3 on Claude, run 1 | 17 | 5 | $0.0086 | 3.1 s |
| v4 on Claude, run 1 | 0 | 21 | $0.0245 | 4.3 s |
| DeepSeek-V4.1-Flash, reasoning off | 0 | 48 | $0.0024 | 2.1 s |
| + arithmetic rechecked (`verify.py`) | 0 | 32 | $0.0025 | 2.1 s |
| + computed facts (`facts.py`) | 0 | 35 | $0.0024 | 1.9 s |
| Reasoning high + rechecked | 0 | 24 | $0.0094 | 7.8 s |

- **Safety held on the open model in every arm.** Over-caution failed the bar in every arm; the best missed by 3.
- **Known limits:** each open arm ran once; the judges (84% exact agreement on 703 holds) are not yet calibrated against human ratings.
- Details and rules learned: [`product/build-learnings.md`](../product/build-learnings.md).

## Keys

    cp .env.example .env     # then paste keys into .env

`ANTHROPIC_API_KEY` for the stored v1 to v4 setup. For open-weight runs, one Together key per role: `TOGETHER_GATE_API_KEY`, `TOGETHER_JUDGE2_API_KEY`, `TOGETHER_JUDGE3_API_KEY`. Without keys, every test still runs.

## Phoenix, locally

    PHOENIX_WORKING_DIR=$PWD/v5/.phoenix .venv/bin/python -m phoenix.server.main serve    # http://localhost:6006
    .venv/bin/python v5/push_phoenix.py                                                    # dataset and stored experiments

Phoenix state stays in `v5/.phoenix/` (gitignored). Stored traces are dated when they ran, so widen the time range to see them.

## Older work in this folder

`router.py` (XGBoost model router), `rag.py` and `rag_eval.py` (LlamaIndex and Chroma retrieval eval), `agents.py` (an early belief-gated agent) and `judge.py` (the first planted-defect judge) come from the first week. Their baseline, on 30 Oct: retrieval recall@3 1.00 and MRR 0.83; the judge held 10 of 11 planted defects. If imports fail or the folder moves: `./setup.sh`.
