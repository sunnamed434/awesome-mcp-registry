"""Raw repository metrics collection for the trust score.

Everything here FETCHES data (GitHub REST + OpenSSF Scorecard API) or extracts
plain statistics from text; all scoring lives in trust.py. Every fetcher
degrades gracefully: a failed call yields None for that field, and trust.py
renormalizes weights so missing data never punishes a repo.
"""

import os
import re
import time
from datetime import datetime, timedelta, timezone

import requests

GITHUB_API = "https://api.github.com"
SCORECARD_API = "https://api.securityscorecards.dev/projects/github.com"
# Scorecard checks surfaced individually in SCORES.md (the overall score feeds
# the security subscore; these are informational, no double-penalty).
SCORECARD_CHECKS = ("Dangerous-Workflow", "Code-Review", "Vulnerabilities", "Maintained")

REQUEST_TIMEOUT = 30
SLEEP_BETWEEN_CALLS = 0.3


def _headers():
    token = os.environ.get("GITHUB_TOKEN", "")
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }


# Install instructions that pipe a download straight into a shell are a
# red-flag input for trust.detect_red_flags. Requires an actual shell on the
# right side of the pipe, so `curl ... | jq` does not match.
PIPE_TO_SHELL_RE = re.compile(
    r"(?:curl|wget)\s+[^|\n]*\|\s*(?:sudo\s+)?(?:ba|z|da)?sh\b"
    r"|\biwr\b[^|\n]*\|\s*iex\b"
    r"|invoke-webrequest[^|\n]*\|\s*invoke-expression"
    r"|base64\s+(?:-d|--decode)\b[^|\n]*\|\s*(?:sudo\s+)?(?:ba|z)?sh\b",
    re.IGNORECASE,
)


def readme_stats(full_text):
    """Plain-text statistics over the FULL (untruncated) README."""
    text = full_text or ""
    return {
        "readme_chars": len(text),
        "readme_headings": len(re.findall(r"(?m)^#{1,6}\s", text)),
        "readme_has_code_block": "```" in text,
        "pipe_to_shell": bool(PIPE_TO_SHELL_RE.search(text)),
    }


def _get(url, **kwargs):
    return requests.get(url, headers=_headers(), timeout=REQUEST_TIMEOUT, **kwargs)


def fetch_repo_details(full_name):
    """Core repo fields. Returns dict, or {'gone': True} on 404, or None on error."""
    try:
        resp = _get(f"{GITHUB_API}/repos/{full_name}")
        if resp.status_code == 404:
            return {"gone": True}
        resp.raise_for_status()
        info = resp.json()
        license_info = info.get("license") or {}
        owner = info.get("owner") or {}
        return {
            "gone": False,
            "repo_id": info.get("id"),
            "stars": info.get("stargazers_count", 0),
            "pushed_at": info.get("pushed_at", ""),
            "created_at": info.get("created_at", ""),
            "archived": bool(info.get("archived")),
            "disabled": bool(info.get("disabled")),
            "license_spdx": license_info.get("spdx_id") or None,
            "default_branch": info.get("default_branch", ""),
            "owner_login": owner.get("login", ""),
            "owner_type": owner.get("type", ""),
            "description": info.get("description", "") or "",
            "language": info.get("language", "") or "",
            "topics": ", ".join(info.get("topics", [])),
            "last_update": info.get("updated_at", ""),
        }
    except requests.RequestException as e:
        print(f"  WARNING: repo details failed for {full_name}: {e}")
        return None


def fetch_commits_90d(full_name):
    """Number of commits in the last 90 days, capped at 30. None on error."""
    since = (datetime.now(timezone.utc) - timedelta(days=90)).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        resp = _get(f"{GITHUB_API}/repos/{full_name}/commits",
                    params={"since": since, "per_page": 30})
        if resp.status_code == 409:  # empty repository
            return 0
        resp.raise_for_status()
        return len(resp.json())
    except requests.RequestException as e:
        print(f"  WARNING: commit count failed for {full_name}: {e}")
        return None


