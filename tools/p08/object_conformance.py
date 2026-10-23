from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MATRIX = Path("implementation/p08/evidence/conformance/p08-object-conformance.current-2020.v1.json")
DIRECT = Path("implementation/p08/p08-09-current-2020-direct-evidence.json")
AUTOMATION = Path("implementation/p08/p08-09-current-2020-automation-projection.json")
THRESHOLDS = Path("implementation/p08/p08-09-threshold-policy.v1.json")
CATALOG = Path("specs/feature-coverage-matrix.json")
CONTRACTS = Path("specs/capability-contracts.generated.json")

MAX_JSON_BYTES = 16 * 1024 * 1024
STAGES = ("cataloged", "unit_passed", "integration_passed", "oracle_verified")
BACKENDS = ("unbound", "component_only", "direct_hwpx", "preserve_only")
AUTOMATION_STATES = (
    "verified_current_target",
    "candidate_unverified",
    "denied_by_policy",
    "unavailable_with_reason",
)

EXPECTED_DIRECT_PROFILES = {
    "image-full-package-v1": {
        "features": ("OBJ-002",),
        "backend": "direct_hwpx",
        "stage": "integration_passed",
        "validations": ("resource_integrity", "semantic_reopen"),
    },
    "geometry-section-v1": {
        "features": ("OBJ-015", "OBJ-016", "OBJ-017", "OBJ-018", "OBJ-032", "OBJ-033"),
        "backend": "direct_hwpx",
        "stage": "integration_passed",
        "validations": ("schema", "semantic_reopen"),
    },
    "basic-shape-package-v1": {
        "features": ("OBJ-001", "OBJ-007", "OBJ-042"),
        "backend": "direct_hwpx",
        "stage": "integration_passed",
        "validations": ("resource_integrity", "semantic_reopen"),
    },
    "object-protect-section-v1": {
        "features": ("OBJ-045",),
        "backend": "direct_hwpx",
        "stage": "integration_passed",
        "validations": ("schema", "semantic_reopen"),
    },
    "appearance-section-v1": {
        "features": ("OBJ-020", "OBJ-021", "OBJ-022", "OBJ-023", "OBJ-024", "OBJ-026", "OBJ-027", "OBJ-028", "OBJ-029", "OBJ-034", "OBJ-035"),
        "backend": "direct_hwpx",
        "stage": "integration_passed",
        "validations": ("schema", "semantic_reopen"),
    },
    "composition-section-v1": {
        "features": ("OBJ-036", "OBJ-037", "OBJ-038", "OBJ-039", "OBJ-040", "OBJ-041"),
        "backend": "direct_hwpx",
        "stage": "integration_passed",
        "validations": ("schema", "semantic_reopen"),
    },
    "chart-component-v1": {
        "features": ("OBJ-006", "OBJ-049", "OBJ-050", "OBJ-051", "OBJ-052", "OBJ-053", "OBJ-054", "OBJ-055", "OBJ-056"),
        "backend": "component_only",
        "stage": "unit_passed",
        "validations": (),
    },
    "drawing-canvas-section-v1": {
        "features": ("OBJ-010", "OBJ-031"),
        "backend": "direct_hwpx",
        "stage": "integration_passed",
        "validations": ("schema", "semantic_reopen"),
    },
    "object-common-properties-section-v1": {
        "features": ("OBJ-019", "OBJ-030", "OBJ-047"),
        "backend": "direct_hwpx",
        "stage": "integration_passed",
        "validations": ("schema", "semantic_reopen"),
    },
    "object-printable-security-v1": {
        "features": ("OBJ-046",),
        "backend": "direct_hwpx",
        "stage": "integration_passed",
        "validations": ("schema", "semantic_reopen"),
    },
    "object-properties-component-v1": {
        "features": ("OBJ-044",),
        "backend": "component_only",
        "stage": "unit_passed",
        "validations": ("schema",),
    },
    "object-hyperlink-target-route-v1": {
        "features": ("OBJ-048",),
        "backend": "direct_hwpx",
        "stage": "integration_passed",
        "validations": ("schema", "semantic_reopen"),
    },
    "caption-insert-section-v1": {
        "features": ("OBJ-013",),
        "backend": "direct_hwpx",
        "stage": "integration_passed",
        "validations": ("schema", "semantic_reopen"),
    },
    "form-insert-section-v1": {
        "features": ("OBJ-012",),
        "backend": "direct_hwpx",
        "stage": "integration_passed",
        "validations": ("schema", "semantic_reopen"),
    },
    "textbox-properties-section-v1": {
        "features": ("OBJ-025",),
        "backend": "direct_hwpx",
        "stage": "integration_passed",
        "validations": ("schema", "semantic_reopen"),
    },
    "shape-points-section-v1": {
        "features": ("OBJ-043",),
        "backend": "direct_hwpx",
        "stage": "integration_passed",
        "validations": ("schema", "semantic_reopen"),
    },
    "special-object-target-v1": {
        "features": ("OBJ-003", "OBJ-014"),
        "backend": "direct_hwpx",
        "stage": "integration_passed",
        "validations": ("schema", "semantic_reopen"),
    },
    "ole-passive-preservation-v1": {
        "features": ("OBJ-011", "OBJ-057"),
        "backend": "preserve_only",
        "stage": "integration_passed",
        "validations": ("binary_preservation", "security_scan"),
    },
}

