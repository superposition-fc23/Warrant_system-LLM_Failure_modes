"""Load the stored plain-rules, v3 and v4 mutation runs into a running Phoenix as one dataset and three experiments. No model calls.

    .venv/bin/python v5/push_phoenix.py [http://localhost:6006]

The dataset is split by tier (a proxy: which version first catches a case). Each stored decision becomes an experiment run with its
repetition number, its stored latency as the run's duration, a code annotation "decision correct" scored against the label the case
was built with, and its stored cost as a "cost_usd" annotation (see push_experiment.py for why cost can't be Phoenix's own column).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import load_runs as L  # noqa: E402
import pandas as pd  # noqa: E402
from phoenix.client import Client  # noqa: E402

DATASET = "warrant-mutations-224"


def main(url):
    from push_experiment import log_stored    # here, not at the top: push_experiment imports DATASET from this file
    cl = Client(base_url=url)
    if any(d["name"] == DATASET for d in cl.datasets.list()):
        sys.exit(f"{DATASET} already exists in Phoenix; delete it there first, so nothing is loaded twice")
    cases = L.load_cases()
    exp = L.load_experiments()
    tier_of = L.tiers(cases, exp)
    rows = [{"case_id": c["case_id"], "mutation": c["mutation"], "base": c["base"], "unsafe": c["unsafe"], "expected": c["expected"], "tier": tier_of[c["case_id"]]} for c in cases]
    ds = cl.datasets.create_dataset(name=DATASET, dataframe=pd.DataFrame(rows), input_keys=["case_id", "mutation", "base"], output_keys=["expected"],
                                    metadata_keys=["unsafe"], split_keys=["tier"],
                                    dataset_description="224 generated cases (120 planted defects, 104 neutrals). Tier is a proxy for which version first catches a case, not measured difficulty.")
    by_case = {e["input"]["case_id"]: e["id"] for e in ds.examples}
    for system in ("rules", "v3", "v4"):
        runs = exp[system]
        e = cl.experiments.create(dataset_id=ds.id, experiment_name=f"{system}-stored", repetitions=max(r["run"] for r in runs),
                                  experiment_description="Stored decisions loaded as is, nothing rerun.",
                                  experiment_metadata={"system": system, "source": L.STORED.get(system, "cheap_rules in mutation_eval.py")})
        log_stored(cl, e["id"], by_case, runs)
        print(system, len(runs), "runs loaded")
    print("done:", url)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "http://localhost:6006")
