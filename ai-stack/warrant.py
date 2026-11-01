"""Warrant v1: a gate in front of support agents' money actions. LangGraph orchestrates the gate's own steps, never the agents.

    read_sources -> freshness -> checks -> rules -> compare -> decide -> (commit | route) -> record

Split by design (index.html section 11): deterministic code reads sources, judges freshness, checks authority, prior
compensation and currency, applies standing rules, and makes the final decision. The model only does what code cannot:
reads contract text into limits, and judges whether conflicting values are material and which source governs. The model
proposes; code decides. Every source read goes through the MCP server in crm_mcp.py; every step is an OpenTelemetry span.

    .venv/bin/python warrant.py PL-01      # one case from evals/crm_cases.json
"""
import asyncio
import json
import re
import sys
import time
from datetime import datetime, timedelta
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from mcp.client.client import Client

import crm_mcp
import llm
from router import route
from telemetry import tracer

FRESHNESS = {"crm": timedelta(hours=6), "billing": timedelta(hours=6), "risk": timedelta(hours=24), "contracts": timedelta(days=30)}
ASSERTION_WINDOW = timedelta(hours=1)    # an agent's remembered fact older than this is replaced by a source read
FACT_OWNER = {"risk": "Risk analyst", "billing": "Billing analyst", "contracts": "Billing analyst", "crm": "Billing analyst"}
RULES = []                               # standing rules, from rulings; v1 keeps them in memory per run


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


class State(TypedDict, total=False):
    case: dict
    now: str
    sources: dict
    authority: dict
    assertions: list
    checks: list
    rule_applied: str
    compare: dict
    decision: str
    question: dict
    record: dict
    usage: dict


async def read_sources(s: State) -> State:
    p = s["case"]["proposal"]
    sources = {}
    async with Client(crm_mcp.server) as client:
        for system, tool in crm_mcp.TOOLS.items():
            with tracer.start_as_current_span(f"mcp.tool {tool}") as sp:
                sources[system] = crm_mcp.parse(await client.call_tool(tool, {"account_id": p["account_id"]}))
                sp.set_attribute("account_id", p["account_id"])
        with tracer.start_as_current_span("mcp.tool authority_get_limits"):
            authority = crm_mcp.parse(await client.call_tool("authority_get_limits", {"action_type": p["type"]}))
    return {"sources": sources, "authority": authority}


def freshness(s: State) -> State:
    now, checks, assertions = ts(s["now"]), [], []
    for system, rec in s["sources"].items():
        seen = rec.get("synced_at") or rec.get("updated_at")
        age = now - ts(seen)
        ok = age <= FRESHNESS[system]
        checks.append({"name": f"fresh.{system}", "result": "pass" if ok else "stale",
                       "detail": f"{system} last changed {seen}, {age.days}d {age.seconds // 3600}h ago, window {FRESHNESS[system]}"})
    for a in s["case"]["proposal"]["asserted"]:
        old = now - ts(a["observed_at"]) > ASSERTION_WINDOW
        assertions.append({**a, "used": not old, "note": "older than 1h, replaced by a source read" if old else "current"})
    return {"checks": checks, "assertions": assertions}


def checks(s: State) -> State:
    p, b, out = s["case"]["proposal"], s["sources"]["billing"], []
    lim = next((l for l in s["authority"]["limits"] if l["who"] == "agent"), {})
    key, val = next(((k, p[f]) for k, f in [("max", "amount"), ("max_pct", "pct"), ("max_seats", "seats")] if k in lim), (None, None))
    if key:
        ok = val is None or lim[key] is None or val <= lim[key]
        out.append({"name": "authority", "result": "pass" if ok else "fail",
                    "detail": f"{val} against agent limit {lim[key]}" + ("" if ok else f"; needs {approver(s['authority'], key, val)}")})
    if p.get("amount") is not None:
        ok = p["currency"] == b["currency"]
        out.append({"name": "currency", "result": "pass" if ok else "fail", "detail": f"proposal {p['currency']}, billing {b['currency']}"})
    prior = [c for c in b["credits"] if p.get("incident_id") and c["incident_id"] == p["incident_id"]]
    out.append({"name": "prior_compensation", "result": "fail" if prior else "pass",
                "detail": "; ".join(f"{c['id']} {c['amount']} {c['currency']} for {c['incident_id']} by {c['issued_by']} at {c['issued_at']}"
                                    for c in prior) or "no earlier credit for this incident"})
    return {"checks": s["checks"] + out}


def approver(authority, key, val):
    for l in authority["limits"]:
        if l["who"] != "agent" and (l[key] is None or val <= l[key]):
            person = next((x for x in authority["people"] if x["name"] == l["who"]), {})
            return f"{l['who']} ({person.get('role', '')})"
    return "a person with authority"


def rules(s: State) -> State:
    failed = {c["name"] for c in s["checks"] if c["result"] != "pass"}
    for r in RULES:
        if r["pattern"]["action_type"] in (s["case"]["proposal"]["type"], "*") and r["pattern"]["check"] in failed:
            return {"rule_applied": r["id"]}
    return {"rule_applied": None}


