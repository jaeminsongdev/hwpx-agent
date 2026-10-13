"""P134 exact formula DATA revocation source/runtime; actual SQL/issuer/native/Gate stay unverified."""
import importlib.util
import json
import re
import subprocess
import sys
import types
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p133_preserved", Path(__file__).with_name("verify_optimized_workspace_lint.py"))
PRE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PRE)
ROOT, R, require = PRE.ROOT, PRE.R, PRE.require
CURRENT = "implementation/p09/evidence/p09-134-formula-policy-revocation.source-progress.v1.json"
DRIVER = "tools/p09/run_formula_policy_revocation.ps1"
LINT_DRIVER = "tools/p09/run_formula_policy_revocation_lint.ps1"
PARENTS = ["crates/revision-service/src/postgres/source_formula_policy.rs",
           "crates/product-cli/src/form_stored_provider/actual_import/source_policy/formulas.rs",
           "crates/product-cli/tests/form_stored_provider/actual_import.rs"]
ARCHIVES = {p: "implementation/p09/source-archive/p09-134-pre-formula-revocation/" + p for p in PARENTS}
ADDED = ["crates/revision-service/src/postgres/source_formula_policy/revocation.rs",
         "crates/product-cli/src/form_stored_provider/actual_import/source_policy/formulas/revocation.rs",
         "crates/product-cli/src/form_stored_provider/actual_import/source_policy/formulas/revocation/postgres.rs",
         "crates/product-cli/tests/form_stored_provider/actual_import/formula_policy_revocation.rs"]
FAILED_ARCHIVES = {stage: f"implementation/p09/source-archive/p09-134-{name}/tools/p09/run_formula_policy_revocation.ps1"
                   for stage, name in zip("abc", ("initial-runner", "json-runner", "diagnostic-runner"))}
INITIAL_SOURCE = "implementation/p09/source-archive/p09-134-initial-revocation/" + ADDED[0]
OLD_DRIVER = "implementation/p09/source-archive/p09-134-pre-scope-split/" + DRIVER
PRE_LINT = {p: "implementation/p09/source-archive/p09-134-pre-lint/" + p for p in (ADDED[0], ADDED[2], ADDED[3], DRIVER)}
SUITES = {"Stored": ("form_stored_provider", 234), "Revision": ("revision_service", 22), "Product": ("hwpx_agent_cli", None), "Revocation": ("form_stored_provider", 6)}
LINT = R.RUN + "p134-workspace-lint-e.json"
LINT_FAILS = [R.RUN + f"p134-workspace-lint-{s}.json" for s in "abcd"]
FAILS = [R.RUN + f"p134-revision-build-{s}.json" for s in "abc"]
SUCCESS = [R.RUN + f"p134-revision-{m}-{('e' if m == 'build' else 'b')}.json" for m in ("build", "list", "test")]
SUCCESS += [R.RUN + f"p134-product-{m}-c.json" for m in ("build", "list", "test")]
SUCCESS += [R.RUN + f"p134-revocation-{m}-c.json" for m in ("list", "test")]
STORED_PREP = [R.RUN + f"p134-stored-{m}-b.json" for m in ("build", "list")]
EARLIER_RUNS = [R.RUN + f"p134-revision-{m}-{('d' if m == 'build' else 'a')}.json" for m in ("build", "list", "test")]
EARLIER_RUNS += [R.RUN + f"p134-product-{m}-b.json" for m in ("build", "list", "test")]
EARLIER_RUNS += [R.RUN + f"p134-revocation-{m}-b.json" for m in ("list", "test")]
EARLIER_RUNS += [R.RUN + f"p134-stored-{m}-a.json" for m in ("build", "list")]
STOP = R.RUN + "p134-stored-test-a.json"
DEFERRED = [R.RUN + "p134-revocation-list-a.json", R.RUN + "p134-product-build-a.json"]
CROSSCHECK = "target/p09-122-resource-crosscheck/p134-after-owned-stop-a.json"
DELTA = [*PARENTS, *ADDED, DRIVER, LINT_DRIVER, "tools/p09/verify_formula_policy_revocation.py",
         "tools/p09/tests/test_formula_policy_revocation.py", "implementation/p09/P09-134_FORMULA_POLICY_REVOCATION_REPORT.md"]


