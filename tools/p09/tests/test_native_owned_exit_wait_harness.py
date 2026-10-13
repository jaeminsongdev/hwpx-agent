from pathlib import Path
import unittest
from tools.p09 import qualify_native_form_diagnostic_batch as q
ROOT=q.ROOT
NEW="implementation/p09/tools/run-hancom-2020-field-auto-number-target-owned-exit-wait.ps1"
WAIT='''    # Quit 호출 이후의 실제 프로세스 종료만 기다린다. 강제 종료나 증거 보정은 하지 않는다.
    $ownedExitWait = [Diagnostics.Stopwatch]::StartNew()
    while ([int]$trace.remaining_hwp_process_count -ne 0 -and $ownedExitWait.ElapsedMilliseconds -lt 10000) {
        Start-Sleep -Milliseconds 100
        $trace.remaining_hwp_process_count = @(
            Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue
        ).Count
    }
    $ownedExitWait.Stop()
'''.encode()
class NativeOwnedExitWaitHarnessTests(unittest.TestCase):
    def test_whole_original_inverse_and_only_bounded_read_only_wait_inserted(self):
        original=q.public.checked(ROOT/q.q.HARNESS,q.q.HARNESS_SHA)
        current=q.public.bounded_bytes(ROOT/NEW,65536)
        self.assertEqual(current.count(WAIT),1)
        self.assertEqual(current.replace(WAIT,b"",1),original)
        self.assertLess(current.index(WAIT),current.index(b"$trace.completed_at_utc"))
        self.assertGreater(current.index(WAIT),current.index(b"Start-Sleep -Milliseconds 500"))
    def test_final_zero_process_requirement_and_failed_exit_unchanged(self):
        current=q.public.bounded_bytes(ROOT/NEW,65536)
        self.assertIn(b"if ($trace.state -ne 'pass' -or [int]$trace.remaining_hwp_process_count -ne 0) { exit 2 }",current)
        self.assertNotIn(b"Stop-Process",current);self.assertNotIn(b"taskkill",current)
        self.assertNotIn(b"remaining_hwp_process_count = 0",current)
        self.assertNotIn(b"Set-ItemProperty",current)
    def test_actual_rejected_c07_trace_remains_one_not_rewritten(self):
        path=q.attempt_paths("p09-35-20261003-r03")[6]
        import json
        trace=json.loads(q.public.bounded_bytes(path/"target-trace.json",131072),object_pairs_hook=q.q.shared.lifecycle.duplicate_guard)
        self.assertEqual(trace["remaining_hwp_process_count"],1)
        manifest=q.q.shared.lifecycle.checked_json(ROOT/q.MANIFEST,q.MANIFEST_SHA)
        with self.assertRaises(ValueError):q.verify_case_trace(trace,manifest["cases"][6])
if __name__=="__main__":unittest.main()
