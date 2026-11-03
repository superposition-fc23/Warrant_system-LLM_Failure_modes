# Design sprint prompt (35 minutes, game mode)

**Task.** Design the v1 product for the committed direction, one step at a time, stopping after each step for my call. Steps: 1 users, 2 pain points, 3 jobs to be done with goals and non-goals, 4 UX as information to decisions to actions, 5 testable requirements with test and metrics (leading, lagging, counter), 6 devil's advocate, 7 design in the harness, 8 critique (me and you as judges), 9 updated design.

**Context from discovery** (`product/01-discovery-memo.md`, `index.html` 01 to 06).
- Direction: a closed reliability loop for multi-agent workflows. Intervene at inference, learn in shadow and offline, prove improvement online against the past.
- First known failure: an agent commits a high-impact action on a belief that is contested (by another agent or a newer source) or stale. Agent disagreement is the lead trigger. Output is bounded: act, gather one named fact, or hold for the person with authority.
- Verticals: banking (instant-payment account takeover after a phone and device change), freight (released vs exam hold), CRM service (refund vs risk flag). Wedge: writes whose evidence spans two or more systems of record.
- User: the person accountable for one agent-run workflow, who sees reversals, clawbacks, false notices and backlog, not conflicts. Buyer: VP of Support, with the head of AI platform approving the technical side.
- Callouts: the loops are the baseline, not the product; learning is stored as revisable state with provenance, not prompt edits; the demo shows one case the harness cannot solve; belief is bias, so beliefs get counterfactual bias tests.

**Output shape.** Each step as one small table or at most five bullets, written into the harness sections (07 user and JTBD, 08 scope, 09 model, 10 solution, 12 guardrails, 13 metrics) and the design callout. Vertical decided: CRM customer service. Three users in it; design for one primary user and one buyer. Label every element vertical-specific or general. Requirements in the form "When [condition], the system must [behaviour]. Test: [method and data]."

**Avoid.** Committing to Dyssonance's architecture or claiming to rebuild CRUU. Agent debate loops or anything priced per token. "Accurate", "fast", "reliable" or "intuitive" without a number and a test. Any figure without a source or an "assumed" marker. More than three users, or designing for more than one primary user. Screens that hide what is mocked. Em dashes. Moving to the next step before I call it.
