#!/usr/bin/env python3
"""Actual public root preparation and exact source successor; never a native Gate."""
from __future__ import annotations
import argparse
import importlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.p09 import verify_p08_additive_export_source_bridge_v4 as old4
from tools.p09 import qualify_native_root_manifest as preparation

ROOT = old4.ROOT
LIB = old4.LIB
sha256 = old4.sha256
checked = old4.checked
bounded_bytes = old4.bounded_bytes
CURRENT_LIB = "95ba3752b2b3c6b2e1bd1879cdb05aabaef1e7ca0ca91e70b2843b2cbd0a247b"
ARCHIVE = "implementation/p09/source-archive/p09-34-pre-root-manifest-export/"
ARCHIVES = {
    LIB: (ARCHIVE + "lib.rs", old4.CURRENT_LIB),
    preparation.MODULE: (ARCHIVE + "native_root_manifest.rs", "b976699375c19771e2ec1fb61f3de2687cc658384111a6c05aa7217b4998c020"),
    "tools/p09/tests/test_native_form_package_public_export.py": (ARCHIVE + "test_native_form_package_public_export.py", "8b4ebc22f75e08126b358ea3b593bce01454a84ed670546a6691ec87ae7a019d"),
    "tools/p09/tests/test_native_form_complete_fixture.py": (ARCHIVE + "test_native_form_complete_fixture.py", "ac09ca9fdfc6ddf5d9fe9fbd5daf0dc07a67a15883d61f01efedc3413260e4a9"),
    "tools/p09/tests/test_native_form_complete_batch.py": (ARCHIVE + "test_native_form_complete_batch.py", "83b0e897e967d8cbbad544ba1f45b504bed71ce2e7be3474799d1024866c5eba"),
    "tools/p09/tests/test_native_root_manifest.py": (ARCHIVE + "test_native_root_manifest.py", "bb9b2a04df2767de29d62a016cb8310bfea231bf137c8064a0a3d86663a3617b"),
}
RECEIPTS = {
    **old4.old3.RECEIPTS, **old4.RECEIPTS,
    "P09-31": (preparation.q.CAPSULE, preparation.q.CAPSULE_SHA),
    "P09-32-preparation": (preparation.predecessor.PREPARATION, preparation.predecessor.PREPARATION_SHA),
    "P09-32": (preparation.PREDECESSOR, preparation.PREDECESSOR_SHA),
    "P09-33": ("implementation/p09/evidence/p09-33-native-root-manifest-preparation.current-2020.v1.json", "1836e2e3e2b2093edeada1a9681ccd7acb31f6bbc2d0d25c06e306c8e3cd2407"),
}
DELTAS = (b"mod native_root_manifest;\n", b"""pub use native_root_manifest::{
    NATIVE_ROOT_MANIFEST_PROFILE_ID, NativeRootManifestError, NativeRootManifestLimits,
    NativeRootManifestOutput, NativeRootManifestPlan, NativeRootManifestPreparer,
    NativeRootManifestPreservation, NativeRootManifestQualification, NativeRootManifestReceipt,
};
""")
OLD_HASH = b"""fn hash(raw: &[u8]) -> String {
    hex::encode(digest(raw))
}
"""
NEW_HASH = b"""fn hash(raw: &[u8]) -> String {
    const HEX: &[u8; 16] = b"0123456789abcdef";
    let mut result = String::with_capacity(64);
    for byte in digest(raw) {
        result.push(char::from(HEX[usize::from(byte >> 4)]));
        result.push(char::from(HEX[usize::from(byte & 15)]));
    }
    result
}
"""
PUBLIC_TEST = "crates/hwpx-package/tests/native_root_manifest_public.rs"
PUBLIC_HEADER = b"""//! Complete predecessor cases through the real public preparation API only.
use domain_ir::{FormControlIdentity, LogicalId};
use hwpx_package as native_root_manifest;
use hwpx_package::{
    NativeFormHwpxMap, NativeFormPackageLimits, NativeFormPackageMap, NativeFormPackageReader,
    NativeFormPackageSectionMap, NativeRootManifestError as E, NativeRootManifestLimits as L,
    NativeRootManifestPlan as Plan, NativeRootManifestPreparer as Prepare,
};
"""
SOURCES = tuple(dict.fromkeys((
    "tools/p09/verify_p08_additive_export_source_bridge_v5.py",
    "tools/p09/tests/test_native_root_manifest_public_export.py",
    "implementation/p09/P09-34_NATIVE_ROOT_MANIFEST_PUBLIC_EXPORT_POLICY.md",
    "protocol/migrations/p09-p08-additive-export-source-bridge-v4-to-v5.md",
    PUBLIC_TEST, *preparation.SOURCES, *old4.SOURCES,
    "tools/p09/qualify_native_form_complete_batch.py",
    "tools/p09/inspect_native_form_complete_fixture.py",
    "tools/p09/tests/test_native_form_complete_fixture.py",
    "tools/p09/tests/test_native_form_complete_batch.py",
    *(path for path, _ in ARCHIVES.values()),
)))