def fetch_contributor_count(full_name):
    """Contributor count via the Link-header trick (per_page=1, read rel=last)."""
    try:
        resp = _get(f"{GITHUB_API}/repos/{full_name}/contributors",
                    params={"per_page": 1, "anonymous": "false"})
        if resp.status_code == 403:
            try:
                message = (resp.json().get("message") or "").lower()
            except ValueError:
                message = ""
            if "too large" in message:
                # "history too large to list contributors" — a huge community
                return 100
            # Any other 403 (rate limit, abuse detection) is missing data.
            print(f"  WARNING: contributor count 403 for {full_name}: {message or 'forbidden'}")
            return None
        if resp.status_code == 204:
            return 0
        resp.raise_for_status()
        link = resp.headers.get("Link", "")
        match = re.search(r'[?&]page=(\d+)>;\s*rel="last"', link)
        if match:
            return int(match.group(1))
        return len(resp.json())
    except requests.RequestException as e:
        print(f"  WARNING: contributor count failed for {full_name}: {e}")
        return None


def fetch_community_health(full_name):
    """GitHub community profile health percentage (0-100). None when unavailable."""
    try:
        resp = _get(f"{GITHUB_API}/repos/{full_name}/community/profile")
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json().get("health_percentage")
    except requests.RequestException as e:
        print(f"  WARNING: community profile failed for {full_name}: {e}")
        return None


def fetch_security_policy(full_name):
    """True if SECURITY.md exists at the root or under .github/."""
    for path in ("SECURITY.md", ".github/SECURITY.md"):
        try:
            resp = _get(f"{GITHUB_API}/repos/{full_name}/contents/{path}")
            if resp.status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(SLEEP_BETWEEN_CALLS)
    return False


def fetch_owner_created_at(owner_login):
    """Account creation date of the repo owner. None on error."""
    if not owner_login:
        return None
    try:
        resp = _get(f"{GITHUB_API}/users/{owner_login}")
        resp.raise_for_status()
        return resp.json().get("created_at")
    except requests.RequestException as e:
        print(f"  WARNING: owner lookup failed for {owner_login}: {e}")
        return None


def fetch_scorecard(full_name):
    """OpenSSF Scorecard result. None when the repo isn't indexed (very common
    for small repos — never treated as a negative signal)."""
    try:
        resp = requests.get(f"{SCORECARD_API}/{full_name}", timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            return None
        data = resp.json()
        checks = {}
        for check in data.get("checks", []):
            if check.get("name") in SCORECARD_CHECKS:
                checks[check["name"]] = check.get("score")
        return {"score": data.get("score"), "date": data.get("date", ""), "checks": checks}
    except (requests.RequestException, ValueError) as e:
        print(f"  WARNING: scorecard fetch failed for {full_name}: {e}")
        return None


def collect_metrics(full_name, readme_statistics=None, include_owner=False):
    """Gather all raw metrics for one repo (~5-8 REST calls + 1 Scorecard call).

    `readme_statistics` is the dict from readme_stats() over the full README
    (the caller already fetched the README for the AI; no second fetch here).
    """
    out = {
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "gone": False,
        "stars": None, "pushed_at": "", "created_at": "",
        "archived": False, "disabled": False,
        "license_spdx": None, "owner_type": "", "owner_created_at": None,
        "commits_90d": None, "contributors": None,
        "health_percentage": None, "security_policy": False,
        "scorecard": None,
    }
    out.update(readme_statistics or {})

    details = fetch_repo_details(full_name)
    if details is not None:
        out.update(details)
    if out.get("gone"):
        return out
    time.sleep(SLEEP_BETWEEN_CALLS)

    out["commits_90d"] = fetch_commits_90d(full_name)
    time.sleep(SLEEP_BETWEEN_CALLS)
    out["contributors"] = fetch_contributor_count(full_name)
    time.sleep(SLEEP_BETWEEN_CALLS)
    out["health_percentage"] = fetch_community_health(full_name)
    time.sleep(SLEEP_BETWEEN_CALLS)
    out["security_policy"] = fetch_security_policy(full_name)

    if include_owner:
        out["owner_created_at"] = fetch_owner_created_at(out.get("owner_login", ""))
        time.sleep(SLEEP_BETWEEN_CALLS)

    out["scorecard"] = fetch_scorecard(full_name)
    return out
