#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any

try:
    from tools.p06 import table_chart_render_diff as render_diff
except ModuleNotFoundError:
    import table_chart_render_diff as render_diff  # type: ignore[no-redef]


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p06-table-chart-render-diff-v1.json"
MIGRATION = "protocol/migrations/p06-table-chart-hwpx-v1-to-render-diff-v1.md"
POLICY = "implementation/p06/P06-09_TABLE_CHART_RENDER_DIFF_POLICY.md"
REPORT = "implementation/p06/P06-09_TABLE_CHART_RENDER_DIFF_REPORT.md"
RECEIPT = (
    "implementation/p06/evidence/target/"
    "p06-table-chart-render-diff.current-2020.calibration01.v1.json"
)
PROFILE_SHA256 = "701248eec6ef0b5fd1524a718d7b18dd2e2077009e74cdacb0fdba34c2a5ba0b"
FEATURE = {"feature_id": "TABLE-006", "capability_id": "table.chart_from_table"}
TARGET = {
    "product": "Hancom Hangul 2020",
    "build": "11.0.0.9136",
    "architecture": "x86",
    "locale": "ko-KR",
}
SOURCE_LOCKS = {
    "protocol/private/p06-table-chart-hwpx-v1.json": (
        "d3074291e72a2e14fea28e873e752ea77a989386641439b6c88e3f1a8adb27cb"
    ),
    "tools/p06/table_chart_render_diff.py": (
        "ded4e1c65f2a6185bc18cffb739dcca8a748fc94a461ce261b72f1fbbefb4091"
    ),
}
ARTIFACTS = {
    "native_hwpx": {
        "path": (
            "fixtures/target-build/"
            "p06-09-table-chart-native-reference-hancom-20260913-01/saved.hwpx"
        ),
        "bytes": 49525,
        "sha256": "985416a6858f2f56c38ac5a8ec85d534d7c948ac0bd6484e96f6b8c11d1b7913",
    },
    "native_pdf": {
        "path": (
            "fixtures/target-build/"
            "p06-09-table-chart-native-reference-hancom-20260913-01/render.pdf"
        ),
        "bytes": 98163,
        "sha256": "99409fe6753825ad7b8ad355642a67a59ee5cad00f17546b9a1cad381219f5ad",
    },
    "product_hwpx": {
        "path": (
            "fixtures/target-build/"
            "p06-09-table-chart-product-hancom-20260913-02/saved.hwpx"
        ),
        "bytes": 49676,
        "sha256": "1647f725469b0501c30b9c856c0c530d98ccf12d0f981b5a7333a7ea3dbdd230",
    },
    "product_pdf": {
        "path": (
            "fixtures/target-build/"
            "p06-09-table-chart-product-hancom-20260913-02/render.pdf"
        ),
        "bytes": 98655,
        "sha256": "9a6c3ecbf2c392416b317afebaecadca32773ce6ea29f6f1bbc1f2e966f9f0ea",
    },
}
CALIBRATION_PAIR = {
    key: {"sha256": value["sha256"], "bytes": value["bytes"]}
    for key, value in ARTIFACTS.items()
}
QUALIFICATION = {
    "calibration_pair_may_pass_profile_fit": True,
    "calibration_pair_may_satisfy_required_render_diff": False,
    "fresh_independent_pair_required_after_profile_freeze": True,
    "outside_default_title_region_difference_allowed": False,
    "photo_or_user_screenshot_required": False,
}
GATE_DECISION = {
    "profile": "frozen_after_calibration",
    "calibration_fit": "pass",
    "required_render_diff": "not_run",
    "rollback_or_retry": "not_run",
    "TABLE-006": "integration_passed",
    "p06_09": "in_progress",
    "p06": "in_progress",
}
RECEIPT_GATE = {
    "calibration_fit": "pass",
    "required_render_diff": "not_run",
    "rollback_or_retry": "not_run",
    "TABLE-006": "integration_passed",
    "p06_09": "in_progress",
    "p06": "in_progress",
    "product_complete": False,
}
NOT_CLAIMED = {
    "calibration_as_oracle": False,
    "required_render_diff": False,
    "rollback_or_retry": False,
    "automation_runtime": False,
    "release_differential": False,
    "p06_09_complete": False,
    "p06_complete": False,
    "production": False,
    "product_complete": False,
}


