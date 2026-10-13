import copy
import io
import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock,patch
import adaptive_host_cpu_sampler as s

class AdaptiveSamplerTests(unittest.TestCase):
    def sampler(self):
        a=s.Sampler();a.initial_warm();return a

    def test_cannot_poll_without_real_initial_warm(self):
        with self.assertRaises(ValueError):s.Sampler().poll(10,Mock())

    def test_initial_warm_only_once(self):
        with self.assertRaises(ValueError):self.sampler().initial_warm()

    def test_first_two_are_collected_even_when_cold(self):
        a=self.sampler();read=Mock(return_value={'native':'fixture'})
        self.assertEqual([a.poll(10,read)[0] for _ in range(2)],['sample','sample'])
        self.assertEqual(read.call_count,2)

    def test_cold_intervals_do_not_query_or_replay(self):
        a=self.sampler();read=Mock(return_value={'native':'fixture'})
        a.poll(10,read);a.poll(10,read)
        for _ in range(100):self.assertEqual(a.poll(10,read),('cold',None))
        self.assertEqual(read.call_count,2);self.assertEqual(a.summary()['skipped_cold_polls'],100)

    def test_hot_resume_discards_average_across_gap(self):
        a=self.sampler();read=Mock(side_effect=['first','second','stale-gap-average','fresh-hot'])
        a.poll(10,read);a.poll(10,read);a.poll(10,read)
        self.assertEqual(a.poll(90,read),('warm',None))
        self.assertEqual(a.poll(90,read),('sample','fresh-hot'))
        self.assertEqual(a.summary()['discarded_resume_warm_calls'],1)

    def test_cold_after_resume_rewarms_again(self):
        a=self.sampler();read=Mock(return_value='native')
        a.poll(10,read);a.poll(10,read);a.poll(10,read);a.poll(90,read);a.poll(10,read)
        self.assertEqual(a.poll(90,read),('warm',None));self.assertEqual(a.poll(90,read)[0],'sample')
        self.assertEqual(a.summary()['discarded_resume_warm_calls'],2)

    def test_continuously_hot_keeps_real_samples_until_bound(self):
        a=self.sampler();read=Mock(return_value='native')
        self.assertEqual([a.poll(90,read)[0] for _ in range(10)],['sample']*10)
        self.assertEqual(read.call_count,10)

    def test_budget_exhaustion_stops_queries_with_explicit_accounting(self):
        a=self.sampler();read=Mock(return_value='native')
        for _ in range(10):a.poll(90,read)
        for _ in range(20):self.assertEqual(a.poll(90,read),('budget',None))
        self.assertEqual(read.call_count,10);self.assertEqual(a.summary()['skipped_budget_polls'],20)

    def test_counter_error_not_hidden_or_replaced_with_cached_sample(self):
        a=self.sampler();read=Mock(side_effect=ValueError('native_failure'))
        with self.assertRaises(ValueError):a.poll(90,read)

    def test_invalid_host_numbers_fail_closed(self):
        for v in (True,-1,101,float('nan'),float('inf'),'10'):
            with self.assertRaises(ValueError):self.sampler().poll(v,Mock())

    def test_footer_accounting_tamper_is_rejected(self):
        a=self.sampler();a.poll(10,lambda:1);a.poll(10,lambda:2);row=a.summary();row['query_calls']+=1
        with self.assertRaises(ValueError):s.validate_schedule(row)

    def test_original_owned_guards_and_full_acceptance_unchanged(self):
        before=copy.deepcopy(s.original.c.POLICY);s.original.original.require_scope(1200)
        self.assertEqual(s.original.c.POLICY,before);self.assertEqual(s.original.MAX_SAVED,10)
        self.assertLess(sum(s.original.FRAME_BOUNDS.values())+9*s.original.FRAME_BOUNDS['sample']+s.FOOTER_LIMIT,32768)

    def test_direct_callback_uses_one_child_one_query_and_skips_cold_queries(self):
        from test_observed_stored_full import sample
        class Kernel:
            def GetCurrentProcess(self):return 1
            def IsProcessInJob(self,p,j,out):out._obj.value=True;return True
        windows=SimpleNamespace(k=Kernel(),processors=16,sample=lambda:dict(system_cpu_percent=10))
        native=Mock();native.collect.side_effect=[None,sample()['observation'],sample()['observation']]
        process=SimpleNamespace(pid=70,poll=Mock(side_effect=[None]*5+[0]));frames=[];footer=io.StringIO()
        args=[str(s.original.c.ROOT/s.original.original.inventory.build.executable_name(1)),'--test-threads=1','--format=terse']
        with patch.object(s.original.c,'Windows',return_value=windows),patch.object(s.original.group,'Observer',return_value=native), \
                patch.object(s.original.subprocess,'Popen',return_value=process) as child,patch.object(s.time,'sleep'), \
                patch.object(s.os,'getpid',return_value=60),patch.object(s.original,'emit',side_effect=frames.append), \
                patch.object(s.original.sys,'stderr',footer):
            self.assertEqual(s.observed_call(args,cwd=s.original.c.ROOT,stdin=s.original.subprocess.DEVNULL,
                env={'RUST_TEST_NOCAPTURE':'0'}),0)
        child.assert_called_once();native.close.assert_called_once();self.assertEqual(native.collect.call_count,3)
        row=json.loads(footer.getvalue()[len(s.FOOTER):]);self.assertEqual(row['skipped_cold_polls'],4)
        self.assertEqual(frames[-1]['total_samples'],6);self.assertEqual(frames[-1]['saved_samples'],2)

    def test_unowned_callback_cannot_start_counter_or_child(self):
        class Kernel:
            def GetCurrentProcess(self):return 1
            def IsProcessInJob(self,p,j,out):out._obj.value=False;return True
        args=[str(s.original.c.ROOT/s.original.original.inventory.build.executable_name(1)),'--test-threads=1','--format=terse']
        with patch.object(s.original.c,'Windows',return_value=SimpleNamespace(k=Kernel())), \
                patch.object(s.original.group,'Observer') as native,patch.object(s.original.subprocess,'Popen') as child:
            with self.assertRaises(ValueError):s.observed_call(args,cwd=s.original.c.ROOT,
                stdin=s.original.subprocess.DEVNULL,env={'RUST_TEST_NOCAPTURE':'0'})
        native.assert_not_called();child.assert_not_called()

    def fixture_capture(self,footer=True):
        from test_observed_stored_full import capture,ready,sample,frame
        c=capture();c.__class__=s.Capture;c.schedule=None;c.schedule_pending=bytearray();c.schedule_error=None
        end=dict(kind='closed',query_cleanup_confirmed=True,total_samples=6,saved_samples=2,
            high_samples=0,unsaved_high_samples=0,diagnostic_budget_limited=False)
        a=self.sampler();a.poll(10,lambda:1);a.poll(10,lambda:2)
        for _ in range(4):a.poll(10,lambda:None)
        schedule=s.FOOTER+json.dumps(a.summary()).encode()+b'\n'
        data=frame(ready())+frame(sample(1))+frame(sample(2))+(schedule if footer else b'')+frame(end)
        for start in range(0,len(data),37):c._accept('stderr',data[start:start+37])
        return c,schedule

    def test_chunked_footer_requires_real_original_closing_and_all249_parser(self):
        c,_=self.fixture_capture()
        with patch.object(s.original.BASE_CAPTURE,'communicate',return_value=('fixture-all249','')):
            self.assertEqual(c.communicate(1),('fixture-all249',''))
        self.assertIsNone(c.schedule_error);self.assertEqual(c.diagnostics()['adaptive_schedule']['query_calls'],3)

    def test_missing_footer_cannot_promote_success(self):
        c,_=self.fixture_capture(footer=False)
        with patch.object(s.original.BASE_CAPTURE,'communicate',return_value=('fixture-all249','')):
            with self.assertRaises(ValueError):c.communicate(1)

    def test_duplicate_footer_or_duplicate_keys_are_rejected(self):
        c,data=self.fixture_capture();c._accept('stderr',data);self.assertIsNotNone(c.schedule_error)
        with self.assertRaises(ValueError):json.loads('{"host_polls":2,"host_polls":3}',object_pairs_hook=s.unique_pairs)

if __name__=='__main__':unittest.main()
