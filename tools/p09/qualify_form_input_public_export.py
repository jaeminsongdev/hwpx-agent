#!/usr/bin/env python3
"""Qualify the actual public atomic-input API; preserve legacy current failures."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.p09 import qualify_form_input_component as prior

ROOT = prior.ROOT
q, public = prior.q, prior.public
LIB = "crates/domain-ir/src/lib.rs"
ARCHIVE = "implementation/p09/source-archive/p09-38-pre-form-input-export/domain-ir-lib.rs"
OLD_LIB = prior.OLD_SOURCES[LIB]
CURRENT_LIB = "6f44e4baca13f0665abc6c2599bc4ab0ff559af11b02f37d7747a9334c5ccb85"
DELTA = b"pub mod form_input;\n"
CAPSULE = "implementation/p09/evidence/p09-37-atomic-form-input-component.current-2020.v1.json"
CAPSULE_SHA = "3075b4bc0c12e383a48d1c3dc0c6fb548612ac6054ab6afda3a3ec20383c21a0"
PUBLIC_TESTS = {
    "domain": ("crates/domain-ir/tests/form_input_public.rs", prior.SOURCES[1], b"use std::error::Error;", "domain-ir", "form_input_public", prior.DOMAIN_TESTS - prior.PRIVATE_TESTS),
    "actual_capture": ("crates/hwpx-package/tests/form_input_native_binding_public.rs", prior.SOURCES[2], b"use hwpx_package::*;", "hwpx-package", "form_input_native_binding_public", {prior.ACTUAL_TEST}),
}
HEADER = b"//! Complete predecessor scenarios through the real public atomic-input API only.\nuse domain_ir::form_input::*;\nuse domain_ir::*;\n"
SOURCES = (LIB, ARCHIVE, *(row[0] for row in PUBLIC_TESTS.values()),
           "tools/p09/qualify_form_input_public_export.py", "tools/p09/tests/test_form_input_public_export.py",
           "implementation/p09/P09-38_FORM_INPUT_PUBLIC_EXPORT_POLICY.md")
LEGACY_P09 = {
    "validate_citation_contract.py": "de8102176a0deea23893c3bccd985cbf923f5d0bd715cbda5f6eb35fd46b0966",
    "validate_comment_model_contract.py": "e674fba6702090fe6a2263d2be8219853d494414ab1aa3378b11204d9b53e8f8",
    "validate_cross_reference_contract.py": "6fa5d2e15e9f152ebf824a52c556198b00a5a46d545a0f358df17893b6333a07",
    "validate_field_core_contract.py": "f4d8354cb89112d8f5760419520368554ca48cfcdb3584c866040934119d35dd",
    "validate_form_control_contract.py": "6008adffc0fdbb516a0d029bfc1dc2112b40d310ffb73b4459b1b9029d862fbc",
    "validate_link_reference_contract.py": "611503a037ca064a19ddf4901a547d91da1d36a774b82f3d7d87c725c5920e54",
    "validate_mail_merge_contract.py": "d06b7a5c18418bb90f1bcdb0b2f9e3b0e5bbc69f16650c762020924d9a0d4970",
    "validate_note_engine_contract.py": "4a4ae911e7861982bae3bf0d219cd138052ccac578b5f4214b5605595dd9a258",
    "validate_reference_auxiliary_contract.py": "d337001cbd4bd1a5cc773147343bfc6936e8d419e4e8a42b299dfd7525bc93c8",
    "validate_toc_index_contract.py": "425f505b52f96f9ebe2a722d3397c64dd49a55f267ac0709c53996a6aeae65b5",
}
DIGEST_PATH_P09 = {"validate_citation_contract.py", "validate_mail_merge_contract.py", "validate_reference_auxiliary_contract.py"}


def domain_error(name):
    return "digest:" + LIB if name in DIGEST_PATH_P09 else "implementation_digest"


def project(raw, root=ROOT):
    if q.sha(raw) != CURRENT_LIB or raw.count(DELTA) != 1:
        raise ValueError("form_input_public_unique_current_delta_invalid")
    old = public.checked(root / ARCHIVE, OLD_LIB)
    if raw.replace(DELTA, b"", 1) != old:
        raise ValueError("form_input_public_complete_source_projection_changed")
    return old


def lineage(root=ROOT):
    capsule = q.shared.lifecycle.checked_json(root / CAPSULE, CAPSULE_SHA)
    result = {}
    for key, (path, pending_path, marker, _, _, _) in PUBLIC_TESTS.items():
        old = public.checked(root / pending_path, capsule["source_sha256"][pending_path])
        actual = public.bounded_bytes(root / path, 2 * 1024 * 1024)
        if old.count(marker) != 1 or actual.count(marker) != 1 or actual[:actual.index(marker)] != HEADER:
            raise ValueError("form_input_public_case_header_changed")
        if actual[actual.index(marker):] != old[old.index(marker):] or b"#[path" in actual or b"../src/" in actual:
            raise ValueError("form_input_public_complete_case_body_changed")
        result[key] = {"source_sha256": q.sha(actual), "original_test_body_byte_exact": True,
                       "compiled_via_public_library_only": True}
    return result


def authority(root=ROOT):
    project(public.checked(root / LIB, CURRENT_LIB), root)
    capsule = q.shared.lifecycle.checked_json(root / CAPSULE, CAPSULE_SHA)
    for path, digest in capsule["source_sha256"].items():
        public.checked(root / path, digest)
    # Only this declared old domain library lock resolves to an explicit raw archive.
    # All unchanged component/target dependencies use their original current paths.
    for path, digest in prior.OLD_SOURCES.items():
        public.checked(root / (ARCHIVE if path == LIB else path), digest)
    preserved = q.shared.lifecycle.checked_json(root / prior.PREDECESSOR, prior.PREDECESSOR_SHA)
    q.exact(preserved["source_sha256"], prior.prior.own_sources(root), "form_input_public_batch_sources_changed")
    for path, digest in preserved["historical_trace_and_artifact_sha256"].items():
        public.checked(root / path, digest, 32 * 1024 * 1024)
    prior.prior.dependency_guard(root)
    historical = public.source_guard(root)
    lineage(root)
    for name, digest in LEGACY_P09.items():
        public.checked(root / "tools/p09" / name, digest)
    return {"predecessor_capsule_sha256": CAPSULE_SHA, "predecessor_source_files": len(capsule["source_sha256"]),
            "older_capsules": len(historical), "older_source_checks": sum(map(len, historical.values())),
            "historical_trace_and_artifact_files": len(preserved["historical_trace_and_artifact_sha256"]),
            "old_domain_library_checked_path": ARCHIVE, "old_domain_library_is_current_full_verifier_pass": False}


def run(command, root=ROOT, timeout=120):
    process = subprocess.run(command, cwd=root, capture_output=True, timeout=timeout,
                             creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
    if len(process.stdout) + len(process.stderr) > 2 * 1024 * 1024:
        raise ValueError("form_input_public_command_output_limit")
    return process.returncode, process.stdout.decode("utf-8", errors="strict")


def compiled(root=ROOT):
    code, _ = run(["cargo", "check", "-p", "domain-ir", "--lib", "--locked", "--offline"], root)
    if code:
        raise ValueError("form_input_public_actual_production_library_failed")
    result = {}
    for key, (_, _, _, package, target, expected) in PUBLIC_TESTS.items():
        result[key] = prior.verify_tests(prior.cargo(package, target, root=root), expected)
    code, stdout = run(["cargo", "test", "-p", "domain-ir", "--lib", "form_input::tests::", "--locked", "--offline"], root)
    found = re.findall(r"(?m)^test ([a-z0-9_:]+) \.\.\. (ok|FAILED|ignored)\s*$", stdout)
    summaries = re.findall(r"(?m)^test result: ok\. 2 passed; 0 failed; 0 ignored; 0 measured; (\d+) filtered out;.*$", stdout)
    if code or len(found) != 2 or {name for name, _ in found} != prior.PRIVATE_TESTS or any(state != "ok" for _, state in found) or len(summaries) != 1:
        raise ValueError("form_input_public_actual_library_unit_inventory_invalid")
    result["actual_library_unit"] = {"passed": 2, "failed": 0, "ignored": 0, "names": sorted(prior.PRIVATE_TESTS),
                                     "explicit_scoped_filter": "form_input::tests::", "filtered_unrelated_library_tests": int(summaries[0])}
    return result


def actual_probe(root=ROOT):
    stdout = prior.cargo("hwpx-package", "form_input_native_binding_public", (prior.ACTUAL_TEST, "--", "--exact", "--nocapture"), root)
    probes = re.findall(r"P09_37_ACTUAL_INPUT_PROBE=(\{[^\r\n]+\})", stdout)
    if len(probes) != 1 or "1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;" not in stdout:
        raise ValueError("form_input_public_actual_probe_inventory_invalid")
    return json.loads(probes[0], object_pairs_hook=q.shared.lifecycle.duplicate_guard)


def expected_current_failures(root=ROOT):
    failures = {}
    for name, function, expected in (("P09-37", prior.authority, "public_export_source_identity_changed"),
                                     ("P09-34-r02", public.verify, "bridge_source_identity_changed")):
        try:
            function(root)
        except ValueError as error:
            if str(error) != expected:
                raise ValueError("form_input_public_unexpected_predecessor_current_failure") from error
            failures[name] = {"state": "fail", "error_code": expected, "actually_invoked": True,
                              "archived_capsule_rewritten": False}
        else:
            raise ValueError("form_input_public_predecessor_current_failure_missing")
    return failures


def audit_legacy(root=ROOT):
    old1, _ = public.old4.old3.predecessors(root)
    paths = {**old1.REQUIRED_VALIDATORS, **{"tools/p09/" + name: digest for name, digest in LEGACY_P09.items()}}
    result = []
    for path, digest in paths.items():
        public.checked(root / path, digest)
        code, stdout = run([sys.executable, path], root, 60)
        value, banner_count = legacy_result(stdout)
        if type(value) is not dict or value.get("state") not in ("pass", "fail") or code != (0 if value["state"] == "pass" else 1):
            raise ValueError("form_input_public_legacy_validator_result_invalid")
        errors = value.get("errors", [])
        if type(errors) is not list or any(type(error) is not str or not re.fullmatch(r"[a-z0-9_:.\-/]+", error) for error in errors):
            raise ValueError("form_input_public_legacy_validator_errors_invalid")
        if path.startswith("tools/p09/validate_") and Path(path).name in LEGACY_P09 and (value["state"] != "fail" or errors != [domain_error(Path(path).name)]):
            raise ValueError("form_input_public_domain_lock_failure_changed")
        result.append({"path": path, "source_sha256": digest, "state": value["state"], "exit_code": code,
                       "errors": errors, "public_summary_banner_lines": banner_count,
                       "actually_invoked": True, "source_locks_refreshed": False})
    for path, digest in paths.items():
        public.checked(root / path, digest)
    return result


def legacy_result(stdout):
    # Several frozen CLIs emit a documented non-JSON public PASS banner AFTER
    # their single JSON result. Parse that protocol, not arbitrary trailing data.
    records, banners = [], []
    for line in stdout.splitlines():
        if not line.strip():
            continue
        if line.startswith("{"):
            records.append(json.loads(line, object_pairs_hook=q.shared.lifecycle.duplicate_guard))
        elif re.fullmatch(r"P0[89]_[A-Z_]+_PASS(?: [a-z0-9_=]+)*", line):
            banners.append(line)
        else:
            raise ValueError("form_input_public_legacy_stdout_protocol_invalid")
    if len(records) != 1 or len(banners) > 1:
        raise ValueError("form_input_public_legacy_json_result_inventory_invalid")
    if type(records[0]) is not dict or (banners and records[0].get("state") != "pass"):
        raise ValueError("form_input_public_legacy_banner_result_conflict")
    return records[0], len(banners)


def qualify(root=ROOT):
    before = {path: q.sha(public.bounded_bytes(root / path, 2 * 1024 * 1024)) for path in SOURCES}
    guard = authority(root)
    independent = q.output.prior.independent_actual(root)
    tests = compiled(root)
    probe = actual_probe(root); prior.verify_probe(probe, independent)
    failures = expected_current_failures(root)
    legacy = audit_legacy(root)
    # Genuine complete offline preparation/strict binder reproduction, not patched authority.
    replay = prior.prior.preflight(root)
    if q.shared.lifecycle.canonical_bytes(replay) != public.checked(root / prior.PREDECESSOR, prior.PREDECESSOR_SHA, 512 * 1024):
        raise ValueError("form_input_public_previous_diagnostic_preflight_changed")
    q.exact(guard, authority(root), "form_input_public_dependencies_changed")
    q.exact(before, {path: q.sha(public.bounded_bytes(root / path, 2 * 1024 * 1024)) for path in SOURCES}, "form_input_public_sources_changed")
    return {"schema_version": "hwpx-agent.p09-38-atomic-form-input-public-export/v1", "task": "P09-38",
            "state": "actual_public_input_api_source_qualified_legacy_current_failures_non_green",
            "source_sha256": before, "source_transition": {"current_raw_sha256": CURRENT_LIB, "predecessor_raw_sha256": OLD_LIB,
            "only_single_public_module_export_added": True, "complete_inverse_byte_exact": True, "added_runtime_dependencies": False},
            "preserved_source_authority": guard, "public_case_lineage": lineage(root),
            "production_library_check": {"state": "pass", "locked": True, "offline": True},
            "compiled_test_suites": tests, "actual_capture_input_probe": probe, "independent_package_bindings": independent,
            "actual_predecessor_current_failures": failures, "actual_legacy_current_validators": legacy,
            "unchanged_complete_diagnostic_preflight_byte_exact": True,
            "claims": {"public_input_api_connected": True, "public_test_bodies_byte_exact": True,
                       "native_input_output_qualified": False, "native_protection_qualified": False,
                       "external_validation_qualified": False, "native_date_binding_qualified": False,
                       "legacy_current_aggregate_pass": False, "legacy_tests_migrated_or_skipped": False,
                       "production_routing_qualified": False, "new_native_execution": False,
                       "render": "not_run", "product_differential": "not_run", "green_rows": 0, "p09_complete": False},
            "future_native_diagnostic_batch": {"cases": 15, "stages": 30, "state": "not_run", "typed_only_inputs_added": 0},
            "privacy": {"raw_document_text_present": False, "absolute_private_paths_present": False,
                        "native_session_started": False, "trust_or_registry_changed": False}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(); group.add_argument("--output", type=Path); group.add_argument("--verify", type=Path)
    args = parser.parse_args()
    try:
        value = qualify(); raw = q.shared.lifecycle.canonical_bytes(value)
        if args.output:
            path = args.output.absolute(); q.shared.within(path.parent, ROOT / "implementation/p09/evidence")
            if "private" in path.relative_to(ROOT).parts or path.is_symlink() or path.is_junction():
                raise ValueError("form_input_public_evidence_boundary_invalid")
            with path.open("xb") as stream: stream.write(raw)
        if args.verify and public.bounded_bytes(args.verify, 512 * 1024) != raw:
            raise ValueError("form_input_public_capsule_reproduction_mismatch")
    except (OSError, ValueError, KeyError, TypeError, UnicodeError, subprocess.SubprocessError) as error:
        code = str(error) if type(error) is ValueError and re.fullmatch(r"[a-z_]+", str(error)) else "form_input_public_verification_failed"
        print(json.dumps({"state": "fail", "error_code": code})); return 2
    print(json.dumps({"state": "pass", "qualification_sha256": q.sha(raw), "compiled_tests_passed": 18,
                      "legacy_current_failures_preserved": True, "native_session_started": False, "green_rows": 0})); return 0


if __name__ == "__main__":
    raise SystemExit(main())
