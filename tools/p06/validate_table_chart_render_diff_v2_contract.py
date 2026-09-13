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
CONTRACT = "protocol/private/p06-table-chart-render-diff-v2.json"
PREDECESSOR = "protocol/private/p06-table-chart-render-diff-v1.json"
MIGRATION = "protocol/migrations/p06-table-chart-render-diff-v1-to-v2.md"
POLICY = "implementation/p06/P06-09_TABLE_CHART_RENDER_DIFF_QUALIFICATION_POLICY.md"
REPORT = "implementation/p06/P06-09_TABLE_CHART_RENDER_DIFF_QUALIFICATION_REPORT.md"
RECEIPT = (
    "implementation/p06/evidence/target/"
    "p06-table-chart-render-diff.current-2020.qualification02.v2.json"
)
PREDECESSOR_SHA256 = "502de1f13fbef5ed638271db2054bde58118dfb79dc46465bfbc8671686b694b"
PROFILE_SHA256 = "701248eec6ef0b5fd1524a718d7b18dd2e2077009e74cdacb0fdba34c2a5ba0b"
RENDER_TOOL_SHA256 = "ded4e1c65f2a6185bc18cffb739dcca8a748fc94a461ce261b72f1fbbefb4091"
EXECUTABLE_SHA256 = "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce"
VISIBLE_TEXT_SHA256 = "87be6fc444e3875b011cb2266d20ef5d0c71642c6cf8c7601be1132e498aa362"

FEATURE = {"feature_id": "TABLE-006", "capability_id": "table.chart_from_table"}
TARGET = {
    "product": "Hancom Hangul 2020",
    "build": "11.0.0.9136",
    "architecture": "x86",
    "locale": "ko-KR",
}
SOURCE_LOCKS = {
    PREDECESSOR: PREDECESSOR_SHA256,
    "tools/p06/table_chart_render_diff.py": RENDER_TOOL_SHA256,
}


def artifact(kind: str, path: str, size: int, digest: str) -> dict[str, Any]:
    return {"kind": kind, "path": path, "bytes": size, "sha256": digest}


