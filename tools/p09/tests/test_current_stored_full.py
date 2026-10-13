import copy
import io
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import run_current_stored_full as s


class CurrentStoredFullTests(unittest.TestCase):
    def worker(self,go='P149_GO\n',member=True):
        class Kernel:
            def GetCurrentProcess(self):return 1
            def IsProcessInJob(self,p,j,out):out._obj.value=member;return True
        calls=[]
        with patch.object(s.c,'Windows',return_value=SimpleNamespace(k=Kernel())),patch.object(s.c.sys,'stdin',io.StringIO(go)), \
                patch.object(s.c.shutil,'which',return_value='cargo'),patch.object(s.subprocess,'call',side_effect=lambda a,**kw:calls.append((a,kw)) or 0):
            result=s.worker(s.task_for(1))
        return result,calls
    def test_closed_task_and_run(self):
        self.assertEqual(s.run_for(s.task_for(1)),1)
        for run in (True,0,100,'1'):
            with self.assertRaises(ValueError):s.task_for(run)
        with self.assertRaises(ValueError):s.run_for('compression-full-stored-tests')
    def test_original1200_cannot_be_extended(self):
        s.require_scope(1200)
        for seconds in (True,180,600,1201):
            with self.assertRaises(ValueError):s.require_scope(seconds)
    def test_current_profile81_unchanged(self):
        self.assertEqual(len(s.inventory.build.CONFIG),81);s.require_scope(1200)
    def test_fresh_suffix_only_not_old_canonical(self):
        _,calls=self.worker();self.assertEqual(calls[0][0][0],str(s.c.ROOT/s.inventory.build.executable_name(1)))
        self.assertIn('-p152-r01.exe',calls[0][0][0])
    def test_all249_unfiltered_single_thread_terse(self):
        _,calls=self.worker();self.assertEqual(calls[0][0][1:],['--test-threads=1','--format=terse'])
        for flag in ('--exact','--skip','--ignored','--nocapture','--show-output'):
            self.assertNotIn(flag,calls[0][0])
    def test_real_GO_and_Job_required(self):
        for go,member in (('wrong\n',True),('P149_GO\n',False)):
            with self.assertRaises(ValueError):self.worker(go,member)
    def test_inherited_nocapture_cannot_override(self):
        with patch.dict(s.c.os.environ,{'RUST_TEST_NOCAPTURE':'1'}):_,calls=self.worker()
        self.assertEqual(calls[0][1]['env']['RUST_TEST_NOCAPTURE'],'0')
    def test_original_assertion_environment(self):
        _,calls=self.worker();env=calls[0][1]['env']
        for key in ('CARGO_PROFILE_TEST_DEBUG_ASSERTIONS','CARGO_PROFILE_TEST_OVERFLOW_CHECKS'):
            self.assertEqual(env[key],'true')
        self.assertEqual(env['RUST_TEST_THREADS'],'1')
    def test_no_new_Cargo_compile(self):
        _,calls=self.worker();self.assertEqual(len(calls),1);self.assertNotIn('cargo',calls[0][0][0])
    def test_policy_not_mutated(self):
        before=copy.deepcopy(s.c.POLICY);self.worker();self.assertEqual(before,s.c.POLICY)
    def test_immutable_compiled_current249_parent(self):
        self.assertEqual(s.PARENT['sha256'],'a8e3c4385af9dd05819ba85055cbfc84884fccf8b60b9918c107e8b445a65f46')
        self.assertIn('current-stored-inventory.terminal-audit',s.PARENT['path'])
    def test_full_capture_and_exact_complete_validator_unchanged(self):
        self.assertEqual(s.full.FullCapture.__module__,'run_compression_full_stored')
        s.full.validate_output('running 249 tests\ntest result: ok. 249 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;\n')
        with self.assertRaises(ValueError):s.full.validate_output('running 249 tests\n')


if __name__=='__main__':unittest.main()
