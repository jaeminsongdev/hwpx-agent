import io
import unittest
from types import SimpleNamespace as NS

MODULE=None
WINDOW=None


class Clock:
    def __init__(self):self.value=0.
    def __call__(self):return self.value


class Event:
    def __init__(self,clock,after=0):self.clock=clock;self.after=after;self.calls=0;self.signals=0
    def wait(self,milliseconds):
        self.calls+=1;self.clock.value+=milliseconds/1000
        return self.clock.value>=self.after
    def signal_and_close(self):self.signals+=1


def fixture(*,after=0,verify=lambda p:True,checkpoint=lambda:None,seconds=15):
    clock=Clock();event=Event(clock,after);pipe=io.BytesIO();process=NS(pid=123,poll=lambda:None)
    gate=MODULE.Gate(pipe,event,process,verify,checkpoint,clock=clock,seconds=seconds)
    return gate,clock,event,pipe,process


class Tests(unittest.TestCase):
    def test_exact_GO_and_original_flush_delegated(self):
        gate,_,_,pipe,_=fixture(after=.2)
        self.assertEqual(gate.write(MODULE.GO),8);gate.flush()
        self.assertEqual(pipe.getvalue(),MODULE.GO);self.assertTrue(gate.ready)

    def test_timeout_prevents_any_original_write_and_latches(self):
        gate,_,_,pipe,_=fixture(after=1,seconds=.1)
        with self.assertRaisesRegex(ValueError,'PREPARATION_TIMEOUT'):gate.write(MODULE.GO)
        self.assertEqual(pipe.getvalue(),b'');self.assertTrue(gate.stopped)
        with self.assertRaises(ValueError):gate.write(MODULE.GO)

    def test_exact_deadline_ready_is_rejected(self):
        gate,_,_,pipe,_=fixture(after=.1,seconds=.1)
        with self.assertRaisesRegex(ValueError,'PREPARATION_TIMEOUT'):gate.write(MODULE.GO)
        self.assertEqual(pipe.getvalue(),b'')

    def test_unowned_worker_rejected_before_event_wait(self):
        gate,_,event,pipe,_=fixture(verify=lambda p:False)
        with self.assertRaisesRegex(ValueError,'OWNED_JOB'):gate.write(MODULE.GO)
        self.assertEqual(event.calls,0);self.assertEqual(pipe.getvalue(),b'')

    def test_worker_exit_after_signal_prevents_GO(self):
        gate,_,event,pipe,process=fixture()
        original=event.wait
        def wait(ms):original(ms);process.poll=lambda:0;return True
        event.wait=wait
        with self.assertRaisesRegex(ValueError,'OWNED_JOB'):gate.write(MODULE.GO)
        self.assertEqual(pipe.getvalue(),b'')

    def test_readiness_does_not_override_resource_guard(self):
        def reject():raise ValueError('RESOURCE_STOP')
        gate,_,event,pipe,_=fixture(checkpoint=reject)
        with self.assertRaisesRegex(ValueError,'RESOURCE_STOP'):gate.write(MODULE.GO)
        self.assertEqual(event.calls,0);self.assertEqual(pipe.getvalue(),b'')

    def test_post_signal_checkpoint_still_runs(self):
        calls=[]
        def check():
            calls.append(1)
            if len(calls)==2:raise ValueError('RESOURCE_STOP')
        gate,_,_,pipe,_=fixture(checkpoint=check)
        with self.assertRaisesRegex(ValueError,'RESOURCE_STOP'):gate.write(MODULE.GO)
        self.assertEqual(pipe.getvalue(),b'')

    def test_no_duplicate_GO(self):
        gate,_,_,pipe,_=fixture();gate.write(MODULE.GO)
        with self.assertRaises(ValueError):gate.write(MODULE.GO)
        self.assertEqual(pipe.getvalue(),MODULE.GO)

    def test_changed_GO_and_flush_before_GO_rejected(self):
        gate,_,_,pipe,_=fixture()
        with self.assertRaises(ValueError):gate.flush()
        with self.assertRaises(ValueError):gate.write(b'OTHER')
        self.assertTrue(gate.stopped);self.assertEqual(pipe.getvalue(),b'')

    def test_nonboolean_event_or_ownership_is_not_success(self):
        for target in ('event','ownership'):
            gate,_,event,pipe,_=fixture()
            if target=='event':event.wait=lambda ms:1
            else:gate.verify_owned=lambda p:1
            with self.assertRaises(ValueError):gate.write(MODULE.GO)
            self.assertEqual(pipe.getvalue(),b'')

    def test_invalid_or_backwards_clock_stops(self):
        for value in (float('nan'),True,-1):
            gate,clock,event,pipe,_=fixture()
            def wait(ms):clock.value=value;return True
            event.wait=wait
            with self.assertRaises(ValueError):gate.write(MODULE.GO)
            self.assertEqual(pipe.getvalue(),b'')

    def test_time_spent_in_guard_is_counted(self):
        gate,clock,_,pipe,_=fixture(seconds=.1)
        gate.checkpoint=lambda:setattr(clock,'value',clock.value+.11)
        with self.assertRaisesRegex(ValueError,'PREPARATION_TIMEOUT'):gate.write(MODULE.GO)
        self.assertEqual(pipe.getvalue(),b'')

    def test_short_write_and_flush_error_latch_but_cleanup_delegates(self):
        gate,_,_,_,_=fixture();closed=[]
        gate.original=NS(write=lambda value:1,close=lambda:closed.append(1))
        with self.assertRaises(ValueError):gate.write(MODULE.GO)
        gate.close();self.assertEqual(closed,[1]);self.assertTrue(gate.stopped)
        gate,_,_,_,_=fixture()
        def fail():raise OSError('PIPE_FAILURE')
        gate.original=NS(write=lambda value:len(value),flush=fail)
        gate.write(MODULE.GO)
        with self.assertRaises(OSError):gate.flush()
        self.assertTrue(gate.stopped)

    def test_readiness_reader_never_invents_or_rewrites_GO(self):
        for text in ('','OTHER\n','P149_GO\n'):
            event=Event(Clock());reader=MODULE.ReadyReader(io.StringIO(text),event)
            self.assertEqual(reader.readline(),text);self.assertEqual(event.signals,1)
            with self.assertRaises(ValueError):reader.readline()

    def test_reader_signals_before_original_blocking_read(self):
        event=Event(Clock())
        def read(*args,**kwargs):self.assertEqual(event.signals,1);return 'unchanged'
        reader=MODULE.ReadyReader(NS(readline=read),event)
        self.assertEqual(reader.readline(1),'unchanged')

    def test_bound_cannot_be_enlarged_and_arguments_are_explicit(self):
        for seconds in (0,-1,True,float('nan'),16):
            with self.assertRaises(ValueError):fixture(seconds=seconds)

    def test_original_strict10_starts_only_at_actual_write_and_still_expires(self):
        clock=Clock();pipe=io.BytesIO();process=NS(stdin=pipe,pid=123,poll=lambda:None)
        class Capture:
            def __init__(self,p):pass
            def communicate(self,timeout):return ('same','result')
        api=WINDOW.connect(lambda:process,Capture,clock)
        api.Popen();original_input=process.stdin;event=Event(clock,after=2)
        gate=MODULE.Gate(original_input,event,process,lambda p:True,lambda:None,clock=clock)
        gate.write(MODULE.GO);gate.flush()
        self.assertGreaterEqual(clock.value,2);self.assertEqual(api.state.started,clock.value)
        self.assertEqual(api.state.go_writes,1);self.assertEqual(pipe.getvalue(),MODULE.GO)
        capture=api.Capture(process);clock.value+=10
        with self.assertRaisesRegex(ValueError,'STOP_STRICT_PRODUCT_WINDOW'):capture.communicate(1)
        self.assertIsNone(api.state.completed)
