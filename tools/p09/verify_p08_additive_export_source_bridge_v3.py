#!/usr/bin/env python3
"""Exact native-form public export successor; archived source proofs are not live target PASS."""
from __future__ import annotations

import argparse
import importlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.p09.inspect_field_auto_number_target import bounded_bytes, sha256

ROOT = Path(__file__).resolve().parents[2]
LIB = "crates/hwpx-package/src/lib.rs"
CURRENT_LIB = "d39fd55db3e98dc3130ca8aca8f35d1dd67557b4bb2f127b9e7ee2c439daa987"
ARCHIVE = "implementation/p09/source-archive/p09-28-pre-public-export/"
ARCHIVES = {
    LIB: (ARCHIVE + "lib.rs", "1eae8f6896cb5bb70762ac41e00d0fa017af794cb6dfaec8463879eb1f366d09"),
    "tools/p09/tests/test_p08_additive_export_source_bridge.py":
        (ARCHIVE + "test_p08_additive_export_source_bridge.py", "2e163672d026f010e363ad8913e4afc68335f77490e73089d645144d2d4f33a9"),
    "tools/p09/tests/test_native_form_observation_component.py":
        (ARCHIVE + "test_native_form_observation_component.py", "c0f2f1d3143c6d721781868ca31051bc9b84284dba90dc2936f940a13e225ec0"),
    "tools/p09/tests/test_click_here_update_target_qualification.py":
        (ARCHIVE + "test_click_here_update_target_qualification.py", "66a169bc84d14d4ff7096e824ff93e0df1bce37d5d190bc7a8d747a8c85d4918"),
}
RECEIPTS = {
    "P09-23": ("implementation/p09/evidence/p09-23-p08-additive-export-source-qualification.current-2020.v2.json",
               "70806cbec581e50a5a4a419ce73e8a1ab32c09c930f7aae915c7b0d47bac38f1"),
    "P09-27": ("implementation/p09/evidence/p09-27-native-form-observation-component.current-2020.v1.json",
               "bf23f8ba6c30f7578284274111f5060070a5edf3b413a8ad557d3ae422cb8c82"),
    "P09-22-C01": ("implementation/p09/evidence/p09-22-click-here-update-target-c01-20261002-attempt01.v1.json",
                   "f17c6386af5a3b1dfa35c7cff0507cd4ac8ef61a05c560824f640f5c85890e9b"),
    "P09-22-C02": ("implementation/p09/evidence/p09-22-click-here-update-target-c02-20261002-attempt01.v1.json",
                   "27db328b1a4c14d73c5a6b4cef75c8ccaa2306e5d87853c7b4656f7a29fcffb9"),
}
DELTAS = (b"mod native_form_hwpx;\n", b"""pub use native_form_hwpx::{
    NATIVE_FORM_HWPX_PROFILE_ID, NativeFormControlObservation, NativeFormHwpxBuilder,
    NativeFormHwpxError, NativeFormHwpxLimits, NativeFormHwpxLowerer,
    NativeFormHwpxLoweringReceipt, NativeFormHwpxMap, NativeFormHwpxPlan, NativeFormHwpxReadback,
    NativeFormHwpxReader, NativeFormObservedIdentity, NativeFormObservedPayload,
    NativeFormPhysicalAnchor,
};
""")
PUBLIC_TEST = "crates/hwpx-package/tests/native_form_hwpx_public.rs"
SOURCES = ("tools/p09/verify_p08_additive_export_source_bridge_v3.py",
           "tools/p09/tests/test_native_form_public_export.py",
           "implementation/p09/P09-28_NATIVE_FORM_PUBLIC_EXPORT_POLICY.md",
           "protocol/migrations/p09-p08-additive-export-source-bridge-v2-to-v3.md",
           PUBLIC_TEST, LIB, *tuple(p for p in ARCHIVES if p != LIB))


def checked(path: Path, expected: str, limit: int = 2 * 1024 * 1024) -> bytes:
    raw = bounded_bytes(path, limit)
    if sha256(raw) != expected:
        raise ValueError("public_export_source_identity_changed")
    return raw


def record(name: str, root: Path = ROOT):
    path, digest = RECEIPTS[name]
    return json.loads(checked(root / path, digest, 256 * 1024))


