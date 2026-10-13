#!/usr/bin/env python3
"""Qualify the exact P09 export delta without rewriting any P08 authority."""
from __future__ import annotations

import argparse
import hashlib
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
PREDECESSOR_LIB = "a22f9f73f04e17ac3439022fcf6aaa0fb5f5ddb02d48257d10998bd01bdf2e12"
CURRENT_LIB = "9b1a0b883e0dfa9f99a61762d21d3bf03c98569289e2aba9b36b6d69ae2311d8"
PREDECESSORS = {
    "tools/p08/validate_asset_pipeline_contract.py": "3d66d5eb4f24822faadefa789675be7d87700031602ebf5064e486d44a32ffdc",
    "protocol/private/p08-asset-pipeline-v1.json": "3cc93cc0869af0d2f9ab9cea2ea5d16a74450eb28c3e6e59abd59d65ddf9087a",
    "implementation/p08/evidence/p08-01-asset-pipeline-source-qualification.v1.json": "c51a238396b7f7b1afa48a8a2567bf0ce9b525852accd8d464e56ad5c2ee693b",
    "tools/p08/validate_object_conformance_contract.py": "b8a0821feecfd47a8beaeb77785240555a410749b52b11fc01bb700ee3aa8b14",
}
ADDITIONS = {
    "crates/hwpx-package/src/field_auto_number_hwpx.rs": "2927752005e5a1f2914089935dcec21fd61239f44e9861dabca8a505e5b05288",
    "crates/hwpx-package/src/field_object_caption_hwpx.rs": "2dd63a557787ffe1f84a0c9f49c7d0ace89af22037ade6ee8d51db380835adda",
}
REQUIRED_VALIDATORS = {
    "tools/p08/validate_asset_pipeline_contract.py": "3d66d5eb4f24822faadefa789675be7d87700031602ebf5064e486d44a32ffdc",
    "tools/p08/validate_image_hwpx_contract.py": "a659e7d31cc1d3540493d13c9dcbb8c45563ca8b35e02d7b7816e5dbfe9e308f",
    "tools/p08/validate_object_geometry_contract.py": "35bb45d1e483f00ff3a69376cd1b8336a31f4049396e7e42fcd000da6d899271",
    "tools/p08/validate_basic_shape_contract.py": "ddaf052311e781a2792f4b44e5a74649e3141440e0c96e6d9ebdf630bc711bc4",
    "tools/p08/validate_object_appearance_contract.py": "ea1489ff47ce701905f3163fdb7bcfa2ac5296aec9fb07af93d84611b52aa510",
    "tools/p08/validate_object_composition_contract.py": "db71ecf973af76b675561e6e6dc55e91e4a7e4154dd01840bef3af16849957de",
    "tools/p08/validate_chart_automation_contract.py": "880558143995265c6908fde0c5908ff465373f69dc8a8e770edbf2ce64d202b8",
    "tools/p08/validate_drawing_canvas_contract.py": "a479b141f430986b4861cb727f4ffb3d460717681940e250c2b5008027d66c58",
    "tools/p08/validate_active_content_contract.py": "798fd8abb23dcbb01a6915d2c0c8d38f4adcfd954d18ddf32a008f0545bb8cdf",
    "tools/p08/validate_object_remainder_contract.py": "0a5319e8a9d9a41944f54542a87bf055a3b232fbf45d2bba8ff90eccc149ba14",
    "tools/p08/validate_object_hwpx_integration_contract.py": "db0f5bef0dc2c344e4b77dcc0fb3e300773b1d2be835d6088c00c4822c766b30",
    "tools/p08/validate_freeform_hwpx_integration_contract.py": "32efc40523fcf7493aee9b4ecc061c6001910f73df13e87211d07f70abf6c6c0",
    "tools/p08/validate_textbox_properties_hwpx_contract.py": "b73070838fbee5e56bac6f99709d5165c6895e27b58eafa9037b126613f30955",
    "tools/p08/validate_object_protect_hwpx_contract.py": "0da02bbed9070921084f71511d45bc38bbfeef647d0f05425cebe527774c13ed",
    "tools/p08/validate_object_hyperlink_hwpx_contract.py": "3b40102487a94f1df52c98e6e19440a5bbe5439f79f51f4130ed20cbc143ba43",
    "tools/p08/validate_object_hyperlink_target_route_contract.py": "d039e801c2cc1113f564bb3a0ed45462d1febc21064969fbc8184600d41debef",
    "tools/p08/validate_object_remainder_hwpx_contract.py": "85722f08fe864fbc1209b5c3dc25a83c6b71c2da1e81a0c91b90a75fb40c53d4",
    "tools/p08/validate_object_target_qualification.py": "f2b47e1eab3a6a6e7d230868e65a5fbfeb8120a861f330ac504d64f75b366bc4",
    "tools/p08/validate_aspect_lock_negative_qualification.py": "51296a984e78b3cc2a6b8033017ecaf09add2d1cff1e6a5d341e2d94c3b70f1d",
    "tools/p08/validate_object_automation_binding_overlay.py": "e602cdd89aad2a953cbb09890c62635cf9a2d5cc7fa96f89878753af0ab714ea",
    "tools/p08/validate_object_surface_qualification.py": "e08ea212a8f62b2dec04f6e55a08d70c258f781f6835d4eb86612f249304d992",
    "tools/p08/validate_object_shape_canary_qualification.py": "0421a76e5485b40acdc933a794ea1c7359214ab2ee9b97e7e80b932d6b34e42a",
    "tools/p08/validate_object_automation_v2_qualification.py": "44e12e706eb29f56cf7a54166d88c64116b34bf9c411dd6d147f57c8cd943955",
    "tools/p09/validate_field_auto_number_hwpx_contract.py": "5b525cdaab8db9a23704c9ff856577b4823e5a4b58bb748c3b7cd413911dfa3f",
    "tools/p09/validate_field_object_caption_hwpx_contract.py": "dffc594a2f92dc71db053e1161dc22370efc396bf99d6e94bb960014daa3f4e4",
}
EXPORT_DRIFT_VALIDATORS = frozenset(
    "tools/p08/" + name + ".py" for name in (
        "validate_asset_pipeline_contract", "validate_image_hwpx_contract",
        "validate_object_geometry_contract", "validate_basic_shape_contract",
        "validate_object_appearance_contract", "validate_active_content_contract",
        "validate_object_hwpx_integration_contract", "validate_freeform_hwpx_integration_contract",
        "validate_textbox_properties_hwpx_contract",
    )
)
DELTAS = (
    b"mod field_auto_number_hwpx;\n",
    b"mod field_object_caption_hwpx;\n",
    b"""pub use field_auto_number_hwpx::{
    FIELD_AUTO_NUMBER_HWPX_PROFILE_ID, FieldAutoNumberHwpxBuilder, FieldAutoNumberHwpxError,
    FieldAutoNumberHwpxLimitConfig, FieldAutoNumberHwpxLimits, FieldAutoNumberHwpxLowerer,
    FieldAutoNumberHwpxLoweringReceipt, FieldAutoNumberHwpxPlan, FieldAutoNumberHwpxReadback,
    FieldAutoNumberHwpxReader,
};
""",
    b"""pub use field_object_caption_hwpx::{
    FIELD_OBJECT_CAPTION_HWPX_PROFILE_ID, FieldObjectCaptionHwpxBuilder,
    FieldObjectCaptionHwpxContext, FieldObjectCaptionHwpxError, FieldObjectCaptionHwpxLowerer,
    FieldObjectCaptionHwpxLoweringReceipt, FieldObjectCaptionHwpxPlan,
    FieldObjectCaptionHwpxReadback, FieldObjectCaptionHwpxReader, FieldObjectCaptionHwpxTarget,
};
""",
)
SOURCE_FILES = (
    "tools/p09/verify_p08_additive_export_source_bridge.py",
    "tools/p09/tests/test_p08_additive_export_source_bridge.py",
    "implementation/p09/P09-21_P08_ADDITIVE_EXPORT_SOURCE_POLICY.md",
    "protocol/migrations/p09-p08-additive-export-source-bridge-v0-to-v1.md",
)


