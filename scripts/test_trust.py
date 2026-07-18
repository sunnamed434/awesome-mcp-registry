"""Unit tests for the pure pieces of the pipeline: trust scoring, red flags,
README-stat extraction, exclusion parsing, star history, and staleness logic.

Run with:  python scripts/test_trust.py
"""

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

sys.path.insert(0, os.path.dirname(__file__))

import metrics
import trust
import utils

NOW = datetime(2026, 6, 10, tzinfo=timezone.utc)


def fake_response(status=200, payload=None):
    """A minimal stand-in for requests.Response (no network in tests)."""
    resp = mock.Mock()
    resp.status_code = status
    resp.json.return_value = payload if payload is not None else {}
    resp.headers = {}
    return resp


def iso(days_ago):
    return (NOW - timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")


def day(days_ago):
    return (NOW - timedelta(days=days_ago)).strftime("%Y-%m-%d")


def sample_metrics(**overrides):
    base = {
        "fetched_at": day(0), "gone": False,
        "stars": 5000, "pushed_at": iso(3), "created_at": iso(700),
        "archived": False, "disabled": False,
        "license_spdx": "MIT", "owner_type": "Organization",
        "owner_created_at": iso(2000),
        "commits_90d": 20, "contributors": 10,
        "health_percentage": 70, "security_policy": True,
        "scorecard": {"score": 6.8, "date": day(2), "checks": {}},
        "readme_chars": 5000, "readme_headings": 6,
        "readme_has_code_block": True, "pipe_to_shell": False,
    }
    base.update(overrides)
    return base


class TestSubscores(unittest.TestCase):
    def test_popularity_bounds(self):
        self.assertEqual(trust.popularity_score(0), 0)
        self.assertEqual(trust.popularity_score(30_000), 100)
        self.assertEqual(trust.popularity_score(2_000_000), 100)
        self.assertIsNone(trust.popularity_score(None))
        self.assertLess(trust.popularity_score(100), trust.popularity_score(5_000))

    def test_maintenance(self):
        self.assertEqual(trust.maintenance_score(0, 12), 100)
        self.assertEqual(trust.maintenance_score(14, 12), 100)
        # Recency dead at 180d; only cadence remains
        self.assertEqual(trust.maintenance_score(400, 0), 0)
        self.assertEqual(trust.maintenance_score(400, 12), 30)
        self.assertIsNone(trust.maintenance_score(None, 5))
        # Unknown commit count != zero commits: recency carries the component
        self.assertEqual(trust.maintenance_score(0, None), 100)
        self.assertGreater(trust.maintenance_score(0, None),
                           trust.maintenance_score(0, 0))

    def test_community(self):
        self.assertIsNone(trust.community_score(None))
        self.assertEqual(trust.community_score(40), 100)
        self.assertEqual(trust.community_score(0), 0)

    def test_docs(self):
        rich = trust.docs_score(70, 5000, 6, True, "MIT", True)
        bare = trust.docs_score(None, 100, 0, False, None, False)
        self.assertGreater(rich, bare)
        self.assertLessEqual(rich, 100)
        self.assertGreaterEqual(bare, 0)
        # NOASSERTION licenses get partial credit
        self.assertGreater(trust.docs_score(50, 3000, 3, True, "NOASSERTION", False),
                           trust.docs_score(50, 3000, 3, True, None, False))
        # README fetch failure (None) renormalizes instead of scoring as empty
        unfetched = trust.docs_score(70, None, None, None, "MIT", False)
        empty = trust.docs_score(70, 0, 0, False, "MIT", False)
        self.assertEqual(unfetched, round((0.45 * 70 + 0.20 * 100) / 0.65))
        self.assertGreater(unfetched, empty)

    def test_security(self):
        self.assertIsNone(trust.security_score(None))
        self.assertIsNone(trust.security_score({"score": None}))
        self.assertEqual(trust.security_score({"score": 6.8}), 68)

    def test_ai_score(self):
        score, source = trust.ai_score(
            {"rubric": {"documentation": 4, "utility": 4, "maturity": 4}})
        self.assertEqual((score, source), (100, "rubric"))
        score, source = trust.ai_score({"rubric": {"documentation": 9, "utility": -2,
                                                   "maturity": 2}})
        self.assertEqual(source, "rubric")
        self.assertEqual(score, 50)  # clamped to 4 + 0 + 2 = 6/12
        score, source = trust.ai_score({"quality_score": 8})
        self.assertEqual((score, source), (80, "legacy"))
        score, source = trust.ai_score({})
        self.assertEqual((score, source), (None, "none"))

    def test_grade(self):
        self.assertEqual(trust.grade(80), "A")
        self.assertEqual(trust.grade(79), "B")
        self.assertEqual(trust.grade(65), "B")
        self.assertEqual(trust.grade(50), "C")
        self.assertEqual(trust.grade(49), "F")


class TestRedFlags(unittest.TestCase):
    def test_clean_repo_has_no_flags(self):
        flags, penalty = trust.detect_red_flags(sample_metrics(), {}, today=NOW)
        self.assertEqual(flags, [])
        self.assertEqual(penalty, 0)

    def test_fatal_flags(self):
        flags, _ = trust.detect_red_flags(sample_metrics(archived=True), {}, today=NOW)
        self.assertTrue(any(f["id"] == "archived" and f["fatal"] for f in flags))
        flags, _ = trust.detect_red_flags({"gone": True}, {}, today=NOW)
        self.assertTrue(any(f["id"] == "repo_gone" and f["fatal"] for f in flags))

    def test_new_repo_and_young_owner(self):
        m = sample_metrics(created_at=iso(5), stars=3, owner_created_at=iso(10))
        flags, penalty = trust.detect_red_flags(m, {}, today=NOW)
        ids = {f["id"] for f in flags}
        self.assertIn("new_repo", ids)
        self.assertIn("young_owner", ids)
        self.assertEqual(penalty, 20)
        # A popular brand-new repo isn't flagged as new
        m = sample_metrics(created_at=iso(5), stars=500)
        flags, _ = trust.detect_red_flags(m, {}, today=NOW)
        self.assertNotIn("new_repo", {f["id"] for f in flags})

    def test_pipe_to_shell_flag(self):
        flags, penalty = trust.detect_red_flags(sample_metrics(pipe_to_shell=True), {},
                                                today=NOW)
        self.assertEqual(flags[0]["id"], "pipe_to_shell")
        self.assertEqual(penalty, 15)

    def test_injection_and_concerns(self):
        analysis = {"injection_attempt": True,
                    "security_concerns": ["a", "b", "c", "d"]}
        flags, penalty = trust.detect_red_flags(sample_metrics(), analysis, today=NOW)
        ids = {f["id"] for f in flags}
        self.assertIn("injection_attempt", ids)
        self.assertIn("ai_security_concern", ids)
        self.assertEqual(penalty, 20 + 15)  # concern penalty caps at 15

    def test_typosquat(self):
        listed = [{"full_name": "github/github-mcp-server", "stars": 29_000}]
        flags, _ = trust.detect_red_flags(
            sample_metrics(stars=2), {}, full_name="githab/github-mcp-server",
            listed_servers=listed, today=NOW)
        self.assertIn("possible_typosquat", {f["id"] for f in flags})
        # Same owner: never a squat
        flags, _ = trust.detect_red_flags(
            sample_metrics(stars=2), {}, full_name="github/github-mcp-server2",
            listed_servers=listed, today=NOW)
        self.assertNotIn("possible_typosquat", {f["id"] for f in flags})
        # Unpopular target: not worth squatting
        small = [{"full_name": "someone/tiny-server", "stars": 100}]
        flags, _ = trust.detect_red_flags(
            sample_metrics(stars=2), {}, full_name="other/tiny-server",
            listed_servers=small, today=NOW)
        self.assertNotIn("possible_typosquat", {f["id"] for f in flags})


class TestComputeTrust(unittest.TestCase):
    def test_full_computation(self):
        analysis = {"rubric": {"documentation": 3, "utility": 3, "maturity": 3}}
        t = trust.compute_trust(sample_metrics(), analysis, today=NOW)
        self.assertEqual(t["formula_version"], trust.FORMULA_VERSION)
        self.assertFalse(t["fatal"])
        self.assertGreaterEqual(t["final"], 0)
        self.assertLessEqual(t["final"], 100)
        weights = [s["weight"] for s in t["subscores"].values()]
        self.assertAlmostEqual(sum(weights), 1.0, places=2)

    def test_renormalization_on_missing_data(self):
        m = sample_metrics(scorecard=None, contributors=None)
        analysis = {"rubric": {"documentation": 3, "utility": 3, "maturity": 3}}
        t = trust.compute_trust(m, analysis, today=NOW)
        self.assertEqual(t["subscores"]["security"]["weight"], 0.0)
        self.assertEqual(t["subscores"]["community"]["weight"], 0.0)
        active = [s["weight"] for s in t["subscores"].values() if s["weight"]]
        self.assertAlmostEqual(sum(active), 1.0, places=2)

    def test_no_metrics_falls_back_to_ai_only(self):
        t = trust.compute_trust({}, {"quality_score": 8}, today=NOW)
        self.assertEqual(t["subscores"]["ai"]["weight"], 1.0)
        self.assertEqual(t["final"], 80)

    def test_penalty_reduces_final(self):
        analysis = {"rubric": {"documentation": 3, "utility": 3, "maturity": 3}}
        clean = trust.compute_trust(sample_metrics(), analysis, today=NOW)
        flagged = trust.compute_trust(sample_metrics(pipe_to_shell=True), analysis,
                                      today=NOW)
        self.assertEqual(clean["final"] - flagged["final"], 15)


class TestReadmeStats(unittest.TestCase):
    def test_pipe_to_shell_regex(self):
        bad = [
            "curl -sSL https://x.sh | bash",
            "curl https://x | sudo sh",
            "wget -qO- https://x | sh",
            "iwr https://x.ps1 | iex",
            "base64 -d payload | sh",
        ]
        good = [
            "curl https://api.example.com | jq '.data'",
            "Install with: pip install my-mcp-server",
            "wget https://example.com/file.tar.gz",
        ]
        for text in bad:
            self.assertTrue(metrics.readme_stats(text)["pipe_to_shell"], text)
        for text in good:
            self.assertFalse(metrics.readme_stats(text)["pipe_to_shell"], text)

    def test_stats_shape(self):
        stats = metrics.readme_stats("# Title\n\n```py\nprint(1)\n```\n## Usage\n### More\n")
        self.assertEqual(stats["readme_headings"], 3)
        self.assertTrue(stats["readme_has_code_block"])
        self.assertGreater(stats["readme_chars"], 0)
        empty = metrics.readme_stats("")
        self.assertEqual(empty["readme_chars"], 0)
        self.assertFalse(empty["pipe_to_shell"])


class TestParseAiResponse(unittest.TestCase):
    BASE = {
        "is_valid_mcp_server": True, "confidence": 90, "category": "dev-tools",
        "rubric": {"documentation": 3, "utility": 5, "maturity": -1},
        "reason": "x", "short_description": "y",
    }

    def test_rubric_clamped(self):
        result = utils.parse_ai_response(json.dumps(self.BASE))
        self.assertEqual(result["rubric"], {"documentation": 3, "utility": 4, "maturity": 0})

    def test_unknown_category_coerced(self):
        payload = dict(self.BASE, category="mobile")
        self.assertEqual(utils.parse_ai_response(json.dumps(payload))["category"], "other")

    def test_legacy_quality_score_synthesizes_rubric(self):
        payload = {k: v for k, v in self.BASE.items() if k != "rubric"}
        payload["quality_score"] = 8
        result = utils.parse_ai_response(json.dumps(payload))
        self.assertEqual(result["rubric"], {"documentation": 3, "utility": 3, "maturity": 3})

    def test_missing_rubric_and_quality_raises(self):
        payload = {k: v for k, v in self.BASE.items() if k != "rubric"}
        with self.assertRaises(ValueError):
            utils.parse_ai_response(json.dumps(payload))

    def test_markdown_fences_stripped(self):
        result = utils.parse_ai_response("```json\n" + json.dumps(self.BASE) + "\n```")
        self.assertTrue(result["is_valid_mcp_server"])


class TestExclusions(unittest.TestCase):
    def test_parsing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "excluded.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write("# comment\n\nOwner/Repo  # opt-out\nbad/spammer\nnot a slug line\n")
            excluded = utils.load_exclusions(path)
        self.assertEqual(excluded, {"owner/repo", "bad/spammer"})

    def test_missing_file(self):
        self.assertEqual(utils.load_exclusions(os.path.join("no", "such", "file.txt")), set())

    def test_enforce_idempotent(self):
        import scan_repos
        cache = {"servers": [
            {"full_name": "Bad/Spammer",
             "analysis": {"is_valid_mcp_server": True, "quality_score": 8}},
            {"full_name": "good/server",
             "analysis": {"is_valid_mcp_server": True, "quality_score": 8}},
        ]}
        changed = scan_repos.enforce_exclusions(cache, {"bad/spammer"})
        self.assertEqual(changed, 1)
        self.assertFalse(cache["servers"][0]["analysis"]["is_valid_mcp_server"])
        self.assertTrue(cache["servers"][0]["excluded"])
        self.assertTrue(cache["servers"][1]["analysis"]["is_valid_mcp_server"])
        self.assertEqual(scan_repos.enforce_exclusions(cache, {"bad/spammer"}), 0)


class TestStarHistory(unittest.TestCase):
    def test_deltas_windows(self):
        history = {"o/r": [(day(30), 900), (day(7), 1000), (day(1), 1090)]}
        deltas = utils.star_deltas(history, "o/r", 1100, day(0))
        self.assertEqual(deltas["d7"], 100)
        self.assertEqual(deltas["d30"], 200)
        # No snapshot in the 6-10 day window -> None
        history = {"o/r": [(day(20), 900)]}
        self.assertIsNone(utils.star_deltas(history, "o/r", 1000, day(0))["d7"])
        self.assertIsNone(utils.star_deltas({}, "o/r", 1000, day(0))["d7"])

    def test_update_appends_and_dedupes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "history.jsonl")
            servers = [{"full_name": "o/r", "stars": 100}]
            utils.update_star_history(path, servers, day(0))
            history = utils.update_star_history(path, servers, day(0))  # same day: no dup
            self.assertEqual(history["o/r"], [(day(0), 100)])

    def test_prune_drops_long_unlisted(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "history.jsonl")
            with open(path, "w", encoding="utf-8") as f:
                f.write(json.dumps({"d": day(200), "r": "gone/repo", "s": 5}) + "\n")
                f.write(json.dumps({"d": day(200), "r": "alive/repo", "s": 5}) + "\n")
            history = utils.update_star_history(
                path, [{"full_name": "alive/repo", "stars": 6}], day(0))
        self.assertNotIn("gone/repo", history)
        self.assertIn("alive/repo", history)


