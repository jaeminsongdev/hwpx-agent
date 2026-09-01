#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

from jsonschema import Draft202012Validator, FormatChecker

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from tools.p02.extract_help import SCHEMA_PATH, read_regular_file
from tools.p02.extract_owpml import MAX_INPUT_BYTES, load_source_entry
from tools.p02.validate_source_records import semantic_errors

APPENDICES = tuple("BCDEFGH")
COMPONENT_TAGS = (
    "import",
    "include",
    "element",
    "attribute",
    "complexType",
    "simpleType",
    "group",
    "attributeGroup",
)
START_TAG = re.compile(r"<xs:(%s)\b([^>]*)>" % "|".join(COMPONENT_TAGS))
EMPTY_TAG = re.compile(r"<xs:(%s)\b([^>]*)/>" % "|".join(COMPONENT_TAGS))
NAME = re.compile(r"\b(?:name|ref)\s*=\s*['\"]([^'\"]+)['\"]")
TARGET_NAMESPACE = re.compile(r"\btargetNamespace\s*=\s*['\"]([^'\"]+)['\"]")
BREAK = re.compile(r"<br\s*/?>", re.IGNORECASE)
PACKAGE_TABLE = re.compile(
    r"<table\b[^>]*>\s*<tr\b[^>]*>\s*<td\b[^>]*>(.*?)</td>",
    re.IGNORECASE | re.DOTALL,
)
LOCATOR_KIND = re.compile(r"(?:^|\|)kind:([^|]+)")
LOCATOR_NAMESPACE = re.compile(r"(?:^|\|)namespace:([^|]+)")
LOCATOR_PATH = re.compile(r"(?:^|\|)path:(.+)$")


def independent_expected(document: dict) -> tuple[Counter[str], set[str], set[str]]:
    counts: Counter[str] = Counter()
    namespaces: set[str] = set()
    package_paths: set[str] = set()
    titles = document.get("title", [])
    contents = document.get("content", [])
    if not isinstance(titles, list) or not isinstance(contents, list) or len(titles) != len(contents):
        return counts, namespaces, package_paths
    for appendix in APPENDICES:
        matches = [
            content
            for title, content in zip(titles, contents, strict=True)
            if isinstance(title, dict)
            and isinstance(content, dict)
            and title.get("NUMBERING") == appendix
        ]
        if len(matches) != 1 or not isinstance(matches[0].get("CONTENT"), str):
            continue
        body = matches[0]["CONTENT"]
        start = body.find("<?xml")
        end = body.find("</xs:schema>", start)
        if start < 0 or end < 0:
            continue
        schema = body[start : end + len("</xs:schema>")]
        namespace_match = TARGET_NAMESPACE.search(schema)
        if namespace_match:
            namespaces.add(namespace_match.group(1))
            counts["schema"] += 1
        seen_spans: set[tuple[int, int]] = set()
        for pattern in (START_TAG, EMPTY_TAG):
            for match in pattern.finditer(schema):
                if match.span() in seen_spans:
                    continue
                seen_spans.add(match.span())
                kind, attributes = match.groups()
                if kind in {"import", "include"} or NAME.search(attributes):
                    counts[kind] += 1
    package_matches = [
        content
        for title, content in zip(titles, contents, strict=True)
        if isinstance(title, dict)
        and isinstance(content, dict)
        and title.get("NUMBERING") == "8.2"
    ]
    if len(package_matches) == 1 and isinstance(package_matches[0].get("CONTENT"), str):
        table_match = PACKAGE_TABLE.search(package_matches[0]["CONTENT"])
        if table_match:
            tokens = [" ".join(piece.split()) for piece in BREAK.split(table_match.group(1))]
            current_directory = ""
            for token in [token for token in tokens if token][1:]:
                normalized = token[1:-1] if token.startswith("[") and token.endswith("]") else token
                if normalized.endswith("/"):
                    current_directory = normalized
                else:
                    package_paths.add(current_directory + normalized)
            counts["package_part"] = len(package_paths)
    return counts, namespaces, package_paths