EXPECTED_AUTOMATION_VERIFIED = {
    "OBJ-001", "OBJ-002", "OBJ-007", "OBJ-010", "OBJ-013", "OBJ-014",
    "OBJ-015", "OBJ-016", "OBJ-017", "OBJ-018", "OBJ-019", "OBJ-020",
    "OBJ-021", "OBJ-022", "OBJ-023", "OBJ-024", "OBJ-026", "OBJ-027",
    "OBJ-028", "OBJ-029", "OBJ-030", "OBJ-031", "OBJ-032", "OBJ-033",
    "OBJ-034", "OBJ-035", "OBJ-036", "OBJ-037", "OBJ-038", "OBJ-039",
    "OBJ-041", "OBJ-042", "OBJ-045", "OBJ-047",
}
EXPECTED_P08_AUTOMATION_UNAVAILABLE = {
    "OBJ-003": "parameterized_gallery_action_returned_false_without_effect",
    "OBJ-012": "form_insert_default_parameter_set_unavailable_on_exact_target",
    "OBJ-025": "selected_textbox_property_route_produced_no_semantic_effect",
    "OBJ-040": "eligible_programmatic_multi_shape_selection_unavailable_on_2020",
    "OBJ-043": "known_modal_edit_points_route_produced_no_semantic_effect",
    "OBJ-044": "exact_target_capability_unavailable",
    "OBJ-046": "no_exact_per_object_printable_automation_surface",
    "OBJ-048": "complete_hyperlink_parameter_route_remained_modal_and_timed_out",
}
EXPECTED_AUTOMATION_CANDIDATES = {
    "OBJ-006", "OBJ-049", "OBJ-050", "OBJ-051", "OBJ-052",
    "OBJ-053", "OBJ-054", "OBJ-055", "OBJ-056",
}
EXPECTED_POLICY_DENIALS = {"OBJ-011", "OBJ-057"}
EXPECTED_UNBOUND_UNAVAILABLE = {"OBJ-004", "OBJ-005", "OBJ-008", "OBJ-009", "OBJ-058"}

TARGET = {
    "profile_id": "hancom-hangul-2020-secondary",
    "product": "Hancom Hangul 2020",
    "build": "11.0.0.9136",
    "locale": "ko-KR",
    "architecture": "x86",
    "scope": "current_pc_personal_local_development",
}
TARGET_QUALIFICATION = Path(
    "implementation/p08/evidence/"
    "p08-20-object-target-qualification.current-2020.v1.json"
)
ASPECT_LOCK_NEGATIVE_QUALIFICATION = Path(
    "implementation/p08/evidence/"
    "p08-21-aspect-lock-negative-qualification.current-2020.v1.json"
)
TARGET_VALIDATIONS = (
    "resource_integrity",
    "semantic_reopen",
    "hancom_open",
    "object_bounds",
    "render_diff",
)
TARGET_FIXTURES = ("boundary", "happy_path", "negative", "preservation", "target_build")


class ConformanceError(ValueError):
    pass


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ConformanceError(f"duplicate_json_key:{key}")
        result[key] = value
    return result


def load_json(path: Path, *, root: Path = ROOT) -> Any:
    absolute = root / path
    data = absolute.read_bytes()
    if not data or len(data) > MAX_JSON_BYTES:
        raise ConformanceError(f"json_size:{path.as_posix()}")
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ConformanceError(f"invalid_json:{path.as_posix()}") from error


def normalized_sha256(path: Path, *, root: Path = ROOT) -> str:
    absolute = root / path
    if not absolute.is_file():
        raise ConformanceError(f"missing_evidence:{path.as_posix()}")
    data = absolute.read_bytes()
    try:
        data = data.decode("utf-8").replace("\r\n", "\n").encode("utf-8")
    except UnicodeDecodeError:
        pass
    return hashlib.sha256(data).hexdigest()


