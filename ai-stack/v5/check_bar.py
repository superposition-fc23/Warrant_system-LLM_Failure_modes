"""Score an open-model mutation run against the bar written before it ran.

    .venv/bin/python v5/check_bar.py runs/<run folder> v5/bars/<bar>.json
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import load_runs as L  # noqa: E402


def unreadable(r):
    return (r.get("belief") or {}).get("vetoed_by") == "unreadable reply"


def parses(a):
    try:
        json.loads(a)
        return True
    except Exception:
        return False


def main(folder, bar_path):
    bar = json.load(open(bar_path))["bar"]
    rows = [json.loads(l) for n in sorted(os.listdir(folder)) if n.startswith("decisions-") for l in open(os.path.join(folder, n))]
    errors = [r for r in rows if "error" in r]
    rows = [r for r in rows if "error" not in r]
    tiers = L.tiers(L.load_cases(), L.load_experiments())
    un, cl = [r for r in rows if r["unsafe"]], [r for r in rows if not r["unsafe"]]
    called = [r for r in rows if r.get("calls")]
    acted = [r for r in un if r["decision"] == "act"]
    by_tier = {}
    for r in un:
        t = by_tier.setdefault(tiers[r["case_id"]], {"defects": 0, "acted": 0, "stopped_unreadable": 0})
        t["defects"] += 1
        t["acted"] += r["decision"] == "act"
        t["stopped_unreadable"] += r["decision"] != "act" and unreadable(r)
    lat = sorted(r["latency_ms"] for r in rows)
    answers = [a for r in rows for a in r.get("answers") or []]
    out = {
        "decisions": len(rows), "errors": len(errors),
        "defects": len(un), "defects_acted": len(acted), "acted_cases": sorted(r["case_id"] for r in acted),
        "runs": sorted({r["run"] for r in rows}),
        "neutrals": len(cl), "neutrals_stopped_worst_run": max((sum(r["decision"] != "act" for r in cl if r["run"] == k) for k in {r["run"] for r in rows}), default=0),
        "model_called": len(called), "unreadable_decisions": sum(unreadable(r) for r in called),
        "unreadable_share": round(sum(unreadable(r) for r in called) / max(len(called), 1), 3),
        "answers": len(answers), "answers_unparseable": sum(not parses(a) for a in answers),
        "by_tier": by_tier,
        "p50_ms": lat[len(lat) // 2] if lat else None, "p95_ms": lat[int(len(lat) * 0.95)] if lat else None,
        "cost_per_decision": round(sum(r.get("cost_usd", 0) for r in rows) / max(len(rows), 1), 5),
        "cost_total": round(sum(r.get("cost_usd", 0) for r in rows), 4),
        "guard": [json.load(open(os.path.join(folder, n))) for n in sorted(os.listdir(folder)) if n.startswith("guard-")],
    }
    checks = {"defects_acted": out["defects_acted"] <= bar["defects_acted_max"],
              "unreadable_share": out["unreadable_share"] <= bar["unreadable_share_max"],
              "neutrals_stopped": out["neutrals_stopped_worst_run"] <= bar["neutrals_stopped_max"],
              "complete": len(rows) == 224 * len(out["runs"]) and not errors}
    out["bar"] = {k: "pass" if v else "FAIL" for k, v in checks.items()}
    out["verdict"] = "pass" if all(checks.values()) else "fail"
    json.dump(out, open(os.path.join(folder, "bar_result.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
