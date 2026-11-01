# When enterprise agents disagree: discovery memo

*31 Oct 2026, revision 4: direction committed, solution not. One page in six-page-memo style, with the sizing model, the review and sources in the appendix. Every figure has a source or is marked (assumed). "Warrant" is a working name; the product angle is set in the design stage.*

## The customer problem

Enterprises are adding specialist agents on top of existing data, identity and policy estates. A typical production pattern, here a financial services reference architecture, puts a coordinator agent in front of accounts, transaction and service agents, each calling its own MCP server and sharing a session store, with authorization, PII redaction, an evaluation suite and observability around them. Every box has an owner except one: **the moment an agent is about to commit an action on a belief that is contested or stale.** The most visible and fastest-growing source of contest is other agents. When two specialists reach different conclusions about the same customer, shipment or account, the coordinator routes rather than adjudicates, and the disagreement is settled by mechanics: last write wins, the most confident agent acts, or the coordinator picks. The other sources are quieter: an observation that expired, a rule that was amended. Either way the action executes, and nobody can later see what it relied on or which fact would have changed it.

**Why a rules table does not fix it.** Each vertical already has precedence rules, and each breaks on age, partial evidence and rules that change:

| Vertical | The conflict | The rule that exists | Where the rule fails |
|---|---|---|---|
| Retail banking | Service agent updates the customer's phone number and enrols a new device; minutes later the payments agent sends an instant payment to a newly added payee (Zelle or RTP in the US, SEPA Instant or Faster Payments in Europe) while the fraud agent's device-risk score predates the change | Account-takeover rule: after a contact or device change, hold new payees for a cooling-off period | It blocks every genuine customer who just replaced a phone, and it cannot tell that the customer passed step-up authentication in the app an hour ago, a fact held in another system |
| Freight | Exception agent tells the customer a container is released on carrier status while the broker shows an exam hold | Customs status outranks carrier status | It cannot express that the broker's hold is itself six hours old, or that the exam finished and was not yet posted |
| CRM customer service | Refund agent approves a credit while a risk agent has flagged the account and the contract overrides standard terms | Risk outranks service | It cannot tell that the risk flag was cleared yesterday, or that a contract amendment changed the terms |

Enterprise structure makes this harder. RBAC means the agent that can act is often not the one that knows. Hierarchy means some views outrank others, but only while they are current. PII rules limit what an escalation may show to whom.

**User and symptom.** The person accountable for one agent-run workflow, for example a contact-centre operations lead, a freight exceptions manager or a banking servicing head. They do not see conflicts; they see the symptoms they already track: **reversed actions, refund clawbacks, false status notices, and an escalation backlog.** The buyer is the head of the AI platform, who pays from a platform budget while the value lands in the operations P&L, so the business case has to be written in the operations owner's numbers.

## Why now

The share of organisations orchestrating multiple agents across workflows rose from 9% to 18% in one quarter (KPMG AI Pulse, to verify against the primary). Gartner expects over 40% of agentic AI projects to be cancelled by end 2027, partly over inadequate risk controls (Jun 2025). Agents are getting identities and a place in the org chart: Microsoft issues them directory identities (Entra Agent ID, May 2025) and Workday registers them beside human workers (Agent System of Record, Sep 2025). Agent-first companies such as Spawn and Block are colour, not evidence of the enterprise problem: they show where action volume is heading, not that enterprises have this pain today.

## The direction (committed), not yet the solution

**A closed reliability loop for multi-agent workflows, working at three time scales**, built from today's agents and LLM architectures:

1. **At inference: intervene on known failure modes.** Before a high-impact write, check the evidence behind it. The first known failure is the anchor above: acting on a belief that is contested, by another agent or a newer source, or stale. The intervention returns a bounded decision: act, gather one named fact, or hold for the person with authority.
2. **During and after the run: shadow and offline evals with observability.** Trace every run, let judges score it in shadow without acting, replay stored traces and planted defects offline, and turn each human ruling into an eval case. What is learned loops back into the interventions.
3. **Over time: online evals benchmarked against the past.** Score live runs continuously and compare each week with the baseline, so improvement is proven rather than asserted, and regressions trip a kill switch.

**Why this answers the harness objection rather than avoiding it.** Loops 1 to 3 are, deliberately, the best harness-era version: interventions, judges and evals around today's agents. The deliverable is not the harness but the evidence from it: what the loop costs to build and run, where it still fails, and a replacement map of which parts a persistent belief state would subsume, improve, or leave untouched. If the loop converges on something belief-like, the parallels are explicit: the intervention is "whether the system knows enough to act"; contested and stale evidence is dissonance and decay; learning from rulings is belief revision; and benchmarking change over time mirrors "transitions between belief states become learning signals." It need not be their architecture to test their hypothesis.

Five constraints: converge by **updating state, not by debating longer**: more agent chatter is the token maximalism C. Lozano argues against ("The Internet of Agents: Google's Surface War, Token Maximalism, and the Benchmark That Pretended to Surprise Us", 23 May 2026), and Spawn found it grows with the square of agent count (p. 5); output a **bounded decision from a small classifier**, costed per resolved conflict, not per token; **escalate only real disagreements**, because users approve about 93% of Claude Code permission prompts (Anthropic, as cited by C. Lozano, 24 Sep 2026); make **hold a first-class output and test it for bias**, because KillBench, which Lozano discusses in the same article, found structured-output integrations collapse refusal rates and amplify bias (White Circle, 2026); and put escalations **in the surface the person already uses**, as a reviewable artifact ruled on by comment, the pattern Google's Antigravity uses to supervise parallel agents, and the surface argument of the same article: distribution beats benchmarks.