def project(data: bytes, *, require_current: bool = True) -> bytes:
    # No normalization: this comparison is exact raw bytes, not a token/marker check.
    if require_current and sha256(data) != CURRENT_LIB:
        raise ValueError("current_shared_lib_identity_changed")
    projected = data
    for delta in DELTAS:
        if projected.count(delta) != 1:
            raise ValueError("additive_export_delta_not_unique")
        projected = projected.replace(delta, b"", 1)
    if sha256(projected) != PREDECESSOR_LIB:
        raise ValueError("predecessor_projection_changed")
    return projected


def check_locked(root: Path, mapping: dict[str, str]) -> dict[str, str]:
    result = {}
    for relative, expected in mapping.items():
        actual = sha256(bounded_bytes(root / relative, 2 * 1024 * 1024))
        if actual != expected:
            raise ValueError("bridge_source_identity_changed")
        result[relative] = actual
    return result


def admit_result(relative: str, exit_code: int, result: dict, unchanged: dict[str, str]) -> str:
    if relative not in EXPORT_DRIFT_VALIDATORS:
        if exit_code == 0 and result.get("state") == "pass":
            return "pass"
    elif (exit_code == 1 and result.get("state") == "fail"
          and result.get("errors") == ["implementation_digest"]
          and result.get("source_qualification_verified") is True
          and result.get("implementation_files") == len(unchanged) + 1
          and unchanged
          and result.get("official_source_locks_verified", True) is True):
        return "exact_export_drift_source_qualified_legacy_fail"
    raise ValueError("bridge_required_validator_failed:" + relative)