def parent_edits():
    for p in PARENTS:
        before, after = (ROOT / ARCHIVES[p]).read_bytes(), (ROOT / p).read_bytes()
        old = b"pub mod registration;\n" if p != PARENTS[2] else b"mod formula_policy_registration;\n"
        new = old + (b"pub mod revocation;\n" if p != PARENTS[2] else
                     b'#[path = "actual_import/formula_policy_revocation.rs"]\nmod formula_policy_revocation;\n')
        require(before.count(old) == 1 and before.replace(old, new) == after, "undeclared_revocation_parent_edit")
    original = (ROOT / INITIAL_SOURCE).read_bytes()
    require(original.count(b'"a".into(), 1') == 1
            and original.replace(b'"a".into(), 1', b'String::from("a"), 1') == (ROOT / PRE_LINT[ADDED[0]]).read_bytes(), "initial_source_transition_drift")
    intermediate = (ROOT / PRE_LINT[ADDED[0]]).read_bytes()
    require(intermediate.count(b'"".into(),') == 1 and intermediate.replace(b'"".into(),', b'String::new(),') == (ROOT / ADDED[0]).read_bytes(), "empty_string_constructor_transition_drift")
    before = (ROOT / PRE_LINT[ADDED[2]]).read_text(encoding="utf-8")
    for old, new in [(".map_err(map_revision_error)?", ".map_err(|error| map_revision_error(&error))?"),
                     ("fn map_revision_error(error: RevisionError)", "fn map_revision_error(error: &RevisionError)"),
                     ("if error == RevisionError::", "if *error == RevisionError::"),
                     ("map_revision_error(RevisionError::", "map_revision_error(&RevisionError::"),
                     ("map_revision_error(e)", "map_revision_error(&e)")]:
        require(before.count(old) == 1, "bridge_borrow_edit_not_unique")
        before = before.replace(old, new)
    require(before == (ROOT / ADDED[2]).read_text(encoding="utf-8"), "undeclared_bridge_borrow_edit")
    before = (ROOT / PRE_LINT[ADDED[3]]).read_text(encoding="utf-8")
    require(before.count("SQL/native NOT_RUN.") == 1 and before.count(".map_err(|_| Error::Repository)?\n                }") == 3, "test_lint_edit_not_unique")
    before = before.replace("SQL/native NOT_RUN.", "SQL/native `NOT_RUN`.").replace(".map_err(|_| Error::Repository)?\n                }", ".map_err(|_| Error::Repository)?;\n                }")
    require(before == (ROOT / ADDED[3]).read_text(encoding="utf-8"), "undeclared_test_lint_edit")


class WholePreimageRoot(type(ROOT)):
    def __truediv__(self, path):
        return ROOT / ARCHIVES.get(str(path).replace("\\", "/"), path)


