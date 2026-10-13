"""Bounded predicate-equivalence contracts; never product acceptance."""
import hashlib
from pathlib import Path
import stat
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import single_snapshot_source_guard_v1 as s
import reusable_audit_chunk_v1 as chunk
import owned_source_read_pressure as pressure

CHECKPOINT = lambda: None
SOURCE_BYTES = None


class Contracts(unittest.TestCase):
    def setUp(self):
        CHECKPOINT()
        self.reader = NS(root=Path("."))
        self.counts = s.Counters()
        self.queries = []
        self.fallbacks = []

    def tearDown(self):
        CHECKPOINT()

    def query(self, value):
        def query(path, *, follow_symlinks):
            self.queries.append((path, follow_symlinks))
            if isinstance(value, Exception): raise value
            return value
        return query

    def original(self, name):
        self.fallbacks.append(name)
        return ("exact-original", name)

    def check(self, value, name="x"):
        return s.source(self.reader, name, self.original, self.counts, query=self.query(value))

    def file(self, **kw):
        return NS(**dict(dict(st_mode=stat.S_IFREG | 0o644, st_file_attributes=32, st_reparse_tag=0), **kw))

    def test_normal_file_uses_one_fresh_no_follow_query_and_no_fallback(self):
        self.assertEqual(self.check(self.file()), Path("x"))
        self.assertEqual(self.queries, [(Path("x"), False)])
        self.assertEqual(self.fallbacks, [])
        self.assertEqual(self.counts.normal, 1)

    def test_directory_and_non_regular_file_not_promoted_to_regular(self):
        for mode, attrs in ((stat.S_IFDIR | 0o755, 16), (stat.S_IFIFO | 0o644, 0)):
            with self.subTest(), self.assertRaisesRegex(ValueError, "sql_source_link_or_missing"):
                self.check(self.file(st_mode=mode, st_file_attributes=attrs))
        self.assertEqual(self.counts.denied, 2)

    def test_symlink_junction_cloud_unknown_reparse_and_device_use_exact_original(self):
        for tag, attrs in ((0xa000000c, 0x400), (0xa0000003, 0x410),
            (0x9000001a, 0x400), (0x12345, 0x400), (0, 0x40)):
            with self.subTest():
                self.assertEqual(self.check(self.file(st_file_attributes=attrs, st_reparse_tag=tag)), ("exact-original", "x"))
        self.assertEqual(self.counts.normal, 0)
        self.assertEqual(self.counts.fallbacks, 5)

    def test_missing_invalid_boolean_or_inconsistent_fields_fall_back(self):
        rows = (NS(st_mode=stat.S_IFREG), self.file(st_file_attributes=True),
            self.file(st_reparse_tag=False), self.file(st_mode=True), self.file(st_file_attributes=-1),
            self.file(st_file_attributes=0x100000000), self.file(st_file_attributes=16),
            self.file(st_reparse_tag=1))
        for row in rows:
            with self.subTest(): self.assertEqual(self.check(row), ("exact-original", "x"))

    def test_stat_oserror_retains_original_failure_and_original_error_text(self):
        error = ValueError("ORIGINAL_SOURCE_FAILURE")
        def original(name): raise error
        with self.assertRaises(ValueError) as got:
            s.source(self.reader, "x", original, self.counts, query=self.query(PermissionError()))
        self.assertIs(got.exception, error)
        self.assertEqual(self.counts.fallbacks, 1)

    def test_no_snapshot_cache_same_name_queries_again_and_detects_directory_change(self):
        self.check(self.file())
        with self.assertRaises(ValueError): self.check(self.file(st_mode=stat.S_IFDIR, st_file_attributes=16))
        self.assertEqual(len(self.queries), 2)
        self.assertFalse(self.counts.summary()["stat_result_cached_or_reused_between_source_requests"])

    def test_factory_requires_frozen_source_and_default_source_method(self):
        Reader, proof = s.reader_type(pressure.WeightedReader, SOURCE_BYTES)
        self.assertTrue(proof["original_source_predicate_conjunction_retained"])
        with self.assertRaises(ValueError): s.reader_type(pressure.WeightedReader, SOURCE_BYTES+b"\n")
        class Changed(pressure.WeightedReader):
            def _source(self, name): return Path(name)
        with self.assertRaises(ValueError): s.reader_type(Changed, SOURCE_BYTES)

    def test_factory_keeps_original_reader_and_chunk_MRO_without_global_mutation(self):
        old = s.original.AuditEvidenceReader._source
        ChunkReader, _ = chunk.reader_type(pressure.WeightedReader, SOURCE_BYTES)
        Reader, _ = s.reader_type(ChunkReader, SOURCE_BYTES)
        self.assertEqual(Reader.__mro__[1:], ChunkReader.__mro__)
        self.assertIs(s.original.AuditEvidenceReader._source, old)
        self.assertFalse(Reader(Path("."), CHECKPOINT).source_snapshot_diagnostics()["original_default_reader_mutated"])

    def test_original_predicate_truth_and_queries_for_normal_metadata(self):
        for regular in (True, False):
            events = []
            class Source:
                def is_file(self): events.append("file"); return regular
                def is_symlink(self): events.append("symlink"); return False
                def is_junction(self): events.append("junction"); return False
            class Root:
                def __truediv__(self, name): return Source()
            original_reader = NS(root=Root())
            value = self.file() if regular else self.file(st_mode=stat.S_IFDIR, st_file_attributes=16)
            if regular:
                s.original.AuditEvidenceReader._source(original_reader, "x")
                self.check(value)
                self.assertEqual(events, ["file", "symlink", "junction"])
                self.assertEqual(len(self.queries), 1)
            else:
                with self.assertRaises(ValueError): s.original.AuditEvidenceReader._source(original_reader, "x")
                with self.assertRaises(ValueError): self.check(value)

    def test_original_file_hash_fresh_read_parse_and_closing_pass_unmodified(self):
        Reader, _ = s.reader_type(pressure.WeightedReader, SOURCE_BYTES)
        reader = Reader(Path("."), CHECKPOINT)
        reader._source = lambda name: NS(open=lambda mode: __import__("io").BytesIO(b"abc"))
        pin = reader.pin("a")
        reader.finish()
        self.assertEqual(pin["sha256"], hashlib.sha256(b"abc").hexdigest())
        self.assertEqual((reader.read_passes, reader.final_fresh_hashes, reader.bytes_read), (2, 1, 6))


if __name__ == "__main__": unittest.main()
