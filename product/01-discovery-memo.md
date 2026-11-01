# When enterprise agents disagree: discovery memo

*31 Oct 2026, revision 3, after a devil's advocate review. One page in six-page-memo style, with the sizing model, the review and sources in the appendix. Every figure has a source or is marked (assumed). "Warrant" is a working name; the product angle is set in the design stage.*

## The customer problem

Enterprises are adding specialist agents on top of existing data, identity and policy estates. A typical production pattern, here a financial services reference architecture, puts a coordinator agent in front of accounts, transaction and service agents, each calling its own MCP server and sharing a session store, with authorization, PII redaction, an evaluation suite and observability around them. Every box has an owner except one: **the moment an agent is about to commit an action on a belief that is contested or stale.** The most visible and fastest-growing source of contest is other agents. When two specialists reach different conclusions about the same customer, shipment or account, the coordinator routes rather than adjudicates, and the disagreement is settled by mechanics: last write wins, the most confident agent acts, or the coordinator picks. The other sources are quieter: an observation that expired, a rule that was amended. Either way the action executes, and nobody can later see what it relied on or which fact would have changed it.

**Why a rules table does not fix it.** Each vertical already has precedence rules, and each breaks on age, partial evidence and rules that change:

| Vertical | The conflict | The rule that exists | Where the rule fails |
|---|---|---|---|
| Retail banking | Service agent sends a cheque book to a just-changed address while the transaction agent holds an open dispute and KYC is stale | Account-takeover rule: address change plus cheque book blocks | It fires on every genuine house move, and it cannot tell that the KYC refresh completed an hour ago in another system |
| Freight | Exception agent tells the customer a container is released on carrier status while the broker shows an exam hold | Customs status outranks carrier status | It cannot express that the broker's hold is itself six hours old, or that the exam finished and was not yet posted |
| CRM customer service | Refund agent approves a credit while a risk agent has flagged the account and the contract overrides standard terms | Risk outranks service | It cannot tell that the risk flag was cleared yesterday, or that a contract amendment changed the terms |

Enterprise structure makes this harder. RBAC means the agent that can act is often not the one that knows. Hierarchy means some views outrank others, but only while they are current. PII rules limit what an escalation may show to whom.

**User and symptom.** The person accountable for one agent-run workflow, for example a contact-centre operations lead, a freight exceptions manager or a banking servicing head. They do not see conflicts; they see the symptoms they already track: **reversed actions, refund clawbacks, false status notices, and an escalation backlog.** The buyer is the head of the AI platform, who pays from a platform budget while the value lands in the operations P&L, so the business case has to be written in the operations owner's numbers.

## Why now

The share of organisations orchestrating multiple agents across workflows rose from 9% to 18% in one quarter (KPMG AI Pulse, to verify against the primary). Gartner expects over 40% of agentic AI projects to be cancelled by end 2027, partly over inadequate risk controls (Jun 2025). Agents are getting identities and a place in the org chart: Microsoft issues them directory identities (Entra Agent ID, May 2025) and Workday registers them beside human workers (Agent System of Record, Sep 2025). Agent-first companies such as Spawn and Block are colour, not evidence of the enterprise problem: they show where action volume is heading, not that enterprises have this pain today.

## The direction

A layer between agents and the systems of record that, before a high-impact write, reads the belief state behind it (evidence, provenance, age, and the authority of each agent holding a view) and returns a bounded decision: **act** when the governing belief is current and uncontested, **gather** when one named fact would settle it, **hold** when only a person with the right authority can. Each decision leaves a record, PII-redacted to the reader's scope, and each human ruling becomes an eval case. **It is not a harness**: it adds no prompts, workflow graph or routing rules; it reads state the agents already produce and decides only whether that state warrants the action. For Dyssonance this is the half of the thesis stated but not shown, whether a system "knows enough to act."

