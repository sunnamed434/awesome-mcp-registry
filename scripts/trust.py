"""Pure trust-score computation. No network, no file I/O.

Raw repository metrics (collected by metrics.py) plus the AI analysis go in; a
fully self-describing ``trust`` object comes out. Keeping this module pure means
the published formula (METHODOLOGY.md) can be re-run offline over the committed
cache by anyone — see scripts/recompute_trust.py.
"""

import math
from datetime import datetime, timezone
from difflib import SequenceMatcher

FORMULA_VERSION = "1.0"

# Component weights. The AI stays the single biggest voice (the project's
# identity is "AI curates"), but the majority of the score is independently
# verifiable math. Missing components are renormalized, never punished.
WEIGHTS = {
    "ai": 0.35,
    "maintenance": 0.20,
    "popularity": 0.15,
    "docs": 0.15,
    "security": 0.10,
    "community": 0.05,
}

# Listing gate and letter grades over the 0-100 final score.
GRADE_BANDS = ((80, "A"), (65, "B"), (50, "C"))  # anything below 50 is "F"

# Popularity saturates here: log scale prevents mega-repos from dominating.
POPULARITY_SATURATION_STARS = 30_000
# Community (bus factor) saturates at this many contributors.
COMMUNITY_SATURATION_CONTRIBUTORS = 40
# Maintenance recency: full credit up to this many days since last push...
RECENCY_FULL_CREDIT_DAYS = 14
# ...and zero credit at this many days.
RECENCY_ZERO_DAYS = 180
# Commit cadence saturates at this many commits per 90 days (~weekly).
CADENCE_SATURATION_COMMITS = 12

# Typosquat heuristic: a repo name this similar to a listed server with at
# least this many stars (and a different owner) is suspicious.
TYPOSQUAT_SIMILARITY = 0.85
TYPOSQUAT_MIN_TARGET_STARS = 5_000


def clamp(lo, hi, value):
    return max(lo, min(hi, value))


def _parse_date(value):
    """Parse an ISO timestamp or YYYY-MM-DD string to an aware datetime, else None."""
    if not value:
        return None
    text = str(value).strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _days_between(earlier, later):
    earlier_dt = _parse_date(earlier)
    if earlier_dt is None:
        return None
    return (later - earlier_dt).days


# ---------------------------------------------------------------------------
# Subscores (each 0-100, or None when the underlying data is unavailable)
# ---------------------------------------------------------------------------

def popularity_score(stars):
    if stars is None:
        return None
    s = max(0, int(stars))
    return round(100 * min(1.0, math.log10(1 + s) / math.log10(1 + POPULARITY_SATURATION_STARS)))


def maintenance_score(days_since_push, commits_90d):
    """0.7 x push recency + 0.3 x commit cadence. When the commit count couldn't
    be fetched (None != zero commits), recency carries the whole component."""
    if days_since_push is None:
        return None
    span = RECENCY_ZERO_DAYS - RECENCY_FULL_CREDIT_DAYS
    recency = clamp(0.0, 100.0, 100.0 * (1 - max(0, days_since_push - RECENCY_FULL_CREDIT_DAYS) / span))
    if commits_90d is None:
        return round(recency)
    cadence = 100.0 * min(1.0, commits_90d / CADENCE_SATURATION_COMMITS)
    return round(0.7 * recency + 0.3 * cadence)


def community_score(contributors):
    if contributors is None:
        return None
    c = max(0, int(contributors))
    return round(100 * min(1.0, math.log10(1 + c) / math.log10(1 + COMMUNITY_SATURATION_CONTRIBUTORS)))


def docs_score(health_percentage, readme_chars, readme_headings,
               readme_has_code_block, license_spdx, security_policy):
    if not license_spdx:
        license_pts = 0
    elif str(license_spdx).upper() in ("NOASSERTION", "OTHER"):
        license_pts = 50
    else:
        license_pts = 100

    # Community-profile health is occasionally unavailable; neutral default.
    health = health_percentage if health_percentage is not None else 50

    if readme_chars is None:
        # README stats couldn't be fetched (a failed call, not an empty README):
        # renormalize the README weight away instead of scoring it as empty.
        base = (0.45 * health + 0.20 * license_pts) / 0.65
    else:
        if readme_chars < 200:
            readme_pts = 0
        elif readme_chars < 1000:
            readme_pts = 40
        elif readme_chars < 2500:
            readme_pts = 70
        else:
            readme_pts = 90
        if (readme_headings or 0) >= 3:
            readme_pts += 10
        if readme_has_code_block:
            readme_pts += 10
        readme_pts = min(100, readme_pts)
        base = 0.45 * health + 0.35 * readme_pts + 0.20 * license_pts

    if security_policy:
        base += 5
    return int(clamp(0, 100, round(base)))


