#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any

try:
    from tools.p06 import render_table_pending_22_target_batch as render
except ModuleNotFoundError:
    import render_table_pending_22_target_batch as render  # type: ignore[no-redef]


OBSERVATION_SCHEMA = (
    "hwpx-agent.p06-09-table-pending-22-visual-review-observations/v1"
)
RECEIPT_SCHEMA = "hwpx-agent.p06-09-table-pending-22-visual-review-receipt/v1"
TRACE_NAME = "pending-22-trace.json"
ORACLE_RECEIPT_NAME = "pending-22-oracle-receipt.json"
RENDER_MANIFEST_NAME = "pending-22-render-manifest.json"
OBSERVATION_NAME = "pending-22-visual-review-observations.json"
RECEIPT_NAME = "pending-22-visual-review-receipt.json"
ACCESS_PROMPT_ACTION = "user_attested_allow_all"
FINDING_RE = re.compile(r"[^\x00-\x1f\x7f]{1,500}\Z")

EXPECTED_MANIFEST_KEYS = {
    "schema_version",
    "state",
    "scope",
    "target",
    "trace_sha256",
    "oracle_receipt_sha256",
    "renderer",
    "pdf_inspector",
    "dpi",
    "case_count",
    "cases",
    "visual_review",
    "not_claimed",
}
EXPECTED_MANIFEST_CASE_KEYS = {
    "feature_id",
    "case_id",
    "group_id",
    "pdf_file",
    "pdf_sha256",
    "pdf_metadata",
    "png_file",
    "bytes",
    "sha256",
    "pixel_size",
    "visual_review_state",
}
EXPECTED_PDF_METADATA_KEYS = {
    "pages",
    "page_size_points",
    "page_rotation",
    "encrypted",
    "pdf_version",
    "creator",
    "producer",
}
EXPECTED_OBSERVATION_KEYS = {
    "schema_version",
    "state",
    "render_manifest_sha256",
    "review_actor",
    "inspection_detail",
    "all_pages_inspected",
    "computer_use_click_or_type_invoked",
    "user_access_prompt_action",
    "cases",
    "not_claimed",
}
EXPECTED_OBSERVATION_CASE_KEYS = {
    "feature_id",
    "case_id",
    "png_sha256",
    "png_bytes",
    "pixel_size",
    "state",
    "clipping",
    "overlap",
    "blank_page",
    "black_boxes",
    "finding",
}
NOT_CLAIMED = {
    "automation_runtime": False,
    "differential_exact_match": False,
    "arbitrary_user_document_compatibility": False,
    "other_pc_or_hancom_version": False,
    "p06_09_complete": False,
    "p06_complete": False,
    "product_complete": False,
}


class VisualReviewError(ValueError):
    pass


