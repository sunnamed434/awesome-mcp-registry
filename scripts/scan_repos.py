import base64
import json
import os
import sys
import time
from datetime import datetime, timezone

import requests

from utils import load_cache, save_cache, truncate_text, parse_ai_response, generate_readme

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
MODELS_API_URL = "https://models.github.ai/inference/chat/completions"
REGISTRY_API_URL = "https://registry.modelcontextprotocol.io/v0/servers"
MODEL_NAME = "openai/gpt-4o-mini"

MAX_NEW_ANALYSES = 40
MAX_RE_EVALUATIONS = 10
STALE_AFTER_DAYS = 90
README_TRUNCATE = 3000

SEARCH_QUERIES = [
    "MCP server",
    "model context protocol server",
    "mcp-server",
    "modelcontextprotocol",
    "@modelcontextprotocol/sdk",
]

GITHUB_HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "X-GitHub-Api-Version": "2022-11-28",
}

CACHE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "known_servers.json")
README_PATH = os.path.join(os.path.dirname(__file__), "..", "README.md")

SYSTEM_PROMPT = """\
You are an expert on the Model Context Protocol (MCP) ecosystem.
Your task: determine if a GitHub repository is a legitimate MCP server
and assess its quality.

VALID MCP server criteria:
- Implements the MCP protocol (exposes tools, resources, or prompts)
- Has working code (not a stub, template, or empty scaffold)
- Has some documentation or usage instructions
- Is a single server (not an "awesome list" or aggregator)

REJECT criteria:
- MCP client only (not a server)
- SDK or library for building MCP servers (e.g. python-sdk, typescript-sdk, csharp-sdk, go-sdk)
- Awesome-list / aggregator / directory / registry
- Abandoned with no functional code
- Not actually MCP (just mentions it in passing)
- Pure fork with no meaningful modifications
- Tutorial/demo with no real utility
- Collection of multiple servers in one repo (not a single focused server)

For valid servers, categorize into EXACTLY one of these values (no other values allowed):
databases, dev-tools, cloud, productivity, communication,
file-systems, web-scraping, ai-ml, finance, security,
monitoring, media, search, knowledge-base, other

Respond ONLY with valid JSON. No markdown fences, no extra text."""

USER_PROMPT_TEMPLATE = """\
Analyze this repository:
Name: {repo_name}
Description: {repo_description}
Stars: {stars}
Last Update: {last_update}
Language: {language}
Topics: {topics}
README (truncated):
{readme_content}

JSON response format:
{{
  "is_valid_mcp_server": true/false,
  "confidence": 0-100,
  "category": "<domain>",
  "quality_score": 1-10,
  "transport": ["stdio"|"sse"|"streamable-http"],
  "tools_count_estimate": 0,
  "reason": "brief explanation",
  "short_description": "one-line description"
}}"""


# ---------------------------------------------------------------------------
# GitHub Search
# ---------------------------------------------------------------------------

def search_github():
    """Search GitHub for MCP-related repositories. Returns deduplicated list."""
    seen = {}
    for query in SEARCH_QUERIES:
        print(f"  Searching GitHub: '{query}'")
        try:
            resp = requests.get(
                "https://api.github.com/search/repositories",
                params={"q": query, "sort": "stars", "order": "desc", "per_page": 30},
                headers=GITHUB_HEADERS,
                timeout=30,
            )
            resp.raise_for_status()
            items = resp.json().get("items", [])
            for item in items:
                fn = item["full_name"]
                if fn not in seen:
                    seen[fn] = {
                        "full_name": fn,
                        "name": item["name"],
                        "url": item["html_url"],
                        "stars": item.get("stargazers_count", 0),
                        "last_update": item.get("updated_at", ""),
                        "language": item.get("language", ""),
                        "description": item.get("description", "") or "",
                        "topics": ", ".join(item.get("topics", [])),
                        "source": "github",
                    }
        except requests.RequestException as e:
            print(f"  WARNING: GitHub search failed for '{query}': {e}")
        time.sleep(2)

    print(f"  GitHub search: {len(seen)} unique repos found")
    return seen


# ---------------------------------------------------------------------------
# Official MCP Registry
# ---------------------------------------------------------------------------

