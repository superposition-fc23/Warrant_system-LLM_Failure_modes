"""Draws the architecture and data flow diagrams as standalone SVG files. The report and the deck carry inline copies.

    python3 product/diagrams/draw.py
"""
import os
import re

LIGHT = {"--fg": "#141c24", "--fg-2": "#46525f", "--fg-3": "#6f7d8c", "--rule": "#d5dce4", "--rule-2": "#bfc9d4", "--surface": "#ffffff",
         "--surface-2": "#f4f6f8", "--accent": "#0f5f8f", "--accent-soft": "#ddeaf4", "--warn": "#8a5a00", "--warn-soft": "#f8eed6",
         "--body": "-apple-system, Helvetica, Arial, sans-serif"}


class Fig:
    def __init__(self, w, h, mid, label):
        self.w, self.h, self.mid, self.label, self.parts = w, h, mid, label, []

    def text(self, x, y, s, size=12, color="--fg-2", anchor="start", weight=400):
        self.parts.append(f'<text x="{x}" y="{y}" style="font-family:var(--body);font-size:{size}px;font-weight:{weight};fill:var({color});text-anchor:{anchor}">{s}</text>')

    def lane(self, x, y, w, h, title):
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" style="fill:none;stroke:var(--rule)"/>')
        self.text(x + 10, y + 16, title, 11, "--fg-3", weight=600)

    def node(self, x, y, w, h, title, sub=None, kind="code", dashed=False):
        fill, stroke = {"code": ("--surface-2", "--rule-2"), "model": ("--accent-soft", "--accent"), "out": ("--warn-soft", "--warn")}[kind]
        dash = ";stroke-dasharray:5 4" if dashed else ""
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" style="fill:var({fill});stroke:var({stroke}){dash}"/>')
        cx = x + w / 2
        if sub:
            self.text(cx, y + h / 2 - 2, title, 13.5, "--fg", "middle", 600)
            self.text(cx, y + h / 2 + 14, sub, 11.5, "--fg-2", "middle")
        else:
            self.text(cx, y + h / 2 + 5, title, 13.5, "--fg", "middle", 600)

    def edge(self, d, dashed=False, both=False, color="--fg-3"):
        dash = ";stroke-dasharray:5 4" if dashed else ""
        start = f' marker-start="url(#{self.mid})"' if both else ""
        self.parts.append(f'<path d="{d}" style="fill:none;stroke:var({color});stroke-width:1.3{dash}" marker-end="url(#{self.mid})"{start}/>')

    def svg(self, attrs='style="width:100%;height:100%"', background=False):
        bg = f'<rect width="{self.w}" height="{self.h}" style="fill:var(--surface)"/>' if background else ""
        marker = (f'<defs><marker id="{self.mid}" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
                  '<path d="M0 0L8 4L0 8Z" style="fill:var(--fg-3)"/></marker></defs>')
        return f'<svg viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{self.label}" {attrs}>{marker}{bg}{"".join(self.parts)}</svg>'


