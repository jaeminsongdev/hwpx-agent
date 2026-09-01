#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET

from jsonschema import Draft202012Validator, FormatChecker

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from tools.p02.extract_help import (
    ExtractionError,
    SCHEMA_PATH,
    publish_no_overwrite,
    read_regular_file,
    resolve_output,
)

EXTRACTOR_ID = "ksx6101-owpml-extractor"
EXTRACTOR_VERSION = "0.1.0"
MAX_INPUT_BYTES = 24 * 1024 * 1024
MAX_SECTIONS = 2_000
MAX_SCHEMA_BYTES = 4 * 1024 * 1024
MAX_SCHEMA_NODES = 100_000
MAX_SCHEMA_DEPTH = 64
MAX_DESCRIPTION_CHARACTERS = 20_000
EXPECTED_APPENDICES = tuple("BCDEFGH")
XML_SCHEMA_NAMESPACE = "http://www.w3.org/2001/XMLSchema"
XS = f"{{{XML_SCHEMA_NAMESPACE}}}"
DECLARATION_KINDS = (
    "element",
    "attribute",
    "complexType",
    "simpleType",
    "group",
    "attributeGroup",
)
GLOSSARY = re.compile(
    r"<div class='jb-container'><div class='jb-title'>([^<>]{1,128})</div>"
    r"<div class='jb-text'>.*?</div></div>",
    re.DOTALL,
)
BREAK = re.compile(r"<br\s*/?>", re.IGNORECASE)
PACKAGE_TABLE = re.compile(
    r"<table\b[^>]*>\s*<tr\b[^>]*>\s*<td\b[^>]*>(.*?)</td>",
    re.IGNORECASE | re.DOTALL,
)
PACKAGE_TOKEN = re.compile(r"^[A-Za-z0-9_.\[\]-]+/?$")
NAMESPACE_VERSION = re.compile(r"^http://www\.owpml\.org/owpml/([0-9]{4})/[a-z0-9-]+$")


@dataclass(frozen=True)
class ExtractionConfig:
    source_lock: Path
    source_id: str
    input_path: Path
    output_root: Path
    output_relative: str


@dataclass(frozen=True)
class SchemaSection:
    appendix: str
    title: str
    namespace: str
    namespace_version: str
    root: ET.Element
    glossary_replacements: int


@dataclass(frozen=True)
class PackagePart:
    path: str
    optional: bool


def normalize_text(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).split())


def load_source_entry(source_lock_path: Path, source_id: str) -> tuple[str, dict]:
    content = read_regular_file(source_lock_path, 8 * 1024 * 1024)
    try:
        source_lock = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ExtractionError(f"invalid UTF-8 source lock: {error}") from error
    if source_lock.get("schema_version") != "hwpx-agent.source-lock/v2":
        raise ExtractionError("unsupported source-lock schema_version")
    source_lock_id = source_lock.get("source_lock_id")
    if not isinstance(source_lock_id, str):
        raise ExtractionError("source lock has no source_lock_id")
    sources = source_lock.get("sources")
    if not isinstance(sources, list) or not all(isinstance(entry, dict) for entry in sources):
        raise ExtractionError("source lock sources must be an array of objects")
    matches = [entry for entry in sources if entry.get("source_id") == source_id]
    if len(matches) != 1:
        raise ExtractionError(f"source_id must match exactly one lock entry: {source_id}")
    entry = matches[0]
    if entry.get("kind") != "machine_readable_standard":
        raise ExtractionError(
            f"source kind is not machine_readable_standard: {entry.get('kind')}"
        )
    if entry.get("license_state") not in {"public_reference", "restricted"}:
        raise ExtractionError(f"source license_state is not admitted: {entry.get('license_state')}")
    if not re.fullmatch(r"[0-9a-f]{64}", str(entry.get("sha256", ""))):
        raise ExtractionError("source lock SHA-256 is malformed")
    return source_lock_id, entry