def security_score(scorecard):
    """OpenSSF Scorecard overall score (0-10) scaled to 0-100; None when not indexed."""
    if not scorecard or scorecard.get("score") is None:
        return None
    return int(clamp(0, 100, round(float(scorecard["score"]) * 10)))


def ai_score(analysis):
    """Returns (score 0-100 or None, source). Rubric-based for fresh analyses;
    falls back to the legacy 1-10 quality_score for entries not yet re-judged."""
    a = analysis or {}
    rubric = a.get("rubric")
    if isinstance(rubric, dict):
        total = 0
        for key in ("documentation", "utility", "maturity"):
            try:
                total += int(clamp(0, 4, int(rubric.get(key, 0))))
            except (TypeError, ValueError):
                pass
        return round(100 * total / 12), "rubric"
    quality = a.get("quality_score")
    if quality is None:
        return None, "none"
    try:
        return int(clamp(0, 100, int(quality) * 10)), "legacy"
    except (TypeError, ValueError):
        return None, "none"


def grade(final):
    for threshold, letter in GRADE_BANDS:
        if final >= threshold:
            return letter
    return "F"


# ---------------------------------------------------------------------------
# Red flags
# ---------------------------------------------------------------------------

def detect_red_flags(metrics, analysis, full_name="", listed_servers=None, today=None):
    """Returns (flags, penalty). Each flag: {id, label, penalty, fatal}.
    Fatal flags (archived/disabled/gone) bar listing regardless of score."""
    flags = []
    m = metrics or {}
    a = analysis or {}
    today = today or datetime.now(timezone.utc)

    if m.get("gone"):
        flags.append({"id": "repo_gone", "label": "Repository no longer accessible",
                      "penalty": 0, "fatal": True})
    if m.get("archived"):
        flags.append({"id": "archived", "label": "Repository is archived",
                      "penalty": 0, "fatal": True})
    if m.get("disabled"):
        flags.append({"id": "disabled", "label": "Repository is disabled",
                      "penalty": 0, "fatal": True})

    repo_age_days = _days_between(m.get("created_at"), today)
    if repo_age_days is not None and repo_age_days < 30 and (m.get("stars") or 0) < 50:
        flags.append({"id": "new_repo", "label": "Repository is less than 30 days old",
                      "penalty": 10, "fatal": False})

    owner_age_days = _days_between(m.get("owner_created_at"), today)
    if owner_age_days is not None and owner_age_days < 30:
        flags.append({"id": "young_owner", "label": "Owner account is less than 30 days old",
                      "penalty": 10, "fatal": False})

    if m.get("pipe_to_shell"):
        flags.append({"id": "pipe_to_shell",
                      "label": "README instructs piping a download into a shell (e.g. curl | bash)",
                      "penalty": 15, "fatal": False})

    markers = (m.get("source_scan") or {}).get("markers") or []
    if markers:
        kinds = []
        for f in markers:
            kind = f.get("marker", "")
            if kind and kind not in kinds:
                kinds.append(kind)
        flags.append({"id": "injection_suspect",
                      "label": "Source contains prompt-injection markers (tool-poisoning "
                               "pattern): " + "; ".join(kinds[:3]),
                      "penalty": 15, "fatal": False})

    squat_target = _typosquat_target(full_name, m.get("stars") or 0, listed_servers or [])
    if squat_target:
        flags.append({"id": "possible_typosquat",
                      "label": f"Name closely resembles listed server `{squat_target}`",
                      "penalty": 15, "fatal": False})

    if a.get("injection_attempt"):
        flags.append({"id": "injection_attempt",
                      "label": "Repository content attempted to manipulate the AI evaluator",
                      "penalty": 20, "fatal": False})

    concerns = [c for c in (a.get("security_concerns") or []) if c]
    if concerns:
        flags.append({"id": "ai_security_concern",
                      "label": "AI flagged README-level security concerns: " + "; ".join(
                          str(c) for c in concerns[:3]),
                      "penalty": min(15, 5 * len(concerns)), "fatal": False})

    return flags, sum(f["penalty"] for f in flags)