def exact_keys(value: Any, expected: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != expected:
        raise VisualReviewError(f"{label}_shape_mismatch")
    return value


def load_json(path: Path, root: Path) -> tuple[dict[str, Any], str, Path]:
    resolved = render.bounded_existing(path, root, render.MAX_JSON_BYTES)
    value, sha256 = render.load_json(resolved, root)
    return value, sha256, resolved


def require_sha256(actual: str, expected: Any, label: str) -> None:
    render.exact_sha256(expected, label)
    if actual != expected:
        raise VisualReviewError(f"{label}_sha256_mismatch")


def require_exact_attempt_file(path: Path, name: str) -> Path:
    attempt = path.parent
    if (
        path.name != name
        or attempt.parent != render.TARGET_ROOT
        or render.ATTEMPT_RE.fullmatch(attempt.name) is None
        or render._is_link(attempt)
    ):
        raise VisualReviewError("attempt_file_boundary_mismatch")
    return attempt


def validate_manifest(
    manifest: dict[str, Any], manifest_sha256: str, attempt: Path
) -> list[dict[str, Any]]:
    exact_keys(manifest, EXPECTED_MANIFEST_KEYS, "render_manifest")
    if (
        manifest["schema_version"] != render.OUTPUT_SCHEMA
        or manifest["state"] != "rendered_not_reviewed"
        or manifest["scope"]
        != "current_pc_exact_hancom_2020_pending_22_review_candidates"
        or manifest["target"] != render.EXPECTED_TRACE_TARGET
        or manifest["renderer"] != "pdftoppm 26.07.0"
        or manifest["pdf_inspector"] != "pdfinfo 26.07.0"
        or manifest["dpi"] != 144
        or manifest["case_count"] != 22
        or manifest["visual_review"]
        != {
            "state": "not_run",
            "required_detail": "original",
            "all_pages_inspected": False,
            "clipping": "unverified",
            "overlap": "unverified",
            "blank_pages": "unverified",
            "black_boxes": "unverified",
        }
        or manifest["not_claimed"]
        != {
            "render_diff": False,
            "direct_oracle_promotion": False,
            "automation_runtime": False,
            "differential": False,
            "p06_09_complete": False,
            "p06_complete": False,
            "product_complete": False,
        }
    ):
        raise VisualReviewError("render_manifest_boundary_mismatch")
    render.exact_sha256(manifest["trace_sha256"], "trace")
    render.exact_sha256(manifest["oracle_receipt_sha256"], "oracle")
    render.exact_sha256(manifest_sha256, "render_manifest")
    trace_path = render.bounded_existing(
        attempt / TRACE_NAME, attempt, render.MAX_JSON_BYTES
    )
    oracle_path = render.bounded_existing(
        attempt / ORACLE_RECEIPT_NAME, attempt, render.MAX_JSON_BYTES
    )
    require_sha256(
        render.sha256_file(trace_path, render.MAX_JSON_BYTES),
        manifest["trace_sha256"],
        "trace",
    )
    require_sha256(
        render.sha256_file(oracle_path, render.MAX_JSON_BYTES),
        manifest["oracle_receipt_sha256"],
        "oracle",
    )

    cases = manifest["cases"]
    if not isinstance(cases, list) or len(cases) != 22:
        raise VisualReviewError("render_manifest_case_count_mismatch")
    checked: list[dict[str, Any]] = []
    for case, feature_id, group_id in zip(
        cases, render.EXPECTED_FEATURES, render.EXPECTED_GROUPS, strict=True
    ):
        actual = exact_keys(case, EXPECTED_MANIFEST_CASE_KEYS, "render_case")
        case_id = actual["case_id"]
        if (
            actual["feature_id"] != feature_id
            or actual["group_id"] != group_id
            or not isinstance(case_id, str)
            or render.CASE_ID_RE.fullmatch(case_id) is None
            or actual["pdf_file"] != f"{case_id}.hancom-2020-render.pdf"
            or actual["png_file"]
            != f"rendered/{feature_id.lower()}-{case_id}.png"
            or actual["visual_review_state"] != "not_run"
        ):
            raise VisualReviewError("render_case_boundary_mismatch")
        render.exact_sha256(actual["pdf_sha256"], "pdf")
        render.exact_sha256(actual["sha256"], "png")
        metadata = exact_keys(
            actual["pdf_metadata"], EXPECTED_PDF_METADATA_KEYS, "pdf_metadata"
        )
        page_size = metadata["page_size_points"]
        if (
            metadata["pages"] != 1
            or metadata["page_rotation"] != 0
            or metadata["encrypted"] is not False
            or metadata["pdf_version"] != "1.4"
            or metadata["creator"] != "Hwp 2020 11.0.0.9136"
            or metadata["producer"] != "Hancom PDF 1.3.0.550"
            or not isinstance(page_size, list)
            or len(page_size) != 2
            or not 594 <= page_size[0] <= 596
            or not 840 <= page_size[1] <= 843
        ):
            raise VisualReviewError("pdf_metadata_boundary_mismatch")

        group_root = render.exact_group_root(group_id)
        pdf_path = render.bounded_existing(
            group_root / actual["pdf_file"], group_root, render.MAX_PDF_BYTES
        )
        require_sha256(
            render.sha256_file(pdf_path, render.MAX_PDF_BYTES),
            actual["pdf_sha256"],
            "pdf",
        )
        png_path = render.bounded_existing(
            attempt / actual["png_file"], attempt, render.MAX_PNG_BYTES
        )
        png_identity = render.png_identity(png_path)
        if (
            png_identity["sha256"] != actual["sha256"]
            or png_identity["bytes"] != actual["bytes"]
            or png_identity["pixel_size"] != actual["pixel_size"]
        ):
            raise VisualReviewError("png_identity_mismatch")
        checked.append(actual)
    return checked


def recheck_artifacts(attempt: Path, manifest: dict[str, Any]) -> None:
    require_sha256(
        render.sha256_file(
            render.bounded_existing(
                attempt / TRACE_NAME, attempt, render.MAX_JSON_BYTES
            ),
            render.MAX_JSON_BYTES,
        ),
        manifest["trace_sha256"],
        "trace_recheck",
    )
    require_sha256(
        render.sha256_file(
            render.bounded_existing(
                attempt / ORACLE_RECEIPT_NAME, attempt, render.MAX_JSON_BYTES
            ),
            render.MAX_JSON_BYTES,
        ),
        manifest["oracle_receipt_sha256"],
        "oracle_recheck",
    )
    for case in manifest["cases"]:
        group_root = render.exact_group_root(case["group_id"])
        pdf_path = render.bounded_existing(
            group_root / case["pdf_file"], group_root, render.MAX_PDF_BYTES
        )
        require_sha256(
            render.sha256_file(pdf_path, render.MAX_PDF_BYTES),
            case["pdf_sha256"],
            "pdf_recheck",
        )
        png_path = render.bounded_existing(
            attempt / case["png_file"], attempt, render.MAX_PNG_BYTES
        )
        identity = render.png_identity(png_path)
        if (
            identity["sha256"] != case["sha256"]
            or identity["bytes"] != case["bytes"]
            or identity["pixel_size"] != case["pixel_size"]
        ):
            raise VisualReviewError("png_recheck_mismatch")


def validate_observations(
    observations: dict[str, Any], manifest_sha256: str, cases: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    exact_keys(observations, EXPECTED_OBSERVATION_KEYS, "observations")
    if (
        observations["schema_version"] != OBSERVATION_SCHEMA
        or observations["state"] != "pass"
        or observations["render_manifest_sha256"] != manifest_sha256
        or observations["review_actor"] != "assistant_visual_review"
        or observations["inspection_detail"] != "original"
        or observations["all_pages_inspected"] is not True
        or observations["computer_use_click_or_type_invoked"] is not False
        or observations["user_access_prompt_action"] != ACCESS_PROMPT_ACTION
        or observations["not_claimed"] != NOT_CLAIMED
    ):
        raise VisualReviewError("observations_boundary_mismatch")
    review_cases = observations["cases"]
    if not isinstance(review_cases, list) or len(review_cases) != 22:
        raise VisualReviewError("observations_case_count_mismatch")
    checked: list[dict[str, Any]] = []
    for observed, rendered in zip(review_cases, cases, strict=True):
        actual = exact_keys(
            observed, EXPECTED_OBSERVATION_CASE_KEYS, "observation_case"
        )
        finding = actual["finding"]
        if (
            actual["feature_id"] != rendered["feature_id"]
            or actual["case_id"] != rendered["case_id"]
            or actual["png_sha256"] != rendered["sha256"]
            or actual["png_bytes"] != rendered["bytes"]
            or actual["pixel_size"] != rendered["pixel_size"]
            or actual["state"] != "pass"
            or any(
                actual[key] is not False
                for key in ("clipping", "overlap", "blank_page", "black_boxes")
            )
            or not isinstance(finding, str)
            or FINDING_RE.fullmatch(finding) is None
        ):
            raise VisualReviewError("observation_case_boundary_mismatch")
        checked.append(actual)
    return checked


def build_receipt(
    attempt_name: str,
    manifest_sha256: str,
    observation_sha256: str,
    manifest: dict[str, Any],
    rendered_cases: list[dict[str, Any]],
    observations: list[dict[str, Any]],
) -> dict[str, Any]:
    cases = []
    for rendered, observed in zip(rendered_cases, observations, strict=True):
        cases.append(
            {
                "feature_id": rendered["feature_id"],
                "case_id": rendered["case_id"],
                "group_id": rendered["group_id"],
                "pdf_sha256": rendered["pdf_sha256"],
                "png_file": rendered["png_file"],
                "png_sha256": rendered["sha256"],
                "png_bytes": rendered["bytes"],
                "pixel_size": rendered["pixel_size"],
                "visual_review_state": "pass",
                "finding": observed["finding"],
            }
        )
    return {
        "schema_version": RECEIPT_SCHEMA,
        "state": "pass",
        "scope": "exact_current_pc_hancom_2020_pending_22_direct_oracle_and_render",
        "attempt_name": attempt_name,
        "target": render.EXPECTED_TRACE_TARGET,
        "render_manifest": {
            "file": RENDER_MANIFEST_NAME,
            "sha256": manifest_sha256,
        },
        "review_observations": {
            "file": OBSERVATION_NAME,
            "sha256": observation_sha256,
            "review_actor": "assistant_visual_review",
            "computer_use_click_or_type_invoked": False,
            "user_access_prompt_action": ACCESS_PROMPT_ACTION,
        },
        "trace_sha256": manifest["trace_sha256"],
        "oracle_receipt_sha256": manifest["oracle_receipt_sha256"],
        "renderer": manifest["renderer"],
        "dpi": manifest["dpi"],
        "case_count": 22,
        "feature_ids": list(render.EXPECTED_FEATURES),
        "cases": cases,
        "render_review": {
            "state": "pass",
            "all_pages_inspected": True,
            "inspection_detail": "original",
            "review_actor": "assistant_visual_review",
            "clipping": False,
            "overlap": False,
            "blank_pages": [],
            "black_boxes": False,
        },
        "gate_decision": {
            "direct_feature_stage": "oracle_verified",
            "direct_feature_count": 22,
            "direct_evidence_promotion_ready": True,
            "automation_runtime": "not_run",
            "differential": "not_run",
            "p06_09": "in_progress",
            "p06": "in_progress",
        },
        "not_claimed": NOT_CLAIMED,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Fail-closed finalizer for all 22 original-detail table render reviews."
        )
    )
    parser.add_argument("--render-manifest", required=True, type=Path)
    parser.add_argument("--render-manifest-sha256", required=True)
    parser.add_argument("--review-observations", required=True, type=Path)
    parser.add_argument("--review-observations-sha256", required=True)
    parser.add_argument("--output-receipt", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest, manifest_sha256, manifest_path = load_json(
        args.render_manifest, render.TARGET_ROOT
    )
    attempt = require_exact_attempt_file(manifest_path, RENDER_MANIFEST_NAME)
    require_sha256(
        manifest_sha256, args.render_manifest_sha256, "render_manifest"
    )
    observations, observation_sha256, observation_path = load_json(
        args.review_observations, attempt
    )
    if observation_path.parent != attempt or observation_path.name != OBSERVATION_NAME:
        raise VisualReviewError("observations_path_mismatch")
    require_sha256(
        observation_sha256,
        args.review_observations_sha256,
        "review_observations",
    )
    rendered_cases = validate_manifest(manifest, manifest_sha256, attempt)
    reviewed_cases = validate_observations(
        observations, manifest_sha256, rendered_cases
    )
    recheck_artifacts(attempt, manifest)
    if render.sha256_file(manifest_path, render.MAX_JSON_BYTES) != manifest_sha256:
        raise VisualReviewError("render_manifest_changed_during_finalize")
    if render.sha256_file(observation_path, render.MAX_JSON_BYTES) != observation_sha256:
        raise VisualReviewError("observations_changed_during_finalize")
    output = render.prepare_output_path(args.output_receipt, attempt, RECEIPT_NAME)
    receipt = build_receipt(
        attempt.name,
        manifest_sha256,
        observation_sha256,
        manifest,
        rendered_cases,
        reviewed_cases,
    )
    with output.open("xb") as stream:
        stream.write(render.canonical_json(receipt))
        stream.flush()
    print(
        "P06_TABLE_PENDING_22_VISUAL_REVIEW_FINALIZED "
        "cases=22 direct_feature_stage=oracle_verified p06=in_progress"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
