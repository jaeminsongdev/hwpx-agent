"""Runtime freshness, checked cleanup, and whole-driver mutation counterexamples."""
import ast
import base64
import copy
import hashlib
import json
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import conservative_maintenance as c
import sql_runtime_supervision as subject
import build_current_issuer_probe as compiler_resources
from tests.sql_runtime_driver_delta import DRIVERS, restore_runtime_driver_changes


class SQLRuntimeSupervisionTests(unittest.TestCase):
    def resource(self):
        from tests.test_build_current_issuer_probe import BuildCurrentIssuerProbeTests
        return BuildCurrentIssuerProbeTests().resource_fixture()

    def watcher(self, *, started=True, alive=False, error=None):
        resources = SimpleNamespace(done=Mock(), thread=SimpleNamespace(ident=1 if started else None,
            join=Mock(side_effect=error), is_alive=Mock(return_value=alive)), reason=None, stop=Mock())
        def fail(code):
            resources.reason = resources.reason or code
            resources.stop.set()
        resources._failed = fail
        return resources

    def test_runtime_uses_original_host_policy_and_freshness_resource_type(self):
        self.assertIs(subject.SQLRuntimeResources, compiler_resources.CurrentCompilerResources)
        resources = self.resource()
        with patch.object(compiler_resources.time, "monotonic", return_value=11):
            resources.checkpoint_io()
        self.assertFalse(resources.stop.is_set())
        self.assertEqual(compiler_resources.MAX_OBSERVATION_AGE_SECONDS, 2)

    def test_stale_or_invalid_clock_stops_inherited_runtime_checkpoint(self):
        for now, reason in ((12.001, "STOP_RESOURCE_OBSERVATION_STALE"), (9, "STOP_RESOURCE_CLOCK_INVALID")):
            resources = self.resource()
            with patch.object(compiler_resources.time, "monotonic", return_value=now):
                with self.assertRaisesRegex(ValueError, reason):
                    resources.checkpoint_io()
            self.assertTrue(resources.stop.is_set())

    def test_never_started_watcher_cleanup_is_confirmed_without_join(self):
        resources, row = self.watcher(started=False), {"state": "NOT_RUN"}
        self.assertTrue(subject.finish_watcher(resources, row))
        resources.done.set.assert_called_once()
        resources.thread.join.assert_not_called()
        self.assertTrue(row["resource_watcher_cleanup_confirmed"])

    def test_started_watcher_is_joined_and_confirmed_before_success(self):
        resources, row = self.watcher(), {"state": "PASS_COMPONENT"}
        self.assertTrue(subject.finish_watcher(resources, row))
        resources.thread.join.assert_called_once_with(timeout=3)
        self.assertEqual(row["state"], "PASS_COMPONENT")

    def test_alive_after_join_watcher_cannot_leave_successful_receipt(self):
        resources, row = self.watcher(alive=True), {"state": "PASS_COMPONENT"}
        self.assertFalse(subject.finish_watcher(resources, row))
        self.assertEqual(row["state"], "FAIL_CLOSED")
        self.assertFalse(row["resource_watcher_cleanup_confirmed"])
        self.assertEqual(resources.reason, "STOP_RESOURCE_WATCHER_CLEANUP_FAILED")

    def test_join_failures_are_closed_but_do_not_raise_and_skip_container_cleanup(self):
        for error in (OSError("PRIVATE_FIXTURE"), RuntimeError("PRIVATE_FIXTURE")):
            resources, row = self.watcher(error=error), {"state": "PASS_COMPONENT"}
            self.assertFalse(subject.finish_watcher(resources, row))
            self.assertEqual(row["state"], "FAIL_CLOSED")
            self.assertNotIn("PRIVATE", json.dumps(row))

    def test_watcher_cleanup_failure_preserves_original_resource_stop_reason(self):
        resources, row = self.watcher(alive=True), {"state": "FAIL_CLOSED"}
        resources.reason = "STOP_SYSTEM_COMMIT_PRESSURE"
        subject.finish_watcher(resources, row)
        self.assertEqual(resources.reason, "STOP_SYSTEM_COMMIT_PRESSURE")
        self.assertFalse(row["resource_watcher_cleanup_confirmed"])

    def test_whole_driver_has_only_resource_type_checkpoint_freeze_and_cleanup_delta(self):
        for name in DRIVERS:
            restore_runtime_driver_changes(ast.parse((c.ROOT/name).read_text(encoding="utf-8")), name)

    def test_runtime_projection_rejects_security_or_freshness_guard_mutation(self):
        for name in DRIVERS:
            text = (c.ROOT/name).read_text(encoding="utf-8")
            for before, after in (("resources.checkpoint_io()", "resources.fake_checkpoint()"),
                    ("finish_watcher(resources, receipt)", "resources.done.set()"),
                    ('"P09_gate": "OPEN"', '"P09_gate": "PASS"')):
                self.assertIn(before, text)
                with self.assertRaisesRegex(ValueError, "SQL_RUNTIME_NONRESOURCE_AST_CHANGED"):
                    restore_runtime_driver_changes(ast.parse(text.replace(before, after, 1)), name)

    def test_integrated_factory_checkpoint_calls_freshness_and_propagates_stop(self):
        from tests.test_sql_job_integration import SQLJobIntegrationTests
        suite = SQLJobIntegrationTests()
        suite.setUp()
        for name in DRIVERS:
            run, namespace, _, _, _, resources = suite.fixture(name)
            run(["fixture-docker"])
            callback = namespace["OwnedSQLJobFactory"].call_args.kwargs["checkpoint"]
            callback()
            resources.checkpoint_io.assert_called_once()
            resources.checkpoint_io.side_effect = ValueError("STOP_RESOURCE_OBSERVATION_STALE")
            with self.assertRaisesRegex(ValueError, "STOP_RESOURCE_OBSERVATION_STALE"):
                callback()

    def test_cleanup_checkpoint_still_allows_owned_teardown_after_host_stop(self):
        from tests.test_sql_job_integration import SQLJobIntegrationTests
        suite = SQLJobIntegrationTests()
        suite.setUp()
        for name in DRIVERS:
            run, namespace, factory, _, _, resources = suite.fixture(name)
            resources.stop.is_set.return_value = True
            resources.checkpoint_io.side_effect = ValueError("STOP_RESOURCE_OBSERVATION_STALE")
            run(["fixture-docker"], cleanup=True)
            namespace["OwnedSQLJobFactory"].call_args.kwargs["checkpoint"]()
            resources.checkpoint_io.assert_not_called()
            factory.close.assert_called_once()

    def test_all_six_runtime_preimages_preserve_original_bytes_and_binding_guards(self):
        archive = json.loads((c.ROOT/subject.ARCHIVE).read_text(encoding="utf-8"))
        self.assertEqual(len(archive["files"]), 6)
        for row in archive["files"]:
            raw = base64.b64decode("".join(row["base64_chunks"]), validate=True)
            self.assertEqual(len(raw), row["bytes"])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row["sha256"])
            if row["path"] in DRIVERS:
                self.assertIn(b"bind_probe_build(reader, build_file)", raw)
                self.assertNotIn(b"finish_watcher(resources, receipt)", raw)

    def test_docker_arguments_bind_local_host_and_preserve_SQL_body(self):
        args = ["fixture-docker", "exec", "owned-id", "psql", "-c", "SELECT fixture"]
        self.assertEqual(subject.local_docker_arguments(args, "fixture-docker"),
            ["fixture-docker", "--host", subject.LOCAL_DOCKER_HOST, *args[1:]])
        self.assertEqual(args[1:], ["exec", "owned-id", "psql", "-c", "SELECT fixture"])

    def test_remote_context_override_and_unreviewed_commands_are_rejected(self):
        for args in (["fixture-docker", "--host", "tcp://PRIVATE", "info"],
                ["fixture-docker", "exec", "--context=PRIVATE"], ["fixture-docker", "info", "-Htcp://PRIVATE"],
                ["fixture-docker", "pull", "arbitrary-image"]):
            with self.assertRaises(ValueError):
                subject.local_docker_arguments(args, "fixture-docker")

    def test_rust_arguments_and_role_environment_remain_identical(self):
        factory = subject.LocalDockerJobFactory.__new__(subject.LocalDockerJobFactory)
        factory.docker = "fixture-docker"
        args, env = ["fixture-rust", "--fixed"], {"P143_ROLE": "fixture-role"}
        with patch.object(subject.OwnedSQLJobFactory, "__call__", return_value="fixture") as original:
            self.assertEqual(factory(args, env=env), "fixture")
        self.assertIs(original.call_args.args[0], args)
        self.assertIs(original.call_args.kwargs["env"], env)

    def test_endpoint_environment_is_removed_only_from_Docker_child_copy(self):
        env = {name: "PRIVATE_FIXTURE" for name in subject.ENDPOINT_ENV}
        env["P143_ROLE"] = "fixture-role"
        preserved = dict(env)
        factory = subject.LocalDockerJobFactory.__new__(subject.LocalDockerJobFactory)
        factory.docker = "fixture-docker"
        with patch.object(subject.OwnedSQLJobFactory, "__call__", return_value="fixture") as original:
            factory(["fixture-docker", "info"], env=env)
        self.assertEqual(env, preserved)
        self.assertFalse(set(subject.ENDPOINT_ENV) & set(original.call_args.kwargs["env"]))
        self.assertEqual(original.call_args.kwargs["env"]["P143_ROLE"], "fixture-role")

    def test_local_factory_keeps_parent_callbacks_partitioned_budget_and_cleanup(self):
        kwargs = dict(windows=object(), allowed_executables=["fixture-docker", "metadata", "crypto"],
            checkpoint=Mock(), record=Mock())
        with patch.object(subject.OwnedSQLJobFactory, "__init__", return_value=None) as original:
            factory = subject.LocalDockerJobFactory(**kwargs)
        self.assertEqual(original.call_args.kwargs, kwargs)
        self.assertIs(subject.LocalDockerJobFactory.close, subject.OwnedSQLJobFactory.close)
        self.assertEqual(factory.docker, "fixture-docker")
