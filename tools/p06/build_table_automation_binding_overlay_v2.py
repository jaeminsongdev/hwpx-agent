#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any

try:
    from tools.p06 import table_conformance as conformance
except ModuleNotFoundError:
    import table_conformance as conformance  # type: ignore[no-redef]


ROOT = Path(__file__).resolve().parents[2]
BASE_OVERLAY = (
    "implementation/p02/evidence/bindings/"
    "p06-table-automation-binding-overlay.2020.v1.json"
)
ACTION_RECORDS = "implementation/p02/evidence/automation/automation-pdf.records.v1.json"
CANDIDATE_GRAPH = "implementation/p02/evidence/candidates/candidate-graph.v1.json"
CANONICAL_MATRIX = "specs/feature-coverage-matrix.json"
PRIVATE_REVIEW = "implementation/p02/evidence/p06-table-automation-binding-review.v2.json"
PUBLIC_CONTRACT = "protocol/private/p06-table-automation-binding-overlay-v2.json"
PRIVATE_OVERLAY = (
    "implementation/p02/evidence/bindings/"
    "p06-table-automation-binding-overlay.2020.v2.json"
)
PUBLIC_PROJECTION = "implementation/p06/p06-09-current-2020-automation-projection.json"

PRIVATE_REVIEW_SCHEMA = "hwpx-agent.p06-table-automation-binding-review-private/v2"
PUBLIC_CONTRACT_SCHEMA = "hwpx-agent.p06-table-automation-binding-overlay-contract/v2"
OVERLAY_SCHEMA = "hwpx-agent.p06-table-automation-binding-overlay/v1"
EXPECTED_COUNT = conformance.EXPECTED_FEATURE_COUNT


