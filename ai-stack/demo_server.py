"""The local server behind the prototype's Live demo tab, so the live path runs from one click.

Bound to this machine. It serves only the prototype, report, slides and run data, and it can do only two things: start the demo clean, or run it again. It takes no commands and shows no logs, so no key can reach the screen.

    Double-click "Warrant Demo.command", or: .venv/bin/python demo_server.py
"""
import glob
import json
import os
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PORT = 8765
PAGE = {"/": "prototype.html", "/prototype.html": "prototype.html", "/index.html": "index.html", "/slides.html": "slides.html", "/ai-stack/runs/sample/prototype-data.js": "ai-stack/runs/sample/prototype-data.js",
        "/ai-stack/runs/latest/prototype-data.js": "ai-stack/runs/latest/prototype-data.js"}
STATE_FILES = ["rules.json", "ledger.jsonl", "beliefs.json"]
STATE_DIR = os.path.join(HERE, "state")
RUNS_DIR = os.path.join(HERE, "runs")
COMMAND = [sys.executable, "agent.py", "v4", "slack", "belief-only", "1200"]
TICKETS = 3
STUCK_AFTER = 180
lock = threading.Lock()
run = {"proc": None, "dir": None, "started": 0.0, "clean": False}
free_accounts = {"count": None}


def read_rows(name):
    path = os.path.join(run["dir"] or "", name)
    if not run["dir"] or not os.path.exists(path):
        return []
    return [json.loads(l) for l in open(path) if l.strip()]


def working():
    """True while tickets are still being worked, when stopping the run could cut a write in half."""
    p = run["proc"]
    return bool(p and p.poll() is None and len(read_rows("tickets.jsonl")) < TICKETS and time.time() - run["started"] < STUCK_AFTER)


def start(clean):
    with lock:
        if working():
            return False
        if run["proc"] and run["proc"].poll() is None:
            run["proc"].terminate()    # only waiting on Slack by now
            run["proc"].wait(timeout=10)
        if clean:
            for name in STATE_FILES:
                path = os.path.join(STATE_DIR, name)
                if os.path.exists(path):
                    os.remove(path)
        os.makedirs(STATE_DIR, exist_ok=True)
        run["dir"] = os.path.join(RUNS_DIR, "demo-" + time.strftime("%Y%m%dT%H%M%S", time.gmtime()))
        os.makedirs(run["dir"], exist_ok=True)
        log = open(os.path.join(STATE_DIR, "demo-server.log"), "a")
        run["proc"] = subprocess.Popen(COMMAND, cwd=HERE, env={**os.environ, "WARRANT_RUN_DIR": run["dir"]}, stdout=log, stderr=subprocess.STDOUT)
        run["started"], run["clean"] = time.time(), clean
    return True


def reliability():
    path = os.path.join(STATE_DIR, "beliefs.json")
    table = json.load(open(path)) if os.path.exists(path) else json.load(open(os.path.join(HERE, "belief_priors.json")))["sources"]
    b = table["billing"]
    return round(b["alpha"] / (b["alpha"] + b["beta"]), 4)


def status():
    rulings = {r["record_id"]: r for r in read_rows("rulings.jsonl")}
    tickets = []
    for row in read_rows("tickets.jsonl"):
        for x in row["records"]:
            rec, b = x["record"], x["record"].get("belief") or {}
            r = rulings.get(rec["record_id"], {})
            tickets.append({"ticket": row["ticket"], "agent": row["agent"], "account": rec["action"]["account_id"], "amount": rec["action"]["amount"], "decision": rec["decision"], "status": x["tool_result"]["status"],
                            "p_safe": b.get("p_safe"), "vetoed_by": b.get("vetoed_by"), "wait_seconds": b.get("wait_seconds"), "fact": rec["discriminating_fact"],
                            "ruling": r.get("ruling"), "ruling_note": r.get("note"), "seconds_to_ruling": r.get("seconds_to_ruling"), "belief_update": r.get("belief_update")})
    p = run["proc"]
    code = p.poll() if p else None
    if not p:
        phase = "idle"
    elif code not in (None, 0) and code != -15:
        phase = "failed"
    elif working():
        phase = "working"
    elif code is None:
        phase = "waiting"
    else:
        phase = "finished"
    return {"phase": phase, "tickets": tickets, "billing_reliability": reliability(), "prior_reliability": 0.995, "free_accounts": free_accounts["count"], "cards_open": sum(1 for t in tickets if t["decision"] != "act" and not t["ruling"])}


def count_free_accounts():
    import live_sources
    import seed_live
    from dotenv import load_dotenv
    load_dotenv(os.path.join(HERE, ".env"))
    while True:
        try:
            free_accounts["count"] = sum(1 for n in range(1, seed_live.POOL + 1) if not live_sources.chargebee("GET", f"/customers/ACC-30{n:02d}")["customer"].get("promotional_credits"))
        except Exception:
            free_accounts["count"] = None
        time.sleep(60)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def allowed_origins(self):
        port = self.server.server_address[1]
        return {f"127.0.0.1:{port}", f"localhost:{port}"}

    def host_ok(self):
        return self.headers.get("Host") in self.allowed_origins()

    def send(self, code, body, kind="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.split("?")[0]
        if not self.host_ok():
            return self.send(403, {"error": "forbidden"})
        if path == "/api/status":
            return self.send(200, status())
        if path in PAGE and os.path.exists(os.path.join(ROOT, PAGE[path])):
            kind = "text/html; charset=utf-8" if PAGE[path].endswith(".html") else "text/javascript; charset=utf-8"
            return self.send(200, open(os.path.join(ROOT, PAGE[path]), "rb").read(), kind)
        self.send(404, {"error": "not found"})

    def do_POST(self):
        origin = (self.headers.get("Origin") or "").replace("http://", "")
        if not self.host_ok() or origin not in self.allowed_origins() or self.headers.get("X-Warrant-Demo") != "1":
            return self.send(403, {"error": "forbidden"})
        if self.path not in ("/api/start", "/api/again"):
            return self.send(404, {"error": "not found"})
        if not start(clean=self.path == "/api/start"):
            return self.send(409, {"error": "the agent is still working"})
        self.send(200, {"ok": True})


def main():
    try:
        server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    except OSError:
        print(f"Already running at http://127.0.0.1:{PORT}")
        return
    threading.Thread(target=count_free_accounts, daemon=True).start()
    print(f"Warrant demo: http://127.0.0.1:{PORT}  Close this window to stop.", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
