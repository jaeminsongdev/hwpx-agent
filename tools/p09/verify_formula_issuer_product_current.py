"""Readonly current P143 component evidence audit. Historical failures never become current PASS."""
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
import unittest

from idle_resource_admission import IdleResources
from run_formula_issuer_product_probe import ROOT_CHECKS, CHECKS
from run_formula_issuer_registry_sql_checks import ROOT, pin as whole_pin, require

BASE = "target/p09-121-resource-optimized/"
EVIDENCE = "implementation/p09/evidence/"
SOURCE = "crates/product-cli/examples/formula_issuer_product_postgres_probe/source.rs"
WORKER = "crates/product-cli/examples/formula_issuer_product_postgres_probe/worker.rs"
REPORT = "implementation/p09/P09-143_CURRENT_CONSUMER_SQL22_PROGRESS.md"
SELF = "tools/p09/verify_formula_issuer_product_current.py"
ARCHIVES = ["implementation/p09/source-archive/p09-143-" + name + "/source-preimages.v1.json" for name in (
    "pre-compiler-fix", "pre-consumer-diagnostic", "pre-independent-outcome", "pre-typed-route-denial",
    "pre-route-audit-newline-fix", "pre-audit-dedup", "pre-post-hash-idle-hook", "pre-strict-lint-corrections",
)]
GUARDS = ["tools/p09/tests/" + name + ".py" for name in (
    "test_formula_issuer_product_progress", "test_formula_issuer_product_route_boundary",
    "test_idle_resource_window", "test_post_hash_idle_admission",
)]


def replace_one(value, old, new):
    require(value.count(old) == 1, "declared_delta_boundary")
    return value.replace(old, new, 1)


def normalized(raw):
    return raw.decode("utf-8").replace("\r\n", "\n")


def lint_delta(source, worker, previous_source, previous_worker):
    restored = replace_one(source,
        "        StoredProductRequest,\n        formula::{FormulaPreparationReceipt, PRODUCT_OPERATION_REQUEST_SCHEMA},",
        "        StoredProductRequest, formula::PRODUCT_OPERATION_REQUEST_SCHEMA,")
    restored = replace_one(restored, "fn key_id(&self) -> &'static str", "fn key_id(&self) -> &str")
    restored = replace_one(restored, "    let actual_outcome = match &prepared.receipt().product.product.formula {",
        "    use hwpx_agent_cli::form_product_request::stored_operations::formula::FormulaPreparationReceipt;\n"
        "    let actual_outcome = match &prepared.receipt().product.product.formula {")
    require(restored == previous_source, "undeclared_consumer_source_delta")
    restored_worker = replace_one(worker, "0x6000_0000_0000_0000_0000_0000_0000_0000", "0x60000000000000000000000000000000")
    require(restored_worker == previous_worker, "undeclared_worker_source_delta")


def route_delta(typed_source, previous_source):
    require(typed_source.count("\n#[cfg(test)]\nmod route_tests") == 1, "typed_unit_boundary")
    stripped = typed_source.split("\n#[cfg(test)]\nmod route_tests", 1)[0]
    require(stripped.count("\nfn route_denial_matches(") == 1, "route_classifier_boundary")
    left, added = stripped.split("\nfn route_denial_matches(", 1)
    require(added.count("\nfn consumer_error(") == 1, "original_error_boundary")
    classifier, right = added.split("\nfn consumer_error(", 1)
    restored = left + "\nfn consumer_error(" + right
    restored = replace_one(restored,
        "        route_denial_matches(\n            actual_outcome,\n            prepared.require_current_product_route(provider, &deps),\n        ),",
        "        prepared\n            .require_current_product_route(provider, &deps)\n            .is_err(),")
    require(restored == previous_source, "undeclared_typed_route_delta")
    require("Err(_)" not in classifier and "is_err" not in classifier, "route_denial_widened")


def run_guards():
    suite = unittest.TestSuite()
    for number, path in enumerate(GUARDS):
        spec = importlib.util.spec_from_file_location("p143_guard_" + str(number), ROOT / path)
        require(spec is not None and spec.loader is not None, "guard_module_missing")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
    result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    require(result.testsRun == 19 and result.wasSuccessful() and not result.skipped, "lightweight_guards_failed")
    return result.testsRun


