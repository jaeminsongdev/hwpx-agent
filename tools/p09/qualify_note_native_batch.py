#!/usr/bin/env python3
"""Read-only qualification of the three original note-native batch attempts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import zipfile
from xml.etree import ElementTree as ET

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.p09 import inspect_note_complete_fixture as prepared
from tools.p09 import qualify_click_here_update_target as click
from PIL import Image, ImageChops

shared = prepared.shared
ROOT = shared.ROOT
MANIFEST = "fixtures/target-build/p09-24-note-target-20261002-03/output/fixture-manifest.json"
MANIFEST_SHA = "ef2e30388827c40e02b99017350f434b33840ce5564c2d46b2bae9c10dac9150"
PREPARATION = "implementation/p09/evidence/p09-24-note-complete-fixture-qualification.current-2020.v1.json"
PREPARATION_SHA = "3aaa98e189fa155129bc348e31367f9a06f2b81b7bd7386c3cecc36076a85ce2"
HARNESS = "implementation/p09/tools/run-hancom-2020-field-auto-number-target.ps1"
HARNESS_SHA = "30341f7a7ff5106e4c3ac74331abdd9b612ec4d88eb060387b506809399338a9"
ATTEMPTS = {
    "P09-24-C01": ("p09-17-field-auto-number-target-p09-24-20261002-c01-attempt01", "1170c77a093728b784cfa47fb6d1cc8dc483017cbaed86189e06bce5cfb576d9"),
    "P09-24-C02": ("p09-17-field-auto-number-target-p09-24-20261002-c02-attempt01", "b2b95139955b0454eff102be10eae8db4a15f062285078db87b7851a18b3977c"),
    "P09-24-C03": ("p09-17-field-auto-number-target-p09-24-20261002-c03-attempt01", "ebb916efc52d52fb0c4ef85e5280cccc40c2630ca8f6caed4654dfb0e9a9629e"),
}
SOURCES = ("tools/p09/qualify_note_native_batch.py", "tools/p09/tests/test_note_native_batch.py",
           "implementation/p09/P09-26_NATIVE_BATCH_POLICY.md", HARNESS, *prepared.SOURCES,
           "tools/p08/object_target_oracle.py")
HP = prepared.HP
LINE_ATTRS = {"baseline", "flags", "horzpos", "horzsize", "spacing", "textheight", "textpos", "vertpos", "vertsize"}


def semantic_node(node):
    return [str(node.tag), sorted(node.attrib.items()), node.text or "", [semantic_node(c) for c in node]]


def native_projection(section: bytes, header):
    tree = prepared.xml(section)
    parents = {child: parent for parent in tree.iter() for child in parent}
    notes = [n for n in tree.iter() if n.tag in (HP + "footNote", HP + "endNote")]
    if not 1 <= len(notes) <= 2:
        raise ValueError("native_note_inventory_invalid")
    for note in notes:
        if set(note.attrib) != {"number", "suffixChar", "instId"} or note.get("number") != "1" or note.get("suffixChar") != "41":
            raise ValueError("native_note_marker_observation_invalid")
    layouts = list(tree.iter(HP + "linesegarray"))
    if len(layouts) != 1 + 2 * len(notes):
        raise ValueError("native_note_layout_inventory_invalid")
    for layout in layouts:
        if (parents[layout].tag != HP + "p" or layout.attrib or not 1 <= len(layout) <= 64
                or (layout.text or "").strip() or (layout.tail or "").strip()):
            raise ValueError("native_note_layout_shape_invalid")
        for line in layout:
            if (line.tag != HP + "lineseg" or set(line.attrib) != LINE_ATTRS or list(line)
                    or (line.text or "").strip() or (line.tail or "").strip()
                    or any(not re.fullmatch(r"0|-?[1-9][0-9]{0,10}", v) for v in line.attrib.values())):
                raise ValueError("native_note_layout_shape_invalid")
    # Retain the frozen oracle's genuine rejection; do not change it or claim byte equality.
    try:
        prepared.note_projection(section, header)
    except ValueError as error:
        if str(error) != "note_marker_shape_invalid":
            raise ValueError("native_note_unexpected_preparation_failure") from error
    else:
        raise ValueError("native_note_preparation_false_pass")
    layout_raw = re.findall(br'<hp:linesegarray>.*?</hp:linesegarray>', section, re.S)
    if len(layout_raw) != len(layouts):
        raise ValueError("native_note_layout_lexical_inventory_invalid")
    semantic = section
    for raw in layout_raw:
        semantic = semantic.replace(raw, b"", 1)
    if semantic.count(b' suffixChar="41"') != len(notes):
        raise ValueError("native_note_marker_lexical_inventory_invalid")
    semantic = re.sub(br'(<hp:(?:footNote|endNote)\b[^>]*) suffixChar="41"', br'\1', semantic)
    projected, _, restored = prepared.note_projection(semantic, header)
    layout_sha = shared.oracle.sha256(shared.lifecycle.canonical_bytes([semantic_node(n) for n in layouts]))
    return projected, {"native_added_suffix_wchar": 41, "native_layout_count": len(layouts),
                       "native_layout_sha256": layout_sha, "preparation_oracle_state": "fail",
                       "preparation_oracle_error": "note_marker_shape_invalid",
                       "semantic_comparison_excludes_only_declared_suffix_and_layout": True,
                       "body_auto_number_field_count": sum(1 for n in notes for c in n.iter(HP + "autoNum"))}, restored


def style_definitions(header):
    result = {}
    for name, ids in (("charPr", {"0", "3"}), ("paraPr", {"10"}), ("style", {"14", "15"})):
        nodes = [n for n in header.iter(prepared.HH + name) if n.get("id") in ids]
        if len(nodes) != len(ids) or {n.get("id") for n in nodes} != ids:
            raise ValueError("native_note_style_inventory_invalid")
        for node in nodes:
            result[name + ":" + node.get("id")] = shared.oracle.sha256(shared.lifecycle.canonical_bytes(semantic_node(node)))
    return result


def pdf_stability(left: Path, right: Path, expected_pages: int):
    info, ppm = (shutil.which(n) for n in ("pdfinfo", "pdftoppm"))
    if not info or not ppm:
        raise ValueError("native_note_pdf_tools_unavailable")
    if expected_pages not in (1, 2) or any(click.pdf_oracle.pdf_page_count(Path(info), p) != expected_pages for p in (left, right)):
        raise ValueError("native_note_pdf_page_profile_invalid")
    pages = []
    with tempfile.TemporaryDirectory(prefix="p09-note-native-oracle-") as directory:
        a = click.pdf_oracle.render_pdf(Path(ppm), left, Path(directory), "left")
        b = click.pdf_oracle.render_pdf(Path(ppm), right, Path(directory), "right")
        if len(a) != expected_pages or len(b) != expected_pages:
            raise ValueError("native_note_pdf_render_count_invalid")
        for la, rb in zip(a, b, strict=True):
            with Image.open(la) as li, Image.open(rb) as ri:
                l, r = li.convert("RGB"), ri.convert("RGB")
                if l.size != (794, 1122) or r.size != l.size:
                    raise ValueError("native_note_pdf_dimensions_invalid")
                delta = ImageChops.difference(l, r)
                white = Image.new("RGB", l.size, "white")
                bounds = [ImageChops.difference(v, white).getbbox() for v in (l, r)]
                if any(b is None for b in bounds):
                    raise ValueError("native_note_pdf_empty_page_rejected")
                pages.append({"width": l.width, "height": l.height,
                              "changed_pixels": sum(1 for p in delta.get_flattened_data() if any(p)),
                              "absolute_rgb_delta_sum": sum(sum(p) for p in delta.get_flattened_data()),
                              "difference_bbox": delta.getbbox(), "nonwhite_bboxes": bounds})
    return {"state": "equal" if all(p["changed_pixels"] == 0 for p in pages) else "mismatch",
            "dpi": 96, "page_count": expected_pages, "pages": pages, "masks_or_tolerances_used": False,
            "renderer_sha256": shared.oracle.sha256(shared.oracle.bounded_bytes(Path(ppm), 64 * 1024 * 1024)),
            "pdfinfo_sha256": shared.oracle.sha256(shared.oracle.bounded_bytes(Path(info), 64 * 1024 * 1024))}


def qualify(root: Path = ROOT):
    prior = shared.lifecycle.checked_json(root / PREPARATION, PREPARATION_SHA)
    for path, digest in prior["source_sha256"].items():
        if shared.oracle.sha256(shared.oracle.bounded_bytes(root / path, 2 * 1024 * 1024)) != digest:
            raise ValueError("native_note_preparation_source_drift")
    if shared.oracle.sha256(shared.oracle.bounded_bytes(root / HARNESS, 64 * 1024)) != HARNESS_SHA:
        raise ValueError("native_note_harness_drift")
    manifest_path = root / MANIFEST
    prepared.inspect(manifest_path, MANIFEST_SHA, root=root)
    manifest = shared.lifecycle.checked_json(manifest_path, MANIFEST_SHA)
    results = []
    for row in manifest["cases"]:
        case = row["case_id"]
        slot, trace_sha = ATTEMPTS[case]
        attempt = shared.within(root / "implementation/p09/evidence/private" / slot, root / "implementation/p09/evidence/private")
        trace = shared.lifecycle.checked_json(attempt / "target-trace.json", trace_sha)
        shared.lifecycle.verify_trace(trace, {"input_package_sha256": row["package_sha256"], "input_package_bytes": row["package_bytes"]})
        if type(trace.get("input_bytes")) is not int:
            raise ValueError("native_note_input_size_invalid")
        _, source_section, source_parts, source_header = prepared.package(manifest_path.parent / row["file"], row["package_sha256"])
        source, _, _ = prepared.note_projection(source_section, source_header)
        definitions = style_definitions(source_header)
        stages = {}
        errors = []
        semantic_preserved = True
        actual_sections = []
        for stage, prefix in (("saved", "output"), ("reopened", "reopened")):
            raw, section, parts, header = prepared.package(attempt / (stage + ".hwpx"), trace[prefix + "_sha256"])
            prepared.exact(trace[prefix + "_bytes"], len(raw), "native_note_artifact_size_invalid")
            observed, additions, _ = native_projection(section, header)
            if len(observed) != len(source):
                raise ValueError("native_note_source_inventory_mismatch")
            differences = [{k: {"input": a[k], "native": b[k]} for k in a if a[k] != b[k]}
                           for a, b in zip(source, observed, strict=True)]
            if any(differences):
                errors.append(stage + "_raw_body_or_style_binding_changed")
            # Preserve the raw-hash failure; separately describe the exact typed fields.
            typed_equal = all(not (set(d) - {"body_graph_sha256", "body_style_sha256"}) for d in differences)
            semantic_preserved = semantic_preserved and typed_equal
            if style_definitions(header) != definitions:
                errors.append(stage + "_referenced_style_definition_changed")
                semantic_preserved = False
            if any(parts.get(k) != v for k, v in source_parts.items() if k.lower().startswith("bindata/")):
                errors.append(stage + "_binary_resource_changed")
            main = prepared.xml(section)
            main_text = "".join("".join(n.itertext()) for p in main if p.tag == HP + "p" for r in p if r.tag == HP + "run" for n in r if n.tag == HP + "t")
            input_main = prepared.xml(source_section)
            expected_main = "".join("".join(n.itertext()) for p in input_main if p.tag == HP + "p" for r in p if r.tag == HP + "run" for n in r if n.tag == HP + "t")
            if main_text != expected_main:
                errors.append(stage + "_main_text_changed")
                semantic_preserved = False
            actual_sections.append(section)
            stages[stage] = {"package_sha256": shared.oracle.sha256(raw), "package_bytes": len(raw),
                             "section_sha256": shared.oracle.sha256(section), "input_section_byte_exact": section == source_section,
                             "semantic_projection": observed, "native_additions": additions,
                             "input_native_projection_differences": differences,
                             "typed_text_style_marker_anchor_equal": typed_equal,
                             "main_text_sha256": shared.oracle.sha256(main_text.encode()),
                             "referenced_style_definitions_sha256": style_definitions(header),
                             "application_changed_non_section_parts": sorted(k for k in set(parts) | set(source_parts) if parts.get(k) != source_parts.get(k))}
        if actual_sections[0] != actual_sections[1]:
            errors.append("saved_reopened_section_changed")
        pdfs = {}
        for filename, prefix in (("saved.pdf", "pdf"), ("reopened.pdf", "reopened_pdf")):
            raw = shared.oracle.bounded_bytes(attempt / filename, 32 * 1024 * 1024)
            if not raw.startswith(b"%PDF-") or shared.oracle.sha256(raw) != shared.lifecycle.digest(trace[prefix + "_sha256"]):
                raise ValueError("native_note_pdf_identity_invalid")
            prepared.exact(trace[prefix + "_bytes"], len(raw), "native_note_pdf_size_invalid")
            pdfs[filename] = {"sha256": shared.oracle.sha256(raw), "bytes": len(raw)}
        stability = pdf_stability(attempt / "saved.pdf", attempt / "reopened.pdf", 2 if case == "P09-24-C03" else 1)
        if stability["state"] != "equal":
            errors.append("saved_reopened_pdf_changed")
        results.append({"case_id": case, "state": "bounded_note_body_semantic_non_green" if not errors else "failed_semantic_non_green",
                        "errors": errors, "trace_sha256": trace_sha, "input_package_sha256": row["package_sha256"],
                        "snapshots": stages, "pdf_identity": pdfs, "saved_reopened_pdf_stability": stability,
                        "lifecycle": {k: trace[k] for k in shared.lifecycle.LIFECYCLE_KEYS},
                        "register_module_returns": [s["register_module_return"] for s in trace["sessions"]],
                        "remaining_hwp_process_count_at_run": trace["remaining_hwp_process_count"],
                        "bounded_text_style_anchor_readback": semantic_preserved,
                        "user_access_state": "not_attested", "body_numbering_render_qualified": False})
    return {"schema_version": "hwpx-agent.p09-note-native-batch-qualification/v1", "task": "P09-26",
            "state": "bounded_note_body_semantic_non_green" if all(not r["errors"] for r in results) else "failed_semantic_non_green",
            "target": shared.lifecycle.TARGET, "fixture_manifest_sha256": MANIFEST_SHA,
            "preparation_receipt_sha256": PREPARATION_SHA, "cases": results,
            "source_sha256": {p: shared.oracle.sha256(shared.oracle.bounded_bytes(root / p, 2 * 1024 * 1024)) for p in dict.fromkeys(SOURCES)},
            "claims": {"actual_three_case_save_fresh_reopen": True, "bounded_note_body_preservation": all(not r["errors"] for r in results),
                       "bounded_note_text_style_anchor_readback": all(r["bounded_text_style_anchor_readback"] for r in results),
                       "native_body_numbering_qualified": False, "full_render_acceptance": "not_run",
                       "product_routing_qualified": False, "automation_fallback": "not_run", "product_differential": "not_run",
                       "predecessor_receipts_rewritten": False, "green_rows": 0, "p09_complete": False, "product_complete": False},
            "privacy": {"raw_document_text_present": False, "absolute_private_paths": False,
                        "qualification_started_native_session": False, "computer_use_click_or_type_invoked": False,
                        "registry_or_trust_setting_changed": False, "external_network_invoked": False}}


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
                raise ValueError("native_note_public_output_invalid")
            with output.open("xb") as handle:
                handle.write(raw)
        if args.verify and shared.oracle.bounded_bytes(args.verify, 256 * 1024) != raw:
            raise ValueError("native_note_record_mismatch")
    except (OSError, ValueError, KeyError, TypeError, AttributeError, ET.ParseError, zipfile.BadZipFile) as error:
        code = str(error) if type(error) is ValueError and re.fullmatch(r"[a-z_]+", str(error)) else "native_note_qualification_failed"
        print(json.dumps({"state": "fail", "error_code": code}))
        return 2
    print(json.dumps({"state": "pass", "qualification_state": value["state"], "qualification_sha256": shared.oracle.sha256(raw),
                      "cases": len(value["cases"]), "green_rows": 0, "p09_complete": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
