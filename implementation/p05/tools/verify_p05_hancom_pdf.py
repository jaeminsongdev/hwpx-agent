#!/usr/bin/env python3
"""Fail-closed PDF geometry, text and raster verifier for disposable P05 fixtures."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import stat
import struct
import subprocess
import sys
import unicodedata
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, NoReturn

from pypdf import PdfReader, __version__ as PYPDF_VERSION
from PIL import Image, __version__ as PILLOW_VERSION


SCHEMA = "hwpx-agent.p05-hancom-pdf-verification/v1"
EXPECTATION_SCHEMA = "hwpx-agent.p05-render-expectation/v1"
SCHEMA_V2 = "hwpx-agent.p05-hancom-pdf-verification/v2"
EXPECTATION_SCHEMA_V2 = "hwpx-agent.p05-render-expectation/v2"
MAX_PDF_BYTES = 32 * 1024 * 1024
MAX_MANIFEST_BYTES = 64 * 1024
MAX_TRACE_BYTES = 256 * 1024
MAX_PAGES = 32
MAX_TOKENS_PER_PAGE = 16
MAX_TOKEN_UTF8_BYTES = 256
MAX_PNG_BYTES = 16 * 1024 * 1024
MAX_TOTAL_PNG_BYTES = 128 * 1024 * 1024
MAX_RENDER_PIXELS_PER_PAGE = 100_000_000
RENDER_DPI = 144
PDF_SIGNATURE = b"%PDF-"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
WHITESPACE_PATTERN = re.compile(r"\s+")
Image.MAX_IMAGE_PIXELS = MAX_RENDER_PIXELS_PER_PAGE


class VerificationError(Exception):
    """One stable, non-sensitive verification failure."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class ColumnFlowExpectation:
    split_x_milli_mm: int
    split_guard_milli_mm: int
    min_text_fragments_per_column: int
    max_bottom_baseline_delta_milli_mm: int
    left_anchor_text: str
    right_anchor_text: str


@dataclass(frozen=True)
class PageExpectation:
    index: int
    width_milli_mm: int
    height_milli_mm: int
    rotation: int
    required_text: tuple[str, ...]
    forbidden_text: tuple[str, ...]
    column_flow: ColumnFlowExpectation | None


@dataclass(frozen=True)
class Expectation:
    schema_version: str
    page_count: int
    tolerance_milli_mm: int
    pages: tuple[PageExpectation, ...]


@dataclass(frozen=True)
class PositionedText:
    text: str
    x_milli_mm: int
    y_milli_mm: int


def fail(code: str) -> NoReturn:
    raise VerificationError(code)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFC", value.replace("\x00", ""))
    return WHITESPACE_PATTERN.sub(" ", normalized).strip()


def require_exact_keys(value: dict[str, Any], expected: set[str], code: str) -> None:
    if set(value) != expected:
        fail(code)


