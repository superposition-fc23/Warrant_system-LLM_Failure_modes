# Demo script (synthetic data)

1. **Retrieval is grounded:** `.venv/bin/python rag.py ask "Who must approve a Brightline purchase order above 25,000 USD?"`. The amendment should outrank the base MSA.
2. **The gate catches a valid-credential, expired-belief write:** `.venv/bin/python agents.py --case PD-11`. Gates 1 and 2 pass; gate 3 holds on a 95 minute old observation with a 30 minute window.
3. **Tenant scope:** `--case PD-01` holds, `--case CTRL-01` acts. Same action, different tenant.
4. **Evals without labels:** `.venv/bin/python judge.py`. Read the catch rate, then the counter-metric, then show PD-07 failing and say why (recency over qualification).
5. **Routing:** `.venv/bin/python router.py` shows why the gate uses a reasoning model and triage would use a cheap one.

Line to carry: output evals tell you it was wrong after it was wrong; belief evals tell you it is about to be.
