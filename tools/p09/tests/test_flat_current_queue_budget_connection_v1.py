import copy
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import flat_current_queue_budget_runtime_v1 as r
import flat_current_queue_budget_acceptance_v1 as accept


class BudgetConnectionContracts(unittest.TestCase):
    def step(self, index=125):
        return NS(index=index, before=index-7,
                  pin=dict(path="step", bytes=1, sha256="0"*64))

    def data(self, index=125):
        step = self.step(index)
        return dict(schema_version="hwpx-agent.p09-flat-budget-connection/v1",
            index=index, before=step.before, run=r.attempt(index), base_step_pin=step.pin,
            metadata_connection_pin=dict(path=r.metadata.data_path(index), bytes=1, sha256="0"*64),
            failed_runtime_pin=r.FAILED125 if index == 125 else None,
            budget_qualification_pin=r.BUDGET_QUAL, observer_qualification_pin=r.OBSERVER_QUAL,
            connection_code_pins=[dict(path=n, bytes=1, sha256="0"*64) for n in r.FILES])

    def failure(self):
        return dict(state="DEFERRED_NOT_STARTED", selected_test_index=125,
            stop_reason="STOP_NATIVE_OPEN_AFTER_HOST_SATURATION", worker_created=False,
            product_body_observed=False, Native_source_frame_qualified=False,
            cleanup_confirmed=True, owned_tree_empty=True, accepted_count_delta=0,
            full249_current_qualified=False, signed16_current_qualified=False,
            P09_gate="OPEN", A12_gate="OPEN", A13_gate="OPEN", passed_test_names=[],
            source_freeze=[], source_frame=dict(frame_state="CLOSED", actual_byte_boundaries=[],
                handles=dict(input_lock_handles_opened=2178, input_lock_handles_closed=2178,
                    input_lock_handles_remaining=0, input_lock_cleanup_confirmed=True,
                    handle_close_failed_attempts=0, active_reader_bindings=0,
                    active_byte_streams=0, byte_stream_identity_checks=0)))

    def binding(self):
        # Synthetic shape only; not a Native/product candidate.
        return dict(serial_CPU_attribution=dict(
            early_budget_probe_connection=dict(existing_observer_instances=1, budget_probe_instances=1,
                same_original_windows_factory=True, original_sample_CPU_RAM_values_retained=True,
                original_cold8_warning75_schedule_retained=True, original_close_and_summary_retained=True,
                second_sampler_thread_or_process=False, additional_PDH_query=False,
                original_K32_decisions_replaced=False, instance_binding_observed=True,
                runtime_product_connection_qualified=False, PC_freeze_resolved=False,
                original_probe_sample_AST_projection=dict(original_sample_AST_restored_exactly=True,
                    original_native_collect_value_PID_status_close_and_final_budget_checks_retained=True,
                    added_cost_sites=4, additional_clock_reads_only=True, extra_CPU_RAM_query_sampler_or_thread=False,
                    original_maximum_sample_seconds=.05, original_maximum_total_seconds=2.0,
                    OS_call_hard_preemption_guaranteed=False)),
            probes=[dict(query_remaining=False, cleanup_confirmed=True,
                cost_checked_before_formatted_reads=True,
                original_seven_counter_PID_status_and_final_cost_checks_retained=True,
                original_CPU_RAM_guards_replaced=False, runtime_connection_qualified=False,
                PC_freeze_resolved=False, early_budget_checks=8, early_budget_stops=0)]))

    def test_only_reviewed125_second_attempt(self):
        self.assertEqual(r.validate_data(self.data(), self.step())["run"], 2)

    def test_later_case_first_attempt_no_automatic_retry(self):
        self.assertEqual(r.validate_data(self.data(126), self.step(126))["run"], 1)

    def test_bad_index_and_types(self):
        for index in (True, 124, 250, 125.0):
            with self.subTest(index=index), self.assertRaises(ValueError):
                r.attempt(index)

    def test_wrong_cursor_run_and_extra_keys(self):
        for key, value in (("run", 1), ("run", 3), ("run", True), ("index", 126),
                           ("before", 119), ("extra", False)):
            row = self.data(); row[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                r.validate_data(row, self.step())

    def test_failure_or_qualification_pin_drift(self):
        for key in ("failed_runtime_pin", "base_step_pin", "budget_qualification_pin",
                    "observer_qualification_pin"):
            row = self.data(); row[key] = dict(row[key], sha256="1"*64)
            with self.subTest(key=key), self.assertRaises(ValueError):
                r.validate_data(row, self.step())
        row = self.data(); row["failed_runtime_pin"] = None
        with self.assertRaises(ValueError):
            r.validate_data(row, self.step())

    def test_metadata_path_and_code_inventory_cannot_shrink(self):
        row = self.data(); row["metadata_connection_pin"]["path"] = r.metadata.data_path(126)
        with self.assertRaises(ValueError): r.validate_data(row, self.step())
        row = self.data(); row["connection_code_pins"].pop()
        with self.assertRaises(ValueError): r.validate_data(row, self.step())

    def test_failure_requires_prebody_cleanup(self):
        self.assertTrue(r.review_failure(self.failure()))
        for key, value in (("product_body_observed", True), ("worker_created", True),
                           ("cleanup_confirmed", False), ("accepted_count_delta", 1),
                           ("source_freeze", ["x"]), ("passed_test_names", ["x"])):
            row = self.failure(); row[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                r.review_failure(row)

    def test_failure_requires_closed_no_bytes_no_handle_leaks(self):
        for key, value in (("frame_state", "COMMITTED"), ("actual_byte_boundaries", ["x"])):
            row = self.failure(); row["source_frame"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): r.review_failure(row)
        row = self.failure(); row["source_frame"]["handles"]["input_lock_handles_remaining"] = 1
        with self.assertRaises(ValueError): r.review_failure(row)

    def test_authorized_root_cannot_select_failed125_or_later_retry(self):
        self.assertTrue(accept.root_path(self.step()).endswith("run002.v1.json"))
        self.assertTrue(accept.root_path(self.step(126)).endswith("run001.v1.json"))

    def test_wrong_root_rejected_before_source_read(self):
        with patch.object(r.base, "CONFIG", self.step()):
            with self.assertRaisesRegex(ValueError, "EXACT_REVIEWED_ROOT"):
                accept.run(dict(path="implementation/p09/evidence/p09-361-case125-current-runtime-run001.v1.json"))

    def test_actual_factory_predicates_positive_and_missing_checks_rejected(self):
        self.assertTrue(accept.actual_budget_binding(self.binding()))
        for value in (0, True, -1):
            row = self.binding(); row["serial_CPU_attribution"]["probes"][0]["early_budget_checks"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                accept.actual_budget_binding(row)

    def test_actual_binding_cannot_use_extra_sampler_or_hide_query(self):
        for key, value in (("existing_observer_instances", 2), ("budget_probe_instances", 0),
            ("instance_binding_observed", False), ("additional_PDH_query", True),
            ("second_sampler_thread_or_process", True), ("original_K32_decisions_replaced", True)):
            row = self.binding(); row["serial_CPU_attribution"]["early_budget_probe_connection"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): accept.actual_budget_binding(row)
        row = self.binding(); row["serial_CPU_attribution"]["probes"][0]["query_remaining"] = True
        with self.assertRaises(ValueError): accept.actual_budget_binding(row)

    def test_original_budget_and_ast_flags_cannot_weaken(self):
        for key, value in (("original_maximum_total_seconds", 3.0), ("original_maximum_total_seconds", 2),
            ("original_maximum_sample_seconds", .1), ("original_sample_AST_restored_exactly", False),
            ("extra_CPU_RAM_query_sampler_or_thread", True)):
            row = self.binding()
            row["serial_CPU_attribution"]["early_budget_probe_connection"]["original_probe_sample_AST_projection"][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                accept.actual_budget_binding(row)

    def test_prepare_counted_root_projection_retained(self):
        raw = b"def prepare(q, root_pin):\n step=r.CONFIG\n require(root_pin['path']==f'implementation/p09/evidence/p09-361-case{step.index}-current-runtime-run001.v1.json','ROOT')\n return 'whole-oracle'\n"
        self.assertTrue(callable(accept.prepare_projection(raw)))
        with self.assertRaises(ValueError):
            accept.prepare_projection(raw.replace(b"run001", b"run003"))

    def test_template_and_full_preflight_preview_no_runtime(self):
        if r.base.CONFIG is None: r.base.configure(125)
        old = r.base.stable.stable.prior.build.pressure.PreSaturationReadCheckpoint
        engine, proof = r.template()
        self.assertIs(r.base.stable.stable.prior.build.pressure.PreSaturationReadCheckpoint, old)
        self.assertTrue(proof["original_engine_bytecode_unchanged"])
        self.assertEqual(engine.run_owned.__globals__["SELF"], r.SELF)
        self.assertIs(engine.run_owned.__globals__["build"].pressure.PreSaturationReadCheckpoint,
                      r.metadata.MetadataCheckpoint)
        pin = r.METADATA_PIN
        with (r.c.ROOT / pin["path"]).open("rb") as stream: raw = stream.read(pin["bytes"] + 1)
        self.assertTrue(callable(r.preflight_projection(raw)))
        with self.assertRaises(ValueError): r.preflight_projection(raw + b"\n")


if __name__ == "__main__": unittest.main()