def architecture():
    f = Fig(1200, 500, "wa", "Warrant v3 architecture. A live support agent calls one credit tool, which sends each proposal through a fixed pipeline of code steps with one model step. "
            "An act writes to the Chargebee test site. A hold posts a Slack card, and a person can keep it held, commit it, or make a standing rule.")
    f.lane(10, 6, 1180, 86, "AGENT AND PEOPLE")
    f.node(20, 30, 120, 52, "Tickets", "scripted", dashed=True)
    f.node(170, 30, 170, 52, "Support agent", "Sonnet 5.5, in a loop", "model")
    f.node(370, 30, 190, 52, "issue_credit tool", "the agent's one tool")
    f.node(800, 30, 200, 52, "Person in Slack", "keep, commit or make a rule")
    f.edge("M140 56H170")
    f.edge("M340 56H370")

    f.lane(10, 118, 994, 114, "WARRANT GATE: A FIXED LANGGRAPH PIPELINE, NOT AN AGENT")
    x = lambda col: 20 + col * 110
    steps = [("read_sources", "parallel, 4 s each"), ("freshness", "per source"), ("checks", "limits, ledger"), ("rules", "standing rules"),
             ("compare", "one model call"), ("decide", "code only"), ("reread", "before any act")]
    for i, (a, b) in enumerate(steps):
        f.node(x(i), 142, 96, 58, a, b, "model" if a == "compare" else "code")
        if i:
            f.edge(f"M{x(i) - 14} 171H{x(i)}")
    f.node(x(7), 140, 96, 28, "commit")
    f.node(x(7), 174, 96, 28, "route")
    f.node(x(8), 142, 96, 58, "record", "every path")
    f.edge(f"M{x(6) + 96} 164L{x(7)} 154")
    f.edge(f"M{x(6) + 96} 180L{x(7)} 188")
    f.edge(f"M{x(7) + 96} 154L{x(8)} 164")
    f.edge(f"M{x(7) + 96} 188L{x(8)} 180")
    f.edge(f"M{x(5) + 48} 200V216H{x(7) + 48}V202")
    f.text(x(6) + 8, 228, "hold, gather", 11.5)

    f.edge("M420 82V118")
    f.text(428, 110, "proposal", 11.5)
    f.edge("M390 118V82")
    f.text(382, 110, "decision", 11.5, anchor="end")
    f.edge("M530 82V104H1060V142")
    f.text(540, 100, "act only: writes the credit", 11.5)
    f.edge("M893 188V82")
    f.text(899, 112, "card", 11.5)
    f.node(1022, 142, 158, 58, "Chargebee write", "test site, promo credit", "out")
    f.edge("M1000 56H1120V142")
    f.text(1010, 48, "Commit, if billing has not moved", 11.5)

    f.lane(10, 246, 994, 164, "SOURCES, MODEL AND STATE")
    f.node(20, 270, 460, 44, "Read-only MCP server", "5 tools, nothing here writes")
    for i, (a, b, live) in enumerate([("HubSpot", "test, live", True), ("Chargebee", "test, live", True), ("Contracts", "local", False), ("Risk", "local", False), ("Authority", "local", False)]):
        f.node(20 + i * 94, 346, 84, 52, a, b, dashed=not live)
        f.parts.append(f'<line x1="{62 + i * 94}" y1="314" x2="{62 + i * 94}" y2="346" style="stroke:var(--fg-3);stroke-width:1"/>')
    f.edge(f"M{x(0) + 48} 200V270", both=True)
    f.text(x(0) + 56, 242, "records", 11.5)
    f.node(500, 270, 150, 58, "Anthropic API", "schema enforced", "model")
    f.edge(f"M{x(4) + 48} 200V270", both=True)
    f.text(x(4) + 56, 242, "names redacted", 11.5)
    f.node(670, 270, 190, 58, "Local state", "rules, ledger, boundary")
    f.edge("M765 232V270", both=True)
    f.node(880, 270, 114, 58, "Decision log", "beliefs, checks")
    f.edge(f"M{x(8) + 48} 200V270")
    f.edge("M1000 72H1012V256H810V270")
    f.text(820, 268, "standing rule", 11.5)

    f.text(1022, 276, "Blue: a model", 12, "--accent", weight=600)
    f.text(1022, 296, "Amber: the money write", 12, "--warn", weight=600)
    f.text(1022, 316, "Grey: code", 12, weight=600)
    f.text(1022, 336, "Dashed: scripted, local", 12, weight=600)
    f.text(1022, 352, "or planned", 12, weight=600)

    f.lane(10, 422, 1180, 72, "PROOF AROUND THE GATE: NEVER DECIDES")
    for i, (a, b, k, d) in enumerate([("Eval runner", "36 cases, 5 runs", "code", False), ("Judge", "Opus 5.5, redacted", "model", False), ("Gate tests", "19, no model calls", "code", False),
                                      ("OpenTelemetry", "a span per step", "code", False), ("PII, secret scan", "pre-commit and CI", "code", False),
                                      ("Prototype", "boundary, shadow, review", "code", False), ("SageOx", "planned", "code", True)]):
        f.node(20 + i * 166, 442, 156, 44, a, b, k, d)
    f.edge("M937 328V422")
    f.text(929, 372, "records, traces", 11.5, anchor="end")
    return f