def run_json_validator(root: Path, relative: str) -> dict:
    # All required validator code is pinned before execution/import. A digest-error string
    # alone is insufficient: independently reproduce every other implementation lock.
    unchanged = {}
    if relative in EXPORT_DRIFT_VALIDATORS:
        module = importlib.import_module(Path(relative).stem)
        if module.IMPLEMENTATION_SHA256.get(LIB) != PREDECESSOR_LIB:
            raise ValueError("legacy_shared_lib_lock_changed")
        unchanged = check_locked(root, {p: h for p, h in module.IMPLEMENTATION_SHA256.items() if p != LIB})
    process = subprocess.run([sys.executable, relative], cwd=root, capture_output=True,
                             encoding="utf-8", errors="replace", timeout=60, check=False)
    values = []
    for line in process.stdout.splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            values.append(value)
    if not values:
        raise ValueError("bridge_required_validator_failed:" + relative)
    admission = admit_result(relative, process.returncode, values[-1], unchanged)
    return {"path": relative, "source_sha256": sha256(bounded_bytes(root / relative, 2 * 1024 * 1024)),
            "state": values[-1]["state"], "exit_code": process.returncode,
            "source_admission": admission, "actual_legacy_result": values[-1],
            "unchanged_implementation_sha256": unchanged}


def verify(root: Path = ROOT) -> dict:
    # Pin predecessor code before importing/executing it. Never monkeypatch its digest or result.
    preserved = check_locked(root, PREDECESSORS)
    additions = check_locked(root, ADDITIONS)
    validators = check_locked(root, REQUIRED_VALIDATORS)
    raw = bounded_bytes(root / LIB, 2 * 1024 * 1024)
    projected = project(raw)
    sys.path.insert(0, str(root / "tools/p08"))
    asset = importlib.import_module("validate_asset_pipeline_contract")
    aggregate = importlib.import_module("validate_object_conformance_contract")
    unchanged = {key: value for key, value in asset.IMPLEMENTATION_SHA256.items() if key != LIB}
    asset_sources = check_locked(root, unchanged)
    stale_result = asset.validate(root)
    if (stale_result["state"] != "fail" or stale_result["errors"] != ["implementation_digest"]
            or stale_result["source_locks"] != 8 or stale_result["implementation_files"] != 6
            or stale_result["source_qualification_verified"] is not True):
        raise ValueError("legacy_failure_is_not_exact_export_drift")
    # All historical matrix/source/privacy/security/route rules are still executed.
    historical = aggregate.validate(run_upstream=False)
    required = aggregate.EXPECTED_UPSTREAM
    if not required or required[0] != "tools/p08/validate_asset_pipeline_contract.py" or len(required) != 23:
        raise ValueError("predecessor_upstream_inventory_changed")
    if list(required) != list(REQUIRED_VALIDATORS)[:23]:
        raise ValueError("predecessor_upstream_inventory_changed")
    checks = [run_json_validator(root, name) for name in REQUIRED_VALIDATORS]
    return {
        "schema_version": "hwpx-agent.p09-p08-additive-export-source-bridge/v1", "task": "P09-21",
        "state": "source_qualified_non_gate", "scope": "exact_additive_p09_exports_over_preserved_p08_source",
        "predecessor_sha256": preserved, "unchanged_asset_implementation_sha256": asset_sources,
        "new_p09_module_sha256": additions,
        "shared_lib": {"current_raw_sha256": sha256(raw), "predecessor_raw_sha256": sha256(projected),
                       "exact_deltas_sha256": [sha256(delta) for delta in DELTAS]},
        "legacy_asset_validator": stale_result,
        "historical_p08_authority": historical,
        "required_current_validators": checks,
        "required_validator_sha256": validators,
        "bridge_source_sha256": {p: sha256(bounded_bytes(root / p, 2 * 1024 * 1024)) for p in SOURCE_FILES},
        "claims": {"dependency_source_qualification": True, "exact_predecessor_projection": True,
                   "legacy_validator_or_receipt_rewritten": False,
                   "legacy_live_aggregate_now_pass": False, "new_target_execution": False,
                   "current_target_promotion": False, "p09_complete": False, "product_complete": False},
        "privacy": {"raw_document_text_present": False, "absolute_private_paths": False,
                    "registry_or_trust_setting_changed": False, "external_network_invoked": False},
    }


def canonical_bytes(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--output", type=Path)
    output.add_argument("--verify", type=Path)
    args = parser.parse_args()
    try:
        result = verify()
        raw = canonical_bytes(result)
        if args.output:
            path = args.output.absolute()
            path.parent.resolve(strict=True).relative_to((ROOT / "implementation/p09/evidence").resolve())
            if (any(p.is_symlink() or p.is_junction() for p in (path, *path.parents))
                    or "private" in path.relative_to(ROOT).parts):
                raise ValueError("bridge_public_output_boundary_rejected")
            with path.open("xb") as handle:
                handle.write(raw)
        if args.verify and bounded_bytes(args.verify, 256 * 1024) != raw:
            raise ValueError("bridge_record_reproduction_mismatch")
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        code = str(error) if type(error) is ValueError else "bridge_verification_failed"
        print(json.dumps({"state": "fail", "error_code": code}))
        return 2
    print(json.dumps({"state": "pass", "qualification_state": result["state"],
                      "qualification_sha256": hashlib.sha256(raw).hexdigest(),
                      "current_validator_count": len(result["required_current_validators"]),
                      "legacy_aggregate_now_pass": False, "p09_complete": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
