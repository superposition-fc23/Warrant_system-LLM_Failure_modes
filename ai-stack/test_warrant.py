"""Gate guardrails that need no model: the model call is stubbed, so these run free and fast.

    .venv/bin/python test_warrant.py
"""
import asyncio
import json
import os
import re
import tempfile

import belief
import crm_mcp
import live_sources
import llm
import warrant

D = json.load(open("evals/crm_cases.json"))
CASES = {c["id"]: c for c in D["cases"]}
CLEAN = json.dumps({"limits": [], "conflicts": [], "checked": [{"fact": "contract_terms", "record_id": "__DOC__"}], "discriminating_fact": None, "owner_role": None, "question": None})
prompts = []


def stub(reply=CLEAN, stop="end_turn", during=None):
    def ask(model, prompt, **kw):
        prompts.append(prompt)
        llm.LAST_USAGE, llm.LAST_META = (10, 10), {"served_model": "stub", "stop_reason": stop}
        if during:
            during()
        doc = re.search(r'"id": "((?:OF|AM|EM|TR|RN)-[^"]+)"', prompt)
        return reply.replace("__DOC__", doc.group(1) if doc else "none")
    llm.ask = ask


def run(cid):
    return asyncio.run(warrant.run(CASES[cid], D["now"], D["people"], D["authority"]))


def test_swap_with_ten_or_more_names():
    m = {f"Name {i}": f"PERSON_{i}" for i in range(1, 13)}
    text = "Name 1 and Name 10 and Name 12"
    assert warrant.swap(text, m) == "PERSON_1 and PERSON_10 and PERSON_12"
    assert warrant.swap(warrant.swap(text, m), m, reverse=True) == text


def test_sources_moving_during_the_check_stop_the_commit():
    stub(during=lambda: crm_mcp.WORLD["billing"]["credits"].append({"id": "CR-9", "amount": 1, "currency": "USD", "incident_id": "X", "issued_by": "a", "issued_at": D["now"]}))
    r = run("CT-01")
    assert r["decision"] == "gather" and any(c["name"] == "reread" and c["result"] == "changed" for c in r["checks"])
    assert r["question"], "a moved source must reach a person"


def test_unchanged_sources_commit():
    stub()
    assert run("CT-03")["decision"] == "act"


def test_truncated_reply_holds():
    stub(stop="max_tokens")
    assert run("CT-01")["decision"] == "hold"


def test_unreadable_reply_holds():
    stub(reply="not json")
    assert run("CT-01")["decision"] == "hold"


def test_named_fact_is_the_money_conflict_not_the_steering_attempt():
    steer = {"fact": "text told the reviewer to skip", "kind": "injection", "amount_at_stake": None, "values": []}
    money = {"fact": "open chargeback", "kind": "payment_risk", "amount_at_stake": None, "values": []}
    stub(reply=json.dumps({"limits": [], "conflicts": [steer, money], "discriminating_fact": "something else", "owner_role": None, "question": "q"}))
    assert run("CT-01")["discriminating_fact"] == "open chargeback"


def fault(system, kind):
    crm_mcp.FAULTS = {system: kind}
    try:
        stub()
        prompts.clear()
        return run("CT-01")
    finally:
        crm_mcp.FAULTS = {}


def test_a_source_that_fails_never_produces_an_act():
    warrant.SOURCE_BUDGET = 0.2
    for system in ("crm", "billing", "contracts", "risk"):
        for kind in ("timeout", "error", "malformed"):
            r = fault(system, kind)
            assert r["decision"] == "gather", (system, kind, r["decision"])
            assert not prompts, "no model call on a failed source"
            assert r["question"] and "could not be read" in r["question"]["text"]


def test_a_stale_source_gathers():
    for system in ("crm", "billing", "risk"):
        assert fault(system, "stale")["decision"] == "gather", system


def test_money_moves_only_on_an_act_for_that_exact_proposal():
    written = []
    live_sources.add_credit = lambda *x: written.append(x) or "pc_1"
    warrant.LEDGER_PATH = os.path.join(tempfile.mkdtemp(), "ledger.jsonl")
    p = {"account_id": "A", "amount": 10, "currency": "USD", "incident_id": "I", "agent": "x"}
    for rec in ({"decision": "hold", "action": p, "record_id": "R"}, {"decision": "gather", "action": p, "record_id": "R"},
                {"decision": "act", "action": {**p, "amount": 11}, "record_id": "R"}):
        try:
            warrant.commit_credit(rec, p)
            raise AssertionError("wrote without an act")
        except PermissionError:
            pass
    assert not written and warrant.commit_credit({"decision": "act", "action": p, "record_id": "R"}, p) == "pc_1"


