"""Synthetic fail-closed tests; no receipt reads, runtime, or queue mutation."""
from __future__ import annotations

import copy
import sys
import unittest
from types import SimpleNamespace
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(TOOLS / "tests"))
import accept_p340_case111_compound as compound
import close_p340_post_product_source_frame as source
import review_p340_post_product_stop as review
import test_close_p340_post_product_source_frame as source_tests


def fixture():
    original = {}
    for i in range(1658):
        name = "bin/runner.exe" if i == 0 else f"src/{i}.rs"
        size = 14216704 if i == 0 else (107079471 if i == 1 else 3)
        original[name] = dict(path=name, bytes=size, sha256=f"{i:064x}")
    extras = {name: dict(path=name, bytes=i + 1, sha256=f"{1662+i:064x}")
              for i, name in enumerate(source.EXTRAS)}
    required = {**original, **extras}
    frame, _ = source_tests.fixture()
    total = sum(row["bytes"] for row in required.values())
    frame["input_bytes"] = total
    for boundary in frame["actual_byte_boundaries"]:
        boundary["actual_byte_pins"] = list(required.values())
        boundary["reader_diagnostics"]["bytes_read"] = total
    source_doc = dict(schema_version=source.SCHEMA, state=source.PASS,
        original_root_pin=source.ROOT_PIN, original_parent_pin=source.BODY_PIN,
        review=None, original_executed_source_pins=list(original.values()),
        extra_controller_pins=list(extras.values()),
        source_kind="INDEPENDENT_CURRENT_SOURCE_AFTER_COMPLETED_PRODUCT_CHILD_NOT_ORIGINAL_PARTIAL_AFTER",
        source_frame=frame,
        preparation_IO=dict(finished=True, bound_inputs=[], final_fresh_hashes=[]),
        source_closing_contract_tests_passed=source.CONTRACT_COUNT,
        source_budget=source.source_budget(required),
        source_acquisition_pacing=source.acquisition_pacing(14),
        resource_stop_reason=None, resource_watcher_cleanup_confirmed=True,
        independent_source_frame_attempted=True, independent_source_frame_qualified=True,
        actual_product_child_executed=False, runtime_acceptance_changed=False,
        accepted_count_delta=0, P09_gate="OPEN", A12_gate="OPEN", A13_gate="OPEN",
        product_complete=False, PC_freeze_resolved=False)
    source_doc["review"] = None
    plan = dict(runtime_source_qualified_individual_cases=104, next_runtime_index=111)
    source_pin = dict(path=source.SOURCE_DIR + "/p340-post-stop-source-run088.v1.json",
                      bytes=123, sha256="a" * 64)
    product_frame = dict(frame_state="CLOSED", registered_live_frame=False,
        input_count=len(original), input_bytes=sum(row["bytes"] for row in original.values()),
        actual_byte_boundaries=[dict(role="before", actual_byte_pins=list(original.values()))])
    product_root = dict(schema_version="hwpx-agent.p09-preserved106-fixed-runtime-queue/v24",
        state="FAILED_NOT_ACCEPTED", error_code=review.STOP, resource_stop_reason=review.STOP,
        selected_test_index=111, selected_test_name=review.TEST_NAME,
        binding={"fixture": "p340"},
        current95_code_pins=[dict(path="src/current.py", bytes=1, sha256="c" * 64)],
        prior_runtime_plan=copy.deepcopy(plan), source_attempted=True, source_qualified=False,
        actual_product_child_executed=False, source_frame=None,
        terminal_parent_failure_sidecar_pin=source.BODY_PIN,
        case_receipt_path=review.CASE_RECEIPT, terminal_source_frame=product_frame,
        P09_gate="OPEN", A12_gate="OPEN", A13_gate="OPEN",
        product_complete=False, PC_freeze_resolved=False)
    product_body = dict(schema_version="hwpx-agent.p09-locked-r07-parent-candidate/v1",
        state="STOPPED_NOT_ACCEPTED", operation_phase="final_source_freeze",
        resource_stop_reason=review.STOP, stop_reason=review.STOP,
        actual_product_child_executed=True, exit_code=0,
        selected_test_names=[review.TEST_NAME], passed_test_names=[review.TEST_NAME],
        terminal_summary=dict(passed=1, failed=0, ignored=0, measured=0, filtered_out=248),
        test_arguments=[review.TEST_NAME, "--exact", "--test-threads=1",
                        "--format=pretty", "--color=never"],
        binding={"fixture": "p340"}, task="p204-r07-case-111-tests",
        minimal_worker_task="p204-r07-case-111-tests",
        minimal_owned_worker_path="tools/p09/minimal_r07_worker.py",
        capture=dict(error_code=None, per_stream_limit_bytes=32768,
                     complete_streams=True, raw_logs_saved=False),
        writer_authorized=True, owned_limits_verified=True,
        actual_job_membership_checked=True,
        owned_limits_readback=dict(verified=True, cpu_hard_cap_machine_percent=6.25,
            affinity_mask=1, priority_class=16384, active_process_limit=16,
            kill_on_close=True, breakaway_disabled=True),
        job_final=dict(active_processes=0, owned_processes=[]),
        cleanup_confirmed=True, owned_tree_empty=True, worker_created=True, job_assigned=True,
        source_freeze=list(original.values()),
        owned_source_reader_passes=[
            dict(read_passes=1658, bytes_read=product_frame["input_bytes"],
                 original_owned_read_operations_preserved=True,
                 read_rates_by_kind=dict(binary=1048576, other=2097152)),
            dict(read_passes=727, bytes_read=product_frame["input_bytes"] - 1,
                 original_owned_read_operations_preserved=True,
                 read_rates_by_kind=dict(binary=1048576, other=2097152))],
        P09_gate="OPEN", A12_gate="OPEN", A13_gate="OPEN",
        product_complete=False, PC_freeze_resolved=False)
    product_root["terminal_parent_failure_sidecar_pin"] = source.BODY_PIN
    return product_root, product_body, source_doc, source_pin, required, plan


