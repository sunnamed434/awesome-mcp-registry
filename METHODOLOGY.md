# Methodology: How Servers Are Scored

Every server in this registry carries a **trust score from 0 to 100**. This document publishes
the exact formula. Nothing about the score is secret: the raw inputs are committed in
[`data/known_servers.json`](data/known_servers.json), the scoring code is
[`scripts/trust.py`](scripts/trust.py), and anyone can re-run the math offline with
`python scripts/recompute_trust.py` — no AI calls, no API keys, no hidden inputs.

Per-server breakdowns live in [SCORES.md](SCORES.md).

## The formula (v1.0)

```
trust = clamp(0, 100, Σ (weight_i × subscore_i) − red-flag penalties)
```

| Component | Weight | What it measures | How it's computed |
|-----------|--------|------------------|-------------------|
| AI assessment | **35%** | Substance of the project: documentation quality, real-world utility, maturity | GPT-4.1-mini rates three anchored dimensions 0–4 each (anchors below); score = (doc + utility + maturity) / 12 × 100 |
| Maintenance | **20%** | Is it alive? | 70% push recency (full credit ≤ 14 days since last push, zero at 180 days, from `pushed_at`) + 30% commit cadence (commits in last 90 days / 12, capped). Recency carries the whole component when the commit count couldn't be fetched |
| Popularity | **15%** | Adoption | `100 × log10(1 + stars) / log10(1 + 30,000)`, capped at 100 — log scale, so mega-repos can't dominate |
| Docs & hygiene | **15%** | Can you actually use it? | 45% GitHub community-profile health (a neutral 50 is assumed when GitHub doesn't report it) + 35% README substance (length, headings, code blocks; renormalized away if the README couldn't be fetched) + 20% license (SPDX-recognized = 100, other = 50, none = 0); +5 bonus for a SECURITY.md |
| Security posture | **10%** | Supply-chain hygiene | [OpenSSF Scorecard](https://scorecard.dev/) overall score × 10, when the repo is indexed |
| Community | **5%** | Bus factor | `100 × log10(1 + contributors) / log10(1 + 40)`, capped at 100 |

**Missing data is never punished.** If a whole component can't be computed (e.g. the repo isn't
indexed by OpenSSF Scorecard), its weight is redistributed across the remaining components and
the breakdown says so explicitly. Within a component, unavailable inputs are imputed neutrally
(noted in the table above) rather than scored as zero.

**Listing gate:** a server appears in the README iff the AI judged it a valid MCP server AND its
trust score is **≥ 50** AND it has no fatal flag (archived, disabled, or deleted repo). A fatal
flag also blocks nomination acceptance — a high-scoring archived repo is reported as
"not listable", never "accepted".

**Letter grades** (shown in [SCORES.md](SCORES.md)) are fixed bands over the final score:
**A ≥ 80, B ≥ 65, C ≥ 50, F < 50**. They are presentation only — listing depends solely on the
gate above.

### Why these weights?

- **AI at 35%** — the largest single component, because AI curation is this project's whole
  premise. But it's no longer one opaque gut number: the model scores three anchored dimensions,
  and the anchors are published below. The other 65% is independently verifiable math.
- **Stars at only 15%** — discovery is already star-biased (GitHub search results are
  star-sorted), so a heavy stars weight would double-count fame. Stars measure popularity, not
  trustworthiness; the log scale stops a 100k-star repo from burying a better-maintained
  1k-star one.
- **Issue responsiveness: deliberately not included (v1.0)** — measuring it honestly costs
  several API calls per repo and is biased against repos with no issues and maintainers who fix
  without commenting. OpenSSF Scorecard's `Maintained` check partially covers it for free.
- **"Tests passing": not included** — CI status is only observable for repos that publicize CI;
  absence is not evidence of badness. Scorecard's `CI-Tests` check covers it where data exists.

### AI rubric anchors

The model is explicitly instructed to ignore stars, dates, and contributor counts (those are
scored deterministically above) and to judge only substance:

- **documentation** — 0: no usable instructions · 1: install command only · 2: install + basic
  configuration · 3: install, configuration, tool list, and a usage example · 4: all of 3 plus MCP
  client setup snippets, environment variable reference, and troubleshooting.
- **utility** — 0: toy/demo/tutorial · 1: thin wrapper · 2: useful to a narrow niche · 3: solves a
  real recurring task for a meaningful audience · 4: high-value integration with real tool depth.
- **maturity** — 0: scaffold/template · 1: runs but minimal · 2: handles configuration and errors ·
  3: tests, CI, or versioned releases · 4: published package, semantic versioning, changelog.

The model must also name the server's concrete entrypoint and example tools in its reason —
"implements the MCP protocol and has documentation" is not accepted as evidence.

### Deterministic MCP signals

