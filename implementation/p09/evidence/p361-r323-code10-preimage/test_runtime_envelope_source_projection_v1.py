import copy
import hashlib
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import runtime_envelope_source_projection_v1 as m

ORIGINAL = "implementation/p09/evidence/p09-361-case157-current-runtime-run001.v1.json"
ENCODED = m.PREFIX + "case157-runtime-run001.envelope.v1.json"


def pin(name, raw):
    return dict(path=name, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def fixture():
    raw = b'{"unchanged":true, "full":"ORIGINAL"}\r\n'
    encoded = m.codec.encode(raw, lambda: None)
    source = pin("crates/product-cli/src/lib.rs", b"source")
    exe = pin("target/debug/exact.exe", b"executable")
    original, physical = pin(ORIGINAL, raw), pin(ENCODED, encoded)
    required = {p["path"]: p for p in (source, exe, original)}
    row = m.descriptor(original, physical, next_case=158)
    return raw, encoded, required, row


class Tests(unittest.TestCase):
    def test_full_scope_bijection_and_no_IO(self):
        raw, encoded, required, row = fixture()
        before = copy.deepcopy(required)
        with patch.object(Path, "open", side_effect=AssertionError("NO_IO")):
            projection = m.Projection(required, [row], next_case=158, checkpoint=lambda: None)
            self.assertEqual(dict(projection.semantic_pins), required)
            self.assertEqual(len(projection.physical_pins), len(required))
            self.assertEqual(projection.decode_fresh(ORIGINAL, row["physical_envelope_pin"], encoded, lambda: None), raw)
        self.assertEqual(required, before)
        for name in ("crates/product-cli/src/lib.rs", "target/debug/exact.exe"):
            self.assertEqual(projection.semantic_pins[name], projection.physical_pins[name])
        self.assertFalse(projection.evidence()["GO_authorized"])

    def test_each_decode_fresh_no_decode_cache(self):
        raw, encoded, required, row = fixture()
        projection = m.Projection(required, [row], next_case=158, checkpoint=lambda: None)
        original_decode = m.codec.decode
        with patch.object(m.codec, "decode", wraps=original_decode) as decode:
            for _ in range(2):
                self.assertEqual(projection.decode_fresh(ORIGINAL, row["physical_envelope_pin"], encoded, lambda: None), raw)
        self.assertEqual(decode.call_count, 2)

    def test_fresh_physical_tamper_pin_and_length_rejected(self):
        raw, encoded, required, row = fixture()
        projection = m.Projection(required, [row], next_case=158, checkpoint=lambda: None)
        for physical, data in ((row["physical_envelope_pin"], encoded[:-1]),
            (dict(row["physical_envelope_pin"], sha256="0" * 64), encoded),
            (row["physical_envelope_pin"], b"x" + encoded[1:])):
            with self.assertRaisesRegex(ValueError, "FRESH_PHYSICAL_BYTES_AND_PIN"):
                projection.decode_fresh(ORIGINAL, physical, data, lambda: None)

    def test_semantic_mismatch_not_hidden_by_valid_envelope(self):
        raw, encoded, required, row = fixture()
        other = m.codec.encode(b"different original", lambda: None)
        changed = m.descriptor(row["semantic_original_pin"], pin(ENCODED, other), next_case=158)
        projection = m.Projection(required, [changed], next_case=158, checkpoint=lambda: None)
        with self.assertRaisesRegex(ValueError, "EXACT_SEMANTIC_ORIGINAL_BYTES_AND_HASH"):
            projection.decode_fresh(ORIGINAL, changed["physical_envelope_pin"], other, lambda: None)

    def test_sources_executable_fixture_DATA_and_current_receipt_never_transform(self):
        raw, encoded, required, row = fixture()
        for path in ("crates/product-cli/src/lib.rs", "target/debug/exact.exe", "fixtures/original.hwpx",
            "implementation/p09/evidence/p09-361-case157-step-config001.v1.json",
            ORIGINAL.replace("case157", "case158"), ORIGINAL.replace("run001", "run000")):
            with self.assertRaisesRegex(ValueError, "ONLY_PRIOR_RUNTIME"):
                m.descriptor(pin(path, raw), row["physical_envelope_pin"], next_case=158)

    def test_duplicate_missing_original_closed_shape_and_context_rejected(self):
        raw, encoded, required, row = fixture()
        for rows in ([row, row], [dict(row, extra=True)], [dict(row, next_case=159)]):
            with self.assertRaises(ValueError):
                m.Projection(required, rows, next_case=158, checkpoint=lambda: None)
        without = {n: p for n, p in required.items() if n != ORIGINAL}
        with self.assertRaisesRegex(ValueError, "EXACT_ORIGINAL_ONE_BINDING"):
            m.Projection(without, [row], next_case=158, checkpoint=lambda: None)

    def test_physical_collision_and_ambiguous_path_rejected(self):
        raw, encoded, required, row = fixture()
        required[ENCODED] = dict(row["physical_envelope_pin"])
        with self.assertRaisesRegex(ValueError, "NO_PHYSICAL_COLLISION"):
            m.Projection(required, [row], next_case=158, checkpoint=lambda: None)
        with self.assertRaises(ValueError):
            m.descriptor(row["semantic_original_pin"], pin(ENCODED + ".extra", encoded), next_case=158)

    def test_nested_pins_immutable_caller_mutation_cannot_change_projection(self):
        raw, encoded, required, row = fixture()
        projection = m.Projection(required, [row], next_case=158, checkpoint=lambda: None)
        required[ORIGINAL]["sha256"] = "0" * 64
        row["physical_envelope_pin"]["sha256"] = "0" * 64
        with self.assertRaises(TypeError):
            projection.semantic_pins[ORIGINAL]["bytes"] = 1
        self.assertEqual(projection.decode_fresh(ORIGINAL, pin(ENCODED, encoded), encoded, lambda: None), raw)

    def test_guard_error_identity_before_any_bytes(self):
        raw, encoded, required, row = fixture()
        error = ValueError("ORIGINAL_HARD_STOP")
        def stop(): raise error
        with self.assertRaises(ValueError) as caught:
            m.Projection(required, [row], next_case=158, checkpoint=stop)
        self.assertIs(caught.exception, error)
        projection = m.Projection(required, [row], next_case=158, checkpoint=lambda: None)
        with self.assertRaises(ValueError) as caught:
            projection.decode_fresh(ORIGINAL, row["physical_envelope_pin"], encoded, stop)
        self.assertIs(caught.exception, error)

    def test_non_bound_name_bools_and_bound_count_rejected(self):
        raw, encoded, required, row = fixture()
        for index in (True, 115, 250):
            with self.assertRaises(ValueError):
                m.descriptor(row["semantic_original_pin"], row["physical_envelope_pin"], next_case=index)
        with self.assertRaises(ValueError):
            m.Projection(required, [], next_case=158, checkpoint=lambda: None)
        projection = m.Projection(required, [row], next_case=158, checkpoint=lambda: None)
        with self.assertRaisesRegex(ValueError, "EXPLICIT_BOUND_LOGICAL_NAME"):
            projection.decode_fresh("target/debug/exact.exe", row["physical_envelope_pin"], encoded, lambda: None)


if __name__ == "__main__":
    unittest.main()
