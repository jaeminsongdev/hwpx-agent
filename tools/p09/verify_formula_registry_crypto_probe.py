"""P142 receipt/source audit. Root AEAD+SQL only, not whole historical graph or product Gate."""
import argparse
import base64
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/p09"))
BUILDS = [f"target/p09-121-resource-optimized/p142-root-crypto-build-r{n}.json" for n in (1, 2, 3)]
LINTS = [f"target/p09-121-resource-optimized/p142-workspace-lint-r{n}.json" for n in (1, 2, 3)]
RUNS = [f"implementation/p09/evidence/p09-142-root-crypto-run0{n}.v1.json" for n in (2, 3)]
ARCHIVES = [f"implementation/p09/source-archive/p09-142-{name}/source-preimages.v1.json" for name in (
    "pre-artifact-schema22", "pre-replication-role-parity", "pre-root-probe-refactor",
    "pre-executable-regex-fix", "pre-strict-lint-doc-fix", "pre-source-guard-format-fix",
    "pre-strict-unit-expect-fix")]
EARLY = "implementation/p09/evidence/p09-142-artifact-schema22.implementation-progress.v1.json"
PREVIOUS = "implementation/p09/evidence/p09-141-formula-issuer-registry-adapter.source-progress.v1.json"
DELTA = ["crates/artifact-service/src/store/postgres_repository/schema22.rs",
    "crates/product-cli/examples/formula_registry_crypto_postgres_probe.rs",
    "tools/p09/build_formula_registry_crypto_probe.ps1", "tools/p09/run_formula_registry_crypto_lint.ps1",
    "tools/p09/run_formula_registry_crypto_probe.py", "tools/p09/fixtures/formula_registry_crypto.sql",
    "tools/p09/tests/test_artifact_schema22_admission.py", "tools/p09/tests/test_formula_registry_crypto_probe.py",
    "tools/p09/verify_formula_registry_crypto_probe.py", "implementation/p09/P09-142_ROOT_CRYPTO_SQL_REPORT.md",
    "implementation/p09/evidence/p09-142-root-crypto-run01.pre-container-failure.v1.json",
    "implementation/p09/evidence/p09-142-source-guard-initial-failure.v1.json"]


def require(ok, code):
    if not ok:
        raise ValueError(code)


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8-sig"))


