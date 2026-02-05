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


def generate_readme(servers, output_path):
    """Generate a markdown README from the list of valid servers."""
    # Group by category
    by_category = {}
    for s in servers:
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

    total = len(servers)
    categories_used = [c for c in CATEGORY_META if c in by_category]
    avg_quality = 0
    if total > 0:
        avg_quality = sum(
            s.get("analysis", {}).get("quality_score", 0) for s in servers
        ) / total

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    lines = []
    lines.append("# Awesome MCP Registry")
    lines.append("")
    lines.append(
        f"> Auto-curated by AI | Updated: {today} | "
        f"{total} servers across {len(categories_used)} categories"
    )
    lines.append("")
    lines.append(
        "An AI-powered, self-updating directory of "
        "[Model Context Protocol](https://modelcontextprotocol.io/) servers. "
        "Discovered from GitHub and the "
        "[Official MCP Registry](https://registry.modelcontextprotocol.io/), "
        "analyzed and rated by AI weekly."
    )
    lines.append("")
    lines.append("## Stats")
    lines.append("")
    lines.append(f"- **Total servers:** {total}")
    lines.append(f"- **Categories:** {len(categories_used)}")
    lines.append(f"- **Avg quality:** {avg_quality:.1f}/10")
    lines.append("")

    for cat in CATEGORY_META:
        if cat not in by_category:
            continue
        cat_servers = by_category[cat]
        display_name = CATEGORY_META[cat]
        lines.append(f"## {display_name} ({len(cat_servers)})")
        lines.append("")
        lines.append("| Server | Stars | Quality | Description |")
        lines.append("|--------|-------|---------|-------------|")
        for s in cat_servers:
            name = s.get("full_name", s.get("name", "unknown"))
            url = s.get("url", f"https://github.com/{name}")
            stars = s.get("stars", 0)
            quality = s.get("analysis", {}).get("quality_score", "?")
            desc = s.get("analysis", {}).get("short_description", "")
            # Escape pipes in description
            desc = desc.replace("|", "\\|")
            lines.append(f"| [{name}]({url}) | {stars} | {quality}/10 | {desc} |")
        lines.append("")

    lines.append("## How This Works")
    lines.append("")
    lines.append(
        "This registry is automatically maintained by a "
        "[GitHub Actions workflow](.github/workflows/auto-scanner.yml) that:"
    )
    lines.append("")
    lines.append("1. Searches GitHub for MCP server repositories")
    lines.append("2. Pulls entries from the [Official MCP Registry](https://registry.modelcontextprotocol.io/)")
    lines.append("3. Analyzes each with AI (GPT-4o-mini via [GitHub Models](https://docs.github.com/en/github-models))")
    lines.append("4. Caches results to avoid re-analysis")
    lines.append("5. Regenerates this README with ranked results")
    lines.append("")
    lines.append("Runs every Sunday at 02:00 UTC. No manual curation, no PRs needed.")
    lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"README generated: {total} servers across {len(categories_used)} categories")
