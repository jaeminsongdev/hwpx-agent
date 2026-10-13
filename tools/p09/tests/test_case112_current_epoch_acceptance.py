"""Small guarded receipt contracts; no product/Native/compiled-list replay."""
import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import accept_case112_current_epoch as a

CHECKPOINT=lambda:None


class EpochAcceptanceContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reader=a.pressure.WeightedReader(a.c.ROOT,CHECKPOINT)
        cls.row=a.read_exact(cls.reader,a.ROOT_PIN)
        cls.listing=a.read_exact(cls.reader,a.scope.LIST_PIN)
        cls.body=a.read_exact(cls.reader,a.BODY_PIN)
        cls.fresh=a.packed.unpack(a.read_exact(cls.reader,a.FRESH_PIN),CHECKPOINT)
    @classmethod
    def tearDownClass(cls):cls.reader.finish()
    def check_bad(self,mutate):
        row=copy.deepcopy(self.row);mutate(row)
        with self.assertRaises((ValueError,KeyError,TypeError)):
            a.validate(row,self.listing,self.body,self.fresh,CHECKPOINT)
    def test_actual_immutable_candidate_full_union_passes(self):
        result=a.validate(self.row,self.listing,self.body,self.fresh,CHECKPOINT)
        self.assertEqual(result["whole_runtime_input_count"],1710)
        self.assertEqual(result["whole_runtime_input_bytes"],140408033)
        self.assertEqual(result["original_resource_samples"],925)
    def test_failed_or_partial_candidate_cannot_count(self):
        for key,value in (("state","STOPPED_NOT_ACCEPTED"),("writer_authorized",False),
            ("exit_code",1),("closing_error_code","CLOSING_FAILED"),("Native_source_frame_qualified",False),
            ("cleanup_confirmed",False),("prior_queue_cases",106),("next_case",113),("accepted_count_delta",1)):
            with self.subTest(key=key):self.check_bad(lambda r:r.update({key:value}))
    def test_bool_int_type_drift_rejected(self):
        for key,value in (("exit_code",False),("selected_test_index",112.0),("job_assigned",1)):
            with self.subTest(key=key):self.check_bad(lambda r:r.update({key:value}))
        self.check_bad(lambda r:r["terminal_summary"].update(passed=True))
    def test_exact_name_and_arguments(self):
        self.check_bad(lambda r:r.update(selected_test_names=["other_test"]))
        self.check_bad(lambda r:r["test_arguments"].pop())
    def test_source_union_duplicate_missing_or_rebase_rejected(self):
        self.check_bad(lambda r:r["source_freeze"].pop())
        self.check_bad(lambda r:r["source_freeze"].append(r["source_freeze"][0]))
        self.check_bad(lambda r:r["source_freeze"][0].update(sha256="a"*64))
    def test_missing_import_and_controller_bootstrap_rejected(self):
        self.check_bad(lambda r:r["imported_worker_source_paths"].pop())
        self.check_bad(lambda r:r["bootstrap_metadata"]["input_pins"].pop())
    def test_two_whole_actual_reads_not_partial_cached_or_swapped(self):
        self.check_bad(lambda r:r["source_frame"]["actual_byte_boundaries"][1]["actual_byte_pins"].pop())
        self.check_bad(lambda r:r["source_frame"]["actual_byte_boundaries"].reverse())
        self.check_bad(lambda r:r["source_frame"].update(serialized_pin_reused_as_live_handle=True))
    def test_identity_and_owned_handle_duplicate_cleanup(self):
        self.check_bad(lambda r:r["source_frame"]["handles"].update(input_lock_handles_remaining=1))
        self.check_bad(lambda r:r["source_frame"]["handles"]["borrowed_byte_streams"].update(shared_offset_resets=3419))
        self.check_bad(lambda r:r["source_frame"]["held_identity_after_owned_cleanup"].update(held_identity_checks_complete=False))
    def test_phase_original_credit_rate_and600_not_relaxed(self):
        self.check_bad(lambda r:r["source_frame"]["handles"]["acquisition_phase_pressure"].update(clock_previous_credit_or_reservation_counter_reset=True))
        self.check_bad(lambda r:r["source_frame"]["handles"].update(maximum_lock_seconds=720))
        self.check_bad(lambda r:r["source_frame"]["handles"]["native_open_pacing"].update(maximum_opens_per_second=32))
    def test_path_guard_not_cached_and_capture_not_truncated(self):
        self.check_bad(lambda r:r["source_path_guard_diagnostics"][1].update(metadata_reused_between_source_requests=True))
        self.check_bad(lambda r:r["capture_diagnostics"]["received_bytes"].update(stdout=229))
    def test_cost_no_product_or_native_pacing_omission(self):
        self.check_bad(lambda r:r["complete_runtime_budget"].update(product_allowance_seconds=0))
        self.check_bad(lambda r:r["complete_runtime_budget"].update(predicted_runtime_combined_seconds=580.0))
    def test_original_resource_cpu_commit_parent_stop_rejected(self):
        for key,value in (("commit_used_percent",95),("available_ram_percent",7),("parent_private_percent",7)):
            with self.subTest(key=key):self.check_bad(lambda r:r["samples"][0].update({key:value}))
        self.check_bad(lambda r:[s.update(system_cpu_percent=100) for s in r["samples"][:4]])
    def test_job_configuration_not_interval_cpu_as_hardcap(self):
        self.check_bad(lambda r:r["owned_limits_readback"].update(verified=False))
        self.check_bad(lambda r:r["job_final"].update(active_processes=1))
        # Actual sampled interval6.3559 does not change configured6.25 cap.
        a.validate(self.row,self.listing,self.body,self.fresh,CHECKPOINT)
    def test_prior105_not_silently_rebased(self):
        fresh=copy.deepcopy(self.fresh);fresh["prior_runtime_plan"]["runtime_source_qualified_individual_cases"]=106
        with self.assertRaises(ValueError):a.validate(self.row,self.listing,self.body,fresh,CHECKPOINT)
    def test_gate_or_full249_promotion_rejected(self):
        for key,value in (("full249_current_qualified",True),("signed16_current_qualified",True),("P09_gate","PASS")):
            with self.subTest(key=key):self.check_bad(lambda r:r.update({key:value}))


if __name__=="__main__":
    guard=a.Guard()
    try:
        guard.acquire();CHECKPOINT=guard.check
        result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(EpochAcceptanceContracts))
    finally:guard.close()
    print(json.dumps(dict(contract_count=result.testsRun,passed=result.wasSuccessful(),
        samples=len(guard.samples),cleanup_confirmed=guard.cleanup,product_child_executed=False)))
    raise SystemExit(0 if result.wasSuccessful() and guard.cleanup else 2)
