---
source: gateway-policy
version: 1
effective_from: 2026-10-01
---
# Gateway policy (synthetic)

Gate 1, principal: human identity valid, agent identity registered, tool session token unexpired and scoped to the tool.
Gate 2, scope: tool is in scope for the task and the environment matches.
Gate 3, warrant: the governing belief for a write action is current (inside its validity window), uncontested
(no open contradicting source), and in scope for the tenant of the target record. Any gate 3 failure turns the write into a draft
and names the belief and the discriminating fact that would resolve it.
Write actions listed as high impact: remote wipe, service restart, purchase order approval, commission payout, customer credit, listing publish.
