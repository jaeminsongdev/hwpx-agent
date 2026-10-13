"""Closed readonly tool wiring and preserved audit conditions, never a full audit."""
import ast
import base64
import copy
import hashlib
from pathlib import Path
import subprocess
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from audit_evidence_io import AuditEvidenceReader
from tests.test_live_audit_io_integration import normalize_live_audit_io_delta
from tests.test_live_absence_integration import read_baseline as read_absence_baseline
import verify_formula_issuer_authority_current as authority
import verify_formula_issuer_live_current as live

ROOT = Path(__file__).resolve().parents[3]
ARCHIVE = "implementation/p09/source-archive/p09-149-pre-bounded-audit-integration/source-preimages.v1.json"
SUBJECTS = (
    (authority, "tools/p09/verify_formula_issuer_authority_current.py", "authenticate_authority_delta"),
    (live, "tools/p09/verify_formula_issuer_live_current.py", "authenticate_baseline"),
)


def function(tree, name):
    return next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)


def dump(node):
    return ast.dump(node, include_attributes=False)


class BoundedAuditToolIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reader = AuditEvidenceReader(ROOT, lambda: None)
        try:
            archive = cls.reader.json(ARCHIVE)
            if archive["schema_version"] != "hwpx-agent.source-preimages/v1":
                raise ValueError("integration_archive_schema")
            cls.trees = {}
            for _, path, _ in SUBJECTS:
                rows = [row for row in archive["files"] if row["path"] == path]
                if len(rows) != 1:
                    raise ValueError("integration_archive_scope")
                row = rows[0]
                raw = base64.b64decode("".join(row["base64_chunks"]), validate=True)
                if (len(raw), hashlib.sha256(raw).hexdigest()) != (row["bytes"], row["sha256"]):
                    raise ValueError("integration_archive_identity")
                cls.trees[path] = (ast.parse(raw.decode("utf-8")), ast.parse(cls.reader.text(path)))
            io_archive = cls.reader.json("implementation/p09/source-archive/p09-149-pre-live-audit-bound-io/source-preimages.v1.json")
            rows = [row for row in io_archive["files"] if row["path"] == live.SELF]
            if io_archive["schema_version"] != "hwpx-agent.source-preimages/v1" or len(rows) != 1:
                raise ValueError("integration_io_archive_scope")
            raw = base64.b64decode("".join(rows[0]["base64_chunks"]), validate=True)
            if (len(raw), hashlib.sha256(raw).hexdigest()) != (rows[0]["bytes"], rows[0]["sha256"]):
                raise ValueError("integration_io_archive_identity")
            cls.live_io_before = ast.parse(raw.decode("utf-8"))
            cls.live_absence_before = read_absence_baseline(cls.reader)
        except BaseException:
            cls.reader = None
            cls.trees = {}
            cls.live_io_before = None
            cls.live_absence_before = None
            raise

    @classmethod
    def tearDownClass(cls):
        try:
            cls.reader.finish()
        finally:
            cls.reader = None
            cls.trees = {}
            cls.live_io_before = None
            cls.live_absence_before = None

    def test_non_audit_functions_and_declared_authentication_transform_are_preserved(self):
        for _, path, auth_name in SUBJECTS:
            before, after = self.trees[path]
            old_functions = {node.name: node for node in before.body if isinstance(node, ast.FunctionDef)}
            current_functions = {node.name: node for node in after.body if isinstance(node, ast.FunctionDef)}
            self.assertEqual(set(old_functions), set(current_functions))
            for name, old in old_functions.items():
                if name == "audit":
                    continue
                new = copy.deepcopy(current_functions[name])
                if name == auth_name:
                    self.assertEqual(new.args.args[-1].arg, "checkpoint")
                    self.assertEqual(dump(new.args.defaults[-1]), dump(ast.Constant(value=None)))
                    new.args.args.pop()
                    new.args.defaults.pop()
                    self.assertEqual(dump(new.body.pop()), dump(ast.Return(value=ast.Attribute(
                        value=ast.Name(id="formatted", ctx=ast.Load()), attr="audit_limits", ctx=ast.Load()))))
                    old_format = next(n for n in old.body if isinstance(n, ast.Assign)
                        and isinstance(n.targets[0], ast.Name) and n.targets[0].id == "formatted")
                    new_format = next(n for n in new.body if isinstance(n, ast.Assign)
                        and isinstance(n.targets[0], ast.Name) and n.targets[0].id == "formatted")
                    new_format.value = copy.deepcopy(old_format.value)
                self.assertEqual(dump(old), dump(new), (path, name))
            for old in (node for node in before.body if isinstance(node, ast.Assign)):
                target = dump(old.targets[0])
                new = next(node for node in after.body if isinstance(node, ast.Assign) and dump(node.targets[0]) == target)
                if isinstance(old.targets[0], ast.Name) and old.targets[0].id == "ARCHIVES":
                    additions = ["p09-149-pre-bounded-audit-integration"]
                    if path == live.SELF:
                        additions.append("p09-149-pre-live-audit-bound-io")
                        additions.append("p09-149-pre-live-bounded-absence")
                    self.assertEqual([dump(n) for n in new.value.elts[:-len(additions)]], [dump(n) for n in old.value.elts])
                    self.assertEqual([n.value for n in new.value.elts[-len(additions):]], additions)
                else:
                    self.assertEqual(dump(old), dump(new))

    def test_formatter_task_exact_input_and_checkpoint_are_forwarded(self):
        for _, path, name in SUBJECTS:
            node = function(self.trees[path][1], name)
            formatted = next(n for n in node.body if isinstance(n, ast.Assign)
                and isinstance(n.targets[0], ast.Name) and n.targets[0].id == "formatted")
            expected = ast.parse('run_audit_tool("rustfmt-stdin", current, checkpoint=checkpoint)', mode="eval").body
            self.assertEqual(dump(formatted.value), dump(expected))

    def test_inventory_task_is_closed_and_legacy_formatter_inventory_spawns_are_absent(self):
        for _, path, _ in SUBJECTS:
            after = self.trees[path][1]
            audit = function(after, "audit")
            inventory = next(n for n in audit.body if isinstance(n, ast.Assign)
                and isinstance(n.targets[0], ast.Name) and n.targets[0].id == "indexed")
            expected = ast.parse('run_audit_tool("rust-input-inventory", checkpoint=checkpoint)', mode="eval").body
            self.assertEqual(dump(inventory.value), dump(expected))
            for call in (n for n in ast.walk(after) if isinstance(n, ast.Call)):
                if isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name) \
                        and call.func.value.id == "subprocess" and call.func.attr in {"run", "Popen", "call"}:
                    if call.args and isinstance(call.args[0], ast.List) and call.args[0].elts \
                            and isinstance(call.args[0].elts[0], ast.Constant):
                        self.assertNotIn(call.args[0].elts[0].value, {"rustfmt", "rg"})

    def test_existing_audit_require_predicates_and_failure_codes_are_unchanged(self):
        def requirements(tree):
            audit = copy.deepcopy(function(tree, "audit"))
            audit.body = [n for n in audit.body if not isinstance(n, ast.FunctionDef) or n.name != "checkpoint"]
            return [dump(n) for n in ast.walk(audit) if isinstance(n, ast.Call)
                and isinstance(n.func, ast.Name) and n.func.id == "require"
                and not (n.args and isinstance(n.args[-1], ast.Constant)
                    and n.args[-1].value == "bounded_readonly_tools_failed")]
        for _, path, _ in SUBJECTS:
            before, after = self.trees[path]
            if path == live.SELF:
                after = copy.deepcopy(after)
                audit = function(after, "audit")
                after.body[after.body.index(audit)] = normalize_live_audit_io_delta(
                    function(self.live_io_before, "audit"), audit,
                    absence_before=function(self.live_absence_before, "audit"))
            self.assertEqual(requirements(before), requirements(after), path)

    def test_transitive_helpers_and_integration_evidence_are_freshly_pinned(self):
        required = {"tools/p09/bounded_audit_tools.py", "tools/p09/tests/test_bounded_audit_tools.py",
            "tools/p09/conservative_maintenance.py", "tools/p09/verify_audit_evidence_io.py",
            "tools/p09/verify_bounded_audit_tools_light.py", "tools/p09/tests/test_bounded_audit_tool_integration.py",
            "tools/p09/verify_bounded_audit_tool_integration_light.py", ARCHIVE}
        for _, path, _ in SUBJECTS:
            audit = function(self.trees[path][1], "audit")
            pin_loop = next(n for n in audit.body if isinstance(n, ast.For)
                and isinstance(n.target, ast.Name) and n.target.id == "path" and isinstance(n.iter, ast.Tuple)
                and any(isinstance(b, ast.Expr) and isinstance(b.value, ast.Call)
                    and isinstance(b.value.func, ast.Name) and b.value.func.id == "pin" for b in n.body))
            literals = {n.value for n in pin_loop.iter.elts if isinstance(n, ast.Constant)}
            self.assertTrue(required.issubset(literals), (path, required-literals))
            first_auth = next(index for index, node in enumerate(audit.body)
                if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Attribute) and node.value.func.attr == "append")
            self.assertLess(audit.body.index(pin_loop), first_auth)
            config_loop = next(n for n in audit.body if isinstance(n, ast.For) and isinstance(n.iter, ast.Tuple)
                and any(isinstance(v, ast.Constant) and v.value == "rustfmt.toml" for v in n.iter.elts))
            self.assertLess(audit.body.index(config_loop), first_auth)

    def invoke_authentication(self, module, name, completed=None, error=None):
        checkpoint = Mock()
        with patch.object(module, "remove_block", side_effect=lambda text, *args: text), \
                patch.object(module, "replace_one", side_effect=lambda text, *args: text), \
                patch.object(module, "run_audit_tool", return_value=completed, side_effect=error) as tool:
            result = getattr(module, name)("fn fixture() {}\n", b"fn fixture() {}\n", checkpoint=checkpoint)
        tool.assert_called_once_with("rustfmt-stdin", "fn fixture() {}\n", checkpoint=checkpoint)
        return result

    def test_mock_formatter_keeps_exact_original_comparison_and_rejects_exit_stderr_or_delta(self):
        for module, _, name in SUBJECTS:
            profile = {"task": "rustfmt-stdin", "owned_tree_empty": True, "cleanup_confirmed": True}
            result = SimpleNamespace(returncode=0, stdout="fn fixture() {}\n", stderr="", audit_limits=profile)
            self.assertIs(self.invoke_authentication(module, name, result), profile)
            for exit_code, output, errors in ((1, result.stdout, ""), (0, result.stdout, "diagnostic"),
                    (0, "changed\n", "")):
                bad = SimpleNamespace(returncode=exit_code, stdout=output, stderr=errors, audit_limits=profile)
                with self.assertRaisesRegex(ValueError, "^original_(approval_)?consumer_undeclared_delta$"):
                    self.invoke_authentication(module, name, bad)

    def test_resource_failure_keeps_same_exception_and_owned_profile_without_fallback(self):
        for module, _, name in SUBJECTS:
            error = ValueError("STOP_LOW_AVAILABLE_RAM")
            error.audit_limits = {"worker_created": False, "job_private_peak_mib": None}
            with self.assertRaisesRegex(ValueError, "^STOP_LOW_AVAILABLE_RAM$") as caught:
                self.invoke_authentication(module, name, error=error)
            self.assertIs(caught.exception, error)
            self.assertIs(caught.exception.audit_limits, error.audit_limits)
            source = (ROOT / module.SELF).read_text(encoding="utf-8")
            self.assertIn('getattr(error, "audit_limits", None)', source)
            self.assertIn('failure["readonly_tool_failure_profile"] = tool_profile', source)

    def test_original_return_evidence_and_open_gates_are_preserved_with_additive_profiles(self):
        additions = {"readonly_tool_profiles", "bounded_readonly_tool_checks", "bounded_readonly_integration_checks"}
        for _, path, _ in SUBJECTS:
            before, after = self.trees[path]
            if path == live.SELF:
                after = copy.deepcopy(after)
                audit = function(after, "audit")
                after.body[after.body.index(audit)] = normalize_live_audit_io_delta(
                    function(self.live_io_before, "audit"), audit,
                    absence_before=function(self.live_absence_before, "audit"))
            old = next(n for n in function(before, "audit").body if isinstance(n, ast.Return)).value
            new = copy.deepcopy(next(n for n in function(after, "audit").body if isinstance(n, ast.Return)).value)
            pairs = [(key, value) for key, value in zip(new.keys, new.values) if key.value not in additions]
            self.assertEqual({key.value for key in new.keys}-{key.value for key in old.keys}, additions)
            new.keys, new.values = [key for key, _ in pairs], [value for _, value in pairs]
            self.assertEqual(dump(old), dump(new), path)


if __name__ == "__main__":
    unittest.main()
