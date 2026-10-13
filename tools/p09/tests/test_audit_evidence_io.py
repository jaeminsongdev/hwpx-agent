"""Small in-memory fixtures only: no actual audit, Git, Cargo, SQL, Docker or child processes."""
import ast
import base64
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_evidence_io import AuditEvidenceReader, AuditReadPacer, CHUNK_BYTES, READ_BYTES_PER_SECOND


class Source:
    def __init__(self, raw):
        self.raw, self.opens, self.requests, self.closed = raw, 0, [], 0

    def open(self, mode):
        assert mode == "rb"
        self.opens += 1
        owner = self

        class Stream(io.BytesIO):
            def read(self, maximum=-1):
                owner.requests.append(maximum)
                return super().read(maximum)

            def close(self):
                owner.closed += 1
                return super().close()

        return Stream(self.raw)


class AuditEvidenceIOTests(unittest.TestCase):
    def reader(self, source, **kwargs):
        reader = AuditEvidenceReader("unused-fixture-root", lambda: None, **kwargs)
        self.addCleanup(patch.stopall)
        patch.object(reader, "_source", return_value=source).start()
        return reader

    def fake_pacer(self):
        clock = [0.0]
        sleeps = []
        def sleep(seconds):
            sleeps.append(seconds)
            clock[0] += seconds
        return AuditReadPacer(lambda: clock[0], sleep), clock, sleeps

    def test_pacing_reserves_before_read_and_caps_idle_credit_to_one_chunk(self):
        pacer, clock, sleeps = self.fake_pacer()
        pacer.reserve(lambda: None)
        pacer.refund(CHUNK_BYTES)
        clock[0] += 100
        pacer.reserve(lambda: None)
        pacer.refund(CHUNK_BYTES)
        self.assertEqual(sleeps, [])
        pacer.reserve(lambda: None)
        self.assertAlmostEqual(sum(sleeps), CHUNK_BYTES / READ_BYTES_PER_SECOND)
        self.assertTrue(all(0 < value <= 0.05 for value in sleeps))
        self.assertEqual(pacer.bytes_paced, CHUNK_BYTES*2)

    def test_pacing_refunds_short_reads_and_eof_without_charging_full_chunks(self):
        pacer, _, _ = self.fake_pacer()
        pacer.reserve(lambda: None)
        pacer.refund(17)
        self.assertEqual(pacer.tokens, CHUNK_BYTES-17)
        pacer.reserve(lambda: None)
        pacer.refund(0)
        self.assertEqual(pacer.tokens, CHUNK_BYTES)
        self.assertEqual(pacer.bytes_paced, 17)

    def test_pacing_is_shared_by_multiple_files_and_the_final_fresh_hash(self):
        source = Source(b"x" * CHUNK_BYTES)
        reader = self.reader(source)
        reader.pacer, _, sleeps = self.fake_pacer()
        for name in ("first.bin", "second.bin"):
            self.assertEqual(reader.pin(name)["sha256"], hashlib.sha256(source.raw).hexdigest())
        reader.finish()
        self.assertEqual(reader.final_fresh_hashes, 2)
        self.assertEqual(reader.read_passes, 4)
        self.assertEqual(reader.pacer.bytes_paced, reader.bytes_read)
        self.assertTrue(sleeps)
        self.assertTrue(all(request == CHUNK_BYTES for request in source.requests))

    def test_pacing_resource_stop_is_checked_before_sleep_and_after_sleep(self):
        for after_sleep in (False, True):
            pacer, _, sleeps = self.fake_pacer()
            pacer.reserve(lambda: None)
            pacer.refund(CHUNK_BYTES)
            calls = 0
            def checkpoint():
                nonlocal calls
                calls += 1
                if calls >= (2 if after_sleep else 1):
                    raise ValueError("fixture_stop")
            with self.assertRaisesRegex(ValueError, "^fixture_stop$"):
                pacer.reserve(checkpoint)
            self.assertEqual(len(sleeps), 1 if after_sleep else 0)

    def test_invalid_or_stalled_pacing_clock_and_charge_fail_closed(self):
        for value in (float("nan"), float("inf"), True):
            with self.assertRaisesRegex(ValueError, "^audit_io_clock_invalid$"):
                AuditReadPacer(lambda: value, lambda _: None)
        pacer, clock, _ = self.fake_pacer()
        clock[0] = -1
        with self.assertRaisesRegex(ValueError, "^audit_io_clock_invalid$"):
            pacer.reserve(lambda: None)
        stalled = AuditReadPacer(lambda: 0, lambda _: None)
        stalled.reserve(lambda: None)
        stalled.refund(CHUNK_BYTES)
        with self.assertRaisesRegex(ValueError, "^audit_io_clock_not_advancing$"):
            stalled.reserve(lambda: None)
        for value in (-1, True, CHUNK_BYTES+1):
            with self.assertRaisesRegex(ValueError, "^audit_io_charge_invalid$"):
                pacer.refund(value)

    def test_json_bom_hash_and_parser_use_one_identical_read(self):
        source = Source(b'\xef\xbb\xbf{"value":1,"text":"\\ud55c\\uae00"}')
        reader = self.reader(source)
        self.assertEqual(reader.json("fixture.json"), {"value": 1, "text": "한글"})
        self.assertEqual(source.opens, 1)
        self.assertEqual(reader.snapshots["fixture.json"], {"path": "fixture.json",
            "bytes": len(source.raw), "sha256": hashlib.sha256(source.raw).hexdigest()})
        reader.finish()
        self.assertEqual(source.opens, 2)  # Old pin + parse + final hash required three reads.
        self.assertEqual(reader.final_fresh_hashes, 1)
        self.assertEqual(reader.bytes_read, 2 * len(source.raw))

    def test_hash_only_never_requests_a_whole_file_buffer(self):
        source = Source(bytes(range(256)) * 1025)
        reader = self.reader(source)
        first = reader.pin("fixture.bin")
        self.assertEqual(first["sha256"], hashlib.sha256(source.raw).hexdigest())
        self.assertEqual(reader.pin("fixture.bin"), first)
        self.assertEqual(source.opens, 1)
        self.assertTrue(source.requests and all(n == CHUNK_BYTES for n in source.requests))
        reader.finish()
        self.assertEqual(source.opens, 2)
        self.assertEqual(source.closed, 2)

    def test_already_pinned_json_change_rejected_before_parsing(self):
        source = Source(b'{"value":1}')
        reader = self.reader(source)
        reader.pin("fixture.json")
        source.raw = b'{"value":2}'
        with self.assertRaisesRegex(ValueError, "^input_changed_during_audit$"):
            reader.json("fixture.json")

    def test_final_fresh_hash_catches_drift(self):
        source = Source(b'{"value":1}')
        reader = self.reader(source)
        reader.json("fixture.json")
        source.raw = b'{"value":2}'
        with self.assertRaisesRegex(ValueError, "^input_changed_during_audit$"):
            reader.finish()
        self.assertEqual(reader.final_fresh_hashes, 0)

    def test_repeated_json_is_not_a_mutable_or_cross_turn_cache(self):
        source = Source(b'{"value":[1]}')
        reader = self.reader(source)
        first = reader.json("fixture.json")
        first["value"].append(2)
        self.assertEqual(reader.json("fixture.json"), {"value": [1]})
        self.assertEqual(source.opens, 2)
        self.assertEqual(len(reader.snapshots), 1)

    def test_parse_budget_fails_not_skips_and_closes_file(self):
        source = Source(b'{"value":1}')
        reader = self.reader(source, maximum_parse_bytes=4)
        with self.assertRaisesRegex(ValueError, "^audit_parse_budget_exceeded$"):
            reader.json("fixture.json")
        self.assertFalse(reader.snapshots)
        self.assertEqual(source.closed, 1)
        for invalid in (0, -1, True, 1.5):
            with self.assertRaisesRegex(ValueError, "^audit_parse_budget_invalid$"):
                AuditEvidenceReader("unused", lambda: None, invalid)

    def test_json_and_text_errors_do_not_include_private_data(self):
        for raw in (b'{"private-fixture-value":', b'\xff'):
            with self.subTest(raw_size=len(raw)):
                reader = self.reader(Source(raw))
                with self.assertRaisesRegex(ValueError, "^audit_json_invalid$"):
                    reader.json("fixture.json")
        reader = self.reader(Source(b'\xff'))
        with self.assertRaisesRegex(ValueError, "^audit_text_invalid$"):
            reader.text("fixture.txt")

    def test_text_has_original_universal_newline_semantics_and_byte_pin(self):
        source = Source(b'first\r\nsecond\rthird\n')
        reader = self.reader(source)
        self.assertEqual(reader.text("fixture.txt"), "first\nsecond\nthird\n")
        self.assertEqual(reader.snapshots["fixture.txt"]["sha256"], hashlib.sha256(source.raw).hexdigest())
        self.assertEqual(source.opens, 1)

    def test_resource_stop_is_checked_before_open_and_between_chunks(self):
        source = Source(b'x' * (CHUNK_BYTES + 1))
        reader = self.reader(source)
        def stopped():
            raise ValueError("resource_stop")
        reader.checkpoint = stopped
        with self.assertRaisesRegex(ValueError, "^resource_stop$"):
            reader.pin("fixture.bin")
        self.assertEqual(source.opens, 0)
        calls = 0
        def during():
            nonlocal calls
            calls += 1
            # pin checkpoint, read checkpoint, first chunk, then stop on second chunk.
            if calls >= 4:
                stopped()
        reader.checkpoint = during
        with self.assertRaisesRegex(ValueError, "^resource_stop$"):
            reader.pin("fixture.bin")
        self.assertEqual(source.closed, 1)
        self.assertFalse(reader.snapshots)
        self.assertEqual(reader.bytes_read, CHUNK_BYTES)

    def test_direct_file_and_link_checks_are_preserved(self):
        for is_file, symlink, junction in ((False, False, False), (True, True, False), (True, False, True)):
            with self.subTest(is_file=is_file, symlink=symlink, junction=junction):
                reader = AuditEvidenceReader("unused-fixture-root", lambda: None)
                with patch.object(Path, "is_file", return_value=is_file), \
                        patch.object(Path, "is_symlink", return_value=symlink), \
                        patch.object(Path, "is_junction", return_value=junction), \
                        patch.object(Path, "open") as opened:
                    with self.assertRaisesRegex(ValueError, "^sql_source_link_or_missing$"):
                        reader.pin("fixture.json")
                    opened.assert_not_called()

    def test_current_auditor_keeps_all_non_io_authority_checks_unchanged(self):
        root = Path(__file__).resolve().parents[3]
        archive = json.loads((root / "implementation/p09/source-archive/p09-149-pre-single-read-audit/source-preimages.v1.json").read_text(encoding="utf-8"))
        self.assertEqual(len(archive["files"]), 1)
        row = archive["files"][0]
        before = base64.b64decode(row["base64"], validate=True)
        self.assertEqual(len(before), row["bytes"])
        self.assertEqual(hashlib.sha256(before).hexdigest(), row["sha256"])
        original = ast.parse(before.decode("utf-8"))
        current = ast.parse((root / row["path"]).read_text(encoding="utf-8"))
        old_functions = {node.name: node for node in original.body
            if isinstance(node, ast.FunctionDef) and node.name != "audit"}
        new_functions = {node.name: node for node in current.body
            if isinstance(node, ast.FunctionDef) and node.name != "audit"}
        self.assertTrue(old_functions)
        self.assertEqual(set(new_functions), set(old_functions))
        for name, old in old_functions.items():
            actual = copy.deepcopy(new_functions[name])
            if name == "authenticate_authority_delta":
                self.assertEqual(actual.args.args[-1].arg, "checkpoint")
                self.assertEqual(ast.dump(actual.args.defaults[-1]), ast.dump(ast.Constant(value=None)))
                actual.args.args.pop()
                actual.args.defaults.pop()
                self.assertEqual(ast.dump(actual.body.pop()), ast.dump(ast.parse(
                    "return formatted.audit_limits").body[0]))
                assignment = lambda node: next(n for n in node.body if isinstance(n, ast.Assign)
                    and isinstance(n.targets[0], ast.Name) and n.targets[0].id == "formatted")
                self.assertEqual(ast.dump(assignment(actual).value), ast.dump(ast.parse(
                    'run_audit_tool("rustfmt-stdin", current, checkpoint=checkpoint)', mode="eval").body))
                assignment(actual).value = copy.deepcopy(assignment(old).value)
            self.assertEqual(ast.dump(actual), ast.dump(old), name)

    def test_current_auditor_final_fresh_hash_precedes_acceptance(self):
        root = Path(__file__).resolve().parents[3]
        tree = ast.parse((root / "tools/p09/verify_formula_issuer_authority_current.py").read_text(encoding="utf-8"))
        audit = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "audit")
        finish = [node for node in audit.body if isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute)
            and isinstance(node.value.func.value, ast.Name)
            and node.value.func.value.id == "reader" and node.value.func.attr == "finish"]
        accepted = [node for node in audit.body if isinstance(node, ast.Return)]
        self.assertEqual(len(finish), 1)
        self.assertEqual(len(accepted), 1)
        self.assertLess(finish[0].lineno, accepted[0].lineno)
        self.assertFalse(any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr in {"read_text", "read_bytes"} for node in ast.walk(audit)))


if __name__ == "__main__":
    unittest.main()
