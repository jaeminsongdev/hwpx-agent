"""Factory ownership and original-acceptor preservation, no actual acceptance."""
import ast
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace as NS

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import optimized_current_queue_acceptance_v1 as o


class Contracts(unittest.TestCase):
    def model(self):
        events = []
        class Guard:
            def __init__(self):
                self.samples = []
                self.cleanup = False
            def check(self):
                events.append("original_hard_check")
            def close(self):
                self.cleanup = True
                events.append("original_close")
        class Reader:
            def __init__(self, root, checkpoint):
                self.checkpoint = checkpoint
        class Binding:
            def __init__(self, reader, owner):
                self.restored = False
                self.original = reader.checkpoint
                self.reader = reader
                reader.checkpoint = self
            def restore(self):
                self.reader.checkpoint = self.original
                self.restored = True
                events.append("exact_restore")
        m = NS(a=NS(Guard=Guard, AcceptanceReader=Reader),
               source=NS(snapshot=NS(reader_type=lambda base, raw: (base, {})),
                         prior=NS(prior=NS(metadata=NS(MetadataCheckpoint=Binding)))))
        return m, events

    def test_one_original_guard_only(self):
        m, _ = self.model()
        Guard, Reader, state = o.factories(m, b"synthetic_unit_test_only")
        g = Guard()
        with self.assertRaisesRegex(ValueError, "ONE_ORIGINAL_SAMPLER"):
            Guard()
        g.close()

    def test_reader_requires_original_owner(self):
        m, _ = self.model()
        Guard, Reader, state = o.factories(m, b"synthetic_unit_test_only")
        g = Guard()
        with self.assertRaisesRegex(ValueError, "SAME_ORIGINAL_OWNER"):
            Reader("synthetic", lambda: None)
        g.close()

    def test_no_reader_before_owner(self):
        m, _ = self.model()
        Guard, Reader, state = o.factories(m, b"synthetic_unit_test_only")
        with self.assertRaisesRegex(ValueError, "ONE_READER_AND_OWNER"):
            Reader("synthetic", lambda: None)

    def test_one_reader_only(self):
        m, _ = self.model()
        Guard, Reader, state = o.factories(m, b"synthetic_unit_test_only")
        g = Guard()
        Reader("synthetic", g.check)
        with self.assertRaisesRegex(ValueError, "ONE_READER_AND_OWNER"):
            Reader("synthetic", g.check)
        g.close()

    def test_unconditional_restore_before_original_close(self):
        m, events = self.model()
        Guard, Reader, state = o.factories(m, b"synthetic_unit_test_only")
        g = Guard()
        reader = Reader("synthetic", g.check)
        original = state.bindings[0].original
        g.close()
        self.assertIs(reader.checkpoint, original)
        self.assertEqual(events, ["exact_restore", "original_close"])
        self.assertTrue(g.cleanup)

    def test_original_default_classes_not_mutated(self):
        m, _ = self.model()
        old_guard, old_reader = m.a.Guard, m.a.AcceptanceReader
        o.factories(m, b"synthetic_unit_test_only")
        self.assertIs(m.a.Guard, old_guard)
        self.assertIs(m.a.AcceptanceReader, old_reader)

    def tree(self):
        return ast.parse(Path(o.__file__).read_text(encoding="utf-8"))

    def test_projection_calls_whole_prepare_before_qualification(self):
        node = next(n for n in ast.walk(self.tree()) if isinstance(n, ast.FunctionDef) and n.name == "prepare")
        self.assertEqual(ast.unparse(node.body[0].value.func), "m.API.prepare")
        self.assertEqual(ast.unparse(node.body[1].value.func), "qualify")

    def test_original_hard_check_not_overridden(self):
        node = next(n for n in ast.walk(self.tree()) if isinstance(n, ast.ClassDef) and n.name == "CaptureGuard")
        self.assertEqual([n.name for n in node.body if isinstance(n, ast.FunctionDef)], ["__init__", "close"])

    def test_no_native_product_retry_or_sampler(self):
        calls = [ast.unparse(n.func) for n in ast.walk(self.tree()) if isinstance(n, ast.Call)]
        self.assertFalse(any(n.endswith((".run_owned", ".worker", ".preflight", ".Thread", ".Popen", ".sample")) for n in calls))
        self.assertEqual(calls.count("execute"), 1)

    def test_four_exact_code_paths_and_one_immutable_qual(self):
        self.assertEqual(len(set(o.CODE_PATHS)), 4)
        self.assertEqual(o.CODE_PATHS[-2:], (o.SELF, o.TEST))
        self.assertEqual(o.QUAL_PATH, "implementation/p09/evidence/p09-361-case142-optimized-acceptance-code-r410.v1.json")


if __name__ == "__main__":
    unittest.main()
