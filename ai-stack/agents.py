"""Belief-gated action agent with LangGraph: an agent proposes a write, a gate decides whether the evidence still warrants it.

    retrieve governing beliefs -> warrant gate -> (act | draft_and_escalate)

The warrant gate is gate 3 from docs/s1-mcp-gateway/gateway-policy.md: is the governing belief current, uncontested and in
scope for the target tenant. Gates 1 and 2 (identity, tool scope) are assumed passed. Each model step picks its model
through router.route(). Without API keys the gate runs deterministic checks on the retrieved front matter, so the graph
still runs. Run:
    .venv/bin/python agents.py "Restart SQL service on SRV-DB-07" --tenant harbor-legal
    .venv/bin/python agents.py --case PD-02          # run one planted case from evals/planted_defects.json
"""
import json
import re
import sys
from datetime import datetime, timedelta
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from llm import ask, has_key
from rag import retrieve
from router import route

NOW = datetime.fromisoformat("2026-10-30T07:45+00:00")   # reference "now" for the synthetic corpus
CONFLICT_WORDS = r"\b(hold|not recognised|discrepancy|unresolved|on purpose|do not restart|never automatic|removed|" \
                 r"not been refreshed|require VP approval|supersedes|replaced|non-OEM|frame damage|support 5 days)\b"


class State(TypedDict, total=False):
    action: str
    tenant: str
    beliefs: list
    decision: str
    reasons: list
    draft: str
    trace: list


def call(prompt, system="", **route_args):
    model, _, _ = route(**route_args)
    if has_key(model):
        return model, ask(model, prompt, system=system, effort="low")
    return f"{model} (offline)", None


def front_matter(text):
    m = re.match(r"---\n(.*?)\n---", text, re.S)
    return dict(l.split(":", 1) for l in m.group(1).splitlines() if ":" in l) if m else {}


def get_beliefs(s: State) -> State:
    hits = retrieve(f"{s['action']} {s.get('tenant', '')}", k=5)
    beliefs = [{"file": h.metadata.get("file_name"), "score": round(h.score or 0, 2), "text": h.get_content(),
                "meta": {k.strip(): v.strip() for k, v in front_matter(h.get_content()).items()}} for h in hits]
    return {"beliefs": beliefs, "trace": [f"retrieved {len(beliefs)} governing beliefs: {[b['file'] for b in beliefs]}"]}


def offline_gate(s: State):
    reasons = []
    for b in s["beliefs"]:
        meta, name = b["meta"], b["file"]
        tenant = meta.get("tenant")
        if tenant and s.get("tenant") and tenant not in ("all", s["tenant"]):
            continue                                   # out-of-scope belief: ignored, not blended
        if "observed_at" in meta and "validity_window" in meta:
            seen = datetime.fromisoformat(meta["observed_at"].replace("Z", "+00:00"))
            if seen.tzinfo is None:
                seen = seen.replace(tzinfo=NOW.tzinfo)
            n, unit = int(meta["validity_window"][:-1]), meta["validity_window"][-1]
            if NOW - seen > timedelta(**{"m": {"minutes": n}, "d": {"days": n}, "h": {"hours": n}}[unit]):
                reasons.append(f"stale: {name} observed {meta['observed_at']}, window {meta['validity_window']}")
        hit = re.search(CONFLICT_WORDS, b["text"], re.I)
        if hit:
            reasons.append(f"contested or superseded: {name} says '{hit.group(0)}'")
    return reasons


def warrant_gate(s: State) -> State:
    evidence = "\n\n".join(f"[{i + 1}] {b['file']}\n{b['text']}" for i, b in enumerate(s["beliefs"]))
    model, out = call(f"Proposed write action: {s['action']}\nTarget tenant: {s.get('tenant')}\nNow: {NOW.isoformat()}\n"
                      f"Evidence:\n{evidence}\n\nReturn JSON: decision (act|hold), reasons (list), "
                      "discriminating_fact (the one fact that would resolve it, or null).",
                      system="You are gate 3 of an action gateway. Hold if the governing belief is stale, contradicted, "
                             "superseded, or from another tenant. Ignore evidence scoped to other tenants rather than "
                             "blending it. Do not hold on a clean case. Return only JSON.",
                      task="reason", cost=1, latency=1, quality=2)
    if out:
        data = json.loads(re.search(r"\{.*\}", out, re.S).group())
        reasons = data.get("reasons", []) + ([f"resolve with: {data['discriminating_fact']}"] if data.get("discriminating_fact") else [])
        decision = data.get("decision", "hold")
    else:
        reasons = offline_gate(s)
        decision = "hold" if reasons else "act"
    return {"decision": decision, "reasons": reasons,
            "trace": s["trace"] + [f"warrant gate via {model}: {decision}" + (f" ({'; '.join(reasons)})" if reasons else "")]}


def act(s: State) -> State:
    return {"draft": f"EXECUTED: {s['action']}", "trace": s["trace"] + ["executed, logged with the beliefs it relied on"]}


def draft_and_escalate(s: State) -> State:
    return {"draft": f"DRAFT ONLY: {s['action']}\nHeld because: " + "; ".join(s["reasons"]),
            "trace": s["trace"] + ["held as a draft, routed to a human with the contested belief named"]}


graph = StateGraph(State)
for name, fn in [("get_beliefs", get_beliefs), ("warrant_gate", warrant_gate), ("act", act),
                 ("draft_and_escalate", draft_and_escalate)]:
    graph.add_node(name, fn)
graph.add_edge(START, "get_beliefs")
graph.add_edge("get_beliefs", "warrant_gate")
graph.add_conditional_edges("warrant_gate", lambda s: "act" if s["decision"] == "act" else "draft_and_escalate",
                            ["act", "draft_and_escalate"])
graph.add_edge("act", END)
graph.add_edge("draft_and_escalate", END)
app = graph.compile()


def run(action, tenant=""):
    return app.invoke({"action": action, "tenant": tenant})


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--case" in args:
        cases = {c["id"]: c for c in json.load(open("evals/planted_defects.json"))["cases"]}
        c = cases[args[args.index("--case") + 1]]
        action, tenant = c["action"], c["tenant"]
        print(f"{c['id']} planted defect: {c['defect']}; expected {c['expected']}\n")
    else:
        action = args[0] if args else "Restart SQL service on SRV-DB-07"
        tenant = args[args.index("--tenant") + 1] if "--tenant" in args else "harbor-legal"
    result = run(action, tenant)
    for line in result["trace"]:
        print("-", line)
    print("\n" + result["draft"])
    if "--graph" in args:
        print("\nGraph (paste into mermaid.live):\n" + app.get_graph().draw_mermaid())