# A mapping is admitted only when its Action identifier is an exact unique record in the
# frozen official Action Table.  Shared actions are intentional: their reviewed parameter or
# context specialization is recorded by mapping_mode and is runtime-qualified separately.
ACTION_BY_FEATURE: dict[str, tuple[str, str]] = {
    "TABLE-001": ("TableCreate", "exact_action"),
    "TABLE-002": ("TableCellBorderDiagonalDown", "reviewed_effect_action"),
    "TABLE-003": ("TableCellBorderNo", "reviewed_effect_action"),
    "TABLE-004": ("TableStringToTable", "exact_action"),
    "TABLE-005": ("TableTableToString", "exact_action"),
    "TABLE-006": ("InsertChart", "exact_action"),
    "TABLE-007": ("TablePropertyDialog", "exact_action"),
    "TABLE-008": ("CellBorder", "reviewed_parameterized_action"),
    "TABLE-009": ("CellZoneBorderFill", "reviewed_parameterized_action"),
    "TABLE-010": ("TableSplitTable", "exact_action"),
    "TABLE-011": ("TableMergeTable", "exact_action"),
    "TABLE-012": ("TableInsertUpperRow", "exact_action"),
    "TABLE-013": ("TableInsertLeftColumn", "exact_action"),
    "TABLE-014": ("TableDeleteRow", "exact_action"),
    "TABLE-015": ("TableDeleteColumn", "exact_action"),
    "TABLE-016": ("TableSplitCell", "exact_action"),
    "TABLE-017": ("TableMergeCell", "exact_action"),
    "TABLE-018": ("TableDistributeCellHeight", "exact_action"),
    "TABLE-019": ("TableDistributeCellWidth", "exact_action"),
    "TABLE-020": ("CellZoneBorderFill", "reviewed_parameterized_action"),
    "TABLE-021": ("TableSwap", "exact_action"),
    "TABLE-022": ("TableFormula", "reviewed_parameterized_action"),
    "TABLE-023": ("TableFormula", "reviewed_parameterized_action"),
    "TABLE-024": ("TableFormula", "reviewed_parameterized_action"),
    "TABLE-025": ("TableFormulaSumHor", "exact_action"),
    "TABLE-026": ("TableFormulaSumVer", "exact_action"),
    "TABLE-027": ("TableFormulaAvgHor", "exact_action"),
    "TABLE-028": ("TableFormulaAvgVer", "exact_action"),
    "TABLE-029": ("TableFormulaProHor", "exact_action"),
    "TABLE-030": ("TableFormulaProVer", "exact_action"),
    "TABLE-031": ("TableFormula", "exact_action"),
    "TABLE-032": ("TableInsertComma", "exact_action"),
    "TABLE-033": ("TableDeleteComma", "exact_action"),
    "TABLE-034": ("TablePropertyDialog", "reviewed_parameterized_action"),
    "TABLE-035": ("TableResizeExRight", "reviewed_composite_action"),
    "TABLE-036": ("TableTreatAsChar", "exact_action"),
    "TABLE-037": ("TablePropertyDialog", "reviewed_parameterized_action"),
    "TABLE-038": ("TablePropertyDialog", "reviewed_parameterized_action"),
    "TABLE-039": ("TablePropertyDialog", "reviewed_parameterized_action"),
    "TABLE-040": ("TableCellAlignCenterCenter", "exact_action"),
    "TABLE-041": ("TableCellTextVertAll", "exact_action"),
    "TABLE-042": ("TablePropertyDialog", "reviewed_parameterized_action"),
    "TABLE-043": ("TableBreakNone", "exact_action"),
    "TABLE-044": ("TableBreakCell", "exact_action"),
    "TABLE-045": ("TablePropertyDialog", "reviewed_parameterized_action"),
    "TABLE-046": ("CellBorder", "exact_action"),
    "TABLE-047": ("TableCellBorderDiagonalUp", "exact_action"),
    "TABLE-048": ("CellFill", "exact_action"),
    "TABLE-049": ("TableFormula", "reviewed_parameterized_action"),
    "TABLE-050": ("TableResizeExDown", "exact_action"),
    "TABLE-051": ("TableResizeExRight", "exact_action"),
    "TABLE-052": ("TableResizeExLeft", "reviewed_effect_action"),
    "TABLE-053": ("TableResizeExRight", "reviewed_effect_action"),
    "TABLE-054": ("TableCreate", "reviewed_context_action"),
    "TABLE-055": ("ShapeObjAttachCaption", "exact_action"),
    "TABLE-056": ("TableTableToString", "reviewed_composite_action"),
    "TABLE-057": ("TableAutoFill", "exact_action"),
    "TABLE-058": ("TableAutoFillDlg", "exact_action"),
    "TABLE-059": ("TableFormula", "reviewed_parameterized_action"),
    "TABLE-060": ("TableFormula", "reviewed_parameterized_action"),
    "TABLE-061": ("TableFormula", "reviewed_parameterized_action"),
}


class OverlayV2Error(ValueError):
    pass


def _load(root: Path, relative: str, maximum: int = 8 * 1024 * 1024) -> tuple[Any, str]:
    try:
        return conformance.load_json_file(root, relative, maximum)
    except conformance.ConformanceError as error:
        raise OverlayV2Error(str(error)) from error


def _digest_text(value: str) -> str:
    return conformance.sha256_bytes(value.encode("utf-8"))


def _digest_json(value: Any) -> str:
    return conformance.sha256_bytes(conformance.canonical_json(value))


