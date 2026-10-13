#!/usr/bin/env python3
"""Read-only, independently hash-bound CLICK_HERE cache evidence; never launches Hangul."""
from __future__ import annotations

import argparse
import io
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import zipfile
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.p09 import qualify_field_object_caption_target as shared
from tools.p08 import object_target_oracle as pdf_oracle
from PIL import Image, ImageChops

lifecycle = shared.lifecycle
oracle = shared.oracle
ROOT = shared.ROOT
HP = oracle.NS
HH = "{http://www.hancom.co.kr/hwpml/2011/head}"
DISCOVERY = "implementation/p09/evidence/private/p09-22-click-here-discovery-20261002-01"
DISCOVERY_SHA = "257f98e1629e547e515a5f4eaf136064b80f5a5960c9a9ef1fc0d475b905a900"
BRIDGE = "implementation/p09/evidence/p09-23-p08-additive-export-source-qualification.current-2020.v2.json"
BRIDGE_SHA = "70806cbec581e50a5a4a419ce73e8a1ab32c09c930f7aae915c7b0d47bac38f1"
CASES = {
    "P09-22-C01": ("empty.hwpx", "60a646f488941bad203d1c1d8bab43a36f2ae5c4712396eeeb3c1acb81d50747",
                   "p09-22-c01-empty-field-update.hwpx", "P09 value & <text> 한글"),
    "P09-22-C02": ("filled.hwpx", "ab6d2d2d8f9d4375c30b16b80e963a71c31c3b3ed6c7466f5bc3da872b00ebaf",
                   "p09-22-c02-filled-field-update.hwpx", "P09 revised & <value> 한글 🚀"),
}
SOURCES = (
    "tools/p09/qualify_click_here_update_target.py",
    "tools/p09/tests/test_click_here_update_target_qualification.py",
    "implementation/p09/P09-22_CLICK_HERE_PRESERVED_CACHE_POLICY.md",
    "implementation/p09/tools/run-hancom-2020-click-here-discovery.ps1",
    "implementation/p09/tools/run-hancom-2020-field-auto-number-target.ps1",
    "crates/hwpx-package/examples/p09_22_click_here_update_target_fixture.rs",
    "crates/hwpx-package/src/click_here_hwpx.rs",
    "crates/hwpx-package/tests/click_here_hwpx.rs",
    "crates/hwpx-package/src/lib.rs",
    "tools/p09/qualify_field_object_caption_target.py",
    "tools/p09/inspect_field_object_caption_target.py",
    "tools/p09/qualify_field_auto_number_target.py",
    "tools/p09/inspect_field_auto_number_target.py",
    "tools/p08/object_target_oracle.py",
)


def exact(value, expected, code):
    if not oracle.exact(value, expected):
        raise ValueError(code)


