# Warrant: a decision gate for agent swarms

*Discovery memo, 31 Oct 2026. Six-page-memo style compressed to one page, with sources and the sizing model in the appendix. Every figure has a source or is marked (assumed).*

## The customer problem

Enterprises now run fleets of agents next to people. Spawn, a 10-person company, spends about 30x its payroll on tokens, lands roughly 108 changes an hour, and coordinates its agents through shared state rather than reviews: whoever lands second reconciles (Spawn CEO blog, 28 Oct 2026, pp. 1 to 6). When two agents reach different conclusions about the same decision, today's systems settle it by mechanics, not evidence. The last writer wins, a supervisor model votes, or the most confident agent acts. The action executes, and nobody can later see that there was a dissent, what each side relied on, or which fact would have settled it. Berkeley's study of 1,642 multi-agent traces attributes about a third of failures to inter-agent misalignment (MAST, arXiv 2503.13657). The cost appears twice. Irreversible actions taken on a contested belief, and a flood of escalations to the few humans with authority. Spawn's founder woke to 700 open questions in one morning (p. 9).

**Customer.** The human accountable for what an agent fleet does in one domain, for example an IT operations lead whose remediation, change and security agents act on the same servers. Spawn calls this person a "paratrooper." The buyer is the head of the AI platform or the CIO.

## Why now

The share of organisations orchestrating multiple agents across workflows doubled from 9% to 18% in one quarter (KPMG AI Pulse, Q2 2026, via aggregator, to verify). Gartner expects over 40% of agentic AI projects to be cancelled by the end of 2027, partly over inadequate risk controls (Gartner, Jun 2025). Agents are gaining real permissions faster than anyone is gaining a way to see when they disagree.

## The idea

Warrant sits between agents and the system of record. When agents propose conflicting actions on the same object, it keeps both positions explicit with their evidence, provenance and age instead of collapsing them, then makes one of three calls: **act** when the governing belief is current and uncontested, **gather** when one named fact would settle it, **hold** for a human when it would not. Every call leaves a decision record that a later agent or person can read back, and every human ruling becomes an eval case. This is the half of Dyssonance's thesis they have stated but not shown: whether the system "knows enough to act." It is not shared agent memory, which their "43 AI agents and zero shared reality" essay already argues, and it is not a supervisor agent, which their belief-conditioned agency page positions against.

Three design constraints follow. **Agents converge by updating a belief state, not by debating longer**: more agent chatter is token maximalism, and Spawn found chatter grows with the square of the agent count (p. 5). **The gate's output is a bounded decision** (act, gather, hold) from a constrained classifier, not prose, so most calls run on a small model and cost is measured per resolved conflict, not per token. **Escalate only real disagreements**: users approve about 93% of Claude Code permission prompts (Anthropic, as cited by C. Lozano, "Classification Is Not New. So What?", 24 Sep 2026), so a gate that asks often is a gate that gets rubber-stamped.

## Market

AI agents spending reaches $48B to $53B by 2030 across three independent estimates (MarketsandMarkets, Grand View, BCC). The spend Warrant would draw from is governance and observability: AI governance platforms reach about $1B by 2030 per Gartner and $15.8B per Forrester, a 15x gap from definitions, and LLM observability grows from about $2B to over $9B (Citi Ventures). **Bottom-up TAM of about $1.4B in 2030 (assumed)**: 12,000 large enterprises running multi-agent workflows, each gating about 1M agent actions a month at $0.01 per gated action. **SAM about $0.6B (assumed)**: the 40% in regulated or high-consequence operations. **SOM about $18M ARR in three years (assumed)**: 150 accounts at $120k, about 3% of SAM. The weakest input is gated-action volume; the appendix shows it.

## Cost, revenue, and what customers will pay for

The fear story, avoiding the wrong irreversible action, is real but secondary value: rare, counterfactual, and hard for a customer to see on an invoice. The tangible value is throughput. Spawn's AI judges handled 11,372 questions in nine days; 64% were decided automatically, 19% returned to the filer, about 16% held, and the founder ruled 27 times, while daily changes rose from about 1,000 to 7,250 (p. 10). The scarce resource is human authority, and the measurable win is raising the share of agent decisions that can safely act without it. Warrant should be sold as cost reduction measured in human review minutes and as safe autonomy expansion, with risk reduction as the insurance argument for the security buyer.

Today customers pay for this problem in four places. They hire reviewers or route approvals into Slack. They hand-code hard gates in front of payments and other irreversible actions (Spawn, p. 7). They pay platform fees for agents inside one vendor's estate: Agentforce at $0.10 per action, Copilot Studio at $200 per 25,000 credits. And they pay for after-the-fact tracing: LangSmith at $39 per seat per month, Langfuse from $29 per month. Orchestrators coordinate agents only inside their own platform. Governance tools such as Zenity, Credo and Lakera check one agent against a policy. Observability tools show the trace after the action ran. **No product found arbitrates between agents that disagree before the action reaches the system of record**; it exists only in research such as the MPAC protocol (arXiv 2604.09744). So the product form is a vendor-neutral gate at the tool or MCP layer, priced per gated decision with a platform minimum, with the decision record surfaced in Slack where the accountable human already works. It is not another orchestrator.

## What we do not know yet

Whether accountable owners trust a hold enough to stop overriding it. Whether conflicts are frequent enough outside agent-native companies like Spawn to justify a line item. Gated-action volume per enterprise, the input that moves TAM most. And whether our TAM is optimistic: Gartner's $1B governance figure is the honest floor.

**Decision requested:** proceed to user and pain-point design with Warrant as the idea and IT operations remediation as the demo workflow. That domain is my own escalation-boundary experience, and its synthetic corpus already exists with planted conflicts (`ai-stack/docs/02-rmm-device-state`, `s1-mcp-gateway`).

---

## Appendix A: sizing model (all inputs assumed unless sourced)

| Input | Value | Basis |
|---|---|---|
| Large enterprises, US and EU, over 1,000 staff | 20,000 | assumed, to verify |
| Share running multi-agent workflows by 2030 | 60% | assumed; 18% in Q2 2026 (KPMG) |
| Gated agent actions per enterprise per month | 1M | assumed; Spawn alone lands about 78k changes a month with 10 people |
| Price per gated action | $0.01 | assumed: 10% of Agentforce's $0.10 per action |
| TAM | 12,000 × 1M × 12 × $0.01 ≈ $1.4B | cross-check: about 9% to 15% of 2030 governance plus observability spend |
| SAM | 40% regulated or high-consequence ≈ $0.6B | assumed |
| SOM, year 3 | 150 accounts × $120k ≈ $18M | assumed, about 3% of SAM |

## Appendix B: sources

- Spawn CEO blog, "How I Built the Most AI-Pilled Company in the World," Jacob (@jsnnsa), 28 Oct 2026 (local PDF).
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

*Caveat: the market figures came from search snippets of press releases and aggregators; check the primary pages before any number goes on a slide.*
