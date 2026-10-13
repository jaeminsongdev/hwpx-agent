"""Readonly current typed-route delta and historical evidence audit; no Rust/DB/native execution."""
import base64
import hashlib
import json
from pathlib import Path
import re
import subprocess

from run_formula_issuer_registry_sql_checks import ROOT, pin as read_pin, require

SOURCE = "crates/product-cli/examples/formula_issuer_product_postgres_probe/source.rs"
ARCHIVE = "implementation/p09/source-archive/p09-143-pre-typed-route-denial/source-preimages.v1.json"
PREVIOUS = "implementation/p09/evidence/p09-143-issuer-product.implementation-progress.v1.json"
REPORT = "implementation/p09/P09-143_TYPED_ROUTE_DENIAL_PROGRESS.md"
CURRENT = [SOURCE, ARCHIVE, PREVIOUS, REPORT,
    "tools/p09/verify_formula_issuer_product_route_boundary.py",
    "tools/p09/tests/test_formula_issuer_product_route_boundary.py",
    "implementation/p09/source-archive/p09-143-pre-route-audit-newline-fix/source-preimages.v1.json",
    "implementation/p09/evidence/p09-143-typed-route-audit-initial-failure.v1.json",
    "implementation/p09/source-archive/p09-143-pre-audit-dedup/source-preimages.v1.json",
    "target/p09-121-resource-optimized/p143-idle-preflight-r2.json"]


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8-sig"))


def archive_rows(paths):
    rows = {}
    for path in paths:
        for item in load(path)["files"]:
            raw = base64.b64decode("".join(item["base64_chunks"]), validate=True)
            require(len(raw) == item["bytes"] and hashlib.sha256(raw).hexdigest() == item["sha256"], "whole_archive_exactness")
            rows[(item["path"], item["bytes"], item["sha256"])] = raw
    return rows