COMPARE_SYSTEM = (
    "You are the comparison step of a gate in front of an AI support agent's money action. You do not decide; code does. "
    "Read the systems of record and report, as JSON only: limits the signed contract documents set, and conflicts between "
    "what the proposal assumes and what the records say. Rules: a signed document governs over an unsigned one, whatever "
    "the dates; a signed amendment with a later effective date supersedes the clause it replaces; a closed flag, or a flag "
    "unrelated to payment, fraud, chargebacks or collections, is not a conflict; differences under 1% are not material. "
    "Never pick a side silently: name both values and their sources. A clean case has no conflicts; say so rather than invent one.")

COMPARE_PROMPT = """Now: {now}
Proposed action by {agent}: {summary}
Proposal: {proposal}

Systems of record (via MCP):
{sources}

Agent assertions still current: {assertions}

Return JSON with:
- limits: list of {{name ("credit_cap" | "sla_credit_rate" | "refund_window_days" | "seats" | "other"), value (number), unit ("pct_of_monthly_fee" | "currency" | "days" | "seats"), doc_id}} from signed, governing documents only
- conflicts: list of {{fact, values: [{{value, source, record_id}}], material (true|false), governing_source, why}}
- discriminating_fact: the one fact that would settle the most material conflict, as a sentence naming the record, or null
- owner_role: who owns that fact ("Billing analyst" | "Risk analyst" | "RevOps manager" | "VP Finance" | "Finance controller"), or null
- question: one question for that owner, under 30 words, or null"""


def summary(p):
    what = {"amount": f"{p['amount']} {p['currency']}" if p.get("amount") is not None else None,
            "pct": f"{p['pct']}%" if p.get("pct") is not None else None, "seats": f"{p['seats']} seats" if p.get("seats") is not None else None}
    return f"{p['type'].replace('_', ' ')} of {next(v for v in what.values() if v)} on {p['account_id']}: {p['rationale']}"


def compare(s: State) -> State:
    if s.get("rule_applied"):
        return {"compare": {"skipped": f"settled by {s['rule_applied']}"}, "usage": {}}
    p = s["case"]["proposal"]
    model, _, _ = route(task="reason", cost=1, latency=1, quality=2)
    prompt = COMPARE_PROMPT.format(now=s["now"], agent=p["agent"], summary=summary(p), proposal=json.dumps(p),
                                   sources=json.dumps(s["sources"], indent=1),
                                   assertions=json.dumps([a for a in s["assertions"] if a["used"]]))
    with tracer.start_as_current_span("llm.compare") as sp:
        t = time.time()
        out = llm.ask(model, prompt, system=COMPARE_SYSTEM, max_tokens=4000, effort="low")
        tin, tout = llm.LAST_USAGE
        cin, cout = llm.MODELS[model]["cost"]
        cost = (tin * cin + tout * cout) / 1e6
        for k, v in {"gen_ai.request.model": llm.MODELS[model]["id"], "gen_ai.usage.input_tokens": tin,
                     "gen_ai.usage.output_tokens": tout, "cost_usd": round(cost, 5), "latency_ms": round((time.time() - t) * 1000)}.items():
            sp.set_attribute(k, v)
    try:
        data = json.loads(re.search(r"\{.*\}", out, re.S).group())
    except Exception:
        data = {"parse_error": out[:300], "conflicts": [], "limits": []}
    return {"compare": data, "usage": {"model": model, "tokens_in": tin, "tokens_out": tout, "cost_usd": cost}}


def decide(s: State) -> State:
    """Deterministic. The model's output is evidence here, not the decision."""
    p, fee = s["case"]["proposal"], s["sources"]["billing"]["monthly_fee"]
    extra = []
    for l in s["compare"].get("limits", []):
        if l.get("name") == "credit_cap" and l.get("unit") == "pct_of_monthly_fee" and p.get("amount") is not None and p["type"] == "service_credit":
            cap = l["value"] * fee / 100
            extra.append({"name": "contract_cap", "result": "pass" if p["amount"] <= cap else "fail",
                          "detail": f"{p['amount']} against cap {cap:g} ({l['value']}% of {fee}, {l.get('doc_id')})"})
    checks = s["checks"] + extra
    material = [c for c in s["compare"].get("conflicts", []) if c.get("material")]
    if s.get("rule_applied"):
        r = next(r for r in RULES if r["id"] == s["rule_applied"])
        decision = "act" if r["effect"] == "act" else "hold"
    elif any(c["result"] == "stale" for c in checks):
        decision = "gather"
    elif any(c["result"] == "fail" for c in checks) or material or "parse_error" in s["compare"]:
        decision = "hold"
    else:
        decision = "act"
    return {"decision": decision, "checks": checks}


