"""Collector-only mocks; original SQL drivers/reader must remain intact."""
import json
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

import sql_call_accounting as subject


class SQLCallAccountingTests(unittest.TestCase):
    def fixture(self, *, code=0, error=None, finished=True, before_reader=False, readers=1):
        made = []
        class Reader:
            def __init__(self, marker):
                self.marker, self.finished = marker, finished
                self.finish = Mock(side_effect=AssertionError("COLLECTOR_FINISH_FORBIDDEN"))
                made.append(self)
            def summary(self):
                return {"read_passes": 3, "bytes_read": 123, "final_fresh_hashes": 1 if self.finished else 0,
                    "finished": self.finished}
        driver = SimpleNamespace(LiveSQLReader=Reader)
        seen = []
        def main(*args):
            seen.append(args)
            if not before_reader:
                for _ in range(readers):
                    driver.LiveSQLReader("original-resource")
            if error:
                raise error
            return code
        driver.main = main
        return driver, Reader, made, seen

    def run_fixture(self, **kwargs):
        driver, original, made, seen = self.fixture(**kwargs)
        row = subject.account_driver_call(driver, ("same-build", "same-receipt", 0, "original", "unchanged", "trust"),
            clock=Mock(side_effect=[10, 18]))
        self.assertIs(driver.LiveSQLReader, original)
        return row, made, seen

    def test_success_preserves_arguments_return_and_completed_IO(self):
        row, made, seen = self.run_fixture()
        self.assertEqual(seen, [("same-build", "same-receipt", 0, "original", "unchanged", "trust")])
        self.assertEqual(row["driver_return_code"], 0)
        self.assertTrue(row["source_final_hash_completed"])
        self.assertEqual(row["reader_IO"]["bytes_read"], 123)
        self.assertEqual(made[0].marker, "original-resource")

    def test_pre_receipt_exception_preserves_partial_IO_not_final_hash(self):
        row, _, _ = self.run_fixture(error=ValueError("STOP_FIXTURE"), finished=False)
        self.assertEqual(row["driver_error_code"], "STOP_FIXTURE")
        self.assertIsNone(row["driver_return_code"])
        self.assertEqual(row["reader_IO"]["read_passes"], 3)
        self.assertFalse(row["source_final_hash_completed"])

    def test_failure_return_code_is_not_success_or_product_qualification(self):
        row, _, _ = self.run_fixture(code=1, finished=False)
        self.assertEqual(row["state"], "ORIGINAL_DRIVER_RETURNED_FAILURE")
        self.assertFalse(row["product_complete"])
        self.assertEqual(row["P09_gate"], "OPEN")

    def test_collector_never_calls_finish_on_success_or_failure(self):
        for error in (None, ValueError("STOP_FIXTURE")):
            _, made, _ = self.run_fixture(error=error)
            made[0].finish.assert_not_called()

    def test_pre_reader_failure_does_not_invent_IO_or_cleanup(self):
        row, made, _ = self.run_fixture(before_reader=True, error=OSError("PRIVATE_FIXTURE"))
        self.assertEqual(row["reader_count"], 0)
        self.assertIsNone(row["reader_IO"])
        self.assertFalse(row["source_final_hash_completed"])
        self.assertEqual(made, [])

    def test_raw_exception_values_are_redacted(self):
        for message in ("PRIVATE FIXTURE=value", "FIXTURETOKEN123"):
            row, _, _ = self.run_fixture(error=ValueError(message))
            self.assertNotIn(message, json.dumps(row))
            self.assertEqual(row["driver_error_code"], "SQL_ACCOUNTED_DRIVER_REDACTED_FAILURE")

    def test_boolean_return_code_is_not_integer_success(self):
        row, _, _ = self.run_fixture(code=False)
        self.assertEqual(row["driver_error_code"], "SQL_ACCOUNTING_DRIVER_EXIT_INVALID")

    def test_multiple_readers_do_not_hide_IO_or_fake_original_contract(self):
        row, _, _ = self.run_fixture(readers=2)
        self.assertEqual(row["state"], "FAILED_NOT_ACCEPTED")
        self.assertEqual(row["accounting_error_code"], "SQL_ACCOUNTING_READER_INVENTORY_CHANGED")

    def test_elapsed_includes_call_and_prehash_but_not_import_or_outer_wrapper(self):
        row, _, _ = self.run_fixture()
        self.assertEqual(row["driver_call_wall_seconds"], 8)
        self.assertTrue(row["includes_driver_admission_and_pre_hash"])
        self.assertFalse(row["includes_module_import_and_outer_supervision"])
        self.assertFalse(row["full_SQL_wrapper_cancellation_and_container_cleanup_qualified"])

    def test_nonfinite_or_regressing_clocks_do_not_leave_success(self):
        for ending in (float("nan"), float("inf"), 9):
            driver, original, _, _ = self.fixture()
            row = subject.account_driver_call(driver, (), clock=Mock(side_effect=[10, ending]))
            self.assertEqual(row["state"], "FAILED_NOT_ACCEPTED")
            self.assertIs(driver.LiveSQLReader, original)
