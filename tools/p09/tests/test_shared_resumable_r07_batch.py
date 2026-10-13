import copy
import contextlib
import io
import json
import unittest
from unittest.mock import patch
import run_shared_resumable_r07_batch as v


class SharedBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prep=json.loads((v.c.ROOT/v.BASE_PREP['path']).read_text(encoding='utf-8'))
        cls.expected=v.v.pins(cls.prep['whole_inputs']);cls.exe=cls.prep['binding']['compiled_test_executable_pin']
    def setUp(self):
        self.engine={n:dict(path=n,bytes=10,sha256='a'*64) for n in (v.SELF,v.TEST)}
    def test_prior1470_and142_contract_baseline_remains_unchanged(self):
        self.assertEqual(len(self.expected),1470);self.assertEqual(self.prep['contract_tests_passed'],142)
        self.assertNotIn(v.SELF,self.expected)
    def test_extensions_keep_all_original_runtime_and_history(self):
        runtime,history=v.OLD_RUNTIME_SCOPE(self.expected,self.exe)
        augmented,after=v.source_extension(runtime,history,self.engine)
        self.assertEqual(set(augmented),set(runtime)|set(self.engine))
        self.assertEqual(after,history);self.assertEqual(len(history),67)
    def test_engine_overlap_or_exe_supplement_rejected(self):
        runtime,history=v.OLD_RUNTIME_SCOPE(self.expected,self.exe)
        for engine in ({self.exe['path']:self.exe},{v.SELF:self.engine[v.SELF]}):
            with self.assertRaises(ValueError):v.source_extension(runtime,history,engine)
    def test_start_budget_and_case_count_are_closed(self):
        v.limits(2,300)
        for count,budget in ((6,300),(0,300),(2,301),(2,0),(True,300)):
            with self.assertRaises(ValueError):v.limits(count,budget)
    def test_generation_cannot_overwrite_old_case001_closing(self):
        with self.assertRaises(ValueError):v.paths(1)
        self.assertNotEqual(v.paths(2)['closing'],v.BASE_CLOSE['path'])
    def test_pending_from_previous_attempt_must_close_before_new_batch(self):
        with self.assertRaises(ValueError):v.select(dict(next_index=2,successful_candidates_requiring_separate_closing=1))
        self.assertEqual(v.select(dict(next_index=2,successful_candidates_requiring_separate_closing=0))['next_index'],2)
    def test_same_baseline_identity_does_not_invalidate_completed_case001(self):
        original=json.loads((v.c.ROOT/v.BASE_CASE['path']).read_text(encoding='utf-8'))
        self.assertEqual(original['binding'],self.prep['binding'])
        # New scheduler is supplementary, not silently inserted into old hash.
        self.assertNotIn(v.SELF,self.expected)
    def test_supplemental_case_requires_two_actual_fresh_passes(self):
        runtime,history=v.OLD_RUNTIME_SCOPE(self.expected,self.exe)
        augmented,_=v.source_extension(runtime,history,self.engine)
        row=dict(binding=self.prep['binding'],source_freeze=list(augmented.values()),
            supplemental_scheduler_input_pins=list(self.engine.values()),baseline_input_manifest_not_rewritten=True,
            serial_single_case_job=True,owned_source_reader_passes=[dict(read_passes=len(augmented),
                bytes_read=sum(p['bytes'] for p in augmented.values())) for _ in range(2)])
        v.validate_supplement(row,self.expected,self.engine)
        row['owned_source_reader_passes'].pop()
        with self.assertRaises(ValueError):v.validate_supplement(row,self.expected,self.engine)
    def test_missing_supplemental_bytes_rejected(self):
        row=dict(binding=self.prep['binding'],source_freeze=list(self.expected.values()))
        with self.assertRaises(ValueError):v.validate_supplement(row,self.expected,self.engine)
    def test_original_guards_and_body_deadline_retained(self):
        self.assertEqual(v.c.POLICY['sample_seconds'],0.5)
        self.assertEqual(v.c.POLICY['emergency_cpu_consecutive_samples'],4)
        v.core.run.original.require_scope(1200)
        with self.assertRaises(ValueError):v.core.run.original.require_scope(1201)
    def test_no_automatic_closing_or_next_case_after_stop(self):
        binding=(self.expected,[],self.exe,dict(next_index=2,next_attempt=1),self.engine)
        with contextlib.redirect_stdout(io.StringIO()), \
                patch.object(v.sys,'argv',[v.SELF,'--mode','actual','--run','2']), \
                patch.object(v,'prepare',return_value=binding),patch.object(v,'one',return_value=(2,'fixture')) as one, \
                patch.object(v,'event',return_value=None),patch.object(v,'close',side_effect=AssertionError('NO_CLOSING')):
            self.assertEqual(v.main(),2);self.assertEqual(one.call_count,1)
    def test_runtime_scope_role_patch_is_restored(self):
        baseline=v.core.runtime_scope
        with patch.object(v.core,'run_case',return_value=(0,'fixture')):
            v.one(2,(self.expected,[],self.exe,{},self.engine),{})
        self.assertIs(v.core.runtime_scope,baseline)


if __name__=='__main__':unittest.main()
