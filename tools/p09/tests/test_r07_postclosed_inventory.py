import copy
import json
import unittest
from unittest.mock import patch
import run_r07_postclosed_inventory as v

class R07PostclosedInventoryTests(unittest.TestCase):
    def row(self):return json.loads((v.c.ROOT/v.CLOSING['path']).read_text(encoding='utf-8'))
    def test_current_separate_closure_and_all68_exes(self):
        expected,exe=v.closing_scope(self.row())
        self.assertEqual(len(expected),1423);self.assertEqual(exe['path'],v.b.executable_name())
    def test_original_stop_cannot_be_retroactively_promoted(self):
        for key,value in (('original_build_accepted',True),('original_run_state','PASS_SCOPED_NOT_GATE'),
            ('original_incomplete_final_freeze_preserved',False),('separate_current_post_closing_exact',False)):
            row=self.row();row[key]=value
            with self.assertRaises(ValueError):v.closing_scope(row)
    def test_partial_stale_or_runtime_closure_denied(self):
        for key,value in (('state','STOPPED_NOT_ACCEPTED'),('total_contract_tests_passed',276),
            ('current_compiled249_qualified',True),('product_complete',True),('protected_executables_exact',66)):
            row=self.row();row[key]=value
            with self.assertRaises(ValueError):v.closing_scope(row)
        row=self.row();row['IO']['final_fresh_hashes']-=1
        with self.assertRaises(ValueError):v.closing_scope(row)
    def test_old_r06_or_missing_protected_exe_denied(self):
        row=self.row();row['compiled_test_executable_pin']=copy.deepcopy(row['compiled_test_executable_pin'])
        row['compiled_test_executable_pin']['path']=row['compiled_test_executable_pin']['path'].replace('r07','r06')
        with self.assertRaises(ValueError):v.closing_scope(row)
        row=self.row();row['bound_input_pins']=[p for p in row['bound_input_pins'] if p['path']!=v.b.executable_name()]
        with self.assertRaises(ValueError):v.closing_scope(row)
    def test_closed_worker_r07_target_and_restore(self):
        old_run=v.i.EXE_RUN;old_target=v.c.TARGET;calls=[]
        with patch.object(v.i,'worker',side_effect=lambda task:calls.append((task,v.i.EXE_RUN,v.c.TARGET)) or 0):
            self.assertEqual(v.worker(v.i.task_for(7)),0)
            with self.assertRaises(ValueError):v.worker(v.i.task_for(6))
        self.assertEqual(calls,[(v.i.task_for(7),7,v.b.TARGET)])
        self.assertEqual(v.i.EXE_RUN,old_run);self.assertEqual(v.c.TARGET,old_target)
    def test_exact_original_names_no_filters_or_duplicates(self):
        names=[f'case_{n}' for n in range(249)];text=''.join(n+': test\n' for n in names)
        v.i.validate_listing(text,names)
        for bad in (text.replace('case_0: test\n',''),text+'foreign: test\n',text+'case_0: test\n'):
            with self.assertRaises(ValueError):v.i.validate_listing(bad,names)