def verify(
    output_path: Path,
    source_lock_path: Path,
    source_id: str,
    source_input: Path,
) -> dict:
    errors: list[str] = []
    output = read_regular_file(output_path, MAX_INPUT_BYTES)
    source = read_regular_file(source_input, MAX_INPUT_BYTES)
    source_lock_id, entry = load_source_entry(source_lock_path, source_id)
    source_sha256 = hashlib.sha256(source).hexdigest()
    if source_sha256 != entry["sha256"]:
        errors.append("source input does not match the locked SHA-256")
    try:
        document = json.loads(source.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        document = {}
        errors.append(f"source is not valid UTF-8 JSON: {error}")
    expected_counts, expected_namespaces, expected_package_paths = independent_expected(document)
    try:
        records = json.loads(output.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        records = []
        errors.append(f"output is not valid UTF-8 JSON: {error}")
    if not isinstance(records, list) or not records:
        errors.append("output must be a non-empty SourceRecord array")
        records = []

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    actual_counts: Counter[str] = Counter()
    actual_namespaces: set[str] = set()
    actual_package_paths: set[str] = set()
    record_ids: list[str] = []
    locator_values: list[str] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"record {index} is not an object")
            continue
        errors.extend(
            f"record {index}: {violation.message}"
            for violation in validator.iter_errors(record)
        )
        errors.extend(f"record {index}: {error}" for error in semantic_errors(record))
        if record.get("source_lock_id") != source_lock_id:
            errors.append(f"record {index}: source_lock_id mismatch")
        if record.get("source_id") != source_id:
            errors.append(f"record {index}: source_id mismatch")
        if record.get("source_sha256") != entry["sha256"]:
            errors.append(f"record {index}: source_sha256 mismatch")
        if record.get("source_kind") != "xsd":
            errors.append(f"record {index}: source_kind is not xsd")
        availability = record.get("availability", {})
        if availability.get("support_scope") != "documentation_only":
            errors.append(f"record {index}: schema metadata must remain documentation_only")
        if availability.get("product") != "hancom_hangul":
            errors.append(f"record {index}: unexpected product availability")
        if any(
            availability.get(key) is not None
            for key in ("target_profile_id", "minimum_version", "maximum_version")
        ):
            errors.append(f"record {index}: documentation schema has runtime availability")
        if record.get("parameters") != []:
            errors.append(f"record {index}: raw XSD metadata must not become executable parameters")
        extraction = record.get("extraction", {})
        if extraction.get("extractor_id") != "ksx6101-owpml-extractor":
            errors.append(f"record {index}: unexpected extractor_id")
        if extraction.get("extractor_version") != "0.1.0":
            errors.append(f"record {index}: unexpected extractor_version")
        if extraction.get("record_ordinal") != index:
            errors.append(f"record {index}: extraction ordinal mismatch")
        locator = record.get("locator", {})
        value = str(locator.get("value", ""))
        if locator.get("kind") != "xsd_component":
            errors.append(f"record {index}: locator is not xsd_component")
        kind_match = LOCATOR_KIND.search(value)
        path_match = LOCATOR_PATH.search(value)
        if not kind_match or not path_match:
            errors.append(f"record {index}: locator does not encode kind/path")
        else:
            kind = kind_match.group(1)
            actual_counts[kind] += 1
            if kind == "package_part":
                actual_package_paths.add(path_match.group(1))
            else:
                namespace_match = LOCATOR_NAMESPACE.search(value)
                if not namespace_match:
                    errors.append(f"record {index}: XSD locator has no namespace")
                elif kind == "schema":
                    actual_namespaces.add(namespace_match.group(1))
        record_ids.append(str(record.get("record_id", "")))
        locator_values.append(value)
    if len(record_ids) != len(set(record_ids)):
        errors.append("record_id values are not unique")
    if len(locator_values) != len(set(locator_values)):
        errors.append("XSD locator values are not unique")
    if actual_counts != expected_counts:
        errors.append(
            f"component coverage mismatch: expected {dict(expected_counts)}, actual {dict(actual_counts)}"
        )
    if actual_namespaces != expected_namespaces:
        errors.append("namespace coverage mismatch")
    namespace_versions = {
        match.group(1)
        for namespace in actual_namespaces
        if (match := re.fullmatch(r"http://www\.owpml\.org/owpml/([0-9]{4})/[a-z0-9-]+", namespace))
    }
    if len(actual_namespaces) != 7 or namespace_versions != {"2024"}:
        errors.append("OWPML namespace/version coverage is not exactly seven 2024 namespaces")
    if actual_package_paths != expected_package_paths:
        errors.append("package part coverage mismatch")
    raw_xml_published = any(
        marker in output for marker in (b"<?xml", b"<xs:", b"<!DOCTYPE", b"<!ENTITY")
    )
    if raw_xml_published:
        errors.append("raw XML was published in SourceRecord output")

    return {
        "schema_version": "hwpx-agent.owpml-extraction-verification/v1",
        "source_lock_id": source_lock_id,
        "source_id": source_id,
        "source_sha256": entry["sha256"],
        "output_sha256": hashlib.sha256(output).hexdigest(),
        "record_count": len(records),
        "component_counts": dict(sorted(actual_counts.items())),
        "namespaces": sorted(actual_namespaces),
        "namespace_versions": sorted(namespace_versions),
        "package_part_count": len(actual_package_paths),
        "raw_xml_published": raw_xml_published,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-lock", type=Path, required=True)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--source-input", type=Path, required=True)
    arguments = parser.parse_args()
    try:
        result = verify(
            arguments.output,
            arguments.source_lock,
            arguments.source_id,
            arguments.source_input,
        )
    except Exception as error:
        print(json.dumps({"state": "failed", "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