def _require_exact_keys(value: dict[str, Any], keys: set[str], context: str) -> None:
    if set(value) != keys:
        raise ConformanceError(f"shape_drift:{context}")


def load_feature_rows(*, root: Path = ROOT) -> list[dict[str, Any]]:
    catalog = load_json(CATALOG, root=root)
    contracts_document = load_json(CONTRACTS, root=root)
    if not isinstance(catalog, list) or not isinstance(contracts_document, dict):
        raise ConformanceError("catalog_shape")
    contracts = contracts_document.get("contracts")
    if not isinstance(contracts, list):
        raise ConformanceError("contract_catalog_shape")
    rows = [row for row in catalog if isinstance(row, dict) and str(row.get("feature_id", "")).startswith("OBJ-")]
    expected_ids = [f"OBJ-{number:03d}" for number in range(1, 59)]
    if [row.get("feature_id") for row in rows] != expected_ids:
        raise ConformanceError("feature_id_sequence")
    contracts_by_id = {row.get("feature_id"): row for row in contracts if isinstance(row, dict) and str(row.get("feature_id", "")).startswith("OBJ-")}
    if set(contracts_by_id) != set(expected_ids):
        raise ConformanceError("contract_feature_set")
    for row in rows:
        contract = contracts_by_id[row["feature_id"]]
        for field in (
            "feature_id",
            "capability_id",
            "preferred_backend",
            "fallback_backend",
            "support_level",
            "phase",
            "validation",
            "permission",
        ):
            if row.get(field) != contract.get(field):
                raise ConformanceError(f"catalog_contract_drift:{row['feature_id']}:{field}")
        release_gate = contract.get("release_gate")
        if not isinstance(release_gate, dict) or release_gate.get("phase") != row.get("phase"):
            raise ConformanceError(f"release_gate_drift:{row['feature_id']}")
        fixtures = release_gate.get("required_fixture_classes")
        if not isinstance(fixtures, list) or not fixtures or any(not isinstance(item, str) for item in fixtures):
            raise ConformanceError(f"fixture_shape:{row['feature_id']}")
        row["required_fixture_classes"] = fixtures
    return rows


def _load_direct_profiles(document: dict[str, Any], feature_ids: set[str], root: Path) -> dict[str, dict[str, Any]]:
    _require_exact_keys(
        document,
        {"schema_version", "target_profile_id", "target_qualification_file", "profiles"},
        "direct",
    )
    if document["schema_version"] != "hwpx-agent.p08-object-direct-evidence/v1" or document["target_profile_id"] != TARGET["profile_id"]:
        raise ConformanceError("direct_identity")
    if document["target_qualification_file"] != TARGET_QUALIFICATION.as_posix():
        raise ConformanceError("direct_target_qualification")
    target_qualification_evidence = {
        "path": TARGET_QUALIFICATION.as_posix(),
        "sha256": normalized_sha256(TARGET_QUALIFICATION, root=root),
    }
    profiles = document["profiles"]
    if not isinstance(profiles, list) or not profiles:
        raise ConformanceError("direct_profiles")
    by_feature: dict[str, dict[str, Any]] = {}
    profile_ids: set[str] = set()
    keys = {
        "profile_id",
        "feature_ids",
        "backend",
        "stage",
        "validations_passed",
        "fixture_classes_passed",
        "negative_passed",
        "rollback_or_retry_passed",
        "evidence_files",
    }
    for profile in profiles:
        if not isinstance(profile, dict):
            raise ConformanceError("direct_profile_shape")
        _require_exact_keys(profile, keys, "direct_profile")
        profile_id = profile["profile_id"]
        if not isinstance(profile_id, str) or not profile_id or profile_id in profile_ids:
            raise ConformanceError("direct_profile_id")
        profile_ids.add(profile_id)
        expected = EXPECTED_DIRECT_PROFILES.get(profile_id)
        if expected is None:
            raise ConformanceError(f"unexpected_direct_profile:{profile_id}")
        if profile["backend"] not in BACKENDS[1:] or profile["stage"] not in STAGES[1:]:
            raise ConformanceError(f"direct_stage:{profile_id}")
        for field in ("feature_ids", "validations_passed", "fixture_classes_passed", "evidence_files"):
            values = profile[field]
            if not isinstance(values, list) or len(values) != len(set(values)) or any(not isinstance(item, str) or not item for item in values):
                raise ConformanceError(f"direct_list:{profile_id}:{field}")
        if not profile["feature_ids"] or not profile["evidence_files"]:
            raise ConformanceError(f"direct_empty:{profile_id}")
        if (
            profile_id == "object-properties-component-v1"
            and ASPECT_LOCK_NEGATIVE_QUALIFICATION.as_posix() not in profile["evidence_files"]
        ):
            raise ConformanceError("obj044_negative_qualification_missing")
        if not isinstance(profile["negative_passed"], bool) or not isinstance(profile["rollback_or_retry_passed"], bool):
            raise ConformanceError(f"direct_boolean:{profile_id}")
        is_target_oracle = expected["backend"] == "direct_hwpx"
        expected_stage = "oracle_verified" if is_target_oracle else expected["stage"]
        expected_validations = TARGET_VALIDATIONS if is_target_oracle else expected["validations"]
        expected_fixtures = (
            (*TARGET_FIXTURES, "security")
            if profile_id == "object-printable-security-v1"
            else TARGET_FIXTURES
            if is_target_oracle
            else ("boundary", "happy_path", "negative", "preservation", "security")
            if expected["backend"] == "preserve_only"
            else ("boundary", "happy_path", "negative", "preservation")
        )
        if (
            tuple(profile["feature_ids"]) != expected["features"]
            or profile["backend"] != expected["backend"]
            or profile["stage"] != expected_stage
            or tuple(profile["validations_passed"]) != expected_validations
            or tuple(profile["fixture_classes_passed"]) != expected_fixtures
            or profile["negative_passed"] is not True
            or profile["rollback_or_retry_passed"] is not is_target_oracle
        ):
            raise ConformanceError(f"direct_profile_semantic_drift:{profile_id}")
        evidence = []
        for value in profile["evidence_files"]:
            path = Path(value)
            if path.is_absolute() or ".." in path.parts:
                raise ConformanceError(f"private_evidence_path:{profile_id}")
            evidence.append({"path": path.as_posix(), "sha256": normalized_sha256(path, root=root)})
        if is_target_oracle:
            evidence.append(target_qualification_evidence)
        compiled = {**profile, "evidence_files": evidence}
        for feature_id in profile["feature_ids"]:
            if feature_id not in feature_ids or feature_id in by_feature:
                raise ConformanceError(f"direct_feature_collision:{feature_id}")
            by_feature[feature_id] = compiled
    if profile_ids != set(EXPECTED_DIRECT_PROFILES):
        raise ConformanceError("direct_profile_set")
    return by_feature


