# When enterprise agents disagree: discovery memo

*31 Oct 2026, revision 2. One page in six-page-memo style, with the sizing model and sources in the appendix. Every figure has a source or is marked (assumed). "Warrant" is a working name; the product angle is set in the design stage.*

## The customer problem

Enterprises are building multi-agent systems on top of existing data, identity and policy estates. The typical production pattern, seen in financial services reference architectures, puts a coordinator agent in front of specialist agents (accounts, transactions, service), each calling its own MCP server, sharing a session store for inter-agent state, with authorization, PII redaction, an evaluation suite and observability around them. Every box in that picture has an owner except one: **what happens when two specialist agents reach different conclusions about the same customer, shipment or account.** Today the coordinator routes, it does not adjudicate. The disagreement is settled by mechanics: the last agent to write wins, the most confident agent acts, or the coordinator picks one. The action executes against the system of record, and nobody can later see that there was a dissent, what each side relied on, or which fact would have settled it. Berkeley's study of 1,642 multi-agent traces attributes about a third of failures to inter-agent misalignment (MAST, arXiv 2503.13657).

The same shape appears wherever enterprises are adding specialist agents:

- **Retail banking.** A service agent processes a change of address, then a cheque book request to the new address, while the transaction agent holds an open dispute and the accounts agent's KYC record is stale. Each agent is correct in its own lane; together they describe a pattern the bank would never approve.
- **Freight and logistics.** An exception agent tells the customer a container is released on the carrier's status while the customs broker still shows an exam hold, and a billing agent attributes the delay the opposite way. Freight forwarders and fleet platforms run exactly these multi-source, multi-party workflows.
- **Customer service on CRM platforms.** A refund agent approves a credit under the support policy while a risk agent has flagged the account and the account agent knows the enterprise contract overrides the standard terms. This is the workflow being automated on Salesforce, Zendesk and DevRev today.

In each case enterprise structure makes the conflict harder, not easier. Agents carry different RBAC scopes, so the agent that can act is not always the one that knows. Business hierarchies mean one view should outrank another (risk over service), and PII rules limit what can be shown to whom when the conflict is escalated.

**Customer.** The person accountable for one agent-run workflow: a contact-centre operations lead, a freight exceptions manager, a banking servicing head. **Buyer:** the head of the AI platform or the CIO, who owns the coordinator architecture and its risk sign-off.

## Why now

The share of organisations orchestrating multiple agents across workflows doubled from 9% to 18% in one quarter (KPMG AI Pulse, Q2 2026, via aggregator, to verify). Gartner expects over 40% of agentic AI projects to be cancelled by the end of 2027, partly over inadequate risk controls (Gartner, Jun 2025). Agent-native companies show where volume goes next: Spawn, ten people, lands about 108 changes an hour, resolves agent conflicts by letting whoever lands second reconcile, and needed AI judges because its founder woke to 700 open questions in a morning (Spawn CEO blog, 28 Oct 2026, pp. 3 to 10). **Spawn is the leading indicator, not the customer.** Enterprises will reach that conflict volume with far more regulation around them.

## The direction

A layer between specialist agents and the systems of record that, when agents disagree about the same object, keeps both positions explicit with evidence, provenance, age and the authority of the agent that holds them, then returns a bounded decision: **act** when the governing belief is current and uncontested, **gather** when one named fact would settle it, **hold** when only a person with the right authority can. Each decision leaves a record a later agent or person can read back, with PII redacted to the reader's scope, and each human ruling becomes an eval case. It fits the reference architecture as one new box beside authorization, rather than a replacement for the coordinator. For Dyssonance, this is the half of the thesis stated but not shown: whether a system "knows enough to act."

Three constraints, already clear: agents converge by **updating a belief state, not by debating longer** (more chatter is token cost, and Spawn found it grows with the square of agent count, p. 5); the output is a **bounded decision from a small classifier**, so cost is measured per resolved conflict, not per token; and it **escalates only real disagreements**, because users approve about 93% of Claude Code permission prompts (Anthropic, as cited by C. Lozano, 24 Sep 2026) and a gate that asks often gets rubber-stamped.

## Market

AI agents spending reaches $48B to $53B by 2030 across three independent estimates (MarketsandMarkets, Grand View, BCC). The budget this draws from is governance and observability: AI governance platforms reach about $1B by 2030 per Gartner and $15.8B per Forrester, a 15x gap from definitions, and LLM observability grows from about $2B to over $9B (Citi Ventures). **Bottom-up TAM about $1.4B in 2030 (assumed)**: 12,000 large enterprises running multi-agent workflows, each gating about 1M agent actions a month at $0.01 per gated action. **SAM about $0.6B (assumed)**: the three verticals above, where actions are irreversible or regulated and specialist agents already overlap. **SOM about $18M ARR in three years (assumed)**: 150 accounts at $120k. Gated-action volume is the weakest input; Gartner's $1B governance figure is the honest floor.

## Cost, revenue, and what customers will pay for