RUNS = [
    {
        "pair": "qualification",
        "side": "native",
        "input": {
            "bytes": 49614,
            "sha256": "454901d38967f3b2a92b407fd09c0ad9f0a3a12d291c8849dfc02257db8bf40a",
        },
        "artifacts": [
            artifact("saved_hwpx", "fixtures/target-build/p06-09-table-chart-native-reference-hancom-20260913-02/saved.hwpx", 49550, "8f1a98c7c7393fc7f8e4ac7615cf5bd8c3c03ab863feab96108969b5c7d5d803"),
            artifact("render_pdf", "fixtures/target-build/p06-09-table-chart-native-reference-hancom-20260913-02/render.pdf", 98163, "f71df8cdc2c99d743c86fdabc8a4eb23f1f37264ec226c7ae48e2731af681a56"),
            artifact("watchdog_trace", "fixtures/target-build/p06-09-table-chart-native-reference-hancom-20260913-02/trace.json", 2464, "b1114cb9160b1b6e254ba52977e48496899a85751d7031485485a467efec35c5"),
            artifact("worker_trace", "fixtures/target-build/p06-09-table-chart-native-reference-hancom-20260913-02/trace.json.inner.42888.json", 1921, "15d2fb89a7068e425038675792c2d88f2da5ba57db89bf17b2eeaca976c0b2de"),
            artifact("progress", "fixtures/target-build/p06-09-table-chart-native-reference-hancom-20260913-02/trace.json.progress.jsonl", 3587, "d1adb152059e241e15bfee449ca837c305b37d47d388cdee48a66d9d79fa2d12"),
        ],
    },
    {
        "pair": "qualification",
        "side": "product",
        "input": {
            "bytes": 15327,
            "sha256": "f9f7baa1f2aa975bd2d7fd63f268176e4cfa6121772e95b1893b9873b05bcf12",
        },
        "artifacts": [
            artifact("saved_hwpx", "fixtures/target-build/p06-09-table-chart-product-hancom-20260913-03/saved.hwpx", 49648, "86cca87eff52f97d6bacc8715f6ddcd1e6dae0bad176dc6e5c0e0c799ee95ec8"),
            artifact("render_pdf", "fixtures/target-build/p06-09-table-chart-product-hancom-20260913-03/render.pdf", 98655, "fbff9ef904bafb38845bbde74fb50d9d20c1929248fde56a95fbe9f128ad3c17"),
            artifact("watchdog_trace", "fixtures/target-build/p06-09-table-chart-product-hancom-20260913-03/trace.json", 2465, "0966f2bff2355baee707a28e5b2fbb314175a38a6af8193ac424f37a831ac149"),
            artifact("worker_trace", "fixtures/target-build/p06-09-table-chart-product-hancom-20260913-03/trace.json.inner.42888.json", 1922, "dc9488399cb89f45705a8f01974c20ea878beded6930a6a12bc4bde03dac3ba4"),
            artifact("progress", "fixtures/target-build/p06-09-table-chart-product-hancom-20260913-03/trace.json.progress.jsonl", 3597, "17b0a9bf2e1db26520118dfe3e2514eee8d3d0b3c6541477e1ddb0fbb92b53e5"),
        ],
    },
    {
        "pair": "retry",
        "side": "native",
        "input": {
            "bytes": 49614,
            "sha256": "454901d38967f3b2a92b407fd09c0ad9f0a3a12d291c8849dfc02257db8bf40a",
        },
        "artifacts": [
            artifact("saved_hwpx", "fixtures/target-build/p06-09-table-chart-native-reference-hancom-20260913-03/saved.hwpx", 49578, "49a7bcb947f641957a02d7a5ffd2cb41941b56d2435fb38ac3bcceb974c97589"),
            artifact("render_pdf", "fixtures/target-build/p06-09-table-chart-native-reference-hancom-20260913-03/render.pdf", 98163, "9142862a16903ca8c696cafee6db676c0a89465ca02a8c28f9deaf58647fc820"),
            artifact("watchdog_trace", "fixtures/target-build/p06-09-table-chart-native-reference-hancom-20260913-03/trace.json", 2465, "0997dfe51961562cdd332c842aa7f587c7c26e570de0bf6996321b5815d0aba9"),
            artifact("worker_trace", "fixtures/target-build/p06-09-table-chart-native-reference-hancom-20260913-03/trace.json.inner.42888.json", 1922, "721a169a9834c114c0f97dad8b4abe356aa1ac7bbedfc8ed84237c03ac10d2df"),
            artifact("progress", "fixtures/target-build/p06-09-table-chart-native-reference-hancom-20260913-03/trace.json.progress.jsonl", 3597, "7d2e73d80be2020e8e8b338617034fe63fef10c278ad2f8886deb2ac03f15764"),
        ],
    },
    {
        "pair": "retry",
        "side": "product",
        "input": {
            "bytes": 15327,
            "sha256": "f9f7baa1f2aa975bd2d7fd63f268176e4cfa6121772e95b1893b9873b05bcf12",
        },
        "artifacts": [
            artifact("saved_hwpx", "fixtures/target-build/p06-09-table-chart-product-hancom-20260913-04/saved.hwpx", 49664, "1f4ec99c2fe5e7b4969b379d2d28adedfd803d249c58256e57b6642704845505"),
            artifact("render_pdf", "fixtures/target-build/p06-09-table-chart-product-hancom-20260913-04/render.pdf", 98655, "f8cd921d81ba96202c876189406593607b36367136eccfccde72511f4a048238"),
            artifact("watchdog_trace", "fixtures/target-build/p06-09-table-chart-product-hancom-20260913-04/trace.json", 2465, "c09998aa2e18d34339d890f678449448f6db15259fedb0c19b627c08e9c72fb7"),
            artifact("worker_trace", "fixtures/target-build/p06-09-table-chart-product-hancom-20260913-04/trace.json.inner.42888.json", 1922, "af1c0f30de674879e1e247828271fd8bcc9ee9faf059abd856209e3c44427a00"),
            artifact("progress", "fixtures/target-build/p06-09-table-chart-product-hancom-20260913-04/trace.json.progress.jsonl", 3597, "999fea9b753e908573a14b3aab4dc74b4e345192b9adc5cc4ad04a51a72be4de"),
        ],
    },
]

