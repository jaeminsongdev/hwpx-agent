import ast
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import optimized_current_queue_acceptance_v3 as v3
from test_terminal_metadata_pressure_v1 import Original


class Tests(unittest.TestCase):
    def projected(self, prepare=lambda q: "whole-original-result"):
        def execute(): return prepare(None)
        # Fixture with prepare in globals, exactly as original projected runner.
        from types import FunctionType
        execute = FunctionType((lambda: None).__code__, {"prepare": prepare})
        state = NS(guards=[])
        original = NS(a=NS(Guard=Original))
        captured = []
        def prior(private, *args):
            captured.append(private)
            state.guards.append(private.a.Guard())
            return execute, state
        with patch.object(v3.prior, "projection", prior):
            result, returned = v3.projection(original, b"leaf", {}, {}, {}, {}, b"leaf")
        return original, execute, result, state, returned, captured

    def test_projection_preserves_original_bytecode(self):
        _, old, new, state, returned, _ = self.projected()
        self.assertIs(new.__code__, old.__code__)
        self.assertIs(returned, state)

    def test_projection_not_mutate_original_prepare(self):
        _, old, new, _, _, _ = self.projected()
        self.assertIsNot(new.__globals__, old.__globals__)
        self.assertIsNot(new.__globals__["prepare"], old.__globals__["prepare"])

    def test_full_original_prepare_before_new_qualification(self):
        calls = []
        _, _, new, _, _, _ = self.projected(lambda q: calls.append("whole") or 123)
        with patch.object(v3, "qualify", lambda *args: calls.append("qualify")):
            self.assertEqual(new.__globals__["prepare"](None), 123)
        self.assertEqual(calls, ["whole", "qualify"])

    def test_original_prepare_error_not_skipped(self):
        def fail(q): raise ValueError("ORIGINAL_FULL_ORACLE_FAILED")
        _, _, new, _, _, _ = self.projected(fail)
        with patch.object(v3, "qualify") as qualify:
            with self.assertRaisesRegex(ValueError, "ORIGINAL_FULL_ORACLE_FAILED"):
                new.__globals__["prepare"](None)
            qualify.assert_not_called()

    def test_private_guard_extends_prior_factories(self):
        original, _, _, state, _, captured = self.projected()
        self.assertIs(original.a.Guard, Original)
        self.assertIsNot(captured[0].a.Guard, Original)
        state.guards[0].value = 100
        with self.assertRaisesRegex(ValueError, "STOP_TERMINAL_METADATA_WARNING"):
            state.guards[0].check(force=True)

    def test_wrong_qualification_path_closed(self):
        with self.assertRaisesRegex(ValueError, "EXACT_QUALIFICATION_PATH"):
            v3.qualify(None, None, dict(path="other"))

    def test_run_reuses_exact_prior_runner_and_publisher(self):
        def runner(m, rp, op, np, name):
            execute, state = projection(m, b"raw", rp, op, np, b"leaf")
            row = dict(state="PASS_FIXTURE_NOT_PRODUCT")
            receipt = publish("destination", name, row)
            return row, receipt
        state = NS(guards=[v3.pressure.guard_type(Original)()])
        state.guards[0].check()
        with patch.object(v3.prior, "run", runner), \
             patch.object(v3, "projection", return_value=(lambda: None, state)), \
             patch.object(v3.prior, "publish", return_value={"fixture": True}) as publisher:
            row, receipt = v3.run(None, {}, {}, {}, {"terminal": True}, "diagnostic")
        publisher.assert_called_once()
        self.assertTrue(receipt["fixture"])
        self.assertEqual(row["terminal_pressure_guard_diagnostics"][0]["checks"], 1)
        self.assertEqual(row["terminal_pressure_code_qualification_pin"], {"terminal": True})

    def test_preserve_v2_diagnostic_failure(self):
        def fail(*args): raise ValueError("EXCLUSIVE_DIAGNOSTIC_EXISTS")
        with patch.object(v3.prior, "run", fail):
            with self.assertRaisesRegex(ValueError, "EXCLUSIVE_DIAGNOSTIC_EXISTS"):
                v3.run(None, {}, {}, {}, {}, "diagnostic")

    def test_no_extra_sampling_process_or_wait_code(self):
        source = Path(v3.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        forbidden = {"sleep", "Popen", "Thread", "sample", "check_output", "system", "kill"}
        calls = [n.func.attr if isinstance(n.func, ast.Attribute) else n.func.id
                 for n in ast.walk(tree) if isinstance(n, ast.Call)
                 and isinstance(n.func, (ast.Attribute, ast.Name))]
        self.assertFalse(set(calls) & forbidden)
        self.assertEqual(v3.CODE_PATHS, (v3.pressure.SELF, v3.pressure.TEST, v3.SELF, v3.TEST))


if __name__ == "__main__": unittest.main()
