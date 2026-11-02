"""Run the demo cases against the live HubSpot and Chargebee test accounts. Contracts, risk and authority stay local fixtures.

Fixture timestamps are shifted to today so only live systems can move the result. Writes runs/<version>-live-<time>/.

    .venv/bin/python live_demo.py v3
"""
import asyncio
import json
import os
import statistics
import sys
from datetime import datetime, timezone

import crm_mcp
import seed_live
import telemetry
import warrant


def shift(world, ref, now):
    """Move fixture timestamps forward by the time since the case set's reference clock."""
    delta = now - warrant.ts(ref)
    out = json.loads(json.dumps(world))
    for system in ("contracts", "risk"):
        for key in ("updated_at", "synced_at"):
            if key in out[system]:
                out[system][key] = (warrant.ts(out[system][key]) + delta).strftime("%Y-%m-%dT%H:%M:%SZ")
    return out


async def main(version):
    d = json.load(open("evals/crm_cases.json"))
    cases = {c["id"]: c for c in d["cases"]}
    now = datetime.now(timezone.utc)
    out = f"runs/{version}-live-{now:%Y%m%dT%H%M}"
    os.makedirs(out, exist_ok=True)
    telemetry.setup(f"{out}/traces.jsonl")
    warrant.RULES_PATH = f"{out}/rules.json"
    crm_mcp.LIVE = True
    rows = []
    for cid in seed_live.DEMO:
        c = {**cases[cid], "world": shift(cases[cid]["world"], d["now"], now)}
        c["proposal"] = {**c["proposal"], "asserted": [{**a, "observed_at": (warrant.ts(a["observed_at"]) + (now - warrant.ts(d["now"]))).strftime("%Y-%m-%dT%H:%M:%SZ")}
                                                       for a in c["proposal"]["asserted"]]}
        rec = await warrant.run(c, now.strftime("%Y-%m-%dT%H:%M:%SZ"), d["people"], d["authority"])
        ok = rec["decision"] == c["expected"]
        rows.append({**rec, "expected": c["expected"], "pass": ok})
        print(f"{cid:6} expected {c['expected']:6} got {rec['decision']:6} {rec['latency_ms']:>6} ms  {rec['discriminating_fact'] or ''}"[:170], flush=True)
    lat = [r["latency_ms"] for r in rows]
    span = [json.loads(l) for l in open(f"{out}/traces.jsonl")]
    reads = sorted((x["end_ns"] - x["start_ns"]) / 1e6 for x in span if x["name"].startswith("mcp.tool") and x["attrs"].get("account_id"))
    summ = {"cases": len(rows), "passed": sum(r["pass"] for r in rows), "p50_ms": statistics.median(lat), "max_ms": max(lat),
            "read_p50_ms": statistics.median(reads) if reads else None, "read_max_ms": max(reads) if reads else None,
            "sources": {"crm": "HubSpot test account, live", "billing": "Chargebee test site, live", "contracts": "local fixture", "risk": "local fixture", "authority": "local config"}}
    with open(f"{out}/decisions.jsonl", "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    json.dump(summ, open(f"{out}/summary.json", "w"), indent=1)
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "v3"))
