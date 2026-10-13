"""Synthetic contracts for P340 case111 source-only closure; no file reads."""
import copy
import ast
import sys
import io
import threading
import types
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import close_p340_post_product_source_frame as p


def fixture():
    required = {f"src/{i}.rs": dict(path=f"src/{i}.rs", bytes=3, sha256="a" * 64)
                for i in range(1662)}
    required.pop("src/0.rs")
    required["bin/runner.exe"] = dict(path="bin/runner.exe", bytes=14216704, sha256="b" * 64)
    required["src/1.rs"]["bytes"] = 107079471
    total = sum(row["bytes"] for row in required.values())
    diag = dict(read_passes=1662, bytes_read=total,
                read_rates_by_kind=dict(binary=1048576, other=2097152),
                original_owned_read_operations_preserved=True, extra_sampler_or_native_query_started=False)
    handles = dict(input_lock_handles_opened=1970, input_lock_handles_closed=1970,
                   input_lock_handles_remaining=0, active_reader_bindings=0, active_byte_streams=0,
                   input_lock_cleanup_confirmed=True, handle_close_failed_attempts=0,
                   byte_stream_identity_checks=3324, separate_pathname_reopens=0,
                   borrowed_byte_streams=dict(duplicate_handles_opened=3324, duplicate_handles_closed=3324,
                       shared_offset_resets=3324, duplicate_handles_remaining=0,
                       duplicate_close_failed_attempts=0, active_borrow_binding=False,
                       byte_stream_pathname_reopens=0, original_pre_read_stream_identity_check_retained=True,
                       original_held_handles_closed_by_borrower=False),
                   maximum_lock_seconds=600,
                   native_open_pacing=dict(maximum_opens_per_second=20),
                   file_write_or_delete_operation_executed=False,
                   native_open_backpressure=dict(original_hard_resource_decisions_unmodified=True,
                       original_IO_deadline_unmodified=True, original_read_checks_skipped=False),
                   acquisition_phase_pressure=dict(
                       acquisition_maximum_reservations_per_second=5,
                       original_global_and_byte_reservation_ceiling_per_second=20,
                       acquisition_used=True, acquisition_complete=True, acquisition_reservations=1970,
                       restored_original_rate=20, same_original_pacer=True,
                       clock_and_sleeper_and_checkpoint_retained=True,
                       clock_previous_credit_or_reservation_counter_reset=False,
                       extra_sampler_or_thread_started=False,
                       original_CPU_RAM600_and_all_byte_identity_guards_preserved=True,
                       cleanup_callback_wrapped=False,
                       nominal_acquisition_density_reduction_percent=100.0 * (1.0 - 5 / 14),
                       CPU_or_PC_freeze_improvement_established=False))
    frame = dict(frame_state="COMMITTED", registered_live_frame=False, input_count=1662,
                 input_bytes=total, original_owned_cleanup_confirmed_before_release=True,
                 original_two_actual_per_case_byte_reads_retained=True,
                 serialized_pin_reused_as_live_handle=False, input_exclusions_added=False,
                 security_sandbox_claimed=False, handles=handles,
                 actual_byte_boundaries=[dict(role=role, actual_byte_pins=list(required.values()),
                     reader_diagnostics=copy.deepcopy(diag)) for role in ("before", "after")],
                 held_identity_after_owned_cleanup=dict(held_identity_checks_complete=True,
                     separate_pathname_reopens=0, regular_file_count=1662, directory_count=308))
    return frame, required


