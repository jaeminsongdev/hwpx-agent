#!/usr/bin/env python3
"""Bind P09-19 case readback to real lifecycle traces, retaining failures."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import zipfile
from xml.etree import ElementTree

# Reuse the frozen lifecycle verifier; do not reinterpret the old P09-17 fixture.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import inspect_field_object_caption_target as oracle
import qualify_field_auto_number_target as lifecycle

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "hwpx-agent.p09-19-object-caption-number-target-qualification/v1"
SOURCES = (
    "tools/p09/qualify_field_object_caption_target.py",
    "tools/p09/tests/test_field_object_caption_target_qualification.py",
    "tools/p09/inspect_field_object_caption_target.py",
    "tools/p09/qualify_field_auto_number_target.py",
    "implementation/p09/tools/run-hancom-2020-field-auto-number-target.ps1",
    "crates/hwpx-package/src/field_object_caption_hwpx.rs",
    "crates/hwpx-package/src/field_auto_number_hwpx.rs",
)
PRIVACY_KEYS = (
    "raw_document_text_present", "user_document_scanned", "external_network_invoked",
    "registry_or_system_setting_changed", "computer_use_click_or_type_invoked",
)


def within(path: Path, boundary: Path) -> Path:
    absolute = path.absolute()
    if any(p.is_symlink() or p.is_junction() for p in (absolute, *absolute.parents)):
        raise ValueError("linked_evidence_rejected")
    absolute.resolve(strict=True).relative_to(boundary.resolve(strict=True))
    return absolute


def verify_attempt(trace: dict, row: dict) -> bool:
    """A failed Open remains an independently identified failure, not a skipped case."""
    expected = {
        "input_package_sha256": row["output_package_sha256"],
        "input_package_bytes": row["output_package_bytes"],
    }
    if trace.get("state") == "pass":
        lifecycle.verify_trace(trace, expected)
        return True
    if (
        trace.get("schema_version") != "hwpx-agent.p09-17-field-auto-number-target-trace/v1"
        or trace.get("target") != {**lifecycle.TARGET, "prog_id": "HWPFrame.HwpObject.2"}
        or trace.get("input_sha256") != expected["input_package_sha256"]
        or type(trace.get("input_bytes")) is not int
        or trace.get("input_bytes") != expected["input_package_bytes"]
        or trace.get("state") != "effect_unknown"
        or trace.get("failed_phase") != "first_open"
        or trace.get("error_code") != "P09_FIELD_AUTO_NUMBER_TARGET_FIRST_OPEN_FAILED"
        or any(trace.get(key) != "not_run" for key in lifecycle.LIFECYCLE_KEYS)
        or trace.get("quit_invoked") is not False
        or type(trace.get("remaining_hwp_process_count")) is not int
        or trace.get("remaining_hwp_process_count") != 0
        or any(trace.get(key) is not False for key in PRIVACY_KEYS)
        or trace.get("security_module") != {
            "name": "FilePathCheckerModuleExample",
            "sha256": "9ac5b97c47ac8aed1e8bca27a3eef39411361d8f68c262509f0c40a8f9d21bb6",
            "preflight_state": "pass",
        }
    ):
        raise ValueError("failed_lifecycle_identity_mismatch")
    sessions = trace.get("sessions")
    if not isinstance(sessions, list) or len(sessions) != 1:
        raise ValueError("failed_lifecycle_sessions_mismatch")
    session = sessions[0]
    process = session.get("process", {})
    if (
        session.get("label") != "save" or session.get("version") != lifecycle.TARGET["build"]
        or type(session.get("register_module_return")) is not bool
        or process.get("executable_sha256") != lifecycle.TARGET["executable_sha256"]
        or type(process.get("process_id")) is not int or process["process_id"] <= 0
    ):
        raise ValueError("failed_lifecycle_process_mismatch")
    for key in ("output_sha256", "output_bytes", "pdf_sha256", "pdf_bytes",
                "reopened_sha256", "reopened_bytes", "reopened_pdf_sha256", "reopened_pdf_bytes"):
        if trace.get(key) is not None:
            raise ValueError("failed_open_output_claim_rejected")
    return False


def qualify(manifest_path: Path, manifest_digest: str, case_id: str, attempt: Path,
            trace_digest: str, *, root: Path = ROOT, access_attested: bool = False) -> dict:
    manifest_path = within(manifest_path, root / "fixtures/target-build")
    attempt = within(attempt, root / "implementation/p09/evidence/private")
    manifest = oracle.load_manifest(manifest_path, manifest_digest)
    row = next((r for r in manifest["cases"] if r["case_id"] == case_id), None)
    if row is None:
        raise ValueError("case_identity_invalid")
    source = oracle.inspect(manifest_path.parent / row["file"], manifest, case_id, "input")
    if source["state"] != "pass":
        raise ValueError("input_oracle_failed")
    trace = lifecycle.checked_json(attempt / "target-trace.json", trace_digest)
    passed = verify_attempt(trace, row)
    snapshots = {}
    pdfs = {}
    if passed:
        for stage, prefix in (("saved", "output"), ("reopened", "reopened")):
            path = attempt / (stage + ".hwpx")
            raw = oracle.bounded_bytes(path, oracle.MAX_PACKAGE)
            if type(trace.get(prefix + "_bytes")) is not int or len(raw) != trace[prefix + "_bytes"]:
                raise ValueError("output_size_mismatch")
            snapshots[stage] = oracle.inspect(path, manifest, case_id, stage,
                                               lifecycle.digest(trace.get(prefix + "_sha256")))
        for name, prefix in (("saved.pdf", "pdf"), ("reopened.pdf", "reopened_pdf")):
            raw = oracle.bounded_bytes(attempt / name, 32 * 1024 * 1024)
            if (not raw.startswith(b"%PDF-") or oracle.sha256(raw) != lifecycle.digest(trace.get(prefix + "_sha256"))
                    or type(trace.get(prefix + "_bytes")) is not int or len(raw) != trace[prefix + "_bytes"]):
                raise ValueError("pdf_identity_mismatch")
            pdfs[name] = {"sha256": oracle.sha256(raw), "bytes": len(raw), "signature": "pass"}
    elif any((attempt / name).exists() for name in ("saved.hwpx", "reopened.hwpx", "saved.pdf", "reopened.pdf")):
        raise ValueError("failed_open_untraced_output_rejected")
    matched = passed and all(v["state"] == "pass" for v in snapshots.values())
    return {
        "schema_version": SCHEMA, "task": "P09-19", "case_id": case_id,
        "target": lifecycle.TARGET,
        "state": ("bounded_semantic_non_green" if matched else
                  "failed_semantic_non_green" if passed else "failed_lifecycle_non_green"),
        "fixture_manifest_sha256": manifest_digest, "lifecycle_trace_sha256": trace_digest,
        "source_sha256": {p: oracle.sha256(oracle.bounded_bytes(root / p, 2 * 1024 * 1024)) for p in SOURCES},
        "input": source, "snapshots": snapshots, "pdf_identity": pdfs,
        "lifecycle": {key: trace[key] for key in lifecycle.LIFECYCLE_KEYS},
        "failed_phase": trace["failed_phase"], "error_code": trace["error_code"],
        "remaining_hwp_process_count_at_run": trace["remaining_hwp_process_count"],
        "register_module_returns": [s["register_module_return"] for s in trace["sessions"]],
        "user_access": {"state": "user_attested" if access_attested else "not_attested",
                        "scope": "permission_interaction_only_not_product_validation"},
        "claims": {
            "actual_open_save_fresh_reopen": passed,
            "bounded_object_caption_recalculation_19_to_1": matched,
            "general_numbering_algorithm_qualified": False,
            "product_field_update_api_qualified": False,
            "render": "not_run", "automation_fallback": "not_run", "differential": "not_run",
            "dependency_source_gate": "held_shared_lib_identity",
            "green_rows": 0, "p09_complete": False, "product_complete": False,
        },
        "privacy": {"absolute_private_paths": False, "raw_document_text_present": False,
                    "user_document_scanned": False, "external_network_invoked": False},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--expected-manifest-sha256", required=True)
    parser.add_argument("--case", required=True, choices=list(oracle.CASES))
    parser.add_argument("--attempt", required=True, type=Path)
    parser.add_argument("--expected-trace-sha256", required=True)
    parser.add_argument("--user-access-attested", action="store_true")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--output", type=Path)
    group.add_argument("--verify", type=Path)
    args = parser.parse_args()
    try:
        result = qualify(args.manifest, args.expected_manifest_sha256, args.case,
                         args.attempt, args.expected_trace_sha256, access_attested=args.user_access_attested)
        encoded = lifecycle.canonical_bytes(result)
        if args.output:
            destination = args.output.absolute()
            within(destination.parent, ROOT / "implementation/p09/evidence")
            if destination.is_symlink() or destination.is_junction() or "private" in destination.relative_to(ROOT).parts:
                raise ValueError("public_output_boundary_rejected")
            with destination.open("xb") as handle:
                handle.write(encoded)
        if args.verify and oracle.bounded_bytes(args.verify, 256 * 1024) != encoded:
            raise ValueError("qualification_record_mismatch")
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, zipfile.BadZipFile, ElementTree.ParseError) as error:
        code = str(error) if type(error) is ValueError and re.fullmatch(r"[a-z_]+", str(error)) else "qualification_failed"
        print(json.dumps({"state": "fail", "error_code": code}))
        return 2
    print(json.dumps({"state": "pass", "case_id": args.case, "qualification_state": result["state"],
                      "qualification_sha256": oracle.sha256(encoded), "claims": result["claims"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
