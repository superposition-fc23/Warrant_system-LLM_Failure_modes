---
source: external-article-summary
author: Manoj Mohan, "Your MCP Server Doesn't Care Which LLM Is Calling", LinkedIn, 9 Sep 2026
---
# MCP gateway security: summary in our own words

MCP is a new API surface and is often secured the way APIs were a decade ago.
Three identity layers: the accountable human (SSO, OIDC), the agent (which model, prompt and version acted),
and the tool session (a short-lived, scoped credential the server validates).
One gateway in front of all MCP servers normalises identity so tools never see the model.
Five vulnerabilities to close first: tool poisoning via prompt injection, confused deputy, eavesdropping on the tool-call stream,
stale or overprivileged service accounts, and unbounded tool output. Audit logs should rebuild a whole session.
The authorization questions it asks: is this tool in scope for this user's task, and is this the right environment.
Both questions are about the principal. Neither asks whether the evidence behind the action is still true.
