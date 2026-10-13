import copy
import io
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import run_writer_current_full as d
class WriterFullTests(unittest.TestCase):
    def worker(self,go='P149_GO\n',member=True):
        class Kernel:
            def GetCurrentProcess(self):return 1
            def IsProcessInJob(self,p,j,out):out._obj.value=member;return True
        calls=[]
        with patch.object(d.c,'Windows',return_value=SimpleNamespace(k=Kernel())), \
                patch.object(d.c.sys,'stdin',io.StringIO(go)),patch.object(d.c.shutil,'which',return_value='fixture-cargo'), \
                patch.object(d.b.subprocess,'call',side_effect=lambda a,**kw:calls.append((a,kw)) or 0):
            result=d.worker(d.original.task_for(6))
        return result,calls
    def test_actual_original_worker_exact_current_unfiltered_handoff(self):
        code,calls=self.worker();self.assertEqual(code,0)
        self.assertEqual(calls[0][0],[str(d.c.ROOT/d.executable_name()),'--test-threads=1','--format=terse'])
        self.assertTrue(calls[0][0][0].endswith('p152-r06.exe'))
    def test_GO_and_Job_required(self):
        for go,member in (('wrong\n',True),('P149_GO\n',False)):
            with self.assertRaises(ValueError):self.worker(go,member)
    def test_foreign_task_no_launch(self):
        with patch.object(d.original,'worker',side_effect=AssertionError('NO_LAUNCH')):
            with self.assertRaises(ValueError):d.worker(d.original.task_for(4))
    def test_profile_checks_environment_no_override(self):
        with patch.dict(d.c.os.environ,{'RUST_TEST_NOCAPTURE':'1'}):_,calls=self.worker()
        env=calls[0][1]['env']
        for k,v in {'RUST_TEST_NOCAPTURE':'0','RUST_TEST_THREADS':'1','RUSTUP_AUTO_INSTALL':'0',
            'CARGO_PROFILE_TEST_DEBUG_ASSERTIONS':'true','CARGO_PROFILE_TEST_OVERFLOW_CHECKS':'true'}.items():self.assertEqual(env[k],v)
    def test_original_full_scope_and_policy_restored(self):
        policy=copy.deepcopy(d.c.POLICY);target=d.c.TARGET;name=d.b.executable_name
        self.worker();self.assertEqual(policy,d.c.POLICY);self.assertEqual(target,d.c.TARGET);self.assertIs(name,d.b.executable_name)
        d.original.require_scope(1200)
        with self.assertRaises(ValueError):d.original.require_scope(1201)
    def test_complete249_zero_ignored_and_filtered_required(self):
        prefix='running 249 tests\ntest result: ok. '
        d.original.full.validate_output(prefix+'249 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;\n')
        for wrong in ('248 passed; 0 failed; 1 ignored; 0 measured; 0 filtered out;',
            '248 passed; 0 failed; 0 ignored; 0 measured; 1 filtered out;','249 passed; 1 failed; 0 ignored; 0 measured; 0 filtered out;'):
            with self.assertRaises(ValueError):d.original.full.validate_output(prefix+wrong+'\n')
    def test_stale_or_incomplete_parent_denied(self):
        for state in ('FAILED_NOT_ACCEPTED','PASS_SOURCE_XML_CURRENT_COMPILED249_INVENTORY_CLOSING_ONLY_NOT_FULL_RUNTIME_OR_GATE'):
            with self.assertRaises(ValueError):d.parent_scope({'state':state})
if __name__=='__main__':unittest.main()