class SourceFrameTests(unittest.TestCase):
    def setUp(self): self.frame, self.required = fixture()
    def reject(self):
        with self.assertRaises((ValueError, KeyError, TypeError)):
            p.validate_frame(self.frame, self.required)
    def test_source_closer_inherits_one_way_native_saturation_guard(self):
        source = Path(__file__).resolve().parents[1] / "close_p340_post_product_source_frame.py"
        tree = ast.parse(source.read_text(encoding="utf-8"))
        wrapper = next(node for node in ast.walk(tree)
                       if isinstance(node, ast.ClassDef) and node.name == "LowerAcquisitionInputLocks")
        self.assertEqual(len(wrapper.bases), 1)
        self.assertIsInstance(wrapper.bases[0], ast.Attribute)
        self.assertEqual(wrapper.bases[0].attr, "AcquisitionInputLocks")
        self.assertIsInstance(wrapper.bases[0].value, ast.Name)
        self.assertEqual(wrapper.bases[0].value.id, "p340")
        self.assertEqual([node.name for node in wrapper.body if isinstance(node, ast.FunctionDef)], ["summary", "take"])
        take=next(node for node in wrapper.body if isinstance(node,ast.FunctionDef) and node.name=="take")
        call=take.body[0].value
        self.assertIsInstance(call.func,ast.Attribute);self.assertEqual(call.func.attr,"take")
        self.assertEqual(call.func.value.func.id,"super")
        self.assertIsInstance(take.body[-1],ast.Return);self.assertEqual(take.body[-1].value.id,"result")
    def test_pacing_reduction_uses_original_candidate_rate_not_global_ceiling(self):
        row = p.acquisition_pacing(14)
        self.assertEqual(row["unchanged_global_and_byte_ceiling_per_second"], 20)
        self.assertAlmostEqual(row["nominal_density_reduction_percent"], 100 * (1 - 5 / 14))
        self.assertFalse(row["measured_CPU_or_freeze_improvement_claimed"])
    def test_document_pacing_guard_rejects_global_ceiling_comparison(self):
        doc = {"source_acquisition_pacing": p.acquisition_pacing(14)}
        self.assertTrue(p.validate_acquisition_pacing(doc))
        doc["source_acquisition_pacing"] = dict(doc["source_acquisition_pacing"],
            nominal_density_reduction_percent=75.0)
        with self.assertRaises(ValueError):
            p.validate_acquisition_pacing(doc)
    def test_exact_two_actual_full_boundaries(self): p.validate_frame(self.frame, self.required)
    def test_cached_or_reduced_input_rejected(self):
        self.frame["actual_byte_boundaries"][1]["reader_diagnostics"]["read_passes"] = 0; self.reject()
    def test_partial_pin_set_rejected(self):
        self.frame["actual_byte_boundaries"][0]["actual_byte_pins"].pop(); self.reject()
    def test_open_lock_rejected(self):
        self.frame["handles"]["input_lock_handles_remaining"] = 1; self.reject()
    def test_unclosed_duplicate_rejected(self):
        self.frame["handles"]["borrowed_byte_streams"]["duplicate_handles_remaining"] = 1; self.reject()
    def test_gate_frame_not_committed_rejected(self):
        self.frame["frame_state"] = "CLOSED"; self.reject()
    def test_lower_acquisition_rate_required(self):
        self.frame["handles"]["acquisition_phase_pressure"]["acquisition_maximum_reservations_per_second"] = 14
        self.reject()
    def test_source_budget_estimate_fits_with_explicit_unallocated_margin(self):
        budget = p.source_budget(self.required)
        self.assertEqual(budget["selected_acquisition_rate_per_second"], 5)
        self.assertEqual(budget["acquisition_reservations"], 1970)
        self.assertLess(budget["predicted_combined_seconds"], 600)
        self.assertTrue(budget["estimate_not_completion_guarantee"])
        self.assertFalse(budget["CPU_or_PC_freeze_improvement_claimed"])
    def test_source_budget_rejects_over_deadline_estimate(self):
        oversized = copy.deepcopy(self.required)
        oversized["src/1.rs"]["bytes"] = 10**12
        with self.assertRaises(ValueError):
            p.source_budget(oversized)
    def test_original_hard_open_ceiling_required(self):
        self.frame["handles"]["acquisition_phase_pressure"]["original_global_and_byte_reservation_ceiling_per_second"] = 7
        self.reject()
    def test_scope_scaled_native_and_path_guards(self):
        total = 1970
        op = dict(started=total, completed=total, failed=0, measured=total, unknown=0,
                  elapsed_total_seconds=1.0, elapsed_max_seconds=0.1)
        diagnostic = dict(take_attempts=total, take_completed=total, take_failed=0, active_take=False,
            input_kinds=dict(directory=dict(started=308, completed=308, failed=0),
                             regular=dict(started=1662, completed=1662, failed=0)),
            last_attempt=dict(ordinal=total, kind="regular",
                              last_native_operation="inspect_metadata", completed=True),
            operations=dict(open_with_pacing=copy.deepcopy(op), inspect_metadata=copy.deepcopy(op)),
            bounded_aggregate_not_per_input_trace=True,
            open_elapsed_includes_original_pacer_and_pressure_wait=True,
            inspect_elapsed_covers_original_metadata_bundle=True,
            original_native_methods_and_arguments_retained=True,
            original_take_guard_and_identity_checks_retained=True,
            original_pacer_clock_sleeper_checkpoint_and_credit_retained=True,
            diagnostic_clock_failures_do_not_mask_original_return_or_exception=True,
            cleanup_callback_or_close_wrapped=False, extra_sampler_or_thread_or_native_query_started=False,
            path_or_handle_or_exception_values_recorded=False,
            CPU_cause_or_PC_freeze_improvement_claimed=False)
        p.validate_acquisition(dict(native_acquisition_diagnostics=diagnostic), 1662, 308)
        path = dict(native_metadata_queries_attempted=1662, fresh_held_metadata_queries=1662,
            original_path_guard_predicates=4986, original_reader_root_restored=True,
            active_path_guard_adapter=False, pathname_metadata_probes=0,
            original_stream_identity_check_retained=True, metadata_reused_between_source_requests=False,
            added_native_queries_recorded_separately_from_original_lock_checks=True,
            kernel_call_reduction_or_CPU_freeze_improvement_claimed=False)
        p.validate_path_guard([path, copy.deepcopy(path)], 1662)
        with self.assertRaises(ValueError):
            p.validate_acquisition(dict(native_acquisition_diagnostics=diagnostic), 1658, 308)


