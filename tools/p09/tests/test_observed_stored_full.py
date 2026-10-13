import copy
import io
import json
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import run_observed_stored_full as s
from test_host_cpu_groups import select


def ready():return dict(kind='ready',worker_pid=60,test_pid=70,processor_count=16)
def sample(sequence=1):
    return dict(kind='sample',worker_pid=60,test_pid=70,sequence=sequence,
        observed_at=f'2026-10-07T01:00:{sequence:02}+00:00',collect_seconds=.008,system_cpu_percent=99.0,
        observation=select({'msmpeng':[1500.],'chatgpt':[16.,32.]},{'msmpeng':[50.],'chatgpt':[51.,52.]})[0])
def closed(count=1):return dict(kind='closed',query_cleanup_confirmed=True,total_samples=count,saved_samples=count,
    high_samples=count,unsaved_high_samples=0,diagnostic_budget_limited=False)
def frame(row):return s.MARKER+json.dumps(row,separators=(',',':')).encode()+b'\n'


def capture():
    # Pure fake capture: never start pipe threads/native calls/child processes.
    c=object.__new__(s.Capture);c.lock=threading.Lock();c.process=SimpleNamespace(pid=60,returncode=0)
    c.records=[];c.observer_pending=bytearray();c.observer_error=None;c.observer_closed=False
    c.accepted=False;c.received_bytes={'stdout':0,'stderr':0};c.buffers={'stdout':bytearray(),'stderr':bytearray()}
    c.error=None;c.output_limit=32768;c.parse_markers=False;c.pending=bytearray();c.markers=[];c.observations=[]
    return c


