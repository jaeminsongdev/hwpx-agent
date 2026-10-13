#!/usr/bin/env python3
"""Read-only object-bound number oracle; snapshot matching is not lifecycle proof."""
from __future__ import annotations

import argparse
import io
import json
from pathlib import Path
import re
import sys
import zipfile
from xml.etree import ElementTree as ET

if __package__:
    from .inspect_field_auto_number_target import bounded_bytes, sha256
    from .validate_field_auto_number_hwpx_contract import duplicate_guard
else:
    from inspect_field_auto_number_target import bounded_bytes, sha256
    from validate_field_auto_number_hwpx_contract import duplicate_guard

NS = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
SECTION = "Contents/section0.xml"
SCHEMA = "hwpx-agent.p09-object-caption-number-target-oracle/v1"
MAX_PACKAGE = 4 * 1024 * 1024
MAX_PART = 2 * 1024 * 1024
DIGEST = re.compile(r"^[0-9a-f]{64}$")
EXPECTATION = "first_object_of_its_category_in_isolated_seed_model_hypothesis_target_unqualified"
CASES = {
    "P09-19-C01": ("rect", 8101, "PICTURE", {"rect": 1}, "659b31bc1f5f86ee46756ea683258e03ba75515179af2f5377a953a108eafbf7"),
    "P09-19-C02": ("pic", 8102, "PICTURE", {"pic": 1}, "e7a202dd4ff75e0cda74681e99d8aec4c490a68189f8c0d658a2b2ea764d857c"),
    "P09-19-C03": ("tbl", 1188510574, "TABLE", {"tbl": 2}, "b6d000efb0076f3b63ea7247601e8efc366f215f91c5d35927ca92de5c7b8021"),
    "P09-19-C04": ("equation", 1192022476, "EQUATION", {"equation": 1}, "a774bf918c5bd57a1b86531e34ea6bc6f62d4b41d74213090358b657a38f224d"),
}
FILES = {
    "P09-19-C01": "p09-19-c01-rectangle-caption-number.hwpx",
    "P09-19-C02": "p09-19-c02-picture-caption-number.hwpx",
    "P09-19-C03": "p09-19-c03-table-caption-number.hwpx",
    "P09-19-C04": "p09-19-c04-equation-caption-number.hwpx",
}
OBJECT_TAGS = ("rect", "pic", "tbl", "equation", "ellipse", "line", "arc", "polygon", "curve", "connectLine")


def exact(value: object, expected: object) -> bool:
    return json.dumps(value, sort_keys=True, allow_nan=False) == json.dumps(expected, sort_keys=True, allow_nan=False)