class FrozenMutablePreflightTests(unittest.TestCase):
    def setUp(self):
        self.original = {row["path"]: copy.deepcopy(row) for row in p.FROZEN_MUTABLE_PINS}
        self.actual = copy.deepcopy(self.original)
        self.names = []
        owner = self
        class Reader:
            def pin(self, name):
                owner.names.append(name)
                return copy.deepcopy(owner.actual[name])
        self.reader = Reader()

    def test_exact_original_reads_do_not_qualify_source_or_modify_pins(self):
        before = copy.deepcopy(self.original)
        row = p.frozen_mutable_preflight(self.reader, self.original)
        self.assertTrue(row["frozen_inputs_match"])
        self.assertEqual(self.names, list(self.original))
        self.assertEqual(self.original, before)
        self.assertFalse(row["full_source_qualification"])
        self.assertFalse(row["native_acquisition_started"])

    def test_changed_product_code_is_detected_before_native_frame(self):
        name = p.FROZEN_MUTABLE_PINS[0]["path"]
        self.actual[name]["bytes"] += 38
        row = p.frozen_mutable_preflight(self.reader, self.original)
        self.assertFalse(row["frozen_inputs_match"])
        self.assertEqual(row["mismatches"], [dict(expected=self.original[name], actual=self.actual[name])])
        self.assertTrue(p.validate_drift_preflight(dict(frozen_mutable_input_preflight=row)))

    def test_same_size_hash_drift_and_forged_acceptance_are_rejected(self):
        name = p.FROZEN_MUTABLE_PINS[1]["path"]
        self.actual[name]["sha256"] = "f" * 64
        row = p.frozen_mutable_preflight(self.reader, self.original)
        self.assertTrue(p.validate_drift_preflight(dict(frozen_mutable_input_preflight=row)))
        row["frozen_inputs_match"] = True
        with self.assertRaises(ValueError):
            p.validate_drift_preflight(dict(frozen_mutable_input_preflight=row))

    def test_changed_expected_pin_cannot_be_rebased_to_current_input(self):
        self.original[p.FROZEN_MUTABLE_PINS[0]["path"]]["bytes"] += 38
        with self.assertRaises(ValueError):
            p.frozen_mutable_preflight(self.reader, self.original)
        self.assertEqual(self.names, [])

    def test_archive_path_cannot_replace_original_path(self):
        name = p.FROZEN_MUTABLE_PINS[1]["path"]
        self.actual[name]["path"] = "implementation/p09/evidence/p361-v24-candidate-code/" + name
        with self.assertRaises(ValueError):
            p.frozen_mutable_preflight(self.reader, self.original)

    def test_missing_frozen_input_is_rejected_without_any_reads(self):
        self.original.pop(p.FROZEN_MUTABLE_PINS[2]["path"])
        with self.assertRaises(ValueError):
            p.frozen_mutable_preflight(self.reader, self.original)
        self.assertEqual(self.names, [])


