"""P259 fresh STOP/source fixtures에 대한 오수용·재실행 금지 계약."""
import copy
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import accept_checkpoint_stop_compound as p
FIXTURES=None


class CompoundTests(unittest.TestCase):
    def setUp(self):
        if FIXTURES is None:raise RuntimeError('FRESH_STOP_SOURCE_FIXTURES_REQUIRED')
        (self.root,self.body,self.source,self.names,self.expected,self.exe,self.required,self.extras,
         self.legacy,self.base)=copy.deepcopy(FIXTURES)
    def combined(self):return p.combine(self.root,self.body,self.source,self.names,self.expected,self.exe,self.required,self.extras)
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError,IndexError)):self.combined()
    def test_exact_preserved_compound(self):
        before=copy.deepcopy((self.root,self.body,self.source));d=self.combined()
        self.assertTrue(d['compound_individual_case_qualified']);self.assertFalse(d['original_STOP_receipt_accepted'])
        self.assertFalse(d['original_partial_post_hash_completed']);self.assertEqual((self.root,self.body,self.source),before)
    def test_wrong_manifest_binding(self):self.body['binding']['exact_input_manifest_sha256']='a'*64;self.reject()
    def test_wrong_case_in_inventory(self):self.names[89],self.names[90]=self.names[90],self.names[89];self.reject()
    def test_wrong_parent_phase(self):self.body['operation_phase']='running';self.reject()
    def test_failed_body_exit(self):self.body['exit_code']=1;self.reject()
    def test_partial_capture(self):self.body['capture']['complete_streams']=False;self.reject()
    def test_subset_original_source(self):self.required.popitem();self.reject()
    def test_EXE_drift(self):self.required[self.exe['path']]['sha256']='b'*64;self.reject()
    def test_worker_drift(self):self.required[p.m.p.m.SELF]['sha256']='b'*64;self.reject()
    def test_relaxed_job_cpu(self):self.body['owned_limits_readback']['cpu_hard_cap_machine_percent']=100;self.reject()
    def test_relaxed_affinity(self):self.body['owned_limits_readback']['affinity_mask']=3;self.reject()
    def test_stopped_independent_source(self):self.source['resource_stop_reason']=p.review.STOP;self.reject()
    def test_controller_drift(self):self.extras[p.closing.SELF]['sha256']='b'*64;self.reject()
    def test_cached_not_live_frame(self):self.source['source_frame']['serialized_pin_reused_as_live_handle']=True;self.reject()
    def test_unclosed_duplicate(self):self.source['source_frame']['handles']['borrowed_byte_streams']['duplicate_handles_remaining']=1;self.reject()
    def test_original_STOP_not_promoted(self):self.body['state']='PASS_SCOPED_NOT_GATE';self.reject()
    def test_original_overall_pass_not_fabricated(self):self.body['tests_passed']=1;self.reject()
    def test_exact_next91_and_no_gate(self):
        d=p.advance(self.legacy,self.base,self.names);self.assertEqual((d['runtime_source_qualified_individual_cases'],d['next_runtime_index']),(84,91))
        self.assertFalse(d['whole1470_current_fresh_qualified']);self.assertFalse(d['full249_current_qualified'])
    def test_duplicate_acceptance_rejected(self):
        self.base['runtime_qualified_test_names'].append(p.review.NAME)
        with self.assertRaises(ValueError):p.advance(self.legacy,self.base,self.names)
    def test_pending_prior_candidate_rejected(self):
        self.base['runtime_successful_candidates_requiring_closing']=1
        with self.assertRaises(ValueError):p.advance(self.legacy,self.base,self.names)
    def test_early_connection_required(self):self.source['early_source_runtime_connection_verified']=False;self.reject()
    def test_no_false_early_improvement(self):
        d=self.combined();self.assertFalse(d['actual_early_warning_yield_observed'])
        self.assertFalse(d['CPU_improvement_or_PC_freeze_solution_established'])
    def rejected_inventory(self,names,*,wrong_pin=False):
        class File:
            def __init__(self,name):self.name=name
            def __lt__(self,other):return self.name<other.name
            def relative_to(self,root):return self
            def as_posix(self):return p.m.p.DIR+'/'+self.name
        class Folder:
            def glob(self,pattern):return [File(n) for n in names] if pattern=='p255-case-*-run*.v1.json' else []
        class Root:
            def __truediv__(self,path):return Folder()
        pin=dict(p.review.ROOT_PIN,bytes=1) if wrong_pin else p.review.ROOT_PIN
        q=SimpleNamespace(json=lambda n:self.root,reader=SimpleNamespace(snapshots={p.review.ROOT_PIN['path']:pin}))
        with patch.object(p.m.p.c,'ROOT',Root()):
            with self.assertRaises(ValueError):p.before_stop(q,self.legacy,self.base,self.names,
                self.required,p.m.p.v.identity(self.names,self.expected,self.exe),{})
    def test_unknown_failure_not_exception_whitelisted(self):self.rejected_inventory(['p255-case-089-run099.v1.json'])
    def test_record_after_literal_stop_rejected(self):self.rejected_inventory(['p255-case-090-run010.v1.json','p255-case-091-run011.v1.json'])
    def test_changed_literal_bytes_rejected(self):self.rejected_inventory(['p255-case-090-run010.v1.json'],wrong_pin=True)
    def test_missing_eight_prior_qualified_cases_rejected(self):self.rejected_inventory(['p255-case-090-run010.v1.json'])