def predecessor():
    parent_edits()
    require(R.pin(PRE.CURRENT) == {"path": PRE.CURRENT, "bytes": 4784,
            "sha256": "5581fe92ae275c2bbac918aedd4159824547af46b3554abe71086d06e3c164eb"}, "P133_checkpoint_drift")
    pending, seen, roots = [PRE], set(), []
    instruction_dir = Path(__file__).resolve().parent
    while pending:
        module = pending.pop()
        if id(module) in seen:
            continue
        seen.add(id(module))
        if isinstance(getattr(module, "ROOT", None), Path) and module.ROOT == ROOT:
            roots.append((module, module.ROOT))
        for item in vars(module).values():
            if isinstance(item, types.ModuleType) and getattr(item, "__file__", None) and Path(item.__file__).resolve().parent == instruction_dir:
                pending.append(item)
    original_run, original_factory, loaders = subprocess.run, importlib.util.module_from_spec, []

    def historical_run(args, *a, **kw):
        result = original_run(args, *a, **kw)
        if isinstance(args, (list, tuple)) and Path(str(args[0])).name in ("rg", "rg.exe") and "--files" in args and result.returncode == 0 and isinstance(result.stdout, str):
            kept = []
            for line in result.stdout.splitlines():
                path = Path(line)
                try:
                    normalized = (path if path.is_absolute() else ROOT / path).resolve().relative_to(ROOT).as_posix()
                except ValueError:
                    normalized = line.replace("\\", "/")
                if normalized not in ADDED:
                    kept.append(line)
            return subprocess.CompletedProcess(result.args, result.returncode, "\n".join(kept) + ("\n" if result.stdout.endswith("\n") else ""), result.stderr)
        return result

    def historical_factory(spec):
        module = original_factory(spec)
        if spec.origin and Path(spec.origin).resolve().parent == instruction_dir:
            loader, original_exec = spec.loader, spec.loader.exec_module
            def exec_with_preimage(loaded):
                original_exec(loaded)
                if isinstance(getattr(loaded, "ROOT", None), Path) and loaded.ROOT == ROOT:
                    loaded.ROOT = WholePreimageRoot(ROOT)
            loaders.append((loader, original_exec))
            loader.exec_module = exec_with_preimage
        return module

    try:
        for module, _ in roots:
            module.ROOT = WholePreimageRoot(ROOT)
        subprocess.run, importlib.util.module_from_spec = historical_run, historical_factory
        result = PRE.current()
    finally:
        subprocess.run, importlib.util.module_from_spec = original_run, original_factory
        for loader, original_exec in loaders:
            loader.exec_module = original_exec
        for module, original in roots:
            module.ROOT = original
    require(result["current_catalog_executions"] == 15 and result["P09_gate"] == "OPEN", "historical_P133_scope_lost")
    return result


def source_paths(driver=DRIVER):
    result = subprocess.run(["rg", "--threads", "1", "--files", "crates", "protocol/generated/rust", "tools/xtask"], cwd=ROOT,
                            capture_output=True, text=True, encoding="utf-8", check=True, timeout=10)
    return {p.replace("\\", "/") for p in result.stdout.splitlines()} | {
        "Cargo.toml", "Cargo.lock", "implementation/p04/trust/p04-direct-route-attestation.json",
        "implementation/p04/trust/p04-direct-route-attestation.sig", driver, "tools/p09/resource_bounded_test_support.ps1",
        "implementation/p09/tests/p09_132_comment_catalog_index.rs", *PRE.PRE.ARCHIVES.values(), *ARCHIVES.values()}


def protected_pins():
    return PRE.protected_pins() + R.read(PRE.CURRENT)["current_executables"]


def resource(doc):
    require(doc["logical_cpu_limit"] == doc["affinity_mask"] == doc["cargo_jobs"] == 1
            and doc["priority"] == "BelowNormal" and doc["sample_seconds"] == 2
            and doc["cpu_stop_percent"] == 85 and doc["cpu_stop_consecutive_samples"] == 3
            and doc["minimum_available_ram_mib"] == 4096 and doc["maximum_root_working_set_mib"] == 2048
            and 0 < doc["elapsed_seconds"] <= doc["maximum_seconds"], "revocation_resource_policy_drift")
    require(doc["samples"] and doc["samples"][0]["system_cpu_percent"] < 85, "hot_revocation_start")
    hot = 0
    for sample in doc["samples"]:
        cpu = sample["system_cpu_percent"]
        hot = hot + 1 if cpu >= 85 else 0
        require(0 <= cpu <= 100 and hot < 3 and sample["available_ram_mib"] >= 4096
                and 0 <= sample["test_working_set_mib"] <= 2048, "revocation_resource_limits_violated")


def frozen(doc, driver=DRIVER, views=None):
    paths, views = source_paths(driver), views or {}
    rows = doc["source_freeze"]
    require(len(paths) == len(rows) == 781 and {r["path"] for r in rows} == paths, "revocation_source_inventory_drift")
    for row in rows:
        pin = R.pin(views.get(row["path"], row["path"]))
        pin["path"] = row["path"]
        require(pin == row, "revocation_frozen_input_drift")
    require(doc["source_freeze_exact_after"] is True and doc["protected_executables_exact_after"] is True
            and doc["protected_executables"] == protected_pins() and len(protected_pins()) == 15
            and all(R.pin(p["path"]) == p for p in protected_pins()), "revocation_prior_binary_drift")
    require(doc["product_complete"] is False and doc["P09_gate"] == "OPEN", "revocation_scope_promoted")


