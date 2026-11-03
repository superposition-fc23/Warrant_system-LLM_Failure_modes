# Demo script (synthetic data)

1. **Retrieval is grounded:** `.venv/bin/python rag.py ask "Who must approve a Brightline purchase order above 25,000 USD?"`. The amendment should outrank the base MSA.
2. **The gate catches a valid-credential, expired-belief write:** `.venv/bin/python agents.py --case PD-11`. Gates 1 and 2 pass; gate 3 holds on a 95 minute old observation with a 30 minute window.
3. **Tenant scope:** `--case PD-01` holds, `--case CTRL-01` acts. Same action, different tenant.
4. **Evals without labels:** `.venv/bin/python judge.py`. Read the catch rate, then the counter-metric, then show PD-07 failing and say why (recency over qualification).
5. **Routing:** `.venv/bin/python router.py` shows why the gate uses a reasoning model and triage would use a cheap one.

Line to carry: output evals tell you it was wrong after it was wrong; belief evals tell you it is about to be.

## Warrant live path (test accounts, seeded data)

Double-click `Warrant Demo.command` in the project folder. It opens the prototype; go to tab 8, Live demo.

1. **Start clean demo.** It clears earlier rulings by itself. The clean credit is applied, written to the Chargebee test site, with no card.
2. **Second agent, same incident:** gathers on belief alone, with P(safe) and a re-read time. Click **Keep held** in Slack, and the tab shows billing's reliability fall.
3. **Over-cap credit:** held, with the clause and its source on the card. Click **Keep held**.
4. **Run again, keep my rulings.** The next clean credit shows the lower P(safe).

If the model API or anything live fails, use **Replay a recorded run** on the same tab. It makes no calls and also works when the prototype is opened from the file. Say it is a replay. It includes the recorded Commit click that wrote a second credit.

Rehearsal only, in a separate run: click **Commit** on the lag card. It should refuse and say why.

Say first: real are the agent, gate, HubSpot and Chargebee test reads, the credit write and Slack clicks. Scripted are the tickets. Contracts and risk are local fixtures. Each run uses clean accounts from the pool; `seed_live.py` adds more if `POOL` is raised.
