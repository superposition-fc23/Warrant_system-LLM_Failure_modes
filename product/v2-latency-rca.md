# Why v2 latency doubled

**Finding.** Median gate latency went from 6.7 s to 14.5 s because 17 of 22 model cases now make two model calls in series. Latency tracks output tokens almost exactly, and v2 did not shorten the output. The harness, tools and data reads account for about 36 ms.

Source: `ai-stack/runs/v1-20261101T0823` and `ai-stack/runs/v2-20261101T0837`, 27 cases each. Times below come from those traces unless marked as an estimate.

## Where the time went

| Path through the gate | Cases | Median | |
|---|---|---|---|
| v1: Opus, one call | 26 | 6.8 s | |
| v2: code decides, no model | 5 | under 0.1 s | Faster |
| v2: Haiku only | 5 | 6.2 s | About the same |
| v2: Haiku, then Opus | 17 | 16.2 s | **The cause** |

The 17-case path now holds the median, so that is what p50 reports. The mean rose less, from 7.1 s to 11.6 s, because code-decided cases cost almost nothing. 20 cases got slower, 6 got faster and 1 was unchanged.

## The usual suspects

| Suspect | Verdict | Evidence |
|---|---|---|
| Context blow-up from tools and orchestration | **Not the cause** | Median input rose from 1,402 to about 1,600 tokens. Tool schemas are not sent to the model, because code reads the sources. Latency barely depends on input at this size |
| External data fetch | **Not the cause today, and not tested yet** | `read_sources` took 10.8 ms in v1 and 10.7 ms in v2. Those reads are local fixtures, so this says nothing about real APIs |
| Loops and redundancy | **Root cause** | No retry loops, but the escalation is redundant: Opus gets the full prompt again and throws away Haiku's answer. Compare calls rose from 26 to 39 |
| Harness and guardrails | **Not the cause** | All non-model time: 31 ms to 36 ms at the median, about 0.25% of the total. Redaction, rules and records are each about 0.1 ms or less |

## Root causes, in order

1. **Two tiers in series.** The second call starts from zero.
2. **Escalation fired too often.** 17 of 22 cases escalated. 6 of those had no material conflict, only a complexity trigger: risk flags on 3, agent assertions on 2, several contract documents on 1.
3. **Long output.** Output tokens explain 93% to 100% of the variation in call time (r² per model and run).

| Model | Time per output token | Median output, v2 | Of which reasoning | Speed |
|---|---|---|---|---|
| Haiku 5.5 | 3.9 ms | 1,629 | 876 | 231 tokens/s |
| Opus 5.5 | 8.3 ms | 976 | 250 | 116 tokens/s |

Haiku is twice as fast per token but wrote 2.2 times what Opus wrote in v1 (752), so it saved no time: 7.1 s against 6.8 s.

4. **Output nobody reads.** 16 of 22 cases reported an "unverifiable" conflict, mostly because the corpus has no incident system. The model writes prose about a gap that code could state.

## Limits of this analysis

- **One run per version.** Treat small differences as noise.
- **No time to first token.** Calls are not streamed, so queueing and generation cannot be split. The fit's intercept of 0.2 to 0.8 s is the nearest proxy.
- **Haiku's answers were not stored.** When Opus overwrote them, the first pass was lost, so we cannot say how often escalation changed the result. This is the gap that matters most for deciding whether to keep two tiers.
- **Fixture reads.** Production latency from real CRM and billing APIs is still unknown.

## Corrective action for v3

| # | Action | Expected effect | Basis |
|---|---|---|---|
| 1 | One model per case. Remove the series path | Median 6.1 s (Opus) or 6.9 s (Haiku), p95 11.9 s for Opus | Replay of the traces with v2's code skip |
| 2 | Compact, evidence-only output with a token cap; code writes the prose. A truncated reply holds | About 3 to 4 s for Opus, about 4.7 s for Haiku at current reasoning | **Estimate** from the fit, at 350 to 450 and about 1,030 output tokens |
| 3 | Add the incident system | Fewer "unverifiable" conflicts and shorter output | Not yet measured |
| 4 | Let code clear more: when the proposal agrees with the governing source, no model is needed. Extract contract terms once per document version and cache them | Clean cases near 0 s | Not yet measured. Largest upside and the largest recall risk |
| 5 | Store every model answer, stream to get time to first token, and fail a run that misses the latency bar | Closes the gaps above | Instrumentation |
| 6 | Read sources in parallel, with a time budget per source. A source that times out produces a gather or hold, never an act | Protects production | Design rule; test with injected delays |

**Do not separate services yet.** At 11 ms there is nothing to gain today. Move MCP to a real process boundary in a later version, inject realistic delays, and split only what the numbers justify. Shadow mode can run off the agent's request path, so latency only blocks an agent once the gate is enforcing.

**Model choice.** Run Opus and Haiku once each on compact output. At list prices, a compact call is about $0.014 on Opus and $0.0007 on Haiku (estimate), so Haiku should win unless it misses the catch-rate bar. Decide on results.

## Proposed v3 bar

All together, set before building: planted held 10 of 10; fact named at least 9 of 10; over-held at most 1 of 10; pairs 6 of 6; median at most 5 s and p95 at most 8 s across all gate runs; cost at most $0.017 per decision.
