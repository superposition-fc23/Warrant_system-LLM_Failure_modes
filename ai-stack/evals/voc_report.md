# Voice of customer: 181 public opinions classified

Opinion mining from Hacker News, Reddit and Medium, classified by Haiku. Not interviews. See biases at the end.

| Outcome | n | Mean importance | Mean satisfaction | Opportunity | Top performer |
|---|---|---|---|---|---|
| O1 | 32 | 6.3 | 3.2 | 9.4 | support or applied AI engineer |
| O2 | 14 | 6.3 | 2.9 | 9.7 | other |
| O3 | 46 | 6.4 | 4.1 | 8.7 | other |
| O4 | 13 | 6.2 | 3.2 | 9.1 | other |
| O5 | 33 | 6.1 | 3.6 | 8.6 | other |
| O6 | 10 | 5.3 | 3.8 | 6.8 | other |
| O7 | 12 | 6.1 | 4.1 | 8.1 | other |
| O8 | 21 | 6.7 | 3.7 | 9.7 | other |

Sources: {'hackernews': 163, 'substack': 18}
Performers: {'other': 90, 'support or applied AI engineer': 61, 'end customer': 19, 'VP or exec buyer': 10, 'finance or RevOps': 1}

## Example quotes per outcome

- **O1** (hackernews, support or applied AI engineer, I6/S4): "an AI agent that doesn't know what a column means will write SQL that looks right and returns wrong numbers." https://news.ycombinator.com/item?id=47705965
- **O1** (hackernews, end customer, I7/S2): "thousands of people will immediately find the right way to jailbreak your chatbot into giving them money" https://news.ycombinator.com/item?id=45948188
- **O2** (hackernews, other, I8/S3): "agents shouldn't just retrieve documents, they should be able to answer "why did we choose this?"" https://news.ycombinator.com/item?id=48841178
- **O2** (hackernews, other, I6/S3): "It's only defensible through narrative, which includes data." https://news.ycombinator.com/item?id=46960778
- **O3** (hackernews, other, I7/S2): "40% of time spent coordinating instead of coding" https://news.ycombinator.com/item?id=45107218
- **O3** (hackernews, support or applied AI engineer, I7/S3): "After completing a task, they sit idle until the human types something." https://news.ycombinator.com/item?id=47391328
- **O4** (hackernews, other, I7/S5): "so every call and ticket shares the same history and "story of the customer."" https://news.ycombinator.com/item?id=46385025
- **O4** (hackernews, end customer, I6/S2): "acknowledges that they didn't send the email they promised but refuse to help anyway" https://news.ycombinator.com/item?id=49536677
- **O5** (hackernews, other, I4/S5): "nobody should be deliberately creating/modifying anything in such a way that it performs undesirable instructions" https://news.ycombinator.com/item?id=48362908
- **O5** (hackernews, other, I3/S3): "as agents want to get more autonomous or we are letting them be" https://news.ycombinator.com/item?id=47264945
- **O6** (hackernews, support or applied AI engineer, I5/S3): "the evals that catch the agent when it does something dumb" https://news.ycombinator.com/item?id=49973773
- **O6** (hackernews, support or applied AI engineer, I6/S4): "the evals that catch the agent when it does something dumb" https://news.ycombinator.com/item?id=49648574
- **O7** (hackernews, support or applied AI engineer, I6/S3): "allowing the agent to handle the query without logging into Chat Data" https://news.ycombinator.com/item?id=41497327
- **O7** (hackernews, VP or exec buyer, I8/S2): "Widespread AI usage is going to be a security nightmare of prompt injection and leaking credentials and PII." https://news.ycombinator.com/item?id=47592506
- **O8** (hackernews, other, I5/S3): "the legal AI companies haven't even scratched the surface of it" https://news.ycombinator.com/item?id=48150740
- **O8** (hackernews, other, I8/S2): "No audit trail. “Why did the system make this decision?” Today’s answer: ¯\(ツ)/¯" https://news.ycombinator.com/item?id=46122300

## Biases (this is a failure mode, not just a caveat)
- Selection: forum authors skew to developers and complainers; VPs and finance analysts rarely post.
- Query bias: the search terms were written from my hypothesis, so they find what I expected.
- Judge bias: a model infers importance and satisfaction from text; belief is bias, and so is the judge.
- Not our customers: no evidence these authors run multi-agent support workflows.
- Recency and platform: Medium skews to vendor content marketing; Reddit search may be rate-limited.