"""Connected call/parent contract mocks; no SQL, subprocess or file writes."""
import copy
import json
from pathlib import PurePosixPath
from types import SimpleNamespace
import threading
import unittest
from unittest.mock import Mock, patch

import conservative_maintenance as c
import sql_owned_execution as subject
from tests.test_sql_container_ownership import NONCE, RUN

RECEIPT = "implementation/p09/evidence/p09-146-corpus-consumer-run91.v1.json"
ARGS = (subject.MISSING_BUILD, RECEIPT, 0, "original", "unchanged", "approval")


class SQLOwnedExecutionTests(unittest.TestCase):
    def fixture(self, *, container=False, failure=True, writer_failed=False):
        log, delegated, made, calls = [], [], [], []
        class Resources:
            def __init__(self):
                self.reason, self.stop = None, threading.Event()
            def _failed(self, reason):
                self.reason = self.reason or reason
                self.stop.set()
            def sample(self):
                return {}
            def checkpoint_io(self):
                if self.reason:
                    raise ValueError(self.reason)
        class Reader:
            def __init__(self, resources):
                self.finished = False
                made.append(self)
            def summary(self):
                return dict(read_passes=3, bytes_read=123, bound_inputs=2, final_fresh_hashes=0,
                    finished=self.finished, chunk_bytes=65536, parse_budget_bytes=16777216,
                    read_bytes_per_second=8388608, maximum_scope_seconds=600)
            def finish(self):
                raise AssertionError("COLLECTOR_FINISH_FORBIDDEN")
        class Factory:
            def __init__(self):
                self.docker = "fixture-docker"
            def __call__(self, args, **kwargs):
                log.append("delegate")
                delegated.append((args, kwargs))
                return "fixture-command"
        driver = SimpleNamespace(IdleResources=Resources, LiveSQLReader=Reader, OwnedSQLJobFactory=Factory)
        intent = subject.ownership.make_intent(NONCE, "approval", RUN)
        pin = {"path": subject.ownership.journal_path(NONCE).relative_to(c.ROOT).as_posix(), "bytes": 500, "sha256": "a"*64}
        def writer(row):
            log.append("journal")
            if writer_failed:
                raise ValueError("SQL_OWNED_INTENT_EXCLUSIVE_REQUIRED")
            self.assertEqual(row, intent)
            return {"intent": row, "journal_pin": pin, "journal_fsync_before_delegate_completed": True}
        command_args = subject.ownership.run_arguments("fixture-docker", intent)
        def main(*arguments):
            calls.append(arguments)
            resources = driver.IdleResources()
            reader = driver.LiveSQLReader(resources)
            resources.checkpoint_io()
            if container:
                driver.OwnedSQLJobFactory()(command_args, env={"PRIVATE_FIXTURE": "NOT_SAVED"})
            print('{"state":"original short summary"}')
            if failure:
                raise ValueError("sql_source_link_or_missing")
            reader.finished = True
            return 0
        driver.main = main
        with patch.object(subject.ownership, "write_intent", side_effect=writer):
            row = subject.journalled_driver_call(driver, ARGS, SimpleNamespace(is_set=lambda: False), NONCE, "approval")
        row["child_event_closed"] = True
        self.assertIs(driver.OwnedSQLJobFactory, Factory)
        self.assertIs(driver.IdleResources, Resources)
        self.assertIs(driver.LiveSQLReader, Reader)
        self.assertEqual(calls, [ARGS])
        self.assertNotIn("NOT_SAVED", json.dumps(row))
        return row, log, delegated, command_args

    def parent(self, worker, *, force=False, active=0):
        return {"state": "FAILED_NOT_ACCEPTED" if force else "OWNED_CALL_TERMINAL_ACCOUNTED_NOT_SQL_OR_GATE",
            "forced_termination": force, "parent_event_closed": True, "worker_result": worker,
            "owned_job_profile": {"limits_readback": {"verified": True}, "owned_tree_empty": True,
                "cleanup_confirmed": True, "job_handle_closed": True, "last_job_accounting": {"active_processes": active}}}

    def finalize(self, *, container=False, failure=True, force=False, active=0, bad_final=False, backend=True,
            event_closed=True, reader_failed=False, count_drift=False, pin_drift=False):
        worker, _, _, _ = self.fixture(container=container, failure=failure)
        if count_drift:
            worker["accounted_call"]["cooperative_resource_count"] = 0
        parent = self.parent(None if force else worker, force=force, active=active)
        parent["parent_event_closed"] = event_closed
        intent = subject.ownership.make_intent(NONCE, "approval", RUN)
        journal = SimpleNamespace(exists=lambda: container,
            relative_to=lambda root: PurePosixPath(f"implementation/p09/evidence/p09-149-SQL-owned-intent-{NONCE}.v1.json"))
        reader = SimpleNamespace(pin=Mock(return_value=worker["journal_pin"]), json=Mock())
        if reader_failed:
            reader.pin.side_effect = ValueError("STOP_LOW_AVAILABLE_RAM")
        loaded_pin = copy.deepcopy(worker["journal_pin"])
        if pin_drift:
            loaded_pin["sha256"] = "b"*64
        original = {"state": subject.COMPONENT_STATE, "live_case": "approval", "source_index": 0,
            "input_mode": "original", "expected_formula_outcome": "unchanged", "run_id": RUN,
            "container_name": intent["container_name"], "image": intent["image_pin"], "resource_stop_reason": None}
        for key in ("container_removed", "source_freeze_exact_after", "protected_executables_exact_after",
                "resource_watcher_cleanup_confirmed", "actual_SQL_executed", "actual_Rust_DB_adapter_executed",
                "original_product_consumer_executed"):
            original[key] = True
        if bad_final:
            original["protected_executables_exact_after"] = False
        reader.json.return_value = original
        fallback = Mock(return_value={"backend_container_cleanup_confirmed": backend,
            "full_SQL_wrapper_cancellation_and_container_cleanup_qualified": False})
        with patch.object(subject.ownership, "journal_path", return_value=journal), \
                patch.object(subject.ownership, "load_intent", return_value={"intent": intent, "journal_pin": loaded_pin}), \
                patch.object(subject, "scoped_path", return_value=SimpleNamespace(exists=lambda: not failure)), \
                patch.object(subject, "parent_cleanup_from_loaded_intent", fallback):
            row = subject.finalize_owned_call(parent, NONCE, "approval", ARGS, object(), reader, "fixture-docker")
        self.assertFalse(row["full_SQL_wrapper_cancellation_and_container_cleanup_qualified"])
        self.assertFalse(row["product_complete"])
        self.assertEqual(row["P09_gate"], "OPEN")
        return row, fallback

    def test_three_cases_have_canonical_original_argument_order(self):
        with patch.object(subject, "scoped_path", return_value=None):
            for case in subject.ownership.CASES:
                row = subject.call_arguments(case, "product", 89, 35, "numeric_derivative", "changed")
                self.assertEqual(row, (subject.BUILD, f"implementation/p09/evidence/{'p09-146-corpus' if case == 'approval' else 'p09-148-authority'}-consumer-run89.v1.json", 35, "numeric_derivative", "changed", case))

    def test_boolean_selection_and_wrong_required_outcome_are_rejected(self):
        for args in ((True, 0, "original", "unchanged"), (1, True, "original", "unchanged"),
                (1, 36, "original", "unchanged"), (1, 0, "numeric_derivative", "unchanged"),
                (91, 0, "original", "unchanged")):
            with self.assertRaises(ValueError):
                subject.call_arguments("approval", "product", *args)

    def test_paths_reject_escape_and_links_without_writes(self):
        with self.assertRaises(ValueError):
            subject.scoped_path("../outside.json")
        with patch("pathlib.Path.is_symlink", return_value=True), self.assertRaises(ValueError):
            subject.scoped_path(RECEIPT)

    def test_journal_before_original_factory_same_args_env_and_restoration(self):
        row, log, delegated, args = self.fixture(container=True)
        self.assertEqual(log, ["journal", "delegate"])
        self.assertEqual(delegated, [(args, {"env": {"PRIVATE_FIXTURE": "NOT_SAVED"}})])
        self.assertTrue(row["journal_fsync_before_delegate_completed"])
        self.assertEqual(row["journal_write_count"], 1)

    def test_original_exception_and_partial_io_preserved_without_finish(self):
        row, _, delegated, _ = self.fixture()
        self.assertEqual(row["accounted_call"]["driver_error_code"], "sql_source_link_or_missing")
        self.assertFalse(row["accounted_call"]["source_final_hash_completed"])
        self.assertEqual(row["accounted_call"]["reader_IO"]["read_passes"], 3)
        self.assertEqual(delegated, [])
        self.assertIsNone(row["journal_pin"])

    def test_writer_failure_never_delegates_and_restores_dependencies(self):
        row, log, delegated, _ = self.fixture(container=True, writer_failed=True)
        self.assertEqual(log, ["journal"])
        self.assertEqual(delegated, [])
        self.assertIsNone(row["accounted_call"]["driver_return_code"])

    def test_discarded_summary_has_cumulative_byte_cap_and_no_content_buffer(self):
        sink = subject.DiscardBoundedSummary()
        self.assertEqual(sink.write("a"*4096), 4096)
        with self.assertRaises(ValueError):
            sink.write("한")
        self.assertEqual(set(vars(sink)), {"bytes_written"})

    def test_decoder_rejects_extra_duplicate_and_foreign_nonce(self):
        row, _, _, _ = self.fixture()
        values = [json.dumps(dict(row, extra="PRIVATE_FIXTURE")), json.dumps(dict(row, parent_nonce=RUN)),
            '{"schema_version":1,"schema_version":2}', "[]"]
        for value in values:
            with self.assertRaises(ValueError):
                subject.decode_worker(value, NONCE, "approval", RECEIPT)

    def test_decoder_rejects_raw_accounting_fields_and_secret_error(self):
        row, _, _, _ = self.fixture()
        for change in ({"extra": "PRIVATE_FIXTURE"}, {"driver_error_code": "PRIVATE_FIXTURE"}):
            changed = copy.deepcopy(row)
            changed["accounted_call"].update(change)
            with self.assertRaises(ValueError):
                subject.decode_worker(json.dumps(changed), NONCE, "approval", RECEIPT)

    def test_decoder_rejects_boolean_count_and_scope_upgrade(self):
        row, _, _, _ = self.fixture()
        for change in ({"journal_write_count": False}, {"accounted_call": dict(row["accounted_call"], product_complete=True)}):
            with self.assertRaises(ValueError):
                subject.decode_worker(json.dumps(dict(row, **change)), NONCE, "approval", RECEIPT)

    def test_parent_live_tree_never_launches_fallback(self):
        row, fallback = self.finalize(container=True, active=1)
        self.assertEqual(row["state"], "FAILED_NOT_ACCEPTED")
        fallback.assert_not_called()

    def test_forced_worker_failure_still_cleans_only_valid_intent_without_success(self):
        row, fallback = self.finalize(container=True, force=True)
        fallback.assert_called_once()
        self.assertTrue(row["backend_container_cleanup_confirmed"])
        self.assertEqual(row["state"], "FAILED_NOT_ACCEPTED")

    def test_pre_container_failure_never_invents_backend_absence(self):
        row, fallback = self.finalize()
        fallback.assert_not_called()
        self.assertEqual(row["state"], "ORIGINAL_DRIVER_FAILURE_ACCOUNTED_NOT_SQL_OR_GATE")
        self.assertIsNone(row["backend_container_cleanup_confirmed"])
        self.assertIsNone(row["original_receipt_pin"])

    def test_component_success_requires_original_protected_final_evidence(self):
        row, fallback = self.finalize(container=True, failure=False)
        self.assertEqual(row["state"], "ORIGINAL_SQL_COMPONENT_ACCOUNTED_NOT_FULL_WRAPPER_OR_GATE")
        fallback.assert_called_once()
        row, _ = self.finalize(container=True, failure=False, bad_final=True)
        self.assertEqual(row["state"], "FAILED_NOT_ACCEPTED")

    def test_backend_failure_never_restamps_original_failure_as_success(self):
        row, fallback = self.finalize(container=True, backend=None)
        fallback.assert_called_once()
        self.assertEqual(row["state"], "FAILED_NOT_ACCEPTED")
        self.assertIsNone(row["backend_container_cleanup_confirmed"])

    def test_event_close_failure_does_not_skip_owned_fallback_or_become_success(self):
        row, fallback = self.finalize(container=True, event_closed=False)
        fallback.assert_called_once()
        self.assertTrue(row["backend_container_cleanup_confirmed"])
        self.assertEqual(row["state"], "FAILED_NOT_ACCEPTED")

    def test_forced_missing_journal_leaves_backend_unknown(self):
        row, fallback = self.finalize(force=True)
        fallback.assert_not_called()
        self.assertIsNone(row["backend_container_cleanup_confirmed"])
        self.assertEqual(row["state"], "FAILED_NOT_ACCEPTED")

    def test_work_reader_stop_does_not_prevent_prior_bounded_fallback(self):
        row, fallback = self.finalize(container=True, reader_failed=True)
        fallback.assert_called_once()
        self.assertTrue(row["backend_container_cleanup_confirmed"])
        self.assertEqual(row["state"], "FAILED_NOT_ACCEPTED")

    def test_component_success_requires_single_original_resource_inventory(self):
        row, fallback = self.finalize(container=True, failure=False, count_drift=True)
        fallback.assert_called_once()
        self.assertEqual(row["state"], "FAILED_NOT_ACCEPTED")

    def test_closed_original_os_failure_and_collector_codes_remain_accounted(self):
        row, _, _, _ = self.fixture()
        for code in ("SQL_ACCOUNTED_DRIVER_OPERATION_FAILED", "SQL_CANCELLED_CALL_RESOURCE_INVENTORY_CHANGED"):
            changed = copy.deepcopy(row)
            changed["accounted_call"]["driver_error_code"] = code
            self.assertEqual(subject.decode_worker(json.dumps(changed), NONCE, "approval", RECEIPT), changed)

    def test_execute_case_event_close_error_still_reaches_finalizer(self):
        import run_supervised_sql_probe as runner
        worker, _, _, _ = self.fixture()
        parent = self.parent(worker)
        event = SimpleNamespace(name="fixture", closed=False, close=Mock(side_effect=ValueError("SQL_CANCEL_CLOSE_FAILED")))
        finalizer = Mock(return_value={"state": "FAILED_NOT_ACCEPTED"})
        with patch.object(runner.CancelEvent, "create", return_value=event), \
                patch.object(runner, "supervise_owned_call", return_value=parent), \
                patch.object(runner.subject.ownership, "journal_path", return_value=SimpleNamespace(exists=lambda: False)), \
                patch.object(runner.subject, "finalize_owned_call", finalizer):
            row = runner.execute_case("missing-input", "approval", ARGS, object(), object())
        self.assertEqual(row["state"], "FAILED_NOT_ACCEPTED")
        finalizer.assert_called_once()
        self.assertEqual(finalizer.call_args.args[0]["parent_event_close_error_code"], "SQL_CANCEL_CLOSE_FAILED")
        self.assertFalse(finalizer.call_args.args[0]["parent_event_closed"])

    def test_worker_intent_byte_drift_is_rejected_before_cleanup(self):
        row, fallback = self.finalize(container=True, pin_drift=True)
        fallback.assert_not_called()
        self.assertEqual(row["state"], "FAILED_NOT_ACCEPTED")

    def test_loaded_intent_adapter_does_not_reload_or_select_another_run(self):
        intent = subject.ownership.make_intent(NONCE, "approval", RUN)
        checked = {"intent": intent, "journal_pin": {"sha256": "fixture-pin"}}
        actor, parent, resources = object(), self.parent(None), object()
        with patch.object(subject.ownership, "load_intent", side_effect=AssertionError("RELOAD_FORBIDDEN")), \
                patch.object(subject, "OwnedCleanupCommand", return_value=actor) as factory, \
                patch.object(subject, "cleanup_from_intent", return_value={"state": "fixture"}) as cleanup:
            row = subject.parent_cleanup_from_loaded_intent(checked, parent, resources, "fixture-docker")
        factory.assert_called_once_with(intent, parent, resources, "fixture-docker")
        cleanup.assert_called_once_with(intent, actor)
        self.assertEqual(row["journal_pin"], checked["journal_pin"])
