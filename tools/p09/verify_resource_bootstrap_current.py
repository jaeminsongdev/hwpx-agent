"""P145 readonly evidence reconciliation; no Rust build, SQL or native execution."""
import argparse
import io
import json
from pathlib import Path
import re
import unittest

from idle_resource_admission import IdleResources
from run_formula_issuer_corpus_probe import CHECKS, ROOT_CHECKS
from run_formula_issuer_corpus_unit_probe import EXPECTED
from run_formula_issuer_registry_sql_checks import ROOT, pin as read_pin, require
from run_resource_bounded_python import HELPERS, SELF, TARGETS, observed_limits
from tests.test_resource_bounded_python import ResourceBootstrap

EVIDENCE = "implementation/p09/evidence/"
AUDIT = EVIDENCE + "p09-144-corpus-consumer.progress.v1.json"
UNIT = "target/p09-121-resource-optimized/p144-corpus-unit-run2.json"
SQL = EVIDENCE + "p09-144-corpus-consumer-run03.v1.json"
REPORT = "implementation/p09/P09-145_PRE_HASH_RESOURCE_BOUND_PROGRESS.md"


def audit(resources):
    snapshots = {}

    def pin(path):
        require(not resources.stop.is_set(), resources.reason or "resource_stop")
        if path not in snapshots:
            snapshots[path] = read_pin(path)
        return snapshots[path]

    def exact(rows):
        for row in rows:
            require(pin(row["path"]) == row, "current_pin_drift")

    def load(path):
        pin(path)
        return json.loads((ROOT / path).read_text(encoding="utf-8-sig"))

    core = load(AUDIT)
    require(core["state"] == TARGETS["current-audit"][2] and core["unique_files_freshly_double_hashed"] == 977
        and core["historical_P143_pins_preserved"] == 959 and len(core["protected_executables"]) == 48
        and core["original_source_indices_covered"] == [0] and core["RAM_derivative_indices_covered"] == [0]
        and core["P09_gate"] == "OPEN" and core["product_complete"] is False, "P144_core_scope_or_acceptance")
    exact(core["verified_direct_pins"])
    manifests = load(EVIDENCE + "p09-77-document-import-active-security.source-progress.v1.json")
    require(len(manifests["actual_inputs"]) == 36, "original_manifest_inventory")
    bootstraps = []
    for number, mode, target_path in ((1, "current-audit", AUDIT), (2, "unit", UNIT), (3, "sql", SQL)):
        path = EVIDENCE + f"p09-145-resource-bootstrap-run{number:02}.v1.json"
        boot = load(path)
        limits = {"affinity_mask": 1, "priority_class": 16384, "logical_cpu_limit": 1, "priority": "BelowNormal"}
        require(boot["state"] == "PASS_PRE_HASH_RESOURCE_BOUND_TARGET_ACCEPTED_NOT_NATIVE_OR_GATE"
            and boot["mode"] == mode and boot["target_started"] and boot["target_exit_code"] == 0
            and boot["source_freeze_exact_after"] and boot["pre_hash_stable_samples"] == 3
            and boot["target_state"] == TARGETS[mode][2] and boot["target_receipt"] == pin(target_path)
            and boot["P09_gate"] == "OPEN" and boot["product_complete"] is False
            and boot["bootstrap_continuous_stop_implemented"] is False
            and boot["target_post_hash_and_continuous_guards_replaced"] is False
            and all(boot[key] == limits for key in ("limits_before_target_and_hashes",
                "limits_immediately_before_target", "limits_after_target")), "bootstrap_case_not_exact")
        require({row["path"] for row in boot["source_freeze"]} == {SELF, *HELPERS, TARGETS[mode][0]}, "bootstrap_source_scope")
        exact(boot["source_freeze"])
        bootstraps.append(pin(path))
    unit = load(UNIT)
    require(unit["state"] == TARGETS["unit"][2] and unit["test_process_started"]
        and unit["tests"] == EXPECTED and unit["source_freeze_exact_after"] and unit["protected_executables_exact_after"]
        and unit["actual_DB_or_native_executed"] is False, "actual_unit11_not_accepted")
    exact(unit["source_freeze"])
    exact(unit["protected_executables"])
    sql = load(SQL)
    probe = sql["product_probe"]["result"]
    require(sql["state"] == TARGETS["sql"][2] and sql["source_index"] == probe["source_index"] == 1
        and sql["input_mode"] == probe["input_mode"] == "original"
        and sql["expected_formula_outcome"] == probe["formula_outcome"] == "unchanged"
        and sql["frozen_original_source_pin"] == manifests["actual_inputs"][1]
        and probe["source_sha256"] == probe["original_source_sha256"] == manifests["actual_inputs"][1]["sha256"]
        and probe["only_one_numeric_leaf_changed"] is False and probe["checks"] == ROOT_CHECKS
        and sql["probe_runs"][0]["result"]["checks"] == CHECKS and sql["original_full_ir_assertions"] == 25
        and len(sql["original_SQL22_checks_committed"]) == 37 and sql["container_removed"]
        and sql["source_freeze_exact_after"] and sql["protected_executables_exact_after"]
        and sql["original_product_consumer_executed"] and sql["real_Ed25519_approval_signature_executed"]
        and sql["P09_gate"] == "OPEN" and sql["product_complete"] is False
        and sql["all_36_source_inputs_qualified"] is False and sql["native_application_executed"] is False,
        "second_original_SQL_consumer_not_accepted")
    exact(sql["source_freeze"])
    exact(sql["protected_executables"])
    pin(SELF)
    pin(REPORT)
    pin("tools/p09/verify_resource_bootstrap_current.py")
    pin("tools/p09/tests/test_resource_bounded_python.py")
    tests = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(ResourceBootstrap))
    require(tests.testsRun == 11 and tests.wasSuccessful() and not tests.skipped, "bootstrap_unit11_failed")
    for path, row in snapshots.items():
        require(not resources.stop.is_set(), resources.reason or "resource_stop")
        require(read_pin(path) == row, "input_changed_during_current_audit")
    return {"schema_version": "hwpx-agent.p09-145-resource-bootstrap-current-progress/v1",
        "state": "CURRENT_PRE_HASH_LIMIT_AND_SECOND_ORIGINAL_SQL22_COMPONENT_PASS_NOT_NATIVE_OR_GATE",
        "verified_direct_pins": list(snapshots.values()), "unique_files_freshly_double_hashed": len(snapshots),
        "P144_core_audit": pin(AUDIT), "bootstrap_cases": bootstraps, "additional_actual_SQL_case": pin(SQL),
        "actual_Rust_unit_tests": 11, "bootstrap_unit_tests": 11,
        "original_source_indices_covered": [0, 1], "RAM_derivative_indices_covered": [0],
        "pre_hash_affinity_and_priority_observed": True, "bootstrap_continuous_stop_implemented": False,
        "original_target_guards_preserved": True, "Codex_freeze_cause_or_resolution_established": False,
        "all_36_original_sources_qualified": False, "consumer_live_SQL_revocation_CAS_race_qualified": False,
        "native_application_executed": False, "durable_blob_store_qualified": False,
        "production_key_custody_qualified": False, "atomic_product_publication_qualified": False,
        "observed_graph_native_fidelity_qualified": False, "P09_gate": "OPEN", "A12_gate": "OPEN", "A13_gate": "OPEN",
        "product_complete": False, "goal_status": "active", "coarse_remaining_minimum": 6, "coarse_closed_this_turn": 0}


