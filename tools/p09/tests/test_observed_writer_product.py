import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import build_observed_writer_product as d
import test_validated_compiler_progress_r2 as fixture

class ObservedWriterBuildTests(unittest.TestCase):
    def observation(self):
        raw=fixture.ReservedCompilerProgressTests().raw();events=[]
        stream=d.progress.CargoStream(emit=events.append)
        for i in range(0,len(raw),4096):stream.feed(raw[i:i+4096])
        stream.finish(0)
        return d.progress.prior.observe(''.join(d.progress.prior.encode_event(r).decode() for r in events))
    def test_closed_product_required(self):d.require_closed(self.observation())
    def test_partial_cannot_accept(self):
        row=self.observation();row['closing_observed']=False
        with self.assertRaises(ValueError):d.require_closed(row)
    def test_closed_without_product_rejected(self):
        row=self.observation();row['records']=[r for r in row['records'] if r['group']!='product-libtest']
        with self.assertRaises(ValueError):d.require_closed(row)
    def test_capture_uses_existing_bounded_stderr_only(self):
        row=self.observation();text=''.join(d.progress.prior.encode_event(r).decode() for r in row['records'])
        capture=SimpleNamespace(lock=threading.Lock(),buffers={'stderr':bytearray(text.encode())})
        self.assertEqual(d.observe_capture(capture),row)
    def test_command_factory_no_recursive_original_class_patch(self):
        original=d.b.CargoStream;seen=[]
        def command(args,kw,validator):
            seen.append((d.b.CargoStream,d.b.legacy.stream.CargoStream));return 0
        with patch.object(d,'RAW_COMMAND',command),patch.object(d.d,'RUN',6):
            self.assertEqual(d.progress_command(['fixture-cargo',*d.d.recipe()['argv_without_cargo']],{},None),0)
        self.assertEqual(seen,[(original,d.progress.CargoStream)]);self.assertIs(d.b.CargoStream,original)
    def test_foreign_command_and_worker_no_launch(self):
        with patch.object(d,'RAW_COMMAND',side_effect=AssertionError('NO_LAUNCH')):
            with self.assertRaises(ValueError):d.progress_command(['other'],{},None)
        with patch.object(d.b,'worker',side_effect=AssertionError('NO_LAUNCH')):
            with self.assertRaises(ValueError):d.worker(d.b.task_for(5))
    def test_r06_original_recipe_caps(self):
        with patch.object(d.d,'RUN',6):row=d.d.recipe()
        self.assertTrue(row['executable_path'].endswith('p152-r06.exe'))
        self.assertEqual((row['compile_maximum_seconds'],row['full249_maximum_seconds']),(600,1200))
        self.assertEqual(len(row['test_package_profile_config']),81)
    def test_stop_parent_not_build_or_gate(self):
        with self.assertRaises(ValueError):d.parent_scope({'state':'PASS_FAKE'})

if __name__=='__main__':unittest.main()
