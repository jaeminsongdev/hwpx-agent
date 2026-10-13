"""Exact issuer signing/AEAD/registry/consumer component evidence; not actual SQL/custody/native/Gate."""
import argparse
import base64
from contextlib import contextmanager
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


PRE = module("p138_preserved", "tools/p09/verify_formula_issuer_registry_management.py")
T = module("p139_contracts", "tools/p09/tests/test_formula_issuer_registry_provision.py")
require, RUN = PRE.require, PRE.RUN
CURRENT = "implementation/p09/evidence/p09-139-formula-issuer-registry-provision.source-progress.v1.json"
REPORT = "implementation/p09/P09-139_FORMULA_ISSUER_REGISTRY_PROVISION_REPORT.md"
FAILURE = "implementation/p09/evidence/p09-139-initial-source-contract-failure.v1.json"
INVOCATION = "implementation/p09/evidence/p09-139-powershell5-invocation-failure.v1.json"
BASE = "implementation/p09/source-archive/"
INITIAL = BASE + "p09-139-initial-clone-error/source-preimages.v1.json"
BINDING = BASE + "p09-139-intermediate-test-binding-errors/source-preimages.v1.json"
FOUR = BASE + "p09-139-pre-role-preflight/parents-four.v1.json"
PRELINT = BASE + "p09-139-pre-strict-lint-refactor/source-preimages.v1.json"
FAILED_GUARD = BASE + "p09-139-initial-source-format-check/tools/p09/tests/test_formula_issuer_registry_provision.py"
READBACK = BASE + "p09-139-pre-readback-extraction/source-preimages.v1.json"
BORROW = BASE + "p09-139-pre-borrow-correction/source-preimages.v1.json"
TEST_LINT = BASE + "p09-139-pre-test-lint-correction/source-preimages.v1.json"
READBACK_GUARD = BASE + "p09-139-readback-guard-binding/tools/p09/tests/test_formula_issuer_registry_provision.py"
READBACK_FAILURE = "implementation/p09/evidence/p09-139-readback-guard-failure.v1.json"
GUARD = "tools/p09/tests/test_formula_issuer_registry_provision.py"
DELTA = list(T.PINS) + [T.SOURCE, T.TEST, T.DRIVER, T.LINT, GUARD,
    "tools/p09/verify_formula_issuer_registry_provision.py", REPORT, FAILURE, INVOCATION, READBACK_FAILURE]
ARCHIVES = [T.ARCHIVE, INITIAL, BINDING, FOUR, PRELINT, FAILED_GUARD, READBACK, BORROW, TEST_LINT, READBACK_GUARD]