def decode_machine_standard(content: bytes) -> dict:
    if b"\x00" in content:
        raise ExtractionError("machine-readable JSON contains NUL bytes")
    try:
        text = content.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise ExtractionError(f"machine-readable JSON is not strict UTF-8: {error}") from error
    if "\ufffd" in text:
        raise ExtractionError("machine-readable JSON contains Unicode replacement characters")
    try:
        document = json.loads(text)
    except json.JSONDecodeError as error:
        raise ExtractionError(f"machine-readable JSON is invalid: {error}") from error
    if not isinstance(document, dict):
        raise ExtractionError("machine-readable JSON root must be an object")
    info = document.get("info")
    titles = document.get("title")
    contents = document.get("content")
    if not isinstance(info, dict):
        raise ExtractionError("machine-readable JSON info must be an object")
    if not isinstance(titles, list) or not isinstance(contents, list):
        raise ExtractionError("machine-readable JSON title/content must be arrays")
    if not titles or len(titles) != len(contents) or len(titles) > MAX_SECTIONS:
        raise ExtractionError("machine-readable JSON title/content cardinality is invalid")
    if not all(isinstance(item, dict) for item in titles + contents):
        raise ExtractionError("machine-readable JSON sections must be objects")
    expected_identity = {
        "ksCode": "KSX6101",
        "tmprKsNo": "KSX6101",
        "reformNo": "03",
        "activeYn": "Y",
        "operationDate": "2024년 10월 30일",
    }
    mismatches = [
        f"{key}={info.get(key)!r}"
        for key, expected in expected_identity.items()
        if info.get(key) != expected
    ]
    if mismatches:
        raise ExtractionError("unexpected KS X 6101 identity: " + ", ".join(mismatches))
    return document


def extract_embedded_schema(body: str, appendix: str) -> tuple[str, int]:
    if len(body.encode("utf-8")) > MAX_SCHEMA_BYTES:
        raise ExtractionError(f"appendix {appendix} exceeds the schema byte limit")
    if re.search(r"<!\s*(?:DOCTYPE|ENTITY)\b", body, re.IGNORECASE):
        raise ExtractionError(f"appendix {appendix} contains a prohibited XML declaration")
    if body.count("<?xml") != 1 or body.count("<xs:schema") != 1:
        raise ExtractionError(f"appendix {appendix} has ambiguous embedded schema boundaries")
    if body.count("</xs:schema>") != 1:
        raise ExtractionError(f"appendix {appendix} has no unique schema closing tag")
    start = body.index("<?xml")
    end = body.index("</xs:schema>", start) + len("</xs:schema>")
    raw_schema = body[start:end]

    def replace_glossary(match: re.Match[str]) -> str:
        title = match.group(1)
        if any(character in title for character in '<>&"'):
            raise ExtractionError(f"appendix {appendix} has an unsafe glossary title")
        return title

    repaired, replacement_count = GLOSSARY.subn(replace_glossary, raw_schema)
    repaired = BREAK.sub("\n", repaired)
    if "jb-container" in repaired or re.search(r"</?(?:div|br)\b", repaired, re.IGNORECASE):
        raise ExtractionError(f"appendix {appendix} contains residual viewer markup")
    return repaired, replacement_count


def validate_tree(root: ET.Element, appendix: str) -> None:
    if root.tag != XS + "schema":
        raise ExtractionError(f"appendix {appendix} root is not xs:schema")
    node_count = 0
    attribute_count = 0
    stack: list[tuple[ET.Element, int]] = [(root, 1)]
    while stack:
        node, depth = stack.pop()
        node_count += 1
        attribute_count += len(node.attrib)
        if node_count > MAX_SCHEMA_NODES or attribute_count > MAX_SCHEMA_NODES:
            raise ExtractionError(f"appendix {appendix} exceeds XML node/attribute limits")
        if depth > MAX_SCHEMA_DEPTH:
            raise ExtractionError(f"appendix {appendix} exceeds XML depth limit")
        if not isinstance(node.tag, str) or not node.tag.startswith(XS):
            raise ExtractionError(f"appendix {appendix} contains a non-XSD element")
        stack.extend((child, depth + 1) for child in reversed(list(node)))


