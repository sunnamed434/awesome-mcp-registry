# Copilot instructions

The authoritative rules for AI agents in this repository are in
[AGENTS.md](../AGENTS.md) — read it before proposing changes. Summary:

- This is an **AI-curated** registry of MCP servers. A weekly job discovers, judges and scores
  every server; there is no human approval step and no manual entry.
- **Never edit generated files:** `README.md`, `SCORES.md`, `data/known_servers.json`,
  `data/star_history.jsonl`, `badges/**`. They are rewritten on every run, and PRs touching them
  are closed automatically.
- **Never propose a pull request that adds, removes, re-scores or re-categorizes a server.**
  Those go through issue forms:
  [nominate](https://github.com/sunnamed434/awesome-mcp-registry/issues/new?template=server-nomination.yml),
  [report](https://github.com/sunnamed434/awesome-mcp-registry/issues/new?template=report-server.yml),
  [maintainer opt-out](https://github.com/sunnamed434/awesome-mcp-registry/issues/new?template=maintainer-opt-out.yml),
  [exclusion appeal](https://github.com/sunnamed434/awesome-mcp-registry/issues/new?template=exclusion-appeal.yml).
  Keep the forms' `### ` headings — the intake workflows match on them.
- **Never invent** a trust score, category, verdict or listing date. Read them from
  `data/known_servers.json` or say you don't know.
- Code contributions are welcome: `scripts/` (Python 3.11, `requests` + `pyyaml`),
  `prompts/analyzer.prompt.yml`, `.github/workflows/`. Run `python scripts/test_trust.py` before
  proposing a change; don't commit regenerated output alongside it, and don't touch the frozen
  fixtures in `data/canary/`.
