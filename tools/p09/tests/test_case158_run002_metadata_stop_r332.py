import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import review_case158_run002_metadata_stop_r332 as m


def fixture():
    return dict(state="DEFERRED_NOT_STARTED",task="case158-current-r002-tests",selected_test_index=158,
        stop_reason="STOP_METADATA_WARNING_BEFORE_COOLING_OR_RESUME",product_body_observed=False,
        actual_product_child_executed=False,worker_created=False,job_assigned=False,
        Native_source_frame_qualified=False,current_generation_runtime_candidate_qualified=False,
        source_frame=None,source_freeze=[],cleanup_confirmed=True,owned_tree_empty=True,
        accepted_count_delta=0,P09_gate="OPEN",A12_gate="OPEN",A13_gate="OPEN",PC_freeze_resolved=False,
        samples=[dict(time_utc=t,system_cpu_percent=cpu,available_ram_percent=63,
            commit_used_percent=29,parent_cpu_machine_percent=.2,parent_private_mib=46,parent_private_percent=.15)
            for t,cpu in (("2026-10-13T00:00:00+00:00",20),("2026-10-13T00:00:00.5+00:00",76))],
        bootstrap_metadata=dict(input_pins=[{}],read_passes=1,bytes_read=100,
            early_pressure=dict(metadata_failfast_connection=dict(warning_CPU_percent=75,warning_stops=1,
                latched=True,active=False,original_checkpoint_restored=True,original_hard_guard_first=True,
                added_sampler_or_native_query=False,added_cooling_waits=0,automatic_retry_or_resume=False,
                complete_source_reads_or_deadlines_weakened=False),
                reusable_chunk_metadata_reader=dict(workspace_bytes=65536,workspace_allocations=1,
                    active_lease=False,leases=1,lease_returns=1))))


class Tests(unittest.TestCase):
    def test_exact_failure_review_never_authorizes_GO(self):
        row=fixture();before=copy.deepcopy(row);proof=m.validate(row)
        self.assertFalse(proof["automatic_retry_or_GO_authorized"])
        self.assertFalse(proof["actual_product_or_Native_executed"])
        self.assertEqual(row,before)
    def test_any_worker_or_frame_or_candidate_disqualifies_pre_native_claim(self):
        for key,value in (("worker_created",True),("job_assigned",True),("source_frame",{}),
                          ("product_body_observed",True),("current_generation_runtime_candidate_qualified",True)):
            row=fixture();row[key]=value
            with self.assertRaises(ValueError):m.validate(row)
    def test_wrong_physical_task_and_boolean_case_rejected(self):
        for key,value in (("task","case158-current-r001-tests"),("selected_test_index",True)):
            row=fixture();row[key]=value
            with self.assertRaises(ValueError):m.validate(row)
    def test_unrestored_latch_or_cooling_cannot_pass(self):
        for key,value in (("latched",False),("original_checkpoint_restored",False),("added_cooling_waits",1)):
            row=fixture();row["bootstrap_metadata"]["early_pressure"]["metadata_failfast_connection"][key]=value
            with self.assertRaises(ValueError):m.validate(row)
    def test_resource_warning_not_invented_from_low_CPU(self):
        row=fixture();row["samples"][-1]["system_cpu_percent"]=20
        with self.assertRaises(ValueError):m.validate(row)
    def test_short_force_sample_is_not_qualified_as_full_interval(self):
        row=fixture();row["samples"][-1]["time_utc"]="2026-10-13T00:00:00.01+00:00"
        with self.assertRaises(ValueError):m.validate(row)
    def test_unreturned_lease_or_partial_pin_pass_rejected(self):
        row=fixture();row["bootstrap_metadata"]["early_pressure"]["reusable_chunk_metadata_reader"]["lease_returns"]=0
        with self.assertRaises(ValueError):m.validate(row)
        row=fixture();row["bootstrap_metadata"]["read_passes"]=2
        with self.assertRaises(ValueError):m.validate(row)


if __name__=="__main__":unittest.main()
