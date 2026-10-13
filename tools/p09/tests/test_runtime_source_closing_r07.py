import copy
import json
import unittest
from unittest.mock import patch
import runtime_source_closing_r07 as r


class RuntimeClosingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prep=json.loads((r.c.ROOT/r.b.BASE_PREP['path']).read_text(encoding='utf-8'))
        cls.expected=r.v.pins(cls.prep['whole_inputs']);cls.exe=cls.prep['binding']['compiled_test_executable_pin']
        cls.parent=json.loads((r.c.ROOT/r.b.run.PARENT['path']).read_text(encoding='utf-8'))
        cls.names=cls.parent['source_test_names']
        cls.case=json.loads((r.c.ROOT/(r.core.DIR+'/p190-case-004-attempt-001.json')).read_text(encoding='utf-8'))
        cls.engine=r.v.pins(cls.case['supplemental_scheduler_input_pins'])
    def controller(self):return {n:dict(path=n,bytes=10,sha256='a'*64) for n in (r.SELF,r.TEST)}
    def scope(self,case=None):return r.case_scope(self.case if case is None else case,self.expected,self.names,self.exe,self.engine,self.controller())
    def legacy(self):return dict(accepted_test_names=self.names[:3],accepted_individual_cases=3,successful_candidates_requiring_separate_closing=1)
    def test_original_case4_keeps_exact1405_runtime_and_history67(self):
        runtime,history=self.scope();self.assertEqual(len(runtime),1405);self.assertEqual(len(history),67)
        self.assertIn(self.exe['path'],runtime);self.assertFalse(set(runtime)&history)
    def test_all_non_EXE_original_sources_retained(self):
        runtime,_=self.scope()
        self.assertTrue({n for n in self.expected if not n.endswith('.exe')}<=set(runtime))
    def test_runtime_scope_does_not_change_original_binding(self):
        self.assertEqual(self.case['binding'],r.v.identity(self.names,self.expected,self.exe))
    def test_missing_runtime_source_rejected(self):
        case=copy.deepcopy(self.case);case['source_freeze'].pop()
        with self.assertRaises(ValueError):self.scope(case)
    def test_missing_second_fresh_body_read_rejected(self):
        case=copy.deepcopy(self.case);case['owned_source_reader_passes'].pop()
        with self.assertRaises(ValueError):self.scope(case)
    def test_changed_executable_or_failed_body_rejected(self):
        case=copy.deepcopy(self.case);case['exit_code']=1
        with self.assertRaises(ValueError):self.scope(case)
    def test_controller_extension_needs_two_real_full_read_passes(self):
        case=copy.deepcopy(self.case);ctrl=self.controller();case['runtime_resume_controller_input_pins']=list(ctrl.values())
        case['source_freeze']+=list(ctrl.values())
        with self.assertRaises(ValueError):self.scope(case)
        for row in case['owned_source_reader_passes']:
            row['read_passes']+=2;row['bytes_read']+=20
        runtime,_=self.scope(case);self.assertEqual(len(runtime),1407)
    def test_legacy_three_not_relabelled_four_when_runtime4_closes(self):
        plan=r.runtime_plan(self.legacy(),self.names,[self.names[3]],self.names[:4])
        self.assertEqual(plan['legacy_whole_accepted_individual_cases'],3)
        self.assertEqual(plan['legacy_whole_pending_successful_candidates'],1)
        self.assertEqual(plan['runtime_source_qualified_individual_cases'],4)
        self.assertEqual(plan['next_runtime_index'],5);self.assertFalse(plan['whole1470_current_fresh_qualified'])
    def test_passed_unclosed_case_not_selected_for_reexecution(self):
        plan=r.runtime_plan(self.legacy(),self.names,[],self.names[:4])
        self.assertEqual(plan['runtime_successful_candidates_requiring_closing'],1)
        self.assertEqual(plan['next_runtime_index'],5)
    def test_duplicate_or_unexecuted_closing_rejected(self):
        for closed in ([self.names[3]]*2,[self.names[4]],[self.names[0]]):
            with self.assertRaises(ValueError):r.runtime_plan(self.legacy(),self.names,closed,self.names[:4])
    def test_runtime_closing_is_not_legacy_whole_schema_or_gate(self):
        self.assertNotEqual(r.SCHEMA,r.v.CLOSING_SCHEMA);self.assertNotEqual(r.PASS,r.v.CLOSING_PASS)
        flags=r.flags();self.assertFalse(flags['whole1470_current_fresh_qualified'])
        self.assertFalse(flags['product_complete']);self.assertEqual(flags['P09_gate'],'OPEN')
    def test_source_status_stop_cleanup_and_false_full_flags_rejected(self):
        runtime,_=self.scope();ctrl=self.controller();pin=dict(path=r.case_path(4,1),bytes=1,sha256='c'*64)
        doc=dict(schema_version=r.SCHEMA,state=r.PASS,**r.flags(),binding=self.case['binding'],case_receipt_pin=pin,
            selected_test_name=self.names[3],pending_legacy_whole_closing_reference=self.case['closing_id'],
            resource_stop_reason=None,resource_watcher_cleanup_confirmed=True,
            IO=dict(finished=True,bound_inputs=1407,final_fresh_hashes=1407,maximum_scope_seconds=600),
            runtime_source_before=list(runtime.values()),runtime_source_after=list(runtime.values()),
            closing_controller_before=list(ctrl.values()),closing_controller_after=list(ctrl.values()),
            bound_input_pins=list(runtime.values())+list(ctrl.values()),sealed_whole_before_anchor=r.b.BASE_CLOSE,
            historical_EXE_boundary_count=67)
        r.validate(doc,self.case,pin,self.expected,self.names,self.exe,self.engine,ctrl)
        for key,value in (('resource_stop_reason','STOP_SUSTAINED_SYSTEM_CPU'),('resource_watcher_cleanup_confirmed',False),
                ('whole1470_current_fresh_qualified',True),('historical67_current_fresh_qualified',True),('product_complete',True)):
            bad=copy.deepcopy(doc);bad[key]=value
            with self.assertRaises(ValueError):r.validate(bad,self.case,pin,self.expected,self.names,self.exe,self.engine,ctrl)
    def test_old_case_and_closing_paths_not_overwritten(self):
        new=r.destination('close',4,1,1)
        self.assertNotEqual(new,self.case['closing_id']);self.assertNotEqual(new,r.case_path(4,1))
        with self.assertRaises(ValueError):r.destination('close',4,1,0)
    def test_original_guard_deadline_and_corpus_deferred(self):
        self.assertEqual(r.c.POLICY['emergency_cpu_consecutive_samples'],4)
        plan=r.runtime_plan(self.legacy(),self.names,[self.names[3]],self.names[:4])
        self.assertEqual(plan['runtime_remaining_corpus_cases'],6)
        self.assertFalse(plan['full249_current_qualified']);self.assertTrue(plan['historical_whole_gate_reconciliation_required'])


if __name__=='__main__':unittest.main()
