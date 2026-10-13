#!/usr/bin/env python3
"""Independent actual-package fingerprint and compiled binder qualification; no new native run."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import posixpath
import re
import subprocess
import sys
from xml.etree import ElementTree as ET
import zipfile

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.p09 import qualify_native_form_compatibility as prior
from tools.p09 import verify_p08_additive_export_source_bridge_v3 as export

ROOT = prior.ROOT
SHARED = prior.shared
RECEIPT = "implementation/p09/evidence/p09-28-native-form-public-export-source.current-2020.r02.v3.json"
RECEIPT_SHA = "cc9318ba2f75d16dad15f59ee5a6d704fcca14e6e772b4740d5b6d94a14026bc"
TARGET = "native_form_package_pending_export"
ACTUAL_TEST = "actual_complete_capture_bindings_and_missing_identity_are_read_without_injection"
EXPECTED_TESTS = {
    ACTUAL_TEST, "legacy_shape_index_actual_failure_and_non_linear_header_spine_are_preserved",
    "complete_global_state_and_real_property_plan_bind_actual_metadata",
    "forged_external_metadata_and_non_form_hashes_are_rejected",
    "derived_multi_section_complete_global_tab_plan_not_a_native_receipt",
    "missing_reordered_extra_or_cross_section_duplicate_maps_rejected",
    "source_metadata_change_cannot_reuse_sealed_readback_or_plan",
    "actual_form_character_and_border_catalog_dangling_refs_fail_closed",
    "explicit_policy_is_complete_and_native_value_not_caller_fabricated",
    "observed_protection_signal_blocks_plan_without_claiming_unlocked_absence",
    "actual_flow_not_constant_component_flow_and_wrong_plan_rejected",
    "finite_bounds_and_debug_errors_never_expose_private_values",
    "extra_unknown_or_dangling_non_form_refs_are_not_ignored_by_native_overlay",
    "duplicate_observed_native_ids_across_sections_are_rejected",
    "empty_form_section_still_has_complete_map_flow_and_package_binding",
    "target_property_reference_catalogs_are_checked_before_plan_binding",
    "all_declared_binary_resource_paths_bind_bytes_not_only_bin_data_prefix",
}
SOURCES = ("tools/p09/qualify_native_form_package_binding.py",
           "tools/p09/tests/test_native_form_package_binding.py",
           "implementation/p09/P09-29_NATIVE_FORM_PACKAGE_BINDING_POLICY.md",
           "crates/hwpx-package/src/native_form_package.rs",
           "crates/hwpx-package/tests/native_form_package_pending_export.rs",
           "crates/hwpx-package/src/lib.rs", "crates/hwpx-package/src/native_form_hwpx.rs",
           "crates/hwpx-package/src/reader.rs", "crates/hwpx-package/src/graph.rs",
           "crates/hwpx-package/src/id_index.rs", "crates/hwpx-package/src/preservation.rs",
           "crates/hwpx-package/src/character_style.rs", "crates/hwpx-package/src/preserving_xml.rs",
           "crates/hwpx-package/src/safe_xml.rs", "crates/domain-ir/src/form_control.rs")
HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
FORMS = {HP + name for name in ("edit", "checkBtn", "radioBtn", "comboBox", "listBox")}
TAG = re.compile(rb'<([A-Za-z_][A-Za-z0-9_.:-]*)(\s(?:[^<>\'\"]|\'[^\']*\'|\"[^\"]*\")*?)?/?>')
ATTR = re.compile(rb'([A-Za-z_][A-Za-z0-9_.:-]*)\s*=\s*([\'\"])(.*?)\2', re.S)


def frame(h, raw: bytes):
    h.update(len(raw).to_bytes(8, "little")); h.update(raw)


def digest_frames(rows):
    h = hashlib.sha256()
    for value in rows:
        frame(h, value)
    return h.hexdigest()


def sources(root=ROOT):
    record = json.loads(export.checked(root / RECEIPT, RECEIPT_SHA, 512 * 1024))
    for path, expected in record["source_sha256"].items():
        export.checked(root / path, expected)
    for name in export.RECEIPTS:
        export.historical_sources(name, root)
    if b"mod native_form_package;" in export.checked(root / export.LIB, export.CURRENT_LIB):
        raise ValueError("native_form_package_pending_export_changed")
    return record


def independent_actual(root=ROOT):
    observed = prior.capture(root)
    raw = SHARED.oracle.bounded_bytes(root / prior.CAPTURE, 32 * 1024 * 1024)
    if export.sha256(raw) != prior.CAPTURE_SHA:
        raise ValueError("native_form_package_actual_capture_changed_before_read")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        entries = z.infolist()
        if (len(entries) != 11 or len({n.filename for n in entries}) != 11
                or any(n.is_dir() or not 0 < n.file_size <= 2 * 1024 * 1024 for n in entries)
                or sum(n.file_size for n in entries) > 16 * 1024 * 1024):
            raise ValueError("native_form_package_actual_part_inventory_invalid")
        parts = {n: z.read(n) for n in z.namelist()}
    if len(parts) != 11 or len(parts) > 256 or sum(map(len, parts.values())) > 16 * 1024 * 1024:
        raise ValueError("native_form_package_actual_part_inventory_invalid")
    header = parts["Contents/header.xml"]
    border = re.findall(rb'<hh:borderFills\b.*?</hh:borderFills>', header, re.S)
    if len(border) != 1:
        raise ValueError("native_form_package_actual_border_invalid")
    opf = ET.fromstring(parts["Contents/content.hpf"])
    items = {n.get("id"): n.get("href") if n.get("href") in parts else posixpath.normpath(posixpath.join("Contents", n.get("href")))
             for n in opf.iter() if n.tag.rsplit("}", 1)[-1] == "item"}
    spine = [items[n.get("idref")] for n in opf.iter() if n.tag.rsplit("}", 1)[-1] == "itemref"]
    if spine != ["Contents/header.xml", "Contents/section0.xml"]:
        raise ValueError("native_form_package_actual_spine_invalid")
    sections = [n for n in spine if n != "Contents/header.xml"]
    section = parts[sections[0]]
    control = list(re.finditer(rb'<hp:edit\b.*?</hp:edit>', section, re.S))
    if len(control) != 1:
        raise ValueError("native_form_package_actual_control_invalid")
    c = control[0]
    non_form = digest_frames([section[:c.start()], section[c.end():]])
    flow = digest_frames([b"native-form-package-flow/v1", sections[0].encode(), non_form.encode()])
    opaque = digest_frames([v for path in sorted(parts) if path not in sections for v in (path.encode(), parts[path])])
    protection = digest_frames([v for path in sorted(parts) if path in ("Contents/header.xml", "settings.xml") for v in (path.encode(), parts[path])])
    refs = hashlib.sha256()
    resource_frames = []
    for path in sorted(parts):
        lower = path.lower()
        if lower.startswith("bindata/") or (path in items.values() and path not in sections and path not in
                ("Contents/header.xml", "settings.xml", "version.xml") and not lower.startswith(("preview/", "meta-inf/"))):
            resource_frames.extend((path.encode(), parts[path]))
        if not lower.endswith((".xml", ".hpf", ".rdf")):
            continue
        data = parts[path]
        tree = ET.fromstring(data)
        elements = list(tree.iter())
        lex = list(TAG.finditer(data))
        if len(lex) != len(elements):
            raise ValueError("native_form_package_reference_lexical_inventory_invalid")
        parents = {child: parent for parent in tree.iter() for child in parent}
        namespaces = {"xml": "http://www.w3.org/XML/1998/namespace"}
        for tag in lex:
            for match in ATTR.finditer(tag.group(0)):
                name = match.group(1).decode()
                if name == "xmlns" or name.startswith("xmlns:"):
                    prefix = name.split(":", 1)[-1] if ":" in name else ""
                    uri = match.group(3).decode()
                    if prefix in namespaces and namespaces[prefix] != uri:
                        raise ValueError("native_form_package_actual_namespace_scope_unsupported")
                    namespaces[prefix] = uri
        for index, (node, tag) in enumerate(zip(elements, lex)):
            parent = node
            inside = False
            while parent is not None:
                inside |= parent.tag in FORMS
                parent = parents.get(parent)
            if inside:
                continue
            if not node.tag.startswith("{"):
                raise ValueError("native_form_package_actual_namespace_invalid")
            ns, local = node.tag[1:].split("}", 1)
            for a in ATTR.finditer(tag.group(0)):
                qualified = a.group(1).decode()
                if qualified == "xmlns" or qualified.startswith("xmlns:"):
                    continue
                attr_ns, attr_name = (namespaces[qualified.split(":")[0]], qualified.split(":")[1]) if ":" in qualified else ("", qualified)
                if attr_name.endswith("IDRef") or attr_name in ("id", "instid", "instId", "fieldid"):
                    for value in (path.encode(), index.to_bytes(8, "little"), ns.encode(), local.encode(),
                                  attr_ns.encode(), attr_name.encode(), a.group(3)):
                        frame(refs, value)
    return {"package_sha256": observed["package_sha256"], "document_flow_sha256": flow, "section_count": 1,
            "bindings": {"style_catalog_sha256": hashlib.sha256(header).hexdigest(),
                         "border_catalog_sha256": hashlib.sha256(border[0]).hexdigest(),
                         "resource_inventory_sha256": digest_frames(resource_frames),
                         "reference_inventory_sha256": refs.hexdigest(), "document_protection_sha256": protection,
                         "opaque_document_state_sha256": opaque, "protection_signal_observed": False},
            "legacy_index_state": "id_index_validation_failed", "verified_overlay_issues": 2}


def test_output(stdout):
    found = re.findall(r"(?m)^test ([a-z0-9_]+) \.\.\. (ok|FAILED|ignored)\s*$", stdout)
    if (len(found) != 17 or {n for n, _ in found} != EXPECTED_TESTS or any(s != "ok" for _, s in found)
            or len(re.findall(r"(?m)^test result: ok\. 17 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;.*$", stdout)) != 1):
        raise ValueError("native_form_package_test_inventory_invalid")
    return {"passed": 17, "failed": 0, "ignored": 0, "names": sorted(EXPECTED_TESTS), "locked": True, "offline": True}


def cargo(extra=(), root=ROOT):
    process = subprocess.run(["cargo", "test", "-p", "hwpx-package", "--test", TARGET, "--locked", "--offline", *extra],
                             cwd=root, capture_output=True, timeout=60,
                             creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    if process.returncode or not 0 < len(process.stdout) <= 128 * 1024:
        raise ValueError("native_form_package_actual_tests_failed")
    return process.stdout.decode("utf-8", errors="strict")


def verify_probe(value, expected):
    if not SHARED.oracle.exact(value, expected):
        raise ValueError("native_form_package_independent_probe_mismatch")


def qualify(root=ROOT):
    sources(root)
    before = {p: export.sha256(export.bounded_bytes(root / p, 2 * 1024 * 1024)) for p in SOURCES}
    independent = independent_actual(root)
    tests = test_output(cargo(root=root))
    output = cargo((ACTUAL_TEST, "--", "--exact", "--nocapture"), root)
    probes = re.findall(r"p09_29_probe_json=(\{[^\n]*\})", output)
    if len(probes) != 1:
        raise ValueError("native_form_package_actual_probe_missing")
    verify_probe(json.loads(probes[0]), independent)
    sources(root)
    if before != {p: export.sha256(export.bounded_bytes(root / p, 2 * 1024 * 1024)) for p in SOURCES} or independent_actual(root) != independent:
        raise ValueError("native_form_package_source_or_capture_changed_during_test")
    return {"schema_version": "hwpx-agent.p09-native-form-package-binding/v1", "task": "P09-29",
            "state": "complete_package_binding_component_non_green", "public_source_predecessor_sha256": RECEIPT_SHA,
            "source_sha256": before, "actual_package_independent_bindings": independent, "actual_rust_tests": tests,
            "claims": {"complete_package_bindings_independently_read": True, "explicit_policy_not_native_inference": True,
                       "global_multi_section_state_and_tab_plan_component_tested": True, "legacy_index_failure_preserved": True,
                       "package_component_exports_connected": False, "package_lowering_implemented": False,
                       "complete_target_cases_prepared": False, "new_native_target_execution": False,
                       "general_document_protection_qualified": False, "nonzero_form_border_type_qualified": False,
                       "production_routing_qualified": False, "render": "not_run", "product_differential": "not_run",
                       "green_rows": 0, "p09_complete": False, "product_complete": False},
            "privacy": {"raw_document_text_present": False, "absolute_private_paths_present": False,
                        "native_session_started": False, "trust_or_registry_changed": False, "external_network_invoked": False}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--output", type=Path); group.add_argument("--verify", type=Path)
    args = parser.parse_args()
    try:
        value = qualify()
        raw = SHARED.lifecycle.canonical_bytes(value)
        if args.output:
            output = args.output.absolute()
            SHARED.within(output.parent, ROOT / "implementation/p09/evidence")
            if output.is_symlink() or output.is_junction() or "private" in output.relative_to(ROOT).parts:
                raise ValueError("native_form_package_public_boundary")
            with output.open("xb") as handle: handle.write(raw)
        if args.verify and export.bounded_bytes(args.verify, 512 * 1024) != raw:
            raise ValueError("native_form_package_capsule_reproduction_mismatch")
    except (OSError, ValueError, KeyError, TypeError, UnicodeError, subprocess.SubprocessError, ET.ParseError, zipfile.BadZipFile) as error:
        code = str(error) if type(error) is ValueError and re.fullmatch(r"[a-z_]+", str(error)) else "native_form_package_qualification_failed"
        print(json.dumps({"state": "fail", "error_code": code})); return 2
    print(json.dumps({"state": "pass", "qualification_state": value["state"], "qualification_sha256": export.sha256(raw),
                      "rust_tests_passed": 17, "green_rows": 0, "p09_complete": False})); return 0


if __name__ == "__main__":
    raise SystemExit(main())
