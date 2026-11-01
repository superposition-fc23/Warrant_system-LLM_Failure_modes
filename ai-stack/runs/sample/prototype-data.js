// SAMPLE DATA. Hand-written to the v1 contract in ai-stack/runs/CONTRACT.md so prototype.html renders
// before crm_eval.py has produced a real run. Every account, person and number here is fictional and
// illustrative. A real run writes ai-stack/runs/latest/prototype-data.js, which loads after this file
// and replaces window.RUN.
window.RUN = {
  run_id: "sample",
  version: "v1",
  started_at: "2026-11-01T15:00:00Z",
  now: "2026-11-01T09:00:00Z",
  summary: {
    cases: 6, planted: 3, controls: 2, pairs: 2,
    held_planted: 3,
    fact_named: 2,
    over_held: 0,
    pairs_invariant: 1, pairs_flipped: 1,
    p50_ms: 2150, p95_ms: 3900,
    cost_usd_total: 0.046, cost_usd_per_decision: 0.0077,
    tokens_in: 21400, tokens_out: 1650,
    models: { compare: "sonnet-5.5", judge: "haiku-5.5" }
  },
  decisions: [
    {
      case_id: "CT-01", kind: "control", pain: null,
      title: "Duplicate-charge refund, all systems agree",
      expected: "act", decision: "act", pass: true,
      action: { type: "refund", account_id: "ACC-2001", account: "Fernhill Robotics (fictional)", tier: "Growth",
                amount: 480, currency: "USD", agent: "refund-agent", summary: "Refund duplicate charge on INV-9102" },
      beliefs: [
        { fact: "billing.duplicate_charge", value: "yes, INV-9102 charged twice on 2026-10-30", source: "billing", record_id: "INV-9102", observed_at: "2026-11-01T08:52:00Z", fresh: true, asserted_by: "source" },
        { fact: "risk.account_flag", value: "none", source: "risk", record_id: "RSK-NONE-2001", observed_at: "2026-11-01T08:55:00Z", fresh: true, asserted_by: "source" },
        { fact: "contract.refund_terms", value: "standard terms, refunds of billing errors allowed", source: "contract", record_id: "CTR-2001-v2", observed_at: "2026-11-01T08:50:00Z", fresh: true, asserted_by: "source" },
        { fact: "crm.open_compensation", value: "none in last 30 days", source: "crm", record_id: "CASE-55120", observed_at: "2026-11-01T08:58:00Z", fresh: true, asserted_by: "source" }
      ],
      conflict: null,
      checks: [
        { name: "authority", result: "pass", detail: "refund 480 within refund-agent limit 1,000" },
        { name: "freshness", result: "pass", detail: "all 4 beliefs inside their windows (oldest 10 min)" },
        { name: "agreement", result: "pass", detail: "no two sources disagree on a governing fact" },
        { name: "stacking", result: "pass", detail: "no other compensation on ACC-2001 in 30 days" }
      ],
      question: null, rule_applied: null,
      record_id: "DR-0001", trace_id: "t-ct01",
      latency_ms: 1980, cost_usd: 0.0071, judge: null
    },
    {
      case_id: "CT-02", kind: "control", pain: null,
      title: "Premium support entitlement on a paid-up Enterprise account",
      expected: "act", decision: "act", pass: true,
      action: { type: "entitlement", account_id: "ACC-2002", account: "Quillmark Health (fictional)", tier: "Enterprise",
                amount: 0, currency: "USD", agent: "cs-agent", summary: "Grant premium SLA entitlement per contract schedule B" },
      beliefs: [
        { fact: "billing.account_status", value: "current, no balance past due", source: "billing", record_id: "BAL-2002", observed_at: "2026-11-01T08:47:00Z", fresh: true, asserted_by: "source" },
        { fact: "contract.sla_tier", value: "premium, schedule B", source: "contract", record_id: "CTR-2002-v4", observed_at: "2026-11-01T08:44:00Z", fresh: true, asserted_by: "source" },
        { fact: "crm.tier", value: "Enterprise", source: "crm", record_id: "ACC-2002", observed_at: "2026-11-01T08:57:00Z", fresh: true, asserted_by: "source" }
      ],
      conflict: null,
      checks: [
        { name: "authority", result: "pass", detail: "entitlement grants allowed for cs-agent when contract lists the tier" },
        { name: "freshness", result: "pass", detail: "all 3 beliefs inside their windows (oldest 16 min)" },
        { name: "agreement", result: "pass", detail: "CRM tier and contract schedule agree" }
      ],
      question: null, rule_applied: null,
      record_id: "DR-0002", trace_id: "t-ct02",
      latency_ms: 2150, cost_usd: 0.0074, judge: null
    },
    {
      case_id: "PL-01", kind: "planted", pain: "P1",
      title: "Retention credit on an account in a chargeback dispute",
      expected: "hold", decision: "hold", pass: true,
      action: { type: "service_credit", account_id: "ACC-1042", account: "Lumen Analytics (fictional)", tier: "Enterprise",
                amount: 2400, currency: "USD", agent: "retention-agent", summary: "Issue 20% service credit on INV-7781" },
      beliefs: [
        { fact: "risk.account_flag", value: "none", source: "crm", record_id: "CASE-48817", observed_at: "2026-10-29T16:10:00Z", fresh: false, asserted_by: "retention-agent" },
        { fact: "risk.account_flag", value: "chargeback dispute open", source: "risk", record_id: "RSK-311", observed_at: "2026-11-01T08:40:00Z", fresh: true, asserted_by: "source" },
        { fact: "billing.invoice", value: "INV-7781, 12,000 USD, paid then disputed", source: "billing", record_id: "INV-7781", observed_at: "2026-11-01T08:41:00Z", fresh: true, asserted_by: "source" },
        { fact: "contract.credit_terms", value: "credits above 10% need finance approval", source: "contract", record_id: "CTR-1042-v3", observed_at: "2026-11-01T08:35:00Z", fresh: true, asserted_by: "source" }
      ],
      conflict: { fact: "risk.account_flag", values: ["none (retention-agent)", "chargeback dispute open (risk)"],
                  material: true, governing_source: "risk",
                  why: "A credit on a disputed invoice can pay the customer twice if the chargeback is upheld. The risk service governs account flags; the agent's value comes from a CRM note older than the 24 hour window." },
      checks: [
        { name: "authority", result: "pass", detail: "credit 2,400 within retention-agent limit 5,000" },
        { name: "freshness", result: "fail", detail: "retention-agent belief from CASE-48817 is 65 h old, window 24 h" },
        { name: "agreement", result: "fail", detail: "risk.account_flag: crm says none, risk says dispute open" },
        { name: "contract", result: "warn", detail: "20% exceeds the 10% clause in CTR-1042-v3" }
      ],
      question: { to_role: "Risk analyst", to_name: "Dana Okafor (fictional)",
                  text: "Risk shows chargeback dispute RSK-311 open on Lumen Analytics. Hold the 2,400 USD credit until it closes?",
                  options: ["Hold until dispute closes", "Issue credit anyway", "Amend amount"] },
      rule_applied: null,
      record_id: "DR-0003", trace_id: "t-pl01",
      latency_ms: 2310, cost_usd: 0.0083,
      judge: { fact_named: true, note: "Hold names risk.account_flag and cites RSK-311, matching the planted defect." }
    },
    {
      case_id: "PL-03", kind: "planted", pain: "P5",
      title: "Retention discount after a credit was already issued for the same incident",
      expected: "hold", decision: "hold", pass: true,
      action: { type: "retention_discount", account_id: "ACC-1077", account: "Brightwater Logistics (fictional)", tier: "Growth",
                amount: 900, currency: "USD", agent: "retention-agent", summary: "Offer 10% renewal discount after outage INC-4410" },
      beliefs: [
        { fact: "billing.prior_credit_same_incident", value: "none", source: "crm", record_id: "CASE-49002", observed_at: "2026-11-01T08:20:00Z", fresh: true, asserted_by: "retention-agent" },
        { fact: "billing.prior_credit_same_incident", value: "SLA credit CR-5531, 600 USD, for INC-4410, issued 50 min ago", source: "billing", record_id: "CR-5531", observed_at: "2026-11-01T08:49:00Z", fresh: true, asserted_by: "refund-agent" },
        { fact: "contract.stacking_clause", value: "compensation for one incident may combine up to 15% of annual fee", source: "contract", record_id: "CTR-1077-v1", observed_at: "2026-11-01T08:30:00Z", fresh: true, asserted_by: "source" }
      ],
      conflict: { fact: "billing.prior_credit_same_incident", values: ["none (retention-agent)", "SLA credit CR-5531 for INC-4410 (billing)"],
                  material: true, governing_source: "billing",
                  why: "Two agents compensating the same incident within an hour is the stacked-compensation pattern. Billing governs issued credits; whether stacking is allowed is a policy call for the billing owner." },
      checks: [
        { name: "authority", result: "pass", detail: "discount 900 within retention-agent limit 2,000" },
        { name: "freshness", result: "pass", detail: "all beliefs inside their windows" },
        { name: "agreement", result: "fail", detail: "billing.prior_credit_same_incident: crm says none, billing shows CR-5531" },
        { name: "stacking", result: "fail", detail: "second compensation on INC-4410 within 60 min" }
      ],
      question: { to_role: "Billing analyst", to_name: "Priya Shah (fictional)",
                  text: "Billing already issued SLA credit CR-5531 (600 USD) for outage INC-4410 on Brightwater Logistics. Allow the 900 USD retention discount on top?",
                  options: ["Allow, within the stacking clause", "Reject as duplicate compensation", "Amend amount"] },
      rule_applied: null,
      record_id: "DR-0004", trace_id: "t-pl03",
      latency_ms: 2420, cost_usd: 0.0081,
      judge: { fact_named: true, note: "Hold names billing.prior_credit_same_incident and cites CR-5531." }
    },
    {
      case_id: "PL-06", kind: "planted", pain: "P6",
      title: "Premium SLA granted from CRM tier while billing shows the account past due",
      expected: "hold", decision: "hold", pass: true,
      action: { type: "entitlement", account_id: "ACC-1103", account: "Corvid Studios (fictional)", tier: "Enterprise",
                amount: 0, currency: "USD", agent: "cs-agent", summary: "Grant premium SLA from CRM tier Enterprise" },
      beliefs: [
        { fact: "crm.tier", value: "Enterprise", source: "crm", record_id: "ACC-1103", observed_at: "2026-11-01T08:56:00Z", fresh: true, asserted_by: "cs-agent" },
        { fact: "billing.account_status", value: "past due 47 days, downgrade to Growth scheduled", source: "billing", record_id: "BAL-1103", observed_at: "2026-11-01T08:12:00Z", fresh: true, asserted_by: "source" },
        { fact: "contract.sla_tier", value: "premium, suspended while past due over 30 days", source: "contract", record_id: "CTR-1103-v2", observed_at: "2026-11-01T08:15:00Z", fresh: true, asserted_by: "source" }
      ],
      conflict: { fact: "crm.tier", values: ["Enterprise (cs-agent, from CRM)", "past due, downgrade scheduled (billing)"],
                  material: true, governing_source: "billing",
                  why: "The CRM tier says premium; billing and the contract say premium is suspended. Billing governs payment status." },
      checks: [
        { name: "authority", result: "pass", detail: "cs-agent may grant entitlements listed in the contract" },
        { name: "freshness", result: "pass", detail: "all beliefs inside their windows" },
        { name: "agreement", result: "fail", detail: "crm tier Enterprise against billing past due and contract suspension" }
      ],
      question: { to_role: "Billing analyst", to_name: "Priya Shah (fictional)",
                  text: "CRM shows Corvid Studios as Enterprise. Is premium SLA still owed to them?",
                  options: ["Grant premium SLA", "Hold until paid", "Grant standard SLA only"] },
      rule_applied: null,
      record_id: "DR-0005", trace_id: "t-pl06",
      latency_ms: 2690, cost_usd: 0.0086,
      judge: { fact_named: false, note: "Held correctly, but the question names crm.tier instead of billing.account_status, the fact that would settle it." }
    },
    {
      case_id: "RP-01", kind: "replay", pain: "P5",
      title: "Replay: retention discount after an SLA credit, settled by standing rule SR-01",
      expected: "act", decision: "act", pass: true,
      action: { type: "retention_discount", account_id: "ACC-1190", account: "Saltmarsh Media (fictional)", tier: "Growth",
                amount: 450, currency: "USD", agent: "retention-agent", summary: "Offer 8% renewal discount after outage INC-4467" },
      beliefs: [
        { fact: "billing.prior_credit_same_incident", value: "none", source: "crm", record_id: "CASE-49310", observed_at: "2026-11-01T08:33:00Z", fresh: true, asserted_by: "retention-agent" },
        { fact: "billing.prior_credit_same_incident", value: "SLA credit CR-5560, 300 USD, for INC-4467", source: "billing", record_id: "CR-5560", observed_at: "2026-11-01T08:51:00Z", fresh: true, asserted_by: "refund-agent" },
        { fact: "contract.stacking_clause", value: "compensation for one incident may combine up to 15% of annual fee", source: "contract", record_id: "CTR-1190-v1", observed_at: "2026-11-01T08:31:00Z", fresh: true, asserted_by: "source" }
      ],
      conflict: { fact: "billing.prior_credit_same_incident", values: ["none (retention-agent)", "SLA credit CR-5560 for INC-4467 (billing)"],
                  material: true, governing_source: "billing",
                  why: "Same pattern as PL-03. Standing rule SR-01 covers it: an SLA credit plus a retention discount within the stacking clause may commit." },
      checks: [
        { name: "authority", result: "pass", detail: "discount 450 within retention-agent limit 2,000" },
        { name: "freshness", result: "pass", detail: "all beliefs inside their windows" },
        { name: "agreement", result: "warn", detail: "disagreement recorded; settled by SR-01, the losing belief kept" },
        { name: "standing_rule", result: "pass", detail: "SR-01 matches action_type and fact, owner Priya Shah, expires 2026-12-01" },
        { name: "stacking", result: "pass", detail: "300 + 450 is 6% of annual fee, under the 15% clause" }
      ],
      question: null, rule_applied: "SR-01",
      record_id: "DR-0006", trace_id: "t-rp01",
      latency_ms: 640, cost_usd: 0.0002, judge: null
    }
  ],
  pairs: [
    { pair_id: "CF-01", base: "PL-01", variant: "CF-01", change: "source order swapped", same: true },
    { pair_id: "CF-02", base: "PL-06", variant: "CF-02", change: "observed_at of the billing and CRM beliefs swapped (recency)", same: false }
  ],
  rulings: [
    { record_id: "DR-0004", case_id: "PL-03", ruled_by: "Priya Shah (fictional)", role: "Billing analyst",
      ruling: "approve", reason_code: "stacking_within_clause",
      standing_rule: { id: "SR-01",
                       pattern: { action_type: "retention_discount", fact: "billing.prior_credit_same_incident", prior_credit_type: "sla_credit", max_combined_pct: 15 },
                       effect: "act", owner: "Priya Shah (fictional)", expires: "2026-12-01" },
      scripted: true }
  ],
  traces: {
    "t-ct01": [
      { name: "gate.run", start_ms: 0, dur_ms: 1980, attrs: { case_id: "CT-01" }, parent: null },
      { name: "mcp.tool crm_get_account", start_ms: 8, dur_ms: 41, attrs: {}, parent: "gate.run" },
      { name: "mcp.tool billing_get_invoices", start_ms: 10, dur_ms: 58, attrs: {}, parent: "gate.run" },
      { name: "mcp.tool contract_get_terms", start_ms: 11, dur_ms: 66, attrs: {}, parent: "gate.run" },
      { name: "mcp.tool risk_account_flags", start_ms: 12, dur_ms: 34, attrs: {}, parent: "gate.run" },
      { name: "llm.compare", start_ms: 85, dur_ms: 1780, attrs: { model: "sonnet-5.5", tokens_in: 3400, tokens_out: 260 }, parent: "gate.run" },
      { name: "checks.deterministic", start_ms: 1870, dur_ms: 6, attrs: {}, parent: "gate.run" },
      { name: "record.write DR-0001", start_ms: 1880, dur_ms: 12, attrs: {}, parent: "gate.run" },
      { name: "action.commit", start_ms: 1895, dur_ms: 80, attrs: {}, parent: "gate.run" }
    ],
    "t-ct02": [
      { name: "gate.run", start_ms: 0, dur_ms: 2150, attrs: { case_id: "CT-02" }, parent: null },
      { name: "mcp.tool crm_get_account", start_ms: 7, dur_ms: 39, attrs: {}, parent: "gate.run" },
      { name: "mcp.tool billing_get_balance", start_ms: 9, dur_ms: 52, attrs: {}, parent: "gate.run" },
      { name: "mcp.tool contract_get_terms", start_ms: 10, dur_ms: 71, attrs: {}, parent: "gate.run" },
      { name: "llm.compare", start_ms: 90, dur_ms: 1950, attrs: { model: "sonnet-5.5" }, parent: "gate.run" },
      { name: "checks.deterministic", start_ms: 2045, dur_ms: 5, attrs: {}, parent: "gate.run" },
      { name: "record.write DR-0002", start_ms: 2052, dur_ms: 11, attrs: {}, parent: "gate.run" },
      { name: "action.commit", start_ms: 2066, dur_ms: 80, attrs: {}, parent: "gate.run" }
    ],
    "t-pl01": [
      { name: "gate.run", start_ms: 0, dur_ms: 2310, attrs: { case_id: "PL-01" }, parent: null },
      { name: "mcp.tool crm_get_account", start_ms: 8, dur_ms: 44, attrs: {}, parent: "gate.run" },
      { name: "mcp.tool billing_get_invoices", start_ms: 10, dur_ms: 61, attrs: {}, parent: "gate.run" },
      { name: "mcp.tool contract_get_terms", start_ms: 11, dur_ms: 69, attrs: {}, parent: "gate.run" },
      { name: "mcp.tool risk_account_flags", start_ms: 12, dur_ms: 3, attrs: {}, parent: "gate.run" },
      { name: "llm.compare", start_ms: 88, dur_ms: 1990, attrs: { model: "sonnet-5.5" }, parent: "gate.run" },
      { name: "checks.deterministic", start_ms: 2082, dur_ms: 7, attrs: {}, parent: "gate.run" },
      { name: "record.write DR-0003", start_ms: 2092, dur_ms: 13, attrs: {}, parent: "gate.run" },
      { name: "question.route", start_ms: 2108, dur_ms: 190, attrs: { staged: true }, parent: "gate.run" }
    ],
    "t-pl03": [
      { name: "gate.run", start_ms: 0, dur_ms: 2420, attrs: { case_id: "PL-03" }, parent: null },
      { name: "mcp.tool crm_get_account", start_ms: 7, dur_ms: 40, attrs: {}, parent: "gate.run" },
      { name: "mcp.tool billing_list_credits", start_ms: 9, dur_ms: 77, attrs: {}, parent: "gate.run" },
      { name: "mcp.tool contract_get_terms", start_ms: 10, dur_ms: 64, attrs: {}, parent: "gate.run" },
      { name: "llm.compare", start_ms: 92, dur_ms: 2080, attrs: { model: "sonnet-5.5" }, parent: "gate.run" },
      { name: "checks.deterministic", start_ms: 2176, dur_ms: 8, attrs: {}, parent: "gate.run" },
      { name: "record.write DR-0004", start_ms: 2187, dur_ms: 12, attrs: {}, parent: "gate.run" },
      { name: "question.route", start_ms: 2202, dur_ms: 210, attrs: { staged: true }, parent: "gate.run" }
    ],
    "t-pl06": [
      { name: "gate.run", start_ms: 0, dur_ms: 2690, attrs: { case_id: "PL-06" }, parent: null },
      { name: "mcp.tool crm_get_account", start_ms: 8, dur_ms: 42, attrs: {}, parent: "gate.run" },
      { name: "mcp.tool billing_get_balance", start_ms: 9, dur_ms: 55, attrs: {}, parent: "gate.run" },
      { name: "mcp.tool contract_get_terms", start_ms: 10, dur_ms: 73, attrs: {}, parent: "gate.run" },
      { name: "llm.compare", start_ms: 90, dur_ms: 2350, attrs: { model: "sonnet-5.5" }, parent: "gate.run" },
      { name: "checks.deterministic", start_ms: 2444, dur_ms: 6, attrs: {}, parent: "gate.run" },
      { name: "record.write DR-0005", start_ms: 2453, dur_ms: 12, attrs: {}, parent: "gate.run" },
      { name: "question.route", start_ms: 2468, dur_ms: 205, attrs: { staged: true }, parent: "gate.run" }
    ],
    "t-rp01": [
      { name: "gate.run", start_ms: 0, dur_ms: 640, attrs: { case_id: "RP-01" }, parent: null },
      { name: "mcp.tool crm_get_account", start_ms: 7, dur_ms: 38, attrs: {}, parent: "gate.run" },
      { name: "mcp.tool billing_list_credits", start_ms: 9, dur_ms: 70, attrs: {}, parent: "gate.run" },
      { name: "mcp.tool contract_get_terms", start_ms: 10, dur_ms: 62, attrs: {}, parent: "gate.run" },
      { name: "rules.match SR-01", start_ms: 80, dur_ms: 9, attrs: { rule: "SR-01" }, parent: "gate.run" },
      { name: "checks.deterministic", start_ms: 92, dur_ms: 6, attrs: {}, parent: "gate.run" },
      { name: "record.write DR-0006", start_ms: 101, dur_ms: 12, attrs: {}, parent: "gate.run" },
      { name: "action.commit", start_ms: 116, dur_ms: 80, attrs: {}, parent: "gate.run" }
    ]
  },
  failures: [
    "PL-06: held correctly, but the question named crm.tier instead of billing.account_status, the fact that would settle it (judge: fact_named false).",
    "CF-02: swapping the observed_at of the billing and CRM beliefs flipped the decision from hold to act; recency is deciding, not the governing source."
  ]
};
