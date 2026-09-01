#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
import hashlib
import itertools
import json
import os
from pathlib import Path
import re
import sys
import unicodedata

from jsonschema import Draft202012Validator, FormatChecker

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from tools.p02.extract_help import (
    ExtractionError,
    SCHEMA_PATH as SOURCE_RECORD_SCHEMA_PATH,
    publish_no_overwrite,
    read_regular_file,
    resolve_output,
)
from tools.p02.validate_source_records import semantic_errors

GRAPH_SCHEMA_PATH = Path(__file__).resolve().parent / "schemas" / "candidate-graph-v1.schema.json"
GENERATOR_ID = "source-record-candidate-generator"
GENERATOR_VERSION = "0.1.0"
MAX_INPUT_BYTES = 16 * 1024 * 1024
MAX_RECORDS = 100_000
ROLE_KINDS = {
    "help": {"help", "webhwp"},
    "automation": {
        "action_table",
        "parameter_table",
        "automation_object",
        "automation_event",
    },
    "owpml": {"xsd"},
}
SHORTCUT_SUFFIX = re.compile(
    r"(?:\s*\(&[A-Za-z0-9]\)|\s+(?:(?:Ctrl|Alt|Shift)\+)+[A-Za-z0-9]+)\s*$",
    re.IGNORECASE,
)
CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
XSD_KIND = re.compile(r"(?:^|\|)kind:([^|]+)")
XSD_NAMESPACE = re.compile(r"(?:^|\|)namespace:([^|]+)")


@dataclass(frozen=True)
class InputSpec:
    role: str
    path: Path
    expected_sha256: str


@dataclass(frozen=True)
class CandidateConfig:
    source_lock: Path
    inputs: tuple[InputSpec, ...]
    output_root: Path
    output_relative: str


@dataclass(frozen=True)
class LoadedInput:
    role: str
    sha256: str
    records: list[dict]
    source_ids: tuple[str, ...]
    license_states: tuple[str, ...]


