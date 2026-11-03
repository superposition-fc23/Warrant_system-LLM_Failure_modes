"""The belief layer: pure functions, no model calls. Sources are noisy, ageing observations of hidden facts, and act, gather or hold is
an expected-value choice. Hard checks in warrant.py still veto; nothing here can override them toward act.

P(safe) is the product over facts, assuming independence. Act if (1 - P(safe)) x stake is below the cost of delay. Otherwise gather the
fact whose re-read most reduces expected loss. Hold if no re-read can bring the decision under the threshold.
"""
import json
import math
import os
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
PRIORS = json.load(open(os.path.join(HERE, "belief_priors.json")))
STATE_PATH = "state/beliefs.json"
WINDOW_HOURS = {"crm": 6, "billing": 6, "risk": 24, "contracts": 720}
FACT_SOURCE = {"entitlement_matches": "crm", "no_prior_compensation": "billing", "credit_list_complete": "billing", "risk_clear": "risk", "evidence_agrees": "contracts", "contract_current": "contracts"}
MAX_WAIT = 600


def ts(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").timestamp()


def sources():
    if os.path.exists(STATE_PATH):
        return json.load(open(STATE_PATH))
    return json.loads(json.dumps(PRIORS["sources"]))


def reliability(source, table=None):
    b = (table or sources())[source]
    return b["alpha"] / (b["alpha"] + b["beta"])


def rule_on(source, kept_held):
    """A ruling is evidence about the source: keeping a hold says the doubted source was wrong; committing says it was right."""
    table = sources()
    table[source]["beta" if kept_held else "alpha"] += 1
    os.makedirs(os.path.dirname(STATE_PATH) or ".", exist_ok=True)
    json.dump(table, open(STATE_PATH, "w"), indent=1)
    return reliability(source, table)


def weight(age_hours, window_hours):
    """How much an observation of this age still counts: flat while fresh, 0.5 at the old window, falling after it."""
    if age_hours <= 0:
        return 1.0
    return 1 / (1 + (age_hours / window_hours) ** PRIORS["decay_steepness"])


def aged(r, age_hours, window_hours):
    w = weight(age_hours, window_hours)
    return w * r + (1 - w) * PRIORS["unread_fact_policy"]


def list_complete(seconds_since_change):
    """P(the credit list includes a write made this long ago)."""
    return 1 - math.exp(-max(seconds_since_change, 0) / PRIORS["credit_list_tau_seconds"])


def stake(p, billing):
    if p.get("amount") is not None:
        return abs(p["amount"])
    fee = billing.get("monthly_fee") or 0
    if p.get("pct") is not None:
        return fee * p["pct"] / 100
    if p.get("seats") is not None and billing.get("seats_billed"):
        return p["seats"] * fee / billing["seats_billed"]
    return 0.0


def delay_cost():
    return PRIORS["review_cost"] + PRIORS["other_delay_cost"]


def model_fact(samples, table=None):
    """P(evidence agrees) from k samples of the compare step. The share raising a material conflict is a likelihood input, not a verdict.
    Clean needs every readable sample to cite a contract record that code confirmed exists, so silence is not evidence."""
    if samples is None:
        return PRIORS["unread_fact_policy"]
    readable = [x for x in samples if "parse_error" not in x]
    raised = sum(1 for x in readable if x.get("raised"))
    if raised:
        return PRIORS["safe_given_share"][str(min(round(3 * raised / len(readable)), 3))]
    if not readable or not all(x.get("checked") for x in readable):
        return PRIORS["unread_fact_policy"]
    return reliability("contracts", table)


def facts(sources_read, now, samples=None, table=None):
    """Every fact the checks test, as a probability."""
    table = table or sources()
    t = ts(now)
    age = {}
    for name, rec in sources_read.items():
        seen = rec.get("synced_at") or rec.get("updated_at")
        age[name] = (t - ts(seen)) / 3600 if seen else 1e6
    billing = sources_read.get("billing", {})
    changed = billing.get("last_changed") or billing.get("updated_at")
    out = {"entitlement_matches": aged(reliability("crm", table), age.get("crm", 1e6), WINDOW_HOURS["crm"]),
           "no_prior_compensation": aged(reliability("billing", table), age.get("billing", 1e6), WINDOW_HOURS["billing"]),
           "credit_list_complete": list_complete(t - ts(changed)) if changed else PRIORS["unread_fact_policy"],
           "risk_clear": aged(reliability("risk", table), age.get("risk", 1e6), WINDOW_HOURS["risk"]),
           "evidence_agrees": model_fact(samples, table),
           "contract_current": aged(1.0, age.get("contracts", 1e6), WINDOW_HOURS["contracts"])}
    return out


def p_safe(f):
    return math.prod(f.values())


def after_reread(name, f, table):
    """What this fact would be worth after a fresh read, or None if reading again cannot help."""
    if name == "evidence_agrees":
        return reliability("contracts", table) if f[name] == PRIORS["unread_fact_policy"] else None    # unverified can be asked again; a raised conflict cannot
    if name == "contract_current":
        return 1.0
    if name == "credit_list_complete":
        return 1 - (1 - f[name]) * math.exp(-MAX_WAIT / PRIORS["credit_list_tau_seconds"])
    return reliability(FACT_SOURCE[name], table)


def decide(f, at_stake, table=None, cost=None):
    """Returns the decision and what drove it. Hard vetoes are applied by the caller, before this."""
    table = table or sources()
    cost = delay_cost() if cost is None else cost
    p = p_safe(f)
    loss = (1 - p) * at_stake
    top = min(f, key=f.get)
    out = {"p_safe": round(p, 4), "expected_loss": round(loss, 2), "cost_of_delay": round(cost, 2), "stake": round(at_stake, 2), "top_doubt": top, "top_doubt_source": FACT_SOURCE[top],
           "facts": {k: round(v, 4) for k, v in f.items()}, "gather": None}
    if loss < cost:
        return {**out, "decision": "act"}
    best, best_loss = None, loss
    for name in f:
        v = after_reread(name, f, table)
        if v is None or v <= f[name]:
            continue
        new = (1 - p_safe({**f, name: v})) * at_stake
        if new < best_loss:
            best, best_loss = name, new
    if best and best_loss < cost:
        wait = next((t for t in range(15, MAX_WAIT + 1, 15) if (1 - p_safe({**f, best: 1 - (1 - f[best]) * math.exp(-t / PRIORS["credit_list_tau_seconds"])})) * at_stake < cost), MAX_WAIT) if best == "credit_list_complete" else 0
        return {**out, "decision": "gather", "gather": best, "wait_seconds": wait, "loss_after_gather": round(best_loss, 2)}
    return {**out, "decision": "hold"}


def assume_clean(f, table=None):
    """The facts if the model were to find nothing: the most it could add."""
    return {**f, "evidence_agrees": reliability("contracts", table or sources())}


def settle_before_model(f, at_stake, table=None, cost=None):
    """What can be said before any model call. "act": safe enough unread. "gather": a re-read must come first, whatever the model says.
    "stake": too much at stake even if the model finds nothing, and no re-read helps. None: the model's answer can change the decision."""
    table = table or sources()
    cost = delay_cost() if cost is None else cost
    if (1 - p_safe(f)) * at_stake < cost:
        return "act"
    best = assume_clean(f, table)
    if (1 - p_safe(best)) * at_stake < cost:
        return None
    return "gather" if decide(best, at_stake, table, cost)["decision"] == "gather" else "stake"


DOUBT = {"credit_list_complete": "the credit list may not yet show a recent write", "no_prior_compensation": "billing is too old to rule out an earlier credit",
         "risk_clear": "the risk feed is too old to rule out an open flag", "entitlement_matches": "the CRM is too old to confirm the entitlement", "evidence_agrees": "the contract comparison raised doubt or could not show what it checked", "contract_current": "the contract record is too old to rely on"}


def describe(d):
    """One line for a person: the probability, the main doubt, and the next step."""
    line = f"P(safe) {d['p_safe']:.3f}. Main doubt: {DOUBT[d['top_doubt']]}."
    if d.get("gather") == "credit_list_complete":
        return f"{line} Re-read in {d.get('wait_seconds', 0)} s."
    if d.get("gather") == "evidence_agrees":
        return f"{line} Run the comparison again."
    if d.get("gather"):
        return f"{line} Re-read {FACT_SOURCE[d['gather']]}."
    return line
