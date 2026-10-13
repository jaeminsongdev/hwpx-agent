"""Small AST/copy boundaries, not execution of authority/timeout/SQL consumer tests."""
import ast
import base64
import copy
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
TARGET = "tools/p09/tests/test_authority_sql_current_audit.py"
METHODS = {
    "test_native_product_or_unrelated_race_promotion_rejected": "original",
    "test_unexecuted_or_wrong_authority_rejected": "original",
    "test_failure_or_post_hash_success_relabelling_rejected": "failed",
    "test_previous_exit_zero_cannot_be_consumer_success": "failed",
    "test_wrong_identity_or_missing_cleanup_rejected": "failed",
}


def trees():
    archive = ROOT / "implementation/p09/source-archive/p09-149-pre-root-only-negative-copies/source-preimages.v1.json"
    row = json.loads(archive.read_text(encoding="utf-8"))["files"][0]
    raw = base64.b64decode(row["base64"], validate=True)
    if row["path"] != TARGET or (len(raw), hashlib.sha256(raw).hexdigest()) != (row["bytes"], row["sha256"]):
        raise ValueError("negative_copy_preimage_not_authenticated")
    return ast.parse(raw.decode("utf-8")), ast.parse((ROOT / TARGET).read_text(encoding="utf-8"))


class NegativeRootCopyTests(unittest.TestCase):
    def test_only_six_declared_copy_sites_changed_whole_ast_otherwise_identical(self):
        original, current = trees()
        counts = {}
        for method in ast.walk(current):
            if not isinstance(method, ast.FunctionDef) or method.name not in METHODS:
                continue
            counts[method.name] = 0
            for node in ast.walk(method):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "dict":
                    self.assertEqual(len(node.args), 1)
                    self.assertFalse(node.keywords)
                    self.assertEqual(ast.dump(node.args[0]), ast.dump(ast.Attribute(
                        value=ast.Name(id="self", ctx=ast.Load()), attr=METHODS[method.name], ctx=ast.Load())))
                    node.func = ast.Attribute(value=ast.Name(id="copy", ctx=ast.Load()), attr="deepcopy", ctx=ast.Load())
                    counts[method.name] += 1
        self.assertEqual(counts, {name: 2 if name == "test_previous_exit_zero_cannot_be_consumer_success" else 1
            for name in METHODS})
        self.assertEqual(sum(counts.values()), 6)
        self.assertEqual(ast.dump(current), ast.dump(original))

    def test_shallow_copy_methods_only_replace_root_fields(self):
        _, tree = trees()
        found = set()
        for method in ast.walk(tree):
            if not isinstance(method, ast.FunctionDef) or method.name not in METHODS:
                continue
            found.add(method.name)
            writes = []
            for node in ast.walk(method):
                if isinstance(node, ast.Subscript) and isinstance(node.ctx, ast.Store):
                    self.assertIsInstance(node.value, ast.Name)
                    self.assertEqual(node.value.id, "bad")
                    writes.append(node)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    self.assertNotIn(node.func.attr, {"pop", "append", "extend", "update", "clear",
                        "remove", "insert", "sort", "reverse", "setdefault", "__setitem__"})
                self.assertNotIsInstance(node, (ast.AugAssign, ast.Delete))
            self.assertTrue(writes)
        self.assertEqual(found, set(METHODS))

    def test_validators_are_unchanged_readonly_not_mutators(self):
        archive = ROOT / "implementation/p09/source-archive/p09-149-pre-single-read-audit/source-preimages.v1.json"
        row = json.loads(archive.read_text(encoding="utf-8"))["files"][0]
        raw = base64.b64decode(row["base64"], validate=True)
        self.assertEqual((len(raw), hashlib.sha256(raw).hexdigest()), (row["bytes"], row["sha256"]))
        before = ast.parse(raw.decode("utf-8"))
        after = ast.parse((ROOT / row["path"]).read_text(encoding="utf-8"))
        for name in ("validate_case", "validate_timeout_failure"):
            old = next(node for node in before.body if isinstance(node, ast.FunctionDef) and node.name == name)
            current = next(node for node in after.body if isinstance(node, ast.FunctionDef) and node.name == name)
            self.assertEqual(ast.dump(old), ast.dump(current))
            for node in ast.walk(current):
                self.assertFalse(isinstance(node, ast.Subscript) and isinstance(node.ctx, (ast.Store, ast.Del)))
                self.assertNotIsInstance(node, (ast.AugAssign, ast.Delete))
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    self.assertNotIn(node.func.attr, {"pop", "append", "extend", "update", "clear",
                        "remove", "insert", "sort", "reverse", "setdefault", "__setitem__"})

    def test_root_replacement_keeps_baseline_and_nested_evidence_intact(self):
        original = {"state": "failed", "flag": False, "probe": {"checks": ["a", "b"]},
            "source_freeze": [{"path": "fixture.rs", "sha256": "0" * 64}], "product_probe": None}
        untouched = copy.deepcopy(original)
        for field, value in (("state", "invented-pass"), ("flag", True), ("product_probe", {"exit_code": 0})):
            bad = dict(original)
            bad[field] = value
            self.assertEqual(original, untouched)
            self.assertIs(bad["source_freeze"], original["source_freeze"])
            self.assertIs(bad["probe"], original["probe"])
            self.assertNotEqual(bad, original)
        # Nested mutation still requires a deep copy, as retained in all other test methods.
        nested = copy.deepcopy(original)
        nested["probe"]["checks"].pop()
        self.assertEqual(original, untouched)


if __name__ == "__main__":
    unittest.main()