class TestNominationIntake(unittest.TestCase):
    def test_fetch_nominations_captures_author_identity(self):
        import scan_repos
        payload = [
            {"number": 41, "title": "Nominate: o/r",
             "body": "https://github.com/o/r",
             "user": {"login": "someone", "id": 12345}},
            {"number": 42, "title": "a PR", "body": "",
             "user": {"login": "x", "id": 1}, "pull_request": {}},  # skipped
        ]
        with mock.patch.object(scan_repos.requests, "get",
                               return_value=fake_response(200, payload)):
            noms = scan_repos.fetch_nominations()
        self.assertEqual(len(noms), 1)
        self.assertEqual(noms[0]["number"], 41)
        self.assertEqual(noms[0]["author"], "someone")
        self.assertEqual(noms[0]["author_id"], 12345)


class TestNominationVerdicts(unittest.TestCase):
    def test_fatal_blocks_acceptance(self):
        import scan_repos
        valid = {"is_valid_mcp_server": True}
        self.assertEqual(scan_repos.result_label_for(valid, 80),
                         scan_repos.STATUS_ACCEPTED)
        self.assertEqual(scan_repos.result_label_for(valid, 80, fatal=True),
                         scan_repos.STATUS_BELOW)
        self.assertEqual(scan_repos.result_label_for(valid, 40),
                         scan_repos.STATUS_BELOW)
        self.assertEqual(scan_repos.result_label_for({"is_valid_mcp_server": False}, 80),
                         scan_repos.STATUS_DECLINED)
        # The close reason follows the label: fatal never closes as 'completed'
        self.assertEqual(scan_repos.close_reason_for(
            scan_repos.result_label_for(valid, 80, fatal=True)), "not_planned")

    def test_verdict_comment_fatal_branch(self):
        import scan_repos
        t = {"final": 83, "fatal": True,
             "flags": [{"id": "archived", "label": "Repository is archived",
                        "penalty": 0, "fatal": True}],
             "subscores": {}, "penalty": 0}
        text = scan_repos.verdict_comment("o/r", {"is_valid_mcp_server": True,
                                                  "reason": "x"}, t)
        self.assertIn("Not listable", text)
        self.assertIn("archived", text)
        self.assertNotIn("will appear in the registry", text)

    def test_already_known_fatal(self):
        import scan_repos
        server = {"full_name": "o/r", "analysis": {"is_valid_mcp_server": True},
                  "trust": {"final": 83, "fatal": True}}
        text = scan_repos.already_known_comment(server)
        self.assertIn("blocking flag", text)
        self.assertNotIn("Already listed", text)


