#!/usr/bin/env python3
"""Bind native-form compatibility failures to a preserved capture and real Rust probe."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from xml.etree import ElementTree as ET

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.p09 import qualify_field_object_caption_target as shared
from tools.p09 import validate_form_control_hwpx_contract as predecessor

ROOT = shared.ROOT
CAPTURE = "implementation/p08/evidence/private/p08-20-object-target-20260915-18/obj-012-form-insert.hancom-2020-readback.hwpx"
CAPTURE_SHA = "02e9b5acef95877b6934a6a3131069402138cc2190eff2e68db79aa7e9ac9ce7"
SECTION_SHA = "89a263eff5d4536cc14223e48847a42e65c7e4f97d5b0c12b5cf73dc4bbba2ff"
PROBE = "crates/hwpx-package/examples/p09_25_native_form_compatibility.rs"
PREDECESSOR_SHA = "cff9addf4f10d9e7defd3717c24dbf0f22f753986a06d6d8713403e2bfa66f66"
P08_RECEIPT = "implementation/p08/evidence/p08-20-object-target-qualification.current-2020.v1.json"
P08_SHA = "2043c20e403ec02dd6a7ec66a013cfab2fbb4663d2eb9324d8fed51547001011"
SOURCES = ("tools/p09/qualify_native_form_compatibility.py", "tools/p09/tests/test_native_form_compatibility.py",
           "implementation/p09/P09-25_NATIVE_FORM_COMPATIBILITY_POLICY.md", PROBE,
           "crates/hwpx-package/examples/p08_19_support/common.rs",
           "tools/p09/validate_form_control_hwpx_contract.py", *predecessor.IMPLEMENTATION_SHA256)


def capture(root: Path = ROOT):
    path = shared.within(root / CAPTURE, root / "implementation/p08/evidence/private")
    section, _, _ = shared.oracle.package_snapshot(path, CAPTURE_SHA)
    raw = shared.oracle.bounded_bytes(path, shared.oracle.MAX_PACKAGE)
    if len(raw) != 14556 or shared.oracle.sha256(section) != SECTION_SHA:
        raise ValueError("native_form_capture_identity_invalid")
    tree = ET.fromstring(section)
    hp = shared.oracle.NS
    edits = list(tree.iter(hp + "edit"))
    if len(edits) != 1:
        raise ValueError("native_form_capture_inventory_invalid")
    edit = edits[0]
    if any(name in edit.attrib for name in ("id", "instid", "instId")):
        raise ValueError("native_form_capture_identity_gap_changed")
    parents = {child: parent for parent in tree.iter() for child in parent}
    run = parents[edit]
    paragraph = parents[run]
    if run.tag != hp + "run" or paragraph.tag != hp + "p" or parents[paragraph] is not tree:
        raise ValueError("native_form_capture_anchor_invalid")
    paragraphs = [n for n in tree if n.tag == hp + "p"]
    return {"package_sha256": CAPTURE_SHA, "package_bytes": len(raw), "section_sha256": SECTION_SHA,
            "control_count": 1, "native_tag": "edit", "native_id_present": False, "native_instance_id_present": False,
            "paragraph_ordinal": paragraphs.index(paragraph),
            "run_ordinal": [n for n in paragraph if n.tag == hp + "run"].index(run),
            "inline_ordinal": list(run).index(edit), "attribute_names": sorted(edit.attrib),
            "field_name_sha256": shared.oracle.sha256(edit.get("name", "").encode()),
            "geometry_child_names": [n.tag[len(hp):] for n in edit if n.tag in (hp + "sz", hp + "pos", hp + "outMargin")],
            "raw_document_text_present": False}


def verify_probe(value):
    expected = {"schema_version": "hwpx-agent.p09-native-form-compatibility-probe/v1", "task": "P09-25",
                "state": "reproduced_native_profile_gap_non_green", "capture_package_sha256": CAPTURE_SHA,
                "capture_section_sha256": SECTION_SHA, "legacy_actual_capture_error": "form_control_hwpx_invalid_attribute",
                "diagnostic_added_identity_not_native_evidence": True, "diagnostic_identity_only_projection_admitted": True,
                "diagnostic_wrong_anchor_and_shape_binding_admitted": True, "source_capture_preserved": True,
                "native_session_started": False, "actual_form_target_pass": False, "product_routing_qualified": False,
                "green_rows": 0, "p09_complete": False, "product_complete": False, "raw_document_text_present": False,
                "absolute_private_paths_present": False}
    if not shared.oracle.exact(value, expected):
        raise ValueError("native_form_probe_contract_invalid")


def run_probe(root: Path = ROOT):
    completed = subprocess.run(["cargo", "run", "-p", "hwpx-package", "--example",
                                "p09_25_native_form_compatibility", "--locked", "--offline"],
                               cwd=root, capture_output=True, timeout=60,
                               creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    if completed.returncode != 0 or not 0 < len(completed.stdout) <= 64 * 1024:
        raise ValueError("native_form_probe_execution_failed")
    value = json.loads(completed.stdout, object_pairs_hook=shared.lifecycle.duplicate_guard)
    verify_probe(value)
    return value


def qualify(root: Path = ROOT):
    observed = capture(root)
    for path, sha in predecessor.IMPLEMENTATION_SHA256.items():
        if shared.oracle.sha256(shared.oracle.bounded_bytes(root / path, 2 * 1024 * 1024)) != sha:
            raise ValueError("native_form_predecessor_implementation_drift")
    prior = shared.lifecycle.checked_json(root / predecessor.QUALIFICATION, PREDECESSOR_SHA)
    if prior.get("task") != "P09-12":
        raise ValueError("native_form_predecessor_identity_invalid")
    historical = shared.lifecycle.checked_json(root / P08_RECEIPT, P08_SHA)
    if historical.get("task") != "P08-20":
        raise ValueError("native_form_historical_capture_authority_invalid")
    result = run_probe(root)
    if capture(root) != observed:
        raise ValueError("native_form_capture_changed_during_probe")
    return {"schema_version": "hwpx-agent.p09-native-form-compatibility-qualification/v1", "task": "P09-25",
            "state": "native_identity_and_anchor_gaps_reproduced_non_green", "capture": observed, "rust_probe": result,
            "predecessor_receipt_sha256": PREDECESSOR_SHA, "historical_p08_receipt_sha256": P08_SHA,
            "source_sha256": {p: shared.oracle.sha256(shared.oracle.bounded_bytes(root / p, 2 * 1024 * 1024)) for p in SOURCES},
            "claims": {"native_identity_gap_reproduced": True, "legacy_anchor_and_shape_readback_gap_reproduced": True,
                       "new_native_identity_profile_implemented": False, "actual_new_form_target_execution": False,
                       "diagnostic_added_id_is_not_native_evidence": True, "old_receipts_rewritten": False,
                       "production_routing_qualified": False, "green_rows": 0, "p09_complete": False, "product_complete": False},
            "privacy": {"absolute_private_paths": False, "raw_document_text_present": False, "user_document_scanned": False,
                        "native_session_started": False, "computer_use_click_or_type_invoked": False,
                        "registry_or_system_setting_changed": False, "external_network_invoked": False}}


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
                raise ValueError("native_form_public_output_invalid")
            with output.open("xb") as handle:
                handle.write(raw)
        if args.verify and shared.oracle.bounded_bytes(args.verify, 256 * 1024) != raw:
            raise ValueError("native_form_qualification_record_mismatch")
    except (OSError, ValueError, KeyError, TypeError, AttributeError, UnicodeError, ET.ParseError,
            subprocess.TimeoutExpired) as error:
        code = str(error) if type(error) is ValueError and re.fullmatch(r"[a-z_]+", str(error)) else "native_form_qualification_failed"
        print(json.dumps({"state": "fail", "error_code": code}))
        return 2
    print(json.dumps({"state": "pass", "qualification_state": value["state"],
                      "qualification_sha256": shared.oracle.sha256(raw), "green_rows": 0, "p09_complete": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