def route_question(s: State) -> State:
    if s.get("rule_applied"):
        return {"question": None}
    c, people = s["compare"], s["authority"]["people"]
    failed = [x for x in s["checks"] if x["result"] != "pass"]
    if failed and failed[0]["name"].startswith("fresh."):
        system = failed[0]["name"].split(".")[1]
        role, text = FACT_OWNER[system], f"{system.title()} data is past its freshness window ({failed[0]['detail']}). Re-sync before this commits?"
    elif failed and failed[0]["name"] == "authority":
        role, text = failed[0]["detail"].split("needs ")[-1], f"Above agent authority: {failed[0]['detail']}. Approve?"
    elif c.get("question"):
        role, text = c.get("owner_role") or "Billing analyst", c["question"]
    else:
        role, text = "Billing analyst", f"Check failed: {failed[0]['detail'] if failed else 'unknown'}. Commit?"
    name = next((x["name"] for x in people if x["active"] and x["role"] in role), None)
    return {"question": {"to_role": re.sub(r".*\((.*)\)", r"\1", role), "to_name": name or re.sub(r" \(.*", "", role), "text": text,
                         "options": ["Hold", "Commit as proposed", "Amend"]}}


def commit(s: State) -> State:
    with tracer.start_as_current_span("commit") as sp:
        sp.set_attribute("note", "v1 records the commit; it does not write to billing")
    return {"question": None}


_seq = [0]


def record(s: State) -> State:
    _seq[0] += 1
    c, p = s["case"], s["case"]["proposal"]
    beliefs = []
    for system, rec in s["sources"].items():
        beliefs.append({"fact": system, "value": rec, "source": system, "record_id": rec.get("account_id"),
                        "observed_at": rec.get("synced_at") or rec.get("updated_at"),
                        "fresh": next(x["result"] == "pass" for x in s["checks"] if x["name"] == f"fresh.{system}"), "asserted_by": "source"})
    for a in s["assertions"]:
        beliefs.append({"fact": a["fact"], "value": a["value"], "source": "agent memory", "record_id": None,
                        "observed_at": a["observed_at"], "fresh": a["used"], "asserted_by": p["agent"]})
    mat = [x for x in s["compare"].get("conflicts", []) if x.get("material")]
    conflict = None
    if mat:
        m = mat[0]
        conflict = {"fact": m.get("fact"), "values": [f"{v.get('value')} ({v.get('source')}{', ' + v['record_id'] if v.get('record_id') else ''})" for v in m.get("values", [])],
                    "material": True, "governing_source": m.get("governing_source"), "why": m.get("why")}
    rec = {"record_id": f"DR-{_seq[0]:04d}", "case_id": c["id"], "decision": s["decision"], "action": p, "beliefs": beliefs,
           "checks": s["checks"], "conflict": conflict, "conflicts_all": s["compare"].get("conflicts", []),
           "limits": s["compare"].get("limits", []), "discriminating_fact": s["compare"].get("discriminating_fact"),
           "question": s.get("question"), "rule_applied": s.get("rule_applied"), "usage": s.get("usage", {}), "at": s["now"]}
    return {"record": rec}


def traced(name, fn):
    if asyncio.iscoroutinefunction(fn):
        async def run(s):
            with tracer.start_as_current_span(f"gate.{name}"):
                return await fn(s)
    else:
        def run(s):
            with tracer.start_as_current_span(f"gate.{name}"):
                return fn(s)
    return run


g = StateGraph(State)
for name, fn in [("read_sources", read_sources), ("freshness", freshness), ("checks", checks), ("rules", rules),
                 ("compare", compare), ("decide", decide), ("route", route_question), ("commit", commit), ("record", record)]:
    g.add_node(name, traced(name, fn))
g.add_edge(START, "read_sources")
for a, b in [("read_sources", "freshness"), ("freshness", "checks"), ("checks", "rules"), ("rules", "compare"), ("compare", "decide")]:
    g.add_edge(a, b)
g.add_conditional_edges("decide", lambda s: "commit" if s["decision"] == "act" else "route", ["commit", "route"])
g.add_edge("commit", "record")
g.add_edge("route", "record")
g.add_edge("record", END)
app = g.compile()


async def run(case, now, people, authority):
    crm_mcp.load(case["world"], people, authority)
    with tracer.start_as_current_span("gate.run") as sp:
        sp.set_attribute("case_id", case["id"])
        t = time.time()
        out = await app.ainvoke({"case": case, "now": now})
        rec = out["record"]
        rec["latency_ms"] = round((time.time() - t) * 1000)
        rec["trace_id"] = f"{sp.get_span_context().trace_id:032x}"
        sp.set_attribute("decision", rec["decision"])
    return rec


if __name__ == "__main__":
    import telemetry
    d = json.load(open("evals/crm_cases.json"))
    telemetry.setup("runs/adhoc-traces.jsonl")
    c = next(x for x in d["cases"] if x["id"] == (sys.argv[1] if len(sys.argv) > 1 else "PL-01"))
    r = asyncio.run(run(c, d["now"], d["people"], d["authority"]))
    print(json.dumps({k: r[k] for k in ("case_id", "decision", "checks", "conflict", "discriminating_fact", "question", "latency_ms", "usage")}, indent=1))
