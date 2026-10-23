#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
ENGINE = "implementation/p08/tools/run-hancom-2020-object-target-batch-engine.ps1"
WRAPPER = "implementation/p08/tools/run-hancom-2020-object-target-batch.ps1"
BUNDLE_GENERATOR = "crates/hwpx-package/examples/p08_19_object_target_bundle.rs"
INSERT_GENERATOR = "crates/hwpx-package/examples/p08_18_object_insert_target_fixture.rs"
ORACLE = "tools/p08/object_target_oracle.py"
GITIGNORE = ".gitignore"

MANIFEST_SHA256 = "2d8bfcbf9fe32092614c8d2cd27a3eee2c56d123b0ae956b27544b819bf71a4b"
HWP_SHA256 = "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce"
SECURITY_MODULE_SHA256 = "9ac5b97c47ac8aed1e8bca27a3eef39411361d8f68c262509f0c40a8f9d21bb6"
FEATURES = [
    "OBJ-001", "OBJ-002", "OBJ-007", "OBJ-042", "OBJ-015", "OBJ-016",
    "OBJ-017", "OBJ-018", "OBJ-032", "OBJ-033", "OBJ-020", "OBJ-021",
    "OBJ-022", "OBJ-023", "OBJ-024", "OBJ-026", "OBJ-027", "OBJ-028",
    "OBJ-029", "OBJ-034", "OBJ-035", "OBJ-019", "OBJ-025", "OBJ-030",
    "OBJ-043", "OBJ-045", "OBJ-046", "OBJ-047", "OBJ-048", "OBJ-013",
    "OBJ-012", "OBJ-003", "OBJ-014", "OBJ-036",
    "OBJ-037", "OBJ-038", "OBJ-039", "OBJ-040", "OBJ-041", "OBJ-031",
    "OBJ-010",
]


def bounded_file(root: Path, relative: str, maximum: int = 2 * 1024 * 1024) -> Path:
    path = (root / relative).resolve()
    path.relative_to(root.resolve())
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= maximum:
        raise ValueError(relative)
    return path


def read(root: Path, relative: str) -> str:
    return bounded_file(root, relative).read_text(encoding="utf-8")


