#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from dataclasses import dataclass
from difflib import SequenceMatcher
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys

from jsonschema import Draft202012Validator, FormatChecker

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from tools.p02.build_candidates import (
    GRAPH_SCHEMA_PATH,
    InputSpec,
    MAX_INPUT_BYTES,
    load_inputs,
    load_source_lock,
    normalize_label,
)
from tools.p02.extract_help import (
    ExtractionError,
    publish_no_overwrite,
    read_regular_file,
    resolve_output,
)
from tools.p02.verify_candidate_graph import verify as verify_candidate_graph

DECISIONS_SCHEMA_PATH = (
    Path(__file__).resolve().parent
    / "schemas"
    / "capability-review-decisions-v1.schema.json"
)
CATALOG_SCHEMA_PATH = (
    Path(__file__).resolve().parent / "schemas" / "reviewed-catalog-v1.schema.json"
)
GENERATOR_ID = "semantic-capability-review-generator"
GENERATOR_VERSION = "0.1.0"
REVIEW_POLICY = "strict_multi_signal_v1"
MAX_GRAPH_BYTES = 64 * 1024 * 1024
MAX_MATRIX_BYTES = 8 * 1024 * 1024
MAX_DECISIONS_BYTES = 8 * 1024 * 1024
SCORE_SCALE = 1_000_000
MIN_COMBINED_SCORE = 800_000
MIN_ACTION_LABEL_SCORE = 350_000
MIN_RUNNER_UP_MARGIN = 80_000
MATRIX_FIELDS = (
    "feature_id",
    "domain",
    "scope_class",
    "feature_ko",
    "capability_id",
    "semantic_operation",
    "document_ir",
    "preferred_backend",
    "fallback_backend",
    "support_level",
    "phase",
    "validation",
    "permission",
    "source_group",
    "notes",
)
IGNORED_REASON_BY_KIND = {
    "help": "documentation_navigation_not_executable_item",
    "webhwp": "documentation_navigation_not_executable_item",
    "xsd": "structural_schema_component_not_standalone_operation",
    "parameter_table": "binding_parameter_metadata_not_standalone_operation",
    "automation_object": "automation_object_metadata_not_standalone_operation",
    "automation_event": "automation_event_signal_not_standalone_operation",
}


@dataclass(frozen=True)
class ReviewConfig:
    source_lock: Path
    inputs: tuple[InputSpec, ...]
    candidate_graph: Path
    candidate_graph_sha256: str
    matrix: Path
    matrix_sha256: str
    expected_matrix_count: int
    decisions: Path
    decisions_sha256: str
    output_root: Path
    output_relative: str


@dataclass(frozen=True)
class Proposal:
    node_id: str
    capability_id: str
    action_label_score_ppm: int
    korean_description_score_ppm: int
    combined_score_ppm: int
    runner_up_margin_ppm: int


