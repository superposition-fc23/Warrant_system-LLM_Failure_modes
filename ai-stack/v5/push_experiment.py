"""Add one stored mutation run as an experiment on the Phoenix dataset made by push_phoenix.py. No model calls.

    .venv/bin/python v5/push_experiment.py <run folder name under runs/> <experiment name> [--replace] [http://localhost:6006]

--replace deletes an experiment of the same name first (and with it any judge annotations; re-run push_judgements.py after).

Phoenix works out an experiment run's latency from its start and end times, and its cost from token counts on a linked trace priced
by Phoenix's model table. The stored runs kept a latency and a cost per decision but no token counts. So each run starts at load time
and ends latency_ms later (the duration is real, the clock time is not), and the stored cost goes on as a "cost_usd" annotation.
"""
import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import load_runs as L  # noqa: E402
from phoenix.client import Client  # noqa: E402
from push_phoenix import DATASET  # noqa: E402


def log_stored(cl, experiment_id, by_case, rows):
    """One experiment run per stored decision: real duration, decision_correct scored by code, stored cost as an annotation."""
    t0 = dt.datetime.now(dt.timezone.utc)
    for r in rows:
        correct = (r["decision"] != "act") if r["unsafe"] else (r["decision"] == "act")
        end = t0 + dt.timedelta(milliseconds=r.get("latency_ms") or 0)
        run = cl.experiments.log_run(experiment_id=experiment_id, dataset_example_id=by_case[r["case_id"]], start_time=t0, end_time=end,
                                     repetition_number=r["run"], output={k: r[k] for k in ("decision", "fact", "p_safe", "vetoed_by", "cost_usd", "latency_ms")})
        cl.experiments.log_evaluation(experiment_run_id=run["id"], name="decision_correct", annotator_kind="CODE", score=float(correct),
                                      label="correct" if correct else "wrong", explanation=f"expected {r['expected']}, got {r['decision']}")
        if r.get("cost_usd") is not None:
            cl.experiments.log_evaluation(experiment_run_id=run["id"], name="cost_usd", annotator_kind="CODE", score=float(r["cost_usd"]),
                                          explanation="stored cost of this decision in USD, all model calls included")


def main(folder, name, url, replace=False):
    cl = Client(base_url=url)
    ds = next(d for d in cl.datasets.list() if d["name"] == DATASET)
    old = [e for e in cl.experiments.list(dataset_id=ds["id"]) if e.get("name") == name]
    if old and not replace:
        sys.exit(f"experiment {name} already exists; pass --replace to load it again")
    for e in old:
        cl.experiments.delete(experiment_id=e["id"])
    ex = cl.datasets.get_dataset(dataset=ds["id"])
    by_case = {e["input"]["case_id"]: e["id"] for e in ex.examples}
    rows = [L._row(name, r) for r in L._stored_rows(folder)]
    e = cl.experiments.create(dataset_id=ds["id"], experiment_name=name, repetitions=max(r["run"] for r in rows),
                              experiment_description="Stored decisions loaded as is, nothing rerun.", experiment_metadata={"system": name, "source": folder})
    log_stored(cl, e["id"], by_case, rows)
    print(name, len(rows), "runs loaded")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--replace"]
    main(args[0], args[1], args[2] if len(args) > 2 else "http://localhost:6006", replace="--replace" in sys.argv)