def validate_run(doc, suite, mode, names, views=None, variant="final"):
    require(doc["schema_version"] == "hwpx-agent.p09-formula-policy-revocation-runtime/v1"
            and doc["state"] == "PASS_SOURCE_ONLY_NOT_GATE" and doc["suite"] == suite and doc["mode"] == mode
            and doc["exit_code"] == 0 and doc["stop_reason"] is None, "revocation_runtime_not_accepted")
    resource(doc)
    frozen(doc, views=views)
    if mode == "Build":
        require(doc["build_marker"] is True and doc["tests"] is None and not doc["build_diagnostics"] and not doc["cargo_failure"], "revocation_build_not_complete")
    else:
        exe = R.RUN + "debug/deps/" + SUITES[suite][0] + "-p134-" + variant + ".exe"
        require(doc["executable_pin"] == R.pin(exe) and doc["expected_test_count"] == len(names), "revocation_current_binary_drift")
        if mode == "List":
            require(len(doc["inventory"]) == len(names) and set(doc["inventory"]) == names, "revocation_case_inventory_drift")
        else:
            validate_summary(doc["tests"], names, 228 if suite == "Revocation" else 0)


def validate_summary(tests, names, filtered=0):
    summary = tests["terminal_summary"]
    require(summary["outcome"] == "ok" and summary["passed"] == len(names)
            and summary["failed"] == summary["ignored"] == summary["measured"] == 0 and summary["filtered"] == filtered
            and len(tests["passed_test_names"]) == len(names) and set(tests["passed_test_names"]) == names
            and not tests["failed_test_names"], "revocation_runtime_coverage_incomplete")


def expected_names(suite):
    listed = R.read(R.RUN + f"p134-{suite.lower()}-list-{('b' if suite in ('Stored', 'Revision') else 'c')}.json")["inventory"]
    names = set(listed)
    require(len(names) == len(listed) and all(re.fullmatch(r"[A-Za-z0-9_:]+", n) for n in names), "revocation_duplicate_case")
    if suite == "Stored":
        new = {"actual_import::formula_policy_revocation::" + n for n in re.findall(r"#\[test\]\s*fn\s+(\w+)", (ROOT / ADDED[3]).read_text(encoding="utf-8"))}
        old = set(R.read(R.LIST)["inventory"])
        require(len(new) == 6 and len(old) == 228 and names == old | new and len(names) == 234, "existing_stored_cases_lost")
    elif suite == "Revocation":
        new = {"actual_import::formula_policy_revocation::" + n for n in re.findall(r"#\[test\]\s*fn\s+(\w+)", (ROOT / ADDED[3]).read_text(encoding="utf-8"))}
        require(len(new) == 6 and names == new, "new_revocation_cases_missing")
    elif suite == "Revision":
        require(len(names) == 22 and {"postgres::source_formula_policy::revocation::tests::" + n for n in re.findall(r"#\[test\]\s*fn\s+(\w+)", (ROOT / ADDED[0]).read_text(encoding="utf-8"))} <= names, "revision_revocation_units_missing")
    else:
        require("form_stored_provider::actual_import::source_policy::formulas::revocation::postgres::tests::ambiguous_commit_is_never_mapped_to_retryable_denial" in names, "ambiguous_commit_unit_missing")
    return names