class Case111CompoundTests(unittest.TestCase):
    def setUp(self):
        self.root, self.body, self.source_doc, self.source_pin, self.required, self.plan = fixture()
        self.review_result = review.validate(self.root, self.body, source.BODY_PIN)
        self.source_doc["review"] = self.review_result

    def validate(self):
        return compound.validate(self.root, self.body, source.ROOT_PIN, source.BODY_PIN,
                                 self.source_doc, self.source_pin, self.required, self.plan)

    def reject(self):
        with self.assertRaises((ValueError, KeyError, TypeError)):
            self.validate()

    def test_exact_child_and_full_source_candidate(self):
        row = self.validate()
        self.assertEqual(row["state"], compound.PASS)
        self.assertTrue(row["completed_source_frame_reused"])

    def test_stale_source_closer_contract_count_is_rejected(self):
        self.source_doc["source_closing_contract_tests_passed"] = 20
        self.reject()

    def test_candidate_does_not_advance_or_accept_queue(self):
        row = self.validate()
        self.assertEqual(row["accepted_count_delta"], 0)
        self.assertFalse(row["runtime_acceptance_changed"])
        self.assertFalse(row["queue_cursor_advanced"])
        self.assertFalse(row["live_current_queue_verified_by_this_contract"])
        self.assertFalse(row["receipt_bytes_rebound_by_this_contract"])
        self.assertEqual(row["P09_gate"], "OPEN")

    def test_product_review_is_semantic_only_and_requires_zero_placeholder(self):
        row = compound.review_product_candidate(self.root, self.body,
            source.ROOT_PIN, source.BODY_PIN, compound.EMPTY_RECEIPT_PIN, self.plan)
        self.assertTrue(row["semantic_body_capture_complete"])
        self.assertFalse(row["runtime_acceptance_changed"])
        self.assertFalse(row["queue_cursor_advanced"])
        with self.assertRaises(ValueError):
            compound.review_product_candidate(self.root, self.body,
                source.ROOT_PIN, source.BODY_PIN,
                dict(compound.EMPTY_RECEIPT_PIN, bytes=1), self.plan)

    def test_same_metadata_reader_binds_all_receipts_before_candidate_review(self):
        docs = {
            compound.PRODUCT_ROOT_PATH: self.root,
            compound.PRODUCT_BODY_PATH: self.body,
            self.source_pin["path"]: self.source_doc,
        }
        pins = {
            compound.PRODUCT_ROOT_PATH: source.ROOT_PIN,
            compound.PRODUCT_BODY_PATH: source.BODY_PIN,
            self.source_pin["path"]: self.source_pin,
        }

        class MetadataReader:
            def __init__(inner):
                inner.reader = SimpleNamespace(snapshots={})
                inner.reads = []

            def json(inner, name):
                inner.reads.append(name)
                inner.reader.snapshots[name] = pins[name]
                return docs[name]

            def pin(inner, name):
                inner.reader.snapshots[name] = compound.EMPTY_RECEIPT_PIN
                return compound.EMPTY_RECEIPT_PIN

        reader = MetadataReader()
        row = compound.validate_from_reader(reader, self.source_pin["path"],
                                            self.required, self.plan)
        self.assertEqual(reader.reads, [compound.PRODUCT_ROOT_PATH,
            compound.PRODUCT_BODY_PATH, self.source_pin["path"]])
        self.assertTrue(row["all_receipt_bytes_bound_to_same_reader"])
        self.assertTrue(row["receipt_bytes_rebound_by_this_contract"])
        self.assertFalse(row["final_reader_freshness_completed_by_this_contract"])
        self.assertFalse(row["queue_cursor_advanced"])

    def test_reader_binding_rejects_wrong_source_snapshot(self):
        docs = {
            compound.PRODUCT_ROOT_PATH: self.root,
            compound.PRODUCT_BODY_PATH: self.body,
            self.source_pin["path"]: self.source_doc,
        }

        class MetadataReader:
            def __init__(inner):
                inner.reader = SimpleNamespace(snapshots={})

            def json(inner, name):
                inner.reader.snapshots[name] = dict(self.source_pin, path=name)
                return docs[name]

            def pin(inner, name):
                inner.reader.snapshots[name] = compound.EMPTY_RECEIPT_PIN
                return compound.EMPTY_RECEIPT_PIN

        with self.assertRaises(ValueError):
            compound.validate_from_reader(MetadataReader(), self.source_pin["path"],
                                          self.required, self.plan)

    def test_reader_binding_rejects_replaced_zero_byte_placeholder(self):
        docs = {
            compound.PRODUCT_ROOT_PATH: self.root,
            compound.PRODUCT_BODY_PATH: self.body,
            self.source_pin["path"]: self.source_doc,
        }

        class MetadataReader:
            def __init__(inner):
                inner.reader = SimpleNamespace(snapshots={})

            def json(inner, name):
                inner.reader.snapshots[name] = {
                    compound.PRODUCT_ROOT_PATH: source.ROOT_PIN,
                    compound.PRODUCT_BODY_PATH: source.BODY_PIN,
                    self.source_pin["path"]: self.source_pin,
                }[name]
                return docs[name]

            def pin(inner, name):
                wrong = dict(compound.EMPTY_RECEIPT_PIN, bytes=1, sha256="a" * 64)
                inner.reader.snapshots[name] = wrong
                return wrong

        with self.assertRaises(ValueError):
            compound.validate_from_reader(MetadataReader(), self.source_pin["path"],
                                          self.required, self.plan)

    def test_changed_current_cursor_rejected(self):
        self.plan["next_runtime_index"] = 112
        self.reject()

    def test_changed_or_wrong_product_pins_rejected(self):
        with self.assertRaises(ValueError):
            compound.validate(self.root, self.body, dict(source.ROOT_PIN, bytes=1),
                source.BODY_PIN, self.source_doc, self.source_pin, self.required, self.plan)

    def test_malformed_source_receipt_pin_rejected(self):
        self.source_pin["path"] = source.SOURCE_DIR + "/run087.v1.json"
        self.reject()

    def test_product_sidecar_tamper_rejected(self):
        self.body["terminal_summary"]["passed"] = 0
        self.reject()

    def test_source_stop_not_completion_rejected(self):
        self.source_doc["state"] = "FAILED_NOT_ACCEPTED"
        self.reject()

    def test_partial_source_boundary_rejected(self):
        self.source_doc["source_frame"]["actual_byte_boundaries"].pop()
        self.reject()

    def test_source_pin_substitution_rejected(self):
        row = dict(self.source_doc["original_executed_source_pins"][0], sha256="f" * 64)
        self.source_doc["original_executed_source_pins"][0] = row
        self.reject()


