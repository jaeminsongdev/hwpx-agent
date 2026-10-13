import ctypes
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import bounded_cpu_attribution_probe_v2 as probe


class Fake:
    def __init__(self,now,delay=0,rows=2,create_delay=0):
        self.now=now;self.delay=delay;self.rows=rows;self.create_delay=create_delay
        self.index=0;self.opened=[];self.closed=[];self.scratch=[]
    def CreateToolhelp32Snapshot(self,*args):
        self.now[0]+=self.create_delay;return 100
    def set_entry(self,pointer):
        entry=pointer._obj;entry.pid=10+self.index;entry.parent=1;entry.name="python.exe"
    def Process32FirstW(self,h,p):
        self.index=0;self.set_entry(p);return True
    def Process32NextW(self,h,p):
        self.index+=1
        if self.index>=self.rows:ctypes.set_last_error(18);return False
        self.set_entry(p);return True
    def OpenProcess(self,access,inherit,pid):
        self.now[0]+=self.delay;self.opened.append(pid);return pid+1000
    def GetProcessTimes(self,h,*pointers):
        self.scratch.append(tuple(id(p._obj) for p in pointers))
        for i,p in enumerate(pointers):p._obj.value=100+i
        return True
    def CloseHandle(self,h):self.closed.append(h);return True


class Tests(unittest.TestCase):
    def run_capture(self,**kw):
        now=[0.];api=Fake(now,**kw);obj=probe.Snapshot.__new__(probe.Snapshot);obj.k=api
        return obj.capture(clock=lambda:now[0]),api

    def test_normal_rows_same_identity_and_scratch_reused(self):
        row,api=self.run_capture(rows=3)
        self.assertEqual(len(row["rows"]),3)
        self.assertFalse(row["measurement_budget_exceeded"])
        self.assertEqual(len(set(api.scratch)),1)
        self.assertEqual(len(api.closed),4)

    def test_slow_create_stops_before_enum_and_closes(self):
        row,api=self.run_capture(create_delay=.08)
        self.assertTrue(row["measurement_budget_exceeded"])
        self.assertEqual(row["enumerated"],0);self.assertFalse(api.opened)
        self.assertEqual(api.closed,[100]);self.assertEqual(row["rows"],{})
        self.assertAlmostEqual(row["collection_seconds"],.08)

    def test_slow_open_closes_process_and_no_time_query(self):
        row,api=self.run_capture(delay=.06)
        self.assertEqual(len(api.opened),1)
        self.assertFalse(api.scratch);self.assertEqual(row["rows"],{})
        self.assertEqual(api.closed,[1010,100])
        self.assertTrue(row["partial_rows_discarded"])

    def test_budget_stops_before_next_process_and_discards_partial(self):
        row,api=self.run_capture(delay=.03,rows=10)
        self.assertEqual(len(api.opened),2)
        self.assertEqual(len(api.scratch),1)
        self.assertTrue(row["measurement_budget_exceeded"])
        self.assertEqual(row["rows"],{});self.assertEqual(len(api.closed),3)

    def test_close_failure_never_successfully_hidden(self):
        now=[0.];api=Fake(now);obj=probe.Snapshot.__new__(probe.Snapshot);obj.k=api
        with patch.object(api,"CloseHandle",return_value=False):
            with self.assertRaises(ValueError):obj.capture(clock=lambda:now[0])

    def test_no_limit_increase_or_causal_claim(self):
        row,api=self.run_capture()
        self.assertEqual(probe.MAX_CAPTURE_SECONDS,.05)
        self.assertFalse(row["OS_call_hard_preemption_guaranteed"])
        self.assertIs(probe.compare,probe.prior.compare)


if __name__=="__main__":unittest.main()
