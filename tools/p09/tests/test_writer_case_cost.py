import io
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import run_writer_case_cost as d
class WriterCaseCostTests(unittest.TestCase):
    def test_actual_worker_no_native_sampler_only_pretty_presentation(self):
        class Kernel:
            def GetCurrentProcess(self):return 1
            def IsProcessInJob(self,p,j,out):out._obj.value=True;return True
        calls=[]
        with patch.object(d.c,'Windows',return_value=SimpleNamespace(k=Kernel())), \
                patch.object(d.c.sys,'stdin',io.StringIO('P149_GO\n')),patch.object(d.c.shutil,'which',return_value='fixture-cargo'), \
                patch.object(d,'RAW_CALL',side_effect=lambda a,**kw:calls.append((a,kw)) or 0):
            self.assertEqual(d.worker(d.task_for(6)),0)
        self.assertEqual(calls[0][0],[str(d.c.ROOT/d.full.executable_name()),'--test-threads=1','--format=pretty','--color=never'])
        self.assertEqual(calls[0][1]['env']['RUST_TEST_NOCAPTURE'],'0')
    def test_foreign_task_or_call_cannot_launch(self):
        with patch.object(d.full,'worker',side_effect=AssertionError('NO_LAUNCH')):
            with self.assertRaises(ValueError):d.worker('foreign')
        with patch.object(d,'RAW_CALL',side_effect=AssertionError('NO_LAUNCH')):
            with self.assertRaises(ValueError):d.present_call(['foreign'])
    def test_diagnostic360_never_changes_original_qualification1200(self):
        calls=[]
        with patch.object(d,'RAW_RUN',side_effect=lambda task,dest,seconds:calls.append(seconds) or 0):
            self.assertEqual(d.diagnostic_run(d.task_for(6),'fixture',1200),0)
            with self.assertRaises(ValueError):d.diagnostic_run(d.task_for(6),'fixture',360)
        self.assertEqual(calls,[360]);self.assertEqual(d.original.MAXIMUM_SECONDS,1200)
    def fixture(self):
        capture=d.Capture.__new__(d.Capture);capture.trace=d.observation.CaseTrace(('a','b'))
        capture.lock=threading.Lock();capture.started=d.time.monotonic();capture.error=None;capture.parse_markers=False
        capture.output_limit=32768;capture.buffers={'stdout':bytearray(),'stderr':bytearray()}
        capture.received_bytes={'stdout':0,'stderr':0};capture.pending=bytearray();capture.markers=[];capture.observations=[]
        return capture
    def test_bounded_original_capture_and_partial_case_redaction(self):
        capture=self.fixture();capture._accept('stdout',b'running 2 tests\ntest a ... ok\ntest b ... ')
        row=capture.diagnostics();trace=row['case_progress']
        self.assertEqual(trace['completed_case_count'],1);self.assertEqual(trace['active']['case'],'b')
        self.assertFalse(row['native_Process_query_started']);self.assertFalse(trace['summary_seen'])
        self.assertEqual(row['per_stream_limit_bytes'],32768)
    def test_original_output_guard_and_unknown_case_denial(self):
        capture=self.fixture();capture._accept('stderr',b'x'*32769)
        self.assertEqual(capture.diagnostics()['error_code'],'FULL_CAPTURE_OUTPUT_LIMIT')
        capture=self.fixture();capture._accept('stdout',b'running 2 tests\ntest foreign ... ok\n')
        self.assertEqual(capture.diagnostics()['error_code'],'FULL_CAPTURE_MARKER_SCOPE')
    def test_failed_parent_not_success(self):
        with self.assertRaises(ValueError):d.parent_scope({'state':'FAILED_NOT_ACCEPTED'})
if __name__=='__main__':unittest.main()