def native(section: bytes, header: bytes) -> dict:
    """One observed pair, direct paragraph/run text only; no generic field inference."""
    tree = ET.fromstring(section, parser=ET.XMLParser(
        target=ET.TreeBuilder(insert_comments=True, insert_pis=True)))
    if tree.tag != "{http://www.hancom.co.kr/hwpml/2011/section}sec":
        raise ValueError("click_section_root_invalid")
    begins, ends = list(tree.iter(HP + "fieldBegin")), list(tree.iter(HP + "fieldEnd"))
    if len(begins) != 1 or len(ends) != 1:
        raise ValueError("click_pair_inventory_invalid")
    begin, end = begins[0], ends[0]
    exact(begin.attrib, {"id": "1210042100", "type": "CLICK_HERE", "name": "p09-click-field",
                         "editable": "1", "dirty": begin.get("dirty"), "zorder": "-1",
                         "fieldid": "627272811"}, "click_begin_identity_invalid")
    if begin.get("dirty") not in ("0", "1"):
        raise ValueError("click_dirty_invalid")
    exact(end.attrib, {"beginIDRef": "1210042100", "fieldid": "627272811"}, "click_end_identity_invalid")
    if list(end) or (end.text or "").strip() or len(begin) != 1:
        raise ValueError("click_pair_children_invalid")
    parameters = begin[0]
    exact(parameters.tag, HP + "parameters", "click_parameters_invalid")
    exact(parameters.attrib, {"cnt": "4", "name": ""}, "click_parameters_invalid")
    expected = [("integerParam", {"name": "Prop"}),
                ("stringParam", {"name": "Command", "{http://www.w3.org/XML/1998/namespace}space": "preserve"}),
                ("stringParam", {"name": "Direction"}), ("stringParam", {"name": "HelpState"})]
    if len(parameters) != len(expected) or (begin.text or "").strip() or (parameters.text or "").strip():
        raise ValueError("click_parameters_invalid")
    for node, (name, attrs) in zip(parameters, expected, strict=True):
        if node.tag != HP + name or node.attrib != attrs or list(node) or (node.tail or "").strip():
            raise ValueError("click_parameters_invalid")
    if parameters[0].text != "9":
        raise ValueError("click_prop_invalid")
    raw_parameters = re.findall(br"<hp:parameters\b.*?</hp:parameters>", section, re.S)
    if len(raw_parameters) != 1:
        raise ValueError("click_parameter_lexical_identity_invalid")
    parents = {child: parent for parent in tree.iter() for child in parent}
    for node in (begin, end):
        ctrl = parents[node]
        if ctrl.tag != HP + "ctrl" or ctrl.attrib or len(ctrl) != 1 or (ctrl.text or "").strip():
            raise ValueError("click_pair_anchor_invalid")
        run = parents[ctrl]
        if run.tag != HP + "run" or parents[run].tag != HP + "p" or parents[parents[run]] is not tree:
            raise ValueError("click_pair_anchor_invalid")
    paragraph = parents[parents[parents[begin]]]
    if paragraph is not parents[parents[parents[end]]]:
        raise ValueError("click_cross_paragraph_rejected")
    active = False
    closed = False
    texts, styles = [], []
    for run in paragraph:
        if run.tag != HP + "run":
            if active:
                raise ValueError("click_non_run_content_rejected")
            continue
        if (run.text or "").strip():
            raise ValueError("click_run_text_rejected")
        for node in run:
            if node.tag == HP + "ctrl" and begin in list(node):
                if active or closed:
                    raise ValueError("click_pair_order_invalid")
                active = True
            elif node.tag == HP + "ctrl" and end in list(node):
                if not active:
                    raise ValueError("click_pair_order_invalid")
                active, closed = False, True
            elif active:
                if node.tag != HP + "t" or node.attrib or list(node):
                    raise ValueError("click_rich_text_rejected")
                texts.append(node.text or "")
                styles.append(run.get("charPrIDRef"))
            if (node.tail or "").strip():
                raise ValueError("click_inline_tail_rejected")
    if not closed or active or not texts:
        raise ValueError("click_pair_order_invalid")
    visible = "".join(texts)
    if begin.get("dirty") == "0" and visible != (parameters[2].text or ""):
        raise ValueError("click_instruction_mismatch")
    if b"<!doctype" in header.lower() or b"<!entity" in header.lower():
        raise ValueError("click_header_active_xml_rejected")
    catalog = ET.fromstring(header)
    definitions = []
    for style in styles:
        nodes = [n for n in catalog.iter(HH + "charPr") if n.get("id") == style]
        if len(nodes) != 1:
            raise ValueError("click_style_definition_invalid")
        definitions.append(oracle.sha256(ET.tostring(nodes[0])))
    return {"native_begin_id": 1210042100, "native_field_id": 627272811,
            "field_name_sha256": oracle.sha256(begin.get("name").encode()),
            "direction_sha256": oracle.sha256((parameters[2].text or "").encode()),
            "memo_sha256": oracle.sha256((parameters[3].text or "").encode()),
            "command_sha256": oracle.sha256((parameters[1].text or "").encode()),
            "parameters_sha256": oracle.sha256(raw_parameters[0]),
            "display_sha256": oracle.sha256((visible if begin.get("dirty") == "1" else "").encode()),
            "selected_character_style_refs": styles, "character_definition_sha256": definitions,
            "dirty": int(begin.get("dirty")), "section_sha256": oracle.sha256(section)}


def snapshot(path: Path, expected: str) -> tuple[dict, bytes, dict]:
    section, _, parts = oracle.package_snapshot(path, lifecycle.digest(expected))
    raw = oracle.bounded_bytes(path, oracle.MAX_PACKAGE)
    # Hash and parse the same bounded snapshot, including the header style catalog.
    if oracle.sha256(raw) != expected:
        raise ValueError("click_package_snapshot_drift")
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        if archive.read(oracle.SECTION) != section:
            raise ValueError("click_package_snapshot_drift")
        header = archive.read("Contents/header.xml")
    result = native(section, header)
    return {**result, "package_sha256": expected, "package_bytes": len(raw)}, section, parts