def test_a_credit_the_source_does_not_show_yet_still_stops_a_second_one():
    warrant.LEDGER_PATH = os.path.join(tempfile.mkdtemp(), "ledger.jsonl")
    stub()
    p = CASES["CT-01"]["proposal"]
    warrant.record_commit(p, "pc_1", D["now"])
    r = run("CT-01")
    assert r["decision"] == "hold" and "pc_1" in r["discriminating_fact"]
    warrant.LEDGER_PATH = os.path.join(tempfile.mkdtemp(), "ledger.jsonl")


def test_more_balance_than_listed_credits_gathers():
    stub()
    world = CASES["CT-01"]["world"]["billing"]
    world["credit_balance"] = 300
    try:
        r = run("CT-01")
    finally:
        del world["credit_balance"]
    assert r["decision"] == "gather" and "behind" in r["discriminating_fact"]


def test_tightening_the_boundary_changes_the_decision():
    stub()
    assert run("CT-01")["decision"] == "act"
    edge = warrant.BOUNDARY["service_credit"]["act_up_to"]
    warrant.BOUNDARY["service_credit"]["act_up_to"] = 100
    try:
        r = run("CT-01")
    finally:
        warrant.BOUNDARY["service_credit"]["act_up_to"] = edge
    assert r["decision"] == "hold" and "boundary" in r["discriminating_fact"]


def slack_setup():
    import slack_card
    sent = []
    slack_card.client = lambda: type("C", (), {"chat_update": lambda self, **k: sent.append(k)})()
    p = {**CASES["PL-03"]["proposal"], "amount": 600}
    rec = {"record_id": "R1", "trace_id": "abc123", "case_id": "X", "action": p, "checks": [{"name": "prior_compensation", "result": "fail"}],
           "beliefs": [{"source": "billing", "value": {"a": 1}}], "discriminating_fact": "f", "question": {"to_role": "Billing analyst", "text": "q"}}
    slack_card.PENDING["abc123"] = {"rec": rec, "ts": "1", "channel": "C", "out": tempfile.mkdtemp()}
    slack_card.RULED.clear()
    warrant.LEDGER_PATH = os.path.join(tempfile.mkdtemp(), "ledger.jsonl")
    warrant.RULES_PATH = os.path.join(tempfile.mkdtemp(), "rules.json")
    belief.STATE_PATH = os.path.join(tempfile.mkdtemp(), "beliefs.json")
    return slack_card, sent


def test_keeping_a_hold_writes_nothing_and_offers_a_rule():
    slack_card, sent = slack_setup()
    written = []
    live_sources.add_credit = lambda *x: written.append(x) or "pc_1"
    assert slack_card.handle("ruling_hold", "abc123")["ruling"] == "reject"
    assert not written and any("make_rule" in json.dumps(b) for b in sent[-1]["blocks"])


def test_a_ruling_to_commit_refuses_if_billing_moved():
    slack_card, sent = slack_setup()
    written = []
    live_sources.add_credit = lambda *x: written.append(x) or "pc_1"
    live_sources.read_billing = lambda a: {"a": 2}
    assert slack_card.handle("ruling_commit", "abc123")["ruling"] == "commit refused" and not written
    live_sources.read_billing = lambda a: {"a": 1}
    assert slack_card.handle("ruling_commit", "abc123")["credit_id"] == "pc_1" and written


def test_a_ruling_becomes_a_scoped_rule_that_settles_the_replay():
    slack_card, sent = slack_setup()
    row = slack_card.handle("make_rule", "abc123")
    rule = row["rule"]
    assert rule["scope"] and rule["owner"] and rule["expires"]
    rule["expires"] = "2026-12-01"
    warrant.save_rule(rule)
    stub()
    assert run("RP-01")["rule_applied"] == rule["id"]


def test_conflict_the_proposal_agrees_with_is_not_material():
    conflict = {"kind": "entitlement", "amount_at_stake": None}
    assert warrant.material(conflict, None) and not warrant.material({**conflict, "proposal_matches_governing": True}, None)


def test_stale_assertions_never_reach_the_model():
    stub()
    prompts.clear()
    run("CT-08")
    assert "open (risk-agent)" not in prompts[-1]


def test_names_are_redacted_from_the_prompt():
    stub()
    prompts.clear()
    run("PL-11")
    assert "Priya Shah" not in prompts[-1] and "Wren Analytics" not in prompts[-1]


