"""Read-only MCP server over the synthetic systems of record: CRM, billing, contracts, risk, and the authority map.

Every tool returns records with their source and the time the source last changed (updated_at or synced_at), so the gate
can judge freshness. Nothing here writes. The world is set per eval case with load(). With LIVE set, CRM and billing come from
the HubSpot and Chargebee test accounts through live_sources.py; contracts, risk and authority stay local. FAULTS injects the
failures real systems have, so the gate's handling can be tested: timeout, error, malformed or stale, per source.

    .venv/bin/python crm_mcp.py            # serve over stdio for any MCP client
"""
import asyncio
import json
from datetime import datetime, timedelta, timezone

import live_sources
from mcp.server.mcpserver import MCPServer

server = MCPServer("warrant-systems-of-record", instructions="Read-only systems of record for Warrant. Nothing here writes.")
WORLD, PEOPLE, AUTHORITY = {}, [], {}
LIVE = False
FAULTS = {}
READERS = {"crm": live_sources.read_crm, "billing": live_sources.read_billing}


def load(world, people=None, authority=None):
    """Point every tool at one case's systems of record."""
    global WORLD, PEOPLE, AUTHORITY
    WORLD = world
    if people is not None:
        PEOPLE = people
    if authority is not None:
        AUTHORITY = authority


async def _get(system, account_id):
    fault = FAULTS.get(system)
    if fault == "timeout":
        await asyncio.sleep(60)
    if fault == "error":
        return {"source": system, "error": f"{system} returned 503"}
    if LIVE and system in READERS:
        try:
            rec = await asyncio.to_thread(READERS[system], account_id)
        except Exception as e:    # any read failure becomes evidence for the gate, never a crash and never an act
            return {"source": system, "error": str(e)[:200]}
    else:
        rec = WORLD.get(system, {})
    if rec.get("account_id") != account_id:
        return {"source": system, "error": f"no {system} record for {account_id}"}
    if fault == "malformed":
        return {"source": system, "account_id": account_id}
    if fault == "stale":
        old = datetime.now(timezone.utc) - timedelta(days=30) if LIVE else datetime(2026, 1, 1, tzinfo=timezone.utc)
        rec = {**rec, "synced_at": old.strftime("%Y-%m-%dT%H:%M:%SZ")}
    return {"source": system, **rec}


@server.tool(description="CRM account: name, tier, region, status, CSM, entitlements as the CRM records them.")
async def crm_get_account(account_id: str) -> dict:
    return await _get("crm", account_id)


@server.tool(description="Billing account: plan and seats billed, monthly fee, currency, invoices with status, credits already issued.")
async def billing_get_account(account_id: str) -> dict:
    return await _get("billing", account_id)


@server.tool(description="Contract documents for the account: order forms, amendments, renewals, email summaries, with signature status.")
async def contracts_get_documents(account_id: str) -> dict:
    return await _get("contracts", account_id)


@server.tool(description="Risk flags for the account (chargebacks, fraud reviews, collections) and when the risk feed last synced.")
async def risk_get_flags(account_id: str) -> dict:
    return await _get("risk", account_id)


@server.tool(description="Who may commit a money action of this type alone, by amount, percent or seats, and who is active.")
def authority_get_limits(action_type: str) -> dict:
    return {"source": "authority", "action_type": action_type, "limits": AUTHORITY.get(action_type, []), "people": PEOPLE}


TOOLS = {"crm": "crm_get_account", "billing": "billing_get_account", "contracts": "contracts_get_documents", "risk": "risk_get_flags"}


def parse(result):
    """CallToolResult -> dict."""
    if getattr(result, "structured_content", None):
        sc = result.structured_content
        return sc.get("result", sc)
    return json.loads(result.content[0].text)


if __name__ == "__main__":
    server.run()
