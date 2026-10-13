"""Actual-receipt injected contracts; never execute product, Native or OS probes."""
import copy
import json
import unittest
from unittest.mock import patch
import review_flat_completed_body_stop_v1 as subject

STOP_ROW = ROOT_PIN = CASE = None
INDEX = PRIOR_COUNT = None
CHECKPOINT = lambda: None
EXPECTED_ORIGINAL_COMPACT = None


class CompletedStopContracts(unittest.TestCase):
    def setUp(self):
        self.assertIsInstance(STOP_ROW, dict)
        CHECKPOINT()

    def review(self, row):
        CHECKPOINT()
        return subject.review(row, ROOT_PIN, case=CASE, index=INDEX, prior_count=PRIOR_COUNT)

    def test_actual_completed_child_is_never_accepted(self):
        proof = self.review(STOP_ROW)
        self.assertEqual(proof["state"], subject.PASS)
        self.assertEqual(proof["accepted_count_delta"], 0)
        self.assertFalse(proof["current_Native_frame_qualified"])
        self.assertFalse(proof["original_after_source_complete"])
        self.assertFalse(proof["original_product_body_reexecution_allowed"])

    def test_closed_output_no_full_source_resources_or_logs(self):
        result = subject.compact(STOP_ROW, self.review(STOP_ROW))
        self.assertLessEqual(len(json.dumps(result).encode()), 8192)
        for name in ("source_freeze", "samples", "source_frame", "capture_diagnostics", "stdout", "stderr"):
            self.assertNotIn(name, result)
        self.assertEqual(len(result["resource_tail"]), 4)
        self.assertFalse(result["causal_trigger_or_PC_freeze_fix_established"])

    def test_output_does_not_use_large_unknown_payload(self):
        row = copy.copy(STOP_ROW)
        class MustNotSerialize:
            def __repr__(self):
                raise AssertionError("UNTRUSTED_OR_LARGE_UNKNOWN_OUTPUT")
        row["raw_log"] = MustNotSerialize()
        row["unknown"] = MustNotSerialize()
        result = subject.compact(row, self.review(row))
        self.assertNotIn("unknown", result)
        self.assertNotIn("raw_log", result)

    def test_streaming_summary_matches_frozen_original_exactly(self):
        self.assertIsInstance(EXPECTED_ORIGINAL_COMPACT, dict)
        self.assertEqual(subject.compact(STOP_ROW, self.review(STOP_ROW)), EXPECTED_ORIGINAL_COMPACT)

    def test_all_samples_are_checked_not_only_tail(self):
        row = copy.copy(STOP_ROW)
        row["samples"] = [dict(STOP_ROW["samples"][0], system_cpu_percent=float("nan"))] + STOP_ROW["samples"]
        with self.assertRaisesRegex(ValueError, "FLAT_COMPLETED_STOP_RESOURCE_VALUES"):
            subject.compact(row, self.review(row))

    def test_both_existing_sample_groups_keep_order(self):
        row = copy.copy(STOP_ROW)
        all_rows = STOP_ROW["samples"] + STOP_ROW.get("post_Job_cleanup_resource_samples", [])
        row["samples"] = all_rows[:-2]
        row["post_Job_cleanup_resource_samples"] = all_rows[-2:]
        self.assertEqual(subject.compact(row, self.review(row)), EXPECTED_ORIGINAL_COMPACT)

    def test_empty_resources_are_not_fabricated(self):
        row = copy.copy(STOP_ROW)
        row["samples"] = []; row["post_Job_cleanup_resource_samples"] = []
        with self.assertRaisesRegex(ValueError, "FLAT_COMPLETED_STOP_RESOURCE_SAMPLES"):
            subject.compact(row, self.review(row))

    def test_arbitrary_resource_iterators_are_denied(self):
        row = copy.copy(STOP_ROW)
        row["samples"] = iter(STOP_ROW["samples"])
        with self.assertRaisesRegex(ValueError, "FLAT_COMPLETED_STOP_RESOURCE_SAMPLE_LIST"):
            subject.compact(row, self.review(row))


def negative(name, change):
    def contract(self):
        row = copy.deepcopy(STOP_ROW)
        change(row)
        with self.assertRaisesRegex(ValueError, "^FLAT_COMPLETED_STOP_"):
            self.review(row)
        CHECKPOINT()
    contract.__name__ = "test_reject_" + name
    setattr(CompletedStopContracts, contract.__name__, contract)


for name, field, value in (
    ("fake_native_pass", "Native_source_frame_qualified", True),
    ("positive_candidate", "state", "PASS_EXACT_CURRENT_QUEUE_NATIVE_RUNTIME_CANDIDATE_NOT_QUEUE_OR_GATE"),
    ("no_completed_child", "product_body_observed", False),
    ("no_actual_child", "actual_product_child_executed", False),
    ("wrong_phase", "operation_phase", "source_preflight"),
    ("failed_cleanup", "cleanup_confirmed", False),
    ("not_empty", "owned_tree_empty", False),
    ("wrong_cursor", "prior_queue_cases", 999),
    ("queue_advance", "accepted_count_delta", 1),
    ("closed_gate", "P09_gate", "CLOSED"),
    ("wrong_passed_case", "passed_test_names", ["different"]),
    ("partial_terminal", "terminal_summary", {}),
    ("no_sources", "source_freeze", []),
    ("bool_exit", "exit_code", False),
    ("extended_deadline", "maximum_seconds", 1201)):
    negative(name, lambda x, k=field, v=value: x.update({k: v}))

negative("partial_capture", lambda x: x["capture_diagnostics"].update(complete_streams=False))
negative("missing_capture_bytes", lambda x: x["capture_diagnostics"]["buffered_bytes"].update(stdout=0))
negative("wrong_before_bytes", lambda x: x["source_frame"]["actual_byte_boundaries"][0]["reader_diagnostics"].update(bytes_read=0))
negative("false_after_complete", lambda x: x["source_frame"]["actual_byte_boundaries"].append(copy.deepcopy(x["source_frame"]["actual_byte_boundaries"][0])))
negative("held_handle_remaining", lambda x: x["source_frame"]["handles"].update(input_lock_handles_remaining=1))
negative("extended_native_deadline", lambda x: x["source_frame"]["handles"].update(maximum_lock_seconds=601))
negative("wrong_job_cpu_limit", lambda x: x["owned_limits_readback"].update(cpu_hard_cap_machine_percent=100))
negative("source_reparse_exclusion", lambda x: x["source_frame"].update(input_exclusions_added=True))
