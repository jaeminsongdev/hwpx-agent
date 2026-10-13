#!/usr/bin/env python3
"""Independently inspect real compiled global package outputs; no Hancom execution."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from xml.etree import ElementTree as ET
import zipfile

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.p09 import qualify_native_form_package_binding as prior

ROOT = prior.ROOT
export = prior.export
SHARED = prior.SHARED
RECEIPT = "implementation/p09/evidence/p09-29-native-form-package-binding.current-2020.v1.json"
RECEIPT_SHA = "82a4112980c36bb901870d88d28810913bdbe64e7b3002f8b117b090bfcb9367"
PROFILE = "hwpx-agent.native-form-package.global-attribute-output/v1"
TARGET = "native_form_package_output_pending_export"
ACTUAL_TEST = "actual_property_output_reopens_complete_package_and_changes_only_declared_attribute"
EXPECTED_TESTS = {
    ACTUAL_TEST,
    "global_tab_reordering_respects_document_order_without_local_contiguity_assumption",
    "global_tab_can_disable_one_section_while_enabling_other_global_zero",
    "properties_change_all_supported_common_and_character_values_with_literal_escaping",
    "optional_missing_group_attribute_is_inserted_without_other_start_tag_normalization",
    "unchanged_noncanonical_lexical_attributes_and_single_quotes_remain_byte_exact",
    "stale_source_header_preview_or_body_cannot_reuse_output_plan",
    "external_output_verifier_rejects_each_changed_nonsection_part_and_target_substitution",
    "external_output_verifier_rejects_extra_missing_order_and_compression_changes",
    "payload_default_validation_and_command_changes_are_not_silently_dropped",
    "changed_target_flow_and_insertion_are_rejected_not_reinterpreted",
    "complete_map_policy_character_border_and_protection_admission_still_fail_closed",
    "finite_archive_part_total_bounds_fail_without_returning_partial_artifacts",
    "debug_errors_and_public_receipt_expose_no_document_text_or_private_paths",
    "cross_section_required_radio_group_is_validated_globally_during_actual_output",
    "form_free_section_is_preserved_with_complete_global_map_and_flow",
    "declared_binary_resources_are_byte_exact_and_external_resource_drift_rejected",
    "observed_native_ids_are_preserved_and_never_replaced_with_component_reservations",
    "character_reference_change_is_bound_to_real_header_catalog_and_header_bytes_preserved",
    "native_form_package_lowering::tests::bounded_zip_sink_checks_write_seek_and_negative_offsets_before_allocation",
    "native_form_package_lowering::tests::attribute_escape_preserves_literal_whitespace_and_xml_metacharacters",
}
SOURCES = (*prior.SOURCES,
           "tools/p09/qualify_native_form_package_output.py",
           "tools/p09/tests/test_native_form_package_output.py",
           "implementation/p09/P09-30_NATIVE_FORM_PACKAGE_OUTPUT_POLICY.md",
           "crates/hwpx-package/src/native_form_package_lowering.rs",
           "crates/hwpx-package/tests/native_form_package_output_pending_export.rs")
CASES = ("actual-property", "global-tab", "disabled-tab", "radio-tab")
ORACLE_ENV = "HWPX_AGENT_P09_30_ORACLE_DIRECTORY"


def sources(root=ROOT):
    record = json.loads(export.checked(root / RECEIPT, RECEIPT_SHA, 512 * 1024))
    for path, expected in record["source_sha256"].items():
        export.checked(root / path, expected)
    prior.sources(root)
    raw = export.checked(root / export.LIB, export.CURRENT_LIB)
    if b"mod native_form_package_lowering;" in raw:
        raise ValueError("native_form_output_pending_export_changed")
    return record


def read_package(raw):
    if type(raw) is not bytes or not 0 < len(raw) <= 32 * 1024 * 1024:
        raise ValueError("native_form_output_archive_bound")
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        entries = archive.infolist()
        names = [n.filename for n in entries]
        if not 0 < len(entries) <= 256 or len(set(names)) != len(names):
            raise ValueError("native_form_output_inventory_invalid")
        if any(n.is_dir() or n.flag_bits & 1 or n.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
               or not 0 < n.file_size <= 2 * 1024 * 1024 or n.compress_size <= 0
               or n.filename.startswith("/") or "\\" in n.filename or ":" in n.filename
               or any(p in ("", ".", "..") for p in n.filename.split("/")) for n in entries):
            raise ValueError("native_form_output_inventory_invalid")
        if sum(n.file_size for n in entries) > 16 * 1024 * 1024:
            raise ValueError("native_form_output_expanded_bound")
        parts = {n.filename: archive.read(n) for n in entries}  # Full CRC read, no extraction.
        if any(len(parts[n.filename]) != n.file_size for n in entries):
            raise ValueError("native_form_output_expanded_bound")
    return {"parts": parts, "order": names, "compression": [n.compress_type for n in entries]}


def original(root=ROOT):
    prior.prior.capture(root)
    raw = export.checked(root / prior.prior.CAPTURE, prior.prior.CAPTURE_SHA, 14556)
    if len(raw) != 14556:
        raise ValueError("native_form_output_original_drift")
    return raw, read_package(raw)


def derived_parts(case, original_parts):
    parts = dict(original_parts)
    if case == "actual-property":
        return parts
    first = parts["Contents/section0.xml"].decode("utf-8")
    edits = list(ET.fromstring(first).iter(prior.HP + "edit"))
    if len(edits) != 1:
        raise ValueError("native_form_output_original_inventory_changed")
    native_name = edits[0].get("name")
    second = first.replace('<hp:p id="0"', '<hp:p id="10"').replace('<hp:p id="1"', '<hp:p id="11"')
    second = second.replace(f'name="{native_name}"', 'name="second-native-derived-field"').replace('tabOrder="1"', 'tabOrder="2"')
    parts["Contents/section1.xml"] = second.encode()
    parts["Contents/header.xml"] = parts["Contents/header.xml"].replace(b'secCnt="1"', b'secCnt="2"')
    opf = parts["Contents/content.hpf"].decode()
    prefix = "opf:" if "</opf:manifest>" in opf else ""
    parts["Contents/content.hpf"] = opf.replace(f"</{prefix}manifest>", f'<{prefix}item id="section1" href="section1.xml" media-type="application/xml"/></{prefix}manifest>').replace(
        f"</{prefix}spine>", f'<{prefix}itemref idref="section1" linear="yes"/></{prefix}spine>').encode()
    if case == "radio-tab":
        for i in range(2):
            part = f"Contents/section{i}.xml"
            text = parts[part].decode()
            start = text.index("<hp:edit "); end = text.index("</hp:edit>") + len("</hp:edit>")
            edit = text[start:end]; geometry = edit[edit.index("<hp:sz "):-len("</hp:edit>")]
            value = "CHECKED" if i == 0 else "UNCHECKED"
            radio = (f'<hp:radioBtn name="radio-{i}" foreColor="#000000" backColor="#FFFFFF" groupName="" tabStop="1" editable="1" tabOrder="{i+1}" enabled="1" borderTypeIDRef="0" drawFrame="1" printable="1" command="" caption="radio" value="{value}" radioGroupName="complete-group" triState="0" backStyle="TRANSPARENT"><hp:formCharPr charPrIDRef="0" followContext="0" autoSz="0" wordWrap="1"/>{geometry}</hp:radioBtn>')
            parts[part] = (text[:start] + radio + text[end:]).encode()
    return parts


def expected_edits(case):
    if case == "actual-property":
        return {"Contents/section0.xml": [(b'enabled="1"', b'enabled="0"')]}
    if case == "global-tab":
        return {"Contents/section1.xml": [(b'tabOrder="2"', b'tabOrder="0"')]}
    if case == "disabled-tab":
        return {"Contents/section0.xml": [(b'tabStop="1"', b'tabStop="0"'), (b'tabOrder="1"', b'tabOrder="-1"')],
                "Contents/section1.xml": [(b'tabOrder="2"', b'tabOrder="0"')]}
    if case == "radio-tab":
        return {"Contents/section0.xml": [(b'tabOrder="1"', b'tabOrder="0"')],
                "Contents/section1.xml": [(b'tabOrder="2"', b'tabOrder="1"')]}
    raise ValueError("native_form_output_case_unknown")


def verify_case(case, source_raw, output_raw, original_raw, baseline):
    source = read_package(source_raw); output = read_package(output_raw)
    parts = derived_parts(case, baseline["parts"])
    if case == "actual-property":
        if source_raw != original_raw:
            raise ValueError("native_form_output_original_substituted")
        expected_order, expected_compression = baseline["order"], baseline["compression"]
    else:
        expected_order = ["mimetype", *sorted(p for p in parts if p != "mimetype")]
        expected_compression = [zipfile.ZIP_STORED, *([zipfile.ZIP_DEFLATED] * (len(parts) - 1))]
    if source["parts"] != parts or source["order"] != expected_order or source["compression"] != expected_compression:
        raise ValueError("native_form_output_complete_source_derivation_mismatch")
    expected = dict(parts)
    edits = expected_edits(case)
    for part, replacements in edits.items():
        for old, new in replacements:
            if expected[part].count(old) != 1:
                raise ValueError("native_form_output_independent_edit_ambiguous")
            expected[part] = expected[part].replace(old, new)
    if output["parts"] != expected or output["order"] != source["order"] or output["compression"] != source["compression"]:
        raise ValueError("native_form_output_independent_package_mismatch")
    changed = sum(parts[n] != expected[n] for n in parts)
    if changed != len(edits):
        raise ValueError("native_form_output_independent_edit_count_mismatch")
    return {"source_package_sha256": export.sha256(source_raw), "output_package_sha256": export.sha256(output_raw),
            "entry_count": len(parts), "changed_sections": changed, "changed_attributes": sum(map(len, edits.values())),
            "output_section_sha256": export.sha256(expected["Contents/section0.xml"]),
            "all_parts_and_outside_edits_independently_byte_exact": True,
            "complete_order_and_compression_independently_verified": True,
            "derived_fixture_not_native_save_evidence": case != "actual-property"}


def artifacts(directory, root=ROOT):
    expected_names = {f"{c}-{stage}.hwpx" for c in CASES for stage in ("source", "output")}
    if {p.name for p in directory.iterdir()} != expected_names:
        raise ValueError("native_form_output_oracle_artifact_inventory_invalid")
    original_raw, baseline = original(root)
    return {c: verify_case(c,
                          export.bounded_bytes(SHARED.within(directory / f"{c}-source.hwpx", directory), 32 * 1024 * 1024),
                          export.bounded_bytes(SHARED.within(directory / f"{c}-output.hwpx", directory), 32 * 1024 * 1024),
                          original_raw, baseline) for c in CASES}


def test_output(stdout):
    found = re.findall(r"(?m)^test ([a-z0-9_:]+) \.\.\. (ok|FAILED|ignored)\s*$", stdout)
    if len(found) != 21 or {n for n, _ in found} != EXPECTED_TESTS or any(s != "ok" for _, s in found) or len(re.findall(
            r"(?m)^test result: ok\. 21 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;.*$", stdout)) != 1:
        raise ValueError("native_form_output_test_inventory_invalid")
    return {"passed": 21, "failed": 0, "ignored": 0, "names": sorted(EXPECTED_TESTS), "locked": True, "offline": True}


def cargo(extra=(), directory=None, root=ROOT):
    env = dict(os.environ); env.pop(ORACLE_ENV, None)
    if directory is not None:
        env[ORACLE_ENV] = str(directory)
    process = subprocess.run(["cargo", "test", "-p", "hwpx-package", "--test", TARGET, "--locked", "--offline", *extra],
                             cwd=root, capture_output=True, timeout=60, env=env,
                             creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    if process.returncode or not 0 < len(process.stdout) <= 256 * 1024 or len(process.stderr) > 1024 * 1024:
        raise ValueError("native_form_output_compiled_tests_failed")
    return process.stdout.decode("utf-8", errors="strict")


def verify_probe(value, proof, independent_source):
    expected = {"profile": PROFILE, "source_package_sha256": proof["source_package_sha256"],
                "output_package_sha256": proof["output_package_sha256"], "document_flow_sha256": independent_source["document_flow_sha256"],
                "changed_sections": 1, "changed_attributes": 1, "non_section_parts_expanded_byte_exact": True,
                "outside_declared_edits_byte_exact": True, "entry_order_and_compression_preserved": True,
                "zip_header_policy": "rewritten_not_byte_exact", "legacy_reference_state": "id_index_validation_failed",
                "verified_native_reference_overlay_issues": 2, "output_section_sha256": proof["output_section_sha256"]}
    if not SHARED.oracle.exact(value, expected):
        raise ValueError("native_form_output_independent_probe_mismatch")


def qualify(root=ROOT):
    record = sources(root)
    if SHARED.lifecycle.canonical_bytes(prior.qualify(root)) != export.checked(root / RECEIPT, RECEIPT_SHA, 512 * 1024):
        raise ValueError("native_form_output_predecessor_reproduction_mismatch")
    before = {p: export.sha256(export.bounded_bytes(root / p, 2 * 1024 * 1024)) for p in SOURCES}
    independent = prior.independent_actual(root)
    with tempfile.TemporaryDirectory(prefix="hwpx-p09-30-output-oracle-") as temporary:
        directory = Path(temporary).resolve()
        tests = test_output(cargo(directory=directory, root=root))
        proof = artifacts(directory, root)
        output = cargo((ACTUAL_TEST, "--", "--exact", "--nocapture"), root=root)
        probes = re.findall(r"p09_30_probe_json=(\{[^\n]*\})", output)
        if len(probes) != 1:
            raise ValueError("native_form_output_actual_probe_missing")
        value = json.loads(probes[0], object_pairs_hook=SHARED.lifecycle.duplicate_guard)
        verify_probe(value, proof["actual-property"], independent)
    sources(root)
    if before != {p: export.sha256(export.bounded_bytes(root / p, 2 * 1024 * 1024)) for p in SOURCES} or prior.independent_actual(root) != independent:
        raise ValueError("native_form_output_source_or_capture_changed")
    return {"schema_version": "hwpx-agent.p09-native-form-package-output/v1", "task": "P09-30",
            "state": "complete_global_package_output_component_non_green", "source_predecessor_sha256": RECEIPT_SHA,
            "source_sha256": before, "actual_rust_tests": tests, "independent_generated_package_checks": proof,
            "claims": {"actual_package_output_lowering_implemented": True, "independent_all_expanded_part_output_comparison": True,
                       "global_tab_and_cross_section_required_radio_output_component_tested": True,
                       "immutable_predecessor_sources_and_receipt_preserved": True, "legacy_index_failure_preserved": True,
                       "independent_python_full_domain_serializer_qualified": False, "zip_headers_raw_byte_exact": False,
                       "public_package_exports_connected": False, "complete_native_target_cases_prepared": False,
                       "new_native_target_execution": False, "general_document_protection_qualified": False,
                       "nonzero_form_border_type_qualified": False, "production_routing_qualified": False,
                       "render": "not_run", "product_differential": "not_run", "green_rows": 0,
                       "p09_complete": False, "product_complete": False},
            "privacy": {"raw_document_text_present": False, "absolute_private_paths_present": False,
                        "native_session_started": False, "trust_or_registry_changed": False, "external_network_invoked": False}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(); group.add_argument("--output", type=Path); group.add_argument("--verify", type=Path)
    args = parser.parse_args()
    try:
        raw = SHARED.lifecycle.canonical_bytes(qualify())
        if args.output:
            output = args.output.absolute(); SHARED.within(output.parent, ROOT / "implementation/p09/evidence")
            if output.is_symlink() or output.is_junction() or "private" in output.relative_to(ROOT).parts:
                raise ValueError("native_form_output_public_boundary")
            with output.open("xb") as handle: handle.write(raw)
        if args.verify and export.bounded_bytes(args.verify, 512 * 1024) != raw:
            raise ValueError("native_form_output_capsule_reproduction_mismatch")
    except (OSError, ValueError, KeyError, TypeError, UnicodeError, subprocess.SubprocessError, ET.ParseError, zipfile.BadZipFile) as error:
        code = str(error) if type(error) is ValueError and re.fullmatch(r"[a-z_]+", str(error)) else "native_form_output_qualification_failed"
        print(json.dumps({"state": "fail", "error_code": code})); return 2
    print(json.dumps({"state": "pass", "qualification_state": "complete_global_package_output_component_non_green",
                      "qualification_sha256": export.sha256(raw), "rust_tests_passed": 21, "green_rows": 0, "p09_complete": False})); return 0


if __name__ == "__main__":
    raise SystemExit(main())