Five constraints: converge by **updating a belief state, not by debating longer** (Spawn found agent chatter grows with the square of agent count, p. 5); output a **bounded decision from a small classifier**, costed per resolved conflict, not per token; **escalate only real disagreements**, because users approve about 93% of Claude Code permission prompts (Anthropic, as cited by C. Lozano, 24 Sep 2026); make **hold a first-class output and test it for bias**, because KillBench found structured-output integrations collapse refusal rates and amplify bias (White Circle, 2026); and put escalations **in the surface the person already uses**, as a reviewable artifact a person rules on by commenting, the pattern Google's Antigravity uses for supervising parallel agents.

## Market

AI agents spending reaches $48B to $53B by 2030 across three estimates (MarketsandMarkets, Grand View, BCC). The budget this draws from is governance and observability: AI governance platforms about $1B by 2030 per Gartner and $15.8B per Forrester, and LLM observability from about $2B to over $9B (Citi Ventures). **Bottom-up TAM in 2030: base about $0.6B, range $0.14B to $2.9B (assumed)**, from 12,000 enterprises running multi-agent workflows, 50k to 1M high-impact agent writes a month each (base 200k), at $0.02 per gated write. That is 2% to 6% of 2030 governance plus observability spend. **SAM about $0.23B (assumed)**: the 40% in regulated or high-consequence operations. **SOM about $7M ARR in year three (assumed)**: 100 accounts at about $73k, roughly 3% of SAM. The weakest input is write volume; the first design partner's logs replace it.

## Cost, revenue, and what customers will pay for

Avoiding the wrong irreversible action is real but **secondary value**: rare, counterfactual, invisible on an invoice. The **tangible value is throughput**: the scarce resource is the person with authority, and the win is a higher share of agent decisions acting safely without them and fewer review minutes on the rest, measured as handle time, reversals and backlog. Lead with cost reduction and safe autonomy expansion; keep risk reduction for the security and compliance sign-off.

Customers pay for this today in reviewers and approval queues, hand-coded hard gates, platform fees for agents inside one vendor's estate (Agentforce $0.10 per action; Copilot Studio $200 per 25,000 credits), and after-the-fact tracing (LangSmith $39 per seat per month; Langfuse from $29). Orchestrators coordinate inside their own estate; governance and control tools (Zenity, Credo, Lakera, White Circle) check one agent or model against a policy; observability shows the trace afterwards. **No product found adjudicates a contested belief before the write.** Platforms will build the in-estate version, so the wedge is what they structurally cannot: **high-impact writes whose evidence spans two or more systems of record** (KYC in core banking, disputes in the card platform, service in the CRM), with provenance and revisable state across them.

## What must be true, and how we find out before design

Conflicts must be frequent outside agent-native companies, and accountable owners must trust a hold enough to stop overriding it. Before committing the design: **five interviews** with operations owners across the three verticals, and **one log pull** counting reversals and overrides on agent actions, to replace the assumed write volume with a measured rate. Until then, the problem is a well-argued projection, and the deck will say so.

**Decision requested:** proceed to design with the problem anchored on actions taken on contested or stale beliefs, agent disagreement as the lead trigger, and the cross-system wedge.

---

## Appendix A: sizing model (all inputs assumed unless sourced)

| Input | Low | Base | High | Basis |
|---|---|---|---|---|
| Enterprises running multi-agent workflows by 2030 | 12,000 | 12,000 | 12,000 | assumed: 60% of 20,000 large US and EU enterprises; 18% today (KPMG) |
| High-impact agent writes per enterprise per month | 50k | 200k | 1M | assumed; every high-impact write is evaluated, only conflicts escalate |
| Price per gated write | $0.02 | $0.02 | $0.02 | assumed: 20% of Agentforce's $0.10 per action |
| TAM | $0.14B | $0.58B | $2.9B | 12,000 × writes × 12 × $0.02 |
| Share of 2030 governance plus observability ($10.0B to $24.8B) | | 2.3% to 5.8% | | base TAM ÷ spend range |
| SAM (40%) | | $0.23B | | assumed |
| SOM, year 3 | | about $7M | | 100 accounts × ($48k usage + $25k platform minimum, assumed) |

## Appendix B: devil's advocate review, and what changed

