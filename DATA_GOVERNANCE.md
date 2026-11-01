# Data governance

This repo is built in public, so anything committed is treated as published permanently. Git history counts.

| Data | Class | Rule |
|---|---|---|
| Accounts, people and amounts in `ai-stack/crm_cases.py` and `ai-stack/docs/` | Synthetic | Fictional by construction; never derived from a real customer |
| Forum text collected by `ai-stack/voc.py` | Public, third-party | Public sources only, through official APIs; no scraping around bot checks or paywalls. Full text stays in the gitignored `ai-stack/.voc_cache/`. Committed files keep only the link, date, classification, a short quote and a rationale |
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

The scan finds patterns: emails, phone numbers, known secret formats and blocked paths. It does not find a person's name in free text, so a model review also checked the short quotes and rationales before publishing. Neither proves zero, and source links still lead to the original public posts, where usernames show. This data is minimised, not anonymised.

## If something leaks

Treat it as published. Rotate any secret first. Then scrub history, and remember that GitHub keeps old commits reachable through pull request refs until GitHub Support removes them.