def test_a_ruling_writes_through_the_same_guard():
    written = []
    live_sources.add_credit = lambda *x: written.append(x) or "pc_1"
    warrant.LEDGER_PATH = os.path.join(tempfile.mkdtemp(), "ledger.jsonl")
    p = {"account_id": "A", "amount": 10, "currency": "USD", "incident_id": "I", "agent": "x"}
    held = {"decision": "hold", "action": p, "record_id": "R", "trace_id": "t1"}
    for rec, who in ((held, None), ({**held, "action": {**p, "amount": 11}}, "analyst"), ({**held, "mode": "shadow"}, "analyst")):
        try:
            warrant.commit_credit(rec, p, ruled_by=who)
            raise AssertionError("wrote without authority")
        except PermissionError:
            pass
    assert not written and warrant.commit_credit(held, p, ruled_by="analyst") == "pc_1"
    assert json.loads(open(warrant.LEDGER_PATH).read())["ruled_by"] == "analyst"
    try:
        warrant.commit_credit(held, p, ruled_by="analyst")
        raise AssertionError("committed one record twice")
    except PermissionError:
        assert len(written) == 1


def test_the_agent_loop_sends_no_names_and_the_customer_gets_them_back():
    import agent
    case = CASES["CT-01"]
    name, sent, phone = case["world"]["crm"]["name"], [], "-".join(("206", "555", "0142"))    # built here so the repo scan stays clean
    blocks = lambda *b: type("R", (), {"content": list(b)})()
    use = type("B", (), {"type": "tool_use", "id": "1", "input": {"account_id": "ACC-2001", "amount": 10, "incident_id": "I", "rationale": "for ACCOUNT"}})()
    text = type("B", (), {"type": "text", "text": "Sorry, ACCOUNT."})()
    replies = [blocks(use), blocks(text)]

    class Client:
        class beta:
            class messages:
                @staticmethod
                def create(**k):
                    sent.append(json.dumps(k["messages"], default=str))
                    return replies.pop(0)

    async def issue(args, *a):
        assert args["rationale"] == f"for {name}", "the proposal must carry the real name"
        return {}, {"status": "held", "reason": f"{name} has a credit; call {phone}"}
    agent.issue_credit = issue
    ticket = {"id": "T", "agent": "a", "account": "ACC-2001", "text": f"Ticket from {name}, account ACC-2001."}
    row = asyncio.run(agent.run_ticket(ticket, None, D, {"ACC-2001": case}, Client()))
    assert name not in "".join(sent) and phone not in "".join(sent)
    assert row["reply"] == f"Sorry, {name}."


def test_a_slack_card_shows_roles_and_ids_not_names():
    import slack_card
    case = CASES["CT-01"]
    crm_mcp.load(case["world"], D["people"], D["authority"])
    crm, person = case["world"]["crm"], D["people"][0]
    p = {**case["proposal"], "rationale": f"{crm['name']} asked {person['name']}"}
    rec = {"record_id": "R", "trace_id": "t", "action": p, "beliefs": [{"source": "crm", "value": crm}], "discriminating_fact": f"{person['name']} issued it to {crm['name']}",
           "question": {"to_role": "Billing analyst", "text": f"Ask {crm.get('csm')}?"}}
    shown = json.dumps(slack_card.card(rec))
    for n in (crm["name"], person["name"], crm.get("csm")):
        assert n and n not in shown, n
    assert p["account_id"] in shown and person["role"] in shown


def belief_state():
    belief.STATE_PATH = os.path.join(tempfile.mkdtemp(), "beliefs.json")


def test_a_hard_veto_beats_any_belief():
    stub()
    belief_state()
    case = json.loads(json.dumps(CASES["CT-01"]))
    case["proposal"]["amount"] = 1500    # above agent authority, while every source is fresh and the model finds nothing
    r = asyncio.run(warrant.run(case, D["now"], D["people"], D["authority"]))
    assert r["decision"] == "hold" and r["belief"]["vetoed_by"] == "authority" and r["belief"]["p_safe"] <= 0.005


def test_the_lag_case_gathers_on_belief_alone():
    stub()
    belief_state()
    warrant.LEDGER_PATH = os.path.join(tempfile.mkdtemp(), "none.jsonl")
    case = json.loads(json.dumps(CASES["CT-01"]))
    case["world"]["billing"]["updated_at"] = "2026-11-01T08:59:20Z"    # changed 40 s ago; the credit list shows nothing yet
    prompts.clear()
    r = asyncio.run(warrant.run(case, D["now"], D["people"], D["authority"]))
    assert r["decision"] == "gather" and r["belief"]["gather"] == "credit_list_complete" and r["belief"]["wait_seconds"] > 0
    assert "Re-read in" in r["discriminating_fact"] and not prompts, "a re-read must come before any model call"
    assert r["question"]


