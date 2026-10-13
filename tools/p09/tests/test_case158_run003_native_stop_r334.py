import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import review_case158_run003_native_stop_r334 as m


def fixture():
    handles=dict(input_lock_handles_opened=854,input_lock_handles_closed=854,input_lock_handles_remaining=0,
        input_lock_cleanup_confirmed=True,handle_close_failed_attempts=0,active_reader_bindings=0,
        active_byte_streams=0,byte_stream_identity_checks=0,probe_handles_opened=0,probe_handles_closed=0,
        probe_handles_remaining=0,probe_handle_close_failed_attempts=0,maximum_lock_seconds=600,
        file_write_or_delete_operation_executed=False,input_scope_reduced=False,
        all_acquisition_checkpoint_warning_fail_fast=dict(original_warning_percent=90,warning_stops=1,
            latched=True,acquisition_active=False,original_hard_guards_called_first=True,
            acquisition_cooling_waits_added=0,sampler_thread_or_native_query_added=False))
    return dict(state="DEFERRED_NOT_STARTED",task="case158-current-r003-tests",selected_test_index=158,
        stop_reason="STOP_NATIVE_OPEN_AFTER_HOST_SATURATION",product_body_observed=False,
        actual_product_child_executed=False,worker_created=False,job_assigned=False,
        Native_source_frame_qualified=False,current_generation_runtime_candidate_qualified=False,
        cleanup_confirmed=True,owned_tree_empty=True,accepted_count_delta=0,
        P09_gate="OPEN",A12_gate="OPEN",A13_gate="OPEN",PC_freeze_resolved=False,source_freeze=[],
        samples=[dict(system_cpu_percent=96,available_ram_percent=58,commit_used_percent=30,
            parent_private_percent=.2,parent_cpu_machine_percent=0)],
        source_frame=dict(frame_state="CLOSED",registered_live_frame=False,actual_byte_boundaries=[],
            original_owned_cleanup_confirmed_before_release=False,input_count=855,handles=handles,
            parent_python_live_raw_access_policy=dict(active_scope=False,all_original_open_function_identities_restored=True,
                unrelated_output_or_cleanup_opens_not_given_extra_live_Native_checkpoint=True,
                original_physical_reader_resource_Frame_and_decoder_guards_not_replaced=True)))


class Tests(unittest.TestCase):
    def test_exact_failure_unchanged_and_no_GO(self):
        row=fixture();before=copy.deepcopy(row);proof=m.validate(row)
        self.assertEqual(row,before);self.assertFalse(proof["automatic_retry_or_GO_authorized"])
    def test_remaining_handle_or_close_failure_rejected(self):
        for key in ("input_lock_handles_remaining","handle_close_failed_attempts"):
            row=fixture();row["source_frame"]["handles"][key]=1
            with self.assertRaises(ValueError):m.validate(row)
    def test_false_COMMITTED_or_byte_boundary_claim_rejected(self):
        for key,value in (("frame_state","COMMITTED"),("actual_byte_boundaries",[{}])):
            row=fixture();row["source_frame"][key]=value
            with self.assertRaises(ValueError):m.validate(row)
    def test_any_product_or_worker_claim_rejected(self):
        for key in ("worker_created","product_body_observed","Native_source_frame_qualified"):
            row=fixture();row[key]=True
            with self.assertRaises(ValueError):m.validate(row)
    def test_wrong_physical_task_rejected(self):
        row=fixture();row["task"]="case158-current-r002-tests"
        with self.assertRaises(ValueError):m.validate(row)
    def test_unrestored_raw_policy_rejected(self):
        row=fixture();row["source_frame"]["parent_python_live_raw_access_policy"]["active_scope"]=True
        with self.assertRaises(ValueError):m.validate(row)
    def test_warning_latch_not_invented(self):
        row=fixture();row["source_frame"]["handles"]["all_acquisition_checkpoint_warning_fail_fast"]["latched"]=False
        with self.assertRaises(ValueError):m.validate(row)
    def test_partial_scope_never_claimed_as_complete(self):
        row=fixture();row["source_frame"]["input_count"]=854;row["source_freeze"]=[{}]*854
        with self.assertRaises(ValueError):m.validate(row)


if __name__=="__main__":unittest.main()
