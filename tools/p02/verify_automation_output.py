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

from tools.p02.extract_automation_pdfs import (
    EXTRACTOR_ID,
    EXTRACTOR_VERSION,
    MAX_INPUT_BYTES,
    SCHEMA_PATH,
    SOURCE_SPECS,
    load_pdf_source_entry,
)
from tools.p02.extract_help import read_regular_file
from tools.p02.validate_source_records import semantic_errors

PAGE_LOCATOR = re.compile(
    r"^(action_table|parameter_table|automation_object|automation_event)/"
    r"p(\d{6})(?:-p(\d{6}))?$"
)


def verify(
    output_path: Path,
    source_lock_path: Path,
    source_ids: dict[str, str],
    source_inputs: dict[str, Path],
) -> dict:
    errors: list[str] = []
    source_lock_snapshot = read_regular_file(source_lock_path, 8 * 1024 * 1024)
    expected: dict[str, dict] = {}
    expected_by_source_id: dict[str, dict] = {}
    source_lock_ids: set[str] = set()
    for source_kind, _, _ in SOURCE_SPECS:
        source_id = source_ids[source_kind]
        source_lock_id, entry = load_pdf_source_entry(source_lock_path, source_id)
        source_lock_ids.add(source_lock_id)
        content = read_regular_file(source_inputs[source_kind], MAX_INPUT_BYTES)
        actual_sha256 = hashlib.sha256(content).hexdigest()
        if actual_sha256 != entry["sha256"]:
            errors.append(f"{source_kind}: source input does not match locked SHA-256")
        expected[source_kind] = {
            "source_id": source_id,
            "source_sha256": entry["sha256"],
        }
        expected_by_source_id[source_id] = {
            "source_sha256": entry["sha256"],
            "input_role": source_kind,
        }
    if len(source_lock_ids) != 1:
        errors.append("source-lock IDs are not identical across PDF sources")
        source_lock_id = ""
    else:
        source_lock_id = next(iter(source_lock_ids))

    output = read_regular_file(output_path, MAX_INPUT_BYTES)
    try:
        decoded_output = output.decode("utf-8")
        if "\ufffd" in decoded_output:
            errors.append("output contains Unicode replacement characters")
        records = json.loads(decoded_output)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        records = []
        errors.append(f"output is not valid UTF-8 JSON: {error}")
    if not isinstance(records, list) or not records:
        errors.append("output must be a non-empty SourceRecord array")
        records = []

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    page_coverage: dict[str, set[int]] = {
        source_id: set() for source_id in expected_by_source_id
    }
    record_ids: list[str] = []
    identities: list[tuple[str, str, str]] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"record {index} is not an object")
            continue
        errors.extend(
            f"record {index}: {violation.message}"
            for violation in validator.iter_errors(record)
        )
        errors.extend(f"record {index}: {violation}" for violation in semantic_errors(record))
        source_kind = record.get("source_kind")
        if source_kind not in expected:
            errors.append(f"record {index}: unexpected source_kind {source_kind!r}")
            continue
        counts[source_kind] += 1
        source_id = record.get("source_id")
        source_expectation = expected_by_source_id.get(str(source_id))
        allowed_source_ids = {expected[source_kind]["source_id"]}
        if source_kind == "automation_event":
            allowed_source_ids.add(expected["automation_object"]["source_id"])
        if source_id not in allowed_source_ids or source_expectation is None:
            errors.append(f"record {index}: source_id mismatch")
            continue
        source_counts[str(source_id)] += 1
        if record.get("source_lock_id") != source_lock_id:
            errors.append(f"record {index}: source_lock_id mismatch")
        if record.get("source_sha256") != source_expectation["source_sha256"]:
            errors.append(f"record {index}: source_sha256 mismatch")
        if record.get("extraction") != {
            "extractor_id": EXTRACTOR_ID,
            "extractor_version": EXTRACTOR_VERSION,
            "record_ordinal": index,
        }:
            errors.append(f"record {index}: extraction identity/ordinal mismatch")
        if record.get("availability", {}).get("support_scope") != "documentation_only":
            errors.append(f"record {index}: PDF metadata must remain documentation_only")
        locator = record.get("locator", {})
        if locator.get("kind") != "automation_item":
            errors.append(f"record {index}: locator kind mismatch")
        locator_match = PAGE_LOCATOR.fullmatch(str(locator.get("value", "")))
        if not locator_match or locator_match.group(1) != source_kind:
            errors.append(f"record {index}: invalid page locator")
        else:
            start = int(locator_match.group(2))
            end = int(locator_match.group(3) or locator_match.group(2))
            if start > end:
                errors.append(f"record {index}: reversed page range")
            else:
                page_coverage[str(source_id)].update(range(start, end + 1))
        section = locator.get("section")
        anchor = locator.get("anchor")
        if not isinstance(section, str) or not section:
            errors.append(f"record {index}: missing section locator")
        if anchor != record.get("original_name"):
            errors.append(f"record {index}: anchor/original_name mismatch")
        if source_kind == "parameter_table":
            parameters = record.get("parameters", [])
            if len(parameters) != 1 or not parameters[0].get("declared_type"):
                errors.append(f"record {index}: parameter item lacks declared type")
        record_ids.append(str(record.get("record_id", "")))
        identities.append((str(source_id), str(section), str(anchor)))
    if len(record_ids) != len(set(record_ids)):
        errors.append("record_id values are not unique")
    if len(identities) != len(set(identities)):
        errors.append("source kind/section/anchor identities are not unique")
    for source_kind in expected:
        if counts[source_kind] == 0:
            errors.append(f"no records for {source_kind}")
    for source_id in expected_by_source_id:
        if source_counts[source_id] == 0:
            errors.append(f"no records for source {source_id}")
    if read_regular_file(source_lock_path, 8 * 1024 * 1024) != source_lock_snapshot:
        errors.append("source lock changed during verification")

    return {
        "schema_version": "hwpx-agent.automation-pdf-extraction-verification/v1",
        "source_lock_id": source_lock_id,
        "output_sha256": hashlib.sha256(output).hexdigest(),
        "record_count": len(records),
        "record_counts": dict(sorted(counts.items())),
        "source_record_counts": dict(sorted(source_counts.items())),
        "page_coverage": {
            source_kind: sorted(pages) for source_kind, pages in page_coverage.items()
        },
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-lock", type=Path, required=True)
    for source_kind, id_field, path_field in SOURCE_SPECS:
        parser.add_argument(f"--{id_field.replace('_', '-')}", required=True)
        parser.add_argument(f"--{path_field.replace('_', '-')}", type=Path, required=True)
    arguments = parser.parse_args()
    values = vars(arguments)
    source_ids = {
        source_kind: values[id_field] for source_kind, id_field, _ in SOURCE_SPECS
    }
    source_inputs = {
        source_kind: values[path_field] for source_kind, _, path_field in SOURCE_SPECS
    }
    try:
        result = verify(arguments.output, arguments.source_lock, source_ids, source_inputs)
    except Exception as error:
        print(json.dumps({"state": "failed", "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