def parse_schema_sections(document: dict) -> list[SchemaSection]:
    matches: dict[str, list[tuple[str, dict]]] = {appendix: [] for appendix in EXPECTED_APPENDICES}
    for title, content in zip(document["title"], document["content"], strict=True):
        numbering = title.get("NUMBERING")
        if numbering in matches:
            if content.get("NUMBERING") != numbering:
                raise ExtractionError(f"appendix {numbering} title/content numbering mismatch")
            title_text = title.get("TITLEINDEX")
            if not isinstance(title_text, str) or "XML 스키마" not in title_text:
                raise ExtractionError(f"appendix {numbering} is not identified as an XML schema")
            matches[numbering].append((title_text, content))
    sections: list[SchemaSection] = []
    namespaces: set[str] = set()
    for appendix in EXPECTED_APPENDICES:
        if len(matches[appendix]) != 1:
            raise ExtractionError(f"appendix {appendix} must occur exactly once")
        title, content = matches[appendix][0]
        body = content.get("CONTENT")
        if not isinstance(body, str):
            raise ExtractionError(f"appendix {appendix} content is not text")
        schema_text, replacement_count = extract_embedded_schema(body, appendix)
        try:
            root = ET.fromstring(schema_text)
        except ET.ParseError as error:
            raise ExtractionError(f"appendix {appendix} schema parse failed: {error}") from error
        validate_tree(root, appendix)
        namespace = root.attrib.get("targetNamespace")
        if not isinstance(namespace, str) or not namespace:
            raise ExtractionError(f"appendix {appendix} has no targetNamespace")
        version_match = NAMESPACE_VERSION.fullmatch(namespace)
        if not version_match:
            raise ExtractionError(f"appendix {appendix} has an unsupported OWPML namespace")
        if namespace in namespaces:
            raise ExtractionError(f"duplicate targetNamespace: {namespace}")
        namespaces.add(namespace)
        sections.append(
            SchemaSection(
                appendix=appendix,
                title=normalize_text(title),
                namespace=namespace,
                namespace_version=version_match.group(1),
                root=root,
                glossary_replacements=replacement_count,
            )
        )
    versions = {section.namespace_version for section in sections}
    if versions != {"2024"}:
        raise ExtractionError(f"OWPML namespace version coverage is not exactly 2024: {versions}")
    return sections


def parse_package_parts(document: dict) -> list[PackagePart]:
    matches = [
        content
        for title, content in zip(document["title"], document["content"], strict=True)
        if title.get("NUMBERING") == "8.2"
    ]
    if len(matches) != 1 or matches[0].get("NUMBERING") != "8.2":
        raise ExtractionError("package profile section 8.2 must occur exactly once")
    body = matches[0].get("CONTENT")
    if not isinstance(body, str):
        raise ExtractionError("package profile section 8.2 content is not text")
    table_match = PACKAGE_TABLE.search(body)
    if not table_match:
        raise ExtractionError("package profile section 8.2 has no authoritative part table")
    cell = table_match.group(1)
    pieces = [normalize_text(piece) for piece in BREAK.split(cell)]
    tokens = [piece for piece in pieces if piece]
    if not tokens or tokens[0] != "* ZIP Container":
        raise ExtractionError("package profile table has an unexpected container root")
    current_directory = ""
    parts: list[PackagePart] = []
    for token in tokens[1:]:
        if not PACKAGE_TOKEN.fullmatch(token):
            raise ExtractionError(f"unsupported package part token: {token!r}")
        optional = token.startswith("[") and token.endswith("]")
        normalized = token[1:-1] if optional else token
        if not normalized or normalized in {".", ".."} or ".." in normalized.split("/"):
            raise ExtractionError(f"unsafe package part token: {token!r}")
        if normalized.endswith("/"):
            if optional:
                raise ExtractionError(f"optional directory token is unsupported: {token!r}")
            current_directory = normalized
            continue
        path = current_directory + normalized
        if path.startswith("/") or "\\" in path or ":" in path:
            raise ExtractionError(f"unsafe package part path: {path!r}")
        parts.append(PackagePart(path=path, optional=optional))
    paths = [part.path for part in parts]
    if not paths or len(paths) != len(set(paths)):
        raise ExtractionError("package profile contains no parts or duplicate part paths")
    required_parts = {"mimetype", "version.xml", "META-INF/container.xml", "Contents/header.xml"}
    if not required_parts.issubset(paths):
        raise ExtractionError("package profile is missing required OWPML part examples")
    return parts


