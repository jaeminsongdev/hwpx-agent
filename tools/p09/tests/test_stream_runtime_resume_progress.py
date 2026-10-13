import copy
import json
import unittest
from unittest.mock import patch
import stream_runtime_resume_progress as s


class StreamProgressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.case=json.loads((s.c.ROOT/(s.p.DIR+'/p190-case-005-attempt-001.json')).read_text(encoding='utf-8'))
        prep=json.loads((s.c.ROOT/s.b.BASE_PREP['path']).read_text(encoding='utf-8'))
        cls.expected=s.v.pins(prep['whole_inputs']);cls.exe=prep['binding']['compiled_test_executable_pin']
        cls.names=json.loads((s.c.ROOT/s.b.run.PARENT['path']).read_text(encoding='utf-8'))['source_test_names']
        cls.engine=s.v.pins(cls.case['supplemental_scheduler_input_pins'])
        cls.original=s.v.pins(cls.case['runtime_resume_controller_input_pins'])

    def control(self):
        return dict(self.original,**{n:dict(path=n,bytes=10,sha256='a'*64) for n in (s.SELF,s.TEST)})

    def test_previous_eight_controllers_reused_without_rewriting_receipt(self):
        self.assertEqual(s.case_controller(self.case,self.control()),self.original)

    def test_changed_previous_controller_rejects_reuse(self):
        current=self.control();current[s.p.SELF]=dict(current[s.p.SELF],sha256='b'*64)
        with self.assertRaises(ValueError):s.case_controller(self.case,current)

    def test_missing_or_unknown_controller_generation_rejected(self):
        for count in (7,9):
            case=copy.deepcopy(self.case);case['runtime_resume_controller_input_pins']=list(self.control().values())[:count]
            with self.assertRaises(ValueError):s.case_controller(case,self.control())

    def test_compact_record_retains_no_full_payload(self):
        record=s.compact_case(self.case,dict(path='public.json',bytes=1,sha256='a'*64),
            self.expected,self.names,self.exe,self.engine,self.control())
        self.assertEqual(len(record),3);self.assertIsInstance(record[2],frozenset)
        self.assertEqual(set(record[1]),{'path','bytes','sha256'})
        self.assertNotIn('samples',str(record));self.assertNotIn('source_freeze',str(record))

    def test_failed_body_is_not_compacted_or_reused(self):
        case=copy.deepcopy(self.case);case['exit_code']=1
        with self.assertRaises(ValueError):s.compact_case(case,{},self.expected,self.names,self.exe,self.engine,self.control())

    def test_new_controllers_need_real_two_extra_reads(self):
        case=copy.deepcopy(self.case);control=self.control();extra=[control[s.SELF],control[s.TEST]]
        case['runtime_resume_controller_input_pins']+=extra;case['source_freeze']+=extra
        with self.assertRaises(ValueError):s.compact_case(case,{},self.expected,self.names,self.exe,self.engine,control)
        for row in case['owned_source_reader_passes']:row['read_passes']+=2;row['bytes_read']+=20
        self.assertEqual(len(s.compact_case(case,{},self.expected,self.names,self.exe,self.engine,control)[2]),10)

    def test_combination_keeps_legacy_three_and_runtime_six_distinct(self):
        legacy=dict(accepted_test_names=self.names[:3],accepted_individual_cases=3,
            successful_candidates_requiring_separate_closing=1)
        base=dict(runtime_qualified_test_names=self.names[:4])
        plan=s.combine(legacy,base,self.names,self.names[4:6],self.names[4:6])
        self.assertEqual(plan['legacy_whole_accepted_individual_cases'],3)
        self.assertEqual(plan['runtime_source_qualified_individual_cases'],6)
        self.assertEqual(plan['next_runtime_index'],7)
        self.assertEqual(plan['all_successful_bodies_pending_whole_reconciliation'],3)
        self.assertFalse(plan['full249_current_qualified'])

    def test_duplicate_closing_or_unexecuted_success_rejected(self):
        legacy=dict(accepted_test_names=self.names[:3],accepted_individual_cases=3,
            successful_candidates_requiring_separate_closing=1);base=dict(runtime_qualified_test_names=self.names[:4])
        for closed in ([self.names[4]]*2,[self.names[6]]):
            with self.assertRaises(ValueError):s.combine(legacy,base,self.names,closed,[self.names[4]])

    def test_unclosed_success_still_blocks_next_body(self):
        legacy=dict(accepted_test_names=self.names[:3],accepted_individual_cases=3,
            successful_candidates_requiring_separate_closing=1);base=dict(runtime_qualified_test_names=self.names[:4])
        plan=s.combine(legacy,base,self.names,[],[self.names[4]])
        with self.assertRaises(ValueError):s.p.select(plan,self.names,{})

    def test_wrapper_restores_original_roles_and_preserves_stop(self):
        old=s.p.progress;controllers=s.p.CONTROLLERS;contracts=s.p.contracts
        with patch.object(s.p,'main',return_value=2) as main:
            self.assertEqual(s.main(),2);self.assertEqual(main.call_count,1)
        self.assertIs(s.p.progress,old);self.assertEqual(s.p.CONTROLLERS,controllers);self.assertIs(s.p.contracts,contracts)


if __name__=='__main__':unittest.main()
