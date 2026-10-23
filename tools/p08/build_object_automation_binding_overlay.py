from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
ACTION_RECORDS = Path("implementation/p02/evidence/automation/automation-pdf.records.v1.json")
CANDIDATE_GRAPH = Path("implementation/p02/evidence/candidates/candidate-graph.v1.json")
CATALOG = Path("specs/feature-coverage-matrix.json")
NEGATIVE_QUALIFICATION = Path(
    "implementation/p08/evidence/"
    "p08-21-aspect-lock-negative-qualification.current-2020.v1.json"
)
PRIVATE_REVIEW = Path("implementation/p02/evidence/p08-object-automation-binding-review.v1.json")
PUBLIC_CONTRACT = Path("protocol/private/p08-object-automation-binding-overlay-v1.json")
PRIVATE_OVERLAY = Path(
    "implementation/p02/evidence/bindings/"
    "p08-object-automation-binding-overlay.2020.v1.json"
)
PUBLIC_PROJECTION = Path("implementation/p08/p08-09-current-2020-automation-projection.json")

REVIEW_SCHEMA = "hwpx-agent.p08-object-automation-binding-review-private/v1"
CONTRACT_SCHEMA = "hwpx-agent.p08-object-automation-binding-overlay-contract/v1"
OVERLAY_SCHEMA = "hwpx-agent.p08-object-automation-binding-overlay/v1"
PROJECTION_SCHEMA = "hwpx-agent.p08-object-automation-projection/v1"
EXPECTED_P08_ROWS = 42
EXPECTED_P08_CANDIDATES = 40
EXPECTED_P08_UNAVAILABLE = 2
P11_CANDIDATES = {
    "OBJ-006", "OBJ-049", "OBJ-050", "OBJ-051", "OBJ-052",
    "OBJ-053", "OBJ-054", "OBJ-055", "OBJ-056",
}
POLICY_DENIALS = {"OBJ-011", "OBJ-057"}
EXPECTED_UNAVAILABLE = {
    "OBJ-004", "OBJ-005", "OBJ-008", "OBJ-009", "OBJ-044", "OBJ-046", "OBJ-058",
}
FEATURE_PATTERN = re.compile(r"OBJ-[0-9]{3}\Z")
DIGEST_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
MAPPING_MODES = {
    "exact_action",
    "exact_method",
    "exact_action_negative_state",
    "reviewed_parameterized_action",
    "reviewed_context_action",
    "reviewed_composite_route",
}
MODAL_RISKS = {"none_expected", "must_probe", "known_modal", "not_applicable"}
TARGET = {
    "profile_id": "hancom-hangul-2020-secondary",
    "product": "Hancom Hangul 2020",
    "build": "11.0.0.9136",
    "locale": "ko-KR",
    "architecture": "x86",
    "scope": "current_pc_personal_local_development",
}


class OverlayError(ValueError):
    pass


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise OverlayError(f"duplicate_json_key:{key}")
        value[key] = item
    return value


def _load(path: Path, maximum: int, *, root: Path = ROOT) -> tuple[Any, str]:
    data = (root / path).read_bytes()
    if not data or len(data) > maximum:
        raise OverlayError(f"json_size:{path.as_posix()}")
    digest = hashlib.sha256(data).hexdigest()
    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise OverlayError(f"invalid_json:{path.as_posix()}") from error
    return value, digest


def _exact_keys(value: Any, expected: set[str], context: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != expected:
        raise OverlayError(f"shape_drift:{context}")
    return value


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _digest_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _digest_json(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)[:-1]).hexdigest()


def _p08_rows(catalog: Any) -> list[dict[str, Any]]:
    if not isinstance(catalog, list):
        raise OverlayError("catalog_shape")
    rows = [row for row in catalog if isinstance(row, dict) and row.get("phase") == "P08"]
    if len(rows) != EXPECTED_P08_ROWS:
        raise OverlayError("catalog_p08_count")
    ids = [row.get("feature_id") for row in rows]
    if ids != sorted(ids) or any(not isinstance(item, str) or not FEATURE_PATTERN.fullmatch(item) for item in ids):
        raise OverlayError("catalog_p08_order")
    return rows


