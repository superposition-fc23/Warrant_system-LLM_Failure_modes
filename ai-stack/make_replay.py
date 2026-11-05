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


def build(folder):
    d = json.load(open("evals/crm_cases.json"))
    crm_mcp.load({}, d["people"], d["authority"])
    rows = [json.loads(l) for l in open(f"{folder}/tickets.jsonl")]
    rulings = {r["record_id"]: r for r in map(json.loads, open(f"{folder}/rulings.jsonl"))}
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
                          "p_safe": b.get("p_safe"), "vetoed_by": b.get("vetoed_by"), "wait_seconds": b.get("wait_seconds"), "fact": rec["discriminating_fact"], "card": card, "credit_id": x["tool_result"].get("credit_id"),
                          "reply": row["reply"][:400], "ruling": r.get("ruling"), "seconds_to_ruling": r.get("seconds_to_ruling"), "ruling_credit": r.get("credit_id"), "belief_update": r.get("belief_update")})
    return {"run": os.path.basename(folder.rstrip("/")), "steps": steps, "next_clean": next_clean(rows)}


if __name__ == "__main__":
    out = "runs/replay/replay-data.js"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        f.write("window.WARRANT_REPLAY = " + json.dumps(build(sys.argv[1]), indent=1) + ";\n")
    print("wrote", out)