def record(name, root=ROOT):
    path, digest = RECEIPTS[name]
    return json.loads(checked(root / path, digest, 512 * 1024),
                      object_pairs_hook=old4.output.SHARED.lifecycle.duplicate_guard)


def historical_sources(name, root=ROOT):
    value = record(name, root)
    mapping = dict(value["source_sha256"])
    if name == "P09-23":
        mapping.update(value["new_adapter_sha256"])
        mapping[LIB] = value["shared_lib"]["current_raw_sha256"]
    result = {}
    for path, digest in mapping.items():
        candidates = [archive for inventory in (ARCHIVES, old4.ARCHIVES, old4.old3.ARCHIVES)
                      if path in inventory for archive, pinned in (inventory[path],) if digest == pinned]
        if path == preparation.predecessor.GENERATOR and digest == preparation.predecessor.GENERATOR_OLD:
            candidates.append(preparation.predecessor.ARCHIVE)
        if len(candidates) > 1:
            raise ValueError("root_public_ambiguous_archive_identity")
        actual = candidates[0] if candidates else path
        checked(root / actual, digest)
        result[path] = {"sha256": digest, "checked_path": actual, "archived_predecessor_source": actual != path}
    return result


def project(raw, root=ROOT, *, require_current=True):
    if require_current and sha256(raw) != CURRENT_LIB:
        raise ValueError("current_root_public_library_identity_changed")
    value = raw
    for delta in DELTAS:
        if value.count(delta) != 1:
            raise ValueError("root_public_export_delta_not_unique")
        value = value.replace(delta, b"", 1)
    if value != checked(root / ARCHIVES[LIB][0], ARCHIVES[LIB][1]):
        raise ValueError("root_public_export_projection_changed")
    return value


def module_lineage(root=ROOT):
    old = checked(root / ARCHIVES[preparation.MODULE][0], ARCHIVES[preparation.MODULE][1])
    actual = bounded_bytes(root / preparation.MODULE, 2 * 1024 * 1024)
    if old.count(OLD_HASH) != 1 or actual.count(NEW_HASH) != 1 or actual.replace(NEW_HASH, OLD_HASH) != old:
        raise ValueError("root_public_hash_only_source_delta_changed")
    return {"predecessor_raw_sha256": sha256(old), "current_raw_sha256": sha256(actual),
            "only_declared_hash_helper_changed": True, "added_runtime_dependencies": False}


def public_lineage(root=ROOT):
    pending = checked(root / preparation.TEST, record("P09-33", root)["source_sha256"][preparation.TEST])
    public = bounded_bytes(root / PUBLIC_TEST, 2 * 1024 * 1024)
    marker = b"use sha2::{Digest as _, Sha256};"
    if pending.count(marker) != 1 or public.count(marker) != 1 or public[:public.index(marker)] != PUBLIC_HEADER:
        raise ValueError("root_public_case_header_changed")
    if public[public.index(marker):] != pending[pending.index(marker):] or b"#[path" in public or b"../src/" in public:
        raise ValueError("root_public_complete_case_body_changed")
    return {"original_test_body_byte_exact": True, "compiled_via_public_library_only": True,
            "public_test_sha256": sha256(public)}


