from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MATRIX = Path(
    "implementation/p09/evidence/conformance/"
    "p09-reference-conformance.current-2020.v1.json"
)
CATALOG = Path("specs/feature-coverage-matrix.json")
CONTRACTS = Path("specs/capability-contracts.generated.json")

MAX_JSON_BYTES = 16 * 1024 * 1024
STAGES = ("cataloged", "unit_passed", "integration_passed", "oracle_verified")
DEFERRED_P11 = {
    "REF-016",
    "REF-020",
    "REF-036",
    "REF-040",
    "REF-043",
    "REF-045",
    "REF-047",
}

TARGET = {
    "profile_id": "hancom-hangul-2020-secondary",
    "product": "Hancom Hangul 2020",
    "build": "11.0.0.9136",
    "locale": "ko-KR",
    "architecture": "x86",
    "scope": "current_pc_personal_local_development",
}

COMPONENT_PROFILES: dict[str, dict[str, tuple[str, ...]]] = {
    "p09-01-field-core-v1": {
        "features": tuple(f"REF-{number:03d}" for number in range(1, 11)),
        "evidence": (
            "crates/domain-ir/src/field_engine.rs",
            "crates/domain-ir/tests/field_engine.rs",
        ),
    },
    "p09-02-form-control-v1": {
        "features": (
            "REF-011",
            "REF-012",
            "REF-013",
            "REF-014",
            "REF-015",
            "REF-017",
            "REF-018",
            "REF-019",
        ),
        "evidence": (
            "crates/domain-ir/src/form_control.rs",
            "crates/domain-ir/tests/form_control.rs",
        ),
    },
    "p09-03-note-engine-v1": {
        "features": tuple(f"REF-{number:03d}" for number in range(21, 26)),
        "evidence": (
            "crates/domain-ir/src/note_engine.rs",
            "crates/domain-ir/tests/note_engine.rs",
        ),
    },
    "p09-04-comment-model-v1": {
        "features": tuple(f"REF-{number:03d}" for number in range(26, 31)),
        "evidence": (
            "crates/domain-ir/src/comment_model.rs",
            "crates/domain-ir/tests/comment_model.rs",
        ),
    },
    "p09-05-link-reference-v1": {
        "features": tuple(f"REF-{number:03d}" for number in range(31, 35)),
        "evidence": (
            "crates/domain-ir/src/link_reference.rs",
            "crates/domain-ir/tests/link_reference.rs",
        ),
    },
    "p09-06-cross-reference-v1": {
        "features": ("REF-035",),
        "evidence": (
            "crates/domain-ir/src/cross_reference.rs",
            "crates/domain-ir/tests/cross_reference.rs",
        ),
    },
    "p09-07-toc-index-v1": {
        "features": ("REF-037", "REF-038", "REF-039", "REF-041", "REF-042"),
        "evidence": (
            "crates/domain-ir/src/toc_index.rs",
            "crates/domain-ir/tests/toc_index.rs",
        ),
    },
    "p09-08-citation-v1": {
        "features": ("REF-044",),
        "evidence": (
            "crates/domain-ir/src/citation.rs",
            "crates/domain-ir/tests/citation.rs",
        ),
    },
    "p09-09-mail-merge-v1": {
        "features": ("REF-046",),
        "evidence": (
            "crates/domain-ir/src/mail_merge.rs",
            "crates/domain-ir/tests/mail_merge.rs",
        ),
    },
    "p09-10-reference-auxiliary-v1": {
        "features": tuple(f"REF-{number:03d}" for number in range(48, 54)),
        "evidence": (
            "crates/domain-ir/src/reference_auxiliary.rs",
            "crates/domain-ir/tests/reference_auxiliary.rs",
        ),
    },
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
        text = data.decode("utf-8").replace("\r\n", "\n")
        data = text.encode("utf-8")
    except UnicodeDecodeError:
        pass
    return hashlib.sha256(data).hexdigest()


def _require_exact_keys(value: dict[str, Any], keys: set[str], context: str) -> None:
    if set(value) != keys:
        raise ConformanceError(f"shape_drift:{context}")


def load_feature_rows(*, root: Path = ROOT) -> list[dict[str, Any]]:
    catalog = load_json(CATALOG, root=root)
    contract_document = load_json(CONTRACTS, root=root)
    if not isinstance(catalog, list) or not isinstance(contract_document, dict):
        raise ConformanceError("catalog_shape")
    contracts = contract_document.get("contracts")
    if not isinstance(contracts, list):
        raise ConformanceError("contract_catalog_shape")
    rows = [
        dict(row)
        for row in catalog
        if isinstance(row, dict) and str(row.get("feature_id", "")).startswith("REF-")
    ]
    expected_ids = [f"REF-{number:03d}" for number in range(1, 54)]
    if [row.get("feature_id") for row in rows] != expected_ids:
        raise ConformanceError("feature_id_sequence")
    contracts_by_id = {
        row.get("feature_id"): row
        for row in contracts
        if isinstance(row, dict) and str(row.get("feature_id", "")).startswith("REF-")
    }
    if set(contracts_by_id) != set(expected_ids):
        raise ConformanceError("contract_feature_set")
    for row in rows:
        feature_id = row["feature_id"]
        contract = contracts_by_id[feature_id]
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
                raise ConformanceError(f"catalog_contract_drift:{feature_id}:{field}")
        release_gate = contract.get("release_gate")
        if not isinstance(release_gate, dict) or release_gate.get("phase") != row.get("phase"):
            raise ConformanceError(f"release_gate_drift:{feature_id}")
        fixtures = release_gate.get("required_fixture_classes")
        if (
            not isinstance(fixtures, list)
            or not fixtures
            or len(fixtures) != len(set(fixtures))
            or any(not isinstance(item, str) or not item for item in fixtures)
        ):
            raise ConformanceError(f"fixture_shape:{feature_id}")
        row["required_fixture_classes"] = fixtures
    return rows


def _compile_profiles(
    feature_ids: set[str],
    *,
    root: Path,
    profiles: dict[str, dict[str, tuple[str, ...]]],
) -> dict[str, dict[str, Any]]:
    expected_profile_ids = set(COMPONENT_PROFILES)
    if set(profiles) != expected_profile_ids:
        raise ConformanceError("component_profile_set")
    compiled: dict[str, dict[str, Any]] = {}
    for profile_id, profile in profiles.items():
        if set(profile) != {"features", "evidence"}:
            raise ConformanceError(f"component_profile_shape:{profile_id}")
        features = profile["features"]
        evidence = profile["evidence"]
        if (
            not isinstance(features, tuple)
            or not features
            or len(features) != len(set(features))
            or any(not isinstance(value, str) or value not in feature_ids for value in features)
        ):
            raise ConformanceError(f"component_feature_list:{profile_id}")
        if (
            not isinstance(evidence, tuple)
            or not evidence
            or len(evidence) != len(set(evidence))
            or any(not isinstance(value, str) or not value for value in evidence)
        ):
            raise ConformanceError(f"component_evidence_list:{profile_id}")
        evidence_locks: list[dict[str, str]] = []
        for value in evidence:
            path = Path(value)
            if path.is_absolute() or ".." in path.parts:
                raise ConformanceError(f"private_evidence_path:{profile_id}")
            evidence_locks.append(
                {"path": path.as_posix(), "sha256": normalized_sha256(path, root=root)}
            )
        for feature_id in features:
            if feature_id in compiled:
                raise ConformanceError(f"component_feature_collision:{feature_id}")
            compiled[feature_id] = {
                "profile_id": profile_id,
                "stage": "unit_passed",
                "evidence_files": evidence_locks,
            }
    expected_implemented = feature_ids - DEFERRED_P11
    if set(compiled) != expected_implemented:
        raise ConformanceError("component_coverage_drift")
    return compiled


def _blockers(phase: str, required_validations: list[str]) -> list[str]:
    if phase == "P11":
        blockers = ["p11_automation_owned"]
    else:
        blockers = ["direct_hwpx_not_implemented", "automation_fallback_unqualified"]
    blockers.extend(f"validation_not_run:{value}" for value in required_validations)
    blockers.append("differential_not_run")
    return blockers


def build_matrix(
    *,
    root: Path = ROOT,
    profiles_override: dict[str, dict[str, tuple[str, ...]]] | None = None,
) -> dict[str, Any]:
    feature_rows = load_feature_rows(root=root)
    feature_ids = {row["feature_id"] for row in feature_rows}
    profiles = profiles_override if profiles_override is not None else COMPONENT_PROFILES
    compiled = _compile_profiles(feature_ids, root=root, profiles=profiles)
    if {row["feature_id"] for row in feature_rows if row["phase"] == "P11"} != DEFERRED_P11:
        raise ConformanceError("p11_deferred_set_drift")

    rows: list[dict[str, Any]] = []
    for catalog in feature_rows:
        feature_id = catalog["feature_id"]
        required_validations = catalog["validation"].split("|")
        component = compiled.get(feature_id)
        row = {
            "feature_id": feature_id,
            "capability_id": catalog["capability_id"],
            "catalog_phase": catalog["phase"],
            "support_level": catalog["support_level"],
            "preferred_backend": catalog["preferred_backend"],
            "fallback_backend": catalog["fallback_backend"],
            "required_validations": required_validations,
            "required_fixture_classes": catalog["required_fixture_classes"],
            "component": component
            if component is not None
            else {"profile_id": None, "stage": "cataloged", "evidence_files": []},
            "direct_hwpx": {
                "implementation_state": "not_run",
                "semantic_reopen": "not_run",
                "field_readback": "not_run",
                "reference_update": "not_run",
                "hancom_open": "not_run",
                "render_diff": "not_run",
                "actual_hwpx": False,
                "actual_hangul": False,
            },
            "automation": {
                "ownership": "p11_deferred"
                if catalog["phase"] == "P11"
                else "fallback_unqualified",
                "binding_state": "not_run",
                "routing_enabled": False,
            },
            "differential_state": "not_run",
            "blockers": _blockers(catalog["phase"], required_validations),
            "gate_state": "non_green",
        }
        rows.append(row)

    stage_counts = Counter(row["component"]["stage"] for row in rows)
    phase_counts = Counter(row["catalog_phase"] for row in rows)
    summary = {
        "required_rows": 53,
        "p09_owned_rows": phase_counts["P09"],
        "p11_deferred_rows": phase_counts["P11"],
        "component_covered_rows": len(compiled),
        "component_stage_counts": {stage: stage_counts[stage] for stage in STAGES},
        "direct_hwpx_implemented_rows": 0,
        "actual_hwpx_rows": 0,
        "actual_hangul_rows": 0,
        "render_verified_rows": 0,
        "automation_verified_rows": 0,
        "differential_passed_rows": 0,
        "green_rows": 0,
        "non_green_rows": 53,
        "required_matrix": "non_green",
    }
    expected_summary = {
        "required_rows": 53,
        "p09_owned_rows": 46,
        "p11_deferred_rows": 7,
        "component_covered_rows": 46,
        "component_stage_counts": {
            "cataloged": 7,
            "unit_passed": 46,
            "integration_passed": 0,
            "oracle_verified": 0,
        },
        "direct_hwpx_implemented_rows": 0,
        "actual_hwpx_rows": 0,
        "actual_hangul_rows": 0,
        "render_verified_rows": 0,
        "automation_verified_rows": 0,
        "differential_passed_rows": 0,
        "green_rows": 0,
        "non_green_rows": 53,
        "required_matrix": "non_green",
    }
    if summary != expected_summary:
        raise ConformanceError("current_summary_drift")
    return {
        "schema_version": "hwpx-agent.p09-reference-conformance/v1",
        "target": TARGET,
        "summary": summary,
        "rows": rows,
        "claims": {
            "component_inventory_complete_for_p09_owned_rows": True,
            "direct_hwpx": False,
            "actual_hwpx": False,
            "actual_hangul": False,
            "semantic_reopen": False,
            "field_readback": False,
            "reference_update": False,
            "hancom_open": False,
            "render": False,
            "automation": False,
            "differential": False,
            "p09_complete": False,
            "production_ready": False,
            "product_complete": False,
        },
        "privacy": {
            "absolute_private_paths": False,
            "document_content": False,
            "raw_action_identifiers": False,
            "raw_parameter_identifiers": False,
            "raw_probe_values": False,
        },
    }


def canonical_bytes(matrix: dict[str, Any]) -> bytes:
    return (
        json.dumps(matrix, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build or verify the P09 reference matrix")
    parser.add_argument("--write", action="store_true")
    arguments = parser.parse_args()
    matrix = build_matrix()
    data = canonical_bytes(matrix)
    output = ROOT / MATRIX
    if arguments.write:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(data)
        print(
            json.dumps(
                {"state": "written", "path": MATRIX.as_posix(), "bytes": len(data)},
                sort_keys=True,
            )
        )
        return 0
    if not output.is_file() or output.read_bytes() != data:
        raise ConformanceError("matrix_drift")
    print(json.dumps({"state": "pass", **matrix["summary"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
