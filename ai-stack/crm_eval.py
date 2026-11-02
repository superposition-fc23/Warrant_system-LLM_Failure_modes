"""Run every case in evals/crm_cases.json through Warrant and score it. One run = one folder in runs/, committed.

    planted and control cases -> pairs (R7) -> scripted ruling on PL-03 becomes standing rule SR-01 -> replay RP-01 (R6)
    -> LLM-as-judge on named facts -> summary, failures, prototype-data.js

Pass: planted cases match the expected decision; controls act; each pair gets its base case's decision; the replay is
settled by the rule with no person. The ruling is scripted (no human in the loop yet); the replay is real.

    .venv/bin/python crm_eval.py v2
"""
import asyncio
import json
import os
import re
import shutil
import statistics
import sys
from datetime import datetime, timezone

import llm
import telemetry
import warrant

JUDGE_SYSTEM = "You grade whether a gate named the right fact when it held a money action. Return only JSON."
JUDGE = """Expected discriminating fact: {expected}
What the gate said: discriminating fact: {named}. Failed checks: {checks}. Material conflict: {conflict}.
Does the gate name the expected fact (same record and same substance; wording may differ)?
Return JSON: fact_named (true|false), note (one sentence)."""


def judge(case, rec):
    failed = [f"{c['name']}: {c['detail']}" for c in rec["checks"] if c["result"] != "pass"]
    out = llm.ask("haiku-5.5", JUDGE.format(expected=case["discriminating_fact"], named=rec["discriminating_fact"],
                                            checks=failed, conflict=rec["conflict"]), system=JUDGE_SYSTEM, max_tokens=800, effort="low")
    try:
        return json.loads(re.search(r"\{.*\}", out, re.S).group())
    except Exception:
        return {"fact_named": False, "note": f"judge output unparsable: {out[:120]}"}


def audit_summary():
    if not os.path.exists("evals/crm_audit.json"):
        return None
    rows = json.load(open("evals/crm_audit.json"))
    ctl = [r for r in rows if r["id"].startswith("CT")]
    return {"controls_clean": sum(r["verdict"] == "clean" for r in ctl), "controls": len(ctl),
            "planted_with_incidental_defects": sum(r["verdict"] != "clean" for r in rows if r["id"].startswith("PL"))}


def describe(source, r):
    if source == "crm":
        return f"{r['name']}, {r['tier']}, {r['entitlements']['seats']} seats entitled"
    if source == "billing":
        s = f"{r['seats_billed']} seats billed, {r['monthly_fee']} {r['currency']}/month, " + ", ".join(f"{i['id']} {i['status']}" for i in r["invoices"])
        return s + ("; credits " + ", ".join(f"{c['id']} {c['amount']} for {c['incident_id']}" for c in r["credits"]) if r["credits"] else "")
    if source == "contracts":
        return "; ".join(f"{d['id']} {d['kind']} {d['status']}" for d in r["documents"])
    return "; ".join(f"{f['id']} {f['type']} {f['status']}" for f in r["flags"]) or "no flags"


def to_ui(case, rec):
    p, crm = rec["action"], case["world"]["crm"]
    beliefs = [{**x, "value": describe(x["source"], x["value"]) if isinstance(x["value"], dict) else x["value"]} for x in rec["beliefs"]]
    return {"case_id": case["id"], "kind": case["kind"], "pain": case.get("pain"), "title": case["title"], "expected": case["expected"],
            "decision": rec["decision"], "pass": None,
            "action": {"type": p["type"], "account_id": p["account_id"], "account": crm["name"], "tier": crm["tier"], "amount": p.get("amount"),
                       "currency": p.get("currency"), "pct": p.get("pct"), "seats": p.get("seats"), "agent": p["agent"], "summary": warrant.summary(p)},
            "beliefs": beliefs, "conflict": rec["conflict"], "checks": rec["checks"], "question": rec["question"],
            "rule_applied": rec["rule_applied"], "record_id": rec["record_id"], "trace_id": rec["trace_id"],
            "latency_ms": rec["latency_ms"], "cost_usd": round(rec["usage"].get("cost_usd", 0), 5), "fact_from": rec.get("fact_from"),
            "escalated": rec["usage"].get("escalated"), "triggers": rec["usage"].get("triggers"), "compare_skipped": rec.get("compare_skipped"),
            "discriminating_fact": rec["discriminating_fact"], "judge": None}


