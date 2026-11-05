"""Turn one recorded live run into the data behind the Live demo tab's replay. No model calls, no live systems.

    .venv/bin/python make_replay.py runs/v4-agent-20261103T0504
"""
import json
import os
import sys

import belief
import crm_mcp
import slack_card


def next_clean(rows):
    """What a kept hold on the lag card would do to the next clean credit. Calculated from the recorded facts with belief.py, because no recorded run has that click."""
    records = [x["record"] for row in rows for x in row["records"]]
    clean = next(r for r in records if r["decision"] == "act")
    lag = next(r for r in records if r["decision"] == "gather")
    src = lag["belief"]["top_doubt_source"]
    table = json.loads(json.dumps(belief.PRIORS["sources"]))
    before = belief.reliability(src, table)
    table[src]["beta"] += 1
    after = belief.reliability(src, table)
    facts = dict(clean["belief"]["facts"])
    facts["no_prior_compensation"] *= after / before
    return {"source": src, "reliability_before": round(before, 4), "reliability_after": round(after, 4), "p_safe_before": clean["belief"]["p_safe"], "p_safe_after": round(belief.p_safe(facts), 4)}


def flow(rec, traces):
    """The recorded steps behind one decision, read from the run's trace: the agent's call before the gate, the gate's spans, the agent's reply after it."""
    ms = lambda span: round((span["end_ns"] - span["start_ns"]) / 1e6)
    at = next(i for i, t in enumerate(traces) if t[0]["trace_id"] == rec["trace_id"])
    gate = {}
    for span in traces[at]:
        gate.setdefault(span["name"], []).append(span)
    samples = gate.get("llm.compare", [])
    steps = [{"step": "Agent proposes the credit", "detail": traces[at - 1][0]["attrs"]["gen_ai.request.model"], "ms": ms(traces[at - 1][0])},
             {"step": "Read 5 sources", "detail": "HubSpot, Chargebee test site, contracts, risk, authority", "ms": ms(gate["gate.read_sources"][0])},
             {"step": "Freshness, checks, rules", "detail": "code", "ms": sum(ms(gate[n][0]) for n in ("gate.freshness", "gate.checks", "gate.rules"))},
             {"step": "Compare", "detail": f"{len(samples)} sample{'s' if len(samples) != 1 else ''}, {samples[0]['attrs']['gen_ai.request.model']}", "ms": ms(gate["gate.compare"][0])} if samples else {"step": "Compare skipped", "detail": rec["compare_skipped"], "ms": None},
             {"step": "Decide: " + rec["decision"], "detail": "code", "ms": ms(gate["gate.decide"][0])}]
    if "gate.commit" in gate:
        steps.append({"step": "Re-read, then commit", "detail": "credit written to Chargebee test site", "ms": ms(gate["gate.reread"][0])})
    else:
        steps.append({"step": "Card posted to Slack", "detail": "waits for a person", "ms": None})
    steps.append({"step": "Agent replies to the customer", "detail": traces[at + 1][0]["attrs"]["gen_ai.request.model"], "ms": ms(traces[at + 1][0])})
    return steps


def build(folder):
    d = json.load(open("evals/crm_cases.json"))
    crm_mcp.load({}, d["people"], d["authority"])
    rows = [json.loads(l) for l in open(f"{folder}/tickets.jsonl")]
    rulings = {r["record_id"]: r for r in map(json.loads, open(f"{folder}/rulings.jsonl"))}
    spans = {}
    for span in map(json.loads, open(f"{folder}/traces.jsonl")):
        spans.setdefault(span["trace_id"], []).append(span)
    traces = sorted(spans.values(), key=lambda t: min(x["start_ns"] for x in t))
    steps = []
    for row in rows:
        for x in row["records"]:
            rec, b = x["record"], x["record"]["belief"]
            r = rulings.get(rec["record_id"], {})
            card = None
            if rec["decision"] != "act":
                rec.setdefault("trace_id", "replay")
                card = [slack_card.re_text(block) for block in slack_card.card(rec) if block["type"] != "actions"]
            steps.append({"ticket": row["ticket"], "agent": row["agent"], "account": rec["action"]["account_id"], "amount": rec["action"]["amount"], "decision": rec["decision"], "status": x["tool_result"]["status"],
                          "p_safe": b.get("p_safe"), "vetoed_by": b.get("vetoed_by"), "wait_seconds": b.get("wait_seconds"), "fact": rec["discriminating_fact"], "card": card, "credit_id": x["tool_result"].get("credit_id"), "flow": flow(rec, traces),
                          "reply": row["reply"][:400], "ruling": r.get("ruling"), "seconds_to_ruling": r.get("seconds_to_ruling"), "ruling_credit": r.get("credit_id"), "belief_update": r.get("belief_update")})
    return {"run": os.path.basename(folder.rstrip("/")), "steps": steps, "next_clean": next_clean(rows)}


if __name__ == "__main__":
    out = "runs/replay/replay-data.js"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        f.write("window.WARRANT_REPLAY = " + json.dumps(build(sys.argv[1]), indent=1) + ";\n")
    print("wrote", out)
