#!/usr/bin/env python3
"""Independent six-case package preflight and strict saved/reopened observations."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from xml.etree import ElementTree as ET
import zipfile

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.p09 import qualify_native_form_package_output as output
from tools.p09 import verify_p08_additive_export_source_bridge_v4 as public

ROOT = output.ROOT
shared = output.SHARED
sha = output.export.sha256
HP = output.prior.HP
HH = "{http://www.hancom.co.kr/hwpml/2011/head}"
OPF = "{http://www.idpf.org/2007/opf/}"
CAPSULE = "implementation/p09/evidence/p09-31-native-form-package-public-export-source.current-2020.v4.json"
CAPSULE_SHA = "22af68bce9aace86095c384f3c6d616145e3bce6a4b46ab0eca10c829e85b503"
HARNESS = "implementation/p09/tools/run-hancom-2020-field-auto-number-target.ps1"
HARNESS_SHA = "30341f7a7ff5106e4c3ac74331abdd9b612ec4d88eb060387b506809399338a9"
FILES = (
    "p09-32-c01-enabled-property.hwpx", "p09-32-c02-colors-editable.hwpx",
    "p09-32-c03-literal-name-group.hwpx", "p09-32-c04-character-properties.hwpx",
    "p09-32-c05-global-tab.hwpx", "p09-32-c06-cross-section-radio-tab.hwpx",
)
KINDS = ("original_native_capture",) * 4 + ("derived_two_section_text", "derived_cross_section_radio")
SOURCES = (
    "tools/p09/inspect_native_form_complete_fixture.py",
    "tools/p09/tests/test_native_form_complete_fixture.py",
    "crates/hwpx-package/examples/p09_32_native_form_target_fixture.rs",
    "implementation/p09/P09-32_NATIVE_FORM_COMPLETE_BATCH_POLICY.md",
    HARNESS,
)


def exact(value, expected, code):
    if not shared.oracle.exact(value, expected):
        raise ValueError(code)


def xml(raw):
    if not raw or b"<!doctype" in raw.lower() or b"<!entity" in raw.lower():
        raise ValueError("form_active_xml_rejected")
    return ET.fromstring(raw, parser=ET.XMLParser(target=ET.TreeBuilder(insert_comments=True, insert_pis=True)))


def package(raw):
    result = output.read_package(raw)
    if result["parts"].get("mimetype") != b"application/hwp+zip":
        raise ValueError("form_package_identity_invalid")
    for name, content in result["parts"].items():
        if name.endswith((".xml", ".hpf", ".rdf")):
            xml(content)
    return result


def authority(root=ROOT):
    record = shared.lifecycle.checked_json(root / CAPSULE, CAPSULE_SHA)
    for path, digest in record["source_sha256"].items():
        output.export.checked(root / path, digest)
    public.project(output.export.checked(root / public.LIB, public.CURRENT_LIB), root)
    for name in (*public.old3.RECEIPTS, *public.RECEIPTS):
        public.historical_sources(name, root)
    output.export.checked(root / HARNESS, HARNESS_SHA)
    return CAPSULE_SHA


def expected_map(count):
    return {"sections": [{"part": f"Contents/section{i}.xml", "map": {
        "paragraph_ids": [f"section-{i}-paragraph-{j}" for j in range(2)],
        "component_controls": [{"logical_control_id": f"section-{i}-control", "native_object_id": 90001 + i}],
    }} for i in range(count)]}


def replacements(index, parts):
    section = "Contents/section0.xml"
    if index == 0:
        return {section: {"edit": {"enabled": "0"}}}
    if index == 1:
        return {section: {"edit": {"foreColor": "#CC1100", "backColor": "#EEF0FA", "editable": "0"}}}
    if index == 2:
        return {section: {"edit": {"name": "P09 새 & <\"'> 폼", "groupName": "P09 그룹 & <\"'>"}}}
    if index == 3:
        refs = [int(n.get("id")) for n in xml(parts["Contents/header.xml"]).iter(HH + "charPr")]
        old = int(next(xml(parts[section]).iter(HP + "formCharPr")).get("charPrIDRef"))
        alternative = sorted(n for n in refs if n != old)[0]
        return {section: {"formCharPr": {"charPrIDRef": str(alternative), "followContext": "1", "autoSz": "1", "wordWrap": "0"}}}
    if index == 4:
        return {f"Contents/section{i}.xml": {"edit": {"tabOrder": str(i)}} for i in range(2)}
    if index == 5:
        return {"Contents/section1.xml": {"radioBtn": {"tabOrder": "0"}}}
    raise ValueError("form_case_unknown")


def escaped(value):
    for old, new in (("&", "&amp;"), ("<", "&lt;"), (">", "&gt;"), ('"', "&quot;"), ("'", "&apos;")):
        value = value.replace(old, new)
    return value.encode("utf-8")


def edit_tag(raw, tag, attributes):
    # Closed lexical bridge for these pinned native-derived inputs, not a general XML rewriter.
    tags = list(re.finditer(rb"<hp:" + tag.encode() + rb"\b[^>]*>", raw))
    if len(tags) != 1:
        raise ValueError("form_independent_edit_ambiguous")
    match = tags[0]
    start = match.group()
    for name, value in attributes.items():
        pattern = rb"(?<![A-Za-z0-9_:])" + name.encode() + rb'="([^"]*)"'
        fields = list(re.finditer(pattern, start))
        if len(fields) == 1:
            field = fields[0]
            start = start[:field.start(1)] + escaped(value) + start[field.end(1):]
        elif not fields and name == "groupName":
            end = -2 if start.endswith(b"/>") else -1
            start = start[:end] + b' groupName="' + escaped(value) + b'"' + start[end:]
        else:
            raise ValueError("form_independent_attribute_ambiguous")
    return raw[:match.start()] + start + raw[match.end():]


def verify_case(index, row, source_raw, target_raw, original_raw, baseline):
    source, target = package(source_raw), package(target_raw)
    parts = output.derived_parts("actual-property" if index < 4 else "global-tab" if index == 4 else "radio-tab", baseline["parts"])
    if index < 4 and source_raw != original_raw:
        raise ValueError("form_original_source_substituted")
    order = baseline["order"] if index < 4 else ["mimetype", *sorted(n for n in parts if n != "mimetype")]
    compression = baseline["compression"] if index < 4 else [zipfile.ZIP_STORED, *([zipfile.ZIP_DEFLATED] * (len(parts) - 1))]
    if source != {"parts": parts, "order": order, "compression": compression}:
        raise ValueError("form_complete_source_derivation_mismatch")
    expected = dict(parts)
    edits = replacements(index, parts)
    for part, tags in edits.items():
        for tag, attrs in tags.items():
            expected[part] = edit_tag(expected[part], tag, attrs)
    if target != {"parts": expected, "order": order, "compression": compression}:
        raise ValueError("form_independent_complete_output_mismatch")
    count = 1 if index < 4 else 2
    exact(row["complete_map"], expected_map(count), "form_complete_map_mismatch")
    for key in ("policy_sha256", "target_state_sha256"):
        shared.lifecycle.digest(row[key])
    if type(row["target_controls_sha256"]) is not list or len(row["target_controls_sha256"]) != count:
        raise ValueError("form_target_control_fingerprints_invalid")
    for digest in row["target_controls_sha256"]:
        shared.lifecycle.digest(digest)
    source_sha, target_sha = sha(source_raw), sha(target_raw)
    exact(row["source_package_sha256"], source_sha, "form_source_digest_mismatch")
    exact(row["package_sha256"], target_sha, "form_target_digest_mismatch")
    exact(row["package_bytes"], len(target_raw), "form_target_bytes_mismatch")
    receipt = row["receipt"]
    flow = shared.lifecycle.digest(receipt["document_flow_sha256"])
    if index < 4 and flow != output.prior.independent_actual()["document_flow_sha256"]:
        raise ValueError("form_original_flow_fingerprint_mismatch")
    changes = sum(len(attrs) for tags in edits.values() for attrs in tags.values())
    expected_receipt = {
        "profile": output.PROFILE, "source_package_sha256": source_sha, "output_package_sha256": target_sha,
        "document_flow_sha256": flow, "target_state_sha256": row["target_state_sha256"],
        "changed_sections": len(edits), "changed_attributes": changes,
        "non_section_parts_expanded_byte_exact": True, "outside_declared_edits_byte_exact": True,
        "entry_order_and_compression_preserved": True, "zip_header_policy": "rewritten_not_byte_exact",
        "legacy_reference_state": "id_index_validation_failed", "verified_native_reference_overlay_issues": count * 2,
    }
    exact(receipt, expected_receipt, "form_output_receipt_mismatch")
    return {"case_id": row["case_id"], "source_kind": KINDS[index], "package_sha256": target_sha,
            "source_package_sha256": source_sha, "package_bytes": len(target_raw), "controls": count,
            "changed_attributes": changes, "changed_sections": len(edits),
            "all_expanded_parts_and_outside_edits_byte_exact": True, "order_and_compression_preserved": True,
            "native_identity_fabricated": False, "actual_hangul": False}


def inspect(manifest_path, manifest_sha, root=ROOT, *, check_authority=True):
    manifest_path = shared.within(manifest_path, root / "fixtures/target-build")
    value = shared.lifecycle.checked_json(manifest_path, manifest_sha)
    fixed = {"schema_version": "hwpx-agent.p09-native-form-target-fixtures/v1", "task": "P09-32",
             "target_profile": {k: v for k, v in shared.lifecycle.TARGET.items() if k != "executable_sha256"},
             "source_capture_sha256": output.prior.prior.CAPTURE_SHA, "public_api_profile": output.PROFILE,
             "actual_hangul": False, "render": "not_run", "green_rows": 0,
             "raw_document_text_present": False, "absolute_private_paths_present": False}
    exact({k: v for k, v in value.items() if k != "cases"}, fixed, "form_manifest_claims_invalid")
    rows = value["cases"]
    if type(rows) is not list or len(rows) != 6:
        raise ValueError("form_complete_case_inventory_invalid")
    names = {"fixture-manifest.json", *FILES, *(f"p09-32-c{i+1:02}-source.hwpx" for i in range(6))}
    if {p.name for p in manifest_path.parent.iterdir()} != names:
        raise ValueError("form_complete_file_inventory_invalid")
    if check_authority:
        authority(root)
    original_raw, baseline = output.original(root)
    results = []
    fields = {"case_id", "file", "source_file", "source_kind", "package_sha256", "package_bytes", "source_package_sha256",
              "complete_map", "policy_sha256", "target_state_sha256", "target_controls_sha256", "receipt",
              "deterministic_retry", "stale_source_rejected"}
    for i, row in enumerate(rows):
        exact(sorted(row), sorted(fields), "form_case_shape_invalid")
        for key, expected in (("case_id", f"P09-32-C{i+1:02}"), ("file", FILES[i]),
                              ("source_file", f"p09-32-c{i+1:02}-source.hwpx"), ("source_kind", KINDS[i]),
                              ("deterministic_retry", True), ("stale_source_rejected", True)):
            exact(row[key], expected, "form_case_identity_invalid")
        source_raw = output.export.bounded_bytes(manifest_path.parent / row["source_file"], 4 * 1024 * 1024)
        target_raw = output.export.bounded_bytes(manifest_path.parent / row["file"], 4 * 1024 * 1024)
        results.append(verify_case(i, row, source_raw, target_raw, original_raw, baseline))
    # Source/native body values never enter the public result.
    return {"schema_version": "hwpx-agent.p09-native-form-complete-preparation/v1", "task": "P09-32",
            "state": "six_complete_cases_prepared_non_green", "manifest_sha256": manifest_sha,
            "public_api_source_capsule_sha256": CAPSULE_SHA, "cases": results,
            "claims": {"complete_independent_expanded_package_checks": True, "real_public_api_generator": True,
                       "independent_python_full_domain_serializer_qualified": False,
                       "zip_headers_raw_byte_exact": False, "actual_hangul": False, "render": "not_run",
                       "production_routing_qualified": False, "green_rows": 0, "p09_complete": False},
            "privacy": {"raw_document_text_present": False, "absolute_private_paths_present": False,
                        "trust_or_registry_changed": False, "native_session_started": False}}


def tree_value(node):
    if not isinstance(node.tag, str):
        raise ValueError("form_unknown_xml_node_rejected")
    return [node.tag, sorted(node.attrib.items()), node.text or "", node.tail or "", [tree_value(n) for n in node]]


def fingerprint(value):
    return sha(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode())


def projection(raw):
    result = package(raw)
    parts = result["parts"]
    header = xml(parts["Contents/header.xml"])
    char_nodes = list(header.iter(HH + "charPr"))
    chars = {n.get("id"): n for n in char_nodes}
    if None in chars or len(chars) != len(char_nodes):
        raise ValueError("form_native_character_catalog_invalid")
    content = xml(parts["Contents/content.hpf"])
    item_nodes = list(content.iter(OPF + "item"))
    items = {n.get("id"): n.get("href") for n in item_nodes}
    if None in items or len(items) != len(item_nodes):
        raise ValueError("form_native_manifest_inventory_invalid")
    sections = []
    for item in content.iter(OPF + "itemref"):
        href = items.get(item.get("idref"))
        if href in parts:
            part = href
        elif isinstance(href, str) and "Contents/" + href in parts:
            part = "Contents/" + href
        else:
            raise ValueError("form_native_spine_reference_missing")
        if part.startswith("Contents/section") and part.endswith(".xml"):
            sections.append(part)
    if not sections or len(sections) != len(set(sections)):
        raise ValueError("form_native_spine_inventory_invalid")
    all_sections = {n for n in parts if re.fullmatch(r"Contents/section[0-9]+\.xml", n)}
    if set(sections) != all_sections or header.get("secCnt") != str(len(sections)):
        raise ValueError("form_native_complete_section_inventory_invalid")
    controls = []
    kinds = {HP + n for n in ("edit", "checkBtn", "radioBtn", "comboBox", "listBox")}
    for part in sections:
        section = xml(parts[part])
        parents = {c: p for p in section.iter() for c in p}
        paragraphs = list(section.iter(HP + "p"))
        for node in section.iter():
            if node.tag not in kinds:
                continue
            run = parents.get(node)
            paragraph = parents.get(run)
            if run is None or paragraph is None or run.tag != HP + "run" or paragraph.tag != HP + "p":
                raise ValueError("form_native_physical_anchor_invalid")
            character = [n for n in node if n.tag == HP + "formCharPr"]
            if len(character) != 1 or character[0].get("charPrIDRef") not in chars:
                raise ValueError("form_native_character_reference_missing")
            controls.append({"part": part, "paragraph": paragraphs.index(paragraph),
                             "run": list(paragraph).index(run), "inline": list(run).index(node),
                             "kind": node.tag, "control_sha256": fingerprint(tree_value(node)),
                             "character_definition_sha256": fingerprint(tree_value(chars[character[0].get("charPrIDRef")]))})
    return result, {"sections": sections, "controls": controls}


def compare_native(input_raw, actual_raw):
    before, expected = projection(input_raw)
    after, observed = projection(actual_raw)
    paths = sorted(set(before["parts"]) | set(after["parts"]))
    changed = [n for n in paths if before["parts"].get(n) != after["parts"].get(n)]
    equal = expected == observed
    return {"package_sha256": sha(actual_raw), "package_bytes": len(actual_raw),
            "controls": len(observed["controls"]), "whole_form_subtrees_anchors_and_referenced_characters_exact": equal,
            "strict_form_semantics": "pass" if equal else "fail", "all_expanded_parts_byte_exact": not changed,
            "raw_preservation": "pass" if not changed else "fail", "changed_part_count": len(changed),
            "changed_part_names": changed, "entry_order_preserved": before["order"] == after["order"],
            "entry_compression_preserved": before["compression"] == after["compression"],
            "native_normalization_qualified": False, "green_rows": 0}


def attempt_paths(prefix, root=ROOT):
    if not isinstance(prefix, str) or re.fullmatch(r"[a-z0-9-]{1,40}", prefix) is None:
        raise ValueError("form_native_batch_prefix_invalid")
    return [root / "implementation/p09/evidence/private" / f"p09-17-field-auto-number-target-{prefix}-c{i+1:02}-attempt01" for i in range(6)]


def native_batch(manifest_path, manifest_sha, prefix, root=ROOT):
    prep = inspect(manifest_path, manifest_sha, root)
    manifest = shared.lifecycle.checked_json(manifest_path, manifest_sha)
    results = []
    pids = []
    for row, directory in zip(manifest["cases"], attempt_paths(prefix, root), strict=True):
        shared.within(directory, root / "implementation/p09/evidence/private")
        trace_raw = output.export.bounded_bytes(directory / "target-trace.json", 128 * 1024)
        trace = json.loads(trace_raw, object_pairs_hook=shared.lifecycle.duplicate_guard)
        record = {"case_id": row["case_id"], "trace_sha256": sha(trace_raw), "lifecycle": "fail",
                  "permission_click_attestation": "not_attested", "saved": {"state": "not_run"},
                  "reopened": {"state": "not_run"}, "green_rows": 0}
        if trace.get("state") == "pass":
            shared.lifecycle.verify_trace(trace, {"input_package_sha256": row["package_sha256"], "input_package_bytes": row["package_bytes"]})
            record["lifecycle"] = "pass"
            pids.extend(n["process"]["process_id"] for n in trace["sessions"])
            input_raw = output.export.checked(manifest_path.parent / row["file"], row["package_sha256"], 4 * 1024 * 1024)
            for stage, digest_key, bytes_key in (("saved", "output_sha256", "output_bytes"), ("reopened", "reopened_sha256", "reopened_bytes")):
                actual = output.export.checked(directory / f"{stage}.hwpx", trace[digest_key], 4 * 1024 * 1024)
                exact(len(actual), trace[bytes_key], "form_native_output_bytes_mismatch")
                try:
                    record[stage] = compare_native(input_raw, actual)
                except (ValueError, KeyError, ET.ParseError, zipfile.BadZipFile) as error:
                    code = str(error) if type(error) is ValueError and re.fullmatch(r"[a-z_]+", str(error)) else "form_native_projection_failed"
                    record[stage] = {"state": "fail", "error_code": code, "package_sha256": sha(actual)}
        else:
            # Preserve unsuccessful native attempts without manufacturing qualified lifecycle acceptance.
            record["failed_trace_qualification"] = "unqualified_failure_retained"
        results.append(record)
    if len(set(pids)) != len(pids):
        raise ValueError("form_native_batch_sessions_not_independent")
    return {"schema_version": "hwpx-agent.p09-native-form-complete-batch/v1", "task": "P09-32",
            "state": "actual_native_observations_non_green", "preparation_sha256": sha(shared.lifecycle.canonical_bytes(prep)),
            "manifest_sha256": manifest_sha, "cases": results, "independent_pass_session_count": len(pids),
            "claims": {"actual_hangul": True, "native_normalization_qualified": False,
                       "pdf_export_is_not_render_acceptance": True, "render": "not_run", "product_differential": "not_run",
                       "production_routing_qualified": False, "green_rows": 0, "p09_complete": False},
            "privacy": {"raw_document_text_present": False, "absolute_private_paths_present": False,
                        "trust_or_registry_changed": False, "computer_use_click_or_type_invoked": False}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--native-prefix")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        before = {p: sha(output.export.bounded_bytes(ROOT / p, 2 * 1024 * 1024)) for p in SOURCES}
        manifest = args.manifest.absolute()
        value = native_batch(manifest, args.manifest_sha256, args.native_prefix) if args.native_prefix else inspect(manifest, args.manifest_sha256)
        if before != {p: sha(output.export.bounded_bytes(ROOT / p, 2 * 1024 * 1024)) for p in SOURCES}:
            raise ValueError("form_preparation_sources_changed")
        value["source_sha256"] = before
        raw = shared.lifecycle.canonical_bytes(value)
        if args.output:
            path = args.output.absolute()
            shared.within(path.parent, ROOT / "implementation/p09/evidence")
            if path.is_symlink() or path.is_junction() or "private" in path.relative_to(ROOT).parts:
                raise ValueError("form_public_output_boundary_invalid")
            with path.open("xb") as stream:
                stream.write(raw)
    except (OSError, ValueError, KeyError, TypeError, IndexError, UnicodeError, ET.ParseError, zipfile.BadZipFile) as error:
        code = str(error) if type(error) is ValueError and re.fullmatch(r"[a-z_]+", str(error)) else "form_complete_inspection_failed"
        print(json.dumps({"state": "fail", "error_code": code})); return 2
    print(json.dumps({"state": "pass", "observation_state": value["state"], "cases": 6,
                      "receipt_sha256": sha(raw), "green_rows": 0, "p09_complete": False})); return 0


if __name__ == "__main__":
    raise SystemExit(main())
