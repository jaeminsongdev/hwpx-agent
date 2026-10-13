import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import review_flat_prebody_stop_v1 as r


class StopReviewContracts(unittest.TestCase):
    def row(self):
        return dict(state="DEFERRED_NOT_STARTED", worker_created=False,
            product_body_observed=False, Native_source_frame_qualified=False,
            cleanup_confirmed=True, owned_tree_empty=True, accepted_count_delta=0,
            full249_current_qualified=False, signed16_current_qualified=False,
            P09_gate="OPEN", A12_gate="OPEN", A13_gate="OPEN",
            stop_reason="STOP_SYSTEM_COMMIT_PRESSURE", source_freeze=[], passed_test_names=[],
            source_frame=None, selected_test_index=125, elapsed_seconds=1.0,
            samples=[dict(time_utc="synthetic", system_cpu_percent=10.0, available_ram_percent=50.0)])

    def test_prebody_only_positive_without_counter_is_unknown(self):
        out = r.review(self.row())
        self.assertIsNone(out["available_PDH_process_maxima"]["MsMpEng"])
        self.assertFalse(out["automatic_retry_authorized"])
        self.assertEqual(out["accepted_count_delta"], 0)

    def test_product_or_cleanup_or_gate_change_refused(self):
        for key, value in (("product_body_observed", True), ("worker_created", True),
                           ("cleanup_confirmed", False), ("P09_gate", "PASS"),
                           ("accepted_count_delta", 1), ("Native_source_frame_qualified", True)):
            row = self.row(); row[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): r.review(row)

    def test_pass_names_or_committed_freeze_refused(self):
        for key in ("source_freeze", "passed_test_names"):
            row = self.row(); row[key] = ["not empty"]
            with self.subTest(key=key), self.assertRaises(ValueError): r.review(row)

    def test_bad_or_oversized_samples_refused(self):
        for samples in ([], {}, [self.row()["samples"][0]]*4097):
            row = self.row(); row["samples"] = samples
            with self.assertRaises(ValueError): r.review(row)
        for value in (True, float("nan"), -1.0, 101.0):
            row = self.row(); row["samples"][0]["system_cpu_percent"] = value
            with self.subTest(value=value), self.assertRaises(ValueError): r.review(row)

    def test_one_pass_aggregate_has_only_three_hot_rows(self):
        row = self.row()
        row["samples"] = [dict(row["samples"][0], system_cpu_percent=float(x)) for x in range(100)]
        out = r.review(row)
        self.assertEqual(len(out["hot_samples"]), 3)
        self.assertEqual(out["CPU_threshold_counts"]["90"]["samples"], 10)
        self.assertEqual(out["CPU_threshold_counts"]["90"]["longest_consecutive_samples"], 10)
        self.assertLess(len(json.dumps(out).encode()), 8192)

    def test_counters_never_relabelled_as_current_hot_or_causal(self):
        row = self.row()
        row["samples"][0]["serial_cpu_attribution"] = dict(available=True, interval_seconds=8.0,
            values=dict(MsMpEng=dict(pid_stable=True, machine_cpu_percent=1.0),
                        System=dict(pid_stable=True, machine_cpu_percent=2.0)))
        out = r.review(row)
        self.assertTrue(out["counters_not_causal_or_hot_interval_proof"])
        self.assertTrue(out["last_available_PDH_sample"]["not_same_original_K32_interval"])
        self.assertFalse(out["hot_samples"][0]["hot_interval_process_attribution_established"])
        row["samples"][0]["serial_cpu_attribution"]["values"]["MsMpEng"]["pid_stable"] = False
        with self.assertRaises(ValueError): r.review(row)

    def test_full_trace_or_secret_field_is_not_copied(self):
        row = self.row(); row["arbitrary_private_field"] = "synthetic-private-sentinel"
        row["samples"][0]["process_command"] = "synthetic-private-sentinel"
        out = r.review(row)
        self.assertNotIn("synthetic-private-sentinel", json.dumps(out))
        self.assertNotIn("samples", out)

    def test_supported_stop_only_and_does_not_mutate_input(self):
        row = self.row(); before = copy.deepcopy(row)
        r.review(row); self.assertEqual(row, before)
        row["stop_reason"] = "UNKNOWN_STOP"
        with self.assertRaises(ValueError): r.review(row)

    def test_frame_requires_all_handles_closed_and_zero_bytes(self):
        row = self.row()
        row["source_frame"] = dict(frame_state="CLOSED", registered_live_frame=False,
            original_two_actual_per_case_byte_reads_retained=True, input_exclusions_added=False,
            actual_byte_boundaries=[], input_count=1, input_bytes=1,
            handles=dict(input_lock_handles_opened=1, input_lock_handles_closed=1,
                input_lock_handles_remaining=0, input_lock_cleanup_confirmed=True,
                handle_close_failed_attempts=0, active_reader_bindings=0,
                active_byte_streams=0, byte_stream_identity_checks=0))
        self.assertEqual(r.review(row)["closed_handles"]["closed"], 1)
        row["source_frame"]["handles"]["input_lock_handles_remaining"] = 1
        with self.assertRaises(ValueError): r.review(row)

    def test_query_cleanup_or_multiple_sampler_refused(self):
        row = self.row()
        row["serial_CPU_attribution"] = dict(existing_observer_instances=1,
            second_sampler_thread_or_process=False, original_CPU_RAM_decisions_replaced=False,
            probes=[dict(query_remaining=False, cleanup_confirmed=True)])
        r.review(row)
        row["serial_CPU_attribution"]["probes"][0]["query_remaining"] = True
        with self.assertRaises(ValueError): r.review(row)
        row["serial_CPU_attribution"]["probes"][0]["query_remaining"] = False
        row["serial_CPU_attribution"]["existing_observer_instances"] = 2
        with self.assertRaises(ValueError): r.review(row)


if __name__ == "__main__": unittest.main()
