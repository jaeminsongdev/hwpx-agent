import sys
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import same_reader_failed_role_admission_v1 as m
import same_reader_source_admission_once_v1 as once


class Reader:
    def __init__(self):
        self.snapshots = {"failed": {"path": "failed", "bytes": 7, "sha256": "a" * 64}}
        self.final_fresh_hashes = 0
        self.checks = 0

    def checkpoint(self):
        self.checks += 1


class Tests(unittest.TestCase):
    def setup_graph(self, original=None):
        calls = []
        authority = NS(read_exact=lambda *x: None, fields=lambda *x: None, exact=lambda *x: None)
        def admission(q, a):
            self.assertIs(a, authority)
            calls.append(q)
            return {"role": ["failed_not_product"]}
        source = NS(__name__="p09_exact_failed_role_test", admission=original or admission)
        shared, proof = m.connect(source, authority, once)
        return source, authority, shared, proof, calls

    def test_parent_and_manifest_share_one_declaration_not_bytes(self):
        source, a, parent, proof, calls = self.setup_graph()
        q = Reader()
        first = parent(q, a)
        second = source.admission(q, a)
        self.assertEqual(first, second)
        self.assertEqual(calls, [q])
        self.assertEqual(q.checks, 2)
        self.assertEqual(proof["actual_admissions"],
                         dict(actual_admissions=1, duplicate_admissions_avoided=1))
        self.assertFalse(proof["final_fresh_hashes_or_reads_bypassed"])

    def test_different_reader_requires_original_admission(self):
        _, a, shared, _, calls = self.setup_graph()
        x, y = Reader(), Reader()
        shared(x, a); shared(y, a)
        self.assertEqual(calls, [x, y])

    def test_final_fresh_phase_never_reuses(self):
        _, a, shared, _, calls = self.setup_graph()
        q = Reader(); shared(q, a); q.final_fresh_hashes = 1
        with self.assertRaisesRegex(ValueError, "FINAL_FRESH_ONLY"):
            shared(q, a)
        self.assertEqual(calls, [q])

    def test_changed_and_removed_pins_fail_closed(self):
        for removed in (False, True):
            _, a, shared, _, _ = self.setup_graph()
            q = Reader(); shared(q, a)
            if removed:
                q.snapshots.clear()
            else:
                q.snapshots["failed"]["bytes"] += 1
            with self.assertRaisesRegex(ValueError, "LEDGER_UNCHANGED"):
                shared(q, a)

    def test_original_resource_stop_is_not_hidden_by_reuse(self):
        _, a, shared, _, _ = self.setup_graph()
        q = Reader(); shared(q, a); stop = ValueError("ORIGINAL_CPU_STOP")
        def checkpoint():
            raise stop
        q.checkpoint = checkpoint
        with self.assertRaises(ValueError) as caught:
            shared(q, a)
        self.assertIs(caught.exception, stop)

    def test_different_authority_object_is_rejected(self):
        _, a, shared, _, _ = self.setup_graph()
        q = Reader(); shared(q, a)
        with self.assertRaisesRegex(ValueError, "SAME_AUTHORITY_IDENTITY"):
            shared(q, NS(**vars(a)))

    def test_changed_authority_method_is_rejected(self):
        _, a, shared, _, _ = self.setup_graph()
        q = Reader(); shared(q, a); a.read_exact = lambda *x: None
        with self.assertRaisesRegex(ValueError, "UNCHANGED_AUTHORITY_METHODS"):
            shared(q, a)

    def test_default_namespace_never_modified(self):
        original = lambda *x: {"ok": True}
        source = NS(__name__="runtime_failed_receipt_projection_v1", admission=original)
        with self.assertRaisesRegex(ValueError, "PRIVATE_SOURCE_NAMESPACE"):
            m.connect(source, NS(), once)
        self.assertIs(source.admission, original)

    def test_reinstallation_rejected(self):
        source, a, _, _, _ = self.setup_graph()
        with self.assertRaisesRegex(ValueError, "ONE_INSTALLATION"):
            m.connect(source, a, once)

    def test_failed_admission_is_never_retained(self):
        calls = []
        def failure(q, a):
            calls.append(q)
            raise ValueError("ORIGINAL_ROLE_FAILURE")
        _, a, shared, proof, _ = self.setup_graph(failure)
        q = Reader()
        for _ in range(2):
            with self.assertRaisesRegex(ValueError, "ORIGINAL_ROLE_FAILURE"):
                shared(q, a)
        self.assertEqual(calls, [q, q])
        self.assertEqual(proof["actual_admissions"]["actual_admissions"], 0)

    def test_returned_mutation_cannot_change_declaration(self):
        _, a, shared, _, _ = self.setup_graph()
        q = Reader(); shared(q, a)["role"].append("forged_product")
        self.assertEqual(shared(q, a), {"role": ["failed_not_product"]})


if __name__ == "__main__":
    unittest.main()
