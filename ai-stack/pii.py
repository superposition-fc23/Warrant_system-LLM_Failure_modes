"""PII and secret guardrails. scrub() cleans text before it is stored; the scanner blocks a commit that would publish any.

    python3 ai-stack/pii.py scan             # every tracked file; used by CI
    python3 ai-stack/pii.py scan --staged    # staged files; used by the pre-commit hook

Standard library only, so the hook runs without the venv. Policy is in DATA_GOVERNANCE.md.
"""
import re
import subprocess
import sys

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE = re.compile(r"(?<![\w.-])(\+?1[ .-])?\(?[2-9][0-9]{2}\)?[ .-][0-9]{3}[ .-][0-9]{4}(?![\w-])")
SECRETS = {"Anthropic key": r"sk-ant-[A-Za-z0-9_-]{10,}", "OpenAI key": r"sk-[A-Za-z0-9]{20,}", "Google key": r"AIza[0-9A-Za-z_-]{20,}",
           "GitHub token": r"gh[pousr]_[A-Za-z0-9]{20,}", "AWS key": r"AKIA[0-9A-Z]{16}", "Private key": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
           "Assigned secret": r"(?:API_KEY|SECRET|TOKEN)=[A-Za-z0-9_-]{12,}"}
ALLOWED_EMAIL = re.compile(r"(^|@|\.)(users\.noreply\.github\.com|anthropic\.com|example\.(com|org|net))$", re.I)
BLOCKED_PATHS = re.compile(r"(^|/)(\.env|reference/.*|.*\.pem)$")


def scrub(text):
    """Remove contact details from third-party text before it is stored."""
    text = EMAIL.sub(lambda m: m.group(0) if ALLOWED_EMAIL.search(m.group(0).split("@")[1]) else "[email removed]", text or "")
    return PHONE.sub("[phone removed]", text)


def findings(path, text):
    for i, line in enumerate(text.splitlines(), 1):
        for m in EMAIL.finditer(line):
            if not ALLOWED_EMAIL.search(m.group(0).split("@")[1]):
                yield f"{path}:{i}: email address"
        if PHONE.search(line):
            yield f"{path}:{i}: phone number"
        for name, pattern in SECRETS.items():
            if re.search(pattern, line):
                yield f"{path}:{i}: {name}"


def main(staged):
    cmd = ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"] if staged else ["git", "ls-files"]
    problems = []
    for path in subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.splitlines():
        if path.endswith(".example"):
            continue
        if BLOCKED_PATHS.search(path):
            problems.append(f"{path}: this path must never be committed")
            continue
        show = ["git", "show", f":{path}"]
        raw = subprocess.run(show, capture_output=True).stdout
        if b"\0" not in raw:
            problems += findings(path, raw.decode("utf-8", "ignore"))
    for p in problems:
        print(p)            # location and type only, so the scan never repeats the value it found
    print(f"pii scan: {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main("--staged" in sys.argv) if sys.argv[1:2] == ["scan"] else print(__doc__))