async def main(version):
    d = json.load(open("evals/crm_cases.json"))
    started = datetime.now(timezone.utc)
    run_id = f"{version}-{started:%Y%m%dT%H%M}"
    out = f"runs/{run_id}"
    os.makedirs(out, exist_ok=True)
    telemetry.setup(f"{out}/traces.jsonl")
    warrant.RULES_PATH = f"{out}/rules.json"      # each run starts with no standing rules; the file is the run's rule state
    cases = {c["id"]: c for c in d["cases"]}
    order = [c for c in d["cases"] if c["kind"] in ("control", "planted")] + [c for c in d["cases"] if c["kind"] == "pair"]
    recs, ui = {}, {}
    for c in order:
        rec = await warrant.run(c, d["now"], d["people"], d["authority"])
        recs[c["id"]], ui[c["id"]] = rec, to_ui(c, rec)
        print(f"{c['id']:6} expected {c['expected']:6} got {rec['decision']:6} {rec['latency_ms']:>6} ms", flush=True)

    # Loop 2: a scripted ruling on PL-03 becomes a standing rule; then the replay case is run for real.
    ruling = {"record_id": recs["PL-03"]["record_id"], "case_id": "PL-03", "ruled_by": "Priya Shah", "role": "Billing analyst",
              "ruling": "reject", "reason_code": "duplicate_compensation",
              "standing_rule": {"id": "SR-01", "pattern": {"action_type": "service_credit", "check": "prior_compensation"},
                                "effect": "hold", "owner": "Priya Shah", "expires": "2026-12-01"}, "scripted": True}
    warrant.save_rule(ruling["standing_rule"])
    rp = cases["RP-01"]
    rec = await warrant.run(rp, d["now"], d["people"], d["authority"])
    recs["RP-01"], ui["RP-01"] = rec, to_ui(rp, rec)
    print(f"RP-01  expected hold by SR-01, got {rec['decision']} rule {rec['rule_applied']}", flush=True)
    # R6: the rule must stop applying after it expires.
    expiry_ok = bool(warrant.active_rules(d["now"])) and not warrant.active_rules("2026-12-02T09:00:00Z")

    failures = []
    for cid, u in ui.items():
        c = cases[cid]
        if c["kind"] == "pair":
            u["pass"] = u["decision"] == ui[c["base"]]["decision"]
        elif c["kind"] == "replay":
            u["pass"] = u["decision"] == "hold" and u["rule_applied"] == "SR-01" and not u["question"]
        else:
            u["pass"] = u["decision"] == c["expected"]
        if c["kind"] in ("planted", "replay") and u["decision"] != "act":
            u["judge"] = judge(c, recs[cid])
        if not u["pass"]:
            why = (f"flipped from {ui[c['base']]['decision']} to {u['decision']} when {c['change']}" if c["kind"] == "pair"
                   else f"expected {c['expected']}, got {u['decision']}")
            failures.append(f"{cid} {c['title']}: {why}")
        elif u["judge"] and not u["judge"].get("fact_named"):
            failures.append(f"{cid} {c['title']}: right decision, wrong fact named ({u['judge'].get('note')})")
    pairs = [{"pair_id": cid, "base": cases[cid]["base"], "variant": cid, "change": cases[cid]["change"],
              "base_decision": ui[cases[cid]["base"]]["decision"], "variant_decision": ui[cid]["decision"], "same": ui[cid]["pass"]}
             for cid in ui if cases[cid]["kind"] == "pair"]
    lat = sorted(r["latency_ms"] for r in recs.values())
    planted = [ui[c] for c in ui if cases[c]["kind"] == "planted"]
    controls = [ui[c] for c in ui if cases[c]["kind"] == "control"]
    cost = sum(r["usage"].get("cost_usd", 0) for r in recs.values())
    summ = {"cases": len(ui), "planted": len(planted), "controls": len(controls), "pairs": len(pairs),
            "held_planted": sum(u["decision"] != "act" for u in planted),
            "expected_planted": sum(u["pass"] for u in planted),
            "fact_named": sum(bool(u["judge"] and u["judge"].get("fact_named")) for u in planted),
            "over_held": sum(u["decision"] != "act" for u in controls),
            "pairs_invariant": sum(p["same"] for p in pairs), "pairs_flipped": sum(not p["same"] for p in pairs),
            "replay_settled_by_rule": ui["RP-01"]["pass"], "rule_expiry_enforced": expiry_ok,
            "model_skipped": sum(1 for r in recs.values() if r.get("compare_skipped")),
            "escalated": sum(1 for r in recs.values() if r["usage"].get("escalated")),
            "first_pass_only": sum(1 for r in recs.values() if r["usage"].get("stages") and not r["usage"].get("escalated")),
            "fact_from_code": sum(1 for r in recs.values() if r.get("fact_from") == "code"),
            "eval_audit": audit_summary(),
            "p50_ms": statistics.median(lat), "p95_ms": lat[int(0.95 * (len(lat) - 1))],
            "cost_usd_total": round(cost, 4), "cost_usd_per_decision": round(cost / len(recs), 5),
            "tokens_in": sum(r["usage"].get("tokens_in", 0) for r in recs.values()),
            "tokens_out": sum(r["usage"].get("tokens_out", 0) for r in recs.values()),
            "models": {"first_pass": warrant.FIRST_PASS, "escalation": warrant.ESCALATE, "judge": "haiku-5.5"}}

    with open(f"{out}/decisions.jsonl", "w") as f:
        for r in recs.values():
            f.write(json.dumps(r) + "\n")
    traces = telemetry.load(f"{out}/traces.jsonl")
    run = {"run_id": run_id, "version": version, "started_at": started.isoformat(timespec="seconds"), "now": d["now"],
           "summary": summ, "decisions": list(ui.values()), "pairs": pairs, "rulings": [ruling], "traces": traces, "failures": failures}
    json.dump({k: run[k] for k in ("run_id", "version", "started_at", "summary", "pairs", "failures")}, open(f"{out}/summary.json", "w"), indent=1)
    open(f"{out}/prototype-data.js", "w").write("window.RUN = " + json.dumps(run, indent=1) + ";\n")
    shutil.rmtree("runs/latest", ignore_errors=True)
    shutil.copytree(out, "runs/latest")
    print(json.dumps(summ, indent=1))
    print("\nFailures:\n" + "\n".join(f"- {x}" for x in failures))


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "v1"))
