"""Read-only P143 partial evidence audit. Never turns failed/old runs into current PASS."""
import base64
import hashlib
import json
from pathlib import Path
import re

from run_formula_issuer_registry_sql_checks import ROOT, pin, require

ARCHIVES = [
    "implementation/p09/source-archive/p09-143-pre-compiler-fix/source-preimages.v1.json",
    "implementation/p09/source-archive/p09-143-pre-consumer-diagnostic/source-preimages.v1.json",
    "implementation/p09/source-archive/p09-143-pre-independent-outcome/source-preimages.v1.json",
]
CURRENT = [
    "crates/product-cli/examples/formula_issuer_product_postgres_probe.rs",
    "crates/product-cli/examples/formula_issuer_product_postgres_probe/source.rs",
    "crates/product-cli/examples/formula_issuer_product_postgres_probe/worker.rs",
    "tools/p09/build_formula_issuer_product_probe.ps1",
    "tools/p09/run_formula_issuer_product_probe.py",
    "tools/p09/fixtures/formula_issuer_product.sql",
    "tools/p09/verify_formula_issuer_product_progress.py",
    "tools/p09/tests/test_formula_issuer_product_progress.py",
    "implementation/p09/P09-143_ISSUER_PRODUCT_SQL_PROGRESS.md",
]
BUILD_PATHS = [f"target/p09-121-resource-optimized/p143-issuer-product-build-r{n}.json" for n in range(1, 6)]
RUN_PATHS = [f"implementation/p09/evidence/p09-143-issuer-product-run{n:02}.v1.json" for n in (1, 2)]


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8-sig"))


def audit():
    require(Path.cwd().resolve() == ROOT.resolve(), "wrong_root")
    archived = set()
    for path in ARCHIVES:
        for row in load(path)["files"]:
            raw = base64.b64decode("".join(row["base64_chunks"]), validate=True)
            require(len(raw) == row["bytes"] and hashlib.sha256(raw).hexdigest() == row["sha256"], "archive_exactness")
            archived.add((row["path"], row["bytes"], row["sha256"]))

    def exact(rows, historical=False):
        for row in rows:
            current = pin(row["path"])
            require(current == row or (historical and (row["path"], row["bytes"], row["sha256"]) in archived), "declared_input_drift")

    previous = load("implementation/p09/evidence/p09-142-root-crypto.source-progress.v1.json")
    exact(previous["verified_direct_pins"])
    builds = [load(path) for path in BUILD_PATHS]
    for index, build in enumerate(builds[:4], start=1):
        require(build["logical_cpu_limit"] == build["cargo_jobs"] == 1 and build["priority"] == "BelowNormal", "build_resource_policy")
        require(build["source_freeze_exact_after"] and build["protected_executables_exact_after"], "build_preservation_missing")
        exact(build["source_freeze"], historical=index != 4)
        exact(build["protected_executables"])
    require(builds[0]["state"] == "NOT_ACCEPTED_STOP_OR_FAILURE" and builds[0]["exit_code"] == 101, "r1_failure_lost")
    for build in builds[1:3]:
        require(build["state"] == "PASS_PROBE_BUILD_ONLY_NOT_DB_OR_GATE" and build["exit_code"] == 0
            and build["catalog_profile"]["test"] is False and not build["diagnostics"], "historical_dev_main_build")
        exact([build["executable_pin"]])
    require(builds[3]["state"] == "NOT_ACCEPTED_STOP_OR_FAILURE" and builds[3]["stop_reason"] == "STOP_SUSTAINED_SYSTEM_CPU"
        and builds[3]["executable_pin"] is None, "r4_stop_lost")
    require(builds[4]["state"] == "DEFERRED_RESOURCE_PRESSURE_NOT_STARTED" and builds[4]["samples"][0]["system_cpu_percent"] >= 85, "r5_defer_lost")
    partial = []
    for index, path in enumerate(RUN_PATHS, start=1):
        run = load(path)
        require(run["state"] == "FAIL_CLOSED" and run["container_removed"] is True
            and run["original_full_ir_assertions"] == 25 and len(run["original_SQL22_checks_committed"]) == 37,
            "failed_runtime_or_original_coverage_lost")
        exact(run["source_freeze"], historical=True)
        exact(run["protected_executables"])
        require(run["product_executable_pin"] == builds[index]["executable_pin"], "failed_run_build_binding")
        metadata = run["probe_runs"]
        require(len(metadata) == 1 and metadata[0]["exit_code"] == 0 and len(metadata[0]["result"]["checks"]) == 42, "metadata_coverage")
        product = run["product_probe"]["result"]
        require(run["product_probe"]["exit_code"] == 1 and product["state"] == "FAIL_CLOSED"
            and product["failed_stage"] == "original_mandatory_signature_consumer"
            and len(product["checks"]) == len(set(product["checks"])) == 14
            and product["checks"][-1] == "original_signature_approval_SQL_commit_readback",
            "partial_source_signature_evidence")
        require(not product["real_approval_signature_and_original_consumer_executed"]
            and not run["original_product_consumer_executed"] and not run["native_application_executed"]
            and not run["production_key_custody_qualified"] and not run["atomic_product_publication_qualified"]
            and run["P09_gate"] == "OPEN" and not run["product_complete"], "scope_promoted")
        partial.append({"path": path, "passed_source_signature_checks": 14, "overall_state": "FAIL_CLOSED", "container_removed": True})
    files = CURRENT + ARCHIVES + BUILD_PATHS + RUN_PATHS
    return {
        "schema_version": "hwpx-agent.p09-143-issuer-product-implementation-progress/v1",
        "state": "PARTIAL_IMPLEMENTATION_RUNTIME14_CURRENT_OUTCOME_FIX_NOT_RUN",
        "verified_direct_pins": [pin(path) for path in files],
        "P142_direct_pins_preserved": len(previous["verified_direct_pins"]),
        "current_Rust_source_freeze": {"receipt": BUILD_PATHS[3], "entries": len(builds[3]["source_freeze"]), "receipt_pin": pin(BUILD_PATHS[3])},
        "current_Rust_freeze_exact": True, "current_accepted_build": None,
        "historical_accepted_builds": [BUILD_PATHS[1], BUILD_PATHS[2]],
        "protected_executables": builds[3]["protected_executables"],
        "protected_executables_exact": True,
        "partial_runtime_evidence": partial,
        "current_NoChange_fix_build_and_runtime": "NOT_RUN_RESOURCE_STOP_AND_DEFER",
        "current_strict_workspace_lint": "NOT_RUN",
        "current_native_application": "NOT_RUN",
        "changed_formula_candidate_SQL22_qualified": False,
        "durable_blob_store_qualified": False, "production_key_custody_qualified": False,
        "atomic_product_publication_qualified": False,
        "P09_gate": "OPEN", "A12_gate": "OPEN", "A13_gate": "OPEN", "product_complete": False,
        "goal_status": "active", "coarse_remaining_minimum": 6, "coarse_closed_this_turn": 0,
    }


if __name__ == "__main__":
    try:
        result = audit()
        print(json.dumps(result))
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        code = str(error) if isinstance(error, ValueError) and re.fullmatch(r"[a-zA-Z0-9_]+", str(error)) else "redacted"
        print(json.dumps({"state": "FAIL_CLOSED", "error_code": code}))
        raise SystemExit(1) from None
