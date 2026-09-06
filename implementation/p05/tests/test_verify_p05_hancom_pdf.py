from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from io import BytesIO
from pathlib import Path

from PIL import Image


MODULE_PATH = Path(__file__).parents[1] / "tools" / "verify_p05_hancom_pdf.py"
SPEC = importlib.util.spec_from_file_location("verify_p05_hancom_pdf", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("unable to load P05 PDF verifier")
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def expectation() -> dict[str, object]:
    return {
        "schema_version": MODULE.EXPECTATION_SCHEMA,
        "expected_page_count": 1,
        "geometry_tolerance_milli_mm": 500,
        "pages": [
            {
                "index": 1,
                "width_milli_mm": 210_000,
                "height_milli_mm": 297_000,
                "rotation": 0,
                "required_text": ["P05 synthetic token"],
                "forbidden_text": ["forbidden token"],
            }
        ],
    }


def dense_expectation() -> dict[str, object]:
    return {
        "schema_version": MODULE.EXPECTATION_SCHEMA_V2,
        "expected_page_count": 1,
        "geometry_tolerance_milli_mm": 500,
        "pages": [
            {
                "index": 1,
                "width_milli_mm": 310_000,
                "height_milli_mm": 230_000,
                "rotation": 0,
                "required_text": ["left-anchor", "right-anchor"],
                "forbidden_text": [],
                "column_flow": {
                    "split_x_milli_mm": 156_000,
                    "split_guard_milli_mm": 3_000,
                    "min_text_fragments_per_column": 2,
                    "max_bottom_baseline_delta_milli_mm": 12_000,
                    "left_anchor_text": "left-anchor",
                    "right_anchor_text": "right-anchor",
                },
            }
        ],
    }


class PdfVerifierContractTests(unittest.TestCase):
    def parse(self, value: object) -> object:
        return MODULE.parse_expectation_bytes(
            json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        )

    def assert_code(self, expected: str, function, *arguments) -> None:
        with self.assertRaises(MODULE.VerificationError) as raised:
            function(*arguments)
        self.assertEqual(raised.exception.code, expected)

    def test_valid_expectation_is_typed(self) -> None:
        parsed = self.parse(expectation())
        self.assertEqual(parsed.page_count, 1)
        self.assertEqual(parsed.pages[0].required_text, ("P05 synthetic token",))

    def test_tracked_p05_expectations_are_valid_and_complete(self) -> None:
        expectation_root = MODULE_PATH.parents[1] / "render-expectations"
        section = MODULE.parse_expectation_bytes(
            (expectation_root / "p05-07-section-columns.json").read_bytes()
        )
        header = MODULE.parse_expectation_bytes(
            (expectation_root / "p05-08-header-footer.json").read_bytes()
        )
        layout = MODULE.parse_expectation_bytes(
            (expectation_root / "p05-09-vs1-layout.json").read_bytes()
        )
        dense = MODULE.parse_expectation_bytes(
            (expectation_root / "p05-07-dense-column-flow.json").read_bytes()
        )
        self.assertEqual(section.page_count, 2)
        self.assertEqual(
            (section.pages[0].width_milli_mm, section.pages[0].height_milli_mm),
            (310_000, 230_000),
        )
        self.assertEqual(header.page_count, 4)
        self.assertIn("P05-08-MASTER-PAGE", header.pages[0].forbidden_text)
        self.assertIn("P05-08-MASTER-PAGE", header.pages[1].required_text)
        self.assertEqual(layout.page_count, 1)
        self.assertEqual(
            (layout.pages[0].width_milli_mm, layout.pages[0].height_milli_mm),
            (310_000, 230_000),
        )
        self.assertIn("P05-09 VS-1 레이아웃", layout.pages[0].required_text)
        self.assertEqual(dense.schema_version, MODULE.EXPECTATION_SCHEMA_V2)
        self.assertEqual(dense.page_count, 2)
        self.assertIsNotNone(dense.pages[0].column_flow)
        self.assertIsNotNone(dense.pages[1].column_flow)
        self.assertEqual(dense.pages[1].column_flow.right_anchor_text, "P05-07-DENSE-END")

    def test_v2_column_flow_contract_is_exact_and_anchors_are_required(self) -> None:
        parsed = self.parse(dense_expectation())
        self.assertEqual(parsed.pages[0].column_flow.min_text_fragments_per_column, 2)
        value = dense_expectation()
        value["pages"][0]["column_flow"]["extra"] = True
        self.assert_code("PDF_EXPECTATION_COLUMN_FLOW_FIELDS_INVALID", self.parse, value)
        value = dense_expectation()
        value["pages"][0]["required_text"] = ["left-anchor"]
        self.assert_code("PDF_EXPECTATION_COLUMN_FLOW_ANCHOR_NOT_REQUIRED", self.parse, value)

    def test_v1_expectation_cannot_smuggle_column_flow_fields(self) -> None:
        value = expectation()
        value["pages"][0]["column_flow"] = dense_expectation()["pages"][0]["column_flow"]
        self.assert_code("PDF_EXPECTATION_PAGE_FIELDS_INVALID", self.parse, value)

    def test_root_extra_field_is_rejected(self) -> None:
        value = expectation()
        value["extra"] = True
        self.assert_code("PDF_EXPECTATION_FIELDS_INVALID", self.parse, value)

    def test_duplicate_json_field_is_rejected(self) -> None:
        raw = b'{"schema_version":"hwpx-agent.p05-render-expectation/v1","schema_version":"x"}'
        self.assert_code("PDF_EXPECTATION_DUPLICATE_FIELD", MODULE.parse_expectation_bytes, raw)

    def test_boolean_integer_is_rejected(self) -> None:
        value = expectation()
        value["expected_page_count"] = True
        self.assert_code("PDF_EXPECTATION_PAGE_COUNT_INVALID", self.parse, value)

    def test_page_order_is_dense(self) -> None:
        value = expectation()
        value["pages"][0]["index"] = 2
        self.assert_code("PDF_EXPECTATION_PAGE_ORDER_INVALID", self.parse, value)

    def test_rotation_is_closed_enum(self) -> None:
        value = expectation()
        value["pages"][0]["rotation"] = 45
        self.assert_code("PDF_EXPECTATION_ROTATION_INVALID", self.parse, value)

    def test_tokens_are_normalized_bounded_and_non_conflicting(self) -> None:
        for token in ["two  spaces", "line\nbreak", "a" * 257, "hidden\u200btext"]:
            value = expectation()
            value["pages"][0]["required_text"] = [token]
            self.assert_code("PDF_EXPECTATION_TOKEN_INVALID", self.parse, value)
        value = expectation()
        value["pages"][0]["forbidden_text"] = ["P05 synthetic token"]
        self.assert_code("PDF_EXPECTATION_TOKEN_CONFLICT", self.parse, value)

    def test_normalize_text_is_nfc_and_whitespace_stable(self) -> None:
        self.assertEqual(MODULE.normalize_text("  A\r\ne\u0301\tB\x00 "), "A é B")

    def test_point_and_pixel_conversion_use_half_up_rounding(self) -> None:
        self.assertEqual(MODULE.points_to_milli_mm("595.275590551"), 210_000)
        self.assertEqual(MODULE.milli_mm_to_pixels(210_000), 1_191)

    def test_text_origin_composes_text_and_content_matrices(self) -> None:
        self.assertEqual(
            MODULE.text_origin_milli_mm(
                [0.119896, 0.0, 0.0, -0.119823, 0.0, 651.0],
                [1.0, 0.0, 0.0, -1.0, 354.0, 898.0],
            ),
            (14_973, 191_699),
        )
        self.assert_code(
            "PDF_TEXT_MATRIX_INVALID",
            MODULE.text_origin_milli_mm,
            [1, 0, 0, 1, 0, float("nan")],
            [1, 0, 0, 1, 0, 0],
        )

    def test_column_flow_requires_both_columns_anchors_and_balanced_bottoms(self) -> None:
        contract = MODULE.ColumnFlowExpectation(156_000, 3_000, 2, 12_000, "left-anchor", "right-anchor")
        fragments = (
            MODULE.PositionedText("left-anchor", 15_000, 205_000),
            MODULE.PositionedText("left body", 15_000, 180_000),
            MODULE.PositionedText("right body", 165_000, 201_000),
            MODULE.PositionedText("right-anchor", 165_000, 181_000),
        )
        result = MODULE.verify_column_flow(fragments, contract, 310_000, 230_000, 500)
        self.assertEqual(result["left_text_fragment_count"], 2)
        self.assertEqual(result["right_text_fragment_count"], 2)
        self.assertEqual(result["bottom_baseline_delta_milli_mm"], 1_000)

        unbalanced = fragments[:-1] + (MODULE.PositionedText("right-anchor", 165_000, 200_000),)
        self.assert_code(
            "PDF_COLUMN_FLOW_BALANCE_MISMATCH",
            MODULE.verify_column_flow,
            unbalanced,
            contract,
            310_000,
            230_000,
            500,
        )

    def test_only_default_pdf_user_unit_is_accepted(self) -> None:
        MODULE.require_default_user_unit({})
        MODULE.require_default_user_unit({"/UserUnit": 1.0})
        self.assert_code(
            "PDF_PAGE_USER_UNIT_UNSUPPORTED",
            MODULE.require_default_user_unit,
            {"/UserUnit": 2},
        )

    def test_non_integral_pdf_rotation_is_rejected(self) -> None:
        self.assert_code(
            "PDF_PAGE_ROTATION_INVALID",
            MODULE._normalized_rotation,
            90.5,
        )

    def test_png_identity_parser_verifies_complete_png(self) -> None:
        buffer = BytesIO()
        Image.new("RGB", (19, 23), "white").save(buffer, format="PNG")
        with tempfile.TemporaryDirectory(prefix="hwpx-agent-p05-png-") as directory:
            path = Path(directory) / "page.png"
            path.write_bytes(buffer.getvalue())
            width, height, size, digest = MODULE.read_png_identity(path)
        self.assertEqual((width, height), (19, 23))
        self.assertEqual(size, len(buffer.getvalue()))
        self.assertRegex(digest, r"^[0-9a-f]{64}$")

    def test_png_identity_parser_rejects_truncated_png(self) -> None:
        with tempfile.TemporaryDirectory(prefix="hwpx-agent-p05-png-") as directory:
            path = Path(directory) / "page.png"
            path.write_bytes(MODULE.PNG_SIGNATURE + b"\x00" * 16)
            self.assert_code("PDF_RENDER_PNG_INVALID", MODULE.read_png_identity, path)

    def test_duplicate_cli_options_are_rejected(self) -> None:
        self.assert_code(
            "PDF_CLI_DUPLICATE_OPTION",
            MODULE.validate_cli_option_uniqueness,
            ["--pdf", "one.pdf", "--pdf", "two.pdf"],
        )

    def test_hash_helpers_do_not_expose_text(self) -> None:
        digest = MODULE.sha256_text("private fixture text")
        self.assertRegex(digest, r"^[0-9a-f]{64}$")
        self.assertNotIn("private", digest)


if __name__ == "__main__":
    unittest.main()
