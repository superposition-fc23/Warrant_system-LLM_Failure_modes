"""Attach judge scores to the matching experiment runs in Phoenix as LLM annotations, one name per judge. No model calls.

    .venv/bin/python v5/push_judgements.py <experiment name>=<run folder> ...
"""
import json
import os
import sys

from phoenix.client import Client

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from push_phoenix import DATASET  # noqa: E402

AI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(pairs, url="http://localhost:6006"):
    cl = Client(base_url=url)
    ds = next(d for d in cl.datasets.list() if d["name"] == DATASET)
    case_of = {e["id"]: e["input"]["case_id"] for e in cl.datasets.get_dataset(dataset=ds["id"]).examples}
    exps = {e["name"]: e for e in cl.experiments.list(dataset_id=ds["id"])}
    for pair in pairs:
        name, folder = pair.split("=")
        runs = cl.experiments.get_experiment(experiment_id=exps[name]["id"])["task_runs"]
        rid = {(case_of[r["dataset_example_id"]], r["repetition_number"]): r["id"] for r in runs}
        n = 0
        for j in map(json.loads, open(os.path.join(AI, "runs", folder, "judgements.jsonl"))):
            if not j["parsed"] or (j["case_id"], j["run"]) not in rid:
                continue
            cl.experiments.log_evaluation(experiment_run_id=rid[(j["case_id"], j["run"])], name=f"fact_named.{j['judge']}", annotator_kind="LLM",
                                          score=float(j["score"]), label=str(j["score"]), explanation=j["note"], metadata={"model": j.get("model")})
            n += 1
        print(name, n, "judge annotations")


if __name__ == "__main__":
    main(sys.argv[1:])