LIFECYCLE_RULE = {
    "run_count": 4,
    "artifacts_per_run": 5,
    "progress_events_per_run": 12,
    "actual_hangul_open_save_reopen_pdf_required": True,
    "visible_text_digest_preserved": True,
    "zero_remaining_hwp_processes": True,
    "computer_use_click_or_type_allowed": False,
    "photo_or_user_screenshot_required": False,
}
GATE_DECISION = {
    "required_render_diff": "pass",
    "rollback_or_retry": "pass",
    "TABLE-006": "oracle_verified",
    "automation_runtime": "not_run",
    "release_differential": "not_run",
    "p06_09": "in_progress",
    "p06": "in_progress",
    "product_complete": False,
}
NOT_CLAIMED = {
    "calibration_as_oracle": False,
    "automation_runtime": False,
    "release_differential": False,
    "table_006_green": False,
    "p06_09_complete": False,
    "p06_complete": False,
    "other_pc_or_version": False,
    "production": False,
    "product_complete": False,
}
RASTER = {
    "render_dpi": 150,
    "render_size": [1240, 1753],
    "diff_bbox": [450, 324, 575, 355],
    "differing_pixels": 1980,
    "differing_pixel_ratio": 0.0009108808862226966,
    "mean_absolute_channel_delta": 0.04153708849345822,
    "maximum_channel_delta": 193,
    "outside_allowed_diff_box_pixels": 0,
    "native_ink_bbox": [176, 212, 1057, 690],
    "product_ink_bbox": [176, 212, 1057, 690],
    "native_ink_pixels": 53402,
    "product_ink_pixels": 53845,
    "ink_pixel_delta": 443,
}
OBSERVATION = {
    "state": "pass",
    "pdf_identity_exact": True,
    "word_text_exact": True,
    "word_count": 8,
    "maximum_word_bbox_delta_points": 0.0,
    "hwpx_semantics_exact": True,
    "raster": RASTER,
}
PROGRESS_ORDER = [
    ("preflight", "pass"),
    ("com_create", "running"),
    ("com_create", "pass"),
    ("input_open", "running"),
    ("input_open", "pass"),
    ("save_as", "running"),
    ("save_as", "pass"),
    ("saved_reopen", "running"),
    ("saved_reopen", "pass"),
    ("pdf_export", "running"),
    ("pdf_export", "pass"),
    ("terminal", "pass"),
]


def _reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _read_json(root: Path, relative: str) -> dict[str, Any]:
    data = (root / relative).read_bytes()
    if not data or len(data) > render_diff.MAX_JSON_BYTES:
        raise ValueError("invalid JSON byte count")
    result = json.loads(data.decode("utf-8"), object_pairs_hook=_reject_duplicates)
    if not isinstance(result, dict):
        raise ValueError("JSON root must be an object")
    return result


