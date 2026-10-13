"""P141 exact credential-bound Rust SQL22 metadata evidence. NOT crypto/custody/native/Gate."""
import argparse
import base64
from contextlib import contextmanager
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/p09"))


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


PRE = module("p140_adapter_preserved", "tools/p09/verify_formula_issuer_registry_sql.py")
H = PRE.PRE
D = module("p141_adapter_driver", "tools/p09/run_formula_issuer_registry_adapter.py")
T = module("p141_adapter_contracts", "tools/p09/tests/test_formula_issuer_registry_adapter.py")
require, pin, read = PRE.require, PRE.pin, PRE.read
CURRENT = "implementation/p09/evidence/p09-141-formula-issuer-registry-adapter.source-progress.v1.json"
REPORT = "implementation/p09/P09-141_FORMULA_ISSUER_REGISTRY_ADAPTER_REPORT.md"
FINDING = "implementation/p09/evidence/p09-141-failure-resolution.v1.json"
BASE = "implementation/p09/source-archive/"
ARCHIVE_NAMES = ["initial-probe-compile", "initial-fixture-run", "pre-fixture-time-fix", "pre-executable-profile-fix",
    "pre-immutable-schema-control", "pre-strict-lint-refactor", "pre-strict-lint-resource-count", "initial-historical-metadata-audit"]
ARCHIVES = [BASE + "p09-141-" + name + "/source-preimages.v1.json" for name in ARCHIVE_NAMES]
BUILDS = ["target/p09-121-resource-optimized/p141-adapter-build-r" + str(n) + ".json" for n in range(1, 6)]
LINTS = ["target/p09-121-resource-optimized/p141-workspace-lint-r" + str(n) + ".json" for n in (4, 5)]
RUNTIME = ["implementation/p09/evidence/p09-141-adapter-run0" + str(n) + ".v1.json" for n in range(1, 7)]
DELTA = [T.PROBE, T.BUILD, T.DRIVER, T.FIXTURE, "tools/p09/run_formula_issuer_registry_adapter_lint.ps1",
    "tools/p09/tests/test_formula_issuer_registry_adapter.py", "tools/p09/verify_formula_issuer_registry_adapter.py", REPORT, FINDING,
    "implementation/p09/evidence/p09-141-initial-source-audit-failure.v1.json"]


def archived(path):
    doc = read(path)
    rows = doc["files"]
    require(len(rows) == len({r["path"] for r in rows}) and rows, "adapter_archive_inventory_drift")
    return {r["path"]: base64.b64decode("".join(r["base64_chunks"]), validate=True) for r in rows}


def snapshots():
    saved = [archived(p) for p in ARCHIVES[:7]]
    initial, fixture, time_fix, harness, immutable, refactor, inverse = saved
    # Overlay authenticated whole files for each actual phase; never rewrite live source/history.
    prior_probe = {T.PROBE: immutable[T.PROBE]}
    build = [{**harness, **initial}, {**harness, **prior_probe}, immutable, refactor, {}]
    runtime = [{**harness, **prior_probe, **fixture}, {**harness, **prior_probe, **fixture, **time_fix}, {**harness, **prior_probe},
        immutable, {**refactor, **inverse}, {}]
    return build, runtime, refactor


def frozen(doc, before, expected_count):
    with H.historical(before):
        require(len(doc["source_freeze"]) == len({r["path"] for r in doc["source_freeze"]}) == expected_count
            and all(pin(r["path"]) == r for r in doc["source_freeze"]), "adapter_execution_source_freeze_drift")
    require(all(pin(r["path"]) == r for r in doc["protected_executables"]), "adapter_old_executable_drift")