class TestDedupe(unittest.TestCase):
    def _srv(self, fn, checked, rid=None, **kw):
        e = {"full_name": fn, "last_checked": checked,
             "analysis": {"is_valid_mcp_server": True, "quality_score": 8}}
        if rid:
            e["repo_id"] = rid
        e.update(kw)
        return e

    def test_same_repo_id_under_two_slugs(self):
        import scan_repos
        # A transferred repo re-discovered under its new slug: one record survives.
        cache = {"servers": [self._srv("jlowin/fastmcp", day(20), rid=5),
                             self._srv("PrefectHQ/fastmcp", day(2), rid=5)]}
        self.assertEqual(scan_repos.dedupe_servers(cache), 1)
        self.assertEqual([s["full_name"] for s in cache["servers"]],
                         ["PrefectHQ/fastmcp"])

    def test_slug_fallback_is_case_insensitive(self):
        import scan_repos
        # Regression: the same repo listed twice (ids not backfilled yet).
        cache = {"servers": [self._srv("getsentry/XcodeBuildMCP", day(20)),
                             self._srv("getsentry/xcodebuildmcp", day(2))]}
        self.assertEqual(scan_repos.dedupe_servers(cache), 1)
        self.assertEqual(len(cache["servers"]), 1)
        self.assertEqual(cache["servers"][0]["last_checked"], day(2))

    def test_known_repo_id_survives_merge(self):
        import scan_repos
        cache = {"servers": [self._srv("o/r", day(20), rid=7),
                             self._srv("o/r", day(2))]}
        scan_repos.dedupe_servers(cache)
        survivor = cache["servers"][0]
        self.assertEqual(survivor["last_checked"], day(2))
        self.assertEqual(survivor["repo_id"], 7)

    def test_first_discovery_provenance_survives(self):
        import scan_repos
        nominated = self._srv("o/r", day(30), rid=7, source="nominated",
                              discovered_via="nomination",
                              nominated_by={"login": "x", "user_id": 1,
                                            "issue_number": 2})
        rediscovered = self._srv("o/r", day(1), rid=7, source="github",
                                 discovered_via="github-search")
        cache = {"servers": [nominated, rediscovered]}
        scan_repos.dedupe_servers(cache)
        survivor = cache["servers"][0]
        self.assertEqual(survivor["last_checked"], day(1))  # freshest verdict
        self.assertEqual(survivor["discovered_via"], "nomination")
        self.assertEqual(survivor["nominated_by"]["user_id"], 1)

    def test_distinct_repos_untouched(self):
        import scan_repos
        cache = {"servers": [self._srv("a/x", day(1), rid=1),
                             self._srv("b/y", day(1), rid=2)]}
        self.assertEqual(scan_repos.dedupe_servers(cache), 0)
        self.assertEqual(len(cache["servers"]), 2)


