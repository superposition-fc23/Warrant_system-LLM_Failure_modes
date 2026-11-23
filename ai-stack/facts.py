"""Neutral numbers code can compute before the model reads anything (arm A+verify+facts).

The model was slipping on arithmetic ("300 exceeds 300", "5% of 6000 is 305"). These lines give it the numbers instead of asking it
to work them out. They state quantities only, never a verdict: whether 300 is too much is still the model's reading of the contract,
and code's checks.
"""
import re
from datetime import datetime

_PCT = re.compile(r"(\d+(?:\.\d+)?)\s*%")


def _num(x):
    return f"{x:g}" if isinstance(x, float) and x != int(x) else f"{int(round(x))}"


def _days(a, b):
    return (datetime.fromisoformat(b[:10]) - datetime.fromisoformat(a[:10])).days


def compute(proposal, sources, now):
    """A list of short lines of computed facts for one case."""
    out = []
    b = sources.get("billing") or {}
    fee, cur = b.get("monthly_fee"), b.get("currency", "")
    amt = proposal.get("amount")
    kind = proposal.get("type", "")
    if fee:
        if amt is not None and kind == "service_credit":    # only a credit is measured against the fee; a refund is measured against its invoice
            out.append(f"The proposed {_num(amt)} {proposal.get('currency', '')} is {_num(round(100 * amt / fee, 2))}% of the monthly fee of {_num(fee)} {cur}.")
        pcts = sorted({float(p) for d in (sources.get("contracts") or {}).get("documents", []) for p in _PCT.findall(d.get("text", "")) if float(p) <= 50}, reverse=True)
        for p in pcts:
            out.append(f"{_num(p)}% of the monthly fee = {_num(round(p / 100 * fee, 2))} {cur}.")
        if proposal.get("pct") is not None:
            out.append(f"The proposed {_num(proposal['pct'])}% of the monthly fee = {_num(round(proposal['pct'] / 100 * fee, 2))} {cur}.")
    for inv in b.get("invoices", []):
        if inv.get("invoice_date"):
            out.append(f"Invoice {inv['id']} issued {inv['invoice_date']}: {_days(inv['invoice_date'], now)} days before now; amount {_num(inv.get('amount', 0))} {inv.get('currency', cur)}.")
    if amt is not None and kind == "refund":
        out.append(f"The proposed refund is {_num(amt)} {proposal.get('currency', '')}.")
    for d in (sources.get("contracts") or {}).get("documents", []):
        if d.get("effective"):
            out.append(f"Document {d['id']} effective {d['effective']}: {_days(d['effective'], now)} days before now.")
    crm_seats = ((sources.get("crm") or {}).get("entitlements") or {}).get("seats")
    if crm_seats is not None or b.get("seats_billed") is not None:
        extra = f", proposal adds {proposal['seats']} (CRM after the grant: {crm_seats + proposal['seats']})" if proposal.get("seats") is not None and crm_seats is not None else ""
        out.append(f"Seats: CRM {crm_seats}, billing {b.get('seats_billed')}{extra}.")
    credits = b.get("credits", [])
    if credits:
        total = sum(c.get("amount", 0) for c in credits)
        out.append(f"Prior credits on the account: {len(credits)}, totalling {_num(total)} {cur}, for incidents {', '.join(sorted({str(c.get('incident_id')) for c in credits}))}.")
    else:
        out.append("Prior credits on the account: none listed in billing.")
    return out
