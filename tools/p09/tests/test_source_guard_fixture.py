"""Bounded in-memory fixture lifecycle and AST preservation; no actual SQL or children."""
import ast
import base64
import hashlib
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from audit_evidence_io import AuditEvidenceReader
import source_guard_fixture as subject


class MemorySource:
    def __init__(self, data):
        self.data, self.opens = data, 0

    def open(self, mode):
        assert mode == "rb"
        self.opens += 1
        return io.BytesIO(self.data)


class SourceGuardFixtureTests(unittest.TestCase):
    def environment(self):
        sources = {"fixture/source.rs": MemorySource(b"prefix BEGIN body END suffix\r\n"),
            "fixture/driver.py": MemorySource(b"driver\r\n")}
        readers = []
        def factory(root, checkpoint):
            reader = AuditEvidenceReader(root, checkpoint)
            reader._source = lambda name: sources[name]
            readers.append(reader)
            return reader
        fixture = type("Fixture", (subject.SourceGuardFixture, unittest.TestCase), {
            "SOURCE_FILES": (("source", "fixture/source.rs"), ("driver", "fixture/driver.py")),
            "SOURCE_SLICE": ("BEGIN", "END")})
        return fixture, sources, readers, factory

    def test_many_instances_share_two_initial_reads_and_two_final_reads(self):
        fixture, sources, readers, factory = self.environment()
        with patch.object(subject, "AuditEvidenceReader", side_effect=factory):
            fixture.setUpClass()
            for _ in range(8):
                instance = fixture()
                self.assertEqual(instance.source, "prefix BEGIN body END suffix\n")
                self.assertEqual(instance.driver, "driver\n")
                self.assertEqual(instance.live, "BEGIN body ")
            self.assertEqual([source.opens for source in sources.values()], [1, 1])
            fixture.tearDownClass()
        self.assertEqual([source.opens for source in sources.values()], [2, 2])
        self.assertEqual(readers[0].final_fresh_hashes, 2)
        for name in ("source", "driver", "live", "_source_reader"):
            self.assertNotIn(name, fixture.__dict__)

    def test_next_suite_gets_new_bytes_and_no_cross_run_reader(self):
        fixture, sources, readers, factory = self.environment()
        with patch.object(subject, "AuditEvidenceReader", side_effect=factory):
            fixture.setUpClass()
            fixture.tearDownClass()
            sources["fixture/driver.py"].data = b"fresh driver\n"
            fixture.setUpClass()
            self.assertEqual(fixture().driver, "fresh driver\n")
            fixture.tearDownClass()
        self.assertEqual(len(readers), 2)
        self.assertIsNot(readers[0], readers[1])
        self.assertNotEqual(readers[0].snapshots["fixture/driver.py"], readers[1].snapshots["fixture/driver.py"])

    def test_change_after_initial_read_rejected_and_text_released(self):
        fixture, sources, readers, factory = self.environment()
        with patch.object(subject, "AuditEvidenceReader", side_effect=factory):
            fixture.setUpClass()
            sources["fixture/source.rs"].data += b"changed"
            with self.assertRaisesRegex(ValueError, "^input_changed_during_audit$"):
                fixture.tearDownClass()
        self.assertNotIn("_source_reader", fixture.__dict__)
        self.assertNotIn("source", fixture.__dict__)

    def test_setup_error_does_not_leave_cached_text(self):
        fixture, sources, readers, factory = self.environment()
        sources["fixture/source.rs"].data = b"no markers"
        with patch.object(subject, "AuditEvidenceReader", side_effect=factory):
            with self.assertRaises(ValueError):
                fixture.setUpClass()
        for name in ("source", "driver", "live", "_source_reader"):
            self.assertNotIn(name, fixture.__dict__)

    def test_input_parse_budget_is_not_bypassed_by_fixture(self):
        fixture, sources, readers, factory = self.environment()
        def small(root, checkpoint):
            reader = factory(root, checkpoint)
            reader.maximum_parse_bytes = 4
            return reader
        with patch.object(subject, "AuditEvidenceReader", side_effect=small):
            with self.assertRaisesRegex(ValueError, "^audit_parse_budget_exceeded$"):
                fixture.setUpClass()
        self.assertNotIn("_source_reader", fixture.__dict__)

    def test_invalid_configuration_and_path_rejected_before_read(self):
        for files in ((), [("source", "a"), ("driver", "b")],
                (("source", "../foreign"), ("driver", "b")),
                (("source", "C:/foreign"), ("driver", "b")),
                (("source", "/foreign"), ("driver", "b")),
                (("source", "a\\b"), ("driver", "b")),
                (("wrong", "a"), ("driver", "b"))):
            fixture, _, _, _ = self.environment()
            fixture.SOURCE_FILES = files
            with patch.object(subject, "AuditEvidenceReader") as reader:
                with self.assertRaises(ValueError):
                    fixture.setUpClass()
            reader.assert_not_called()

    def test_overlapping_suite_rejected_and_original_reader_retained(self):
        fixture, _, readers, factory = self.environment()
        with patch.object(subject, "AuditEvidenceReader", side_effect=factory):
            fixture.setUpClass()
            with self.assertRaisesRegex(ValueError, "^source_fixture_lifecycle_overlap$"):
                fixture.setUpClass()
            self.assertIs(fixture._source_reader, readers[0])
            fixture.tearDownClass()

    def test_all_fourteen_original_test_methods_ast_identical(self):
        archive = subject.ROOT / "implementation/p09/source-archive/p09-149-pre-shared-source-fixtures/source-preimages.v1.json"
        rows = json.loads(archive.read_text(encoding="utf-8"))["files"]
        count = 0
        for row in rows[:2]:
            raw = base64.b64decode(row["base64"], validate=True)
            self.assertEqual((len(raw), hashlib.sha256(raw).hexdigest()), (row["bytes"], row["sha256"]))
            before = ast.parse(raw.decode("utf-8"))
            after = ast.parse((subject.ROOT / row["path"]).read_text(encoding="utf-8"))
            tests = lambda tree: {node.name: ast.dump(node) for node in ast.walk(tree)
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")}
            self.assertEqual(tests(before), tests(after))
            count += len(tests(before))
            self.assertFalse(any(isinstance(node, ast.FunctionDef) and node.name == "setUp" for node in ast.walk(after)))
        self.assertEqual(count, 14)

    def test_reader_is_fresh_bounded_and_has_no_subprocess_or_json_cache(self):
        tree = ast.parse(Path(subject.__file__).read_text(encoding="utf-8"))
        self.assertFalse(any(isinstance(node, ast.Name) and node.id in {"subprocess", "lru_cache", "json"}
            for node in ast.walk(tree)))
        reader_calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name) and node.func.id == "AuditEvidenceReader"]
        self.assertEqual(len(reader_calls), 1)
        finish = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute) and node.func.attr == "finish"]
        self.assertEqual(len(finish), 1)

    def test_full_auditor_pins_helpers_and_runs_fixture_boundaries_before_finish(self):
        tree = ast.parse((subject.ROOT / "tools/p09/verify_formula_issuer_authority_current.py").read_text(encoding="utf-8"))
        audit = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "audit")
        loops = [node for node in audit.body if isinstance(node, ast.For)]
        tests = next(node for node in loops if isinstance(node.target, ast.Tuple)
            and [target.id for target in node.target.elts] == ["cls", "count"])
        fixtures = [pair for pair in tests.iter.elts if pair.elts[0].id == "SourceGuardFixtureTests"]
        self.assertEqual(len(fixtures), 1)
        self.assertEqual(fixtures[0].elts[1].value, 10)
        final_pin_loops = [node for node in loops if isinstance(node.target, ast.Name)
            and node.target.id == "path" and node.lineno > tests.end_lineno]
        self.assertEqual(len(final_pin_loops), 1)
        pins = final_pin_loops[0]
        pin_calls = [node for node in ast.walk(pins) if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name) and node.func.id == "pin"]
        self.assertEqual(len(pin_calls), 1)
        self.assertEqual(ast.dump(pin_calls[0].args[0]), ast.dump(ast.Name(id="path", ctx=ast.Load())))
        paths = {node.value for node in pins.iter.elts if isinstance(node, ast.Constant)}
        self.assertTrue({"tools/p09/source_guard_fixture.py", "tools/p09/tests/test_source_guard_fixture.py",
            "tools/p09/tests/test_live_sql_consumer_boundary.py",
            "tools/p09/run_formula_issuer_live_sql_probe.py"}.issubset(paths))
        finish = next(node for node in audit.body if isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute)
            and node.value.func.attr == "finish")
        self.assertLess(tests.lineno, pins.lineno)
        self.assertLess(pins.lineno, finish.lineno)


if __name__ == "__main__":
    unittest.main()
