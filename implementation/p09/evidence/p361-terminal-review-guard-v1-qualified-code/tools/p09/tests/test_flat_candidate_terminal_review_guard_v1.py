import copy
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import flat_candidate_terminal_review_guard_v1 as guard


class TerminalReviewContracts(unittest.TestCase):
    def row(self):
        return dict(state=guard.original.original.r.PASS, exit_code=0, worker_created=True,
            product_body_observed=True, Native_source_frame_qualified=True,
            current_generation_runtime_candidate_qualified=True, cleanup_confirmed=True,
            owned_tree_empty=True, stop_reason=None, capture_diagnostics={})

    def test_complete_shape_is_only_admission_not_acceptance(self):
        row = self.row(); before = copy.deepcopy(row)
        self.assertTrue(guard.require_completed_body(row))
        self.assertEqual(row, before)

    def test_prebody_refused_before_missing_capture(self):
        row = self.row(); row.update(state="DEFERRED_NOT_STARTED", worker_created=False,
                                    product_body_observed=False, capture_diagnostics=None)
        with self.assertRaisesRegex(ValueError, "TERMINAL_REVIEW_COMPLETED_BODY_REQUIRED"):
            guard.require_completed_body(row)

    def test_incomplete_flag_types_and_cleanup_refused(self):
        for key, value in (("exit_code", True), ("worker_created", False),
            ("product_body_observed", False), ("Native_source_frame_qualified", False),
            ("current_generation_runtime_candidate_qualified", False),
            ("cleanup_confirmed", False), ("owned_tree_empty", False), ("stop_reason", "STOP")):
            row = self.row(); row[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                guard.require_completed_body(row)

    def test_missing_capture_refused_even_if_forged_flags(self):
        row = self.row(); row["capture_diagnostics"] = None
        with self.assertRaisesRegex(ValueError, "TERMINAL_REVIEW_CAPTURE_REQUIRED"):
            guard.require_completed_body(row)

    def test_complete_shape_still_calls_original_full_validator(self):
        sentinel = object()
        with patch.object(guard.original, "validate_candidate", return_value=sentinel) as full:
            self.assertIs(guard.validate_candidate(None, self.row(), None, None, None, None), sentinel)
            full.assert_called_once()

    def test_prebody_never_calls_or_swallows_original_validator(self):
        row = self.row(); row["worker_created"] = False
        with patch.object(guard.original, "validate_candidate", side_effect=AssertionError("FULL_NOT_REACHED")) as full:
            with self.assertRaises(ValueError):
                guard.validate_candidate(None, row, None, None, None, None)
            full.assert_not_called()

    def test_original_validator_errors_not_promoted_to_pass(self):
        with patch.object(guard.original, "validate_candidate", side_effect=ValueError("FULL_ORACLE_REJECT")):
            with self.assertRaisesRegex(ValueError, "FULL_ORACLE_REJECT"):
                guard.validate_candidate(None, self.row(), None, None, None, None)

    def test_same_original_counted_root_projection_no_drift(self):
        raw = b"def prepare(q, root_pin):\n step=r.CONFIG\n require(root_pin['path']==f'implementation/p09/evidence/p09-361-case{step.index}-current-runtime-run001.v1.json','ROOT')\n return 'whole-oracle'\n"
        self.assertTrue(callable(guard.prepare_projection(raw)))
        with self.assertRaises(ValueError):
            guard.prepare_projection(raw.replace(b"run001", b"run003"))


if __name__ == "__main__": unittest.main()
