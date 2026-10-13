"""Combined collector and unchanged driver cleanup AST fixtures, no Docker."""
import ast
import json
import re
import subprocess
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

import conservative_maintenance as c
import sql_cancelled_call as subject
from sql_cooperative_cancel import CANCEL_REASON
from sql_runtime_supervision import finish_watcher

DRIVERS = ("tools/p09/run_formula_issuer_live_sql_probe.py", "tools/p09/run_formula_issuer_authority_sql_probe.py")


class SQLCancelledCallTests(unittest.TestCase):
    def fixture(self, *, cancelled=False, partial=False, redacted=False, prior=None, count=1,
            false_success=False, before_resources=False):
        made, calls, cleanup = [], [], []
        class Resources:
            def __init__(self):
                self.stop, self.reason = threading.Event(), prior
                if prior:
                    self.stop.set()
                made.append(self)
            def _failed(self, reason):
                self.reason = self.reason or reason
                self.stop.set()
            def sample(self):
                return {"original": True}
            def checkpoint_io(self):
                if self.stop.is_set():
                    raise ValueError(self.reason)
        class Reader:
            def __init__(self, resources):
                self.resources, self.finished = resources, False
                self.finish = Mock(side_effect=AssertionError("COLLECTOR_FINISH_FORBIDDEN"))
            def summary(self):
                return {"read_passes": 3, "bytes_read": 123, "finished": self.finished}
        driver = SimpleNamespace(IdleResources=Resources, LiveSQLReader=Reader)
        def main(*arguments):
            calls.append(arguments)
            if before_resources:
                raise ValueError("sql_fixture_before_resource")
            for _ in range(count):
                resources = driver.IdleResources()
            if partial:
                driver.LiveSQLReader(resources)
            try:
                resources.checkpoint_io()
                return 0
            except ValueError:
                if false_success:
                    return 0
                if redacted:
                    raise ValueError("redacted") from None
                raise
            finally:
                cleanup.append(resources.reason)
        driver.main = main
        cancel = SimpleNamespace(is_set=Mock(return_value=cancelled))
        return driver, cancel, made, calls, cleanup, Resources, Reader

    def run_fixture(self, **kwargs):
        driver, cancel, made, calls, cleanup, original, reader = self.fixture(**kwargs)
        arguments = ("build", "receipt", 0, "original", "unchanged", "trust")
        row = subject.account_cancellable_driver_call(driver, arguments, cancel,
            clock=Mock(side_effect=[10, 18]))
        self.assertIs(driver.IdleResources, original)
        self.assertIs(driver.LiveSQLReader, reader)
        self.assertEqual(calls, [arguments])
        self.assertTrue(row["original_driver_dependencies_restored"])
        self.assertFalse(row["full_SQL_wrapper_cancellation_and_container_cleanup_qualified"])
        return row, made, cleanup

    def test_normal_call_preserves_arguments_timing_and_original_resource(self):
        row, _, cleanup = self.run_fixture()
        self.assertEqual(row["driver_return_code"], 0)
        self.assertEqual(row["driver_call_wall_seconds"], 8)
        self.assertTrue(row["original_resource_type_inherited"])
        self.assertFalse(row["cooperative_resource_stop_latched"])
        self.assertEqual(cleanup, [None])

    def test_admission_cancel_preserves_exception_and_does_not_invent_IO(self):
        row, _, cleanup = self.run_fixture(cancelled=True)
        self.assertEqual(row["driver_error_code"], CANCEL_REASON)
        self.assertEqual(row["reader_count"], 0)
        self.assertIsNone(row["reader_IO"])
        self.assertFalse(row["source_final_hash_completed"])
        self.assertEqual(cleanup, [CANCEL_REASON])

    def test_redacted_error_and_actual_resource_reason_remain_separate(self):
        row, _, _ = self.run_fixture(cancelled=True, redacted=True)
        self.assertEqual(row["driver_error_code"], "SQL_ACCOUNTED_DRIVER_REDACTED_FAILURE")
        self.assertEqual(row["cooperative_resource_stop_reason"], CANCEL_REASON)

    def test_cancel_after_reader_keeps_partial_IO_and_runs_original_finally(self):
        row, _, cleanup = self.run_fixture(cancelled=True, partial=True)
        self.assertEqual(row["reader_IO"]["bytes_read"], 123)
        self.assertFalse(row["source_final_hash_completed"])
        self.assertFalse(row["reader_IO"]["finished"])
        self.assertEqual(cleanup, [CANCEL_REASON])

    def test_existing_stop_reason_is_not_replaced_by_cancel(self):
        row, _, _ = self.run_fixture(cancelled=True, prior="STOP_EXISTING_FIXTURE")
        self.assertEqual(row["cooperative_resource_stop_reason"], "STOP_EXISTING_FIXTURE")

    def test_success_return_with_latched_stop_cannot_be_accepted(self):
        row, _, _ = self.run_fixture(cancelled=True, false_success=True)
        self.assertEqual(row["driver_return_code"], 0)
        self.assertEqual(row["state"], "FAILED_NOT_ACCEPTED")
        self.assertEqual(row["cooperative_error_code"], "SQL_CANCELLED_CALL_STOP_RETURNED_SUCCESS")

    def test_multiple_resources_are_rejected_without_fake_single_observation(self):
        row, _, _ = self.run_fixture(count=2)
        self.assertEqual(row["state"], "FAILED_NOT_ACCEPTED")
        self.assertEqual(row["cooperative_resource_count"], 2)
        self.assertIsNone(row["cooperative_resource_stop_latched"])

    def test_failure_before_resource_keeps_unobserved_fields_null(self):
        row, _, _ = self.run_fixture(before_resources=True)
        self.assertEqual(row["state"], "ORIGINAL_DRIVER_EXCEPTION_PRESERVED_NOT_SUCCESS")
        self.assertEqual(row["cooperative_resource_count"], 0)
        self.assertIsNone(row["cooperative_resource_stop_reason"])

    def test_clock_failure_restores_both_driver_dependencies(self):
        driver, cancel, _, _, _, original, reader = self.fixture()
        with self.assertRaisesRegex(ValueError, "SQL_ACCOUNTING_CLOCK_INVALID"):
            subject.account_cancellable_driver_call(driver, (), cancel, clock=lambda: float("nan"))
        self.assertIs(driver.IdleResources, original)
        self.assertIs(driver.LiveSQLReader, reader)

    def test_invalid_observer_is_rejected_before_driver_call(self):
        driver, _, _, calls, _, _, _ = self.fixture()
        with self.assertRaisesRegex(ValueError, "SQL_CANCELLED_CALL_OBSERVER_REQUIRED"):
            subject.account_cancellable_driver_call(driver, (), SimpleNamespace())
        self.assertEqual(calls, [])


