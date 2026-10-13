"""Strict actual115 acceptance contracts; no Native/product replay."""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import accept_case115_current_epoch as m

CHECKPOINT=lambda:None


class Current115AcceptanceContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.q=m.a.AcceptanceReader(m.a.c.ROOT,CHECKPOINT)
        cls.row,cls.listing,cls.evidence,cls.proof=m.prepare(cls.q)
        cls.oldbody=m.a.read_exact(cls.q,m.a.BODY_PIN)
        cls.fresh=m.a.packed.unpack(m.a.read_exact(cls.q,m.a.FRESH_PIN),CHECKPOINT)
        project,_=m.validator(m.candidate.read_source(cls.q,m.candidate.ACCEPTOR_PIN))
        check,_=project(m.candidate.read_source(cls.q,m.candidate.original.ORACLE_PIN),cls.row,cls.listing,cls.oldbody)
        cls.check=staticmethod(check)
        raw=m.candidate.read_source(cls.q,m.candidate.ACCEPTOR_PIN)
        cls.execute,cls.run_proof=m.run_projection(raw)
    @classmethod
    def tearDownClass(cls):cls.q.finish()
    def bad(self,mutate):
        CHECKPOINT();row=copy.deepcopy(self.row);mutate(row)
        with self.assertRaises((ValueError,KeyError,TypeError)):
            self.check(row,self.listing,self.oldbody,self.fresh,CHECKPOINT)
        CHECKPOINT()
    def test_actual_full115_same_frame_not_114_recovery_or_gate(self):
        self.assertEqual(self.row['selected_test_index'],115)
        self.assertEqual(self.row['state'],m.runtime.PASS)
        self.assertEqual(self.row['terminal_summary']['passed'],1)
        self.assertTrue(self.row['Native_source_frame_qualified'])
        self.assertEqual(self.row['source_frame']['frame_state'],'COMMITTED')
        self.assertGreater(len(self.row['post_Job_cleanup_resource_samples']),0)
        self.assertTrue(self.proof['same_frame_Native_and_actual_product_complete'])
        self.assertTrue(self.proof['prior114_distinct_epoch_not_promoted_to_same_frame'])
    def test_missing_actual_root_or_immutable_pin_drift_refused(self):
        with patch.object(m,'ROOT_PIN',None),self.assertRaises(ValueError):m.prepare(self.q)
        with patch.object(m,'ROOT_PIN',dict(m.ROOT_PIN,sha256='0'*64)),self.assertRaises(ValueError):m.prepare(self.q)
    def test_original_product_GO_Job_terminal_capture_cleanup_guards(self):
        self.bad(lambda row:row.update(writer_authorized=False))
        self.bad(lambda row:row.update(job_assigned=False))
        self.bad(lambda row:row['terminal_summary'].update(passed=2))
        self.bad(lambda row:row['capture_diagnostics']['received_bytes'].update(stdout=1))
        self.bad(lambda row:row['job_final'].update(active_processes=1))
        self.bad(lambda row:row.update(cleanup_confirmed=False))
    def test_complete_native_scope_both_byte_reads_and_actual_fresh_identities(self):
        self.bad(lambda row:row['source_freeze'].pop())
        self.bad(lambda row:row['source_frame']['actual_byte_boundaries'].pop())
        self.bad(lambda row:row['source_frame']['actual_byte_boundaries'][1]['actual_byte_pins'].pop())
        self.bad(lambda row:row['source_frame']['actual_byte_boundaries'][0]['reader_diagnostics'].update(bytes_read=1))
        self.bad(lambda row:row['source_frame'].update(held_identity_after_owned_cleanup=None))
    def test_physical_retained_stream_and_two_logical_pass_counters(self):
        n=len(self.row['source_freeze'])
        self.bad(lambda row:row['source_frame']['handles']['borrowed_byte_streams'].update(duplicate_handles_opened=2*n))
        self.bad(lambda row:row['source_frame']['handles']['borrowed_byte_streams'].update(shared_offset_resets=n))
        row=copy.deepcopy(self.row);row['source_frame']['handles']['borrowed_byte_streams']['logical_read_lease_returns']=n
        with self.assertRaises(ValueError):m.candidate.retained_evidence(row)
    def test_no_missing_post_sample_zero_fabrication_resource_or_deadline_relaxation(self):
        self.bad(lambda row:row.update(post_Job_cleanup_resource_samples=[]))
        self.bad(lambda row:row['post_Job_cleanup_resource_samples'][0].update(system_cpu_percent=None))
        self.bad(lambda row:row['samples'][0].update(commit_used_percent=95))
        self.bad(lambda row:row['source_frame']['handles'].update(maximum_lock_seconds=720))
    def test_complete_final_resource_wait_and_serial_cost_not_omitted(self):
        self.bad(lambda row:row['complete_runtime_budget'].update(predicted_runtime_combined_seconds=0))
        self.bad(lambda row:row['complete_runtime_budget'].update(final_postcleanup_distinct_sample_wait_allowance_seconds=0))
        self.bad(lambda row:row['complete_runtime_budget'].update(unallocated_margin_seconds=0))
        self.bad(lambda row:row['complete_runtime_budget'].update(additional_serial_PDH_maximum_sample_budget_seconds=0))
    def test_original_run_guards_exact_with_ten_metadata_and_one_final_wait(self):
        self.assertTrue(self.run_proof['original_acceptor_AST_restored_exactly'])
        self.assertEqual(len(self.run_proof['queue_metadata_projected']),10)
        self.assertEqual(self.run_proof['qualifier_distinct_sample_wait_seconds'],.5)
        self.assertTrue(self.run_proof['original_final_guard_retained'])
        self.assertFalse(self.run_proof['extra_observer_or_sample_zero_fabricated'])
    def test_failed114_or_gate_promotion_not_115_candidate(self):
        row=m.a.read_exact(self.q,m.runtime.accepted114.s.BODY_PIN)
        with self.assertRaises(ValueError):self.check(row,self.listing,self.oldbody,self.fresh,CHECKPOINT)
        self.bad(lambda row:row.update(P09_gate='PASS'))
        self.bad(lambda row:row.update(full249_current_qualified=True))
    def test_actual_observations_and_roots_unchanged_after_validation(self):
        before=copy.deepcopy(self.row)
        self.check(self.row,self.listing,self.oldbody,self.fresh,CHECKPOINT)
        self.assertEqual(before,self.row)
        self.assertEqual(m.a.read_exact(self.q,m.ROOT_PIN),self.row)


if __name__=='__main__':
    guard=m.a.Guard();result=None
    try:
        guard.acquire();CHECKPOINT=guard.check
        result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(Current115AcceptanceContracts))
    finally:guard.close()
    print(json.dumps(dict(contract_count=result.testsRun if result else 0,passed=bool(result and result.wasSuccessful()),
        cleanup_confirmed=guard.cleanup,actual_product_or_Native_replayed=False,queue_delta=0)))
    raise SystemExit(0 if result and result.wasSuccessful() and guard.cleanup else 2)
