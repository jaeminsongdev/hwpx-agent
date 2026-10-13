#!/usr/bin/env python3
"""Exact source successor for the new preserving CLICK_HERE adapter; no target promotion."""
from __future__ import annotations
import argparse
import importlib
import json
from pathlib import Path
import subprocess
import sys

if __package__:
    from .inspect_field_auto_number_target import bounded_bytes, sha256
else:
    from inspect_field_auto_number_target import bounded_bytes, sha256

ROOT = Path(__file__).resolve().parents[2]
LIB = "crates/hwpx-package/src/lib.rs"
CURRENT_LIB = "1eae8f6896cb5bb70762ac41e00d0fa017af794cb6dfaec8463879eb1f366d09"
RECEIPT = "implementation/p09/evidence/p09-21-p08-additive-export-source-qualification.current-2020.v1.json"
RECEIPT_SHA = "e62e69a558683d41eb6bb29663f86781ec7b324f07520f8b29126975ca7d21f6"
ARCHIVED_LIB = "implementation/p09/source-archive/p09-21-additive-exports-v1/lib.rs"
ARCHIVED_TEST = "implementation/p09/source-archive/p09-21-additive-exports-v1/test_p08_additive_export_source_bridge.py"
ADDITIONS = {
    "crates/hwpx-package/src/click_here_hwpx.rs": "5252ed2bafc7f6d311fe2368e4287ea5afd8f54dd85a0d2a15e5a99fc63fb213",
    "crates/hwpx-package/tests/click_here_hwpx.rs": "e16c15ecf2ca6eaf9fc615f92ded493d8280d55ff8150af4f4ae3d70947e2c35",
}
DELTAS = (b"mod click_here_hwpx;\n", b"""pub use click_here_hwpx::{
    CLICK_HERE_HWPX_PROFILE_ID, ClickHereHwpxBuilder, ClickHereHwpxError, ClickHereHwpxField,
    ClickHereHwpxLimits, ClickHereHwpxLowerer, ClickHereHwpxLoweringReceipt, ClickHereHwpxPlan,
    ClickHereHwpxReadback, ClickHereHwpxReader,
};
""")
SOURCES = ("tools/p09/verify_p08_additive_export_source_bridge_v2.py",
           "tools/p09/tests/test_p08_additive_export_source_bridge.py",
           "implementation/p09/P09-23_P08_ADDITIVE_EXPORT_SOURCE_POLICY.v2.md",
           "protocol/migrations/p09-p08-additive-export-source-bridge-v1-to-v2.md")

def checked(path: Path, expected: str, limit: int = 2 * 1024 * 1024) -> bytes:
    raw = bounded_bytes(path, limit)
    if sha256(raw) != expected:
        raise ValueError("source_successor_identity_changed")
    return raw

def predecessor(root: Path = ROOT):
    record = json.loads(checked(root / RECEIPT, RECEIPT_SHA, 256 * 1024))
    checked(root / "tools/p09/verify_p08_additive_export_source_bridge.py",
            record["bridge_source_sha256"]["tools/p09/verify_p08_additive_export_source_bridge.py"])
    return importlib.import_module("tools.p09.verify_p08_additive_export_source_bridge"), record

def project(data: bytes, root: Path = ROOT, *, require_current: bool = True) -> bytes:
    old, _ = predecessor(root)
    if require_current and sha256(data) != CURRENT_LIB:
        raise ValueError("current_successor_lib_identity_changed")
    projected = data
    for delta in DELTAS:
        if projected.count(delta) != 1:
            raise ValueError("successor_delta_not_unique")
        projected = projected.replace(delta, b"", 1)
    if sha256(projected) != old.CURRENT_LIB:
        raise ValueError("successor_projection_changed")
    archived = checked(root / ARCHIVED_LIB, old.CURRENT_LIB)
    if projected != archived:
        raise ValueError("successor_projection_archive_mismatch")
    return projected

def verify(root: Path = ROOT) -> dict:
    # Import only after raw pinning, and never replace the predecessor's expected digest/verdict.
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(root / "tools/p08"))
    old, record = predecessor(root)
    raw = bounded_bytes(root / LIB, 2 * 1024 * 1024)
    projected = project(raw, root)
    old.project(projected)  # A real archived byte projection, not a forged current-file verdict.
    old.check_locked(root, old.PREDECESSORS)
    old.check_locked(root, old.ADDITIONS)
    old.check_locked(root, old.REQUIRED_VALIDATORS)
    old.check_locked(root, ADDITIONS)
    test_sha = record["bridge_source_sha256"]["tools/p09/tests/test_p08_additive_export_source_bridge.py"]
    checked(root / ARCHIVED_TEST, test_sha)
    for path, digest in record["bridge_source_sha256"].items():
        if path != "tools/p09/tests/test_p08_additive_export_source_bridge.py":
            checked(root / path, digest)
    # The old verifier must reject this new live file, not pretend its old receipt is current.
    try:
        old.verify(root)
    except ValueError as error:
        if str(error) != "current_shared_lib_identity_changed":
            raise ValueError("unexpected_predecessor_failure") from error
    else:
        raise ValueError("predecessor_false_current_pass")
    aggregate = importlib.import_module("validate_object_conformance_contract")
    historical = aggregate.validate(run_upstream=False)
    if list(aggregate.EXPECTED_UPSTREAM) != list(old.REQUIRED_VALIDATORS)[:23]:
        raise ValueError("upstream_inventory_changed")
    checks = [old.run_json_validator(root, name) for name in old.REQUIRED_VALIDATORS]
    return {"schema_version": "hwpx-agent.p09-p08-additive-export-source-bridge/v2", "task": "P09-23",
            "state": "source_qualified_non_gate", "predecessor_receipt_sha256": RECEIPT_SHA,
            "predecessor_current_verifier_state": "fail", "predecessor_current_error": "current_shared_lib_identity_changed",
            "archived_predecessor_test_sha256": test_sha,
            "shared_lib": {"current_raw_sha256": sha256(raw), "predecessor_raw_sha256": sha256(projected),
                           "p08_predecessor_raw_sha256": sha256(old.project(projected)),
                           "new_exact_deltas_sha256": [sha256(d) for d in DELTAS]},
            "new_adapter_sha256": ADDITIONS, "required_current_validators": checks,
            "historical_p08_authority": historical,
            "source_sha256": {p: sha256(bounded_bytes(root / p, 2 * 1024 * 1024)) for p in SOURCES},
            "claims": {"dependency_source_qualification": True, "exact_additive_export_chain": True,
                       "predecessor_receipts_rewritten": False, "legacy_live_aggregate_now_pass": False,
                       "new_adapter_target_execution": False, "current_target_promotion": False,
                       "green_rows": 0, "p09_complete": False, "product_complete": False},
            "privacy": {"absolute_private_paths": False, "raw_document_text_present": False,
                        "registry_or_trust_setting_changed": False, "external_network_invoked": False}}

def main() -> int:
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
                raise ValueError("source_successor_public_boundary")
            with output.open("xb") as handle:
                handle.write(raw)
        if args.verify and bounded_bytes(args.verify, 256 * 1024) != raw:
            raise ValueError("source_successor_reproduction_mismatch")
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(json.dumps({"state": "fail", "error_code": str(error) if type(error) is ValueError else "source_successor_failed"}))
        return 2
    print(json.dumps({"state": "pass", "qualification_state": value["state"], "qualification_sha256": sha256(raw),
                      "validator_count": len(value["required_current_validators"]), "p09_complete": False}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
