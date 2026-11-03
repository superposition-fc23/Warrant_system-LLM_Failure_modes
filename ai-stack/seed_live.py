"""Seed the demo accounts from evals/crm_cases.json into the HubSpot and Chargebee test accounts. Safe to rerun.

Refuses anything but a HubSpot developer test account and a Chargebee test key. All names and numbers are fictional.

    .venv/bin/python seed_live.py
"""
import json
import sys

import live_sources as L

DEMO = ["CT-01", "CT-03", "CT-09", "PL-02", "PL-03", "PL-04"]
POOL = 24
PRICE_ID, SEAT_PRICE = "warrant-business-usd-monthly", 30
PROPS = {"warrant_account_id": "Warrant account id", "warrant_tier": "Warrant tier", "warrant_seats": "Warrant seats entitled",
         "warrant_plan": "Warrant plan", "warrant_csm": "Warrant CSM", "warrant_region": "Warrant region"}


def exists(fn):
    try:
        fn()
        return True
    except L.SourceError as e:
        if " 404" in str(e) or "resource_not_found" in str(e):
            return False
        raise


def seed_catalog():
    if not exists(lambda: L.chargebee("GET", "/item_families/warrant")):
        L.chargebee("POST", "/item_families", data={"id": "warrant", "name": "Warrant demo"})
    if not exists(lambda: L.chargebee("GET", "/items/warrant-business")):
        L.chargebee("POST", "/items", data={"id": "warrant-business", "name": "Warrant demo Business", "type": "plan", "item_family_id": "warrant"})
    if not exists(lambda: L.chargebee("GET", f"/item_prices/{PRICE_ID}")):
        L.chargebee("POST", "/item_prices", data={"id": PRICE_ID, "name": "Warrant demo Business monthly", "item_id": "warrant-business", "pricing_model": "per_unit",
                                                  "price": SEAT_PRICE * 100, "currency_code": "USD", "period": 1, "period_unit": "month"})


def seed_props():
    have = {p["name"] for p in L.hubspot("GET", "/crm/v3/properties/companies")["results"]}
    for name, label in PROPS.items():
        if name not in have:
            L.hubspot("POST", "/crm/v3/properties/companies", json={"name": name, "label": label, "groupName": "companyinformation", "type": "string", "fieldType": "text"})


def pool_case(c, n):
    """Copies of the clean control under a fresh account, so each live agent demo starts with no credits on file."""
    acc = f"ACC-30{n:02d}"
    return json.loads(json.dumps(c).replace("ACC-2001", acc).replace("OF-2001", f"OF-30{n:02d}"))


def seed_case(c):
    crm, bill = c["world"]["crm"], c["world"]["billing"]
    acc = crm["account_id"]
    props = {"name": crm["name"], "warrant_account_id": acc, "warrant_tier": crm["tier"], "warrant_seats": str(crm["entitlements"]["seats"]),
             "warrant_plan": crm["entitlements"]["plan"], "warrant_csm": crm["csm"], "warrant_region": crm["region"]}
    found = L.find_company(acc)
    if found:
        L.hubspot("PATCH", f"/crm/v3/objects/companies/{found['id']}", json={"properties": props})
    else:
        L.hubspot("POST", "/crm/v3/objects/companies", json={"properties": props})

    if not exists(lambda: L.chargebee("GET", f"/customers/{acc}")):
        L.chargebee("POST", "/customers", data={"id": acc, "company": crm["name"], "auto_collection": "off"})
        L.chargebee("POST", f"/customers/{acc}/subscription_for_items", data={"subscription_items[item_price_id][0]": PRICE_ID,
                                                                             "subscription_items[quantity][0]": bill["seats_billed"]})
        for i in L.chargebee("GET", "/invoices", {"customer_id[is]": acc, "limit": 1})["list"]:
            inv = i["invoice"]
            L.chargebee("POST", f"/invoices/{inv['id']}/record_payment", data={"transaction[amount]": inv["amount_due"], "transaction[payment_method]": "bank_transfer"})
    if bill["credits"] and not L.chargebee("GET", "/promotional_credits", {"customer_id[is]": acc, "type[is]": "increment", "limit": 1})["list"]:
        for x in bill["credits"]:
            L.add_credit(acc, x["amount"], x["incident_id"], x["issued_by"])
    return acc


if __name__ == "__main__":
    if not L.check():
        sys.exit("HubSpot is not a developer test account; nothing was written")
    seed_props()
    seed_catalog()
    cases = {c["id"]: c for c in json.load(open("evals/crm_cases.json"))["cases"]}
    for cid in DEMO:
        print(cid, seed_case(cases[cid]), flush=True)
    for n in range(1, POOL + 1):
        print("pool", seed_case(pool_case(cases["CT-01"], n)), flush=True)