def historical_sources(name: str, root: Path = ROOT):
    value = record(name, root)
    mapping = dict(value["source_sha256"])
    if name == "P09-23":
        mapping.update(value["new_adapter_sha256"])
        mapping[LIB] = value["shared_lib"]["current_raw_sha256"]
    result = {}
    for path, expected in mapping.items():
        actual_path = path
        if path in ARCHIVES:
            actual_path, pinned = ARCHIVES[path]
            if expected != pinned:
                raise ValueError("public_export_archive_pin_not_exact")
        checked(root / actual_path, expected)
        result[path] = {"sha256": expected, "checked_path": actual_path,
                        "archived_predecessor_source": actual_path != path}
    return result


def predecessors(root: Path = ROOT):
    bound = record("P09-23", root)
    checked(root / "tools/p09/verify_p08_additive_export_source_bridge_v2.py",
            bound["source_sha256"]["tools/p09/verify_p08_additive_export_source_bridge_v2.py"])
    old2 = importlib.import_module("tools.p09.verify_p08_additive_export_source_bridge_v2")
    old1, _ = old2.predecessor(root)
    return old1, old2


def project(data: bytes, root: Path = ROOT, *, require_current: bool = True) -> bytes:
    if require_current and sha256(data) != CURRENT_LIB:
        raise ValueError("current_public_export_lib_identity_changed")
    value = data
    for delta in DELTAS:
        if value.count(delta) != 1:
            raise ValueError("public_export_delta_not_unique")
        value = value.replace(delta, b"", 1)
    archived = checked(root / ARCHIVES[LIB][0], ARCHIVES[LIB][1])
    if value != archived:
        raise ValueError("public_export_projection_changed")
    return value