def tag_local_name(tag: str) -> str:
    return tag[len(XS) :] if tag.startswith(XS) else tag


def iter_tree_paths(root: ET.Element) -> list[tuple[ET.Element, str]]:
    result: list[tuple[ET.Element, str]] = []

    def visit(node: ET.Element, path: str) -> None:
        result.append((node, path))
        counts: Counter[str] = Counter()
        for child in node:
            local_name = tag_local_name(child.tag)
            counts[local_name] += 1
            visit(child, f"{path}/xs:{local_name}[{counts[local_name]}]")

    visit(root, "/xs:schema[1]")
    return result


def component_description(node: ET.Element) -> str | None:
    annotation = node.find(XS + "annotation")
    if annotation is None:
        return None
    documents = []
    for documentation in annotation.findall(XS + "documentation"):
        text = normalize_text("".join(documentation.itertext()))
        if text:
            documents.append(text)
    if not documents:
        return None
    description = normalize_text(" ".join(documents))
    if len(description) > MAX_DESCRIPTION_CHARACTERS:
        raise ExtractionError("XSD component description exceeds SourceRecord limit")
    return description


def source_record(
    *,
    source_lock_id: str,
    source_id: str,
    source_sha256: str,
    ordinal: int,
    locator_value: str,
    section: str,
    original_name: str,
    description: str | None,
) -> dict:
    if len(locator_value) > 2048:
        raise ExtractionError("XSD component locator exceeds SourceRecord limit")
    return {
        "schema_version": "hwpx-agent.source-record/v1",
        "record_id": f"{source_id}:xsd:{ordinal:06d}",
        "source_lock_id": source_lock_id,
        "source_id": source_id,
        "source_sha256": source_sha256,
        "source_kind": "xsd",
        "locator": {
            "kind": "xsd_component",
            "value": locator_value,
            "section": section,
        },
        "original_name": original_name,
        "description_ko": description,
        "parameters": [],
        "availability": {
            "product": "hancom_hangul",
            "target_profile_id": None,
            "minimum_version": None,
            "maximum_version": None,
            "locales": ["ko-KR"],
            "support_scope": "documentation_only",
        },
        "extraction": {
            "extractor_id": EXTRACTOR_ID,
            "extractor_version": EXTRACTOR_VERSION,
            "record_ordinal": ordinal,
        },
    }


