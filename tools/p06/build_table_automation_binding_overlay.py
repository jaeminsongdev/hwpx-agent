#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from pathlib import Path
import re
from typing import Any

try:
    from tools.p06 import table_conformance as conformance
except ModuleNotFoundError:
    import table_conformance as conformance  # type: ignore[no-redef]


ROOT = Path(__file__).resolve().parents[2]
PARENT_REGISTRY = (
    "implementation/p02/evidence/bindings/automation-bindings.2020.v1.final.json"
)
ACTION_RECORDS = "implementation/p02/evidence/automation/automation-pdf.records.v1.json"
CANDIDATE_GRAPH = "implementation/p02/evidence/candidates/candidate-graph.v1.json"
CANONICAL_MATRIX = "specs/feature-coverage-matrix.json"
PRIVATE_REVIEW = "implementation/p02/evidence/p06-table-automation-binding-review.v1.json"
PUBLIC_CONTRACT = "protocol/private/p06-table-automation-binding-overlay-v1.json"
PRIVATE_OVERLAY = (
    "implementation/p02/evidence/bindings/"
    "p06-table-automation-binding-overlay.2020.v1.json"
)
PUBLIC_PROJECTION = "implementation/p06/p06-09-current-2020-automation-projection.json"

PRIVATE_REVIEW_SCHEMA = "hwpx-agent.p06-table-automation-binding-review-private/v1"
PUBLIC_CONTRACT_SCHEMA = "hwpx-agent.p06-table-automation-binding-overlay-contract/v1"
OVERLAY_SCHEMA = "hwpx-agent.p06-table-automation-binding-overlay/v1"
EXPECTED_CANDIDATES = 32
EXPECTED_UNAVAILABLE = conformance.EXPECTED_FEATURE_COUNT - EXPECTED_CANDIDATES
ACTION_NAME_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_]*\Z")
SOURCE_LOCK_KEYS = {
    "parent_registry_sha256",
    "action_records_sha256",
    "candidate_graph_sha256",
    "canonical_matrix_sha256",
    "private_review_sha256",
}
MAPPING_KEYS = {
    "feature_id",
    "capability_id",
    "record_id_sha256",
    "node_id_sha256",
    "action_identifier_sha256",
    "description_sha256",
    "parameter_signal_sha256",
    "parameter_set_state",
    "locator_sha256",
    "record_sha256",
}


class OverlayError(ValueError):
    pass


