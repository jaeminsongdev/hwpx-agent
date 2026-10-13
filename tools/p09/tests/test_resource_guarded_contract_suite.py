"""작은 합성 계약검사. Native/제품/자원 실측 수용 증거가 아니다."""
import io
import unittest
from unittest.mock import patch
import resource_guarded_contract_suite as m


class Tests(unittest.TestCase):
    def suite(self, events, count=2, failure=False, skipped=False):
        class Case(unittest.TestCase):
            def setUp(self): events.append('setup')
            def tearDown(self): events.append('teardown')
            def runTest(self):
                events.append('body')
                if skipped: self.skipTest('synthetic')
                if failure: self.fail('synthetic')
        return unittest.TestSuite(Case() for _ in range(count))

    def run_bound(self, checkpoint, suite, **options):
        with m.bind(checkpoint) as stats:
            result = unittest.TextTestRunner(stream=io.StringIO(), **options).run(suite)
        return result, stats.summary()

    def test_exact_order(self):
        events=[]
        result, stats=self.run_bound(lambda:events.append('guard'),self.suite(events))
        self.assertTrue(result.wasSuccessful());self.assertEqual(result.testsRun,2)
        self.assertEqual(events,['guard','guard','setup','body','teardown','guard',
                                 'guard','setup','body','teardown','guard','guard'])
        self.assertEqual(stats['successful_after_test_checks'],2)

    def test_before_setUp_STOP(self):
        events=[];calls=[]
        def guard():
            calls.append(1)
            if len(calls)==2: raise ValueError('STOP_SUSTAINED_SYSTEM_CPU')
        with self.assertRaisesRegex(ValueError,'STOP_SUSTAINED_SYSTEM_CPU'):
            self.run_bound(guard,self.suite(events))
        self.assertEqual(events,[])

    def test_after_test_STOP_no_next(self):
        events=[];calls=[]
        def guard():
            calls.append(1)
            if len(calls)==3: raise ValueError('STOP_SUSTAINED_SYSTEM_CPU')
        with self.assertRaisesRegex(ValueError,'STOP_SUSTAINED_SYSTEM_CPU'):
            self.run_bound(guard,self.suite(events))
        self.assertEqual(events,['setup','body','teardown'])

    def test_runner_admission_STOP(self):
        events=[]
        def guard(): raise ValueError('STOP_LOW_RAM')
        with self.assertRaisesRegex(ValueError,'STOP_LOW_RAM'):
            self.run_bound(guard,self.suite(events))
        self.assertEqual(events,[])

    def test_runner_completion_STOP(self):
        events=[];calls=[]
        def guard():
            calls.append(1)
            if len(calls)==4: raise ValueError('STOP_SQL_IO_SCOPE_TIME')
        with self.assertRaisesRegex(ValueError,'STOP_SQL_IO_SCOPE_TIME'):
            self.run_bound(guard,self.suite(events,1))
        self.assertEqual(events,['setup','body','teardown'])

    def test_failure_not_promoted(self):
        result,stats=self.run_bound(lambda:None,self.suite([],failure=True))
        self.assertFalse(result.wasSuccessful());self.assertEqual(len(result.failures),2)
        self.assertEqual(stats['started_tests'],2)

    def test_skip_not_hidden(self):
        result,_=self.run_bound(lambda:None,self.suite([],skipped=True))
        self.assertEqual(len(result.skipped),2);self.assertEqual(result.testsRun,2)

    def test_failfast_preserved(self):
        result,stats=self.run_bound(lambda:None,self.suite([],failure=True),failfast=True)
        self.assertEqual(result.testsRun,1);self.assertEqual(stats['stopped_tests'],1)

    def test_runner_restored_on_success(self):
        before=unittest.TextTestRunner
        self.run_bound(lambda:None,self.suite([]))
        self.assertIs(before,unittest.TextTestRunner);self.assertFalse(m._ACTIVE)

    def test_runner_restored_on_STOP(self):
        before=unittest.TextTestRunner
        def guard(): raise ValueError('STOP_SUSTAINED_SYSTEM_CPU')
        with self.assertRaises(ValueError): self.run_bound(guard,self.suite([]))
        self.assertIs(before,unittest.TextTestRunner);self.assertFalse(m._ACTIVE)

    def test_invalid_checkpoint(self):
        with self.assertRaises(ValueError):
            with m.bind(None): self.fail('unreachable')
        self.assertFalse(m._ACTIVE)

    def test_nested_binding_rejected(self):
        with m.bind(lambda:None):
            with self.assertRaises(ValueError):
                with m.bind(lambda:None): self.fail('unreachable')

    def test_changed_runner_rejected_without_overwrite(self):
        replacement=object()
        with patch.object(unittest,'TextTestRunner',replacement):
            with self.assertRaises(ValueError):
                with m.bind(lambda:None): self.fail('unreachable')
            self.assertIs(unittest.TextTestRunner,replacement)

    def test_multiple_runners_accounted(self):
        with m.bind(lambda:None) as stats:
            for _ in range(2):
                result=unittest.TextTestRunner(stream=io.StringIO()).run(self.suite([]))
                self.assertEqual(result.testsRun,2)
        row=stats.summary();self.assertEqual(row['started_tests'],4)
        self.assertEqual(row['runner_calls'],2);self.assertEqual(row['returned_runner_calls'],2)

    def test_no_new_process_thread_sleep(self):
        with patch('subprocess.Popen',side_effect=AssertionError('NO_CHILD')), \
             patch('subprocess.run',side_effect=AssertionError('NO_CHILD')), \
             patch('threading.Thread.start',side_effect=AssertionError('NO_THREAD')), \
             patch('time.sleep',side_effect=AssertionError('NO_NEW_SLEEP')):
            result,stats=self.run_bound(lambda:None,self.suite([]))
        self.assertTrue(result.wasSuccessful())
        self.assertFalse(stats['new_sampler_or_thread_or_sleep_started'])

    def test_custom_result_preserved(self):
        calls=[]
        class Result(unittest.TextTestResult):
            def addSuccess(self,test): calls.append('success');super().addSuccess(test)
        result,_=self.run_bound(lambda:None,self.suite([]),resultclass=Result)
        self.assertIsInstance(result,Result);self.assertEqual(calls,['success','success'])

    def test_empty_suite_checks_twice(self):
        calls=[];result,stats=self.run_bound(lambda:calls.append(1),unittest.TestSuite())
        self.assertEqual(result.testsRun,0);self.assertEqual(len(calls),2)
        self.assertEqual(stats['started_tests'],0)

    def test_stopped_counts_not_acceptance(self):
        events=[];calls=[]
        def guard():
            calls.append(1)
            if len(calls)==3: raise ValueError('STOP_SUSTAINED_SYSTEM_CPU')
        with m.bind(guard) as stats:
            with self.assertRaises(ValueError):
                unittest.TextTestRunner(stream=io.StringIO()).run(self.suite(events))
        row=stats.summary();self.assertEqual(row['stopped_tests'],1)
        self.assertEqual(row['successful_after_test_checks'],0)
        self.assertEqual(row['returned_runner_calls'],0)

    def test_exception_inside_binding_restores(self):
        before=unittest.TextTestRunner
        with self.assertRaises(RuntimeError):
            with m.bind(lambda:None): raise RuntimeError('synthetic')
        self.assertIs(unittest.TextTestRunner,before);self.assertFalse(m._ACTIVE)

    def test_summary_no_acceptance_claim(self):
        _,row=self.run_bound(lambda:None,self.suite([]))
        self.assertTrue(row['test_results_are_not_product_acceptance'])
        self.assertTrue(row['original_unittest_results_preserved'])
        self.assertFalse(row['original_guard_or_test_coverage_relaxed'])

    def test_keyboard_interrupt_restores(self):
        def guard(): raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):self.run_bound(guard,self.suite([]))
        self.assertIs(unittest.TextTestRunner,m._ORIGINAL_RUNNER);self.assertFalse(m._ACTIVE)
