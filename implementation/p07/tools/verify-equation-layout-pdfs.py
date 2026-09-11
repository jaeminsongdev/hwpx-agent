#!/usr/bin/env python3
"""Rasterize exact P07-07 PDFs and measure bounded page ink without visual promotion."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from typing import Any, NoReturn

from PIL import Image, __version__ as PILLOW_VERSION
from pypdf import PdfReader, __version__ as PYPDF_VERSION


SCHEMA = "hwpx-agent.p07-07-equation-layout-raster-evidence/v1"
PLAN_SCHEMA = "hwpx-agent.p07-07-equation-layout-target-plan/v1"
TARGET_SCHEMA = "hwpx-agent.p07-07-equation-layout-target-evidence/v1"
PROFILE = "hwpx-agent.equation-layout.hangul-2020-11.0.0.9136-x86-ko-KR/v1"
MAX_JSON_BYTES = 4 * 1024 * 1024
MAX_PDF_BYTES = 32 * 1024 * 1024
MAX_PNG_BYTES = 16 * 1024 * 1024
MAX_RENDERER_BYTES = 128 * 1024 * 1024
MAX_PIXELS = 100_000_000
RENDER_DPI = 144
INK_THRESHOLD = 250
SHA256 = re.compile(r"^[0-9a-f]{64}$")
Image.MAX_IMAGE_PIXELS = MAX_PIXELS


class VerificationError(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class DuplicateKey(ValueError):
    pass


def fail(code: str) -> NoReturn:
    raise VerificationError(code)


def duplicate_guard(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise DuplicateKey(key)
        value[key] = item
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_reparse_point(path: Path) -> bool:
    try:
        attributes = getattr(os.lstat(path), "st_file_attributes", 0)
    except OSError:
        return False
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))


def ensure_file(path: Path, maximum: int, code: str) -> tuple[Path, int]:
    if is_reparse_point(path):
        fail(code)
    resolved = path.resolve(strict=True)
    info = resolved.stat()
    if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= maximum:
        fail(code)
    return resolved, info.st_size


def ensure_new_child(path: Path, boundary: Path, suffix: str | None, code: str) -> Path:
    resolved = path.resolve(strict=False)
    try:
        resolved.relative_to(boundary)
    except ValueError:
        fail(code)
    if resolved.parent != boundary or resolved.exists() or resolved.is_symlink():
        fail(code)
    if suffix is not None and resolved.suffix.lower() != suffix:
        fail(code)
    return resolved


def load_json(path: Path, expected_sha256: str, code: str) -> tuple[Any, int]:
    if not SHA256.fullmatch(expected_sha256):
        fail(code)
    resolved, size = ensure_file(path, MAX_JSON_BYTES, code)
    data = resolved.read_bytes()
    if len(data) != size or hashlib.sha256(data).hexdigest() != expected_sha256:
        fail(code)
    try:
        return json.loads(data, object_pairs_hook=duplicate_guard), size
    except (UnicodeDecodeError, json.JSONDecodeError, DuplicateKey):
        fail(code)


def require_digest(value: Any, code: str) -> str:
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        fail(code)
    return value


def parse_args(arguments: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--run-directory", required=True)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--expected-plan-sha256", required=True)
    parser.add_argument("--target-evidence", required=True)
    parser.add_argument("--expected-target-evidence-sha256", required=True)
    parser.add_argument("--pdftoppm", required=True)
    parser.add_argument("--expected-pdftoppm-sha256", required=True)
    parser.add_argument("--render-directory", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args(arguments)


def render_page(renderer: Path, pdf: Path, prefix: Path) -> Path:
    command = [
        str(renderer), "-png", "-r", str(RENDER_DPI), "-f", "1", "-l", "1",
        "-singlefile", str(pdf), str(prefix),
    ]
    try:
        completed = subprocess.run(
            command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=60, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        fail("LAYOUT_RENDERER_EXECUTION_FAILED")
    output = prefix.with_suffix(".png")
    if completed.returncode != 0 or completed.stdout or not output.is_file():
        fail("LAYOUT_RENDERER_EXECUTION_FAILED")
    return output


def inspect_pdf(pdf: Path, expected_sha256: str, renderer: Path, prefix: Path) -> dict[str, Any]:
    resolved, size = ensure_file(pdf, MAX_PDF_BYTES, "LAYOUT_PDF_INVALID")
    if sha256_file(resolved) != expected_sha256 or resolved.read_bytes()[:5] != b"%PDF-":
        fail("LAYOUT_PDF_IDENTITY_MISMATCH")
    try:
        reader = PdfReader(str(resolved), strict=True)
        if reader.is_encrypted or len(reader.pages) != 1:
            fail("LAYOUT_PDF_PAGE_COUNT_MISMATCH")
        page = reader.pages[0]
        rotation = int(page.get("/Rotate", 0)) % 360
        width_points = float(page.mediabox.width)
        height_points = float(page.mediabox.height)
    except VerificationError:
        raise
    except Exception:
        fail("LAYOUT_PDF_PARSE_FAILED")
    if rotation != 0 or not 590 <= width_points <= 600 or not 837 <= height_points <= 845:
        fail("LAYOUT_PDF_PAGE_GEOMETRY_MISMATCH")
    png = render_page(renderer, resolved, prefix)
    png_resolved, png_size = ensure_file(png, MAX_PNG_BYTES, "LAYOUT_PNG_INVALID")
    try:
        with Image.open(png_resolved) as image:
            if image.format != "PNG" or image.width * image.height > MAX_PIXELS:
                fail("LAYOUT_PNG_INVALID")
            gray = image.convert("L")
            mask = gray.point(lambda value: 255 if value < INK_THRESHOLD else 0)
            box = mask.getbbox()
            page_width, page_height = image.size
    except VerificationError:
        raise
    except Exception:
        fail("LAYOUT_PNG_INVALID")
    if box is None:
        fail("LAYOUT_INK_BOX_EMPTY")
    left, top, right, bottom = box
    if left <= 0 or top <= 0 or right >= page_width or bottom >= page_height:
        fail("LAYOUT_INK_BOX_TOUCHES_PAGE_EDGE")
    if sha256_file(resolved) != expected_sha256:
        fail("LAYOUT_PDF_CHANGED_DURING_RENDER")
    return {
        "pdf_sha256": expected_sha256,
        "pdf_bytes": size,
        "page_count": 1,
        "page_width_points": width_points,
        "page_height_points": height_points,
        "rotation": rotation,
        "png_sha256": sha256_file(png_resolved),
        "png_bytes": png_size,
        "ink_box": {
            "page_width_pixels": page_width,
            "page_height_pixels": page_height,
            "left": left,
            "top": top,
            "width": right - left,
            "height": bottom - top,
            "dpi": RENDER_DPI,
        },
        "edge_contact": False,
    }


def verify(arguments: argparse.Namespace) -> dict[str, Any]:
    repo = Path(__file__).resolve().parents[3]
    private = (repo / "implementation/p07/evidence/private").resolve(strict=True)
    run_input = Path(arguments.run_directory)
    if is_reparse_point(run_input):
        fail("LAYOUT_RUN_INVALID")
    run = run_input.resolve(strict=True)
    try:
        run.relative_to(private)
    except ValueError:
        fail("LAYOUT_RUN_OUTSIDE_PRIVATE_BOUNDARY")
    if run.parent != private or run.is_symlink() or not run.is_dir():
        fail("LAYOUT_RUN_INVALID")
    plan_path, _ = ensure_file(Path(arguments.plan), MAX_JSON_BYTES, "LAYOUT_PLAN_INVALID")
    target_path, _ = ensure_file(
        Path(arguments.target_evidence), MAX_JSON_BYTES, "LAYOUT_TARGET_EVIDENCE_INVALID"
    )
    if plan_path.parent != run or target_path.parent != run:
        fail("LAYOUT_EVIDENCE_OUTSIDE_RUN")
    plan, _ = load_json(
        plan_path, arguments.expected_plan_sha256, "LAYOUT_PLAN_IDENTITY_MISMATCH"
    )
    target, _ = load_json(
        target_path, arguments.expected_target_evidence_sha256,
        "LAYOUT_TARGET_EVIDENCE_IDENTITY_MISMATCH",
    )
    if (
        not isinstance(plan, dict) or plan.get("schema_version") != PLAN_SCHEMA
        or plan.get("profile_version") != PROFILE or len(plan.get("samples", [])) != 8
        or not isinstance(target, dict) or target.get("schema_version") != TARGET_SCHEMA
        or target.get("profile_version") != PROFILE
        or target.get("state") != "native_pass_visual_not_run"
        or target.get("plan_file_sha256") != arguments.expected_plan_sha256
        or len(target.get("samples", [])) != 8
    ):
        fail("LAYOUT_INPUT_CONTRACT_MISMATCH")
    renderer, _ = ensure_file(
        Path(arguments.pdftoppm), MAX_RENDERER_BYTES, "LAYOUT_RENDERER_INVALID"
    )
    renderer_sha256 = require_digest(
        arguments.expected_pdftoppm_sha256, "LAYOUT_RENDERER_SHA256_INVALID"
    )
    if sha256_file(renderer) != renderer_sha256:
        fail("LAYOUT_RENDERER_IDENTITY_MISMATCH")
    render_dir = ensure_new_child(
        Path(arguments.render_directory), run, None, "LAYOUT_RENDER_DIRECTORY_INVALID"
    )
    output = ensure_new_child(Path(arguments.output), run, ".json", "LAYOUT_OUTPUT_INVALID")
    render_dir.mkdir(mode=0o700)
    results: list[dict[str, Any]] = []
    for index, (sample, observed) in enumerate(
        zip(plan["samples"], target["samples"], strict=True)
    ):
        if not isinstance(sample, dict) or not isinstance(observed, dict):
            fail("LAYOUT_SAMPLE_SHAPE_INVALID")
        sample_id = sample.get("id")
        layout = sample.get("layout")
        if (
            not isinstance(sample_id, str) or observed.get("id") != sample_id
            or layout not in {"inline", "display"} or observed.get("layout") != layout
        ):
            fail("LAYOUT_SAMPLE_IDENTITY_MISMATCH")
        pdf_sha256 = require_digest(observed.get("pdf_sha256"), "LAYOUT_PDF_SHA256_INVALID")
        pdf = run / f"{sample_id}.pdf"
        prefix = render_dir / f"sample-{index + 1:03d}-{sample_id}"
        item = inspect_pdf(pdf, pdf_sha256, renderer, prefix)
        item.update({"id": sample_id, "ordinal": index, "layout": layout})
        results.append(item)
    expected_pngs = {
        render_dir / f"sample-{index + 1:03d}-{sample['id']}.png"
        for index, sample in enumerate(plan["samples"])
    }
    if set(render_dir.iterdir()) != expected_pngs:
        fail("LAYOUT_RENDER_OUTPUT_SET_MISMATCH")
    if (
        sha256_file(plan_path) != arguments.expected_plan_sha256
        or sha256_file(target_path) != arguments.expected_target_evidence_sha256
        or sha256_file(renderer) != renderer_sha256
    ):
        fail("LAYOUT_INPUT_CHANGED_DURING_VERIFICATION")
    return {
        "schema_version": SCHEMA,
        "profile_version": PROFILE,
        "state": "structural_pass_manual_not_run",
        "plan_sha256": plan["plan_sha256"],
        "plan_file_sha256": arguments.expected_plan_sha256,
        "target_evidence_sha256": arguments.expected_target_evidence_sha256,
        "renderer": "pdftoppm",
        "renderer_sha256": renderer_sha256,
        "render_dpi": RENDER_DPI,
        "ink_threshold": INK_THRESHOLD,
        "python_executable_sha256": sha256_file(Path(sys.executable).resolve(strict=True)),
        "verifier_sha256": sha256_file(Path(__file__).resolve(strict=True)),
        "pypdf_version": PYPDF_VERSION,
        "pillow_version": PILLOW_VERSION,
        "sample_count": 8,
        "all_pages_rasterized": True,
        "edge_contact_count": 0,
        "samples": results,
        "manual_review_state": "not_run",
        "all_pages_inspected": False,
        "qualification_eligible": False,
        "raw_document_text_present": False,
        "user_document_opened": False,
        "computer_use_click_or_type_invoked": False,
        "p07_07_complete": False,
        "p07_complete": False,
        "product_complete": False,
    }


def write_new_json(path: Path, value: dict[str, Any]) -> None:
    encoded = (json.dumps(value, ensure_ascii=True, separators=(",", ":")) + "\n").encode()
    if len(encoded) > MAX_JSON_BYTES:
        fail("LAYOUT_OUTPUT_LIMIT")
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


def main(arguments: list[str]) -> int:
    namespace = parse_args(arguments)
    try:
        value = verify(namespace)
        output = Path(namespace.output).resolve(strict=False)
        write_new_json(output, value)
        print(json.dumps({
            "schema_version": "hwpx-agent.p07-07-equation-layout-raster-receipt/v1",
            "state": value["state"],
            "output_sha256": sha256_file(output),
            "sample_count": value["sample_count"],
            "qualification_eligible": False,
            "product_complete": False,
        }, separators=(",", ":")))
        return 0
    except VerificationError as error:
        print(error.code, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
