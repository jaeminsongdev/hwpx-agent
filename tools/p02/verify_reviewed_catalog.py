#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from difflib import SequenceMatcher
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import unicodedata

from jsonschema import Draft202012Validator, FormatChecker

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from tools.p02.build_candidates import GRAPH_SCHEMA_PATH, InputSpec, MAX_INPUT_BYTES
from tools.p02.extract_help import ExtractionError, read_regular_file
from tools.p02.review_capabilities import (
    CATALOG_SCHEMA_PATH,
    DECISIONS_SCHEMA_PATH,
    MATRIX_FIELDS,
    MAX_DECISIONS_BYTES,
    MAX_GRAPH_BYTES,
    MAX_MATRIX_BYTES,
    MIN_ACTION_LABEL_SCORE,
    MIN_COMBINED_SCORE,
    MIN_RUNNER_UP_MARGIN,
    SCORE_SCALE,
)
from tools.p02.verify_candidate_graph import verify as verify_candidate_graph

SHORTCUT_SUFFIX = re.compile(
    r"(?:\s*\(&[A-Za-z0-9]\)|\s+(?:(?:Ctrl|Alt|Shift)\+)+[A-Za-z0-9]+)\s*$",
    re.IGNORECASE,
)
CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
IGNORED_REASON_BY_KIND = {
    "help": "documentation_navigation_not_executable_item",
    "webhwp": "documentation_navigation_not_executable_item",
    "xsd": "structural_schema_component_not_standalone_operation",
    "parameter_table": "binding_parameter_metadata_not_standalone_operation",
    "automation_object": "automation_object_metadata_not_standalone_operation",
    "automation_event": "automation_event_signal_not_standalone_operation",
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def independent_normalize(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        return ""
    if "\t" in value:
        value = value.split("\t", 1)[0]
    value = SHORTCUT_SUFFIX.sub("", unicodedata.normalize("NFC", value))
    if any(unicodedata.category(character) in {"Cc", "Cf", "Cs"} for character in value):
        return ""
    value = CAMEL_BOUNDARY.sub(" ", value).casefold()
    normalized = "".join(
        character if unicodedata.category(character)[0] in {"L", "M", "N"} else " "
        for character in value
    )
    return " ".join(normalized.split())


def similarity_ppm(left: str, right: str) -> int:
    if not left or not right:
        return 0
    return round(SequenceMatcher(None, left, right, autojunk=False).ratio() * SCORE_SCALE)


def independent_score(node: dict, record: dict, rows: list[dict]) -> dict | None:
    ranked: list[tuple[int, int, int, str]] = []
    description = independent_normalize(record.get("description_ko"))
    for row in rows:
        if "desktop_automation" not in {
            row["preferred_backend"],
            row["fallback_backend"],
        }:
            continue
        suffix = row["capability_id"].partition(".")[2] or row["capability_id"]
        action = similarity_ppm(
            node["normalized_label"], independent_normalize(suffix)
        )
        korean = max(
            similarity_ppm(description, independent_normalize(row["feature_ko"])),
            similarity_ppm(
                description, independent_normalize(row["semantic_operation"])
            ),
        )
        combined = (7 * action + 3 * korean + 5) // 10
        ranked.append((combined, action, korean, row["capability_id"]))
    if not ranked:
        return None
    ranked.sort(key=lambda item: (-item[0], -item[1], -item[2], item[3]))
    top = ranked[0]
    margin = top[0] - (ranked[1][0] if len(ranked) > 1 else 0)
    return {
        "capability_id": top[3],
        "action_label_score_ppm": top[1],
        "korean_description_score_ppm": top[2],
        "combined_score_ppm": top[0],
        "runner_up_margin_ppm": margin,
        "strict": (
            top[0] >= MIN_COMBINED_SCORE
            and top[1] >= MIN_ACTION_LABEL_SCORE
            and margin >= MIN_RUNNER_UP_MARGIN
        ),
    }


def parse_json(content: bytes, label: str, errors: list[str]) -> dict:
    try:
        value = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        errors.append(f"{label} is not valid UTF-8 JSON: {error}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{label} root is not an object")
        return {}
    return value


def validate_document(document: dict, schema_path: Path, label: str, errors: list[str]) -> None:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    for violation in Draft202012Validator(
        schema, format_checker=FormatChecker()
    ).iter_errors(document):
        errors.append(f"{label} schema: {violation.message}")


def read_matrix(content: bytes, expected_count: int, errors: list[str]) -> list[dict]:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        errors.append(f"canonical matrix is not valid UTF-8: {error}")
        return []
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if tuple(reader.fieldnames or ()) != MATRIX_FIELDS:
        errors.append("canonical matrix header mismatch")
    rows = list(reader)
    if len(rows) != expected_count:
        errors.append(
            f"canonical matrix row count mismatch: expected {expected_count}, actual {len(rows)}"
        )
    feature_ids = [row.get("feature_id") for row in rows]
    capability_ids = [row.get("capability_id") for row in rows]
    if len(feature_ids) != len(set(feature_ids)) or len(capability_ids) != len(
        set(capability_ids)
    ):
        errors.append("canonical matrix identifiers are not unique")
    for index, row in enumerate(rows):
        feature_id = str(row.get("feature_id", ""))
        capability_id = str(row.get("capability_id", ""))
        if not re.fullmatch(r"[A-Z]+-[0-9]{3}", feature_id):
            errors.append(f"canonical matrix feature_id invalid at row {index}")
        if not re.fullmatch(r"[a-z][a-z0-9_.-]+", capability_id):
            errors.append(f"canonical matrix capability_id invalid at row {index}")
        if not all(
            row.get(field)
            for field in (
                "domain",
                "scope_class",
                "feature_ko",
                "semantic_operation",
                "support_level",
            )
        ):
            errors.append(f"canonical matrix semantics missing at row {index}")
        if not re.fullmatch(r"(?:P[0-9]{2}|N/A)", str(row.get("phase", ""))):
            errors.append(f"canonical matrix phase invalid at row {index}")
        if not row.get("preferred_backend") and row.get("support_level") != "UNSUPPORTED":
            errors.append(f"canonical matrix backend missing at row {index}")
    return rows


def expected_evidence(score: dict | None, mapped: bool) -> dict:
    return {
        "policy": "strict_multi_signal_v1",
        "action_label_score_ppm": (
            score["action_label_score_ppm"] if score is not None else None
        ),
        "korean_description_score_ppm": (
            score["korean_description_score_ppm"] if score is not None else None
        ),
        "combined_score_ppm": score["combined_score_ppm"] if score is not None else None,
        "runner_up_margin_ppm": (
            score["runner_up_margin_ppm"] if score is not None else None
        ),
        "assertions": (
            [
                "action_identifier",
                "korean_description",
                "backend_compatibility",
                "human_approval",
            ]
            if mapped
            else (["backend_compatibility"] if score is not None else [])
        ),
    }


def projection(row: dict) -> dict:
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


def count_by_code(values: list[str]) -> list[dict]:
    return [
        {"code": code, "count": count}
        for code, count in sorted(Counter(values).items())
    ]


def verify(
    output_path: Path,
    source_lock_path: Path,
    specs: tuple[InputSpec, ...],
    candidate_graph_path: Path,
    candidate_graph_sha256: str,
    matrix_path: Path,
    matrix_sha256: str,
    expected_matrix_count: int,
    decisions_path: Path,
    decisions_sha256: str,
) -> dict:
    errors: list[str] = []
    output_content = read_regular_file(output_path, 128 * 1024 * 1024)
    catalog = parse_json(output_content, "reviewed catalog", errors)
    if catalog:
        validate_document(catalog, CATALOG_SCHEMA_PATH, "reviewed catalog", errors)

    graph_content = read_regular_file(candidate_graph_path, MAX_GRAPH_BYTES)
    if sha256_bytes(graph_content) != candidate_graph_sha256:
        errors.append("candidate graph SHA-256 mismatch")
    graph = parse_json(graph_content, "candidate graph", errors)
    if graph:
        validate_document(graph, GRAPH_SCHEMA_PATH, "candidate graph", errors)
    graph_result = verify_candidate_graph(candidate_graph_path, source_lock_path, specs)
    errors.extend(f"candidate graph: {error}" for error in graph_result["errors"])

    matrix_content = read_regular_file(matrix_path, MAX_MATRIX_BYTES)
    if sha256_bytes(matrix_content) != matrix_sha256:
        errors.append("canonical matrix SHA-256 mismatch")
    rows = read_matrix(matrix_content, expected_matrix_count, errors)
    matrix_by_capability = {
        str(row.get("capability_id")): row
        for row in rows
        if isinstance(row.get("capability_id"), str)
    }

    decisions_content = read_regular_file(decisions_path, MAX_DECISIONS_BYTES)
    if sha256_bytes(decisions_content) != decisions_sha256:
        errors.append("review decisions SHA-256 mismatch")
    decisions = parse_json(decisions_content, "review decisions", errors)
    if decisions:
        validate_document(decisions, DECISIONS_SCHEMA_PATH, "review decisions", errors)
        if decisions.get("candidate_graph_sha256") != candidate_graph_sha256:
            errors.append("review decisions candidate graph reference mismatch")
        if decisions.get("canonical_matrix_sha256") != matrix_sha256:
            errors.append("review decisions matrix reference mismatch")

    records_by_ref: dict[tuple[str, int], dict] = {}
    input_hashes: list[str] = []
    for spec in sorted(specs, key=lambda item: item.role):
        content = read_regular_file(spec.path, MAX_INPUT_BYTES)
        actual = sha256_bytes(content)
        input_hashes.append(actual)
        if actual != spec.expected_sha256:
            errors.append(f"{spec.role} source-record SHA-256 mismatch")
        try:
            records = json.loads(content.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            errors.append(f"{spec.role} source records invalid: {error}")
            records = []
        if not isinstance(records, list):
            errors.append(f"{spec.role} source records root is not an array")
            records = []
        for ordinal, record in enumerate(records):
            if isinstance(record, dict):
                records_by_ref[(spec.role, ordinal)] = record

    if errors and (not graph or not catalog or not decisions or not rows):
        return {
            "schema_version": "hwpx-agent.reviewed-catalog-verification/v1",
            "errors": errors,
            "output_sha256": sha256_bytes(output_content),
        }

    graph_nodes = {node["node_id"]: node for node in graph.get("nodes", [])}
    graph_edges = {edge["candidate_id"]: edge for edge in graph.get("edges", [])}
    scores: dict[str, dict] = {}
    strict: dict[str, dict] = {}
    for node in graph_nodes.values():
        if node["source_kind"] != "action_table":
            continue
        record = records_by_ref.get((node["input_role"], node["input_ordinal"]))
        if record is None or record.get("record_id") != node["record_id"]:
            errors.append(f"node source reference mismatch: {node['node_id']}")
            continue
        score = independent_score(node, record, rows)
        if score is not None:
            scores[node["node_id"]] = score
            if score["strict"]:
                strict[node["node_id"]] = score

    items_list = decisions.get("items", [])
    items = {
        item.get("node_id"): item for item in items_list if isinstance(item, dict)
    }
    if len(items) != len(items_list):
        errors.append("review decisions contain duplicate or malformed node IDs")
    if set(items) != set(strict):
        errors.append("review decisions do not exactly cover strict proposals")
    for node_id, item in items.items():
        score = strict.get(str(node_id))
        if score is None:
            continue
        if item.get("status") == "mapped":
            if item.get("capability_id") != score["capability_id"]:
                errors.append(f"mapped decision differs from strict proposal: {node_id}")
        elif item.get("reason_code") != "ambiguous_canonical_semantics":
            errors.append(f"rejected strict proposal lacks ambiguity reason: {node_id}")

    dispositions_list = catalog.get("node_dispositions", [])
    dispositions = {
        item.get("node_id"): item
        for item in dispositions_list
        if isinstance(item, dict)
    }
    if len(dispositions) != len(dispositions_list):
        errors.append("node dispositions contain duplicate or malformed node IDs")
    if set(dispositions) != set(graph_nodes):
        errors.append("node dispositions do not exactly cover graph nodes")

    refs: dict[str, list[str]] = defaultdict(list)
    for edge in graph_edges.values():
        refs[edge["left_node_id"]].append(edge["candidate_id"])
        refs[edge["right_node_id"]].append(edge["candidate_id"])
    for node_id, node in graph_nodes.items():
        disposition = dispositions.get(node_id)
        if disposition is None:
            continue
        for field in ("record_id", "source_id", "source_kind"):
            if disposition.get(field) != node[field]:
                errors.append(f"node disposition source field mismatch: {node_id}/{field}")
        if disposition.get("candidate_refs") != sorted(refs[node_id]):
            errors.append(f"node disposition candidate refs mismatch: {node_id}")
        item = items.get(node_id)
        mapped = item is not None and item.get("status") == "mapped"
        if mapped:
            expected_status = "mapped"
            expected_reason = "strict_multi_signal_semantic_match"
            row = matrix_by_capability.get(str(item.get("capability_id")))
            expected_capability = projection(row) if row is not None else None
        elif item is not None:
            expected_status = "ignored_with_reason"
            expected_reason = "ambiguous_canonical_semantics"
            expected_capability = None
        elif node["source_kind"] == "action_table":
            expected_status = "ignored_with_reason"
            expected_reason = "no_strict_canonical_semantic_match"
            expected_capability = None
        else:
            expected_status = "ignored_with_reason"
            expected_reason = IGNORED_REASON_BY_KIND.get(node["source_kind"])
            expected_capability = None
        expected_values = {
            "status": expected_status,
            "reason_code": expected_reason,
            "capability": expected_capability,
            "semantic_evidence": expected_evidence(scores.get(node_id), mapped),
            "runtime_support_state": "unverified",
        }
        for field, expected in expected_values.items():
            if disposition.get(field) != expected:
                errors.append(f"node disposition mismatch: {node_id}/{field}")

    edge_list = catalog.get("edge_dispositions", [])
    edge_dispositions = {
        item.get("candidate_id"): item for item in edge_list if isinstance(item, dict)
    }
    if len(edge_dispositions) != len(edge_list):
        errors.append("edge dispositions contain duplicate or malformed candidate IDs")
    if set(edge_dispositions) != set(graph_edges):
        errors.append("edge dispositions do not exactly cover candidate edges")
    for candidate_id, edge in graph_edges.items():
        disposition = edge_dispositions.get(candidate_id)
        if disposition is None:
            continue
        left = dispositions.get(edge["left_node_id"], {})
        right = dispositions.get(edge["right_node_id"], {})
        left_cap = (
            left.get("capability", {}).get("capability_id")
            if isinstance(left.get("capability"), dict)
            else None
        )
        right_cap = (
            right.get("capability", {}).get("capability_id")
            if isinstance(right.get("capability"), dict)
            else None
        )
        if left_cap is not None and left_cap == right_cap:
            status = "same_capability_evidence_link"
            reason = "both_nodes_mapped_same_capability_without_merge"
        elif left_cap is not None and right_cap is not None:
            status = "distinct_capabilities"
            reason = "nodes_mapped_to_distinct_capabilities"
        elif edge["candidate_state"] == "collision_review":
            status = "collision_preserved"
            reason = "candidate_conflict_preserved_without_merge"
        else:
            status = "not_semantically_mapped"
            reason = "one_or_both_nodes_not_semantically_mapped"
        expected = {
            "candidate_id": candidate_id,
            "left_node_id": edge["left_node_id"],
            "right_node_id": edge["right_node_id"],
            "candidate_state": edge["candidate_state"],
            "status": status,
            "reason_code": reason,
            "left_capability_id": left_cap,
            "right_capability_id": right_cap,
            "auto_merge": False,
        }
        if disposition != expected:
            errors.append(f"edge disposition mismatch: {candidate_id}")

    mapped_count = sum(
        item.get("status") == "mapped" for item in dispositions_list if isinstance(item, dict)
    )
    expected_coverage = {
        "node_count": len(graph_nodes),
        "mapped_node_count": mapped_count,
        "ignored_node_count": len(graph_nodes) - mapped_count,
        "unresolved_node_count": 0,
        "node_reason_counts": count_by_code(
            [str(item.get("reason_code")) for item in dispositions_list if isinstance(item, dict)]
        ),
        "edge_count": len(graph_edges),
        "disposed_edge_count": len(graph_edges),
        "undisposed_edge_count": 0,
        "edge_status_counts": count_by_code(
            [str(item.get("status")) for item in edge_list if isinstance(item, dict)]
        ),
        "strict_proposal_count": len(strict),
        "review_decision_count": len(items),
        "runtime_qualified_count": 0,
        "auto_merge_count": 0,
    }
    if catalog.get("coverage") != expected_coverage:
        errors.append("reviewed catalog coverage mismatch")

    expected_top = {
        "source_lock_id": graph.get("source_lock_id"),
        "restricted_derivative": graph.get("restricted_derivative"),
        "candidate_graph": {
            "sha256": candidate_graph_sha256,
            "node_count": len(graph_nodes),
            "edge_count": len(graph_edges),
            "input_sha256": sorted(input_hashes),
        },
        "canonical_matrix": {
            "sha256": matrix_sha256,
            "row_count": len(rows),
        },
        "review_decisions": {
            "sha256": decisions_sha256,
            **decisions.get("reviewer", {}),
            "item_count": len(items_list),
        },
        "runtime_qualification": {
            "state": "unverified",
            "target_profile_id": None,
            "evidence_refs": [],
        },
    }
    for field, expected in expected_top.items():
        if catalog.get(field) != expected:
            errors.append(f"reviewed catalog top-level mismatch: {field}")
    if catalog.get("generator") != {
        "generator_id": "semantic-capability-review-generator",
        "generator_version": "0.1.0",
        "review_policy": "strict_multi_signal_v1",
        "auto_merge": False,
        "runtime_qualification_performed": False,
    }:
        errors.append("reviewed catalog generator contract mismatch")

    return {
        "schema_version": "hwpx-agent.reviewed-catalog-verification/v1",
        "errors": errors,
        "output_sha256": sha256_bytes(output_content),
        "candidate_graph_sha256": sha256_bytes(graph_content),
        "canonical_matrix_sha256": sha256_bytes(matrix_content),
        "review_decisions_sha256": sha256_bytes(decisions_content),
        "node_count": len(dispositions_list),
        "mapped_node_count": mapped_count,
        "ignored_node_count": len(dispositions_list) - mapped_count,
        "edge_count": len(edge_list),
        "strict_proposal_count": len(strict),
        "runtime_qualified_count": 0,
        "auto_merge_count": 0,
    }


def parse_input(value: str) -> InputSpec:
    try:
        role, expected_sha256, path = value.split("=", 2)
    except ValueError as error:
        raise argparse.ArgumentTypeError("input must be ROLE=SHA256=PATH") from error
    return InputSpec(role=role, expected_sha256=expected_sha256, path=Path(path))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-lock", type=Path, required=True)
    parser.add_argument("--input", type=parse_input, action="append", required=True)
    parser.add_argument("--candidate-graph", type=Path, required=True)
    parser.add_argument("--candidate-graph-sha256", required=True)
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--matrix-sha256", required=True)
    parser.add_argument("--expected-matrix-count", type=int, required=True)
    parser.add_argument("--decisions", type=Path, required=True)
    parser.add_argument("--decisions-sha256", required=True)
    arguments = parser.parse_args()
    try:
        result = verify(
            arguments.output,
            arguments.source_lock,
            tuple(arguments.input),
            arguments.candidate_graph,
            arguments.candidate_graph_sha256,
            arguments.matrix,
            arguments.matrix_sha256,
            arguments.expected_matrix_count,
            arguments.decisions,
            arguments.decisions_sha256,
        )
    except ExtractionError as error:
        print(
            json.dumps({"state": "failed", "error": str(error)}, ensure_ascii=False),
            file=sys.stderr,
        )
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
