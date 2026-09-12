#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p08-object-remainder-v1.json"
MIGRATION = "protocol/migrations/p08-object-remainder-v0-to-v1.md"
POLICY = "implementation/p08/P08-10_OBJECT_REMAINDER_POLICY.md"
REPORT = "implementation/p08/P08-10_OBJECT_REMAINDER_REPORT.md"
QUALIFICATION = "implementation/p08/evidence/p08-10-object-remainder-source-qualification.v1.json"
BASE_COMMIT = "9c06106ee26d84ebb4a0c877b1d4cddec8b08c31"

SOURCE_SHA256 = {
    "docs/04_feature_catalog/09_obj.md": "e3c4c71e8d8c608c8e403404c1cf7767bbd91bdfd93dbcdb07f2e91e90c785e8",
    "docs/04_feature_catalog/contracts/09_obj_contracts.md": "e1274922109762ab3de1b7118e954510f37d1f0686b9b0c5fc1152936983bec2",
    "docs/09_roadmap/P08_images_shapes_drawing_charts.md": "f07ee05eb72481f86b9499fbc9aa3f5e8191f42f875b6e0bd1a88fc7c9a62fe3",
    "implementation/p08/P08-03_OBJECT_GEOMETRY_POLICY.md": "55797042198bd08c99fae4a5eafdbe55323a80a80d91c04da69861734e438aab",
    "implementation/p08/P08-04_BASIC_SHAPE_POLICY.md": "8cacd71f5debc14508e95b2645b91dfe4b625ccc2f71fcf105bbd5932b8ab1ad",
    "implementation/p08/P08-05_OBJECT_APPEARANCE_POLICY.md": "1d05d280c00b8e61f216ed44fcfe4ed7ea4fcbb4ba86ac72be7fcf806b3da68a",
}
IMPLEMENTATION_SHA256 = {
    "crates/domain-ir/src/lib.rs": "223c597e4c067566417237a852bed55d6f3893ac36418256c7943c0163724433",
    "crates/domain-ir/src/basic_shape.rs": "6eebfbe838b9f76530a2f3cddc414d146df2f97384305232db8f3e7b02acb3c6",
    "crates/domain-ir/src/object_properties.rs": "f0bed7df4dc15092f764edd18f10351de2420b9f90dbd0e3909cdda6c3415695",
    "crates/domain-ir/src/shape_points.rs": "e64750c645c00fcd4c40543dde7c8f6736e699e0b7781044458fc2b2f60909af",
    "crates/domain-ir/src/object_special.rs": "d608b15109c0a3168fec0b8b0d70b0709759a6e533e44e5fd87ae65ccddbcabc",
    "crates/domain-ir/tests/basic_shape.rs": "40a582bcbae8939a46ce1cc661aaa46174e04bec814ced94b1aebb8775ec55a1",
    "crates/domain-ir/tests/object_properties.rs": "256bb9d3b6f05215b31e0a8c6cb8af9bf94f6a9da19d1c8fb660edc44b0120ac",
    "crates/domain-ir/tests/shape_points.rs": "415465edd2a14b60264711db2abdee2b48a7ea260fe16fc4b164a40388b16c0e",
    "crates/domain-ir/tests/object_special.rs": "49a7d3ac95312701d9ca4951c83127280682f8b9f54a92cbbec555b6b14d45bd",
}
CAPABILITIES = {
    "OBJ-003": "obj.drawing_gallery",
    "OBJ-012": "obj.form_object_insert",
    "OBJ-013": "obj.caption_insert",
    "OBJ-014": "obj.paragraph_band_object",
    "OBJ-019": "obj.margin_caption",
    "OBJ-025": "obj.textbox_properties",
    "OBJ-030": "obj.image_properties",
    "OBJ-042": "obj.freeform",
    "OBJ-043": "obj.shape_edit_points",
    "OBJ-044": "obj.aspect_lock",
    "OBJ-045": "obj.object_protect",
    "OBJ-046": "obj.printable",
    "OBJ-047": "obj.alt_text",
    "OBJ-048": "obj.object_hyperlink",
}
MODELS = {
    "hwpx-agent.object-properties/v1": [
        "OBJ-019", "OBJ-025", "OBJ-030", "OBJ-044", "OBJ-045", "OBJ-046", "OBJ-047", "OBJ-048",
    ],
    "hwpx-agent.basic-shape/v1": ["OBJ-042"],
    "hwpx-agent.shape-points/v1": ["OBJ-043"],
    "hwpx-agent.object-special/v1": ["OBJ-003", "OBJ-012", "OBJ-013", "OBJ-014"],
}
STATE_BINDING = {
    "object_properties": "identity_kind_geometry_appearance_payload_resource_embedded_content_and_opaque_properties",
    "shape_points": "identity_complete_freeform_topology_geometry_appearance_properties_resources_embedded_content_and_opaque_state",
    "special_objects": "document_order_all_object_caption_paragraph_resource_relationship_inventories_and_document_state_digests",
    "request_and_build": "exact_source_state_grid_independent_document_flow_rechecked_and_plan_binding_sealed",
    "preservation": "only_the_named_transition_may_change_state",
}
FAILURE_POLICY = [
    "zero_or_over_ceiling_limits_rejected",
    "duplicate_unknown_missing_malformed_or_oversized_json_rejected",
    "invalid_complete_state_or_digest_rejected",
    "object_kind_and_operation_mismatch_rejected",
    "freeform_topology_kind_mismatch_or_degeneracy_rejected",
    "no_op_transition_rejected",
    "unsafe_or_local_file_hyperlink_rejected",
    "active_form_content_rejected",
    "missing_paragraph_or_caption_target_rejected",
    "object_caption_resource_and_relationship_collisions_rejected",
    "source_state_and_document_flow_drift_rejected_at_request_and_build",
    "plan_binding_tamper_rejected",
    "unrelated_identity_payload_property_formula_cache_resource_and_opaque_state_change_rejected",
    "identifiers_paths_text_links_resources_and_digests_redacted_from_debug",
    "no_partial_result_or_fallback_after_failure",
]
CLAIMS = {
    "unit_model_implemented": True,
    "fourteen_capabilities_unit_passed": True,
    "complete_bound_state_preserved": True,
    "request_and_build_drift_rejected": True,
    "direct_hwpx": False,
    "actual_hwpx": False,
    "actual_hangul": False,
    "save_reopen": False,
    "property_readback": False,
    "render": False,
    "automation": False,
    "differential": False,
    "p08_10_green": False,
    "p08_complete": False,
    "production_ready": False,
    "product_complete": False,
}
MARKERS = {
    "crates/domain-ir/src/lib.rs": (
        "mod object_properties;", "mod object_special;", "mod shape_points;",
        "ObjectPropertiesBuilder", "ObjectSpecialBuilder", "ShapePointsBuilder",
    ),
    "crates/domain-ir/src/basic_shape.rs": (
        'Self::Freeform { .. } => "obj.freeform"',
        'Self::TextBox { .. } => "obj.textbox_insert"',
    ),
    "crates/domain-ir/src/object_properties.rs": (
        'OBJECT_PROPERTIES_SCHEMA_VERSION: &str = "hwpx-agent.object-properties/v1"',
        "pub enum ObjectPropertiesOperation", "pub struct ObjectPropertiesBuilder",
        "fn validate_state(", "fn reject_duplicate_json_keys(", "<redacted>",
    ),
    "crates/domain-ir/src/shape_points.rs": (
        'SHAPE_POINTS_SCHEMA_VERSION: &str = "hwpx-agent.shape-points/v1"',
        "pub struct ShapePointsBuilder", "fn validate_freeform(",
        "fn reject_duplicate_json_keys(", "<redacted>",
    ),
    "crates/domain-ir/src/object_special.rs": (
        'OBJECT_SPECIAL_SCHEMA_VERSION: &str = "hwpx-agent.object-special/v1"',
        "pub enum ObjectSpecialOperation", "pub struct ObjectSpecialBuilder",
        "resource_inventory_sha256_for", "active", "fn reject_duplicate_json_keys(", "<redacted>",
    ),
    "crates/domain-ir/tests/basic_shape.rs": ("plans_and_builds_all_five_semantic_shape_families",),
    "crates/domain-ir/tests/object_properties.rs": (
        "plans_and_builds_all_six_common_property_capabilities",
        "every_transition_preserves_identity_payload_resources_and_opaque_state",
        "request_and_build_both_reject_state_and_flow_drift",
    ),
    "crates/domain-ir/tests/shape_points.rs": (
        "freeform_insert_has_its_exact_capability_id",
        "edits_polygon_and_curve_points_without_touching_other_state",
        "request_and_build_recheck_exact_source_state_and_flow",
    ),
    "crates/domain-ir/tests/object_special.rs": (
        "plans_and_builds_all_four_exact_special_capabilities",
        "insertion_preserves_document_state_and_updates_only_exact_inventories",
        "request_and_build_recheck_exact_state_and_flow",
    ),
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


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        contract = load(root, CONTRACT)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return result(["contract_json_or_path"], 0, 0, False)

    expected_root = {
        "schema_version", "task", "scope", "source_lock_canonicalization",
        "source_qualification", "migration", "policy", "report", "source_locks",
        "capability_features", "models", "implementation_files", "state_binding",
        "failure_policy", "evidence_boundary", "gate_decision",
    }
    if not isinstance(contract, dict) or set(contract) != expected_root:
        errors.append("contract_shape")
    if contract.get("schema_version") != "hwpx-agent.object-remainder-contract/v1":
        errors.append("schema_version")
    if contract.get("task") != "P08-10" or contract.get("scope") != (
        "fourteen_previously_cataloged_p08_owned_object_capabilities_complete_typed_unit_models"
    ):
        errors.append("identity")
    if contract.get("source_lock_canonicalization") != "utf8_text_crlf_to_lf_sha256":
        errors.append("source_lock_mode")
    if (contract.get("source_qualification"), contract.get("migration"), contract.get("policy"), contract.get("report")) != (
        QUALIFICATION, MIGRATION, POLICY, REPORT,
    ):
        errors.append("document_paths")
    if contract.get("capability_features") != CAPABILITIES:
        errors.append("capability_mapping")
    if contract.get("models") != MODELS:
        errors.append("model_mapping")
    if contract.get("implementation_files") != list(IMPLEMENTATION_SHA256):
        errors.append("implementation_files")
    if contract.get("state_binding") != STATE_BINDING:
        errors.append("state_binding")
    if contract.get("failure_policy") != FAILURE_POLICY:
        errors.append("failure_policy")
    expected_boundary = {**CLAIMS, "focused_rust_tests": "27/27 PASS", "direct_stage": "unit_passed"}
    if contract.get("evidence_boundary") != expected_boundary:
        errors.append("evidence_boundary")
    if contract.get("gate_decision") != {
        "component": "pass",
        "direct_stage": "unit_passed",
        "actual_target": "not_run",
        "p08_10": "unit_models_passed_direct_hwpx_and_target_evidence_not_run",
        "p08_10_green": False,
        "p08": "in_progress",
        "product_complete": False,
    }:
        errors.append("gate_decision")

    source_count = validate_sources(root, contract.get("source_locks"), errors)
    implementation_count = validate_implementation(root, errors)
    qualification_ok = validate_qualification(root, errors)
    validate_documents(root, errors)
    return result(errors, source_count, implementation_count, qualification_ok)


def validate_sources(root: Path, value: Any, errors: list[str]) -> int:
    if not isinstance(value, list):
        errors.append("source_lock_shape")
        return 0
    declared: dict[str, str] = {}
    for item in value:
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            errors.append("source_lock_shape")
            continue
        relative, expected = item.get("path"), item.get("sha256")
        if not isinstance(relative, str) or relative in declared or not isinstance(expected, str) or not DIGEST.fullmatch(expected):
            errors.append("source_lock_identity")
            continue
        declared[relative] = expected
        try:
            if canonical_digest(file(root, relative)) != expected:
                errors.append("source_lock_digest")
        except (OSError, ValueError):
            errors.append("source_lock_path")
    if declared != SOURCE_SHA256:
        errors.append("source_lock_paths_exact")
    return len(declared)


def validate_implementation(root: Path, errors: list[str]) -> int:
    for relative, expected in IMPLEMENTATION_SHA256.items():
        try:
            path = file(root, relative)
            if canonical_digest(path) != expected:
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
    if not isinstance(value, dict) or set(value) != {
        "schema_version", "task", "base_commit", "scope", "source_sha256",
        "implementation_sha256", "tests", "claims",
    }:
        errors.append("qualification_shape")
    if value.get("schema_version") != "hwpx-agent.p08-object-remainder-source-qualification/v1" or value.get("task") != "P08-10":
        errors.append("qualification_identity")
    if value.get("base_commit") != BASE_COMMIT or value.get("scope") != "fourteen_p08_owned_capability_unit_models_only":
        errors.append("qualification_scope")
    if value.get("source_sha256") != SOURCE_SHA256:
        errors.append("qualification_sources")
    if value.get("implementation_sha256") != IMPLEMENTATION_SHA256:
        errors.append("qualification_implementation")
    if value.get("tests") != {
        "basic_shape_regression": "6/6 PASS",
        "object_properties": "8/8 PASS",
        "shape_points": "6/6 PASS",
        "object_special": "7/7 PASS",
        "test_kind": "typed_component_state",
        "network_used": False,
        "licensed_application_used": False,
    }:
        errors.append("qualification_tests")
    if value.get("claims") != CLAIMS:
        errors.append("qualification_claims")
    return not any(error.startswith("qualification_") for error in errors)


def validate_documents(root: Path, errors: list[str]) -> None:
    expected = {
        MIGRATION: ("There is no accepted v0", "fail closed", "no migration switch"),
        POLICY: ("fourteen_capabilities_unit_passed=true", "direct_hwpx=false", "Reasoning level: max"),
        REPORT: ("27/27 PASS", "cataloged=5", "actual_hangul=false"),
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
        "schema_version": "hwpx-agent.p08-object-remainder-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": sources,
        "implementation_files": implementation,
        "source_qualification_verified": qualification,
        "task": "P08-10",
        "capabilities": 14,
        "direct_stage": "unit_passed" if not unique else "not_proven",
        "direct_hwpx": "not_run",
        "actual_hwpx": "not_run",
        "actual_hangul": "not_run",
        "render": "not_run",
        "automation": "not_run",
        "differential": "not_run",
        "p08_10_green": False,
        "p08": "in_progress",
        "product_complete": False,
    }


if __name__ == "__main__":
    value = validate()
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    sys.exit(0 if value["state"] == "pass" else 1)
