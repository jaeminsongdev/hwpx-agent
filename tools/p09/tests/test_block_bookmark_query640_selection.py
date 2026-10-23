"""Only two new metadata-selection controls, not a Native provenance attestation."""
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import inspect_block_bookmark_sources640 as m

class Tests(unittest.TestCase):
    def test_actual_trace_marker_is_required(self):
        for marker in ('case-trace.json','target-trace.json','owner-identities.json','capture-trace.json'):
            self.assertTrue(m.capture_directory({'saved.hwpx',marker}))
    def test_native_label_or_hwpx_alone_is_not_provenance(self):
        for names in (set(),{'saved.hwpx'},{'native-fixture.hwpx','manifest.json'},{'case-trace.json.backup'}):
            self.assertFalse(m.capture_directory(names))

if __name__=='__main__':
    result=unittest.TestResult()
    unittest.defaultTestLoader.loadTestsFromTestCase(Tests).run(result)
    print(json.dumps(dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))))
    raise SystemExit(0 if result.wasSuccessful() else 2)