@contextmanager
def predecessor_metadata():
    original = subprocess.run

    def historical_run(args, *pos, **kw):
        result = original(args, *pos, **kw)
        if isinstance(args, (list, tuple)) and Path(str(args[0])).name in ("cargo", "cargo.exe") and "metadata" in args and result.returncode == 0:
            doc = json.loads(result.stdout)
            require(len(doc["workspace_members"]) == 32 and sum(len(p["targets"]) for p in doc["packages"]) == 359,
                "adapter_current_metadata_inventory_drift")
            removed = []
            for package in doc["packages"]:
                kept = []
                for target in package["targets"]:
                    if target["name"] == "formula_issuer_registry_postgres_probe":
                        require(package["name"] == "revision-service" and target["kind"] == ["example"]
                            and Path(target["src_path"]).resolve() == ROOT / T.PROBE, "adapter_new_target_identity_drift")
                        removed.append(target)
                    else:
                        kept.append(target)
                package["targets"] = kept
            require(len(removed) == 1, "adapter_historical_target_delta_inexact")
            return subprocess.CompletedProcess(result.args, result.returncode, json.dumps(doc), result.stderr)
        return result

    try:
        subprocess.run = historical_run
        yield
    finally:
        subprocess.run = original


def process_resources(doc):
    require(doc["logical_cpu_limit"] == doc["cargo_jobs"] == 1 and doc["affinity_mask"] == 1
        and doc["priority"] == "BelowNormal" and doc["stop_reason"] is None
        and doc["cpu_stop_percent"] == 85 and doc["cpu_stop_consecutive_samples"] == 3
        and doc["minimum_available_ram_mib"] == 4096 and doc["maximum_root_working_set_mib"] == 2048,
        "adapter_build_resource_policy_drift")
    require(doc["samples"] and 0 < doc["elapsed_seconds"] < 650, "adapter_resource_samples_missing")
    require(all(0 <= r["system_cpu_percent"] <= 100 and r["available_ram_mib"] >= 4096
        and r["test_working_set_mib"] <= 2048 for r in doc["samples"]), "adapter_process_resource_pressure")
    hot = 0
    for row in doc["samples"]:
        hot = hot + 1 if row["system_cpu_percent"] >= 85 else 0
        require(hot < 3, "adapter_sustained_CPU_pressure")


def build_checks(before):
    docs = [read(p) for p in BUILDS]
    for n, (doc, old) in enumerate(zip(docs, before), 1):
        frozen(doc, old, 820 if n <= 2 else 818 + n)
        process_resources(doc)
        require(doc["source_freeze_exact_after"] and doc["protected_executables_exact_after"]
            and doc["actual_DB_executed"] is False and doc["P09_gate"] == "OPEN" and doc["product_complete"] is False,
            "adapter_build_scope_promoted")
        if n == 1:
            require(doc["state"] == "NOT_ACCEPTED_STOP_OR_FAILURE" and doc["exit_code"] == 101
                and [r["code"] for r in doc["diagnostics"]] == ["E0308", "E0382", "E0382", "E0382"]
                and doc["executable_pin"] is None, "adapter_initial_compiler_failures_missing")
        else:
            require(doc["state"] == "PASS_PROBE_BUILD_ONLY_NOT_DB_OR_GATE" and doc["exit_code"] == 0
                and doc["build_finished_success"] and not doc["diagnostics"] and pin(doc["executable_pin"]["path"]) == doc["executable_pin"],
                "adapter_build_not_accepted")
            if n >= 3:
                require(doc["catalog_profile"]["test"] is False and doc["catalog_profile"]["opt_level"] == "1"
                    and doc["catalog_profile"]["debug_assertions"] is True and doc["catalog_profile"]["overflow_checks"] is True,
                    "adapter_main_executable_profile_missing")
        require(len(doc["protected_executables"]) == (32 if n <= 2 else 30 + n), "adapter_protected_executable_coverage_drift")
    return docs[-1]


