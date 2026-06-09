import json
import os
import re
from datetime import datetime, timezone


def load_cache(path):
    """Load the known servers cache from disk."""
    if not os.path.exists(path):
        return {"servers": [], "last_scan": None}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_cache(path, data):
    """Save the known servers cache to disk."""
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
    """Parse AI response text into a dict. Strips markdown fences if present."""
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = cleaned.strip()

    result = json.loads(cleaned)

    required = [
        "is_valid_mcp_server",
        "confidence",
        "category",
        "quality_score",
        "reason",
        "short_description",
    ]
    for field in required:
        if field not in result:
            raise ValueError(f"Missing required field: {field}")

    if not isinstance(result["is_valid_mcp_server"], bool):
        raise ValueError("is_valid_mcp_server must be a boolean")

    return result


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
MIN_QUALITY_SCORE = 5       # Don't show servers rated below this
MAX_PER_CATEGORY = 20       # Show top N per category in README


def generate_readme(servers, output_path):
    """Generate a markdown README from the list of valid servers."""
    # Filter by minimum quality
    qualified = [
        s for s in servers
        if s.get("analysis", {}).get("quality_score", 0) >= MIN_QUALITY_SCORE
    ]
    filtered_count = len(servers) - len(qualified)

    # Group by category
    by_category = {}
    for s in qualified:
        cat = s.get("analysis", {}).get("category", "other")
        if cat not in CATEGORY_META:
            cat = "other"
        by_category.setdefault(cat, []).append(s)

    # Sort each category by quality_score desc, then stars desc
    for cat in by_category:
        by_category[cat].sort(
            key=lambda s: (
                s.get("analysis", {}).get("quality_score", 0),
                s.get("stars", 0),
            ),
            reverse=True,
        )

    total = len(qualified)
    categories_used = [c for c in CATEGORY_META if c in by_category]
    avg_quality = 0
    if total > 0:
        avg_quality = sum(
            s.get("analysis", {}).get("quality_score", 0) for s in qualified
        ) / total

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    # shields.io uses hyphens as separators, so escape date hyphens with double hyphens
    today_badge = today.replace("-", "--")

    lines = []
    lines.append("# Awesome MCP Registry")
    lines.append("")
    lines.append(
        f"![Servers](https://img.shields.io/badge/servers-{total}-blue) "
        f"![Categories](https://img.shields.io/badge/categories-{len(categories_used)}-green) "
        f"![Avg Quality](https://img.shields.io/badge/avg%20quality-{avg_quality:.1f}%2F10-orange) "
        f"![Updated](https://img.shields.io/badge/updated-{today_badge}-lightgrey) "
        "![Auto-curated](https://img.shields.io/badge/curated%20by-GPT--4o--mini-purple)"
    )
    lines.append("")
    lines.append(
        "An AI-powered, self-updating directory of "
        "[Model Context Protocol](https://modelcontextprotocol.io/) servers. "
        "Discovered from GitHub and the "
        "[Official MCP Registry](https://registry.modelcontextprotocol.io/), "
        "analyzed and rated by GPT-4o-mini weekly."
    )
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
        lines.append("| Server | Stars | Quality | Description |")
        lines.append("|--------|-------|---------|-------------|")
        for s in shown:
            name = s.get("full_name", s.get("name", "unknown"))
            url = s.get("url", f"https://github.com/{name}")
            stars = s.get("stars", 0)
            quality = s.get("analysis", {}).get("quality_score", "?")
            desc = s.get("analysis", {}).get("short_description", "")
            # Escape pipes in description
            desc = desc.replace("|", "\\|")
            lines.append(f"| [{name}]({url}) | {stars} | {quality}/10 | {desc} |")
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
                 "[Official MCP Registry](https://registry.modelcontextprotocol.io/) for new servers")
    lines.append("2. **Analyze** — each new repo is evaluated by AI "
                 "(GPT-4o-mini via [GitHub Models](https://docs.github.com/en/github-models))")
    lines.append("3. **Re-evaluate** — servers older than 90 days are re-analyzed with fresh data. "
                 "If a project is abandoned, loses quality, or stops being relevant, "
                 "its score drops and it falls off the list")
    lines.append("4. **Rank** — only servers scoring "
                 f"{MIN_QUALITY_SCORE}+/10 appear here, "
                 f"top {MAX_PER_CATEGORY} per category, sorted by quality then stars")
    lines.append("")
    lines.append(
        "Servers are curated entirely by AI — they earn their spot through quality and lose it "
        "if they fall behind. Maintainers don't hand-pick entries."
    )
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
        f"{MIN_QUALITY_SCORE}+/10 it appears here automatically."
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
          f" ({filtered_count} below quality threshold)")