def archived_fixture():
    original = {f"src/{i}.rs": dict(path=f"src/{i}.rs", bytes=3, sha256="a" * 64)
                for i in range(1655)}
    original.update({row["path"]: copy.deepcopy(row) for row in p.FROZEN_MUTABLE_PINS})
    original.pop("src/0.rs")
    original["bin/runner.exe"] = dict(path="bin/runner.exe", bytes=14216704, sha256="b" * 64)
    original["src/1.rs"]["bytes"] = 106400000
    extras = {name: dict(path=name, bytes=100, sha256="c" * 64) for name in p.EXTRAS}
    observed = {row["path"]: dict(row, bytes=row["bytes"] + 38, sha256="d" * 64)
                for row in p.FROZEN_MUTABLE_PINS}
    required = p.archived_scope(original, extras, observed)
    frame, _ = fixture()
    n = len(required)
    directories = p.directory_count(required)
    total = sum(row["bytes"] for row in required.values())
    frame.update(input_count=n, input_bytes=total)
    frame["held_identity_after_owned_cleanup"]["regular_file_count"] = n
    frame["held_identity_after_owned_cleanup"]["directory_count"] = directories
    h = frame["handles"]
    h.update(input_lock_handles_opened=n + directories, input_lock_handles_closed=n + directories,
             byte_stream_identity_checks=2 * n)
    h["acquisition_phase_pressure"]["acquisition_reservations"] = n + directories
    h["acquisition_phase_pressure"]["acquisition_maximum_reservations_per_second"] = p.ACQUISITION_RATE
    h["acquisition_phase_pressure"]["nominal_acquisition_density_reduction_percent"] = 100.0 * (1.0 - p.ACQUISITION_RATE / p.ORIGINAL_OPEN_CEILING)
    for key in ("duplicate_handles_opened", "duplicate_handles_closed", "shared_offset_resets"):
        h["borrowed_byte_streams"][key] = 2 * n
    for boundary in frame["actual_byte_boundaries"]:
        boundary["actual_byte_pins"] = copy.deepcopy(list(required.values()))
        boundary["reader_diagnostics"].update(read_passes=n, bytes_read=total)
    op = dict(started=n + directories, completed=n + directories, failed=0,
              measured=n + directories, unknown=0, elapsed_total_seconds=1.0, elapsed_max_seconds=0.1)
    h["native_acquisition_diagnostics"] = dict(take_attempts=n + directories,
        take_completed=n + directories, take_failed=0, active_take=False,
        input_kinds=dict(directory=dict(started=directories, completed=directories, failed=0),
                         regular=dict(started=n, completed=n, failed=0)),
        last_attempt=dict(ordinal=n + directories, kind="regular", last_native_operation="inspect_metadata", completed=True),
        operations=dict(open_with_pacing=copy.deepcopy(op), inspect_metadata=copy.deepcopy(op)),
        bounded_aggregate_not_per_input_trace=True, open_elapsed_includes_original_pacer_and_pressure_wait=True,
        inspect_elapsed_covers_original_metadata_bundle=True, original_native_methods_and_arguments_retained=True,
        original_take_guard_and_identity_checks_retained=True, original_pacer_clock_sleeper_checkpoint_and_credit_retained=True,
        diagnostic_clock_failures_do_not_mask_original_return_or_exception=True,
        cleanup_callback_or_close_wrapped=False, extra_sampler_or_thread_or_native_query_started=False,
        path_or_handle_or_exception_values_recorded=False, CPU_cause_or_PC_freeze_improvement_claimed=False)
    return original, extras, observed, required, frame