| Objection | Change made |
|---|---|
| Rewrites Dyssonance's "43 agents and zero shared reality" essay; a gate is a harness | Anchor moved to acting on contested or stale beliefs, disagreement as lead trigger; one line on why this reads state rather than adding a harness |
| Each example is solved by a precedence rule | Added the rules-table row per vertical |
| No customer evidence | Five interviews and one log pull named as the gate before design |
| TAM circular, cross-check wrong | Sized on high-impact writes with a range; arithmetic corrected (was "9% to 15%", is 2% to 6%) |
| Platforms ship it as a feature | Wedge narrowed to cross-system writes platforms cannot see |
| User cannot feel the pain | User anchored on reversals, clawbacks, false notices, backlog; payer and beneficiary mapped |
| Snippet sourcing; MAST scoped to research tasks | KPMG flagged to verify; MAST removed from the headline; own measured rate promised from the eval set |
| Spawn and Block are trend-chasing | Demoted to colour |

## Appendix C: sources

- Spawn CEO blog, "How I Built the Most AI-Pilled Company in the World," Jacob (@jsnnsa), 28 Oct 2026 (local PDF).
- Financial services production RAG reference architecture (diagram supplied by the author).
- KPMG AI Pulse: https://kpmg.com/us/en/media/news/q4-ai-pulse.html
- Gartner agentic AI cancellations: https://w.media/over-40-percent-of-agentic-ai-projects-could-face-the-axe-by-end-of-2027-gartner/
- Microsoft Entra Agent ID: https://learn.microsoft.com/lt-lt/entra/agent-id/agent-users
- Workday Agent System of Record: https://investor.workday.com/news-and-events/press-releases/news-details/2025/Workday-and-Microsoft-to-Deliver-Unified-AI-Agent-Experience-for-the-Enterprise-09-16-2025/default.aspx
- Block restructuring: https://euronews.com/business/2026/02/27/jack-dorseys-block-cuts-roughly-50-of-jobs-as-it-embraces-ai-and-shares-jump
- AI agents market: https://prnewswire.co.uk/news-releases/ai-agents-market-worth-52-62-billion-by-2030---exclusive-report-by-marketsandmarkets-302435498.html ; https://www.prnewswire.co.uk/news-releases/ai-agents-market-size-to-hit-50-31-billion-by-2030-at-cagr-45-8---grand-view-research-inc-302447061.html ; https://www.bccresearch.com/pressroom/ait/ai-agents-market-to-grow-433-annually
- Gartner AI governance platforms: https://www.gartner.com/en/newsroom/press-releases/2026-02-17-gartner-global-ai-regulations-fuel-billion-dollar-market-for-ai-governance-platforms
- Forrester AI governance spend: https://www.forrester.com/blogs/ai-governance-software-spend-will-see-30-cagr-from-2024-to-2030
- Citi Ventures LLM observability: https://www.citi.com/ventures/perspectives/opinion/llm-observability-next-major-play.html
- Pricing: https://www.salesforce.com/agentforce/pricing/ ; https://www.microsoft.com/en-us/microsoft-365-copilot/microsoft-copilot-studio/ ; https://www.costbench.com/compare/arize-phoenix-vs-langsmith/ ; https://latitude.so/blog/best-langfuse-alternatives
- Zenity Series C: https://www.businesswire.com/news/home/20260803963850/en/
- White Circle, KillBench: https://whitecircle.com/research/killbench ; funding: https://dc.fortune.com/2026/05/12/exclusive-white-circle-raises-11-million-to-stop-ai-models-from-going-rogue-in-the-workplace/
- Google Antigravity: https://developers.googleblog.com/build-with-google-antigravity-our-new-agentic-development-platform/
- MPAC protocol: https://arxiv.org/pdf/2604.09744
- MAST, Why Do Multi-Agent LLM Systems Fail (research frameworks, coding and maths tasks): https://arxiv.org/abs/2503.13657v2
- C. Lozano, "Classification Is Not New. So What?", 24 Sep 2026: https://lecharles.medium.com/classification-is-not-new-so-what-b14d2b8740a1

*Market figures came from search snippets of press releases and aggregators; check primaries before any number goes on a slide.*
