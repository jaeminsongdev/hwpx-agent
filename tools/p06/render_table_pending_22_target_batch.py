#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
from typing import Any
import zlib


ROOT = Path(__file__).resolve().parents[2]
TARGET_ROOT = (ROOT / "fixtures" / "target-build").resolve(strict=True)
TRACE_SCHEMA = "hwpx-agent.p06-09-table-pending-22-target-batch-readback/v1"
ORACLE_SCHEMA = "hwpx-agent.p06-09-table-pending-22-target-oracle/v1"
OUTPUT_SCHEMA = "hwpx-agent.p06-09-table-pending-22-render-candidates/v1"
EXPECTED_TRACE_TARGET = {
    "prog_id": "HWPFrame.HwpObject.2",
    "registry_view": "Registry32",
    "client": "windows_powershell_x86_sta",
    "file_version": "11.0.0.9136",
    "executable_sha256": (
        "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce"
    ),
}
EXPECTED_ACCESS_CONTROL = {
    "source": "verified_hancom_saved_table_012_control",
    "input_file": "table-012-insert-row-3x3.hancom-2020-readback.hwpx",
    "input_sha256": "04f7910b122ded578975f379a7053b3dc62a0a5b73c2ea40505374500e665a0c",
    "input_unchanged": True,
    "open_state": "pass",
    "close_state": "pass",
}
GROUP_DIRECTORIES = {
    "merge_split": "p06-09-table-merge-split-target-20260913-06",
    "layout_placement": "p06-09-table-layout-placement-target-20260913-04",
    "remaining": "p06-09-table-remaining-target-20260913-10",
}
EXPECTED_FEATURES = (
    "TABLE-016",
    "TABLE-017",
    "TABLE-018",
    "TABLE-019",
    "TABLE-050",
    "TABLE-051",
    "TABLE-052",
    "TABLE-053",
    "TABLE-034",
    "TABLE-036",
    "TABLE-037",
    "TABLE-038",
    "TABLE-020",
    "TABLE-021",
    "TABLE-032",
    "TABLE-033",
    "TABLE-049",
    "TABLE-054",
    "TABLE-056",
    "TABLE-057",
    "TABLE-058",
    "TABLE-060",
)
EXPECTED_GROUPS = (
    *("merge_split" for _ in range(2)),
    *("layout_placement" for _ in range(10)),
    *("remaining" for _ in range(10)),
)
EXPECTED_GROUP_CASE_INDEXES = (*range(1, 3), *range(1, 11), *range(1, 11))
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
CASE_ID_RE = re.compile(r"table-[0-9]{3}-[a-z0-9-]+\Z")
ATTEMPT_RE = re.compile(r"p06-09-table-pending-22-target-[0-9]{8}-[0-9]{2}\Z")
PAGE_SIZE_RE = re.compile(
    r"(?P<width>[0-9]+(?:\.[0-9]+)?)\s+x\s+"
    r"(?P<height>[0-9]+(?:\.[0-9]+)?)\s+pts(?:\s+\([^)]+\))?"
)
MAX_JSON_BYTES = 1024 * 1024
MAX_PDF_BYTES = 32 * 1024 * 1024
MAX_PNG_BYTES = 16 * 1024 * 1024
MAX_TOOL_OUTPUT_BYTES = 1024 * 1024
RENDER_DPI = 144


