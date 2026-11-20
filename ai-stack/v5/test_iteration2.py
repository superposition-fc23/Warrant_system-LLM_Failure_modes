"""Iteration 2 "done when", written before the loader: the stored v3 and v4 mutation runs, rebuilt as dataset and experiment rows,
reproduce the stored scores exactly, and the tiers match the split in the learnings (36 / 63 / 6 / 15 of 120).
Run from ai-stack:  .venv/bin/python v5/test_iteration2.py   (no model calls, no Phoenix needed)
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import load_runs as L  # noqa: E402

RUNS = os.path.join(os.path.dirname(HERE), "runs")
STORED = {"v3": "v3-mut-20261103T0429", "v4": "v4-mut-20261103T0430"}


def main():
    cases = L.load_cases()
    assert len(cases) == 224, len(cases)
    assert sum(c["unsafe"] for c in cases) == 120 and sum(not c["unsafe"] for c in cases) == 104

    exp = L.load_experiments()
    for system, folder in STORED.items():
        want = json.load(open(os.path.join(RUNS, folder, "score.json")))["per_run"]
        got = L.per_run_scores(exp[system])
        assert got == want, f"{system}: per-run scores differ\n got {got}\nwant {want}"
        assert len(exp[system]) == 1120, (system, len(exp[system]))

    rules = L.per_run_scores(exp["rules"])
    assert len(rules) == 1 and rules[0]["defects_stopped"] == 36, rules

    tiers = L.tiers(cases, exp)
    counts = {t: sum(v == t for v in tiers.values()) for t in ("rules", "v3-always", "v3-sometimes", "v3-never")}
    assert counts == {"rules": 36, "v3-always": 63, "v3-sometimes": 6, "v3-never": 15}, counts
    v4 = L.per_tier_catch(exp["v4"], tiers)
    assert all(share == 1.0 for share in v4.values()), v4
    print("iteration 2 check passed:", counts, "v4 per tier", v4)


if __name__ == "__main__":
    main()
