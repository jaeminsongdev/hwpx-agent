#!/usr/bin/env python3
"""Qualify actual compiled atomic form input; no native launch or HWPX write."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.p09 import qualify_native_form_diagnostic_batch as prior

ROOT = prior.ROOT
q = prior.q
public = prior.public
SOURCES = (
    "crates/domain-ir/src/form_input.rs", "crates/domain-ir/tests/form_input_pending_export.rs",
    "crates/hwpx-package/tests/form_input_native_binding_pending_export.rs",
    "tools/p09/qualify_form_input_component.py", "tools/p09/tests/test_form_input_component.py",
    "implementation/p09/P09-37_FORM_INPUT_POLICY.md",
)
PREDECESSOR = "implementation/p09/evidence/p09-36-native-form-diagnostic-binding-component.current-2020.v1.json"
PREDECESSOR_SHA = "aa2cf63c8de33bc9ceb1476b2ebcfd488586d6059cbef9d429c53a00b0d0bff7"
OLD_SOURCES = {
    "crates/domain-ir/src/lib.rs": "b4726732a47175205a7e35f3aa8e018e66b2a0fbada144bebeac3f395540c058",
    "crates/domain-ir/src/form_control.rs": "19e4c23c1318d477fd85a851d9f0e76dbe70012d9295b8202b162247105fabb5",
    "crates/domain-ir/tests/form_control.rs": "11af786a06c4792a30546f6e73e4123eb33b573b84eb69c2a2b9c05f3ed750b5",
}
PRIVATE_TESTS = {"form_input::tests::private_seal_fields_cannot_be_forged", "form_input::tests::private_bounded_serializer_rejects_before_over_limit_allocation"}
DOMAIN_TESTS = PRIVATE_TESTS | {
    "all_six_value_kinds_change_only_current_values_in_one_atomic_transition",
    "complete_default_reset_preserves_policies_and_atomically_restores_radio_group",
    "required_radio_switch_accepts_either_assignment_order_but_not_partial_group",
    "each_requested_target_enforces_shape_enabled_editable_and_text_read_only",
    "caller_access_and_exact_protection_digest_are_mandatory_not_native_proof",
    "missing_duplicate_cross_kind_and_empty_targets_fail_without_partial_state",
    "text_numeric_multiline_length_and_required_rules_reuse_real_domain_validation",
    "selection_membership_checkbox_required_and_date_range_fail_closed",
    "external_validator_references_never_count_as_executed_validation",
    "source_flow_and_protection_drift_invalidate_request_plan_and_build",
    "strict_json_duplicate_nested_unknown_coercion_trailing_and_size_reject",
    "retry_is_byte_exact_and_value_and_reset_noops_reject",
    "debug_error_and_public_receipt_redact_document_values_and_private_paths",
    "fresh_caller_access_revocation_rejects_an_earlier_valid_plan",
    "complete_private_plan_output_limit_returns_no_partial_result",
}
ACTUAL_TEST = "actual_capture_input_binds_complete_public_readback_and_keeps_old_lowerer_failure"
ACTUAL_TESTS = PRIVATE_TESTS | {ACTUAL_TEST}
PROBE_HASHES = {
    "source_state_sha256": "7841acc0e27ca1a96ace5c21375f46e3a3936ac9efa3a03efc9aecb699a708e1",
    "target_state_sha256": "e201df8bf80c6df99ce98e30fb8b89900d74c3ead494e3f4432d2efe2be57026",
    "document_flow_sha256": "1c1df01dadb3475fe7f1d6ca0c5692770f54a1d403dd8eedcbc39d9634f4a22b",
    "plan_sha256": "c8abe430e6bc9d55e8e4606958ce8638a97cb3a6368910e0fcadaa00b7660651",
}


def authority(root=ROOT):
    value = q.shared.lifecycle.checked_json(root / PREDECESSOR, PREDECESSOR_SHA)
    q.exact(value["source_sha256"], prior.own_sources(root), "form_input_predecessor_source_changed")
    for path, digest in value["historical_trace_and_artifact_sha256"].items():
        public.checked(root / path, digest, 32 * 1024 * 1024)
    prior.dependency_guard(root)
    for path, digest in OLD_SOURCES.items():
        public.checked(root / path, digest)
    if b"mod form_input;" in public.bounded_bytes(root / "crates/domain-ir/src/lib.rs", 2 * 1024 * 1024):
        raise ValueError("form_input_pending_export_boundary_changed")


def verify_tests(stdout, expected):
    found = re.findall(r"(?m)^test ([a-z0-9_:]+) \.\.\. (ok|FAILED|ignored)\s*$", stdout)
    count = len(expected)
    if len(found) != count or {n for n, _ in found} != expected or any(s != "ok" for _, s in found):
        raise ValueError("form_input_actual_test_inventory_invalid")
    if len(re.findall(rf"(?m)^test result: ok\. {count} passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;.*$", stdout)) != 1:
        raise ValueError("form_input_actual_test_summary_invalid")
    return {"passed": count, "failed": 0, "ignored": 0, "names": sorted(expected), "locked": True, "offline": True}


def cargo(package, target, extra=(), root=ROOT):
    process = subprocess.run(["cargo", "test", "-p", package, "--test", target, "--locked", "--offline", *extra],
                             cwd=root, capture_output=True, timeout=120,
                             creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
    if process.returncode or not 0 < len(process.stdout) <= 128 * 1024 or len(process.stderr) > 1024 * 1024:
        raise ValueError("form_input_actual_compiled_tests_failed")
    return process.stdout.decode("utf-8", errors="strict")


def verify_probe(value, independent):
    expected = {
        "schema_version": "hwpx-agent.p09-37-actual-capture-input-component/v1",
        "source_package_sha256": q.output.prior.prior.CAPTURE_SHA, **PROBE_HASHES,
        "controls": 1, "changed_controls": 1,
        "requested_value_sha256": hashlib.sha256("P09 실제 입력".encode()).hexdigest(),
        "every_other_complete_state_field_exact": True, "observed_native_identity_missing": True,
        "caller_policy_only": True, "old_native_output": "nonrepresentable",
        "native_protection_qualified": False, "native_output_qualified": False, "native_session_started": False,
        "raw_document_text_present": False, "absolute_private_paths_present": False, "green_rows": 0, "p09_complete": False,
    }
    q.exact(value, expected, "form_input_actual_probe_mismatch")
    q.exact(value["source_package_sha256"], independent["package_sha256"], "form_input_independent_package_mismatch")
    q.exact(value["document_flow_sha256"], independent["document_flow_sha256"], "form_input_independent_flow_mismatch")


def actual_probe(root=ROOT):
    stdout = cargo("hwpx-package", "form_input_native_binding_pending_export", (ACTUAL_TEST, "--", "--exact", "--nocapture"), root)
    found = re.findall(r"P09_37_ACTUAL_INPUT_PROBE=(\{[^\r\n]+\})", stdout)
    if len(found) != 1 or "1 passed; 0 failed; 0 ignored; 0 measured; 2 filtered out;" not in stdout:
        raise ValueError("form_input_actual_probe_inventory_invalid")
    return json.loads(found[0], object_pairs_hook=q.shared.lifecycle.duplicate_guard)


def legacy_validation(root=ROOT):
    process = subprocess.run([sys.executable, "tools/p09/validate_form_control_contract.py"], cwd=root,
                             capture_output=True, timeout=60,
                             creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
    if process.returncode or not 0 < len(process.stdout) <= 128 * 1024:
        raise ValueError("form_input_unchanged_legacy_validator_failed")
    value = json.loads(process.stdout, object_pairs_hook=q.shared.lifecycle.duplicate_guard)
    required = {"schema_version": "hwpx-agent.p09-form-control-validation/v1", "state": "pass", "errors": [],
                "task": "P09-02", "capabilities": 8, "date_native_binding": "unverified", "direct_hwpx": "not_run",
                "actual_hwpx": "not_run", "actual_hangul": "not_run", "render": "not_run", "automation": "not_run",
                "differential": "not_run", "p09_02_green": False, "product_complete": False}
    q.exact({k: value.get(k) for k in required}, required, "form_input_legacy_result_promoted_or_changed")
    return value


def qualify(root=ROOT):
    before = {path: q.sha(public.bounded_bytes(root / path, 2 * 1024 * 1024)) for path in SOURCES}
    authority(root)
    independent = q.output.prior.independent_actual(root)
    suites = {
        "domain": verify_tests(cargo("domain-ir", "form_input_pending_export", root=root), DOMAIN_TESTS),
        "actual_capture": verify_tests(cargo("hwpx-package", "form_input_native_binding_pending_export", root=root), ACTUAL_TESTS),
    }
    probe = actual_probe(root); verify_probe(probe, independent)
    legacy = legacy_validation(root)
    authority(root)
    q.exact(before, {path: q.sha(public.bounded_bytes(root / path, 2 * 1024 * 1024)) for path in SOURCES}, "form_input_component_sources_changed")
    return {"schema_version": "hwpx-agent.p09-37-atomic-form-input-component/v1", "task": "P09-37",
            "state": "actual_compiled_atomic_input_pending_export_non_green", "source_sha256": before,
            "predecessor_sha256": PREDECESSOR_SHA, "unchanged_domain_source_sha256": OLD_SOURCES,
            "compiled_test_suites": suites, "actual_capture_input_probe": probe, "independent_package_bindings": independent,
            "unchanged_legacy_validator": legacy,
            "claims": {"six_semantic_input_kinds": True, "atomic_radio_and_defaults": True,
                       "fresh_caller_policy_and_builtin_validation_enforced": True,
                       "external_validation_without_execution_rejected": True, "public_export_qualified": False,
                       "native_protection_qualified": False, "native_input_output_qualified": False,
                       "native_date_binding_qualified": False, "independent_python_full_domain_serializer_qualified": False,
                       "production_routing_qualified": False, "new_native_execution": False, "render": "not_run",
                       "product_differential": "not_run", "green_rows": 0, "p09_complete": False},
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
            raise ValueError("form_input_capsule_reproduction_mismatch")
    except (OSError, ValueError, KeyError, TypeError, UnicodeError, subprocess.SubprocessError) as error:
        code = str(error) if type(error) is ValueError and re.fullmatch(r"[a-z_]+", str(error)) else "form_input_component_verification_failed"
        print(json.dumps({"state": "fail", "error_code": code})); return 2
    print(json.dumps({"state": "pass", "qualification_sha256": q.sha(raw), "compiled_tests_passed": 20,
                      "native_session_started": False, "green_rows": 0, "p09_complete": False})); return 0


if __name__ == "__main__":
    raise SystemExit(main())
