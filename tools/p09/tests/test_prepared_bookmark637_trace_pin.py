"""Only the two new trace-shape controls; previous eight controls are retained."""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import inspect_prepared_bookmark637_render as m


class Tests(unittest.TestCase):
    def test_trace_digest_without_path_is_bound_to_exact_current_file(self):
        pin = dict(path='private/fixed.bmp', bytes=54, sha256='a'*64)
        m.trace_pin_matches(pin, dict(pin=dict(bytes=54, sha256='a'*64)))

    def test_wrong_size_digest_or_injected_path_is_rejected(self):
        pin = dict(path='private/fixed.bmp', bytes=54, sha256='a'*64)
        for bad in (dict(bytes=55, sha256='a'*64), dict(bytes=54, sha256='b'*64), dict(pin)):
            with self.assertRaisesRegex(ValueError, 'NATIVE_TRACE_EXACT_ARTIFACT'):
                m.trace_pin_matches(pin, dict(pin=bad))


if __name__ == '__main__':
    result = unittest.TestResult()
    unittest.defaultTestLoader.loadTestsFromTestCase(Tests).run(result)
    print(json.dumps(dict(run=result.testsRun, errors=len(result.errors), failures=len(result.failures), skipped=len(result.skipped))))
    raise SystemExit(0 if result.wasSuccessful() else 2)
