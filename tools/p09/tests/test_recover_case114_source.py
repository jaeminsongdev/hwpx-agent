"""Guarded recovery eligibility contracts; actual recovery is separate."""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import recover_case114_source as s

CHECKPOINT=lambda:None


class RecoveryContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.q=s.a.AcceptanceReader(s.a.c.ROOT,CHECKPOINT)
        cls.body,cls.listing,cls.evidence,cls.proof=s.eligible(cls.q)
        old=s.a.read_exact(cls.q,s.a.BODY_PIN)
        cls.oldbody=old
        cls.fresh=s.a.packed.unpack(s.a.read_exact(cls.q,s.a.FRESH_PIN),CHECKPOINT)
        project,_=s.candidate.projection(s.candidate.read_source(cls.q,s.candidate.ACCEPTOR_PIN),'validator')
        project.__globals__['mechanics_projection']=s.eligible_mechanics
        check,_=project(s.candidate.read_source(cls.q,s.candidate.original.ORACLE_PIN),cls.body,cls.listing,old)
        cls.check=staticmethod(check)
    @classmethod
    def tearDownClass(cls):cls.q.finish()
    def bad(self,mutate):
        row=copy.deepcopy(self.body);mutate(row)
        with self.assertRaises(ValueError):self.check(row,self.listing,self.oldbody,self.fresh,CHECKPOINT)
    def test_actual_passed_body_two_complete_reads_and_exact_missing_close_not_promoted(self):
        self.assertEqual(self.evidence['whole_runtime_input_count'],1750)
        self.assertEqual(self.body['state'],'STOPPED_NOT_ACCEPTED')
        self.assertIsNone(self.body['source_frame']['held_identity_after_owned_cleanup'])
        self.assertTrue(self.proof['eligibility_is_not_complete_candidate_acceptance'])
        self.assertTrue(self.proof['complete_product_and_before_after_checks_preserved'])
    def test_only_exact_missing_interval_after_complete_passed_body_is_eligible(self):
        for key,value in (('closing_error_code','STOP_SYSTEM_CPU_PRESSURE'),('stop_reason',None),
                ('product_body_observed',False),('current_generation_runtime_candidate_qualified',True),
                ('Native_source_frame_qualified',True),('state',s.r.PASS)):
            with self.subTest(key=key):self.bad(lambda r:r.update({key:value}))
    def test_missing_original_identity_and_samples_required_not_made_up(self):
        self.bad(lambda r:r['source_frame'].update(held_identity_after_owned_cleanup={}))
        self.bad(lambda r:r['source_frame'].update(original_owned_cleanup_confirmed_before_release=True))
        self.bad(lambda r:r.update(post_Job_cleanup_resource_samples=[r['samples'][-1]]))
        self.bad(lambda r:r['source_frame']['handles'].update(handle_metadata_checks=7694))
    def test_complete_before_after_bytes_and_actual_source_scope_cannot_be_removed(self):
        self.bad(lambda r:r['source_freeze'].pop())
        self.bad(lambda r:r['source_frame']['actual_byte_boundaries'][1]['actual_byte_pins'].pop())
        self.bad(lambda r:r['source_frame']['actual_byte_boundaries'].reverse())
        self.bad(lambda r:r['source_frame']['actual_byte_boundaries'][1]['reader_diagnostics'].update(bytes_read=1))
    def test_original_Job_GO_capture_terminal_and_cleanup_guards_retained(self):
        self.bad(lambda r:r.update(job_assigned=False))
        self.bad(lambda r:r.update(writer_authorized=False))
        self.bad(lambda r:r['terminal_summary'].update(passed=2))
        self.bad(lambda r:r['job_final'].update(active_processes=1))
        self.bad(lambda r:r['capture_diagnostics']['received_bytes'].update(stdout=234))
        self.bad(lambda r:r.update(cleanup_confirmed=False))
    def test_original_resources_retained_unknown_or_full_commit_not_zeroed(self):
        self.bad(lambda r:r['samples'][0].update(commit_used_percent=95))
        self.bad(lambda r:r['samples'][0].update(system_cpu_percent=None))
        self.bad(lambda r:r['source_frame']['handles'].update(maximum_lock_seconds=720))
        self.bad(lambda r:r['complete_runtime_budget'].update(predicted_runtime_combined_seconds=0))
    def test_complete_inherited_and_new_closure_conflicts_not_rebased(self):
        required,imports=s.pin_closure(self.q,self.body)
        inherited=s.a.scope.pins(self.body['source_freeze'],1750)
        self.assertTrue(all(required[n]==pin for n,pin in inherited.items()))
        self.assertIn(s.SELF,imports);self.assertIn(s.TEST,imports)
        row=copy.deepcopy(self.body);name=s.r.SELF
        for p in row['source_freeze']:
            if p['path']==name:p['sha256']='0'*64
        with self.assertRaises(ValueError):s.pin_closure(self.q,row)
    def test_single_frame_full_candidate_acceptor_still_rejects_this_failed_root(self):
        with patch.object(s.candidate,'ROOT_PIN',s.BODY_PIN):
            with self.assertRaises(ValueError):s.candidate.prepare(self.q)
    def test_root_and_body_observations_unchanged_after_check(self):
        original=copy.deepcopy(self.body)
        self.check(self.body,self.listing,self.oldbody,self.fresh,CHECKPOINT)
        self.assertEqual(self.body,original)
        self.assertEqual(s.a.read_exact(self.q,s.BODY_PIN),original)


if __name__=='__main__':
    guard=s.a.Guard();result=None
    try:
        guard.acquire();CHECKPOINT=guard.check
        result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(RecoveryContracts))
    finally:guard.close()
    print(json.dumps(dict(contract_count=result.testsRun if result else 0,passed=bool(result and result.wasSuccessful()),
        cleanup_confirmed=guard.cleanup,product_or_Native_source_replayed=False,actual_queue_delta=0)))
    raise SystemExit(0 if result and result.wasSuccessful() and guard.cleanup else 2)
