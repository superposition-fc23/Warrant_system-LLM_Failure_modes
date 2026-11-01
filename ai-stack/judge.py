"""LLM-as-judge over the planted-defect set: runs the agent on every case and scores the decision.

Ground truth exists by construction (evals/planted_defects.json), so the judge only has to grade two things:
did the agent make the expected decision, and did it name the discriminating fact. The decision check is
deterministic; the "named the fact" check uses a judge model when a key is set, else keyword overlap.

    .venv/bin/python judge.py                    # all cases
    .venv/bin/python judge.py --judge opus-5.5   # pick the judge model

Reports: catch rate on planted defects (leading), over-hold rate on clean controls (counter), fact-named rate.
"""
import json
import re
import sys

from agents import run
from llm import ask, has_key

JUDGE_SYSTEM = ("You grade an AI gate's reasoning. Given the planted defect, the discriminating fact, and the gate's "
                "stated reasons, return JSON: named_fact (true if the reasons identify the same fact, in any wording), "
                "rationale (one sentence). Do not reward reasons that are merely cautious. Return only JSON.")


def named_fact(case, reasons, judge_model):
    text = " ".join(reasons)
    if has_key(judge_model):
        out = ask(judge_model, f"Planted defect: {case['defect']}\nDiscriminating fact: {case['discriminating_fact']}\n"
                               f"Gate reasons: {text}", system=JUDGE_SYSTEM, effort="low")
        data = json.loads(re.search(r"\{.*\}", out, re.S).group())
        return bool(data.get("named_fact")), data.get("rationale", "")
    words = {w for w in re.findall(r"[a-z0-9-]{4,}", case["discriminating_fact"].lower())}
    overlap = words & set(re.findall(r"[a-z0-9-]{4,}", text.lower()))
    return len(overlap) >= 2, f"offline keyword overlap: {sorted(overlap)[:5]}"


if __name__ == "__main__":
    judge_model = sys.argv[sys.argv.index("--judge") + 1] if "--judge" in sys.argv else "sonnet-5.5"
    cases = json.load(open("evals/planted_defects.json"))["cases"]
    rows, caught, planted, over_held, controls, named = [], 0, 0, 0, 0, 0
    for c in cases:
        r = run(c["action"], c["tenant"])
        ok = r["decision"] == c["expected"]
        fact, why = named_fact(c, r.get("reasons", []), judge_model) if c["expected"] == "hold" else (None, "")
        if c["expected"] == "hold":
            planted += 1; caught += ok; named += bool(fact)
        else:
            controls += 1; over_held += not ok
        rows.append((c["id"], c["defect"], c["expected"], r["decision"], "PASS" if ok else "FAIL", fact, why))
    print(f"{'id':8} {'defect':38} {'exp':5} {'got':5} {'':5} named_fact")
    for row in rows:
        print(f"{row[0]:8} {row[1]:38} {row[2]:5} {row[3]:5} {row[4]:5} {row[5]}")
    print(f"\ncatch rate (planted defects held): {caught}/{planted}")
    print(f"discriminating fact named:         {named}/{planted}")
    print(f"over-hold rate on clean controls:  {over_held}/{controls}   <- counter-metric")
