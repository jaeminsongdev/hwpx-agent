import copy
import io
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import run_current_r07_full as v

class CurrentR07FullTests(unittest.TestCase):
    def row(self):return json.loads((v.c.ROOT/v.PARENT['path']).read_text(encoding='utf-8'))
    def worker(self,go='P149_GO\n',member=True):
        class Kernel:
            def GetCurrentProcess(self):return 1
            def IsProcessInJob(self,p,j,out):out._obj.value=member;return True
        calls=[]
        with patch.object(v.c,'Windows',return_value=SimpleNamespace(k=Kernel())),patch.object(v.c.sys,'stdin',io.StringIO(go)), \
                patch.object(v.c.shutil,'which',return_value='fixture-cargo'), \
                patch.object(v.original.subprocess,'call',side_effect=lambda a,**kw:calls.append((a,kw)) or 0):
            code=v.worker(v.original.task_for(7))
        return code,calls
    def test_fresh_r07_unfiltered_threads1_terse_no_Cargo(self):
        code,calls=self.worker();self.assertEqual(code,0)
        self.assertEqual(calls[0][0],[str(v.c.ROOT/v.b.executable_name()),'--test-threads=1','--format=terse'])
        self.assertEqual(len(calls),1);self.assertNotIn('cargo',calls[0][0][0])
    def test_GO_Job_and_exact_task_still_required(self):
        for go,member in (('wrong\n',True),('P149_GO\n',False)):
            with self.assertRaises(ValueError):self.worker(go,member)
        with patch.object(v.original,'worker',side_effect=AssertionError('NO_LAUNCH')):
            with self.assertRaises(ValueError):v.worker(v.original.task_for(6))
    def test_original_assertions_nocapture_and_scope_preserved(self):
        with patch.dict(v.c.os.environ,{'RUST_TEST_NOCAPTURE':'1'}):_,calls=self.worker()
        env=calls[0][1]['env']
        for k,val in {'RUST_TEST_NOCAPTURE':'0','RUST_TEST_THREADS':'1','RUSTUP_AUTO_INSTALL':'0',
            'CARGO_PROFILE_TEST_DEBUG_ASSERTIONS':'true','CARGO_PROFILE_TEST_OVERFLOW_CHECKS':'true'}.items():
            self.assertEqual(env[k],val)
        v.original.require_scope(1200)
        with self.assertRaises(ValueError):v.original.require_scope(1201)
    def test_policy_target_and_original_exe_lookup_restored(self):
        policy=copy.deepcopy(v.c.POLICY);target=v.c.TARGET;fn=v.original.inventory.build.executable_name
        self.worker();self.assertEqual(policy,v.c.POLICY);self.assertEqual(target,v.c.TARGET)
        self.assertIs(fn,v.original.inventory.build.executable_name)
    def test_only_current_separate_postclosed249_parent(self):
        expected,exe=v.parent_scope(self.row());self.assertEqual(len(expected),1442);self.assertEqual(exe,v.listing.EXE)
        for key,value in (('state','STOPPED_NOT_ACCEPTED'),('current_compiled249_qualified',False),
            ('original_listing_run_accepted',True),('full249_current_qualified',True),('product_complete',True)):
            row=self.row();row[key]=value
            with self.assertRaises(ValueError):v.parent_scope(row)
    def test_partial_or_old_r06_parent_cannot_authorize(self):
        row=self.row();row['IO']['final_fresh_hashes']-=1
        with self.assertRaises(ValueError):v.parent_scope(row)
        row=self.row();row['compiled_test_executable_pin']['path']=row['compiled_test_executable_pin']['path'].replace('r07','r06')
        with self.assertRaises(ValueError):v.parent_scope(row)
    def test_original249_complete_no_ignored_filtered_failed(self):
        start='running 249 tests\ntest result: ok. '
        v.original.full.validate_output(start+'249 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;\n')
        for wrong in ('248 passed; 0 failed; 1 ignored; 0 measured; 0 filtered out;',
            '248 passed; 0 failed; 0 ignored; 0 measured; 1 filtered out;',
            '249 passed; 1 failed; 0 ignored; 0 measured; 0 filtered out;'):
            with self.assertRaises(ValueError):v.original.full.validate_output(start+wrong+'\n')