def _read_progress(root: Path, relative: str) -> list[dict[str, Any]]:
    data = (root / relative).read_bytes()
    if not data or len(data) > render_diff.MAX_JSON_BYTES:
        raise ValueError("invalid progress byte count")
    rows: list[dict[str, Any]] = []
    for raw in data.decode("utf-8").splitlines():
        value = json.loads(raw, object_pairs_hook=_reject_duplicates)
        if not isinstance(value, dict):
            raise ValueError("progress row must be an object")
        rows.append(value)
    return rows


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _profile_digest(profile: dict[str, Any]) -> str:
    canonical = json.dumps(
        profile, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _add(errors: list[str], code: str) -> None:
    if code not in errors:
        errors.append(code)


def _artifact_map(run: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["kind"]: item for item in run["artifacts"]}


def _receipt_pairs() -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for pair in ("qualification", "retry"):
        projected: list[dict[str, Any]] = []
        for run in (item for item in RUNS if item["pair"] == pair):
            for item in run["artifacts"]:
                projected.append(
                    {
                        "role": f"{run['side']}.{item['kind']}",
                        "bytes": item["bytes"],
                        "sha256": item["sha256"],
                    }
                )
        output.append(
            {
                "kind": pair,
                "run_count": 2,
                "artifact_count": 10,
                "artifacts": projected,
            }
        )
    return output


def validate_contract(root: Path, errors: list[str]) -> dict[str, Any] | None:
    try:
        contract = _read_json(root, CONTRACT)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        _add(errors, "contract_json_or_path")
        return None
    expected_keys = {
        "schema_version", "predecessor", "scope", "feature", "target",
        "frozen_profile", "runs", "lifecycle_rule", "source_locks",
        "failure_policy", "migration", "policy", "report", "receipt",
        "gate_decision", "not_claimed",
    }
    if set(contract) != expected_keys:
        _add(errors, "contract_shape")
    exact = {
        "schema_version": "hwpx-agent.table-chart-render-diff-contract/v2",
        "scope": "p06_09_table_006_post_freeze_exact_target_render_diff_qualification_and_retry",
        "feature": FEATURE,
        "target": TARGET,
        "runs": RUNS,
        "lifecycle_rule": LIFECYCLE_RULE,
        "migration": MIGRATION,
        "policy": POLICY,
        "report": REPORT,
        "receipt": RECEIPT,
        "gate_decision": GATE_DECISION,
        "not_claimed": NOT_CLAIMED,
    }
    if any(contract.get(key) != value for key, value in exact.items()):
        _add(errors, "contract_semantics")
    predecessor = {
        "path": PREDECESSOR,
        "sha256": PREDECESSOR_SHA256,
        "state": "immutable_calibration_contract",
    }
    frozen = {
        "contract_path": PREDECESSOR,
        "contract_sha256": PREDECESSOR_SHA256,
        "profile_sha256": PROFILE_SHA256,
        "state": "immutable_post_freeze_profile",
    }
    if contract.get("predecessor") != predecessor:
        _add(errors, "predecessor")
    if contract.get("frozen_profile") != frozen:
        _add(errors, "frozen_profile_ref")
    if contract.get("source_locks") != [
        {"path": path, "sha256": digest} for path, digest in SOURCE_LOCKS.items()
    ]:
        _add(errors, "source_locks")
    failure_policy = contract.get("failure_policy")
    if (
        not isinstance(failure_policy, list)
        or len(failure_policy) != 10
        or len(set(failure_policy)) != 10
    ):
        _add(errors, "failure_policy")
    return contract


def validate_sources(root: Path, errors: list[str]) -> dict[str, Any] | None:
    for relative, expected in SOURCE_LOCKS.items():
        try:
            if _digest(root / relative) != expected:
                _add(errors, "source_lock_digest")
        except OSError:
            _add(errors, "source_lock_path")
    try:
        predecessor = _read_json(root, PREDECESSOR)
        profile = predecessor.get("frozen_profile")
        if (
            predecessor.get("gate_decision", {}).get("required_render_diff") != "not_run"
            or not isinstance(profile, dict)
            or _profile_digest(profile) != PROFILE_SHA256
        ):
            _add(errors, "frozen_profile")
            return None
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        _add(errors, "frozen_profile")
        return None
    markers = {
        MIGRATION: ("immutable calibration record", "oracle_verified", "does not enable"),
        POLICY: ("Two independent", "zero Hwp processes", "release differential remain `not_run`"),
        REPORT: ("Four fresh post-freeze runs", "1,980 differing pixels", "Automation runtime was not exercised"),
    }
    for relative, required in markers.items():
        try:
            text = (root / relative).read_text(encoding="utf-8")
            if any(marker not in text for marker in required):
                _add(errors, "document_marker")
        except (OSError, UnicodeDecodeError):
            _add(errors, "document_path")
    return profile


def validate_artifact_identities(root: Path, errors: list[str]) -> None:
    new_digests: list[str] = []
    for run in RUNS:
        kinds = [item["kind"] for item in run["artifacts"]]
        if kinds != ["saved_hwpx", "render_pdf", "watchdog_trace", "worker_trace", "progress"]:
            _add(errors, "artifact_kinds")
        for item in run["artifacts"]:
            new_digests.append(item["sha256"])
            try:
                identity = render_diff.artifact_identity(root / item["path"])
                if identity != {"bytes": item["bytes"], "sha256": item["sha256"]}:
                    _add(errors, "artifact_identity")
            except (OSError, ValueError):
                _add(errors, "artifact_path")
    if len(new_digests) != 20 or len(set(new_digests)) != 20:
        _add(errors, "artifact_reuse")
    try:
        calibration = _read_json(root, PREDECESSOR).get("calibration_pair", {})
        calibration_digests = {
            value["sha256"] for value in calibration.values() if isinstance(value, dict)
        }
        if set(new_digests) & calibration_digests:
            _add(errors, "calibration_artifact_reuse")
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        _add(errors, "calibration_artifact_reuse")


def _validate_trace(
    root: Path,
    run: dict[str, Any],
    errors: list[str],
) -> None:
    artifacts = _artifact_map(run)
    try:
        watchdog = _read_json(root, artifacts["watchdog_trace"]["path"])
        worker = _read_json(root, artifacts["worker_trace"]["path"])
        progress = _read_progress(root, artifacts["progress"]["path"])
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError, KeyError):
        _add(errors, "trace_json_or_path")
        return
    expected = {
        "target_build": TARGET["build"],
        "executable_sha256": EXECUTABLE_SHA256,
        "input_hwpx_sha256": run["input"]["sha256"],
        "input_hwpx_size": run["input"]["bytes"],
        "output_hwpx_sha256": artifacts["saved_hwpx"]["sha256"],
        "output_hwpx_size": artifacts["saved_hwpx"]["bytes"],
        "render_pdf_sha256": artifacts["render_pdf"]["sha256"],
        "render_pdf_size": artifacts["render_pdf"]["bytes"],
        "input_visible_text_sha256": VISIBLE_TEXT_SHA256,
        "output_visible_text_sha256": VISIBLE_TEXT_SHA256,
        "input_open": "pass",
        "hwp_save_as": "pass",
        "saved_reopen": "pass",
        "pdf_export": "pass",
        "automation_differential": "not_run",
        "state": "pass",
    }
    for trace in (watchdog, worker):
        if any(trace.get(key) != value for key, value in expected.items()):
            _add(errors, "trace_semantics")
        for key in (
            "hwp_process_identity_bound", "window_visible_for_user_access",
            "source_text_preserved", "save_reopen_verified", "actual_hangul_2020",
            "actual_hwpx_open", "actual_hwpx_save_reopen", "actual_pdf_export",
        ):
            if trace.get(key) is not True:
                _add(errors, "trace_semantics")
        for key in (
            "render_visual_verified", "user_attested_visual", "raw_document_text_present",
            "raw_chart_payload_present", "user_document_opened", "external_network_invoked",
            "registry_or_system_setting_changed", "computer_use_click_or_type_invoked",
            "progress_write_failed", "document_close_failed", "hwp_quit_failed",
        ):
            if trace.get(key) is not False:
                _add(errors, "trace_privacy_or_side_effect")
        for key in (
            "failed_phase", "error_code", "exception_type", "exception_hresult",
            "exception_message_sha256",
        ):
            if trace.get(key) is not None:
                _add(errors, "trace_failure_state")
    hwp_process_id = watchdog.get("hwp_process_id")
    if (
        not isinstance(hwp_process_id, int)
        or hwp_process_id <= 0
        or worker.get("hwp_process_id") != hwp_process_id
        or watchdog.get("schema_version")
        != "hwpx-agent.p06-09-hancom-2020-table-chart-product-watchdog/v1"
        or worker.get("schema_version")
        != "hwpx-agent.p06-09-hancom-2020-table-chart-product/v1"
        or watchdog.get("delegated_worker_schema") != worker.get("schema_version")
        or watchdog.get("expected_executable_sha256") != EXECUTABLE_SHA256
    ):
        _add(errors, "trace_binding")
    summary = watchdog.get("watchdog")
    if (
        not isinstance(summary, dict)
        or summary.get("timeout_seconds") != 300
        or summary.get("timed_out") is not False
        or summary.get("child_exit_code") != 0
        or summary.get("output_drained") is not True
        or summary.get("cleaned_process_count") != 0
        or summary.get("cleanup_refused_count") != 0
        or summary.get("cleanup_error_count") != 0
        or summary.get("remaining_hwp_process_count") != 0
        or summary.get("progress_present") is not True
        or summary.get("progress_valid") is not True
        or summary.get("progress_event_count") != 12
        or summary.get("progress_last_phase") != "terminal"
        or summary.get("progress_last_state") != "pass"
        or summary.get("inner_trace_preserved") is not True
    ):
        _add(errors, "watchdog_finalizer")
    if len(progress) != 12:
        _add(errors, "progress_count")
        return
    worker_process_ids: set[int] = set()
    for index, (row, expected_phase) in enumerate(zip(progress, PROGRESS_ORDER, strict=True), 1):
        if (
            row.get("schema_version")
            != "hwpx-agent.p06-09-hancom-2020-table-chart-product-progress/v1"
            or row.get("sequence") != index
            or (row.get("phase"), row.get("state")) != expected_phase
            or row.get("raw_document_text_present") is not False
            or row.get("raw_chart_payload_present") is not False
            or not isinstance(row.get("recorded_at_utc"), str)
            or not row["recorded_at_utc"].endswith("Z")
            or not isinstance(row.get("worker_process_id"), int)
            or row["worker_process_id"] <= 0
        ):
            _add(errors, "progress_semantics")
        else:
            worker_process_ids.add(row["worker_process_id"])
        expected_hwp = None if index <= 2 else hwp_process_id
        if row.get("hwp_process_id") != expected_hwp:
            _add(errors, "progress_process_binding")
    if len(worker_process_ids) != 1:
        _add(errors, "progress_process_binding")


