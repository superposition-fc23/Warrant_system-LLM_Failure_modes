# LLM and agent failure modes seen while building

A running log from one real build: failures of LLMs and agentic workflows, in the tools used to build this product and in the product itself. Add a row whenever a run or a review catches one. Each row needs evidence.

**Who wrote this.** The model that built the system drafted this log from its own record. It lists only failures someone caught, so silent failures are missing by construction. Treat it as a proposal and have an independent reader check it.

## Levels

- **Build:** the LLM agent writing code, tests, docs and analysis.
- **Product:** the LLM inside Warrant, at inference.
- **Eval:** LLMs used to audit or grade.

## Log

| # | Level | Pattern | What happened | Evidence | Caught by | When | Fix or status |
|---|---|---|---|---|---|---|---|
| 1 | Build | Over-broad belief, persisted | An instruction about what to keep out of public text became a ban on naming a tool. It was saved to agent memory, restated as a hard constraint by a context summary, acted on in two public docs, and led to a proposed history rewrite | Commits `500bf22`, `01729ce`; restored on this branch | User, before the rewrite | 1 Nov | Memory corrected; scope of the rule restated |
| 2 | Build | Plausible prior | Assumed importance scores ran 2 to 3 points above the evidence | `index.html` section 07 step 3d; learnings | Evidence check | 31 Oct | Assumed scores labelled |
| 3 | Build | Biased method | Averaged the top 100 by importance, inflating it by 0.6 to 1.0 per outcome | Learnings; `ai-stack/voc.py` | Review | 31 Oct | Report uses every relevant item |
| 4 | Build | False null | 7 of 10 long queries returned nothing, which looked like weak evidence | Learnings | Recall check | 1 Nov | Queries shortened, bar unchanged |
| 5 | Build | Wrong number stated confidently | "92% from one source" for 95% (378 of 396) | `product/v3-plan.md` history | Recount | 1 Nov | Corrected |
| 6 | Build | Misquoted a spec | README stated the wrong v2 latency target | `bf3abf0` | Trace review | 1 Nov | Corrected |
| 7 | Build | Unsafe default | 28 third-party addresses reached git history; later, 100 of 407 items still held personal details | `dcae2f0`, `1255905` | Pre-publish scan | 1 Nov | Scanner, hook, CI, minimisation |
| 8 | Build | Plausible prior | "A smaller model is faster" shaped v2. It wrote 2.2 times the output, so it saved no time | `product/v2-latency-rca.md` | Traces | 1 Nov | Bar failed and reported |
| 9 | Build | Local fit, lost goal | v3 UX plan ranks the analyst P0 and the engineer P2; section 07 names the engineer as primary | `product/v3-plan.md`; `index.html` section 07 | System map | 1 Nov | Open: user decision |
| 10 | Build | Gate not enforced | Five interviews and one log pull were set as the gate before design; design went ahead on a labelled stand-in | `product/01-discovery-memo.md` | System map | 1 Nov | Open |
| 11 | Build | Claim narrower than reality | Records said 9 facts came "from code", but 2 planted ones rest on a limit the model read | `ai-stack/warrant.py` `decide`; `runs/v2-20261101T0837/decisions.jsonl` | System map | 1 Nov | Stated in section 09 |
| 12 | Product | Override by model | The model's named fact overrode a failed code check on 2 cases | PR 1, PL-02, PL-06 | v1 run | 1 Nov | Fixed in v2 |
| 13 | Product | Wrong emphasis | Named an unverifiable incident over the superseding amendment | PR 2, PL-05 | LLM judge | 1 Nov | Fixed in v3: code names the money conflict |
| 14 | Product | Dissent discarded | Escalation overwrites the first answer, so tier disagreement is lost. This is the failure section 02 describes | `ai-stack/warrant.py` `compare` | Trace review | 1 Nov | Fixed in v3: one model per case, every answer stored |
| 15 | Product | Output nobody reads | 16 of 22 cases wrote prose about unverifiable claims | RCA | Trace review | 1 Nov | Reduced in v3: at most one such conflict, output capped |
| 16 | Product | Silent guard edge | Token restore breaks at ten or more names | PR 2 review comment | Code review | 1 Nov | Fixed in v3, tested |
| 17 | Product | Guard gap | Judge prompt carries restored names; redaction covers the compare path only | `ai-stack/crm_eval.py` `judge` | System map | 1 Nov | Fixed in v3 |
| 18 | Product | Fail-open on silence | Every act rests on the model finding nothing material; a missed conflict trips no check | `ai-stack/warrant.py` `decide`; 11 of 11 acts in v2 | System map | 1 Nov | Proposed: measure miss rate |
| 19 | Product | Untested surface | 0 adversarial cases, though agent rationale and contract text enter the prompt | `ai-stack/evals/crm_cases.json` | System map | 1 Nov | Started in v3: 5 injection cases, all model-written |
| 20 | Product | Unverified identity | Traces log the requested model while server-side fallback is on | `ai-stack/llm.py`, `warrant.py` `ask_compare` | System map | 1 Nov | Fixed in v3: served model logged |
| 21 | Eval | Wrong answer key | 3 clean controls actually had defects; the gate was right | PR 1, CT-02, CT-04, CT-10 | The gate's own holds | 1 Nov | Fixed; audit added |
| 22 | Eval | Correlated checker | One model wrote the cases, prompt rules, audit and judge | Git history of `crm_cases.py`, `warrant.py`, `crm_eval.py` | System map | 1 Nov | Proposed: blind cases, human labels |
| 23 | Eval | Unmeasured noise | A rerun of the same data moved a model-scored outcome by 1.9 points; the gate itself has run once per version | Learnings; `runs/` | Rerun | 31 Oct | Fixed in v3: five runs per case |
| 24 | Product | Right for the wrong reason | Sonnet sometimes wrote malformed JSON, then a self-correction. The gate could not parse it and held, so IN-01 counted as a catch and two cases flipped | `ai-stack/runs/v3-20261102T0521` | Reading stored raw answers while chasing flips | 2 Nov | Fixed: schema enforced, unreadable replies counted |
| 25 | Eval | Wrong answer key | CT-09 proposed a grant of 0 seats. The model questioned it on 3 of 5 runs, reasonably | `ai-stack/crm_cases.py` | Five runs per case | 2 Nov | Fixed: case rewritten, disclosed |
| 26 | Build | Own rule broken | The repeat loop kept decisions but dropped records, right after a change meant to store every answer | `ai-stack/crm_eval.py` | Needing the data to explain a flip | 2 Nov | Fixed: repeats written to file |
| 27 | Product | Passed tests, failed live | The first live agent run committed a second credit for the same incident. Every eval passed; Chargebee's credit list showed nothing for over a minute after the write, and the gate trusted the empty list | `ai-stack/runs/v3-agent-*` | Running a real agent against a real system | 2 Nov | Fixed: gate keeps a commit ledger, and holds when balance exceeds listed credits |
| 28 | Build | Test not independent | The fixture had one record per source that was always current, so the lag could not appear in any test | `ai-stack/evals/crm_cases.json` | Same live run | 2 Nov | Fault tests added; fixtures still cannot model unknown lags |

## Patterns so far

1. **The harmful failures looked competent.** Nearly all of them read as well-formed work, and none announced itself.
2. **Catches came from outside the writer's reasoning:** traces, recounts, a scan, a person. Rereading its own output caught few.
3. **Persistence amplifies.** A slightly wrong belief is cheap in one reply; saved to memory and summarised, it gets acted on later without its original context.
4. **The same pattern repeats across levels.** Row 14 sits in the very gate built to stop it, so writing about a failure does not protect against it.