class FailedSourceReceiptTests(unittest.TestCase):
    def setUp(self):
        self.pin=dict(path=source.SOURCE_DIR+"/p340-post-stop-source-run099.v1.json",
                      bytes=321,sha256="b"*64)
        self.doc=dict(schema_version=source.SCHEMA,state="FAILED_NOT_ACCEPTED",
            error_code="STOP_SUSTAINED_SYSTEM_CPU",resource_stop_reason="STOP_SUSTAINED_SYSTEM_CPU",
            failure_diagnostic=dict(stage="source_frame_acquire"),resource_watcher_cleanup_confirmed=True,
            actual_product_child_executed=False,runtime_acceptance_changed=False,accepted_count_delta=0,
            independent_source_frame_qualified=False,P09_gate="OPEN",A12_gate="OPEN",A13_gate="OPEN")
    def attach_latched_breaker_summary(self):
        self.doc["source_frame"] = dict(frame_state="CLOSED",registered_live_frame=False,
            handles=dict(input_lock_handles_remaining=0,input_lock_cleanup_confirmed=True,
                active_reader_bindings=0,active_byte_streams=0,
                one_way_native_saturation_circuit_breaker=dict(one_way_circuit_breaker=True,
                    warning_entries_at_start=0,early_source_warning_entries_at_start=0,saturation_seen=True,
                    opens_resume_after_cooldown=False,
                    original_checkpoint_and_resource_guards_run_before_unlatched_reservations=True,
                    latched_warning_preempts_next_resource_checkpoint=True,
                    native_open_or_identity_checks_skipped_for_success=False,
                    policy_stop_code=compound.CIRCUIT_BREAKER_STOP)))
    def test_resource_stop_is_retained_without_acceptance(self):
        row=compound.validate_failed_source_receipt(self.doc,self.pin)
        self.assertEqual(row["stop_classification"],"RESOURCE_GUARD")
        self.assertFalse(row["queue_cursor_advanced"]);self.assertEqual(row["accepted_count_delta"],0)
    def test_one_way_circuit_breaker_is_retained_without_fabricated_resource_reason(self):
        self.doc["error_code"]=compound.CIRCUIT_BREAKER_STOP
        self.doc["resource_stop_reason"]=None
        self.attach_latched_breaker_summary()
        row=compound.validate_failed_source_receipt(self.doc,self.pin)
        self.assertIsNone(row["resource_stop_reason"])
        self.assertEqual(row["stop_classification"],"POLICY_CIRCUIT_BREAKER")
        self.assertFalse(row["queue_cursor_advanced"]);self.assertEqual(row["accepted_count_delta"],0)
    def test_policy_stop_without_latched_breaker_summary_rejected(self):
        self.doc["error_code"]=compound.CIRCUIT_BREAKER_STOP
        self.doc["resource_stop_reason"]=None
        self.attach_latched_breaker_summary()
        self.doc["source_frame"]["handles"]["one_way_native_saturation_circuit_breaker"]["saturation_seen"]=False
        with self.assertRaisesRegex(ValueError,"FAILED_SOURCE_MUST_REMAIN_UNACCEPTED"):
            compound.validate_failed_source_receipt(self.doc,self.pin)
    def test_policy_stop_with_open_frame_or_live_handles_rejected(self):
        self.doc["error_code"]=compound.CIRCUIT_BREAKER_STOP
        self.doc["resource_stop_reason"]=None
        self.attach_latched_breaker_summary()
        self.doc["source_frame"]["handles"]["input_lock_handles_remaining"]=1
        with self.assertRaisesRegex(ValueError,"FAILED_SOURCE_MUST_REMAIN_UNACCEPTED"):
            compound.validate_failed_source_receipt(self.doc,self.pin)
    def test_policy_stop_code_cannot_be_relabelled_as_resource_reason(self):
        self.doc["error_code"]=compound.CIRCUIT_BREAKER_STOP
        self.doc["resource_stop_reason"]=compound.CIRCUIT_BREAKER_STOP
        with self.assertRaisesRegex(ValueError,"FAILED_SOURCE_MUST_REMAIN_UNACCEPTED"):
            compound.validate_failed_source_receipt(self.doc,self.pin)
    def test_unknown_local_failure_without_resource_reason_rejected(self):
        self.doc["error_code"]="SOME_OTHER_FAILURE";self.doc["resource_stop_reason"]=None
        with self.assertRaisesRegex(ValueError,"FAILED_SOURCE_MUST_REMAIN_UNACCEPTED"):
            compound.validate_failed_source_receipt(self.doc,self.pin)

    def test_exact_frozen_drift_is_retained_without_native_or_acceptance(self):
        actual = copy.deepcopy(list(source.FROZEN_MUTABLE_PINS))
        actual[0]["bytes"] += 38
        class Reader:
            def pin(self, name):return next(pin for pin in actual if pin["path"] == name)
        self.doc.update(error_code=source.DRIFT_ERROR, resource_stop_reason=None,
            failure_diagnostic=dict(stage="frozen_mutable_input_preflight"),
            independent_source_frame_attempted=False,
            frozen_mutable_input_preflight=source.frozen_mutable_preflight(
                Reader(), {pin["path"]: pin for pin in source.FROZEN_MUTABLE_PINS}))
        row = compound.validate_failed_source_receipt(self.doc, self.pin)
        self.assertEqual(row["stop_classification"], "FROZEN_INPUT_DRIFT_BEFORE_NATIVE")
        self.assertFalse(row["queue_cursor_advanced"])
        self.assertEqual(row["accepted_count_delta"], 0)
        self.doc["independent_source_frame_attempted"] = True
        with self.assertRaises(ValueError):
            compound.validate_failed_source_receipt(self.doc, self.pin)


