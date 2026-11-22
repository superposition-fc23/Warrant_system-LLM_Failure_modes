"""Iteration 1 "done when" for the stored-span import, written before the importer: for v3 and v4, every stored span is in Phoenix under its
original trace id, each gate decision has a DECISION span whose P(safe) equals the decision record, and LLM spans carry token counts.
Run from ai-stack with Phoenix up and the import done:  .venv/bin/python v5/test_iteration1.py
"""
import collections
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import import_traces as T  # noqa: E402
from phoenix.client import Client  # noqa: E402


def main(url="http://localhost:6006"):
    cl = Client(base_url=url)
    for version, folder in T.RUNS.items():
        path = os.path.join(T.AI, "runs", folder)
        stored = [json.loads(l) for l in open(os.path.join(path, "traces.jsonl"))]
        for _ in range(30):  # Phoenix ingests asynchronously after an import
            spans = cl.spans.get_spans(project_identifier=T.project(version), limit=100000)
            if len(spans) == len(stored):
                break
            time.sleep(1)
        assert len(spans) == len(stored), (version, len(spans), len(stored))
        assert {s["context"]["trace_id"] for s in spans} == {s["trace_id"] for s in stored}
        kinds = collections.Counter(s["span_kind"] for s in spans)
        decisions = [json.loads(l) for n in ("decisions.jsonl", "decisions_repeats.jsonl") for l in open(os.path.join(path, n))]
        p = {r["trace_id"]: r["belief"]["p_safe"] for r in decisions if r.get("belief")}  # v3 has no belief layer
        dspans = [s for s in spans if s["span_kind"] == "DECISION"]
        assert len(dspans) == len(decisions) == 176, (len(dspans), len(decisions))
        assert all(abs(s["attributes"]["warrant.p_safe"] - p[s["context"]["trace_id"]]) < 1e-9 for s in dspans if p)
        assert not p or len(p) == 176
        llm = [s for s in spans if s["span_kind"] == "LLM"]
        assert llm and all(s["attributes"].get("llm.token_count.prompt", 0) > 0 for s in llm)
        print(version, "ok", dict(kinds))


if __name__ == "__main__":
    main()