def canonical_json(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


def normalize_label(value: str) -> tuple[str, tuple[str, ...]]:
    if "\t" in value:
        value = value.split("\t", 1)[0]
    value = SHORTCUT_SUFFIX.sub("", unicodedata.normalize("NFC", value))
    if any(unicodedata.category(character) in {"Cc", "Cf", "Cs"} for character in value):
        raise ExtractionError("source label contains prohibited control/format characters")
    value = CAMEL_BOUNDARY.sub(" ", value).casefold()
    normalized_characters = []
    for character in value:
        category = unicodedata.category(character)
        normalized_characters.append(character if category[0] in {"L", "M", "N"} else " ")
    normalized = " ".join("".join(normalized_characters).split())
    if not normalized:
        raise ExtractionError("source label normalizes to an empty value")
    tokens = tuple(normalized.split())
    if len(normalized) > 2048 or len(tokens) > 256 or any(len(token) > 512 for token in tokens):
        raise ExtractionError("normalized source label exceeds candidate graph limits")
    return normalized, tokens


def normalize_signal_value(value: str) -> str:
    try:
        return normalize_label(value)[0]
    except ExtractionError as error:
        if "empty value" not in str(error):
            raise
    value = unicodedata.normalize("NFC", value)
    if any(unicodedata.category(character) in {"Cc", "Cf", "Cs"} for character in value):
        raise ExtractionError("source signal contains prohibited control/format characters")
    codepoints = [f"u{ord(character):04x}" for character in value if not character.isspace()]
    if not codepoints:
        raise ExtractionError("source signal normalizes to an empty value")
    return "symbol-" + "-".join(codepoints)


def load_source_lock(path: Path) -> tuple[str, dict[str, dict]]:
    content = read_regular_file(path, 8 * 1024 * 1024)
    try:
        document = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ExtractionError(f"invalid UTF-8 source lock: {error}") from error
    if document.get("schema_version") != "hwpx-agent.source-lock/v2":
        raise ExtractionError("unsupported source-lock schema_version")
    source_lock_id = document.get("source_lock_id")
    sources = document.get("sources")
    if not isinstance(source_lock_id, str) or not isinstance(sources, list):
        raise ExtractionError("source lock identity/sources are invalid")
    entries: dict[str, dict] = {}
    for entry in sources:
        if not isinstance(entry, dict) or not isinstance(entry.get("source_id"), str):
            raise ExtractionError("source lock contains an invalid source entry")
        source_id = entry["source_id"]
        if source_id in entries:
            raise ExtractionError(f"duplicate source-lock source_id: {source_id}")
        if entry.get("license_state") not in {"public_reference", "restricted"}:
            raise ExtractionError(f"source {source_id} has an unadmitted license_state")
        if not re.fullmatch(r"[0-9a-f]{64}", str(entry.get("sha256", ""))):
            raise ExtractionError(f"source {source_id} has a malformed SHA-256")
        entries[source_id] = entry
    return source_lock_id, entries


def load_inputs(
    specs: tuple[InputSpec, ...], source_lock_id: str, source_entries: dict[str, dict]
) -> list[LoadedInput]:
    roles = [spec.role for spec in specs]
    if sorted(roles) != sorted(ROLE_KINDS) or len(roles) != len(set(roles)):
        raise ExtractionError("inputs must contain exactly one help, automation and owpml role")
    source_schema = json.loads(SOURCE_RECORD_SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(source_schema, format_checker=FormatChecker())
    loaded: list[LoadedInput] = []
    global_record_ids: set[str] = set()
    for spec in sorted(specs, key=lambda item: item.role):
        if not re.fullmatch(r"[0-9a-f]{64}", spec.expected_sha256):
            raise ExtractionError(f"{spec.role} expected SHA-256 is malformed")
        content = read_regular_file(spec.path, MAX_INPUT_BYTES)
        actual_sha256 = hashlib.sha256(content).hexdigest()
        if actual_sha256 != spec.expected_sha256:
            raise ExtractionError(
                f"{spec.role} input SHA-256 mismatch: expected {spec.expected_sha256}, actual {actual_sha256}"
            )
        try:
            records = json.loads(content.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ExtractionError(f"{spec.role} input is not valid UTF-8 JSON: {error}") from error
        if not isinstance(records, list) or not records or len(records) > MAX_RECORDS:
            raise ExtractionError(f"{spec.role} input record cardinality is invalid")
        source_ids: set[str] = set()
        license_states: set[str] = set()
        for index, record in enumerate(records):
            if not isinstance(record, dict):
                raise ExtractionError(f"{spec.role} record {index} is not an object")
            violations = [error.message for error in validator.iter_errors(record)]
            violations.extend(semantic_errors(record))
            if violations:
                raise ExtractionError(
                    f"{spec.role} record {index} is invalid: " + "; ".join(violations[:10])
                )
            if record["source_lock_id"] != source_lock_id:
                raise ExtractionError(f"{spec.role} record {index} source_lock_id mismatch")
            if record["source_kind"] not in ROLE_KINDS[spec.role]:
                raise ExtractionError(f"{spec.role} record {index} has an incompatible source_kind")
            if record["extraction"]["record_ordinal"] != index:
                raise ExtractionError(f"{spec.role} record ordinals are not contiguous")
            record_id = record["record_id"]
            if record_id in global_record_ids:
                raise ExtractionError(f"duplicate input record_id: {record_id}")
            global_record_ids.add(record_id)
            source_id = record["source_id"]
            entry = source_entries.get(source_id)
            if entry is None or record["source_sha256"] != entry["sha256"]:
                raise ExtractionError(f"{spec.role} record {index} source identity mismatch")
            source_ids.add(source_id)
            license_states.add(entry["license_state"])
        loaded.append(
            LoadedInput(
                role=spec.role,
                sha256=actual_sha256,
                records=records,
                source_ids=tuple(sorted(source_ids)),
                license_states=tuple(sorted(license_states)),
            )
        )
    return loaded


def parameter_descriptor(parameter: dict) -> str:
    name = normalize_signal_value(parameter["original_name"])
    declared_type = parameter.get("declared_type")
    type_label = normalize_signal_value(declared_type) if declared_type else "unknown"
    required = parameter.get("required")
    required_label = "required" if required is True else "optional" if required is False else "unknown"
    return f"{name}|{type_label}|{required_label}"


def io_signature(record: dict) -> dict:
    source_kind = record["source_kind"]
    locator_value = str(record.get("locator", {}).get("value", ""))
    xsd_kind_match = XSD_KIND.search(locator_value)
    xsd_kind = xsd_kind_match.group(1) if xsd_kind_match else None
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
    inputs: list[str] = []
    outputs: list[str] = []
    unknowns: list[str] = []
    for parameter in record["parameters"]:
        descriptor = parameter_descriptor(parameter)
        direction = parameter["direction"]
        if direction in {"in", "inout"}:
            inputs.append(descriptor)
        if direction in {"out", "inout"}:
            outputs.append(descriptor)
        if direction == "unknown":
            unknowns.append(descriptor)
    return {
        "domain": domain,
        "confidence": confidence,
        "inputs": inputs,
        "outputs": outputs,
        "unknowns": unknowns,
    }


def target_scope(record: dict) -> str | None:
    source_kind = record["source_kind"]
    locator = record.get("locator", {})
    value = str(locator.get("value", ""))
    if source_kind == "xsd":
        match = XSD_NAMESPACE.search(value)
        return match.group(1) if match else None
    if source_kind not in {"automation_object", "automation_event", "parameter_table"}:
        return None
    section = locator.get("section")
    if not isinstance(section, str) or not section.strip():
        return None
    owner = re.split(r"\s*[|:]\s*", section, maxsplit=1)[0]
    return normalize_label(owner)[0]


def build_nodes(inputs: list[LoadedInput]) -> list[dict]:
    nodes: list[dict] = []
    for loaded in inputs:
        for index, record in enumerate(loaded.records):
            normalized_label, tokens = normalize_label(record["original_name"])
            identity = f"{loaded.role}\0{loaded.sha256}\0{record['record_id']}"
            nodes.append(
                {
                    "node_id": f"node:{hashlib.sha256(identity.encode('utf-8')).hexdigest()[:24]}",
                    "input_role": loaded.role,
                    "input_sha256": loaded.sha256,
                    "input_ordinal": index,
                    "record_id": record["record_id"],
                    "source_id": record["source_id"],
                    "source_sha256": record["source_sha256"],
                    "source_kind": record["source_kind"],
                    "normalized_label": normalized_label,
                    "label_tokens": list(tokens),
                    "io_signature": io_signature(record),
                    "availability_digest": hashlib.sha256(
                        canonical_json(record["availability"])
                    ).hexdigest(),
                    "target_scope": target_scope(record),
                }
            )
    return sorted(nodes, key=lambda node: (node["input_role"], node["input_ordinal"]))


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


def build_edges(nodes: list[dict]) -> list[dict]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for node in nodes:
        groups[node["normalized_label"]].append(node)
    edges: list[dict] = []
    for normalized_label in sorted(groups):
        group = sorted(groups[normalized_label], key=lambda node: node["node_id"])
        for left, right in itertools.combinations(group, 2):
            input_state = signature_match(left, right, "inputs")
            output_state = signature_match(left, right, "outputs")
            target_state = scope_match(left, right)
            states = (input_state, output_state, target_state)
            candidate_state = "collision_review" if "conflict" in states else "review_candidate"
            identity = f"{left['node_id']}\0{right['node_id']}"
            edges.append(
                {
                    "candidate_id": f"candidate:{hashlib.sha256(identity.encode('utf-8')).hexdigest()[:24]}",
                    "left_node_id": left["node_id"],
                    "right_node_id": right["node_id"],
                    "normalized_label": normalized_label,
                    "candidate_state": candidate_state,
                    "input_match": input_state,
                    "output_match": output_state,
                    "scope_match": target_state,
                    "reasons": [
                        "exact_normalized_label",
                        f"input_{input_state}",
                        f"output_{output_state}",
                        f"scope_{target_state}",
                    ],
                    "auto_merge": False,
                }
            )
    return edges


def build_graph(source_lock_id: str, inputs: list[LoadedInput]) -> dict:
    nodes = build_nodes(inputs)
    edges = build_edges(nodes)
    label_counts: dict[str, int] = defaultdict(int)
    for node in nodes:
        label_counts[node["normalized_label"]] += 1
    graph = {
        "schema_version": "hwpx-agent.candidate-graph/v1",
        "source_lock_id": source_lock_id,
        "generator": {
            "generator_id": GENERATOR_ID,
            "generator_version": GENERATOR_VERSION,
            "auto_merge": False,
        },
        "restricted_derivative": any(
            "restricted" in loaded.license_states for loaded in inputs
        ),
        "inputs": [
            {
                "role": loaded.role,
                "input_sha256": loaded.sha256,
                "record_count": len(loaded.records),
                "source_ids": list(loaded.source_ids),
                "license_states": list(loaded.license_states),
            }
            for loaded in inputs
        ],
        "nodes": nodes,
        "edges": edges,
        "coverage": {
            "input_record_count": sum(len(loaded.records) for loaded in inputs),
            "node_count": len(nodes),
            "edge_count": len(edges),
            "normalized_label_count": len(label_counts),
            "singleton_node_count": sum(count == 1 for count in label_counts.values()),
            "review_candidate_count": sum(
                edge["candidate_state"] == "review_candidate" for edge in edges
            ),
            "collision_review_count": sum(
                edge["candidate_state"] == "collision_review" for edge in edges
            ),
            "auto_merge_count": 0,
        },
    }
    schema = json.loads(GRAPH_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    violations = [
        error.message
        for error in Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(
            graph
        )
    ]
    if violations:
        raise ExtractionError("generated candidate graph is invalid: " + "; ".join(violations[:20]))
    return graph


def serialize_graph(graph: dict) -> bytes:
    return (json.dumps(graph, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def run(config: CandidateConfig) -> dict:
    source_lock_id, source_entries = load_source_lock(config.source_lock)
    inputs = load_inputs(config.inputs, source_lock_id, source_entries)
    graph = build_graph(source_lock_id, inputs)
    if graph["restricted_derivative"] and os.path.normcase(
        str(config.output_root.absolute())
    ) != os.path.normcase(
        str((REPOSITORY_ROOT / "implementation" / "p02" / "evidence").absolute())
    ):
        raise ExtractionError("restricted candidate graph may publish only to implementation/p02/evidence")
    for spec, loaded in zip(sorted(config.inputs, key=lambda item: item.role), inputs, strict=True):
        if hashlib.sha256(read_regular_file(spec.path, MAX_INPUT_BYTES)).hexdigest() != loaded.sha256:
            raise ExtractionError(f"{spec.role} input changed during candidate generation")
    payload = serialize_graph(graph)
    output = resolve_output(config.output_root, config.output_relative)
    publish_no_overwrite(output, payload)
    return {
        "schema_version": "hwpx-agent.candidate-generation-receipt/v1",
        "source_lock_id": source_lock_id,
        "restricted_derivative": graph["restricted_derivative"],
        "coverage": graph["coverage"],
        "output_relative": config.output_relative,
        "output_sha256": hashlib.sha256(payload).hexdigest(),
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
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--output-relative", required=True)
    arguments = parser.parse_args()
    try:
        receipt = run(
            CandidateConfig(
                source_lock=arguments.source_lock,
                inputs=tuple(arguments.input),
                output_root=arguments.output_root,
                output_relative=arguments.output_relative,
            )
        )
    except ExtractionError as error:
        print(json.dumps({"state": "failed", "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