def _exact_keys(value: Any, keys: set[str], code: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise OverlayError(code)
    return value


def _load_json(root: Path, relative: str, maximum: int) -> tuple[Any, str]:
    try:
        return conformance.load_json_file(root, relative, maximum)
    except conformance.ConformanceError as error:
        raise OverlayError(str(error)) from error


def _digest_text(value: str) -> str:
    return conformance.sha256_bytes(value.encode("utf-8"))


def _digest_json(value: Any) -> str:
    return conformance.sha256_bytes(conformance.canonical_json(value))


def _source_digests(root: Path) -> dict[str, str]:
    return {
        "parent_registry_sha256": conformance.sha256_file(
            conformance.bounded_repo_file(root, PARENT_REGISTRY)
        ),
        "action_records_sha256": conformance.sha256_file(
            conformance.bounded_repo_file(root, ACTION_RECORDS)
        ),
        "candidate_graph_sha256": conformance.sha256_file(
            conformance.bounded_repo_file(root, CANDIDATE_GRAPH)
        ),
        "canonical_matrix_sha256": conformance.sha256_file(
            conformance.bounded_repo_file(root, CANONICAL_MATRIX)
        ),
    }


def _load_inputs(root: Path) -> tuple[Any, Any, Any, Any, dict[str, str]]:
    parent, parent_sha256 = _load_json(root, PARENT_REGISTRY, 4 * 1024 * 1024)
    records, records_sha256 = _load_json(root, ACTION_RECORDS, 8 * 1024 * 1024)
    graph, graph_sha256 = _load_json(root, CANDIDATE_GRAPH, 8 * 1024 * 1024)
    review, review_sha256 = _load_json(root, PRIVATE_REVIEW, 1024 * 1024)
    digests = _source_digests(root)
    if digests != {
        "parent_registry_sha256": parent_sha256,
        "action_records_sha256": records_sha256,
        "candidate_graph_sha256": graph_sha256,
        "canonical_matrix_sha256": digests["canonical_matrix_sha256"],
    }:
        raise OverlayError("source_digest_read_mismatch")
    digests["private_review_sha256"] = review_sha256
    return parent, records, graph, review, digests


def _validate_parent(parent: Any, parent_sha256: str) -> dict[str, dict[str, Any]]:
    projection = conformance.build_automation_projection(parent, parent_sha256)
    rows = conformance.validate_projection(projection)
    bindings = parent.get("bindings") if isinstance(parent, dict) else None
    if not isinstance(bindings, list):
        raise OverlayError("parent_bindings")
    table_bindings = {
        item["feature_id"]: item
        for item in bindings
        if isinstance(item, dict)
        and isinstance(item.get("feature_id"), str)
        and conformance.FEATURE_ID_PATTERN.fullmatch(item["feature_id"])
    }
    if set(table_bindings) != set(rows):
        raise OverlayError("parent_table_coverage")
    for item in table_bindings.values():
        if item.get("runtime_support_state") != "unverified" \
                or item.get("routing_enabled") is not False:
            raise OverlayError("parent_runtime_or_routing_promoted")
    return table_bindings


def _validate_review(
    review: Any,
    source_digests: dict[str, str],
    table_bindings: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    value = _exact_keys(
        review,
        {"schema_version", "source_locks", "review_policy", "items"},
        "review_shape",
    )
    if value["schema_version"] != PRIVATE_REVIEW_SCHEMA:
        raise OverlayError("review_schema")
    if value["source_locks"] != {
        key: source_digests[key]
        for key in (
            "parent_registry_sha256",
            "action_records_sha256",
            "candidate_graph_sha256",
            "canonical_matrix_sha256",
        )
    }:
        raise OverlayError("review_source_locks")
    if value["review_policy"] != {
        "source_kind": "action_table",
        "match": "exact_unique_official_action",
        "composition": "not_admitted",
        "runtime_qualification": "not_run",
        "routing_enabled": False,
    }:
        raise OverlayError("review_policy")
    items = value["items"]
    if not isinstance(items, list) or len(items) != EXPECTED_CANDIDATES:
        raise OverlayError("review_count")
    normalized: list[dict[str, str]] = []
    last = ""
    seen_actions: set[str] = set()
    for item in items:
        row = _exact_keys(
            item,
            {"feature_id", "capability_id", "action_name"},
            "review_item_shape",
        )
        feature_id = row["feature_id"]
        capability_id = row["capability_id"]
        action_name = row["action_name"]
        if not isinstance(feature_id, str) or not conformance.FEATURE_ID_PATTERN.fullmatch(
            feature_id
        ) or feature_id <= last:
            raise OverlayError("review_feature_order")
        if feature_id not in table_bindings \
                or table_bindings[feature_id].get("capability_id") != capability_id:
            raise OverlayError("review_capability_mismatch")
        if not isinstance(action_name, str) or not ACTION_NAME_PATTERN.fullmatch(action_name) \
                or action_name in seen_actions:
            raise OverlayError("review_action_identity")
        normalized.append(
            {
                "feature_id": feature_id,
                "capability_id": capability_id,
                "action_name": action_name,
            }
        )
        last = feature_id
        seen_actions.add(action_name)
    parent_candidates = {
        feature_id
        for feature_id, binding in table_bindings.items()
        if binding.get("status") == "candidate_unverified"
    }
    if not parent_candidates.issubset({item["feature_id"] for item in normalized}):
        raise OverlayError("parent_candidate_demoted")
    return normalized


def _select_source_proofs(
    records: Any,
    graph: Any,
    review_items: list[dict[str, str]],
) -> tuple[list[dict[str, Any]], dict[str, tuple[dict[str, Any], dict[str, Any]]]]:
    if not isinstance(records, list) or len(records) > 10_000:
        raise OverlayError("action_records_shape")
    if not isinstance(graph, dict) or graph.get("schema_version") \
            != "hwpx-agent.candidate-graph/v1" or not isinstance(graph.get("nodes"), list):
        raise OverlayError("candidate_graph_shape")
    action_records: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        if not isinstance(record, dict) or record.get("source_kind") != "action_table":
            continue
        name = record.get("original_name")
        if isinstance(name, str):
            action_records.setdefault(name, []).append(record)
    nodes_by_record: dict[str, list[dict[str, Any]]] = {}
    for node in graph["nodes"]:
        if not isinstance(node, dict):
            raise OverlayError("candidate_node_shape")
        record_id = node.get("record_id")
        if isinstance(record_id, str):
            nodes_by_record.setdefault(record_id, []).append(node)

    mappings: list[dict[str, Any]] = []
    selected: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    for decision in review_items:
        matches = action_records.get(decision["action_name"], [])
        if len(matches) != 1:
            raise OverlayError("official_action_not_unique")
        record = matches[0]
        record_id = record.get("record_id")
        if not isinstance(record_id, str):
            raise OverlayError("official_record_id")
        node_matches = nodes_by_record.get(record_id, [])
        if len(node_matches) != 1:
            raise OverlayError("candidate_node_not_unique")
        node = node_matches[0]
        node_id = node.get("node_id")
        description = record.get("description_ko")
        parameters = record.get("parameters")
        locator = record.get("locator")
        if not isinstance(node_id, str) or not isinstance(description, str) \
                or not isinstance(parameters, list) or len(parameters) != 1 \
                or not isinstance(parameters[0], dict) or not isinstance(locator, dict):
            raise OverlayError("official_record_shape")
        for identity_key in ("source_kind", "source_id", "source_sha256"):
            if node.get(identity_key) != record.get(identity_key):
                raise OverlayError("candidate_node_source_mismatch")
        if not isinstance(record.get("source_id"), str) \
                or not isinstance(record.get("source_sha256"), str) \
                or not conformance.SHA256_PATTERN.fullmatch(record["source_sha256"]):
            raise OverlayError("official_source_identity")
        parameter_name = parameters[0].get("original_name")
        if not isinstance(parameter_name, str) or not parameter_name:
            raise OverlayError("official_parameter_signal")
        parameter_state = (
            "source_declares_none" if parameter_name == "-" else "documented_candidate"
        )
        feature_id = decision["feature_id"]
        mappings.append(
            {
                "feature_id": feature_id,
                "capability_id": decision["capability_id"],
                "record_id_sha256": _digest_text(record_id),
                "node_id_sha256": _digest_text(node_id),
                "action_identifier_sha256": _digest_text(decision["action_name"]),
                "description_sha256": _digest_text(description),
                "parameter_signal_sha256": _digest_text(parameter_name),
                "parameter_set_state": parameter_state,
                "locator_sha256": _digest_json(locator),
                "record_sha256": _digest_json(record),
            }
        )
        selected[feature_id] = (record, node)
    return mappings, selected


def build_public_contract(
    parent: Any,
    records: Any,
    graph: Any,
    review: Any,
    source_digests: dict[str, str],
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], dict[str, tuple[dict[str, Any], dict[str, Any]]]]:
    table_bindings = _validate_parent(parent, source_digests["parent_registry_sha256"])
    review_items = _validate_review(review, source_digests, table_bindings)
    mappings, selected = _select_source_proofs(records, graph, review_items)
    contract = {
        "schema_version": PUBLIC_CONTRACT_SCHEMA,
        "target": conformance.exact_target(
            {
                "profile_id": parent["target"]["profile_id"],
                "product": parent["target"]["product"],
                "build": parent["target"]["exact_build"],
                "locale": parent["target"]["locale"],
                "architecture": parent["target"]["architecture"],
                "scope": "current_pc_personal_local_development",
            }
        ),
        "source_locks": source_digests,
        "review_policy": {
            "source": "official_action_table_records",
            "match": "exact_unique_action_identifier",
            "composition": "not_admitted",
            "ambiguous_or_partial_matches": "unavailable_with_reason",
        },
        "coverage": {
            "required_rows": conformance.EXPECTED_FEATURE_COUNT,
            "candidate_unverified": EXPECTED_CANDIDATES,
            "unavailable_with_reason": EXPECTED_UNAVAILABLE,
            "runtime_verified": 0,
            "routing_enabled": 0,
        },
        "mappings": mappings,
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
    validate_public_contract_shape(contract)
    return contract, table_bindings, selected


def build_overlay(
    parent: dict[str, Any],
    table_bindings: dict[str, dict[str, Any]],
    selected: dict[str, tuple[dict[str, Any], dict[str, Any]]],
    source_digests: dict[str, str],
    contract_sha256: str,
) -> dict[str, Any]:
    bindings: list[dict[str, Any]] = []
    for feature_id in sorted(table_bindings):
        binding = deepcopy(table_bindings[feature_id])
        if feature_id in selected:
            record, node = selected[feature_id]
            parameter_name = record["parameters"][0]["original_name"]
            parameter_set_id = None if parameter_name == "-" else parameter_name
            binding.update(
                {
                    "invocation": {
                        "action_id": record["original_name"],
                        "kind": "action",
                        "parameter_map": [],
                        "parameter_map_state": "pending_runtime_probe",
                        "parameter_set_id": parameter_set_id,
                        "parameter_set_state": (
                            "source_declares_none"
                            if parameter_set_id is None
                            else "documented_candidate"
                        ),
                    },
                    "raw_identifiers_present": True,
                    "routing_enabled": False,
                    "runtime_support_state": "unverified",
                    "source_refs": [
                        {
                            "artifact_sha256": source_digests["action_records_sha256"],
                            "kind": "p06_exact_action_table_review",
                            "node_id": node["node_id"],
                            "record_id": record["record_id"],
                            "source_id": record["source_id"],
                            "source_sha256": record["source_sha256"],
                        }
                    ],
                    "status": "candidate_unverified",
                    "unavailable_reason": None,
                }
            )
        elif binding.get("status") != "unavailable_with_reason":
            raise OverlayError("unselected_binding_not_unavailable")
        bindings.append(binding)

    counts = Counter(binding["status"] for binding in bindings)
    if counts != Counter(
        {
            "candidate_unverified": EXPECTED_CANDIDATES,
            "unavailable_with_reason": EXPECTED_UNAVAILABLE,
        }
    ):
        raise OverlayError("overlay_coverage")
    if any(
        binding["runtime_support_state"] != "unverified"
        or binding["routing_enabled"] is not False
        for binding in bindings
    ):
        raise OverlayError("overlay_runtime_or_routing_promoted")
    return {
        "schema_version": OVERLAY_SCHEMA,
        "target": deepcopy(parent["target"]),
        "source_locks": source_digests,
        "review_contract_sha256": contract_sha256,
        "coverage": {
            "required_rows": conformance.EXPECTED_FEATURE_COUNT,
            "candidate_unverified": EXPECTED_CANDIDATES,
            "unavailable_with_reason": EXPECTED_UNAVAILABLE,
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


def validate_public_contract_shape(value: Any) -> dict[str, str]:
    contract = _exact_keys(
        value,
        {
            "schema_version",
            "target",
            "source_locks",
            "review_policy",
            "coverage",
            "mappings",
            "privacy",
            "not_claimed",
        },
        "public_contract_shape",
    )
    if contract["schema_version"] != PUBLIC_CONTRACT_SCHEMA:
        raise OverlayError("public_contract_schema")
    conformance.exact_target(contract["target"])
    source_locks = _exact_keys(
        contract["source_locks"], SOURCE_LOCK_KEYS, "public_contract_source_locks"
    )
    if any(
        not isinstance(value, str) or not conformance.SHA256_PATTERN.fullmatch(value)
        for value in source_locks.values()
    ):
        raise OverlayError("public_contract_source_digest")
    if contract["review_policy"] != {
        "source": "official_action_table_records",
        "match": "exact_unique_action_identifier",
        "composition": "not_admitted",
        "ambiguous_or_partial_matches": "unavailable_with_reason",
    }:
        raise OverlayError("public_contract_review_policy")
    if contract["coverage"] != {
        "required_rows": conformance.EXPECTED_FEATURE_COUNT,
        "candidate_unverified": EXPECTED_CANDIDATES,
        "unavailable_with_reason": EXPECTED_UNAVAILABLE,
        "runtime_verified": 0,
        "routing_enabled": 0,
    }:
        raise OverlayError("public_contract_coverage")
    mappings = contract["mappings"]
    if not isinstance(mappings, list) or len(mappings) != EXPECTED_CANDIDATES:
        raise OverlayError("public_contract_mapping_count")
    output: dict[str, str] = {}
    last = ""
    proof_keys = MAPPING_KEYS - {"feature_id", "capability_id", "parameter_set_state"}
    for item in mappings:
        mapping = _exact_keys(item, MAPPING_KEYS, "public_contract_mapping_shape")
        feature_id = mapping["feature_id"]
        capability_id = mapping["capability_id"]
        if not isinstance(feature_id, str) or not conformance.FEATURE_ID_PATTERN.fullmatch(
            feature_id
        ) or feature_id <= last or feature_id in output:
            raise OverlayError("public_contract_mapping_order")
        if not isinstance(capability_id, str) or not conformance.CAPABILITY_ID_PATTERN.fullmatch(
            capability_id
        ):
            raise OverlayError("public_contract_mapping_capability")
        if mapping["parameter_set_state"] not in {
            "source_declares_none",
            "documented_candidate",
        }:
            raise OverlayError("public_contract_parameter_state")
        if any(
            not isinstance(mapping[key], str)
            or not conformance.SHA256_PATTERN.fullmatch(mapping[key])
            for key in proof_keys
        ):
            raise OverlayError("public_contract_mapping_digest")
        output[feature_id] = capability_id
        last = feature_id
    if contract["privacy"] != {
        "raw_action_identifiers": False,
        "raw_parameter_identifiers": False,
        "raw_probe_values": False,
        "absolute_private_paths": False,
    }:
        raise OverlayError("public_contract_privacy")
    if contract["not_claimed"] != {
        "runtime_qualification": False,
        "routing_support": False,
        "direct_automation_differential": False,
        "p06_09_complete": False,
        "p06_phase_complete": False,
        "product_complete": False,
    }:
        raise OverlayError("public_contract_nonclaim")
    return output


def validate_public_contract(actual: Any, expected: dict[str, Any]) -> None:
    validate_public_contract_shape(actual)
    validate_public_contract_shape(expected)
    if conformance.canonical_json(actual) != conformance.canonical_json(expected):
        raise OverlayError("public_contract_drift")


def build_current_bundle(root: Path = ROOT) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    parent, records, graph, review, digests = _load_inputs(root)
    contract, table_bindings, selected = build_public_contract(
        parent, records, graph, review, digests
    )
    contract_sha256 = conformance.sha256_bytes(conformance.canonical_json(contract))
    overlay = build_overlay(
        parent, table_bindings, selected, digests, contract_sha256
    )
    projection = conformance.build_automation_projection(
        overlay,
        conformance.sha256_bytes(conformance.canonical_json(overlay)),
    )
    conformance.validate_projection(projection)
    return contract, overlay, projection


def _write_new(path: Path, value: dict[str, Any]) -> None:
    conformance.write_new(path.resolve(), conformance.canonical_json(value))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the fail-closed P06 exact ActionTable binding overlay."
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--contract", default=PUBLIC_CONTRACT)
    parser.add_argument("--bootstrap-contract", action="store_true")
    parser.add_argument("--output-overlay", type=Path)
    parser.add_argument("--output-projection", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve(strict=True)
    contract, overlay, projection = build_current_bundle(root)
    contract_path = Path(args.contract)
    if not contract_path.is_absolute():
        contract_path = root / contract_path
    if args.bootstrap_contract:
        _write_new(contract_path, contract)
    else:
        relative = contract_path.resolve(strict=True).relative_to(root).as_posix()
        actual, _ = _load_json(root, relative, 2 * 1024 * 1024)
        validate_public_contract(actual, contract)
    if args.output_overlay is not None:
        _write_new(args.output_overlay, overlay)
    if args.output_projection is not None:
        _write_new(args.output_projection, projection)
    print(
        "P06_TABLE_AUTOMATION_BINDING_OVERLAY_PASS "
        f"candidate={EXPECTED_CANDIDATES} unavailable={EXPECTED_UNAVAILABLE} "
        "runtime_verified=0 routing_enabled=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
