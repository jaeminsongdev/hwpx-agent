import io
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import readonly_parent_file_observation as d

class ReadonlyParentFileObservationTests(unittest.TestCase):
    def test_existing_resource_constructor_gets_one_own_parent_only(self):
        seen=[];fake=object()
        with patch.object(d.observer,'RAW_PARENT',return_value=fake) as own, \
                patch.object(d.OriginalResources,'__init__',side_effect=lambda **kw:seen.append(kw)):
            d.ObservedResources()
        own.assert_called_once_with();self.assertEqual(seen,[dict(windows=fake)])
    def test_every_fresh_read_and_finish_unchanged_rates(self):
        raw=b'x'*1000;opens=[];path=SimpleNamespace(open=lambda mode:opens.append(mode) or io.BytesIO(raw))
        reader=d.TraceReader('fixture',lambda:None,protected=('known.exe',))
        with patch.object(reader,'_source',return_value=path):
            pin=reader.fresh_pin('known.exe');self.assertEqual(reader.fresh_pin('known.exe'),pin);reader.finish()
        self.assertEqual(opens,['rb']*3);self.assertEqual(reader.bytes_read,3000)
        self.assertEqual(reader.pacer.rate,2621440);self.assertEqual(reader.final_fresh_hashes,1)
        self.assertEqual(reader.context()['last_completed_protected_EXE_path'],'known.exe')
    def test_failure_context_only_closed_exe_never_private_name(self):
        reader=d.TraceReader('fixture',lambda:None,protected=('known.exe',))
        with patch.object(reader,'_source',side_effect=ValueError('fixture_stop')):
            for name in ('known.exe','private-original.hwpx'):
                with self.assertRaises(ValueError):reader.fresh_pin(name)
                self.assertIsNone(reader.active)
                self.assertEqual(reader.context()['interrupted_protected_EXE_path'],'known.exe' if name=='known.exe' else None)
        self.assertFalse(reader.context()['arbitrary_source_paths_or_private_artifact_names_saved'])
    def test_invalid_allowlist_and_guard_not_suppressed(self):
        with self.assertRaises(ValueError):d.TraceReader('fixture',lambda:None,protected=('private.hwpx',))
        reader=d.TraceReader('fixture',lambda:(_ for _ in ()).throw(ValueError('fixture_stop')))
        with self.assertRaisesRegex(ValueError,'fixture_stop'):reader.fresh_pin('fixture.rs')