class ArchivedSourceProjectionTests(unittest.TestCase):
    def setUp(self):
        self.original, self.extras, self.observed, self.required, self.frame = archived_fixture()
        self.doc = dict(schema_version=p.ARCHIVED_SCHEMA, source_kind=p.ARCHIVED_KIND,
            source_archive_bindings=copy.deepcopy(list(p.ARCHIVE_BINDINGS)),
            current_observed_source_pins=copy.deepcopy(list(self.observed.values())),
            current_product_source_qualified=False, original_runtime_file_identities_reused=False)

    def rebuild(self):
        return p.required_from_document(self.doc, dict(source_freeze=list(self.original.values())),
                                        self.extras, self.observed)

    def test_full_original_bytes_and_current_paths_both_retained_without_mutation(self):
        before = copy.deepcopy((self.original, self.observed, self.extras))
        self.assertEqual(self.rebuild(), self.required)
        self.assertEqual(len(self.required), 1665)
        for row in p.ARCHIVE_BINDINGS:
            self.assertEqual(self.required[row["archive_pin"]["path"]], row["archive_pin"])
            self.assertEqual(self.required[row["logical_pin"]["path"]], self.observed[row["logical_pin"]["path"]])
        self.assertEqual((self.original, self.observed, self.extras), before)

    def test_missing_logical_original_is_not_an_exclusion(self):
        self.original.pop(p.FROZEN_MUTABLE_PINS[0]["path"])
        with self.assertRaises(ValueError):self.rebuild()

    def test_original_sha_cannot_be_rebased_to_current_source(self):
        name=p.FROZEN_MUTABLE_PINS[0]["path"]
        self.original[name]=self.observed[name]
        with self.assertRaises(ValueError):self.rebuild()

    def test_forged_archive_mapping_or_digest_rejected(self):
        self.doc["source_archive_bindings"][0]["archive_pin"]["sha256"]="f"*64
        with self.assertRaises(ValueError):self.rebuild()

    def test_current_observation_cannot_be_removed_or_replaced(self):
        self.doc["current_observed_source_pins"].pop()
        with self.assertRaises(ValueError):self.rebuild()

    def test_archived_source_cannot_claim_current_product_or_old_handle_identity(self):
        for key in ("current_product_source_qualified", "original_runtime_file_identities_reused"):
            with self.subTest(key=key):
                self.doc[key]=True
                with self.assertRaises(ValueError):self.rebuild()
                self.doc[key]=False

    def test_two_full_actual_boundaries_and_all_physical_locks_required(self):
        p.validate_frame(self.frame,self.required,archived=True)
        p.validate_acquisition(self.frame["handles"],1665,p.directory_count(self.required))
        self.frame["actual_byte_boundaries"][1]["actual_byte_pins"].pop()
        with self.assertRaises(ValueError):p.validate_frame(self.frame,self.required,archived=True)

    def test_legacy_frame_profile_cannot_accept_new_projection_or_unclosed_handles(self):
        with self.assertRaises(ValueError):p.validate_frame(self.frame,self.required)
        self.frame["handles"]["input_lock_handles_remaining"]=1
        with self.assertRaises(ValueError):p.validate_frame(self.frame,self.required,archived=True)

    def test_archived_budget_counts_all_physical_inputs_and_ancestors(self):
        budget=p.source_budget(self.required,archived=True)
        self.assertEqual(budget["acquisition_reservations"],1665+p.directory_count(self.required))
        self.assertLess(budget["predicted_combined_seconds"],600)
        self.assertEqual(budget["unchanged_lock_deadline_seconds"],600)

    def test_byte_pass_native_reservations_are_serial_costs_not_free_overlap(self):
        budget=p.source_budget(self.required,archived=True)
        self.assertEqual(budget["two_actual_byte_pass_native_reservations"],3330)
        self.assertEqual(budget["two_actual_byte_pass_native_pacing_seconds"],166.5)
        self.assertEqual(budget["unchanged_byte_reservation_ceiling_per_second"],20)
        self.assertFalse(budget["byte_and_native_pacing_costs_assumed_overlapped"])
        self.assertFalse(budget["idle_pacer_credit_assumed"])
        self.assertAlmostEqual(budget["predicted_combined_seconds"],
            budget["native_acquisition_seconds"]+budget["two_actual_byte_pass_nominal_seconds"]+
            166.5+budget["nominal_early_yield_allowance_seconds"]+budget["unallocated_margin_seconds"])

    def test_previous_five_per_second_is_rejected_before_native_acquisition(self):
        with self.assertRaisesRegex(ValueError,"LOW_RATE_MUST_FIT_UNCHANGED_600_SECOND_LOCK"):
            p.source_budget(self.required,archived=True,acquisition_rate=5)
        for rate in (0,15,True):
            with self.subTest(rate=rate),self.assertRaises(ValueError):
                p.source_budget(self.required,archived=True,acquisition_rate=rate)
        row=p.acquisition_pacing(14,archived=True)
        self.assertEqual(row["selected_reservations_per_second"],9)
        self.assertEqual(row["unchanged_global_and_byte_ceiling_per_second"],20)

    def test_physical_archive_is_read_and_verified_not_a_serialized_pin_alias(self):
        owner=self
        class Reader:
            def pin(self,name):return copy.deepcopy(owner.required[name])
        required,observed=p.archived_preflight(Reader(),self.original,self.extras)
        self.assertEqual(required,self.required);self.assertEqual(observed,self.observed)
        name=p.ARCHIVE_BINDINGS[0]["archive_pin"]["path"]
        self.required[name]=dict(self.required[name],sha256="f"*64)
        with self.assertRaisesRegex(ValueError,"ARCHIVED_EXACT_PHYSICAL_BYTES"):
            p.archived_preflight(Reader(),self.original,self.extras)


