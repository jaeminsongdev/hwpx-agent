#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.p07 import validate_eqedit_adapter_contract
from tools.p07 import validate_equation_automation_contract
from tools.p07 import validate_equation_corpus_contract
from tools.p07 import validate_equation_differential_contract
from tools.p07 import validate_equation_editor_smoke_contract
from tools.p07 import validate_equation_hwpx_contract
from tools.p07 import validate_equation_layout_contract
from tools.p07 import validate_latex_adapter_contract
from tools.p07 import validate_math_ast_contract
from tools.p07 import validate_mathml_adapter_contract


CONTRACT = "protocol/private/p07-phase-gate-v1.json"
MIGRATION = "protocol/migrations/p07-phase-gate-v0-to-v1.md"
REPORT = "implementation/p07/P07_GATE_REPORT.md"
PROFILE = "hwpx-agent.equation-layout.hangul-2020-11.0.0.9136-x86-ko-KR/v1"
DIGEST = re.compile(r"^[0-9a-f]{64}$")

SOURCES = {
    "WORK_BREAKDOWN_STRUCTURE.csv": "3a115b34b4bb57d50ac3899aee7d8155e69a6290c524b976e9b65b848efad444",
    "docs/09_roadmap/P07_native_equation_engine.md": "5e2f87f8b568cc60023b9571ddace660f10189eefa6fa6f348be94ac54ea803f",
    "tools/p07/validate_math_ast_contract.py": "2a08c5b87878b0dc69f30731eb51f91e221e3920ad79f2da48e517cf02847a18",
    "tools/p07/validate_latex_adapter_contract.py": "033e6801fd35f62d7f3e229650d4d4e16631df18ac49bcdc1f4f0422c73b45e2",
    "tools/p07/validate_mathml_adapter_contract.py": "4d95b5e497ee7e25b125dc11f59df4873ec16bce3363c1cfc090a3ead38f87b7",
    "tools/p07/validate_eqedit_adapter_contract.py": "7aae97a2e1a0fd4f0dd5d4b92f55429b133426b7bcc3ccc0d947e103e87d733b",
    "tools/p07/validate_equation_hwpx_contract.py": "76d49b0b33f892a7e7e5166f5b06eb0f007b1ba258841425560d37d4c07b2154",
    "tools/p07/validate_equation_automation_contract.py": "9073593f558bcf3cde9b454627928046b4baa3eb74e05552d8556edaa7c820ca",
    "tools/p07/validate_equation_layout_contract.py": "f15fe62cb5d555c9f079adb308375285d1f2fa12a8479111b4efb62ba0790d88",
    "tools/p07/validate_equation_corpus_contract.py": "476e399e37ad52b3b96f73f482ad71e202c1b52897b78c4500915c95965323d0",
    "tools/p07/validate_equation_editor_smoke_contract.py": "a1c858ccee4a67a04f230f84e69aaa43dc4534f2bdc74a0df7942c06b2e6d785",
    "tools/p07/validate_equation_differential_contract.py": "f5fadee20a644617c808a49464c87e9b7302d999a00382077cecfe5f86de6950",
}

VALIDATORS: dict[str, Callable[[Path], dict[str, Any]]] = {
    "P07-01": validate_math_ast_contract.validate,
    "P07-02": validate_latex_adapter_contract.validate,
    "P07-03": validate_mathml_adapter_contract.validate,
    "P07-04": validate_eqedit_adapter_contract.validate,
    "P07-05": validate_equation_hwpx_contract.validate,
    "P07-06": validate_equation_automation_contract.validate,
    "P07-07": validate_equation_layout_contract.validate,
    "P07-08": validate_equation_corpus_contract.validate,
    "P07-09": validate_equation_editor_smoke_contract.validate,
    "differential": validate_equation_differential_contract.validate,
}

REQUIRED_RESULTS = [
    {"id": "P07-01", "required": {"task": "P07-01", "state": "pass", "direct_stage": "unit_passed", "actual_hangul": False}},
    {"id": "P07-02", "required": {"task": "P07-02", "state": "pass", "direct_stage": "unit_passed", "actual_hangul": False}},
    {"id": "P07-03", "required": {"task": "P07-03", "state": "pass", "direct_stage": "unit_passed", "actual_hangul": False}},
    {"id": "P07-04", "required": {"task": "P07-04", "state": "pass", "direct_stage": "unit_passed", "installed_source_qualified": True}},
    {"id": "P07-05", "required": {"task": "P07-05", "state": "pass", "direct_stage": "oracle_verified", "actual_hangul": True, "target_evidence_verified": True}},
    {"id": "P07-06", "required": {"task": "P07-06", "state": "pass", "direct_stage": "oracle_verified", "actual_hangul": True, "target_evidence_verified": True}},
    {"id": "P07-07", "required": {"task": "P07-07", "state": "pass", "direct_stage": "target_passed", "actual_hangul": True, "render": True, "target_qualification": "pass", "manual_review": "user_attested", "verified_estimator_active": False, "unknown_shapes": "render_required"}},
    {"id": "P07-08", "required": {"task": "P07-08", "state": "pass", "direct_stage": "target_passed", "actual_hangul": True, "save_reopen": True, "tier_b_target": "pass"}},
    {"id": "P07-09", "required": {"task": "P07-09", "state": "pass", "direct_stage": "target_passed", "actual_hangul": True, "save_reopen": True, "editor_target": "pass"}},
    {"id": "differential", "required": {"task": "P07-GATE", "state": "pass", "differential": "pass", "matched_cases": 8, "actual_hangul": True}},
]


