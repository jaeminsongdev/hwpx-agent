import ctypes
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import native_open_phase_timing_v1 as m


class Tests(unittest.TestCase):
    def graph(self, active=True, clock=None):
        calls=[]; owner=[1]; ticks=[0.0]
        def reserve():
            calls.append("reserve"); ticks[0] += 2
        def create(*args):
            calls.append(("CreateFileW", args)); ticks[0] += 3
            ctypes.set_last_error(32); return 71
        pacer=NS(reserve=reserve, checkpoint=object(), rate=14, previous=17.0, opens=9)
        kernel=NS(CreateFileW=create, CloseHandle=lambda h: calls.append(("close", h)))
        native=NS(pacer=pacer, k=kernel)
        acquisition=NS(current=None)
        timing, proof=m.connect(native, acquisition, clock=clock or (lambda:ticks[0]), identity=lambda:owner[0])
        if active: acquisition.current={"ordinal":1}
        return native, acquisition, timing, proof, calls, owner

    def test_original_reserve_and_CreateFileW_once_with_exact_arguments(self):
        n, _, t, p, calls, _=self.graph()
        n.pacer.reserve(); result=n.k.CreateFileW("path", 1, 2, None, 3, 4, None)
        self.assertEqual(result,71)
        self.assertEqual(calls,["reserve",("CreateFileW",("path",1,2,None,3,4,None))])
        self.assertEqual(t.rows["original_reserve_including_checkpoints"]["elapsed_total_seconds"],2)
        self.assertEqual(t.rows["original_CreateFileW"]["elapsed_total_seconds"],3)
        self.assertFalse(p["default_class_or_module_mutated"])

    def test_clock_last_error_never_changes_original_CreateFileW_result(self):
        ticks=iter((1.0,2.0))
        def clock():
            ctypes.set_last_error(999); return next(ticks)
        n, _, _, _, _, _=self.graph(clock=clock)
        ctypes.set_last_error(7); self.assertEqual(n.k.CreateFileW("x"),71)
        self.assertEqual(ctypes.get_last_error(),32)

    def test_clock_before_reserve_retains_entry_last_error(self):
        n, _, _, p, _, _=self.graph(clock=lambda:(ctypes.set_last_error(999) or 1.0))
        original=p["original_pacer"].reserve
        def reserve():
            self.assertEqual(ctypes.get_last_error(),77); original()
        p["original_pacer"].reserve=reserve
        ctypes.set_last_error(77); n.pacer.reserve()
        self.assertEqual(ctypes.get_last_error(),77)

    def test_original_reserve_stop_identity_preserved_and_no_OS_open(self):
        n, _, t, p, calls, _=self.graph(); error=ValueError("ORIGINAL_RESOURCE_STOP")
        def stop(): raise error
        p["original_pacer"].reserve=stop
        with self.assertRaises(ValueError) as caught:n.pacer.reserve()
        self.assertIs(caught.exception,error); self.assertEqual(calls,[])
        self.assertEqual(t.rows["original_reserve_including_checkpoints"]["failed"],1)
        self.assertEqual(t.rows["original_CreateFileW"]["started"],0)

    def test_original_CreateFileW_error_is_not_masked_by_clock_failure(self):
        def clock():raise RuntimeError("CLOCK_UNAVAILABLE")
        n, _, t, p, _, _=self.graph(clock=clock); error=OSError("ORIGINAL_OS_FAILURE")
        def fail(*args):raise error
        p["original_kernel"].CreateFileW=fail
        with self.assertRaises(OSError) as caught:n.k.CreateFileW("x")
        self.assertIs(caught.exception,error)
        self.assertEqual(t.rows["original_CreateFileW"]["unknown"],1)

    def test_unknown_or_backward_clock_is_not_zero(self):
        for values in ((None,2.0),(3.0,2.0),(float("nan"),2.0),(True,2.0)):
            ticks=iter(values)
            n, _, t, _, _, _=self.graph(clock=lambda:next(ticks)); n.pacer.reserve()
            row=t.rows["original_reserve_including_checkpoints"]
            self.assertEqual(row["unknown"],1); self.assertEqual(row["measured"],0)
            self.assertIsNone(row["elapsed_max_seconds"])

    def test_outside_acquisition_delegates_without_clocks_or_new_stats(self):
        def clock():self.fail("OUTSIDE_PHASE_CLOCK")
        n, _, t, _, _, _=self.graph(active=False,clock=clock)
        n.pacer.reserve(); n.k.CreateFileW("x"); n.k.CloseHandle(71)
        self.assertTrue(all(row["started"]==0 for row in t.rows.values()))

    def test_pacer_checkpoint_rate_credit_and_counters_forward_exactly(self):
        n, _, _, p, _, _=self.graph(); changed=object()
        n.pacer.checkpoint=changed; n.pacer.rate=20; n.pacer.previous=24.0
        self.assertIs(p["original_pacer"].checkpoint,changed)
        self.assertEqual(p["original_pacer"].rate,20)
        self.assertEqual(p["original_pacer"].previous,24.0)
        self.assertEqual(n.pacer.opens,9)

    def test_close_and_other_kernel_functions_are_original_objects(self):
        n, _, t, p, _, _=self.graph()
        self.assertIs(n.k.CloseHandle,p["original_kernel"].CloseHandle)
        n.k.CloseHandle(71)
        self.assertTrue(all(row["started"]==0 for row in t.rows.values()))

    def test_reinstall_or_active_install_rejected(self):
        n, a, _, _, _, _=self.graph(active=False)
        with self.assertRaisesRegex(ValueError,"ONE_INSTALLATION"):m.connect(n,a)
        other=NS(pacer=n.pacer,k=n.k)
        with self.assertRaisesRegex(ValueError,"BEFORE_ACQUISITION"):
            m.connect(other,NS(current={}))

    def test_different_owner_fails_before_original_OS_call(self):
        n, _, _, _, calls, owner=self.graph(); owner[0]=2
        with self.assertRaisesRegex(ValueError,"SAME_ACQUISITION_OWNER"):n.k.CreateFileW("x")
        self.assertEqual(calls,[])

    def test_summary_cannot_mutate_internal_aggregate_and_no_path_or_handle(self):
        n, _, t, _, _, _=self.graph(); n.k.CreateFileW("private_path")
        row=t.summary(); row["operations"]["original_CreateFileW"]["started"]=123
        self.assertEqual(t.rows["original_CreateFileW"]["started"],1)
        self.assertNotIn("private_path",str(t.summary()))
        self.assertFalse(t.summary()["CPU_cause_or_PC_freeze_resolution_proven"])


    def test_late_accounting_failure_cannot_lose_original_handle_return(self):
        n, _, t, _, _, _=self.graph()
        class Broken(dict):
            def __setitem__(self,key,value):
                if key=="completed":raise MemoryError("ACCOUNTING_ALLOCATION_FAILURE")
                super().__setitem__(key,value)
        t.rows["original_CreateFileW"]=Broken(t.rows["original_CreateFileW"])
        self.assertEqual(n.k.CreateFileW("x"),71)
        self.assertTrue(t.accounting_unavailable)
        self.assertEqual(ctypes.get_last_error(),32)

    def test_late_accounting_failure_cannot_mask_original_OS_exception(self):
        n, _, t, p, _, _=self.graph(); error=OSError("ORIGINAL_OS_FAILURE")
        class Broken(dict):
            def __setitem__(self,key,value):
                if key=="failed":raise MemoryError("ACCOUNTING_ALLOCATION_FAILURE")
                super().__setitem__(key,value)
        t.rows["original_CreateFileW"]=Broken(t.rows["original_CreateFileW"])
        def fail(*args):raise error
        p["original_kernel"].CreateFileW=fail
        with self.assertRaises(OSError) as caught:n.k.CreateFileW("x")
        self.assertIs(caught.exception,error)
        self.assertTrue(t.summary()["accounting_unavailable"])


if __name__=="__main__":unittest.main()
