"""Voice of customer from public forums: a stand-in for JTBD interviews until real ones are run.

Collects public opinions about AI agents in support and multi-agent workflows, classifies each into a desired
outcome (O1 to O9 from index.html step 3d; O9 added for P3) with an inferred job performer, importance and satisfaction (1 to 10,
Ulwick's sense: how much the outcome matters to them; how well today's tools deliver it), and aggregates an
opportunity score per outcome. Sources: Hacker News (Algolia API, no auth); Reddit via its official Data API (app-only OAuth, keys in .env);
Medium tag RSS where it responds. Medium and Substack are otherwise gathered by domain-restricted search and read
by an agent into evals/voc_web.json, which collect() merges in.

    .venv/bin/python voc.py collect      # -> evals/voc_raw.json
    .venv/bin/python voc.py classify     # -> evals/voc_classified.json (Haiku, about 300 calls)
    .venv/bin/python voc.py reddit       # search-API results for Reddit, snippets only, capped at 100 URLs, merged into voc_classified.json
    .venv/bin/python voc.py report       # -> evals/voc_report.md

This is opinion mining, not interviews. The biases are listed in the report it writes.
"""
import html
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

import httpx

from llm import ask  # also loads .env
from pii import scrub

# Full third-party text stays in this gitignored cache; committed files keep the link and classification only
CACHE = ".voc_cache"
RAW_CACHE, WEB_CACHE = f"{CACHE}/voc_raw.json", f"{CACHE}/voc_web.json"

QUERIES = [
    "AI agents conflicting decisions", "multi-agent system conflict", "AI support agent refund mistake",
    "AI agent issued credit wrong", "Agentforce agents production", "Zendesk AI agent", "AI customer support agent escalation",
    "human in the loop approval fatigue", "AI agent autonomy guardrails production", "LLM agents disagree",
    "AI agent hallucinated policy refund", "agentic AI customer service failure", "AI triage ticket severity wrong",
    "AI agent bug or feature request triage", "agent observability evals production",
    "AI chatbot gave refund", "Air Canada chatbot refund", "Klarna AI assistant customer service", "AI agent approval workflow",
    "agents overwriting each other", "AI agent took wrong action production", "AI support bot contradicts", "LLM agent permissions RBAC",
    "AI agent audit trail", "when to let AI agents act autonomously", "AI agents shared state coordination", "AI customer service escalation to human",
    "AI agent cost of mistakes", "AI agents billing errors", "trust AI agents enterprise",
    # P3, severity and SLA (added 1 Nov). Short on purpose: Algolia matches every word, and the first long phrasings
    # returned zero hits (a recall failure, not evidence). The last two are written to disconfirm: they look for satisfaction.
    "ticket triage", "SLA breach", "incident severity", "auto triage", "ticket priority AI", "on-call severity",
    "triage LLM", "AI ticket triage works well", "PagerDuty severity automation",
]
FEEDS = ["ai-agents", "agentic-ai", "customer-support", "multi-agent-systems"]
OUTCOMES = {
    "O1": "Minimise money actions committed while evidence across systems disagrees",
    "O2": "Minimise the time to know which conclusion should govern a disputed ticket, and on what basis",
    "O3": "Minimise human reviews spent on cases agents could have settled",
    "O4": "Minimise contradictory statements made to the same customer",
    "O5": "Minimise the time to detect that an autonomy boundary is set wrong",
    "O6": "Maximise confidence that widening autonomy has not raised reopens or clawbacks",
    "O7": "Minimise exposure of restricted data when a case is escalated",
    "O8": "Minimise the effort to trace a reversed action to its evidence",
    "O9": "Minimise the time a ticket or incident sits at the wrong severity or SLA tier",
}
PERFORMERS = ["support or applied AI engineer", "CSM", "finance or RevOps", "VP or exec buyer", "end customer", "other"]
UA = {"User-Agent": "voc-research/0.1 (product discovery; contact via repo owner)"}


def clean(text):
    return scrub(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(text or ""))).strip())


