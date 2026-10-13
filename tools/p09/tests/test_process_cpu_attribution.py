import copy
import unittest
from unittest.mock import patch
import process_cpu_attribution as p


def snapshot(rows,system=(100,200,100),counts=None):
    return dict(rows=rows,system=system,counts=counts or {'git.exe':2},inaccessible=1,
        scan_seconds=.01,time=1 if system==(100,200,100) else 2)


class CPUAttributionTests(unittest.TestCase):
    def pair(self):
        return snapshot({10:(1,20,'git.exe'),11:(2,30,'git.exe')}), \
            snapshot({10:(1,30,'git.exe'),11:(2,50,'git.exe')},(120,300,200))

    def test_machine_denominator_and_group_sum(self):
        row=p.compare(*self.pair())
        self.assertEqual(row['system_cpu_percent'],90)
        self.assertEqual(row['top_cpu_groups'][0]['machine_cpu_percent'],15)
        self.assertEqual(row['top_cpu_groups'][0]['matched_processes'],2)

    def test_PID_reuse_not_compared(self):
        before,after=self.pair();after['rows'][10]=(3,100000,'git.exe')
        row=p.compare(before,after);self.assertEqual(row['newly_seen_or_reused_PIDs'],1)
        self.assertEqual(row['top_cpu_groups'][0]['machine_cpu_percent'],10)

    def test_new_and_exited_processes_are_missing_not_zero_complete(self):
        before,after=self.pair();after['rows'].pop(10);after['rows'][12]=(4,100,'OTHER')
        row=p.compare(before,after);self.assertEqual(row['no_longer_readable_PIDs'],1)
        self.assertFalse(row['all_system_CPU_attributed'])

    def test_counter_reset_not_negative_CPU(self):
        before,after=self.pair();after['rows'][10]=(1,5,'git.exe')
        self.assertEqual(p.compare(before,after)['counter_reset_processes'],1)

    def test_unknown_names_or_paths_never_persisted(self):
        for name in ('private-client-secret.exe',r'C:\private\git.exe','TOKEN=value'):
            self.assertEqual(p.label(name),'OTHER')
        self.assertEqual(p.label('MSMPENG.EXE'),'MsMpEng.exe')

    def test_invalid_system_delta_rejected(self):
        before,after=self.pair()
        for system in ((100,200,100),(9999,300,200),(100,0,0)):
            after['system']=system
            with self.assertRaises(ValueError):p.compare(before,after)

    def test_top_groups_bounded_no_cause_claim(self):
        before,after=self.pair()
        for i,name in enumerate(sorted(p.LABEL_VALUES)):
            before['rows'][i+100]=(100,0,name);after['rows'][i+100]=(100,1,name)
        row=p.compare(before,after);self.assertLessEqual(len(row['top_cpu_groups']),p.TOP)
        self.assertTrue(row['CPU_samples_not_atomic'])
        self.assertFalse(row['CPU_cause_or_PC_freeze_resolution_established'])

    def test_disallowed_persisted_label_rejected(self):
        before,after=self.pair();after['rows'][10]=(1,30,'secret-name.exe')
        with self.assertRaises(ValueError):p.compare(before,after)

    def test_interval_gate_no_extra_thread_or_guard_change(self):
        windows=p.AttributionWindows.__new__(p.AttributionWindows)
        windows.attribution=[];windows.attribution_error=None;windows.previous=None;windows.due=999
        with patch.object(p.observation.ObservedWindows,'sample',return_value={'original':True}), \
                patch.object(p.time,'monotonic',return_value=1):
            self.assertEqual(windows.sample(),{'original':True})
        self.assertEqual(p.c.POLICY['emergency_cpu_consecutive_samples'],4)
        self.assertEqual(p.c.POLICY['sample_seconds'],.5)

    def test_native_error_preserves_original_sample_and_not_zero(self):
        windows=p.AttributionWindows.__new__(p.AttributionWindows)
        windows.attribution=[];windows.attribution_error=None;windows.previous=None;windows.due=0
        class Broken:
            def snapshot(self):raise ValueError('CPU_ATTRIBUTION_SCAN_TIME_LIMIT')
        windows.process_cpu=Broken()
        with patch.object(p.observation.ObservedWindows,'sample',return_value={'system_cpu_percent':99}), \
                patch.object(p.time,'monotonic',return_value=1):
            self.assertEqual(windows.sample()['system_cpu_percent'],99)
        self.assertEqual(windows.attribution,[])
        self.assertEqual(windows.attribution_error,'CPU_ATTRIBUTION_SCAN_TIME_LIMIT')


if __name__=='__main__':unittest.main()