def _exact_keys(value: Any, expected: set[str], code: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != expected:
        raise OverlayV2Error(code)
    return value


def _catalog_rows(catalog: Any) -> list[dict[str, Any]]:
    if not isinstance(catalog, list):
        raise OverlayV2Error("catalog_shape")
    rows = sorted(
        (row for row in catalog if isinstance(row, dict) and row.get("phase") == "P06"),
        key=lambda row: row.get("feature_id", ""),
    )
    expected = [f"TABLE-{index:03d}" for index in range(1, EXPECTED_COUNT + 1)]
    if [row.get("feature_id") for row in rows] != expected:
        raise OverlayV2Error("catalog_coverage")
    if set(ACTION_BY_FEATURE) != set(expected):
        raise OverlayV2Error("mapping_coverage")
    return rows


def _official_actions(records: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(records, list) or len(records) > 10_000:
        raise OverlayV2Error("action_records_shape")
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        if isinstance(record, dict) and record.get("source_kind") == "action_table":
            name = record.get("original_name")
            if isinstance(name, str):
                grouped.setdefault(name, []).append(record)
    output: dict[str, dict[str, Any]] = {}
    for action_name in {value[0] for value in ACTION_BY_FEATURE.values()}:
        matches = grouped.get(action_name, [])
        if len(matches) != 1:
            raise OverlayV2Error("official_action_not_unique")
        record = matches[0]
        parameters = record.get("parameters")
        if not isinstance(parameters, list) or len(parameters) != 1 \
                or not isinstance(parameters[0], dict) \
                or not isinstance(parameters[0].get("original_name"), str):
            raise OverlayV2Error("official_action_parameter_shape")
        output[action_name] = record
    return output


def _nodes_by_record(graph: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(graph, dict) or graph.get("schema_version") \
            != "hwpx-agent.candidate-graph/v1" or not isinstance(graph.get("nodes"), list):
        raise OverlayV2Error("candidate_graph_shape")
    grouped: dict[str, list[dict[str, Any]]] = {}
    for node in graph["nodes"]:
        if not isinstance(node, dict):
            raise OverlayV2Error("candidate_node_shape")
        record_id = node.get("record_id")
        if isinstance(record_id, str):
            grouped.setdefault(record_id, []).append(node)
    output: dict[str, dict[str, Any]] = {}
    for record_id, nodes in grouped.items():
        if len(nodes) == 1:
            output[record_id] = nodes[0]
    return output


def build_review(root: Path) -> dict[str, Any]:
    base, base_sha = _load(root, BASE_OVERLAY)
    records, records_sha = _load(root, ACTION_RECORDS)
    graph, graph_sha = _load(root, CANDIDATE_GRAPH)
    catalog, catalog_sha = _load(root, CANONICAL_MATRIX)
    rows = _catalog_rows(catalog)
    actions = _official_actions(records)
    nodes = _nodes_by_record(graph)
    items: list[dict[str, str]] = []
    for row in rows:
        feature_id = row["feature_id"]
        action_name, mapping_mode = ACTION_BY_FEATURE[feature_id]
        record = actions[action_name]
        record_id = record.get("record_id")
        node = nodes.get(record_id) if isinstance(record_id, str) else None
        if node is None or node.get("source_id") != record.get("source_id") \
                or node.get("source_sha256") != record.get("source_sha256"):
            raise OverlayV2Error("candidate_node_source_mismatch")
        items.append(
            {
                "feature_id": feature_id,
                "capability_id": row["capability_id"],
                "action_name": action_name,
                "mapping_mode": mapping_mode,
            }
        )
    return {
        "schema_version": PRIVATE_REVIEW_SCHEMA,
        "source_locks": {
            "base_overlay_sha256": base_sha,
            "action_records_sha256": records_sha,
            "candidate_graph_sha256": graph_sha,
            "canonical_matrix_sha256": catalog_sha,
        },
        "review_policy": {
            "source_kind": "action_table",
            "identifier_match": "exact_unique_official_action",
            "shared_action": "requires_feature_specific_parameter_or_context_runtime_probe",
            "runtime_qualification": "not_run",
            "routing_enabled": False,
        },
        "items": items,
    }


def validate_review(actual: Any, expected: dict[str, Any]) -> list[dict[str, str]]:
    if conformance.canonical_json(actual) != conformance.canonical_json(expected):
        raise OverlayV2Error("private_review_drift")
    value = _exact_keys(
        actual,
        {"schema_version", "source_locks", "review_policy", "items"},
        "private_review_shape",
    )
    if value["schema_version"] != PRIVATE_REVIEW_SCHEMA \
            or not isinstance(value["items"], list) \
            or len(value["items"]) != EXPECTED_COUNT:
        raise OverlayV2Error("private_review_contract")
    return value["items"]


def build_bundle(root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    expected_review = build_review(root)
    review, review_sha = _load(root, PRIVATE_REVIEW)
    review_items = validate_review(review, expected_review)
    base, base_sha = _load(root, BASE_OVERLAY)
    records, records_sha = _load(root, ACTION_RECORDS)
    graph, graph_sha = _load(root, CANDIDATE_GRAPH)
    catalog, catalog_sha = _load(root, CANONICAL_MATRIX)
    rows = _catalog_rows(catalog)
    actions = _official_actions(records)
    nodes = _nodes_by_record(graph)
    base_bindings = {
        binding.get("feature_id"): binding
        for binding in base.get("bindings", [])
        if isinstance(binding, dict)
    }
    if set(base_bindings) != {row["feature_id"] for row in rows}:
        raise OverlayV2Error("base_overlay_coverage")

    public_mappings: list[dict[str, Any]] = []
    bindings: list[dict[str, Any]] = []
    review_by_feature = {item["feature_id"]: item for item in review_items}
    for row in rows:
        feature_id = row["feature_id"]
        decision = review_by_feature.get(feature_id)
        if decision is None or decision.get("capability_id") != row.get("capability_id"):
            raise OverlayV2Error("review_catalog_identity")
        action_name = decision["action_name"]
        mapping_mode = decision["mapping_mode"]
        record = actions[action_name]
        record_id = record["record_id"]
        node = nodes.get(record_id)
        if node is None:
            raise OverlayV2Error("candidate_node_missing")
        parameter_signal = record["parameters"][0]["original_name"]
        parameter_set_id = None if parameter_signal == "-" else parameter_signal
        public_mappings.append(
            {
                "feature_id": feature_id,
                "capability_id": row["capability_id"],
                "mapping_mode": mapping_mode,
                "action_identifier_sha256": _digest_text(action_name),
                "parameter_signal_sha256": _digest_text(parameter_signal),
                "record_id_sha256": _digest_text(record_id),
                "node_id_sha256": _digest_text(node["node_id"]),
                "description_sha256": _digest_text(record["description_ko"]),
                "locator_sha256": _digest_json(record["locator"]),
                "record_sha256": _digest_json(record),
            }
        )
        binding = deepcopy(base_bindings[feature_id])
        binding.update(
            {
                "invocation": {
                    "action_id": action_name,
                    "kind": "action",
                    "mapping_mode": mapping_mode,
                    "parameter_map": [],
                    "parameter_map_state": "pending_runtime_probe",
                    "parameter_set_id": parameter_set_id,
                    "parameter_set_state": (
                        "source_declares_none"
                        if parameter_set_id is None
                        else "documented_candidate"
                    ),
                },
                "probe": {
                    "expected_effect": row["capability_id"],
                    "external_side_effect_risk": "bounded_disposable_document_only",
                    "fixture_id": None,
                    "modal_risk": "unverified",
                    "post_snapshot": None,
                    "pre_snapshot": None,
                    "state": "not_run",
                },
                "raw_identifiers_present": True,
                "routing_enabled": False,
                "runtime_support_state": "unverified",
                "source_refs": [
                    {
                        "artifact_sha256": records_sha,
                        "kind": "p06_v2_exact_action_table_review",
                        "node_id": node["node_id"],
                        "record_id": record_id,
                        "source_id": record["source_id"],
                        "source_sha256": record["source_sha256"],
                    }
                ],
                "status": "candidate_unverified",
                "unavailable_reason": None,
            }
        )
        bindings.append(binding)

    if Counter(binding["status"] for binding in bindings) != Counter(
        {"candidate_unverified": EXPECTED_COUNT}
    ):
        raise OverlayV2Error("overlay_status_coverage")
    source_locks = {
        "base_overlay_sha256": base_sha,
        "action_records_sha256": records_sha,
        "candidate_graph_sha256": graph_sha,
        "canonical_matrix_sha256": catalog_sha,
        "private_review_sha256": review_sha,
    }
    contract = {
        "schema_version": PUBLIC_CONTRACT_SCHEMA,
        "target": conformance.exact_target(
            {
                "profile_id": base["target"]["profile_id"],
                "product": base["target"]["product"],
                "build": base["target"]["exact_build"],
                "locale": base["target"]["locale"],
                "architecture": base["target"]["architecture"],
                "scope": "current_pc_personal_local_development",
            }
        ),
        "source_locks": source_locks,
        "review_policy": {
            "source": "official_action_table_records",
            "identifier_match": "exact_unique_action_identifier",
            "shared_action": "feature_specific_parameter_or_context_probe_required",
        },
        "coverage": {
            "required_rows": EXPECTED_COUNT,
            "candidate_unverified": EXPECTED_COUNT,
            "unavailable_with_reason": 0,
            "runtime_verified": 0,
            "routing_enabled": 0,
        },
        "mappings": public_mappings,
        "privacy": {
            "raw_action_identifiers": False,
            "raw_parameter_identifiers": False,
            "raw_probe_values": False,
            "absolute_private_paths": False,
        },
        "not_claimed": {
            "runtime_qualification": False,
            "routing_support": False,
            "direct_automation_differential": False,
            "p06_09_complete": False,
            "p06_phase_complete": False,
            "product_complete": False,
        },
    }
    contract_sha = conformance.sha256_bytes(conformance.canonical_json(contract))
    overlay = {
        "schema_version": OVERLAY_SCHEMA,
        "target": deepcopy(base["target"]),
        "source_locks": source_locks,
        "review_contract_sha256": contract_sha,
        "coverage": {
            "required_rows": EXPECTED_COUNT,
            "candidate_unverified": EXPECTED_COUNT,
            "unavailable_with_reason": 0,
        },
        "runtime_qualification": {
            "state": "not_run",
            "verified_current_target": 0,
            "failed_current_target": 0,
        },
        "routing_enabled": False,
        "restricted_derivative": True,
        "bindings": bindings,
    }
    projection = conformance.build_automation_projection(
        overlay, conformance.sha256_bytes(conformance.canonical_json(overlay))
    )
    conformance.validate_projection(projection)
    return expected_review, contract, overlay, projection


def _write_new(path: Path, value: Any) -> None:
    conformance.write_new(path.resolve(), conformance.canonical_json(value))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the P06 61-row ActionTable v2 overlay.")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--bootstrap-review", action="store_true")
    parser.add_argument("--bootstrap-contract", action="store_true")
    parser.add_argument("--output-overlay", type=Path)
    parser.add_argument("--output-projection", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve(strict=True)
    if args.bootstrap_review:
        _write_new(root / PRIVATE_REVIEW, build_review(root))
        print("P06_TABLE_AUTOMATION_V2_PRIVATE_REVIEW_CREATED rows=61")
        return 0
    review, contract, overlay, projection = build_bundle(root)
    if args.bootstrap_contract:
        _write_new(root / PUBLIC_CONTRACT, contract)
    else:
        actual, _ = _load(root, PUBLIC_CONTRACT, 2 * 1024 * 1024)
        if conformance.canonical_json(actual) != conformance.canonical_json(contract):
            raise OverlayV2Error("public_contract_drift")
    if args.output_overlay is not None:
        _write_new(args.output_overlay, overlay)
    if args.output_projection is not None:
        _write_new(args.output_projection, projection)
    if review != build_review(root):
        raise OverlayV2Error("review_rebuild_drift")
    print("P06_TABLE_AUTOMATION_BINDING_OVERLAY_V2_PASS candidate=61 unavailable=0 runtime_verified=0 routing_enabled=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
