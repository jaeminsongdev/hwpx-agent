"""Full bundle history binding without per-case history replay; never Native."""
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import run_prepared_bookmark_native630 as entry


class Contracts(unittest.TestCase):
    def reader(self, drift=False):
        runtime = entry.runtime
        paths = runtime.SOURCES | {entry.SELF, runtime.SELF}
        history = 'implementation/p09/evidence/modeled-history-not-an-actual-input.json'
        pins = {path: dict(path=path, bytes=1, sha256='0'*64) for path in paths | {history}}
        proof = dict(state=entry.STATE, cleanup=True, fresh_inputs=1, final_fresh_hashes=1,
            contracts=dict(run=14, errors=0, failures=0, skipped=0),
            port_models=dict(run=7, errors=0, failures=0, skipped=0),
            entry_failure_contracts=dict(run=3, errors=0, failures=0, skipped=0),
            bundle_history_contracts=dict(run=2, errors=0, failures=0, skipped=0),
            actual_native_started=False, current_session_worker_source_requalified_not_called_unchanged=True,
            current_session_worker_check=dict(native_constructor_trap_calls=0, cleanup=True),
            ready_denial=dict(cleanup=True, requests=1, result=dict(completed_callback_cases=0)),
            source_pins=list(pins.values()), execution_dependency_paths=sorted(paths))
        class Reader:
            def __init__(self):
                self.calls=[]
            def json(self, path):
                return proof
            def pin(self, path):
                self.calls.append(path)
                return dict(pins[path], sha256='f'*64) if drift and path == history else pins[path]
        return Reader(), paths, history, pins
    def test_bundle_reads_every_history_pin_but_case_paths_exclude_it(self):
        reader, paths, history, pins = self.reader()
        with patch.object(entry.codec, 'unpack', side_effect=lambda x: x), patch.object(entry.runtime.prepared, 'loaded_dependencies', return_value=set()):
            _, actual = entry.load_code(reader)
        self.assertEqual(set(reader.calls), set(pins))
        self.assertIn(history, reader.calls)
        self.assertNotIn(history, actual)
        self.assertEqual(actual, paths)
    def test_changed_history_is_rejected_not_cached_or_skipped(self):
        reader, _, _, _ = self.reader(drift=True)
        with patch.object(entry.codec, 'unpack', side_effect=lambda x: x), patch.object(entry.runtime.prepared, 'loaded_dependencies', return_value=set()):
            with self.assertRaisesRegex(ValueError, 'CHANGED_BUNDLE_HISTORY'):
                entry.load_code(reader)


if __name__ == '__main__':
    result = unittest.TextTestRunner(stream=io.StringIO()).run(unittest.defaultTestLoader.loadTestsFromTestCase(Contracts))
    print(json.dumps(dict(run=result.testsRun, errors=len(result.errors), failures=len(result.failures), skipped=len(result.skipped),
        failed_tests=[test.id().rsplit('.', 1)[-1] for test, _ in result.errors+result.failures])), flush=True)
    raise SystemExit(0 if result.wasSuccessful() and not result.skipped else 2)