def audit(resources):
    require(Path.cwd().resolve() == ROOT.resolve(), "wrong_root")
    snapshots = {}
    archive_bytes = {}

    def pin(path):
        require(not resources.stop.is_set(), resources.reason or "resource_stop")
        if path not in snapshots:
            snapshots[path] = whole_pin(path)
        return snapshots[path]

    def load(path):
        pin(path)
        return json.loads((ROOT / path).read_text(encoding="utf-8-sig"))

    for path in ARCHIVES:
        for row in load(path)["files"]:
            raw = base64.b64decode("".join(row["base64_chunks"]), validate=True)
            require(len(raw) == row["bytes"] and hashlib.sha256(raw).hexdigest() == row["sha256"], "whole_preimage_drift")
            archive_bytes[(row["path"], row["bytes"], row["sha256"])] = raw

    def exact(rows, historical=False):
        for row in rows:
            require(pin(row["path"]) == row or (historical and
                (row["path"], row["bytes"], row["sha256"]) in archive_bytes), "declared_pin_drift")

    typed = load(EVIDENCE + "p09-143-typed-route-denial.progress.v1.json")
    previous = load(EVIDENCE + "p09-143-issuer-product.implementation-progress.v1.json")
    exact(typed["verified_direct_pins"], historical=True)
    exact(previous["verified_direct_pins"], historical=True)
    prior_source = next(row for row in previous["verified_direct_pins"] if row["path"] == SOURCE)
    typed_source = next(row for row in typed["verified_direct_pins"] if row["path"] == SOURCE)
    typed_worker = next(row for row in typed["verified_direct_pins"] if row["path"] == WORKER)
    archived_source = normalized(archive_bytes[(SOURCE, typed_source["bytes"], typed_source["sha256"])])
    archived_worker = normalized(archive_bytes[(WORKER, typed_worker["bytes"], typed_worker["sha256"])])
    lint_delta(normalized((ROOT / SOURCE).read_bytes()), normalized((ROOT / WORKER).read_bytes()), archived_source, archived_worker)
    route_delta(archived_source, normalized(archive_bytes[(SOURCE, prior_source["bytes"], prior_source["sha256"])]))
    predecessor_path = EVIDENCE + "p09-142-root-crypto.source-progress.v1.json"
    predecessor = load(predecessor_path)
    exact(predecessor["verified_direct_pins"])
    require(len(predecessor["verified_direct_pins"]) == 29, "P142_coverage_drift")

    builds = [load(BASE + f"p143-issuer-product-build-r{n}.json") for n in range(1, 8)]
    for build in builds:
        if "source_freeze" in build:
            exact(build["source_freeze"], historical=True)
            exact(build["protected_executables"])
            require(build["source_freeze_exact_after"] and build["protected_executables_exact_after"], "build_history_preservation")
        if build.get("executable_pin"):
            exact([build["executable_pin"]])
    require(builds[0]["exit_code"] == 101 and builds[0]["state"] == "NOT_ACCEPTED_STOP_OR_FAILURE", "compiler_failure_lost")
    require(builds[3]["stop_reason"] == "STOP_SUSTAINED_SYSTEM_CPU" and builds[3]["executable_pin"] is None, "CPU_stop_lost")
    require(builds[4]["state"] == "DEFERRED_RESOURCE_PRESSURE_NOT_STARTED", "before_start_defer_lost")
    current_build = builds[6]
    require(current_build["state"] == "PASS_PROBE_BUILD_ONLY_NOT_DB_OR_GATE"
        and current_build["exit_code"] == 0 and not current_build["catalog_profile"]["test"]
        and not current_build["diagnostics"] and len(current_build["source_freeze"]) == 842, "current_build_not_accepted")
    exact(current_build["source_freeze"])

    runs = [load(EVIDENCE + f"p09-143-issuer-product-run{n:02}.v1.json") for n in range(1, 6)]
    for run in runs:
        exact(run["source_freeze"], historical=True)
        exact(run["protected_executables"])
        require(run["container_removed"] and not run["native_application_executed"]
            and run["P09_gate"] == "OPEN" and not run["product_complete"], "runtime_scope_or_cleanup_drift")
    for run in runs[:2]:
        require(run["state"] == "FAIL_CLOSED" and len(run["product_probe"]["result"]["checks"]) == 14
            and not run["original_product_consumer_executed"], "partial_failures_promoted")
    require(runs[2]["state"] == "FAIL_CLOSED" and runs[2]["error_code"] == "STOP_SUSTAINED_SYSTEM_CPU"
        and not runs[2]["original_product_consumer_executed"], "runtime_CPU_stop_promoted")
    current_run = runs[4]
    exact(current_run["source_freeze"])
    require(current_run["product_executable_pin"] == current_build["executable_pin"], "current_runtime_build_binding")
    require(current_run["state"] == "PASS_ORIGINAL_SIGNATURE_CONSUMER_SQL22_COMPONENT_NOT_NATIVE_OR_GATE"
        and current_run["source_freeze_exact_after"] and current_run["protected_executables_exact_after"]
        and current_run["product_probe"]["result"]["checks"] == ROOT_CHECKS
        and current_run["product_probe"]["exit_code"] == 0
        and current_run["product_probe"]["result"]["formula_outcome"] == "unchanged"
        and current_run["probe_runs"][0]["result"]["checks"] == CHECKS
        and len(current_run["probe_runs"]) == 3 and current_run["original_full_ir_assertions"] == 25
        and len(current_run["original_SQL22_checks_committed"]) == 37 and len(current_run["migrations_applied"]) == 22
        and current_run["original_product_consumer_executed"] and current_run["real_Ed25519_approval_signature_executed"],
        "current_consumer_runtime_not_accepted")
    require(current_run["final_history"] == {"root_history": 4, "root_max": 4, "approval_history": 4,
        "approval_max": 3, "root_revocations": 2, "approval_revocations": 2}, "current_history_drift")
    require(current_run["source_inputs_covered"] == 1 and not current_run["all_36_source_inputs_qualified"]
        and not any(current_run[key] for key in ("durable_blob_store_qualified", "production_key_custody_qualified",
            "atomic_product_publication_qualified", "observed_graph_native_fidelity_qualified")), "component_scope_promoted")

    unit_builds = [load(BASE + f"p143-typed-route-unit-build-r{n}.json") for n in (1, 2)]
    unit_runs = [load(BASE + f"p143-typed-route-unit-run{n}.json") for n in (1, 2)]
    for unit_build, unit_run in zip(unit_builds, unit_runs, strict=True):
        exact(unit_build["source_freeze"], historical=True)
        exact(unit_run["source_freeze"], historical=True)
        exact(unit_run["protected_executables"])
        require(unit_build["catalog_profile"]["test"] and unit_build["exit_code"] == 0
            and unit_run["state"] == "PASS_TYPED_ROUTE_UNIT6_NOT_DB_NATIVE_OR_GATE" and unit_run["test_process_started"]
            and unit_run["executable_pin"] == unit_build["executable_pin"] and len(unit_run["tests"]) == 6,
            "actual_unit_evidence_not_accepted")
    exact(unit_builds[1]["source_freeze"])
    exact(unit_runs[1]["source_freeze"])

    earlier_lint = load(BASE + "p143-workspace-lint-r1.json")
    exact(earlier_lint["source_freeze"], historical=True)
    exact(earlier_lint["protected_executables"])
    require(earlier_lint["state"] == "NOT_ACCEPTED_STOP_OR_FAILURE" and earlier_lint["exit_code"] == 101
        and [row["code"] for row in earlier_lint["diagnostics"]] == ["clippy::unreadable_literal",
            "clippy::unnecessary_literal_bound", "clippy::items_after_statements"], "strict_lint_failure_lost")
    lint = load(BASE + "p143-workspace-lint-r2.json")
    exact(lint["source_freeze"])
    exact(lint["protected_executables"])
    key = lambda row: (row["package_id"], row["name"], tuple(sorted(row["kind"])))
    expected_targets = {key(row) for row in lint["workspace_inventory"]}
    actual_targets = {key(row) for row in lint["workspace_artifacts"]}
    require(lint["state"] == "PASS_SOURCE_ONLY_NOT_GATE" and lint["exit_code"] == 0
        and lint["source_freeze_exact_after"] and lint["protected_executables_exact_after"]
        and lint["workspace_target_coverage_exact"] and not lint["diagnostics"]
        and len({row["package_id"] for row in lint["workspace_inventory"]}) == 32
        and len(expected_targets) == len(actual_targets) == 361 and expected_targets == actual_targets
        and not lint["missing_targets"] and not lint["unexpected_targets"]
        and len(lint["protected_executables"]) == 46 and "-D" in lint["cargo_arguments"]
        and lint["cargo_arguments"][-1] == "warnings" and not lint["test_or_app_executed"], "current_strict_lint_not_accepted")
    for executable in [build["executable_pin"] for build in builds if build.get("executable_pin")] + [row["executable_pin"] for row in unit_builds]:
        require(executable in lint["protected_executables"], "historical_executable_not_protected")
    indexed = subprocess.run(["rg", "--threads", "1", "--files", "crates", "protocol/generated/rust", "tools/xtask",
        "-g", "*.rs", "-g", "Cargo.toml"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=10, check=False)
    require(indexed.returncode == 0 and not indexed.stderr and set(indexed.stdout.replace("\\", "/").splitlines()).issubset(
        {row["path"] for row in current_build["source_freeze"]}), "whole_current_Rust_input_coverage")
    for path in [REPORT, SELF, *GUARDS, "tools/p09/run_formula_issuer_product_lint.ps1",
        "tools/p09/idle_resource_admission.py", "tools/p09/check_idle_resource_window.py"]:
        pin(path)
    guards = run_guards()
    docker = shutil.which("docker")
    require(docker is not None, "owned_container_absence_tool_missing")
    absence = []
    for reference in (current_run["container_id"], current_run["container_name"]):
        child = subprocess.run([docker, "inspect", reference], cwd=ROOT, capture_output=True, text=True, timeout=10, check=False)
        require(child.returncode != 0 and re.search(r"no such (object|container)", child.stderr, re.IGNORECASE), "owned_container_still_present")
        absence.append({"reference": reference, "absent": True})
    for path, expected in snapshots.items():
        require(not resources.stop.is_set(), resources.reason or "resource_stop")
        require(whole_pin(path) == expected, "audit_input_changed")
    return {
        "schema_version": "hwpx-agent.p09-143-current-consumer-sql22-progress/v1",
        "state": "CURRENT_ORIGINAL_SIGNATURE_CONSUMER_COMPONENT_PASS_NOT_NATIVE_OR_GATE",
        "verified_direct_pins": list(snapshots.values()), "unique_files_freshly_double_hashed": len(snapshots),
        "cross_turn_hash_cache_used": False, "whole_lint_source_delta_verified": True, "whole_typed_route_delta_verified": True,
        "P142_direct_pins_preserved": 29, "historical_failures_preserved": True,
        "current_main_build": pin(BASE + "p143-issuer-product-build-r7.json"),
        "current_Rust_unit_build": pin(BASE + "p143-typed-route-unit-build-r2.json"),
        "current_Rust_unit_run": pin(BASE + "p143-typed-route-unit-run2.json"),
        "current_consumer_runtime": pin(EVIDENCE + "p09-143-issuer-product-run05.v1.json"),
        "current_strict_workspace_lint": pin(BASE + "p143-workspace-lint-r2.json"),
        "protected_executables": lint["protected_executables"], "protected_executables_exact": True,
        "current_source_checks": {"Rust_units": 6, "source_resource_guards": guards, "packages": 32, "targets": 361},
        "current_DB_checks": {"original_full_IR": 25, "original_SQL22": 37, "credential_metadata": 42,
            "signature_consumer": 18, "fingerprint_controls": 2},
        "current_owned_container_absence": absence, "source_inputs_covered": 1, "formula_outcomes_covered": ["unchanged"],
        "all_36_source_inputs_qualified": False, "native_application_executed": False,
        "durable_blob_store_qualified": False, "production_key_custody_qualified": False, "atomic_product_publication_qualified": False,
        "P09_gate": "OPEN", "A12_gate": "OPEN", "A13_gate": "OPEN", "product_complete": False, "goal_status": "active",
        "coarse_remaining_minimum": 6, "coarse_closed_this_turn": 0,
    }


if __name__ == "__main__":
    resources = None
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("--receipt", required=True)
        args = parser.parse_args()
        require(re.fullmatch(r"implementation/p09/evidence/p09-143-current-consumer-sql22\.progress\.v[1-9][0-9]*\.json", args.receipt), "fresh_progress_receipt_scope")
        destination = ROOT / args.receipt
        require(not destination.exists() and destination.parent.is_dir() and not destination.parent.is_symlink()
            and not destination.parent.is_junction(), "fresh_progress_receipt_required")
        resources = IdleResources()
        resources.start()
        result = audit(resources)
        result["audit_resource_samples"] = resources.samples
        result["audit_resource_stop_reason"] = resources.reason
        # Runtime audit receipt only. Never overwrite a historical checkpoint or dump the full pin ledger.
        with destination.open("x", encoding="utf-8", newline="\n") as output:
            output.write(json.dumps(result, indent=2) + "\n")
        print(json.dumps({"state": result["state"], "receipt": args.receipt,
            "unique_files_freshly_double_hashed": result["unique_files_freshly_double_hashed"],
            "protected_executables": len(result["protected_executables"]), "current_checks": result["current_source_checks"]}))
    except (OSError, ValueError, KeyError, json.JSONDecodeError, subprocess.SubprocessError) as error:
        code = str(error) if isinstance(error, ValueError) and re.fullmatch(r"[A-Za-z0-9_]+", str(error)) else "redacted"
        print(json.dumps({"state": "FAIL_CLOSED", "error_code": code, "P09_gate": "OPEN"}))
        raise SystemExit(1) from None
    finally:
        if resources is not None:
            resources.done.set()
            if resources.thread.is_alive():
                resources.thread.join(timeout=3)
