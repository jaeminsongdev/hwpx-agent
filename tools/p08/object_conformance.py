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
AUTOMATION_STATES = ("candidate_unverified", "denied_by_policy", "unavailable_with_reason")

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
    "object-properties-component-v1": {
        "features": ("OBJ-019", "OBJ-030", "OBJ-044", "OBJ-045", "OBJ-046", "OBJ-047", "OBJ-048"),
        "backend": "component_only",
        "stage": "unit_passed",
        "validations": ("schema",),
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
    "special-object-component-v1": {
        "features": ("OBJ-003", "OBJ-012", "OBJ-013", "OBJ-014"),
        "backend": "component_only",
        "stage": "unit_passed",
        "validations": ("schema",),
    },
    "ole-passive-preservation-v1": {
        "features": ("OBJ-011", "OBJ-057"),
        "backend": "preserve_only",
        "stage": "integration_passed",
        "validations": ("binary_preservation", "security_scan"),
    },
}

EXPECTED_AUTOMATION_CANDIDATES = {
    "OBJ-006", "OBJ-049", "OBJ-050", "OBJ-051", "OBJ-052",
    "OBJ-053", "OBJ-054", "OBJ-055", "OBJ-056",
}
EXPECTED_POLICY_DENIALS = {"OBJ-011", "OBJ-057"}

TARGET = {
    "profile_id": "hancom-hangul-2020-secondary",
    "product": "Hancom Hangul 2020",
    "build": "11.0.0.9136",
    "locale": "ko-KR",
    "architecture": "x86",
    "scope": "current_pc_personal_local_development",
}


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
    _require_exact_keys(document, {"schema_version", "target_profile_id", "profiles"}, "direct")
    if document["schema_version"] != "hwpx-agent.p08-object-direct-evidence/v1" or document["target_profile_id"] != TARGET["profile_id"]:
        raise ConformanceError("direct_identity")
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
        if not isinstance(profile["negative_passed"], bool) or not isinstance(profile["rollback_or_retry_passed"], bool):
            raise ConformanceError(f"direct_boolean:{profile_id}")
        if (
            tuple(profile["feature_ids"]) != expected["features"]
            or profile["backend"] != expected["backend"]
            or profile["stage"] != expected["stage"]
            or tuple(profile["validations_passed"]) != expected["validations"]
            or profile["negative_passed"] is not True
            or profile["rollback_or_retry_passed"] is not False
        ):
            raise ConformanceError(f"direct_profile_semantic_drift:{profile_id}")
        evidence = []
        for value in profile["evidence_files"]:
            path = Path(value)
            if path.is_absolute() or ".." in path.parts:
                raise ConformanceError(f"private_evidence_path:{profile_id}")
            evidence.append({"path": path.as_posix(), "sha256": normalized_sha256(path, root=root)})
        compiled = {**profile, "evidence_files": evidence}
        for feature_id in profile["feature_ids"]:
            if feature_id not in feature_ids or feature_id in by_feature:
                raise ConformanceError(f"direct_feature_collision:{feature_id}")
            by_feature[feature_id] = compiled
    if profile_ids != set(EXPECTED_DIRECT_PROFILES):
        raise ConformanceError("direct_profile_set")
    return by_feature


def _load_automation(document: dict[str, Any], feature_ids: set[str]) -> dict[str, str]:
    keys = {
        "schema_version",
        "target_profile_id",
        "candidate_unverified",
        "denied_by_policy",
        "runtime_support_state",
        "routing_enabled",
        "differential_state",
        "actual_target_profile",
        "raw_action_identifiers",
        "raw_parameter_identifiers",
    }
    _require_exact_keys(document, keys, "automation")
    if document["schema_version"] != "hwpx-agent.p08-object-automation-projection/v1" or document["target_profile_id"] != TARGET["profile_id"]:
        raise ConformanceError("automation_identity")
    if document["runtime_support_state"] != "unverified" or document["routing_enabled"] is not False or document["differential_state"] != "not_run":
        raise ConformanceError("automation_promotion")
    if document["actual_target_profile"] is not False or document["raw_action_identifiers"] is not False or document["raw_parameter_identifiers"] is not False:
        raise ConformanceError("automation_private_or_actual_claim")
    candidate = document["candidate_unverified"]
    denied = document["denied_by_policy"]
    if not isinstance(candidate, list) or not isinstance(denied, list) or len(candidate) != len(set(candidate)) or len(denied) != len(set(denied)):
        raise ConformanceError("automation_lists")
    if set(candidate) & set(denied) or not (set(candidate) | set(denied)) <= feature_ids:
        raise ConformanceError("automation_feature_set")
    if set(candidate) != EXPECTED_AUTOMATION_CANDIDATES or set(denied) != EXPECTED_POLICY_DENIALS:
        raise ConformanceError("automation_semantic_drift")
    return {
        feature_id: (
            "candidate_unverified"
            if feature_id in candidate
            else "denied_by_policy"
            if feature_id in denied
            else "unavailable_with_reason"
        )
        for feature_id in feature_ids
    }