def load_manifest(path: Path, expected_sha256: str) -> dict:
    if not DIGEST.fullmatch(expected_sha256):
        raise ValueError("manifest_digest_invalid")
    raw = bounded_bytes(path, 1024 * 1024)
    if sha256(raw) != expected_sha256:
        raise ValueError("manifest_digest_mismatch")
    value = json.loads(raw, object_pairs_hook=duplicate_guard)
    if not isinstance(value, dict) or value.get("schema_version") != "hwpx-agent.p09-object-caption-number-target-fixture/v1" or value.get("task") != "P09-19":
        raise ValueError("manifest_identity_invalid")
    for key, expected in {
        "static_evidence": {"complete_package_graph": True, "original_object_payloads_and_resources_preserved": True, "cached_result_is_not_target_recalculation_proof": True},
        "fixture_caption_attachment_is_not_product_caption_creation": True,
        "actual_hangul": False, "semantic_save_reopen": "not_run", "render": "not_run",
        "differential": "not_run", "green_rows": 0, "product_complete": False,
    }.items():
        if not exact(value.get(key), expected):
            raise ValueError("manifest_claim_promotion")
    rows = value.get("cases")
    if not isinstance(rows, list) or len(rows) != 4 or [row.get("case_id") for row in rows if isinstance(row, dict)] != list(CASES):
        raise ValueError("manifest_cases_invalid")
    for row in rows:
        name, native_id, kind, counts, seed_digest = CASES[row["case_id"]]
        checks = {
            "file": FILES[row["case_id"]],
            "object_tag": name, "native_object_id": native_id, "numbering_type": kind,
            "object_counts": counts, "source_package_sha256": seed_digest,
            "feature_ids": ["REF-008", "REF-009"], "input_cached_number": 19,
            "expected_saved_number": 1, "expectation_basis": EXPECTATION,
            "non_field_section_restores_to_seed": True,
            "retry_checks": {"stale_source_rejected": True, "deterministic_retry": True},
            "fixture_caption_attached_from_seed": row["case_id"] != "P09-19-C01",
            "fixture_none_numbering_type_assigned": row["case_id"] == "P09-19-C01",
        }
        if any(not exact(row.get(key), expected) for key, expected in checks.items()):
            raise ValueError("manifest_case_contract_mismatch")
        for key in ("output_package_sha256", "output_section_sha256", "composition_plan_sha256", "inner_plan_sha256", "caption_sha256"):
            if not isinstance(row.get(key), str) or not DIGEST.fullmatch(row[key]):
                raise ValueError("manifest_case_digest_invalid")
        parts = row.get("unrelated_parts_sha256")
        if not isinstance(parts, dict) or not parts or any(not isinstance(k, str) or not isinstance(v, str) or not DIGEST.fullmatch(v) for k, v in parts.items()):
            raise ValueError("manifest_inventory_invalid")
    return value


def package_snapshot(path: Path, expected_digest: str | None) -> tuple[bytes, str, dict[str, str]]:
    raw = bounded_bytes(path, MAX_PACKAGE)
    digest = sha256(raw)
    if expected_digest is not None and (not DIGEST.fullmatch(expected_digest) or digest != expected_digest):
        raise ValueError("package_sha256_mismatch")
    parts: dict[str, str] = {}
    section = b""
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        entries = archive.infolist()
        if not 0 < len(entries) <= 64 or sum(entry.file_size for entry in entries) > 8 * 1024 * 1024:
            raise ValueError("package_bounds_invalid")
        if len({entry.filename for entry in entries}) != len(entries):
            raise ValueError("package_duplicate_entry")
        for entry in entries:
            name = entry.filename
            if entry.is_dir() or entry.flag_bits & 1 or "\\" in name or ":" in name or name.startswith("/") or any(part in ("", ".", "..") for part in name.split("/")) or not 0 <= entry.file_size <= MAX_PART:
                raise ValueError("package_entry_invalid")
            data = archive.read(entry)
            if name == SECTION:
                section = data
            else:
                parts[name] = sha256(data)
    if not section or b"<!doctype" in section.lower() or b"<!entity" in section.lower():
        raise ValueError("section_invalid")
    return section, digest, parts


