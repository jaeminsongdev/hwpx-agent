"""Original22 contracts and five explicit bootstrap/environment regressions."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import case160_attempt_controller as controller

MODULE, AST_PROOF, current = controller.test_namespace()


class Tests(MODULE.Tests):
    def test_run004_default_identity_preserved(self):
        self.assertEqual(controller.base.RETRY.task(160), "case160-current-r004-tests")
        self.assertEqual(current.RETRY.task(160), "case160-current-r006-tests")
        self.assertNotEqual(current.RETRY.root_path(current.old.base.CONFIG), controller.base.attempt.ROOT)

    def test_legacy_initial_reads_precede_current_admission(self):
        required = {p["path"]:p for p in controller.LEGACY_PINS}
        class Reader:
            def __init__(self):
                self.snapshots = {}; self.final_fresh_hashes = 0
            def checkpoint(self): pass
            def pin(self, path):
                value = dict(required[path]); self.snapshots[path] = value; return value
            def json(self, path): raise OSError("current DATA deliberately unavailable")
        q = Reader()
        with self.assertRaises(OSError): current.owned(q)
        self.assertEqual(q.snapshots, required)
        for path in ("tools/p09/tests/test_case112_current_stored_runtime.py", "tools/p09/tests/test_current_stored_native_bridge.py"):
            self.assertIn(path, q.snapshots)

    def test_closed_wrong_attempt_configuration_rejected(self):
        row, _ = controller.read_config()
        row["physical_product_run"] = 5
        with self.assertRaises(ValueError): controller.validate_config(row)

    def test_actual_binding_function_uses_current_dependencies(self):
        self.assertIs(current.binding.__globals__["binding_module"], current.binding_module)
        self.assertIs(current.binding.__globals__["_env"], current._env)
        self.assertIs(current.binding.__globals__["owned"], current.owned)

    def test_independent_oracle_function_uses_current_dependencies(self):
        self.assertIs(current.prepare_candidate.__globals__["M"], current.M)
        self.assertIs(current.prepare_candidate.__globals__["API"], current.API)
        self.assertIs(current.prepare_candidate.__globals__["binding"], current.binding)


if __name__ == "__main__": unittest.main()
