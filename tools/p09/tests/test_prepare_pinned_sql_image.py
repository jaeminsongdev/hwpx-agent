"""Pinned pull supervisor mocks; no Docker/network/threads."""
import json
from types import SimpleNamespace
import unittest
from unittest.mock import Mock
from unittest.mock import patch
import base64
import hashlib
import itertools
import ast
import os
import conservative_maintenance as c

import prepare_pinned_sql_image as subject
from tests.test_owned_probe_build import OwnedProbeBuildTests


class PreparePinnedSQLImageTests(unittest.TestCase):
    def fixture(self):
        data = OwnedProbeBuildTests().fixture()
        data[0].samples = [{"available_ram_percent": 50, "commit_used_percent": 30}]
        return data

    def run_fixture(self, data, **kwargs):
        # 과거 supervisor/cleanup 검사만 fixture 안에서 실행. 실제 entrypoint나
        # production guard에 opt-in 우회 인자를 추가하지 않는다.
        with patch.object(subject, "require_backend_pull_containment"):
            return subject.pull_owned(data[0], "fixture-docker", data[0].samples[0],
                process_factory=data[3], capture_factory=data[4], **kwargs)

    def test_pull_arguments_are_one_digest_local_host_and_platform_only(self):
        self.assertEqual(subject.pull_arguments("fixture-docker"), ["fixture-docker", "--host",
            subject.LOCAL_DOCKER_HOST, "image", "pull", "--platform", "linux/amd64", subject.IMAGE])
        self.assertEqual(subject.MAX_PULL_SECONDS, 120)

    def test_host_growth_boundary_allows_ordinary_load(self):
        resources = SimpleNamespace(checkpoint_io=Mock(), samples=[{"available_ram_percent": 47, "commit_used_percent": 32}])
        subject.growth_checkpoint(resources, {"available_ram_percent": 50, "commit_used_percent": 30})
        resources.checkpoint_io.assert_called_once()

    def test_host_RAM_or_commit_growth_stops_before_emergency_pressure(self):
        for row in ({"available_ram_percent": 46.999, "commit_used_percent": 30},
                {"available_ram_percent": 50, "commit_used_percent": 32.001}):
            resources = SimpleNamespace(checkpoint_io=Mock(), samples=[row])
            with self.assertRaisesRegex(ValueError, "STOP_SQL_IMAGE_HOST_"):
                subject.growth_checkpoint(resources, {"available_ram_percent": 50, "commit_used_percent": 30})

    def test_fast_pull_success_keeps_output_cap_and_all_owned_cleanup(self):
        data = self.fixture()
        row = self.run_fixture(data)
        self.assertIsNone(row["error_code"])
        self.assertTrue(row["cleanup_confirmed"])
        data[4].assert_called_once_with(data[1], output_limit=subject.MAX_OUTPUT, parse_markers=False)
        data[1].kill.assert_called_once()
        data[1].wait.assert_called_once_with(timeout=2)
        data[2].close.assert_called_once()
        data[1].close.assert_called_once()

    def test_duration_stop_does_not_collect_or_skip_cleanup(self):
        data = self.fixture()
        row = self.run_fixture(data, clock=Mock(side_effect=[0, 121]))
        self.assertEqual(row["error_code"], "STOP_SQL_IMAGE_PULL_DURATION")
        data[2].communicate.assert_not_called()
        data[1].close.assert_called_once()

    def test_output_overflow_and_close_failure_remain_failed(self):
        data = self.fixture()
        data[2].communicate.side_effect = ValueError("live_progress_output_limit")
        row = self.run_fixture(data)
        self.assertEqual(row["error_code"], "live_progress_output_limit")
        data[1].close.assert_called_once()
        data = self.fixture()
        data[2].close.side_effect = OSError("PRIVATE_FIXTURE")
        row = self.run_fixture(data)
        self.assertEqual(row["error_code"], "SQL_IMAGE_PULL_PIPE_CLOSE_FAILED")
        self.assertFalse(row["cleanup_confirmed"])

    def test_rejected_pull_does_not_retain_raw_secret_output(self):
        data = self.fixture()
        data[1].returncode = 1
        data[2].communicate.return_value = ("PRIVATE_FIXTURE", "PRIVATE_FAILURE")
        row = self.run_fixture(data)
        self.assertEqual(row["error_code"], "SQL_IMAGE_PULL_REJECTED")
        self.assertNotIn("PRIVATE", json.dumps(row))

    def test_image_identity_requires_exact_digest_and_bounded_full_JSON(self):
        output = json.dumps("sha256:"+"a"*64)+"|"+json.dumps(["postgres@"+subject.IMAGE.split("@")[1]])
        self.assertEqual(subject.identity(output), "sha256:"+"a"*64)
        for bad in ("invalid", json.dumps("sha256:"+"a"*64)+"|[]", "x"*16385):
            with self.assertRaises(ValueError):
                subject.identity(bad)

    def post_fixture(self, deltas=None, *, repeated=False, stopped=False):
        resources = SimpleNamespace(samples=[], last_sample_at=0, stop=Mock(), reason="STOP_FIXTURE")
        resources.stop.is_set.return_value = stopped
        values = iter(deltas or [(50, 30)]*64)
        def refresh():
            available, commit = next(values)
            resources.samples[:] = [{"system_cpu_percent": 45, "available_ram_percent": available,
                "commit_used_percent": commit}]
            if not repeated:
                resources.last_sample_at += 0.5
        resources._check_observation_freshness = Mock(side_effect=refresh)
        return resources

    def test_post_observation_uses_fresh_samples_and_never_claims_backend_quiescence(self):
        resources = self.post_fixture()
        row = subject.observe_post_pull_host(resources, clock=Mock(side_effect=itertools.count()), sleep=Mock())
        self.assertTrue(row["host_growth_stabilized"])
        self.assertEqual(len(row["samples"]), 3)
        self.assertIsNone(row["backend_quiescence_confirmed"])

    def test_repeated_sample_cannot_fake_consecutive_stability(self):
        resources = self.post_fixture(repeated=True)
        row = subject.observe_post_pull_host(resources, clock=Mock(side_effect=itertools.count()), sleep=Mock())
        self.assertFalse(row["host_growth_stabilized"])
        self.assertEqual(len(row["samples"]), 1)
        self.assertEqual(row["error_code"], "SQL_IMAGE_POST_NOT_STABILIZED")

    def test_continuing_growth_is_bounded_and_remains_unqualified(self):
        resources = self.post_fixture([(50-i, 30) for i in range(40)])
        row = subject.observe_post_pull_host(resources, clock=Mock(side_effect=itertools.count()), sleep=Mock())
        self.assertFalse(row["host_growth_stabilized"])
        self.assertLessEqual(len(row["samples"]), 31)

    def test_stale_watcher_or_resource_stop_is_not_success(self):
        resources = self.post_fixture()
        resources._check_observation_freshness.side_effect = ValueError("STOP_RESOURCE_OBSERVATION_STALE")
        row = subject.observe_post_pull_host(resources, clock=Mock(side_effect=itertools.count()), sleep=Mock())
        self.assertEqual(row["error_code"], "STOP_RESOURCE_OBSERVATION_STALE")
        resources = self.post_fixture(stopped=True)
        row = subject.observe_post_pull_host(resources, clock=Mock(side_effect=itertools.count()), sleep=Mock())
        self.assertEqual(row["error_code"], "STOP_FIXTURE")
        self.assertFalse(row["host_growth_stabilized"])

    def test_post_observation_never_starts_another_child_or_sampler(self):
        resources = self.post_fixture()
        with patch.object(subject.subprocess, "Popen", side_effect=AssertionError("CHILD_FORBIDDEN")):
            row = subject.observe_post_pull_host(resources, clock=Mock(side_effect=itertools.count()), sleep=Mock())
        self.assertTrue(row["host_growth_stabilized"])
        resources._check_observation_freshness.assert_called()

    def test_both_post_observation_preimages_preserve_exact_original_bytes(self):
        archive = json.loads((c.ROOT/subject.POST_ARCHIVE).read_text(encoding="utf-8"))
        self.assertEqual(len(archive["files"]), 2)
        for row in archive["files"]:
            raw = base64.b64decode("".join(row["base64_chunks"]), validate=True)
            self.assertEqual(len(raw), row["bytes"])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row["sha256"])

    def test_uncontained_backend_rejected_before_process_or_capture(self):
        data = self.fixture()
        row = subject.pull_owned(data[0], "fixture-docker", data[0].samples[0],
            process_factory=data[3], capture_factory=data[4])
        self.assertEqual(row["error_code"], "SQL_IMAGE_BACKEND_CONTAINMENT_UNAVAILABLE")
        self.assertTrue(row["backend_pull_guard_rejected"])
        self.assertFalse(row["pull_authorized"])
        self.assertIsNone(row["owned_job_profile"])
        self.assertFalse(row["cleanup_confirmed"])
        data[3].assert_not_called()
        data[4].assert_not_called()

    def test_guard_has_no_environment_or_argument_opt_in(self):
        with patch.dict(os.environ, {"SQL_IMAGE_ALLOW_PULL": "1", "DOCKER_BACKEND_LIMITED": "true"}):
            with self.assertRaisesRegex(ValueError, "^SQL_IMAGE_BACKEND_CONTAINMENT_UNAVAILABLE$"):
                subject.require_backend_pull_containment()
        tree = ast.parse((c.ROOT/"tools/p09/prepare_pinned_sql_image.py").read_text(encoding="utf-8"))
        guard = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
            and node.name == "require_backend_pull_containment")
        self.assertEqual(len(guard.args.args), 0)
        self.assertEqual(len(guard.body), 1)
        self.assertIsInstance(guard.body[0], ast.Raise)

    def cached_fixture(self, *, code=0, output=None, error=""):
        if output is None:
            output = json.dumps("sha256:"+"a"*64)+"|"+json.dumps(["postgres@"+subject.IMAGE.split("@")[1]])
        return SimpleNamespace(returncode=code, stdout=output, stderr=error), [
            {"cleanup_confirmed": True, "owned_tree_empty": True, "job_handle_closed": True}]

    def test_cached_identity_reuses_only_exact_digest_and_clean_job(self):
        result, profiles = self.cached_fixture()
        self.assertEqual(subject.cached_identity(result, profiles), "sha256:"+"a"*64)
        for invalid in ([], profiles*2, [{**profiles[0], "cleanup_confirmed": False}]):
            with self.assertRaisesRegex(ValueError, "SQL_IMAGE_IDENTITY_QUERY_OR_CLEANUP_FAILED"):
                subject.cached_identity(result, invalid)
        result.stdout = json.dumps("sha256:"+"a"*64)+"|[]"
        with self.assertRaisesRegex(ValueError, "SQL_IMAGE_PINNED_DIGEST_MISSING"):
            subject.cached_identity(result, profiles)

    def test_only_closed_missing_image_becomes_unavailable_without_raw_log(self):
        result, profiles = self.cached_fixture(code=1, error="Error: No such image: PRIVATE_FIXTURE")
        self.assertIsNone(subject.cached_identity(result, profiles))
        for code, error in ((1, "PRIVATE_FAILURE"), (2, "No such image"), (1, "x"*16385)):
            result, profiles = self.cached_fixture(code=code, error=error)
            with self.assertRaisesRegex(ValueError, "^SQL_IMAGE_IDENTITY_QUERY_FAILED$"):
                subject.cached_identity(result, profiles)

    def test_main_inspects_existing_image_and_does_not_claim_pull_success_on_rejection(self):
        tree = ast.parse((c.ROOT/"tools/p09/prepare_pinned_sql_image.py").read_text(encoding="utf-8"))
        main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
        calls = [node for node in ast.walk(main) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)]
        inspect_call = next(node for node in calls if node.func.id == "inspect_owned_local_image")
        pull_call = next(node for node in calls if node.func.id == "pull_owned")
        self.assertLess(inspect_call.lineno, pull_call.lineno)
        missing = next(node for node in ast.walk(main) if isinstance(node, ast.If)
            and ast.unparse(node.test) == "image_id is None")
        self.assertTrue(any(node is pull_call for node in ast.walk(missing)))
        self.assertIn('c.require(False, pulled[\'error_code\'] or \'SQL_IMAGE_PREPARATION_UNAVAILABLE\')',
            ast.unparse(missing))

    def test_backend_guard_preimages_preserve_whole_originals(self):
        archive = json.loads((c.ROOT/subject.BACKEND_ARCHIVE).read_text(encoding="utf-8"))
        self.assertEqual({row["path"] for row in archive["files"]},
            {"tools/p09/prepare_pinned_sql_image.py", "tools/p09/tests/test_prepare_pinned_sql_image.py"})
        for row in archive["files"]:
            raw = base64.b64decode("".join(row["base64_chunks"]), validate=True)
            self.assertEqual(len(raw), row["bytes"])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row["sha256"])
