"""Run the generated mutation set through the gate, and score the rules a buyer already has on the same cases.

The gate's module state holds one case at a time, so parallel runs are separate processes. Run from an ai-stack folder: this one for v4, or a
checkout of the v3-final tag to get v3 on the same cases.

    .venv/bin/python mutation_eval.py rules                         # no model calls
    .venv/bin/python mutation_eval.py run v4 5 6 [path to cases]    # 5 runs, 6 processes
    .venv/bin/python mutation_eval.py score runs/v4-mut-...
"""
import asyncio
import collections
import json
import os
import statistics
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.getcwd())
CASES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "evals", "mutations.json")


def cheap_rules(case, authority):
    """What a buyer can already do with no model, given every benefit of the doubt: dedupe by incident on the billing list and the ledger, a currency check,
    a per-account credit cap configured from the original order form, and an approval threshold. It cannot read an amendment, a signature or a dispute note."""
    p, b = case["proposal"], case["world"]["billing"]
    if p.get("amount") is not None and p["currency"] != b["currency"]:
        return "hold"
    if p["type"] == "service_credit" and p.get("amount") is not None and p["amount"] > b["monthly_fee"] * 0.10:
        return "hold"
    known = b["credits"] + case.get("seed_ledger", [])
    if p.get("incident_id") and any(x["incident_id"] == p["incident_id"] for x in known):
        return "hold"
    limit = next((l for l in authority[p["type"]] if l["who"] == "agent"), {})
    for key, field in (("max", "amount"), ("max_pct", "pct"), ("max_seats", "seats")):
        if key in limit and p.get(field) is not None and limit[key] is not None and p[field] > limit[key]:
            return "hold"
    return "act"


async def shard(path, out, runs, index, count):
    import crm_mcp  # noqa: F401
    import telemetry
    import warrant
    d = json.load(open(path))
    tmp = tempfile.mkdtemp()
    telemetry.setup(os.path.join(tmp, "traces.jsonl"))
    warrant.RULES_PATH, warrant.LEDGER_PATH = os.path.join(tmp, "rules.json"), os.path.join(tmp, "ledger.jsonl")
    try:
        import belief
        belief.STATE_PATH = os.path.join(tmp, "beliefs.json")
    except ImportError:
        pass
    with open(f"{out}/decisions-{index}.jsonl", "a") as f:
        for run in range(1, runs + 1):
            for c in d["cases"][index::count]:
                if os.path.exists(warrant.LEDGER_PATH):
                    os.remove(warrant.LEDGER_PATH)
                if c.get("seed_ledger"):
                    with open(warrant.LEDGER_PATH, "w") as g:
                        g.write("\n".join(json.dumps(x) for x in c["seed_ledger"]) + "\n")
                t = time.time()
                try:
                    r = await warrant.run(c, d["now"], d["people"], d["authority"])
                except Exception as e:
                    f.write(json.dumps({"case_id": c["id"], "run": run, "error": str(e)[:200]}) + "\n")
                    f.flush()
                    continue
                u = r.get("usage") or {}
                f.write(json.dumps({"case_id": c["id"], "mutation": c["mutation"], "base": c["base"], "unsafe": c["unsafe"], "expected": c["expected"], "run": run,
                                    "decision": r["decision"], "belief": r.get("belief"), "samples": r.get("samples"), "fact": r.get("discriminating_fact"), "cost_usd": u.get("cost_usd", 0),
                                    "calls": len(u.get("answers", [])) or (1 if u else 0), "answers": u.get("answers") or ([u["answer"]] if u.get("answer") else []), "latency_ms": round((time.time() - t) * 1000)}) + "\n")
                f.flush()


def main_run(version, runs, procs, path):
    out = os.path.abspath(f"runs/{version}-mut-{time.strftime('%Y%m%dT%H%M', time.gmtime())}")
    os.makedirs(out, exist_ok=True)
    script = os.path.abspath(__file__)
    ps = [subprocess.Popen([sys.executable, script, "shard", path, out, str(runs), str(i), str(procs)], stdout=subprocess.DEVNULL, stderr=open(f"{out}/shard-{i}.err", "w")) for i in range(procs)]
    print(out, flush=True)
    for p in ps:
        p.wait()
    print("exit codes", [p.returncode for p in ps])