def prepare(manifest_path: Path, expected: str, *, root: Path = ROOT):
    shared.within(manifest_path, root / "fixtures/target-build")
    manifest = lifecycle.checked_json(manifest_path, expected)
    for key, value in {"schema_version": "hwpx-agent.p09-click-here-update-target-fixture/v1",
                       "task": "P09-22", "complete_package_graph": True, "actual_hangul": False,
                       "semantic_save_reopen": "not_run", "render": "not_run", "differential": "not_run",
                       "green_rows": 0, "p09_complete": False, "product_complete": False}.items():
        exact(manifest.get(key), value, "click_manifest_contract_invalid")
    rows = manifest.get("cases")
    if not isinstance(rows, list) or [r.get("case_id") for r in rows] != list(CASES):
        raise ValueError("click_manifest_cases_invalid")
    results = {}
    for row in rows:
        seed, sha, file, display = CASES[row["case_id"]]
        for key, value in {"source_file": seed, "source_package_sha256": sha, "file": file,
                           "feature_ids": ["REF-009"], "native_begin_id": 1210042100,
                           "native_field_id": 627272811, "deterministic_retry": True,
                           "stale_source_rejected": True, "outside_declared_edits_byte_exact": True,
                           "expected_display_sha256": oracle.sha256(display.encode())}.items():
            exact(row.get(key), value, "click_case_contract_invalid")
        seed_state, source, source_parts = snapshot(root / DISCOVERY / seed, sha)
        result, output, parts = snapshot(manifest_path.parent / file, row["output_package_sha256"])
        # This oracle does not call the Rust adapter: independently reconstruct the only allowed edits.
        begin = re.search(br'<hp:fieldBegin\b[^>]*>', source)
        stop = source.find(b"<hp:fieldEnd")
        span = source[begin.end():stop]
        texts = list(re.finditer(br"<hp:t>(.*?)</hp:t>", span, re.S))
        if len(texts) != 1 or source.count(b"<hp:fieldBegin") != 1:
            raise ValueError("click_seed_edit_spans_invalid")
        text = texts[0]
        a, b = begin.end() + text.start(1), begin.end() + text.end(1)
        reconstructed = source[:a] + escape(display).encode() + source[b:]
        reconstructed = reconstructed[:begin.start()] + begin[0].replace(b'dirty="0"', b'dirty="1"') + reconstructed[begin.end():]
        if output != reconstructed or parts != source_parts:
            raise ValueError("click_declared_edits_or_resources_changed")
        for key, value in {"source_section_sha256": seed_state["section_sha256"],
                           "output_section_sha256": result["section_sha256"],
                           "output_package_bytes": result["package_bytes"],
                           "parameters_sha256": seed_state["parameters_sha256"],
                           "unrelated_parts_sha256": source_parts}.items():
            exact(row.get(key), value, "click_case_artifact_binding_invalid")
        lifecycle.digest(row.get("plan_sha256"))
        if result["display_sha256"] != row["expected_display_sha256"]:
            raise ValueError("click_input_display_invalid")
        results[row["case_id"]] = (row, result, output, parts)
    return manifest, results