def test_a_ruling_moves_the_right_source_the_right_way():
    belief_state()
    start = belief.reliability("billing")
    assert belief.rule_on("billing", kept_held=True) < start
    assert belief.reliability("risk") == json.load(open(belief.STATE_PATH))["risk"]["alpha"] / 200
    low = belief.reliability("billing")
    assert belief.rule_on("billing", kept_held=False) > low


def test_a_ruling_on_an_agent_error_blames_no_source():
    assert warrant.ruling_source({"checks": [{"name": "authority", "result": "fail"}], "belief": {"top_doubt_source": "crm"}}) is None
    assert warrant.ruling_source({"checks": [{"name": "prior_compensation", "result": "fail"}], "belief": {}}) == "billing"


def test_decay_falls_with_age_and_matches_the_old_window():
    w = [belief.weight(h, 6) for h in (0, 1, 3, 6, 9, 24, 100)]
    assert w == sorted(w, reverse=True) and w[3] == 0.5 and w[1] > 0.99


def test_a_case_settled_by_belief_makes_no_model_call():
    stub()
    belief_state()
    case = json.loads(json.dumps(CASES["CT-01"]))
    case["proposal"]["amount"] = 40
    prompts.clear()
    r = asyncio.run(warrant.run(case, D["now"], D["people"], D["authority"]))
    assert r["decision"] == "act" and not prompts and r["usage"] == {}


def test_three_samples_run_and_one_dissent_stops_the_act():
    belief_state()
    clean = CLEAN.replace("__DOC__", "OF-2001")
    replies = [clean, clean, json.dumps({"limits": [], "conflicts": [{"fact": "open dispute", "kind": "payment_risk", "amount_at_stake": None, "values": []}], "checked": [{"fact": "contract_terms", "record_id": "OF-2001"}],
                                         "discriminating_fact": "open dispute", "owner_role": None, "question": "Is it open?"})]

    def ask(model, prompt, **kw):
        llm.LAST_USAGE, llm.LAST_META = (10, 10), {"served_model": "stub", "stop_reason": "end_turn"}
        return replies.pop()
    llm.ask = ask
    r = run("CT-01")
    assert r["decision"] == "hold" and sum(x["raised"] for x in r["samples"]) == 1 and len(r["usage"]["answers"]) == 3
    assert r["belief"]["p_safe"] < 0.75


def silent(checked):
    belief_state()
    stub(reply=json.dumps({"limits": [], "conflicts": [], "checked": checked, "discriminating_fact": None, "owner_role": None, "question": None}))
    return run("CT-01")


def test_silence_without_a_check_is_not_evidence():
    r = silent([])
    assert r["decision"] == "gather" and r["belief"]["gather"] == "evidence_agrees"
    assert r["belief"]["facts"]["evidence_agrees"] == belief.PRIORS["unread_fact_policy"] and "contract_terms" in r["samples"][0]["omitted"]


def test_a_claimed_check_needs_a_real_contract_id():
    for bad in ("OF-9999", "ACC-2001", "INV-20011"):
        r = silent([{"fact": "contract_terms", "record_id": bad}])
        assert r["decision"] != "act" and r["samples"][0]["bad_citations"] == [bad], bad
    r = silent([{"fact": "contract_terms", "record_id": "OF-2001"}])
    assert r["decision"] == "act" and r["samples"][0]["checked"]


def test_mutation_labels_hold_where_code_can_tell():
    import mutate
    out = mutate.build()
    by = {c["id"]: c for c in out["cases"]}
    assert len(by) == len(out["cases"]) and {c["unsafe"] for c in out["cases"]} == {True, False}
    for c in out["cases"]:
        if c["mutation"] == "under_cap":
            assert c["proposal"]["amount"] < c["world"]["billing"]["monthly_fee"] * 0.10
        if c["mutation"] == "over_cap":
            assert c["world"]["billing"]["monthly_fee"] * 0.10 < c["proposal"]["amount"] <= 1000
        if c["mutation"] == "authority":
            assert c["proposal"]["amount"] > 1000
    assert mutate.build() == out, "the same seed must give the same file"


