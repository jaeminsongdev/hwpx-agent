import unittest
from types import SimpleNamespace
from unittest.mock import patch
import pre_go_parent_cpu_observer as d

class ParentCPUObserverTests(unittest.TestCase):
    def fixture(self,own=(11,7),after=(110,170,60)):
        observer=object.__new__(d.ParentCPUWindows);observer.last=(100,150,50);observer.own_last=(10,5);observer.mask=1
        def sample(self):
            self.last=after
            return dict(system_cpu_percent=66.666667,available_ram_percent=40,commit_used_percent=30)
        return observer,sample,own
    def test_actual_system_delta_and_own_ratio_separate(self):
        observer,sample,own=self.fixture()
        with patch.object(d.c.Windows,'sample',sample),patch.object(observer,'own_times',return_value=own):r=observer.sample()
        self.assertEqual(r['system_cpu_percent'],66.666667);self.assertEqual(r['parent_cpu_machine_percent'],10)
        self.assertEqual(r['raw_system_cpu_delta_100ns'],dict(idle=10,kernel_including_idle=20,user=10,total=30))
        self.assertTrue(r['parent_process_only']);self.assertFalse(r['foreign_Process_query_executed'])
    def test_original_emergency_guard_not_changed_by_self_idle(self):
        before=dict(d.c.POLICY);row=dict(system_cpu_percent=100,available_ram_percent=40,commit_used_percent=30,parent_cpu_machine_percent=0)
        self.assertEqual(d.c.decision(row,3),(4,'STOP_SUSTAINED_SYSTEM_CPU'));self.assertEqual(d.c.POLICY,before)
    def test_counter_reset_or_impossible_raw_delta_denied(self):
        for own,after in (((9,5),(110,170,60)),((11,7),(99,170,60)),((11,7),(140,170,60))):
            observer,sample,value=self.fixture(own,after)
            with patch.object(d.c.Windows,'sample',sample),patch.object(observer,'own_times',return_value=value):
                with self.assertRaises(ValueError):observer.sample()
    def test_query_uses_only_current_process_pseudo_handle(self):
        calls=[];observer=object.__new__(d.ParentCPUWindows)
        def times(handle,*values):
            calls.append(handle);values[2]._obj.value=12;values[3]._obj.value=3;return True
        observer.k=SimpleNamespace(GetCurrentProcess=lambda:77,GetProcessTimes=times)
        self.assertEqual(observer.own_times(),(12,3));self.assertEqual(calls,[77])
    def test_failed_own_query_cannot_qualify(self):
        observer=object.__new__(d.ParentCPUWindows)
        observer.k=SimpleNamespace(GetCurrentProcess=lambda:77,GetProcessTimes=lambda *args:False)
        with self.assertRaises(ValueError):observer.own_times()

if __name__=='__main__':unittest.main()