def _reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _read_json(root: Path, relative: str) -> dict[str, Any]:
    path = root / relative
    data = path.read_bytes()
    if len(data) > render_diff.MAX_JSON_BYTES:
        raise ValueError("JSON exceeds byte bound")
    result = json.loads(data.decode("utf-8"), object_pairs_hook=_reject_duplicates)
    if not isinstance(result, dict):
        raise ValueError("JSON root must be an object")
    return result


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _profile_digest(profile: dict[str, Any]) -> str:
    encoded = json.dumps(
        profile,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _add(errors: list[str], code: str) -> None:
    if code not in errors:
        errors.append(code)


def validate_contract(root: Path, errors: list[str]) -> dict[str, Any] | None:
    try:
        contract = _read_json(root, CONTRACT)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        _add(errors, "contract_json_or_path")
        return None
    expected_keys = {
        "schema_version", "predecessor", "scope", "feature", "target",
        "calibration_pair", "frozen_profile", "qualification_rule", "source_locks",
        "failure_policy", "migration", "policy", "report", "receipt",
        "gate_decision", "not_claimed",
    }
    if set(contract) != expected_keys:
        _add(errors, "contract_shape")
    if (
        contract.get("schema_version")
        != "hwpx-agent.table-chart-render-diff-contract/v1"
        or contract.get("feature") != FEATURE
        or contract.get("target") != TARGET
        or contract.get("calibration_pair") != CALIBRATION_PAIR
        or contract.get("qualification_rule") != QUALIFICATION
        or contract.get("migration") != MIGRATION
        or contract.get("policy") != POLICY
        or contract.get("report") != REPORT
        or contract.get("receipt") != RECEIPT
        or contract.get("gate_decision") != GATE_DECISION
        or contract.get("not_claimed") != NOT_CLAIMED
    ):
        _add(errors, "contract_semantics")
    if contract.get("predecessor") != {
        "path": "protocol/private/p06-table-chart-hwpx-v1.json",
        "sha256": SOURCE_LOCKS["protocol/private/p06-table-chart-hwpx-v1.json"],
        "state": "immutable_integration_contract",
    }:
        _add(errors, "predecessor")
    if contract.get("source_locks") != [
        {"path": path, "sha256": digest} for path, digest in SOURCE_LOCKS.items()
    ]:
        _add(errors, "source_locks")
    profile = contract.get("frozen_profile")
    if not isinstance(profile, dict) or _profile_digest(profile) != PROFILE_SHA256:
        _add(errors, "frozen_profile")
    failure_policy = contract.get("failure_policy")
    if not isinstance(failure_policy, list) or len(failure_policy) != 8 or len(
        set(failure_policy)
    ) != 8:
        _add(errors, "failure_policy")
    return contract


def validate_sources(root: Path, errors: list[str]) -> None:
    for relative, expected in SOURCE_LOCKS.items():
        try:
            if _digest(root / relative) != expected:
                _add(errors, "source_lock_digest")
        except OSError:
            _add(errors, "source_lock_path")
    markers = {
        MIGRATION: (
            "calibration only",
            "may not be reused",
            "integration_passed",
            "remain separate Gates",
        ),
        POLICY: (
            "exact-target calibration / non-gating",
            "one changed pixel outside",
            "cannot satisfy `required_render_diff`",
            "User screenshots and photo evidence are not required",
        ),
        REPORT: (
            "calibration_fit_pass",
            "Required `render_diff`: `not_run`",
            "0/61 green",
            "new native/product pair",
        ),
    }
    for relative, required in markers.items():
        try:
            text = (root / relative).read_text(encoding="utf-8")
            if any(marker not in text for marker in required):
                _add(errors, "document_marker")
        except (OSError, UnicodeDecodeError):
            _add(errors, "document_path")


def validate_artifacts(root: Path, errors: list[str], profile: dict[str, Any] | None) -> None:
    for key, expected in ARTIFACTS.items():
        try:
            path = root / expected["path"]
            identity = render_diff.artifact_identity(path)
            if identity != CALIBRATION_PAIR[key]:
                _add(errors, "artifact_identity")
        except (OSError, ValueError):
            _add(errors, "artifact_path")
    if profile is None:
        return
    try:
        native = render_diff.chart_package_semantics(root / ARTIFACTS["native_hwpx"]["path"])
        product = render_diff.chart_package_semantics(root / ARTIFACTS["product_hwpx"]["path"])
        expected_semantics = profile.get("hwpx_semantics")
        if native != expected_semantics or product != expected_semantics:
            _add(errors, "artifact_hwpx_semantics")
    except (OSError, ValueError):
        _add(errors, "artifact_hwpx_semantics")
    for key in ("native_pdf", "product_pdf"):
        try:
            pdf = (root / ARTIFACTS[key]["path"]).read_bytes()
            if (
                not pdf.startswith(b"%PDF-1.4")
                or b"Hwp 2020 11.0.0.9136" not in pdf
                or b"Hancom PDF 1.3.0.550" not in pdf
                or not re.search(rb"/Count\s+1\b", pdf)
                or not re.search(rb"/MediaBox\s*\[\s*0\s+0\s+595\s+841\s*\]", pdf)
            ):
                _add(errors, "artifact_pdf_identity")
        except OSError:
            _add(errors, "artifact_pdf_path")


def validate_receipt(root: Path, errors: list[str]) -> None:
    try:
        receipt = _read_json(root, RECEIPT)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        _add(errors, "receipt_json_or_path")
        return
    expected_keys = {
        "schema_version", "evidence_id", "scope", "feature", "target",
        "profile_sha256", "artifacts", "observation", "qualification", "privacy",
        "gate_decision", "not_claimed",
    }
    if set(receipt) != expected_keys:
        _add(errors, "receipt_shape")
    if (
        receipt.get("schema_version")
        != "hwpx-agent.p06-09-table-chart-render-diff-calibration/v1"
        or receipt.get("feature") != FEATURE
        or receipt.get("target") != TARGET
        or receipt.get("profile_sha256") != PROFILE_SHA256
        or receipt.get("artifacts") != CALIBRATION_PAIR
        or receipt.get("gate_decision") != RECEIPT_GATE
        or receipt.get("not_claimed") != NOT_CLAIMED
    ):
        _add(errors, "receipt_semantics")
    qualification = receipt.get("qualification")
    if qualification != {
        "profile_frozen": True,
        "calibration_pair": True,
        "calibration_pair_reusable_for_gate": False,
        "fresh_independent_pair_required": True,
        "photo_or_user_screenshot_required": False,
    }:
        _add(errors, "receipt_qualification")
    privacy = receipt.get("privacy")
    if not isinstance(privacy, dict) or any(value is not False for value in privacy.values()):
        _add(errors, "receipt_privacy")
    observation = receipt.get("observation")
    raster = observation.get("raster") if isinstance(observation, dict) else None
    if (
        not isinstance(observation, dict)
        or observation.get("state") != "pass"
        or observation.get("word_text_exact") is not True
        or observation.get("maximum_word_bbox_delta_points") != 0.0
        or observation.get("hwpx_semantics_exact") is not True
        or observation.get("anchor_semantics_exact") is not True
        or not isinstance(raster, dict)
        or raster.get("outside_allowed_diff_box_pixels") != 0
        or raster.get("diff_bbox") != [450, 324, 575, 355]
        or raster.get("differing_pixels") != 1980
        or raster.get("ink_pixel_delta") != 443
    ):
        _add(errors, "receipt_observation")


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    contract = validate_contract(root, errors)
    validate_sources(root, errors)
    profile = contract.get("frozen_profile") if contract else None
    validate_artifacts(root, errors, profile if isinstance(profile, dict) else None)
    validate_receipt(root, errors)
    errors.sort()
    return {
        "schema_version": "hwpx-agent.p06-table-chart-render-diff-contract-validation/v1",
        "state": "pass" if not errors else "fail",
        "errors": errors,
        "source_locks": len(SOURCE_LOCKS),
        "artifacts": len(ARTIFACTS),
        "profile": "frozen_after_calibration" if not errors else "not_proven",
        "calibration_fit": "pass" if not errors else "not_proven",
        "required_render_diff": "not_run",
        "TABLE-006": "integration_passed",
        "p06_09": "in_progress",
        "product_complete": False,
    }


if __name__ == "__main__":
    result = validate()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    raise SystemExit(0 if result["state"] == "pass" else 1)
