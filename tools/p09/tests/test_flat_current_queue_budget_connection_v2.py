import copy
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import flat_current_queue_budget_runtime_v2 as r
import flat_current_queue_budget_acceptance_v2 as accept


class TerminalConnectionContracts(unittest.TestCase):
    def step(self, index=125):
        return NS(index=index, before=index-7, pin=dict(path="step", bytes=1, sha256="0"*64))

    def data(self, index=125):
        step = self.step(index)
        return dict(schema_version="hwpx-agent.p09-flat-budget-terminal-connection/v2",
            index=index, before=step.before, run=r.attempt(index), base_step_pin=step.pin,
            prior_budget_connection_pin=dict(path=r.prior.data_path(index), bytes=1, sha256="0"*64),
            failed_runtime_pins=[r.FAILED125, r.FAILED002] if index == 125 else [],
            terminal_qualification_pin=r.TERMINAL_QUAL,
            connection_code_pins=[dict(path=n, bytes=1, sha256="0"*64) for n in r.FILES])

    def failure(self):
        return dict(state="DEFERRED_NOT_STARTED", selected_test_index=125,
            stop_reason="STOP_NATIVE_OPEN_AFTER_HOST_SATURATION", worker_created=False,
            product_body_observed=False, Native_source_frame_qualified=False,
            current_generation_runtime_candidate_qualified=False,
            cleanup_confirmed=True, owned_tree_empty=True, accepted_count_delta=0,
            full249_current_qualified=False, signed16_current_qualified=False,
            P09_gate="OPEN", A12_gate="OPEN", A13_gate="OPEN", source_freeze=[],
            passed_test_names=[], source_frame=dict(frame_state="CLOSED", registered_live_frame=False,
                actual_byte_boundaries=[], handles=dict(input_lock_handles_opened=1020,
                    input_lock_handles_closed=1020, input_lock_handles_remaining=0,
                    input_lock_cleanup_confirmed=True, handle_close_failed_attempts=0,
                    active_reader_bindings=0, active_byte_streams=0, byte_stream_identity_checks=0)),
            serial_CPU_attribution=dict(early_budget_probe_connection=dict(
                existing_observer_instances=1, budget_probe_instances=1,
                instance_binding_observed=True, additional_PDH_query=False,
                second_sampler_thread_or_process=False, original_K32_decisions_replaced=False),
                probes=[dict(query_remaining=False, cleanup_confirmed=True,
                             early_budget_checks=113, early_budget_stops=1)]))

    def complete_shape(self):
        return dict(state=r.base.PASS, exit_code=0, worker_created=True, product_body_observed=True,
            Native_source_frame_qualified=True, current_generation_runtime_candidate_qualified=True,
            cleanup_confirmed=True, owned_tree_empty=True, stop_reason=None, capture_diagnostics={})

    def test_exact125_third_attempt_only(self):
        self.assertEqual(r.validate_data(self.data(), self.step())["run"], 3)
        for value in (1, 2, 4, True):
            row = self.data(); row["run"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                r.validate_data(row, self.step())

    def test_later_first_attempt_not_automatic_retry(self):
        self.assertEqual(r.validate_data(self.data(126), self.step(126))["run"], 1)
        row = self.data(126); row["run"] = 2
        with self.assertRaises(ValueError): r.validate_data(row, self.step(126))

    def test_bad_typed_cursor_and_extra_data(self):
        for key, value in (("index", True), ("before", 119), ("extra", False)):
            row = self.data(); row[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                r.validate_data(row, self.step())
        for index in (124, 250, True):
            with self.assertRaises(ValueError): r.attempt(index)

    def test_both_failed_pins_exact_order_and_whole_inventory(self):
        for value in ([], [r.FAILED125], [r.FAILED002, r.FAILED125],
                      [r.FAILED125, dict(r.FAILED002, sha256="1"*64)]):
            row = self.data(); row["failed_runtime_pins"] = value
            with self.assertRaises(ValueError): r.validate_data(row, self.step())
        row = self.data(); row["connection_code_pins"].pop()
        with self.assertRaises(ValueError): r.validate_data(row, self.step())

    def test_prior_data_and_qualification_drift_refused(self):
        row = self.data(); row["prior_budget_connection_pin"]["path"] = r.prior.data_path(126)
        with self.assertRaises(ValueError): r.validate_data(row, self.step())
        row = self.data(); row["terminal_qualification_pin"] = dict(r.TERMINAL_QUAL, bytes=1)
        with self.assertRaises(ValueError): r.validate_data(row, self.step())

    def test_second_failure_exact_prebody_positive_not_acceptance(self):
        row = self.failure(); before = copy.deepcopy(row)
        self.assertTrue(r.review_second_failure(row)); self.assertEqual(row, before)

    def test_second_failure_cannot_replay_body_or_hide_cleanup(self):
        for key, value in (("product_body_observed", True), ("worker_created", True),
            ("current_generation_runtime_candidate_qualified", True), ("cleanup_confirmed", False),
            ("source_freeze", ["x"]), ("passed_test_names", ["x"]), ("accepted_count_delta", 1)):
            row = self.failure(); row[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                r.review_second_failure(row)

    def test_second_failure_locks_frame_and_probe_exact(self):
        for branch, key, value in (("handles", "input_lock_handles_remaining", 1),
                                  ("handles", "input_lock_handles_opened", 1021)):
            row = self.failure(); row["source_frame"][branch][key] = value
            with self.assertRaises(ValueError): r.review_second_failure(row)
        row = self.failure(); row["source_frame"]["actual_byte_boundaries"] = ["x"]
        with self.assertRaises(ValueError): r.review_second_failure(row)
        row = self.failure(); row["serial_CPU_attribution"]["probes"][0]["query_remaining"] = True
        with self.assertRaises(ValueError): r.review_second_failure(row)

    def test_canonical_roots_exclude_prior_attempts(self):
        self.assertTrue(accept.root_path(self.step()).endswith("run003.v1.json"))
        self.assertTrue(accept.root_path(self.step(126)).endswith("run001.v1.json"))
        with patch.object(r.base, "CONFIG", self.step()):
            for run in (1, 2, 4):
                with self.assertRaisesRegex(ValueError, "EXACT_TERMINAL_REVIEWED_ROOT"):
                    accept.run(dict(path=f"implementation/p09/evidence/p09-361-case125-current-runtime-run{run:03}.v1.json"))

    def test_prebody_rejected_before_capture_or_full_oracle(self):
        with patch.object(accept.prior.metadata, "validate_candidate", side_effect=AssertionError("NOT_REACHED")):
            with self.assertRaisesRegex(ValueError, "TERMINAL_REVIEW_COMPLETED_BODY_REQUIRED"):
                accept.validate_candidate(None, self.failure(), None, None, None, None)

    def test_complete_shape_still_delegates_retained_full_oracle(self):
        events = []
        # 원 validator와 같이 closure 없는 module-level 함수로 계약을 검사한다.
        environment = {"events": events}
        exec("def full(q,row,listing,oldbody,fresh,ctx,flat=True):\n"
             " events.append('full')\n return {'sentinel':True},{}", environment)
        full = environment["full"]
        with patch.object(accept.prior.metadata, "validate_candidate", full), \
             patch.object(accept.prior, "actual_budget_binding", side_effect=lambda row: events.append("budget")):
            evidence, proof = accept.validate_candidate(None, self.complete_shape(), None, None, None, None)
        self.assertEqual(events, ["full", "budget"])
        self.assertTrue(evidence["sentinel"])
        self.assertTrue(proof["actual_completed_body_admission_before_capture_access"])

    def test_prepare_counted_root_ast_preserved(self):
        raw = b"def prepare(q, root_pin):\n step=r.CONFIG\n require(root_pin['path']==f'implementation/p09/evidence/p09-361-case{step.index}-current-runtime-run001.v1.json','ROOT')\n return 'whole-oracle'\n"
        self.assertTrue(callable(accept.prepare_projection(raw)))
        with self.assertRaises(ValueError):
            accept.prepare_projection(raw.replace(b"run001", b"run004"))

    def test_template_and_full_preflight_preview_no_module_mutation(self):
        if r.base.CONFIG is None: r.base.configure(125)
        old = r.base.stable.stable.prior.build.pressure.PreSaturationReadCheckpoint
        engine, proof = r.template()
        self.assertIs(r.base.stable.stable.prior.build.pressure.PreSaturationReadCheckpoint, old)
        self.assertTrue(proof["original_engine_bytecode_unchanged"])
        self.assertEqual(engine.run_owned.__globals__["SELF"], r.SELF)
        pin = r.prior.METADATA_PIN
        with (r.c.ROOT / pin["path"]).open("rb") as stream: raw = stream.read(pin["bytes"] + 1)
        self.assertTrue(callable(r.preflight_projection(raw)))
        with self.assertRaises(ValueError): r.preflight_projection(raw + b"\n")

    def test_parent_rejects_unauthorized_runs_before_worker_or_native(self):
        if r.base.CONFIG is None: r.base.configure(125)
        for run in (1, 2, 4, True):
            with self.subTest(run=run), self.assertRaises(ValueError):
                r.run_owned(run)


if __name__ == "__main__": unittest.main()
