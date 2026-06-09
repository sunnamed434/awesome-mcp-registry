# Contributing

This is an **AI-curated** registry. The list curates itself — a weekly job discovers MCP
servers, scores them with AI, and regenerates everything. That shapes how you contribute.

## Suggesting a server → open a nomination, not a PR

**Do not open a pull request to add a server.** `README.md` and `data/known_servers.json` are
**machine-generated** on every weekly run, so any edit to them is overwritten — and PRs that
touch them are **closed automatically** by a bot.

Instead, **[open a nomination](https://github.com/sunnamed434/awesome-mcp-registry/issues/new?template=server-nomination.yml)**:

1. You provide the server's **public GitHub repository** URL.
2. On the next weekly scan, the **same AI** that curates the whole list evaluates it — it reads
   the repo's README and metadata and assigns a quality score.
3. The bot posts the verdict on your issue and closes it. If the server scores **5+/10**, it
   appears in the README automatically. If not, it's recorded and re-evaluated later — if it
   improves, it can still make the list.

Only **open-source servers with a public GitHub repo** can be nominated — the AI needs a repo to
read. Hosted-only endpoints with no public source can't be evaluated.

There's no human approval step and no favouritism: the AI decides, and the same gate applies to
everything, including servers discovered automatically.

## How servers leave the list

Every server is **re-evaluated every ~90 days** against fresh data. If a project is abandoned,
loses quality, or stops being a real MCP server, its score drops and it falls off the list. You
don't need to report dead projects — the re-evaluation handles it.

## Code contributions are welcome

Bug fixes and improvements to the scanner, prompts, or workflows are genuinely welcome — those
PRs are **not** auto-closed. The relevant code lives in:

- `scripts/scan_repos.py` — discovery, AI analysis, re-evaluation, nomination intake
- `scripts/utils.py` — README generation and parsing helpers
- `prompts/analyzer.prompt.yml` — the AI evaluation prompt
- `.github/workflows/` — the automation

Open a normal PR for those. Just don't edit the generated files (`README.md`,
`data/known_servers.json`) by hand — let the scanner regenerate them.

## A note on AI mistakes

The verdicts are automated and not perfect. If you think the AI got your server wrong, comment on
the (closed) nomination issue — threads stay open for a few weeks before they lock, so there's a
window to flag genuine misjudgements.
