"""P147 declared IO-only delta and synthetic byte binding; never a full audit/tool run."""
import ast
import base64
import copy
import hashlib
import unittest
from unittest.mock import patch

from audit_evidence_io import AuditEvidenceReader, CHUNK_BYTES
from tests.test_audit_evidence_io import Source
from tests.test_live_absence_integration import read_baseline as read_absence_baseline, normalize_live_absence_audit, normalize_live_absence_module
import verify_formula_issuer_live_current as subject

ARCHIVE = "implementation/p09/source-archive/p09-149-pre-live-audit-bound-io/source-preimages.v1.json"
NEW_PINS = ("tools/p09/audit_evidence_io.py", "tools/p09/tests/test_audit_evidence_io.py",
    "tools/p09/tests/test_live_audit_io_integration.py", "tools/p09/verify_live_audit_io_light.py", ARCHIVE)
FINISH = '''try:
    reader.finish()
except ValueError as error:
    if str(error) == "input_changed_during_audit":
        raise ValueError("input_changed_during_current_audit") from None
    raise
'''
PROFILE = '''{"hash_chunk_bytes": 65536, "single_read_json_byte_binding": True,
    "parsed_inputs_cached": False, "read_passes": reader.read_passes, "bytes_read": reader.bytes_read,
    "final_fresh_hashes": reader.final_fresh_hashes, "maximum_parse_bytes": reader.maximum_parse_bytes,
    "io_pacing_bytes_per_second": 8388608, "io_pacing_burst_bytes": 65536,
    "io_pacing_charged_bytes": reader.pacer.bytes_paced,
    "requested_pacing_sleep_seconds": reader.pacer.requested_sleep_seconds}'''


def dump(node):
    return ast.dump(node, include_attributes=False)


def require(ok):
    if not ok:
        raise ValueError("live_io_undeclared_delta")


def function(tree, name):
    return next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)


def normalize_live_audit_io_delta(original, current, absence_before=None):
    """Validate every declared replacement, invert it, then compare the entire audit AST."""
    if any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "inspect_absence"
            for n in ast.walk(current)):
        require(absence_before is not None)
        current = normalize_live_absence_audit(absence_before, current)
    normalized = copy.deepcopy(current)
    require(dump(normalized.body[0]) == dump(ast.parse("originals = {}").body[0]))
    normalized.body[0] = copy.deepcopy(original.body[0])
    setup = ast.parse("reader = AuditEvidenceReader(ROOT, checkpoint)\n"
        "snapshots = reader.snapshots\npin, load = reader.pin, reader.json").body
    for expected in setup:
        matches = [n for n in normalized.body if dump(n) == dump(expected)]
        require(len(matches) == 1)
        normalized.body.remove(matches[0])
    first_pin = next(n for n in normalized.body if isinstance(n, ast.For)
        and isinstance(n.target, ast.Name) and n.target.id == "path")
    removed = [n.value for n in first_pin.iter.elts if isinstance(n, ast.Constant) and n.value in NEW_PINS]
    require(tuple(removed) == NEW_PINS)
    first_pin.iter.elts = [n for n in first_pin.iter.elts
        if not isinstance(n, ast.Constant) or n.value not in NEW_PINS]
    old_defs = [n for n in original.body if isinstance(n, ast.FunctionDef) and n.name in {"pin", "load"}]
    require(len(old_defs) == 2)
    index = normalized.body.index(first_pin)
    normalized.body[index:index] = copy.deepcopy(old_defs)
    auth = [n for n in ast.walk(normalized) if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name) and n.func.id == "authenticate_baseline"]
    require(len(auth) == 1 and dump(auth[0].args[0]) == dump(ast.parse("reader.text(SOURCE)", mode="eval").body))
    auth[0].args[0] = ast.parse('(ROOT / SOURCE).read_text(encoding="utf-8")', mode="eval").body
    for name in ("AuditEvidenceIOTests", "LiveAuditIOIntegrationTests"):
        imports = [n for n in normalized.body if isinstance(n, ast.ImportFrom)
            and len(n.names) == 1 and n.names[0].name == name]
        expected = ast.parse("from tests.test_" + ("audit_evidence_io" if name == "AuditEvidenceIOTests"
            else "live_audit_io_integration") + " import " + name).body[0]
        require(len(imports) == 1 and dump(imports[0]) == dump(expected))
        normalized.body.remove(imports[0])
    loops = [n for n in normalized.body if isinstance(n, ast.For) and isinstance(n.target, ast.Tuple)
        and [t.id for t in n.target.elts] == ["cls", "count"]]
    require(len(loops) == 1)
    loop = loops[0]
    expected_pairs = ast.parse("((AuditEvidenceIOTests, 17), (LiveAuditIOIntegrationTests, 6))", mode="eval").body.elts
    require([dump(n) for n in loop.iter.elts[-2:]] == [dump(n) for n in expected_pairs])
    loop.iter.elts = loop.iter.elts[:-2]
    finish = [n for n in normalized.body if isinstance(n, ast.Try)]
    require(len(finish) == 1 and dump(finish[0]) == dump(ast.parse(FINISH).body[0]))
    old_finish = [n for n in original.body if isinstance(n, ast.For) and isinstance(n.target, ast.Tuple)
        and [n.id for n in n.target.elts] == ["path", "expected"]]
    require(len(old_finish) == 1)
    normalized.body[normalized.body.index(finish[0])] = copy.deepcopy(old_finish[0])
    result = next(n for n in normalized.body if isinstance(n, ast.Return)).value
    positions = [i for i, key in enumerate(result.keys) if isinstance(key, ast.Constant)
        and key.value == "evidence_read_profile"]
    require(len(positions) == 1 and dump(result.values[positions[0]]) == dump(ast.parse(PROFILE, mode="eval").body))
    result.keys.pop(positions[0])
    result.values.pop(positions[0])
    require(dump(normalized) == dump(original))
    return normalized


class LiveAuditIOIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reader = AuditEvidenceReader(subject.ROOT, lambda: None)
        try:
            archive = cls.reader.json(ARCHIVE)
            require(archive["schema_version"] == "hwpx-agent.source-preimages/v1")
            rows = [row for row in archive["files"] if row["path"] == subject.SELF]
            require(len(rows) == 1)
            row = rows[0]
            raw = base64.b64decode("".join(row["base64_chunks"]), validate=True)
            require((len(raw), hashlib.sha256(raw).hexdigest()) == (row["bytes"], row["sha256"]))
            cls.before = ast.parse(raw.decode("utf-8"))
            cls.after = ast.parse(cls.reader.text(subject.SELF))
            cls.after = normalize_live_absence_module(read_absence_baseline(cls.reader), cls.after)
        except BaseException:
            cls.reader = cls.before = cls.after = None
            raise

    @classmethod
    def tearDownClass(cls):
        try:
            cls.reader.finish()
        finally:
            cls.reader = cls.before = cls.after = None

    def bindings(self, source, maximum_parse_bytes=None, checkpoint=lambda: None):
        # Execute only the exact checked reader setup/finalization statements, not audit().
        audit = function(self.after, "audit")
        setup = [n for n in audit.body if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)
            and n.targets[0].id in {"reader", "snapshots"} or isinstance(n, ast.Assign)
            and isinstance(n.targets[0], ast.Tuple) and [t.id for t in n.targets[0].elts] == ["pin", "load"]]
        self.assertEqual(len(setup), 3)
        reader_type = AuditEvidenceReader
        if maximum_parse_bytes is not None:
            reader_type = lambda root, check: AuditEvidenceReader(root, check, maximum_parse_bytes)
        scope = {"ROOT": subject.ROOT, "checkpoint": checkpoint, "AuditEvidenceReader": reader_type}
        exec(compile(ast.Module(body=copy.deepcopy(setup), type_ignores=[]), "<checked-reader-setup>", "exec"), scope)
        patcher = patch.object(scope["reader"], "_source", return_value=source)
        patcher.start()
        self.addCleanup(patcher.stop)
        return scope

    def finish(self, scope):
        exec(compile(ast.Module(body=ast.parse(FINISH).body, type_ignores=[]), "<checked-finish>", "exec"), scope)

    def test_entire_audit_has_only_exact_declared_io_delta(self):
        normalize_live_audit_io_delta(function(self.before, "audit"), function(self.after, "audit"))
        for mutation in ("predicate", "gate", "freshness"):
            changed = copy.deepcopy(function(self.after, "audit"))
            if mutation == "predicate":
                call = next(n for n in ast.walk(changed) if isinstance(n, ast.Call)
                    and isinstance(n.func, ast.Name) and n.func.id == "require"
                    and isinstance(n.args[-1], ast.Constant)
                    and n.args[-1].value == "current_case_pin_inventory")
                call.args[0] = ast.Constant(value=True)
            elif mutation == "gate":
                result = next(n for n in changed.body if isinstance(n, ast.Return)).value
                index = next(i for i, key in enumerate(result.keys) if key.value == "P09_gate")
                result.values[index] = ast.Constant(value="PASS")
            else:
                finalization = next(n for n in changed.body if isinstance(n, ast.Try))
                finalization.body[0] = ast.Pass()
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, "^live_io_undeclared_delta$"):
                normalize_live_audit_io_delta(function(self.before, "audit"), changed)

    def test_non_audit_functions_constants_and_gate_metadata_are_preserved(self):
        functions = lambda tree: {n.name: dump(n) for n in tree.body if isinstance(n, ast.FunctionDef) and n.name != "audit"}
        self.assertEqual(functions(self.before), functions(self.after))
        for old in (n for n in self.before.body if isinstance(n, ast.Assign)):
            actual = next(n for n in self.after.body if isinstance(n, ast.Assign) and dump(n.targets[0]) == dump(old.targets[0]))
            if old.targets[0].id == "ARCHIVES":
                self.assertEqual([dump(n) for n in actual.value.elts[:-1]], [dump(n) for n in old.value.elts])
                self.assertEqual(actual.value.elts[-1].value, "p09-149-pre-live-audit-bound-io")
            else:
                self.assertEqual(dump(old), dump(actual))
        normalized = copy.deepcopy(self.after)
        registry = next(n for n in normalized.body if isinstance(n, ast.ImportFrom)
            and n.module == "run_formula_issuer_registry_sql_checks")
        self.assertEqual(dump(registry), dump(ast.parse(
            "from run_formula_issuer_registry_sql_checks import ROOT, require").body[0]))
        old_registry = next(n for n in self.before.body if isinstance(n, ast.ImportFrom)
            and n.module == registry.module)
        normalized.body[normalized.body.index(registry)] = copy.deepcopy(old_registry)
        reader_imports = [n for n in normalized.body if isinstance(n, ast.ImportFrom)
            and n.module == "audit_evidence_io"]
        self.assertEqual(len(reader_imports), 1)
        self.assertEqual(dump(reader_imports[0]), dump(ast.parse(
            "from audit_evidence_io import AuditEvidenceReader").body[0]))
        normalized.body.remove(reader_imports[0])
        archives = next(n for n in normalized.body if isinstance(n, ast.Assign) and n.targets[0].id == "ARCHIVES")
        archives.value.elts.pop()
        audit = function(normalized, "audit")
        normalized.body[normalized.body.index(audit)] = normalize_live_audit_io_delta(function(self.before, "audit"), audit)
        self.assertEqual(dump(normalized), dump(self.before))

    def test_new_json_parse_and_fresh_hash_use_two_reads_not_three(self):
        source = Source(b'\xef\xbb\xbf{"value":[1]}')
        scope = self.bindings(source)
        first = scope["load"]("fixture.json")
        self.assertEqual(first, {"value": [1]})
        self.assertEqual(source.opens, 1)
        self.assertEqual(scope["pin"]("fixture.json")["sha256"], hashlib.sha256(source.raw).hexdigest())
        self.finish(scope)
        self.assertEqual(source.opens, 2)
        self.assertEqual(scope["reader"].final_fresh_hashes, 1)
        self.assertTrue(all(n == CHUNK_BYTES for n in source.requests))

    def test_drift_before_parse_or_final_hash_is_rejected_with_original_final_code(self):
        source = Source(b'{"value":1}')
        scope = self.bindings(source)
        scope["pin"]("fixture.json")
        source.raw = b'{"value":2}'
        with self.assertRaisesRegex(ValueError, "^input_changed_during_audit$"):
            scope["load"]("fixture.json")
        with self.assertRaisesRegex(ValueError, "^input_changed_during_current_audit$"):
            self.finish(scope)
        self.assertEqual(scope["reader"].final_fresh_hashes, 0)

    def test_parse_errors_budgets_and_resource_stops_are_fail_closed(self):
        for raw, budget, code in ((b'{"private-fixture":', None, "audit_json_invalid"),
                (b'{"value":1}', 4, "audit_parse_budget_exceeded")):
            with self.subTest(code=code):
                source = Source(raw)
                scope = self.bindings(source, budget)
                with self.assertRaisesRegex(ValueError, "^"+code+"$"):
                    scope["load"]("fixture.json")
                self.assertEqual(source.closed, 1)
        source = Source(b'{"value":1}')
        scope = self.bindings(source, checkpoint=lambda: (_ for _ in ()).throw(ValueError("fixture_resource_stop")))
        with self.assertRaisesRegex(ValueError, "^fixture_resource_stop$"):
            scope["load"]("fixture.json")
        self.assertEqual(source.opens, 0)

    def test_mutable_json_is_not_cached_and_text_remains_byte_bound(self):
        source = Source(b'{"value":[1]}')
        scope = self.bindings(source)
        scope["load"]("fixture.json")["value"].append(2)
        self.assertEqual(scope["load"]("fixture.json"), {"value": [1]})
        self.assertEqual(source.opens, 2)
        source.raw = b'first\r\nsecond\rthird\n'
        self.assertEqual(scope["reader"].text("fixture.rs"), "first\nsecond\nthird\n")
        self.assertEqual(scope["snapshots"]["fixture.rs"]["sha256"], hashlib.sha256(source.raw).hexdigest())


if __name__ == "__main__":
    unittest.main()
