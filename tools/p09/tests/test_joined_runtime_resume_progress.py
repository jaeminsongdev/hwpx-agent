import copy
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import joined_runtime_resume_progress as j


class JoinedProgressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=j.p.DIR+'/p190-case-005-attempt-001.json'
        cls.close=j.p.META+'/p198-case-005-attempt-001-close-01.v1.json'
        cls.case=json.loads((j.c.ROOT/cls.source).read_text(encoding='utf-8'))
        cls.closing=json.loads((j.c.ROOT/cls.close).read_text(encoding='utf-8'))
        prep=json.loads((j.c.ROOT/j.b.BASE_PREP['path']).read_text(encoding='utf-8'))
        cls.expected=j.v.pins(prep['whole_inputs']);cls.exe=prep['binding']['compiled_test_executable_pin']
        cls.names=json.loads((j.c.ROOT/j.b.run.PARENT['path']).read_text(encoding='utf-8'))['source_test_names']
        cls.engine=j.v.pins(cls.case['supplemental_scheduler_input_pins'])
        cls.pin=cls.closing['case_receipt_pin'];cls.control=j.v.pins(cls.case['runtime_resume_controller_input_pins'])

    def current(self):
        return dict(self.control,**{n:dict(path=n,bytes=10,sha256='a'*64)
            for n in j.CONTROLLERS if n not in self.control})

    def verify(self,case=None,closing=None,pin=None,files=None,closings=None):
        values={self.source:self.case if case is None else case,self.close:self.closing if closing is None else closing}
        parsed=[];rechecked=[];snapshots={}
        def read(name):
            parsed.append(name);snapshots[name]=self.pin if name==self.source else dict(path=name,bytes=1,sha256='b'*64)
            return copy.deepcopy(values[name])
        def fresh(name):
            rechecked.append(name);return self.pin if pin is None else pin
        q=SimpleNamespace(json=read,pin=fresh,reader=SimpleNamespace(snapshots=snapshots))
        result=j.verify_new_cases(q,self.expected,self.names,self.exe,self.engine,self.current(),
            [j.c.ROOT/self.source] if files is None else files,
            [j.c.ROOT/self.close] if closings is None else closings)
        return result,parsed,rechecked

    def test_one_parse_one_fresh_recheck_and_full_original_validation(self):
        result,parsed,fresh=self.verify()
        self.assertEqual(parsed,[self.source,self.close]);self.assertEqual(fresh,[self.source])
        self.assertEqual(result[0],[self.names[4]]);self.assertEqual(result[1],[self.names[4]])
        self.assertEqual(result[4]['redundant_case_JSON_parses_avoided'],1)
        self.assertEqual(result[4]['case_payloads_retained_at_once_limit'],1)

    def test_changed_second_read_rejected(self):
        with self.assertRaises(ValueError):self.verify(pin=dict(self.pin,sha256='c'*64))

    def test_changed_or_missing_controller_rejected(self):
        current=self.current();current[j.p.SELF]=dict(current[j.p.SELF],sha256='c'*64)
        with self.assertRaises(ValueError):j.case_controller(self.case,current)
        current=self.current();del current[j.p.SELF]
        with self.assertRaises(ValueError):j.case_controller(self.case,current)

    def test_only_eight_ten_twelve_controller_generations_allowed(self):
        for count in (7,9,11):
            case=copy.deepcopy(self.case);case['runtime_resume_controller_input_pins']=list(self.current().values())[:count]
            with self.assertRaises(ValueError):j.case_controller(case,self.current())
        for count in (8,10,12):
            case=copy.deepcopy(self.case);case['runtime_resume_controller_input_pins']=list(self.current().values())[:count]
            self.assertEqual(len(j.case_controller(case,self.current())),count)

    def test_new_controller_declaration_without_actual_reads_rejected(self):
        case=copy.deepcopy(self.case);case['runtime_resume_controller_input_pins']=list(self.current().values())
        with self.assertRaises(ValueError):self.verify(case=case)

    def test_incomplete_terminal_body_is_not_reused(self):
        case=copy.deepcopy(self.case);case['exit_code']=1
        with self.assertRaises(ValueError):self.verify(case=case)

    def test_incomplete_or_promoted_closing_rejected(self):
        for mutate in (lambda d:d['IO'].update(finished=False),lambda d:d.update(product_complete=True),
                lambda d:d.update(resource_watcher_cleanup_confirmed=False)):
            closing=copy.deepcopy(self.closing);mutate(closing)
            with self.assertRaises(ValueError):self.verify(closing=closing)

    def test_failed_closing_remains_unclosed_without_body_retry(self):
        result,parsed,fresh=self.verify(closing=dict(state='FAILED_NOT_ACCEPTED'))
        self.assertEqual(result[0],[]);self.assertEqual(result[1],[self.names[4]])
        self.assertEqual(parsed,[self.source,self.close]);self.assertEqual(fresh,[])

    def test_orphan_passed_closing_rejected_and_orphan_failure_preserved(self):
        with self.assertRaises(ValueError):self.verify(files=[])
        result,parsed,fresh=self.verify(files=[],closing=dict(state='FAILED_NOT_ACCEPTED'))
        self.assertEqual(result[0],[]);self.assertEqual(parsed,[self.close]);self.assertEqual(fresh,[])

    def test_duplicate_attempts_rejected(self):
        with self.assertRaises(ValueError):self.verify(files=[j.c.ROOT/self.source]*2)

    def test_duplicate_closings_cannot_count_two_successes(self):
        result,_,_=self.verify(closings=[j.c.ROOT/self.close]*2)
        legacy=dict(accepted_test_names=self.names[:3],accepted_individual_cases=3,
            successful_candidates_requiring_separate_closing=1)
        base=dict(runtime_qualified_test_names=self.names[:4])
        with self.assertRaises(ValueError):j.s.combine(legacy,base,self.names,result[0],result[1])

    def test_wrapper_preserves_terminal_stop_and_restores_original_roles(self):
        progress=j.p.progress;control=j.p.CONTROLLERS;contracts=j.p.contracts;dump=j.p.RAW_DUMP
        with patch.object(j.p,'main',return_value=2) as main:
            self.assertEqual(j.main(),2);self.assertEqual(main.call_count,1)
        self.assertIs(j.p.progress,progress);self.assertEqual(j.p.CONTROLLERS,control)
        self.assertIs(j.p.contracts,contracts);self.assertIs(j.p.RAW_DUMP,dump)


if __name__=='__main__':unittest.main()
