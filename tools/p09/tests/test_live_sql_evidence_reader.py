"""Exact live reader delta, bounded in-memory fixtures and one immutable manifest read."""
import ast
import base64
import copy
import hashlib
import math
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import conservative_maintenance as c
import sql_percentage_resources as resources_module
from audit_evidence_io import CHUNK_BYTES
from live_sql_evidence_reader import LiveSQLReader, MAX_SCOPE_SECONDS
from audit_evidence_io import AuditEvidenceReader
from tests.test_audit_evidence_io import Source

ARCHIVE = "implementation/p09/source-archive/p09-149-pre-live-sql-paced-reader/source-preimages.v1.json"
DRIVERS = ("tools/p09/run_formula_issuer_live_sql_probe.py", "tools/p09/run_formula_issuer_authority_sql_probe.py")


def dump(node):
    return ast.dump(node, include_attributes=False)


def originals():
    reader = AuditEvidenceReader(c.ROOT, lambda: None)
    rows = {}
    for row in reader.json(ARCHIVE)["files"]:
        raw = base64.b64decode("".join(row["base64_chunks"]), validate=True)
        c.require(len(raw) == row["bytes"] and hashlib.sha256(raw).hexdigest() == row["sha256"], "live_SQL_IO_preimage_drift")
        rows[row["path"]] = ast.parse(raw.decode("utf-8"))
    reader.finish()
    return rows


def expected_driver(old):
    expected = copy.deepcopy(old)
    imported = ast.parse("from live_sql_evidence_reader import LiveSQLReader").body[0]
    index = next(i for i, node in enumerate(expected.body) if isinstance(node, ast.ImportFrom) and node.module == "owned_sql_job")
    expected.body.insert(index+1, imported)
    main = next(node for node in expected.body if isinstance(node, ast.FunctionDef) and node.name == "main")
    index = next(i for i, node in enumerate(main.body) if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "pre_hash_stable_samples" for t in node.targets))
    main.body[index+1:index+1] = ast.parse("reader = LiveSQLReader(resources)\npin = reader.pin").body
    counts = {"json": 0, "text": 0}
    class IOTransform(ast.NodeTransformer):
        def visit_Call(self, node):
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == "json" \
                    and node.func.attr == "loads" and len(node.args) == 1 and isinstance(node.args[0], ast.Call) \
                    and isinstance(node.args[0].func, ast.Attribute) and node.args[0].func.attr == "read_text":
                read = node.args[0]
                c.require(not read.args and len(read.keywords) == 1 and read.keywords[0].arg == "encoding"
                    and read.keywords[0].value.value == "utf-8-sig", "live_SQL_JSON_encoding_delta")
                counts["json"] += 1
                return ast.Call(func=ast.Attribute(value=ast.Name(id="reader", ctx=ast.Load()), attr="json", ctx=ast.Load()),
                    args=[read.func.value], keywords=[])
            if isinstance(node.func, ast.Attribute) and node.func.attr == "read_text":
                c.require(not node.args and len(node.keywords) == 1 and node.keywords[0].arg == "encoding"
                    and node.keywords[0].value.value == "utf-8", "live_SQL_text_encoding_delta")
                counts["text"] += 1
                return ast.Call(func=ast.Attribute(value=ast.Name(id="reader", ctx=ast.Load()), attr="text", ctx=ast.Load()),
                    args=[node.func.value], keywords=[])
            return self.generic_visit(node)
    IOTransform().visit(main)
    c.require(counts == {"json": 4, "text": 9}, "live_SQL_IO_read_inventory_delta")
    additions = next(node.value for node in main.body if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "additions" for t in node.targets))
    index = next(i for i, node in enumerate(additions.elts) if isinstance(node, ast.Constant)
        and node.value == "tools/p09/owned_sql_job.py")
    additions.elts.insert(index+1, ast.Constant(value="tools/p09/live_sql_evidence_reader.py"))
    marker = next(node for node in ast.walk(main) if isinstance(node, ast.Assign) and len(node.targets) == 2
        and all(isinstance(t, ast.Subscript) for t in node.targets)
        and [t.slice.value for t in node.targets] == ["source_freeze_exact_after", "protected_executables_exact_after"])
    outer_try = next(node for node in main.body if isinstance(node, ast.Try) and marker in node.body)
    index = outer_try.body.index(marker)
    outer_try.body[index:index] = ast.parse('reader.finish()\nreceipt["bounded_input_IO"] = reader.summary()').body
    return expected


