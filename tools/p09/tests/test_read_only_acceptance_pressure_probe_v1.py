"""No actual product, Native frame, OS sampler, or queue publication in tests."""
import ast
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import read_only_acceptance_pressure_probe_v1 as p


class ProbeContracts(unittest.TestCase):
    def sample(self, cpu=10, ram=60, commit=30):
        return dict(system_cpu_percent=cpu, available_ram_percent=ram,
                    commit_used_percent=commit, parent_private_percent=.2,
                    secret_unapproved_field="MUST_NOT_APPEAR")

    def decision(self, row, hot):
        hot = hot + 1 if row["system_cpu_percent"] >= 98 else 0
        reason = "STOP_LOW_AVAILABLE_RAM" if row["available_ram_percent"] < 8 else (
            "STOP_SYSTEM_COMMIT_PRESSURE" if row["commit_used_percent"] >= 95 else (
            "STOP_SUSTAINED_SYSTEM_CPU" if hot >= 4 else None))
        return hot, reason

    def review(self, rows):
        return p.resource_diagnostics(NS(samples=rows), self.decision)

    def test_low_ram_cause_preserved(self):
        self.assertEqual(self.review([self.sample(ram=7)])["first_original_policy_stop"]["reason"], "STOP_LOW_AVAILABLE_RAM")

    def test_commit_cause_preserved(self):
        self.assertEqual(self.review([self.sample(commit=96)])["first_original_policy_stop"]["reason"], "STOP_SYSTEM_COMMIT_PRESSURE")

    def test_cpu_four_distinct_original_rows(self):
        r = self.review([self.sample(cpu=99) for _ in range(4)])
        self.assertEqual(r["first_original_policy_stop"], dict(index=3, reason="STOP_SUSTAINED_SYSTEM_CPU", hot=4))

    def test_cpu_streak_reset_not_relaxed(self):
        self.assertIsNone(self.review([self.sample(cpu=c) for c in (99, 99, 10, 99, 99)])["first_original_policy_stop"])

    def test_only_approved_fields_no_secret_or_log(self):
        self.assertNotIn("secret_unapproved_field", self.review([self.sample()])["last_original_samples"][0])

    def test_no_samples_is_not_fake_zero(self):
        r = self.review([])
        self.assertIsNone(r["CPU_max"])
        self.assertIsNone(r["available_RAM_min"])
        self.assertEqual(r["last_original_samples"], [])

    def test_history_bound(self):
        with self.assertRaisesRegex(ValueError, "PROBE_RESOURCE_HISTORY_BOUND"):
            self.review([{}] * 4097)

    def test_error_text_is_closed(self):
        self.assertEqual(p.closed_error(ValueError("SAFE_CLOSED_CODE")), "SAFE_CLOSED_CODE")
        self.assertEqual(p.closed_error(ValueError("secret path / token")), "REDACTED_PROBE_FAILURE")
        self.assertEqual(p.closed_error(OSError("private data")), "REDACTED_PROBE_FAILURE")

    def test_decision_errors_are_not_ignored(self):
        with self.assertRaises(KeyError):
            self.review([{}])

    def test_complete_prepare_and_final_hash_not_accept_or_runtime(self):
        tree = ast.parse(Path(p.__file__).read_text(encoding="utf-8"))
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "probe")
        calls = [ast.unparse(n.func) for n in ast.walk(node) if isinstance(n, ast.Call)]
        self.assertIn("m.API.prepare", calls)
        self.assertIn("q.finish", calls)
        self.assertIn("g.check", calls)
        self.assertFalse(any(n.endswith((".accept", ".run_owned", ".worker", ".preflight")) for n in calls))

    def test_single_existing_sampler_no_child_or_thread(self):
        tree = ast.parse(Path(p.__file__).read_text(encoding="utf-8"))
        calls = [ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)]
        self.assertEqual(calls.count("m.a.Guard"), 1)
        self.assertFalse(any(n.endswith((".Thread", ".Popen", ".sample")) for n in calls))

    def fake_runtime(self, error=None):
        events = []
        guard = NS(samples=[self.sample()], cleanup=False)
        guard.acquire = lambda: events.append("original_acquire")
        guard.check = lambda **kw: events.append("original_check")
        def close():
            guard.cleanup = True
            events.append("original_close")
        guard.close = close
        class Reader:
            def __init__(self, root, checkpoint):
                self.checkpoint = checkpoint
                self.snapshots = {}
                self.read_passes = self.bytes_read = self.final_fresh_hashes = 0
            def pin(self, name):
                self.snapshots[name] = dict(path=name, bytes=1, sha256="synthetic_unit_test_only")
            def finish(self):
                self.final_fresh_hashes = len(self.snapshots)
                events.append("all_original_final_hashes")
            def source_snapshot_diagnostics(self):
                return dict(synthetic_unit_test_only=True)
        class Binding:
            def __init__(self, reader, owner):
                events.append("metadata_binding")
            def restore(self):
                events.append("exact_binding_restore")
            def summary(self):
                return dict(synthetic_unit_test_only=True)
        def prepare(q, pin):
            events.append("complete_original_prepare")
            if error is not None:
                raise error
            return dict(state="SYNTHETIC_UNIT_TEST_ONLY_NOT_EVIDENCE"), {}, {}, {}
        runtime = NS(require=lambda ok, code: self.assertTrue(ok, code),
                     base=NS(CONFIG=NS(index=142, before=135), scope=NS(pins=lambda rows, count: rows)),
                     source=NS(root_path=lambda config: "synthetic/root",
                               prior=NS(leaf_bytes=lambda: b"synthetic", prior=NS(metadata=NS(MetadataCheckpoint=Binding))),
                               snapshot=NS(reader_type=lambda base, raw: (Reader, {}))),
                     a=NS(Guard=lambda: guard, AcceptanceReader=Reader),
                     c=NS(ROOT="synthetic_unit_test_only", decision=self.decision),
                     API=NS(prepare=prepare))
        return runtime, events

    def test_prepare_error_cleanup_and_failure_not_success(self):
        runtime, events = self.fake_runtime(ValueError("CURRENT_EPOCH_ACCEPT_ORIGINAL_RESOURCE_STOP"))
        with patch.object(p.time, "sleep", side_effect=AssertionError("NO_RETRY_WAIT")):
            row = p.probe(runtime, dict(path="synthetic/root"))
        self.assertTrue(row["state"].startswith("FAILED_"))
        self.assertEqual(row["stage"], "original_full_prepare")
        self.assertEqual(row["accepted_count_delta"], 0)
        self.assertTrue(row["cleanup_confirmed"])
        self.assertEqual(events[-2:], ["exact_binding_restore", "original_close"])

    def test_probe_success_is_not_queue_acceptance(self):
        runtime, events = self.fake_runtime()
        with patch.object(p.time, "sleep") as sleeper:
            row = p.probe(runtime, dict(path="synthetic/root"))
        sleeper.assert_called_once_with(.5)
        self.assertTrue(row["state"].startswith("PASS_"))
        self.assertFalse(row["queue_acceptance_called"])
        self.assertEqual(row["accepted_count_delta"], 0)
        self.assertIn("all_original_final_hashes", events)
        self.assertEqual(events[-2:], ["exact_binding_restore", "original_close"])

    def test_protected_exception_values_never_leak(self):
        runtime, _ = self.fake_runtime(OSError("unapproved secret text"))
        row = p.probe(runtime, dict(path="synthetic/root"))
        self.assertEqual(row["error_code"], "REDACTED_PROBE_FAILURE")
        self.assertNotIn("unapproved secret text", str(row))


if __name__ == "__main__":
    unittest.main()
