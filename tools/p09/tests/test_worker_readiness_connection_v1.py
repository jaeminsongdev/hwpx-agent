import io
import unittest
from types import SimpleNamespace as NS

MODULE=None
PROTOCOL=None
WINDOW=None


class Clock:
    def __init__(self):self.value=0.
    def __call__(self):return self.value


class Event:
    def __init__(self,clock):self.clock=clock;self.closed=False;self.closes=0
    def wait(self,ms):self.clock.value+=.1;return True
    def close(self):self.closed=True;self.closes+=1


class Capture:
    def __init__(self,process):self.process=process;process.stdin.close()
    def communicate(self,timeout):return ('exact','result')


def setup(*,launch=None,verify=lambda p:True,checkpoint=lambda:None):
    clock=Clock();event=Event(clock);pipe=io.BytesIO();process=NS(stdin=pipe,pid=123,poll=lambda:None)
    calls=[]
    def factory(*args,**kwargs):calls.append((args,kwargs));return process
    def default_launch(original,actual_event,*args,**kwargs):
        assert actual_event is event
        return original(*args,**kwargs)
    api=MODULE.connect(WINDOW,PROTOCOL,factory,Capture,default_launch if launch is None else launch,
        verify,checkpoint,event_factory=lambda:event,clock=clock)
    return api,clock,event,pipe,process,calls


def model():
    return dict(unchanged_lock_deadline_seconds=600,unallocated_margin_seconds=60,
        product_allowance_seconds=10,strict_GO_to_complete_capture_window_seconds=10,
        selected_acquisition_rate_per_second=14,aggregate_envelope_decoder_allowance_seconds=5.0,
        actual_two_pass_byte_reads_retained=True,predicted_runtime_combined_seconds=579.)


class Tests(unittest.TestCase):
    def test_original_factory_arguments_and_same_process_retained(self):
        api,_,_,_,process,calls=setup()
        self.assertIs(api.Popen('original-argv',flag=7),process)
        self.assertEqual(calls,[(('original-argv',),{'flag':7})])
        process.stdin.close()

    def test_gate_outside_actual_window_input_and_real_GO_clock(self):
        api,clock,event,pipe,process,_=setup();api.Popen()
        self.assertIs(process.stdin.original.state,api.original_binding.state)
        process.stdin.write(PROTOCOL.GO);process.stdin.flush()
        self.assertEqual(api.state.started,.1);self.assertEqual(pipe.getvalue(),PROTOCOL.GO)
        self.assertTrue(api.state.diagnostics()['readiness_outside_actual_window_input'])
        cap=api.Capture(process);self.assertTrue(event.closed)
        self.assertEqual(cap.communicate(1),('exact','result'))
        self.assertTrue(api.state.completed is not None)

    def test_original10_still_stops_capture(self):
        api,clock,_,_,process,_=setup();api.Popen();process.stdin.write(PROTOCOL.GO)
        cap=api.Capture(process);clock.value+=10
        with self.assertRaisesRegex(ValueError,'STOP_STRICT_PRODUCT_WINDOW'):cap.communicate(1)

    def test_preGO_failure_can_close_event_and_original_input(self):
        api,_,event,pipe,process,_=setup(verify=lambda p:False);api.Popen()
        with self.assertRaises(ValueError):process.stdin.write(PROTOCOL.GO)
        self.assertEqual(api.state.go_writes,0);self.assertEqual(pipe.getvalue(),b'')
        process.stdin.close();self.assertTrue(event.closed);self.assertTrue(pipe.closed)

    def test_launch_failure_closes_event_and_no_automatic_retry(self):
        def fail(*args,**kwargs):raise OSError('LAUNCH_FAILURE')
        api,_,event,_,_,_=setup(launch=fail)
        with self.assertRaises(OSError):api.Popen()
        self.assertTrue(event.closed)
        with self.assertRaises(ValueError):api.Popen()

    def test_postspawn_setup_failure_is_deferred_until_after_process_return(self):
        api,_,event,_,process,_=setup();process.pid=True
        self.assertIs(api.Popen(),process)
        with self.assertRaises(ValueError):process.stdin.write(PROTOCOL.GO)
        process.stdin.close();self.assertTrue(event.closed)
        self.assertEqual(api.state.go_writes,0)

    def test_no_capture_before_original_GO(self):
        api,_,_,_,process,_=setup();api.Popen()
        with self.assertRaises(ValueError):api.Capture(process)
        process.stdin.close()

    def test_same_capture_state_and_original_default_window_not_changed(self):
        before=WINDOW.SECONDS;api,_,_,_,process,_=setup();api.Popen()
        self.assertIs(api.Capture,api.original_binding.Capture)
        self.assertEqual(WINDOW.SECONDS,before);self.assertEqual(before,10)
        process.stdin.close()

    def test_budget_adds_all_costs_without_margin_or_assignment_credit(self):
        base=model();before=dict(base)
        row=MODULE.budget_delta(base,additional_acquisitions=14,additional_other_bytes=1048576,
            additional_inventory_checkpoints=20)
        self.assertEqual(row['predicted_seconds'],597.)
        self.assertEqual(base,before);self.assertFalse(row['GO_authorized'])

    def test_budget_600_or_more_is_rejected(self):
        for extra in (6,7):
            with self.assertRaisesRegex(ValueError,'OUTSIDE_ORIGINAL600'):
                MODULE.budget_delta(model(),additional_acquisitions=0,additional_other_bytes=extra*1048576,
                    additional_inventory_checkpoints=0)

    def test_budget_protected_terms_and_boolean_counts_rejected(self):
        for key,value in (('unallocated_margin_seconds',59),('product_allowance_seconds',11),
                          ('selected_acquisition_rate_per_second',15),('actual_two_pass_byte_reads_retained',1)):
            base=model();base[key]=value
            with self.assertRaises(ValueError):MODULE.budget_delta(base,additional_acquisitions=0,
                additional_other_bytes=0,additional_inventory_checkpoints=0)
        with self.assertRaises(ValueError):MODULE.budget_delta(model(),additional_acquisitions=True,
            additional_other_bytes=0,additional_inventory_checkpoints=0)

    def test_resource_check_failure_does_not_start_original_window(self):
        def fail():raise ValueError('RESOURCE_STOP')
        api,_,_,_,process,_=setup(checkpoint=fail);api.Popen()
        with self.assertRaisesRegex(ValueError,'RESOURCE_STOP'):process.stdin.write(PROTOCOL.GO)
        self.assertIsNone(api.state.started);process.stdin.close()