class DuplicateKey(ValueError):
    pass


def duplicate_guard(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise DuplicateKey(key)
        value[key] = item
    return value


def bounded_file(root: Path, relative: str, maximum: int = 16 * 1024 * 1024) -> Path:
    path = (root / relative).resolve()
    path.relative_to(root.resolve())
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= maximum:
        raise ValueError("invalid bounded file")
    return path


def load_json(root: Path, relative: str) -> Any:
    return json.loads(
        bounded_file(root, relative).read_bytes(), object_pairs_hook=duplicate_guard
    )


def text_digest(path: Path) -> str:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(text.encode()).hexdigest()


def collect_constituent_results(root: Path = ROOT) -> dict[str, dict[str, Any]]:
    return {identifier: validator(root) for identifier, validator in VALIDATORS.items()}


def required_subset_matches(value: Any, required: Any) -> bool:
    if isinstance(required, dict):
        return isinstance(value, dict) and all(
            key in value and required_subset_matches(value[key], item)
            for key, item in required.items()
        )
    if isinstance(required, list):
        return isinstance(value, list) and len(value) == len(required) and all(
            required_subset_matches(actual, expected)
            for actual, expected in zip(value, required)
        )
    return value == required


def task_is_closed(identifier: str, value: dict[str, Any]) -> bool:
    if value.get("state") != "pass":
        return False
    if identifier in {"P07-01", "P07-02", "P07-03", "P07-04"}:
        return value.get("direct_stage") == "unit_passed"
    if identifier in {"P07-05", "P07-06"}:
        return value.get("direct_stage") == "oracle_verified" and value.get("actual_hangul") is True
    if identifier == "P07-07":
        return (
            value.get("target_qualification") == "pass"
            and value.get("actual_hangul") is True
            and value.get("render") is True
            and value.get("manual_review") == "user_attested"
        )
    if identifier == "P07-08":
        return value.get("tier_b_target") == "pass" and value.get("save_reopen") is True
    if identifier == "P07-09":
        return value.get("editor_target") == "pass" and value.get("save_reopen") is True
    raise ValueError(f"not a task validator: {identifier}")


def derive_phase(results: dict[str, dict[str, Any]]) -> dict[str, Any]:
    closed = sum(task_is_closed(identifier, results.get(identifier, {})) for identifier in VALIDATORS if identifier != "differential")
    differential = results.get("differential", {})
    differential_pass = (
        differential.get("state") == "pass"
        and differential.get("differential") == "pass"
        and differential.get("matched_cases") == 8
    )
    phase_pass = closed == 9 and differential_pass
    return {
        "validator_count": len(VALIDATORS),
        "task_count": 9,
        "closed_task_count": closed,
        "differential_case_count": 8 if differential_pass else 0,
        "manual_review": "user_attested" if task_is_closed("P07-07", results.get("P07-07", {})) else "not_run",
        "p07": "pass_scoped_current_pc_hangul_2020_native_equation" if phase_pass else "in_progress",
        "p08_authorization": "authorized_current_pc_local_only" if phase_pass else "blocked_by_p07_07_user_attested_manual_review",
    }


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        contract = load_json(root, CONTRACT)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return result(
            ["contract_json_or_path"], 0, 0, 0, "not_proven", "not_proven",
            "not_authorized",
        )

    exact = {
        "schema_version": "hwpx-agent.p07-phase-gate-contract/v1",
        "profile_id": PROFILE,
        "phase": "P07",
        "scope": "current_pc_hangul_2020_bounded_native_equation_engine",
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "migration": MIGRATION,
        "report": REPORT,
        "required_validator_results": REQUIRED_RESULTS,
        "gate_policy": {
            "required_task_count": 9,
            "required_validator_count": 10,
            "required_differential_cases": 8,
            "p07_07_requires_actual_hangul": True,
            "p07_07_requires_render": True,
            "p07_07_requires_user_attested_manual_review": True,
            "unknown_layout_shapes_require_render": True,
            "verified_general_estimator_required": False,
        },
        "failure_policy": [
            "malformed_duplicate_unknown_oversized_or_untrusted_contract_rejected",
            "source_or_constituent_validator_drift_rejected",
            "task_validator_failure_or_required_result_mismatch_rejected",
            "phase_pass_rejected_until_all_nine_tasks_and_differential_pass",
            "automation_or_structural_raster_cannot_replace_user_attested_visual_review",
            "general_estimator_is_not_promoted_when_fit_thresholds_fail",
            "other_version_production_or_product_overclaim_rejected",
        ],
        "not_claimed": {
            "general_verified_layout_estimator": False,
            "arbitrary_equation_or_document_compatibility": False,
            "other_hangul_versions": False,
            "production_ready": False,
            "product_complete": False,
        },
        "gate_decision": {
            "validator_contracts": "pass_10_of_10",
            "tasks_closed": "9_of_9",
            "differential": "pass_8_of_8",
            "manual_review": "user_attested",
            "p07": "pass_scoped_current_pc_hangul_2020_native_equation",
            "p08_authorization": "authorized_current_pc_local_only",
        },
    }
    for key, expected in exact.items():
        if contract.get(key) != expected:
            errors.append(key)
    if set(contract) != {*exact, "source_locks"}:
        errors.append("contract_keys")

    source_count = validate_sources(root, contract.get("source_locks"), errors)
    try:
        values = collect_constituent_results(root)
    except Exception:
        errors.append("constituent_validator_exception")
        values = {}
    if set(values) != set(VALIDATORS):
        errors.append("constituent_validator_set")
    for item in REQUIRED_RESULTS:
        identifier = item["id"]
        if not required_subset_matches(values.get(identifier), item["required"]):
            errors.append(f"constituent_result_{identifier}")

    try:
        phase = derive_phase(values)
    except (KeyError, TypeError, ValueError):
        errors.append("phase_derivation")
        phase = {
            "closed_task_count": 0,
            "differential_case_count": 0,
            "p07": "not_proven",
            "p08_authorization": "not_authorized",
        }
    if phase.get("closed_task_count") != 9:
        errors.append("closed_task_count")
    if phase.get("differential_case_count") != 8:
        errors.append("differential_case_count")
    if phase.get("manual_review") != "user_attested":
        errors.append("manual_review")
    if phase.get("p07") != "pass_scoped_current_pc_hangul_2020_native_equation":
        errors.append("phase_decision")
    if phase.get("p08_authorization") != "authorized_current_pc_local_only":
        errors.append("p08_authorization")
    validate_documents(root, errors)
    return result(
        errors,
        source_count,
        sum(value.get("state") == "pass" for value in values.values()),
        int(phase.get("closed_task_count", 0)),
        str(phase.get("manual_review", "not_proven")),
        str(phase.get("p07", "not_proven")),
        str(phase.get("p08_authorization", "not_authorized")),
    )


def validate_sources(root: Path, value: Any, errors: list[str]) -> int:
    if not isinstance(value, list):
        errors.append("source_locks_shape")
        return 0
    declared: dict[str, str] = {}
    for item in value:
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            errors.append("source_lock_shape")
            continue
        relative, expected = item.get("path"), item.get("sha256")
        if (
            not isinstance(relative, str)
            or relative in declared
            or not isinstance(expected, str)
            or not DIGEST.fullmatch(expected)
        ):
            errors.append("source_lock_identity")
            continue
        declared[relative] = expected
        try:
            if text_digest(bounded_file(root, relative)) != expected:
                errors.append("source_lock_digest")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("source_lock_path")
    if declared != SOURCES:
        errors.append("source_lock_paths_exact")
    return len(declared)


def validate_documents(root: Path, errors: list[str]) -> None:
    required = {
        MIGRATION: ("There is no stored P07 phase Gate v0", "MUST NOT", "user_attested"),
        REPORT: ("Overall state: `pass_scoped_current_pc_hangul_2020_native_equation`", "9/9", "P07-07", "P08 authorization"),
    }
    for relative, markers in required.items():
        try:
            text = bounded_file(root, relative).read_text(encoding="utf-8")
            if any(marker not in text for marker in markers):
                errors.append("document_marker")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("document_path")


def result(
    errors: list[str],
    source_locks: int,
    validators_passed: int,
    tasks_closed: int,
    manual_review: str,
    gate_state: str,
    p08_authorization: str,
) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p07-phase-gate-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": source_locks,
        "validators_passed": validators_passed if not unique else 0,
        "tasks_closed": tasks_closed if not unique else 0,
        "tasks_required": 9,
        "differential_cases": 8 if not unique else 0,
        "manual_review": manual_review if not unique else "not_proven",
        "gate_state": gate_state if not unique else "not_proven",
        "p08_authorization": p08_authorization if not unique else "not_authorized",
        "product_complete": False,
    }


if __name__ == "__main__":
    value = validate()
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))
    if value["state"] != "pass":
        sys.exit(1)
    print(
        "P07_PHASE_GATE_CONTRACT_PASS "
        f"validators={value['validators_passed']}/10 tasks={value['tasks_closed']}/9 "
        f"gate_state={value['gate_state']}"
    )
