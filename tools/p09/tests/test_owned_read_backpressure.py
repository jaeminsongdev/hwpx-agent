import io
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import owned_read_backpressure as d

class OwnedReadBackpressureTests(unittest.TestCase):
    def test_same_original_sample_no_second_native_query_or_history_copy(self):
        calls=[];row=dict(system_cpu_percent=20)
        class Base:
            def sample(self):calls.append(True);return row
        box=d.LatestOriginalSample()
        with patch.object(d.observer,'RAW_PARENT',Base):windows=d.windows_type(box)()
        self.assertIs(windows.sample(),row);self.assertIs(box.samples[0],row);self.assertEqual(calls,[True])
        next_row=dict(system_cpu_percent=30);box.record(next_row);self.assertEqual(len(box.samples),1)
        self.assertIs(box.samples[0],next_row)
    def test_original_owned_whole_repeat_final_bytes_and_rates(self):
        box=d.LatestOriginalSample();box.record(dict(system_cpu_percent=20));calls=[]
        reader=d.OwnedReader('fixture',lambda:calls.append(True),samples=box,protected=('known.exe',))
        opens=[];path=SimpleNamespace(open=lambda mode:opens.append(mode) or io.BytesIO(b'x'*1000))
        with patch.object(reader,'_source',return_value=path):
            first=reader.fresh_pin('known.exe');self.assertEqual(reader.fresh_pin('known.exe'),first);reader.finish()
        self.assertEqual(opens,['rb']*3);self.assertEqual(reader.bytes_read,3000)
        self.assertEqual(reader.pacer.rate,1048576);self.assertEqual(reader.final_fresh_hashes,1)
        self.assertGreater(len(calls),3);self.assertEqual(reader.diagnostics()['near_saturation_read_backpressure']['warning_entries'],0)
    def test_original_stop_and_closed_exe_context_not_suppressed(self):
        box=d.LatestOriginalSample();box.record(dict(system_cpu_percent=20))
        reader=d.OwnedReader('fixture',lambda:(_ for _ in ()).throw(ValueError('STOP_LOW_AVAILABLE_RAM')),
            samples=box,protected=('known.exe',))
        with self.assertRaisesRegex(ValueError,'STOP_LOW_AVAILABLE_RAM'):reader.fresh_pin('known.exe')
        self.assertIsNone(reader.active);self.assertEqual(reader.diagnostics()['interrupted_protected_EXE_path'],'known.exe')
        with self.assertRaises(ValueError):reader.fresh_pin('private-original.hwpx')
        self.assertIsNone(reader.diagnostics()['interrupted_protected_EXE_path'])
    def test_same_sampler_supplies_two_distinct_cool_windows(self):
        box=d.LatestOriginalSample();values=iter((96,94,93));calls=[];sleeps=[]
        def original_checkpoint():
            calls.append(True);box.record(dict(system_cpu_percent=next(values)))
        gate=d.pressure.PressureCheckpoint(original_checkpoint,box,sleep=sleeps.append)
        gate();self.assertEqual(len(calls),3);self.assertEqual(sleeps,[0.5,0.5])
        self.assertEqual(len(box.samples),1);self.assertEqual(gate.summary()['warning_entries'],1)
