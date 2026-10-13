import contextlib
import threading
import types
import unittest
from unittest.mock import Mock,patch
import observe_shared_metadata_recheck as v


class ObservationTests(unittest.TestCase):
    def kernel(self,success=True):
        kernel=Mock();kernel.GetCurrentProcess.return_value='CURRENT_SELF_ONLY'
        def query(handle,ptr,size):
            self.assertEqual(handle,'CURRENT_SELF_ONLY');self.assertEqual(size,ptr._obj.size)
            ptr._obj.private=200;ptr._obj.ws=300;return success
        kernel.K32GetProcessMemoryInfo.side_effect=query;return kernel
    def test_memory_queries_current_handle_once(self):
        kernel=self.kernel();row=v.own_memory(kernel,1000)
        self.assertEqual(row['own_private_percent_total_ram'],20)
        self.assertEqual(row['own_working_set_percent_total_ram'],30)
        kernel.GetCurrentProcess.assert_called_once();kernel.K32GetProcessMemoryInfo.assert_called_once()
        kernel.OpenProcess.assert_not_called()
    def test_memory_query_failure_is_not_zero_usage(self):
        with self.assertRaisesRegex(ValueError,'OWN_MEMORY_QUERY_FAILED'):v.own_memory(self.kernel(False),1000)
    def test_existing_sample_once_and_all_original_fields_preserved(self):
        source=dict(system_cpu_percent=99,available_ram_percent=50,commit_used_percent=20,parent_cpu_machine_percent=1)
        window=object.__new__(v.ObservedWindows);window.context=v.Context();window.k=self.kernel();window.total_ram=1000
        with patch.object(v.RAW_WINDOWS,'sample',return_value=source.copy()) as base:
            row=window.sample();base.assert_called_once()
        for key,value in source.items():self.assertEqual(row[key],value)
        window.k.K32GetProcessMemoryInfo.assert_called_once()
    def test_closed_nested_phase_and_multi_phase_window(self):
        box=v.Context()
        with box.scope('metadata_hash'):
            with box.scope('document_read'):self.assertEqual(box.phase,'document_read')
            self.assertEqual(box.phase,'metadata_hash')
        self.assertEqual(box.phase,'admission')
        self.assertEqual(box.snapshot()['phases_since_previous_sample'],['admission','document_read','metadata_hash'])
        with self.assertRaises(ValueError):
            with box.scope('private_file_or_secret'):pass
    def test_unobserved_counters_null_then_delta(self):
        box=v.Context();self.assertIsNone(box.snapshot()['audited_logical_read_bytes'])
        box.reader=types.SimpleNamespace(bytes_read=30,read_passes=1)
        self.assertIsNone(box.snapshot()['audited_logical_read_bytes_delta'])
        box.reader.bytes_read=55;self.assertEqual(box.snapshot()['audited_logical_read_bytes_delta'],25)
    def test_counter_reset_fail_closed(self):
        box=v.Context();box.reader=types.SimpleNamespace(bytes_read=30,read_passes=1);box.snapshot()
        box.reader.bytes_read=0
        with self.assertRaises(ValueError):box.snapshot()
    def test_external_CPU_saturation_is_not_ignored_when_own_CPU_zero(self):
        row=dict(system_cpu_percent=100,available_ram_percent=50,commit_used_percent=20,parent_cpu_machine_percent=0)
        hot=0
        for _ in range(4):hot,reason=v.c.decision(row,hot)
        self.assertEqual(reason,'STOP_SUSTAINED_SYSTEM_CPU')
    def test_summary_filtered_bounded_and_no_cause_claim(self):
        owner=types.SimpleNamespace(thread=types.SimpleNamespace(ident=None),lock=threading.Lock(),
            samples=[dict(system_cpu_percent=100,parent_cpu_machine_percent=0,own_private_bytes=200,
                available_ram_percent=50,private_log='DO_NOT_SAVE')])
        row=v.summary(owner);self.assertNotIn('private_log',row['samples'][0])
        self.assertFalse(row['CPU_cause_or_PC_freeze_resolution_established'])
        self.assertFalse(row['new_sampler_thread_started'])
        owner.samples=[];self.assertIsNone(v.summary(owner)['own_cpu_max_machine_percent'])
    def test_reader_delegates_original_fresh_finish_and_reads(self):
        reader=object.__new__(v.Reader);reader.context=v.Context()
        for method,arg,phase in (('pin','public','metadata_hash'),('json','public','metadata_read_parse'),
                ('text','public','document_read'),('finish',None,'final_fresh_hash')):
            def original(*args):self.assertEqual(reader.context.phase,phase);return 'delegated'
            with patch.object(v.RAW_READER,method,side_effect=original) as base:
                actual=getattr(reader,method)() if arg is None else getattr(reader,method)(arg)
                self.assertEqual(actual,'delegated');base.assert_called_once()
    def test_adapter_restores_roles_and_does_not_run_product_or_new_thread(self):
        before=(v.old.DEST,v.observation.ObservedResources,v.old.run.pressure.PressureReader,
            v.old.batch.contracts,v.json.dump)
        with patch.object(v.old,'main',return_value=2) as main:
            self.assertEqual(v.observe('fixture-unused'),2);main.assert_called_once()
        self.assertEqual(before,(v.old.DEST,v.observation.ObservedResources,v.old.run.pressure.PressureReader,
            v.old.batch.contracts,v.json.dump))
        actual=object();fixture=object();box=v.Context()
        with patch.object(v,'RAW_READER',return_value='old_fixture') as original, \
                patch.object(v,'Reader',return_value='observed_actual') as observed:
            self.assertEqual(v.reader_for_owner(fixture,box,[actual],protected=('known.exe',)),'old_fixture')
            original.assert_called_once_with(fixture,protected=('known.exe',));observed.assert_not_called()
            self.assertEqual(v.reader_for_owner(actual,box,[actual]),'observed_actual')
            observed.assert_called_once_with(actual,box)


if __name__=='__main__':unittest.main()