class TestIdentityResolution(unittest.TestCase):
    def _entry(self, **kw):
        e = {"full_name": "old/name",
             "analysis": {"is_valid_mcp_server": True, "quality_score": 8}}
        e.update(kw)
        return e

    def _resolve(self, entry, responses):
        import scan_repos
        cache = {"servers": [entry]}
        with mock.patch.object(scan_repos.requests, "get", side_effect=responses), \
             mock.patch.object(scan_repos.time, "sleep"):
            return scan_repos.resolve_known_entries(cache, set())

    def test_rename_updates_slug(self):
        entry = self._entry(repo_id=111)
        renamed, jacked, _ = self._resolve(entry, [fake_response(200, {
            "id": 111, "full_name": "new/name", "name": "name",
            "html_url": "https://github.com/new/name"})])
        self.assertEqual(renamed, [("old/name", "new/name")])
        self.assertEqual(jacked, [])
        self.assertEqual(entry["full_name"], "new/name")
        self.assertEqual(entry["url"], "https://github.com/new/name")
        self.assertFalse(entry.get("quarantined"))

    def test_repojacked_slug_is_quarantined_not_updated(self):
        entry = self._entry(repo_id=111)
        renamed, jacked, _ = self._resolve(entry, [
            fake_response(404),  # by id: our repo is gone
            fake_response(200, {"id": 999, "full_name": "old/name",  # slug re-registered
                                "stargazers_count": 5}),
        ])
        self.assertEqual(jacked, ["old/name"])
        self.assertTrue(entry["quarantined"])
        self.assertIn("repojack", entry["quarantine_reason"])
        self.assertEqual(entry["full_name"], "old/name")  # entry left untouched
        self.assertEqual(entry["repo_id"], 111)

    def test_plain_deletion_is_not_quarantined(self):
        entry = self._entry(repo_id=111)
        renamed, jacked, _ = self._resolve(entry, [fake_response(404), fake_response(404)])
        self.assertEqual(jacked, [])
        self.assertFalse(entry.get("quarantined"))  # existing fatal-flag path handles it

    def test_backfills_missing_repo_id(self):
        entry = self._entry()
        _, _, backfilled = self._resolve(entry, [fake_response(200, {
            "id": 222, "full_name": "old/name", "stargazers_count": 1})])
        self.assertEqual(backfilled, 1)
        self.assertEqual(entry["repo_id"], 222)

    def test_reconcile_repo_id(self):
        import scan_repos
        entry = self._entry(repo_id=111)
        self.assertFalse(scan_repos.reconcile_repo_id(entry, 999))
        self.assertTrue(entry["quarantined"])
        fresh = self._entry()
        self.assertTrue(scan_repos.reconcile_repo_id(fresh, 42))  # lazy backfill
        self.assertEqual(fresh["repo_id"], 42)
        self.assertTrue(scan_repos.reconcile_repo_id(fresh, 42))  # match: fine
        self.assertTrue(scan_repos.reconcile_repo_id(fresh, None))  # no data: tolerated

    def test_quarantined_dropped_from_generation(self):
        good = {"full_name": "good/server", "stars": 10, "url": "https://github.com/good/server",
                "analysis": {"is_valid_mcp_server": True, "quality_score": 8,
                             "category": "dev-tools", "short_description": "fine"}}
        bad = {"full_name": "jacked/server", "stars": 10, "url": "https://github.com/jacked/server",
               "quarantined": True, "quarantine_reason": "repo_id mismatch",
               "analysis": {"is_valid_mcp_server": True, "quality_score": 8,
                            "category": "dev-tools", "short_description": "fine"}}
        self.assertFalse(utils.is_listed(bad))
        with tempfile.TemporaryDirectory() as tmp:
            readme = os.path.join(tmp, "README.md")
            scores = os.path.join(tmp, "SCORES.md")
            utils.generate_readme([good, bad], readme)
            utils.generate_scores_md([good, bad], scores)
            with open(readme, encoding="utf-8") as f:
                readme_text = f.read()
            with open(scores, encoding="utf-8") as f:
                scores_text = f.read()
        self.assertIn("good/server", readme_text)
        self.assertNotIn("jacked/server", readme_text)
        self.assertIn("good/server", scores_text)
        self.assertNotIn("jacked/server", scores_text)


