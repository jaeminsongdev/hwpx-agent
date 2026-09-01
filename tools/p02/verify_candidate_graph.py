#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import itertools
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
from tools.p02.extract_help import read_regular_file

SHORTCUT_SUFFIX = re.compile(
    r"(?:\s*\(&[A-Za-z0-9]\)|\s+(?:(?:Ctrl|Alt|Shift)\+)+[A-Za-z0-9]+)\s*$",
    re.IGNORECASE,
)
CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
XSD_KIND = re.compile(r"(?:^|\|)kind:([^|]+)")
XSD_NAMESPACE = re.compile(r"(?:^|\|)namespace:([^|]+)")


def independent_normalize(value: str) -> str:
    if "\t" in value:
        value = value.split("\t", 1)[0]
    value = SHORTCUT_SUFFIX.sub("", unicodedata.normalize("NFC", value))
    value = CAMEL_BOUNDARY.sub(" ", value).casefold()
    characters = [
        character if unicodedata.category(character)[0] in {"L", "M", "N"} else " "
        for character in value
    ]
    return " ".join("".join(characters).split())


def canonical_json(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


def independent_signal_value(value: str) -> str:
    normalized = independent_normalize(value)
    if normalized:
        return normalized
    codepoints = [
        f"u{ord(character):04x}" for character in unicodedata.normalize("NFC", value)
        if not character.isspace()
    ]
    return "symbol-" + "-".join(codepoints)


def parameter_descriptor(parameter: dict) -> str:
    name = independent_signal_value(parameter["original_name"])
    declared_type = parameter.get("declared_type")
    type_label = independent_signal_value(declared_type) if declared_type else "unknown"
    required = parameter.get("required")
    required_label = "required" if required is True else "optional" if required is False else "unknown"
    return f"{name}|{type_label}|{required_label}"


def independent_io_signature(record: dict) -> dict:
    source_kind = record["source_kind"]
    locator_value = str(record.get("locator", {}).get("value", ""))
    xsd_match = XSD_KIND.search(locator_value)
    xsd_kind = xsd_match.group(1) if xsd_match else None
    if source_kind in {"action_table", "automation_object", "automation_event"}:
        domain = "callable"
    elif source_kind == "parameter_table" or (
        source_kind == "xsd" and xsd_kind == "attribute"
    ):
        domain = "field"
    elif source_kind == "xsd":
        domain = "entity"
    else:
        domain = "none"
    if source_kind == "action_table":
        confidence = "indirect"
    elif source_kind in {"automation_object", "automation_event", "parameter_table"}:
        confidence = "direct"
    else:
        confidence = "none"
    result = {
        "domain": domain,
        "confidence": confidence,
        "inputs": [],
        "outputs": [],
        "unknowns": [],
    }
    for parameter in record["parameters"]:
        descriptor = parameter_descriptor(parameter)
        direction = parameter["direction"]
        if direction in {"in", "inout"}:
            result["inputs"].append(descriptor)
        if direction in {"out", "inout"}:
            result["outputs"].append(descriptor)
        if direction == "unknown":
            result["unknowns"].append(descriptor)
    return result


def independent_target_scope(record: dict) -> str | None:
    source_kind = record["source_kind"]
    locator = record.get("locator", {})
    if source_kind == "xsd":
        match = XSD_NAMESPACE.search(str(locator.get("value", "")))
        return match.group(1) if match else None
    if source_kind not in {"automation_object", "automation_event", "parameter_table"}:
        return None
    section = locator.get("section")
    if not isinstance(section, str) or not section.strip():
        return None
    owner = re.split(r"\s*[|:]\s*", section, maxsplit=1)[0]
    return independent_normalize(owner)


def load_source_lock(path: Path) -> tuple[str | None, dict[str, dict]]:
    content = read_regular_file(path, 8 * 1024 * 1024)
    try:
        document = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, {}
    sources = document.get("sources", [])
    entries = {
        entry["source_id"]: entry
        for entry in sources
        if isinstance(entry, dict) and isinstance(entry.get("source_id"), str)
    }
    return document.get("source_lock_id"), entries


def signature_match(left: dict, right: dict, field: str) -> str:
    left_signature = left["io_signature"]
    right_signature = right["io_signature"]
    if left_signature["domain"] == "none" or right_signature["domain"] == "none":
        return "unknown_compatible"
    if left_signature["domain"] != right_signature["domain"]:
        return "conflict"
    if "indirect" in {left_signature["confidence"], right_signature["confidence"]}:
        return "unknown_compatible"
    if "none" in {left_signature["confidence"], right_signature["confidence"]}:
        return "unknown_compatible"
    return "exact" if left_signature[field] == right_signature[field] else "conflict"


def scope_match(left: dict, right: dict) -> str:
    if left["availability_digest"] != right["availability_digest"]:
        return "conflict"
    if left["target_scope"] is None or right["target_scope"] is None:
        return "unknown_compatible"
    return "exact" if left["target_scope"] == right["target_scope"] else "conflict"


def verify(
    output_path: Path, source_lock_path: Path, specs: tuple[InputSpec, ...]
) -> dict:
    errors: list[str] = []
    output = read_regular_file(output_path, 64 * 1024 * 1024)
    try:
        graph = json.loads(output.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        graph = {}
        errors.append(f"output is not valid UTF-8 JSON: {error}")
    schema = json.loads(GRAPH_SCHEMA_PATH.read_text(encoding="utf-8"))
    errors.extend(
        error.message
        for error in Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(
            graph
        )
    )
    records_by_role: dict[str, list[dict]] = {}
    input_hashes: dict[str, str] = {}
    source_lock_id, source_entries = load_source_lock(source_lock_path)
    if graph.get("source_lock_id") != source_lock_id:
        errors.append("candidate graph source_lock_id mismatch")
    expected_restricted = False
    for spec in sorted(specs, key=lambda item: item.role):
        content = read_regular_file(spec.path, MAX_INPUT_BYTES)
        actual_sha256 = hashlib.sha256(content).hexdigest()
        if actual_sha256 != spec.expected_sha256:
            errors.append(f"{spec.role} input SHA-256 mismatch")
        input_hashes[spec.role] = actual_sha256
        try:
            value = json.loads(content.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            value = []
        records_by_role[spec.role] = value if isinstance(value, list) else []
    input_summaries = {
        item.get("role"): item for item in graph.get("inputs", []) if isinstance(item, dict)
    }
    expected_refs: dict[tuple[str, int], dict] = {}
    for role, records in records_by_role.items():
        summary = input_summaries.get(role, {})
        if summary.get("input_sha256") != input_hashes[role]:
            errors.append(f"{role} graph input hash mismatch")
        if summary.get("record_count") != len(records):
            errors.append(f"{role} graph input record count mismatch")
        source_ids = sorted(
            {record.get("source_id") for record in records if isinstance(record, dict)}
        )
        license_states = sorted(
            {
                source_entries.get(source_id, {}).get("license_state")
                for source_id in source_ids
            }
        )
        if summary.get("source_ids") != source_ids:
            errors.append(f"{role} graph source ID coverage mismatch")
        if summary.get("license_states") != license_states:
            errors.append(f"{role} graph license-state coverage mismatch")
        expected_restricted = expected_restricted or "restricted" in license_states
        for index, record in enumerate(records):
            expected_refs[(role, index)] = record
            entry = source_entries.get(record.get("source_id"), {})
            if record.get("source_lock_id") != source_lock_id or record.get(
                "source_sha256"
            ) != entry.get("sha256"):
                errors.append(f"{role} input record {index} source identity mismatch")
    if graph.get("restricted_derivative") is not expected_restricted:
        errors.append("candidate graph restricted-derivative state mismatch")
    nodes = graph.get("nodes", []) if isinstance(graph.get("nodes"), list) else []
    node_ids: set[str] = set()
    node_by_id: dict[str, dict] = {}
    seen_refs: set[tuple[str, int]] = set()
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            continue
        node_id = node.get("node_id")
        if node_id in node_ids:
            errors.append(f"duplicate node_id at node {index}")
        node_ids.add(node_id)
        node_by_id[str(node_id)] = node
        ref = (str(node.get("input_role")), int(node.get("input_ordinal", -1)))
        if ref in seen_refs:
            errors.append(f"duplicate input reference at node {index}")
        seen_refs.add(ref)
        record = expected_refs.get(ref)
        if not isinstance(record, dict):
            errors.append(f"node {index} references an unknown input record")
            continue
        if any(
            node.get(node_key) != record.get(record_key)
            for node_key, record_key in (
                ("record_id", "record_id"),
                ("source_id", "source_id"),
                ("source_sha256", "source_sha256"),
                ("source_kind", "source_kind"),
            )
        ):
            errors.append(f"node {index} provenance mismatch")
        normalized = independent_normalize(str(record.get("original_name", "")))
        if node.get("normalized_label") != normalized:
            errors.append(f"node {index} normalized_label mismatch")
        if node.get("label_tokens") != normalized.split():
            errors.append(f"node {index} label token mismatch")
        if node.get("input_sha256") != input_hashes[ref[0]]:
            errors.append(f"node {index} input SHA-256 mismatch")
        if node.get("io_signature") != independent_io_signature(record):
            errors.append(f"node {index} I/O signature mismatch")
        expected_availability_digest = hashlib.sha256(
            canonical_json(record.get("availability"))
        ).hexdigest()
        if node.get("availability_digest") != expected_availability_digest:
            errors.append(f"node {index} availability digest mismatch")
        if node.get("target_scope") != independent_target_scope(record):
            errors.append(f"node {index} target scope mismatch")
        identity = f"{ref[0]}\0{input_hashes[ref[0]]}\0{record.get('record_id')}"
        expected_node_id = f"node:{hashlib.sha256(identity.encode('utf-8')).hexdigest()[:24]}"
        if node_id != expected_node_id:
            errors.append(f"node {index} deterministic ID mismatch")
    if seen_refs != set(expected_refs):
        errors.append("not every input record appears exactly once as a node")

    expected_pairs: set[tuple[str, str]] = set()
    groups: dict[str, list[str]] = defaultdict(list)
    for node in nodes:
        if isinstance(node, dict):
            groups[str(node.get("normalized_label"))].append(str(node.get("node_id")))
    for group in groups.values():
        expected_pairs.update(itertools.combinations(sorted(group), 2))
    edges = graph.get("edges", []) if isinstance(graph.get("edges"), list) else []
    actual_pairs: set[tuple[str, str]] = set()
    states: defaultdict[str, int] = defaultdict(int)
    for index, edge in enumerate(edges):
        if not isinstance(edge, dict):
            continue
        pair = (str(edge.get("left_node_id")), str(edge.get("right_node_id")))
        if pair in actual_pairs:
            errors.append(f"duplicate candidate pair at edge {index}")
        actual_pairs.add(pair)
        left = node_by_id.get(pair[0])
        right = node_by_id.get(pair[1])
        if left is None or right is None:
            errors.append(f"edge {index} references an unknown node")
            continue
        input_state = signature_match(left, right, "inputs")
        output_state = signature_match(left, right, "outputs")
        target_state = scope_match(left, right)
        state = (
            "collision_review"
            if "conflict" in {input_state, output_state, target_state}
            else "review_candidate"
        )
        identity = f"{pair[0]}\0{pair[1]}"
        expected_id = f"candidate:{hashlib.sha256(identity.encode('utf-8')).hexdigest()[:24]}"
        if edge.get("candidate_id") != expected_id:
            errors.append(f"edge {index} deterministic ID mismatch")
        if (
            edge.get("input_match") != input_state
            or edge.get("output_match") != output_state
            or edge.get("scope_match") != target_state
            or edge.get("candidate_state") != state
        ):
            errors.append(f"edge {index} match classification mismatch")
        expected_reasons = [
            "exact_normalized_label",
            f"input_{input_state}",
            f"output_{output_state}",
            f"scope_{target_state}",
        ]
        if edge.get("normalized_label") != left.get("normalized_label"):
            errors.append(f"edge {index} normalized label mismatch")
        if edge.get("reasons") != expected_reasons:
            errors.append(f"edge {index} reason list mismatch")
        if edge.get("auto_merge") is not False:
            errors.append(f"edge {index} attempts automatic merge")
        states[state] += 1
    if actual_pairs != expected_pairs:
        errors.append("candidate edge coverage differs from exact-label pair coverage")
    coverage = graph.get("coverage", {})
    expected_coverage = {
        "input_record_count": len(expected_refs),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "normalized_label_count": len(groups),
        "singleton_node_count": sum(len(group) == 1 for group in groups.values()),
        "review_candidate_count": states["review_candidate"],
        "collision_review_count": states["collision_review"],
        "auto_merge_count": 0,
    }
    if coverage != expected_coverage:
        errors.append("candidate graph coverage summary mismatch")

    return {
        "schema_version": "hwpx-agent.candidate-graph-verification/v1",
        "output_sha256": hashlib.sha256(output).hexdigest(),
        "input_record_count": len(expected_refs),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "review_candidate_count": states["review_candidate"],
        "collision_review_count": states["collision_review"],
        "auto_merge_count": 0,
        "errors": errors,
    }


def parse_input(value: str) -> InputSpec:
    role, expected_sha256, path = value.split("=", 2)
    return InputSpec(role=role, expected_sha256=expected_sha256, path=Path(path))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-lock", type=Path, required=True)
    parser.add_argument("--input", type=parse_input, action="append", required=True)
    arguments = parser.parse_args()
    try:
        result = verify(arguments.output, arguments.source_lock, tuple(arguments.input))
    except Exception as error:
        print(json.dumps({"state": "failed", "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
