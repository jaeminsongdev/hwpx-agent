import io
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import strict_product_window_v1 as m

class Clock:
    def __init__(self):self.t=0.
    def __call__(self):return self.t
class Capture:
    def __init__(self,p,*args,**kwargs):self.process=p;self.closed=False;self.timeouts=[]
    def communicate(self,timeout):self.timeouts.append(timeout);return ("ok","")
    def progress(self):return ([],[])
    def close(self):self.closed=True
def connected(cls=Capture):
    clock=Clock();p=NS(stdin=io.BytesIO(),pid=1)
    api=m.connect(lambda *a,**k:p,cls,clock)
    return api,clock,p
def started(cls=Capture):
    api,clock,p=connected(cls);api.Popen("same",flag=1)
    p.stdin.write(m.GO);p.stdin.flush();return api,clock,p

class Tests(unittest.TestCase):
    def test_same_process_and_original_pipe_delegate(self):
        api,clock,p=connected();original=p.stdin
        self.assertIs(api.Popen(),p);self.assertIs(p.stdin.original,original)
        self.assertEqual(p.stdin.write(m.GO),8);p.stdin.flush()
        self.assertEqual(original.getvalue(),m.GO)
    def test_no_changed_duplicate_or_unowned_GO(self):
        api,_,p=connected()
        with self.assertRaises(ValueError):m.Input(p.stdin,api.state).write(m.GO)
        api.Popen()
        with self.assertRaises(ValueError):p.stdin.write(b"OTHER")
        p.stdin.write(m.GO)
        with self.assertRaises(ValueError):p.stdin.write(m.GO)
    def test_only_one_process_and_one_exact_capture(self):
        api,_,p=started();cap=api.Capture(p)
        with self.assertRaises(ValueError):api.Popen()
        with self.assertRaises(ValueError):api.Capture(p)
        self.assertEqual(api.state.capture_count,1);cap.close()
    def test_capture_before_GO_rejected(self):
        api,_,p=connected();api.Popen()
        with self.assertRaises(ValueError):api.Capture(p)
    def test_timeout_capped_to_remaining_and_original_result_preserved(self):
        api,clock,p=started();cap=api.Capture(p);clock.t=14.
        self.assertEqual(cap.communicate(100),("ok",""));self.assertEqual(cap.timeouts,[1.])
        self.assertEqual(api.state.diagnostics()["GO_to_complete_capture_elapsed_seconds"],14.)
    def test_exact15_expiry_stops_before_original_wait(self):
        api,clock,p=started();cap=api.Capture(p);clock.t=15.
        with self.assertRaisesRegex(ValueError,"STOP_STRICT_PRODUCT_WINDOW"):cap.communicate(.5)
        self.assertEqual(cap.timeouts,[]);cap.close();self.assertTrue(cap.closed)
    def test_overrun_after_original_wait_not_completion(self):
        clock=Clock()
        class Slow(Capture):
            def communicate(self,timeout):clock.t=16.;return super().communicate(timeout)
        p=NS(stdin=io.BytesIO());api=m.connect(lambda:p,Slow,clock);api.Popen();p.stdin.write(m.GO);cap=api.Capture(p)
        with self.assertRaises(ValueError):cap.communicate(.5)
        self.assertIsNone(api.state.completed);cap.close();self.assertTrue(cap.closed)
    def test_original_capture_error_identity_retained(self):
        error=ValueError("ORIGINAL_CAPTURE_ERROR")
        class Failed(Capture):
            def communicate(self,timeout):raise error
        api,_,p=started(Failed);cap=api.Capture(p)
        with self.assertRaises(ValueError) as ctx:cap.communicate(.5)
        self.assertIs(ctx.exception,error);cap.close()
    def test_timeout_error_not_retried_or_marked_complete(self):
        import subprocess
        error=subprocess.TimeoutExpired("original",.5)
        class Pending(Capture):
            def communicate(self,timeout):raise error
        api,_,p=started(Pending);cap=api.Capture(p)
        with self.assertRaises(subprocess.TimeoutExpired) as ctx:cap.communicate(.5)
        self.assertIs(ctx.exception,error);self.assertIsNone(api.state.completed);cap.close()
    def test_constructor_post_guard_returns_capture_then_errors_for_cleanup(self):
        clock=Clock()
        class SlowInit(Capture):
            def __init__(self,p):super().__init__(p);clock.t=16.
        p=NS(stdin=io.BytesIO());api=m.connect(lambda:p,SlowInit,clock);api.Popen();p.stdin.write(m.GO)
        cap=api.Capture(p)
        with self.assertRaises(ValueError):cap.communicate(.5)
        cap.close();self.assertTrue(cap.closed);self.assertTrue(api.state.diagnostics()["capture_constructor_window_check_failed"])
    def test_cleanup_does_not_check_time_or_close_Job(self):
        api,clock,p=started();cap=api.Capture(p);clock.t=100.;cap.close();p.stdin.close()
        self.assertTrue(cap.closed);self.assertTrue(p.stdin.original.closed)
    def test_invalid_and_backward_clocks_rejected(self):
        for bad in (True,float("nan"),-1.):
            api,clock,p=started();clock.t=bad
            with self.assertRaises(ValueError):api.state.remaining()
    def test_short_GO_write_rejected(self):
        class Short(io.BytesIO):
            def write(self,b):return 1
        p=NS(stdin=Short());api=m.connect(lambda:p,Capture,Clock());api.Popen()
        with self.assertRaises(ValueError):p.stdin.write(m.GO)
    def test_diagnostics_no_acceptance_or_OS_preemption_claim(self):
        api,_,p=started();cap=api.Capture(p);cap.communicate(.5);d=api.state.diagnostics()
        self.assertEqual(d["maximum_GO_to_complete_capture_seconds"],15)
        self.assertIs(d["queue_advance_authorized"],False)
        self.assertIs(d["blocking_OS_latency_hard_preemption_guaranteed"],False);cap.close()

if __name__=="__main__":unittest.main()