class ExactClosedPhaseFailureTests(unittest.TestCase):
    def setUp(self):
        FailedSourceReceiptTests.setUp(self)
        FailedSourceReceiptTests.attach_latched_breaker_summary(self)
        self.pin=copy.deepcopy(compound.CLOSED_PHASE092_PIN)
        self.doc.update(schema_version=source.ARCHIVED_SCHEMA,error_code="P193_CLOSED_PHASE",
            resource_stop_reason=None,source_closing_contract_tests_passed=44,
            bound_preparation_input_pins=copy.deepcopy(list(compound.CLOSED_PHASE092_CODE)),
            preparation_IO=dict(finished=True))
        self.doc["source_frame"]["actual_byte_boundaries"]=[]
        self.doc["source_frame"]["handles"].update(input_lock_handles_opened=0,
            input_lock_handles_closed=0,byte_stream_identity_checks=0,
            native_open_pacing=dict(open_reservations=0))
    def test_exact_failed_phase_is_preserved_without_acceptance(self):
        row=compound.validate_failed_source_receipt(self.doc,self.pin)
        self.assertEqual(row["stop_classification"],"EXACT_LOCAL_PHASE_BINDING_FAILURE")
        self.assertEqual(row["accepted_count_delta"],0);self.assertFalse(row["queue_cursor_advanced"])
    def test_unknown_pin_code_or_started_native_cannot_reuse_historical_failure(self):
        with self.assertRaises(ValueError):
            compound.validate_failed_source_receipt(self.doc,dict(self.pin,sha256="f"*64))
        self.doc["bound_preparation_input_pins"].pop()
        with self.assertRaises(ValueError):compound.validate_failed_source_receipt(self.doc,self.pin)
        self.doc["bound_preparation_input_pins"]=copy.deepcopy(list(compound.CLOSED_PHASE092_CODE))
        self.doc["source_frame"]["handles"]["input_lock_handles_opened"]=1
        with self.assertRaises(ValueError):compound.validate_failed_source_receipt(self.doc,self.pin)


