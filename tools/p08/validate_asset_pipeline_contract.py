#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p08-asset-pipeline-v1.json"
MIGRATION = "protocol/migrations/p08-asset-pipeline-v0-to-v1.md"
POLICY = "implementation/p08/P08-01_ASSET_PIPELINE_POLICY.md"
REPORT = "implementation/p08/P08-01_ASSET_PIPELINE_REPORT.md"
QUALIFICATION = "implementation/p08/evidence/p08-01-asset-pipeline-source-qualification.v1.json"
SOURCES = {
    "WORK_BREAKDOWN_STRUCTURE.csv",
    "README.md",
    "docs/03_document_model/08_drawing_image_chart.md",
    "docs/04_feature_catalog/09_obj.md",
    "docs/04_feature_catalog/contracts/09_obj_contracts.md",
    "docs/09_roadmap/P08_images_shapes_drawing_charts.md",
    "docs/12_implementation_guides/08_validation_oracle_visual_diff.md",
    "implementation/p05/P05_GATE_REPORT.md",
}
IMPLEMENTATION_SHA256 = {
    "crates/hwpx-package/src/lib.rs": "20274fe4624c17d3e39a8fe6409d80ecb18321118402752e174cf8cfcc0c5f9f",
    "crates/hwpx-package/src/asset.rs": "2a7aa557159e6c68fe1ed05111f44a846b9d174a9382c7f42d4295f7cdc72f9e",
    "crates/hwpx-package/tests/asset_pipeline.rs": "1310a39646ff821c9a8549502ef6ce0d8c70b371eef7f89df21ff7e3482720df",
    "crates/hwpx-package/src/patch.rs": "370e0547f12b69042a493d6db67d9d08176ee737abd49ef365d160bd788aee67",
    "crates/hwpx-package/src/graph.rs": "8a3f32bb1e849150139d26eca4ed02c829e940c329b9a6233168c2078da960ba",
    "crates/hwpx-package/src/preservation.rs": "2b07ad95631e9b1d4dd45e7133e96afad0dbd458b48736db0f89d5f6d2986498",
}
MARKERS = {
    "crates/hwpx-package/src/lib.rs": ("mod asset;", "AssetStoreAdapter"),
    "crates/hwpx-package/src/asset.rs": (
        'ASSET_PIPELINE_SCHEMA_VERSION: &str = "hwpx-agent.asset-pipeline/v1"',
        "fn sniff_image",
        "fn parse_png",
        "pub fn build_patch_intents",
        "pub fn load_private_plan_json",
        "finish_non_exhaustive",
    ),
    "crates/hwpx-package/tests/asset_pipeline.rs": (
        "all_five_profile_media_are_structurally_sniffed",
        "malformed_truncated_and_mismatched_media_fail_closed",
        "existing_content_is_reused_without_duplicate_patch_intents",
        "new_asset_part_and_manifest_relationship_apply_atomically_and_reopen",
    ),
    "crates/hwpx-package/src/patch.rs": (
        "AddRelationship",
        "AddPart",
        "PartRelationshipMismatch",
    ),
    "crates/hwpx-package/src/graph.rs": ("raw_sha256", "relationships"),
    "crates/hwpx-package/src/preservation.rs": (
        "OpaqueBinarySignature",
        '"image/png"',
    ),
}
MEDIA_PROFILE = {
    "image/png": "signature_chunks_ihdr_idat_iend_crc_dimensions",
    "image/jpeg": "soi_segments_frame_scan_eoi_dimensions",
    "image/gif": "header_logical_screen_color_tables_extensions_image_blocks_trailer",
    "image/webp": "exact_riff_size_chunks_padding_vp8_or_vp8l_dimensions",
    "image/bmp": "file_and_dib_headers_encoding_pixel_offset_and_uncompressed_extent",
}
WORKFLOW = {
    "plan": "sniff_and_validate_payload_bind_complete_ordered_package_graph_and_select_exact_reuse_or_content_addressed_add",
    "reload": "strict_private_json_raw_digest_plus_full_graph_payload_media_dimension_dedup_path_relationship_and_plan_recompute",
    "lower": "recheck_graph_and_plan_then_emit_zero_reuse_intents_or_exactly_one_part_plus_one_manifest_relationship",
    "transaction": "existing_preserving_patch_engine_rebuilds_graph_and_requires_atomic_relationship_part_closure",
}
LIMITS = {
    "max_asset_bytes": 67_108_864,
    "max_existing_assets": 4_096,
    "max_plan_json_bytes": 16_384,
    "max_dimension_px": 100_000,
    "max_pixels": 1_000_000_000,
}
FAILURE_POLICY = [
    "zero_or_over_ceiling_limits_rejected",
    "empty_oversized_unsupported_truncated_or_structurally_malformed_payload_rejected",
    "declared_media_must_equal_sniffed_media",
    "dimension_and_pixel_limits_checked_before_plan",
    "complete_ordered_package_graph_bound_at_plan_and_lowering",
    "supported_bindata_parts_require_one_consistent_package_document_manifest_relationship",
    "same_digest_and_size_with_different_media_rejected",
    "deterministic_relationship_id_or_part_path_collision_rejected",
    "reuse_emits_no_duplicate_part_or_relationship",
    "new_asset_emits_one_part_and_one_non_spine_manifest_relationship",
    "private_plan_excludes_payload_and_requires_pinned_raw_sha256",
    "missing_duplicate_unknown_relabelled_oversized_or_tampered_plan_json_rejected",
    "payload_relationship_path_and_digest_redacted_from_debug",
    "no_partial_result_or_fallback_after_failure",
]
NOT_CLAIMED = {
    "tiff_svg_or_other_media": False,
    "linked_fetch": False,
    "pixel_decode": False,
    "image_control_lowering": False,
    "actual_hwpx_image": False,
    "actual_hangul": False,
    "save_reopen": False,
    "render": False,
    "direct_automation_differential": False,
    "p08_complete": False,
    "production_ready": False,
    "product_complete": False,
}
GATE = {
    "component": "pass",
    "direct_stage": "unit_passed",
    "asset_target": "not_run",
    "actual_hangul": False,
    "render": False,
    "p08_01": "component_pass",
    "p08": "in_progress",
    "product_complete": False,
}
DIGEST = re.compile(r"^[0-9a-f]{64}$")