def discovery(root: Path) -> dict:
    trace = lifecycle.checked_json(root / DISCOVERY / "discovery-trace.json", DISCOVERY_SHA)
    expected = {"schema_version": "hwpx-agent.p09-click-here-discovery-trace/v1", "task": "P09-22",
                "state": "pass", "target": {**lifecycle.TARGET, "prog_id": "HWPFrame.HwpObject.2"},
                "security_preflight": "pass", "lifecycle_helper_sha256": "30341f7a7ff5106e4c3ac74331abdd9b612ec4d88eb060387b506809399338a9",
                "official_api_pdf_sha256": "c787c69d46f26a9fca49ac9d34106bb4f146fb29da9f1caf92c6e77d46cef45b",
                "security_module_sha256": "9ac5b97c47ac8aed1e8bca27a3eef39411361d8f68c262509f0c40a8f9d21bb6",
                "failed_phase": None, "error_code": None, "remaining_hwp_process_count": 0,
                **{key: "pass" for key in ("create_field", "field_list", "filled_readback", "fresh_readback")},
                **{key: False for key in (*shared.PRIVACY_KEYS, "product_routing_qualified", "p09_complete", "product_complete")}}
    for key, value in expected.items():
        exact(trace.get(key), value, "click_discovery_trace_invalid")
    for path, digest, maximum in (
        ("implementation/p09/tools/run-hancom-2020-field-auto-number-target.ps1",
         trace["lifecycle_helper_sha256"], 2 * 1024 * 1024),
        ("fixtures/target-build/official-source-cache/devcenter-archive-main-20260906/hwp-automation/HwpAutomation.pdf",
         trace["official_api_pdf_sha256"], 64 * 1024 * 1024),
    ):
        if oracle.sha256(oracle.bounded_bytes(root / path, maximum)) != digest:
            raise ValueError("click_discovery_authority_drift")
    sessions = trace.get("sessions")
    if not isinstance(sessions, list) or len(sessions) != 2:
        raise ValueError("click_discovery_sessions_invalid")
    pids = []
    for session, label in zip(sessions, ("capture", "reopen"), strict=True):
        process = session.get("process", {})
        if (session.get("label") != label or session.get("version") != lifecycle.TARGET["build"]
                or type(session.get("register_module_return")) is not bool
                or process.get("executable_sha256") != lifecycle.TARGET["executable_sha256"]
                or type(process.get("process_id")) is not int or process["process_id"] <= 0):
            raise ValueError("click_discovery_process_invalid")
        pids.append(process["process_id"])
    if len(set(pids)) != 2:
        raise ValueError("click_discovery_not_fresh")
    states = {}
    for name in ("empty.hwpx", "filled.hwpx", "reopened.hwpx", "filled.pdf", "reopened.pdf"):
        row = trace["artifacts"][name]
        raw = oracle.bounded_bytes(root / DISCOVERY / name, 32 * 1024 * 1024)
        if oracle.sha256(raw) != lifecycle.digest(row.get("sha256")) or type(row.get("bytes")) is not int or row["bytes"] != len(raw):
            raise ValueError("click_discovery_artifact_invalid")
        if name.endswith(".hwpx"):
            states[name], _, _ = snapshot(root / DISCOVERY / name, row["sha256"])
        elif not raw.startswith(b"%PDF-"):
            raise ValueError("click_discovery_pdf_invalid")
    for key in ("field_name_sha256", "direction_sha256", "memo_sha256"):
        if any(state[key] != trace[key] for state in states.values()):
            raise ValueError("click_discovery_metadata_invalid")
    if (states["empty.hwpx"]["dirty"] != 0 or states["empty.hwpx"]["display_sha256"] != oracle.sha256(b"")
            or any(states[name]["dirty"] != 1 or states[name]["display_sha256"] != trace["filled_text_sha256"]
                   for name in ("filled.hwpx", "reopened.hwpx"))
            or states["filled.hwpx"]["section_sha256"] != states["reopened.hwpx"]["section_sha256"]):
        raise ValueError("click_discovery_cache_invalid")
    return {"trace_sha256": DISCOVERY_SHA, "snapshots": states,
            "register_module_returns": [s["register_module_return"] for s in sessions],
            "artifact_identity": trace["artifacts"], "product_routing_qualified": False}


def pdf_comparison(left: Path, right: Path) -> dict:
    info, ppm = (shutil.which(name) for name in ("pdfinfo", "pdftoppm"))
    if not info or not ppm:
        raise ValueError("click_pdf_tools_unavailable")
    if any(pdf_oracle.pdf_page_count(Path(info), path) != 1 for path in (left, right)):
        raise ValueError("click_pdf_page_profile_invalid")
    with tempfile.TemporaryDirectory(prefix="p09-click-here-oracle-") as directory:
        a = pdf_oracle.render_pdf(Path(ppm), left, Path(directory), "left")
        b = pdf_oracle.render_pdf(Path(ppm), right, Path(directory), "right")
        if len(a) != 1 or len(b) != 1:
            raise ValueError("click_pdf_render_count_invalid")
        with Image.open(a[0]) as la, Image.open(b[0]) as rb:
            l, r = la.convert("RGB"), rb.convert("RGB")
            if l.size != r.size or l.width > 2048 or l.height > 2048:
                raise ValueError("click_pdf_render_dimensions_invalid")
            difference = ImageChops.difference(l, r)
            white = Image.new("RGB", l.size, "white")
            left_bounds = ImageChops.difference(l, white).getbbox()
            right_bounds = ImageChops.difference(r, white).getbbox()
            if left_bounds is None or right_bounds is None:
                raise ValueError("click_pdf_empty_page_rejected")
            changed = sum(1 for pixel in difference.get_flattened_data() if any(pixel))
            delta = sum(sum(pixel) for pixel in difference.get_flattened_data())
            return {"state": "equal" if changed == 0 else "mismatch", "dpi": 96, "page_count": 1,
                    "width": l.width, "height": l.height, "changed_pixels": changed,
                    "absolute_rgb_delta_sum": delta, "difference_bbox": difference.getbbox(),
                    "left_nonwhite_bbox": left_bounds, "right_nonwhite_bbox": right_bounds,
                    "masks_or_tolerances_used": False,
                    "renderer_sha256": oracle.sha256(oracle.bounded_bytes(Path(ppm), 64 * 1024 * 1024)),
                    "pdfinfo_sha256": oracle.sha256(oracle.bounded_bytes(Path(info), 64 * 1024 * 1024))}


