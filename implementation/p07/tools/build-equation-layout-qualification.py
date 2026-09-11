#!/usr/bin/env python3
"""Build a strict P07-07 qualification only from target, raster, and manual evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from typing import Any, NoReturn


QUALIFICATION_SCHEMA = "hwpx-agent.equation-layout-qualification/v1"
PLAN_SCHEMA = "hwpx-agent.p07-07-equation-layout-target-plan/v1"
TARGET_SCHEMA = "hwpx-agent.p07-07-equation-layout-target-evidence/v1"
RASTER_SCHEMA = "hwpx-agent.p07-07-equation-layout-raster-evidence/v1"
MANUAL_SCHEMA = "hwpx-agent.p07-07-equation-layout-manual-review/v1"
PROFILE = "hwpx-agent.equation-layout.hangul-2020-11.0.0.9136-x86-ko-KR/v1"
MAX_JSON_BYTES = 4 * 1024 * 1024
MAX_EXTENT_ERROR = 150
MAX_BASELINE_ERROR = 50
SHA256 = re.compile(r"^[0-9a-f]{64}$")
METRIC_KEYS = {
    "advance_units", "above_levels", "below_levels", "nodes", "depth",
    "matrix_rows", "matrix_columns",
}


class QualificationError(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class DuplicateKey(ValueError):
    pass


def fail(code: str) -> NoReturn:
    raise QualificationError(code)


def duplicate_guard(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise DuplicateKey(key)
        value[key] = item
    return value


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    return sha256_bytes(json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode())


def is_reparse_point(path: Path) -> bool:
    try:
        attributes = getattr(os.lstat(path), "st_file_attributes", 0)
    except OSError:
        return False
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))


def ensure_file(path: Path, code: str) -> tuple[Path, int]:
    if is_reparse_point(path):
        fail(code)
    resolved = path.resolve(strict=True)
    info = resolved.stat()
    if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= MAX_JSON_BYTES:
        fail(code)
    return resolved, info.st_size


def load_exact(path: Path, expected_sha256: str, code: str) -> tuple[dict[str, Any], Path]:
    if not SHA256.fullmatch(expected_sha256):
        fail(code)
    resolved, size = ensure_file(path, code)
    data = resolved.read_bytes()
    if len(data) != size or sha256_bytes(data) != expected_sha256:
        fail(code)
    try:
        value = json.loads(data, object_pairs_hook=duplicate_guard)
    except (UnicodeDecodeError, json.JSONDecodeError, DuplicateKey):
        fail(code)
    if not isinstance(value, dict):
        fail(code)
    return value, resolved


def require_digest(value: Any, code: str) -> str:
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        fail(code)
    return value


def require_int(value: Any, minimum: int, maximum: int, code: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        fail(code)
    return value


def parse_args(arguments: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--run-directory", required=True)
    for name in ["plan", "target-evidence", "raster-evidence", "manual-review"]:
        parser.add_argument(f"--{name}", required=True)
        parser.add_argument(f"--expected-{name}-sha256", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args(arguments)


def fit_linear(samples: list[tuple[int, int]], maximum_slope: int) -> tuple[int, int, int]:
    best: tuple[int, int, int] | None = None
    for slope in range(1, maximum_slope + 1):
        residuals = [observed - units * slope for units, observed in samples]
        midpoint = (min(residuals) + max(residuals)) // 2
        for intercept in {max(1, min(100_000, midpoint)), max(1, min(100_000, midpoint + 1))}:
            error = max(abs(units * slope + intercept - observed) for units, observed in samples)
            candidate = (error, slope, intercept)
            if best is None or candidate < best:
                best = candidate
    if best is None:
        fail("LAYOUT_MODEL_FIT_FAILED")
    return best


def baseline_hwpunit(height: int, percent: int) -> int:
    return (height * percent + 50) // 100


def fit_baseline(
    mode: str, samples: list[dict[str, Any]], line_height: int, vertical_level: int
) -> tuple[int, int]:
    selected = [sample for sample in samples if sample["layout"] == mode]
    best: tuple[int, int] | None = None
    for percent in range(1, 101):
        error = 0
        for sample in selected:
            metrics = sample["metrics"]
            levels = metrics["above_levels"] + metrics["below_levels"] + 1
            predicted_height = line_height + levels * vertical_level
            predicted = baseline_hwpunit(predicted_height, percent)
            observed = baseline_hwpunit(sample["height_hwpunit"], sample["baseline_percent"])
            error = max(error, abs(predicted - observed))
        candidate = (error, percent)
        if best is None or candidate < best:
            best = candidate
    if best is None:
        fail("LAYOUT_BASELINE_FIT_FAILED")
    return best


def validate_manual(
    manual: dict[str, Any], plan_sha256: str, target_sha256: str, raster_sha256: str,
    raster_samples: list[dict[str, Any]],
) -> None:
    expected_keys = {
        "schema_version", "profile_version", "plan_sha256", "target_evidence_sha256",
        "raster_evidence_sha256", "state", "inspection_detail", "sample_count", "samples",
        "all_pages_inspected", "clipping_count", "overlap_count", "silent_fallback_count",
        "user_document_opened", "computer_use_click_or_type_invoked", "product_complete",
    }
    if set(manual) != expected_keys or (
        manual.get("schema_version") != MANUAL_SCHEMA or manual.get("profile_version") != PROFILE
        or manual.get("plan_sha256") != plan_sha256
        or manual.get("target_evidence_sha256") != target_sha256
        or manual.get("raster_evidence_sha256") != raster_sha256
        or manual.get("state") != "pass" or manual.get("inspection_detail") != "original"
        or manual.get("sample_count") != 8 or manual.get("all_pages_inspected") is not True
        or manual.get("clipping_count") != 0 or manual.get("overlap_count") != 0
        or manual.get("silent_fallback_count") != 0
        or manual.get("user_document_opened") is not False
        or manual.get("computer_use_click_or_type_invoked") is not False
        or manual.get("product_complete") is not False
        or not isinstance(manual.get("samples"), list) or len(manual["samples"]) != 8
    ):
        fail("LAYOUT_MANUAL_REVIEW_CONTRACT_MISMATCH")
    for index, (review, raster) in enumerate(zip(manual["samples"], raster_samples, strict=True)):
        if not isinstance(review, dict) or set(review) != {
            "id", "ordinal", "png_sha256", "clipping", "overlap", "silent_fallback"
        } or (
            review.get("id") != raster.get("id") or review.get("ordinal") != index
            or review.get("png_sha256") != raster.get("png_sha256")
            or review.get("clipping") is not False or review.get("overlap") is not False
            or review.get("silent_fallback") is not False
        ):
            fail("LAYOUT_MANUAL_SAMPLE_MISMATCH")


def build(arguments: argparse.Namespace) -> tuple[dict[str, Any], Path]:
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
    names = {
        "plan": (arguments.plan, arguments.expected_plan_sha256, "LAYOUT_PLAN_IDENTITY_MISMATCH"),
        "target": (
            arguments.target_evidence, arguments.expected_target_evidence_sha256,
            "LAYOUT_TARGET_EVIDENCE_IDENTITY_MISMATCH",
        ),
        "raster": (
            arguments.raster_evidence, arguments.expected_raster_evidence_sha256,
            "LAYOUT_RASTER_EVIDENCE_IDENTITY_MISMATCH",
        ),
        "manual": (
            arguments.manual_review, arguments.expected_manual_review_sha256,
            "LAYOUT_MANUAL_REVIEW_IDENTITY_MISMATCH",
        ),
    }
    loaded: dict[str, dict[str, Any]] = {}
    paths: dict[str, Path] = {}
    for name, (path, digest, code) in names.items():
        loaded[name], paths[name] = load_exact(Path(path), digest, code)
        if paths[name].parent != run:
            fail("LAYOUT_INPUT_OUTSIDE_RUN")
    plan, target, raster, manual = (
        loaded["plan"], loaded["target"], loaded["raster"], loaded["manual"]
    )
    if (
        plan.get("schema_version") != PLAN_SCHEMA or plan.get("profile_version") != PROFILE
        or target.get("schema_version") != TARGET_SCHEMA or target.get("profile_version") != PROFILE
        or target.get("state") != "native_pass_visual_not_run"
        or raster.get("schema_version") != RASTER_SCHEMA or raster.get("profile_version") != PROFILE
        or raster.get("state") != "structural_pass_manual_not_run"
        or raster.get("manual_review_state") != "not_run"
        or raster.get("qualification_eligible") is not False
        or raster.get("all_pages_rasterized") is not True or raster.get("edge_contact_count") != 0
        or not isinstance(plan.get("samples"), list) or len(plan["samples"]) != 8
        or not isinstance(target.get("samples"), list) or len(target["samples"]) != 8
        or not isinstance(raster.get("samples"), list) or len(raster["samples"]) != 8
        or target.get("plan_file_sha256") != arguments.expected_plan_sha256
        or raster.get("plan_file_sha256") != arguments.expected_plan_sha256
        or raster.get("target_evidence_sha256") != arguments.expected_target_evidence_sha256
    ):
        fail("LAYOUT_EVIDENCE_CONTRACT_MISMATCH")
    plan_sha256 = require_digest(plan.get("plan_sha256"), "LAYOUT_PLAN_DIGEST_INVALID")
    validate_manual(
        manual, plan_sha256, arguments.expected_target_evidence_sha256,
        arguments.expected_raster_evidence_sha256, raster["samples"],
    )

    samples: list[dict[str, Any]] = []
    for index, (planned, observed, rendered) in enumerate(
        zip(plan["samples"], target["samples"], raster["samples"], strict=True)
    ):
        if not all(isinstance(value, dict) for value in (planned, observed, rendered)):
            fail("LAYOUT_SAMPLE_SHAPE_INVALID")
        sample_id = planned.get("id")
        layout = planned.get("layout")
        metrics = observed.get("metrics")
        if (
            not isinstance(sample_id, str) or observed.get("id") != sample_id
            or rendered.get("id") != sample_id or observed.get("layout") != layout
            or rendered.get("layout") != layout or layout not in {"inline", "display"}
            or planned.get("ordinal") != index or rendered.get("ordinal") != index
            or planned.get("base_unit") != 1000 or not isinstance(metrics, dict)
            or set(metrics) != METRIC_KEYS or metrics != planned.get("metrics")
        ):
            fail("LAYOUT_SAMPLE_IDENTITY_MISMATCH")
        checked_metrics = {
            key: require_int(
                value,
                0 if key in {"above_levels", "below_levels", "matrix_rows", "matrix_columns"} else 1,
                1_000_000,
                "LAYOUT_SAMPLE_METRICS_INVALID",
            )
            for key, value in metrics.items()
        }
        ink = rendered.get("ink_box")
        if not isinstance(ink, dict) or set(ink) != {
            "page_width_pixels", "page_height_pixels", "left", "top", "width", "height", "dpi"
        }:
            fail("LAYOUT_SAMPLE_INK_BOX_INVALID")
        checked_ink = {
            "page_width_pixels": require_int(ink["page_width_pixels"], 1, 100_000, "LAYOUT_SAMPLE_INK_BOX_INVALID"),
            "page_height_pixels": require_int(ink["page_height_pixels"], 1, 100_000, "LAYOUT_SAMPLE_INK_BOX_INVALID"),
            "left": require_int(ink["left"], 1, 99_999, "LAYOUT_SAMPLE_INK_BOX_INVALID"),
            "top": require_int(ink["top"], 1, 99_999, "LAYOUT_SAMPLE_INK_BOX_INVALID"),
            "width": require_int(ink["width"], 1, 100_000, "LAYOUT_SAMPLE_INK_BOX_INVALID"),
            "height": require_int(ink["height"], 1, 100_000, "LAYOUT_SAMPLE_INK_BOX_INVALID"),
            "dpi": require_int(ink["dpi"], 72, 1_200, "LAYOUT_SAMPLE_INK_BOX_INVALID"),
        }
        if (
            checked_ink["left"] + checked_ink["width"] >= checked_ink["page_width_pixels"]
            or checked_ink["top"] + checked_ink["height"] >= checked_ink["page_height_pixels"]
        ):
            fail("LAYOUT_SAMPLE_INK_BOX_INVALID")
        samples.append({
            "semantic_sha256": require_digest(planned.get("semantic_sha256"), "LAYOUT_SAMPLE_DIGEST_INVALID"),
            "layout": layout,
            "base_unit": 1000,
            "width_hwpunit": require_int(observed.get("width_hwpunit"), 1, 10_000_000, "LAYOUT_SAMPLE_EXTENT_INVALID"),
            "height_hwpunit": require_int(observed.get("height_hwpunit"), 1, 10_000_000, "LAYOUT_SAMPLE_EXTENT_INVALID"),
            "baseline_percent": require_int(observed.get("baseline_percent"), 1, 100, "LAYOUT_SAMPLE_BASELINE_INVALID"),
            "native_readback_sha256": require_digest(observed.get("native_readback_sha256"), "LAYOUT_SAMPLE_DIGEST_INVALID"),
            "render_evidence_sha256": require_digest(rendered.get("png_sha256"), "LAYOUT_SAMPLE_DIGEST_INVALID"),
            "metrics": checked_metrics,
            "ink_box": checked_ink,
        })
    if sum(sample["layout"] == "inline" for sample in samples) != 4:
        fail("LAYOUT_SAMPLE_MODE_COVERAGE_INVALID")

    width_error, width_slope, width_padding = fit_linear(
        [(sample["metrics"]["advance_units"], sample["width_hwpunit"]) for sample in samples],
        10_000,
    )
    height_error, vertical_level, line_height = fit_linear([
        (
            sample["metrics"]["above_levels"] + sample["metrics"]["below_levels"] + 1,
            sample["height_hwpunit"],
        ) for sample in samples
    ], 100_000)
    inline_baseline_error, inline_baseline = fit_baseline(
        "inline", samples, line_height, vertical_level
    )
    display_baseline_error, display_baseline = fit_baseline(
        "display", samples, line_height, vertical_level
    )
    extent_error = max(width_error, height_error)
    baseline_error = max(inline_baseline_error, display_baseline_error)
    if extent_error > MAX_EXTENT_ERROR or baseline_error > MAX_BASELINE_ERROR:
        fail("LAYOUT_MODEL_THRESHOLD_FAILED")
    evidence_bundle = {
        "plan_file_sha256": arguments.expected_plan_sha256,
        "target_evidence_sha256": arguments.expected_target_evidence_sha256,
        "raster_evidence_sha256": arguments.expected_raster_evidence_sha256,
        "manual_review_sha256": arguments.expected_manual_review_sha256,
    }
    qualification = {
        "schema_version": QUALIFICATION_SCHEMA,
        "profile_version": PROFILE,
        "target": {
            "build": "11.0.0.9136", "architecture": "x86", "locale": "ko-KR",
            "font_name": "HancomEQN",
        },
        "evidence_sha256": canonical_sha256(evidence_bundle),
        "font_metrics_sha256": canonical_sha256([
            {
                "semantic_sha256": sample["semantic_sha256"], "layout": sample["layout"],
                "width_hwpunit": sample["width_hwpunit"], "height_hwpunit": sample["height_hwpunit"],
                "baseline_percent": sample["baseline_percent"], "metrics": sample["metrics"],
            } for sample in samples
        ]),
        "corpus_semantic_sha256": canonical_sha256(sorted({
            sample["semantic_sha256"] for sample in samples
        })),
        "model": {
            "width_per_advance_milli": width_slope,
            "horizontal_padding_milli": width_padding,
            "line_height_milli": line_height,
            "vertical_level_milli": vertical_level,
            "inline_baseline_percent": inline_baseline,
            "display_baseline_percent": display_baseline,
        },
        "envelope": {
            "maximum_nodes": max(sample["metrics"]["nodes"] for sample in samples),
            "maximum_depth": max(sample["metrics"]["depth"] for sample in samples),
            "maximum_advance_units": max(sample["metrics"]["advance_units"] for sample in samples),
            "maximum_vertical_levels": max(
                sample["metrics"]["above_levels"] + sample["metrics"]["below_levels"] + 1
                for sample in samples
            ),
            "maximum_matrix_rows": max(sample["metrics"]["matrix_rows"] for sample in samples),
            "maximum_matrix_columns": max(sample["metrics"]["matrix_columns"] for sample in samples),
        },
        "validation": {
            "sample_count": 8, "inline_sample_count": 4, "display_sample_count": 4,
            "extent_max_error_hwpunit": extent_error,
            "baseline_max_error_hwpunit": baseline_error,
            "ink_box_overflow_count": 0, "clipping_count": 0, "overlap_count": 0,
            "silent_fallback_count": 0, "all_pages_inspected": True,
        },
        "exact_samples": samples,
    }
    output = Path(arguments.output).resolve(strict=False)
    try:
        output.relative_to(run)
    except ValueError:
        fail("LAYOUT_OUTPUT_OUTSIDE_RUN")
    if output.parent != run or output.suffix.lower() != ".json" or output.exists() or output.is_symlink():
        fail("LAYOUT_OUTPUT_INVALID")
    for name, path in paths.items():
        if sha256_file(path) != getattr(arguments, f"expected_{'target_evidence' if name == 'target' else 'raster_evidence' if name == 'raster' else 'manual_review' if name == 'manual' else 'plan'}_sha256"):
            fail("LAYOUT_INPUT_CHANGED_DURING_BUILD")
    return qualification, output


def write_new_json(path: Path, value: dict[str, Any]) -> None:
    encoded = (json.dumps(value, ensure_ascii=True, separators=(",", ":")) + "\n").encode()
    if len(encoded) > MAX_JSON_BYTES:
        fail("LAYOUT_OUTPUT_LIMIT")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            descriptor = -1
            stream.write(encoded); stream.flush(); os.fsync(stream.fileno())
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def main(arguments: list[str]) -> int:
    namespace = parse_args(arguments)
    try:
        qualification, output = build(namespace)
        write_new_json(output, qualification)
        print(json.dumps({
            "schema_version": "hwpx-agent.p07-07-equation-layout-qualification-build/v1",
            "state": "candidate_pass", "qualification_sha256": sha256_file(output),
            "sample_count": 8, "qualification_candidate": True,
            "actual_hangul_asserted_by_builder": False,
            "render_asserted_by_builder": False,
            "product_complete": False,
        }, separators=(",", ":")))
        return 0
    except QualificationError as error:
        print(error.code, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
