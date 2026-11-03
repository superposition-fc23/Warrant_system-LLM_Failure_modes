"""Gate guardrails that need no model: the model call is stubbed, so these run free and fast.

    .venv/bin/python test_warrant.py
"""
import asyncio
import json
import os
import tempfile

import crm_mcp
import live_sources
import llm
import warrant

D = json.load(open("evals/crm_cases.json"))
CASES = {c["id"]: c for c in D["cases"]}
CLEAN = json.dumps({"limits": [], "conflicts": [], "discriminating_fact": None, "owner_role": None, "question": None})
prompts = []


def stub(reply=CLEAN, stop="end_turn", during=None):
    def ask(model, prompt, **kw):
        prompts.append(prompt)
        llm.LAST_USAGE, llm.LAST_META = (10, 10), {"served_model": "stub", "stop_reason": stop}
        if during:
            during()
        return reply
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
    import agent
    written = []
    live_sources.add_credit = lambda *x: written.append(x) or "pc_1"
    warrant.LEDGER_PATH = os.path.join(tempfile.mkdtemp(), "ledger.jsonl")
    p = {"account_id": "A", "amount": 10, "currency": "USD", "incident_id": "I", "agent": "x"}
    for rec in ({"decision": "hold", "action": p, "record_id": "R"}, {"decision": "gather", "action": p, "record_id": "R"},
                {"decision": "act", "action": {**p, "amount": 11}, "record_id": "R"}):
        try:
            agent.commit_credit(rec, p)
            raise AssertionError("wrote without an act")
        except PermissionError:
            pass
    assert not written and agent.commit_credit({"decision": "act", "action": p, "record_id": "R"}, p) == "pc_1"


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
