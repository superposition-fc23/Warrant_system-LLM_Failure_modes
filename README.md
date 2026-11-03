# Warrant

A checkpoint for AI agents in customer service. When an agent is about to take a money action, such as a credit or a refund, Warrant reads the source systems. If they disagree, it holds the action and names the exact fact in conflict, so a person can rule on it. Each ruling becomes a standing rule and an eval case.

Built for an enterprise AI case challenge. The commits and pull requests are kept as a public record of how it developed.

## Where to look

| What | Where |
|---|---|
| The product report, from failure mode to requirements | [`index.html`](index.html) |
| The demo, rendered from real run data | [`prototype.html`](prototype.html) |
| The gate, MCP tools and evals | [`ai-stack/`](ai-stack/): `warrant.py`, `crm_mcp.py`, `crm_eval.py` |
| Run logs: traces, decision records, summaries | [`ai-stack/runs/`](ai-stack/runs/) |
| What building this changed about how I build | [`product/build-learnings.md`](product/build-learnings.md) |
| How data is classified and protected | [`DATA_GOVERNANCE.md`](DATA_GOVERNANCE.md) |

## Results so far

All cases are synthetic: 10 planted failures, 10 clean controls and 6 counterfactual pairs. The bar for v2, set before building, was to beat v1 on catch rate, over-holds, cost and latency together.

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

The eval needs an Anthropic API key in `.env`. Full forum text is not in this repo, so the evidence classification cannot be rerun from here; each row keeps its source link. A local cache holds the text.
