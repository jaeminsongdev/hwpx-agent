from __future__ import annotations

import json
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

from tools.p06 import render_table_pending_22_target_batch as render


def png_chunk(kind: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + kind
        + data
        + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    )


def minimal_png(width: int = 1190, height: int = 1682) -> bytes:
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", header)
        + png_chunk(b"IDAT", zlib.compress(b"\0"))
        + png_chunk(b"IEND", b"")
    )


def success_inputs() -> tuple[dict[str, object], dict[str, object]]:
    cases: list[dict[str, object]] = []
    for feature_id, group_id, group_index in zip(
        render.EXPECTED_FEATURES,
        render.EXPECTED_GROUPS,
        render.EXPECTED_GROUP_CASE_INDEXES,
        strict=True,
    ):
        case_id = f"table-{feature_id.removeprefix('TABLE-').lower()}-fixture"
        cases.append(
            {
                "feature_id": feature_id,
                "group_id": group_id,
                "group_case_index": group_index,
                "case_id": case_id,
                "render_pdf_file": f"{case_id}.hancom-2020-render.pdf",
                "render_pdf_saved": True,
                "render_pdf_signature_valid": True,
                "render_pdf_sha256": "a" * 64,
            }
        )
    trace: dict[str, object] = {
        "schema_version": render.TRACE_SCHEMA,
        "state": "pass",
        "target": render.EXPECTED_TRACE_TARGET,
        "security_module": dict(render.EXPECTED_SECURITY_MODULE),
        "access_control": dict(render.EXPECTED_ACCESS_CONTROL),
        "case_count": 22,
        "completed_case_count": 22,
        "cases": cases,
    }
    oracle: dict[str, object] = {
        "schema_version": render.ORACLE_SCHEMA,
        "state": "pass",
        "runtime_trace_sha256": "b" * 64,
        "case_count": 22,
        "feature_ids": list(render.EXPECTED_FEATURES),
        "lifecycle_trace_passed": 22,
        "typed_semantic_readback_passed": 22,
        "input_immutability_passed": 22,
        "pdf_signature_passed": 22,
        "actual_hangul_2020": True,
        "security_module_register_return": False,
        "render": "pdf_signature_passed_external_original_detail_review_required",
    }
    return trace, oracle


class Pending22RenderTests(unittest.TestCase):
    def test_pdfinfo_requires_one_unrotated_unencrypted_a4_page(self) -> None:
        result = render.parse_pdfinfo(
            "Pages: 1\nPage size: 595 x 841 pts (A4)\nPage rot: 0\n"
            "Encrypted: no\nJavaScript: no\nPDF version: 1.4\n"
        )
        self.assertEqual(result["pages"], 1)
        self.assertEqual(result["page_size_points"], [595.0, 841.0])

        with self.assertRaisesRegex(render.RenderPreparationError, "pdf_boundary_mismatch"):
            render.parse_pdfinfo(
                "Pages: 2\nPage size: 595 x 841 pts (A4)\nPage rot: 0\n"
                "Encrypted: no\nPDF version: 1.4\n"
            )

    def test_pdfinfo_rejects_javascript(self) -> None:
        with self.assertRaisesRegex(render.RenderPreparationError, "pdf_javascript_present"):
            render.parse_pdfinfo(
                "Pages: 1\nPage size: 595 x 841 pts (A4)\nPage rot: 0\n"
                "Encrypted: no\nJavaScript: yes\nPDF version: 1.4\n"
            )

    def test_png_identity_checks_structure_crc_and_dimensions(self) -> None:
        with tempfile.TemporaryDirectory(dir=render.ROOT / "target") as directory:
            path = Path(directory) / "candidate.png"
            path.write_bytes(minimal_png())
            identity = render.png_identity(path)
            self.assertEqual(identity["pixel_size"], [1190, 1682])
            self.assertEqual(identity["bytes"], path.stat().st_size)

            tampered = bytearray(path.read_bytes())
            tampered[-1] ^= 1
            path.write_bytes(tampered)
            with self.assertRaisesRegex(render.RenderPreparationError, "png_crc_invalid"):
                render.png_identity(path)

    def test_png_identity_rejects_wrong_dimensions(self) -> None:
        with tempfile.TemporaryDirectory(dir=render.ROOT / "target") as directory:
            path = Path(directory) / "candidate.png"
            path.write_bytes(minimal_png(width=800, height=600))
            with self.assertRaisesRegex(render.RenderPreparationError, "png_dimensions_invalid"):
                render.png_identity(path)

    def test_success_inputs_bind_exact_order_and_group_indexes(self) -> None:
        trace, oracle = success_inputs()
        cases = render.validate_inputs(trace, "b" * 64, oracle, "c" * 64)
        self.assertEqual(len(cases), 22)

        cases[2]["group_case_index"] = 3
        with self.assertRaisesRegex(
            render.RenderPreparationError, "trace_case_boundary_mismatch"
        ):
            render.validate_inputs(trace, "b" * 64, oracle, "c" * 64)

    def test_success_inputs_require_all_oracle_counters(self) -> None:
        trace, oracle = success_inputs()
        oracle["input_immutability_passed"] = 21
        with self.assertRaisesRegex(render.RenderPreparationError, "oracle_boundary_mismatch"):
            render.validate_inputs(trace, "b" * 64, oracle, "c" * 64)

    def test_success_inputs_reject_access_control_drift(self) -> None:
        trace, oracle = success_inputs()
        trace["access_control"]["open_state"] = "failed"  # type: ignore[index]
        with self.assertRaisesRegex(render.RenderPreparationError, "trace_boundary_mismatch"):
            render.validate_inputs(trace, "b" * 64, oracle, "c" * 64)

    def test_success_inputs_accept_first_open_without_retry(self) -> None:
        trace, oracle = success_inputs()
        trace["access_control"]["open_attempt_count"] = 1  # type: ignore[index]
        trace["access_control"]["first_open_returned_false"] = False  # type: ignore[index]
        self.assertEqual(
            len(render.validate_inputs(trace, "b" * 64, oracle, "c" * 64)), 22
        )

    def test_success_inputs_reject_inconsistent_access_control_retry(self) -> None:
        trace, oracle = success_inputs()
        trace["access_control"]["first_open_returned_false"] = False  # type: ignore[index]
        with self.assertRaisesRegex(render.RenderPreparationError, "trace_boundary_mismatch"):
            render.validate_inputs(trace, "b" * 64, oracle, "c" * 64)

    def test_group_roots_are_exact_and_unknown_group_fails(self) -> None:
        for group_id, directory in render.GROUP_DIRECTORIES.items():
            self.assertEqual(render.exact_group_root(group_id).name, directory)
        with self.assertRaisesRegex(render.RenderPreparationError, "unknown_group"):
            render.exact_group_root("other")

    def test_duplicate_json_keys_are_rejected(self) -> None:
        with self.assertRaisesRegex(render.RenderPreparationError, "duplicate_json_key"):
            json.loads(
                '{"state":"pass","state":"failed"}',
                object_pairs_hook=render.reject_duplicate_keys,
            )


if __name__ == "__main__":
    unittest.main()
