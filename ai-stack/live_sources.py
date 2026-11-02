"""Live systems of record for Warrant: HubSpot as the CRM and Chargebee as billing, test accounts only.

read_crm() and read_billing() return the same shape the fixtures use, so the gate cannot tell the difference except through
what real systems add: latency, rate limits, timeouts and schema drift. Contracts and risk stay local fixtures, labelled.
A read is current as of the read, so synced_at is the read time and last_changed is what the system reports.

    .venv/bin/python live_sources.py check     # confirm both keys reach test accounts
"""
import json
import os
import sys
from datetime import datetime, timezone

import httpx
from dotenv import load_dotenv

load_dotenv()
TIMEOUT = 5.0


class SourceError(Exception):
    pass


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def epoch(sec):
    return datetime.fromtimestamp(sec, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def configured():
    return all(os.getenv(k) for k in ("HUBSPOT_TOKEN", "CHARGEBEE_SITE", "CHARGEBEE_API_KEY"))


# HubSpot
def hubspot(method, path, **kw):
    r = httpx.request(method, f"https://api.hubapi.com{path}", headers={"Authorization": f"Bearer {os.environ['HUBSPOT_TOKEN']}"}, timeout=TIMEOUT, **kw)
    if r.status_code >= 400:
        raise SourceError(f"hubspot {r.status_code}: {r.text[:200]}")
    return r.json() if r.content else {}


CRM_PROPS = ["name", "warrant_account_id", "warrant_tier", "warrant_seats", "warrant_plan", "warrant_csm", "warrant_region", "hs_lastmodifieddate"]


def find_company(account_id):
    d = hubspot("POST", "/crm/v3/objects/companies/search", json={
        "filterGroups": [{"filters": [{"propertyName": "warrant_account_id", "operator": "EQ", "value": account_id}]}], "properties": CRM_PROPS, "limit": 1})
    return d["results"][0] if d.get("results") else None


def read_crm(account_id):
    c = find_company(account_id)
    if not c:
        raise SourceError(f"no HubSpot company for {account_id}")
    p = c["properties"]
    return {"account_id": account_id, "name": p["name"], "tier": p["warrant_tier"], "region": p["warrant_region"], "status": "active", "csm": p["warrant_csm"],
            "entitlements": {"seats": int(p["warrant_seats"]), "plan": p["warrant_plan"]}, "synced_at": now_iso(), "last_changed": p["hs_lastmodifieddate"],
            "record_url_id": c["id"]}


# Chargebee
def chargebee_site():
    site = os.environ["CHARGEBEE_SITE"].replace("https://", "").replace("http://", "").split(".")[0].strip()
    return site if site.endswith("-test") else f"{site}-test"


def chargebee(method, path, params=None, data=None):
    key = os.environ["CHARGEBEE_API_KEY"].strip()
    if not key.startswith("test_"):
        raise SourceError("refusing a Chargebee key that is not a test key")
    r = httpx.request(method, f"https://{chargebee_site()}.chargebee.com/api/v2{path}", auth=(key, ""), params=params, data=data, timeout=TIMEOUT)
    if r.status_code >= 400:
        raise SourceError(f"chargebee {r.status_code}: {r.json().get('api_error_code', r.text[:120])}")
    return r.json()


def parse_credit(desc):
    """Promotional credits carry the incident and issuer in the description: 'INC-1 by cs-agent'."""
    incident, _, by = (desc or "").partition(" by ")
    return incident, by


def read_billing(account_id):
    cust = chargebee("GET", f"/customers/{account_id}")["customer"]
    subs = chargebee("GET", "/subscriptions", {"customer_id[is]": account_id, "status[is]": "active", "limit": 1})["list"]
    if not subs:
        raise SourceError(f"no active Chargebee subscription for {account_id}")
    sub = subs[0]["subscription"]
    item = sub["subscription_items"][0]
    invoices = chargebee("GET", "/invoices", {"customer_id[is]": account_id, "limit": 5, "sort_by[desc]": "date"})["list"]
    credits = chargebee("GET", "/promotional_credits", {"customer_id[is]": account_id, "type[is]": "increment", "limit": 10})["list"]
    def credit(c):
        incident, by = parse_credit(c["promotional_credit"].get("description"))
        return {"id": c["promotional_credit"]["id"], "amount": c["promotional_credit"]["amount"] / 100, "currency": c["promotional_credit"]["currency_code"],
                "incident_id": incident, "issued_by": by, "issued_at": epoch(c["promotional_credit"]["created_at"])}
    return {"account_id": account_id, "plan_billed": "Business", "seats_billed": item["quantity"], "monthly_fee": item["amount"] / 100,
            "currency": sub["currency_code"],
            "invoices": [{"id": i["invoice"]["id"], "amount": i["invoice"]["total"] / 100, "currency": i["invoice"]["currency_code"],
                          "status": i["invoice"]["status"], "date": epoch(i["invoice"]["date"])[:10],
                          "lines": [{"item": l["description"], "amount": l["amount"] / 100} for l in i["invoice"].get("line_items", [])]} for i in invoices],
            "credits": [credit(c) for c in credits], "synced_at": now_iso(), "last_changed": epoch(cust["updated_at"])}


def add_credit(account_id, amount, incident_id, issued_by):
    """The one write Warrant makes, and only after an act decision. Test site only."""
    d = chargebee("POST", "/promotional_credits/add", data={"customer_id": account_id, "amount": round(amount * 100),
                                                             "description": f"{incident_id} by {issued_by}", "credit_type": "general"})
    return d["promotional_credit"]["id"]


def check():
    acct = hubspot("GET", "/account-info/v3/details")
    print("hubspot account type:", acct.get("accountType"), "| chargebee test site:", chargebee_site().endswith("-test"),
          "| customers:", len(chargebee("GET", "/customers", {"limit": 5})["list"]))
    return acct.get("accountType") == "DEVELOPER_TEST"


if __name__ == "__main__" and sys.argv[1:] == ["check"]:
    print("ok" if check() else "not a test account")
