#!/usr/bin/env python3
"""Independent bounded complete-package note oracle; no Hangul, COM, UI or network."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import struct
import sys
import unicodedata
import zipfile
from xml.etree import ElementTree as ET

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.p09 import qualify_field_object_caption_target as shared
from tools.p09 import validate_note_hwpx_contract as predecessor

ROOT = shared.ROOT
HP = shared.oracle.NS
HH = "{http://www.hancom.co.kr/hwpml/2011/head}"
SECTION = "Contents/section0.xml"
SEED_SHA = "494f62f4b5e996bd241c09b16e17a8323cb17fe0974fcdf36af230dad73763d5"
PREDECESSOR = "implementation/p09/evidence/p09-15-note-hwpx-source-qualification.v1.json"
PREDECESSOR_SHA = "b21ad030fece13baf723561f1bfc54f82abe59f5a36728e6116392772132508b"
CASES = {
    "P09-24-C01": ("p09-24-c01-footnote.hwpx", [("footNote", 24001, 0)]),
    "P09-24-C02": ("p09-24-c02-endnote.hwpx", [("endNote", 24002, 1)]),
    "P09-24-C03": ("p09-24-c03-footnote-endnote.hwpx", [("footNote", 24001, 0), ("endNote", 24002, 1)]),
}
SOURCES = (
    "tools/p09/inspect_note_complete_fixture.py",
    "tools/p09/tests/test_note_complete_fixture.py",
    "implementation/p09/P09-24_NOTE_COMPLETE_PACKAGE_POLICY.md",
    "crates/hwpx-package/examples/p09_24_note_target_fixture.rs",
    "crates/hwpx-package/examples/p08_19_support/common.rs",
    "crates/hwpx-package/src/vs0.rs",
    "crates/hwpx-package/src/hancom_2020_minimal_header.xml",
    "tools/p09/validate_note_hwpx_contract.py",
    "tools/p09/qualify_field_object_caption_target.py",
    "tools/p09/qualify_field_auto_number_target.py",
    "tools/p09/inspect_field_auto_number_target.py",
    *predecessor.IMPLEMENTATION_SHA256,
)


def exact(value, expected, code):
    if not shared.oracle.exact(value, expected):
        raise ValueError(code)


def xml(data: bytes):
    if not data or b"<!doctype" in data.lower() or b"<!entity" in data.lower():
        raise ValueError("note_active_xml_rejected")
    return ET.fromstring(data, parser=ET.XMLParser(target=ET.TreeBuilder(insert_comments=True, insert_pis=True)))


def package(path: Path, expected: str):
    raw = shared.oracle.bounded_bytes(path, 4 * 1024 * 1024)
    if shared.oracle.sha256(raw) != shared.lifecycle.digest(expected):
        raise ValueError("note_package_digest_mismatch")
    parts = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        entries = archive.infolist()
        if not 0 < len(entries) <= 64 or sum(e.file_size for e in entries) > 8 * 1024 * 1024:
            raise ValueError("note_archive_bounds_invalid")
        aliases = set()
        for entry in entries:
            name = entry.filename
            alias = unicodedata.normalize("NFC", name).casefold()
            if (entry.is_dir() or entry.flag_bits & 1 or not 0 <= entry.file_size <= 2 * 1024 * 1024
                    or "\\" in name or ":" in name or name.startswith("/")
                    or any(p in ("", ".", "..") or p.endswith((" ", ".")) for p in name.split("/"))
                    or alias in aliases):
                raise ValueError("note_archive_entry_invalid")
            aliases.add(alias)
            parts[name] = archive.read(entry)
    if parts.get("mimetype") != b"application/hwp+zip" or SECTION not in parts:
        raise ValueError("note_package_identity_invalid")
    content = xml(parts["Contents/content.hpf"])
    opf = "{http://www.idpf.org/2007/opf/}"
    items = list(content.iter(opf + "item"))
    manifest = {n.get("id"): n.get("href") for n in items}
    if len(manifest) != len(items) or not items or any(href not in parts for href in manifest.values()):
        raise ValueError("note_package_manifest_graph_invalid")
    if any(n.get("idref") not in manifest for n in content.iter(opf + "itemref")):
        raise ValueError("note_package_spine_graph_invalid")
    section = parts[SECTION]
    xml(section)
    return raw, section, {k: shared.oracle.sha256(v) for k, v in parts.items() if k != SECTION}, xml(parts["Contents/header.xml"])


def note_projection(section: bytes, header):
    tree = xml(section)
    if tree.tag != "{http://www.hancom.co.kr/hwpml/2011/section}sec":
        raise ValueError("note_section_root_invalid")
    parents = {child: parent for parent in tree.iter() for child in parent}
    catalog = {name: {n.get("id") for n in header.iter(HH + name)} for name in ("charPr", "paraPr", "style")}
    notes = [n for n in tree.iter() if n.tag in (HP + "footNote", HP + "endNote")]
    raw_wrappers = list(re.finditer(br'<hp:ctrl><hp:(footNote|endNote)\b[^>]*>.*?</hp:\1></hp:ctrl>', section, re.S))
    if len(notes) != len(raw_wrappers):
        raise ValueError("note_wrapper_lexical_inventory_invalid")
    projected = []
    for node, wrapper in zip(notes, raw_wrappers, strict=True):
        kind = node.tag[len(HP):]
        attrs = node.attrib
        # The unchanged production writer omits zero flag and absent optional WCHARs.
        exact(sorted(attrs), ["instId", "number"], "note_marker_shape_invalid")
        if attrs != {"number": "1", "instId": attrs["instId"]}:
            raise ValueError("note_marker_profile_invalid")
        if not re.fullmatch(r"[1-9][0-9]*", attrs["instId"]) or int(attrs["instId"]) > 2**32 - 1:
            raise ValueError("note_instance_invalid")
        ctrl = parents[node]
        run = parents[ctrl]
        paragraph = parents[run]
        if (ctrl.tag != HP + "ctrl" or ctrl.attrib or len(ctrl) != 1 or run.tag != HP + "run"
                or paragraph.tag != HP + "p" or parents[paragraph] is not tree or len(node) != 1):
            raise ValueError("note_anchor_invalid")
        if (ctrl.text or "").strip() or (node.text or "").strip():
            raise ValueError("note_container_text_rejected")
        body = node[0]
        exact(body.tag, HP + "subList", "note_body_root_invalid")
        exact(body.attrib, {"id": "", "textDirection": "HORIZONTAL", "lineWrap": "BREAK", "vertAlign": "TOP",
                            "linkListIDRef": "0", "linkListNextIDRef": "0", "textWidth": "0", "textHeight": "0",
                            "hasTextRef": "0", "hasNumRef": "0"}, "note_body_attributes_invalid")
        paragraphs = list(body)
        if len(paragraphs) != 2:
            raise ValueError("note_body_paragraph_inventory_invalid")
        decoded = []
        style_refs = []
        for ordinal, p in enumerate(paragraphs):
            style_id = "14" if kind == "footNote" else "15"
            exact(p.tag, HP + "p", "note_body_paragraph_invalid")
            exact(p.attrib, {"id": str(101 + ordinal), "paraPrIDRef": "10", "styleIDRef": style_id,
                             "pageBreak": "0", "columnBreak": "0", "merged": "0"}, "note_body_paragraph_invalid")
            if p.get("paraPrIDRef") not in catalog["paraPr"] or p.get("styleIDRef") not in catalog["style"]:
                raise ValueError("note_body_style_reference_missing")
            runs = list(p)
            if len(runs) != (2 if ordinal == 0 else 1):
                raise ValueError("note_body_run_inventory_invalid")
            for run_ordinal, body_run in enumerate(runs):
                char = "0" if ordinal == 0 and run_ordinal == 1 else "3"
                if body_run.tag != HP + "run" or body_run.attrib != {"charPrIDRef": char} or len(body_run) != 1:
                    raise ValueError("note_body_run_shape_invalid")
                text = body_run[0]
                if text.tag != HP + "t" or text.attrib or list(text):
                    raise ValueError("note_body_rich_text_rejected")
                if char not in catalog["charPr"]:
                    raise ValueError("note_body_style_reference_missing")
                decoded.append(text.text or "")
                style_refs.append({"charPrIDRef": char, "paraPrIDRef": "10", "styleIDRef": style_id})
        for container in body.iter():
            if container.tag != HP + "t" and (container.text or "").strip() or (container.tail or "").strip():
                raise ValueError("note_body_stray_text_rejected")
        expected_text = "P09 footnote & <body> 한글 🚀" if kind == "footNote" else "P09 endnote & <body> 한글"
        if decoded != [expected_text, " continuation", "second paragraph"]:
            raise ValueError("note_body_expected_text_mismatch")
        raw_body = re.search(br'<hp:subList\b.*?</hp:subList>', wrapper[0], re.S)
        if raw_body is None:
            raise ValueError("note_raw_body_missing")
        body_sha = shared.oracle.sha256(raw_body[0])
        styles = hashlib.sha256()
        for tag in re.findall(br'<hp:(?:subList|p|run|t)\b[^>]*>', raw_body[0]):
            styles.update(struct.pack("<Q", len(tag)))
            styles.update(tag)
        siblings = list(run)
        inline = sum(1 for sibling in siblings[:siblings.index(ctrl)]
                     if not (sibling.tag == HP + "ctrl" and len(sibling) == 1 and sibling[0].tag in (HP + "footNote", HP + "endNote")))
        run_index = [child for child in paragraph if child.tag == HP + "run"].index(run)
        projected.append({"kind": kind, "native_inst_id": int(attrs["instId"]), "run_ordinal": run_index,
                          "inline_ordinal": inline, "input_marker_number": 1, "body_graph_sha256": body_sha,
                          "plain_text_sha256": shared.oracle.sha256("".join(decoded).encode()),
                          "body_style_sha256": styles.hexdigest(), "style_references": style_refs,
                          "marker_style_sha256": shared.oracle.sha256(f'<hp:run charPrIDRef="{run.get("charPrIDRef")}">'.encode())})
    restored = section
    for wrapper in reversed(raw_wrappers):
        restored = restored[:wrapper.start()] + restored[wrapper.end():]
    return projected, raw_wrappers, restored


def inspect(manifest_path: Path, manifest_sha: str, *, root: Path = ROOT):
    shared.within(manifest_path, root / "fixtures/target-build")
    value = shared.lifecycle.checked_json(manifest_path, manifest_sha)
    for key, expected in {"schema_version": "hwpx-agent.p09-note-complete-target-fixture/v1", "task": "P09-24",
                          "seed_file": "p09-24-note-seed.hwpx", "seed_package_sha256": SEED_SHA,
                          "complete_package_graph": True, "actual_hangul": False, "save_reopen": "not_run",
                          "render": "not_run", "automation": "not_run", "differential": "not_run",
                          "marker_expectation": "input_preservation_model_hypothesis_target_unqualified",
                          "green_rows": 0, "p09_complete": False, "product_complete": False}.items():
        exact(value.get(key), expected, "note_manifest_contract_invalid")
    seed, seed_section, seed_parts, header = package(manifest_path.parent / value["seed_file"], SEED_SHA)
    exact(value.get("seed_package_bytes"), len(seed), "note_seed_size_invalid")
    exact(value.get("seed_section_sha256"), shared.oracle.sha256(seed_section), "note_seed_section_invalid")
    if note_projection(seed_section, header)[0]:
        raise ValueError("note_seed_not_empty")
    rows = value.get("cases")
    if not isinstance(rows, list) or [r.get("case_id") for r in rows] != list(CASES):
        raise ValueError("note_manifest_cases_invalid")
    results = []
    for row in rows:
        file, expected_notes = CASES[row["case_id"]]
        exact(row.get("file"), file, "note_case_filename_invalid")
        exact(row.get("note_count"), len(expected_notes), "note_case_count_invalid")
        exact(row.get("deterministic_retry"), True, "note_retry_claim_invalid")
        exact(row.get("feature_ids"), ["REF-021" if n[0] == "footNote" else "REF-022" for n in expected_notes], "note_case_feature_invalid")
        raw, section, parts, actual_header = package(manifest_path.parent / file, row["package_sha256"])
        exact(row.get("package_bytes"), len(raw), "note_case_size_invalid")
        exact(row.get("section_sha256"), shared.oracle.sha256(section), "note_case_section_invalid")
        projected, wrappers, restored = note_projection(section, actual_header)
        if restored != seed_section or parts != seed_parts or row.get("expanded_non_section_parts_sha256") != seed_parts:
            raise ValueError("note_nonselected_content_or_parts_changed")
        if [(n["kind"], n["native_inst_id"], n["inline_ordinal"]) for n in projected] != expected_notes:
            raise ValueError("note_native_inventory_or_anchor_invalid")
        operations = row.get("operations")
        if not isinstance(operations, list) or len(operations) != len(projected):
            raise ValueError("note_operation_inventory_invalid")
        for index, (operation, observed) in enumerate(zip(operations, projected, strict=True)):
            for key, observed_value in observed.items():
                if key != "style_references":
                    exact(operation.get(key), observed_value, "note_operation_binding_invalid")
            exact(operation.get("capability_id"), "ref.footnote_insert" if observed["kind"] == "footNote" else "ref.endnote_insert", "note_capability_invalid")
            for key in ("stale_source_rejected", "stale_payload_rejected"):
                exact(operation.get(key), True, "note_stale_claim_invalid")
            # Independently remove later wrappers to recover each actual intermediate section.
            intermediate = section
            for wrapper in reversed(wrappers[index + 1:]):
                intermediate = intermediate[:wrapper.start()] + intermediate[wrapper.end():]
            before = seed_section if index == 0 else previous
            exact(operation.get("source_section_sha256"), shared.oracle.sha256(before), "note_source_chain_invalid")
            exact(operation.get("output_section_sha256"), shared.oracle.sha256(intermediate), "note_output_chain_invalid")
            for key in ("source_state_sha256", "target_state_sha256", "plan_sha256"):
                shared.lifecycle.digest(operation.get(key))
            if index and operation["source_state_sha256"] != operations[index - 1]["target_state_sha256"]:
                raise ValueError("note_state_chain_invalid")
            previous = intermediate
        results.append({"case_id": row["case_id"], "package_sha256": row["package_sha256"],
                        "package_bytes": len(raw), "section_sha256": row["section_sha256"],
                        "native_projection": projected, "exact_section_reversal": True,
                        "all_other_expanded_parts_preserved": True, "actual_hangul": False})
    record = shared.lifecycle.checked_json(root / PREDECESSOR, PREDECESSOR_SHA)
    if record.get("task") != "P09-15":
        raise ValueError("note_predecessor_invalid")
    for path, sha in predecessor.IMPLEMENTATION_SHA256.items():
        if shared.oracle.sha256(shared.oracle.bounded_bytes(root / path, 2 * 1024 * 1024)) != sha:
            raise ValueError("note_frozen_implementation_drift")
    return {"schema_version": "hwpx-agent.p09-note-complete-fixture-qualification/v1", "task": "P09-24",
            "state": "complete_package_static_non_green", "manifest_sha256": manifest_sha,
            "predecessor_receipt_sha256": PREDECESSOR_SHA, "seed_package_sha256": SEED_SHA, "cases": results,
            "source_sha256": {p: shared.oracle.sha256(shared.oracle.bounded_bytes(root / p, 2 * 1024 * 1024)) for p in SOURCES},
            "claims": {"three_complete_package_fixtures": True, "independent_note_body_style_anchor_readback": True,
                       "actual_hangul": False, "save_reopen": "not_run", "render": "not_run", "automation": "not_run",
                       "differential": "not_run", "arbitrary_rich_notes": False, "note_style_convert_export_qualified": False,
                       "production_routing_qualified": False, "green_rows": 0, "p09_complete": False, "product_complete": False},
            "privacy": {"absolute_private_paths": False, "raw_document_text_present": False, "user_document_scanned": False,
                        "registry_or_system_setting_changed": False, "external_network_invoked": False,
                        "computer_use_click_or_type_invoked": False}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--expected-manifest-sha256", required=True)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--output", type=Path)
    group.add_argument("--verify", type=Path)
    args = parser.parse_args()
    try:
        result = inspect(args.manifest, args.expected_manifest_sha256)
        raw = shared.lifecycle.canonical_bytes(result)
        if args.output:
            output = args.output.absolute()
            shared.within(output.parent, ROOT / "implementation/p09/evidence")
            if output.is_symlink() or output.is_junction() or "private" in output.relative_to(ROOT).parts:
                raise ValueError("note_public_output_boundary_invalid")
            with output.open("xb") as handle:
                handle.write(raw)
        if args.verify and shared.oracle.bounded_bytes(args.verify, 256 * 1024) != raw:
            raise ValueError("note_qualification_record_mismatch")
    except (OSError, ValueError, KeyError, TypeError, AttributeError, UnicodeError, zipfile.BadZipFile, ET.ParseError) as error:
        code = str(error) if type(error) is ValueError and re.fullmatch(r"[a-z_]+", str(error)) else "note_qualification_failed"
        print(json.dumps({"state": "fail", "error_code": code}))
        return 2
    print(json.dumps({"state": "pass", "qualification_state": result["state"],
                      "qualification_sha256": shared.oracle.sha256(raw), "cases": len(result["cases"]),
                      "actual_hangul": False, "green_rows": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