def inspect(path: Path, manifest: dict, case_id: str, stage: str, expected_sha256: str | None = None) -> dict:
    if case_id not in CASES or stage not in ("input", "saved", "reopened"):
        raise ValueError("case_or_stage_invalid")
    row = next(value for value in manifest["cases"] if value["case_id"] == case_id)
    if stage == "input":
        if expected_sha256 is not None and expected_sha256 != row["output_package_sha256"]:
            raise ValueError("input_digest_override_rejected")
        expected_sha256 = row["output_package_sha256"]
    section, digest, parts = package_snapshot(path, expected_sha256)
    root = ET.fromstring(section)
    if root.tag != "{http://www.hancom.co.kr/hwpml/2011/section}sec":
        raise ValueError("section_root_invalid")
    parents = {child: parent for parent in root.iter() for child in parent}
    counts = {name: len(list(root.iter(NS + name))) for name in OBJECT_TAGS}
    counts = {key: value for key, value in counts.items() if value}
    errors = []
    if counts != row["object_counts"]:
        errors.append("native_object_inventory_mismatch")
    objects = [n for n in root.iter(NS + row["object_tag"]) if n.get("id") == str(row["native_object_id"])]
    if len(objects) != 1:
        raise ValueError("selected_object_identity_invalid")
    obj = objects[0]
    if obj.get("numberingType") != row["numbering_type"] or obj.get("lock") != "0" or parents[obj].tag != NS + "run":
        errors.append("native_object_kind_or_lock_mismatch")
    captions = [n for n in obj if n.tag == NS + "caption"]
    if len(captions) != 1 or len(list(captions[0].iter(NS + "subList"))) != 1:
        raise ValueError("selected_caption_invalid")
    numbers = list(root.iter(NS + "autoNum"))
    if len(numbers) != 1 or numbers[0] not in set(captions[0].iter()):
        raise ValueError("object_caption_number_binding_invalid")
    number = numbers[0]
    value = number.get("num", "")
    if not re.fullmatch(r"0|[1-9][0-9]*", value) or int(value) > 2147483647:
        raise ValueError("number_lexical_shape_invalid")
    wrapper = parents[number]
    if wrapper.tag != NS + "ctrl" or parents[wrapper].tag != NS + "run" or len(wrapper) != 1:
        errors.append("number_anchor_invalid")
    if set(number.attrib) != {"num", "numType"} or number.get("numType") != row["numbering_type"] or len(number) != 1:
        errors.append("number_kind_or_shape_invalid")
    fmt = number[0] if len(number) == 1 else None
    if fmt is None or fmt.tag != NS + "autoNumFormat" or len(fmt) != 0 or (fmt.text or "").strip() or fmt.attrib != {"type": "DIGIT", "userChar": "", "prefixChar": "", "suffixChar": "", "supscript": "0"}:
        errors.append("number_format_invalid")
    expected = row["input_cached_number"] if stage == "input" else row["expected_saved_number"]
    if int(value) != expected:
        errors.append("cached_number_mismatch" if stage == "input" else "application_number_expectation_mismatch")
    if stage == "input" and (sha256(section) != row["output_section_sha256"] or parts != row["unrelated_parts_sha256"]):
        errors.append("prepared_fixture_preservation_mismatch")
    assets = {key: value for key, value in row["unrelated_parts_sha256"].items() if key.lower().startswith("bindata/")}
    if any(parts.get(key) != value for key, value in assets.items()):
        errors.append("binary_resource_integrity_mismatch")
    return {
        "schema_version": SCHEMA, "state": "fail" if errors else "pass", "errors": sorted(set(errors)),
        "case_id": case_id, "stage": stage, "package_sha256": digest, "section_sha256": sha256(section),
        "native_object_counts": counts, "caption_number": int(value), "expected_number": expected,
        "caption_object_binding": not any("binding" in error or "identity" in error for error in errors),
        "expectation_basis": EXPECTATION, "model_expectation_target_qualified": False,
        "actual_hangul": False, "lifecycle_qualification": "not_run", "render": "not_run",
        "differential": "not_run", "green_rows": 0, "p09_complete": False, "product_complete": False,
        "raw_document_text_present": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("package", type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--expected-manifest-sha256", required=True)
    parser.add_argument("--case", required=True, choices=list(CASES))
    parser.add_argument("--stage", choices=["input", "saved", "reopened"], default="input")
    parser.add_argument("--expected-sha256")
    args = parser.parse_args()
    try:
        manifest = load_manifest(args.manifest, args.expected_manifest_sha256)
        value = inspect(args.package, manifest, args.case, args.stage, args.expected_sha256)
    except (OSError, ValueError, UnicodeError, zipfile.BadZipFile, ET.ParseError):
        value = {"schema_version": SCHEMA, "state": "fail", "errors": ["bounded_input_or_contract_rejected"], "actual_hangul": False, "product_complete": False}
    print(json.dumps(value, sort_keys=True, separators=(",", ":")))
    return 0 if value["state"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
