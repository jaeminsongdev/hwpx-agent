from __future__ import annotations

import importlib.util
import io
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "tools/p09/inspect_field_auto_number_target.py"
SPEC = importlib.util.spec_from_file_location("field_auto_number_target_oracle", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
ORACLE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ORACLE)


def package(section: bytes) -> bytes:
    with tempfile.NamedTemporaryFile(suffix=".hwpx", delete=False) as handle:
        path = Path(handle.name)
    try:
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("mimetype", "application/hwp+zip")
            archive.writestr("Contents/section0.xml", section)
        return path.read_bytes()
    finally:
        path.unlink(missing_ok=True)


def section(number: str = "9", native_type: str = "PAGE") -> bytes:
    fields = []
    values = [(native_type, number), ("PICTURE", "2"), ("TABLE", "3"), ("EQUATION", "4")]
    for kind, value in values:
        fields.append(
            f'<hp:ctrl><hp:autoNum num="{value}" numType="{kind}">'
            '<hp:autoNumFormat type="DIGIT" userChar="" prefixChar="" '
            'suffixChar="" supscript="0"/></hp:autoNum></hp:ctrl>'
        )
    return (
        '<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" '
        'xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">'
        '<hp:p><hp:run>' + "".join(fields) + "</hp:run></hp:p></hs:sec>"
    ).encode()


class FieldAutoNumberTargetOracleTests(unittest.TestCase):
    def inspect_bytes(self, value: bytes, expected=None):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.hwpx"
            path.write_bytes(value)
            return ORACLE.inspect(path, None, expected_projection=expected)

    def test_exact_projection_passes(self):
        result = self.inspect_bytes(package(section()))
        self.assertEqual(result["state"], "structural_only")
        self.assertEqual(result["semantic_state"], "not_run")
        self.assertFalse(result["actual_hangul"])
        self.assertFalse(result["product_complete"])
        self.assertEqual(result["native_object_counts"], {"pic": 0, "tbl": 0, "equation": 0})
        self.assertTrue(all(not item["caption_ancestor_present"] for item in result["field_object_context"]))
        self.assertEqual(result["field_count"], 4)
        self.assertEqual(result["projection"][0], {"native_type": "PAGE", "number": 9})

    def test_wrong_order_and_noncanonical_number_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "field_projection_mismatch"):
            self.inspect_bytes(package(section(native_type="TABLE")))
        with self.assertRaisesRegex(ValueError, "auto_number_noncanonical"):
            self.inspect_bytes(package(section(number="09")))

    def test_extension_and_digest_drift_fail_closed(self):
        extended = section().replace(b'<hp:autoNum num="9"', b'<hp:autoNum extra="x" num="9"', 1)
        with self.assertRaisesRegex(ValueError, "auto_number_attributes_invalid"):
            self.inspect_bytes(package(extended))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.hwpx"
            path.write_bytes(package(section()))
            with self.assertRaisesRegex(ValueError, "package_sha256_mismatch"):
                ORACLE.inspect(path, "0" * 64)

    def test_semantic_projection_rejects_historical_zero_recalculation(self):
        expected = [{"native_type": kind, "number": number}
                    for kind, number in zip(ORACLE.EXPECTED_TYPES, (9, 2, 3, 4))]
        original = self.inspect_bytes(package(section()), expected)
        self.assertEqual(original["state"], "pass")
        zeroed = section().replace(b'num="2"', b'num="0"').replace(b'num="3"', b'num="0"').replace(b'num="4"', b'num="0"')
        result = self.inspect_bytes(package(zeroed), expected)
        self.assertEqual(result["state"], "fail")
        self.assertEqual(result["structural_state"], "pass")
        self.assertEqual(result["semantic_state"], "fail")
        self.assertEqual(result["error_code"], "semantic_projection_mismatch")
        self.assertEqual([row["number"] for row in result["projection"]], [9, 0, 0, 0])
        self.assertEqual(result["green_rows"], 0)

    def test_object_and_caption_context_is_observed_without_qualifying_binding(self):
        value = section().replace(
            b'<hp:ctrl><hp:autoNum num="2"',
            b'<hp:pic><hp:caption><hp:subList><hp:p><hp:run><hp:ctrl><hp:autoNum num="2"',
        ).replace(
            b'</hp:autoNum></hp:ctrl><hp:ctrl><hp:autoNum num="3"',
            b'</hp:autoNum></hp:ctrl></hp:run></hp:p></hp:subList></hp:caption></hp:pic><hp:ctrl><hp:autoNum num="3"',
        )
        result = self.inspect_bytes(package(value))
        self.assertEqual(result["state"], "structural_only")
        self.assertEqual(result["native_object_counts"]["pic"], 1)
        self.assertTrue(result["field_object_context"][1]["caption_ancestor_present"])
        self.assertEqual(result["semantic_state"], "not_run")

    def test_expected_projection_must_have_exact_types_order_and_integer_values(self):
        expected = [{"native_type": kind, "number": number}
                    for kind, number in zip(ORACLE.EXPECTED_TYPES, (9, 2, 3, 4))]
        for invalid in ([], expected[::-1], [{**expected[0], "number": True}, *expected[1:]],
                        [{**expected[0], "number": -1}, *expected[1:]]):
            with self.subTest(invalid=invalid), self.assertRaisesRegex(ValueError, "expected_projection_invalid"):
                self.inspect_bytes(package(section()), invalid)

    def test_bounds_checked_before_reading_oversize_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "oversize.hwpx"
            with path.open("wb") as handle:
                handle.truncate(ORACLE.MAX_PACKAGE_BYTES + 1)
            with self.assertRaisesRegex(ValueError, "package_size_invalid"):
                ORACLE.inspect(path, None)

    def test_zip_member_alias_duplicate_and_total_expansion_rejected(self):
        for extra in ("Contents//other.xml", "C:/other.xml", "../other.xml", "Contents/./other.xml"):
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, "w") as archive:
                archive.writestr(ORACLE.SECTION_PATH, section())
                archive.writestr(extra, b"x")
            with self.subTest(extra=extra), self.assertRaisesRegex(ValueError, "entry_policy_invalid"):
                self.inspect_bytes(buffer.getvalue())
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(ORACLE.SECTION_PATH, section())
            for index in range(5):
                archive.writestr(f"extra{index}", b"x" * ORACLE.MAX_ENTRY_BYTES)
        with self.assertRaisesRegex(ValueError, "total_entry_size_invalid"):
            self.inspect_bytes(buffer.getvalue())

    def test_comments_doctype_and_format_tail_fail_closed(self):
        altered = (
            section().replace(b"<hp:ctrl>", b"<hp:ctrl><!--hidden-->", 1),
            b'<!DOCTYPE x>' + section(),
            section().replace(b"/></hp:autoNum>", b"/>stray</hp:autoNum>", 1),
        )
        errors = ("non_element_xml_node", "active_xml_construct_rejected", "auto_number_text_invalid")
        for value, code in zip(altered, errors):
            with self.subTest(code=code), self.assertRaisesRegex(ValueError, code):
                self.inspect_bytes(package(value))

    def test_symbolic_link_rejected_before_resolving(self):
        with tempfile.TemporaryDirectory() as directory:
            real = Path(directory) / "real.hwpx"
            real.write_bytes(package(section()))
            link = Path(directory) / "link.hwpx"
            try:
                link.symlink_to(real)
            except OSError:
                self.skipTest("symbolic-link privilege unavailable")
            with self.assertRaisesRegex(ValueError, "package_not_regular_file"):
                ORACLE.inspect(link, None)


if __name__ == "__main__":
    unittest.main()