Before the AI judges a repo, the scanner collects hard evidence and feeds it into the prompt:
which MCP SDK dependencies appear in the repo's manifests (`package.json`, `pyproject.toml`,
`go.mod`, `Cargo.toml`, …), the repo's own package name (a repo whose package *is* `fastmcp` is a
framework, not a server), the presence of an MCP `server.json` manifest, and the root file
listing (which exposes multi-server monorepos). The AI still decides — the signals exist to stop
README-only judgment errors, and they're stored on each entry as `mcp_signals` for auditing.

## Red flags

Penalties subtract from the weighted score; fatal flags block listing outright. Every triggered
flag is shown in [SCORES.md](SCORES.md).

| Flag | Effect | Trigger |
|------|--------|---------|
| Archived / disabled / deleted repo | **fatal** | GitHub repo state |
| New repo | −10 | Repo < 30 days old with < 50 stars (typosquat window) |
| Young owner | −10 | Owner account < 30 days old |
| Pipe-to-shell install | −15 | README instructs `curl … \| bash`, `iwr … \| iex`, `base64 -d … \| sh`, etc. |
| Possible typosquat | −15 | Name ≥ 85% similar to a listed 5k+ star server under a different owner, where the candidate has fewer stars than the target |
| Injection attempt | −20 | Repo content tried to manipulate the AI evaluator |
| AI security concern | −5 each (max −15) | Concrete README evidence (obfuscated install scripts, excessive credential demands, remote code execution at runtime) |

## What this is NOT

- **Not a code audit.** No entry's source code has been reviewed for vulnerabilities or malice.
- **Not executed.** This registry never installs or runs the servers it lists. (Running
  nominated third-party code is itself the attack vector this registry refuses to host.)
- **Not an endorsement.** A high score means strong *public signals* — maintained, documented,
  licensed, popular, decent supply-chain hygiene. A backdoor can hide behind all of those.
  Review any MCP server, and the credentials you grant it, before connecting it to your tools.

The score is honest about its limits so you don't have to guess at them.

## Trends

Star counts are snapshotted weekly into [`data/star_history.jsonl`](data/star_history.jsonl)
(forward-only — no backfill). Weekly deltas appear in the README's Stars column and the
"Trending This Week" section; 7-day and 30-day deltas appear in SCORES.md. Snapshots older than
~53 weeks are thinned to one per month.

## Identity: renames, transfers, repojacking

Each entry stores GitHub's immutable numeric repository ID (`repo_id`) as its canonical key;
the `owner/name` slug is just the current display name. Every weekly scan re-resolves entries
by ID, so renamed or transferred repositories keep their history and scores under the new slug
automatically.

If a stored repository disappears by ID while its old slug resolves to a **different**
repository — the repojacking pattern (an abandoned name re-registered by someone else) — the
entry is **quarantined** instead of updated: marked `quarantined: true` with a reason in
[`data/known_servers.json`](data/known_servers.json), dropped from README and SCORES, and no
longer fetched, until a human reviews and clears it. The same guard applies anywhere the
scanner fetches by slug: a response whose repository ID doesn't match the stored `repo_id` is
discarded and the entry quarantined.

## Exclusion list

[`data/excluded-repos.txt`](data/excluded-repos.txt) is the only place a human overrides the AI,
reserved for two cases: **policy removals** (spam, scams, malicious content) and **maintainer
opt-outs**. Excluded repos are never analyzed or listed, and nominations for them are declined
automatically with a link to the list. To appeal or opt out, use the dedicated issue forms
(see [CONTRIBUTING.md](CONTRIBUTING.md)).

## Phase 2 (deferred by design): live testing & source scanning

The obvious next step — actually running each server in a sandbox to report "works: yes,
latency: 420ms, tools: 12" — is **deliberately deferred**:

1. **It contradicts the security posture above.** Executing nominated third-party code in CI is
   exactly the supply-chain attack vector this registry warns about. Doing it safely requires
   real isolation engineering, not a weekend patch.
2. **It's not a moat.** [Glama.ai](https://glama.ai/mcp/methodology) already runs sandboxed
   execution with syscall/network monitoring at scale. This registry's differentiator is the
   *fully open, reproducible, zero-gatekeeper pipeline* — not secret infrastructure.

If/when it's built, the hardened design is: a **separate** monthly workflow with **no secrets**
in its environment; servers installed and started inside a container with `--network=none` after
install and hard timeouts; only `initialize` + `tools/list` exercised (never tool calls);
results written as data, never granted write access to the repo. A cheaper intermediate step is
static-only scanning of cloned sources with a pinned OSS scanner (e.g. `mcp-shield` or Cisco's
`mcp-scanner`) — code is read, never executed. Both remain opt-in future work.

## Changelog

- **v1.0** (2026-06) — first published formula. Replaced the single AI 1–10 "quality score"
  (which rated 93% of servers an identical 8/10) with the weighted composite above. Existing
  entries keep a derived legacy score until their next AI re-evaluation; the `source` field in
  each entry's AI subscore shows `rubric` vs `legacy`.