def _source_records(records: Any) -> dict[tuple[str, str], dict[str, Any]]:
    if not isinstance(records, list) or len(records) > 10_000:
        raise OverlayError("source_records_shape")
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for record in records:
        if not isinstance(record, dict):
            raise OverlayError("source_record_shape")
        kind = record.get("source_kind")
        name = record.get("original_name")
        if kind in {"action_table", "automation_object"} and isinstance(name, str):
            grouped.setdefault((kind, name), []).append(record)
    return {
        identity: matches[0]
        for identity, matches in grouped.items()
        if len(matches) == 1
    }


def _nodes(graph: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(graph, dict) or graph.get("schema_version") != "hwpx-agent.candidate-graph/v1":
        raise OverlayError("candidate_graph_shape")
    values = graph.get("nodes")
    if not isinstance(values, list):
        raise OverlayError("candidate_graph_nodes")
    grouped: dict[str, list[dict[str, Any]]] = {}
    for node in values:
        if not isinstance(node, dict):
            raise OverlayError("candidate_node_shape")
        record_id = node.get("record_id")
        if isinstance(record_id, str):
            grouped.setdefault(record_id, []).append(node)
    return {record_id: nodes[0] for record_id, nodes in grouped.items() if len(nodes) == 1}


def _validate_review(
    review: Any,
    rows: list[dict[str, Any]],
    source_locks: dict[str, str],
) -> list[dict[str, Any]]:
    value = _exact_keys(review, {"schema_version", "source_locks", "review_policy", "items"}, "review")
    if value["schema_version"] != REVIEW_SCHEMA or value["source_locks"] != source_locks:
        raise OverlayError("review_identity_or_source_locks")
    if value["review_policy"] != {
        "match": "exact_unique_official_record",
        "shared_source": "feature_specific_parameter_or_context_probe_required",
        "modal_route": "source_candidate_only_until_isolated_runtime_probe",
        "runtime_qualification": "not_run",
        "routing_enabled": False,
    }:
        raise OverlayError("review_policy")
    items = value["items"]
    if not isinstance(items, list) or len(items) != EXPECTED_P08_ROWS:
        raise OverlayError("review_count")
    expected_ids = [row["feature_id"] for row in rows]
    if [item.get("feature_id") if isinstance(item, dict) else None for item in items] != expected_ids:
        raise OverlayError("review_order")
    catalog_by_id = {row["feature_id"]: row for row in rows}
    counts: Counter[str] = Counter()
    for item in items:
        entry = _exact_keys(
            item,
            {
                "feature_id", "capability_id", "state", "source_kind", "source_name",
                "mapping_mode", "modal_risk", "unavailable_reason",
            },
            "review_item",
        )
        feature_id = entry["feature_id"]
        if catalog_by_id[feature_id].get("capability_id") != entry["capability_id"]:
            raise OverlayError("review_capability")
        if entry["modal_risk"] not in MODAL_RISKS:
            raise OverlayError("review_modal_risk")
        state = entry["state"]
        counts[state] += 1
        if state == "candidate_unverified":
            if (
                entry["source_kind"] not in {"action_table", "automation_object"}
                or not isinstance(entry["source_name"], str)
                or not entry["source_name"]
                or entry["mapping_mode"] not in MAPPING_MODES
                or entry["modal_risk"] == "not_applicable"
                or entry["unavailable_reason"] is not None
            ):
                raise OverlayError("review_candidate")
        elif state == "unavailable_with_reason":
            if (
                entry["source_kind"] is not None
                or entry["source_name"] is not None
                or entry["mapping_mode"] is not None
                or entry["modal_risk"] != "not_applicable"
                or not isinstance(entry["unavailable_reason"], str)
                or not entry["unavailable_reason"]
            ):
                raise OverlayError("review_unavailable")
        else:
            raise OverlayError("review_state")
    if counts != Counter({"candidate_unverified": 40, "unavailable_with_reason": 2}):
        raise OverlayError("review_coverage")
    if {item["feature_id"] for item in items if item["state"] == "unavailable_with_reason"} != {"OBJ-044", "OBJ-046"}:
        raise OverlayError("review_unavailable_set")
    return items


def build_bundle(
    *,
    root: Path = ROOT,
    review_override: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    records, records_sha = _load(ACTION_RECORDS, 8 * 1024 * 1024, root=root)
    graph, graph_sha = _load(CANDIDATE_GRAPH, 8 * 1024 * 1024, root=root)
    catalog, catalog_sha = _load(CATALOG, 16 * 1024 * 1024, root=root)
    _, negative_sha = _load(NEGATIVE_QUALIFICATION, 1024 * 1024, root=root)
    review, review_sha = _load(PRIVATE_REVIEW, 1024 * 1024, root=root)
    if review_override is not None:
        review = review_override
    source_locks = {
        "action_records_sha256": records_sha,
        "candidate_graph_sha256": graph_sha,
        "canonical_matrix_sha256": catalog_sha,
        "aspect_lock_negative_qualification_sha256": negative_sha,
    }
    rows = _p08_rows(catalog)
    items = _validate_review(review, rows, source_locks)
    records_by_identity = _source_records(records)
    nodes_by_record = _nodes(graph)

    public_mappings: list[dict[str, Any]] = []
    public_unavailable: list[dict[str, Any]] = []
    private_routes: list[dict[str, Any]] = []
    for item in items:
        if item["state"] == "unavailable_with_reason":
            public_unavailable.append(
                {
                    "feature_id": item["feature_id"],
                    "capability_id": item["capability_id"],
                    "reason": item["unavailable_reason"],
                }
            )
            private_routes.append(dict(item))
            continue
        identity = (item["source_kind"], item["source_name"])
        record = records_by_identity.get(identity)
        if record is None:
            raise OverlayError(f"official_record_not_unique:{item['feature_id']}")
        record_id = record.get("record_id")
        node = nodes_by_record.get(record_id) if isinstance(record_id, str) else None
        if node is None:
            raise OverlayError(f"candidate_node_not_unique:{item['feature_id']}")
        for key in ("source_id", "source_sha256", "source_kind"):
            if node.get(key) != record.get(key):
                raise OverlayError(f"candidate_node_source_mismatch:{item['feature_id']}")
        if not isinstance(record.get("source_sha256"), str) or not DIGEST_PATTERN.fullmatch(record["source_sha256"]):
            raise OverlayError("official_source_digest")
        mapping = {
            "feature_id": item["feature_id"],
            "capability_id": item["capability_id"],
            "source_kind": item["source_kind"],
            "mapping_mode": item["mapping_mode"],
            "modal_risk": item["modal_risk"],
            "source_name_sha256": _digest_text(item["source_name"]),
            "record_id_sha256": _digest_text(record_id),
            "node_id_sha256": _digest_text(node["node_id"]),
            "record_sha256": _digest_json(record),
        }
        public_mappings.append(mapping)
        route = dict(item)
        route.update(
            {
                "record_id": record_id,
                "node_id": node["node_id"],
                "source_id": record["source_id"],
                "source_sha256": record["source_sha256"],
                "runtime_support_state": "unverified",
                "routing_enabled": False,
            }
        )
        private_routes.append(route)

    modal_counts = Counter(item["modal_risk"] for item in items if item["state"] == "candidate_unverified")
    contract = {
        "schema_version": CONTRACT_SCHEMA,
        "target": TARGET,
        "source_locks": {**source_locks, "private_review_sha256": review_sha},
        "review_policy": {
            "source": "pinned_official_action_parameter_and_automation_records",
            "match": "exact_unique_record_and_candidate_graph_node",
            "shared_source": "feature_specific_runtime_probe_required",
            "known_modal": "excluded_from_unattended_batch_until_isolated_probe",
        },
        "coverage": {
            "p08_rows": EXPECTED_P08_ROWS,
            "candidate_unverified": EXPECTED_P08_CANDIDATES,
            "unavailable_with_reason": EXPECTED_P08_UNAVAILABLE,
            "runtime_verified": 0,
            "routing_enabled": 0,
            "modal_risk_counts": {
                "none_expected": modal_counts["none_expected"],
                "must_probe": modal_counts["must_probe"],
                "known_modal": modal_counts["known_modal"],
            },
        },
        "mappings": public_mappings,
        "unavailable": public_unavailable,
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
            "p08_complete": False,
            "production_ready": False,
            "product_complete": False,
        },
    }
    contract_sha = hashlib.sha256(_canonical_bytes(contract)).hexdigest()
    overlay = {
        "schema_version": OVERLAY_SCHEMA,
        "target": TARGET,
        "source_locks": contract["source_locks"],
        "public_contract_sha256": contract_sha,
        "coverage": contract["coverage"],
        "runtime_qualification": {"state": "not_run", "verified": 0, "failed": 0},
        "routing_enabled": False,
        "routes": private_routes,
    }

    p08_candidates = {item["feature_id"] for item in items if item["state"] == "candidate_unverified"}
    all_ids = {f"OBJ-{number:03d}" for number in range(1, 59)}
    candidates = p08_candidates | P11_CANDIDATES
    unavailable = all_ids - candidates - POLICY_DENIALS
    if unavailable != EXPECTED_UNAVAILABLE or len(candidates) != 49:
        raise OverlayError("projection_coverage")
    projection = {
        "schema_version": PROJECTION_SCHEMA,
        "target_profile_id": TARGET["profile_id"],
        "candidate_unverified": sorted(candidates),
        "denied_by_policy": sorted(POLICY_DENIALS),
        "runtime_support_state": "unverified",
        "routing_enabled": False,
        "differential_state": "not_run",
        "actual_target_profile": False,
        "raw_action_identifiers": False,
        "raw_parameter_identifiers": False,
    }
    return contract, overlay, projection


def _write(path: Path, value: Any, *, root: Path = ROOT, new_only: bool = False) -> None:
    absolute = root / path
    absolute.parent.mkdir(parents=True, exist_ok=True)
    if new_only and absolute.exists():
        raise OverlayError(f"output_exists:{path.as_posix()}")
    absolute.write_bytes(_canonical_bytes(value))


def main() -> int:
    parser = argparse.ArgumentParser(description="Build or verify the P08 object automation source overlay")
    parser.add_argument("--bootstrap-contract", action="store_true")
    parser.add_argument("--write-overlay", action="store_true")
    parser.add_argument("--write-projection", action="store_true")
    args = parser.parse_args()
    try:
        contract, overlay, projection = build_bundle()
        if args.bootstrap_contract:
            _write(PUBLIC_CONTRACT, contract, new_only=True)
        else:
            actual, _ = _load(PUBLIC_CONTRACT, 2 * 1024 * 1024)
            if actual != contract:
                raise OverlayError("public_contract_drift")
        if args.write_overlay:
            _write(PRIVATE_OVERLAY, overlay)
        if args.write_projection:
            raise OverlayError("projection_superseded_by_p08_25")
    except (OverlayError, OSError) as error:
        print(json.dumps({"state": "fail", "error": str(error)}, sort_keys=True))
        return 1
    print(json.dumps({
        "state": "pass",
        "p08_rows": 42,
        "candidate_unverified": 40,
        "unavailable_with_reason": 2,
        "all_matrix_candidates": 49,
        "runtime_verified": 0,
        "routing_enabled": 0,
        "differential": "not_run",
    }, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
