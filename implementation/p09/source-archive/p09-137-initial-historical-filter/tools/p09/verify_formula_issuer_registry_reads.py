"""SQL22 typed read/product bridge: exact historical preimages, current guards and bounded runtime evidence."""
import argparse
import hashlib
import importlib.util
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("p136_preserved", Path(__file__).with_name("verify_formula_issuer_registry.py"))
PRE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PRE)
TSPEC = importlib.util.spec_from_file_location("p137_source", Path(__file__).parent / "tests/test_formula_issuer_registry_reads.py")
T = importlib.util.module_from_spec(TSPEC)
TSPEC.loader.exec_module(T)
require = PRE.require
CURRENT = "implementation/p09/evidence/p09-137-formula-issuer-registry-reads.source-progress.v1.json"
DRIVER = T.DRIVER
ADDED = [T.REVISION, T.ARTIFACT, T.PRODUCT, T.WIRE, T.TEST]
PARENTS = list(T.PARENT_PINS)
ARCHIVES = [T.ARCHIVE,
    "implementation/p09/source-archive/p09-137-initial-runner-parse/" + DRIVER,
    "implementation/p09/source-archive/p09-137-initial-missing-uuid/" + T.TEST,
    "implementation/p09/source-archive/p09-137-intermediate-missing-branch/" + T.TEST,
    "implementation/p09/source-archive/p09-137-pre-artifact-domain-fix/" + T.TEST]
DELTA = [*PARENTS, *ADDED, DRIVER, "tools/p09/tests/test_formula_issuer_registry_reads.py",
    "tools/p09/verify_formula_issuer_registry_reads.py", "implementation/p09/P09-137_FORMULA_ISSUER_REGISTRY_READS_REPORT.md"]
RUN = "target/p09-121-resource-optimized/"


