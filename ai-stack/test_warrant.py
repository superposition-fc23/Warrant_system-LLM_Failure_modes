"""Gate guardrails that need no model: the model call is stubbed, so these run free and fast.

    .venv/bin/python test_warrant.py
"""
import asyncio
import json
import os
import tempfile

import crm_mcp
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