class OriginalLockDeadlineTests(unittest.TestCase):
    def setUp(self):
        FailedSourceReceiptTests.setUp(self)
        FailedSourceReceiptTests.attach_latched_breaker_summary(self)
        self.doc.update(schema_version=source.ARCHIVED_SCHEMA,error_code="P206_LOCK_DEADLINE_EXCEEDED",
            resource_stop_reason=None,failure_diagnostic=dict(stage="final_fresh_hash"))
        self.doc["source_frame"]["handles"].update(maximum_lock_seconds=600,
            lock_timing_diagnostic=dict(original_lock_limit_seconds=600,
                original_check_invoked_without_replacement=True,original_resource_guard_or_deadline_extended=False,
                first_original_error=dict(original_error_code="P206_LOCK_DEADLINE_EXCEEDED",
                    original_lock_elapsed_seconds=600.02,original_lock_limit_seconds=600)))
    def test_resource_stop_is_retained_without_acceptance(self):
        row=compound.validate_failed_source_receipt(self.doc,self.pin)
        self.assertEqual(row["stop_classification"],"ORIGINAL_LOCK_DEADLINE")
        self.assertEqual(row["accepted_count_delta"],0);self.assertFalse(row["queue_cursor_advanced"])
    def test_deadline_without_original_error_or_with_live_handles_is_rejected(self):
        for field,value in (("input_lock_handles_remaining",1),("active_reader_bindings",1),
                            ("active_byte_streams",1),("maximum_lock_seconds",601),
                            ("lock_timing_diagnostic",{})):
            with self.subTest(field=field):
                doc=copy.deepcopy(self.doc);doc["source_frame"]["handles"][field]=value
                with self.assertRaises(ValueError):compound.validate_failed_source_receipt(doc,self.pin)