def pin(path):
    raw = (ROOT / path).read_bytes()
    return {"path": path, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def read(path):
    return json.loads((ROOT / path).read_bytes())


def predecessor():
    require(pin(PRE.CURRENT) == {"path": PRE.CURRENT, "bytes": 8167,
        "sha256": "8b2eddbfccddadc0de482e37b0d1db900b36554d9fb2a923cb7f64e9bcb4a117"}, "P136_checkpoint_drift")
    before = T.preimages()
    # In-memory views of WHOLE authenticated bytes only. No file/DB rewind or weakened old checks.
    old_bytes, old_text, old_run = Path.read_bytes, Path.read_text, subprocess.run
    excluded = set(ADDED + ARCHIVES + DELTA + [CURRENT])

    def key(path):
        try:
            return path.resolve().relative_to(ROOT).as_posix()
        except ValueError:
            return ""

    def preserved_bytes(path):
        name = key(path)
        return before[name] if name in before else old_bytes(path)

    def preserved_text(path, *a, **kw):
        name = key(path)
        if name not in before:
            return old_text(path, *a, **kw)
        encoding = kw.get("encoding", a[0] if a else "utf-8") or "utf-8"
        return before[name].decode(encoding).replace("\r\n", "\n")

    def preserved_run(args, *a, **kw):
        result = old_run(args, *a, **kw)
        if isinstance(args, (list, tuple)) and Path(str(args[0])).name in ("rg", "rg.exe") and "--files" in args and result.returncode == 0 and isinstance(result.stdout, str):
            kept = [line for line in result.stdout.splitlines()
                if key(Path(line) if Path(line).is_absolute() else ROOT / line) not in excluded]
            return subprocess.CompletedProcess(result.args, result.returncode,
                "\n".join(kept) + ("\n" if result.stdout.endswith("\n") else ""), result.stderr)
        return result

    try:
        Path.read_bytes, Path.read_text, subprocess.run = preserved_bytes, preserved_text, preserved_run
        result = PRE.current()
    finally:
        Path.read_bytes, Path.read_text, subprocess.run = old_bytes, old_text, old_run
    require(result["historical_stored_cases"] == 234 and result["source_contract_tests"] == 12
        and result["actual_sql_executed"] is False and result["P09_gate"] == "OPEN", "P136_history_promoted")
    return result


def source_contracts():
    result = unittest.TestResult()
    unittest.defaultTestLoader.loadTestsFromTestCase(T.Contracts).run(result)
    require(result.testsRun == 8 and result.wasSuccessful() and not result.skipped,
        "SQL22_read_bridge_source_contracts_not_accepted")
    return result.testsRun


def resource(doc):
    require(doc["logical_cpu_limit"] == doc["cargo_jobs"] == 1 and doc["priority"] == "BelowNormal"
        and doc["sample_seconds"] == 2 and doc["cpu_stop_percent"] == 85
        and doc["cpu_stop_consecutive_samples"] == 3 and doc["minimum_available_ram_mib"] == 4096
        and doc["maximum_root_working_set_mib"] == 2048 and doc["maximum_seconds"] <= 1800,
        "SQL22_read_bridge_resource_limits_changed")
    require(doc["samples"] and doc["samples"][0]["system_cpu_percent"] < 85
        and all(s["available_ram_mib"] >= 4096 and s["test_working_set_mib"] <= 2048 for s in doc["samples"]),
        "SQL22_read_bridge_resource_pressure")
    hot = 0
    for sample in doc["samples"]:
        hot = hot + 1 if sample["system_cpu_percent"] >= 85 else 0
        require(hot < 3, "SQL22_read_bridge_sustained_cpu")
    require(doc["elapsed_seconds"] <= doc["maximum_seconds"] + 15, "SQL22_read_bridge_duration_exceeded")


def accepted_runtime(suite, variant):
    paths = [RUN + f"p137-{suite.lower()}-{m}-{variant + ('b' if suite == 'Registry' and m != 'build' else '')}.json" for m in ("build", "list", "test")]
    docs = [read(p) for p in paths]
    names = docs[1]["inventory"]
    require(names and len(set(names)) == len(names), "SQL22_read_bridge_test_inventory_not_distinct")
    for doc in docs:
        require(doc["state"] == "PASS_SOURCE_ONLY_NOT_GATE" and doc["suite"] == suite
            and doc["exit_code"] == 0 and doc["stop_reason"] is None
            and doc["source_freeze_exact_after"] is True and doc["protected_executables_exact_after"] is True
            and doc["P09_gate"] == "OPEN" and doc["product_complete"] is False,
            "SQL22_read_bridge_runtime_not_accepted")
        resource(doc)
        require(len(doc["protected_executables"]) == 21 and all(pin(p["path"]) == p for p in doc["protected_executables"]), "old_executable_drift")
        require(len(doc["source_freeze"]) == 810 and len({p["path"] for p in doc["source_freeze"]}) == 810
            and all(pin(p["path"]) == p for p in doc["source_freeze"]), "current_compiled_input_drift")
    require(docs[0]["build_marker"] is True and not docs[0]["build_diagnostics"], "SQL22_read_bridge_build_not_clean")
    exe = docs[1]["executable_pin"]
    require(pin(exe["path"]) == exe and docs[2]["executable_pin"] == exe, "SQL22_read_bridge_executable_drift")
    summary, passed = docs[2]["tests"]["terminal_summary"], docs[2]["tests"]["passed_test_names"]
    require(summary["outcome"] == "ok" and summary["passed"] == len(names)
        and summary["failed"] == summary["ignored"] == summary["measured"] == 0
        and summary["filtered"] == (234 if suite == "Registry" else 0)
        and len(passed) == len(names) and set(passed) == set(names), "SQL22_read_bridge_exact_runtime_summary_missing")
    if suite == "Registry":
        require(len(names) == 7 and all(n.startswith("actual_import::formula_policy_issuer::registry::") for n in names), "SQL22_read_bridge_scope_changed")
    return paths, exe, len(names)


def failures():
    doc = read(RUN + "p137-registry-list-r5.json")
    require(doc["state"] == "DEFERRED_RESOURCE_PRESSURE_NOT_STARTED"
        and doc["samples"][0]["system_cpu_percent"] == 100, "resource_deferred_not_preserved")
    for variant, count in [("r1", 6), ("r2", 1)]:
        doc = read(RUN + f"p137-registry-build-{variant}.json")
        require(doc["state"] == "NOT_ACCEPTED_STOP_OR_FAILURE" and doc["exit_code"] == 101
            and len(doc["build_diagnostics"]) == count
            and all(d["code"] == "E0433" for d in doc["build_diagnostics"]), "build_failures_not_preserved")
    doc = read(RUN + "p137-registry-test-r3.json")
    summary = doc["tests"]["terminal_summary"]
    require(doc["state"] == "NOT_ACCEPTED_STOP_OR_FAILURE" and summary["passed"] == 6
        and summary["failed"] == 1 and summary["filtered"] == 234
        and doc["tests"]["failed_test_names"] == ["actual_import::formula_policy_issuer::registry::registry_root_artifact_media_kind_digest_acl_and_aead_fail_closed"], "fixture_failure_not_preserved")


def audit():
    old = predecessor()
    tests = source_contracts()
    failures()
    accepted, exes, count = [], [], 0
    for suite, variant in [("Registry", "r5"), ("Revision", "r5"), ("Product", "r5"), ("Artifact", "r5")]:
        paths, exe, executed = accepted_runtime(suite, variant)
        accepted.extend(paths)
        exes.append(exe)
        count += executed
    return {"state": "PASS_SQL22_READ_BRIDGE_COMPONENT_NOT_ACTUAL_SQL_PRODUCTION_ISSUER_NATIVE_OR_GATE",
        "source_contract_tests": tests, "current_scoped_runtime_executions": count,
        "registry_product_cases": 7, "historical_stored_cases": old["historical_stored_cases"],
        "SQL22_read_adapters_implemented": True, "SQL22_write_adapters_implemented": False,
        "actual_sql_executed": False, "native_application_executed": False,
        "trust_configuration_changed": False, "production_key_custody_qualified": False,
        "P09_gate": "OPEN", "A12_gate": "OPEN", "A13_gate": "OPEN", "product_complete": False,
        "P10_new_implementation": False, "goal_status": "active",
        "accepted_runtime_receipts": [pin(p) for p in accepted], "current_executables": exes}


def groups(result):
    return {"source_delta": [pin(p) for p in DELTA], "source_archives_added": [pin(p) for p in ARCHIVES],
        "predecessor_receipts_added": [pin(PRE.CURRENT)],
        "unaccepted_runtime_receipts": [pin(RUN + p) for p in ["p137-registry-build-r1.json", "p137-registry-build-r2.json", "p137-registry-test-r3.json", "p137-registry-list-r5.json"]],
        "earlier_runtime_receipts": [pin(RUN + p) for p in ["p137-registry-build-r3.json", "p137-registry-list-r3.json"]],
        "migration_inputs": [pin(p.relative_to(ROOT).as_posix()) for p in sorted((ROOT / "migrations/postgres").glob("*.up.sql"))]}


def current():
    result = audit()
    doc = read(CURRENT)
    require(all(doc[k] == v for k, v in result.items()), "SQL22_read_bridge_checkpoint_scope_drift")
    require(all(doc[k] == v for k, v in groups(result).items()), "SQL22_read_bridge_checkpoint_pins_drift")
    require(doc["remaining_coarse_groups_minimum"] == 6 and doc["remaining_groups_closed_by_slice"] == 0
        and doc["minimum_30_conditions_not_exhaustive"] is True, "SQL22_read_bridge_remaining_count_promoted")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", action="store_true")
    args = parser.parse_args()
    try:
        result = audit() if args.source else current()
        print(json.dumps({k: v for k, v in result.items() if k not in ("accepted_runtime_receipts", "current_executables")}, indent=2))
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        code = str(error) if isinstance(error, ValueError) and str(error).replace("_", "").isalnum() else "redacted"
        print(json.dumps({"state": "FAIL_CLOSED", "error_code": code, "P09_gate": "OPEN"}))
        raise SystemExit(1) from None
