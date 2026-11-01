# AI stack for the Dyssonance live case

Python 3.12, managed by uv. Every script runs from this folder. Everything in `docs/` is synthetic.

| File | What it is | Try it |
|---|---|---|
| `llm.py` | `ask()`, `speak()`, `transcribe()` across Claude, GPT, Gemini, Deepgram. Model registry with ids, costs, modality | `.venv/bin/python llm.py` |
| `router.py` | XGBoost classifier choosing a model from task, modality, cost, latency, quality, input size. Policy is in `label()` | `.venv/bin/python router.py` |
| `rag.py` | LlamaIndex + local Chroma + local embeddings. Retrieval needs no key | `.venv/bin/python rag.py index docs` then `rag.py ask "question"` |
| `agents.py` | LangGraph belief-gated agent: retrieve governing beliefs, warrant gate (current, uncontested, in tenant scope), act or draft and escalate | `.venv/bin/python agents.py --case PD-02` |
| `judge.py` | LLM-as-judge over the planted-defect set: catch rate, fact named, over-hold rate on clean controls (counter-metric) | `.venv/bin/python judge.py` |
| `rag_eval.py` | Retrieval eval: recall@3, precision@3, MRR across chunk sizes, questions from the planted set | `.venv/bin/python rag_eval.py` |
| `docs/` | One folder per idea in the probable ideas list, each with planted defects. See `docs/README.md` | |
| `evals/planted_defects.json` | Ground truth by construction: 11 planted defects plus a clean control | |

## Baseline on 30 Oct (real models, keys set)

- Retrieval: recall@3 1.00, MRR 0.83 at chunk 256/32.
- Judge: 10 of 11 planted defects held, 9 of 11 named the discriminating fact, 0 of 1 clean controls over-held.
- **Known miss, PD-07:** the gate trusted the newer seller self-report over the older certified inspection (recency bias). Good live example of auditing output.
- **Weakness to say out loud:** one clean control is not enough to measure over-holding. Add controls before trusting the counter-metric.

## Keys

    cp .env.example .env     # then paste keys into .env

Without keys everything still runs: retrieval is real, the gate falls back to deterministic front-matter checks, the judge to keyword overlap.

## Adapting live

- New idea or data: drop files in `docs/<folder>/` with the same front matter (source, tenant, version, effective_from, observed_at, validity_window, supersedes), then `rag.py index docs`.
- New eval case: add a row to `evals/planted_defects.json` (action, tenant, defect, expected, discriminating_fact, question, gold_phrase).
- If imports fail or the folder moves: `./setup.sh`.