def _load_automation(document: dict[str, Any], feature_ids: set[str]) -> dict[str, dict[str, Any]]:
    keys = {
        "schema_version",
        "target_profile_id",
        "verified_current_target",
        "unavailable_with_reason",
        "candidate_unverified",
        "denied_by_policy",
        "unbound_unavailable",
        "differential_exact_match",
        "differential_not_applicable_fallback_unavailable",
        "differential_not_applicable_target_unavailable",
        "runtime_support_state",
        "routing_enabled_count",
        "actual_target_profile",
        "qualification_receipt_sha256",
        "qualified_overlay_sha256",
        "raw_action_identifiers",
        "raw_parameter_identifiers",
    }
    _require_exact_keys(document, keys, "automation")
    if document["schema_version"] != "hwpx-agent.p08-object-automation-projection/v2" or document["target_profile_id"] != TARGET["profile_id"]:
        raise ConformanceError("automation_identity")
    if document["runtime_support_state"] != "partially_verified_current_target" \
            or document["routing_enabled_count"] != 34:
        raise ConformanceError("automation_runtime_state")
    if document["actual_target_profile"] is not True or document["raw_action_identifiers"] is not False or document["raw_parameter_identifiers"] is not False:
        raise ConformanceError("automation_private_or_actual_claim")
    for field in ("qualification_receipt_sha256", "qualified_overlay_sha256"):
        value = document[field]
        if not isinstance(value, str) or len(value) != 64:
            raise ConformanceError("automation_qualification_digest")
    verified = document["verified_current_target"]
    unavailable = document["unavailable_with_reason"]
    candidate = document["candidate_unverified"]
    denied = document["denied_by_policy"]
    unbound = document["unbound_unavailable"]
    exact = document["differential_exact_match"]
    fallback_na = document["differential_not_applicable_fallback_unavailable"]
    target_na = document["differential_not_applicable_target_unavailable"]
    lists = (verified, candidate, denied, unbound, exact, fallback_na, target_na)
    if any(not isinstance(values, list) or len(values) != len(set(values)) for values in lists) \
            or not isinstance(unavailable, dict):
        raise ConformanceError("automation_lists")
    partitions = (set(verified), set(unavailable), set(candidate), set(denied), set(unbound))
    if any(partitions[left] & partitions[right] for left in range(5) for right in range(left + 1, 5)) \
            or set().union(*partitions) != feature_ids:
        raise ConformanceError("automation_feature_set")
    if set(verified) != EXPECTED_AUTOMATION_VERIFIED \
            or unavailable != EXPECTED_P08_AUTOMATION_UNAVAILABLE \
            or set(candidate) != EXPECTED_AUTOMATION_CANDIDATES \
            or set(denied) != EXPECTED_POLICY_DENIALS \
            or set(unbound) != EXPECTED_UNBOUND_UNAVAILABLE \
            or set(exact) != EXPECTED_AUTOMATION_VERIFIED \
            or set(fallback_na) != set(EXPECTED_P08_AUTOMATION_UNAVAILABLE) - {"OBJ-044"} \
            or target_na != ["OBJ-044"]:
        raise ConformanceError("automation_semantic_drift")
    output: dict[str, dict[str, Any]] = {}
    for feature_id in feature_ids:
        if feature_id in verified:
            output[feature_id] = {
                "binding_status": "verified_current_target",
                "runtime_support_state": "verified_current_target",
                "routing_enabled": True,
                "unavailable_reason": None,
                "differential_state": "exact_match",
            }
        elif feature_id in unavailable:
            output[feature_id] = {
                "binding_status": "unavailable_with_reason",
                "runtime_support_state": (
                    "target_capability_unavailable"
                    if feature_id == "OBJ-044"
                    else "unavailable_with_reason"
                ),
                "routing_enabled": False,
                "unavailable_reason": unavailable[feature_id],
                "differential_state": (
                    "not_applicable_target_capability_unavailable"
                    if feature_id == "OBJ-044"
                    else "not_applicable_fallback_unavailable"
                ),
            }
        elif feature_id in candidate:
            output[feature_id] = {
                "binding_status": "candidate_unverified",
                "runtime_support_state": "unverified",
                "routing_enabled": False,
                "unavailable_reason": None,
                "differential_state": "not_run",
            }
        elif feature_id in denied:
            output[feature_id] = {
                "binding_status": "denied_by_policy",
                "runtime_support_state": "denied_by_policy",
                "routing_enabled": False,
                "unavailable_reason": "active_content_policy_denial",
                "differential_state": "not_run",
            }
        else:
            output[feature_id] = {
                "binding_status": "unavailable_with_reason",
                "runtime_support_state": "unavailable_with_reason",
                "routing_enabled": False,
                "unavailable_reason": "no_qualified_binding_in_current_phase",
                "differential_state": "not_run",
            }
    return output


