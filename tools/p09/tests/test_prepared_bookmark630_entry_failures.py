"""Only new entry exception handling. No Native constructor, files or process IO."""
import io
import json
from contextlib import ExitStack, redirect_stdout
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import run_prepared_bookmark_native630 as entry


class Contracts(unittest.TestCase):
    def check_failure(self, error):
        guard = NS(acquire=Mock(side_effect=error), close=Mock(), samples=[], cleanup=True,
                   section_summary=lambda: dict(failed=True))
        retained = {}
        def retain(root, spool, row):
            retained.update(row)
            return row, dict(model=True)
        with ExitStack() as stack:
            stack.enter_context(patch.object(entry.runtime.prepared, 'require_absent'))
            stack.enter_context(patch.object(entry.runtime, 'absent'))
            stack.enter_context(patch.object(entry.r.tools, 'select_own_single_cpu', return_value=dict(model=True)))
            stack.enter_context(patch.object(entry.r.shared.host, 'configure_host_policy'))
            stack.enter_context(patch.object(entry.runtime.sections, 'guard_type', return_value=lambda: guard))
            stack.enter_context(patch.object(entry.retention, 'retain', side_effect=retain))
            publish = stack.enter_context(patch.object(entry, 'publish', return_value=dict(model=True)))
            native = stack.enter_context(patch.object(entry.runtime, 'execute', side_effect=AssertionError('NATIVE_MUST_NOT_RUN')))
            output = io.StringIO()
            with redirect_stdout(output):
                status = entry.main(['--execute-prepared-eight-once'])
        self.assertEqual(status, 2)
        self.assertEqual(retained['state'], 'FAILED630_PREPARED_NATIVE_CAPTURE')
        self.assertIs(retained['fixed_eight_executed'], False)
        self.assertIs(retained['native_claim_created'], False)
        self.assertIs(retained['rerun_forbidden'], True)
        self.assertIs(retained['reference_semantics_qualified'], False)
        self.assertEqual(retained['error_type'], type(error).__name__)
        self.assertNotIn('PRIVATE VALUE', json.dumps(retained))
        self.assertEqual(publish.call_count, 1)
        native.assert_not_called()
        guard.close.assert_called_once()
        self.assertEqual(json.loads(output.getvalue())['state'], retained['state'])
    def test_timeout_is_recorded_without_traceback_or_native_claim(self):
        self.check_failure(subprocess.TimeoutExpired(['PRIVATE VALUE'], 2))
    def test_os_error_is_recorded_without_native_or_raw_values(self):
        self.check_failure(OSError('PRIVATE VALUE'))
    def test_interrupt_is_recorded_and_forbids_replay(self):
        self.check_failure(KeyboardInterrupt())


if __name__ == '__main__':
    result = unittest.TextTestRunner(stream=io.StringIO()).run(unittest.defaultTestLoader.loadTestsFromTestCase(Contracts))
    print(json.dumps(dict(run=result.testsRun, errors=len(result.errors), failures=len(result.failures), skipped=len(result.skipped),
        failed_tests=[test.id().rsplit('.', 1)[-1] for test, _ in result.errors+result.failures])), flush=True)
    raise SystemExit(0 if result.wasSuccessful() and not result.skipped else 2)
