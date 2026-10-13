import ctypes
import unittest
from unittest.mock import patch
import owned_job_io_observer as v

class Kernel:
    def __init__(self,values=None,ok=True):self.values=values or {};self.ok=ok;self.calls=[]
    def QueryInformationJobObject(self,job,kind,out,size,length):
        self.calls.append((job,kind,size,length))
        for key,field in v.FIELDS.items():setattr(out._obj.io,field,self.values.get(key,0))
        return self.ok

class JobIoTests(unittest.TestCase):
    def test_exact_official_structure_and_single_explicit_job_query(self):
        k=Kernel({'read_bytes':123});row=v.JobIoReader(k).query(17)
        self.assertEqual(k.calls,[(17,8,ctypes.sizeof(v.CombinedAccounting),None)])
        self.assertEqual(v.CombinedAccounting.io.offset,ctypes.sizeof(v.c.Accounting))
        self.assertEqual(ctypes.sizeof(v.CombinedAccounting),ctypes.sizeof(v.c.Accounting)+ctypes.sizeof(v.c.IoCounters))
        self.assertEqual(row['job_IO_totals']['read_bytes'],123)
    def test_first_observation_is_not_an_invented_zero_delta(self):
        row=v.JobIoReader(Kernel()).query(17)
        self.assertTrue(row['job_IO_observed']);self.assertIsNone(row['job_IO_delta_since_previous_query'])
        self.assertEqual(sum(row['job_IO_totals'].values()),0)
    def test_all_six_monotonic_counters_and_exact_deltas(self):
        k=Kernel({n:10 for n in v.FIELDS});reader=v.JobIoReader(k);reader.query(17)
        k.values={n:23 for n in v.FIELDS};row=reader.query(17)
        self.assertEqual(row['job_IO_delta_since_previous_query'],{n:13 for n in v.FIELDS})
        self.assertEqual(row['job_IO_query_sequence'],2)
    def test_failed_native_query_is_never_zero_or_completed(self):
        reader=v.JobIoReader(Kernel(ok=False))
        with self.assertRaises(ValueError):reader.query(17)
        self.assertEqual(reader.completed_queries,0);self.assertIsNone(reader.previous)
    def test_each_counter_reset_rejected_without_overwriting_last_good(self):
        for name in v.FIELDS:
            k=Kernel({n:10 for n in v.FIELDS});reader=v.JobIoReader(k);reader.query(17);k.values[name]=9
            with self.assertRaises(ValueError):reader.query(17)
            self.assertEqual(reader.completed_queries,1);self.assertEqual(reader.previous[name],10)
    def test_null_or_other_job_cannot_reuse_or_fallback_to_current_process(self):
        reader=v.JobIoReader(Kernel())
        for bad in (None,0,-1,True,'17'):
            with self.assertRaises(ValueError):reader.query(bad)
        reader.query(17)
        with self.assertRaises(ValueError):reader.query(18)
        self.assertEqual(reader.completed_queries,1)
    def test_original_CPU_RAM_member_rows_are_preserved_no_extra_sampler(self):
        original=dict(active_processes=2,job_cpu_seconds=3.25,peak_job_private_mib=4.5,owned_processes=[])
        class Base:
            def __init__(self):self.k=Kernel();self.calls=[]
            def accounting(self,job):self.calls.append(job);return dict(original)
        with patch('threading.Thread.start',side_effect=AssertionError('NO_SAMPLER')), \
                patch('subprocess.Popen',side_effect=AssertionError('NO_CHILD')):
            win=v.windows_type(Base)();row=win.accounting(17)
        self.assertEqual({n:row[n] for n in original},original);self.assertEqual(win.calls,[17])
        self.assertEqual(len(win.k.calls),1)
    def test_transfer_counters_do_not_claim_physical_IO_or_freeze_cause(self):
        row=v.JobIoReader(Kernel({'write_bytes':10**12})).query(17)
        self.assertFalse(row['job_IO_physical_disk_or_external_cause_proven'])
        self.assertNotIn('PID',row);self.assertNotIn('path',row)
