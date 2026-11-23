"""Run fixture cases through the real gate on a Together model, traced to Phoenix. Each run is its own labelled folder; never mixed with Claude runs.

    WARRANT_OTLP_ENDPOINT=http://localhost:6006/v1/traces .venv/bin/python v5/live_run.py <together model id> <case ids, comma-separated | all> [label]

The model is registered as "together-gate" with TOGETHER_GATE_API_KEY. v4's priors are unchanged. Writes runs/v4-open-<label>-<time>/ with
decisions.jsonl, traces.jsonl and summary.json (the call guard's totals included). Budget: WARRANT_RUN_MAX_USD (default here 0.50).
"""
import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime, timezone

AI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(AI)
sys.path.insert(0, AI)
os.environ.setdefault("WARRANT_RUN_MAX_USD", "0.50")

import callguard  # noqa: E402
import llm  # noqa: E402
import telemetry  # noqa: E402


def _parses(text):
    try:
        json.loads(text)
        return True
    except Exception:
        return False


def main(model_id, which, label):
    d = json.load(open("evals/crm_cases.json"))
    cases = [c for c in d["cases"] if c["kind"] in ("control", "planted", "injection")]
    if which != "all":
        ids = which.split(",")
        cases = [c for c in cases if c["id"] in ids]
    tag = re.sub(r"[^a-z0-9.]+", "-", label.lower())
    run_id = f"v4-open-{tag}-{datetime.now(timezone.utc):%Y%m%dT%H%M}"
    out = os.path.join("runs", run_id)
    os.makedirs(out)
    telemetry.setup(os.path.join(out, "traces.jsonl"), project=f"warrant-v4-open-{tag}")
    effort = llm._effort(os.getenv("TOGETHER_GATE_REASONING", "off"))
    llm.register_together("together-gate", model_id, "TOGETHER_GATE_API_KEY", reasoning=effort)
    llm.cost_of("together-gate")    # fail before any call if the price can't be found, so the budget works
    import warrant
    warrant.COMPARE_MODEL = "together-gate"
    warrant.RULES_PATH, warrant.LEDGER_PATH = os.path.join(out, "rules.json"), os.path.join(out, "ledger.jsonl")
    rows, t0 = [], time.time()
    with open(os.path.join(out, "decisions.jsonl"), "w") as f:
        for c in cases:
            try:
                rec = asyncio.run(warrant.run(c, d["now"], d["people"], d["authority"]))
            except callguard.GuardError as e:
                print(f"stopped at {c['id']}: {e}")
                break
            answers = (rec.get("usage") or {}).get("answers") or []
            parse_failures = sum(1 for a in answers if not _parses(a))
            row = {"case_id": c["id"], "kind": c["kind"], "expected": c["expected"], "decision": rec["decision"], "pass": rec["decision"] == c["expected"],
                   "parse_failures": parse_failures, "samples": len(answers), "latency_ms": rec["latency_ms"], "cost_usd": (rec.get("usage") or {}).get("cost_usd", 0.0),
                   "trace_id": rec["trace_id"], "served_model": (rec.get("usage") or {}).get("served_model")}
            f.write(json.dumps({**rec, "v5": row}) + "\n")
            rows.append(row)
            print(f"{c['id']:6} expected {c['expected']:6} got {rec['decision']:6} {rec['latency_ms']:>6} ms  parse fails {parse_failures}/{len(answers)}", flush=True)
    lat = sorted(r["latency_ms"] for r in rows) or [0]
    summary = {"run_id": run_id, "model": model_id, "cases": len(rows), "passed": sum(r["pass"] for r in rows),
               "parse_failures": sum(r["parse_failures"] for r in rows), "samples": sum(r["samples"] for r in rows),
               "p50_ms": lat[len(lat) // 2], "p95_ms": lat[min(len(lat) - 1, int(len(lat) * 0.95))],
               "cost_usd": round(sum(r["cost_usd"] for r in rows), 4), "wall_s": round(time.time() - t0, 1),
               "call_guard": callguard.GUARD.summary(), "priors": "v4, unchanged"}
    json.dump({"summary": summary, "decisions": rows}, open(os.path.join(out, "summary.json"), "w"), indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else sys.argv[1].split("/")[-1])