def lint_checks(before):
    failed, current = (read(p) for p in LINTS)
    for doc, old, count in [(failed, before, 823), (current, {}, 824)]:
        frozen(doc, old, count)
        process_resources(doc)
        require(doc["test_or_app_executed"] is False and doc["mode"] == "workspace_strict_lint"
            and doc["source_freeze_exact_after"] and doc["protected_executables_exact_after"], "adapter_lint_scope_drift")
        require(doc["cargo_arguments"] == ["clippy", "--workspace", "--all-targets", "--locked", "--offline", "--jobs", "1",
            "--target-dir", str(ROOT / "target/p09-121-resource-optimized"), "--message-format", "json", "--", "-D", "warnings"],
            "adapter_strict_lint_arguments_drift")
    require(failed["exit_code"] == 101 and failed["state"] == "NOT_ACCEPTED_STOP_OR_FAILURE"
        and len(failed["diagnostics"]) == 1 and failed["diagnostics"][0]["code"] == "clippy::too_many_lines",
        "adapter_original_lint_failure_missing")
    require(current["state"] == "PASS_SOURCE_ONLY_NOT_GATE" and current["exit_code"] == 0
        and current["build_finished_success"] and not current["diagnostics"], "adapter_strict_lint_failed")
    identity = lambda row: (row["package_id"], row["name"], tuple(row["kind"]))
    expected = {identity(r) for r in current["workspace_inventory"]}
    require(len(expected) == len(current["workspace_inventory"]) == 359
        and len({r["package_id"] for r in current["workspace_inventory"]}) == 32
        and {identity(r) for r in current["workspace_artifacts"]} == expected, "adapter_lint_target_coverage_missing")
    old = before[T.PROBE].decode("utf-8")
    replacement = old.replace("fn read_and_context_checks(", "fn read_checks(")
    marker = '    probe.check(\n        "fixed_subject_context_denied",'
    replacement = replacement.replace(marker, '    Ok(())\n}\nfn context_checks(probe: &mut Probe, db: &Connections) -> Result<(), RevisionError> {\n    let ctx = context(\'a\')?;\n' + marker)
    replacement = replacement.replace("    read_and_context_checks(probe, &db)?;", "    read_checks(probe, &db)?;\n    context_checks(probe, &db)?;")
    compact = lambda text: re.sub(r"\s+", "", text)
    require(compact(replacement) == compact((ROOT / T.PROBE).read_text(encoding="utf-8")), "adapter_lint_refactor_changed_checks")
    return current


def absent(doc):
    require(doc["container_removed"] is True and doc["container_id"] and doc["container_name"] == "hwpx-p141-" + doc["run_id"],
        "adapter_owned_cleanup_receipt_missing")
    docker = shutil.which("docker")
    require(docker is not None, "docker_audit_missing")
    for identity in [doc["container_id"], doc["container_name"]]:
        result = subprocess.run([docker, "inspect", identity], capture_output=True, text=True, timeout=15,
            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS)
        require(result.returncode != 0 and re.search(r"no such (object|container)", result.stderr, re.IGNORECASE),
            "adapter_owned_container_present_or_unknown")