def _validate_thresholds(document: dict[str, Any]) -> None:
    _require_exact_keys(document, {"schema_version", "target_profile_id", "asset_profiles", "render_profiles", "green_rule"}, "thresholds")
    if document["schema_version"] != "hwpx-agent.p08-object-threshold-policy/v1" or document["target_profile_id"] != TARGET["profile_id"]:
        raise ConformanceError("threshold_identity")
    asset = document["asset_profiles"]
    render = document["render_profiles"]
    green = document["green_rule"]
    if set(asset) != {
        "relationship-exact-v1",
        "relationship-hancom-2020-canonical-v1",
        "opaque-binary-exact-v1",
        "not-applicable",
    } or set(render) != {"object-affected-region-strict-v1", "not-applicable"}:
        raise ConformanceError("threshold_profile_set")
    relationship = asset["relationship-exact-v1"]
    target_relationship = asset["relationship-hancom-2020-canonical-v1"]
    opaque = asset["opaque-binary-exact-v1"]
    strict = render["object-affected-region-strict-v1"]
    if relationship != {
        "applies_when_required_validation": "resource_integrity",
        "package_path_exact": True,
        "relationship_target_exact": True,
        "media_type_exact": True,
        "expanded_length_exact": True,
        "payload_sha256_exact": True,
        "dangling_or_ambiguous_references_max": 0,
    }:
        raise ConformanceError("asset_threshold_weakened")
    if target_relationship != {
        "applies_when_required_validation": "resource_integrity",
        "source_path_profile": "BinData/p08-{payload_sha256}.{media_extension}",
        "target_path_profile": "BinData/image1.{media_extension}",
        "target_relationship_id": "image1",
        "single_embedded_resource_required": True,
        "media_type_exact": True,
        "expanded_length_exact": True,
        "payload_sha256_exact": True,
        "reference_multiplicity_exact": True,
        "arbitrary_path_remap_allowed": False,
        "dangling_or_ambiguous_references_max": 0,
    }:
        raise ConformanceError("asset_threshold_weakened")
    if opaque != {
        "applies_when_required_validation": "binary_preservation",
        "package_path_exact": True,
        "relationship_target_exact": True,
        "media_type_exact": True,
        "expanded_length_exact": True,
        "payload_sha256_exact": True,
        "activation_allowed": False,
        "payload_mutations_max": 0,
    }:
        raise ConformanceError("asset_threshold_weakened")
    if strict != {
        "applies_when_required_validation": "render_diff",
        "same_target_build_required": True,
        "same_font_inventory_required": True,
        "same_dpi_required": True,
        "affected_region_required": True,
        "unchanged_region_changed_pixels_max": 0,
        "structural_mismatches_max": 0,
        "missing_glyphs_max": 0,
        "object_placement_and_size": "strict",
        "antialias_color_tolerance": "fixture_bound_narrow_required",
        "calibration_state": "pass",
        "calibration_profile_id": "hancom-2020-object-affected-region-calibrated-v1",
        "calibrated_features": {
            "OBJ-020": {"affected_bbox": [135, 166, 274, 242], "changed_pixels_max": 208, "channel_delta_max": 40, "channel_delta_sum_max": 3272},
            "OBJ-021": {"affected_bbox": [130, 170, 270, 243], "changed_pixels_max": 2425, "channel_delta_max": 47, "channel_delta_sum_max": 50525},
            "OBJ-022": {"affected_bbox": [130, 170, 270, 238], "changed_pixels_max": 3100, "channel_delta_max": 51, "channel_delta_sum_max": 52050},
            "OBJ-023": {"affected_bbox": [130, 170, 270, 238], "changed_pixels_max": 2077, "channel_delta_max": 45, "channel_delta_sum_max": 18070},
            "OBJ-024": {"affected_bbox": [165, 170, 236, 243], "changed_pixels_max": 1628, "channel_delta_max": 49, "channel_delta_sum_max": 31792},
            "OBJ-026": {"affected_bbox": [139, 250, 346, 323], "changed_pixels_max": 228, "channel_delta_max": 26, "channel_delta_sum_max": 1881},
            "OBJ-034": {"affected_bbox": [135, 166, 274, 242], "changed_pixels_max": 224, "channel_delta_max": 57, "channel_delta_sum_max": 5354},
        },
    }:
        raise ConformanceError("render_threshold_weakened")
    if green != {
        "asset_profile_definition_required": True,
        "render_profile_definition_required": True,
        "render_fixture_calibration_required_when_render_diff_required": True,
        "unbound_global_pixel_tolerance_forbidden": True,
        "synthetic_render_cannot_substitute_for_target_hancom": True,
    }:
        raise ConformanceError("green_rule_weakened")


