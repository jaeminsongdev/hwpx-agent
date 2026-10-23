from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
ATTEMPT = ROOT / (
    "implementation/p08/evidence/private/"
    "p08-23-object-surface-20260915-06"
)
TRACE = ATTEMPT / "surface-trace.private.json"
RECEIPT = ATTEMPT / "runtime-receipt.json"
OVERLAY = ROOT / (
    "implementation/p02/evidence/bindings/"
    "p08-object-automation-binding-overlay.2020.v1.json"
)
OUTPUT = ROOT / (
    "implementation/p08/evidence/"
    "p08-23-object-surface.current-2020.v1.json"
)

EXPECTED_HASHES = {
    "binding_overlay_sha256": "8fd12846d8f998018d79ec872abfab18af8fc2d1d8753a6c5801312ce3b9908f",
    "binding_public_contract_sha256": "9a01ba026c858c9ebdad9bbe1762b74295a112faed028aba47906567bc53c52d",
    "fixture_manifest_sha256": "2d8bfcbf9fe32092614c8d2cd27a3eee2c56d123b0ae956b27544b819bf71a4b",
    "progress_sha256": "7fb85250d3384a02f97e3513d16f5b69461245824c6a906152c245b4140b2dfe",
    "private_trace_sha256": "9fe392bcdcbcc67538f8c22de138ed361f8c835d21a7e27cd29d90958ecbc42e",
    "runtime_receipt_sha256": "61a700e7d7cd8789aa5f4b7e6a4c24c3d004071ac743a58e5cd8888503eb50bc",
    "wrapper_sha256": "e92532c70aba40575bea5f46c65266e79bd5cd0f08fbe92c6d902d70a22bcf71",
    "child_sha256": "13d4c73b1256a900ed3664de72c69c6ca2585de99518f96a673a633e6d3e0be4",
}
EXPECTED_TARGET = {
    "product": "Hancom Hangul 2020",
    "build": "11.0.0.9136",
    "architecture": "x86",
    "locale": "ko-KR",
    "executable_sha256": "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce",
}
EXPECTED_EXCLUDED = ("OBJ-003", "OBJ-043")


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
    if _sha256(TRACE) != EXPECTED_HASHES["private_trace_sha256"]:
        raise FinalizationError("private_trace_identity")
    if _sha256(RECEIPT) != EXPECTED_HASHES["runtime_receipt_sha256"]:
        raise FinalizationError("runtime_receipt_identity")
    if _sha256(OVERLAY) != EXPECTED_HASHES["binding_overlay_sha256"]:
        raise FinalizationError("binding_overlay_identity")

    trace = _load(TRACE)
    receipt = _load(RECEIPT)
    overlay = _load(OVERLAY)
    if trace.get("schema_version") != "hwpx-agent.p08-object-surface-batch-private/v1":
        raise FinalizationError("trace_schema")
    if receipt.get("schema_version") != "hwpx-agent.p08-object-surface-wrapper-receipt/v1":
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
    if tuple(trace.get("excluded_known_modal", [])) != EXPECTED_EXCLUDED:
        raise FinalizationError("excluded_set")
    exact_counts = {
        "candidate_count": 40,
        "probed_case_count": 38,
        "completed_case_count": 38,
        "action_case_count": 37,
        "method_case_count": 1,
        "enabled_case_count": 10,
        "action_created_count": 37,
        "set_created_count": 21,
        "get_default_passed_count": 10,
        "method_present_count": 1,
        "action_execute_count": 0,
        "hwp_file_open_count": 0,
        "document_save_count": 0,
    }
    for key, expected in exact_counts.items():
        if trace.get(key) != expected:
            raise FinalizationError(f"trace_count:{key}")
    if trace.get("quit_invoked") is not True or trace.get("error_code") is not None:
        raise FinalizationError("trace_completion")
    cleanup = receipt.get("cleanup")
    if cleanup != {"cleaned": 0, "refused": 0, "errors": 0, "remaining_owned": 0}:
        raise FinalizationError("cleanup")
    configuration = receipt.get("configuration", {})
    if (
        configuration.get("action_execute_allowed") is not False
        or configuration.get("hwp_file_open_allowed") is not False
        or configuration.get("document_save_allowed") is not False
        or receipt.get("timed_out") is not False
        or receipt.get("stalled") is not False
        or receipt.get("child_exit_code") != 0
        or receipt.get("trace_sha256") != EXPECTED_HASHES["private_trace_sha256"]
        or receipt.get("progress_sha256") != EXPECTED_HASHES["progress_sha256"]
    ):
        raise FinalizationError("receipt_boundary")

    routes = {
        item["feature_id"]: item
        for item in overlay.get("routes", [])
        if item.get("state") == "candidate_unverified"
    }
    cases = trace.get("cases")
    if not isinstance(cases, list) or len(cases) != 38:
        raise FinalizationError("case_count")
    expected_features = sorted(set(routes) - set(EXPECTED_EXCLUDED))
    if [item.get("feature_id") for item in cases] != expected_features:
        raise FinalizationError("case_order")

    public_cases: list[dict[str, Any]] = []
    for item in cases:
        feature_id = item.get("feature_id")
        route = routes[feature_id]
        if (
            item.get("capability_id") != route.get("capability_id")
            or item.get("source_kind") != route.get("source_kind")
            or item.get("source_name") != route.get("source_name")
            or item.get("modal_risk") != route.get("modal_risk")
            or item.get("context") != "one_shared_blank_disposable_document"
            or item.get("error_code") is not None
        ):
            raise FinalizationError(f"case_binding:{feature_id}")
        if item.get("source_kind") == "automation_object":
            if item.get("state") != "surface_present_method_not_invoked" or item.get(
                "method_present"
            ) is not True:
                raise FinalizationError(f"method_surface:{feature_id}")
        elif item.get("action_created") is not True or item.get("state") not in {
            "surface_present_enabled",
            "surface_present_disabled_in_blank_context",
        }:
            raise FinalizationError(f"action_surface:{feature_id}")
        public_cases.append(
            {
                "feature_id": feature_id,
                "capability_id": item["capability_id"],
                "surface_kind": item["source_kind"],
                "source_identifier_sha256": _identifier_sha256(item["source_name"]),
                "modal_risk": item["modal_risk"],
                "context": item["context"],
                "surface_state": item["state"],
                "is_action_enable": item["is_action_enable"],
                "action_created": item["action_created"],
                "set_created": item["set_created"],
                "get_default_state": item["get_default_state"],
                "method_present": item["method_present"],
            }
        )

    state_counts = Counter(item["surface_state"] for item in public_cases)
    default_counts = Counter(item["get_default_state"] for item in public_cases)
    document = {
        "schema_version": "hwpx-agent.p08-object-surface-qualification/v1",
        "task": "P08-23",
        "recorded_date": "2026-09-15",
        "attempt_id": "p08-23-object-surface-20260915-06",
        "state": "pass",
        "target": EXPECTED_TARGET,
        "identities": EXPECTED_HASHES,
        "execution": {
            "candidate_count": 40,
            "probed_case_count": 38,
            "excluded_known_modal": list(EXPECTED_EXCLUDED),
            "surface_present_count": 38,
            "action_created_count": 37,
            "method_present_count": 1,
            "enabled_in_blank_context_count": state_counts["surface_present_enabled"],
            "disabled_in_blank_context_count": state_counts[
                "surface_present_disabled_in_blank_context"
            ],
            "set_created_count": 21,
            "get_default_passed_count": default_counts["pass"],
            "get_default_returned_false_count": default_counts["returned_false"],
            "get_default_not_applicable_count": default_counts["not_applicable"],
            "action_execute_count": 0,
            "hwp_file_open_count": 0,
            "document_save_count": 0,
            "remaining_owned_hwp_processes": 0,
            "timed_out": False,
            "stalled": False,
        },
        "predecessor_attempts": [
            {"attempt_id": "p08-23-object-surface-20260915-01", "state": "failed"},
            {"attempt_id": "p08-23-object-surface-20260915-02", "state": "failed"},
            {"attempt_id": "p08-23-object-surface-20260915-03", "state": "failed"},
            {"attempt_id": "p08-23-object-surface-20260915-04", "state": "superseded_pass"},
            {"attempt_id": "p08-23-object-surface-20260915-05", "state": "superseded_pass"},
        ],
        "cases": public_cases,
        "boundaries": {
            "one_shared_blank_disposable_document": True,
            "known_modal_executed": False,
            "candidate_action_executed": False,
            "automation_method_invoked": False,
            "fixture_or_user_document_opened_by_hwp": False,
            "document_saved": False,
            "effect_observed": False,
            "undo_verified": False,
            "differential_run": False,
        },
        "claims": {
            "exact_target_surface_inventory": True,
            "source_candidate_binding": True,
            "automation_runtime_support": False,
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
    if any(route["source_name"] in serialized for route in routes.values()):
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
        text = json.dumps(document, ensure_ascii=False, indent=2) + "\n"
        if args.write:
            OUTPUT.write_text(text, encoding="utf-8", newline="\n")
    except (FinalizationError, OSError) as error:
        print(json.dumps({"state": "fail", "error": str(error)}, sort_keys=True))
        return 1
    print(
        json.dumps(
            {
                "state": "pass",
                "task": "P08-23",
                "attempt_id": document["attempt_id"],
                "probed_case_count": len(document["cases"]),
                "output_written": args.write,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

