import io
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import build_parent_observed_xml_product as d

class ParentObservedBuildTests(unittest.TestCase):
    def test_original_run_rate_and_worker_restore(self):
        original=d.base.c.Windows;seen=[]
        def run(destination,binding):
            seen.append(d.base.c.Windows);reader=d.base.weighted.WeightedReader('fixture',lambda:None)
            reader.pacer.select('x.exe');self.assertEqual(reader.pacer.rate,1048576)
            stream=io.StringIO();json.dump(dict(samples=[]),stream);row=json.loads(stream.getvalue())
            self.assertTrue(row['parent_ProcessTimes_observation_connected']);self.assertFalse(row['foreign_Process_query_executed'])
            self.assertFalse(row['additional_observer_thread_started']);return 2
        with patch.object(d.base,'weighted',d.driver.pressure),patch.object(d,'RAW_RUN',run):
            self.assertEqual(d.observed_run('fixture',({},[],[])),2)
        self.assertEqual(seen,[d.observer.RAW_PARENT]);self.assertIs(d.base.c.Windows,original)
        self.assertEqual(d.base.recipe()['compile_maximum_seconds'],600)
    def test_tracing_preserves_whole_fresh_reads_and_closed_context(self):
        raw=b'exact original bytes';path=SimpleNamespace(open=lambda mode:io.BytesIO(raw));out=[]
        pin=dict(path='target/fixture.exe',bytes=len(raw),sha256='0'*64)
        def run(destination,binding):
            reader=d.base.weighted.WeightedReader('fixture',lambda:None)
            with patch.object(reader,'_source',return_value=path):reader.fresh_pin(pin['path']);reader.finish()
            self.assertEqual(reader.bytes_read,2*len(raw));self.assertEqual(reader.final_fresh_hashes,1)
            stream=io.StringIO();json.dump(dict(samples=[]),stream);out.append(json.loads(stream.getvalue()));return 2
        with patch.object(d.base,'weighted',d.driver.pressure),patch.object(d,'RAW_RUN',run):
            self.assertEqual(d.observed_run('fixture',({},[pin],[])),2)
        context=out[0]['protected_file_read_context'][0]
        self.assertEqual(context['last_completed_protected_EXE_path'],pin['path']);self.assertIsNone(context['interrupted_protected_EXE_path'])
        self.assertFalse(context['arbitrary_source_paths_or_private_artifact_names_saved'])

if __name__=='__main__':unittest.main()