def validate_package_and_pdf(
    root: Path,
    profile: dict[str, Any] | None,
    errors: list[str],
) -> None:
    if profile is None:
        return
    expected_semantics = profile.get("hwpx_semantics")
    for run in RUNS:
        artifacts = _artifact_map(run)
        try:
            semantics = render_diff.chart_package_semantics(
                root / artifacts["saved_hwpx"]["path"]
            )
            if semantics != expected_semantics:
                _add(errors, "artifact_hwpx_semantics")
        except (OSError, ValueError):
            _add(errors, "artifact_hwpx_semantics")
        try:
            pdf = (root / artifacts["render_pdf"]["path"]).read_bytes()
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
        "schema_version", "evidence_id", "scope", "feature", "target", "profile",
        "pairs", "observations", "lifecycle", "privacy", "gate_decision", "not_claimed",
    }
    if set(receipt) != expected_keys:
        _add(errors, "receipt_shape")
    expected_exact = {
        "schema_version": "hwpx-agent.p06-09-table-chart-render-diff-qualification/v2",
        "evidence_id": "p06-table-chart-render-diff-current-2020-qualification02",
        "scope": "post_freeze_exact_target_native_reference_product_pair_and_retry",
        "feature": FEATURE,
        "target": TARGET,
        "profile": {
            "contract_sha256": PREDECESSOR_SHA256,
            "profile_sha256": PROFILE_SHA256,
            "calibration_pair_reused": False,
        },
        "pairs": _receipt_pairs(),
        "observations": {"qualification": OBSERVATION, "retry": OBSERVATION},
        "lifecycle": {
            "run_count": 4,
            "passing_run_count": 4,
            "progress_event_count": 48,
            "actual_hangul_2020": True,
            "actual_hwpx_open": True,
            "actual_hwpx_save_reopen": True,
            "actual_pdf_export": True,
            "source_text_preserved": True,
            "remaining_hwp_process_count": 0,
            "computer_use_click_or_type_invoked": False,
        },
        "gate_decision": GATE_DECISION,
        "not_claimed": NOT_CLAIMED,
    }
    if any(receipt.get(key) != value for key, value in expected_exact.items()):
        _add(errors, "receipt_semantics")
    privacy = receipt.get("privacy")
    if (
        not isinstance(privacy, dict)
        or not privacy
        or any(value is not False for value in privacy.values())
    ):
        _add(errors, "receipt_privacy")
    raw = (root / RECEIPT).read_text(encoding="utf-8")
    if re.search(r"[A-Za-z]:[\\/]", raw) or "fixtures/target-build" in raw:
        _add(errors, "receipt_path_leak")


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    validate_contract(root, errors)
    profile = validate_sources(root, errors)
    validate_artifact_identities(root, errors)
    for run in RUNS:
        _validate_trace(root, run, errors)
    validate_package_and_pdf(root, profile, errors)
    validate_receipt(root, errors)
    errors.sort()
    passed = not errors
    return {
        "schema_version": "hwpx-agent.p06-table-chart-render-diff-contract-validation/v2",
        "state": "pass" if passed else "fail",
        "errors": errors,
        "source_locks": len(SOURCE_LOCKS),
        "runs": len(RUNS),
        "artifacts": sum(len(run["artifacts"]) for run in RUNS),
        "progress_events": len(RUNS) * len(PROGRESS_ORDER),
        "required_render_diff": "pass" if passed else "not_proven",
        "rollback_or_retry": "pass" if passed else "not_proven",
        "TABLE-006": "oracle_verified" if passed else "not_proven",
        "automation_runtime": "not_run",
        "release_differential": "not_run",
        "p06_09": "in_progress",
        "p06": "in_progress",
        "product_complete": False,
    }


if __name__ == "__main__":
    result = validate()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    raise SystemExit(0 if result["state"] == "pass" else 1)