def pin(path):
    data = (ROOT / path).read_bytes()
    return {"path": path, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def audit():
    archived = {}
    for path in ARCHIVES:
        rows = read(path)["files"]
        require(rows and len(rows) == len({r["path"] for r in rows}), "archive_inventory_drift")
        for row in rows:
            data = base64.b64decode("".join(row["base64_chunks"]), validate=True)
            candidate = {"path": row["path"], "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
            if "sha256" in row:
                require(all(candidate[k] == row[k] for k in candidate), "archive_bytes_or_hash_drift")
            archived.setdefault(row["path"], []).append(candidate)
    current_pins = {}

    def matches(row, history=False):
        actual = current_pins.setdefault(row["path"], pin(row["path"]))
        return actual == row or (history and row in archived.get(row["path"], []))

    def frozen(doc, count, history=False):
        rows = doc["source_freeze"]
        require(len(rows) == len({r["path"] for r in rows}) == count
            and all(matches(r, history) for r in rows), "execution_input_snapshot_drift")
        require(doc["source_freeze_exact_after"] and doc["protected_executables_exact_after"]
            and all(matches(r) for r in doc["protected_executables"]), "protected_execution_drift")

    def resources(doc):
        require(doc["logical_cpu_limit"] == doc["cargo_jobs"] == doc["affinity_mask"] == 1
            and doc["priority"] == "BelowNormal" and doc["stop_reason"] is None
            and doc["cpu_stop_percent"] == 85 and doc["cpu_stop_consecutive_samples"] == 3
            and doc["minimum_available_ram_mib"] == 4096 and doc["maximum_root_working_set_mib"] == 2048,
            "build_or_lint_resource_policy_drift")
        require(0 < doc["elapsed_seconds"] < doc["maximum_seconds"] and doc["samples"], "bounded_execution_missing")
        hot = 0
        for sample in doc["samples"]:
            require(0 <= sample["system_cpu_percent"] <= 100 and sample["available_ram_mib"] >= 4096
                and sample["test_working_set_mib"] <= 2048, "execution_resource_sample_unsafe")
            hot = hot + 1 if sample["system_cpu_percent"] >= 85 else 0
            require(hot < 3, "sustained_CPU_pressure")

    previous = read(PREVIOUS)
    require(pin(PREVIOUS)["sha256"] == "61b957cf379a062bad6b6281c6797524c7d4f9fc32a73f8af5879cc469a88cee"
        and all(matches(r) for r in previous["source_delta"]), "P141_checkpoint_or_sources_changed")
    early = read(EARLY)
    require(all(matches(r, True) for r in early["post_build_explicit_source_pins"])
        and matches(early["unit_runtime"]["executable_pin"]), "early_P142_history_drift")
    builds = [read(p) for p in BUILDS]
    for index, doc in enumerate(builds):
        frozen(doc, 833, index < 2)
        resources(doc)
        require(doc["state"] == "PASS_PROBE_BUILD_ONLY_NOT_DB_OR_GATE" and doc["exit_code"] == 0
            and not doc["diagnostics"] and doc["build_finished_success"] and matches(doc["executable_pin"])
            and doc["catalog_profile"]["test"] is False and doc["catalog_profile"]["opt_level"] == "1"
            and doc["catalog_profile"]["debug_assertions"] and doc["catalog_profile"]["overflow_checks"]
            and doc["actual_DB_executed"] is False and doc["P09_gate"] == "OPEN"
            and doc["product_complete"] is False and len(doc["protected_executables"]) == 37 + index,
            "root_probe_build_scope_or_identity_drift")
    lints = [read(p) for p in LINTS]
    for index, doc in enumerate(lints):
        frozen(doc, 834, index < 2)
        resources(doc)
        require(doc["mode"] == "workspace_strict_lint" and doc["test_or_app_executed"] is False
            and len(doc["workspace_inventory"]) == 360 and doc["P09_gate"] == "OPEN"
            and doc["product_complete"] is False, "lint_scope_drift")
        require(doc["cargo_arguments"][-3:] == ["--", "-D", "warnings"], "strict_warnings_weakened")
    require([r["code"] for r in lints[0]["diagnostics"]] == ["clippy::doc_markdown"]
        and [r["code"] for r in lints[1]["diagnostics"]] == ["clippy::expect_used"]
        and all(r["exit_code"] == 101 for r in lints[:2]), "historical_lint_failures_missing")
    lint = lints[-1]
    identity = lambda r: (r["package_id"], r["name"], tuple(r["kind"]))
    expected = {identity(r) for r in lint["workspace_inventory"]}
    require(lint["exit_code"] == 0 and lint["state"] == "PASS_SOURCE_ONLY_NOT_GATE" and not lint["diagnostics"]
        and lint["build_finished_success"] and len(expected) == 360
        and len({r["package_id"] for r in lint["workspace_inventory"]}) == 32
        and {identity(r) for r in lint["workspace_artifacts"]} == expected, "current_strict_target_coverage_missing")
    driver = load("tools/p09/run_formula_registry_crypto_probe.py", "p142_crypto_driver")
    runs = [read(p) for p in RUNS]
    for index, doc in enumerate(runs):
        frozen(doc, 841, index == 0)
        require(doc["state"] == "PASS_ORIGINAL_ROOT_AEAD_SQL22_NOT_APPROVAL_CONSUMER_NATIVE_OR_GATE"
            and doc["actual_SQL_executed"] and doc["actual_Rust_DB_adapter_executed"] and doc["real_AEAD_executed"]
            and doc["Ed25519_public_key_generated"] and doc["original_full_ir_assertions"] == 25
            and len(doc["original_SQL22_checks_committed"]) == 37 and len(doc["migrations_applied"]) == 22
            and doc["server_version_num"] == 180004, "actual_same_DB_root_evidence_missing")
        require(doc["executable_pin"] == previous["current_executable"]
            and doc["crypto_executable_pin"] == builds[0 if index == 0 else 2]["executable_pin"], "runtime_build_binding_drift")
        require([r["result"]["checks"] for r in doc["probe_runs"]] == [driver.CHECKS,
            ["changed_schema22_fingerprint_denied"], ["correct_schema22_fingerprint_control_admitted"]]
            and all(r["exit_code"] == 0 for r in doc["probe_runs"]), "metadata_or_schema_controls_missing")
        crypto = doc["crypto_probe"]
        require(crypto["exit_code"] == 0 and crypto["result"]["checks"] == driver.ROOT_CHECKS
            and len(driver.ROOT_CHECKS) == 9 and crypto["result"]["failed_stage"] is None
            and crypto["result"]["state"] == "PASS_ORIGINAL_ROOT_AEAD_AND_SQL_NOT_APPROVAL_CONSUMER_OR_GATE",
            "actual_original_root_checks_missing")
        for field in ["real_Ed25519_approval_signature_executed", "original_product_consumer_executed",
            "durable_blob_store_qualified", "native_application_executed", "production_key_custody_qualified",
            "atomic_product_publication_qualified", "product_complete"]:
            require(doc[field] is False, "partial_root_evidence_promoted_to_product")
        require(doc["final_history"] == {"root_history": 4, "root_max": 4, "approval_history": 3,
            "approval_max": 3, "root_revocations": 2, "approval_revocations": 2}, "current_root_history_drift")
        require(doc["resource_stop_reason"] is None and doc["resource_samples"]
            and doc["resource_policy"]["logical_cpu_limit"] == 1 and doc["resource_policy"]["priority"] == "BelowNormal",
            "DB_resource_guard_missing")
        require(doc["container_removed"] and doc["container_name"] == "hwpx-p142-" + doc["run_id"], "owned_cleanup_missing")
        for target in [doc["container_id"], doc["container_name"]]:
            child = subprocess.run([shutil.which("docker"), "inspect", target], capture_output=True, text=True,
                timeout=15, creationflags=subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS)
            require(child.returncode != 0 and re.search(r"no such (object|container)", child.stderr, re.I), "owned_container_present_or_unknown")
    failure = read(DELTA[-2])
    require(failure["state"] == "FAIL_CLOSED_BEFORE_OWNED_CONTAINER" and failure["container_created"] is False
        and failure["actual_DB_executed"] is False, "initial_driver_failure_missing")
    suite = unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromName("tools.p09.tests.test_artifact_schema22_admission"),
        unittest.defaultTestLoader.loadTestsFromName("tools.p09.tests.test_formula_registry_crypto_probe")])
    result = unittest.TextTestRunner(stream=io.StringIO()).run(suite)
    require(result.wasSuccessful() and result.testsRun == 10, "current_source_contracts_failed")
    runtime = runs[-1]
    return {"schema_version": "hwpx-agent.p09-142-root-crypto-source-progress/v1",
        "state": "PASS_ROOT_AEAD_SQL22_SOURCE_PROGRESS_NOT_PRODUCT_OR_GATE", "source_contract_tests": 10,
        "actual_original_root_checks": 9, "same_run_original_metadata_checks": 42, "same_run_schema_controls": 2,
        "same_run_SQL22_checks": 37, "same_run_full_IR_assertions": 25,
        "strict_lint_packages": 32, "strict_lint_targets": 360, "protected_historical_executables": 39,
        "current_executable": builds[-1]["executable_pin"], "current_build_receipt": pin(BUILDS[-1]),
        "current_runtime_receipt": pin(RUNS[-1]), "current_lint_receipt": pin(LINTS[-1]),
        "current_runtime_seconds": runtime["elapsed_seconds"],
        "current_runtime_CPU_max_percent": max(r["system_cpu_percent"] for r in runtime["resource_samples"]),
        "current_runtime_available_RAM_min_MiB": min(r["available_ram_mib"] for r in runtime["resource_samples"]),
        "current_DB_and_AEAD_root_workflow_qualified": True, "Ed25519_public_key_generated": True,
        "actual_Ed25519_approval_signature_qualified": False, "original_product_consumer_same_run_qualified": False,
        "new_diagnostic_schema22_constructor_actual_DB_qualified": False, "current_schema22_unit_execution_qualified": False,
        "durable_blob_store_qualified": False, "production_key_custody_qualified": False,
        "atomic_product_publication_qualified": False, "native_application_executed": False,
        "app_freeze_cause_resolved": False, "whole_predecessor_verifier_graph_reexecuted": False,
        "owned_containers_confirmed_absent": 2, "remaining_coarse_groups_minimum": 6,
        "remaining_groups_closed_by_slice": 0, "minimum_30_conditions_not_exhaustive": True,
        "native34_state": "NOT_RUN_INPUT_CHANGED_RE_ADMISSION_REQUIRED", "P09_gate": "OPEN",
        "A12_gate": "OPEN", "A13_gate": "OPEN", "product_complete": False, "P10_new_implementation": False,
        "goal_status": "active", "verified_direct_pins": [pin(p) for p in DELTA + ARCHIVES + BUILDS + LINTS + RUNS + [EARLY, PREVIOUS]]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint-json", action="store_true")
    args = parser.parse_args()
    try:
        doc = audit()
        print(json.dumps(doc if args.checkpoint_json else {"state": doc["state"], "root_checks": 9,
            "strict_targets": 360, "owned_containers_absent": 2, "P09_gate": "OPEN"}, indent=2))
    except (OSError, ValueError, KeyError, subprocess.SubprocessError, json.JSONDecodeError) as error:
        code = str(error) if isinstance(error, ValueError) and re.fullmatch(r"[A-Za-z0-9_]+", str(error)) else "redacted"
        print(json.dumps({"state": "FAIL_CLOSED", "error_code": code, "P09_gate": "OPEN"}))
        raise SystemExit(1) from None
