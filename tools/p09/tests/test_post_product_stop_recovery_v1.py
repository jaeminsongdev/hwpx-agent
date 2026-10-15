"""Synthetic negative controls only; no Native, product, GO or queue mutation."""
import copy
import unittest

MODULE=None


def fixture():
    pins=[dict(path=f"fixtures/public-{i}.bin",bytes=1,sha256="a"*64) for i in range(3056)]
    pins[-1]["bytes"]=228558382-3055
    return dict(state="STOPPED_NOT_ACCEPTED",task="case165-current-r007-tests",selected_test_index=165,
        operation_phase="final_source_freeze",stop_reason="STOP_NATIVE_SOURCE_PRESSURE_NO_COOLING",exit_code=0,
        worker_created=True,job_assigned=True,writer_authorized=True,heavy_work_started=True,
        product_body_observed=True,actual_product_child_executed=True,actual_Cargo_SQL_Hangul_run=False,
        product_complete=False,Native_source_frame_qualified=False,current_generation_runtime_candidate_qualified=False,
        accepted_count_delta=0,separate_queue_epoch_acceptance_required=True,full249_current_qualified=False,
        signed16_current_qualified=False,P09_gate="OPEN",A12_gate="OPEN",A13_gate="OPEN",cleanup_confirmed=True,
        owned_tree_empty=True,selected_test_names=[MODULE.CASE],passed_test_names=[MODULE.CASE],
        terminal_summary=dict(passed=1,failed=0,ignored=0,measured=0,filtered_out=248),
        strict_product_window=dict(maximum_GO_to_complete_capture_seconds=15,actual_GO_writes=1,actual_capture_count=1,
            actual_complete_capture_within_window=True,stopped=False,GO_to_complete_capture_elapsed_seconds=2.44),
        parent_live_raw_access_policy=dict(active_scope=False,all_original_open_function_identities_restored=True),
        source_frame=dict(frame_state="CLOSED",registered_live_frame=False,input_count=3056,input_bytes=228558382,
            serialized_pin_reused_as_live_handle=False,input_exclusions_added=False,
            handles=dict(input_lock_handles_opened=3428,input_lock_handles_closed=3428,input_lock_handles_remaining=0,
                input_lock_cleanup_confirmed=True,active_reader_bindings=0,active_byte_streams=0,
                handle_close_failed_attempts=0,file_write_or_delete_operation_executed=False),
            actual_byte_boundaries=[dict(role="before",actual_byte_pins=pins,
                reader_diagnostics=dict(read_passes=3056,bytes_read=228558382))]))


class Tests(unittest.TestCase):
    def test_exact_closed_failure_is_only_eligible_for_design_not_GO_or_PASS(self):
        row=fixture();before=copy.deepcopy(row);result=MODULE.validate_candidate(row)
        self.assertEqual(row,before);self.assertTrue(result["eligible_for_retry_design"])
        for flag in ("GO_authorized","next_Native_start_authorized","runtime_retry_admission_implemented",
            "queue_advance_authorized","product_result_reusable_as_full_PASS","after_boundary_reconstructed"):
            self.assertIs(result[flag],False)
        self.assertEqual(result["next_physical_run"],8)

    def test_no_accepted_pass_or_unknown_stop_can_be_reclassified(self):
        for key,value in (("state","PASS"),("stop_reason","UNKNOWN_STOP"),("accepted_count_delta",1),
            ("accepted_count_delta",False),("product_complete",True),("Native_source_frame_qualified",True),
            ("current_generation_runtime_candidate_qualified",True),("P09_gate","PASS")):
            row=fixture();row[key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):MODULE.validate_candidate(row)

    def test_other_case_run_or_external_runtime_is_not_authorized(self):
        for key,value in (("task","case165-current-r008-tests"),("selected_test_index",166),
            ("actual_Cargo_SQL_Hangul_run",True),("passed_test_names",["other-case"]),("exit_code",1)):
            row=fixture();row[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):MODULE.validate_candidate(row)

    def test_summary_requires_one_complete_product_not_filtered_or_partial(self):
        for key,value in (("passed",2),("failed",1),("ignored",1),("filtered_out",247),("passed",True)):
            row=fixture();row["terminal_summary"][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):MODULE.validate_candidate(row)

    def test_live_frame_job_or_handles_cannot_be_replayed(self):
        for key,value in (("input_lock_handles_closed",3427),("input_lock_handles_remaining",1),
            ("input_lock_handles_remaining",False),("active_reader_bindings",1),("active_byte_streams",1),
            ("handle_close_failed_attempts",1),("file_write_or_delete_operation_executed",True)):
            row=fixture();row["source_frame"]["handles"][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):MODULE.validate_candidate(row)
        for location,key,value in (("source_frame","registered_live_frame",True),
            ("parent_live_raw_access_policy","active_scope",True),(None,"owned_tree_empty",False)):
            row=fixture();(row if location is None else row[location])[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):MODULE.validate_candidate(row)

    def test_missing_duplicate_or_invented_byte_boundaries_rejected(self):
        for mode in ("missing","second","duplicate_pin","bad_total","bad_digest"):
            row=fixture();boundaries=row["source_frame"]["actual_byte_boundaries"]
            if mode=="missing":boundaries.clear()
            elif mode=="second":boundaries.append(copy.deepcopy(boundaries[0]))
            elif mode=="duplicate_pin":boundaries[0]["actual_byte_pins"][1]=copy.deepcopy(boundaries[0]["actual_byte_pins"][0])
            elif mode=="bad_total":boundaries[0]["actual_byte_pins"][0]["bytes"]+=1
            else:boundaries[0]["actual_byte_pins"][0]["sha256"]="not-a-hash"
            with self.subTest(mode=mode),self.assertRaises(ValueError):MODULE.validate_candidate(row)

    def test_incomplete_or_out_of_window_capture_rejected(self):
        for key,value in (("actual_complete_capture_within_window",False),("actual_GO_writes",2),
            ("GO_to_complete_capture_elapsed_seconds",15.001),("GO_to_complete_capture_elapsed_seconds",float("nan")),
            ("GO_to_complete_capture_elapsed_seconds",True)):
            row=fixture();row["strict_product_window"][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):MODULE.validate_candidate(row)

    def test_user_design_authorization_never_allows_another_candidate(self):
        for response in (None,"",True,"unrelated"):
            with self.subTest(response=response),self.assertRaises(ValueError):MODULE.review(b"{}",response)
        with self.assertRaisesRegex(ValueError,"EXACT_IMMUTABLE_FAILED_CANDIDATE"):
            MODULE.review(b"{}",MODULE.RESPONSE)