def hacker_news(q):
    r = httpx.get("https://hn.algolia.com/api/v1/search", params={"query": q, "tags": "comment", "hitsPerPage": 15}, timeout=20)
    return [{"source": "hackernews", "url": f"https://news.ycombinator.com/item?id={h['objectID']}",
             "date": h.get("created_at", "")[:10], "text": clean(h.get("comment_text"))} for h in r.json().get("hits", [])]


_reddit_token = None


def reddit(q):
    # Official Data API, app-only OAuth (read-only). Needs a free "script" app from reddit.com/prefs/apps
    # with REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env. Without them Reddit is skipped, not scraped.
    global _reddit_token
    cid, secret = os.getenv("REDDIT_CLIENT_ID"), os.getenv("REDDIT_CLIENT_SECRET")
    if not (cid and secret):
        return []
    if _reddit_token is None:
        t = httpx.post("https://www.reddit.com/api/v1/access_token", data={"grant_type": "client_credentials"},
                       auth=(cid, secret), headers=UA, timeout=20)
        _reddit_token = t.json().get("access_token")
    r = httpx.get("https://oauth.reddit.com/search", params={"q": q, "limit": 10, "sort": "relevance", "type": "link"},
                  headers={**UA, "Authorization": f"bearer {_reddit_token}"}, timeout=20)
    if r.status_code != 200:
        return []
    out = []
    for c in r.json().get("data", {}).get("children", []):
        d = c["data"]
        out.append({"source": f"reddit r/{d.get('subreddit')}", "url": "https://www.reddit.com" + d.get("permalink", ""),
                    "date": "", "text": clean(d.get("title", "") + ". " + d.get("selftext", ""))})
    return out


def medium(tag):
    r = httpx.get(f"https://medium.com/feed/tag/{tag}", headers=UA, timeout=20, follow_redirects=True)
    if r.status_code != 200:
        return []
    items = ET.fromstring(r.content).iter("item")
    ns = "{http://purl.org/rss/1.0/modules/content/}encoded"
    return [{"source": "medium", "url": i.findtext("link"), "date": (i.findtext("pubDate") or "")[:16],
             "text": clean((i.findtext("title") or "") + ". " + (i.findtext(ns) or ""))[:2500]} for i in items]


# Reddit through a search API, added in v3. Reddit's agreement reportedly bars scraping without consent and its pages refused automated
# reads, so nothing here fetches reddit.com: rows hold what the search result returned. Snippets are thin, so label them as such.
REDDIT_CAP = 100
REDDIT_QUERIES = [
    "multi-agent conflict production", "AI support agent refund mistake", "Zendesk AI agent wrong refund", "Agentforce production problems",
    "Intercom Fin wrong answer customers", "AI agent credit customer wrong", "AI agents overwriting each other", "AI agent stale data wrong decision",
    "human in the loop approval fatigue agents", "AI agent audit trail who approved", "CRM and billing data don't match AI agent",
    "AI customer service escalation to human bad", "when to let AI agents act autonomously",
    # Written to disconfirm: these look for people satisfied with what they have.
    "AI support agent works well for us", "AI chatbot reduced support tickets success", "agent guardrails solved our problem",
]


def serper(q):
    out = []
    for page in (1, 2):
        r = httpx.post("https://google.serper.dev/search", headers={"X-API-KEY": os.environ["SERPER_API_KEY"]},
                       json={"q": f"site:reddit.com {q}", "num": 10, "page": page}, timeout=20)
        r.raise_for_status()
        out += r.json().get("organic", [])
    return out


