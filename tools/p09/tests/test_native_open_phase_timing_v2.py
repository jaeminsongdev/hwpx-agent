import ctypes
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import native_open_phase_timing_v2 as m


class Tests(unittest.TestCase):
    def graph(self, stop=False, clock_fail=False):
        calls=[]; ticks=[0.0]; owner=[1]
        error=ValueError("ORIGINAL_RESOURCE_STOP")
        def reserve():
            calls.append("reserve")
            if stop:raise error
            ticks[0]+=2
        def create(*args):
            calls.append(("CreateFileW",args)); ticks[0]+=3
            ctypes.set_last_error(32); return 71
        checkpoint=object()
        pacer=NS(reserve=reserve,checkpoint=checkpoint,rate=14,previous=12.0,opens=9)
        close=lambda h:calls.append(("close",h))
        kernel=NS(CreateFileW=create,CloseHandle=close)
        native=NS(pacer=pacer,k=kernel)
        phase=NS(current=None)
        def clock():
            ctypes.set_last_error(999)
            if clock_fail:raise RuntimeError("CLOCK_UNKNOWN")
            return ticks[0]
        timing,proof=m.connect(native,phase,clock=clock,identity=lambda:owner[0])
        phase.current={"ordinal":1}
        return native,phase,timing,proof,calls,owner,error,checkpoint

    def test_native_pacer_kernel_and_existing_phase_aliases_stay_exact(self):
        n, _, _, p, _, _, _, cp=self.graph()
        self.assertIs(n,p["original_native_instance"])
        self.assertIs(n.pacer,p["original_pacer"]);self.assertIs(n.k,p["original_kernel"])
        self.assertIs(n.pacer.checkpoint,cp)
        self.assertEqual((n.pacer.previous,n.pacer.opens,n.pacer.rate),(12.0,9,14))

    def test_original_calls_once_and_separate_elapsed_totals(self):
        n, _, t, _, calls, _, _, _=self.graph()
        n.pacer.reserve();self.assertEqual(n.k.CreateFileW("path",7),71)
        self.assertEqual(calls,["reserve",("CreateFileW",("path",7))])
        self.assertEqual(t.rows["original_reserve_including_checkpoints"]["elapsed_total_seconds"],2)
        self.assertEqual(t.rows["original_CreateFileW"]["elapsed_total_seconds"],3)
        self.assertEqual(ctypes.get_last_error(),32)

    def test_original_stop_identity_and_no_OS_call(self):
        n, _, t, _, calls, _, error, _=self.graph(stop=True)
        with self.assertRaises(ValueError) as caught:n.pacer.reserve()
        self.assertIs(caught.exception,error);self.assertEqual(calls,["reserve"])
        self.assertEqual(t.rows["original_CreateFileW"]["started"],0)

    def test_unavailable_clock_keeps_handle_and_explicit_unknown(self):
        n, _, t, _, _, _, _, _=self.graph(clock_fail=True)
        self.assertEqual(n.k.CreateFileW("x"),71)
        self.assertEqual(t.rows["original_CreateFileW"]["unknown"],1)
        self.assertEqual(ctypes.get_last_error(),32)

    def test_close_callback_is_exact_and_not_timed(self):
        n, _, t, p, _, _, _, _=self.graph()
        self.assertIs(n.k.CloseHandle,p["original_kernel"].CloseHandle)
        n.k.CloseHandle(71)
        self.assertTrue(all(row["started"]==0 for row in t.rows.values()))

    def test_outside_acquisition_delegates_without_measurement(self):
        n, phase, t, _, calls, _, _, _=self.graph();phase.current=None
        n.pacer.reserve();n.k.CreateFileW("x")
        self.assertEqual(len(calls),2)
        self.assertTrue(all(row["started"]==0 for row in t.rows.values()))

    def test_owner_change_and_reinstallation_denied(self):
        n, phase, _, _, calls, owner, _, _=self.graph();owner[0]=2
        with self.assertRaisesRegex(ValueError,"SAME_ACQUISITION_OWNER"):n.k.CreateFileW("x")
        self.assertEqual(calls,[])
        phase.current=None
        with self.assertRaisesRegex(ValueError,"ONE_INSTALLATION"):m.connect(n,phase)

    def test_installation_failure_restores_prior_pacer_and_kernel_bindings(self):
        reserve=lambda:None; create=lambda *args:None
        class Refuse:
            def __init__(self):object.__setattr__(self,"CreateFileW",create)
            def __setattr__(self,name,value):
                if name=="CreateFileW" and value is not create:raise ValueError("ASSIGNMENT_REFUSED")
                object.__setattr__(self,name,value)
        pacer=NS(reserve=reserve);kernel=Refuse();native=NS(pacer=pacer,k=kernel)
        with self.assertRaisesRegex(ValueError,"ASSIGNMENT_REFUSED"):
            m.connect(native,NS(current=None))
        self.assertIs(pacer.reserve,reserve);self.assertIs(kernel.CreateFileW,create)
        self.assertFalse(hasattr(native,"acquisition_phase_timing"))


if __name__=="__main__":unittest.main()