def require_int(value: Any, minimum: int, maximum: int, code: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        fail(code)
    return value


def validate_token(value: Any) -> str:
    if not isinstance(value, str) or not value:
        fail("PDF_EXPECTATION_TOKEN_INVALID")
    normalized = normalize_text(value)
    if normalized != value or len(value.encode("utf-8")) > MAX_TOKEN_UTF8_BYTES:
        fail("PDF_EXPECTATION_TOKEN_INVALID")
    if any(unicodedata.category(character) in {"Cc", "Cf", "Cs"} for character in value):
        fail("PDF_EXPECTATION_TOKEN_INVALID")
    return value


def validate_token_list(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list) or len(value) > MAX_TOKENS_PER_PAGE:
        fail("PDF_EXPECTATION_TOKEN_LIST_INVALID")
    tokens = tuple(validate_token(token) for token in value)
    if len(set(tokens)) != len(tokens):
        fail("PDF_EXPECTATION_TOKEN_DUPLICATE")
    return tokens


def parse_column_flow(value: Any, page_width_milli_mm: int, rotation: int) -> ColumnFlowExpectation:
    if not isinstance(value, dict):
        fail("PDF_EXPECTATION_COLUMN_FLOW_INVALID")
    require_exact_keys(
        value,
        {
            "split_x_milli_mm",
            "split_guard_milli_mm",
            "min_text_fragments_per_column",
            "max_bottom_baseline_delta_milli_mm",
            "left_anchor_text",
            "right_anchor_text",
        },
        "PDF_EXPECTATION_COLUMN_FLOW_FIELDS_INVALID",
    )
    if rotation != 0:
        fail("PDF_EXPECTATION_COLUMN_FLOW_ROTATION_UNSUPPORTED")
    split = require_int(
        value["split_x_milli_mm"],
        10_000,
        page_width_milli_mm - 10_000,
        "PDF_EXPECTATION_COLUMN_FLOW_SPLIT_INVALID",
    )
    guard = require_int(
        value["split_guard_milli_mm"],
        100,
        10_000,
        "PDF_EXPECTATION_COLUMN_FLOW_GUARD_INVALID",
    )
    if split - guard <= 0 or split + guard >= page_width_milli_mm:
        fail("PDF_EXPECTATION_COLUMN_FLOW_GUARD_INVALID")
    minimum = require_int(
        value["min_text_fragments_per_column"],
        2,
        256,
        "PDF_EXPECTATION_COLUMN_FLOW_MINIMUM_INVALID",
    )
    bottom_delta = require_int(
        value["max_bottom_baseline_delta_milli_mm"],
        0,
        50_000,
        "PDF_EXPECTATION_COLUMN_FLOW_BALANCE_INVALID",
    )
    left_anchor = validate_token(value["left_anchor_text"])
    right_anchor = validate_token(value["right_anchor_text"])
    if left_anchor == right_anchor:
        fail("PDF_EXPECTATION_COLUMN_FLOW_ANCHOR_CONFLICT")
    return ColumnFlowExpectation(
        split,
        guard,
        minimum,
        bottom_delta,
        left_anchor,
        right_anchor,
    )


def parse_expectation_bytes(raw: bytes) -> Expectation:
    if not raw or len(raw) > MAX_MANIFEST_BYTES:
        fail("PDF_EXPECTATION_SIZE_INVALID")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError):
        fail("PDF_EXPECTATION_JSON_INVALID")
    if not isinstance(value, dict):
        fail("PDF_EXPECTATION_ROOT_INVALID")
    require_exact_keys(
        value,
        {"schema_version", "expected_page_count", "geometry_tolerance_milli_mm", "pages"},
        "PDF_EXPECTATION_FIELDS_INVALID",
    )
    schema_version = value["schema_version"]
    if not isinstance(schema_version, str) or schema_version not in {
        EXPECTATION_SCHEMA,
        EXPECTATION_SCHEMA_V2,
    }:
        fail("PDF_EXPECTATION_SCHEMA_INVALID")
    page_count = require_int(value["expected_page_count"], 1, MAX_PAGES, "PDF_EXPECTATION_PAGE_COUNT_INVALID")
    tolerance = require_int(
        value["geometry_tolerance_milli_mm"], 0, 2_000, "PDF_EXPECTATION_TOLERANCE_INVALID"
    )
    pages_value = value["pages"]
    if not isinstance(pages_value, list) or len(pages_value) != page_count:
        fail("PDF_EXPECTATION_PAGES_INVALID")
    pages: list[PageExpectation] = []
    for expected_index, page in enumerate(pages_value, start=1):
        if not isinstance(page, dict):
            fail("PDF_EXPECTATION_PAGE_INVALID")
        page_fields = {
            "index",
            "width_milli_mm",
            "height_milli_mm",
            "rotation",
            "required_text",
            "forbidden_text",
        }
        if schema_version == EXPECTATION_SCHEMA_V2:
            page_fields.add("column_flow")
        require_exact_keys(page, page_fields, "PDF_EXPECTATION_PAGE_FIELDS_INVALID")
        index = require_int(page["index"], 1, MAX_PAGES, "PDF_EXPECTATION_PAGE_INDEX_INVALID")
        if index != expected_index:
            fail("PDF_EXPECTATION_PAGE_ORDER_INVALID")
        width = require_int(page["width_milli_mm"], 10_000, 5_000_000, "PDF_EXPECTATION_WIDTH_INVALID")
        height = require_int(page["height_milli_mm"], 10_000, 5_000_000, "PDF_EXPECTATION_HEIGHT_INVALID")
        rotation = require_int(page["rotation"], 0, 270, "PDF_EXPECTATION_ROTATION_INVALID")
        if rotation not in {0, 90, 180, 270}:
            fail("PDF_EXPECTATION_ROTATION_INVALID")
        required = validate_token_list(page["required_text"])
        forbidden = validate_token_list(page["forbidden_text"])
        if set(required) & set(forbidden):
            fail("PDF_EXPECTATION_TOKEN_CONFLICT")
        column_flow = (
            parse_column_flow(page["column_flow"], width, rotation)
            if schema_version == EXPECTATION_SCHEMA_V2
            else None
        )
        if column_flow is not None and (
            column_flow.left_anchor_text not in required
            or column_flow.right_anchor_text not in required
        ):
            fail("PDF_EXPECTATION_COLUMN_FLOW_ANCHOR_NOT_REQUIRED")
        pages.append(PageExpectation(index, width, height, rotation, required, forbidden, column_flow))
    return Expectation(schema_version, page_count, tolerance, tuple(pages))


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            fail("PDF_EXPECTATION_DUPLICATE_FIELD")
        result[key] = value
    return result