def public_cases(root: Path = ROOT):
    component = record("P09-27", root)
    pending_path = "crates/hwpx-package/tests/native_form_hwpx_pending_export.rs"
    pending = checked(root / pending_path, component["source_sha256"][pending_path])
    public = bounded_bytes(root / PUBLIC_TEST, 2 * 1024 * 1024)
    marker = b"use std::{error::Error, fmt::Write as _, fs, path::Path};"
    if (public.count(marker) != 1 or pending.count(marker) != 1
            or public[public.index(marker):] != pending[pending.index(marker):]
            or b'use hwpx_package::{' not in public
            or b'../src/native_form_hwpx.rs' in public or b'mod native_form_hwpx;' in public):
        raise ValueError("public_export_case_lineage_changed")
    q = importlib.import_module("tools.p09.qualify_native_form_observation_component")
    process = subprocess.run(["cargo", "test", "-p", "hwpx-package", "--test", "native_form_hwpx_public",
                              "--locked", "--offline"], cwd=root, capture_output=True, timeout=60,
                             creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    if process.returncode != 0 or not 0 < len(process.stdout) <= 128 * 1024:
        raise ValueError("public_export_actual_tests_failed")
    result = q.verify_test_output(process.stdout.decode("utf-8", errors="strict"))
    result["test_target"] = "native_form_hwpx_public"
    result["compiled_via_public_library_only"] = True
    result["compiled_actual_successor_source"] = True
    result["preceding_test_body_byte_exact"] = True
    return result


def expected_failure(operation, expected: str):
    try:
        operation()
    except ValueError as error:
        if str(error) != expected:
            raise ValueError("public_export_unexpected_predecessor_failure") from error
        return {"state": "fail", "error_code": expected, "actually_invoked": True}
    raise ValueError("public_export_false_predecessor_current_pass")


def verify(root: Path = ROOT):
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(root / "tools/p08"))
    historical = {name: historical_sources(name, root) for name in RECEIPTS}
    old1, old2 = predecessors(root)
    raw = checked(root / LIB, CURRENT_LIB)
    projected = project(raw, root)
    v1 = old2.project(projected, root)
    p08 = old1.project(v1)
    for mapping in (old1.PREDECESSORS, old1.ADDITIONS, old1.REQUIRED_VALIDATORS, old2.ADDITIONS):
        old1.check_locked(root, mapping)
    for path, digest in ARCHIVES.values():
        checked(root / path, digest)
    observation = importlib.import_module("tools.p09.qualify_native_form_observation_component")
    failures = {
        "P09-21": expected_failure(lambda: old1.verify(root), "current_shared_lib_identity_changed"),
        "P09-23": expected_failure(lambda: old2.verify(root), "current_successor_lib_identity_changed"),
        "P09-27": expected_failure(lambda: observation.qualify(root), "native_form_observation_pending_export_boundary_changed"),
    }
    before = {p: sha256(bounded_bytes(root / p, 2 * 1024 * 1024)) for p in SOURCES}
    original_capture = observation.prior.capture(root)
    if original_capture != record("P09-27", root)["capture"]:
        raise ValueError("public_export_original_capture_changed")
    tests = public_cases(root)
    aggregate = importlib.import_module("validate_object_conformance_contract")
    if list(aggregate.EXPECTED_UPSTREAM) != list(old1.REQUIRED_VALIDATORS)[:23]:
        raise ValueError("public_export_upstream_inventory_changed")
    checks = [old1.run_json_validator(root, name) for name in old1.REQUIRED_VALIDATORS]
    if before != {p: sha256(bounded_bytes(root / p, 2 * 1024 * 1024)) for p in SOURCES}:
        raise ValueError("public_export_source_changed_during_test")
    if historical != {name: historical_sources(name, root) for name in RECEIPTS}:
        raise ValueError("public_export_authority_changed_during_test")
    if observation.prior.capture(root) != original_capture:
        raise ValueError("public_export_capture_changed_during_test")
    return {"schema_version": "hwpx-agent.p09-p08-additive-export-source-bridge/v3", "task": "P09-28",
            "state": "public_export_source_qualified_non_gate",
            "predecessor_receipt_sha256": RECEIPTS["P09-23"][1],
            "predecessor_current_verifier_state": "fail",
            "predecessor_current_error": "current_successor_lib_identity_changed",
            "actual_predecessor_current_failures": failures,
            "historical_source_checks": historical,
            "preserved_receipt_sha256": {name: pin for name, (_, pin) in RECEIPTS.items()},
            "shared_lib": {"current_raw_sha256": sha256(raw), "v2_raw_sha256": sha256(projected),
                           "v1_raw_sha256": sha256(v1), "p08_predecessor_raw_sha256": sha256(p08),
                           "new_exact_deltas_sha256": [sha256(d) for d in DELTAS]},
            "unchanged_component_source_sha256": record("P09-27", root)["source_sha256"]["crates/hwpx-package/src/native_form_hwpx.rs"],
            "actual_public_rust_tests": tests, "required_current_validators": checks,
            "historical_p08_authority": aggregate.validate(run_upstream=False), "source_sha256": before,
            "claims": {"shared_library_export_connected": True, "exact_additive_export_chain": True,
                       "dependency_source_qualification": True, "public_component_tests_executed": True,
                       "archived_sources_are_current_full_verifier_pass": False,
                       "predecessor_receipts_rewritten": False, "legacy_live_aggregate_now_pass": False,
                       "new_adapter_target_execution": False, "current_target_promotion": False,
                       "package_part_bindings_independently_read": False, "production_routing_qualified": False,
                       "render": "not_run", "product_differential": "not_run", "green_rows": 0,
                       "p09_complete": False, "product_complete": False},
            "privacy": {"absolute_private_paths": False, "raw_document_text_present": False,
                        "native_session_started": False, "registry_or_trust_setting_changed": False,
                        "external_network_invoked": False}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--output", type=Path)
    group.add_argument("--verify", type=Path)
    args = parser.parse_args()
    try:
        value = verify()
        raw = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
        if args.output:
            output = args.output.absolute()
            output.parent.resolve(strict=True).relative_to((ROOT / "implementation/p09/evidence").resolve())
            if "private" in output.relative_to(ROOT).parts or any(p.is_symlink() or p.is_junction() for p in (output, *output.parents)):
                raise ValueError("public_export_evidence_boundary")
            with output.open("xb") as handle:
                handle.write(raw)
        if args.verify and bounded_bytes(args.verify, 512 * 1024) != raw:
            raise ValueError("public_export_receipt_reproduction_mismatch")
    except (OSError, ValueError, KeyError, TypeError, UnicodeError, subprocess.SubprocessError) as error:
        code = str(error) if type(error) is ValueError and re.fullmatch(r"[a-z_]+", str(error)) else "public_export_qualification_failed"
        print(json.dumps({"state": "fail", "error_code": code}))
        return 2
    print(json.dumps({"state": "pass", "qualification_state": value["state"], "qualification_sha256": sha256(raw),
                      "rust_tests_passed": value["actual_public_rust_tests"]["passed"],
                      "validator_count": len(value["required_current_validators"]), "p09_complete": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
