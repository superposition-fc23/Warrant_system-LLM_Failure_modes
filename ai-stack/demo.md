# Demo script (synthetic data)

1. **Retrieval is grounded:** `.venv/bin/python rag.py ask "Who must approve a Brightline purchase order above 25,000 USD?"`. The amendment should outrank the base MSA.
2. **The gate catches a valid-credential, expired-belief write:** `.venv/bin/python agents.py --case PD-11`. Gates 1 and 2 pass; gate 3 holds on a 95 minute old observation with a 30 minute window.
3. **Tenant scope:** `--case PD-01` holds, `--case CTRL-01` acts. Same action, different tenant.
4. **Evals without labels:** `.venv/bin/python judge.py`. Read the catch rate, then the counter-metric, then show PD-07 failing and say why (recency over qualification).
5. **Routing:** `.venv/bin/python router.py` shows why the gate uses a reasoning model and triage would use a cheap one.

Line to carry: output evals tell you it was wrong after it was wrong; belief evals tell you it is about to be.

## Warrant v3 live path (test accounts, seeded data)

Before the call, clear earlier rulings so the first run posts both cards:

    rm -f state/rules.json state/ledger.jsonl state/beliefs.json
    .venv/bin/python agent.py v4 slack belief-only 900

1. Clean credit: applied, written to the Chargebee test site, no notification.
2. Second agent, same incident: held, naming the first credit. Click Keep held, then Make this a standing rule.
3. Over-cap credit: held, naming the contract cap. Click either button.
4. Run the same command again without clearing: the duplicate is settled by the rule, with no card.

Say first: real are the agent, gate, HubSpot and Chargebee test reads, the credit write and Slack clicks. Scripted are the tickets. Contracts and risk are local fixtures. Each run uses clean accounts from the pool; `seed_live.py` adds more if `POOL` is raised.
