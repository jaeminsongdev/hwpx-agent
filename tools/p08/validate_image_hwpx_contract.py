#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p08-image-hwpx-v1.json"
MIGRATION = "protocol/migrations/p08-image-hwpx-v0-to-v1.md"
POLICY = "implementation/p08/P08-02_IMAGE_HWPX_POLICY.md"
REPORT = "implementation/p08/P08-02_IMAGE_HWPX_REPORT.md"
QUALIFICATION = "implementation/p08/evidence/p08-02-image-hwpx-source-qualification.v1.json"
SOURCES = {
    "WORK_BREAKDOWN_STRUCTURE.csv",
    "docs/03_document_model/08_drawing_image_chart.md",
    "docs/04_feature_catalog/09_obj.md",
    "docs/04_feature_catalog/contracts/09_obj_contracts.md",
    "docs/09_roadmap/P08_images_shapes_drawing_charts.md",
    "implementation/p08/P08-01_ASSET_PIPELINE_POLICY.md",
    "implementation/p08/P08-01_ASSET_PIPELINE_REPORT.md",
    "protocol/private/p08-asset-pipeline-v1.json",
    "implementation/p00/source-archive/original/web/KS_X_6101_MachineReadable_Content_20260901.json",
}
IMPLEMENTATION_SHA256 = {
    "crates/hwpx-package/src/lib.rs": "7acbf7cfee7dc9f4eebae1017189356bb955a24ec9ca8c63189933af12fc005f",
    "crates/hwpx-package/src/image_hwpx.rs": "12bc3bc3419163dda1c9d1211757d8b414ef37b165f3e053a4893d0021ae6e49",
    "crates/hwpx-package/src/asset.rs": "2a7aa557159e6c68fe1ed05111f44a846b9d174a9382c7f42d4295f7cdc72f9e",
    "crates/hwpx-package/src/id_index.rs": "5ec151bb7ea37af66a67608f01ab3676eac9a0b23e2d8c3870aa97c1b53adbb0",
    "crates/hwpx-package/src/patch.rs": "370e0547f12b69042a493d6db67d9d08176ee737abd49ef365d160bd788aee67",
    "crates/hwpx-package/src/graph.rs": "8a3f32bb1e849150139d26eca4ed02c829e940c329b9a6233168c2078da960ba",
    "crates/hwpx-package/tests/image_hwpx.rs": "7c1d6aebf69808f892ee031f8c7dfcc71860cd105167af9353f61cc3d1eaa1f3",
}
MARKERS = {
    "crates/hwpx-package/src/lib.rs": ("mod image_hwpx;", "ImageHwpxLowerer"),
    "crates/hwpx-package/src/image_hwpx.rs": (
        'IMAGE_HWPX_SCHEMA_VERSION: &str = "hwpx-agent.image-hwpx/v1"',
        "pub struct ImageHwpxRequestDraft",
        "pub struct ImageHwpxBuilder",
        "pub struct ImageHwpxReader",
        "pub struct ImageHwpxLowerer",
        "IdRuleProfile::hwpml_2011_picture_v5()",
        "UnsupportedLinkMode",
        "finish_non_exhaustive",
    ),
    "crates/hwpx-package/src/asset.rs": ("pub struct AssetStoreAdapter", "build_patch_intents"),
    "crates/hwpx-package/src/id_index.rs": (
        "hwpml_2011_picture_v5",
        "PICTURE_DECLARATION_RULES",
        "PICTURE_REFERENCE_RULES",
        "TargetSelector::PackageDocument",
    ),
    "crates/hwpx-package/src/patch.rs": ("AddPart", "AddRelationship", "InsertSibling"),
    "crates/hwpx-package/src/graph.rs": ("raw_sha256", "package_document"),
    "crates/hwpx-package/tests/image_hwpx.rs": (
        "new_png_is_lowered_atomically_and_full_artifact_reopens",
        "existing_asset_is_reused_without_manifest_or_part_mutation",
        "crop_dpi_alt_text_and_native_shape_are_strictly_read",
        "request_and_lowerer_recheck_source_flow_and_asset_drift",
        "picture_id_profile_closes_manifest_reference_and_rejects_tamper",
    ),
}
OFFICIAL = {
    "local_standard_sections": ["10.9.6.1", "10.9.6.4", "10.9.6.5", "10.9.6.6"],
    "repository": "https://github.com/hancom-io/owpml-model",
    "commit": "1453388472c703a4b299a0834f425cdac16644b9",
    "scope": "static_vocabulary_and_type_model_not_runtime_oracle",
}
ADMITTED = {
    "asset_mode": "embed_only_via_exact_p08_01_asset_plan",
    "anchor": "one_exact_empty_text_element_in_caller_selected_spine_run",
    "placement": "inline_treat_as_character_only",
    "geometry": "positive_absolute_display_extent_plus_positive_independent_dpi",
    "crop": "nonempty_pixel_rectangle_within_exact_asset_dimensions_converted_half_up_to_hwpunit",
    "alternate_text": "nonempty_bounded_xml_safe_shape_comment",
    "identity": "distinct_nonzero_picture_object_instance_and_manifest_resource_domains",
    "preservation": "remove_inserted_picture_and_optional_manifest_item_to_restore_exact_source_bytes",
}
WORKFLOW = {
    "inspect": "bind_complete_ordered_package_section_paragraph_run_object_instance_and_insertion_state",
    "admit": "bind_exact_asset_plan_before_after_flow_ids_geometry_crop_dpi_alt_text_and_reject_links",
    "lower": "reinspect_and_rebuild_asset_then_apply_picture_part_relationship_in_one_preserving_transaction",
    "verify": "strict_picture_readback_manifest_part_digest_closure_exact_byte_restoration_and_writer_reopen",
}
LIMITS = {
    "section_bytes": 33_554_432,
    "elements": 1_000_000,
    "pictures": 65_536,
    "serialized_bytes": 16_777_216,
    "extent_hwpunit": 10_000_000,
    "object_id": 4_294_967_294,
    "instance_id": 4_294_967_294,
    "dpi": 2_400,
    "alt_text_bytes": 4_096,
}
FAILURE_POLICY = [
    "zero_or_over_ceiling_limits_rejected",
    "non_spine_ambiguous_missing_or_nonempty_anchor_rejected",
    "source_package_section_paragraph_run_object_instance_drift_rejected_at_request_and_build",
    "document_flow_drift_rejected_at_request_and_build",
    "asset_binding_must_equal_exact_rebuilt_p08_01_plan",
    "link_and_package_relationship_modes_rejected_without_fetch",
    "zero_colliding_or_out_of_range_object_and_instance_ids_rejected",
    "zero_out_of_bounds_empty_or_rounding_collapsed_crop_and_invalid_dpi_or_extent_rejected",
    "empty_oversized_or_xml_invalid_alternate_text_rejected",
    "new_asset_requires_exact_section_manifest_and_one_added_part_counts",
    "reused_asset_requires_exact_section_only_change_count",
    "picture_manifest_media_target_digest_and_length_must_close",
    "strict_reader_rejects_unknown_missing_reordered_or_tampered_shape_fields",
    "inserted_spans_must_reverse_to_exact_source_bytes_and_unrelated_parts_remain_identical",
    "duplicate_unknown_missing_malformed_or_oversized_json_rejected",
    "paths_text_ids_asset_identity_and_digests_redacted_from_debug",
    "no_partial_result_or_fallback_after_failure",
]
NOT_CLAIMED = {
    "linked_image": False,
    "floating_anchor": False,
    "border_or_effects": False,
    "pixel_decode_or_visual_correctness": False,
    "exact_current_2020_serialization": False,
    "actual_hwpx_image": False,
    "actual_hangul": False,
    "save_reopen": False,
    "render": False,
    "direct_automation_differential": False,
    "p08_02_complete": False,
    "p08_complete": False,
    "production_ready": False,
    "product_complete": False,
}
GATE = {
    "component": "pass",
    "direct_stage": "unit_passed",
    "static_hwpml": "pass",
    "actual_hwpx_target": "not_run",
    "actual_hangul": False,
    "render": False,
    "p08_02": "static_component_pass_target_not_run_task_incomplete",
    "p08_02_complete": False,
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
        "schema_version": "hwpx-agent.image-hwpx-contract/v1",
        "request_schema_version": "hwpx-agent.image-hwpx/v1",
        "profile_id": "hwpx-agent.image-hwpx.hwpml-2011-static-embed/v1",
        "task": "P08-02",
        "scope": "bounded_embed_only_inline_picture_static_hwpml_lowering_with_exact_asset_source_geometry_anchor_and_flow_binding",
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "source_qualification": QUALIFICATION,
        "migration": MIGRATION,
        "policy": POLICY,
        "report": REPORT,
        "implementation_files": list(MARKERS),
        "official_model_source": OFFICIAL,
        "admitted_profile": ADMITTED,
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
        "schema_version", "task", "recorded_date", "profile_id", "official_sources",
        "implementation_sources", "component_execution", "target_execution", "claims",
    }:
        errors.append("qualification_keys")
    if (
        value.get("schema_version") != "hwpx-agent.image-hwpx-source-qualification/v1"
        or value.get("task") != "P08-02"
        or value.get("recorded_date") != "2026-09-12"
        or value.get("profile_id") != "hwpx-agent.image-hwpx.hwpml-2011-static-embed/v1"
    ):
        errors.append("qualification_identity")
    if value.get("implementation_sources") != IMPLEMENTATION_SHA256:
        errors.append("qualification_sources")
    official = value.get("official_sources")
    if not isinstance(official, dict) or official.get("evidence_scope") != "static_vocabulary_and_type_model_only" or official.get("hancom_owpml_commit") != OFFICIAL["commit"]:
        errors.append("qualification_official_sources")
    if value.get("component_execution") != {
        "state": "pass", "rust_tests_passed": 9, "embed_only_request": "pass",
        "complete_source_asset_and_flow_binding": "pass", "static_hwpml_picture_readback": "pass",
        "picture_manifest_id_closure": "pass", "atomic_new_and_reuse_lowering": "pass",
        "synthetic_package_writer_reopen": "pass", "crop_dpi_alt_text": "pass",
        "tamper_and_drift_rejection": "pass", "bounded_json_and_redacted_debug": "pass",
    }:
        errors.append("qualification_component")
    if value.get("target_execution") != {
        "state": "not_run", "actual_hwpx_image": None, "hangul_open": None,
        "save_reopen": None, "render": None, "direct_automation_differential": None,
    }:
        errors.append("qualification_target")
    if value.get("claims") != {
        "static_component_pass": True, "embedded_image_lowering": True, "linked_image": False,
        "actual_hwpx_image": False, "actual_hangul": False, "save_reopen": False,
        "render": False, "p08_02_complete": False, "p08_complete": False,
        "production_ready": False, "product_complete": False,
    }:
        errors.append("qualification_claims")
    return not any(error.startswith("qualification_") for error in errors)