def reddit_search():
    rows, seen = [], set()
    with ThreadPoolExecutor(4) as ex:
        results = list(ex.map(lambda q: _safe(serper, q), REDDIT_QUERIES))
    for res in results:
        for it in res:
            url = it.get("link", "").split("?")[0]
            m = re.search(r"reddit\.com/r/([^/]+)/comments/", url)
            text = clean(f"{it.get('title', '')}. {it.get('snippet', '')}")
            if not m or url in seen or len(text) < 60 or len(rows) >= REDDIT_CAP:
                continue
            seen.add(url)
            rows.append({"source": f"reddit-search r/{m.group(1)}", "url": url, "date": it.get("date"), "evidence": "search snippet", "text": scrub(text)})
    with ThreadPoolExecutor(8) as ex:
        classified = list(ex.map(classify_one, rows))
    os.makedirs(CACHE, exist_ok=True)
    json.dump(rows, open(f"{CACHE}/voc_reddit.json", "w"), indent=1)
    for r in classified:
        r["quote"] = " ".join((r.get("quote") or "").split()[:20])    # the model is asked for 20 words and sometimes writes more
    keep = [r for r in json.load(open("evals/voc_classified.json")) if not r["source"].startswith("reddit-search")]
    json.dump(keep + _public(classified), open("evals/voc_classified.json", "w"), indent=1)
    rel = [r for r in classified if r.get("relevant") and r.get("outcome") in OUTCOMES]
    print(f"reddit: {len(rows)} URLs, {len(rel)} relevant with an outcome, {sum(1 for r in classified if r.get('error'))} errors")


def _public(rows):
    return [{k: v for k, v in r.items() if k != "text"} for r in rows]


def collect():
    web = json.load(open(WEB_CACHE)) if os.path.exists(WEB_CACHE) else []
    jobs = [(hacker_news, q) for q in QUERIES] + [(reddit, q) for q in QUERIES] + [(medium, t) for t in FEEDS]
    items, seen = [], set()
    for it in web:
        if it["url"] not in seen:
            seen.add(it["url"]); items.append(it)
    with ThreadPoolExecutor(8) as ex:
        for res in ex.map(lambda j: _safe(*j), jobs):
            for it in res:
                if it["url"] not in seen and len(it["text"]) > 120:
                    seen.add(it["url"]); items.append(it)
    os.makedirs(CACHE, exist_ok=True)
    json.dump(items, open(RAW_CACHE, "w"), indent=1)
    json.dump(_public(items), open("evals/voc_raw.json", "w"), indent=1)
    by = {}
    for it in items:
        by[it["source"].split()[0]] = by.get(it["source"].split()[0], 0) + 1
    print(f"collected {len(items)} items: {by}")


def _safe(fn, arg):
    try:
        return fn(arg)
    except Exception as e:
        print(f"  {fn.__name__}({arg!r}) failed: {type(e).__name__}")
        return []


SYSTEM = ("You classify public opinions for product research on AI agents that take actions in business workflows: customer "
          "support, operations, finance, and coding or multi-agent setups where agents coordinate, conflict, or need human approval. "
          "The outcomes are general; map a comment to the closest one if it expresses a need or frustration about it. "
          "Mark irrelevant only if it is not about AI agents or automation acting on someone's behalf. Return only a JSON object.")


def classify_one(it):
    outcomes = "\n".join(f"{k}: {v}" for k, v in OUTCOMES.items())
    prompt = (f"Text ({it['source']}):\n{it['text'][:2000]}\n\nDesired outcomes:\n{outcomes}\n\n"
              f"Return JSON: relevant (true/false), outcome (one ID above or null), performer (one of {PERFORMERS}), "
              "importance (1-10: how much the author cares about that outcome), satisfaction (1-10: how well the author says "
              "current tools or practices deliver it; 5 if not stated), quote (the author's own words, at most 20 words), "
              "rationale (one sentence).")
    try:
        out = ask("haiku-5.5", prompt, system=SYSTEM, max_tokens=1500, effort="low")
        return {**it, **json.loads(re.search(r"\{.*\}", out, re.S).group())}
    except Exception as e:
        return {**it, "relevant": False, "error": type(e).__name__}


