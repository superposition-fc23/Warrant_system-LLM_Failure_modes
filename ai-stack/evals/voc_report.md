# Voice of customer: 284 public opinions classified

Opinion mining from Hacker News, Substack and Reddit search snippets (Medium pending), classified by Haiku. Not interviews. See biases at the end.

| Outcome | n | Mean importance | Mean satisfaction | Opportunity | Top performer |
|---|---|---|---|---|---|
| O1 | 50 | 6.5 | 3.5 | 9.5 | other |
| O2 | 25 | 6.4 | 3.3 | 9.6 | support or applied AI engineer |
| O3 | 85 | 6.1 | 3.7 | 8.5 | other |
| O4 | 22 | 6.7 | 3.0 | 10.3 | support or applied AI engineer |
| O5 | 38 | 6.4 | 3.6 | 9.2 | other |
| O6 | 12 | 6.2 | 4.1 | 8.4 | other |
| O7 | 18 | 6.2 | 4.3 | 8.1 | other |
| O8 | 28 | 7.0 | 4.1 | 9.9 | support or applied AI engineer |
| O9 | 6 | 6.8 | 3.2 | 10.5 | other |

Sources: {'substack': 18, 'hackernews': 196, 'reddit-search': 70}
Performers: {'other': 140, 'support or applied AI engineer': 94, 'VP or exec buyer': 14, 'end customer': 28, 'CSM': 6, 'finance or RevOps': 2}

## Per source: an outcome that only ranks high in one source is suspect

| Outcome | Hacker News n, opp. | Substack n, opp. | Reddit snippets n, opp. |
|---|---|---|---|
| O1 | 25, 9.7 | 2, 10.0 | 23, 9.3 |
| O2 | 17, 9.8 | 0 | 8, 9.1 |
| O3 | 60, 8.0 | 7, 11.1 | 18, 9.1 |
| O4 | 13, 9.8 | 0 | 9, 11.1 |
| O5 | 30, 9.1 | 4, 10.8 | 4, 9.0 |
| O6 | 8, 7.8 | 2, 12.5 | 2, 7.0 |
| O7 | 17, 8.4 | 0 | 1, 4.0 |
| O8 | 22, 9.0 | 3, 14.7 | 3, 11.7 |
| O9 | 4, 9.0 | 0 | 2, 13.5 |

## Example quotes per outcome

- **O1** (substack, other, I5/S4): "agents that impress in demos falter on messy data and real workflows" https://gradientflow.substack.com/p/real-world-lessons-from-agentic-ai
- **O1** (substack, support or applied AI engineer, I8/S2): "green dashboards don't mean safety they just mean the AI is confident." https://qubytes.substack.com/p/beyond-mlops-how-to-monitor-debug
- **O2** (hackernews, support or applied AI engineer, I8/S2): "every agent session started from zero, so we were pasting the same context about our codebase and our decisions into Claude Code dozens of times a day." https://news.ycombinator.com/item?id=48841178
- **O2** (hackernews, other, I7/S4): "at some point someone has to make an imperfect judgment call that's not reducible to a single metric" https://news.ycombinator.com/item?id=46960778
- **O3** (substack, other, I8/S2): "After the twentieth prompt you're no longer reading, you're just clicking." https://cobusgreyling.substack.com/p/humans-cannot-keep-up-with-agents
- **O3** (substack, other, I6/S3): "Approving everything and approving nothing produce the same audit trail." https://paice.substack.com/p/agentic-ai-approval-fatigue-and-rubber
- **O4** (hackernews, support or applied AI engineer, I7/S5): "so every call and ticket shares the same history and "story of the customer."" https://news.ycombinator.com/item?id=46385025
- **O4** (hackernews, end customer, I7/S1): "customer support agent acknowledges that they didn't send the email they promised but refuse to help anyway" https://news.ycombinator.com/item?id=49536677
- **O5** (substack, other, I8/S2): "The human can remain in the loop while oversight has already left it." https://adrianlerer.substack.com/p/the-human-is-still-in-the-loop-the
- **O5** (substack, other, I6/S2): "Most of it doesn't work. Not the way it was sold, anyway." https://mirelaxhota01.substack.com/p/beyond-the-hype-hard-won-lessons
- **O6** (substack, other, I7/S2): "companies rarely measure oversight quality while efficiency targets squeeze review time" https://operatingmodeldispatch.substack.com/p/human-in-the-loop-isnt-real-oversight
- **O6** (substack, support or applied AI engineer, I8/S3): "The gap between a compelling demo and a production-grade system is wide" https://nexo.substack.com/p/what-i-learned-building-ai-agents
- **O7** (hackernews, support or applied AI engineer, I6/S5): "URL is whitelabeled, allowing the agent to handle the query without logging into Chat Data." https://news.ycombinator.com/item?id=41497327
- **O7** (hackernews, other, I9/S2): "Widespread AI usage is going to be a security nightmare of prompt injection and leaking credentials and PII." https://news.ycombinator.com/item?id=47592506
- **O8** (substack, other, I9/S3): "Autonomy without accountability is not production readiness." https://bhavishyapandit9.substack.com/p/who-owns-an-ai-agents-actions
- **O8** (substack, other, I9/S2): "You cannot retroactively create an audit trail." https://kiteworks.substack.com/p/ai-agent-audit-trail-compliance-attribution-gap
- **O9** (hackernews, other, I6/S5): "raises their priority on repeats, alerts Discord, and adds optional AI diagnosis and a suggested patch" https://news.ycombinator.com/item?id=49920135
- **O9** (hackernews, other, I5/S7): "it filters the subject for "security" and alerts the on-call engineer who can evaluate the severity" https://news.ycombinator.com/item?id=5248217

## Biases (this is a failure mode, not just a caveat)
- Selection: forum authors skew to developers and complainers; VPs and finance analysts rarely post.
- Query bias: the search terms were written from my hypothesis, so they find what I expected.
- Judge bias: a model infers importance and satisfaction from text; belief is bias, and so is the judge.
- Not our customers: no evidence these authors run multi-agent support workflows.
- Recency and platform: Medium skews to vendor content marketing.
- Reddit rows are search snippets, not threads: ranked by a search engine, thin on context, so satisfaction often sits at the default of 5.