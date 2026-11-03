window.WARRANT_REPLAY = {
 "run": "v4-agent-20261103T0504",
 "steps": [
  {
   "ticket": "T1",
   "agent": "cs-agent",
   "account": "ACC-3007",
   "amount": 300,
   "decision": "act",
   "status": "applied",
   "p_safe": 0.9752,
   "vetoed_by": null,
   "wait_seconds": null,
   "fact": null,
   "card": null,
   "credit_id": "pc_6obJiVZsq5BqI04",
   "reply": "Hello Harbor Freight Labs,\n\nWe've applied the credit to account ACC-3007. The credit is 300 USD, which is 5% of your 6,000 USD monthly fee, for the one SLA breach in October (incident INC-110305041). The credit ID is pc_6obJiVZsq5BqI04.\n\nPlease contact us if you have any other questions.",
   "ruling": null,
   "seconds_to_ruling": null,
   "ruling_credit": null,
   "belief_update": null
  },
  {
   "ticket": "T2",
   "agent": "retention-agent",
   "account": "ACC-3007",
   "amount": 300,
   "decision": "gather",
   "status": "held",
   "p_safe": 0.0214,
   "vetoed_by": null,
   "wait_seconds": 285,
   "fact": "P(safe) 0.021. Main doubt: the credit list may not yet show a recent write. Re-read in 285 s.",
   "card": [
    ":raised_hand: *Held before commit*\n*retention-agent* proposes a service credit of *300 USD* on ACC-3007",
    "*Why:* P(safe) 0.021. Main doubt: the credit list may not yet show a recent write. Re-read in 285 s.\n*Question for Billing analyst:* Keep this held, or commit it?",
    "Rationale: Goodwill credit for customer impacted by incident INC-110305041 who is at risk of churning.  |  record DR-0002  |  seeded test data"
   ],
   "credit_id": null,
   "reply": "Hello Harbor Freight Labs,\n\nThank you for your patience, and I'm sorry about the disruption from incident INC-110305041. I tried to apply a 300 USD goodwill credit to your account. **The credit has not been applied yet.** It is on hold while a billing analyst finishes a verification check. The system will re-check in about five minutes.\n\nI can't promise a credit until that check clears. I'll keep ",
   "ruling": "commit",
   "seconds_to_ruling": 311,
   "ruling_credit": "pc_AzqZ6BVZsrQdXJ5E",
   "belief_update": {
    "source": "billing",
    "before": 0.995,
    "after": 0.995
   }
  },
  {
   "ticket": "T3",
   "agent": "cs-agent",
   "account": "ACC-3008",
   "amount": 900,
   "decision": "hold",
   "status": "held",
   "p_safe": 0.005,
   "vetoed_by": "contract_cap",
   "wait_seconds": null,
   "fact": "Above the contract's credit cap: 900 against cap 600 (10% of 6000.0, OF-3008)",
   "card": [
    ":raised_hand: *Held before commit*\n*cs-agent* proposes a service credit of *900 USD* on ACC-3008",
    "*Why:* Above the contract's credit cap: 900 against cap 600 (10% of 6000.0, OF-3008)\n*Source:* OF-3008, order form, signed, from the local contract records (a CLM in production)\n*Clause:* \"Service credits in any month may not exceed 10% of that month's subscription fee.\"\n*Question for Billing analyst:* Commit anyway?",
    "Rationale: Customer requested a 15% credit of the 6,000 USD monthly fee for three days of degraded service during INC-110305042.  |  record DR-0003  |  seeded test data"
   ],
   "credit_id": null,
   "reply": "Hello Harbor Freight Labs,\n\nThank you for your patience during the three days of degraded service on INC-110305042. I'm sorry for the disruption.\n\nWe have not applied the 900 USD credit (15% of your monthly fee) you asked for. Your contract caps service credits at 10% of the monthly fee, which is 600 USD. Because your request is above that cap, the system held it. It is now waiting for review by a",
   "ruling": "reject",
   "seconds_to_ruling": 588,
   "ruling_credit": null,
   "belief_update": null
  }
 ]
};