**Callout: decision, trade-off, conclusion.** *Decision:* build the harness-era loop on purpose as the baseline. *Trade-off:* it can read as more guardrails, the symptom containment Lozano argues against; in return it yields evidence of where harnesses break. *Conclusion:* it supports the thesis only if the loops are framed as the baseline, learning is stored as revisable state with provenance rather than prompt edits, and the demo shows one case the harness cannot solve. **Belief is bias:** a belief is a prior held with confidence, and unaudited it is bias, so every learned belief carries provenance and is tested with counterfactual pairs.

## Market

Revision 3 sized a feature: a gate priced at $0.02 per write, measured against governance spend alone, which gave a base TAM of $0.58B. The committed direction is a category, agent reliability (intervene, evaluate, observe, prove), which draws on observability, evals and governance budgets together.

**Landscape, 2030.** AI agents $48B to $53B (MarketsandMarkets, Grand View, BCC). LLM observability over $9B (Citi Ventures). AI governance $1B (Gartner) to $15.8B (Forrester). The reliability spend pool is therefore **$10B to $25B**, with the definitional spread mostly in governance.

**Bottom-up TAM: base $3.0B, range $1.2B to $6.0B (assumed)**, from 12,000 large enterprises running multi-agent workflows at an annual contract of $100k to $500k (base $250k), priced as a platform with a usage component rather than per write. That is 12% to 30% of the 2030 pool, plausible as an addressable share for the category, not as capture. **SAM about $1.2B (assumed)**: the 40% in regulated or high-consequence operations, where an unproven agent cannot ship. **SOM about $25M ARR in year three (assumed)**: 100 accounts at $250k, about 2% of SAM. The weakest input is contract size; three design-partner conversations replace it.

## Cost, revenue, and what customers will pay for

Avoiding the wrong irreversible action is real but **secondary value**: rare, counterfactual, invisible on an invoice. The **tangible value is throughput**: the scarce resource is the person with authority, and the win is a higher share of agent decisions acting safely without them and fewer review minutes on the rest, measured as handle time, reversals and backlog. Lead with cost reduction and safe autonomy expansion; keep risk reduction for the security and compliance sign-off.

Customers pay for this today in reviewers and approval queues, hand-coded hard gates, platform fees for agents inside one vendor's estate (Agentforce $0.10 per action; Copilot Studio $200 per 25,000 credits), and after-the-fact tracing (LangSmith $39 per seat per month; Langfuse from $29). Orchestrators coordinate inside their own estate; governance and control tools (Zenity, Credo, Lakera, White Circle) check one agent or model against a policy; observability shows the trace afterwards. **No product found adjudicates a contested belief before the write.** Platforms will build the in-estate version, so the wedge is what they structurally cannot: **high-impact writes whose evidence spans two or more systems of record** (device risk in the fraud platform, payees in core banking, contact changes in the CRM), with provenance and revisable state across them.

## What must be true, and how we find out before design

Conflicts must be frequent outside agent-native companies, and accountable owners must trust a hold enough to stop overriding it. Before committing the design: **five interviews** with operations owners across the three verticals, and **one log pull** counting reversals and overrides on agent actions, to replace the assumed write volume with a measured rate. Until then, the problem is a well-argued projection, and the deck will say so.

**Key fork, recorded 31 Oct.** *Decision:* narrow to one vertical with three users; design for one primary user and one buyer; label every element vertical-specific or general so it abstracts later; keep TAM horizontal and resize SAM and SOM to the beachhead in design. *Assumption:* three verticals made the persona vague, and the shared failure means one concrete vertical still abstracts. *Vertical decided:* CRM customer service (audience fit, the author's own domain, and a VP of Support owns both the agent budget and the handle-time metrics); freight stays as a second use case, banking as an abstraction example.

**Decision requested:** commit to the direction, a closed reliability loop at three time scales, with acting on contested or stale beliefs (agent disagreement as the lead trigger) as the first known failure it intervenes on. Leave the solution open for the design iteration.

---

## Appendix A: sizing model (all inputs assumed unless sourced)

| Input | Low | Base | High | Basis |
|---|---|---|---|---|
| Enterprises running multi-agent workflows by 2030 | 12,000 | 12,000 | 12,000 | assumed: 60% of 20,000 large US and EU enterprises; 18% today (KPMG) |
| Annual contract, platform plus usage | $100k | $250k | $500k | assumed: priced as reliability platform, not per write |
| TAM | $1.2B | $3.0B | $6.0B | 12,000 × contract |
| Share of 2030 reliability pool ($10B to $25B) | | 12% to 30% | | base TAM ÷ pool |
| SAM (40%) | | $1.2B | | assumed |
| SOM, year 3 | | $25M | | 100 accounts × $250k, about 2% of SAM |
| Revision 3, for comparison | | $0.58B | | gate only, 200k writes a month × $0.02 |

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
- C. Lozano, "The Internet of Agents: Google's Surface War, Token Maximalism, and the Benchmark That Pretended to Surprise Us", Medium, 23 May 2026 (read via Medium's RSS feed; body partly truncated): https://lecharles.medium.com/the-internet-of-agents-googles-surface-war-token-maximalism-and-the-benchmark-that-pretended-to-0185ebecea69
- C. Lozano, "Classification Is Not New. So What?", 24 Sep 2026: https://lecharles.medium.com/classification-is-not-new-so-what-b14d2b8740a1

*Market figures came from search snippets of press releases and aggregators; check primaries before any number goes on a slide.*