class ArchivedCase111CompoundTests(Case111CompoundTests):
    """The same candidate invariants also hold for lossless archived source scope."""
    def setUp(self):
        super().setUp()
        original,extras,observed,required,frame=source_tests.archived_fixture()
        self.required=required
        total=sum(pin["bytes"] for pin in original.values())
        self.body["source_freeze"]=copy.deepcopy(list(original.values()))
        self.body["owned_source_reader_passes"][0]["bytes_read"]=total
        self.body["owned_source_reader_passes"][1]["bytes_read"]=total-1
        before=self.root["terminal_source_frame"]
        before.update(input_bytes=total,input_count=1658)
        before["actual_byte_boundaries"][0]["actual_byte_pins"]=copy.deepcopy(list(original.values()))
        guards=[]
        for _ in range(2):
            guards.append(dict(native_metadata_queries_attempted=1665,fresh_held_metadata_queries=1665,
                original_path_guard_predicates=4995,original_reader_root_restored=True,
                active_path_guard_adapter=False,pathname_metadata_probes=0,
                original_stream_identity_check_retained=True,metadata_reused_between_source_requests=False,
                added_native_queries_recorded_separately_from_original_lock_checks=True,
                kernel_call_reduction_or_CPU_freeze_improvement_claimed=False))
        self.source_doc.update(schema_version=source.ARCHIVED_SCHEMA,source_kind=source.ARCHIVED_KIND,
            source_acquisition_pacing=source.acquisition_pacing(14,archived=True),
            source_archive_bindings=copy.deepcopy(list(source.ARCHIVE_BINDINGS)),
            current_observed_source_pins=copy.deepcopy(list(observed.values())),
            current_product_source_qualified=False,original_runtime_file_identities_reused=False,
            original_executed_source_pins=copy.deepcopy(list(original.values())),
            extra_controller_pins=copy.deepcopy(list(extras.values())),source_frame=frame,
            source_budget=source.source_budget(required,archived=True),
            source_closing_contract_tests_passed=source.ARCHIVED_CONTRACT_COUNT,
            source_path_guard_diagnostics=guards)
        self.source_doc["review"]=review.validate(self.root,self.body,source.BODY_PIN)

    def test_archived_source_cannot_promote_current_product_source(self):
        self.source_doc["current_product_source_qualified"]=True
        self.reject()

    def test_archived_source_cannot_alias_original_runtime_file_identity(self):
        self.source_doc["original_runtime_file_identities_reused"]=True
        self.reject()

    def test_archive_bytes_or_current_observation_drift_rejected(self):
        row=self.source_doc["source_frame"]["actual_byte_boundaries"][0]["actual_byte_pins"][0]
        row["sha256"]="f"*64
        self.reject()

    def test_archived_native_acquisition_or_path_guards_not_optional(self):
        self.source_doc["source_path_guard_diagnostics"][0]["fresh_held_metadata_queries"]-=1
        self.reject()


if __name__ == "__main__":
    unittest.main()
