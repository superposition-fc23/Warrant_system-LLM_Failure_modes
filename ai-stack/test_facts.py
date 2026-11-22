"""Arm A+verify+facts, written before the code: code computes neutral numbers and the prompt carries them. No conclusions, no model calls.

    .venv/bin/python test_facts.py
"""
import json

import facts
import warrant

D = json.load(open("evals/crm_cases.json"))
CASES = {c["id"]: c for c in D["cases"]}


def lines(cid):
    c = CASES[cid]
    return facts.compute(c["proposal"], c["world"], D["now"])


def test_ct01_numbers_are_computed_not_judged():
    text = "\n".join(lines("CT-01"))
    assert "300 USD is 5% of the monthly fee of 6000 USD" in text, text
    assert "10% of the monthly fee = 600 USD" in text and "5% of the monthly fee = 300 USD" in text, text
    assert "INV-20011 issued 2026-10-20: 12 days before now" in text, text
    assert "Seats: CRM 200, billing 200" in text, text
    assert "Prior credits on the account: none" in text, text


def test_facts_fit_the_action_type():
    assert not any("monthly fee of" in l for l in lines("CT-10")), "a refund is not measured against the fee"
    assert any("The proposed refund is 300 EUR" in l for l in lines("CT-10"))
    assert any("CRM after the grant: 220" in l for l in lines("CT-04")), lines("CT-04")


def test_no_verdicts_in_the_facts():
    for cid in ("CT-01", "PL-02", "CT-10", "PL-06"):
        text = " ".join(lines(cid)).lower()
        for word in ("exceed", "within", "allowed", "violat", "breach of", "conflict", "should"):
            assert word not in text, (cid, word)


def test_uptime_style_percentages_are_not_applied_to_the_fee():
    assert not any("99.9%" in l for l in lines("CT-01"))


def test_prompt_carries_facts_only_when_switched_on():
    c = CASES["CT-01"]
    warrant.COMPUTED_FACTS = False
    assert warrant.facts_block(c["proposal"], c["world"], D["now"]) == ""
    warrant.COMPUTED_FACTS = True
    block = warrant.facts_block(c["proposal"], c["world"], D["now"])
    assert block.startswith("\n\nComputed by code") and "6000" in block
    warrant.COMPUTED_FACTS = False


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print("ok", t.__name__)
    print(f"{len(tests)} passed")