class TestStaleness(unittest.TestCase):
    def test_is_stale(self):
        import scan_repos
        v = scan_repos.PROMPT_VERSION
        fresh = {"analysis": {"reason": "fine"}, "prompt_version": v, "last_checked": day(5)}
        failed = {"analysis": {"reason": "Analysis failed: 429"}, "prompt_version": v,
                  "last_checked": day(1)}
        old_prompt = {"analysis": {"reason": "fine"}, "prompt_version": v - 1,
                      "last_checked": day(5)}
        old_date = {"analysis": {"reason": "fine"}, "prompt_version": v,
                    "last_checked": day(120)}
        self.assertFalse(scan_repos.is_stale(fresh, NOW))
        self.assertTrue(scan_repos.is_stale(failed, NOW))
        self.assertTrue(scan_repos.is_stale(old_prompt, NOW))
        self.assertTrue(scan_repos.is_stale(old_date, NOW))

    def test_reaudit_priority_order(self):
        import scan_repos
        failed = {"analysis": {"reason": "Analysis failed: 429"}, "last_checked": day(1)}
        listed = {"analysis": {"is_valid_mcp_server": True, "quality_score": 8,
                               "reason": "ok"},
                  "trust": {"final": 80}, "last_checked": day(5)}
        rest = {"analysis": {"is_valid_mcp_server": False, "reason": "no"},
                "last_checked": day(400)}
        ordered = sorted([rest, listed, failed], key=scan_repos.reaudit_priority)
        self.assertIs(ordered[0], failed)
        self.assertIs(ordered[1], listed)
        self.assertIs(ordered[2], rest)


