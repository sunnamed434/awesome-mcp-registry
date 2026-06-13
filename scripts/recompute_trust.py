"""Recompute trust scores offline over the committed cache.

No AI calls, no GitHub API: this re-runs the pure formula (trust.py) on the raw
metrics already stored in data/known_servers.json. Anyone can use it to audit
the published scores; the maintainer uses it after a formula change.

Usage:
    python scripts/recompute_trust.py            # report only
    python scripts/recompute_trust.py --write    # also save updated scores
"""

import os
import sys

import trust
from utils import load_cache, save_cache, trust_final, is_listed, MIN_TRUST_SCORE

CACHE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "known_servers.json")


def main():
    write = "--write" in sys.argv
    cache = load_cache(CACHE_PATH)

    listed_for_squat = [
        {"full_name": s.get("full_name", ""), "stars": s.get("stars", 0)}
        for s in cache["servers"]
        if s.get("analysis", {}).get("is_valid_mcp_server")
        and (s.get("stars") or 0) >= trust.TYPOSQUAT_MIN_TARGET_STARS
    ]

    recomputed = 0
    pending_metrics = 0
    for s in cache["servers"]:
        if not s.get("metrics"):
            pending_metrics += 1
            continue
        s["trust"] = trust.compute_trust(
            s["metrics"], s.get("analysis", {}),
            full_name=s.get("full_name", ""), listed_servers=listed_for_squat)
        recomputed += 1

    valid = [s for s in cache["servers"]
             if s.get("analysis", {}).get("is_valid_mcp_server")]
    finals = sorted((trust_final(s), s.get("full_name", "")) for s in valid)

    print(f"Formula v{trust.FORMULA_VERSION} — recomputed {recomputed} entries "
          f"({pending_metrics} have no stored metrics yet; their score is the "
          f"legacy AI fallback until the next weekly scan)")
    print(f"Valid servers: {len(valid)}, listed (>= {MIN_TRUST_SCORE}): "
          f"{sum(1 for s in valid if is_listed(s))}")

    if finals:
        print("\nScore distribution (valid servers):")
        buckets = {}
        for final, _ in finals:
            buckets[final // 10 * 10] = buckets.get(final // 10 * 10, 0) + 1
        for bucket in sorted(buckets, reverse=True):
            bar = "#" * buckets[bucket]
            print(f"  {bucket:3d}-{bucket + 9:<3d} {buckets[bucket]:3d} {bar}")
        spread = finals[-1][0] - finals[0][0]
        biggest = max(buckets.values())
        print(f"\n  span: {spread} points; largest bucket holds "
              f"{biggest}/{len(finals)} ({100 * biggest // len(finals)}%)")

        print("\nTop 10:")
        for final, fn in finals[:-11:-1]:
            print(f"  {final:3d}  {fn}")
        print("Bottom 10:")
        for final, fn in finals[:10]:
            print(f"  {final:3d}  {fn}")

    if write:
        save_cache(CACHE_PATH, cache)
        print(f"\nSaved {CACHE_PATH}")
    else:
        print("\nDry run (pass --write to save).")


if __name__ == "__main__":
    main()