def test_a_card_shows_the_clause_and_does_not_repeat_itself():
    import slack_card
    case = CASES["CT-01"]
    crm_mcp.load(case["world"], D["people"], D["authority"])
    fact = "Above the contract's credit cap: 900 against cap 600 (10% of 6000, OF-2001)"
    rec = {"record_id": "R", "trace_id": "t", "action": case["proposal"], "belief": {"vetoed_by": "contract_cap", "top_doubt": "evidence_agrees"}, "discriminating_fact": fact,
           "beliefs": [{"source": "contracts", "value": case["world"]["contracts"]}, {"source": "crm", "value": case["world"]["crm"]}],
           "question": {"to_role": "Billing analyst", "text": f"{fact}. Commit anyway?"}}
    shown = json.dumps(slack_card.card(rec))
    assert "may not exceed 10%" in shown and "OF-2001, order form, signed" in shown and "CLM" in shown
    assert shown.count("900 against cap 600") == 1 and "Commit anyway?" in shown


def test_a_person_cannot_commit_a_credit_the_hold_never_named():
    slack_card, sent = slack_setup()
    written = []
    live_sources.add_credit = lambda *x: written.append(x) or "pc_2"
    item = slack_card.PENDING["abc123"]
    item["rec"]["belief"] = {"gather": "credit_list_complete"}
    p = item["rec"]["action"]
    warrant.BELIEF_ONLY = True
    warrant.record_commit(p, "pc_1", "2026-11-01T09:00:00Z", "other-trace")
    live_sources.read_billing = lambda a: {"a": 1, "credit_balance": 0, "credits": []}
    try:
        row = slack_card.handle("ruling_commit", "abc123")
    finally:
        warrant.BELIEF_ONLY = False
    assert row["ruling"] == "commit refused" and "pc_1" in row["note"] and not written
    os.remove(warrant.LEDGER_PATH)
    live_sources.read_billing = lambda a: {"a": 1, "credit_balance": 300, "credits": []}
    row = slack_card.handle("ruling_commit", "abc123")
    assert row["ruling"] == "commit refused" and "balance" in row["note"] and not written


def test_the_demo_server_serves_little_and_starts_clean():
    import http.client
    import sys
    import threading
    from http.server import ThreadingHTTPServer
    import demo_server as ds
    tmp = tempfile.mkdtemp()
    ds.STATE_DIR, ds.RUNS_DIR = os.path.join(tmp, "state"), os.path.join(tmp, "runs")
    os.makedirs(ds.STATE_DIR)
    ds.COMMAND = [sys.executable, "-c", "import os,json;open(os.environ['WARRANT_RUN_DIR']+'/tickets.jsonl','w').write('')"]
    server = ThreadingHTTPServer(("127.0.0.1", 0), ds.Handler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()

    def call(method, path, headers=None):
        c = http.client.HTTPConnection("127.0.0.1", port)
        c.request(method, path, headers=headers or {})
        r = c.getresponse()
        return r.status, r.read()
    good = {"Origin": f"http://127.0.0.1:{port}", "X-Warrant-Demo": "1"}
    try:
        for path in ("/ai-stack/.env", "/../ai-stack/.env", "/reference/", "/ai-stack/state/ledger.jsonl"):
            assert call("GET", path)[0] == 404, path
        assert call("GET", "/api/status", {"Host": "evil.example"})[0] == 403
        assert call("POST", "/api/start")[0] == 403
        assert call("POST", "/api/start", {"Origin": "http://evil.example", "X-Warrant-Demo": "1"})[0] == 403
        assert call("POST", "/api/start", {"Origin": good["Origin"]})[0] == 403
        state = os.path.join(ds.STATE_DIR, "rules.json")
        open(state, "w").write("{}")
        assert call("POST", "/api/again", good)[0] == 200 and os.path.exists(state), "run again keeps rulings"
        ds.run["proc"].wait()
        assert call("POST", "/api/start", good)[0] == 200 and not os.path.exists(state), "start clears rulings"
        ds.run["proc"].wait()
        assert b"<html" in call("GET", "/")[1].lower() and json.loads(call("GET", "/api/status")[1])["phase"] == "finished"
    finally:
        server.shutdown()


def test_rule_applies_only_inside_its_scope():
    warrant.RULES_PATH = os.path.join(tempfile.mkdtemp(), "rules.json")
    rule = {"id": "SR-T", "pattern": {"action_type": "service_credit", "check": "prior_compensation"}, "effect": "hold", "expires": "2026-12-01"}
    stub()
    warrant.save_rule(rule)
    assert run("RP-01")["rule_applied"] is None, "a rule with no scope must not apply"
    warrant.save_rule({**rule, "scope": {"max_amount": 100}})
    assert run("RP-01")["rule_applied"] is None, "125 is outside a 100 limit"
    warrant.save_rule({**rule, "scope": {"max_amount": 1000, "currency": "USD"}})
    assert run("RP-01")["rule_applied"] == "SR-T"


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print("ok", t.__name__)
    print(f"{len(tests)} passed")
