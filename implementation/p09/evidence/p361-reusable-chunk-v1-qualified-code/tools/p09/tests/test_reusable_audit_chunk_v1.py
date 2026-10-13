"""Bounded synthetic contracts, never full Native/product/Gate acceptance."""
import hashlib
import io
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import reusable_audit_chunk_v1 as r
import owned_source_read_pressure as pressure

CHECKPOINT = lambda: None
SOURCE_BYTES = None


class Source:
    def __init__(self, content, events, maximum=None, bad_count=None, error=None):
        self.content = content
        self.events = events
        self.maximum = maximum
        self.bad_count = bad_count
        self.error = error

    def open(self, mode):
        self.events.append(("open", mode))
        outer = self

        class Stream(io.BytesIO):
            def read(self, count=-1):
                outer.events.append(("read", count))
                return super().read(count if outer.maximum is None else min(count, outer.maximum))

            def readinto(self, window):
                outer.events.append(("readinto", len(window)))
                if outer.error:
                    raise outer.error
                if outer.bad_count is not None:
                    return outer.bad_count[0]
                data = super().read(len(window) if outer.maximum is None else min(len(window), outer.maximum))
                window[:len(data)] = data
                return len(data)

            def close(self):
                if not self.closed:
                    outer.events.append(("close",))
                super().close()

        return Stream(self.content)


class Pacer:
    def __init__(self, events):
        self.events = events

    def select(self, name):
        self.events.append(("select", name))

    def reserve(self, checkpoint):
        self.events.append(("reserve",))
        checkpoint()

    def refund(self, count):
        self.events.append(("refund", count))


class Contracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if SOURCE_BYTES is None:
            raise ValueError("TEST_SOURCE_MUST_BE_FRESH_GUARDED_BYTES")
        cls.Reader, cls.proof = r.reader_type(pressure.WeightedReader, SOURCE_BYTES)

    def setUp(self):
        CHECKPOINT()

    def tearDown(self):
        CHECKPOINT()

    def reader(self, new=True, content=b"abc", maximum=None, bad_count=None, error=None, budget=16777216):
        events = []
        def checkpoint():
            CHECKPOINT()
            events.append(("checkpoint",))
        reader = (self.Reader if new else pressure.WeightedReader)(Path("."), checkpoint, budget)
        reader.pacer = Pacer(events)
        reader._source = lambda _: Source(content, events, maximum, bad_count, error)
        return reader, events

    @staticmethod
    def canonical(events):
        return [("read", *row[1:]) if row[0] == "readinto" else row for row in events]

    def test_original_AST_source_and_MRO_restored_exactly(self):
        self.assertTrue(self.proof["original_leaf_read_AST_restored_exactly"])
        self.assertTrue(self.proof["original_MRO_preserved_with_one_leaf_insert"])
        self.assertEqual(self.proof["original_checkpoints_hash_parse_pacing_and_stream_statements_removed"], 0)
        for raw in (SOURCE_BYTES[:-1], SOURCE_BYTES.replace(b"self.checkpoint()", b"pass", 1)):
            with self.subTest(), self.assertRaisesRegex(ValueError, "EXACT_FROZEN_SOURCE"):
                r.project_read(raw)

    def test_complete_hash_bytes_and_event_order_equal_original_many_chunks(self):
        content = b"ab" * (r.original.CHUNK_BYTES + 7)
        old, left = self.reader(False, content)
        new, right = self.reader(True, content)
        self.assertEqual(old._read("x", True), new._read("x", True))
        self.assertEqual(left, self.canonical(right))
        self.assertEqual(new.bytes_read, len(content))
        self.assertEqual(r.summary(new)["workspace_allocations"], 1)

    def test_empty_short_and_non_chunk_aligned_reads_equal_original(self):
        for content, maximum in ((b"", None), (b"abcdefg", 3), (b"x"*65539, None)):
            with self.subTest():
                old, left = self.reader(False, content, maximum)
                new, right = self.reader(True, content, maximum)
                self.assertEqual(old._read("x", True), new._read("x", True))
                self.assertEqual(left, self.canonical(right))

    def test_same_workspace_reused_across_files_and_finish_fresh_reads(self):
        reader, events = self.reader(content=b"abc")
        first = reader.pin("a")
        storage = getattr(reader, r.ATTRIBUTE).storage
        reader.pin("b")
        reader.finish()
        self.assertIs(storage, getattr(reader, r.ATTRIBUTE).storage)
        self.assertEqual(reader.final_fresh_hashes, 2)
        self.assertEqual(reader.read_passes, 4)
        self.assertEqual(reader.bytes_read, 12)
        self.assertEqual(first["sha256"], hashlib.sha256(b"abc").hexdigest())
        row = r.summary(reader)
        self.assertEqual((row["leases"], row["lease_returns"], row["workspace_bytes"]), (4, 4, 65536))
        self.assertEqual(sum(x[0] == "open" for x in events), 4)

    def test_changed_file_on_closing_pass_still_rejected_no_byte_cache(self):
        reader, events = self.reader(content=b"old")
        reader.pin("a")
        reader._source = lambda _: Source(b"new", events)
        with self.assertRaisesRegex(ValueError, "input_changed_during_audit"):
            reader.finish()
        self.assertFalse(r.summary(reader)["active_lease"])
        self.assertEqual(reader.final_fresh_hashes, 0)

    def test_long_then_short_file_does_not_expose_previous_tail(self):
        reader, events = self.reader(content=b"secret-tail" * 9000)
        reader._read("long", True)
        reader._source = lambda _: Source(b"s", events)
        pin, raw = reader._read("short", True)
        self.assertEqual((pin["bytes"], raw), (1, b"s"))
        self.assertEqual(pin["sha256"], hashlib.sha256(b"s").hexdigest())

    def test_original_parse_budget_failure_closes_stream_and_lease(self):
        reader, events = self.reader(content=b"abc", budget=2)
        with self.assertRaisesRegex(ValueError, "audit_parse_budget_exceeded"):
            reader._read("x", True)
        self.assertEqual(events[-1], ("close",))
        self.assertFalse(r.summary(reader)["active_lease"])

    def test_stream_error_has_no_fallback_or_success_and_returns_lease(self):
        reader, events = self.reader(error=OSError("SYNTHETIC_READ_FAILURE"))
        with self.assertRaises(OSError):
            reader._read("x")
        row = r.summary(reader)
        self.assertEqual((row["readinto_attempts"], row["readinto_completed"], reader.bytes_read), (1, 0, 0))
        self.assertEqual(events[-1], ("close",))
        self.assertFalse(row["active_lease"])

    def test_invalid_None_bool_float_negative_and_oversize_counts_fail_closed(self):
        for count in (None, True, 1.0, -1, 65537):
            reader, events = self.reader(bad_count=(count,))
            with self.subTest(), self.assertRaisesRegex(ValueError, "INVALID_READINTO_COUNT"):
                reader._read("x")
            self.assertEqual(reader.bytes_read, 0)
            self.assertEqual(r.summary(reader)["invalid_readinto_returns"], 1)
            self.assertFalse(r.summary(reader)["active_lease"])
            self.assertEqual(events[-1], ("close",))

    def test_original_checkpoint_failure_before_and_during_read_retained(self):
        for stop_at in (1, 2, 3, 4):
            reader, events = self.reader(content=b"abc")
            checks = 0
            def fail():
                nonlocal checks
                CHECKPOINT()
                checks += 1
                if checks == stop_at:
                    raise ValueError("ORIGINAL_CPU_STOP")
            reader.checkpoint = fail
            with self.subTest(), self.assertRaisesRegex(ValueError, "ORIGINAL_CPU_STOP"):
                reader._read("x")
            if hasattr(reader, r.ATTRIBUTE):
                self.assertFalse(r.summary(reader)["active_lease"])

    def test_exact_workspace_owner_reentrancy_and_binding_rejected(self):
        reader, _ = self.reader()
        reader._read("x")
        workspace = getattr(reader, r.ATTRIBUTE)
        with workspace.lease():
            with self.assertRaisesRegex(ValueError, "REENTRANT_READ"):
                reader._read("x")
        with patch.object(r.threading, "get_ident", return_value=workspace.owner+1):
            with self.assertRaisesRegex(ValueError, "SERIAL_OWNER"):
                reader._read("x")
        setattr(reader, r.ATTRIBUTE, NS())
        with self.assertRaisesRegex(ValueError, "WORKSPACE_TYPE"):
            reader._read("x")

    def test_reader_instances_do_not_share_storage(self):
        first, _ = self.reader()
        second, _ = self.reader()
        first._read("x")
        second._read("x")
        self.assertIsNot(getattr(first, r.ATTRIBUTE).storage, getattr(second, r.ATTRIBUTE).storage)

    def test_original_byte_open_rates_and_default_class_are_unmodified(self):
        reader = self.Reader(Path("."), CHECKPOINT)
        reader.pacer.select("x.exe")
        self.assertEqual(reader.pacer.rate, 1048576)
        reader.pacer.select("x.py")
        self.assertEqual(reader.pacer.rate, 2097152)
        self.assertIs(r.original.AuditEvidenceReader._read.__globals__["AuditEvidenceReader"], r.original.AuditEvidenceReader)
        self.assertNotEqual(r.original.AuditEvidenceReader._read, self.Reader._read)

    def test_json_and_text_full_parse_semantics_unchanged(self):
        reader, _ = self.reader(content=b'\xef\xbb\xbf{"a":1}')
        self.assertEqual(reader.json("a"), {"a": 1})
        reader, _ = self.reader(content=b"a\r\nb\rc\n")
        self.assertEqual(reader.text("a"), "a\nb\nc\n")

    def test_unrelated_base_or_unqualified_original_leaf_rejected(self):
        for base in (object, r.original.AuditEvidenceReader, NS()):
            with self.subTest(), self.assertRaisesRegex(ValueError, "DERIVED_READER_REQUIRED"):
                r.reader_type(base, SOURCE_BYTES)