def qualify(manifest_path: Path, expected: str, case: str, attempt: Path, trace_sha: str,
            *, root: Path = ROOT, access_attested: bool = False) -> dict:
    _, prepared = prepare(manifest_path, expected, root=root)
    if case not in CASES:
        raise ValueError("click_case_unknown")
    shared.within(attempt, root / "implementation/p09/evidence/private")
    row, source, section, parts = prepared[case]
    trace = lifecycle.checked_json(attempt / "target-trace.json", trace_sha)
    lifecycle.verify_trace(trace, {"input_package_sha256": row["output_package_sha256"],
                                   "input_package_bytes": row["output_package_bytes"]})
    # Tighten types locally without changing the historical lifecycle verifier.
    if type(trace.get("input_bytes")) is not int:
        raise ValueError("click_lifecycle_input_size_invalid")
    captured = discovery(root)
    states = {}
    errors = []
    for stage, prefix in (("saved", "output"), ("reopened", "reopened")):
        state, actual, actual_parts = snapshot(attempt / (stage + ".hwpx"), trace[prefix + "_sha256"])
        exact(trace[prefix + "_bytes"], state["package_bytes"], "click_target_size_invalid")
        if (actual != section or state["display_sha256"] != row["expected_display_sha256"]
                or state["parameters_sha256"] != source["parameters_sha256"]):
            errors.append(stage + "_field_section_changed")
        if state["character_definition_sha256"] != source["character_definition_sha256"]:
            errors.append(stage + "_character_definition_changed")
        if any(actual_parts.get(k) != v for k, v in parts.items() if k.lower().startswith("bindata/")):
            errors.append(stage + "_binary_resources_changed")
        states[stage] = {**state, "section_byte_exact_to_lowered_input": actual == section,
                         "application_changed_non_section_parts": sorted(k for k in set(parts) | set(actual_parts)
                                                                           if parts.get(k) != actual_parts.get(k))}
    pdfs = {}
    for name, prefix in (("saved.pdf", "pdf"), ("reopened.pdf", "reopened_pdf")):
        raw = oracle.bounded_bytes(attempt / name, 32 * 1024 * 1024)
        if not raw.startswith(b"%PDF-") or oracle.sha256(raw) != lifecycle.digest(trace[prefix + "_sha256"]):
            raise ValueError("click_target_pdf_identity_invalid")
        exact(trace[prefix + "_bytes"], len(raw), "click_target_pdf_size_invalid")
        pdfs[name] = {"sha256": oracle.sha256(raw), "bytes": len(raw)}
    stability = pdf_comparison(attempt / "saved.pdf", attempt / "reopened.pdf")
    if stability["state"] != "equal":
        errors.append("saved_reopened_pdf_changed")
    comparison = {"state": "not_run", "product_differential_qualified": False}
    if case == "P09-22-C01":
        native_auto = captured["snapshots"]["filled.hwpx"]
        equal_text = states["saved"]["display_sha256"] == native_auto["display_sha256"]
        equal_styles = states["saved"]["character_definition_sha256"] == native_auto["character_definition_sha256"]
        rendered = pdf_comparison(attempt / "saved.pdf", root / DISCOVERY / "filled.pdf")
        comparison = {"state": "observed_equal_non_gate" if equal_text and equal_styles and rendered["state"] == "equal" else "observed_mismatch_non_gate",
                      "scope": "same_captured_empty_seed_and_same_value_not_qualified_fallback_route",
                      "text_equal": equal_text, "character_definitions_equal": equal_styles,
                      "direct_style_refs": states["saved"]["selected_character_style_refs"],
                      "automation_style_refs": native_auto["selected_character_style_refs"],
                      "pdf": rendered, "product_differential_qualified": False}
    bridge = lifecycle.checked_json(root / BRIDGE, BRIDGE_SHA)
    if bridge.get("state") != "source_qualified_non_gate" or bridge.get("task") != "P09-23":
        raise ValueError("click_source_bridge_invalid")
    for path, digest in {**bridge["new_adapter_sha256"],
                          "crates/hwpx-package/src/lib.rs": bridge["shared_lib"]["current_raw_sha256"]}.items():
        if oracle.sha256(oracle.bounded_bytes(root / path, 2 * 1024 * 1024)) != digest:
            raise ValueError("click_source_bridge_drift")
    return {"schema_version": "hwpx-agent.p09-click-here-update-target-qualification/v1",
            "task": "P09-22", "case_id": case, "target": lifecycle.TARGET,
            "state": "bounded_cached_semantic_non_green" if not errors else "failed_semantic_non_green",
            "errors": sorted(set(errors)), "manifest_sha256": expected, "lifecycle_trace_sha256": trace_sha,
            "source_bridge_receipt_sha256": BRIDGE_SHA, "native_discovery": captured,
            "source_sha256": {p: oracle.sha256(oracle.bounded_bytes(root / p, 2 * 1024 * 1024)) for p in SOURCES},
            "input": source, "snapshots": states, "pdf_identity": pdfs, "saved_reopened_pdf_stability": stability,
            "automation_comparison": comparison, "lifecycle": {key: trace[key] for key in lifecycle.LIFECYCLE_KEYS},
            "register_module_returns": [s["register_module_return"] for s in trace["sessions"]],
            "remaining_hwp_process_count_at_run": trace["remaining_hwp_process_count"],
            "user_access": {"state": "user_attested" if access_attested else "not_attested",
                            "scope": "permission_interaction_only_not_product_validation"},
            "claims": {"actual_open_save_fresh_reopen": True, "bounded_existing_click_here_cache_preservation": not errors,
                       "general_field_update_api_qualified": False, "field_insertion_qualified": False,
                       "field_locking_qualified": False, "product_routing_qualified": False,
                       "full_render_acceptance": "not_run", "automation_fallback": "not_run",
                       "product_differential": "not_run", "green_rows": 0, "p09_complete": False,
                       "product_complete": False},
            "privacy": {"absolute_private_paths": False, "raw_document_text_present": False,
                        "user_document_scanned": False, "external_network_invoked": False,
                        "registry_or_system_setting_changed": False, "computer_use_click_or_type_invoked": False}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--expected-manifest-sha256", required=True)
    parser.add_argument("--case", choices=list(CASES), default="P09-22-C01")
    parser.add_argument("--attempt", type=Path)
    parser.add_argument("--expected-trace-sha256")
    parser.add_argument("--user-access-attested", action="store_true")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--output", type=Path)
    output.add_argument("--verify", type=Path)
    args = parser.parse_args()
    try:
        if args.attempt:
            value = qualify(args.manifest, args.expected_manifest_sha256, args.case, args.attempt,
                            args.expected_trace_sha256, access_attested=args.user_access_attested)
        else:
            if args.output or args.verify or args.expected_trace_sha256:
                raise ValueError("click_static_prepare_cannot_publish_target")
            _, rows = prepare(args.manifest, args.expected_manifest_sha256)
            value = {"state": "static_preparation_only", "cases": list(rows), "actual_hangul": False, "green_rows": 0}
        encoded = lifecycle.canonical_bytes(value)
        if args.output:
            destination = args.output.absolute()
            shared.within(destination.parent, ROOT / "implementation/p09/evidence")
            if destination.is_symlink() or destination.is_junction() or "private" in destination.relative_to(ROOT).parts:
                raise ValueError("click_public_output_boundary_rejected")
            with destination.open("xb") as handle:
                handle.write(encoded)
        if args.verify and oracle.bounded_bytes(args.verify, 256 * 1024) != encoded:
            raise ValueError("click_qualification_record_mismatch")
    except (OSError, ValueError, TypeError, KeyError, AttributeError, UnicodeError, zipfile.BadZipFile,
            ET.ParseError, pdf_oracle.OracleError) as error:
        code = str(error) if type(error) is ValueError and re.fullmatch(r"[a-z_]+", str(error)) else "click_qualification_failed"
        print(json.dumps({"state": "fail", "error_code": code}))
        return 2
    print(json.dumps({"state": "pass", "qualification_state": value["state"],
                      "qualification_sha256": oracle.sha256(encoded), "green_rows": 0, "p09_complete": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
