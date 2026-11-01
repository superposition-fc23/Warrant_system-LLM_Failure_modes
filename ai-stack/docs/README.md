# Synthetic corpus for the live case (all fictional)

Every company, person, number and policy here is invented for the case. Nothing is real data from any company.

Each file starts with front matter: source, tenant, version, effective_from, effective_to, observed_at, supersedes.
Reference date for "now" in this corpus: 2026-10-30. The defects are planted on purpose and listed in ../evals/planted_defects.json,
so evals need no labelling: did the system catch the one we planted.

| Folder | Idea | Planted defects |
|---|---|---|
| 01-msp-tenants | Multi-tenant policy contamination | Two clients with contradicting remote-wipe policies |
| 02-rmm-device-state | Auto-remediation on stale device state | Monitoring alert older than its validity window, contradicted by ticket and change calendar |
| 03-product-versions | Copilot answering from a deprecated version | v4.2 doc better written than the v4.3 doc that supersedes it |
| 04-05-sales-comp | What am I owed, plan-change blast radius | CRM closed-won vs finance not recognised; mid-period plan amendment |
| 06-inventory | Replenishment on contradicted inventory | POS depletion vs cycle count; lead time stale after disruption |
| 07-vehicle-condition | Listing on contested condition | Two inspections disagree; older one is better qualified |
| 08-09-freight | Exception agent on contradicted status; charge explanation | Broker, carrier and terminal disagree; storage days not supported by events |
| 10-procurement | Approving against terms that moved | Amendment supersedes base clause; approval authority stale after reorg |
| s1-mcp-gateway | Belief-conditioned authorization at the MCP gateway | Valid credentials, in-scope tool, expired belief |
