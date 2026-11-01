# Run output contract (v1)

`crm_eval.py` writes one folder per run, `runs/<run_id>/`, and copies the latest to `runs/latest/`:

- `decisions.jsonl`: one decision record per case (shape of `decisions[]` below)
- `traces.jsonl`: one OpenTelemetry span per line
- `summary.json`: the run summary
- `prototype-data.js`: `window.RUN = {...}` with everything below, loaded by `prototype.html` via
  `<script src="ai-stack/runs/latest/prototype-data.js"></script>` (works from file://)

```js
window.RUN = {
  run_id: "v1-20261101T1500",
  version: "v1",
  started_at: "2026-11-01T15:00:00Z",
  now: "2026-11-01T09:00:00Z",          // reference clock of the synthetic systems
  summary: {
    cases: 26, planted: 10, controls: 10, pairs: 6,
    held_planted: 9,                     // planted cases not committed (hold or gather)
    fact_named: 8,                       // planted holds whose named fact matched, per the judge
    over_held: 1,                        // controls held
    pairs_invariant: 5, pairs_flipped: 1,
    p50_ms: 2100, p95_ms: 5400,
    cost_usd_total: 0.21, cost_usd_per_decision: 0.008,
    tokens_in: 120000, tokens_out: 9000,
    models: {"compare": "sonnet-5.5", "judge": "haiku-5.5"}
  },
  decisions: [{
    case_id: "PL-01", kind: "planted",   // planted | control | pair | replay
    pain: "P1",                          // P1, P5, P6, P8, P9 or null
    title: "Retention credit on an account in a chargeback dispute",
    expected: "hold",                    // act | gather | hold
    decision: "hold",
    pass: true,
    action: {type: "service_credit", account_id: "ACC-1042", account: "Lumen Analytics", tier: "Enterprise",
             amount: 2400, currency: "USD", agent: "retention-agent", summary: "Issue 20% service credit on INV-7781"},
    beliefs: [{fact: "risk.account_flag", value: "chargeback dispute open", source: "risk", record_id: "RSK-311",
               observed_at: "2026-11-01T08:40:00Z", fresh: true, asserted_by: "source"}],   // asserted_by: source | <agent name>
    conflict: {fact: "risk.account_flag", values: ["none (retention-agent)", "chargeback dispute open (risk)"],
               material: true, governing_source: "risk", why: "..."},   // or null
    checks: [{name: "authority", result: "pass", detail: "credit 2,400 within agent limit 5,000"}],   // deterministic checks
    question: {to_role: "Billing analyst", to_name: "Priya Shah",
               text: "Risk shows chargeback dispute RSK-311 open on Lumen Analytics. Hold the 2,400 USD credit until it closes?",
               options: ["Hold until dispute closes", "Issue credit anyway", "Amend amount"]},   // or null
    rule_applied: null,                  // standing rule id when one settled it
    record_id: "DR-0001",
    trace_id: "4f1c...",
    latency_ms: 2300, cost_usd: 0.009,
    judge: {fact_named: true, note: "..."}   // planted holds only
  }],
  pairs: [{pair_id: "CF-01", base: "PL-01", variant: "CF-01", change: "source order swapped", same: true}],
  rulings: [{record_id: "DR-0003", case_id: "PL-03", ruled_by: "Priya Shah", role: "Billing analyst",
             ruling: "reject", reason_code: "duplicate_compensation",
             standing_rule: {id: "SR-01", pattern: {action_type: "service_credit", fact: "billing.prior_credit_same_incident"},
                             effect: "hold", owner: "Priya Shah", expires: "2026-12-01"},
             scripted: true}],             // the ruling is scripted for the demo; the replay is real
  traces: {"4f1c...": [{name: "gate.run", start_ms: 0, dur_ms: 2300, attrs: {}, parent: null},
                       {name: "mcp.tool risk_account_flags", start_ms: 12, dur_ms: 3, attrs: {}, parent: "gate.run"}]},
  failures: ["PL-09: ..."]              // what the run got wrong, written by the runner
}
```