class DuplicateKey(ValueError):
    pass


def duplicate_guard(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKey(key)
        result[key] = value
    return result


def file(root: Path, relative: str, maximum: int = 32 * 1024 * 1024) -> Path:
    path = (root / relative).resolve()
    path.relative_to(root.resolve())
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= maximum:
        raise ValueError("invalid bounded file")
    return path


def load(root: Path, relative: str) -> Any:
    return json.loads(file(root, relative).read_bytes(), object_pairs_hook=duplicate_guard)


def canonical_digest(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def raw_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        contract = load(root, CONTRACT)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return result(["contract_json_or_path"], 0, 0, False)
    exact = {
        "schema_version": "hwpx-agent.asset-pipeline-contract/v1",
        "plan_schema_version": "hwpx-agent.asset-pipeline/v1",
        "profile_id": "hwpx-agent.asset-pipeline.hwp-image-v1",
        "task": "P08-01",
        "scope": "bounded_embedded_image_asset_sniff_hash_dedup_relationship_and_atomic_part_planning",
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "source_qualification": QUALIFICATION,
        "migration": MIGRATION,
        "policy": POLICY,
        "report": REPORT,
        "implementation_files": list(MARKERS),
        "media_profile": MEDIA_PROFILE,
        "workflow": WORKFLOW,
        "default_limits": LIMITS,
        "failure_policy": FAILURE_POLICY,
        "not_claimed": NOT_CLAIMED,
        "gate_decision": GATE,
    }
    for key, expected in exact.items():
        if contract.get(key) != expected:
            errors.append(key)
    if set(contract) != {*exact, "source_locks"}:
        errors.append("contract_keys")
    source_count = validate_sources(root, contract.get("source_locks"), errors)
    implementation_count = validate_implementation(root, errors)
    qualification_ok = validate_qualification(root, errors)
    validate_documents(root, errors)
    return result(errors, source_count, implementation_count, qualification_ok)


def validate_sources(root: Path, value: Any, errors: list[str]) -> int:
    if not isinstance(value, list):
        errors.append("source_locks_shape")
        return 0
    declared: dict[str, str] = {}
    for item in value:
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            errors.append("source_lock_shape")
            continue
        relative, expected = item.get("path"), item.get("sha256")
        if (
            not isinstance(relative, str)
            or relative in declared
            or not isinstance(expected, str)
            or not DIGEST.fullmatch(expected)
        ):
            errors.append("source_lock_identity")
            continue
        declared[relative] = expected
        try:
            if canonical_digest(file(root, relative)) != expected:
                errors.append("source_lock_digest")
        except (OSError, ValueError):
            errors.append("source_lock_path")
    if set(declared) != SOURCES:
        errors.append("source_lock_paths_exact")
    return len(declared)


def validate_implementation(root: Path, errors: list[str]) -> int:
    for relative, expected in IMPLEMENTATION_SHA256.items():
        try:
            path = file(root, relative)
            if raw_digest(path) != expected:
                errors.append("implementation_digest")
            text = path.read_text(encoding="utf-8")
            if any(marker not in text for marker in MARKERS[relative]):
                errors.append("implementation_marker")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("implementation_path")
    return len(IMPLEMENTATION_SHA256)


def validate_qualification(root: Path, errors: list[str]) -> bool:
    try:
        value = load(root, QUALIFICATION)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        errors.append("qualification_json_or_path")
        return False
    if set(value) != {
        "schema_version",
        "task",
        "recorded_date",
        "profile_id",
        "implementation_sources",
        "component_execution",
        "target_execution",
        "claims",
    }:
        errors.append("qualification_keys")
    if (
        value.get("schema_version") != "hwpx-agent.asset-pipeline-source-qualification/v1"
        or value.get("task") != "P08-01"
        or value.get("recorded_date") != "2026-09-12"
        or value.get("profile_id") != "hwpx-agent.asset-pipeline.hwp-image-v1"
    ):
        errors.append("qualification_identity")
    if value.get("implementation_sources") != IMPLEMENTATION_SHA256:
        errors.append("qualification_sources")
    if value.get("component_execution") != {
        "state": "pass",
        "rust_tests_passed": 10,
        "media_formats_structurally_validated": 5,
        "strict_private_plan": "pass",
        "complete_graph_drift_binding": "pass",
        "dedup_and_collision_policy": "pass",
        "atomic_part_relationship_patch": "pass",
        "synthetic_package_writer_reopen": "pass",
        "redacted_debug": "pass",
    }:
        errors.append("qualification_component")
    if value.get("target_execution") != {
        "state": "not_run",
        "actual_hwpx_image": None,
        "hangul_open": None,
        "save_reopen": None,
        "render": None,
        "direct_automation_differential": None,
    }:
        errors.append("qualification_target")
    if value.get("claims") != {
        "component_pass": True,
        "finite_embedded_image_profile": True,
        "malformed_media_tests": True,
        "actual_hwpx_image": False,
        "actual_hangul": False,
        "save_reopen": False,
        "render": False,
        "p08_01_complete": True,
        "p08_complete": False,
        "production_ready": False,
        "product_complete": False,
    }:
        errors.append("qualification_claims")
    return not any(error.startswith("qualification_") for error in errors)


def validate_documents(root: Path, errors: list[str]) -> None:
    for relative, markers in {
        MIGRATION: ("There is no stored v0", "MUST NOT be relabeled", "no defaultable fields"),
        POLICY: (
            "component_pass / target_not_run",
            "canonical `image/png`",
            "No actual HWPX fixture",
        ),
        REPORT: ("10/10 PASS", "synthetic HWPX package graph", "actual_hangul=false"),
    }.items():
        try:
            text = file(root, relative).read_text(encoding="utf-8")
            if any(marker not in text for marker in markers):
                errors.append("document_marker")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("document_path")


def result(
    errors: list[str], sources: int, implementation: int, qualification: bool
) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p08-asset-pipeline-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": sources,
        "implementation_files": implementation,
        "source_qualification_verified": qualification,
        "task": "P08-01",
        "direct_stage": "unit_passed" if not unique else "not_proven",
        "asset_target": "not_run",
        "actual_hangul": False,
        "render": False,
        "p08": "in_progress",
        "product_complete": False,
    }


if __name__ == "__main__":
    value = validate()
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))
    if value["state"] != "pass":
        sys.exit(1)
    print(
        "P08_ASSET_PIPELINE_CONTRACT_PASS "
        f"source_locks={value['source_locks']} "
        f"implementation_files={value['implementation_files']} asset_target=not_run"
    )