def fetch_from_registry():
    """Fetch servers from the official MCP Registry API. Returns dict keyed by full_name."""
    seen = {}
    cursor = None
    page = 0

    while True:
        page += 1
        params = {"limit": 100}
        if cursor:
            params["cursor"] = cursor

        print(f"  Fetching MCP Registry page {page}...")
        try:
            resp = requests.get(REGISTRY_API_URL, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            print(f"  WARNING: Registry fetch failed: {e}")
            break

        servers = data.get("servers", data.get("items", []))
        if not servers:
            break

        for entry in servers:
            repo_url = entry.get("repository", {}).get("url", "") if isinstance(entry.get("repository"), dict) else ""
            if not repo_url:
                repo_url = entry.get("repo_url", entry.get("url", ""))

            # Extract full_name from GitHub URL
            full_name = ""
            if "github.com/" in repo_url:
                parts = repo_url.rstrip("/").split("github.com/")[-1]
                segments = parts.split("/")
                if len(segments) >= 2:
                    full_name = f"{segments[0]}/{segments[1]}"

            if not full_name:
                continue

            if full_name not in seen:
                seen[full_name] = {
                    "full_name": full_name,
                    "name": entry.get("name", full_name.split("/")[-1]),
                    "url": f"https://github.com/{full_name}",
                    "stars": 0,  # Registry doesn't always provide stars
                    "last_update": entry.get("updated_at", ""),
                    "language": "",
                    "description": entry.get("description", "") or "",
                    "topics": "",
                    "source": "registry",
                }

        # Pagination
        metadata = data.get("metadata", {})
        next_cursor = metadata.get("nextCursor", metadata.get("next_cursor"))
        if not next_cursor or next_cursor == cursor:
            break
        cursor = next_cursor
        time.sleep(1)

    print(f"  MCP Registry: {len(seen)} unique servers found")
    return seen


# ---------------------------------------------------------------------------
# Merge sources
# ---------------------------------------------------------------------------

def merge_sources(github_results, registry_results):
    """Merge and deduplicate results from GitHub and Registry."""
    merged = dict(github_results)
    for fn, entry in registry_results.items():
        if fn in merged:
            merged[fn]["source"] = "github+registry"
        else:
            merged[fn] = entry
    print(f"  Merged: {len(merged)} unique repos total")
    return list(merged.values())


# ---------------------------------------------------------------------------
# Fetch README
# ---------------------------------------------------------------------------

def fetch_readme(full_name):
    """Fetch and decode the README for a repository."""
    try:
        resp = requests.get(
            f"https://api.github.com/repos/{full_name}/readme",
            headers=GITHUB_HEADERS,
            timeout=30,
        )
        if resp.status_code == 404:
            return ""
        resp.raise_for_status()
        content_b64 = resp.json().get("content", "")
        content = base64.b64decode(content_b64).decode("utf-8", errors="replace")
        return truncate_text(content, README_TRUNCATE)
    except Exception as e:
        print(f"  WARNING: Could not fetch README for {full_name}: {e}")
        return ""


# ---------------------------------------------------------------------------
# AI Analysis
# ---------------------------------------------------------------------------

def analyze_with_ai(repo_data, readme_content):
    """Send repo data to GitHub Models API for analysis."""
    user_message = USER_PROMPT_TEMPLATE.format(
        repo_name=repo_data.get("name", ""),
        repo_description=repo_data.get("description", ""),
        stars=repo_data.get("stars", 0),
        last_update=repo_data.get("last_update", ""),
        language=repo_data.get("language", ""),
        topics=repo_data.get("topics", ""),
        readme_content=readme_content,
    )

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.3,
        "max_tokens": 500,
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    resp = requests.post(MODELS_API_URL, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"]
    return parse_ai_response(content)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if not GITHUB_TOKEN:
        print("ERROR: GITHUB_TOKEN environment variable is required")
        sys.exit(1)

    print("=" * 60)
    print("MCP Server Scanner")
    print("=" * 60)

    # 1. Load cache
    print("\n[1/7] Loading cache...")
    cache = load_cache(CACHE_PATH)
    cached_names = {s["full_name"] for s in cache["servers"]}
    print(f"  Cache contains {len(cached_names)} servers")

    # 2. Search GitHub
    print("\n[2/7] Searching GitHub...")
    github_repos = search_github()

    # 3. Fetch from MCP Registry
    print("\n[3/7] Fetching from MCP Registry...")
    registry_repos = fetch_from_registry()

    # 4. Merge and deduplicate
    print("\n[4/7] Merging sources...")
    all_repos = merge_sources(github_repos, registry_repos)
    new_repos = [r for r in all_repos if r["full_name"] not in cached_names]
    print(f"  New repos to analyze: {len(new_repos)}")

    # 5. Analyze new repos with AI
    print(f"\n[5/7] Analyzing (max {MAX_NEW_ANALYSES} new repos)...")
    analyzed = 0
    for repo in new_repos[:MAX_NEW_ANALYSES]:
        fn = repo["full_name"]
        print(f"  [{analyzed + 1}/{min(len(new_repos), MAX_NEW_ANALYSES)}] {fn}")

        readme = fetch_readme(fn)
        time.sleep(1)  # Pace GitHub API calls

        try:
            analysis = analyze_with_ai(repo, readme)
            valid_str = "VALID" if analysis["is_valid_mcp_server"] else "REJECTED"
            print(f"    -> {valid_str} (confidence: {analysis['confidence']}%)")
        except Exception as e:
            print(f"    -> ERROR: {e}")
            analysis = {
                "is_valid_mcp_server": False,
                "confidence": 0,
                "category": "other",
                "quality_score": 0,
                "transport": [],
                "tools_count_estimate": 0,
                "reason": f"Analysis failed: {e}",
                "short_description": "",
            }

        cache["servers"].append({
            "full_name": fn,
            "name": repo.get("name", ""),
            "url": repo.get("url", f"https://github.com/{fn}"),
            "stars": repo.get("stars", 0),
            "source": repo.get("source", ""),
            "last_checked": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "analysis": analysis,
        })

        analyzed += 1
        time.sleep(4)  # Rate limit: stay under 15 req/min for Models API

    # 6. Re-evaluate stale entries
    print(f"\n[6/7] Re-evaluating stale entries (older than {STALE_AFTER_DAYS} days)...")
    today = datetime.now(timezone.utc)
    stale = []
    for s in cache["servers"]:
        checked = s.get("last_checked", "")
        if not checked:
            stale.append(s)
            continue
        try:
            checked_date = datetime.strptime(checked, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            if (today - checked_date).days >= STALE_AFTER_DAYS:
                stale.append(s)
        except ValueError:
            stale.append(s)

    # Sort stale by oldest first
    stale.sort(key=lambda s: s.get("last_checked", "0000-00-00"))
    re_evaluated = 0

    for s in stale[:MAX_RE_EVALUATIONS]:
        fn = s["full_name"]
        print(f"  [{re_evaluated + 1}/{min(len(stale), MAX_RE_EVALUATIONS)}] Re-evaluating {fn}")

        readme = fetch_readme(fn)
        time.sleep(1)

        # Update stars from GitHub API
        try:
            resp = requests.get(
                f"https://api.github.com/repos/{fn}",
                headers=GITHUB_HEADERS,
                timeout=30,
            )
            if resp.status_code == 200:
                repo_info = resp.json()
                s["stars"] = repo_info.get("stargazers_count", s.get("stars", 0))
                s["last_update"] = repo_info.get("updated_at", "")
                s["description"] = repo_info.get("description", "") or ""
                s["language"] = repo_info.get("language", "")
                s["topics"] = ", ".join(repo_info.get("topics", []))
            elif resp.status_code == 404:
                # Repo deleted or made private — mark as invalid
                print(f"    -> GONE (404)")
                s["analysis"]["is_valid_mcp_server"] = False
                s["analysis"]["reason"] = "Repository no longer accessible"
                s["analysis"]["quality_score"] = 0
                s["last_checked"] = today.strftime("%Y-%m-%d")
                re_evaluated += 1
                time.sleep(4)
                continue
        except requests.RequestException:
            pass

        try:
            repo_data = {
                "name": s.get("name", ""),
                "description": s.get("description", ""),
                "stars": s.get("stars", 0),
                "last_update": s.get("last_update", ""),
                "language": s.get("language", ""),
                "topics": s.get("topics", ""),
            }
            analysis = analyze_with_ai(repo_data, readme)
            old_valid = s["analysis"].get("is_valid_mcp_server", False)
            new_valid = analysis["is_valid_mcp_server"]
            old_quality = s["analysis"].get("quality_score", 0)
            new_quality = analysis.get("quality_score", 0)

            status = "KEPT"
            if old_valid and not new_valid:
                status = "REMOVED"
            elif not old_valid and new_valid:
                status = "PROMOTED"
            elif old_quality != new_quality:
                status = f"RESCORED {old_quality} -> {new_quality}"

            print(f"    -> {status}")
            s["analysis"] = analysis
        except Exception as e:
            print(f"    -> ERROR: {e}")

        s["last_checked"] = today.strftime("%Y-%m-%d")
        re_evaluated += 1
        time.sleep(4)

    print(f"  Re-evaluated {re_evaluated} stale entries ({len(stale)} total stale)")

    # 7. Save and generate
    print(f"\n[7/7] Saving results...")
    save_cache(CACHE_PATH, cache)

    valid_servers = [
        s for s in cache["servers"]
        if s.get("analysis", {}).get("is_valid_mcp_server", False)
    ]
    generate_readme(valid_servers, README_PATH)

    print(f"\nDone! Analyzed {analyzed} new repos, re-evaluated {re_evaluated} stale. "
          f"Total valid servers: {len(valid_servers)}")


if __name__ == "__main__":
    main()