def failed_runs():
    for stage, path in zip("abc", FAILS):
        doc = R.read(path)
        require(doc["state"] == "NOT_ACCEPTED_STOP_OR_FAILURE" and doc["exit_code"] == 101 and doc["build_marker"] is False
                and doc["mode"] == "Build" and doc["suite"] == "Revision" and doc["stop_reason"] is None, "failed_build_promoted")
        resource(doc)
        frozen(doc, views={**PRE_LINT, DRIVER: FAILED_ARCHIVES[stage], ADDED[0]: INITIAL_SOURCE})
    require(R.read(FAILS[2])["cargo_failure"] == ["error: Option 'test' given more than once", "error: could not compile `revision-service` (lib test)"], "confirmed_duplicate_option_failure_lost")
    stopped = R.read(STOP)
    require(stopped["state"] == "NOT_ACCEPTED_STOP_OR_FAILURE" and stopped["stop_reason"] == "STOP_SUSTAINED_SYSTEM_CPU"
            and stopped["exit_code"] != 0 and stopped["suite"] == "Stored" and stopped["mode"] == "Test"
            and len(stopped["samples"]) >= 3 and all(s["system_cpu_percent"] >= 85 for s in stopped["samples"][-3:])
            and stopped["logical_cpu_limit"] == stopped["cargo_jobs"] == 1 and stopped["priority"] == "BelowNormal"
            and stopped["tests"]["terminal_summary"] is None and len(stopped["tests"]["passed_test_names"]) == 49
            and not stopped["tests"]["failed_test_names"], "stopped_full_regression_promoted")
    frozen(stopped, views={**PRE_LINT, DRIVER: OLD_DRIVER})
    for path in DEFERRED:
        deferred = R.read(path)
        require(deferred["state"] == "DEFERRED_RESOURCE_PRESSURE_NOT_STARTED" and len(deferred["samples"]) == 1
                and deferred["samples"][0]["system_cpu_percent"] >= 85 and "exit_code" not in deferred
                and deferred["P09_gate"] == "OPEN" and deferred["product_complete"] is False, "deferred_start_promoted")
    cross = R.read(CROSSCHECK)
    require(cross["state"] == "MEASURED_READ_ONLY_NOT_TEST_RUN_OR_MONITOR_REPLACEMENT" and cross["stored_test_started"] is False
            and cross["pressure_cause"] == "NOT_DETERMINED" and len(cross["samples"]) == 3, "resource_crosscheck_scope_promoted")
    for path in EARLIER_RUNS:
        doc = R.read(path)
        views = {**PRE_LINT, DRIVER: OLD_DRIVER if doc["suite"] in ("Stored", "Revision") else PRE_LINT[DRIVER]}
        validate_run(doc, doc["suite"], doc["mode"], expected_names(doc["suite"]), views, "current")
    for stage, path in zip("abc", LINT_FAILS[:3]):
        doc = R.read(path)
        require(doc["state"] == "NOT_ACCEPTED_STOP_OR_FAILURE" and doc["exit_code"] == 101 and doc["stop_reason"] is None
                and doc["build_finished_success"] is False, "failed_lint_promoted")
        expected = ["clippy::needless_pass_by_value"] if stage == "a" else ["clippy::doc_markdown"] + ["clippy::semicolon_if_nothing_returned"] * 3 if stage == "b" else ["clippy::manual_string_new"]
        require(sorted(d["code"] for d in doc["diagnostics"]) == sorted(expected), "lint_diagnostics_lost")
        views = {ADDED[0]: PRE_LINT[ADDED[0]]}
        if stage in "ab":
            views[ADDED[3]] = PRE_LINT[ADDED[3]]
        if stage == "a":
            views[ADDED[2]] = PRE_LINT[ADDED[2]]
        frozen(doc, LINT_DRIVER, views)
    stopped_lint = R.read(LINT_FAILS[3])
    require(stopped_lint["state"] == "NOT_ACCEPTED_STOP_OR_FAILURE" and stopped_lint["stop_reason"] == "STOP_SUSTAINED_SYSTEM_CPU"
            and stopped_lint["exit_code"] != 0 and all(s["system_cpu_percent"] >= 85 for s in stopped_lint["samples"][-3:]), "stopped_lint_promoted")
    frozen(stopped_lint, LINT_DRIVER)


def validate_lint(doc):
    require(doc["schema_version"] == "hwpx-agent.p09-current-optimized-workspace-lint/v1"
            and doc["state"] == "PASS_SOURCE_ONLY_NOT_GATE" and doc["mode"] == "workspace_strict_lint"
            and doc["exit_code"] == 0 and doc["stop_reason"] is None and doc["build_finished_success"] is True
            and doc["test_or_app_executed"] is False and not doc["diagnostics"], "revocation_whole_lint_incomplete")
    resource(doc)
    frozen(doc, LINT_DRIVER)
    expected = ["clippy", "--workspace", "--all-targets", "--locked", "--offline", "--jobs", "1", "--target-dir",
                str(ROOT / "target/p09-121-resource-optimized"), "--message-format", "json", "--", "-D", "warnings"]
    require(doc["cargo_arguments"] == expected, "revocation_lint_arguments_drift")
    old = R.read(PRE.RUN)["workspace_inventory"]
    require(doc["workspace_inventory"] == old and len(old) == 358 and {PRE.key(x) for x in doc["workspace_artifacts"]} == {PRE.key(x) for x in old}, "revocation_workspace_target_missing")