class ObservedStoredFullTests(unittest.TestCase):
    def test_task_closed_and_different_generation(self):
        self.assertEqual(s.run_for(s.task_for(1)),1)
        for task in ('p152-current-stored-full-r01-tests','p154-observed-full-r00-tests','p154-observed-full-r100-tests',None):
            with self.assertRaises(ValueError):s.run_for(task)
    def test_original1200_all249_capture_and_policy(self):
        s.original.require_scope(1200);self.assertEqual(s.original.MAXIMUM_SECONDS,1200)
        self.assertEqual(s.c.POLICY['output_limit_bytes_per_stream'],32768)
        self.assertEqual(s.c.POLICY['emergency_cpu_percent'],98)
        self.assertEqual(s.c.POLICY['emergency_cpu_consecutive_samples'],4)
        s.original.full.validate_output('running 249 tests\ntest result: ok. 249 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;')
    def test_original_worker_GO_owned_environment_no_filter(self):
        class Kernel:
            def GetCurrentProcess(self):return 1
            def IsProcessInJob(self,p,j,out):out._obj.value=True;return True
        with patch.object(s.c.sys,'stdin',io.StringIO('P149_GO\n')),patch.object(s.c,'Windows',return_value=SimpleNamespace(k=Kernel())), \
                patch.object(s.c.shutil,'which',return_value='cargo'),patch.object(s,'observed_call',return_value=0) as called:
            self.assertEqual(s.worker(s.task_for(1)),0)
        args=called.call_args.args[0];kw=called.call_args.kwargs
        self.assertEqual(args,[str(s.c.ROOT/s.original.inventory.build.executable_name(1)),'--test-threads=1','--format=terse'])
        self.assertEqual(kw['env']['RUST_TEST_NOCAPTURE'],'0');self.assertEqual(kw['cwd'],s.c.ROOT)
    def test_GO_before_native_or_EXE(self):
        with patch.object(s.c.sys,'stdin',io.StringIO('wrong\n')),patch.object(s.group,'Observer') as native:
            with self.assertRaises(ValueError):s.worker(s.task_for(1))
            native.assert_not_called()
    def test_observed_direct_call_exact_scope(self):
        for args in (['cargo','test'],['old.exe','--list'],[str(s.c.ROOT/s.original.inventory.build.executable_name(1)),'--skip','one']):
            with self.assertRaisesRegex(ValueError,'EXACT_EXE'):s.observed_call(args,cwd=s.c.ROOT,stdin=s.subprocess.DEVNULL,env={})
    def test_native_only_after_confirmed_job(self):
        class Kernel:
            def GetCurrentProcess(self):return 1
            def IsProcessInJob(self,p,j,out):out._obj.value=False;return True
        args=[str(s.c.ROOT/s.original.inventory.build.executable_name(1)),'--test-threads=1','--format=terse']
        with patch.object(s.c,'Windows',return_value=SimpleNamespace(k=Kernel())),patch.object(s.group,'Observer') as native:
            with self.assertRaisesRegex(ValueError,'OWNED_BEFORE_QUERY'):s.observed_call(args,cwd=s.c.ROOT,stdin=s.subprocess.DEVNULL,env={'RUST_TEST_NOCAPTURE':'0'})
            native.assert_not_called()
    def test_record_closed_schema_no_private_fields(self):
        for row in (ready(),sample(),closed()):s.valid_record(row,60)
        row=sample();row['private_path']='not_saved'
        with self.assertRaises(ValueError):s.valid_record(row)
    def test_multi_core_not_clamped_and_group_not_fake_PID(self):
        row=s.valid_record(sample());top=row['observation']['top']
        self.assertEqual(top[0]['processor_time_raw_percent'],1500);self.assertEqual(top[0]['machine_cpu_percent'],93.75)
        self.assertIsNone(top[1]['pid']);self.assertEqual(top[1]['identity_granularity'],'group')
    def test_invalid_owner_and_sequence(self):
        for mutate in (lambda r:r.update(worker_pid=61),lambda r:r.update(test_pid=60),lambda r:r.update(sequence=11),lambda r:r.update(system_cpu_percent=float('nan'))):
            row=sample();mutate(row)
            with self.assertRaises(ValueError):s.valid_record(row,60)
    def test_chunked_capture_ready_sample_closed(self):
        c=capture();data=frame(ready())+frame(sample())+frame(closed())
        for start in range(0,len(data),37):c._accept('stderr',data[start:start+37])
        self.assertIsNone(c.observer_error);self.assertTrue(c.observer_closed);self.assertEqual(len(c.records),3)
        d=c.diagnostics();self.assertFalse(d['causal_attribution']);self.assertFalse(d['raw_names_paths_commands_saved'])
        self.assertNotIn('private',json.dumps(d))
    def test_duplicate_ready_and_after_close_rejected(self):
        for data in (frame(ready())*2,frame(ready())+frame(sample())+frame(closed())+frame(sample(2))):
            c=capture();c._accept('stderr',data);self.assertEqual(c.observer_error,'P154_CLOSED_DIAGNOSTIC_REJECTED')
    def test_missing_ready_bad_json_unbound_pid_rejected(self):
        row=sample();row['test_pid']=71
        for data in (frame(sample()),s.MARKER+b'{bad}\n',frame(ready())+frame(row)):
            c=capture();c._accept('stderr',data);self.assertIsNotNone(c.observer_error)
    def test_frame_bound_original_stream_limit(self):
        c=capture();c._accept('stderr',s.MARKER+b'x'*s.MAX_FRAME)
        self.assertIsNotNone(c.observer_error);self.assertEqual(c.output_limit,32768)
        self.assertLess(s.MAX_FRAME*s.MAX_SAVED+sum(s.FRAME_BOUNDS[k] for k in ('ready','budget','closed')),32768)
    def test_no_saved_raw_panic_text(self):
        c=capture();c._accept('stderr',b'private panic text\n'+frame(ready()))
        self.assertEqual(len(c.records),1);self.assertNotIn('private panic text',json.dumps(c.diagnostics()))
    def test_diagnostic_budget_is_explicit_not_test_filter(self):
        c=capture();c._accept('stderr',frame(ready()))
        for index in range(1,11):c._accept('stderr',frame(sample(index)))
        c._accept('stderr',frame(dict(kind='budget',saved_samples=10,diagnostic_budget_limited=True)))
        end=closed(10);end.update(total_samples=12,high_samples=12,unsaved_high_samples=2,diagnostic_budget_limited=True)
        c._accept('stderr',frame(end));self.assertTrue(c.observer_closed);self.assertIsNone(c.observer_error)
        self.assertEqual(len([r for r in c.records if r['kind']=='sample']),10)
    def test_success_requires_explicit_query_close(self):
        c=capture();c._accept('stderr',frame(ready())+frame(sample()))
        with patch.object(s.BASE_CAPTURE,'communicate',return_value=('all249','')):
            with self.assertRaisesRegex(ValueError,'QUERY_CLOSING_REQUIRED'):c.communicate(1)
        c._accept('stderr',frame(closed()))
        with patch.object(s.BASE_CAPTURE,'communicate',return_value=('all249','')):self.assertEqual(c.communicate(1),('all249',''))
    def test_schema_adapter_never_persists_artificial_samples(self):
        row=sample();before=copy.deepcopy(row);s.valid_record(row)
        self.assertEqual(row,before);self.assertNotIn('samples',row)
    def test_threshold_diagnostic_not_emergency_override(self):
        self.assertEqual(s.HOT_DIAGNOSTIC_PERCENT,80);self.assertEqual(s.OBSERVATION_SECONDS,1)
        self.assertEqual(s.c.POLICY['emergency_cpu_percent'],98)


if __name__=='__main__':unittest.main()
