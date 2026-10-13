#!/usr/bin/env python3
"""Independent whole-package 15-case preparation; never starts native automation."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile
from xml.etree import ElementTree as ET

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.p09 import verify_p08_additive_export_source_bridge_v5 as public

q = public.preparation.q
ROOT = public.ROOT
CAPSULE = "implementation/p09/evidence/p09-34-native-root-manifest-public-export-source.current-2020.r02.v5.json"
CAPSULE_SHA = "fca4d66f3f23e75c7348daf327b92b1fd8f590ab446c43cacbe871cc56993ce4"
GENERATOR = "crates/hwpx-package/examples/p09_35_native_form_diagnostic_fixture.rs"
SOURCES = (GENERATOR, "tools/p09/inspect_native_form_diagnostic_fixture.py",
           "tools/p09/tests/test_native_form_diagnostic_fixture.py", "implementation/p09/P09-35_NATIVE_FORM_DIAGNOSTIC_PREPARATION_POLICY.md")
LABELS = (
    "root-two-section-text", "root-two-section-radio", "red-foreground-only", "blue-foreground-only",
    "blue-existing-style", "blue-existing-style-noneditable", "red-existing-blue-style", "noneditable-only",
    "unicode-name-only", "ampersand-name-only", "less-than-name-only", "greater-than-name-only",
    "double-quote-name-only", "apostrophe-name-only", "metachar-group-only",
)
NAMES = ("P09 이름 한글", "P09 이름 & 폼", "P09 이름 < 폼", "P09 이름 > 폼", 'P09 이름 " 폼', "P09 이름 ' 폼")
EXPECTED_TESTS = {
    "tests::all_fifteen_different_complete_cases_retry_verify_and_keep_full_intent",
    "tests::original_as_native_output_cannot_pass_property_or_packaging_intent",
    "tests::public_manifest_contains_hashes_not_document_values_paths_or_native_claims",
    "tests::existing_output_relative_and_outside_boundaries_are_rejected",
}


def authority(root=ROOT):
    value = q.shared.lifecycle.checked_json(root / CAPSULE, CAPSULE_SHA)
    for path, digest in value["source_sha256"].items():
        public.checked(root / path, digest)
    public.source_guard(root)
    public.checked(root / q.HARNESS, q.HARNESS_SHA)
    return CAPSULE_SHA


def replacements(index):
    if index < 2:
        return {}
    if index == 2:
        return {"edit": {"foreColor": "#CC1100"}}
    if index == 3:
        return {"edit": {"foreColor": "#2E74B5"}}
    if 4 <= index <= 6:
        return {"edit": {"foreColor": "#CC1100" if index == 6 else "#2E74B5", **({"editable": "0"} if index == 5 else {})},
                "formCharPr": {"charPrIDRef": "5"}}
    if index == 7:
        return {"edit": {"editable": "0"}}
    if 8 <= index <= 13:
        return {"edit": {"name": NAMES[index - 8]}}
    if index == 14:
        return {"edit": {"groupName": 'P09 그룹 & <"\'>'}}
    raise ValueError("diagnostic_case_unknown")


def source(index, root=ROOT):
    if index < 2:
        path, digest = public.preparation.CASES["two-section-text" if index == 0 else "two-section-radio"]
    else:
        path, digest = q.output.prior.prior.CAPTURE, q.output.prior.prior.CAPTURE_SHA
    return public.checked(root / path, digest, 4 * 1024 * 1024)


def fields(row):
    expected = {"case_id", "file", "source_file", "pre_root_file", "source_kind", "source_package_sha256",
                "pre_root_package_sha256", "package_sha256", "package_bytes", "complete_map", "controls", "policy_sha256",
                "pre_root_state_sha256", "target_state_sha256", "target_controls_sha256", "document_flow_sha256", "property_receipt",
                "root_receipt", "packaging_transition_changes_complete_state", "root_control_intent_and_flow_preserved",
                "deterministic_retry", "stale_source_rejected"}
    q.exact(sorted(row), sorted(expected), "diagnostic_case_shape_invalid")


def verify_case(index, row, source_raw, pre_root_raw, target_raw, root=ROOT):
    fields(row)
    if source_raw != source(index, root):
        raise ValueError("diagnostic_original_source_substituted")
    before, pre_root, target = q.package(source_raw), q.package(pre_root_raw), q.package(target_raw)
    expected_parts = dict(before["parts"])
    changes = replacements(index)
    for tag, attributes in changes.items():
        expected_parts["Contents/section0.xml"] = q.edit_tag(expected_parts["Contents/section0.xml"], tag, attributes)
    expected = {"parts": expected_parts, "order": before["order"], "compression": before["compression"]}
    if expected != pre_root:
        raise ValueError("diagnostic_property_complete_output_mismatch")
    if index < 2 and source_raw != pre_root_raw:
        raise ValueError("diagnostic_root_input_not_raw_exact")
    prepared_parts = dict(expected_parts)
    if index < 2:
        metadata = prepared_parts["Contents/content.hpf"]
        old = b'href="section1.xml"'
        if metadata.count(old) != 1:
            raise ValueError("diagnostic_root_edit_ambiguous")
        prepared_parts["Contents/content.hpf"] = metadata.replace(old, b'href="Contents/section1.xml"')
    elif pre_root_raw != target_raw:
        raise ValueError("diagnostic_original_root_noop_not_raw_exact")
    if target != {"parts": prepared_parts, "order": before["order"], "compression": before["compression"]}:
        raise ValueError("diagnostic_root_complete_output_mismatch")
    count = 2 if index < 2 else 1
    for key, value in (("case_id", f"P09-35-C{index+1:02}"), ("file", f"p09-35-c{index+1:02}-{LABELS[index]}.hwpx"),
                       ("source_file", f"p09-35-c{index+1:02}-source.hwpx"), ("pre_root_file", f"p09-35-c{index+1:02}-pre-root.hwpx"),
                       ("source_kind", "immutable_failed_native_batch_input" if index < 2 else "original_native_capture"),
                       ("source_package_sha256", q.sha(source_raw)), ("pre_root_package_sha256", q.sha(pre_root_raw)),
                       ("package_sha256", q.sha(target_raw)), ("package_bytes", len(target_raw)), ("controls", count),
                       ("complete_map", q.expected_map(count)), ("deterministic_retry", True), ("stale_source_rejected", True),
                       ("root_control_intent_and_flow_preserved", True), ("packaging_transition_changes_complete_state", index < 2)):
        q.exact(row[key], value, "diagnostic_case_identity_invalid")
    for key in ("policy_sha256", "pre_root_state_sha256", "target_state_sha256", "document_flow_sha256"):
        q.shared.lifecycle.digest(row[key])
    if (row["pre_root_state_sha256"] == row["target_state_sha256"]) != (index >= 2):
        raise ValueError("diagnostic_packaging_state_transition_hidden")
    if type(row["target_controls_sha256"]) is not list or len(row["target_controls_sha256"]) != count:
        raise ValueError("diagnostic_control_fingerprint_inventory_invalid")
    for digest in row["target_controls_sha256"]:
        q.shared.lifecycle.digest(digest)
    source_projection = q.projection(source_raw)[1]
    final_projection = q.projection(target_raw)[1]
    if source_projection["sections"] != final_projection["sections"] or len(final_projection["controls"]) != count:
        raise ValueError("diagnostic_complete_physical_inventory_changed")
    if q.projection(pre_root_raw)[1] != final_projection:
        raise ValueError("diagnostic_root_control_intent_changed")
    header = q.xml(target["parts"]["Contents/header.xml"])
    styles = [n for n in header.iter(q.HH + "charPr") if n.get("id") in ("0", "5")]
    if {n.get("id"): n.get("textColor") for n in styles} != {"0": "#000000", "5": "#2E74B5"} or len(styles) != 2:
        raise ValueError("diagnostic_real_existing_style_catalog_changed")
    if index < 2:
        old_manifest = q.shared.lifecycle.checked_json(root / public.preparation.predecessor.MANIFEST, public.preparation.predecessor.MANIFEST_SHA)
        old = old_manifest["cases"][index + 4]
        q.exact(row["target_controls_sha256"], old["target_controls_sha256"], "diagnostic_previous_control_intent_changed")
        q.exact(row["policy_sha256"], old["policy_sha256"], "diagnostic_previous_policy_changed")
        q.exact(row["document_flow_sha256"], old["receipt"]["document_flow_sha256"], "diagnostic_previous_flow_changed")
        if row["property_receipt"] is not None:
            raise ValueError("diagnostic_root_property_operation_fabricated")
    else:
        expected_receipt = {
            "profile": q.output.PROFILE, "source_package_sha256": q.sha(source_raw), "output_package_sha256": q.sha(pre_root_raw),
            "document_flow_sha256": row["document_flow_sha256"], "target_state_sha256": row["pre_root_state_sha256"],
            "changed_sections": 1, "changed_attributes": sum(map(len, changes.values())),
            "non_section_parts_expanded_byte_exact": True, "outside_declared_edits_byte_exact": True,
            "entry_order_and_compression_preserved": True, "zip_header_policy": "rewritten_not_byte_exact",
            "legacy_reference_state": "id_index_validation_failed", "verified_native_reference_overlay_issues": 2,
        }
        q.exact(row["property_receipt"], expected_receipt, "diagnostic_property_receipt_mismatch")
        q.exact(row["document_flow_sha256"], q.output.prior.independent_actual(root)["document_flow_sha256"], "diagnostic_original_flow_changed")
    root_receipt = {
        "profile": public.preparation.PROFILE, "source_package_sha256": q.sha(pre_root_raw), "output_package_sha256": q.sha(target_raw),
        "source_manifest_sha256": q.sha(expected_parts["Contents/content.hpf"]), "output_manifest_sha256": q.sha(prepared_parts["Contents/content.hpf"]),
        "entry_count": len(prepared_parts), "changed_href_attributes": int(index < 2), "graph_relationships_and_spine_preserved": True,
        "preservation": {"non_manifest_parts_expanded_byte_exact": True, "manifest_outside_href_edits_byte_exact": True, "entry_order_and_compression_preserved": True},
        "zip_header_policy": "rewritten_not_byte_exact" if index < 2 else "original_raw_byte_exact",
        "qualification": "package_preparation_only_native_and_typed_reference_unqualified",
    }
    q.exact(row["root_receipt"], root_receipt, "diagnostic_root_receipt_mismatch")
    return {"case_id": row["case_id"], "package_sha256": q.sha(target_raw), "package_bytes": len(target_raw), "controls": count,
            "property_attribute_count": sum(map(len, changes.values())), "root_href_attribute_count": int(index < 2),
            "all_expanded_parts_outside_edits_order_compression_verified": True, "source_intent_independently_derived": True,
            "packaging_transition_changes_complete_state": index < 2, "native_normalization_qualified": False, "green_rows": 0}


def inspect(manifest_path, manifest_sha, root=ROOT, *, check_authority=True):
    path = q.shared.within(manifest_path, root / "fixtures/target-build")
    value = q.shared.lifecycle.checked_json(path, manifest_sha)
    q.exact({k: v for k, v in value.items() if k != "cases"}, {
        "schema_version": "hwpx-agent.p09-native-form-diagnostic-fixtures/v1", "task": "P09-35",
        "source_capture_sha256": q.output.prior.prior.CAPTURE_SHA, "previous_manifest_sha256": public.preparation.predecessor.MANIFEST_SHA,
        "actual_hangul": False, "render": "not_run", "green_rows": 0, "source_policy": "caller_declared_not_native_inferred",
        "raw_document_text_present": False, "absolute_private_paths_present": False,
    }, "diagnostic_manifest_claims_invalid")
    if type(value["cases"]) is not list or len(value["cases"]) != 15:
        raise ValueError("diagnostic_complete_case_inventory_invalid")
    names = {"fixture-manifest.json"}
    for i, label in enumerate(LABELS):
        names.update((f"p09-35-c{i+1:02}-{label}.hwpx", f"p09-35-c{i+1:02}-source.hwpx", f"p09-35-c{i+1:02}-pre-root.hwpx"))
    if {p.name for p in path.parent.iterdir()} != names:
        raise ValueError("diagnostic_complete_file_inventory_invalid")
    if check_authority:
        authority(root)
    result = []
    for i, row in enumerate(value["cases"]):
        fields(row)
        # Derive fixed names first. Untrusted row paths are never opened before exact validation.
        raws = [public.bounded_bytes(path.parent / n, 4 * 1024 * 1024) for n in (
            f"p09-35-c{i+1:02}-source.hwpx", f"p09-35-c{i+1:02}-pre-root.hwpx", f"p09-35-c{i+1:02}-{LABELS[i]}.hwpx")]
        result.append(verify_case(i, row, *raws, root))
    if len({row["package_sha256"] for row in result}) != 15:
        raise ValueError("diagnostic_duplicate_candidates_invalid")
    return {"schema_version": "hwpx-agent.p09-native-form-diagnostic-preparation/v1", "task": "P09-35",
            "state": "fifteen_complete_changed_cases_prepared_non_green", "manifest_sha256": manifest_sha,
            "public_api_source_capsule_sha256": CAPSULE_SHA, "cases": result,
            "claims": {"independent_complete_package_and_declared_intent_checks": True,
                       "independent_python_full_domain_serializer_qualified": False, "actual_hangul": False,
                       "native_open_failure_resolved": False, "arbitrary_color_or_name_repair_qualified": False,
                       "native_normalization_qualified": False, "production_routing_qualified": False,
                       "render": "not_run", "product_differential": "not_run", "green_rows": 0, "p09_complete": False},
            "privacy": {"raw_document_text_present": False, "absolute_private_paths_present": False,
                        "native_session_started": False, "trust_or_registry_changed": False}}


def compiled_tests(root=ROOT):
    process = subprocess.run(["cargo", "test", "-p", "hwpx-package", "--example", "p09_35_native_form_diagnostic_fixture",
                              "--locked", "--offline"], cwd=root, capture_output=True, timeout=60,
                             creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
    if process.returncode or not 0 < len(process.stdout) <= 256 * 1024 or len(process.stderr) > 1024 * 1024:
        raise ValueError("diagnostic_actual_compiled_tests_failed")
    stdout = process.stdout.decode("utf-8", errors="strict")
    return test_inventory(stdout)


def test_inventory(stdout):
    matches = re.findall(r"(?m)^test ([a-z0-9_:]+) \.\.\. (ok|FAILED|ignored)\s*$", stdout)
    if len(matches) != 4 or {n for n, _ in matches} != EXPECTED_TESTS or any(s != "ok" for _, s in matches):
        raise ValueError("diagnostic_compiled_inventory_invalid")
    if len(re.findall(r"(?m)^test result: ok\. 4 passed; 0 failed; 0 ignored;", stdout)) != 1:
        raise ValueError("diagnostic_compiled_summary_invalid")
    return {"passed": 4, "failed": 0, "ignored": 0, "names": sorted(EXPECTED_TESTS), "locked": True, "offline": True}


def qualify(manifest_path, manifest_sha, root=ROOT):
    authority(root)
    before = {p: q.sha(public.bounded_bytes(root / p, 2 * 1024 * 1024)) for p in SOURCES}
    result = inspect(manifest_path, manifest_sha, root)
    value = q.shared.lifecycle.checked_json(manifest_path, manifest_sha)
    verify_real_manifest(value, real_manifest(root))
    result["actual_public_generator_manifest_exact"] = True
    result["read_only_missing_native_output_probe"] = missing_native_outputs(root)
    result["actual_public_generator_rust_tests"] = compiled_tests(root)
    result["source_sha256"] = before
    authority(root)
    if before != {p: q.sha(public.bounded_bytes(root / p, 2 * 1024 * 1024)) for p in SOURCES}:
        raise ValueError("diagnostic_sources_changed_during_qualification")
    return result


def real_manifest(root=ROOT):
    process = subprocess.run(["cargo", "run", "-p", "hwpx-package", "--example", "p09_35_native_form_diagnostic_fixture",
                              "--locked", "--offline", "--", "--oracle-manifest"], cwd=root, capture_output=True, timeout=60,
                             creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
    if process.returncode or not 0 < len(process.stdout) <= 512 * 1024 or len(process.stderr) > 1024 * 1024:
        raise ValueError("diagnostic_actual_public_manifest_probe_failed")
    return json.loads(process.stdout, object_pairs_hook=q.shared.lifecycle.duplicate_guard)


def verify_real_manifest(value, actual):
    q.exact(value, actual, "diagnostic_actual_public_manifest_mismatch")


def missing_native_outputs(root=ROOT):
    prefix = "p09-35-not-dispatched"
    private = root / "implementation/p09/evidence/private"
    if any((private / f"p09-17-field-auto-number-target-{prefix}-c{i+1:02}-attempt01").exists() for i in range(15)):
        raise ValueError("diagnostic_missing_output_probe_directory_exists")
    process = subprocess.run(["cargo", "run", "-p", "hwpx-package", "--example", "p09_35_native_form_diagnostic_fixture",
                              "--locked", "--offline", "--", "--inspect-native-batch", prefix], cwd=root, capture_output=True, timeout=60,
                             creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
    if process.returncode or not 0 < len(process.stdout) <= 256 * 1024 or len(process.stderr) > 1024 * 1024:
        raise ValueError("diagnostic_missing_native_output_probe_failed")
    value = json.loads(process.stdout, object_pairs_hook=q.shared.lifecycle.duplicate_guard)
    expected = {"schema_version": "hwpx-agent.p09-native-form-diagnostic-readback/v1", "task": "P09-35",
                "qualification": "file_readback_only_native_trace_binding_required", "native_session_started": False,
                "raw_document_text_present": False, "absolute_private_paths_present": False, "green_rows": 0, "p09_complete": False}
    q.exact({k: v for k, v in value.items() if k != "cases"}, expected, "diagnostic_missing_output_claims_invalid")
    missing = {"complete_public_reader_or_policy_binding": "not_run", "error_code": "native_output_missing", "green_rows": 0}
    rows = [{"case_id": f"P09-35-C{i+1:02}", "saved": missing, "reopened": missing} for i in range(15)]
    q.exact(value["cases"], rows, "diagnostic_missing_outputs_promoted")
    return {"cases": 15, "not_run_stages": 30, "native_session_started": False,
            "file_readback_does_not_prove_native_session": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True); parser.add_argument("--manifest-sha256", required=True)
    group = parser.add_mutually_exclusive_group(); group.add_argument("--output", type=Path); group.add_argument("--verify", type=Path)
    args = parser.parse_args()
    try:
        raw = q.shared.lifecycle.canonical_bytes(qualify(args.manifest, args.manifest_sha256))
        if args.output:
            path = args.output.absolute(); q.shared.within(path.parent, ROOT / "implementation/p09/evidence")
            if "private" in path.relative_to(ROOT).parts or path.is_symlink() or path.is_junction():
                raise ValueError("diagnostic_public_evidence_boundary_invalid")
            with path.open("xb") as stream: stream.write(raw)
        if args.verify and public.bounded_bytes(args.verify, 512 * 1024) != raw:
            raise ValueError("diagnostic_capsule_reproduction_mismatch")
    except (OSError, ValueError, KeyError, TypeError, UnicodeError, subprocess.SubprocessError, ET.ParseError, zipfile.BadZipFile) as error:
        code = str(error) if type(error) is ValueError and re.fullmatch(r"[a-z_]+", str(error)) else "diagnostic_preparation_failed"
        print(json.dumps({"state": "fail", "error_code": code})); return 2
    print(json.dumps({"state": "pass", "qualification_sha256": q.sha(raw), "complete_cases": 15,
                      "actual_public_generator_tests_passed": 4, "native_session_started": False, "green_rows": 0})); return 0


if __name__ == "__main__":
    raise SystemExit(main())