def classify():
    items = json.load(open(RAW_CACHE))
    with ThreadPoolExecutor(8) as ex:
        rows = list(ex.map(classify_one, items))
    json.dump(_public(rows), open("evals/voc_classified.json", "w"), indent=1)
    rel = [r for r in rows if r.get("relevant") and r.get("outcome") in OUTCOMES]
    print(f"classified {len(rows)}; relevant with an outcome: {len(rel)}")


def report():
    rows = [r for r in json.load(open("evals/voc_classified.json")) if r.get("relevant") and r.get("outcome") in OUTCOMES]
    # All relevant rows. Never select on importance: ranking by the scored field and then averaging it inflates the mean.
    lines = [f"# Voice of customer: {len(rows)} public opinions classified\n",
             "Opinion mining from Hacker News, Substack and Reddit search snippets (Medium pending), classified by Haiku. Not interviews. See biases at the end.\n",
             "| Outcome | n | Mean importance | Mean satisfaction | Opportunity | Top performer |", "|---|---|---|---|---|---|"]
    agg = {}
    for k in OUTCOMES:
        g = [r for r in rows if r["outcome"] == k]
        if not g:
            lines.append(f"| {k} | 0 | | | | |"); continue
        i = sum(r["importance"] for r in g) / len(g); s = sum(r["satisfaction"] for r in g) / len(g)
        top = max(set(r["performer"] for r in g), key=[r["performer"] for r in g].count)
        agg[k] = (len(g), round(i, 1), round(s, 1), round(i + max(i - s, 0), 1), top)
        lines.append(f"| {k} | {len(g)} | {i:.1f} | {s:.1f} | {i + max(i - s, 0):.1f} | {top} |")
    src = {}
    for r in rows:
        src[r["source"].split()[0]] = src.get(r["source"].split()[0], 0) + 1
    perf = {}
    for r in rows:
        perf[r["performer"]] = perf.get(r["performer"], 0) + 1
    lines += ["", f"Sources: {src}", f"Performers: {perf}", "", "## Per source: an outcome that only ranks high in one source is suspect", "",
              "| Outcome | Hacker News n, opp. | Substack n, opp. | Reddit snippets n, opp. |", "|---|---|---|---|"]
    def cell(k, prefix):
        g = [r for r in rows if r["outcome"] == k and r["source"].startswith(prefix)]
        if not g:
            return "0"
        i = sum(r["importance"] for r in g) / len(g); t = sum(r["satisfaction"] for r in g) / len(g)
        return f"{len(g)}, {i + max(i - t, 0):.1f}"
    srcs = sorted({r["source"].split()[0] for r in rows})
    hn = next((x for x in srcs if x.lower().startswith(("hacker", "hn"))), "hacker")
    for k in OUTCOMES:
        lines.append(f"| {k} | {cell(k, hn)} | {cell(k, 'substack')} | {cell(k, 'reddit-search')} |")
    lines += ["", "## Example quotes per outcome", ""]
    for k in OUTCOMES:
        for r in [r for r in rows if r["outcome"] == k][:2]:
            lines.append(f"- **{k}** ({r['source']}, {r['performer']}, I{r['importance']}/S{r['satisfaction']}): \"{r.get('quote', '')}\" {r['url']}")
    lines += ["", "## Biases (this is a failure mode, not just a caveat)",
              "- Selection: forum authors skew to developers and complainers; VPs and finance analysts rarely post.",
              "- Query bias: the search terms were written from my hypothesis, so they find what I expected.",
              "- Judge bias: a model infers importance and satisfaction from text; belief is bias, and so is the judge.",
              "- Not our customers: no evidence these authors run multi-agent support workflows.",
              "- Recency and platform: Medium skews to vendor content marketing.",
              "- Reddit rows are search snippets, not threads: ranked by a search engine, thin on context, so satisfaction often sits at the default of 5."]
    open("evals/voc_report.md", "w").write("\n".join(lines))
    json.dump(agg, open("evals/voc_agg.json", "w"), indent=1)
    print("\n".join(lines[:14]))


if __name__ == "__main__":
    {"collect": collect, "classify": classify, "reddit": reddit_search, "report": report}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