class SourceProgressTests(unittest.TestCase):
    def setUp(self):
        self.now=100.0;self.stream=io.StringIO()
        self.owner=types.SimpleNamespace(lock=threading.Lock(),samples=[dict(
            system_cpu_percent=20,parent_cpu_machine_percent=1,available_ram_percent=35,
            own_private_bytes=1000,audited_logical_read_bytes=123)])
        self.progress=p.SourceProgress(self.owner,self.stream,lambda:self.now)

    def test_progress_reuses_sample_and_is_bounded_to_45_seconds(self):
        before=copy.deepcopy(self.owner.samples)
        self.progress.emit("source_frame_acquire",1)
        for _ in range(100):self.progress.emit("source_frame_acquire",2)
        self.assertEqual(len(self.stream.getvalue().splitlines()),1)
        self.assertEqual(self.owner.samples,before)
        self.now+=45;self.progress.emit("source_frame_acquire",3)
        self.assertEqual(self.progress.summary()["emitted_rows"],2)
        self.assertFalse(self.progress.summary()["new_native_query_or_sampler_or_thread_started"])

    def test_progress_output_failure_does_not_raise_into_native_return_or_cleanup(self):
        class Stream:
            def write(self,_):raise OSError("DIAGNOSTIC_STREAM_FAILURE")
        self.progress.stream=Stream();self.progress.emit("source_frame_acquire",1)
        self.assertEqual(self.progress.output_errors,1)
        self.assertFalse(self.progress.summary()["original_guards_or_deadlines_or_pacer_credit_modified"])

    def test_progress_without_sample_does_not_invent_resource_values(self):
        self.owner.samples=[];self.progress.emit("metadata_hash",10,force=True)
        import json
        row=json.loads(self.stream.getvalue())
        self.assertTrue(all(value is None for value in row["existing_watcher_sample"].values()))
        self.assertFalse(row["progress_is_acceptance_evidence"])


if __name__ == "__main__": unittest.main()