def ensure_regular_input(path: Path, maximum_bytes: int, code: str) -> tuple[Path, int]:
    try:
        link_metadata = path.lstat()
        reparse_attribute = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        file_attributes = getattr(link_metadata, "st_file_attributes", 0)
        if path.is_symlink() or (reparse_attribute and file_attributes & reparse_attribute):
            fail(code)
        resolved = path.resolve(strict=True)
        metadata = resolved.stat()
    except (OSError, RuntimeError):
        fail(code)
    if not stat.S_ISREG(metadata.st_mode) or not 0 < metadata.st_size <= maximum_bytes:
        fail(code)
    return resolved, metadata.st_size


def ensure_new_child_path(path: Path, boundary: Path, suffix: str | None, code: str) -> Path:
    if path.exists() or path.is_symlink():
        fail(code)
    try:
        parent = path.parent.resolve(strict=True)
    except (OSError, RuntimeError):
        fail(code)
    if parent != boundary or (suffix is not None and path.suffix != suffix):
        fail(code)
    return parent / path.name


def points_to_milli_mm(points: Any) -> int:
    try:
        value = Decimal(str(points)) * Decimal(25_400) / Decimal(72)
    except Exception:
        fail("PDF_PAGE_GEOMETRY_INVALID")
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def require_matrix(value: Any) -> tuple[float, float, float, float, float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 6:
        fail("PDF_TEXT_MATRIX_INVALID")
    matrix: list[float] = []
    for component in value:
        if isinstance(component, bool):
            fail("PDF_TEXT_MATRIX_INVALID")
        try:
            number = float(component)
        except (TypeError, ValueError, OverflowError):
            fail("PDF_TEXT_MATRIX_INVALID")
        if not math.isfinite(number):
            fail("PDF_TEXT_MATRIX_INVALID")
        matrix.append(number)
    return (matrix[0], matrix[1], matrix[2], matrix[3], matrix[4], matrix[5])


def text_origin_milli_mm(cm: Any, tm: Any) -> tuple[int, int]:
    content = require_matrix(cm)
    text = require_matrix(tm)
    x_points = text[4] * content[0] + text[5] * content[2] + content[4]
    y_points = text[4] * content[1] + text[5] * content[3] + content[5]
    return points_to_milli_mm(x_points), points_to_milli_mm(y_points)


def extract_positioned_text(page: Any) -> tuple[str, tuple[PositionedText, ...]]:
    fragments: list[PositionedText] = []

    def visitor(text: Any, cm: Any, tm: Any, _font: Any, _font_size: Any) -> None:
        if not isinstance(text, str):
            fail("PDF_TEXT_FRAGMENT_INVALID")
        normalized = normalize_text(text)
        if not normalized:
            return
        x, y = text_origin_milli_mm(cm, tm)
        fragments.append(PositionedText(normalized, x, y))

    try:
        extracted = normalize_text(page.extract_text(visitor_text=visitor) or "")
    except VerificationError:
        raise
    except Exception:
        fail("PDF_TEXT_EXTRACTION_FAILED")
    return extracted, tuple(fragments)


def find_unique_anchor_origin(
    fragments: tuple[PositionedText, ...],
    anchor_text: str,
    page_height_milli_mm: int,
    geometry_tolerance_milli_mm: int,
) -> PositionedText:
    """Find one normalized anchor even when a PDF producer splits it across text fragments."""
    joined = " ".join(fragment.text for fragment in fragments)
    start = joined.find(anchor_text)
    if start < 0 or joined.find(anchor_text, start + 1) >= 0:
        fail("PDF_COLUMN_FLOW_ANCHOR_CARDINALITY")

    anchor_end = start + len(anchor_text)
    cursor = 0
    for fragment in fragments:
        end = cursor + len(fragment.text)
        overlaps_anchor = cursor < anchor_end and end > start
        unpositioned_page_edge_callback = (
            fragment.x_milli_mm == 0
            and abs(fragment.y_milli_mm - page_height_milli_mm)
            <= geometry_tolerance_milli_mm
        )
        if overlaps_anchor and not unpositioned_page_edge_callback:
            return fragment
        cursor = end + 1
    fail("PDF_COLUMN_FLOW_ANCHOR_CARDINALITY")


def verify_column_flow(
    fragments: tuple[PositionedText, ...],
    expectation: ColumnFlowExpectation,
    page_width_milli_mm: int,
    page_height_milli_mm: int,
    geometry_tolerance_milli_mm: int,
) -> dict[str, Any]:
    if not fragments:
        fail("PDF_COLUMN_FLOW_TEXT_MISSING")
    for fragment in fragments:
        if not (
            -geometry_tolerance_milli_mm
            <= fragment.x_milli_mm
            <= page_width_milli_mm + geometry_tolerance_milli_mm
            and -geometry_tolerance_milli_mm
            <= fragment.y_milli_mm
            <= page_height_milli_mm + geometry_tolerance_milli_mm
        ):
            fail("PDF_COLUMN_FLOW_COORDINATE_OUT_OF_PAGE")
    positioned = tuple(
        fragment
        for fragment in fragments
        if not (
            fragment.x_milli_mm == 0
            and abs(fragment.y_milli_mm - page_height_milli_mm)
            <= geometry_tolerance_milli_mm
        )
    )
    left_limit = expectation.split_x_milli_mm - expectation.split_guard_milli_mm
    right_limit = expectation.split_x_milli_mm + expectation.split_guard_milli_mm
    left = tuple(fragment for fragment in positioned if fragment.x_milli_mm < left_limit)
    right = tuple(fragment for fragment in positioned if fragment.x_milli_mm > right_limit)
    if (
        len(left) < expectation.min_text_fragments_per_column
        or len(right) < expectation.min_text_fragments_per_column
    ):
        fail("PDF_COLUMN_FLOW_COLUMN_UNDERFILLED")
    left_anchor = find_unique_anchor_origin(
        fragments,
        expectation.left_anchor_text,
        page_height_milli_mm,
        geometry_tolerance_milli_mm,
    )
    right_anchor = find_unique_anchor_origin(
        fragments,
        expectation.right_anchor_text,
        page_height_milli_mm,
        geometry_tolerance_milli_mm,
    )
    if left_anchor.x_milli_mm >= left_limit:
        fail("PDF_COLUMN_FLOW_LEFT_ANCHOR_MISMATCH")
    if right_anchor.x_milli_mm <= right_limit:
        fail("PDF_COLUMN_FLOW_RIGHT_ANCHOR_MISMATCH")
    left_bottom = min(fragment.y_milli_mm for fragment in left)
    right_bottom = min(fragment.y_milli_mm for fragment in right)
    bottom_delta = abs(left_bottom - right_bottom)
    if bottom_delta > expectation.max_bottom_baseline_delta_milli_mm:
        fail("PDF_COLUMN_FLOW_BALANCE_MISMATCH")
    return {
        "split_x_milli_mm": expectation.split_x_milli_mm,
        "split_guard_milli_mm": expectation.split_guard_milli_mm,
        "left_text_fragment_count": len(left),
        "right_text_fragment_count": len(right),
        "unclassified_text_fragment_count": len(fragments) - len(left) - len(right),
        "left_bottom_baseline_milli_mm": left_bottom,
        "right_bottom_baseline_milli_mm": right_bottom,
        "bottom_baseline_delta_milli_mm": bottom_delta,
        "left_anchor_text_sha256": sha256_text(expectation.left_anchor_text),
        "right_anchor_text_sha256": sha256_text(expectation.right_anchor_text),
        "left_anchor_x_milli_mm": left_anchor.x_milli_mm,
        "left_anchor_y_milli_mm": left_anchor.y_milli_mm,
        "right_anchor_x_milli_mm": right_anchor.x_milli_mm,
        "right_anchor_y_milli_mm": right_anchor.y_milli_mm,
        "raw_document_text_present": False,
    }


def require_default_user_unit(page: Any) -> None:
    try:
        user_unit = Decimal(str(page.get("/UserUnit", 1)))
    except Exception:
        fail("PDF_PAGE_USER_UNIT_INVALID")
    if user_unit != Decimal(1):
        fail("PDF_PAGE_USER_UNIT_UNSUPPORTED")


def _normalized_rotation(value: Any) -> int:
    if isinstance(value, bool):
        fail("PDF_PAGE_ROTATION_INVALID")
    try:
        rotation_decimal = Decimal(str(value))
        if not rotation_decimal.is_finite() or rotation_decimal != rotation_decimal.to_integral_value():
            fail("PDF_PAGE_ROTATION_INVALID")
        return int(rotation_decimal) % 360
    except VerificationError:
        raise
    except Exception:
        fail("PDF_PAGE_ROTATION_INVALID")


def milli_mm_to_pixels(milli_mm: int) -> int:
    value = Decimal(milli_mm) * Decimal(RENDER_DPI) / Decimal(25_400)
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def read_png_identity(path: Path) -> tuple[int, int, int, str]:
    resolved, size = ensure_regular_input(path, MAX_PNG_BYTES, "PDF_RENDER_PNG_INVALID")
    with resolved.open("rb") as stream:
        header = stream.read(24)
    if len(header) != 24 or header[:8] != PNG_SIGNATURE or header[12:16] != b"IHDR":
        fail("PDF_RENDER_PNG_INVALID")
    width, height = struct.unpack(">II", header[16:24])
    if not 1 <= width <= 32_768 or not 1 <= height <= 32_768:
        fail("PDF_RENDER_PNG_DIMENSIONS_INVALID")
    if width * height > MAX_RENDER_PIXELS_PER_PAGE:
        fail("PDF_RENDER_PNG_PIXEL_LIMIT")
    try:
        with Image.open(resolved) as image:
            if image.format != "PNG" or image.size != (width, height):
                fail("PDF_RENDER_PNG_INVALID")
            image.verify()
    except VerificationError:
        raise
    except Exception:
        fail("PDF_RENDER_PNG_INVALID")
    return width, height, size, sha256_file(resolved)


def validate_cli_option_uniqueness(arguments: list[str]) -> None:
    seen: set[str] = set()
    for argument in arguments:
        if not argument.startswith("--"):
            continue
        option = argument.split("=", 1)[0]
        if option in seen:
            fail("PDF_CLI_DUPLICATE_OPTION")
        seen.add(option)


def parse_args(arguments: list[str]) -> argparse.Namespace:
    validate_cli_option_uniqueness(arguments)
    parser = argparse.ArgumentParser(add_help=True, allow_abbrev=False)
    parser.add_argument("--pdf", required=True)
    parser.add_argument("--expected-pdf-sha256", required=True)
    parser.add_argument("--expectation", required=True)
    parser.add_argument("--trace", required=True)
    parser.add_argument("--render-dir", required=True)
    parser.add_argument("--pdftoppm", required=True)
    parser.add_argument("--expected-pdftoppm-sha256", required=True)
    namespace = parser.parse_args(arguments)
    if not SHA256_PATTERN.fullmatch(namespace.expected_pdf_sha256):
        fail("PDF_EXPECTED_SHA256_INVALID")
    if not SHA256_PATTERN.fullmatch(namespace.expected_pdftoppm_sha256):
        fail("PDF_RENDERER_EXPECTED_SHA256_INVALID")
    return namespace


def write_new_json(path: Path, value: dict[str, Any]) -> None:
    encoded = (json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=False) + "\n").encode("utf-8")
    if len(encoded) > MAX_TRACE_BYTES:
        fail("PDF_TRACE_SIZE_LIMIT")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            descriptor = -1
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def write_failure_trace_if_safe(arguments: argparse.Namespace, result: dict[str, Any]) -> None:
    """Best-effort failure trace after a trustworthy fixture boundary can be established."""
    try:
        pdf, _ = ensure_regular_input(Path(arguments.pdf), MAX_PDF_BYTES, "PDF_INPUT_INVALID")
        boundary = pdf.parent.resolve(strict=True)
        trace = ensure_new_child_path(
            Path(arguments.trace), boundary, ".json", "PDF_TRACE_PATH_INVALID"
        )
        write_new_json(trace, result)
    except Exception:
        return


