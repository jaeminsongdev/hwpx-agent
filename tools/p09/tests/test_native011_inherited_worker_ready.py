"""Original readiness deadline and fail-closed GO sink, no product permission."""
from types import SimpleNamespace as NS
import unittest
import native011_inherited_worker_ready_inspection as candidate
import worker_readiness_v1 as protocol


class WorkerReadyContracts(unittest.TestCase):
    def fixture(self,*,delay=.01,owned=True):
        time=[0.0];starts=[];ownership=[];sink=candidate.NoGoReadySink(protocol.GO)
        class Event:
            def wait(self,milliseconds):time[0]+=delay;return True
        process=NS(pid=10,poll=lambda:None)
        def verify(actual):ownership.append(actual);return owned
        def checkpoint():starts.append(time[0])
        gate=protocol.Gate(sink,Event(),process,verify,checkpoint,clock=lambda:time[0])
        return gate,sink,starts,ownership
    def test_original_gate_observes_ready_then_no_go_is_written(self):
        gate,sink,starts,owned=self.fixture()
        with self.assertRaisesRegex(ValueError,'READINESS_PROBE_PRODUCT_GO_DENIED'):gate.write(protocol.GO)
        self.assertTrue(gate.ready);self.assertTrue(gate.stopped);self.assertFalse(gate.written)
        self.assertEqual(sink.attempts,1);self.assertEqual(starts[0],0.0)
        self.assertEqual(len(owned),3);self.assertEqual(gate.seconds,15)
        self.assertFalse(gate.diagnostics()['actual_original_GO_written'])
    def test_late_event_does_not_reach_the_go_sink(self):
        gate,sink,_,_=self.fixture(delay=15)
        with self.assertRaisesRegex(ValueError,'PREPARATION_TIMEOUT'):gate.write(protocol.GO)
        self.assertEqual(sink.attempts,0);self.assertFalse(gate.ready);self.assertTrue(gate.stopped)
    def test_wrong_job_member_never_receives_preparation_start(self):
        gate,sink,starts,_=self.fixture(owned=False)
        with self.assertRaisesRegex(ValueError,'SAME_LIVE_OWNED_JOB_MEMBER'):gate.write(protocol.GO)
        self.assertEqual(starts,[]);self.assertEqual(sink.attempts,0)
    def test_sink_has_no_raw_writer_and_never_accepts_second_write(self):
        sink=candidate.NoGoReadySink(protocol.GO)
        self.assertFalse(hasattr(sink,'original'))
        with self.assertRaises(ValueError):sink.write(b'not_GO')
        with self.assertRaisesRegex(ValueError,'READINESS_PROBE_PRODUCT_GO_DENIED'):sink.write(protocol.GO)
        with self.assertRaises(ValueError):sink.write(protocol.GO)
        with self.assertRaises(ValueError):sink.flush()
