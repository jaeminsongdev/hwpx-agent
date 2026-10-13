#!/usr/bin/env python3
"""Actual bounded component output plus independent whole-package oracle; non-green."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.p09 import inspect_native_form_value_output as oracle
from tools.p09 import qualify_legacy_domain_contract_regression as prior

ROOT = prior.ROOT
public, q = prior.public, prior.q
PREDECESSOR = "implementation/p09/evidence/p09-39-legacy-domain-regression-successor.current-2020.v1.json"
PREDECESSOR_SHA = "b5a3207f318fd038a1805908c57c1ab5fa05ec32cd148b6b8524b63bc604de92"
RUST_SOURCE = "crates/hwpx-package/src/native_form_value_output.rs"
RUST_TEST = "crates/hwpx-package/tests/native_form_value_output_pending_export.rs"
SOURCES = (RUST_SOURCE, RUST_TEST, "tools/p09/inspect_native_form_value_output.py", "tools/p09/qualify_native_form_value_output.py", "tools/p09/tests/test_native_form_value_output.py", "implementation/p09/P09-40_NATIVE_FORM_VALUE_OUTPUT_POLICY.md")
SHARED = {"crates/domain-ir/src/lib.rs": "6f44e4baca13f0665abc6c2599bc4ab0ff559af11b02f37d7747a9334c5ccb85", "crates/hwpx-package/src/lib.rs": "95ba3752b2b3c6b2e1bd1879cdb05aabaef1e7ca0ca91e70b2843b2cbd0a247b"}
ENVIRONMENT = "HWPX_P09_40_COMPONENT_ARTIFACT_DIR"
PRIVATE_TESTS = {"native_value::tests::private_seal_rejects_profile_map_policy_source_access_and_seal_mutations", "native_value::tests::private_bounded_write_seek_and_escaped_value_reject_before_allocation", "native_value::tests::private_gap_patch_rejects_overlap_invalid_ranges_and_small_limit"}
INTEGRATION_TESTS = {
    "actual_capture_value_output_reopens_complete_package_with_distinct_v2_opaque_profile_and_preserves_old_failure",
    "five_native_kinds_cross_section_required_radio_and_all_unknown_bytes_are_preserved",
    "reset_all_explicit_caller_defaults_roundtrips_atomically_without_claiming_native_defaults",
    "empty_text_expansion_preserves_raw_head_attributes_and_v2_fingerprint",
    "both_selection_clear_values_remain_none_not_invented_items_or_empty_literal",
    "required_radio_intermediate_invalid_transition_is_rejected_before_any_output",
    "fresh_access_revocation_and_protection_digest_drift_fail_both_output_and_external_verification",
    "external_output_tampering_rejects_unknown_control_attributes_children_nonform_and_nonsection_bytes",
    "external_output_inventory_order_compression_extra_missing_and_wrong_values_fail",
    "original_source_package_drift_is_not_rebound_or_accepted_by_output",
    "complete_v1_plan_is_not_silently_substituted_for_versioned_v2_source",
    "output_limits_fail_without_clamping_or_partial_package",
    "invalid_xml_values_and_unqualified_date_kind_fail_closed",
    "debug_and_hash_receipts_do_not_expose_values_or_unknown_text",
    "missing_selection_attribute_is_unqualified_even_when_v1_can_observe_none",
    "map_policy_and_package_source_bindings_are_fresh_not_receipt_claims",
    "observed_protection_signal_is_rejected_even_if_caller_says_allowed",
    "locked_disabled_noneditable_readonly_requested_targets_reject_even_if_one_value_is_a_noop",
    "external_validator_is_not_executed_or_promoted_and_value_noop_stays_rejected",
    "ambiguous_unknown_namespace_text_keeps_original_v1_profile_rejection",
    "five_complete_component_fixture_pairs_are_real_retry_verified_and_not_native_candidates",
    "component_artifact_directory_rejects_relative_nested_traversal_and_wrong_prefix",
}
EXPECTED_TESTS = PRIVATE_TESTS | INTEGRATION_TESTS


def own_sources(root=ROOT):
    return {path: q.sha(public.bounded_bytes(root / path, 2*1024*1024)) for path in SOURCES}


def authority(root=ROOT):
    value = q.shared.lifecycle.checked_json(root / PREDECESSOR, PREDECESSOR_SHA)
    for path, digest in value["source_sha256"].items():
        public.checked(root / path, digest)
    prior.authority(root)
    for path, digest in SHARED.items():
        public.checked(root / path, digest)
    oracle.require(b"mod native_form_value_output;" not in public.bounded_bytes(root / "crates/hwpx-package/src/lib.rs", 2*1024*1024), "value_output_pending_export_boundary_changed")
    return PREDECESSOR_SHA


def tests_protocol(stdout):
    found = re.findall(r"(?m)^test ([a-z0-9_:]+) \.\.\. (ok|FAILED|ignored)\s*$", stdout)
    oracle.require(len(found) == len(EXPECTED_TESTS) and {n for n, _ in found} == EXPECTED_TESTS and all(s == "ok" for _, s in found), "value_output_compiled_inventory")
    oracle.require(len(re.findall(r"(?m)^test result: ok\. 25 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;.*$", stdout)) == 1, "value_output_compiled_summary")
    return {"passed": 25, "failed": 0, "ignored": 0, "filtered": 0, "names": sorted(EXPECTED_TESTS), "locked": True, "offline": True, "pending_export_source_inclusion": True, "native_candidate": False}


def generate(directory, root=ROOT):
    authority(root)
    oracle.directory_guard(directory, root)
    oracle.require(not any(directory.iterdir()), "value_output_generation_directory_nonempty")
    environment = dict(os.environ)
    environment[ENVIRONMENT] = str(directory)
    process = subprocess.run(["cargo", "test", "--offline", "--locked", "-p", "hwpx-package", "--test", "native_form_value_output_pending_export", "--", "--show-output", "--test-threads=1"], cwd=root, env=environment, capture_output=True, timeout=120, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
    oracle.require(process.returncode == 0 and 0 < len(process.stdout) <= 128*1024 and len(process.stderr) <= 1024*1024, "value_output_compiled_execution_failed")
    stdout = process.stdout.decode("utf-8", errors="strict")
    tests = tests_protocol(stdout)
    probes = re.findall(r"P09_40_COMPONENT_BUNDLE_PROBE=(\{[^\r\n]+\})", stdout)
    oracle.require(len(probes) == 1, "value_output_bundle_probe_inventory")
    probe = json.loads(probes[0], object_pairs_hook=oracle.duplicate_guard)
    independent = oracle.inspect_bundle(directory, root)
    oracle.require(probe == {"cases": 5, "files": 11, "manifest_sha256": independent["manifest_sha256"], "artifact_bytes": independent["artifact_bytes"], "native_session_started": False} and type(probe["cases"]) is int and type(probe["files"]) is int and type(probe["artifact_bytes"]) is int and probe["native_session_started"] is False, "value_output_bundle_probe_mismatch")
    actual = re.findall(r"P09_40_ACTUAL_VALUE_PROBE=(\{[^\r\n]+\})", stdout)
    oracle.require(len(actual) == 1, "value_output_actual_probe_inventory")
    actual_probe = json.loads(actual[0], object_pairs_hook=oracle.duplicate_guard)
    manifest = json.loads(oracle.checked_bytes(directory / "fixture-manifest.json", 64*1024), object_pairs_hook=oracle.duplicate_guard)
    oracle.require(actual_probe == manifest["cases"][0]["receipt"], "value_output_actual_probe_mismatch")
    return {"compiled_tests": tests, "independent_oracle": independent, "fixture_manifest": manifest, "zip_limit_drop_diagnostic_observed": b"ZipWriter::drop" in process.stderr}


def qualify(root=ROOT):
    authority(root)
    before = own_sources(root)
    base = (root / "fixtures/target-build").resolve(strict=True)
    bundles = []
    for _ in range(2):
        with tempfile.TemporaryDirectory(prefix="p09-40-component-", dir=base) as temporary:
            bundles.append(generate(Path(temporary), root))
        oracle.require(not Path(temporary).exists(), "value_output_component_scratch_not_cleaned")
    oracle.require(bundles[0] == bundles[1], "value_output_two_fresh_generations_differ")
    replay = prior.qualify(root)
    raw = q.shared.lifecycle.canonical_bytes(replay)
    oracle.require(q.sha(raw) == PREDECESSOR_SHA and raw == public.bounded_bytes(root / PREDECESSOR, 512*1024), "value_output_full_predecessor_not_reproduced")
    authority(root)
    oracle.require(own_sources(root) == before, "value_output_current_sources_changed")
    return {"schema_version": "hwpx-agent.p09-40-managed-value-output-component-source-qualification/v1", "state": "compiled_complete_package_value_output_and_independent_oracle_qualified_non_green", "source_sha256": before,
            "predecessor_capsule_sha256": PREDECESSOR_SHA, "actual_full_predecessor_byte_exact_reproduction": True,
            "two_fresh_component_generations_byte_exact": True, **bundles[0],
            "actual_current_legacy_failures_preserved": replay["actual_current_legacy_failures_preserved"],
            "actual_current_predecessor_failures_preserved": replay["actual_current_predecessor_failures_preserved"],
            "qualification": {"complete_package_component_output": True, "independent_whole_output_oracle": True, "public_export": False, "product_routing": False, "native_execution": False, "native_protection": False, "native_defaults": False, "native_date": False, "external_validation": False, "render": "not_run", "product_differential": "not_run", "green_rows": 0, "p09_complete": False},
            "privacy": {"raw_document_values_present": False, "absolute_private_paths_present": False, "native_session_started": False, "trust_or_registry_changed": False}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--output", type=Path); group.add_argument("--verify", type=Path)
    args = parser.parse_args()
    try:
        value = qualify()
        raw = q.shared.lifecycle.canonical_bytes(value)
        if args.output:
            path = args.output.absolute()
            q.shared.within(path.parent, ROOT / "implementation/p09/evidence")
            oracle.no_links(path.parent)
            oracle.require("private" not in path.relative_to(ROOT).parts and not path.is_symlink() and not path.is_junction(), "value_output_public_evidence_boundary")
            with path.open("xb") as stream:
                stream.write(raw)
        if args.verify:
            q.shared.within(args.verify.absolute().parent, ROOT / "implementation/p09/evidence")
            oracle.require(public.bounded_bytes(args.verify, 512*1024) == raw, "value_output_capsule_reproduction_mismatch")
    except (OSError, ValueError, KeyError, TypeError, UnicodeError, subprocess.SubprocessError):
        print(json.dumps({"state": "fail", "error_code": "managed_value_output_qualification_failed"})); return 2
    print(json.dumps({"state": "pass", "qualification_sha256": q.sha(raw), "compiled_component_tests": 25, "independent_complete_output_pairs": 5, "native_session_started": False, "green_rows": 0})); return 0


if __name__ == "__main__":
    raise SystemExit(main())
