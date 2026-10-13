import copy
import io
import json
import unittest
from unittest.mock import patch
import run_runtime_resumable_r07_case as p


class RuntimeResumeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        prep=json.loads((p.c.ROOT/p.b.BASE_PREP['path']).read_text(encoding='utf-8'))
        cls.expected=p.v.pins(prep['whole_inputs']);cls.exe=prep['binding']['compiled_test_executable_pin']
        cls.names=json.loads((p.c.ROOT/p.b.run.PARENT['path']).read_text(encoding='utf-8'))['source_test_names']

    def control(self):return {n:dict(path=n,bytes=10,sha256='a'*64) for n in p.CONTROLLERS}
    def engine(self):return {n:dict(path=n,bytes=10,sha256='b'*64) for n in (p.b.SELF,p.b.TEST)}
    def plan(self):return dict(runtime_successful_candidates_requiring_closing=0,next_runtime_index=5,
        runtime_qualified_test_names=self.names[:4])

    def test_select5_skips_original_four_and_attempts_increment_only_failed(self):
        self.assertEqual(p.select(self.plan(),self.names,{}),dict(next_index=5,next_attempt=1))
        self.assertEqual(p.select(self.plan(),self.names,{5:1}),dict(next_index=5,next_attempt=2))

    def test_unclosed_success_blocks_new_body(self):
        plan=self.plan();plan['runtime_successful_candidates_requiring_closing']=1
        with self.assertRaises(ValueError):p.select(plan,self.names,{})

    def test_closed_name_cannot_be_reexecuted(self):
        plan=self.plan();plan['next_runtime_index']=4
        with self.assertRaises(ValueError):p.select(plan,self.names,{})

    def test_corpus_deferred_not_silently_executed(self):
        plan=self.plan();plan['next_runtime_index']=next(i for i,n in enumerate(self.names,1) if n.startswith(p.v.CORPUS_PREFIX))
        with self.assertRaises(ValueError):p.select(plan,self.names,{})

    def test_all_original_runtime_plus_exact_controllers(self):
        scope,history=p.extended_scope(self.expected,self.exe,self.engine(),self.control())
        self.assertEqual(len(scope),1413);self.assertEqual(len(history),67)
        self.assertEqual({n for n in scope if n.endswith('.exe')},{self.exe['path']})
        self.assertTrue({n for n in self.expected if not n.endswith('.exe')}<=set(scope))

    def test_missing_or_extra_controller_rejected(self):
        controls=self.control();controls.pop(p.SELF)
        with self.assertRaises(ValueError):p.extended_scope(self.expected,self.exe,self.engine(),controls)

    def test_extra_controllers_need_real_two_full_body_reads(self):
        case=json.loads((p.c.ROOT/p.r.case_path(4,1)).read_text(encoding='utf-8'))
        control=self.control();engine=p.v.pins(case['supplemental_scheduler_input_pins'])
        case['runtime_resume_controller_input_pins']=list(control.values());case['source_freeze']+=list(control.values())
        with self.assertRaises(ValueError):p.r.case_scope(case,self.expected,self.names,self.exe,engine,control)
        for row in case['owned_source_reader_passes']:row['read_passes']+=8;row['bytes_read']+=80
        scope,_=p.r.case_scope(case,self.expected,self.names,self.exe,engine,control)
        self.assertEqual(len(scope),1413)

    def test_original_terminal_failure_and_gate_flags_not_weakened(self):
        case=json.loads((p.c.ROOT/p.r.case_path(4,1)).read_text(encoding='utf-8'))
        case['terminal_summary']['passed']=249
        with self.assertRaises(ValueError):p.v.validate_case(case,self.names[3],case['binding'])
        self.assertFalse(p.r.flags()['whole1470_current_fresh_qualified'])
        self.assertTrue(p.r.flags()['historical_whole_gate_reconciliation_required'])

    def test_new_receipt_directory_keeps_frozen_legacy_progress(self):
        self.assertNotEqual(p.DIR,p.core.DIR)
        self.assertNotEqual(p.target('close',1,5,1),p.r.destination('close',5,1,1))

    def test_invalid_run_and_scope_no_overwrite(self):
        for number in (0,100,True):
            with self.assertRaises(ValueError):p.target('plan',number)
        with self.assertRaises(ValueError):p.target('close',1,250,1)

    def test_stop_does_not_retry_or_close_or_start_next(self):
        binding=(self.expected,self.names,self.exe,dict(next_index=5,next_attempt=1),self.engine(),self.control())
        with patch.object(p.sys,'argv',[p.SELF,'--mode','actual','--run','1']), \
                patch.object(p,'prepare',return_value=binding),patch.object(p,'one',return_value=(2,'fixture')) as one, \
                patch.object(p,'close',side_effect=AssertionError('NO_CLOSE')),patch('sys.stdout',new=io.StringIO()):
            self.assertEqual(p.main(),2);self.assertEqual(one.call_count,1)

    def test_pass_starts_one_body_and_one_closing_only(self):
        binding=(self.expected,self.names,self.exe,dict(next_index=5,next_attempt=1),self.engine(),self.control())
        with patch.object(p.sys,'argv',[p.SELF,'--mode','actual','--run','1']), \
                patch.object(p,'prepare',return_value=binding),patch.object(p,'one',return_value=(0,'fixture')) as one, \
                patch.object(p,'close',return_value=0) as close,patch('sys.stdout',new=io.StringIO()):
            self.assertEqual(p.main(),0);self.assertEqual(one.call_count,1);self.assertEqual(close.call_count,1)

    def test_close_only_recovery_never_reexecutes_body(self):
        binding=(self.expected,self.names,self.exe,dict(next_index=5,next_attempt=1),self.engine(),self.control())
        with patch.object(p.sys,'argv',[p.SELF,'--mode','close','--run','2','--index','5','--attempt','1']), \
                patch.object(p,'prepare',return_value=binding),patch.object(p,'one',side_effect=AssertionError('NO_BODY')), \
                patch.object(p,'close',return_value=0) as close:
            self.assertEqual(p.main(),0);self.assertEqual(close.call_count,1)

    def test_actual_case_override_and_incomplete_close_pair_rejected(self):
        for args in (['--mode','actual','--run','1','--index','5'],
                ['--mode','close','--run','2','--index','5']):
            with patch.object(p.sys,'argv',[p.SELF,*args]), \
                    patch.object(p,'prepare',side_effect=AssertionError('NO_PREPARE')):
                with self.assertRaises(ValueError):p.main()


if __name__=='__main__':unittest.main()
