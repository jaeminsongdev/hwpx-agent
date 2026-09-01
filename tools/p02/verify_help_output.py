#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator, FormatChecker

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from tools.p02.extract_help import MAX_INPUT_BYTES, SCHEMA_PATH, load_source_entry, read_regular_file
from tools.p02.validate_source_records import semantic_errors


def verify(output_path: Path, source_lock_path: Path, source_id: str, source_input: Path) -> dict:
    errors: list[str] = []
    output = read_regular_file(output_path, MAX_INPUT_BYTES)
    source = read_regular_file(source_input, MAX_INPUT_BYTES)
    source_lock_id, entry = load_source_entry(source_lock_path, source_id)
    source_sha256 = hashlib.sha256(source).hexdigest()
    if source_sha256 != entry["sha256"]:
        errors.append("source input does not match the locked SHA-256")
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
    record_ids: list[str] = []
    anchored = 0
    positioned = 0
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"record {index} is not an object")
            continue
        errors.extend(
            f"record {index}: {violation.message}" for violation in validator.iter_errors(record)
        )
        errors.extend(f"record {index}: {violation}" for violation in semantic_errors(record))
        if record.get("source_lock_id") != source_lock_id:
            errors.append(f"record {index}: source_lock_id mismatch")
        if record.get("source_id") != source_id:
            errors.append(f"record {index}: source_id mismatch")
        if record.get("source_sha256") != entry["sha256"]:
            errors.append(f"record {index}: source_sha256 mismatch")
        if record.get("source_kind") not in {"help", "webhwp"}:
            errors.append(f"record {index}: source_kind is not help/webhwp")
        if record.get("extraction", {}).get("record_ordinal") != index:
            errors.append(f"record {index}: extraction ordinal mismatch")
        record_ids.append(str(record.get("record_id", "")))
        locator = record.get("locator", {})
        if locator.get("kind") == "anchor":
            anchored += 1
        elif locator.get("kind") == "section" and "@L" in str(locator.get("value", "")):
            positioned += 1
        else:
            errors.append(f"record {index}: locator is neither original anchor nor source position")
    if len(record_ids) != len(set(record_ids)):
        errors.append("record_id values are not unique")

    return {
        "schema_version": "hwpx-agent.help-extraction-verification/v1",
        "source_lock_id": source_lock_id,
        "source_id": source_id,
        "source_sha256": entry["sha256"],
        "output_sha256": hashlib.sha256(output).hexdigest(),
        "record_count": len(records),
        "anchor_locator_count": anchored,
        "source_position_locator_count": positioned,
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