def original_cleanup_program(path):
    # 두 원래 driver의 inspect와 finally 앞 세 노드를 변형 없이 실행한다.
    tree = ast.parse((c.ROOT/path).read_text(encoding="utf-8"))
    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
    inspect = next(node for node in main.body if isinstance(node, ast.FunctionDef) and node.name == "inspect")
    finals = [node.finalbody for node in main.body if isinstance(node, ast.Try) and node.finalbody]
    c.require(len(finals) == 1 and len(finals[0]) >= 3, "SQL_CANCELLED_CLEANUP_AST_SCOPE")
    selected = finals[0][:3]
    c.require(isinstance(selected[0], ast.Expr) and isinstance(selected[0].value, ast.Call)
        and isinstance(selected[0].value.func, ast.Name) and selected[0].value.func.id == "finish_watcher"
        and all(isinstance(node, ast.If) for node in selected[1:]), "SQL_CANCELLED_CLEANUP_AST_SCOPE")
    return compile(ast.Module(body=[inspect, *selected], type_ignores=[]), path, "exec")


class SQLCancelledCleanupTests(unittest.TestCase):
    def fixture(self, path, *, unknown=False, missing=False, mutate=None, rm_exit=0,
            still_present=False, watcher_alive=False, inspect_error=False):
        item = {"Id": "fixture-owned-id", "Name": "/fixture-owned-name",
            "Config": {"Labels": {"fixture.label": "fixture-run"}, "Image": "fixture-image-pin"},
            "Image": "fixture-image-id", "Mounts": [],
            "HostConfig": {"PortBindings": {"5432/tcp": [{"HostIp": "127.0.0.1"}]},
                "NetworkMode": "bridge", "ReadonlyRootfs": True, "NanoCpus": 1000000000,
                "Memory": 536870912, "MemorySwap": 536870912, "PidsLimit": 64,
                "Tmpfs": {"/var/lib/postgresql": {}, "/tmp": {}, "/var/run/postgresql": {}}}}
        if mutate:
            mutate(item)
        class Resources:
            def __init__(self):
                self.reason = CANCEL_REASON
                self.stop, self.done = threading.Event(), threading.Event()
                self.stop.set()
                self.thread = SimpleNamespace(ident=1, join=Mock(), is_alive=Mock(return_value=watcher_alive))
            def _failed(self, reason):
                self.reason = self.reason or reason
                self.stop.set()
        resources, calls = Resources(), []
        receipt = {"state": "FAIL_CLOSED", "image_id": "fixture-image-id", "container_removed": False}
        def command(args, *, cleanup=False):
            self.assertTrue(cleanup)
            self.assertTrue(resources.stop.is_set())
            calls.append(args)
            if args[1] == "rm":
                return SimpleNamespace(returncode=rm_exit, stdout="", stderr="")
            if inspect_error:
                raise OSError("PRIVATE_FIXTURE")
            if args[-1] == "fixture-owned-name" and not missing:
                return SimpleNamespace(returncode=0, stdout=json.dumps([item]), stderr="")
            if still_present:
                return SimpleNamespace(returncode=0, stdout=json.dumps([item]), stderr="")
            return SimpleNamespace(returncode=1, stdout="", stderr="No such container: fixture")
        scope = dict(command=command, require=c.require, json=json, re=re, subprocess=subprocess,
            finish_watcher=finish_watcher, resources=resources, receipt=receipt, requested=True,
            created_id=None if unknown else "fixture-owned-id", docker="fixture-docker",
            name="fixture-owned-name", LABEL="fixture.label", run_id="fixture-run", IMAGE="fixture-image-pin")
        exec(original_cleanup_program(path), scope)
        self.assertTrue(resources.stop.is_set())
        self.assertEqual(resources.reason, CANCEL_REASON)
        self.assertTrue(resources.done.is_set())
        self.assertEqual(receipt["state"], "FAIL_CLOSED")
        return receipt, calls, scope

    def test_latched_cancel_still_inspects_removes_and_verifies_owned_container(self):
        for path in DRIVERS:
            with self.subTest(driver=path):
                receipt, calls, _ = self.fixture(path)
                self.assertTrue(receipt["container_removed"])
                self.assertTrue(receipt["resource_watcher_cleanup_confirmed"])
                self.assertEqual(calls, [["fixture-docker", "inspect", "fixture-owned-name"],
                    ["fixture-docker", "rm", "--force", "fixture-owned-id"],
                    ["fixture-docker", "inspect", "fixture-owned-id"]])

    def test_unknown_creation_recovers_identity_before_owned_removal(self):
        for path in DRIVERS:
            receipt, calls, scope = self.fixture(path, unknown=True)
            self.assertTrue(receipt["container_removed"])
            self.assertEqual(scope["created_id"], "fixture-owned-id")
            self.assertEqual(receipt["container_id"], "fixture-owned-id")
            self.assertEqual(len(calls), 4)

    def test_unknown_creation_absence_never_runs_removal(self):
        for path in DRIVERS:
            receipt, calls, scope = self.fixture(path, unknown=True, missing=True)
            self.assertTrue(receipt["container_removed"])
            self.assertIsNone(scope["created_id"])
            self.assertEqual(len(calls), 1)

    def test_wrong_known_identity_cannot_remove_another_container(self):
        mutations = (lambda x: x.update(Id="other-id"), lambda x: x.update(Name="/other-name"),
            lambda x: x["Config"]["Labels"].update({"fixture.label": "other-run"}),
            lambda x: x["Config"].update(Image="other-pin"), lambda x: x.update(Image="other-image-id"))
        for path in DRIVERS:
            for mutate in mutations:
                receipt, calls, _ = self.fixture(path, mutate=mutate)
                self.assertFalse(receipt["container_removed"])
                self.assertEqual(receipt["cleanup_error_code"], "owned_container_cleanup_unverified")
                self.assertFalse(any(args[1] == "rm" for args in calls))

    def test_unknown_creation_wrong_identity_is_preserved_for_review(self):
        for path in DRIVERS:
            receipt, calls, scope = self.fixture(path, unknown=True,
                mutate=lambda x: x["Config"]["Labels"].update({"fixture.label": "other-run"}))
            self.assertFalse(receipt["container_removed"])
            self.assertIsNone(scope["created_id"])
            self.assertEqual(receipt["cleanup_error_code"], "unknown_creation_preserved_for_review")
            self.assertFalse(any(args[1] == "rm" for args in calls))

    def test_isolation_drift_cannot_authorize_removal(self):
        mutations = (lambda x: x.update(Mounts=[{"fixture": True}]),
            lambda x: x["HostConfig"].update(Memory=1073741824),
            lambda x: x["HostConfig"].update(ReadonlyRootfs=False),
            lambda x: x["HostConfig"]["PortBindings"]["5432/tcp"][0].update(HostIp="0.0.0.0"))
        for path in DRIVERS:
            for mutate in mutations:
                receipt, calls, _ = self.fixture(path, mutate=mutate)
                self.assertFalse(receipt["container_removed"])
                self.assertFalse(any(args[1] == "rm" for args in calls))

    def test_removal_failure_or_still_present_is_not_cleanup_success(self):
        for path in DRIVERS:
            for options in ({"rm_exit": 1}, {"still_present": True}):
                receipt, _, _ = self.fixture(path, **options)
                self.assertFalse(receipt["container_removed"])
                self.assertEqual(receipt["cleanup_error_code"], "owned_container_cleanup_unverified")

    def test_watcher_teardown_failure_does_not_skip_container_cleanup(self):
        for path in DRIVERS:
            receipt, calls, _ = self.fixture(path, watcher_alive=True)
            self.assertFalse(receipt["resource_watcher_cleanup_confirmed"])
            self.assertTrue(receipt["container_removed"])
            self.assertTrue(any(args[1] == "rm" for args in calls))

    def test_inspect_failure_keeps_unverified_and_redacts_raw_error(self):
        for path in DRIVERS:
            receipt, calls, _ = self.fixture(path, inspect_error=True)
            self.assertFalse(receipt["container_removed"])
            self.assertEqual(len(calls), 1)
            self.assertNotIn("PRIVATE_FIXTURE", json.dumps(receipt))
