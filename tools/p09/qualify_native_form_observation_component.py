#!/usr/bin/env python3
"""Qualify the compiled pending-export native-form successor; no new native session."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.p09 import qualify_native_form_compatibility as prior

shared = prior.shared
ROOT = prior.ROOT
COMPATIBILITY = "implementation/p09/evidence/p09-25-native-form-compatibility-qualification.current-2020.v1.json"
COMPATIBILITY_SHA = "a5f86b629ef65d31f3eb49e9cbfacb081aec2165910ed033300b32a80c81e307"
BRIDGE = "implementation/p09/evidence/p09-23-p08-additive-export-source-qualification.current-2020.v2.json"
BRIDGE_SHA = "70806cbec581e50a5a4a419ce73e8a1ab32c09c930f7aae915c7b0d47bac38f1"
LIB = "crates/hwpx-package/src/lib.rs"
SOURCE = "crates/hwpx-package/src/native_form_hwpx.rs"
TEST = "crates/hwpx-package/tests/native_form_hwpx_pending_export.rs"
POLICY = "implementation/p09/P09-27_NATIVE_FORM_OBSERVATION_POLICY.md"
SOURCES = ("tools/p09/qualify_native_form_observation_component.py",
           "tools/p09/tests/test_native_form_observation_component.py", POLICY, SOURCE, TEST, LIB,
           "crates/hwpx-package/src/preserving_xml.rs", "crates/hwpx-package/src/safe_xml.rs", *prior.SOURCES)
EXPECTED_TESTS = {
    "actual_native_missing_id_observed_without_injection",
    "actual_properties_lower_keep_missing_ids_geometry_payload_and_opaque_bytes",
    "forged_component_anchor_geometry_or_opaque_hash_not_admitted",
    "all_five_native_kinds_support_real_typed_properties_without_synthetic_xml_ids",
    "complete_tab_order_updates_all_controls_and_preserves_every_native_identity",
    "native_optional_id_variants_never_equal_component_reservations",
    "duplicate_native_ids_aliases_or_namespaced_semantic_attributes_fail_closed",
    "incomplete_duplicate_or_changed_maps_rejected",
    "source_payload_geometry_or_nonselected_drift_aborts_lowering",
    "optional_missing_group_attribute_can_be_added_without_opaque_drift",
    "unknown_opaque_attributes_children_and_command_preserved_not_executed",
    "rich_text_wrong_namespace_or_duplicate_geometry_rejected",
    "protected_actual_shape_blocks_typed_properties_without_output",
    "payload_update_or_command_change_not_disguised_as_properties",
    "debug_redacts_actual_values_names_maps_paths_and_hashes",
    "finite_limits_refuse_zero_hard_ceilings_and_changed_output_budgets",
    "opaque_character_contents_and_inter_child_comments_are_independently_bound",
    "nested_paragraph_path_is_real_and_source_bound_not_only_native_ids",
}


def checked_sources(root: Path = ROOT):
    previous = shared.lifecycle.checked_json(root / COMPATIBILITY, COMPATIBILITY_SHA)
    bridge = shared.lifecycle.checked_json(root / BRIDGE, BRIDGE_SHA)
    for path, digest in previous["source_sha256"].items():
        if shared.oracle.sha256(shared.oracle.bounded_bytes(shared.within(root / path, root), 2 * 1024 * 1024)) != digest:
            raise ValueError("native_form_observation_predecessor_drift")
    expected = bridge["shared_lib"]["current_raw_sha256"]
    lib = shared.oracle.bounded_bytes(shared.within(root / LIB, root), 2 * 1024 * 1024)
    if shared.oracle.sha256(lib) != expected or b"mod native_form_hwpx;" in lib:
        raise ValueError("native_form_observation_pending_export_boundary_changed")
    for path, digest in {**bridge["new_adapter_sha256"], **bridge["source_sha256"]}.items():
        if shared.oracle.sha256(shared.oracle.bounded_bytes(shared.within(root / path, root), 2 * 1024 * 1024)) != digest:
            raise ValueError("native_form_observation_export_authority_drift")
    return previous, expected


def verify_test_output(output: str):
    matches = re.findall(r"(?m)^test ([a-z0-9_]+) \.\.\. (ok|FAILED|ignored)\s*$", output)
    if (len(matches) != len(EXPECTED_TESTS) or {name for name, _ in matches} != EXPECTED_TESTS
            or any(state != "ok" for _, state in matches)
            or len(re.findall(r"(?m)^test result: ok\. 18 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;.*$", output)) != 1):
        raise ValueError("native_form_observation_test_inventory_or_result_invalid")
    return {"state": "pass", "test_target": "native_form_hwpx_pending_export", "passed": 18,
            "failed": 0, "ignored": 0, "locked": True, "offline": True,
            "compiled_actual_successor_source": True, "test_names": sorted(EXPECTED_TESTS)}


def run_tests(root: Path = ROOT):
    result = subprocess.run(["cargo", "test", "-p", "hwpx-package", "--test", "native_form_hwpx_pending_export",
                             "--locked", "--offline"], cwd=root, capture_output=True, timeout=60,
                            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    if result.returncode != 0 or not 0 < len(result.stdout) <= 128 * 1024:
        raise ValueError("native_form_observation_actual_test_execution_failed")
    return verify_test_output(result.stdout.decode("utf-8", errors="strict"))


def qualify(root: Path = ROOT):
    previous, lib_sha = checked_sources(root)
    observed = prior.capture(root)
    if observed != previous["capture"]:
        raise ValueError("native_form_observation_capture_drift")
    sources = {p: shared.oracle.sha256(shared.oracle.bounded_bytes(shared.within(root / p, root), 2 * 1024 * 1024)) for p in dict.fromkeys(SOURCES)}
    tests = run_tests(root)
    if prior.capture(root) != observed:
        raise ValueError("native_form_observation_capture_changed_during_test")
    checked_sources(root)
    if sources != {p: shared.oracle.sha256(shared.oracle.bounded_bytes(root / p, 2 * 1024 * 1024)) for p in sources}:
        raise ValueError("native_form_observation_source_changed_during_test")
    return {"schema_version": "hwpx-agent.p09-native-form-observation-component/v1", "task": "P09-27",
            "state": "observed_native_identity_component_non_green", "profile_id": "hwpx-agent.native-form-hwpx.hwpml-2011-observed-identity/v1",
            "compatibility_receipt_sha256": COMPATIBILITY_SHA, "export_predecessor_receipt_sha256": BRIDGE_SHA,
            "unchanged_pending_export_lib_sha256": lib_sha, "capture": observed, "source_sha256": sources, "actual_rust_tests": tests,
            "claims": {"observed_missing_id_reader_and_property_lowering_implemented": True,
                       "native_and_component_ids_separate": True, "actual_anchor_geometry_opaque_checks_implemented": True,
                       "five_kind_property_and_complete_tab_order_component_tested": True,
                       "shared_library_export_connected": False, "package_part_bindings_independently_read": False,
                       "new_native_target_execution": False, "complete_target_packages_prepared": False,
                       "production_routing_qualified": False, "predecessor_receipts_rewritten": False,
                       "render": "not_run", "product_differential": "not_run", "green_rows": 0,
                       "p09_complete": False, "product_complete": False},
            "privacy": {"raw_document_text_present": False, "absolute_private_paths": False,
                        "user_document_scanned": False, "computer_use_click_or_type_invoked": False,
                        "native_session_started": False, "registry_or_trust_setting_changed": False, "external_network_invoked": False}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--output", type=Path)
    group.add_argument("--verify", type=Path)
    args = parser.parse_args()
    try:
        value = qualify()
        raw = shared.lifecycle.canonical_bytes(value)
        if args.output:
            output = args.output.absolute()
            shared.within(output.parent, ROOT / "implementation/p09/evidence")
            if output.is_symlink() or output.is_junction() or "private" in output.relative_to(ROOT).parts:
                raise ValueError("native_form_observation_public_boundary")
            with output.open("xb") as handle:
                handle.write(raw)
        if args.verify and shared.oracle.bounded_bytes(args.verify, 256 * 1024) != raw:
            raise ValueError("native_form_observation_record_mismatch")
    except (OSError, ValueError, KeyError, TypeError, AttributeError, UnicodeError, subprocess.TimeoutExpired) as error:
        code = str(error) if type(error) is ValueError and re.fullmatch(r"[a-z_]+", str(error)) else "native_form_observation_qualification_failed"
        print(json.dumps({"state": "fail", "error_code": code}))
        return 2
    print(json.dumps({"state": "pass", "qualification_state": value["state"], "qualification_sha256": shared.oracle.sha256(raw),
                      "rust_tests_passed": value["actual_rust_tests"]["passed"], "shared_exports_connected": False, "green_rows": 0, "p09_complete": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