def _validate_thresholds(document: dict[str, Any]) -> None:
    _require_exact_keys(document, {"schema_version", "target_profile_id", "asset_profiles", "render_profiles", "green_rule"}, "thresholds")
    if document["schema_version"] != "hwpx-agent.p08-object-threshold-policy/v1" or document["target_profile_id"] != TARGET["profile_id"]:
        raise ConformanceError("threshold_identity")
    asset = document["asset_profiles"]
    render = document["render_profiles"]
    green = document["green_rule"]
    if set(asset) != {"relationship-exact-v1", "opaque-binary-exact-v1", "not-applicable"} or set(render) != {"object-affected-region-strict-v1", "not-applicable"}:
        raise ConformanceError("threshold_profile_set")
    relationship = asset["relationship-exact-v1"]
    opaque = asset["opaque-binary-exact-v1"]
    strict = render["object-affected-region-strict-v1"]
    exact_asset_fields = ("package_path_exact", "relationship_target_exact", "media_type_exact", "expanded_length_exact", "payload_sha256_exact")
    if any(relationship.get(field) is not True or opaque.get(field) is not True for field in exact_asset_fields):
        raise ConformanceError("asset_threshold_weakened")
    if relationship.get("dangling_or_ambiguous_references_max") != 0 or opaque.get("payload_mutations_max") != 0 or opaque.get("activation_allowed") is not False:
        raise ConformanceError("asset_threshold_weakened")
    if strict.get("unchanged_region_changed_pixels_max") != 0 or strict.get("structural_mismatches_max") != 0 or strict.get("missing_glyphs_max") != 0:
        raise ConformanceError("render_threshold_weakened")
    if strict.get("object_placement_and_size") != "strict" or strict.get("calibration_state") != "not_run":
        raise ConformanceError("render_threshold_promotion")
    if any(value is not True for value in green.values()):
        raise ConformanceError("green_rule_weakened")


def _threshold_binding(required: list[str], validations_passed: list[str]) -> dict[str, str]:
    if "binary_preservation" in required:
        asset_profile = "opaque-binary-exact-v1"
        asset_state = "synthetic_passed" if "binary_preservation" in validations_passed else "not_run"
    elif "resource_integrity" in required:
        asset_profile = "relationship-exact-v1"
        asset_state = "synthetic_passed" if "resource_integrity" in validations_passed else "not_run"
    else:
        asset_profile = "not-applicable"
        asset_state = "not_applicable"
    if "render_diff" in required:
        render_profile = "object-affected-region-strict-v1"
        render_state = "not_run"
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
    if support != "PRESERVE_ONLY":
        blockers.append("automation_binding_unverified" if binding == "candidate_unverified" else "automation_binding_unavailable")
        blockers.append("automation_runtime_unverified")
    if row["differential_state"] != "pass":
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
                "binding_status": automation_by_feature[feature_id],
                "runtime_support_state": "unverified",
                "routing_enabled": False,
            },
            "differential_state": "not_run",
            "thresholds": _threshold_binding(required_validations, direct["validations_passed"]),
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
        "differential_counts": {"not_run": sum(row["differential_state"] == "not_run" for row in rows)},
        "required_matrix": "green" if green_rows == len(rows) else "non_green",
    }
    expected_summary = {
        "required_rows": 58,
        "implementation_covered_rows": 53,
        "green_rows": 0,
        "non_green_rows": 58,
        "direct_stage_counts": {"cataloged": 5, "unit_passed": 20, "integration_passed": 33, "oracle_verified": 0},
        "automation_binding_counts": {"candidate_unverified": 9, "denied_by_policy": 2, "unavailable_with_reason": 47},
        "phase_counts": {"P08": 42, "P11": 16},
        "support_level_counts": {"HYBRID": 42, "AUTOMATION_FULL": 11, "OPTIONAL_EXTERNAL": 3, "PRESERVE_ONLY": 2},
        "asset_threshold_required_rows": 44,
        "render_threshold_required_rows": 53,
        "render_threshold_calibrated_rows": 0,
        "differential_counts": {"not_run": 58},
        "required_matrix": "non_green",
    }
    if summary != expected_summary:
        raise ConformanceError("current_summary_drift")
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
