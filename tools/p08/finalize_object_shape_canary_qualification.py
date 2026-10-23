from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
ATTEMPT = ROOT / (
    "implementation/p08/evidence/private/"
    "p08-24-object-shape-canary-20260915-05"
)
TRACE = ATTEMPT / "canary-trace.private.json"
RECEIPT = ATTEMPT / "runtime-receipt.json"
OVERLAY = ROOT / (
    "implementation/p02/evidence/bindings/"
    "p08-object-automation-binding-overlay.2020.v1.json"
)
WRAPPER = ROOT / "implementation/p08/tools/run-hancom-2020-object-shape-canary.ps1"
CHILD = ROOT / "implementation/p08/tools/run-hancom-2020-object-shape-canary-child.ps1"
OUTPUT = ROOT / (
    "implementation/p08/evidence/"
    "p08-24-object-shape-canary.current-2020.v1.json"
)

FEATURE_ORDER = ("OBJ-026", "OBJ-033", "OBJ-038", "OBJ-045", "OBJ-013")
EXPECTED_HASHES = {
    "binding_overlay_sha256": "8fd12846d8f998018d79ec872abfab18af8fc2d1d8753a6c5801312ce3b9908f",
    "progress_sha256": "21ef4916ac2b76e7c29d8e350e77932250cf9ce3eb2a8e7057894b38fc9653ba",
    "private_trace_sha256": "c327552c0077dbce523f2388fe18ea8d98380a9dd9d8778b18fc520658962628",
    "runtime_receipt_sha256": "3412306a0de52692b01c368e60734745049c258a2aa7439df34f3565614197b3",
    "wrapper_sha256": "0c858f7515330be5d14a815c46efe6d18e1515e4acad8b8c232ddfdcfcceaf4f",
    "child_sha256": "ec56a085af9684076543299e7c5ee6b6da1ab5aacc49ea3b744f1144519c0f89",
}
EXPECTED_TARGET = {
    "product": "Hancom Hangul 2020",
    "build": "11.0.0.9136",
    "architecture": "x86",
    "locale": "ko-KR",
    "executable_sha256": "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce",
}


class FinalizationError(ValueError):
    pass


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _identifier_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise FinalizationError(f"duplicate_json_key:{key}")
        value[key] = item
    return value


