#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError as error:
    print(f"required dependency missing: {error}", file=sys.stderr)
    raise SystemExit(2) from error

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "protocol" / "json-schema" / "source-record-v1.schema.json"
SAMPLES = ROOT / "fixtures" / "synthetic" / "p02-source-records"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def semantic_errors(record: dict) -> list[str]:
    errors: list[str] = []
    availability = record.get("availability", {})
    if not isinstance(availability, dict):
        return errors
    minimum = availability.get("minimum_version")
    maximum = availability.get("maximum_version")
    if isinstance(minimum, str) and isinstance(maximum, str):
        try:
            minimum_parts = tuple(int(part) for part in minimum.split("."))
            maximum_parts = tuple(int(part) for part in maximum.split("."))
        except ValueError:
            pass  # lexical version errors are reported by JSON Schema
        else:
            width = max(len(minimum_parts), len(maximum_parts))
            normalized_minimum = minimum_parts + (0,) * (width - len(minimum_parts))
            normalized_maximum = maximum_parts + (0,) * (width - len(maximum_parts))
            if normalized_minimum > normalized_maximum:
                errors.append("minimum_version is greater than maximum_version")
    parameters = record.get("parameters", [])
    if isinstance(parameters, list):
        ordinals = [
            parameter.get("ordinal")
            for parameter in parameters
            if isinstance(parameter, dict)
        ]
        if ordinals != list(range(len(parameters))):
            errors.append("parameter ordinals must be unique and contiguous from zero")
    if availability.get("support_scope") == "runtime_observed" and minimum != maximum:
        errors.append("runtime_observed records must bind one exact version")
    return errors


def main() -> int:
    errors: list[str] = []
    schema = load(SCHEMA_PATH)
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as error:  # jsonschema reports heterogeneous schema errors
        errors.append(f"schema compile failed: {error}")
    validator = Draft202012Validator(schema, format_checker=FormatChecker())

    samples = sorted(SAMPLES.glob("*.json"))
    if len(samples) < 5:
        errors.append(f"expected at least five source-record samples, found {len(samples)}")
    records = [load(path) for path in samples]
    for path, record in zip(samples, records, strict=True):
        violations = sorted(validator.iter_errors(record), key=lambda item: list(item.path))
        errors.extend(
            f"sample {path.relative_to(ROOT)}: {violation.message}" for violation in violations
        )
        errors.extend(
            f"sample {path.relative_to(ROOT)}: {violation}"
            for violation in semantic_errors(record)
        )

    record_ids = [record.get("record_id") for record in records]
    if len(record_ids) != len(set(record_ids)):
        errors.append("sample record_id values are not unique")
    covered_kinds = {record.get("source_kind") for record in records}
    required_kinds = {"help", "pdf", "xsd", "action_table", "runtime"}
    if not required_kinds.issubset(covered_kinds):
        errors.append(f"sample source kinds missing: {sorted(required_kinds - covered_kinds)}")

    if records:
        valid = next(
            (record for record in records if record.get("source_kind") == "help"),
            None,
        )
        if valid is None:
            errors.append("help sample is required for negative-case derivation")
            valid = records[0]
        negatives: dict[str, dict] = {}

        candidate = deepcopy(valid)
        candidate.pop("source_sha256", None)
        negatives["missing_source_hash"] = candidate

        candidate = deepcopy(valid)
        candidate["source_sha256"] = "ABC"
        negatives["malformed_source_hash"] = candidate

        candidate = deepcopy(valid)
        candidate["unexpected"] = True
        negatives["unknown_root_property"] = candidate

        candidate = deepcopy(valid)
        candidate["source_kind"] = "xsd"
        candidate["locator"] = {"kind": "page", "page": 1}
        negatives["xsd_page_locator"] = candidate

        candidate = deepcopy(valid)
        candidate["source_kind"] = "pdf"
        candidate["locator"] = {"kind": "page", "page": 1, "value": "ambiguous"}
        negatives["page_with_value"] = candidate

        candidate = deepcopy(valid)
        candidate["source_kind"] = "runtime"
        candidate["locator"] = {"kind": "runtime_probe", "value": "probe"}
        candidate["availability"] = {
            **candidate["availability"],
            "support_scope": "runtime_observed",
            "target_profile_id": None,
        }
        negatives["runtime_without_target"] = candidate

        candidate = deepcopy(valid)
        candidate["parameters"] = [
            {
                "ordinal": 0,
                "original_name": "SyntheticParameter",
                "declared_type": None,
                "required": None,
                "description_ko": None,
            }
        ]
        negatives["parameter_without_direction"] = candidate

        candidate = deepcopy(valid)
        candidate["locator"] = {"kind": "automation_item", "value": "wrong-kind"}
        negatives["help_automation_locator"] = candidate

        candidate = deepcopy(valid)
        candidate["availability"] = {
            **candidate["availability"],
            "minimum_version": "13.0.0.0",
            "maximum_version": "11.0.0.0",
        }
        negatives["reversed_build_range"] = candidate

        candidate = deepcopy(valid)
        candidate["parameters"] = [
            {
                "ordinal": 1,
                "original_name": "SyntheticParameter",
                "declared_type": None,
                "direction": "unknown",
                "required": None,
                "description_ko": None,
            }
        ]
        negatives["noncontiguous_parameter_ordinal"] = candidate

        for name, candidate in negatives.items():
            if validator.is_valid(candidate) and not semantic_errors(candidate):
                errors.append(f"negative source record unexpectedly valid: {name}")

    result = {
        "schema": str(SCHEMA_PATH.relative_to(ROOT)).replace("\\", "/"),
        "valid_samples": len(records),
        "source_kinds_covered": sorted(covered_kinds),
        "negative_cases": len(negatives) if records else 0,
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
