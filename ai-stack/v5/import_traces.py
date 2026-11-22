"""Import the stored v3 and v4 fixture traces (runs/*/traces.jsonl) into Phoenix, one project per version. No model calls.

    .venv/bin/python v5/import_traces.py [http://localhost:6006]

Spans keep their original trace and span ids, parents and times. Only the shape is mapped to OpenInference span kinds: the gate's step spans are CHAIN,
MCP source reads are TOOL, model calls are LLM, and gate.decide is a DECISION span carrying P(safe), expected loss, cost of delay and any veto under
Warrant's own names (warrant.*). Prompts and model replies were never stored, so the LLM spans have tokens, cost and latency but no text.
Anthropic organisation and workspace ids are dropped from the attributes.
"""
import datetime as dt
import json
import os
import sys

AI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNS = {"v3": "v3-20261102T0537", "v4": "v4-20261103T0430"}
DROP = {"anthropic.organization.id", "anthropic.workspace.id"}


def project(version):
    return f"warrant-{version}-stored"


def _iso(ns):
    return dt.datetime.fromtimestamp(ns / 1e9, dt.timezone.utc).isoformat()


def kind(name, parent_is_none):
    if name == "gate.decide":
        return "DECISION"
    if name.startswith("mcp.tool "):
        return "TOOL"
    if name == "anthropic.messages.create":
        return "LLM"
    if name == "gate.run" or name.startswith("gate.") or name in ("llm.compare", "pii.redact", "commit"):
        return "CHAIN"
    return "UNKNOWN"  # MCP protocol steps: tools/call, tools/list, server/discover


def convert(rows, decisions):
    by_trace = {d["trace_id"]: d for d in decisions}
    out = []
    for r in rows:
        a = {k: v for k, v in r["attrs"].items() if k not in DROP}
        k = kind(r["name"], r["parent_id"] is None)
        d = by_trace.get(r["trace_id"])
        if k == "LLM":
            a.update({"llm.model_name": a.get("gen_ai.response.model"), "llm.provider": "anthropic",
                      "llm.token_count.prompt": a.get("gen_ai.usage.input_tokens", 0), "llm.token_count.completion": a.get("gen_ai.usage.output_tokens", 0)})
            if r["parent_id"] is None:
                r = {**r, "name": "judge"}  # the orphan model calls are the fact-named judge
        if k == "TOOL":
            a["tool.name"] = r["name"].split(" ", 1)[1]
        if r["name"] == "gate.run" and d:
            a.update({"openinference.span.kind": "CHAIN", "warrant.record_id": d.get("record_id"), "warrant.mode": d.get("mode"), "warrant.latency_ms": d.get("latency_ms"),
                      "input.value": (d.get("action") or {}).get("rationale") or json.dumps(d.get("action"))[:500], "output.value": d["decision"]})
        if k == "DECISION" and d:
            b = d.get("belief") or {}  # v3 has no belief layer, so its decision spans carry the decision only
            a.update({"warrant.p_safe": b.get("p_safe"), "warrant.expected_loss": b.get("expected_loss"), "warrant.cost_of_delay": b.get("cost_of_delay"), "warrant.stake": b.get("stake"),
                      "warrant.top_doubt": b.get("top_doubt"), "warrant.top_doubt_source": b.get("top_doubt_source"), "warrant.gather": b.get("gather"),
                      "warrant.decision": d["decision"], "warrant.vetoed_by": b.get("vetoed_by"), "warrant.rule_applied": d.get("rule_applied"),
                      "output.value": d["decision"]})
        a["openinference.span.kind"] = k
        a = {x: y for x, y in a.items() if y is not None}
        s = {"name": r["name"], "context": {"trace_id": r["trace_id"], "span_id": r["span_id"]}, "span_kind": k, "start_time": _iso(r["start_ns"]),
             "end_time": _iso(r["end_ns"]), "status_code": "ERROR" if r["status"] == "ERROR" else "OK" if r["status"] == "OK" else "UNSET", "attributes": a}
        if r["parent_id"]:
            s["parent_id"] = r["parent_id"]
        out.append(s)
    return out


def main(url):
    from phoenix.client import Client
    cl = Client(base_url=url)
    for version, folder in RUNS.items():
        path = os.path.join(AI, "runs", folder)
        rows = [json.loads(l) for l in open(os.path.join(path, "traces.jsonl"))]
        decisions = [json.loads(l) for n in ("decisions.jsonl", "decisions_repeats.jsonl") for l in open(os.path.join(path, n))]
        try:
            if cl.spans.get_spans(project_identifier=project(version), limit=1):
                sys.exit(f"{project(version)} already has spans; delete the project in Phoenix first, so nothing is loaded twice")
        except Exception as e:  # a project that does not exist yet
            if "exit" in type(e).__name__.lower():
                raise
        spans = convert(rows, decisions)
        for i in range(0, len(spans), 500):
            cl.spans.log_spans(project_identifier=project(version), spans=spans[i:i + 500])
        print(version, len(spans), "spans ->", project(version))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "http://localhost:6006")
