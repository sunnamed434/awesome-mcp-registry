"""Weekly registry diff rendered as markdown release notes.

Usage:
    python scripts/release_notes.py old_known_servers.json new_known_servers.json

Compares the listed set of two cache snapshots (added / dropped / trust movers,
matched by immutable repo_id with a slug fallback) and prints markdown to
stdout. Pure file comparison — no network, no AI. The Auto Scanner feeds the
output into the update PR body and a GitHub Release, so watchers get a free
weekly changelog (and releases.atom is a free RSS feed).
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import REPO, is_listed, trust_final

MOVER_THRESHOLD = 5   # minimum |trust delta| worth mentioning


def load_servers(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f).get("servers", [])
    except (OSError, ValueError):
        return []


def _key(s):
    return s.get("repo_id") or (s.get("full_name") or "").lower()


def diff(old_servers, new_servers):
    """{added, removed, movers} over the LISTED sets of two snapshots."""
    old_listed = {_key(s): s for s in old_servers if is_listed(s)}
    new_listed = {_key(s): s for s in new_servers if is_listed(s)}
    added = [s for k, s in new_listed.items() if k not in old_listed]
    removed = [s for k, s in old_listed.items() if k not in new_listed]
    movers = []
    for k, s in new_listed.items():
        if k in old_listed:
            before, after = trust_final(old_listed[k]), trust_final(s)
            if abs(after - before) >= MOVER_THRESHOLD:
                movers.append((s, before, after))
    movers.sort(key=lambda x: abs(x[2] - x[1]), reverse=True)
    return {"added": added, "removed": removed, "movers": movers}


def _entry(s):
    fn = s.get("full_name", "?")
    return f"[`{fn}`](https://github.com/{fn}) ({trust_final(s)}/100)"


def render(d, total_listed):
    lines = [f"Weekly automated scan. **{total_listed}** servers listed "
             f"(+{len(d['added'])} / −{len(d['removed'])}).", ""]
    if d["added"]:
        lines.append("### Added")
        lines.extend(f"- {_entry(s)}" for s in d["added"])
        lines.append("")
    if d["removed"]:
        lines.append("### Dropped")
        lines.extend(f"- {_entry(s)}" for s in d["removed"])
        lines.append("")
    if d["movers"]:
        lines.append("### Trust movers")
        lines.extend(
            f"- [`{s.get('full_name')}`](https://github.com/{s.get('full_name')}) "
            f"{before} → {after}"
            for s, before, after in d["movers"][:10])
        lines.append("")
    if not (d["added"] or d["removed"] or d["movers"]):
        lines.append("Metrics refreshed; no listing changes this week.")
        lines.append("")
    lines.append(f"Full breakdown: [SCORES.md](https://github.com/{REPO}/blob/master/SCORES.md) "
                 f"· formula: [METHODOLOGY.md](https://github.com/{REPO}/blob/master/METHODOLOGY.md)")
    return "\n".join(lines)


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    old = load_servers(sys.argv[1])
    new = load_servers(sys.argv[2])
    print(render(diff(old, new), sum(1 for s in new if is_listed(s))))


if __name__ == "__main__":
    main()