class TestDisplayHelpers(unittest.TestCase):
    def test_trust_final_fallback(self):
        self.assertEqual(utils.trust_final({"trust": {"final": 72}}), 72)
        self.assertEqual(utils.trust_final({"analysis": {"quality_score": 8}}), 80)
        self.assertEqual(utils.trust_final({}), 0)

    def test_is_listed_gate(self):
        listed = {"analysis": {"is_valid_mcp_server": True}, "trust": {"final": 50}}
        below = {"analysis": {"is_valid_mcp_server": True}, "trust": {"final": 49}}
        fatal = {"analysis": {"is_valid_mcp_server": True},
                 "trust": {"final": 90, "fatal": True}}
        invalid = {"analysis": {"is_valid_mcp_server": False}, "trust": {"final": 90}}
        self.assertTrue(utils.is_listed(listed))
        self.assertFalse(utils.is_listed(below))
        self.assertFalse(utils.is_listed(fatal))
        self.assertFalse(utils.is_listed(invalid))

    def test_gh_anchor(self):
        self.assertEqual(utils.gh_anchor("jlowin/fastmcp"), "jlowinfastmcp")
        self.assertEqual(utils.gh_anchor("trigger.dev x"), "triggerdev-x")

    def test_format_trust_breakdown(self):
        t = trust.compute_trust(sample_metrics(),
                                {"rubric": {"documentation": 3, "utility": 3,
                                            "maturity": 3}}, today=NOW)
        lines = utils.format_trust_breakdown(t)
        self.assertEqual(len(lines), 6)
        self.assertTrue(any("AI assessment" in line for line in lines))


if __name__ == "__main__":
    unittest.main(verbosity=2)