class RenderPreparationError(ValueError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise RenderPreparationError("duplicate_json_key")
        result[key] = value
    return result


def sha256_file(path: Path, maximum: int) -> str:
    digest = hashlib.sha256()
    total = 0
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            total += len(chunk)
            if total > maximum:
                raise RenderPreparationError("file_size_limit")
            digest.update(chunk)
    if total == 0:
        raise RenderPreparationError("empty_file")
    return digest.hexdigest()


def _is_link(path: Path) -> bool:
    return path.is_symlink() or (
        hasattr(path, "is_junction") and path.is_junction()
    )


def bounded_existing(path: Path, root: Path, maximum: int) -> Path:
    resolved_root = root.resolve(strict=True)
    candidate = path if path.is_absolute() else ROOT / path
    lexical = candidate.absolute()
    try:
        relative = lexical.relative_to(resolved_root)
    except ValueError as error:
        raise RenderPreparationError("path_outside_boundary") from error
    cursor = resolved_root
    for part in relative.parts:
        cursor /= part
        if _is_link(cursor):
            raise RenderPreparationError("linked_path")
    resolved = lexical.resolve(strict=True)
    if resolved_root not in resolved.parents or not resolved.is_file():
        raise RenderPreparationError("path_outside_or_not_file")
    size = resolved.stat().st_size
    if size <= 0 or size > maximum:
        raise RenderPreparationError("file_size_limit")
    return resolved


def load_json(path: Path, root: Path) -> tuple[dict[str, Any], str]:
    resolved = bounded_existing(path, root, MAX_JSON_BYTES)
    data = resolved.read_bytes()
    if len(data) != resolved.stat().st_size:
        raise RenderPreparationError("file_changed_during_read")
    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RenderPreparationError("invalid_json") from error
    if not isinstance(value, dict):
        raise RenderPreparationError("json_root_not_object")
    return value, hashlib.sha256(data).hexdigest()


def exact_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        raise RenderPreparationError(f"{label}_sha256_invalid")
    return value


def bounded_tool(path: Path) -> Path:
    resolved = path.resolve(strict=True)
    if _is_link(path) or not resolved.is_file():
        raise RenderPreparationError("pdf_tool_invalid")
    size = resolved.stat().st_size
    if size <= 0 or size > 64 * 1024 * 1024:
        raise RenderPreparationError("pdf_tool_size_limit")
    return resolved


def run_tool(arguments: list[str], timeout: int) -> tuple[str, str]:
    completed = subprocess.run(
        arguments,
        check=False,
        capture_output=True,
        timeout=timeout,
    )
    if (
        completed.returncode != 0
        or len(completed.stdout) > MAX_TOOL_OUTPUT_BYTES
        or len(completed.stderr) > MAX_TOOL_OUTPUT_BYTES
    ):
        raise RenderPreparationError("pdf_tool_failed")
    return (
        completed.stdout.decode("utf-8", errors="replace"),
        completed.stderr.decode("utf-8", errors="replace"),
    )


def require_tool_version(tool: Path, label: str) -> None:
    stdout, stderr = run_tool([str(tool), "-v"], 10)
    if f"{label} version 26.07.0" not in stdout + stderr:
        raise RenderPreparationError("pdf_tool_version_mismatch")


def parse_pdfinfo(output: str) -> dict[str, Any]:
    fields: dict[str, str] = {}
    for line in output.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    required = {"Pages", "Page size", "Page rot", "Encrypted", "PDF version"}
    if not required.issubset(fields):
        raise RenderPreparationError("pdfinfo_fields_missing")
    match = PAGE_SIZE_RE.fullmatch(fields["Page size"])
    if match is None:
        raise RenderPreparationError("pdf_page_size_invalid")
    width = float(match.group("width"))
    height = float(match.group("height"))
    if (
        fields["Pages"] != "1"
        or fields["Page rot"] != "0"
        or fields["Encrypted"].lower() != "no"
        or not 594.0 <= width <= 596.0
        or not 840.0 <= height <= 843.0
    ):
        raise RenderPreparationError("pdf_boundary_mismatch")
    if fields.get("JavaScript", "no").lower() != "no":
        raise RenderPreparationError("pdf_javascript_present")
    return {
        "pages": 1,
        "page_size_points": [width, height],
        "page_rotation": 0,
        "encrypted": False,
        "pdf_version": fields["PDF version"],
        "creator": fields.get("Creator", ""),
        "producer": fields.get("Producer", ""),
    }


def png_identity(path: Path) -> dict[str, Any]:
    size = path.stat().st_size
    if size <= 0 or size > MAX_PNG_BYTES:
        raise RenderPreparationError("png_size_limit")
    data = path.read_bytes()
    if (
        len(data) != size
        or len(data) < 57
        or data[:8] != b"\x89PNG\r\n\x1a\n"
    ):
        raise RenderPreparationError("png_header_invalid")
    offset = 8
    chunk_index = 0
    width = 0
    height = 0
    saw_idat = False
    saw_iend = False
    while offset < len(data):
        if len(data) - offset < 12:
            raise RenderPreparationError("png_chunk_truncated")
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        chunk_end = offset + 12 + length
        if length > MAX_PNG_BYTES or chunk_end > len(data):
            raise RenderPreparationError("png_chunk_invalid")
        chunk_data = data[offset + 8 : offset + 8 + length]
        observed_crc = struct.unpack(">I", data[offset + 8 + length : chunk_end])[0]
        expected_crc = zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF
        if observed_crc != expected_crc:
            raise RenderPreparationError("png_crc_invalid")
        if chunk_index == 0:
            if chunk_type != b"IHDR" or length != 13:
                raise RenderPreparationError("png_ihdr_invalid")
            width, height = struct.unpack(">II", chunk_data[:8])
            if (
                chunk_data[8] not in {1, 2, 4, 8, 16}
                or chunk_data[9] not in {0, 2, 3, 4, 6}
                or chunk_data[10] != 0
                or chunk_data[11] != 0
                or chunk_data[12] not in {0, 1}
            ):
                raise RenderPreparationError("png_ihdr_encoding_invalid")
        elif chunk_type == b"IHDR":
            raise RenderPreparationError("png_duplicate_ihdr")
        if chunk_type == b"IDAT":
            if saw_iend or length == 0:
                raise RenderPreparationError("png_idat_invalid")
            saw_idat = True
        if chunk_type == b"IEND":
            if length != 0 or not saw_idat or chunk_end != len(data):
                raise RenderPreparationError("png_iend_invalid")
            saw_iend = True
        offset = chunk_end
        chunk_index += 1
    if not saw_iend:
        raise RenderPreparationError("png_iend_missing")
    if not 1188 <= width <= 1192 or not 1680 <= height <= 1686:
        raise RenderPreparationError("png_dimensions_invalid")
    return {
        "bytes": size,
        "sha256": hashlib.sha256(data).hexdigest(),
        "pixel_size": [width, height],
    }


def exact_group_root(group_id: str) -> Path:
    relative = GROUP_DIRECTORIES.get(group_id)
    if relative is None:
        raise RenderPreparationError("unknown_group")
    candidate = TARGET_ROOT / relative
    if _is_link(candidate) or not candidate.is_dir():
        raise RenderPreparationError("group_directory_invalid")
    resolved = candidate.resolve(strict=True)
    if resolved.parent != TARGET_ROOT:
        raise RenderPreparationError("group_directory_outside_boundary")
    return resolved


def validate_inputs(
    trace: dict[str, Any],
    trace_sha256: str,
    oracle: dict[str, Any],
    oracle_sha256: str,
) -> list[dict[str, Any]]:
    exact_sha256(trace_sha256, "trace")
    exact_sha256(oracle_sha256, "oracle")
    if (
        trace.get("schema_version") != TRACE_SCHEMA
        or trace.get("state") != "pass"
        or trace.get("target") != EXPECTED_TRACE_TARGET
        or trace.get("access_control") != EXPECTED_ACCESS_CONTROL
        or trace.get("case_count") != 22
        or trace.get("completed_case_count") != 22
    ):
        raise RenderPreparationError("trace_boundary_mismatch")
    cases = trace.get("cases")
    if not isinstance(cases, list) or len(cases) != 22:
        raise RenderPreparationError("trace_case_count_mismatch")
    if (
        oracle.get("schema_version") != ORACLE_SCHEMA
        or oracle.get("state") != "pass"
        or oracle.get("runtime_trace_sha256") != trace_sha256
        or oracle.get("case_count") != 22
        or oracle.get("feature_ids") != list(EXPECTED_FEATURES)
        or oracle.get("lifecycle_trace_passed") != 22
        or oracle.get("typed_semantic_readback_passed") != 22
        or oracle.get("input_immutability_passed") != 22
        or oracle.get("pdf_signature_passed") != 22
        or oracle.get("actual_hangul_2020") is not True
        or oracle.get("render")
        != "pdf_signature_passed_external_original_detail_review_required"
    ):
        raise RenderPreparationError("oracle_boundary_mismatch")
    for case, feature_id, group_id, group_case_index in zip(
        cases,
        EXPECTED_FEATURES,
        EXPECTED_GROUPS,
        EXPECTED_GROUP_CASE_INDEXES,
        strict=True,
    ):
        if not isinstance(case, dict):
            raise RenderPreparationError("trace_case_not_object")
        case_id = case.get("case_id")
        pdf_file = case.get("render_pdf_file")
        if (
            case.get("feature_id") != feature_id
            or case.get("group_id") != group_id
            or case.get("group_case_index") != group_case_index
            or not isinstance(case_id, str)
            or not CASE_ID_RE.fullmatch(case_id)
            or pdf_file != f"{case_id}.hancom-2020-render.pdf"
            or case.get("render_pdf_saved") is not True
            or case.get("render_pdf_signature_valid") is not True
        ):
            raise RenderPreparationError("trace_case_boundary_mismatch")
        exact_sha256(case.get("render_pdf_sha256"), "pdf")
    return cases


def prepare_output_path(path: Path, expected_parent: Path, expected_name: str) -> Path:
    candidate = path if path.is_absolute() else ROOT / path
    if candidate.name != expected_name or candidate.parent.resolve(strict=True) != expected_parent:
        raise RenderPreparationError("output_path_mismatch")
    if candidate.exists() or candidate.is_symlink():
        raise RenderPreparationError("output_already_exists")
    return candidate


def canonical_json(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render all 22 exact-target table PDFs for later original-detail review."
    )
    parser.add_argument("--trace", required=True, type=Path)
    parser.add_argument("--trace-sha256", required=True)
    parser.add_argument("--oracle-receipt", required=True, type=Path)
    parser.add_argument("--oracle-receipt-sha256", required=True)
    parser.add_argument("--pdfinfo", required=True, type=Path)
    parser.add_argument("--pdftoppm", required=True, type=Path)
    parser.add_argument("--output-directory", required=True, type=Path)
    parser.add_argument("--output-manifest", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    trace_path = bounded_existing(args.trace, TARGET_ROOT, MAX_JSON_BYTES)
    attempt_directory = trace_path.parent
    if (
        attempt_directory.parent != TARGET_ROOT
        or ATTEMPT_RE.fullmatch(attempt_directory.name) is None
        or _is_link(attempt_directory)
    ):
        raise RenderPreparationError("attempt_directory_invalid")
    oracle_path = bounded_existing(args.oracle_receipt, attempt_directory, MAX_JSON_BYTES)
    trace, observed_trace_sha256 = load_json(trace_path, TARGET_ROOT)
    oracle, observed_oracle_sha256 = load_json(oracle_path, attempt_directory)
    if observed_trace_sha256 != args.trace_sha256:
        raise RenderPreparationError("trace_sha256_mismatch")
    if observed_oracle_sha256 != args.oracle_receipt_sha256:
        raise RenderPreparationError("oracle_sha256_mismatch")
    cases = validate_inputs(trace, observed_trace_sha256, oracle, observed_oracle_sha256)

    pdfinfo = bounded_tool(args.pdfinfo)
    pdftoppm = bounded_tool(args.pdftoppm)
    require_tool_version(pdfinfo, "pdfinfo")
    require_tool_version(pdftoppm, "pdftoppm")
    output_directory = prepare_output_path(
        args.output_directory, attempt_directory, "rendered"
    )
    output_manifest = prepare_output_path(
        args.output_manifest,
        attempt_directory,
        "pending-22-render-manifest.json",
    )

    output_directory.mkdir(mode=0o700)
    rendered: list[dict[str, Any]] = []
    for case in cases:
        feature_id = str(case["feature_id"])
        group_id = str(case["group_id"])
        pdf_name = str(case["render_pdf_file"])
        group_root = exact_group_root(group_id)
        pdf_path = bounded_existing(group_root / pdf_name, group_root, MAX_PDF_BYTES)
        pdf_sha256 = sha256_file(pdf_path, MAX_PDF_BYTES)
        if (
            pdf_sha256 != case["render_pdf_sha256"]
            or pdf_path.stat().st_size != case["render_pdf_bytes"]
        ):
            raise RenderPreparationError("pdf_identity_mismatch")
        with pdf_path.open("rb") as stream:
            if stream.read(5) != b"%PDF-":
                raise RenderPreparationError("pdf_signature_mismatch")
        stdout, _ = run_tool([str(pdfinfo), str(pdf_path)], 30)
        pdf_metadata = parse_pdfinfo(stdout)
        png_name = f"{feature_id.lower()}-{case['case_id']}.png"
        prefix = output_directory / png_name.removesuffix(".png")
        run_tool(
            [
                str(pdftoppm),
                "-f",
                "1",
                "-l",
                "1",
                "-singlefile",
                "-r",
                str(RENDER_DPI),
                "-png",
                str(pdf_path),
                str(prefix),
            ],
            90,
        )
        png_path = prefix.with_suffix(".png")
        if not png_path.is_file() or _is_link(png_path):
            raise RenderPreparationError("rendered_png_missing")
        if sha256_file(pdf_path, MAX_PDF_BYTES) != pdf_sha256:
            raise RenderPreparationError("pdf_changed_during_render")
        rendered.append(
            {
                "feature_id": feature_id,
                "case_id": case["case_id"],
                "group_id": group_id,
                "pdf_file": pdf_name,
                "pdf_sha256": pdf_sha256,
                "pdf_metadata": pdf_metadata,
                "png_file": f"rendered/{png_name}",
                **png_identity(png_path),
                "visual_review_state": "not_run",
            }
        )

    if sha256_file(trace_path, MAX_JSON_BYTES) != observed_trace_sha256:
        raise RenderPreparationError("trace_changed_during_render")
    if sha256_file(oracle_path, MAX_JSON_BYTES) != observed_oracle_sha256:
        raise RenderPreparationError("oracle_changed_during_render")
    manifest = {
        "schema_version": OUTPUT_SCHEMA,
        "state": "rendered_not_reviewed",
        "scope": "current_pc_exact_hancom_2020_pending_22_review_candidates",
        "target": EXPECTED_TRACE_TARGET,
        "trace_sha256": observed_trace_sha256,
        "oracle_receipt_sha256": observed_oracle_sha256,
        "renderer": "pdftoppm 26.07.0",
        "pdf_inspector": "pdfinfo 26.07.0",
        "dpi": RENDER_DPI,
        "case_count": 22,
        "cases": rendered,
        "visual_review": {
            "state": "not_run",
            "required_detail": "original",
            "all_pages_inspected": False,
            "clipping": "unverified",
            "overlap": "unverified",
            "blank_pages": "unverified",
            "black_boxes": "unverified",
        },
        "not_claimed": {
            "render_diff": False,
            "direct_oracle_promotion": False,
            "automation_runtime": False,
            "differential": False,
            "p06_09_complete": False,
            "p06_complete": False,
            "product_complete": False,
        },
    }
    with output_manifest.open("xb") as stream:
        stream.write(canonical_json(manifest))
        stream.flush()
    print(
        "P06_TABLE_PENDING_22_RENDER_CANDIDATES_CREATED "
        f"cases={len(rendered)} visual_review=not_run"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