def render_page(renderer: Path, pdf: Path, render_dir: Path, page_index: int) -> Path:
    prefix = render_dir / f"page-{page_index:04d}"
    output = prefix.with_suffix(".png")
    if output.exists():
        fail("PDF_RENDER_OUTPUT_ALREADY_EXISTS")
    try:
        completed = subprocess.run(
            [
                str(renderer),
                "-f",
                str(page_index),
                "-l",
                str(page_index),
                "-r",
                str(RENDER_DPI),
                "-png",
                "-singlefile",
                str(pdf),
                str(prefix),
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=60,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.TimeoutExpired):
        fail("PDF_RENDERER_EXECUTION_FAILED")
    if completed.returncode != 0 or not output.exists():
        fail("PDF_RENDERER_EXECUTION_FAILED")
    return output


def verify(arguments: argparse.Namespace) -> dict[str, Any]:
    pdf, pdf_size = ensure_regular_input(Path(arguments.pdf), MAX_PDF_BYTES, "PDF_INPUT_INVALID")
    boundary = pdf.parent.resolve(strict=True)
    expectation_path, expectation_size = ensure_regular_input(
        Path(arguments.expectation), MAX_MANIFEST_BYTES, "PDF_EXPECTATION_INPUT_INVALID"
    )
    if expectation_path.parent != boundary:
        fail("PDF_EXPECTATION_OUTSIDE_FIXTURE_BOUNDARY")
    trace = ensure_new_child_path(Path(arguments.trace), boundary, ".json", "PDF_TRACE_PATH_INVALID")
    render_dir = ensure_new_child_path(Path(arguments.render_dir), boundary, None, "PDF_RENDER_DIR_INVALID")
    renderer, _ = ensure_regular_input(
        Path(arguments.pdftoppm), 128 * 1024 * 1024, "PDF_RENDERER_INPUT_INVALID"
    )
    python_runtime, _ = ensure_regular_input(
        Path(sys.executable), 128 * 1024 * 1024, "PDF_PYTHON_RUNTIME_INVALID"
    )
    verifier_source, _ = ensure_regular_input(
        Path(__file__), 1024 * 1024, "PDF_VERIFIER_SOURCE_INVALID"
    )
    renderer_sha256 = sha256_file(renderer)
    python_runtime_sha256 = sha256_file(python_runtime)
    verifier_sha256 = sha256_file(verifier_source)
    if renderer_sha256 != arguments.expected_pdftoppm_sha256:
        fail("PDF_RENDERER_SHA256_MISMATCH")
    with pdf.open("rb") as stream:
        if stream.read(len(PDF_SIGNATURE)) != PDF_SIGNATURE:
            fail("PDF_SIGNATURE_INVALID")
    pdf_sha256 = sha256_file(pdf)
    if pdf_sha256 != arguments.expected_pdf_sha256:
        fail("PDF_SHA256_MISMATCH")
    with expectation_path.open("rb") as stream:
        expectation_bytes = stream.read(MAX_MANIFEST_BYTES + 1)
    if len(expectation_bytes) != expectation_size:
        fail("PDF_EXPECTATION_CHANGED_DURING_READ")
    expectation_sha256 = hashlib.sha256(expectation_bytes).hexdigest()
    expectation = parse_expectation_bytes(expectation_bytes)

    try:
        reader = PdfReader(str(pdf), strict=True)
    except Exception:
        fail("PDF_PARSE_FAILED")
    if reader.is_encrypted:
        fail("PDF_ENCRYPTED_UNSUPPORTED")
    if len(reader.pages) != expectation.page_count:
        fail("PDF_PAGE_COUNT_MISMATCH")

    render_dir.mkdir(mode=0o700)
    page_results: list[dict[str, Any]] = []
    total_png_bytes = 0
    for page_expectation, page in zip(expectation.pages, reader.pages, strict=True):
        require_default_user_unit(page)
        rotation_value = page.get("/Rotate", 0)
        rotation = _normalized_rotation(rotation_value)
        if rotation != page_expectation.rotation:
            fail("PDF_PAGE_ROTATION_MISMATCH")
        width = points_to_milli_mm(page.mediabox.width)
        height = points_to_milli_mm(page.mediabox.height)
        if rotation in {90, 270}:
            width, height = height, width
        if (
            abs(width - page_expectation.width_milli_mm) > expectation.tolerance_milli_mm
            or abs(height - page_expectation.height_milli_mm) > expectation.tolerance_milli_mm
        ):
            fail("PDF_PAGE_GEOMETRY_MISMATCH")
        column_flow_result: dict[str, Any] | None = None
        if page_expectation.column_flow is not None:
            text, fragments = extract_positioned_text(page)
            column_flow_result = verify_column_flow(
                fragments,
                page_expectation.column_flow,
                width,
                height,
                expectation.tolerance_milli_mm,
            )
        else:
            try:
                text = normalize_text(page.extract_text() or "")
            except Exception:
                fail("PDF_TEXT_EXTRACTION_FAILED")
        missing = [token for token in page_expectation.required_text if token not in text]
        forbidden = [token for token in page_expectation.forbidden_text if token in text]
        if missing:
            fail("PDF_REQUIRED_TEXT_MISSING")
        if forbidden:
            fail("PDF_FORBIDDEN_TEXT_PRESENT")
        expected_png_width = milli_mm_to_pixels(page_expectation.width_milli_mm)
        expected_png_height = milli_mm_to_pixels(page_expectation.height_milli_mm)
        if (
            expected_png_width * expected_png_height > MAX_RENDER_PIXELS_PER_PAGE
            or expected_png_width > 32_768
            or expected_png_height > 32_768
        ):
            fail("PDF_RENDER_EXPECTED_PIXEL_LIMIT")
        png = render_page(renderer, pdf, render_dir, page_expectation.index)
        png_width, png_height, png_bytes, png_sha256 = read_png_identity(png)
        total_png_bytes += png_bytes
        if total_png_bytes > MAX_TOTAL_PNG_BYTES:
            fail("PDF_RENDER_TOTAL_SIZE_LIMIT")
        if abs(png_width - expected_png_width) > 3 or abs(png_height - expected_png_height) > 3:
            fail("PDF_RENDER_PNG_GEOMETRY_MISMATCH")
        page_result = {
            "index": page_expectation.index,
            "width_milli_mm": width,
            "height_milli_mm": height,
            "rotation": rotation,
            "extracted_text_sha256": sha256_text(text),
            "extracted_text_utf8_bytes": len(text.encode("utf-8")),
            "required_text_sha256": [sha256_text(token) for token in page_expectation.required_text],
            "forbidden_text_sha256": [sha256_text(token) for token in page_expectation.forbidden_text],
            "png_sha256": png_sha256,
            "png_bytes": png_bytes,
            "png_width": png_width,
            "png_height": png_height,
        }
        if column_flow_result is not None:
            page_result["column_flow"] = column_flow_result
        page_results.append(page_result)

    expected_outputs = {render_dir / f"page-{index:04d}.png" for index in range(1, expectation.page_count + 1)}
    try:
        actual_outputs = set(render_dir.iterdir())
    except OSError:
        fail("PDF_RENDER_DIRECTORY_INVALID")
    if actual_outputs != expected_outputs:
        fail("PDF_RENDER_OUTPUT_SET_MISMATCH")
    if sha256_file(pdf) != arguments.expected_pdf_sha256:
        fail("PDF_INPUT_CHANGED_DURING_VERIFICATION")
    if sha256_file(expectation_path) != expectation_sha256:
        fail("PDF_EXPECTATION_CHANGED_DURING_VERIFICATION")
    if sha256_file(renderer) != arguments.expected_pdftoppm_sha256:
        fail("PDF_RENDERER_CHANGED_DURING_VERIFICATION")
    if sha256_file(python_runtime) != python_runtime_sha256:
        fail("PDF_PYTHON_RUNTIME_CHANGED_DURING_VERIFICATION")
    if sha256_file(verifier_source) != verifier_sha256:
        fail("PDF_VERIFIER_CHANGED_DURING_VERIFICATION")

    result = {
        "schema_version": SCHEMA_V2 if expectation.schema_version == EXPECTATION_SCHEMA_V2 else SCHEMA,
        "state": "pass",
        "error_code": None,
        "pdf_sha256": pdf_sha256,
        "pdf_bytes": pdf_size,
        "pdf_signature_valid": True,
        "expectation_sha256": expectation_sha256,
        "page_count": len(page_results),
        "geometry_tolerance_milli_mm": expectation.tolerance_milli_mm,
        "render_dpi": RENDER_DPI,
        "renderer_sha256": renderer_sha256,
        "python_runtime_sha256": python_runtime_sha256,
        "verifier_sha256": verifier_sha256,
        "pypdf_version": PYPDF_VERSION,
        "pillow_version": PILLOW_VERSION,
        "pages": page_results,
        "raw_document_text_present": False,
        "user_document_scanned": False,
        "external_network_invoked": False,
        "pdf_modified": False,
    }
    write_new_json(trace, result)
    return result


def main(arguments: list[str]) -> int:
    namespace: argparse.Namespace | None = None
    try:
        namespace = parse_args(arguments)
        result = verify(namespace)
    except VerificationError as error:
        result = {
            "schema_version": SCHEMA,
            "state": "failed",
            "error_code": error.code,
            "raw_document_text_present": False,
            "user_document_scanned": False,
            "external_network_invoked": False,
            "pdf_modified": False,
        }
        if namespace is not None:
            write_failure_trace_if_safe(namespace, result)
        print(json.dumps(result, ensure_ascii=True, separators=(",", ":")))
        return 2
    except SystemExit:
        raise
    except Exception as error:
        result = {
            "schema_version": SCHEMA,
            "state": "failed",
            "error_code": "PDF_VERIFIER_UNEXPECTED_EXCEPTION",
            "exception_type": type(error).__name__,
            "raw_document_text_present": False,
            "user_document_scanned": False,
            "external_network_invoked": False,
            "pdf_modified": False,
        }
        if namespace is not None:
            write_failure_trace_if_safe(namespace, result)
        print(json.dumps(result, ensure_ascii=True, separators=(",", ":")))
        return 3
    print(json.dumps(result, ensure_ascii=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