def audit():
    require(Path.cwd().resolve() == ROOT.resolve(), "wrong_root")
    snapshots = {}
    def pin(path):
        # One whole-byte digest per unique path in this snapshot; never a metadata-only shortcut.
        if path not in snapshots:
            snapshots[path] = read_pin(path)
        return snapshots[path]
    previous = load(PREVIOUS)
    before_pin = next(row for row in previous["verified_direct_pins"] if row["path"] == SOURCE)
    before_key = (before_pin["path"], before_pin["bytes"], before_pin["sha256"])
    archive_paths = [row["path"] for row in previous["verified_direct_pins"]
        if row["path"].startswith("implementation/p09/source-archive/")]
    archived = archive_rows(archive_paths + [ARCHIVE])
    require(before_key in archived, "prior_current_source_not_preserved")
    before = archived[before_key].decode("utf-8").replace("\r\n", "\n")
    current = (ROOT / SOURCE).read_text(encoding="utf-8").replace("\r\n", "\n")
    # Authenticate the WHOLE previous source, not a digest refresh or token-only historical claim.
    require(current.count("\n#[cfg(test)]\nmod route_tests") == 1, "new_unit_module_boundary")
    stripped = current.split("\n#[cfg(test)]\nmod route_tests", 1)[0]
    require(stripped.count("\nfn route_denial_matches(") == 1, "route_classifier_boundary")
    left, added = stripped.split("\nfn route_denial_matches(", 1)
    require(added.count("\nfn consumer_error(") == 1, "unchanged_error_classifier_boundary")
    classifier, right = added.split("\nfn consumer_error(", 1)
    restored = left + "\nfn consumer_error(" + right
    new_call = "        route_denial_matches(\n            actual_outcome,\n            prepared.require_current_product_route(provider, &deps),\n        ),"
    old_call = "        prepared\n            .require_current_product_route(provider, &deps)\n            .is_err(),"
    require(restored.count(new_call) == 1, "new_call_boundary")
    require(restored.replace(new_call, old_call) == before, "undeclared_source_change")
    require("Err(_)" not in classifier and "is_err" not in classifier
        and "Operation::RouteUnqualified" in classifier and "Compiler::Source(Output::RouteUnqualified)" in classifier,
        "route_denial_widened")

    def exact(rows, historical=False):
        for row in rows:
            require(pin(row["path"]) == row or (historical and (row["path"], row["bytes"], row["sha256"]) in archived),
                "input_drift")

    exact(previous["verified_direct_pins"], historical=True)
    predecessor = load("implementation/p09/evidence/p09-142-root-crypto.source-progress.v1.json")
    exact(predecessor["verified_direct_pins"])
    builds = [load(f"target/p09-121-resource-optimized/p143-issuer-product-build-r{n}.json") for n in range(1, 6)]
    for build in builds[:4]:
        exact(build["source_freeze"], historical=True)
        exact(build["protected_executables"])
        require(build["source_freeze_exact_after"] and build["protected_executables_exact_after"], "historical_preservation")
    require(builds[0]["state"] == "NOT_ACCEPTED_STOP_OR_FAILURE" and builds[0]["exit_code"] == 101, "r1_failure_lost")
    for build in builds[1:3]:
        require(build["state"] == "PASS_PROBE_BUILD_ONLY_NOT_DB_OR_GATE" and build["catalog_profile"]["test"] is False, "historical_build_scope")
        exact([build["executable_pin"]])
    require(builds[3]["stop_reason"] == "STOP_SUSTAINED_SYSTEM_CPU" and builds[3]["executable_pin"] is None, "r4_stop_lost")
    require(builds[4]["state"] == "DEFERRED_RESOURCE_PRESSURE_NOT_STARTED", "r5_defer_lost")
    for item in previous["partial_runtime_evidence"]:
        run = load(item["path"])
        exact(run["source_freeze"], historical=True)
        exact(run["protected_executables"])
        require(run["state"] == "FAIL_CLOSED" and run["container_removed"]
            and len(run["product_probe"]["result"]["checks"]) == 14 and not run["original_product_consumer_executed"], "failed_runtime_promoted")
    preflight = load(CURRENT[-1])
    exact(preflight["source_freeze"])
    require(preflight["state"] == "DEFERRED_RESOURCE_PRESSURE_NO_HEAVY_WORK_STARTED"
        and not preflight["build_test_DB_or_native_started"] and preflight["consecutive_stable_samples"] == 0,
        "resource_admission_promoted")
    indexed = subprocess.run(["rg", "--threads", "1", "--files", "crates", "protocol/generated/rust", "tools/xtask", "-g", "*.rs", "-g", "Cargo.toml"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=10, check=False)
    frozen_paths = [row["path"] for row in builds[3]["source_freeze"]]
    require(indexed.returncode == 0 and not indexed.stderr
        and set(indexed.stdout.replace("\\", "/").splitlines()).issubset(set(frozen_paths)), "whole_Rust_source_coverage")
    materialized = [pin(path) for path in frozen_paths]
    direct = list(dict.fromkeys(CURRENT + [row["path"] for row in previous["verified_direct_pins"]]))
    result = {
        "schema_version": "hwpx-agent.p09-143-typed-route-boundary-progress/v1",
        "state": "IMPLEMENTED_EXACT_ROUTE_DENIAL_CURRENT_BUILD_RUNTIME_NOT_RUN",
        "verified_direct_pins": [pin(path) for path in direct],
        "prior_current_checkpoint_now_historical": pin(PREVIOUS),
        "whole_prior_source_authenticated": before_pin,
        "declared_source_delta": ["typed_route_denial_classifier", "one_original_call_replaced", "six_pending_Rust_tests"],
        "current_Rust_input_freeze": {"base_receipt": pin("target/p09-121-resource-optimized/p143-issuer-product-build-r4.json"),
            "overrides": [pin(SOURCE)], "entries": len(materialized),
            "materialized_sha256": hashlib.sha256(json.dumps(materialized, sort_keys=True, separators=(",", ":")).encode()).hexdigest()},
        "whole_workspace_Rust_input_coverage_verified": True,
        "P142_direct_pins_preserved": len(predecessor["verified_direct_pins"]),
        "protected_executables": builds[3]["protected_executables"], "protected_executables_exact": True,
        "lightweight_guards_executed": 15, "lightweight_guards_passed": 15,
        "Rust_typed_route_tests_added": 6, "Rust_typed_route_tests_execution": "NOT_RUN_RESOURCE_DEFER",
        "current_accepted_build": None, "current_consumer_runtime": "NOT_RUN", "current_strict_workspace_lint": "NOT_RUN",
        "native_application_executed": False, "heavy_workload_started_this_turn": False,
        "P09_gate": "OPEN", "A12_gate": "OPEN", "A13_gate": "OPEN", "product_complete": False,
        "goal_status": "active", "coarse_remaining_minimum": 6, "coarse_closed_this_turn": 0,
    }
    # A separate second whole-byte pass closes the audit. No stale cache across calls or turns.
    for path, expected in snapshots.items():
        require(read_pin(path) == expected, "audit_input_changed_during_readonly")
    result["unique_files_freshly_double_hashed"] = len(snapshots)
    result["cross_turn_hash_cache_used"] = False
    return result


if __name__ == "__main__":
    try:
        print(json.dumps(audit()))
    except (OSError, ValueError, KeyError, json.JSONDecodeError, subprocess.SubprocessError) as error:
        code = str(error) if isinstance(error, ValueError) and re.fullmatch(r"[a-zA-Z0-9_]+", str(error)) else "redacted"
        print(json.dumps({"state": "FAIL_CLOSED", "error_code": code}))
        raise SystemExit(1) from None
