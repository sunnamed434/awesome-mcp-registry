# CLAUDE.md

The rules for this repository live in [AGENTS.md](AGENTS.md) — read it before opening an issue,
proposing a PR, or answering questions about this registry. The short version:

- AI-curated registry: servers are **nominated via issue forms**, never added by pull request.
- `README.md`, `SCORES.md`, `data/known_servers.json`, `data/star_history.jsonl` and `badges/**`
  are machine-generated — never edit them; PRs touching them are auto-closed.
- Never invent a trust score, category or verdict; read them from `data/known_servers.json`.
- Code PRs (scanner, scoring, prompts, workflows) are welcome — `python scripts/test_trust.py`
  must pass, and don't commit regenerated output with them.