def pin(path):
    raw = (ROOT / path).read_bytes()
    return {"path": path, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def read(path):
    return json.loads((ROOT / path).read_bytes())


def archive(path, count):
    doc = read(path)
    require(doc["schema_version"] == "hwpx-agent.source-preimage/base64-v1" and len(doc["sources"]) == count,
        "provision_archive_shape_drift")
    result = {}
    for row in doc["sources"]:
        raw = base64.b64decode("".join(row["base64_chunks"]), validate=True)
        require(row["path"] not in result and len(raw) == row["bytes"]
            and hashlib.sha256(raw).hexdigest() == row["sha256"], "provision_archive_digest_drift")
        result[row["path"]] = raw
    return result


def key(path):
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return ""


@contextmanager
def historical(before, excluded=()):
    old_bytes, old_text, old_run = Path.read_bytes, Path.read_text, subprocess.run

    def saved_bytes(path):
        item = key(path)
        return before[item] if item in before else old_bytes(path)

    def saved_text(path, *args, **kw):
        item = key(path)
        if item not in before:
            return old_text(path, *args, **kw)
        return before[item].decode(kw.get("encoding", args[0] if args else "utf-8") or "utf-8").replace("\r\n", "\n")

    def saved_run(args, *pos, **kw):
        result = old_run(args, *pos, **kw)
        if isinstance(args, (list, tuple)) and Path(str(args[0])).name in ("rg", "rg.exe") and "--files" in args and result.returncode == 0 and isinstance(result.stdout, str):
            lines = [line for line in result.stdout.splitlines()
                if key(Path(line) if Path(line).is_absolute() else ROOT / line) not in excluded]
            return subprocess.CompletedProcess(result.args, result.returncode,
                "\n".join(lines) + ("\n" if result.stdout.endswith("\n") else ""), result.stderr)
        return result

    try:
        Path.read_bytes, Path.read_text, subprocess.run = saved_bytes, saved_text, saved_run
        yield
    finally:
        Path.read_bytes, Path.read_text, subprocess.run = old_bytes, old_text, old_run


def predecessor():
    require(pin(PRE.CURRENT) == {"path": PRE.CURRENT, "bytes": 9176,
        "sha256": "2ae1209e6503e5fc3c621840cc37ec98067bd6d556716ef58e5fcd4be4d97432"}, "P138_checkpoint_drift")
    before = T.preimages()
    excluded = set([p for p in DELTA if p not in T.PINS] + ARCHIVES + [CURRENT])
    with historical(before, excluded):
        result = PRE.current()
    require(result["current_revision_library_cases"] == 32 and result["historical_P137_component_executions"] == 63
        and result["historical_stored_cases"] == 234 and result["issuer_product_provisioning_implemented"] is False
        and result["actual_sql_executed"] is False and result["P09_gate"] == "OPEN", "P138_history_scope_promoted")
    return result


def contracts(test_module):
    result = unittest.TestResult()
    unittest.defaultTestLoader.loadTestsFromTestCase(test_module.Contracts).run(result)
    return result


def failed_guard():
    prelint = archive(PRELINT, 2)
    require(set(prelint) == {T.SOURCE, GUARD}, "provision_pre_lint_inventory_drift")
    require(hashlib.sha256(prelint[T.SOURCE]).hexdigest() == "b07dc349b83ac7ea84ce14a6eb7c39616a33b5007db06b5723d0ddad78788c0d"
        and hashlib.sha256(prelint[GUARD]).hexdigest() == "24f822700377825faec306b54fb6cadcc7fca93b5ad7ccc4cf679e1a31fc71d6",
        "provision_pre_lint_original_drift")
    saved = module("p139_failed_guard", FAILED_GUARD)
    saved.ROOT = ROOT
    with historical(prelint):
        result = contracts(saved)
    finding = read(FAILURE)
    require(result.testsRun == 8 and len(result.failures) == 4 and not result.errors and not result.skipped
        and [t._testMethodName for t, _ in result.failures] == finding["failed_contracts"]
        and finding["state"] == "FAIL_CLOSED" and finding["passed"] == finding["failed"] == 4
        and finding["failed_source_archive"] == FAILED_GUARD and finding["Rust_or_SQL_changed_to_fix_guard"] is False
        and finding["actual_sql_executed"] is False and finding["product_complete"] is False
        and finding["P09_gate"] == "OPEN", "provision_failed_guard_not_preserved")
    before = (ROOT / FAILED_GUARD).read_text(encoding="utf-8")
    fixed = before.replace("class Contracts(unittest.TestCase):\n", "class Contracts(unittest.TestCase):\n    def contains(self, marker, source):\n        self.assertIn(re.sub(r\"\\s+\", \"\", marker), re.sub(r\"\\s+\", \"\", source))\n\n")
    fixed = fixed.replace("self.assertIn(", "self.contains(").replace("self.contains(re.sub", "self.assertIn(re.sub")
    require(fixed == prelint[GUARD].decode("utf-8"), "provision_guard_correction_transition_drift")
    corrected = module("p139_corrected_guard", GUARD)
    exec(compile(prelint[GUARD], str(ROOT / GUARD), "exec"), corrected.__dict__)
    with historical(prelint):
        result = contracts(corrected)
    require(result.testsRun == 8 and result.wasSuccessful() and not result.skipped,
        "provision_historical_corrected_guard_not_accepted")
    return prelint


def inputs(doc):
    require(doc["source_freeze_exact_after"] is True and doc["protected_executables_exact_after"] is True
        and len(doc["source_freeze"]) == len({p["path"] for p in doc["source_freeze"]}) == 817
        and all(pin(p["path"]) == p for p in doc["source_freeze"]), "provision_compiled_input_drift")
    protected = read(RUN + "p135-case-001-attempt-001.json")["protected_executables"]
    p137 = read(PRE.PRE.CURRENT)
    protected += p137["current_executables"] + p137["earlier_executables_preserved"] + [read(PRE.CURRENT)["current_executable"]]
    require(doc["protected_executables"] == protected and len(protected) == len({p["path"] for p in protected}) == 28
        and all(pin(p["path"]) == p for p in protected), "provision_old_executable_drift")
    PRE.PRE.resource(doc)


def runtime(variant):
    paths = [RUN + f"p139-provision-{mode}-{variant}.json" for mode in ("build", "list", "test")]
    docs = [read(p) for p in paths]
    for mode, doc in zip(("Build", "List", "Test"), docs):
        require(doc["mode"] == mode and doc["suite"] == "Provision" and doc["state"] == "PASS_SOURCE_ONLY_NOT_GATE"
            and doc["exit_code"] == 0 and doc["stop_reason"] is None
            and doc["P09_gate"] == "OPEN" and doc["product_complete"] is False, "provision_runtime_not_accepted")
        inputs(doc)
    require(docs[0]["build_marker"] is True and not docs[0]["build_diagnostics"] and not docs[0]["cargo_failure"],
        "provision_build_not_clean")
    names = docs[1]["inventory"]
    require(len(names) == len(set(names)) == 8 and all(n.startswith("actual_import::formula_policy_issuer::provision::") for n in names),
        "provision_test_inventory_drift")
    exe = docs[1]["executable_pin"]
    require(exe["path"] == RUN + f"debug/deps/form_stored_provider-p139-{variant}.exe"
        and pin(exe["path"]) == exe and docs[2]["executable_pin"] == exe, "provision_executable_drift")
    summary, passed = docs[2]["tests"]["terminal_summary"], docs[2]["tests"]["passed_test_names"]
    require(summary["outcome"] == "ok" and summary["passed"] == 8 and summary["filtered"] == 241
        and summary["failed"] == summary["ignored"] == summary["measured"] == 0
        and len(passed) == 8 and set(passed) == set(names) and not docs[2]["tests"]["failed_test_names"],
        "provision_exact_runtime_summary_missing")
    return [pin(p) for p in paths], exe


def earlier_failures(prelint):
    receipts = []
    four = (ROOT / FOUR).read_bytes()
    require(set(archive(FOUR, 4)) == set(T.PINS) - {T.MANAGEMENT}, "provision_four_parent_inventory_drift")
    for variant, path, source, codes, lines in [
        ("r1", INITIAL, T.SOURCE, ["E0277"], [185]),
        ("r2", BINDING, T.TEST, ["E0433", "E0433", "E0609", "E0609"], [60, 81, 602, 619])]:
        receipt = RUN + f"p139-provision-build-{variant}.json"
        doc = read(receipt)
        preserved = archive(path, 1)[source]
        require(doc["state"] == "NOT_ACCEPTED_STOP_OR_FAILURE" and doc["exit_code"] == 101
            and doc["stop_reason"] is None and doc["mode"] == "Build" and doc["suite"] == "Provision"
            and [d["code"] for d in doc["build_diagnostics"]] == codes
            and [s["line"] for d in doc["build_diagnostics"] for s in d["spans"]] == lines,
            "provision_compiler_failure_drift")
        selected = {row["path"]: row for row in doc["source_freeze"]}
        require(selected[source] == {"path": source, "bytes": len(preserved), "sha256": hashlib.sha256(preserved).hexdigest()}
            and selected[T.ARCHIVE] == {"path": T.ARCHIVE, "bytes": len(four), "sha256": hashlib.sha256(four).hexdigest()},
            "provision_failed_source_freeze_binding_drift")
        PRE.PRE.resource(doc)
        receipts.append(pin(receipt))
    with historical({**prelint, **archive(TEST_LINT, 1)}):
        earlier, exe = runtime("r3")
        doc = read(RUN + "p139-workspace-lint-r3.json")
        inputs(doc)
    require(doc["state"] == "NOT_ACCEPTED_STOP_OR_FAILURE" and doc["exit_code"] == 101
        and doc["stop_reason"] is None and doc["test_or_app_executed"] is False
        and [d["code"] for d in doc["diagnostics"]] == ["clippy::needless_pass_by_value", "clippy::too_many_lines"]
        and [s["line_start"] for d in doc["diagnostics"] for s in d["spans"]] == [97, 641],
        "provision_strict_lint_failure_not_preserved")
    invocation = read(INVOCATION)
    require(invocation["state"] == "FAILED_BEFORE_COMPILER_START" and invocation["compiler_started"] is False
        and invocation["new_runtime_receipt_created"] is False and invocation["runner_or_thresholds_changed"] is False,
        "provision_runtime_invocation_failure_not_preserved")
    return receipts + earlier + [pin(RUN + "p139-workspace-lint-r3.json")], exe


def refactor_failures():
    r4, r5, tests = archive(READBACK, 1), archive(BORROW, 1), archive(TEST_LINT, 1)
    require(set(r4) == set(r5) == {T.SOURCE} and set(tests) == {T.TEST}, "provision_refactor_archive_coverage_drift")
    finding = read(READBACK_FAILURE)
    require(hashlib.sha256(r5[T.SOURCE]).hexdigest() == finding["tested_workflow_sha256"], "provision_readback_guard_workflow_drift")
    saved = module("p139_readback_failed_guard", READBACK_GUARD)
    saved.ROOT = ROOT
    with historical({**r5, **tests}):
        result = contracts(saved)
    require(result.testsRun == 8 and len(result.failures) == 1 and not result.errors and not result.skipped
        and result.failures[0][0]._testMethodName == finding["failed_contract"]
        and finding["state"] == "FAIL_CLOSED" and finding["passed"] == 7 and finding["failed"] == 1
        and finding["Rust_or_SQL_changed_to_fix_guard"] is False
        and finding["actual_sql_executed"] is False and finding["product_complete"] is False,
        "provision_readback_guard_failure_not_preserved")
    with historical({**r4, **tests}):
        receipts, exe = runtime("r4")
    for variant, snapshot, codes, lines in [
        ("r4", {**r4, **tests}, ["clippy::too_many_lines"], [650]),
        ("r5", {**r5, **tests}, ["clippy::needless_borrow"] * 8, [779] * 4 + [788] * 4),
        ("r6", tests, ["clippy::expect_used"] * 3 + ["clippy::collapsible_if"] + ["clippy::expect_used"] * 3,
            [409, 444, 524, 558, 571, 608, 645])]:
        path = RUN + f"p139-workspace-lint-{variant}.json"
        with historical(snapshot):
            doc = read(path)
            inputs(doc)
        require(doc["state"] == "NOT_ACCEPTED_STOP_OR_FAILURE" and doc["exit_code"] == 101
            and doc["stop_reason"] is None and doc["test_or_app_executed"] is False
            and [d["code"] for d in doc["diagnostics"]] == codes
            and [s["line_start"] for d in doc["diagnostics"] for s in d["spans"]] == lines,
            "provision_refactor_lint_failure_drift")
        receipts.append(pin(path))
    path = RUN + "p139-provision-build-r5.json"
    with historical({**r5, **tests}):
        doc = read(path)
        inputs(doc)
    require(doc["state"] == "PASS_SOURCE_ONLY_NOT_GATE" and doc["build_marker"] is True
        and doc["exit_code"] == 0 and doc["stop_reason"] is None and not doc["build_diagnostics"] and not doc["cargo_failure"],
        "provision_historical_build_missing")
    receipts.append(pin(path))
    return receipts, [exe, pin(RUN + "debug/deps/form_stored_provider-p139-r5.exe")]


def lint():
    path = RUN + "p139-workspace-lint-r7.json"
    doc = read(path)
    require(doc["state"] == "PASS_SOURCE_ONLY_NOT_GATE" and doc["mode"] == "workspace_strict_lint"
        and doc["exit_code"] == 0 and doc["stop_reason"] is None and doc["build_finished_success"] is True
        and not doc["diagnostics"] and doc["test_or_app_executed"] is False
        and doc["P09_gate"] == "OPEN" and doc["product_complete"] is False, "provision_strict_lint_not_accepted")
    inputs(doc)
    require(doc["cargo_arguments"] == ["clippy", "--workspace", "--all-targets", "--locked", "--offline", "--jobs", "1",
        "--target-dir", str(ROOT / "target/p09-121-resource-optimized"), "--message-format", "json", "--", "-D", "warnings"],
        "provision_lint_arguments_drift")
    identity = lambda row: (row["package_id"], row["name"], tuple(row["kind"]))
    expected = {identity(row) for row in doc["workspace_inventory"]}
    require(len(expected) == len(doc["workspace_inventory"]) == 358
        and len({row["package_id"] for row in doc["workspace_inventory"]}) == 32
        and {identity(row) for row in doc["workspace_artifacts"]} == expected, "provision_lint_target_coverage_missing")
    return pin(path)


def audit():
    old = predecessor()
    prelint = failed_guard()
    historic, historic_exe = earlier_failures(prelint)
    refactor_receipts, refactor_exes = refactor_failures()
    result = contracts(T)
    require(result.testsRun == 8 and result.wasSuccessful() and not result.skipped, "provision_source_contracts_not_accepted")
    receipts, exe = runtime("r7")
    return {"state": "PASS_ISSUER_PROVISION_COMPONENT_NOT_ACTUAL_SQL_CUSTODY_ATOMIC_NATIVE_OR_GATE",
        "source_contract_tests": 8, "historical_failed_guard_replays": 5, "historical_corrected_guard_tests": 8,
        "preserved_compiler_diagnostic_count": 5, "preserved_strict_lint_failure_count": 18,
        "current_provision_cases": 8, "stored_cases_filtered_not_currently_rerun": 241,
        "historical_P138_revision_cases": old["current_revision_library_cases"],
        "historical_P137_component_executions": old["historical_P137_component_executions"],
        "historical_stored_cases": old["historical_stored_cases"], "strict_lint_packages": 32, "strict_lint_targets": 358,
        "issuer_product_provisioning_implemented": True, "AEAD_and_Ed25519_original_consumer_component_executed": True,
        "project_role_preflight_is_lease_or_atomic_authority": False,
        "actual_sql_executed": False, "schema22_migration_applied": False, "trust_configuration_changed": False,
        "production_key_custody_qualified": False, "atomic_publication_qualified": False,
        "native_application_executed": False, "app_freeze_cause_resolved": False,
        "P09_gate": "OPEN", "A12_gate": "OPEN", "A13_gate": "OPEN", "product_complete": False,
        "goal_status": "active", "P10_new_implementation": False,
        "accepted_runtime_receipts": receipts, "accepted_lint_receipt": lint(), "current_executable": exe,
        "historical_receipts_preserved": historic + refactor_receipts,
        "earlier_executables_preserved": [historic_exe] + refactor_exes,
        "failed_build_entire_input_freeze_revalidated": False}


def groups():
    return {"source_delta": [pin(p) for p in DELTA], "source_archives_added": [pin(p) for p in ARCHIVES],
        "predecessor_receipts_added": [pin(PRE.CURRENT)], "migration_inputs": [pin(p.relative_to(ROOT).as_posix())
            for p in sorted((ROOT / "migrations/postgres").glob("*.up.sql"))]}


def checkpoint():
    result = audit()
    pins = groups()
    return {"schema_version": "hwpx-agent.p09-formula-issuer-registry-provision-source-progress/v1", **result, **pins,
        "previous_source_files_count": 1210, "current_source_files_count": 1210 + len(DELTA),
        "source_inventory_counting": "historical_graph_plus_declared_delta_not_unique_path_union",
        "inherited_raw_pin_entries": 3437,
        "new_raw_pin_entries": sum(len(v) for v in pins.values()) + len(result["accepted_runtime_receipts"]) + 2
            + len(result["historical_receipts_preserved"]) + len(result["earlier_executables_preserved"]),
        "remaining_coarse_groups_minimum": 6, "remaining_groups_closed_by_slice": 0,
        "minimum_30_conditions_not_exhaustive": True, "native34_state": "NOT_RUN_INPUT_CHANGED_RE_ADMISSION_REQUIRED"}


def current():
    expected = checkpoint()
    require(read(CURRENT) == expected, "provision_checkpoint_scope_or_pin_drift")
    return expected


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", action="store_true")
    parser.add_argument("--checkpoint", action="store_true")
    args = parser.parse_args()
    try:
        result = checkpoint() if args.checkpoint else audit() if args.source else current()
        hidden = {"accepted_runtime_receipts", "accepted_lint_receipt", "current_executable", "historical_receipts_preserved",
            "earlier_executables_preserved", "source_delta", "source_archives_added", "predecessor_receipts_added", "migration_inputs"}
        print(json.dumps(result if args.checkpoint else {k: v for k, v in result.items() if k not in hidden}, indent=2))
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        code = str(error) if isinstance(error, ValueError) and str(error).replace("_", "").isalnum() else "redacted"
        print(json.dumps({"state": "FAIL_CLOSED", "error_code": code, "P09_gate": "OPEN"}))
        raise SystemExit(1) from None
