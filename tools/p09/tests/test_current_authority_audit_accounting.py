"""Closed call/receipt contract mocks; no audit worker or filesystem writes."""
import copy
import json
from types import SimpleNamespace
import sys
import threading
import unittest
from unittest.mock import Mock, patch

import conservative_maintenance as c
import current_authority_audit_accounting as subject

PATH = "implementation/p09/evidence/p09-149-current-authority-SQL-receipts.actual-run90.v1.json"


class CurrentAuthorityAuditAccountingTests(unittest.TestCase):
    def fixture(self, *, code=3, error=None, count=1):
        previous = sys.argv
        calls = []
        class Resources:
            def __init__(self):
                self.reason, self.stop = None, threading.Event()
            def _failed(self, value):
                self.reason = self.reason or value
                self.stop.set()
            def sample(self):
                return {}
            def checkpoint_io(self):
                if self.reason:
                    raise ValueError(self.reason)
        audit = SimpleNamespace(SQLRuntimeResources=Resources)
        def main():
            calls.append(list(sys.argv))
            for _ in range(count):
                audit.SQLRuntimeResources().checkpoint_io()
            print("original short summary")
            if error:
                raise error
            return code
        audit.main = main
        with patch.object(subject, "original_receipt_path", return_value=PATH):
            row = subject.account_original_audit(audit, 90, SimpleNamespace(is_set=lambda: False),
                clock=Mock(side_effect=[10, 85]))
        self.assertIs(audit.SQLRuntimeResources, Resources)
        self.assertIs(sys.argv, previous)
        self.assertEqual(calls, [[str(c.ROOT/subject.SELF_AUDIT), "--audit", "--run", "90"]])
        row["child_event_closed"] = True
        return row

    def original(self):
        return json.loads((c.ROOT/"implementation/p09/evidence/p09-149-current-authority-SQL-receipts.actual-run01.v1.json").read_text(encoding="utf-8"))

    def test_original_arguments_dependencies_and_full_call_clock_preserved(self):
        row = self.fixture()
        self.assertTrue(row["original_dependencies_restored"])
        self.assertTrue(row["original_argv_restored"])
        self.assertEqual(row["call_wall_seconds"], 75)
        self.assertEqual(row["resource_count"], 1)

    def test_original_partial_exit_three_is_not_returned_as_success(self):
        row = self.fixture()
        self.assertEqual(row["original_return_code"], 3)
        self.assertFalse(row["raw_stdout_stored"])
        self.assertNotIn("original short summary", json.dumps(row))

    def test_original_exception_is_closed_and_dependencies_restored(self):
        row = self.fixture(error=OSError("PRIVATE_FIXTURE"))
        self.assertEqual(row["state"], "FAILED_NOT_ACCEPTED")
        self.assertEqual(row["original_error_code"], "CURRENT_AUTHORITY_CALL_OPERATION_FAILED")
        self.assertNotIn("PRIVATE_FIXTURE", json.dumps(row))

    def test_boolean_or_unexpected_original_exit_is_rejected(self):
        for value in (True, 1, 2, None):
            row = self.fixture(code=value)
            self.assertEqual(row["state"], "FAILED_NOT_ACCEPTED")
            self.assertIsNone(row["original_return_code"])

    def test_multiple_resources_cannot_become_one_accounted_workload(self):
        row = self.fixture(count=2)
        self.assertEqual(row["state"], "FAILED_NOT_ACCEPTED")
        self.assertEqual(row["resource_count"], 2)

    def test_decoder_rejects_extra_duplicate_and_wrong_receipt(self):
        row = self.fixture()
        with patch.object(subject, "original_receipt_path", return_value=PATH):
            self.assertEqual(subject.decode_worker(json.dumps(row), 90), row)
            for value in (json.dumps(dict(row, raw="PRIVATE_FIXTURE")), json.dumps(dict(row, original_receipt_path="other")),
                    '{"state":1,"state":2}'):
                with self.assertRaises(ValueError):
                    subject.decode_worker(value, 90)

    def test_decoder_rejects_nonfinite_time_boolean_code_and_secret_error(self):
        row = self.fixture()
        with patch.object(subject, "original_receipt_path", return_value=PATH):
            for change in ({"call_wall_seconds": float("nan")}, {"original_return_code": True},
                    {"original_error_code": "PRIVATE_FIXTURE"}):
                with self.assertRaises(ValueError):
                    subject.decode_worker(json.dumps(dict(row, **change)), 90)

    def test_actual_original_three_case_receipt_stays_partial_with_three_missing(self):
        result = subject.classify_original_receipt(self.original(), 3)
        self.assertEqual(len(result["validated_current_cases"]), 3)
        self.assertEqual(len(result["missing_required_replays"]), 3)
        self.assertFalse(result["all_six_current_replays_validated"])
        self.assertFalse(result["product_complete"])

    def test_final_hash_watcher_or_full_scope_upgrade_cannot_override_partial(self):
        original = self.original()
        for key, value in (("source_freeze_exact_after", False), ("resource_watcher_cleanup_confirmed", False),
                ("all_six_current_replays_validated", True), ("full_current_authority_audit_executed", True),
                ("product_complete", True)):
            with self.assertRaises(ValueError):
                subject.classify_original_receipt(dict(original, **{key: value}), 3)

    def test_missing_replays_false_io_and_exit_zero_are_rejected(self):
        original = self.original()
        for change in ({"missing_required_replays": []}, {"bounded_input_IO": dict(original["bounded_input_IO"], finished=False)}):
            with self.assertRaises(ValueError):
                subject.classify_original_receipt(dict(original, **change), 3)
        with self.assertRaises(ValueError):
            subject.classify_original_receipt(original, 0)