def public_cargo(extra=(), directory=None, root=ROOT):
    env = dict(os.environ); env.pop(preparation.ENV, None)
    if directory is not None:
        env[preparation.ENV] = str(directory)
    result = subprocess.run(["cargo", "test", "-p", "hwpx-package", "--test", "native_root_manifest_public",
                             "--locked", "--offline", *extra], cwd=root, env=env, capture_output=True, timeout=60,
                            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    if result.returncode or not 0 < len(result.stdout) <= 256 * 1024 or len(result.stderr) > 1024 * 1024:
        raise ValueError("root_public_actual_compiled_tests_failed")
    return result.stdout.decode("utf-8", errors="strict")


def root_public(root=ROOT):
    lineage = public_lineage(root)
    with tempfile.TemporaryDirectory(prefix="hwpx-p09-34-public-root-") as temporary:
        directory = Path(temporary).resolve()
        tests = preparation.test_inventory(public_cargo(directory=directory, root=root))
        proof = preparation.artifacts(directory, root)
    with tempfile.TemporaryDirectory(prefix="hwpx-p09-34-public-probe-") as temporary:
        stdout = public_cargo((preparation.ACTUAL, "--", "--exact", "--nocapture"), Path(temporary).resolve(), root)
    probes = re.findall(r"p09_33_root_manifest_probe_json=(\{[^\n]*\})", stdout)
    if len(probes) != 1:
        raise ValueError("root_public_actual_probe_missing")
    preparation.q.exact(json.loads(probes[0], object_pairs_hook=old4.output.SHARED.lifecycle.duplicate_guard),
                        proof["two-section-text"], "root_public_actual_probe_mismatch")
    return {**tests, **lineage, "independent_generated_package_checks": proof,
            "actual_public_typed_receipt_independently_verified": True}


def source_guard(root=ROOT):
    project(checked(root / LIB, CURRENT_LIB), root)
    module_lineage(root); public_lineage(root)
    for path, digest in ARCHIVES.values():
        checked(root / path, digest)
    return {name: historical_sources(name, root) for name in RECEIPTS}


def retained_preparation_and_readback(root=ROOT):
    # Explicit archived source checks precede this bounded independent replay.
    # It does not call a failed old current verifier through patched authorities.
    historical_sources("P09-32-preparation", root)
    historical_sources("P09-32", root)
    previous = preparation.predecessor
    old = checked(root / previous.ARCHIVE, previous.GENERATOR_OLD)
    current = bounded_bytes(root / previous.GENERATOR, 2 * 1024 * 1024)
    if old.count(previous.OLD) != 1 or current.count(previous.NEW) != 1 or current.replace(previous.NEW, previous.OLD) != old:
        raise ValueError("root_public_retained_generator_delta_changed")
    initial = record("P09-32-preparation", root)
    replay = preparation.q.inspect(root / previous.MANIFEST, previous.MANIFEST_SHA, root, check_authority=False)
    replay["source_sha256"] = initial["source_sha256"]
    if old4.output.SHARED.lifecycle.canonical_bytes(replay) != checked(root / previous.PREPARATION, previous.PREPARATION_SHA):
        raise ValueError("root_public_retained_preparation_reproduction_changed")
    traces = previous.verified_traces(root)
    actual = previous.rust_observations(root)
    previous.verify_rust(actual, traces)
    receipt = record("P09-32", root)
    preparation.q.exact(actual["cases"], [case["complete_public_readback"] for case in receipt["cases"]],
                        "root_public_retained_native_readback_changed")
    return {"initial_preparation_byte_exact_reproduction": True, "original_missing_output_delta_byte_exact": True,
            "existing_trace_count_reverified": len(traces), "existing_owned_session_count": sum(len(t[2]["sessions"]) for t in traces),
            "existing_native_public_readback_exact": True, "new_native_session_started": False,
            "previous_native_failures_resolved": False, "pdf_render_rerun": False}


def failures(root=ROOT):
    old1, old2 = old4.old3.predecessors(root)
    observation = importlib.import_module("tools.p09.qualify_native_form_observation_component")
    expected = old4.old3.expected_failure
    return {
        "P09-21": expected(lambda: old1.verify(root), "current_shared_lib_identity_changed"),
        "P09-23": expected(lambda: old2.verify(root), "current_successor_lib_identity_changed"),
        "P09-27": expected(lambda: observation.qualify(root), "native_form_observation_pending_export_boundary_changed"),
        "P09-28": expected(lambda: old4.old3.verify(root), "public_export_source_identity_changed"),
        "P09-29": expected(lambda: old4.binding.qualify(root), "public_export_source_identity_changed"),
        "P09-30": expected(lambda: old4.output.qualify(root), "public_export_source_identity_changed"),
        "P09-31": expected(lambda: old4.verify(root), "public_export_source_identity_changed"),
        "P09-32-preparation": expected(lambda: preparation.q.authority(root), "public_export_source_identity_changed"),
        "P09-32": expected(lambda: preparation.predecessor.source_bridge(root), "public_export_source_identity_changed"),
        "P09-33": expected(lambda: preparation.qualify(root), "public_export_source_identity_changed"),
    }


def verify(root=ROOT):
    sys.path.insert(0, str(root)); sys.path.insert(0, str(root / "tools/p08"))
    historical = source_guard(root)
    raw = checked(root / LIB, CURRENT_LIB)
    v4 = project(raw, root); v3 = old4.project(v4, root); v2 = old4.old3.project(v3, root)
    old1, old2 = old4.old3.predecessors(root)
    v1 = old2.project(v2, root); p08 = old1.project(v1)
    for mapping in (old1.PREDECESSORS, old1.ADDITIONS, old1.REQUIRED_VALIDATORS, old2.ADDITIONS):
        old1.check_locked(root, mapping)
    before = {path: sha256(bounded_bytes(root / path, 2 * 1024 * 1024)) for path in SOURCES}
    predecessor_failures = failures(root)
    retained = retained_preparation_and_readback(root)
    library = subprocess.run(["cargo", "check", "-p", "hwpx-package", "--lib", "--locked", "--offline"],
                             cwd=root, capture_output=True, timeout=60,
                             creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    if library.returncode or len(library.stdout) + len(library.stderr) > 1024 * 1024:
        raise ValueError("root_public_production_library_check_failed")
    tests = {"binding": old4.public_binding(root), "output": old4.public_output(root), "root_preparation": root_public(root)}
    aggregate = importlib.import_module("validate_object_conformance_contract")
    if list(aggregate.EXPECTED_UPSTREAM) != list(old1.REQUIRED_VALIDATORS)[:23]:
        raise ValueError("root_public_upstream_inventory_changed")
    validators = [old1.run_json_validator(root, path) for path in old1.REQUIRED_VALIDATORS]
    if before != {path: sha256(bounded_bytes(root / path, 2 * 1024 * 1024)) for path in SOURCES} or historical != source_guard(root):
        raise ValueError("root_public_source_changed_during_verification")
    return {"schema_version": "hwpx-agent.p09-p08-additive-export-source-bridge/v5", "task": "P09-34",
            "state": "root_preparation_public_export_source_qualified_non_gate", "source_sha256": before,
            "historical_source_checks": historical, "preserved_receipt_sha256": {n: d for n, (_, d) in RECEIPTS.items()},
            "actual_predecessor_current_failures": predecessor_failures,
            "retained_preparation_and_native_readback": retained,
            "shared_lib": {"current_raw_sha256": sha256(raw), "v4_raw_sha256": sha256(v4), "v3_raw_sha256": sha256(v3),
                           "v2_raw_sha256": sha256(v2), "v1_raw_sha256": sha256(v1), "p08_predecessor_raw_sha256": sha256(p08),
                           "new_exact_deltas_sha256": [sha256(delta) for delta in DELTAS]},
            "module_source_transition": module_lineage(root), "production_library_check": {"state": "pass", "locked": True, "offline": True},
            "actual_public_rust_tests": tests, "required_current_validators": validators,
            "historical_p08_authority": aggregate.validate(run_upstream=False),
            "claims": {"exact_additive_export_chain": True, "public_root_preparation_exports_connected": True,
                       "public_package_reader_and_lowerer_tests_executed": True, "complete_generated_output_packages_independently_verified": True,
                       "production_library_checked_without_test_dependencies": True,
                       "archived_sources_are_current_full_verifier_pass": False, "predecessor_receipts_rewritten": False,
                       "legacy_live_aggregate_now_pass": False, "new_adapter_target_execution": False, "current_target_promotion": False,
                       "native_open_failure_resolved": False, "color_and_native_name_failures_resolved": False,
                       "typed_reference_semantics_qualified": False, "production_routing_qualified": False,
                       "render": "not_run", "product_differential": "not_run", "green_rows": 0, "p09_complete": False, "product_complete": False},
            "privacy": {"raw_document_text_present": False, "absolute_private_paths_present": False, "native_session_started": False,
                        "trust_or_registry_changed": False, "external_network_invoked": False}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(); group.add_argument("--output", type=Path); group.add_argument("--verify", type=Path)
    args = parser.parse_args()
    try:
        value = verify(); raw = old4.output.SHARED.lifecycle.canonical_bytes(value)
        if args.output:
            path = args.output.absolute(); old4.output.SHARED.within(path.parent, ROOT / "implementation/p09/evidence")
            if "private" in path.relative_to(ROOT).parts or path.is_symlink() or path.is_junction():
                raise ValueError("root_public_evidence_boundary_invalid")
            with path.open("xb") as stream: stream.write(raw)
        if args.verify and bounded_bytes(args.verify, 512 * 1024) != raw:
            raise ValueError("root_public_receipt_reproduction_mismatch")
    except (OSError, ValueError, KeyError, TypeError, UnicodeError, subprocess.SubprocessError) as error:
        code = str(error) if type(error) is ValueError and re.fullmatch(r"[a-z_]+", str(error)) else "root_public_qualification_failed"
        print(json.dumps({"state": "fail", "error_code": code})); return 2
    print(json.dumps({"state": "pass", "qualification_sha256": sha256(raw), "actual_public_integration_passed": 48,
                      "actual_library_unit_passed": 2, "validator_count": 25, "native_session_started": False, "green_rows": 0})); return 0


if __name__ == "__main__":
    raise SystemExit(main())
