"""The person in the loop: a hold becomes a Slack card with buttons, and the click returns as a ruling on the decision record.

A clean commit sends nothing. One case gets one card, updated in place. Socket Mode means no public URL. A ruling to commit reads
billing again first, and a standing rule needs an owner, a scope and an expiry. Cards show roles and account IDs, not names; the names
stay in the record. Slack user ids stay in gitignored state, never in run logs.

    .venv/bin/python slack_card.py check
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse

import belief
import crm_mcp
import live_sources
import pii
import warrant

load_dotenv()
PENDING = {}    # trace id -> {"rec", "ts", "out"}
RULED = []


def client():
    return WebClient(os.environ["SLACK_BOT_TOKEN"])


def configured():
    return all(os.getenv(k) for k in ("SLACK_BOT_TOKEN", "SLACK_APP_TOKEN", "SLACK_CHANNEL"))


def header(rec):
    p = rec["action"]
    return f"*{p['agent']}* proposes a {p['type'].replace('_', ' ')} of *{p['amount']:g} {p['currency']}* on {p['account_id']}"


def button(text, action, value, style=None):
    b = {"type": "button", "text": {"type": "plain_text", "text": text}, "action_id": action, "value": value}
    return {**b, "style": style} if style else b


def mask(rec, text):
    """A channel can hold more people than a record should reach, so people show as roles and the account as its ID."""
    crm = next((b["value"] for b in rec["beliefs"] if b["source"] == "crm"), {})
    m = {p["name"]: p["role"] for p in crm_mcp.PEOPLE}
    m.update({crm[k]: v for k, v in (("csm", "the CSM"), ("name", rec["action"]["account_id"])) if crm.get(k)})
    return pii.scrub(warrant.swap(text or "", m))


def card(rec):
    key = rec["trace_id"]
    q = rec["question"] or {}
    doubt = belief.describe(rec["belief"]) if rec.get("belief", {}).get("top_doubt") else ""
    return [{"type": "section", "text": {"type": "mrkdwn", "text": f":raised_hand: *Held before commit*\n{header(rec)}" + (f"\n{doubt}" if doubt else "")}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Why:* {mask(rec, rec['discriminating_fact'])}\n*Question for {q.get('to_role', 'the owner')}:* {mask(rec, q.get('text', ''))}"}},
            {"type": "context", "elements": [{"type": "mrkdwn", "text": f"Rationale: {mask(rec, rec['action']['rationale'])}  |  record {rec['record_id']}  |  seeded test data"}]},
            {"type": "actions", "elements": [button("Keep held", "ruling_hold", key, "danger"), button("Commit as proposed", "ruling_commit", key)]}]


def ruled_card(rec, text, offer_rule=False):
    blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": header(rec)}}, {"type": "section", "text": {"type": "mrkdwn", "text": text}}]
    if offer_rule:
        blocks.append({"type": "actions", "elements": [button("Make this a standing rule, 30 days", "make_rule", rec["trace_id"])]})
    return blocks


def post_hold(rec, out):
    r = client().chat_postMessage(channel=os.environ["SLACK_CHANNEL"], text=f"Held: {mask(rec, rec['discriminating_fact'])}", blocks=card(rec))
    PENDING[rec["trace_id"]] = {"rec": rec, "ts": r["ts"], "channel": r["channel"], "out": out, "posted": datetime.now(timezone.utc)}
    return r["ts"]


def failed_check(rec):
    return next((c["name"] for c in rec["checks"] if c["result"] != "pass"), None)


def standing_rule(rec, now):
    p = rec["action"]
    return {"id": f"SR-{rec['trace_id'][:6]}", "pattern": {"action_type": p["type"], "check": failed_check(rec)}, "scope": {"max_amount": 1000, "currency": p["currency"]},
            "effect": "hold", "owner": "Billing analyst", "expires": (now + timedelta(days=30)).date().isoformat()}


def write_ruling(out, row):
    with open(f"{out}/rulings.jsonl", "a") as f:
        f.write(json.dumps(row) + "\n")
    RULED.append(row)


def stale_since(rec):
    """Billing as the gate saw it against billing now, for a person committing later."""
    before = next(b["value"] for b in rec["beliefs"] if b["source"] == "billing")
    now = live_sources.read_billing(rec["action"]["account_id"])
    return {k: v for k, v in before.items() if k not in ("synced_at", "source")} != {k: v for k, v in now.items() if k != "synced_at"}


def handle(action_id, key):
    """Apply one button click. Returns the ruling, or None for an unknown card."""
    item = PENDING.get(key)
    if not item:
        return None
    rec, now = item["rec"], datetime.now(timezone.utc)
    at = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    row = {"record_id": rec["record_id"], "trace_id": key, "case_id": rec["case_id"], "at": at, "ruled_by": "Billing analyst, via Slack"}
    if item.get("posted"):
        row["seconds_to_ruling"] = round((now - item["posted"]).total_seconds())
    if action_id == "ruling_hold":
        row.update(ruling="reject")
        rule_ok = bool(failed_check(rec)) and failed_check(rec) in ("prior_compensation", "boundary", "authority", "currency")
        text = ":no_entry: *Kept held* by the billing analyst. Nothing was written." + (" Should this pattern settle without a person next time?" if rule_ok else "")
        blocks = ruled_card(rec, text, offer_rule=rule_ok)
    elif action_id == "ruling_commit":
        if stale_since(rec):
            row.update(ruling="commit refused", note="billing changed since the check")
            blocks = ruled_card(rec, ":warning: *Not committed:* billing changed since the check, so this needs a fresh look.")
        else:
            try:
                ref = warrant.commit_credit(rec, rec["action"], ruled_by=row["ruled_by"])
                row.update(ruling="commit", credit_id=ref)
                blocks = ruled_card(rec, f":white_check_mark: *Committed by a person's ruling.* Credit {ref} on the Chargebee test site.")
            except PermissionError as e:
                row.update(ruling="commit refused", note=str(e))
                blocks = ruled_card(rec, f":warning: *Not committed:* {e}.")
    elif action_id == "make_rule":
        rule = standing_rule(rec, now)
        warrant.save_rule(rule)
        row.update(ruling="standing rule", rule=rule)
        blocks = ruled_card(rec, f":scroll: *Standing rule {rule['id']}:* {rule['pattern']['action_type']} failing {rule['pattern']['check']} holds with no question, up to {rule['scope']['max_amount']} {rule['scope']['currency']}. Owner {rule['owner']}, expires {rule['expires']}.")
    else:
        return None
    src = warrant.ruling_source(rec)
    if src and row["ruling"] in ("reject", "commit"):
        before = belief.reliability(src)
        row["belief_update"] = {"source": src, "before": round(before, 4), "after": round(belief.rule_on(src, row["ruling"] == "reject"), 4)}
    write_ruling(item["out"], row)
    client().chat_update(channel=item["channel"], ts=item["ts"], text=row["ruling"], blocks=blocks)
    return row


def listen():
    """Connect over Socket Mode and apply clicks until the process stops or the caller closes the client."""
    sock = SocketModeClient(app_token=os.environ["SLACK_APP_TOKEN"], web_client=client())

    def on_request(c, req: SocketModeRequest):
        c.send_socket_mode_response(SocketModeResponse(envelope_id=req.envelope_id))
        if req.type != "interactive":
            return
        for a in req.payload.get("actions", []):
            row = handle(a["action_id"], a["value"])
            print("ruling:", json.dumps({k: row[k] for k in ("case_id", "ruling")} if row else {"unknown card": a["value"][:8]}), flush=True)

    sock.socket_mode_request_listeners.append(on_request)
    sock.connect()
    return sock


if __name__ == "__main__" and sys.argv[1:] == ["check"]:
    print("bot ok:", client().auth_test()["ok"], "| channel set:", bool(os.getenv("SLACK_CHANNEL")))