def data_flow():
    f = Fig(1200, 556, "wf", "Warrant v3 data flow. Data leaves the process on six paths: the agent's own model calls without redaction, CRM and billing reads, "
            "the compare call with names redacted, the credit write, the Slack card with names restored, and the eval judge with names redacted.")
    f.text(20, 16, "INSIDE OUR PROCESS", 11, "--fg-3", weight=600)
    f.text(900, 16, "LEAVES OUR PROCESS", 11, "--warn", weight=600)
    f.parts.append('<line x1="870" y1="4" x2="870" y2="552" style="stroke:var(--warn);stroke-width:1.3;stroke-dasharray:6 4"/>')
    out = lambda y, a, b: f.node(900, y, 280, 50, a, b, "out")

    f.node(20, 30, 130, 50, "Ticket", "scripted", dashed=True)
    f.node(190, 30, 170, 50, "1 Agent loop", "Sonnet 5.5", "model")
    out(30, "Anthropic: agent", "not redacted")
    f.edge("M150 55H190")
    f.edge("M360 55H900", both=True)
    f.text(372, 48, "ticket text, proposal, tool results: not redacted", 12)
    f.edge("M275 80V120")
    f.text(283, 104, "proposal: account, amount, incident, rationale", 12)

    f.node(20, 120, 130, 50, "Local records", "contracts, risk, limits", dashed=True)
    f.node(190, 120, 170, 50, "2 Read sources", "code, 4 s budget each")
    out(120, "HubSpot, Chargebee", "test accounts")
    f.edge("M150 145H190")
    f.edge("M360 145H900", both=True)
    f.text(372, 138, "account ID out; records and timestamps back", 12)
    f.edge("M275 170V210")

    f.node(190, 210, 170, 50, "3 Code checks", "fresh, limits, ledger")
    f.node(420, 210, 170, 50, "4 Redact, restore", "code")
    out(210, "Anthropic: compare", "JSON, schema enforced")
    f.edge("M360 235H420")
    f.text(366, 228, "all pass", 11.5)
    f.edge("M590 235H900", both=True)
    f.text(600, 228, "names as tokens; contract text, amounts stay", 12)

    f.node(190, 300, 170, 50, "5 Decide", "code: act, gather, hold")
    f.edge("M275 260V300")
    f.text(283, 284, "a check fails: no model call", 12)
    f.edge("M505 260V313H360")
    f.text(373, 306, "limits, conflicts", 12)
    f.node(560, 300, 190, 50, "6 Reread, commit", "then ledger entry")
    out(300, "Chargebee write", "test site")
    f.edge("M360 338H560")
    f.text(440, 332, "act", 12, weight=600)
    f.edge("M750 325H900")
    f.text(760, 318, "credit", 12)

    f.node(190, 390, 170, 50, "7 Route question", "hold or gather")
    out(390, "Slack", "card, buttons")
    f.edge("M275 350V390")
    f.text(283, 374, "hold, gather", 12)
    f.edge("M360 403H900")
    f.text(372, 397, "reason and question, names restored", 12)
    f.node(560, 418, 190, 46, "8 Ruling", "keep, commit, make rule")
    f.edge("M900 430H750")
    f.text(760, 449, "the click", 12)
    f.edge("M655 418V350")
    f.text(663, 386, "commit, if unchanged", 12)
    f.node(20, 418, 130, 46, "Rule store", "owner, scope, expiry")
    f.edge("M560 452H150")
    f.text(372, 468, "standing rule", 12)
    f.edge("M85 418V325H190")
    f.text(93, 318, "next match: no", 11.5)
    f.text(93, 332, "model, no card", 11.5)

    f.node(190, 490, 170, 50, "9 Decision record", "traces; every path")
    f.edge("M275 440V490")
    f.node(490, 490, 190, 50, "10 Evals, prototype", "judge names redacted")
    f.edge("M360 515H490")
    out(490, "Anthropic: judge", "eval time only")
    f.edge("M680 515H900")
    f.text(690, 508, "expected and named fact", 12)
    return f


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    for name, fig in (("warrant-architecture", architecture()), ("warrant-data-flow", data_flow())):
        s = fig.svg('xmlns="http://www.w3.org/2000/svg"', background=True)
        s = re.sub(r"var\((--[\w-]+)\)", lambda m: LIGHT[m.group(1)], s)
        open(os.path.join(here, name + ".svg"), "w").write(s + "\n")
