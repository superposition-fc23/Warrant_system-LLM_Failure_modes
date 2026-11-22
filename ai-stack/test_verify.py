"""Arm A+verify, written before the code: a conflict that rests on arithmetic or dates states a claim, and code rechecks it.
A false claim drops the conflict; a true one, a missing one or an ungrounded one keeps it. Off by default, so v4 is unchanged.
No model calls.

    .venv/bin/python test_verify.py
"""
import asyncio
import json
import re

import llm
import verify
import warrant

D = json.load(open("evals/crm_cases.json"))
CASES = {c["id"]: c for c in D["cases"]}
SOURCES = 'Proposal: {"amount": 300, "currency": "USD"} monthly_fee 6000, invoice_date "2026-10-20", Now: 2026-11-01, cap 10%, rate 5%, refund window 30 days'


def conflict(claim, kind="amount"):
    return {"fact": "credit vs cap", "kind": kind, "amount_at_stake": 300, "values": [], "governing_source": "contracts",
            "proposal_matches_governing": False, "why": "x", "claim": claim}


def test_evaluator_supports_pct_and_days_only():
    assert verify.evaluate("pct(5, 6000)") == 300
    assert verify.evaluate('days("2026-10-20", "2026-11-01")') == 12
    assert verify.evaluate("days(2026-10-20, 2026-11-01)") == 12, "bare dates are quoted before parsing"
    assert verify.evaluate("300 + 6000 * 0") == 300
    for bad in ("__import__('os')", "open('x')", "2 ** 10", "x + 1", "pct(5)", "[1][0]"):
        assert verify.evaluate(bad) is None, bad


def test_false_claim_drops_the_conflict():
    data = {"conflicts": [conflict({"left": "300", "op": ">", "right": "pct(5, 6000)"})], "limits": []}
    out, refuted = verify.check(data, SOURCES)
    assert out["conflicts"] == [] and len(refuted) == 1


def test_true_claim_keeps_the_conflict():
    data = {"conflicts": [conflict({"left": "300", "op": ">", "right": "pct(5, 3000)"})], "limits": []}
    src = SOURCES + " monthly_fee 3000"
    out, refuted = verify.check(data, src)
    assert len(out["conflicts"]) == 1 and not refuted


def test_date_claim_is_checked():
    data = {"conflicts": [conflict({"left": 'days("2026-10-20", "2026-11-01")', "op": ">", "right": "30"}, kind="contract_terms")], "limits": []}
    out, refuted = verify.check(data, SOURCES)
    assert out["conflicts"] == [] and len(refuted) == 1


def test_missing_or_ungrounded_claim_keeps_the_conflict():
    for claim in (None, {"left": "300", "op": ">", "right": "pct(5, 4000)"}, {"left": "300", "op": ">", "right": "bogus"}):
        out, refuted = verify.check({"conflicts": [conflict(claim)], "limits": []}, SOURCES)
        assert len(out["conflicts"]) == 1 and not refuted, claim


def test_a_claim_must_state_a_violation():
    agree = {"left": "pct(5, 6000)", "op": "==", "right": "300"}
    out, refuted = verify.check({"conflicts": [conflict(agree)], "limits": []}, SOURCES)
    assert len(out["conflicts"]) == 1 and not refuted, "'==' is not a violation, so code can't judge it and keeps the conflict"
    out, refuted = verify.check({"conflicts": [conflict({"left": "300", "op": "!=", "right": "pct(5, 6000)"})], "limits": []}, SOURCES)
    assert out["conflicts"] == [] and len(refuted) == 1


def test_never_drops_kinds_that_are_not_arithmetic():
    for kind in ("injection", "payment_risk", "duplicate", "authority", "currency"):
        out, refuted = verify.check({"conflicts": [conflict({"left": "300", "op": ">", "right": "pct(5, 6000)"}, kind=kind)], "limits": []}, SOURCES)
        assert len(out["conflicts"]) == 1 and not refuted, kind


def test_off_by_default_leaves_v4_schema_and_prompt_alone():
    warrant.VERIFY_CLAIMS = False
    assert "claim" not in warrant.compare_schema()["properties"]["conflicts"]["items"]["properties"]
    assert "claim" not in warrant.compare_prompt_tail()
    warrant.VERIFY_CLAIMS = True
    items = warrant.compare_schema()["properties"]["conflicts"]["items"]
    assert "claim" in items["properties"] and "claim" in items["required"]
    assert "claim" in warrant.compare_prompt_tail()
    warrant.VERIFY_CLAIMS = False


def test_gate_acts_when_the_only_conflict_is_refuted():
    """CT-01 is clean: a 300 credit at 5% of a 6000 fee. A conflict claiming 300 > 5% of 6000 must not stop it."""
    def reply(claim):
        doc = None

        def ask(model, prompt, **kw):
            nonlocal doc
            doc = re.search(r'"id": "((?:OF|AM)-[^"]+)"', prompt).group(1)
            llm.LAST_USAGE, llm.LAST_META = (10, 10), {"served_model": "stub", "stop_reason": "end_turn"}
            return json.dumps({"limits": [], "conflicts": [{"fact": "credit above the SLA rate", "kind": "amount", "amount_at_stake": 300,
                                                            "values": [{"value": "300", "source": "proposal", "record_id": None}], "governing_source": "contracts",
                                                            "proposal_matches_governing": False, "why": "over the rate", "claim": claim}],
                               "checked": [{"fact": "contract_terms", "record_id": doc}], "discriminating_fact": "x", "owner_role": "Billing analyst", "question": "q"})
        return ask
    warrant.VERIFY_CLAIMS = True
    try:
        llm.ask = reply({"left": "300", "op": ">", "right": "pct(5, 6000)"})
        assert asyncio.run(warrant.run(CASES["CT-01"], D["now"], D["people"], D["authority"]))["decision"] == "act"
        llm.ask = reply(None)
        assert asyncio.run(warrant.run(CASES["CT-01"], D["now"], D["people"], D["authority"]))["decision"] != "act", "an unverified conflict still stops it"
    finally:
        warrant.VERIFY_CLAIMS = False


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print("ok", t.__name__)
    print(f"{len(tests)} passed")
