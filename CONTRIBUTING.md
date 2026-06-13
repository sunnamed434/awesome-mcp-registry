# Contributing

This is an **AI-curated** registry. The list curates itself — a weekly job discovers MCP
servers, scores them with a published trust formula, and regenerates everything. That shapes how
you contribute.

## Suggesting a server → open a nomination, not a PR

**Do not open a pull request to add a server.** `README.md`, `SCORES.md`,
`data/known_servers.json`, and `data/star_history.jsonl` are **machine-generated** on every
weekly run, so any edit to them is overwritten — and PRs that touch them are **closed
automatically** by a bot.

Instead, **[open a nomination](https://github.com/sunnamed434/awesome-mcp-registry/issues/new?template=server-nomination.yml)**:

1. You provide the server's **public GitHub repository** URL.
2. On the next weekly scan, the **same AI** that curates the whole list evaluates it, and the
   pipeline computes its [trust score](METHODOLOGY.md) — 35% AI rubric, 65% verifiable metrics
   (maintenance, popularity, docs, security posture, community).
3. The bot posts the verdict **with the full score breakdown** on your issue and closes it. If
   the server scores **50+/100**, it appears in the README automatically. If not, it's recorded
   and re-evaluated later — if it improves, it can still make the list.

Only **open-source servers with a public GitHub repo** can be nominated — the AI needs a repo to
read. Hosted-only endpoints with no public source can't be evaluated.

There's no human approval step and no favouritism: the same gate applies to everything,
including servers discovered automatically. The scoring formula is public
([METHODOLOGY.md](METHODOLOGY.md)) and reproducible offline (`python scripts/recompute_trust.py`).

## How servers leave the list

Metrics and trust scores refresh **every week**; the AI re-judges every server roughly **every
90 days** against fresh data. If a project is abandoned, loses quality, or stops being a real
MCP server, its score drops and it falls off the list. You don't need to report dead projects —
the re-evaluation handles it.

## Exclusion list and maintainer opt-out

A small exclusion list at [`data/excluded-repos.txt`](data/excluded-repos.txt) is the only place
a human overrides the AI, reserved for two cases: repos removed for **policy reasons**
(spam, scam, malicious or deceptive content) and repos whose **maintainers asked not to be
listed**. Excluded repos are never analyzed, never listed, and nominations for them are declined
automatically with a link to the list.

- **Maintainer opt-out:** if you maintain a listed server and want it removed, open a regular
  issue from the repo's owner account (or with a verifiable link to it) and it will be added.
- **Appeals:** if you think a repo is excluded by mistake, open a regular issue (not a
  nomination) referencing the entry — the list is plain text with a reason next to each line,
  and every change to it is a reviewable commit.

## Code contributions are welcome

Bug fixes and improvements to the scanner, scoring, prompts, or workflows are genuinely
welcome — those PRs are **not** auto-closed. The relevant code lives in:

- `scripts/scan_repos.py` — discovery, AI analysis, re-evaluation, nomination intake
- `scripts/metrics.py` — raw GitHub / OpenSSF Scorecard metric collection
- `scripts/trust.py` — the pure trust-score formula (see [METHODOLOGY.md](METHODOLOGY.md))
- `scripts/utils.py` — README/SCORES generation and parsing helpers
- `scripts/test_trust.py` — unit tests (`python scripts/test_trust.py`)
- `prompts/analyzer.prompt.yml` — the AI evaluation prompt
- `.github/workflows/` — the automation

Open a normal PR for those. Just don't edit the generated files by hand — let the scanner
regenerate them.

## A note on AI mistakes

The verdicts are automated and not perfect. If you think the AI got your server wrong, comment on
the (closed) nomination issue — threads stay open for a few weeks before they lock, so there's a
window to flag genuine misjudgements. The per-server breakdown in [SCORES.md](SCORES.md) shows
exactly which component cost the points.
