# Data governance

This repo is built in public, so anything committed is treated as published permanently. Git history counts.

| Data | Class | Rule |
|---|---|---|
| Accounts, people and amounts in `ai-stack/crm_cases.py` and `ai-stack/docs/` | Synthetic | Fictional by construction; never derived from a real customer |
| Forum text collected by `ai-stack/voc.py` | Public, third-party | Public sources only, through official APIs; emails and phone numbers scrubbed before storage; each row keeps its source URL; no scraping around bot checks or paywalls |
| Articles, PDFs and private notes in `reference/` | Third-party or private | Gitignored; never committed |
| API keys in `.env` | Secret | Gitignored; only `.env.example` is tracked |
| Author identity | Personal | Commits use the GitHub noreply address |
| Run logs in `ai-stack/runs/` | Synthetic | Traces and decision records from synthetic cases only |

## Controls

- **Before a model call:** `warrant.py` replaces people and account names with tokens and restores them afterwards.
- **Before storage:** `pii.scrub()` runs on collected text.
- **Before a commit:** `.githooks/pre-commit` runs `ai-stack/pii.py scan --staged`. Enable it once per clone: `git config core.hooksPath .githooks`.
- **On every push:** the `pii-scan` workflow scans all tracked files, so a skipped hook is still caught.

## Limits

The scan finds patterns: emails, phone numbers, known secret formats and blocked paths. It does not find a person's name in free text, so forum text is public-source data with contact details removed, not anonymised data.

## If something leaks

Treat it as published. Rotate any secret first. Then scrub history, and remember that GitHub keeps old commits reachable through pull request refs until GitHub Support removes them.