def runtime_checks(before, build):
    docs = [read(p) for p in RUNTIME]
    for n, (doc, old) in enumerate(zip(docs, before), 1):
        frozen(doc, old, 826 if n <= 3 else 827 if n == 4 else 828 if n == 5 else 829)
        PRE.resource(doc)
        require(doc["image"] == D.IMAGE and doc["server_version_num"] == 180004 and len(doc["migrations_applied"]) == 22
            and doc["original_full_ir_assertions"] == 25 and len(doc["original_SQL22_checks_committed"]) == 37,
            "adapter_original_SQL_execution_coverage_missing")
        absent(doc)
        for field in ["real_AEAD_or_Ed25519_executed", "native_application_executed", "production_key_custody_qualified",
            "atomic_product_publication_qualified", "product_complete"]:
            require(doc[field] is False, "adapter_metadata_promoted_to_product")
        if n <= 2:
            require(doc["state"] == "FAIL_CLOSED" and doc["failed_stage"] == "new_credential_profiles" and doc["sqlstate"] == "23514"
                and doc["actual_Rust_DB_adapter_executed"] is False and not doc["probe_runs"], "adapter_fixture_failure_missing")
            if n == 2:
                require(doc["sql_constraint_name"] == "artifacts_time_order", "adapter_fixture_constraint_evidence_missing")
        elif n == 3:
            require(doc["state"] == "FAIL_CLOSED" and doc["failed_stage"] == "Rust_credential_bound_metadata_probe"
                and not doc["probe_runs"] and doc["actual_Rust_DB_adapter_executed"] is False,
                "adapter_test_harness_misqualified")
        else:
            require(doc["probe_runs"][0]["result"]["checks"] == D.CHECKS and doc["probe_runs"][0]["exit_code"] == 0
                and doc["actual_Rust_DB_adapter_executed"] is True, "adapter_actual_metadata_checks_missing")
            if n == 4:
                require(doc["state"] == "FAIL_CLOSED" and doc["failed_stage"] == "owned_schema22_fingerprint_negative"
                    and doc["sqlstate"] == "55000" and len(doc["probe_runs"]) == 1, "adapter_immutable_schema_failure_missing")
            else:
                require(doc["state"] == "PASS_CREDENTIAL_BOUND_RUST_SQL22_METADATA_NOT_CRYPTO_NATIVE_OR_GATE"
                    and len(doc["probe_runs"]) == 3 and doc["source_freeze_exact_after"] and doc["protected_executables_exact_after"],
                    "adapter_same_run_metadata_acceptance_missing")
                require([r["result"]["mode"] for r in doc["probe_runs"]] == ["metadata", "changed_schema_denied", "correct_schema_admitted"]
                    and all(r["exit_code"] == 0 and r["result"]["failed_stage"] is None and r["result"]["error_code"] is None for r in doc["probe_runs"]),
                    "adapter_negative_positive_control_missing")
                require(doc["probe_runs"][1]["result"]["checks"] == ["changed_schema22_fingerprint_denied"]
                    and doc["probe_runs"][2]["result"]["checks"] == ["correct_schema22_fingerprint_control_admitted"], "adapter_schema_control_checks_drift")
                controls = doc["schema_controls"]
                require(len(controls["base_migrations"]) == 21 and controls["same_original_migration_and_grants"] is True
                    and controls["schema_identity_or_triggers_mutated"] is False and controls["wrong_fingerprint"] == "0"*64
                    and controls["correct_fingerprint"] == pin(controls["SQL22_source_pin"]["path"])["sha256"], "adapter_fingerprint_control_binding_drift")
                require(doc["final_history"] == {"root_history": 3, "root_max": 3, "approval_history": 3,
                    "approval_max": 3, "root_revocations": 2, "approval_revocations": 2}, "adapter_final_rows_inexact")
    require(docs[-1]["executable_pin"] == build["executable_pin"], "adapter_latest_DB_build_binding_drift")
    return docs[-1]


