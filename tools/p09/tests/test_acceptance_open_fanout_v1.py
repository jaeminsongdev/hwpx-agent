import sys
import math
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import acceptance_open_fanout_v1 as m
import locked_runtime_inputs as locks

class Reader:
    def __init__(self,clock,sleeper,checkpoint):
        self.open_pacer=locks.OpenPacer(checkpoint,rate=20,clock=clock,sleeper=sleeper)
        self.pacer=object();self.checkpoint=checkpoint
    def _read(self):return "original-read"
    def finish(self):return "original-final-hash"

class Tests(unittest.TestCase):
    def make(self):
        now=[0.];checks=[]
        def sleep(n):now[0]=math.nextafter(now[0]+n,math.inf)
        private,readers=m.runtime(NS(a=NS(AcceptanceReader=Reader),source=object()))
        r=private.a.AcceptanceReader(lambda:now[0],sleep,lambda:checks.append(1))
        return r,readers,now,checks
    def test_rate10_same_original_class_clock_and_guard(self):
        r,_,now,checks=self.make()
        self.assertIs(type(r.open_pacer),locks.OpenPacer)
        self.assertEqual(r.open_pacer.rate,10)
        r.open_pacer.reserve();r.open_pacer.reserve()
        self.assertAlmostEqual(now[0],.1);self.assertGreaterEqual(len(checks),3)
    def test_idle_does_not_create_multiple_open_burst_credit(self):
        r,_,now,_=self.make();r.open_pacer.reserve();now[0]+=10
        r.open_pacer.reserve();before=now[0];r.open_pacer.reserve()
        self.assertAlmostEqual(now[0]-before,.1)
    def test_read_final_hash_and_all_other_original_methods_unchanged(self):
        r,_,_,_=self.make()
        self.assertIs(type(r)._read,Reader._read);self.assertIs(type(r).finish,Reader.finish)
        self.assertEqual(r._read(),"original-read");self.assertEqual(r.finish(),"original-final-hash")
    def test_original_guard_error_propagated_without_clock_or_open(self):
        def fail():raise ValueError("ORIGINAL_STOP")
        p=locks.OpenPacer(fail,rate=10)
        with self.assertRaisesRegex(ValueError,"ORIGINAL_STOP"):p.reserve()
        self.assertEqual(p.opens,0)
    def test_bad_original_pacer_not_replaced_or_silently_admitted(self):
        class Bad(Reader):
            def __init__(self,*args):
                super().__init__(*args);self.open_pacer.opens=1
        private,_=m.runtime(NS(a=NS(AcceptanceReader=Bad)))
        with self.assertRaises(ValueError):private.a.AcceptanceReader(lambda:0.,lambda x:None,lambda:None)
    def test_default_module_and_reader_unmodified_and_trace_closed(self):
        r,readers,_,_=self.make()
        self.assertEqual(Reader(lambda:0.,lambda x:None,lambda:None).open_pacer.rate,20)
        r.open_pacer.reserve();trace=m.summary(readers)
        self.assertEqual(trace[0]["actual_open_reservations"],1)
        self.assertFalse(trace[0]["Native_input_claimed"])
        self.assertFalse(trace[0]["new_sampler_thread_or_process"])

if __name__=="__main__":unittest.main()