def canonical_json(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def validate_sha256(value: str, label: str) -> None:
    if not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ExtractionError(f"{label} expected SHA-256 is malformed")


def parse_json_document(content: bytes, label: str) -> dict:
    try:
        document = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ExtractionError(f"{label} is not valid UTF-8 JSON: {error}") from error
    if not isinstance(document, dict):
        raise ExtractionError(f"{label} root must be an object")
    return document


def schema_errors(document: dict, schema_path: Path) -> list[str]:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return [
        error.message
        for error in Draft202012Validator(
            schema, format_checker=FormatChecker()
        ).iter_errors(document)
    ]


def read_locked_json(path: Path, expected_sha256: str, maximum: int, label: str) -> tuple[bytes, dict]:
    validate_sha256(expected_sha256, label)
    content = read_regular_file(path, maximum)
    actual_sha256 = sha256_bytes(content)
    if actual_sha256 != expected_sha256:
        raise ExtractionError(
            f"{label} SHA-256 mismatch: expected {expected_sha256}, actual {actual_sha256}"
        )
    return content, parse_json_document(content, label)


def load_graph(path: Path, expected_sha256: str) -> tuple[bytes, dict]:
    content, graph = read_locked_json(path, expected_sha256, MAX_GRAPH_BYTES, "candidate graph")
    violations = schema_errors(graph, GRAPH_SCHEMA_PATH)
    if violations:
        raise ExtractionError("candidate graph schema invalid: " + "; ".join(violations[:20]))
    return content, graph


def load_matrix(path: Path, expected_sha256: str, expected_count: int) -> tuple[bytes, list[dict]]:
    validate_sha256(expected_sha256, "canonical matrix")
    if expected_count < 1 or expected_count > 100_000:
        raise ExtractionError("canonical matrix expected row count is invalid")
    content = read_regular_file(path, MAX_MATRIX_BYTES)
    actual_sha256 = sha256_bytes(content)
    if actual_sha256 != expected_sha256:
        raise ExtractionError(
            f"canonical matrix SHA-256 mismatch: expected {expected_sha256}, actual {actual_sha256}"
        )
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ExtractionError(f"canonical matrix is not valid UTF-8 CSV: {error}") from error
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if tuple(reader.fieldnames or ()) != MATRIX_FIELDS:
        raise ExtractionError("canonical matrix headers do not match the fixed contract")
    rows = list(reader)
    if len(rows) != expected_count:
        raise ExtractionError(
            f"canonical matrix row count mismatch: expected {expected_count}, actual {len(rows)}"
        )
    feature_ids: set[str] = set()
    capability_ids: set[str] = set()
    for index, row in enumerate(rows):
        if any(value is None for value in row.values()):
            raise ExtractionError(f"canonical matrix row {index} is malformed")
        feature_id = row["feature_id"]
        capability_id = row["capability_id"]
        if not re.fullmatch(r"[A-Z]+-[0-9]{3}", feature_id):
            raise ExtractionError(f"canonical matrix row {index} has invalid feature_id")
        if not re.fullmatch(r"[a-z][a-z0-9_.-]+", capability_id):
            raise ExtractionError(f"canonical matrix row {index} has invalid capability_id")
        if feature_id in feature_ids or capability_id in capability_ids:
            raise ExtractionError("canonical matrix feature_id/capability_id must be unique")
        if not all(
            row[field]
            for field in (
                "domain",
                "scope_class",
                "feature_ko",
                "semantic_operation",
                "support_level",
            )
        ):
            raise ExtractionError(f"canonical matrix row {index} is missing required semantics")
        if not re.fullmatch(r"(?:P[0-9]{2}|N/A)", row["phase"]):
            raise ExtractionError(f"canonical matrix row {index} has invalid phase")
        if not row["preferred_backend"] and row["support_level"] != "UNSUPPORTED":
            raise ExtractionError(
                f"canonical matrix row {index} lacks a backend outside UNSUPPORTED"
            )
        feature_ids.add(feature_id)
        capability_ids.add(capability_id)
    return content, rows


def load_decisions(
    path: Path,
    expected_sha256: str,
    candidate_graph_sha256: str,
    matrix_sha256: str,
) -> tuple[bytes, dict]:
    content, decisions = read_locked_json(
        path, expected_sha256, MAX_DECISIONS_BYTES, "review decisions"
    )
    violations = schema_errors(decisions, DECISIONS_SCHEMA_PATH)
    if violations:
        raise ExtractionError("review decisions schema invalid: " + "; ".join(violations[:20]))
    if decisions["candidate_graph_sha256"] != candidate_graph_sha256:
        raise ExtractionError("review decisions candidate graph SHA-256 mismatch")
    if decisions["canonical_matrix_sha256"] != matrix_sha256:
        raise ExtractionError("review decisions canonical matrix SHA-256 mismatch")
    node_ids = [item["node_id"] for item in decisions["items"]]
    if len(node_ids) != len(set(node_ids)):
        raise ExtractionError("review decisions contain duplicate node_id")
    return content, decisions


def safe_normalize(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        return ""
    try:
        return normalize_label(value)[0]
    except ExtractionError:
        return ""


def similarity_ppm(left: str, right: str) -> int:
    if not left or not right:
        return 0
    return round(SequenceMatcher(None, left, right, autojunk=False).ratio() * SCORE_SCALE)


def capability_label(capability_id: str) -> str:
    _, separator, suffix = capability_id.partition(".")
    return safe_normalize(suffix if separator else capability_id)


def matrix_is_automation_compatible(row: dict) -> bool:
    return "desktop_automation" in {
        row["preferred_backend"],
        row["fallback_backend"],
    }


def score_action(node: dict, record: dict, matrix_rows: list[dict]) -> tuple[Proposal | None, Proposal | None]:
    action_label = node["normalized_label"]
    description = safe_normalize(record.get("description_ko"))
    ranked: list[tuple[int, int, int, str]] = []
    for row in matrix_rows:
        if not matrix_is_automation_compatible(row):
            continue
        action_score = similarity_ppm(action_label, capability_label(row["capability_id"]))
        korean_score = max(
            similarity_ppm(description, safe_normalize(row["feature_ko"])),
            similarity_ppm(description, safe_normalize(row["semantic_operation"])),
        )
        combined = (7 * action_score + 3 * korean_score + 5) // 10
        ranked.append((combined, action_score, korean_score, row["capability_id"]))
    if not ranked:
        return None, None
    ranked.sort(key=lambda item: (-item[0], -item[1], -item[2], item[3]))
    top = ranked[0]
    runner_up = ranked[1][0] if len(ranked) > 1 else 0
    margin = top[0] - runner_up
    scored = Proposal(
        node_id=node["node_id"],
        capability_id=top[3],
        action_label_score_ppm=top[1],
        korean_description_score_ppm=top[2],
        combined_score_ppm=top[0],
        runner_up_margin_ppm=margin,
    )
    strict = (
        top[0] >= MIN_COMBINED_SCORE
        and top[1] >= MIN_ACTION_LABEL_SCORE
        and margin >= MIN_RUNNER_UP_MARGIN
    )
    return scored, scored if strict else None


def build_proposals(
    graph: dict, records_by_ref: dict[tuple[str, int], dict], matrix_rows: list[dict]
) -> tuple[dict[str, Proposal], dict[str, Proposal]]:
    scores: dict[str, Proposal] = {}
    proposals: dict[str, Proposal] = {}
    for node in graph["nodes"]:
        if node["source_kind"] != "action_table":
            continue
        reference = (node["input_role"], node["input_ordinal"])
        record = records_by_ref.get(reference)
        if record is None or record.get("record_id") != node["record_id"]:
            raise ExtractionError(f"candidate node source record reference is invalid: {node['node_id']}")
        scored, strict = score_action(node, record, matrix_rows)
        if scored is not None:
            scores[node["node_id"]] = scored
        if strict is not None:
            proposals[node["node_id"]] = strict
    return scores, proposals


def validate_review_items(
    decisions: dict,
    graph: dict,
    proposals: dict[str, Proposal],
    matrix_by_capability: dict[str, dict],
) -> dict[str, dict]:
    nodes = {node["node_id"]: node for node in graph["nodes"]}
    items = {item["node_id"]: item for item in decisions["items"]}
    if set(items) != set(proposals):
        missing = sorted(set(proposals) - set(items))
        extra = sorted(set(items) - set(proposals))
        raise ExtractionError(
            f"review decisions must disposition every strict proposal exactly once: missing={len(missing)}, extra={len(extra)}"
        )
    for node_id, item in items.items():
        node = nodes.get(node_id)
        if node is None or node["source_kind"] != "action_table":
            raise ExtractionError(f"review decision references an invalid action node: {node_id}")
        proposal = proposals[node_id]
        if item["status"] == "mapped":
            capability_id = item["capability_id"]
            if capability_id != proposal.capability_id:
                raise ExtractionError(f"review decision does not match strict proposal: {node_id}")
            if capability_id not in matrix_by_capability:
                raise ExtractionError(f"review decision references unknown capability: {capability_id}")
        elif item["reason_code"] != "ambiguous_canonical_semantics":
            raise ExtractionError(f"strict proposal rejection lacks ambiguity reason: {node_id}")
    return items


def semantic_evidence(proposal: Proposal | None, mapped: bool) -> dict:
    return {
        "policy": REVIEW_POLICY,
        "action_label_score_ppm": (
            proposal.action_label_score_ppm if proposal is not None else None
        ),
        "korean_description_score_ppm": (
            proposal.korean_description_score_ppm if proposal is not None else None
        ),
        "combined_score_ppm": proposal.combined_score_ppm if proposal is not None else None,
        "runner_up_margin_ppm": (
            proposal.runner_up_margin_ppm if proposal is not None else None
        ),
        "assertions": (
            [
                "action_identifier",
                "korean_description",
                "backend_compatibility",
                "human_approval",
            ]
            if mapped
            else (["backend_compatibility"] if proposal is not None else [])
        ),
    }


def capability_projection(row: dict) -> dict:
    return {
        field: row[field]
        for field in (
            "feature_id",
            "capability_id",
            "domain",
            "scope_class",
            "support_level",
            "preferred_backend",
            "fallback_backend",
            "phase",
        )
    }


def build_node_dispositions(
    graph: dict,
    scores: dict[str, Proposal],
    proposals: dict[str, Proposal],
    review_items: dict[str, dict],
    matrix_by_capability: dict[str, dict],
) -> list[dict]:
    candidate_refs: dict[str, list[str]] = defaultdict(list)
    for edge in graph["edges"]:
        candidate_refs[edge["left_node_id"]].append(edge["candidate_id"])
        candidate_refs[edge["right_node_id"]].append(edge["candidate_id"])
    dispositions: list[dict] = []
    for node in graph["nodes"]:
        node_id = node["node_id"]
        item = review_items.get(node_id)
        mapped = item is not None and item["status"] == "mapped"
        if mapped:
            reason_code = "strict_multi_signal_semantic_match"
            capability = capability_projection(matrix_by_capability[item["capability_id"]])
        elif item is not None:
            reason_code = item["reason_code"]
            capability = None
        elif node["source_kind"] == "action_table":
            reason_code = "no_strict_canonical_semantic_match"
            capability = None
        else:
            reason_code = IGNORED_REASON_BY_KIND[node["source_kind"]]
            capability = None
        dispositions.append(
            {
                "node_id": node_id,
                "record_id": node["record_id"],
                "source_id": node["source_id"],
                "source_kind": node["source_kind"],
                "candidate_refs": sorted(candidate_refs[node_id]),
                "status": "mapped" if mapped else "ignored_with_reason",
                "reason_code": reason_code,
                "capability": capability,
                "semantic_evidence": semantic_evidence(scores.get(node_id), mapped),
                "runtime_support_state": "unverified",
            }
        )
    return dispositions


def build_edge_dispositions(graph: dict, nodes: list[dict]) -> list[dict]:
    node_by_id = {node["node_id"]: node for node in nodes}
    dispositions: list[dict] = []
    for edge in graph["edges"]:
        left = node_by_id[edge["left_node_id"]]
        right = node_by_id[edge["right_node_id"]]
        left_id = left["capability"]["capability_id"] if left["capability"] else None
        right_id = right["capability"]["capability_id"] if right["capability"] else None
        if left_id is not None and left_id == right_id:
            status = "same_capability_evidence_link"
            reason = "both_nodes_mapped_same_capability_without_merge"
        elif left_id is not None and right_id is not None:
            status = "distinct_capabilities"
            reason = "nodes_mapped_to_distinct_capabilities"
        elif edge["candidate_state"] == "collision_review":
            status = "collision_preserved"
            reason = "candidate_conflict_preserved_without_merge"
        else:
            status = "not_semantically_mapped"
            reason = "one_or_both_nodes_not_semantically_mapped"
        dispositions.append(
            {
                "candidate_id": edge["candidate_id"],
                "left_node_id": edge["left_node_id"],
                "right_node_id": edge["right_node_id"],
                "candidate_state": edge["candidate_state"],
                "status": status,
                "reason_code": reason,
                "left_capability_id": left_id,
                "right_capability_id": right_id,
                "auto_merge": False,
            }
        )
    return dispositions


def count_by_code(values: list[str]) -> list[dict]:
    return [
        {"code": code, "count": count}
        for code, count in sorted(Counter(values).items())
    ]


def build_catalog(
    graph: dict,
    graph_sha256: str,
    matrix_rows: list[dict],
    matrix_sha256: str,
    decisions: dict,
    decisions_sha256: str,
    records_by_ref: dict[tuple[str, int], dict],
) -> dict:
    matrix_by_capability = {row["capability_id"]: row for row in matrix_rows}
    scores, proposals = build_proposals(graph, records_by_ref, matrix_rows)
    review_items = validate_review_items(
        decisions, graph, proposals, matrix_by_capability
    )
    node_dispositions = build_node_dispositions(
        graph, scores, proposals, review_items, matrix_by_capability
    )
    edge_dispositions = build_edge_dispositions(graph, node_dispositions)
    mapped_count = sum(node["status"] == "mapped" for node in node_dispositions)
    ignored_count = len(node_dispositions) - mapped_count
    catalog = {
        "schema_version": "hwpx-agent.reviewed-catalog/v1",
        "source_lock_id": graph["source_lock_id"],
        "generator": {
            "generator_id": GENERATOR_ID,
            "generator_version": GENERATOR_VERSION,
            "review_policy": REVIEW_POLICY,
            "auto_merge": False,
            "runtime_qualification_performed": False,
        },
        "restricted_derivative": graph["restricted_derivative"],
        "candidate_graph": {
            "sha256": graph_sha256,
            "node_count": len(graph["nodes"]),
            "edge_count": len(graph["edges"]),
            "input_sha256": sorted(item["input_sha256"] for item in graph["inputs"]),
        },
        "canonical_matrix": {
            "sha256": matrix_sha256,
            "row_count": len(matrix_rows),
        },
        "review_decisions": {
            "sha256": decisions_sha256,
            **decisions["reviewer"],
            "item_count": len(decisions["items"]),
        },
        "runtime_qualification": {
            "state": "unverified",
            "target_profile_id": None,
            "evidence_refs": [],
        },
        "node_dispositions": node_dispositions,
        "edge_dispositions": edge_dispositions,
        "coverage": {
            "node_count": len(node_dispositions),
            "mapped_node_count": mapped_count,
            "ignored_node_count": ignored_count,
            "unresolved_node_count": 0,
            "node_reason_counts": count_by_code(
                [node["reason_code"] for node in node_dispositions]
            ),
            "edge_count": len(edge_dispositions),
            "disposed_edge_count": len(edge_dispositions),
            "undisposed_edge_count": 0,
            "edge_status_counts": count_by_code(
                [edge["status"] for edge in edge_dispositions]
            ),
            "strict_proposal_count": len(proposals),
            "review_decision_count": len(review_items),
            "runtime_qualified_count": 0,
            "auto_merge_count": 0,
        },
    }
    violations = schema_errors(catalog, CATALOG_SCHEMA_PATH)
    if violations:
        raise ExtractionError("reviewed catalog schema invalid: " + "; ".join(violations[:20]))
    return catalog


def serialize_catalog(catalog: dict) -> bytes:
    return (
        json.dumps(catalog, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def run(config: ReviewConfig) -> dict:
    source_lock_content = read_regular_file(config.source_lock, 8 * 1024 * 1024)
    source_lock_id, source_entries = load_source_lock(config.source_lock)
    loaded_inputs = load_inputs(config.inputs, source_lock_id, source_entries)
    graph_content, graph = load_graph(
        config.candidate_graph, config.candidate_graph_sha256
    )
    graph_verification = verify_candidate_graph(
        config.candidate_graph, config.source_lock, config.inputs
    )
    if graph_verification["errors"]:
        raise ExtractionError(
            "candidate graph independent verification failed: "
            + "; ".join(graph_verification["errors"][:20])
        )
    if graph["source_lock_id"] != source_lock_id:
        raise ExtractionError("candidate graph source_lock_id mismatch")
    matrix_content, matrix_rows = load_matrix(
        config.matrix, config.matrix_sha256, config.expected_matrix_count
    )
    decisions_content, decisions = load_decisions(
        config.decisions,
        config.decisions_sha256,
        config.candidate_graph_sha256,
        config.matrix_sha256,
    )
    records_by_ref = {
        (loaded.role, ordinal): record
        for loaded in loaded_inputs
        for ordinal, record in enumerate(loaded.records)
    }
    catalog = build_catalog(
        graph,
        config.candidate_graph_sha256,
        matrix_rows,
        config.matrix_sha256,
        decisions,
        config.decisions_sha256,
        records_by_ref,
    )
    if catalog["restricted_derivative"] and os.path.normcase(
        str(config.output_root.absolute())
    ) != os.path.normcase(
        str((REPOSITORY_ROOT / "implementation" / "p02" / "evidence").absolute())
    ):
        raise ExtractionError(
            "restricted reviewed catalog may publish only to implementation/p02/evidence"
        )
    for spec, loaded in zip(
        sorted(config.inputs, key=lambda item: item.role), loaded_inputs, strict=True
    ):
        if sha256_bytes(read_regular_file(spec.path, MAX_INPUT_BYTES)) != loaded.sha256:
            raise ExtractionError(f"{spec.role} input changed during semantic review")
    locked_artifacts = (
        (config.source_lock, source_lock_content, 8 * 1024 * 1024, "source lock"),
        (config.candidate_graph, graph_content, MAX_GRAPH_BYTES, "candidate graph"),
        (config.matrix, matrix_content, MAX_MATRIX_BYTES, "canonical matrix"),
        (config.decisions, decisions_content, MAX_DECISIONS_BYTES, "review decisions"),
    )
    for path, original, maximum, label in locked_artifacts:
        if read_regular_file(path, maximum) != original:
            raise ExtractionError(f"{label} changed during semantic review")
    payload = serialize_catalog(catalog)
    output = resolve_output(config.output_root, config.output_relative)
    publish_no_overwrite(output, payload)
    return {
        "schema_version": "hwpx-agent.capability-review-receipt/v1",
        "source_lock_id": source_lock_id,
        "restricted_derivative": catalog["restricted_derivative"],
        "candidate_graph_sha256": config.candidate_graph_sha256,
        "canonical_matrix_sha256": config.matrix_sha256,
        "review_decisions_sha256": config.decisions_sha256,
        "coverage": catalog["coverage"],
        "output_relative": config.output_relative,
        "output_sha256": sha256_bytes(payload),
        "runtime_qualification_performed": False,
        "auto_merge_performed": False,
    }


def parse_input(value: str) -> InputSpec:
    try:
        role, expected_sha256, path = value.split("=", 2)
    except ValueError as error:
        raise argparse.ArgumentTypeError("input must be ROLE=SHA256=PATH") from error
    return InputSpec(role=role, expected_sha256=expected_sha256, path=Path(path))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-lock", type=Path, required=True)
    parser.add_argument("--input", type=parse_input, action="append", required=True)
    parser.add_argument("--candidate-graph", type=Path, required=True)
    parser.add_argument("--candidate-graph-sha256", required=True)
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--matrix-sha256", required=True)
    parser.add_argument("--expected-matrix-count", type=int, required=True)
    parser.add_argument("--decisions", type=Path, required=True)
    parser.add_argument("--decisions-sha256", required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--output-relative", required=True)
    arguments = parser.parse_args()
    try:
        receipt = run(
            ReviewConfig(
                source_lock=arguments.source_lock,
                inputs=tuple(arguments.input),
                candidate_graph=arguments.candidate_graph,
                candidate_graph_sha256=arguments.candidate_graph_sha256,
                matrix=arguments.matrix,
                matrix_sha256=arguments.matrix_sha256,
                expected_matrix_count=arguments.expected_matrix_count,
                decisions=arguments.decisions,
                decisions_sha256=arguments.decisions_sha256,
                output_root=arguments.output_root,
                output_relative=arguments.output_relative,
            )
        )
    except ExtractionError as error:
        print(
            json.dumps({"state": "failed", "error": str(error)}, ensure_ascii=False),
            file=sys.stderr,
        )
        return 1
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