def audit():
    require(pin(PRE.CURRENT)["sha256"] == "f51bb2abeab6744e7b3fe3b1fd586ac20f650232c999dd859f190c0050577e36", "P140_checkpoint_drift")
    with H.historical({}, set(DELTA + ARCHIVES + BUILDS + LINTS + RUNTIME + [CURRENT])), predecessor_metadata():
        inherited = PRE.current()
    require(inherited["actual_sql_executed"] is True and inherited["Rust_adapter_actual_database_executed"] is False
        and inherited["P09_gate"] == "OPEN", "adapter_predecessor_scope_promoted")
    result = unittest.TestResult()
    unittest.defaultTestLoader.loadTestsFromTestCase(T.AdapterContracts).run(result)
    require(result.testsRun == 8 and result.wasSuccessful() and not result.skipped, "adapter_source_contracts_failed")
    build_before, runtime_before, refactor = snapshots()
    build = build_checks(build_before)
    lint = lint_checks(refactor)
    runtime = runtime_checks(runtime_before, build)
    finding = read(FINDING)
    require(finding["failed_runs_preserved"] == RUNTIME[:4] and finding["failed_build_receipt"] == BUILDS[0]
        and finding["failed_lint_receipt"] == LINTS[0] and finding["production_SQL_or_adapter_modified"] is False,
        "adapter_failure_resolution_missing")
    return {"state": "PASS_RUST_SQL22_CREDENTIAL_BOUND_METADATA_NOT_CRYPTO_CUSTODY_ATOMIC_NATIVE_OR_GATE",
        "source_contract_tests": 8, "current_metadata_checks": 42, "current_schema_admission_controls": 2,
        "original_full_ir_assertions": 25, "original_SQL22_checks_committed": 37,
        "actual_SQL_executed": True, "actual_Rust_DB_adapter_executed": True,
        "same_run_real_AEAD_Ed25519_and_DB_qualified": False, "strict_lint_packages": 32, "strict_lint_targets": 359,
        "historical_engine_failure_runs_preserved": 4, "historical_compiler_diagnostics_preserved": 4,
        "historical_strict_lint_failure_preserved": 1, "owned_containers_confirmed_absent": 6,
        "current_executable": build["executable_pin"], "historical_executables_preserved": build["protected_executables"],
        "current_runtime_receipt": RUNTIME[-1], "current_lint_receipt": LINTS[-1],
        "current_DB_elapsed_seconds": runtime["elapsed_seconds"],
        "current_DB_system_CPU_max_percent": max(r["system_cpu_percent"] for r in runtime["resource_samples"]),
        "current_DB_available_RAM_min_MiB": min(r["available_ram_mib"] for r in runtime["resource_samples"]),
        "production_SQL_or_adapter_modified": False, "operational_DB_or_trust_configuration_changed": False,
        "production_key_custody_qualified": False, "atomic_product_publication_qualified": False,
        "native_application_executed": False, "app_freeze_cause_resolved": False,
        "P09_gate": "OPEN", "A12_gate": "OPEN", "A13_gate": "OPEN", "product_complete": False,
        "P10_new_implementation": False, "goal_status": "active"}


def checkpoint():
    result = audit()
    groups = {"source_delta": [pin(p) for p in DELTA], "source_archives_added": [pin(p) for p in ARCHIVES],
        "build_receipts": [pin(p) for p in BUILDS], "lint_receipts": [pin(p) for p in LINTS],
        "runtime_receipts": [pin(p) for p in RUNTIME], "predecessor_receipts_added": [pin(PRE.CURRENT)],
        "migration_inputs": [pin(p.relative_to(ROOT).as_posix()) for p in sorted((ROOT / "migrations/postgres").glob("*.up.sql"))]}
    return {"schema_version": "hwpx-agent.p09-141-adapter-source-progress/v1", **result, **groups,
        "previous_source_files_count": 1233, "current_source_files_count": 1233 + len(DELTA),
        "source_inventory_counting": "historical_graph_plus_declared_delta_not_unique_path_union",
        "inherited_raw_pin_entries": 3545, "new_raw_pin_entries": sum(len(v) for v in groups.values()) + 1 + len(result["historical_executables_preserved"]),
        "remaining_coarse_groups_minimum": 6, "remaining_groups_closed_by_slice": 0,
        "minimum_30_conditions_not_exhaustive": True, "native34_state": "NOT_RUN_INPUT_CHANGED_RE_ADMISSION_REQUIRED"}


def current():
    result = checkpoint()
    require(read(CURRENT) == result, "adapter_checkpoint_scope_or_pin_drift")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", action="store_true")
    parser.add_argument("--source", action="store_true")
    args = parser.parse_args()
    resources = D.Resources()
    try:
        resources.start()
        result = checkpoint() if args.checkpoint else audit() if args.source else current()
        require(not resources.stop.is_set(), resources.reason or "adapter_audit_resource_stop")
        print(json.dumps(result, indent=2))
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        code = str(error) if isinstance(error, ValueError) and re.fullmatch(r"[A-Za-z0-9_]+", str(error)) else "redacted"
        print(json.dumps({"state": "FAIL_CLOSED", "error_code": code, "P09_gate": "OPEN"}))
        raise SystemExit(1) from None
    finally:
        resources.done.set()
        if resources.thread.is_alive():
            resources.thread.join(timeout=3)