def _threshold_binding(required: list[str], validations_passed: list[str]) -> dict[str, str]:
    if "binary_preservation" in required:
        asset_profile = "opaque-binary-exact-v1"
        asset_state = "synthetic_passed" if "binary_preservation" in validations_passed else "not_run"
    elif "resource_integrity" in required:
        target_passed = "hancom_open" in validations_passed
        asset_profile = (
            "relationship-hancom-2020-canonical-v1"
            if target_passed
            else "relationship-exact-v1"
        )
        asset_state = (
            "target_passed"
            if target_passed and "resource_integrity" in validations_passed
            else "synthetic_passed"
            if "resource_integrity" in validations_passed
            else "not_run"
        )
    else:
        asset_profile = "not-applicable"
        asset_state = "not_applicable"
    if "render_diff" in required:
        render_profile = "object-affected-region-strict-v1"
        render_state = "pass" if "render_diff" in validations_passed else "not_run"
    else:
        render_profile = "not-applicable"
        render_state = "not_applicable"
    return {
        "asset_profile": asset_profile,
        "asset_state": asset_state,
        "render_profile": render_profile,
        "render_calibration_state": render_state,
    }


def _blockers(row: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    support = row["support_level"]
    if support == "HYBRID" and row["direct"]["stage"] != "oracle_verified":
        blockers.append("direct_oracle_not_verified")
    elif support == "PRESERVE_ONLY" and row["direct"]["stage"] != "oracle_verified":
        blockers.append("preservation_oracle_not_verified")
    for validation in row["required_validations"]:
        if validation not in row["direct"]["validations_passed"]:
            blockers.append(f"validation_missing:{validation}")
    for fixture in row["required_fixture_classes"]:
        if fixture not in row["direct"]["fixture_classes_passed"]:
            blockers.append(f"fixture_missing:{fixture}")
    if not row["direct"]["negative_passed"]:
        blockers.append("negative_not_passed")
    if not row["direct"]["rollback_or_retry_passed"]:
        blockers.append("rollback_or_retry_not_passed")
    binding = row["automation"]["binding_status"]
    is_p08 = row["catalog_phase"] == "P08"
    if row["feature_id"] == "OBJ-044":
        blockers.append("target_capability_unavailable")
    elif is_p08 and binding == "verified_current_target":
        if row["automation"]["runtime_support_state"] != "verified_current_target" \
                or row["automation"]["routing_enabled"] is not True:
            blockers.append("automation_runtime_unverified")
        if row["differential_state"] != "exact_match":
            blockers.append("differential_not_passed")
    elif is_p08 and binding == "unavailable_with_reason":
        if row["automation"]["routing_enabled"] is not False \
                or row["differential_state"] != "not_applicable_fallback_unavailable":
            blockers.append("fallback_unavailable_state_invalid")
    elif support != "PRESERVE_ONLY":
        blockers.append("automation_binding_unverified" if binding == "candidate_unverified" else "automation_binding_unavailable")
        blockers.append("automation_runtime_unverified")
        if row["differential_state"] != "exact_match":
            blockers.append("differential_not_passed")
    elif row["differential_state"] != "exact_match":
        blockers.append("differential_not_passed")
    if row["thresholds"]["render_calibration_state"] == "not_run":
        blockers.append("render_threshold_not_calibrated")
    return blockers


def build_matrix(
    *,
    root: Path = ROOT,
    direct_override: dict[str, Any] | None = None,
    automation_override: dict[str, Any] | None = None,
    threshold_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    feature_rows = load_feature_rows(root=root)
    feature_ids = {row["feature_id"] for row in feature_rows}
    direct_document = direct_override if direct_override is not None else load_json(DIRECT, root=root)
    automation_document = automation_override if automation_override is not None else load_json(AUTOMATION, root=root)
    threshold_document = threshold_override if threshold_override is not None else load_json(THRESHOLDS, root=root)
    if not isinstance(direct_document, dict) or not isinstance(automation_document, dict) or not isinstance(threshold_document, dict):
        raise ConformanceError("projection_shape")
    direct_by_feature = _load_direct_profiles(direct_document, feature_ids, root)
    automation_by_feature = _load_automation(automation_document, feature_ids)
    _validate_thresholds(threshold_document)

    rows: list[dict[str, Any]] = []
    for catalog in feature_rows:
        feature_id = catalog["feature_id"]
        required_validations = catalog["validation"].split("|")
        profile = direct_by_feature.get(feature_id)
        direct = {
            "backend": profile["backend"] if profile else "unbound",
            "stage": profile["stage"] if profile else "cataloged",
            "validations_passed": sorted(profile["validations_passed"]) if profile else [],
            "fixture_classes_passed": sorted(profile["fixture_classes_passed"]) if profile else [],
            "negative_passed": profile["negative_passed"] if profile else False,
            "rollback_or_retry_passed": profile["rollback_or_retry_passed"] if profile else False,
            "evidence_files": profile["evidence_files"] if profile else [],
        }
        if not set(direct["validations_passed"]) <= set(required_validations) | {"schema"}:
            raise ConformanceError(f"unexpected_validation:{feature_id}")
        if not set(direct["fixture_classes_passed"]) <= set(catalog["required_fixture_classes"]):
            raise ConformanceError(f"unexpected_fixture:{feature_id}")
        row = {
            "feature_id": feature_id,
            "capability_id": catalog["capability_id"],
            "catalog_phase": catalog["phase"],
            "support_level": catalog["support_level"],
            "required_validations": required_validations,
            "required_fixture_classes": catalog["required_fixture_classes"],
            "direct": direct,
            "automation": {
                "binding_status": automation_by_feature[feature_id]["binding_status"],
                "runtime_support_state": automation_by_feature[feature_id]["runtime_support_state"],
                "routing_enabled": automation_by_feature[feature_id]["routing_enabled"],
                "unavailable_reason": automation_by_feature[feature_id]["unavailable_reason"],
            },
            "differential_state": automation_by_feature[feature_id]["differential_state"],
            "thresholds": _threshold_binding(required_validations, direct["validations_passed"]),
            "phase_acceptance": (
                "target_unavailable_accepted"
                if feature_id == "OBJ-044"
                else "supported"
                if catalog["phase"] == "P08"
                else "deferred"
            ),
        }
        row["blockers"] = _blockers(row)
        row["gate_state"] = "green" if not row["blockers"] else "non_green"
        rows.append(row)

    stage_counts = Counter(row["direct"]["stage"] for row in rows)
    automation_counts = Counter(row["automation"]["binding_status"] for row in rows)
    phase_counts = Counter(row["catalog_phase"] for row in rows)
    support_counts = Counter(row["support_level"] for row in rows)
    green_rows = sum(row["gate_state"] == "green" for row in rows)
    summary = {
        "required_rows": len(rows),
        "implementation_covered_rows": len(rows) - stage_counts["cataloged"],
        "green_rows": green_rows,
        "non_green_rows": len(rows) - green_rows,
        "direct_stage_counts": {stage: stage_counts[stage] for stage in STAGES},
        "automation_binding_counts": {state: automation_counts[state] for state in AUTOMATION_STATES},
        "phase_counts": {"P08": phase_counts["P08"], "P11": phase_counts["P11"]},
        "support_level_counts": {
            "HYBRID": support_counts["HYBRID"],
            "AUTOMATION_FULL": support_counts["AUTOMATION_FULL"],
            "OPTIONAL_EXTERNAL": support_counts["OPTIONAL_EXTERNAL"],
            "PRESERVE_ONLY": support_counts["PRESERVE_ONLY"],
        },
        "asset_threshold_required_rows": sum(row["thresholds"]["asset_profile"] != "not-applicable" for row in rows),
        "render_threshold_required_rows": sum(row["thresholds"]["render_profile"] != "not-applicable" for row in rows),
        "render_threshold_calibrated_rows": sum(row["thresholds"]["render_calibration_state"] == "pass" for row in rows),
        "differential_counts": {
            state: sum(row["differential_state"] == state for row in rows)
            for state in (
                "exact_match",
                "not_applicable_fallback_unavailable",
                "not_applicable_target_capability_unavailable",
                "not_run",
            )
        },
        "p08_supported_rows": 41,
        "p08_green_rows": sum(
            row["catalog_phase"] == "P08" and row["gate_state"] == "green"
            for row in rows
        ),
        "p08_target_unavailable_rows": sum(
            row["phase_acceptance"] == "target_unavailable_accepted" for row in rows
        ),
        "p08_phase_gate": "pass_with_target_unavailable",
        "p11_green_rows": sum(
            row["catalog_phase"] == "P11" and row["gate_state"] == "green"
            for row in rows
        ),
        "p11_phase_gate": "deferred",
        "required_matrix": "deferred_p11_non_green",
    }
    expected_summary = {
        "required_rows": 58,
        "implementation_covered_rows": 53,
        "green_rows": 41,
        "non_green_rows": 17,
        "direct_stage_counts": {"cataloged": 5, "unit_passed": 10, "integration_passed": 2, "oracle_verified": 41},
        "automation_binding_counts": {
            "verified_current_target": 34,
            "candidate_unverified": 9,
            "denied_by_policy": 2,
            "unavailable_with_reason": 13,
        },
        "phase_counts": {"P08": 42, "P11": 16},
        "support_level_counts": {"HYBRID": 42, "AUTOMATION_FULL": 11, "OPTIONAL_EXTERNAL": 3, "PRESERVE_ONLY": 2},
        "asset_threshold_required_rows": 44,
        "render_threshold_required_rows": 53,
        "render_threshold_calibrated_rows": 41,
        "differential_counts": {
            "exact_match": 34,
            "not_applicable_fallback_unavailable": 7,
            "not_applicable_target_capability_unavailable": 1,
            "not_run": 16,
        },
        "p08_supported_rows": 41,
        "p08_green_rows": 41,
        "p08_target_unavailable_rows": 1,
        "p08_phase_gate": "pass_with_target_unavailable",
        "p11_green_rows": 0,
        "p11_phase_gate": "deferred",
        "required_matrix": "deferred_p11_non_green",
    }
    if summary != expected_summary:
        raise ConformanceError(f"current_summary_drift:{summary}")
    return {
        "schema_version": "hwpx-agent.p08-object-conformance/v1",
        "target": TARGET,
        "summary": summary,
        "rows": rows,
        "privacy": {
            "absolute_private_paths": False,
            "document_content": False,
            "raw_action_identifiers": False,
            "raw_parameter_identifiers": False,
            "raw_probe_values": False,
        },
    }


def canonical_bytes(matrix: dict[str, Any]) -> bytes:
    return (json.dumps(matrix, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build or verify the P08 object conformance matrix")
    parser.add_argument("--write", action="store_true")
    arguments = parser.parse_args()
    matrix = build_matrix()
    data = canonical_bytes(matrix)
    output = ROOT / MATRIX
    if arguments.write:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(data)
        print(json.dumps({"state": "written", "path": MATRIX.as_posix(), "bytes": len(data)}, sort_keys=True))
        return 0
    if output.read_bytes() != data:
        raise ConformanceError("matrix_drift")
    print(json.dumps({"state": "pass", **matrix["summary"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