def _typosquat_target(full_name, stars, listed_servers):
    """A lookalike name of a popular listed server under a different owner."""
    if not full_name or "/" not in full_name:
        return None
    owner, name = full_name.lower().split("/", 1)
    for srv in listed_servers:
        target = (srv.get("full_name") or "").lower()
        if not target or "/" not in target or target == f"{owner}/{name}":
            continue
        t_owner, t_name = target.split("/", 1)
        if t_owner == owner:
            continue
        if (srv.get("stars") or 0) < TYPOSQUAT_MIN_TARGET_STARS:
            continue
        # The squatter is the smaller repo imitating the bigger one.
        if (srv.get("stars") or 0) <= stars:
            continue
        if SequenceMatcher(None, name, t_name).ratio() >= TYPOSQUAT_SIMILARITY:
            return target
    return None


# ---------------------------------------------------------------------------
# Composite
# ---------------------------------------------------------------------------

def compute_trust(metrics, analysis, full_name="", listed_servers=None, today=None):
    """Compute the 0-100 trust score. Pure: same inputs, same output.

    Missing subscores get their weight renormalized across the rest, so a repo
    is never punished for data we couldn't fetch (e.g. not indexed by OpenSSF
    Scorecard). Red-flag penalties subtract from the weighted sum.
    """
    m = metrics or {}
    today = today or datetime.now(timezone.utc)

    ai, ai_source = ai_score(analysis)
    days_since_push = _days_between(m.get("pushed_at"), today)

    subscores = {
        "ai": {
            "score": ai,
            "detail": {"source": ai_source,
                       "rubric": (analysis or {}).get("rubric")},
        },
        "maintenance": {
            "score": maintenance_score(days_since_push, m.get("commits_90d")),
            "detail": {"days_since_push": days_since_push,
                       "commits_90d": m.get("commits_90d")},
        },
        "popularity": {
            "score": popularity_score(m.get("stars")),
            "detail": {"stars": m.get("stars")},
        },
        "docs": {
            "score": docs_score(m.get("health_percentage"), m.get("readme_chars"),
                                m.get("readme_headings"), m.get("readme_has_code_block"),
                                m.get("license_spdx"), m.get("security_policy"))
            if m else None,
            "detail": {"health_percentage": m.get("health_percentage"),
                       "license": m.get("license_spdx"),
                       "security_policy": bool(m.get("security_policy"))},
        },
        "security": {
            "score": security_score(m.get("scorecard")),
            "detail": {"scorecard": (m.get("scorecard") or {}).get("score"),
                       "note": None if m.get("scorecard")
                       else "not indexed by OpenSSF Scorecard; weight redistributed"},
        },
        "community": {
            "score": community_score(m.get("contributors")),
            "detail": {"contributors": m.get("contributors")},
        },
    }

    available = {k: v for k, v in subscores.items() if v["score"] is not None}
    total_weight = sum(WEIGHTS[k] for k in available) or 1.0
    weighted = 0.0
    for key, sub in subscores.items():
        if sub["score"] is None:
            sub["weight"] = 0.0
        else:
            sub["weight"] = round(WEIGHTS[key] / total_weight, 4)
            weighted += sub["weight"] * sub["score"]

    flags, penalty = detect_red_flags(m, analysis, full_name=full_name,
                                      listed_servers=listed_servers, today=today)
    final = int(clamp(0, 100, round(weighted - penalty)))

    return {
        "formula_version": FORMULA_VERSION,
        "computed_at": today.strftime("%Y-%m-%d"),
        "final": final,
        "grade": grade(final),
        "subscores": subscores,
        "flags": flags,
        "penalty": penalty,
        "fatal": any(f["fatal"] for f in flags),
    }