def groups():
    return {"source_delta": DELTA, "predecessor_receipts_added": [PRE.CURRENT],
            "source_archives": [*ARCHIVES.values(), *FAILED_ARCHIVES.values(), INITIAL_SOURCE, OLD_DRIVER, *PRE_LINT.values()],
            "runtime_runs": [*FAILS, *SUCCESS, *STORED_PREP, *EARLIER_RUNS, STOP, *DEFERRED, CROSSCHECK, *LINT_FAILS, LINT],
            "migration_inputs": sorted(p.relative_to(ROOT).as_posix() for p in (ROOT / "migrations/postgres").glob("*.up.sql")),
            "current_executables": [R.RUN + "debug/deps/" + stem + "-p134-final.exe" for stem in ("form_stored_provider", "revision_service", "hwpx_agent_cli")],
            "earlier_executables": [R.RUN + "debug/deps/" + stem + "-p134-current.exe" for stem in ("form_stored_provider", "revision_service", "hwpx_agent_cli")]}


def runtime():
    predecessor()
    failed_runs()
    total = 0
    for suite in ("Revision", "Product", "Revocation"):
        names = expected_names(suite)
        for mode in (("List", "Test") if suite == "Revocation" else ("Build", "List", "Test")):
            stage = ("e" if mode == "Build" else "b") if suite == "Revision" else "c"
            validate_run(R.read(R.RUN + f"p134-{suite.lower()}-{mode.lower()}-{stage}.json"), suite, mode, names)
        total += len(names)
    names = expected_names("Stored")
    for path, mode in zip(STORED_PREP, ("Build", "List")):
        validate_run(R.read(path), "Stored", mode, names)
    validate_lint(R.read(LINT))
    return {"state": "PASS_SOURCE_FORMULA_POLICY_REVOCATION_FULL_REGRESSION_RESOURCE_DEFERRED_NOT_SQL_OR_GATE", "test_executions": total,
            "current_full_stored234_accepted": False, "revocation_cases": 6, "revision_cases": 22, "product_cases": len(expected_names("Product")),
            "P09_gate": "OPEN", "product_complete": False}


def current():
    result = runtime()
    doc = R.read(CURRENT)
    for name, paths in groups().items():
        rows = doc[name]
        require(len(rows) == len(paths) and {r["path"] for r in rows} == set(paths) and all(R.pin(r["path"]) == r for r in rows), "P134_pin_coverage_drift")
    require(doc["state"] == result["state"] and doc["goal_status"] == "active" and doc["P09_gate"] == "OPEN"
            and doc["product_complete"] is False and doc["P10_new_implementation"] is False
            and doc["actual_sql_accepted"] is False and doc["production_issuer_accepted"] is False and doc["native_application_accepted"] is False
            and doc["current_full_stored234_accepted"] is False
            and doc["current_test_executions"] == result["test_executions"] and doc["remaining_coarse_groups_minimum"] == 6
            and doc["remaining_groups_closed_by_slice"] == 0 and len(doc["migration_inputs"]) == 21, "P134_scope_promoted")
    require(doc["previous_source_files_count"] == 1165 and doc["current_source_files_count"] == 1174
            and doc["inherited_raw_pin_entries"] == 2959 and doc["guard_units_passed"] == 13
            and doc["current_whole_workspace_runtime_accepted"] is False
            and doc["current_workspace_strict_lint_accepted"] is True, "P134_inventory_scope_drift")
    return result


if __name__ == "__main__":
    try:
        print(json.dumps(runtime() if "--runtime" in sys.argv[1:] else current(), separators=(",", ":")))
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        code = str(error) if isinstance(error, ValueError) and str(error).replace("_", "").isalnum() else "redacted"
        print(json.dumps({"state": "FAIL_CLOSED", "error_code": code, "P09_gate": "OPEN"}))
        raise SystemExit(1) from None