Avoiding the wrong irreversible action (a cheque book to a fraudster, a false release notice, a credit against contract) is real but **secondary value**: rare, counterfactual, and invisible on an invoice. The **tangible value is throughput**: the scarce resource in every one of these workflows is the person with authority, and the measurable win is raising the share of agent decisions that act safely without them, while cutting review minutes on the rest. Spawn's judges decided 64% of 11,372 questions in nine days and the founder ruled 27 times (p. 10). For a contact centre or exceptions desk, that is handle time and backlog, which buyers already measure. Lead with cost reduction and safe autonomy expansion; keep risk reduction as the argument for the security and compliance sign-off.

Customers pay for this problem today in four places: reviewers and Slack approval queues; hand-coded hard gates in front of payments and other irreversible actions; platform fees for agents inside one vendor's estate (Agentforce at $0.10 per action; Copilot Studio at $200 per 25,000 credits); and after-the-fact tracing (LangSmith at $39 per seat per month; Langfuse from $29 per month). Orchestrators coordinate agents only inside their own platform; governance tools such as Zenity, Credo and Lakera check one agent against a policy; observability shows the trace after the action ran. **No product found adjudicates between agents that disagree before the action reaches the system of record**; it exists only in research such as the MPAC protocol (arXiv 2604.09744). The product form is therefore a vendor-neutral layer at the tool or MCP boundary that respects the enterprise's existing IAM and RBAC, priced per gated decision with a platform minimum, with escalations surfaced where the accountable person already works.

## What we do not know yet

Whether accountable owners trust a hold enough to stop overriding it. How often specialist agents actually conflict in production today outside agent-native companies. Gated-action volume per enterprise, the input that moves TAM most. And whether CRM platforms build this natively inside their own estate, which would shrink the market to cross-vendor cases.

**Decision requested:** proceed to user and pain-point design across the three verticals, choose the product angle there, and use one workflow as the live demo with the others shown as use cases.

---

## Appendix A: sizing model (all inputs assumed unless sourced)

| Input | Value | Basis |
|---|---|---|
| Large enterprises, US and EU, over 1,000 staff | 20,000 | assumed, to verify |
| Share running multi-agent workflows by 2030 | 60% | assumed; 18% in Q2 2026 (KPMG) |
| Gated agent actions per enterprise per month | 1M | assumed; Spawn alone lands about 78k changes a month with 10 people |
| Price per gated action | $0.01 | assumed: 10% of Agentforce's $0.10 per action |
| TAM | 12,000 × 1M × 12 × $0.01 ≈ $1.4B | cross-check: about 9% to 15% of 2030 governance plus observability spend |
| SAM | 40%, the three verticals ≈ $0.6B | assumed |
| SOM, year 3 | 150 accounts × $120k ≈ $18M | assumed, about 3% of SAM |

## Appendix B: sources

- Spawn CEO blog, "How I Built the Most AI-Pilled Company in the World," Jacob (@jsnnsa), 28 Oct 2026 (local PDF).
- Financial services production RAG reference architecture (diagram supplied by the author; coordinator, specialist agents, MCP servers, shared session state).
- MAST, Why Do Multi-Agent LLM Systems Fail: https://arxiv.org/abs/2503.13657v2
- Gartner agentic AI cancellations: https://w.media/over-40-percent-of-agentic-ai-projects-could-face-the-axe-by-end-of-2027-gartner/
- KPMG AI Pulse: https://kpmg.com/us/en/media/news/q4-ai-pulse.html
- AI agents market: MarketsandMarkets https://prnewswire.co.uk/news-releases/ai-agents-market-worth-52-62-billion-by-2030---exclusive-report-by-marketsandmarkets-302435498.html ; Grand View https://www.prnewswire.co.uk/news-releases/ai-agents-market-size-to-hit-50-31-billion-by-2030-at-cagr-45-8---grand-view-research-inc-302447061.html ; BCC https://www.bccresearch.com/pressroom/ait/ai-agents-market-to-grow-433-annually
- Gartner AI governance platforms: https://www.gartner.com/en/newsroom/press-releases/2026-02-17-gartner-global-ai-regulations-fuel-billion-dollar-market-for-ai-governance-platforms
- Forrester AI governance spend: https://www.forrester.com/blogs/ai-governance-software-spend-will-see-30-cagr-from-2024-to-2030
- Citi Ventures LLM observability: https://www.citi.com/ventures/perspectives/opinion/llm-observability-next-major-play.html
- Pricing: Agentforce https://www.salesforce.com/agentforce/pricing/ ; Copilot Studio https://www.microsoft.com/en-us/microsoft-365-copilot/microsoft-copilot-studio/ ; LangSmith https://www.costbench.com/compare/arize-phoenix-vs-langsmith/ ; Langfuse https://latitude.so/blog/best-langfuse-alternatives
- Zenity Series C: https://www.businesswire.com/news/home/20260803963850/en/
- MPAC protocol: https://arxiv.org/pdf/2604.09744
- C. Lozano, "Classification Is Not New. So What?", Medium, 24 Sep 2026: https://lecharles.medium.com/classification-is-not-new-so-what-b14d2b8740a1

*Caveat: the market figures came from search snippets of press releases and aggregators; check the primary pages before any number goes on a slide.*