if __name__ == "__main__":
    resources = None
    try:
        resources = IdleResources()
        observed_limits(resources)
        parser = argparse.ArgumentParser()
        parser.add_argument("--receipt", required=True)
        args = parser.parse_args()
        require(Path.cwd().resolve() == ROOT.resolve(), "wrong_root")
        require(re.fullmatch(r"implementation/p09/evidence/p09-145-resource-bootstrap\.progress\.v[1-9][0-9]*\.json", args.receipt), "receipt_scope")
        destination = ROOT / args.receipt
        require(not destination.exists() and destination.parent.is_dir() and not destination.parent.is_symlink()
            and not destination.parent.is_junction(), "fresh_progress_required")
        resources.start()
        result = audit(resources)
        result["resource_samples"], result["resource_stop_reason"] = resources.samples, resources.reason
        with destination.open("x", encoding="utf-8", newline="\n") as output:
            output.write(json.dumps(result, indent=2) + "\n")
        print(json.dumps({"state": result["state"], "receipt": args.receipt,
            "unique_files_freshly_double_hashed": result["unique_files_freshly_double_hashed"], "P09_gate": "OPEN"}))
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        code = str(error) if isinstance(error, ValueError) and re.fullmatch(r"[A-Za-z0-9_]+", str(error)) else "redacted"
        print(json.dumps({"state": "FAIL_CLOSED", "error_code": code, "P09_gate": "OPEN"}))
        raise SystemExit(1) from None
    finally:
        if resources is not None:
            resources.done.set()
            if resources.thread.is_alive():
                resources.thread.join(timeout=3)
