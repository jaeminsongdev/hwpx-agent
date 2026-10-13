import copy
import io
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import run_observed_r07_full as v

class ObservedFullTests(unittest.TestCase):
    def worker(self,go='P149_GO\n',member=True):
        class Kernel:
            def GetCurrentProcess(self):return 1
            def IsProcessInJob(self,p,j,out):out._obj.value=member;return True
        calls=[]
        with patch.object(v.c,'Windows',return_value=SimpleNamespace(k=Kernel())),patch.object(v.c.sys,'stdin',io.StringIO(go)), \
                patch.object(v.c.shutil,'which',return_value='fixture-cargo'), \
                patch.object(v.run.original.subprocess,'call',side_effect=lambda a,**kw:calls.append((a,kw)) or 0):
            code=v.worker(v.run.original.task_for(7))
        return code,calls
    def test_exact_current_r07_pretty_no_filter_no_compile_threads1(self):
        code,calls=self.worker();self.assertEqual(code,0);self.assertEqual(len(calls),1)
        self.assertEqual(calls[0][0],[str(v.c.ROOT/v.run.b.executable_name()),'--test-threads=1','--format=pretty','--color=never'])
    def test_original_GO_and_actual_membership_and_closed_task(self):
        for go,member in (('bad\n',True),('P149_GO\n',False)):
            with self.assertRaises(ValueError):self.worker(go,member)
        with self.assertRaises(ValueError):v.worker(v.run.original.task_for(6))
    def test_original_assertions_overflow_no_capture_override(self):
        with patch.dict(v.c.os.environ,{'RUST_TEST_NOCAPTURE':'1'}):_,calls=self.worker()
        env=calls[0][1]['env']
        for key,val in dict(RUST_TEST_NOCAPTURE='0',RUST_TEST_THREADS='1',RUSTUP_AUTO_INSTALL='0',
                CARGO_PROFILE_TEST_DEBUG_ASSERTIONS='true',CARGO_PROFILE_TEST_OVERFLOW_CHECKS='true').items():
            self.assertEqual(env[key],val)
    def test_original_worker_target_policy_and_lookup_restored(self):
        policy=copy.deepcopy(v.c.POLICY);target=v.c.TARGET;worker=v.run.worker;call=v.run.original.subprocess.call
        self.worker();self.assertEqual(v.c.POLICY,policy);self.assertEqual(v.c.TARGET,target)
        self.assertIs(v.run.worker,worker);self.assertIs(v.run.original.subprocess.call,call)
        v.run.original.require_scope(1200)
        with self.assertRaises(ValueError):v.run.original.require_scope(1201)
    def test_real249_nominal_names_fit_unchanged32768_not_a_slow_or_failure_waiver(self):
        parent=json.loads((v.c.ROOT/v.run.PARENT['path']).read_text(encoding='utf-8'))
        names=parent['source_test_names'];self.assertEqual(len(names),249)
        self.assertLessEqual(v.nominal_output_bytes(names),32768)
        with self.assertRaises(ValueError):v.progress(b'x'*32769,names)
    def test_only_actual_named_pending_line_marks_public_active_not_terse_count(self):
        row=v.progress(b'\nrunning 2 tests\ntest a::one ... ok\ntest a::two ... ',['a::one','a::two'])
        self.assertEqual(row['public_active_test_name'],'a::two');self.assertEqual(row['public_passed_test_count'],1)
        self.assertIsNone(v.progress(b'\nrunning 2 tests\n..',['a::one','a::two'])['public_active_test_name'])
    def test_complete_known_results_and_failed_ignored_duplicate_not_all_ok(self):
        names=['a::one','a::two'];data=b'test a::one ... ok\ntest a::two ... ok\n'
        row=v.progress(data,names);self.assertTrue(row['public_all_expected_results_seen'])
        self.assertEqual(row['public_passed_test_count'],2);self.assertIsNone(row['public_active_test_name'])
        self.assertEqual(v.progress(data.replace(b'two ... ok',b'two ... FAILED'),names)['public_failed_test_count'],1)
        self.assertEqual(v.progress(data.replace(b'two ... ok',b'two ... ignored'),names)['public_ignored_test_count'],1)
        self.assertTrue(v.progress(data+data,names)['public_duplicate_result_seen'])
    def test_unknown_private_and_panic_log_content_not_persisted(self):
        sentinel='DO_NOT_PERSIST_PRIVATE_VALUE';data=f'test {sentinel} ... \npanic: {sentinel}\ntest public::one ... ok\n'.encode()
        row=v.progress(data,['public::one']);self.assertNotIn(sentinel,json.dumps(row));self.assertIsNone(row['public_active_test_name'])
        self.assertFalse(row['raw_logs_or_unknown_names_saved'])
    def test_original_full_validator_retained_no_failed_ignored_filtered_summary(self):
        banner='running 249 tests\ntest result: ok. '
        v.run.original.full.validate_output(banner+'249 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;\n')
        for wrong in ('248 passed; 0 failed; 1 ignored; 0 measured; 0 filtered out;',
                '248 passed; 0 failed; 0 ignored; 0 measured; 1 filtered out;',
                '249 passed; 1 failed; 0 ignored; 0 measured; 0 filtered out;'):
            with self.assertRaises(ValueError):v.run.original.full.validate_output(banner+wrong+'\n')
