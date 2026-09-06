import json
import os
import re
from datetime import datetime, timezone

from trust import FORMULA_VERSION, WEIGHTS, clamp, grade


def load_cache(path):
    """Load the known servers cache from disk."""
    if not os.path.exists(path):
        return {"servers": [], "last_scan": None}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# Data-format version of known_servers.json, for anyone building on the file.
# 2 = repo_id/discovered_via/nominated_by/quarantine fields (2026-07).
SCHEMA_VERSION = 2


def save_cache(path, data):
    """Save the known servers cache to disk."""
    data["schema_version"] = SCHEMA_VERSION
    data["last_scan"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def truncate_text(text, max_chars=3000):
    """Truncate text to max_chars, appending '...' if cut."""
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."


def parse_ai_response(text):
    """Parse AI response text into a dict. Strips markdown fences if present.

    Validates and sanitizes: category must be a known value (unknown -> 'other'),
    rubric dimensions are clamped to 0-4. A reply that still uses the legacy
    quality_score-only shape gets a rubric synthesized from it rather than
    failing the whole analysis.
    """
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = cleaned.strip()

    result = json.loads(cleaned)

    required = [
        "is_valid_mcp_server",
        "confidence",
        "category",
        "reason",
        "short_description",
    ]
    for field in required:
        if field not in result:
            raise ValueError(f"Missing required field: {field}")

    if not isinstance(result["is_valid_mcp_server"], bool):
        raise ValueError("is_valid_mcp_server must be a boolean")

    if result.get("category") not in CATEGORY_META:
        print(f"  WARNING: model returned unknown category "
              f"{result.get('category')!r}; coercing to 'other'")
        result["category"] = "other"

    try:
        result["confidence"] = int(clamp(0, 100, int(result.get("confidence", 0))))
    except (TypeError, ValueError):
        result["confidence"] = 0

    rubric = result.get("rubric")
    if not isinstance(rubric, dict):
        if "quality_score" not in result:
            raise ValueError("Missing required field: rubric")
        # Legacy-shaped reply: synthesize an equivalent rubric from the 1-10 score.
        try:
            q = int(clamp(0, 10, int(result.get("quality_score", 0))))
        except (TypeError, ValueError):
            q = 0
        approx = int(round(q * 4 / 10))
        print("  WARNING: model returned no rubric; synthesizing one from quality_score")
        rubric = {"documentation": approx, "utility": approx, "maturity": approx}
    sanitized = {}
    for key in ("documentation", "utility", "maturity"):
        try:
            sanitized[key] = int(clamp(0, 4, int(rubric.get(key, 0))))
        except (TypeError, ValueError):
            sanitized[key] = 0
    result["rubric"] = sanitized

    if not isinstance(result.get("security_concerns"), list):
        result["security_concerns"] = []

    return result


# ---------------------------------------------------------------------------
# Exclusion list (data/excluded-repos.txt)
# ---------------------------------------------------------------------------

EXCLUSION_LINE_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def load_exclusions(path):
    """Parse the exclusion file into a set of lowercase 'owner/repo' slugs.

    Lines may be blank, full-line '# comments', or a slug with a structured
    comment: 'owner/repo  # reason | YYYY-MM-DD | issue-link'. Only the slug is
    parsed — everything after '#' is for humans and the appeal bot — so old
    bare 'owner/repo # reason' lines remain valid. GitHub repo names are
    case-insensitive, so all slugs are lowercased. A missing file yields an
    empty set (the mechanism is optional)."""
    excluded = set()
    if not os.path.exists(path):
        return excluded
    with open(path, "r", encoding="utf-8") as f:
        for lineno, raw in enumerate(f, 1):
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            if EXCLUSION_LINE_RE.match(line):
                excluded.add(line.lower())
            else:
                print(f"  WARNING: {path}:{lineno}: ignoring malformed exclusion line: "
                      f"{raw.strip()!r}")
    return excluded


# ---------------------------------------------------------------------------
# Star history (data/star_history.jsonl) — weekly snapshots for trends
# ---------------------------------------------------------------------------

HISTORY_FULL_RETENTION_DAYS = 371      # keep every snapshot for ~53 weeks
HISTORY_DROP_UNLISTED_AFTER_DAYS = 180  # forget repos that left the registry


def _parse_day(text):
    try:
        return datetime.strptime(text, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def load_star_history(path):
    """Load history as {full_name: [(date_str, stars), ...]} sorted by date."""
    history = {}
    if not os.path.exists(path):
        return history
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            try:
                row = json.loads(raw)
                history.setdefault(row["r"], []).append((row["d"], int(row["s"])))
            except (ValueError, KeyError, TypeError):
                continue
    for snapshots in history.values():
        snapshots.sort(key=lambda x: x[0])
    return history


def update_star_history(path, servers, today_str):
    """Append today's snapshot for each server, prune old data, rewrite the file.

    Returns the updated history dict (used for delta computation this run).
    Retention: every snapshot for ~53 weeks, then first-of-month only; repos
    absent from `servers` whose newest snapshot is older than 180 days are dropped.
    """
    history = load_star_history(path)
    current = set()
    for s in servers:
        fn = s.get("full_name", "")
        stars = s.get("stars")
        if not fn or stars is None:
            continue
        current.add(fn)
        snapshots = history.setdefault(fn, [])
        if not snapshots or snapshots[-1][0] != today_str:
            snapshots.append((today_str, int(stars)))

    today = _parse_day(today_str)
    pruned = {}
    for fn, snapshots in history.items():
        newest = _parse_day(snapshots[-1][0]) if snapshots else None
        if fn not in current and (
                newest is None or today is None
                or (today - newest).days > HISTORY_DROP_UNLISTED_AFTER_DAYS):
            continue
        kept, seen_months = [], set()
        for day_str, stars in snapshots:
            day = _parse_day(day_str)
            if day is None:
                continue
            if today is not None and (today - day).days > HISTORY_FULL_RETENTION_DAYS:
                month = day_str[:7]
                if month in seen_months:
                    continue
                seen_months.add(month)
            kept.append((day_str, stars))
        if kept:
            pruned[fn] = kept

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for fn in sorted(pruned):
            for day_str, stars in pruned[fn]:
                f.write(json.dumps({"d": day_str, "r": fn, "s": stars}) + "\n")
    return pruned


def star_deltas(history, full_name, stars_now, today_str):
    """Star growth vs the nearest snapshot 6-10 days back (d7) and 25-40 (d30).
    None when no snapshot falls in the window (e.g. first runs)."""
    deltas = {"d7": None, "d30": None}
    today = _parse_day(today_str)
    snapshots = history.get(full_name, [])
    if today is None or not snapshots or stars_now is None:
        return deltas
    for key, lo, hi in (("d7", 6, 10), ("d30", 25, 40)):
        best = None
        for day_str, stars in snapshots:
            day = _parse_day(day_str)
            if day is None:
                continue
            age = (today - day).days
            if lo <= age <= hi and (best is None or age < best[0]):
                best = (age, stars)
        if best is not None:
            deltas[key] = stars_now - best[1]
    return deltas


# Category display order and emoji mapping
CATEGORY_META = {
    "databases": "Databases",
    "dev-tools": "Dev Tools",
    "cloud": "Cloud",
    "productivity": "Productivity",
    "communication": "Communication",
    "file-systems": "File Systems",
    "web-scraping": "Web Scraping",
    "ai-ml": "AI & ML",
    "finance": "Finance",
    "security": "Security",
    "monitoring": "Monitoring",
    "media": "Media",
    "search": "Search",
    "knowledge-base": "Knowledge Base",
    "other": "Other",
}


# README generation controls
REPO = "sunnamed434/awesome-mcp-registry"   # public home of this registry
MIN_TRUST_SCORE = 50        # Entry threshold: new servers need at least this to be listed
LISTING_EXIT_SCORE = 48     # Hysteresis: already-listed servers stay until below this
MAX_PER_CATEGORY = 20       # Show top N per category in README
TRENDING_MIN_D7 = 10        # Minimum weekly star growth to appear in Trending
MODEL_DISPLAY = "DeepSeek-V4-Flash"   # AI model shown in the README; keep in sync with scan_repos.MODEL_NAME

COMPONENT_LABELS = {
    "ai": "AI assessment",
    "maintenance": "Maintenance",
    "popularity": "Popularity",
    "docs": "Docs & hygiene",
    "security": "Security posture",
    "community": "Community",
}


def trust_final(server):
    """The 0-100 trust score; legacy fallback (quality_score x 10) for entries
    the new pipeline hasn't re-scored yet."""
    t = server.get("trust") or {}
    if isinstance(t.get("final"), (int, float)):
        return int(t["final"])
    quality = (server.get("analysis") or {}).get("quality_score") or 0
    try:
        return int(clamp(0, 100, int(quality) * 10))
    except (TypeError, ValueError):
        return 0


def is_listed(server):
    """Listing gate: valid MCP server, no fatal flag, not quarantined
    (slug/repo_id identity mismatch awaiting human review), and enough trust.

    Trust uses a hysteresis band so borderline entries don't flap in and out
    of the README week to week: entry needs >= MIN_TRUST_SCORE, but a server
    listed last scan (the stamped `listed` field) stays until it drops below
    LISTING_EXIT_SCORE. Fatal flags and quarantine override the band."""
    if server.get("quarantined"):
        return False
    analysis = server.get("analysis") or {}
    if not analysis.get("is_valid_mcp_server"):
        return False
    if (server.get("trust") or {}).get("fatal"):
        return False
    final = trust_final(server)
    if final >= MIN_TRUST_SCORE:
        return True
    return bool(server.get("listed")) and final >= LISTING_EXIT_SCORE


BADGE_COLORS = {"A": "brightgreen", "B": "green", "C": "orange", "F": "red"}


def badge_url(repo_id):
    """The shields.io endpoint URL for one server's live trust badge."""
    return (f"https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/"
            f"{REPO}/master/badges/{repo_id}.json")


def badge_markdown(repo_id):
    """Ready-to-paste README snippet: the live badge, linked to SCORES.md."""
    return (f"[![MCP trust score]({badge_url(repo_id)})]"
            f"(https://github.com/{REPO}/blob/master/SCORES.md)")


def badge_offer(repo_id):
    """Comment block offering a freshly listed server its badge, with the
    rendered image and the exact markdown to copy. Empty without a repo_id."""
    if not repo_id:
        return ""
    snippet = badge_markdown(repo_id)
    return (
        f"\n\n---\n**Optional: show it off** — totally up to you, but you can embed "
        f"your live trust badge in your README. "
        f"It updates with every weekly scan, and the URL survives repo renames "
        f"(it's keyed by repository id, not name):\n\n"
        f"{snippet}\n\n"
        f"```markdown\n{snippet}\n```\n"
        f"_If the badge shows \"resource not found\", this week's registry update "
        f"hasn't merged yet — it self-heals within the hour._"
    )


def generate_badges(servers, out_dir):
    """One shields.io endpoint JSON per (non-quarantined) valid server, keyed by
    immutable repo_id so embedded badge URLs survive renames. Delisted servers
    keep a grey 'not listed' badge rather than a broken image."""
    os.makedirs(out_dir, exist_ok=True)
    for name in os.listdir(out_dir):
        if name.endswith(".json"):
            os.remove(os.path.join(out_dir, name))
    written = 0
    for s in servers:
        rid = s.get("repo_id")
        if not rid or s.get("quarantined"):
            continue
        final = trust_final(s)
        letter = grade(final)
        if is_listed(s):
            payload = {"schemaVersion": 1, "label": "mcp registry",
                       "message": f"trust {final}/100 ({letter})",
                       "color": BADGE_COLORS.get(letter, "lightgrey")}
        else:
            payload = {"schemaVersion": 1, "label": "mcp registry",
                       "message": "not listed", "color": "lightgrey"}
        with open(os.path.join(out_dir, f"{rid}.json"), "w", encoding="utf-8") as f:
            json.dump(payload, f)
        written += 1
    print(f"Badges generated: {written}")
    return written


def gh_anchor(heading):
    """GitHub's anchor slug for a markdown heading."""
    slug = re.sub(r"[^\w\- ]", "", heading.lower())
    return slug.replace(" ", "-")


def format_trust_breakdown(trust_obj):
    """Compact component breakdown lines for issue comments."""
    lines = []
    for key in WEIGHTS:
        sub = (trust_obj.get("subscores") or {}).get(key) or {}
        label = COMPONENT_LABELS[key]
        if sub.get("score") is None:
            lines.append(f"- {label}: n/a (weight redistributed)")
        else:
            lines.append(f"- {label}: **{sub['score']}/100** (weight {sub.get('weight', 0):.0%})")
    penalty = trust_obj.get("penalty") or 0
    if penalty:
        lines.append(f"- Red-flag penalty: **-{penalty}**")
    return lines


def _trust_cell(server):
    final = trust_final(server)
    anchor = gh_anchor(server.get("full_name", ""))
    flags = (server.get("trust") or {}).get("flags") or []
    warn = " ⚠" if any(not f.get("fatal") for f in flags) else ""
    return f"[{final}/100](SCORES.md#{anchor}){warn}"


def _stars_cell(server, history, today_str):
    stars = server.get("stars", 0)
    deltas = star_deltas(history or {}, server.get("full_name", ""), stars, today_str)
    if deltas["d7"] is not None and deltas["d7"] >= 1:
        return f"{stars} (+{deltas['d7']}/wk)"
    return f"{stars}"


def generate_readme(servers, output_path, history=None):
    """Generate the README from the list of valid servers."""
    history = history or {}
    qualified = [s for s in servers if is_listed(s)]
    filtered_count = len(servers) - len(qualified)

    # Group by category
    by_category = {}
    for s in qualified:
        cat = s.get("analysis", {}).get("category", "other")
        if cat not in CATEGORY_META:
            cat = "other"
        by_category.setdefault(cat, []).append(s)

    # Sort each category by trust desc, then stars desc
    for cat in by_category:
        by_category[cat].sort(key=lambda s: (trust_final(s), s.get("stars", 0)), reverse=True)

    total = len(qualified)
    categories_used = [c for c in CATEGORY_META if c in by_category]
    avg_trust = sum(trust_final(s) for s in qualified) / total if total else 0

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    # shields.io uses hyphens as separators, so escape hyphens with double hyphens
    today_badge = today.replace("-", "--")
    model_badge = MODEL_DISPLAY.replace("-", "--")

    lines = []
    lines.append("# Awesome MCP Registry")
    lines.append("")
    lines.append(
        f"![Servers](https://img.shields.io/badge/servers-{total}-blue) "
        f"![Categories](https://img.shields.io/badge/categories-{len(categories_used)}-green) "
        f"![Avg Trust](https://img.shields.io/badge/avg%20trust-{avg_trust:.0f}%2F100-orange) "
        f"![Updated](https://img.shields.io/badge/updated-{today_badge}-lightgrey) "
        f"![Auto-curated](https://img.shields.io/badge/curated%20by-{model_badge}-purple)"
    )
    lines.append("")
    lines.append(
        "A self-curating directory of "
        "[Model Context Protocol](https://modelcontextprotocol.io/) servers — a "
        "[Continuous AI](https://githubnext.com/projects/continuous-ai/) experiment. "
        "Discovered from GitHub and the "
        "[Official MCP Registry](https://registry.modelcontextprotocol.io/), "
        f"analyzed by {MODEL_DISPLAY} weekly and scored with a published, "
        "reproducible [trust formula](METHODOLOGY.md)."
    )
    lines.append("")
    lines.append(
        "> **Our bet:** curation is a job for AI, not gatekeepers. No maintainers deciding what's "
        "\"in\", no PR queues, no politics — just a [Continuous AI]"
        "(https://githubnext.com/projects/continuous-ai/) workflow that discovers, judges, and "
        "re-judges every server on merit, week after week. This list is a small proof of a bigger "
        "idea: that AI can own a real, useful, self-maintaining system end to end. Humans set the "
        "rules once; the AI runs it."
    )
    lines.append("")

    trending = []
    for s in qualified:
        d7 = star_deltas(history, s.get("full_name", ""), s.get("stars", 0), today)["d7"]
        if d7 is not None and d7 >= TRENDING_MIN_D7:
            trending.append((d7, s))
    trending.sort(key=lambda x: x[0], reverse=True)
    if trending:
        lines.append("## Trending This Week")
        lines.append("")
        lines.append("| Server | Stars | Δ 7 days |")
        lines.append("|--------|-------|----------|")
        for d7, s in trending[:5]:
            name = s.get("full_name", "unknown")
            url = s.get("url", f"https://github.com/{name}")
            lines.append(f"| [{name}]({url}) | {s.get('stars', 0)} | +{d7} |")
        lines.append("")

    for cat in CATEGORY_META:
        if cat not in by_category:
            continue
        cat_servers = by_category[cat]
        shown = cat_servers[:MAX_PER_CATEGORY]
        overflow = len(cat_servers) - len(shown)
        display_name = CATEGORY_META[cat]
        lines.append(f"## {display_name} ({len(cat_servers)})")
        lines.append("")
        lines.append("| Server | Trust | Stars | Description |")
        lines.append("|--------|-------|-------|-------------|")
        for s in shown:
            name = s.get("full_name", s.get("name", "unknown"))
            url = s.get("url", f"https://github.com/{name}")
            desc = s.get("analysis", {}).get("short_description", "")
            # Escape pipes in description
            desc = desc.replace("|", "\\|")
            lines.append(f"| [{name}]({url}) | {_trust_cell(s)} | "
                         f"{_stars_cell(s, history, today)} | {desc} |")
        if overflow > 0:
            lines.append("")
            lines.append(
                f"*...and {overflow} more. "
                f"See [known_servers.json](data/known_servers.json) for the full list.*"
            )
        lines.append("")

    lines.append("## How This Works")
    lines.append("")
    lines.append(
        "This registry is automatically maintained by a "
        "[GitHub Actions workflow](.github/workflows/auto-scanner.yml) that runs weekly:"
    )
    lines.append("")
    lines.append("1. **Discover** — searches GitHub and the "
                 "[Official MCP Registry](https://registry.modelcontextprotocol.io/) for new "
                 "servers; community [nominations](CONTRIBUTING.md) join the same queue")
    lines.append(f"2. **Analyze** — each repo is evaluated by AI "
                 f"({MODEL_DISPLAY} via the [DeepSeek API](https://api-docs.deepseek.com/)) "
                 "on an anchored rubric, informed by deterministic scanner evidence (MCP SDK "
                 "dependencies found in the repo's manifests). Prompt-injection attempts are "
                 "flagged and penalized")
    lines.append("3. **Score** — a transparent 0-100 trust score: 35% AI rubric + 65% verifiable "
                 "metrics (maintenance, popularity, docs, security posture, community). The exact "
                 "formula is published in [METHODOLOGY.md](METHODOLOGY.md); every server's "
                 "breakdown is in [SCORES.md](SCORES.md)")
    lines.append("4. **Re-evaluate** — the AI re-judges servers every ~90 days; metrics and trust "
                 "scores refresh every week. Projects that stagnate fall off the list")
    lines.append(f"5. **Rank** — only servers scoring {MIN_TRUST_SCORE}+/100 appear here, "
                 f"top {MAX_PER_CATEGORY} per category, sorted by trust then stars")
    lines.append("6. **Exclude** — a small human-maintained "
                 "[exclusion list](data/excluded-repos.txt) overrides the AI only for spam/scam "
                 "removals and maintainer opt-outs (see [CONTRIBUTING.md](CONTRIBUTING.md))")
    lines.append("")
    lines.append(f"> **Model history:** until August 2026 servers were judged by GPT-4.1-mini via "
                 f"GitHub Models, which GitHub [shut down on July 30, 2026]"
                 f"(https://github.blog/changelog/2026-07-30-github-models-is-now-retired), "
                 f"so the judge is now {MODEL_DISPLAY}. The story: "
                 f"[#36](https://github.com/{REPO}/issues/36).")
    lines.append("")
    lines.append(
        "Servers are curated entirely by AI — they earn their spot through quality and lose it "
        "if they fall behind. Maintainers don't hand-pick entries. Every automated change lands as "
        "an auto-merged pull request, so the full history stays auditable and revertable."
    )
    lines.append("")

    lines.append("## A Note on Security")
    lines.append("")
    lines.append(
        "Trust scores are computed from public metadata, the README, and "
        "[OpenSSF Scorecard](https://scorecard.dev/) data. Every entry's source is additionally "
        "scanned — **read, never executed** — for tool-poisoning markers (hidden instructions "
        "aimed at the model inside tool descriptions; flagged entries lose points in "
        "[SCORES.md](SCORES.md)). Entries are keyed by GitHub's immutable repository id, so "
        "renames are followed and a known name silently re-registered by someone else "
        "(repojacking) is quarantined instead of trusted. **Still: no entry has been "
        "code-audited or executed by this registry.** A high score means strong public signals, "
        "not a security guarantee — review any MCP server (and the credentials you grant it) "
        "before connecting it to your tools."
    )
    lines.append("")

    lines.append("## Badges")
    lines.append("")
    lines.append(
        "Maintain a listed server? Embed your live trust score — it updates weekly and the "
        "URL survives repo renames (keyed by immutable repository id):"
    )
    lines.append("")
    lines.append(f"`![MCP trust score]({badge_url('<repo_id>')})`")
    lines.append("")
    lines.append("Your exact copy-paste snippet is under your entry in [SCORES.md](SCORES.md).")
    lines.append("")

    lines.append("## Contributing")
    lines.append("")
    lines.append(
        "**Don't open a pull request to add a server.** This README is generated from "
        "[`data/known_servers.json`](data/known_servers.json) on every run, so edits to it are "
        "overwritten — and such PRs are closed automatically."
    )
    lines.append("")
    lines.append(
        "To suggest a server, "
        "[open a nomination]"
        "(https://github.com/sunnamed434/awesome-mcp-registry/issues/new?template=server-nomination.yml). "
        "The same AI evaluates it on the next weekly run and posts the verdict; if it scores "
        f"{MIN_TRUST_SCORE}+/100 it appears here automatically."
    )
    lines.append("")
    lines.append(
        "Code contributions (bug fixes, scanner improvements) are welcome — see "
        "[CONTRIBUTING.md](CONTRIBUTING.md)."
    )
    lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"README generated: {total} servers across {len(categories_used)} categories"
          f" ({filtered_count} below trust threshold)")


def _component_evidence(key, sub):
    """One human-readable evidence string per component for SCORES.md."""
    d = sub.get("detail") or {}

    def shown(name, fallback="?"):
        # dict.get fallbacks don't fire for present-but-None values
        value = d.get(name)
        return fallback if value is None else value

    if key == "ai":
        rubric = d.get("rubric") or {}
        if d.get("source") == "rubric":
            return (f"rubric: documentation {rubric.get('documentation', '?')}/4, "
                    f"utility {rubric.get('utility', '?')}/4, "
                    f"maturity {rubric.get('maturity', '?')}/4")
        return "legacy 1-10 AI score (pending re-evaluation on the new rubric)"
    if key == "maintenance":
        return (f"last push {shown('days_since_push')} days ago, "
                f"{shown('commits_90d', 'unknown')} commits in 90 days")
    if key == "popularity":
        return f"{shown('stars')} stars (log-scaled)"
    if key == "docs":
        health = d.get("health_percentage")
        health_text = "n/a (neutral 50 assumed)" if health is None else f"{health}%"
        return (f"community health {health_text}, "
                f"license {d.get('license') or 'none'}, "
                f"security policy {'yes' if d.get('security_policy') else 'no'}")
    if key == "security":
        if d.get("scorecard") is not None:
            return f"OpenSSF Scorecard {d['scorecard']}/10"
        return d.get("note") or "n/a"
    if key == "community":
        return f"{shown('contributors')} contributor(s)"
    return ""


def generate_scores_md(servers, output_path, history=None):
    """Generate SCORES.md: the full per-server trust breakdown."""
    history = history or {}
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    # Quarantined entries (identity mismatch awaiting human review) are not rendered.
    scored = sorted((s for s in servers if not s.get("quarantined")),
                    key=lambda s: (trust_final(s), s.get("stars", 0)), reverse=True)

    lines = []
    lines.append("# Trust Score Breakdown")
    lines.append("")
    lines.append(
        "Per-server breakdown of the registry's 0-100 trust score. The formula is published "
        "in [METHODOLOGY.md](METHODOLOGY.md) and can be recomputed from "
        "[`data/known_servers.json`](data/known_servers.json) with "
        "`python scripts/recompute_trust.py` — no AI required, no hidden inputs."
    )
    lines.append("")
    lines.append("> Scores are computed from public metadata only. **Nothing here is a code "
                 "audit or a security guarantee.**")
    lines.append("")

    for s in scored:
        fn = s.get("full_name", "unknown")
        url = s.get("url", f"https://github.com/{fn}")
        t = s.get("trust") or {}
        final = trust_final(s)
        lines.append(f"### {fn}")
        lines.append("")
        status = "Listed" if is_listed(s) else f"Not listed (needs {MIN_TRUST_SCORE}+)"
        lines.append(f"[{url}]({url})")
        lines.append("")
        if t.get("formula_version"):
            provenance = (f"formula v{t['formula_version']}, "
                          f"computed {t.get('computed_at', s.get('last_checked', '?'))}")
        else:
            provenance = (f"legacy AI score — recomputed with formula v{FORMULA_VERSION} "
                          f"on the next weekly scan")
        lines.append(f"**{final}/100 ({t.get('grade') or grade(final)})** — {status} — "
                     f"{provenance}")
        lines.append("")
        if t.get("subscores"):
            lines.append("| Component | Score | Weight | Evidence |")
            lines.append("|-----------|-------|--------|----------|")
            for key in WEIGHTS:
                sub = t["subscores"].get(key) or {}
                label = COMPONENT_LABELS[key]
                score = "n/a" if sub.get("score") is None else f"{sub['score']}/100"
                weight = f"{sub.get('weight', 0):.0%}"
                evidence = _component_evidence(key, sub).replace("|", "\\|")
                lines.append(f"| {label} | {score} | {weight} | {evidence} |")
            lines.append("")
        flags = t.get("flags") or []
        if flags:
            lines.append("Flags:")
            for f in flags:
                effect = "blocks listing" if f.get("fatal") else f"-{f.get('penalty', 0)}"
                lines.append(f"- ⚠ {f.get('label', f.get('id', ''))} ({effect})")
            lines.append("")
        deltas = star_deltas(history, fn, s.get("stars", 0), today)
        trend_bits = []
        if deltas["d7"] is not None:
            trend_bits.append(f"Δ7d {deltas['d7']:+d}")
        if deltas["d30"] is not None:
            trend_bits.append(f"Δ30d {deltas['d30']:+d}")
        trend = f" ({', '.join(trend_bits)})" if trend_bits else ""
        lines.append(f"Stars: {s.get('stars', 0)}{trend}")
        lines.append("")
        nb = s.get("nominated_by") or {}
        owner = (fn or "/").split("/")[0].lower()
        metrics_owner = ((s.get("metrics") or {}).get("owner_login") or "").lower()
        if nb.get("login") and nb["login"].lower() in (owner, metrics_owner):
            # Transparency, not a judgement: self-nomination is allowed.
            lines.append("_Nominated by the repository's own maintainer._")
            lines.append("")
        rid = s.get("repo_id")
        if rid:
            lines.append(f"Badge (copy into your README): `![MCP trust score]({badge_url(rid)})`")
            lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"SCORES.md generated: {len(scored)} servers")