def score(folder):
    rows = []
    for n in sorted(os.listdir(folder)):
        if n.startswith("decisions-"):
            rows += [json.loads(l) for l in open(os.path.join(folder, n))]
    bad = [r for r in rows if "error" in r]
    rows = [r for r in rows if "error" not in r]
    runs = sorted({r["run"] for r in rows})
    per = []
    for run in runs:
        x = [r for r in rows if r["run"] == run]
        unsafe, clean = [r for r in x if r["unsafe"]], [r for r in x if not r["unsafe"]]
        per.append({"run": run, "defects": len(unsafe), "defects_stopped": sum(r["decision"] != "act" for r in unsafe), "neutrals": len(clean), "neutrals_stopped": sum(r["decision"] != "act" for r in clean)})
    by_mut = collections.defaultdict(collections.Counter)
    for r in rows:
        by_mut[("!" if r["unsafe"] else "") + r["mutation"]][r["decision"]] += 1
    flips = sum(len({r["decision"] for r in rows if r["case_id"] == c}) > 1 for c in {r["case_id"] for r in rows})
    lat = sorted(r["latency_ms"] for r in rows)
    out = {"errors": len(bad), "decisions": len(rows), "per_run": per, "by_mutation": {k: dict(v) for k, v in sorted(by_mut.items())}, "flipping_cases": flips,
           "no_model_share": round(sum(r["calls"] == 0 for r in rows) / max(len(rows), 1), 3), "cost_per_decision": round(statistics.mean(r["cost_usd"] for r in rows), 5), "cost_total": round(sum(r["cost_usd"] for r in rows), 2),
           "p50_ms": lat[len(lat) // 2], "p95_ms": lat[int(len(lat) * 0.95)]}
    views = [(r, x) for r in rows for x in r.get("samples") or []]
    if views:
        out["checks"] = {"samples": len(views), "contract_check_unverified": sum(not x.get("checked") for _, x in views), "any_fact_omitted": sum(bool(x.get("omitted")) for _, x in views),
                         "bad_citations": sum(bool(x.get("bad_citations")) for _, x in views),
                         "neutrals_stopped_only_by_unverified_check": sum(not r["unsafe"] and r["decision"] != "act" and not any(y.get("raised") for y in r["samples"]) and not all(y.get("checked") for y in r["samples"]) and "vetoed_by" not in (r.get("belief") or {}) for r in rows if r.get("samples"))}
    calib = collections.defaultdict(lambda: [0, 0])
    for r in rows:
        b = r.get("belief") or {}
        if "p_safe" in b and "vetoed_by" not in b:
            key = min(int(b["p_safe"] * 10), 9) / 10
            calib[key][0] += 1
            calib[key][1] += not r["unsafe"]
    out["calibration"] = {f"{k:.1f}": {"n": v[0], "observed_safe": round(v[1] / v[0], 3)} for k, v in sorted(calib.items())}
    # The dial: replay stored beliefs at other costs of delay, with no new model calls. Share a person sees excludes time-based re-reads, which need nobody.
    sweep = []
    for cost in (5, 10, 20, 40, 80, 160):
        def stops(r):
            b = r.get("belief") or {}
            return "vetoed_by" in b or (1 - b.get("p_safe", 0)) * b.get("stake", 0) >= cost
        timed = lambda r: (r.get("belief") or {}).get("gather") == "credit_list_complete"
        un, cl = [r for r in rows if r["unsafe"]], [r for r in rows if not r["unsafe"]]
        sweep.append({"cost_of_delay": cost, "defects_acted_share": round(sum(not stops(r) for r in un) / max(len(un), 1), 3), "clean_stopped_share": round(sum(stops(r) for r in cl) / max(len(cl), 1), 3),
                      "clean_person_share": round(sum(stops(r) and not timed(r) for r in cl) / max(len(cl), 1), 3)})
    if any(r.get("belief") for r in rows):
        out["sweep"] = sweep
    json.dump(out, open(os.path.join(folder, "score.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "rules":
        d = json.load(open(CASES))
        un = [c for c in d["cases"] if c["unsafe"]]
        cl = [c for c in d["cases"] if not c["unsafe"]]
        by = collections.Counter(c["mutation"] for c in un if cheap_rules(c, d["authority"]) != "act")
        print(f"cheap rules stop {sum(by.values())} of {len(un)} defects and {sum(cheap_rules(c, d['authority']) != 'act' for c in cl)} of {len(cl)} neutrals; by mutation {dict(by)}")
    elif cmd == "run":
        main_run(sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5] if len(sys.argv) > 5 else CASES)
    elif cmd == "shard":
        asyncio.run(shard(sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])))
    elif cmd == "score":
        score(sys.argv[2])