def build_records(
    source_lock_id: str,
    source_id: str,
    source_sha256: str,
    document: dict,
) -> tuple[list[dict], dict]:
    sections = parse_schema_sections(document)
    package_parts = parse_package_parts(document)
    records: list[dict] = []
    component_counts: Counter[str] = Counter()

    def append(**values: object) -> None:
        records.append(
            source_record(
                source_lock_id=source_lock_id,
                source_id=source_id,
                source_sha256=source_sha256,
                ordinal=len(records),
                **values,
            )
        )

    for part in package_parts:
        append(
            locator_value=f"section:8.2|kind:package_part|path:{part.path}",
            section="8.2 OCF OWPML 프로파일",
            original_name=part.path,
            description="선택 패키지 part" if part.optional else "패키지 part",
        )
        component_counts["package_part"] += 1

    for section in sections:
        section_label = f"Appendix {section.appendix} | {section.title}"
        append(
            locator_value=(
                f"appendix:{section.appendix}|namespace:{section.namespace}|"
                "kind:schema|path:/xs:schema[1]"
            ),
            section=section_label,
            original_name=section.title,
            description=f"OWPML {section.namespace_version} namespace schema",
        )
        component_counts["schema"] += 1
        for node, path in iter_tree_paths(section.root)[1:]:
            kind = tag_local_name(node.tag)
            if kind == "import" or kind == "include":
                name = node.attrib.get("schemaLocation") or node.attrib.get("namespace")
                if not name:
                    raise ExtractionError(
                        f"appendix {section.appendix} has an unnamed {kind} declaration"
                    )
            elif kind in DECLARATION_KINDS:
                name = node.attrib.get("name") or node.attrib.get("ref")
                if not name:
                    # Anonymous inline types are represented by their owning declaration.
                    continue
            else:
                continue
            append(
                locator_value=(
                    f"appendix:{section.appendix}|namespace:{section.namespace}|"
                    f"kind:{kind}|path:{path}"
                ),
                section=section_label,
                original_name=normalize_text(name),
                description=component_description(node),
            )
            component_counts[kind] += 1

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    violations = [
        f"record {index}: {violation.message}"
        for index, record in enumerate(records)
        for violation in validator.iter_errors(record)
    ]
    if violations:
        raise ExtractionError("generated SourceRecord validation failed: " + "; ".join(violations[:20]))
    coverage = {
        "section_count": len(document["title"]),
        "appendices": [section.appendix for section in sections],
        "namespaces": [section.namespace for section in sections],
        "namespace_versions": sorted({section.namespace_version for section in sections}),
        "glossary_replacement_count": sum(
            section.glossary_replacements for section in sections
        ),
        "component_counts": dict(sorted(component_counts.items())),
        "optional_package_part_count": sum(part.optional for part in package_parts),
    }
    return records, coverage


def serialize_records(records: list[dict]) -> bytes:
    return (json.dumps(records, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def run(config: ExtractionConfig) -> dict:
    source_lock_id, entry = load_source_entry(config.source_lock, config.source_id)
    if entry["license_state"] == "restricted" and os.path.normcase(
        str(config.output_root.absolute())
    ) != os.path.normcase(
        str((REPOSITORY_ROOT / "implementation" / "p02" / "evidence").absolute())
    ):
        raise ExtractionError("restricted sources may publish only to implementation/p02/evidence")
    content = read_regular_file(config.input_path, MAX_INPUT_BYTES)
    actual_sha256 = hashlib.sha256(content).hexdigest()
    if actual_sha256 != entry["sha256"]:
        raise ExtractionError(
            f"source SHA-256 mismatch: expected {entry['sha256']}, actual {actual_sha256}"
        )
    document = decode_machine_standard(content)
    records, coverage = build_records(
        source_lock_id, config.source_id, actual_sha256, document
    )
    payload = serialize_records(records)
    if read_regular_file(config.input_path, MAX_INPUT_BYTES) != content:
        raise ExtractionError("source changed during extraction")
    output = resolve_output(config.output_root, config.output_relative)
    publish_no_overwrite(output, payload)
    return {
        "schema_version": "hwpx-agent.owpml-extraction-receipt/v1",
        "source_lock_id": source_lock_id,
        "source_id": config.source_id,
        "source_sha256": actual_sha256,
        "license_state": entry["license_state"],
        "record_count": len(records),
        "coverage": coverage,
        "output_relative": config.output_relative,
        "output_sha256": hashlib.sha256(payload).hexdigest(),
        "source_modified": False,
        "raw_xml_published": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-lock", type=Path, required=True)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--output-relative", required=True)
    arguments = parser.parse_args()
    try:
        receipt = run(
            ExtractionConfig(
                source_lock=arguments.source_lock,
                source_id=arguments.source_id,
                input_path=arguments.input,
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
