import io
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import near_saturation_read_backpressure as d

class NearSaturationReadBackpressureTests(unittest.TestCase):
    def gate(self,values,stop=None,cached=False):
        resources=SimpleNamespace(lock=threading.Lock(),samples=[],hot=0);calls=[];sleeps=[];seq=iter(values)
        def base():
            calls.append(True)
            if stop:raise ValueError(stop)
            if cached and resources.samples:return
            row=dict(system_cpu_percent=next(seq),available_ram_percent=30,commit_used_percent=40)
            resources.hot,reason=d.c.decision(row,resources.hot);resources.samples.append(row)
            if reason:raise ValueError(reason)
        return d.PressureCheckpoint(base,resources,sleep=sleeps.append),calls,sleeps,resources
    def test_normal_background_load_has_no_start_CPU_gate_or_sleep(self):
        gate,calls,sleeps,_=self.gate((70,94.99))
        gate();gate();self.assertEqual(len(calls),2);self.assertEqual(sleeps,[])
    def test_near_saturation_yields_until_two_distinct_cool_windows(self):
        gate,calls,sleeps,resources=self.gate((96,94,97,93,92))
        gate();self.assertEqual(len(calls),5);self.assertEqual(sleeps,[0.5]*4)
        self.assertEqual(len(resources.samples),5);self.assertEqual(gate.summary()['warning_entries'],1)
        self.assertEqual(gate.summary()['completed_pause_windows'],4)
    def test_original_98_four_consecutive_stop_is_not_reset_or_suppressed(self):
        gate,calls,sleeps,resources=self.gate((98,99,100,100))
        with self.assertRaisesRegex(ValueError,'STOP_SUSTAINED_SYSTEM_CPU'):gate()
        self.assertEqual(resources.hot,4);self.assertEqual(len(calls),4);self.assertEqual(sleeps,[0.5]*3)
    def test_pause_is_bounded_and_cached_samples_cannot_qualify(self):
        gate,_,sleeps,_=self.gate((95,)*9)
        with self.assertRaisesRegex(ValueError,'STOP_READ_PRESSURE_NOT_COOLING'):gate()
        self.assertEqual(sleeps,[0.5]*8)
        gate,_,_,_=self.gate((95,),cached=True)
        with self.assertRaisesRegex(ValueError,'BACKPRESSURE_ORIGINAL_SAMPLE_NOT_ADVANCED'):gate()
    def test_existing_IO_or_memory_emergency_is_never_swallowed(self):
        for code in ('STOP_SQL_IO_SCOPE_TIME','STOP_LOW_AVAILABLE_RAM','STOP_SYSTEM_COMMIT_PRESSURE'):
            gate,_,sleeps,_=self.gate((),stop=code)
            with self.assertRaisesRegex(ValueError,code):gate()
            self.assertEqual(sleeps,[])
    def test_reader_keeps_whole_repeat_final_bytes_and_drift_detection(self):
        resources=SimpleNamespace(lock=threading.Lock(),samples=[dict(system_cpu_percent=20)],checkpoint_io=lambda:None)
        reader=d.PressureReader(resources,protected=('known.exe',));raw=[b'x'*1000];opens=[]
        path=SimpleNamespace(open=lambda mode:opens.append(mode) or io.BytesIO(raw[0]))
        with patch.object(reader.reader,'_source',return_value=path):
            first=reader.pin('known.exe');self.assertEqual(reader.pin('known.exe'),first);reader.finish()
        self.assertEqual(opens,['rb']*3);self.assertEqual(reader.summary()['bytes_read'],3000)
        self.assertEqual(reader.summary()['final_fresh_hashes'],1)
        self.assertEqual(reader.summary()['read_rates_by_kind'],dict(binary=2621440,other=4194304))
        reader=d.PressureReader(resources)
        with patch.object(reader.reader,'_source',return_value=path):
            reader.pin('known.exe');raw[0]=b'changed'
            with self.assertRaises(ValueError):reader.finish()