def normalized_sha256(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def expected_feature_block(engine: str) -> list[str]:
    match = re.search(
        r"\$expectedFeatures\s*=\s*@\((?P<body>.*?)\)\s*\n"
        r"\$representativeRetryFeatures",
        engine,
        re.DOTALL,
    )
    if not match:
        return []
    return re.findall(r"'(?P<feature>OBJ-[0-9]{3})'", match.group("body"))


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        engine_path = bounded_file(root, ENGINE)
        wrapper_path = bounded_file(root, WRAPPER)
        engine = engine_path.read_text(encoding="utf-8")
        wrapper = wrapper_path.read_text(encoding="utf-8")
        bundle = read(root, BUNDLE_GENERATOR)
        insert = read(root, INSERT_GENERATOR)
        oracle_path = bounded_file(root, ORACLE)
        oracle = oracle_path.read_text(encoding="utf-8")
        gitignore = read(root, GITIGNORE)
    except (OSError, UnicodeDecodeError, ValueError):
        return result(["bounded_source_files"], None, None, None)

    if expected_feature_block(engine) != FEATURES:
        errors.append("expected_feature_order")
    if engine.count("New-Object -ComObject $ProgId") != 2:
        errors.append("bounded_com_creation_paths")
    if engine.count(".Quit()") != 3:
        errors.append("bounded_hwp_quit_paths")
    active_before_open = re.findall(
        r"\$document\s*=\s*\$Documents\.Add\(\$false\).*?"
        r"\$document\.SetActive_XHwpDocument\(\).*?\$document\.Open\(",
        engine,
        re.DOTALL,
    )
    if len(active_before_open) != 2:
        errors.append("active_document_before_open")

    engine_required = {
        MANIFEST_SHA256: "manifest_pin",
        HWP_SHA256: "hwp_identity_pin",
        SECURITY_MODULE_SHA256: "security_module_pin",
        "HWPFrame.HwpObject.2": "exact_progid",
        "11.0.0.9136": "exact_build",
        "FilePathCheckDLL": "security_module_type",
        "FilePathCheckerModuleExample": "security_module_name",
        "Registry32": "registry_view",
        "windows_powershell_x86_sta": "x86_sta_client",
        "single_hwp_process_with_fail_closed_restart_for_41_primary_plus_bounded_retry_cases": "session_strategy",
        "effective_completed_case_count": "retry_recovery_accounting",
        "session_restart_count": "failed_session_restart_accounting",
        "scheduled_session_restart_count": "scheduled_session_restart_accounting",
        "retry_session_restart_count": "retry_session_restart_accounting",
        "retry_session_restart": "fresh_retry_session",
        "(($index + 1) % 12) -eq 0": "bounded_twelve_case_sessions",
        "retry_all_primary_failures_plus_OBJ-002_OBJ-024_OBJ-010_from_immutable_source": "retry_policy",
        "@('OBJ-002', 'OBJ-024', 'OBJ-010')": "representative_retry_set",
        "$seenCaseIds = @{}": "stable_case_id_set",
        "$seenCaseIds.ContainsKey($caseId)": "unique_case_id_guard",
        "^P08-19-C(0[1-9]|[1-3][0-9]|4[01])$": "bounded_case_id_guard",
        "$index -eq 0 -and $caseFailed -and": "first_open_fail_fast_guard",
        "first_fixture_open_failed": "first_open_fail_closed_state",
        "_FIRST_CASE_OPEN_GATE_FAILED": "first_open_fail_fast_error",
        "export_before_pdf": "baseline_pdf_phase",
        "save_as_hwpx": "save_phase",
        "reopen_output": "reopen_phase",
        "export_after_pdf": "readback_pdf_phase",
        "GetTextFile('UNICODE', '')": "native_text_readback",
        "input_unchanged": "immutable_input_check",
        "raw_document_text_present = $false": "raw_text_exclusion",
        "user_document_scanned = $false": "user_document_exclusion",
        "external_network_invoked = $false": "network_exclusion",
        "registry_or_system_setting_changed = $false": "setting_change_exclusion",
        "computer_use_click_or_type_invoked = $false": "computer_use_exclusion",
    }
    for needle, label in engine_required.items():
        if needle not in engine:
            errors.append(label)

    wrapper_required = {
        MANIFEST_SHA256: "wrapper_manifest_pin",
        HWP_SHA256: "wrapper_hwp_pin",
        "SpecialFolder]::SystemX86": "wrapper_x86_host",
        "'-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-STA'":
            "wrapper_sta_launch",
        "CreateNoWindow = $true": "hidden_worker",
        "Stop-OwnedHancomProcesses": "owned_process_cleanup",
        "stalled_hwp_recovery_count": "progress_stall_watchdog",
        "inactivityLimitSeconds": "bounded_inactivity_timeout",
        "$progressChangeCount -le 3": "first_open_approval_grace_bound",
        "{ 180 } else { 30 }": "first_open_then_normal_stall_timeout",
        "CreationDate": "cleanup_creation_time_bound",
        "-Automation\\s+-Embedding": "cleanup_automation_bound",
        "if (-not $child.HasExited)": "interrupted_worker_cleanup",
        "runtime-receipt.json": "runtime_receipt",
        "stdout_sha256": "bounded_stdout_projection",
        "stderr_sha256": "bounded_stderr_projection",
        "engine_stderr_error_code": "sanitized_engine_error_projection",
        "@($engineValue.cases).Count -le 41": "failed_trace_case_bound",
        "$engineTraceCaseShapeValid": "state_aware_trace_validation",
        "raw_document_text_present = $false": "wrapper_raw_text_exclusion",
        "computer_use_click_or_type_invoked = $false": "wrapper_computer_use_exclusion",
    }
    for needle, label in wrapper_required.items():
        if needle not in wrapper:
            errors.append(label)

    oracle_required = {
        HWP_SHA256: "oracle_hwp_identity_pin",
        "EXPECTED_CASES = 41": "oracle_case_count",
        "REPRESENTATIVE_RETRIES = {\"OBJ-002\", \"OBJ-024\", \"OBJ-010\"}":
            "oracle_retry_set",
        "ambiguous_zip_member": "oracle_windows_zip_alias_guard",
        "source.tag != target.tag": "oracle_namespace_guard",
        "object_structure(source_root) != object_structure(target_root)":
            "oracle_object_tree_guard",
        "source_projection != target_projection": "oracle_resource_reference_guard",
        "source_inventory != target_inventory": "oracle_resource_inventory_guard",
        "ImageChops.difference": "oracle_exact_render_guard",
        '"unchanged_region_changed_pixels_max": 0': "oracle_zero_pixel_threshold",
        'with output.open("xb")': "oracle_atomic_no_overwrite_output",
    }
    for needle, label in oracle_required.items():
        if needle not in oracle:
            errors.append(label)
    if ".extractall(" in oracle or ".extract(" in oracle:
        errors.append("oracle_zip_extraction_forbidden")

    forbidden_engine = {
        "Remove-Item": "engine_delete",
        "Stop-Process": "engine_process_kill",
        "SetMessageBoxMode": "dialog_suppression",
        "SendKeys": "synthetic_input",
        "mouse_event": "synthetic_mouse",
        "Invoke-WebRequest": "network_call",
    }
    for needle, label in forbidden_engine.items():
        if needle in engine:
            errors.append(label)

    if "/implementation/p08/evidence/private/" not in gitignore.replace("\\", "/"):
        errors.append("private_evidence_ignore")
    if (
        "hwpx-agent.p08-19-object-target-bundle/v1" not in bundle
        or "direct_feature_count: manifest_cases.len()" not in bundle
        or "cases.extend(p08_19_support::canvas::cases" not in bundle
        or "actual_hangul_2020" not in bundle
        or 'rollback_or_retry: "not_run"' not in bundle
    ):
        errors.append("complete_bundle_generator_contract")
    if (
        "hwpx-agent.p08-18-object-insert-target-fixture/v1" not in insert
        or "PreservingWriter" not in insert
        or "AtomicPackagePublisher" not in insert
    ):
        errors.append("insert_bundle_generator_contract")

    return result(
        errors,
        normalized_sha256(engine_path),
        normalized_sha256(wrapper_path),
        normalized_sha256(oracle_path),
    )


def result(
    errors: list[str],
    engine_sha256: str | None,
    wrapper_sha256: str | None,
    oracle_sha256: str | None,
) -> dict[str, Any]:
    return {
        "schema_version": "hwpx-agent.p08-object-target-batch-tooling-validation/v1",
        "state": "pass" if not errors else "fail",
        "errors": sorted(set(errors)),
        "direct_feature_count": len(FEATURES),
        "representative_retry_count": 3,
        "bounded_session_restart": not errors or "bounded_com_creation_paths" not in errors,
        "engine_normalized_sha256": engine_sha256,
        "wrapper_normalized_sha256": wrapper_sha256,
        "oracle_normalized_sha256": oracle_sha256,
        "actual_hangul_2020": "not_run",
        "p08_complete": False,
    }


def main() -> int:
    value = validate()
    if value["state"] == "pass":
        print(
            "P08_OBJECT_TARGET_BATCH_TOOLING_PASS "
            f"features={value['direct_feature_count']} "
            f"retry={value['representative_retry_count']} "
            "target=not_run p08_complete=false"
        )
        return 0
    print("P08_OBJECT_TARGET_BATCH_TOOLING_FAIL " + ",".join(value["errors"]), file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
