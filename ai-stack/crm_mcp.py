"""Read-only MCP server over the synthetic systems of record: CRM, billing, contracts, risk, and the authority map.

Every tool returns records with their source and the time the source last changed (updated_at or synced_at), so the gate
can judge freshness. Nothing here writes. The world is set per eval case with load(); in a pilot each tool would wrap the
customer's real API (Salesforce or Zendesk, Stripe or Zuora, the contract repository, the risk service, the identity directory).

    .venv/bin/python crm_mcp.py            # serve over stdio for any MCP client
"""
import json

from mcp.server.mcpserver import MCPServer

server = MCPServer("warrant-systems-of-record", instructions="Read-only systems of record for Warrant. Nothing here writes.")
WORLD, PEOPLE, AUTHORITY = {}, [], {}


def load(world, people=None, authority=None):
    """Point every tool at one case's systems of record."""
    global WORLD, PEOPLE, AUTHORITY
    WORLD = world
    if people is not None:
        PEOPLE = people
    if authority is not None:
        AUTHORITY = authority


def _get(system, account_id):
    rec = WORLD.get(system, {})
    if rec.get("account_id") != account_id:
        return {"source": system, "error": f"no {system} record for {account_id}"}
    return {"source": system, **rec}


@server.tool(description="CRM account: name, tier, region, status, CSM, entitlements as the CRM records them.")
def crm_get_account(account_id: str) -> dict:
    return _get("crm", account_id)


@server.tool(description="Billing account: plan and seats billed, monthly fee, currency, invoices with status, credits already issued.")
def billing_get_account(account_id: str) -> dict:
    return _get("billing", account_id)


@server.tool(description="Contract documents for the account: order forms, amendments, renewals, email summaries, with signature status.")
def contracts_get_documents(account_id: str) -> dict:
    return _get("contracts", account_id)


@server.tool(description="Risk flags for the account (chargebacks, fraud reviews, collections) and when the risk feed last synced.")
def risk_get_flags(account_id: str) -> dict:
    return _get("risk", account_id)


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