def restore_live_reader_driver_changes(tree, name):
    from tests.sql_build_driver_delta import restore_build_contract_driver_changes
    try:
        tree = restore_build_contract_driver_changes(tree, name)
    except ValueError as error:
        if str(error) != "SQL_BUILD_NONBINDING_AST_CHANGED":
            raise
        raise ValueError("live_SQL_reader_AST_delta") from None
    old = originals()[name]
    c.require(dump(tree) == dump(expected_driver(old)), "live_SQL_reader_AST_delta")
    return copy.deepcopy(old)


class LiveSQLReaderTests(unittest.TestCase):
    def fixture(self, raw=b'{"a": 1}\r\n'):
        resources = SimpleNamespace(checkpoint_io=Mock())
        reader = LiveSQLReader(resources, clock=lambda: 0)
        source = Source(raw)
        self.addCleanup(patch.stopall)
        patch.object(reader.reader, "_source", return_value=source).start()
        return reader, resources, source

    def test_exact_whole_driver_and_inventory_guard_mutation_rejection(self):
        reader = AuditEvidenceReader(c.ROOT, lambda: None)
        for name in DRIVERS:
            tree = ast.parse(reader.text(name))
            restore_live_reader_driver_changes(tree, name)
            changed = copy.deepcopy(tree)
            guard = next(node for node in ast.walk(changed) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "require" and len(node.args) > 1 and isinstance(node.args[1], ast.Constant)
                and node.args[1].value == "new_build_coverage_missing")
            guard.args[0] = ast.Constant(value=True)
            with self.assertRaisesRegex(ValueError, "^live_SQL_reader_AST_delta$"):
                restore_live_reader_driver_changes(changed, name)
        reader.finish()

    def test_repeated_pin_reads_every_byte_and_finish_is_separate_fresh_pass(self):
        reader, resources, source = self.fixture()
        first = reader.pin("fixture.json")
        self.assertEqual(reader.pin("fixture.json"), first)
        self.assertEqual(reader.json(c.ROOT/"fixture.json"), {"a": 1})
        self.assertEqual(reader.text("fixture.json"), '{"a": 1}\n')
        reader.finish()
        self.assertEqual(source.opens, 5)
        self.assertTrue(all(size == CHUNK_BYTES for size in source.requests))
        self.assertEqual(reader.summary()["final_fresh_hashes"], 1)
        self.assertEqual(reader.summary()["bytes_read"], len(source.raw)*5)
        self.assertGreater(resources.checkpoint_io.call_count, 5)
        with self.assertRaisesRegex(ValueError, "^sql_io_already_finished$"):
            reader.pin("fixture.json")

    def test_repeated_pin_and_finish_reject_changed_input(self):
        for at_finish in (False, True):
            reader, _, source = self.fixture()
            reader.pin("fixture.json")
            source.raw = b'{"a": 2}\r\n'
            with self.assertRaisesRegex(ValueError, "^input_changed_during_audit$"):
                reader.finish() if at_finish else reader.pin("fixture.json")
            self.assertFalse(reader.finished)

    def test_parse_budget_scope_clock_and_resource_failure_are_closed(self):
        reader, resources, _ = self.fixture()
        reader.reader.maximum_parse_bytes = 5
        with self.assertRaisesRegex(ValueError, "^audit_parse_budget_exceeded$"):
            reader.json("fixture.json")
        with self.assertRaisesRegex(ValueError, "^sql_io_path_outside_root$"):
            reader.pin(c.ROOT.parent/"outside.json")
        for now, code in ((MAX_SCOPE_SECONDS+0.001, "STOP_SQL_IO_SCOPE_TIME"), (math.nan, "sql_io_clock_invalid"),
                (-1, "sql_io_clock_invalid")):
            reader.clock = lambda: now
            with self.assertRaisesRegex(ValueError, "^"+code+"$"):
                reader.checkpoint()
        reader.clock = lambda: 0
        resources.checkpoint_io.side_effect = ValueError("STOP_SYSTEM_COMMIT_PRESSURE")
        with self.assertRaisesRegex(ValueError, "^STOP_SYSTEM_COMMIT_PRESSURE$"):
            reader.pin("fixture.json")

    def resource_fixture(self):
        kernel = SimpleNamespace(GetCurrentProcess=Mock(return_value=1))
        resources = resources_module.PercentageResources(SimpleNamespace(mask=1, k=kernel))
        resources.samples = [{"fixture": True}]
        resources.last_sample_at = 0
        resources.sample = Mock()
        return resources

    def test_pre_hash_sampling_is_paced_and_runtime_uses_existing_watcher(self):
        resources = self.resource_fixture()
        with patch.object(resources_module.time, "monotonic", return_value=.49):
            resources.checkpoint_io()
        resources.sample.assert_not_called()
        with patch.object(resources_module.time, "monotonic", return_value=.5):
            resources.checkpoint_io()
        resources.sample.assert_called_once_with()
        resources.sample.reset_mock()
        resources.thread = SimpleNamespace(ident=1, is_alive=Mock(return_value=True))
        with patch.object(resources_module.time, "monotonic", return_value=1):
            resources.checkpoint_io()
        resources.sample.assert_not_called()
        resources.thread.is_alive.return_value = False
        with patch.object(resources_module.time, "monotonic", return_value=1), \
                self.assertRaisesRegex(ValueError, "^STOP_RESOURCE_WATCHER_NOT_ALIVE$"):
            resources.checkpoint_io()

    def test_pre_hash_resource_stop_and_missing_admission_cannot_be_ignored(self):
        resources = self.resource_fixture()
        def stop():
            resources.reason = "STOP_LOW_AVAILABLE_RAM"
            resources.stop.set()
        resources.sample.side_effect = stop
        with patch.object(resources_module.time, "monotonic", return_value=.5), \
                self.assertRaisesRegex(ValueError, "^STOP_LOW_AVAILABLE_RAM$"):
            resources.checkpoint_io()
        resources = self.resource_fixture()
        resources.samples = []
        with self.assertRaisesRegex(ValueError, "^sql_io_without_live_admission$"):
            resources.checkpoint_io()

    def test_original_reader_old_methods_AST_are_unchanged(self):
        old = originals()["tools/p09/audit_evidence_io.py"]
        reader = AuditEvidenceReader(c.ROOT, lambda: None)
        now = ast.parse(reader.text("tools/p09/audit_evidence_io.py"))
        reader.finish()
        cls = next(node for node in now.body if isinstance(node, ast.ClassDef) and node.name == "AuditEvidenceReader")
        new_method = [node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == "fresh_pin"]
        self.assertEqual(len(new_method), 1)
        cls.body.remove(new_method[0])
        self.assertEqual(dump(now), dump(old))


class LiveSQLReaderActualTests(unittest.TestCase):
    def test_immutable_manifest_whole_reads_under_real_pre_hash_admission(self):
        resources = resources_module.PercentageResources()
        self.assertEqual(resources.admit(), 2)
        reader = LiveSQLReader(resources)
        name = "implementation/p09/evidence/p09-77-document-import-active-security.source-progress.v1.json"
        first = reader.pin(name)
        self.assertEqual(first["sha256"], "36b30c931b760bddedb4950c46c8bf7ed84a046dc8998f7f4a51530cfe9f693d")
        self.assertEqual(reader.pin(name), first)
        self.assertEqual(len(reader.json(name)["actual_inputs"]), 36)
        reader.finish()
        self.actual_reader_summary = reader.summary()
        self.assertTrue(reader.finished)
        self.assertEqual(self.actual_reader_summary["read_passes"], 4)
        self.assertEqual(self.actual_reader_summary["bytes_read"], first["bytes"]*4)
        self.assertIsNone(resources.thread.ident)
        self.assertFalse(resources.stop.is_set())


if __name__ == "__main__":
    unittest.main()