def _load(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    if not data or len(data) > 2 * 1024 * 1024:
        raise FinalizationError(f"input_size:{path.name}")
    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise FinalizationError(f"input_json:{path.name}") from error
    if not isinstance(value, dict):
        raise FinalizationError(f"input_shape:{path.name}")
    return value


def build() -> dict[str, Any]:
    identity_paths = {
        "binding_overlay_sha256": OVERLAY,
        "progress_sha256": ATTEMPT / "progress.jsonl",
        "private_trace_sha256": TRACE,
        "runtime_receipt_sha256": RECEIPT,
        "wrapper_sha256": WRAPPER,
        "child_sha256": CHILD,
    }
    for key, path in identity_paths.items():
        if _sha256(path) != EXPECTED_HASHES[key]:
            raise FinalizationError(f"source_identity:{key}")

    trace = _load(TRACE)
    receipt = _load(RECEIPT)
    overlay = _load(OVERLAY)
    if trace.get("schema_version") != "hwpx-agent.p08-object-shape-canary-private/v1":
        raise FinalizationError("trace_schema")
    if receipt.get("schema_version") != "hwpx-agent.p08-object-shape-canary-wrapper-receipt/v1":
        raise FinalizationError("receipt_schema")
    if overlay.get("schema_version") != "hwpx-agent.p08-object-automation-binding-overlay/v1":
        raise FinalizationError("overlay_schema")
    if trace.get("state") != "pass" or receipt.get("state") != "pass":
        raise FinalizationError("execution_state")
    if trace.get("target_build") != EXPECTED_TARGET["build"] or trace.get(
        "target_executable_sha256"
    ) != EXPECTED_TARGET["executable_sha256"]:
        raise FinalizationError("target_identity")
    if trace.get("hwp_process_identity_verified") is not True:
        raise FinalizationError("process_identity")
    if tuple(trace.get("feature_order", [])) != FEATURE_ORDER:
        raise FinalizationError("feature_order")
    exact_counts = {
        "setup_rectangle_count": 2,
        "completed_case_count": 5,
        "candidate_execute_count": 5,
        "effect_observed_count": 5,
        "undo_verified_count": 5,
        "hwp_file_open_count": 0,
        "document_save_count": 0,
    }
    for key, expected in exact_counts.items():
        if trace.get(key) != expected:
            raise FinalizationError(f"trace_count:{key}")
    if (
        trace.get("quit_invoked") is not True
        or trace.get("error_code") is not None
        or trace.get("external_network_invoked") is not False
        or trace.get("registry_or_system_setting_changed") is not False
        or trace.get("computer_use_click_or_type_invoked") is not False
    ):
        raise FinalizationError("trace_boundary")
    if receipt.get("cleanup") != {
        "cleaned": 0,
        "refused": 0,
        "errors": 0,
        "remaining_owned": 0,
    }:
        raise FinalizationError("cleanup")
    configuration = receipt.get("configuration", {})
    if (
        configuration.get("feature_count") != 5
        or tuple(configuration.get("feature_ids", [])) != FEATURE_ORDER
        or configuration.get("hwp_file_open_allowed") is not False
        or configuration.get("document_save_allowed") is not False
        or configuration.get("candidate_execute_allowed") is not True
        or configuration.get("exact_undo_required") is not True
        or receipt.get("timed_out") is not False
        or receipt.get("stalled") is not False
        or receipt.get("child_exit_code") != 0
        or receipt.get("trace_sha256") != EXPECTED_HASHES["private_trace_sha256"]
        or receipt.get("progress_sha256") != EXPECTED_HASHES["progress_sha256"]
    ):
        raise FinalizationError("receipt_boundary")

    routes = {item.get("feature_id"): item for item in overlay.get("routes", [])}
    cases = trace.get("cases")
    if not isinstance(cases, list) or len(cases) != 5:
        raise FinalizationError("case_count")
    if tuple(item.get("feature_id") for item in cases) != FEATURE_ORDER:
        raise FinalizationError("case_order")

    public_cases: list[dict[str, Any]] = []
    for item in cases:
        feature_id = item["feature_id"]
        route = routes.get(feature_id)
        if not isinstance(route, dict):
            raise FinalizationError(f"missing_route:{feature_id}")
        if (
            item.get("capability_id") != route.get("capability_id")
            or item.get("source_name") != route.get("source_name")
            or route.get("source_kind") != "action_table"
            or route.get("state") != "candidate_unverified"
            or route.get("routing_enabled") is not False
            or route.get("modal_risk") != "none_expected"
            or item.get("context")
            != "two_rectangle_unsaved_blank_document_first_shape_selected"
            or item.get("state") != "pass"
            or item.get("is_action_enable") is not True
            or item.get("effect_observed") is not True
            or item.get("undo_verified") is not True
            or item.get("error_code") is not None
        ):
            raise FinalizationError(f"case_binding:{feature_id}")
        if item.get("before_sha256") != item.get("undo_sha256") or item.get(
            "before_sha256"
        ) == item.get("after_sha256"):
            raise FinalizationError(f"semantic_snapshot:{feature_id}")
        if feature_id == "OBJ-038":
            if item.get("context_setup_undo_verified") is not True:
                raise FinalizationError("z_order_context_undo")
        elif item.get("context_setup_undo_verified") is not None:
            raise FinalizationError(f"unexpected_context_undo:{feature_id}")
        if feature_id == "OBJ-026":
            if (
                item.get("undo_raw_exact") is not False
                or item.get("before_normalization_count") != 0
                or item.get("after_normalization_count") != 1
                or item.get("undo_normalization_count") != 1
            ):
                raise FinalizationError("shadow_normalization")
        elif (
            item.get("undo_raw_exact") is not True
            or item.get("before_normalization_count") != 1
            or item.get("after_normalization_count") != 1
            or item.get("undo_normalization_count") != 1
        ):
            raise FinalizationError(f"raw_undo:{feature_id}")
        public_cases.append(
            {
                "feature_id": feature_id,
                "capability_id": item["capability_id"],
                "source_identifier_sha256": _identifier_sha256(item["source_name"]),
                "context": item["context"],
                "is_action_enable": item["is_action_enable"],
                "execute_return_advisory": item["execute_return"],
                "effect_observed": item["effect_observed"],
                "undo_semantic_verified": item["undo_verified"],
                "undo_raw_exact": item["undo_raw_exact"],
                "empty_name_normalization_counts": {
                    "before": item["before_normalization_count"],
                    "after": item["after_normalization_count"],
                    "undo": item["undo_normalization_count"],
                },
                "context_setup_undo_verified": item["context_setup_undo_verified"],
                "state": item["state"],
            }
        )

    document = {
        "schema_version": "hwpx-agent.p08-object-shape-canary-qualification/v1",
        "task": "P08-24",
        "recorded_date": "2026-09-15",
        "attempt_id": "p08-24-object-shape-canary-20260915-05",
        "state": "pass",
        "target": EXPECTED_TARGET,
        "identities": EXPECTED_HASHES,
        "execution": {
            "canary_case_count": 5,
            "candidate_execute_count": 5,
            "effect_observed_count": 5,
            "semantic_undo_verified_count": 5,
            "raw_undo_exact_count": 4,
            "serializer_default_normalized_count": 1,
            "context_setup_undo_verified_count": 1,
            "hwp_file_open_count": 0,
            "document_save_count": 0,
            "remaining_owned_hwp_processes": 0,
            "timed_out": False,
            "stalled": False,
        },
        "normalization": {
            "id": "hwpml2x-drawtext-empty-name-default/v1",
            "scope": "empty_Name_attribute_on_DRAWTEXT_only",
            "non_empty_names_remain_hash_significant": True,
            "geometry_style_text_remain_hash_significant": True,
            "raw_mismatch_preserved": True,
        },
        "predecessor_attempts": [
            {"attempt_id": "p08-24-object-shape-canary-20260915-01", "state": "failed"},
            {"attempt_id": "p08-24-object-shape-canary-20260915-02", "state": "failed"},
            {"attempt_id": "p08-24-object-shape-canary-20260915-03", "state": "diagnostic_failed"},
            {"attempt_id": "p08-24-object-shape-canary-20260915-04", "state": "superseded_single_case_pass"},
        ],
        "cases": public_cases,
        "boundaries": {
            "one_session_one_unsaved_disposable_document": True,
            "setup_rectangle_count": 2,
            "known_modal_executed": False,
            "fixture_or_user_document_opened_by_hwp": False,
            "document_saved": False,
            "candidate_action_executed": True,
            "effect_observed": True,
            "undo_semantic_verified": True,
            "routing_enabled": False,
            "differential_run": False,
        },
        "claims": {
            "exact_target_selected_object_canary": True,
            "qualified_canary_case_count": 5,
            "automation_runtime_support_for_all_candidates": False,
            "routing_enabled": False,
            "differential": False,
            "required_matrix_green": False,
            "p08_complete": False,
            "production_ready": False,
            "product_complete": False,
        },
        "privacy": {
            "absolute_private_paths_present": False,
            "raw_action_identifiers_present": False,
            "raw_parameter_identifiers_present": False,
            "document_content_present": False,
            "user_document_scanned": False,
            "external_network_invoked": False,
            "registry_or_system_setting_changed": False,
            "computer_use_click_or_type_invoked": False,
        },
    }
    serialized = json.dumps(document, ensure_ascii=False, sort_keys=True)
    if any(
        route["source_name"] in serialized
        for route in routes.values()
        if isinstance(route.get("source_name"), str)
    ):
        raise FinalizationError("raw_source_identifier_leak")
    if ":\\" in serialized or "D:/" in serialized or "D:\\" in serialized:
        raise FinalizationError("absolute_path_leak")
    return document


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    try:
        document = build()
        if args.write:
            OUTPUT.write_text(
                json.dumps(document, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )
    except (FinalizationError, OSError) as error:
        print(json.dumps({"state": "fail", "error": str(error)}, sort_keys=True))
        return 1
    print(
        json.dumps(
            {
                "state": "pass",
                "task": "P08-24",
                "attempt_id": document["attempt_id"],
                "qualified_canary_case_count": len(document["cases"]),
                "output_written": args.write,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
