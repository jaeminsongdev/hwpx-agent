"""Bounded synthetic contracts; no actual Native/product/queue acceptance."""
import ast
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import optimized_current_queue_acceptance_v2 as r
import owned_source_read_pressure as pressure
SOURCE_BYTES = None


class Contracts(unittest.TestCase):
    def tree(self):
        return ast.parse(Path(r.__file__).read_text(encoding="utf-8"))

    def test_guard_and_original_runner_code_not_replaced(self):
        calls = [ast.unparse(n.func) for n in ast.walk(self.tree()) if isinstance(n, ast.Call)]
        self.assertIn("FunctionType", calls)
        self.assertFalse(any(n.endswith((".sample", ".Thread", ".Popen", ".run_owned", ".worker")) for n in calls))

    def test_complete_original_prepare_precedes_extra_witnesses(self):
        n = next(n for n in ast.walk(self.tree()) if isinstance(n, ast.FunctionDef) and n.name == "prepare")
        self.assertEqual(ast.unparse(n.body[0].value.func), "original_prepare")
        self.assertEqual(ast.unparse(n.body[1].value.func), "qualify")

    def test_private_reader_default_not_mutated(self):
        m = NS(a=NS(AcceptanceReader=pressure.WeightedReader))
        old = m.a.AcceptanceReader
        private, proof = r.reader_runtime(m, SOURCE_BYTES)
        self.assertIs(m.a.AcceptanceReader, old)
        self.assertIsNot(private.a.AcceptanceReader, old)
        self.assertTrue(proof["original_leaf_read_AST_restored_exactly"])

    def test_one_workspace_two_full_fresh_hash_reads(self):
        m = NS(a=NS(AcceptanceReader=pressure.WeightedReader))
        private, _ = r.reader_runtime(m, SOURCE_BYTES)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "small.json"
            path.write_bytes(b'{"value":1}\n')
            reader = private.a.AcceptanceReader(directory, lambda: None)
            first = reader.pin("small.json")
            reader.finish()
            self.assertEqual(reader.read_passes, 2)
            self.assertEqual(reader.final_fresh_hashes, 1)
            self.assertEqual(reader.bytes_read, 2 * path.stat().st_size)
            self.assertEqual(first["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
            summary = r.chunk.summary(reader)
            self.assertEqual(summary["workspace_allocations"], 1)
            self.assertEqual(summary["workspace_bytes"], 65536)
            self.assertEqual(summary["leases"], summary["lease_returns"])
            self.assertFalse(summary["active_lease"])

    def test_publish_preserves_failure_and_float_types(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.json"
            row = dict(state="FAILED_TEST_ONLY_NOT_EVIDENCE", accepted_count_delta=0, sample=0.0)
            pin = r.publish(path, "synthetic", row)
            actual = json.loads(path.read_bytes())
            self.assertEqual(actual, row)
            self.assertIs(type(actual["sample"]), float)
            self.assertEqual(pin["bytes"], path.stat().st_size)

    def test_publish_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.json"
            path.write_bytes(b"original")
            with self.assertRaises(FileExistsError):
                r.publish(path, "synthetic", {})
            self.assertEqual(path.read_bytes(), b"original")

    def test_diagnostic_size_bound_is_not_truncation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.json"
            with self.assertRaisesRegex(ValueError, "DIAGNOSTIC_SIZE_BOUND"):
                r.publish(path, "synthetic", {"data": "x" * r.MAX_DIAGNOSTIC_BYTES})
            self.assertFalse(path.exists())

    def test_traversal_and_wrong_case_paths_rejected(self):
        for name in ("../result.json", "C:/result.json", "implementation/p09/evidence/p09-361-case144-optimized-acceptance-attempt001.v2.json"):
            with self.assertRaisesRegex(ValueError, "EXACT_BOUNDED_DIAGNOSTIC_PATH"):
                r.diagnostic_destination(Path("."), 143, name)

    def test_correct_path_refuses_existing_before_runner(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory) / "implementation/p09/evidence"
            parent.mkdir(parents=True)
            name = "implementation/p09/evidence/p09-361-case143-optimized-acceptance-attempt001.v2.json"
            path = r.diagnostic_destination(directory, 143, name)
            path.write_bytes(b"original")
            with self.assertRaisesRegex(ValueError, "REFUSE_DIAGNOSTIC_OVERWRITE"):
                r.diagnostic_destination(directory, 143, name)

    def test_missing_parent_not_created_implicitly(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "DIAGNOSTIC_PARENT_EXISTS"):
                r.diagnostic_destination(directory, 143, "implementation/p09/evidence/p09-361-case143-optimized-acceptance-attempt001.v2.json")

    def test_failure_is_written_after_original_runner_returns(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory) / "implementation/p09/evidence"
            parent.mkdir(parents=True)
            m = NS(c=NS(ROOT=Path(directory)), base=NS(CONFIG=NS(index=143)))
            fail = dict(state="FAILED_TEST_ONLY_NOT_EVIDENCE", accepted_count_delta=0, cleanup_confirmed=True)
            with patch.object(r, "FunctionType", return_value=lambda *a: dict(fail)):
                row, pin = r.run(m, {}, {}, {}, "implementation/p09/evidence/p09-361-case143-optimized-acceptance-attempt001.v2.json")
            self.assertEqual(row["accepted_count_delta"], 0)
            self.assertTrue((Path(directory) / pin["path"]).is_file())

    def test_no_automatic_retry(self):
        calls = [ast.unparse(n.func) for n in ast.walk(self.tree()) if isinstance(n, ast.Call)]
        self.assertEqual(calls.count("runner"), 1)
        self.assertFalse(any(n.endswith(".sleep") for n in calls))

    def test_new_code_is_acceptance_witness_not_native_rebase(self):
        self.assertIn("diagnostic_is_not_additional_product_or_Native_evidence", Path(r.__file__).read_text(encoding="utf-8"))

    def test_source_projection_rejects_wrong_leaf(self):
        with self.assertRaises(ValueError):
            r.reader_runtime(NS(a=NS(AcceptanceReader=pressure.WeightedReader)), b"wrong")

    def test_persistent_write_is_after_runner(self):
        n = next(n for n in self.tree().body if isinstance(n, ast.FunctionDef) and n.name == "run")
        calls = {node.func.id: node.lineno for node in ast.walk(n)
                 if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                 and node.func.id in ("runner", "publish")}
        self.assertEqual(set(calls), {"runner", "publish"})
        self.assertLess(calls["runner"], calls["publish"])

    def test_no_delete_move_or_os_configuration(self):
        calls = [ast.unparse(n.func) for n in ast.walk(self.tree()) if isinstance(n, ast.Call)]
        self.assertFalse(any(n.endswith((".unlink", ".remove", ".rename", ".replace", ".system")) for n in calls))

    def test_non_current_case_and_bool_rejected(self):
        for index in (True, 133, 250):
            with self.assertRaisesRegex(ValueError, "CURRENT_CASE_RANGE"):
                r.diagnostic_destination(Path("."), index, "synthetic")

    def test_unexpected_runner_error_persisted_without_exception_text(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory) / "implementation/p09/evidence"
            parent.mkdir(parents=True)
            m = NS(c=NS(ROOT=Path(directory)), base=NS(CONFIG=NS(index=143)))
            def broken(*args):
                raise OSError("private unapproved details")
            with patch.object(r, "FunctionType", return_value=broken):
                row, pin = r.run(m, {}, {}, {}, "implementation/p09/evidence/p09-361-case143-optimized-acceptance-attempt001.v2.json")
            self.assertEqual(row["accepted_count_delta"], 0)
            self.assertNotIn("private unapproved details", str(row))
            self.assertTrue((Path(directory) / pin["path"]).is_file())


if __name__ == "__main__":
    unittest.main()