def validate_documents(root: Path, errors: list[str]) -> None:
    expected = {
        MIGRATION: ("There is no stored v0", "MUST NOT be relabeled", "no defaultable fields"),
        POLICY: ("static_component_pass / target_not_run / task_incomplete", "Only `embed` is admitted", "p08_02_complete=false"),
        REPORT: ("9/9 PASS", "synthetic component fixtures", "Linked images are not"),
    }
    for relative, markers in expected.items():
        try:
            text = file(root, relative).read_text(encoding="utf-8")
            if any(marker not in text for marker in markers):
                errors.append("document_marker")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("document_path")


def result(errors: list[str], sources: int, implementation: int, qualification: bool) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p08-image-hwpx-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": sources,
        "implementation_files": implementation,
        "source_qualification_verified": qualification,
        "task": "P08-02",
        "direct_stage": "unit_passed" if not unique else "not_proven",
        "static_hwpml": "pass" if not unique else "not_proven",
        "actual_hwpx_target": "not_run",
        "actual_hangul": False,
        "render": False,
        "p08_02_complete": False,
        "p08": "in_progress",
        "product_complete": False,
    }


if __name__ == "__main__":
    value = validate()
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))
    if value["state"] != "pass":
        sys.exit(1)
    print(
        "P08_IMAGE_HWPX_CONTRACT_PASS "
        f"source_locks={value['source_locks']} implementation_files={value['implementation_files']} "
        "actual_hwpx_target=not_run p08_02_complete=false"
    )
