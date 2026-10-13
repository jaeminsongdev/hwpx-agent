#!/usr/bin/env python3
"""Strict P09-20 successor for the failed P09-19 picture seed; no COM calls."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import zipfile
from xml.etree import ElementTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qualify_field_object_caption_target as shared

oracle = shared.oracle
lifecycle = shared.lifecycle
ROOT = shared.ROOT
CASE = "P09-19-C02"
CANONICAL = "implementation/p08/evidence/private/p08-20-object-target-20260915-18/obj-002-image-insert.hancom-2020-readback.hwpx"
CANONICAL_SHA = "12ea24d735c7c6db1eb92ce8260b617866307fd0ad2a30ac82be78d744f5dbef"
CAPTION = "fixtures/target-build/p08-19-object-target-complete-20260914-02/output/obj-019-margin-caption.hwpx"
CAPTION_SHA = "659b31bc1f5f86ee46756ea683258e03ba75515179af2f5377a953a108eafbf7"
SOURCES = (
    "tools/p09/qualify_canonical_picture_caption_target.py",
    "tools/p09/tests/test_canonical_picture_caption_target.py",
    "crates/hwpx-package/examples/p09_20_canonical_picture_number_target_fixture.rs",
    *shared.SOURCES,
)


def prepare(manifest_path: Path, expected: str, *, root: Path = ROOT) -> tuple[dict, dict]:
    shared.within(manifest_path, root / "fixtures/target-build")
    value = lifecycle.checked_json(manifest_path, expected)
    if (value.get("schema_version") != "hwpx-agent.p09-canonical-picture-caption-number-target-fixture/v1"
            or value.get("task") != "P09-20" or not isinstance(value.get("cases"), list)
            or len(value["cases"]) != 1 or value.get("caption_seed_relative") != CAPTION
            or value.get("caption_seed_package_sha256") != CAPTION_SHA):
        raise ValueError("canonical_manifest_identity_invalid")
    for key, required in {
        "actual_hangul": False, "semantic_save_reopen": "not_run", "render": "not_run",
        "differential": "not_run", "green_rows": 0, "product_complete": False,
        "fixture_caption_attachment_is_not_product_caption_creation": True,
        "static_evidence": {"complete_package_graph": True,
                            "original_object_payloads_and_resources_preserved": True,
                            "cached_result_is_not_target_recalculation_proof": True},
    }.items():
        if not oracle.exact(value.get(key), required):
            raise ValueError("canonical_manifest_claim_promotion")
    row = value["cases"][0]
    for key, required in {
        "case_id": CASE, "file": oracle.FILES[CASE], "source_relative": CANONICAL,
        "source_package_sha256": CANONICAL_SHA, "feature_ids": ["REF-008", "REF-009"],
        "object_tag": "pic", "native_object_id": 8102, "numbering_type": "PICTURE",
        "object_counts": {"pic": 1}, "input_cached_number": 19, "expected_saved_number": 1,
        "expectation_basis": oracle.EXPECTATION, "fixture_caption_attached_from_seed": True,
        "fixture_none_numbering_type_assigned": False, "non_field_section_restores_to_seed": True,
        "retry_checks": {"stale_source_rejected": True, "deterministic_retry": True},
    }.items():
        if not oracle.exact(row.get(key), required):
            raise ValueError("canonical_case_contract_invalid")
    for key in ("source_section_sha256", "prepared_caption_section_sha256", "output_package_sha256",
                "output_section_sha256", "composition_plan_sha256", "inner_plan_sha256", "caption_sha256"):
        lifecycle.digest(row.get(key))
    if type(row.get("output_package_bytes")) is not int or not 0 < row["output_package_bytes"] <= oracle.MAX_PACKAGE:
        raise ValueError("canonical_package_size_invalid")
    source, _, source_parts = oracle.package_snapshot(root / CANONICAL, CANONICAL_SHA)
    caption_source, _, _ = oracle.package_snapshot(root / CAPTION, CAPTION_SHA)
    section, _, parts = oracle.package_snapshot(manifest_path.parent / row["file"], row["output_package_sha256"])
    captions = re.findall(br"<hp:caption\b.*?</hp:caption>", caption_source, re.S)
    controls = re.findall(br"<hp:ctrl><hp:autoNum\b.*?</hp:ctrl>", section, re.S)
    if len(captions) != 1 or len(controls) != 1:
        raise ValueError("canonical_fixture_reversal_ambiguous")
    prepared = section.replace(controls[0], b"", 1)
    if prepared.count(captions[0]) != 1 or prepared.replace(captions[0], b"", 1) != source:
        raise ValueError("canonical_native_payload_preservation_failed")
    if (source_parts != parts or row.get("unrelated_parts_sha256") != source_parts
            or row["source_section_sha256"] != oracle.sha256(source)
            or row["prepared_caption_section_sha256"] != oracle.sha256(prepared)
            or len(oracle.bounded_bytes(manifest_path.parent / row["file"], oracle.MAX_PACKAGE)) != row["output_package_bytes"]):
        raise ValueError("canonical_resource_or_source_identity_failed")
    inspected = oracle.inspect(manifest_path.parent / row["file"], value, CASE, "input")
    if inspected["state"] != "pass":
        raise ValueError("canonical_input_oracle_failed")
    return value, inspected


def qualify(manifest_path: Path, expected: str, attempt: Path, trace_sha: str,
            *, root: Path = ROOT, access_attested: bool = False) -> dict:
    manifest, source = prepare(manifest_path, expected, root=root)
    shared.within(attempt, root / "implementation/p09/evidence/private")
    trace = lifecycle.checked_json(attempt / "target-trace.json", trace_sha)
    if not shared.verify_attempt(trace, manifest["cases"][0]):
        raise ValueError("canonical_target_lifecycle_failed")
    snapshots = {}
    pdfs = {}
    for stage, prefix in (("saved", "output"), ("reopened", "reopened")):
        raw = oracle.bounded_bytes(attempt / (stage + ".hwpx"), oracle.MAX_PACKAGE)
        if type(trace.get(prefix + "_bytes")) is not int or len(raw) != trace[prefix + "_bytes"]:
            raise ValueError("canonical_target_size_mismatch")
        snapshots[stage] = oracle.inspect(attempt / (stage + ".hwpx"), manifest, CASE, stage,
                                           lifecycle.digest(trace.get(prefix + "_sha256")))
    for name, prefix in (("saved.pdf", "pdf"), ("reopened.pdf", "reopened_pdf")):
        raw = oracle.bounded_bytes(attempt / name, 32 * 1024 * 1024)
        if (not raw.startswith(b"%PDF-") or oracle.sha256(raw) != lifecycle.digest(trace.get(prefix + "_sha256"))
                or type(trace.get(prefix + "_bytes")) is not int or len(raw) != trace[prefix + "_bytes"]):
            raise ValueError("canonical_pdf_identity_mismatch")
        pdfs[name] = {"sha256": oracle.sha256(raw), "bytes": len(raw), "signature": "pass"}
    matched = all(v["state"] == "pass" for v in snapshots.values())
    return {
        "schema_version": "hwpx-agent.p09-20-canonical-picture-caption-target-qualification/v1",
        "task": "P09-20", "case_id": CASE, "target": lifecycle.TARGET,
        "state": "bounded_semantic_non_green" if matched else "failed_semantic_non_green",
        "fixture_manifest_sha256": expected, "lifecycle_trace_sha256": trace_sha,
        "canonical_seed_sha256": CANONICAL_SHA,
        "source_sha256": {p: oracle.sha256(oracle.bounded_bytes(root / p, 2 * 1024 * 1024)) for p in SOURCES},
        "input": source, "snapshots": snapshots, "pdf_identity": pdfs,
        "lifecycle": {key: trace[key] for key in lifecycle.LIFECYCLE_KEYS},
        "user_access": {"state": "user_attested" if access_attested else "not_attested",
                        "scope": "permission_interaction_only_not_product_validation"},
        "register_module_returns": [s["register_module_return"] for s in trace["sessions"]],
        "remaining_hwp_process_count_at_run": trace["remaining_hwp_process_count"],
        "claims": {"actual_open_save_fresh_reopen": True,
                   "bounded_picture_caption_recalculation_19_to_1": matched,
                   "general_numbering_algorithm_qualified": False,
                   "product_field_update_api_qualified": False,
                   "render": "not_run", "automation_fallback": "not_run", "differential": "not_run",
                   "dependency_source_gate": "held_shared_lib_identity",
                   "green_rows": 0, "p09_complete": False, "product_complete": False},
        "privacy": {"absolute_private_paths": False, "raw_document_text_present": False,
                    "user_document_scanned": False, "external_network_invoked": False},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--expected-manifest-sha256", required=True)
    parser.add_argument("--attempt", type=Path)
    parser.add_argument("--expected-trace-sha256")
    parser.add_argument("--user-access-attested", action="store_true")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--output", type=Path)
    output.add_argument("--verify", type=Path)
    args = parser.parse_args()
    try:
        if args.attempt:
            value = qualify(args.manifest, args.expected_manifest_sha256, args.attempt,
                            args.expected_trace_sha256, access_attested=args.user_access_attested)
        else:
            if args.output or args.verify or args.expected_trace_sha256:
                raise ValueError("canonical_prepare_cannot_publish_target_record")
            _, inspected = prepare(args.manifest, args.expected_manifest_sha256)
            value = {"state": "static_preparation_only", "input": inspected}
        encoded = lifecycle.canonical_bytes(value)
        if args.output:
            destination = args.output.absolute()
            shared.within(destination.parent, ROOT / "implementation/p09/evidence")
            if destination.is_symlink() or destination.is_junction() or "private" in destination.relative_to(ROOT).parts:
                raise ValueError("canonical_public_output_boundary_rejected")
            with destination.open("xb") as handle:
                handle.write(encoded)
        if args.verify and oracle.bounded_bytes(args.verify, 256 * 1024) != encoded:
            raise ValueError("canonical_qualification_record_mismatch")
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, zipfile.BadZipFile, ElementTree.ParseError) as error:
        code = str(error) if type(error) is ValueError and re.fullmatch(r"[a-z_]+", str(error)) else "canonical_qualification_failed"
        print(json.dumps({"state": "fail", "error_code": code}))
        return 2
    print(json.dumps({"state": "pass", "qualification_state": value["state"],
                      "qualification_sha256": oracle.sha256(encoded), "green_rows": 0,
                      "p09_complete": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
