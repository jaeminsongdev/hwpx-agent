#!/usr/bin/env python3
"""Independently qualify actual complete root-href preparation, pending public export."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile
from xml.etree import ElementTree as ET

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.p09 import qualify_native_form_complete_batch as predecessor

q = predecessor.prepared
ROOT = q.ROOT
TARGET = "native_root_manifest_pending_export"
ENV = "HWPX_AGENT_P09_33_ORACLE_DIRECTORY"
ACTUAL = "real_failed_two_section_text_changes_only_one_href_value_and_preserves_all_parts"
MODULE = "crates/hwpx-package/src/native_root_manifest.rs"
TEST = "crates/hwpx-package/tests/native_root_manifest_pending_export.rs"
PREDECESSOR = "implementation/p09/evidence/p09-32-native-form-complete-batch.current-2020.v1.json"
PREDECESSOR_SHA = "0daf958b52e6259c483e0869a1a29439070585f8d753d047b8a7d6c4f198ca67"
PROFILE = "hwpx-agent.native-root-manifest.complete-package/v1"
EXPECTED = {
    "actual_original_root_manifest_is_full_raw_byte_exact_noop", ACTUAL,
    "complete_public_form_reader_still_observes_both_text_and_required_radio_sections",
    "deterministic_retry_external_verification_and_prepared_noop_are_exact",
    "stale_body_header_preview_and_archive_tail_cannot_reuse_plan",
    "externally_rehashed_nonselected_part_or_manifest_damage_is_rejected",
    "all_relative_items_not_just_section_one_are_prepared_without_other_lexical_edits",
    "declared_unicode_entity_and_percent_resources_keep_exact_targets_and_bytes",
    "external_escape_duplicate_spine_and_ambiguous_root_relative_sources_fail_closed",
    "altered_entry_order_compression_missing_extra_parts_and_malformed_xml_rejected",
    "finite_limits_and_reduced_verifier_ceiling_do_not_clamp_or_publish_artifacts",
    "errors_plan_output_and_receipt_never_expose_document_values_or_absolute_paths",
}
SOURCES = (MODULE, TEST, "tools/p09/qualify_native_root_manifest.py", "tools/p09/tests/test_native_root_manifest.py",
           "implementation/p09/P09-33_NATIVE_ROOT_MANIFEST_POLICY.md", "crates/hwpx-package/src/lib.rs",
           "crates/hwpx-package/src/graph.rs", "crates/hwpx-package/src/reader.rs", "crates/hwpx-package/src/limits.rs",
           "crates/hwpx-package/src/path.rs", "crates/hwpx-package/src/safe_xml.rs", "crates/hwpx-package/src/preserving_xml.rs",
           "crates/hwpx-package/src/native_form_package.rs", "Cargo.toml", "Cargo.lock", "crates/hwpx-package/Cargo.toml")
CASES = {
    "actual-native": (q.output.prior.prior.CAPTURE, q.output.prior.prior.CAPTURE_SHA),
    "two-section-text": (str(Path(predecessor.MANIFEST).parent / q.FILES[4]), "98f6c41d1ca3a10da2d8754ad2d73e71acb3d1a28e33ac0f573a8f654301aacc"),
    "two-section-radio": (str(Path(predecessor.MANIFEST).parent / q.FILES[5]), "2525a8da465b257a9171a46a7d95a7a5d2ba6da68ac1449764e208b374fe06e9"),
}


def sources(root=ROOT):
    predecessor.source_bridge(root)
    previous = q.shared.lifecycle.checked_json(root / PREDECESSOR, PREDECESSOR_SHA)
    for path, digest in previous["source_sha256"].items():
        q.output.export.checked(root / path, digest)
    lib = q.output.export.checked(root / q.public.LIB, q.public.CURRENT_LIB)
    if b"mod native_root_manifest;" in lib or b"pub use native_root_manifest" in lib:
        raise ValueError("root_manifest_pending_export_boundary_changed")
    raw = q.output.export.bounded_bytes(root / TEST, 2*1024*1024)
    if raw.count(b'#[path = "../src/native_root_manifest.rs"]') != 1:
        raise ValueError("root_manifest_pending_source_link_invalid")


def verify_case(name, source_raw, output_raw, root=ROOT):
    path, digest = CASES[name]
    if source_raw != q.output.export.checked(root / path, digest, 4*1024*1024):
        raise ValueError("root_manifest_original_source_substituted")
    source = q.package(source_raw)
    actual = q.package(output_raw)
    expected = dict(source["parts"])
    old = expected["Contents/content.hpf"]
    if name == "actual-native":
        if source_raw != output_raw:
            raise ValueError("root_manifest_original_noop_not_raw_exact")
        changed = 0
    else:
        marker = b'href="section1.xml"'
        if old.count(marker) != 1:
            raise ValueError("root_manifest_independent_edit_ambiguous")
        expected["Contents/content.hpf"] = old.replace(marker, b'href="Contents/section1.xml"')
        changed = 1
    if actual != {"parts": expected, "order": source["order"], "compression": source["compression"]}:
        raise ValueError("root_manifest_independent_complete_output_mismatch")
    # Both are whole closed body-spine/form observations, not per-section substitutes.
    if q.projection(source_raw)[1] != q.projection(output_raw)[1]:
        raise ValueError("root_manifest_independent_form_state_changed")
    return {"profile": PROFILE, "source_package_sha256": q.sha(source_raw), "output_package_sha256": q.sha(output_raw),
            "source_manifest_sha256": q.sha(old), "output_manifest_sha256": q.sha(expected["Contents/content.hpf"]),
            "entry_count": len(expected), "changed_href_attributes": changed, "graph_relationships_and_spine_preserved": True,
            "preservation": {"non_manifest_parts_expanded_byte_exact": True, "manifest_outside_href_edits_byte_exact": True,
                             "entry_order_and_compression_preserved": True},
            "zip_header_policy": "original_raw_byte_exact" if not changed else "rewritten_not_byte_exact",
            "qualification": "package_preparation_only_native_and_typed_reference_unqualified"}


def artifacts(directory, root=ROOT):
    expected_names = {f"{case}-{stage}.hwpx" for case in CASES for stage in ("source", "output")}
    if {p.name for p in directory.iterdir()} != expected_names:
        raise ValueError("root_manifest_artifact_inventory_invalid")
    return {name: verify_case(name, q.output.export.bounded_bytes(directory / f"{name}-source.hwpx", 4*1024*1024),
                             q.output.export.bounded_bytes(directory / f"{name}-output.hwpx", 4*1024*1024), root) for name in CASES}


def cargo(extra=(), directory=None, root=ROOT):
    env = dict(os.environ); env.pop(ENV, None)
    if directory is not None:
        env[ENV] = str(directory)
    p = subprocess.run(["cargo", "test", "-p", "hwpx-package", "--test", TARGET, "--locked", "--offline", *extra],
                       cwd=root, capture_output=True, timeout=60, env=env,
                       creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    if p.returncode or not 0 < len(p.stdout) <= 256*1024 or len(p.stderr) > 1024*1024:
        raise ValueError("root_manifest_compiled_tests_failed")
    return p.stdout.decode("utf-8", errors="strict")


def test_inventory(stdout):
    tests = re.findall(r"(?m)^test ([a-z0-9_]+) \.\.\. (ok|FAILED|ignored)\s*$", stdout)
    if len(tests) != 12 or {n for n, _ in tests} != EXPECTED or any(s != "ok" for _, s in tests):
        raise ValueError("root_manifest_compiled_test_inventory_invalid")
    if len(re.findall(r"(?m)^test result: ok\. 12 passed; 0 failed; 0 ignored;", stdout)) != 1:
        raise ValueError("root_manifest_compiled_test_summary_invalid")
    return {"passed": 12, "failed": 0, "ignored": 0, "names": sorted(EXPECTED), "locked": True, "offline": True}


def qualify(root=ROOT):
    sources(root)
    before = {p: q.sha(q.output.export.bounded_bytes(root / p, 2*1024*1024)) for p in SOURCES}
    with tempfile.TemporaryDirectory(prefix="hwpx-p09-33-root-manifest-oracle-") as temporary:
        directory = Path(temporary).resolve()
        tests = test_inventory(cargo(directory=directory, root=root))
        proof = artifacts(directory, root)
        # A fresh one-test execution binds a real typed receipt, not hand-authored fixture claims.
        with tempfile.TemporaryDirectory(prefix="hwpx-p09-33-root-manifest-probe-") as probe_dir:
            stdout = cargo((ACTUAL, "--", "--exact", "--nocapture"), Path(probe_dir).resolve(), root)
        probes = re.findall(r"p09_33_root_manifest_probe_json=(\{[^\n]*\})", stdout)
        if len(probes) != 1:
            raise ValueError("root_manifest_real_probe_missing")
        q.exact(json.loads(probes[0], object_pairs_hook=q.shared.lifecycle.duplicate_guard), proof["two-section-text"], "root_manifest_real_probe_mismatch")
    sources(root)
    if before != {p: q.sha(q.output.export.bounded_bytes(root / p, 2*1024*1024)) for p in SOURCES}:
        raise ValueError("root_manifest_sources_changed_during_verification")
    return {"schema_version": "hwpx-agent.p09-native-root-manifest-preparation/v1", "task": "P09-33",
            "state": "complete_package_root_href_preparation_pending_public_non_green", "predecessor_sha256": PREDECESSOR_SHA,
            "source_sha256": before, "actual_rust_tests": tests, "independent_generated_package_checks": proof,
            "claims": {"complete_root_href_source_component_implemented": True, "all_parts_and_href_gaps_independently_verified": True,
                       "actual_public_complete_form_reader_checked": True, "public_root_preparation_exports_connected": False,
                       "native_open_failure_resolved": False, "color_and_native_name_failures_resolved": False,
                       "typed_reference_semantics_qualified": False, "new_native_target_execution": False,
                       "production_routing_qualified": False, "render": "not_run", "product_differential": "not_run",
                       "green_rows": 0, "p09_complete": False},
            "privacy": {"raw_document_text_present": False, "absolute_private_paths_present": False,
                        "native_session_started": False, "trust_or_registry_changed": False, "external_network_invoked": False}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(); group.add_argument("--output", type=Path); group.add_argument("--verify", type=Path)
    args = parser.parse_args()
    try:
        raw = q.shared.lifecycle.canonical_bytes(qualify())
        if args.output:
            path = args.output.absolute(); q.shared.within(path.parent, ROOT / "implementation/p09/evidence")
            if path.is_symlink() or path.is_junction() or "private" in path.relative_to(ROOT).parts:
                raise ValueError("root_manifest_public_output_boundary_invalid")
            with path.open("xb") as stream: stream.write(raw)
        if args.verify and q.output.export.bounded_bytes(args.verify, 512*1024) != raw:
            raise ValueError("root_manifest_capsule_reproduction_mismatch")
    except (OSError, ValueError, KeyError, TypeError, UnicodeError, subprocess.SubprocessError, ET.ParseError, zipfile.BadZipFile) as error:
        code = str(error) if type(error) is ValueError and re.fullmatch(r"[a-z_]+", str(error)) else "root_manifest_qualification_failed"
        print(json.dumps({"state": "fail", "error_code": code})); return 2
    print(json.dumps({"state": "pass", "qualification_sha256": q.sha(raw), "rust_tests_passed": 12,
                      "public_preparation_connected": False, "native_session_started": False, "green_rows": 0})); return 0


if __name__ == "__main__":
    raise SystemExit(main())
