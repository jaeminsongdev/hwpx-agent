"""P132 exact typed-comment optimization; historical evidence is not current/native acceptance."""
import importlib.util
import json
import re
import statistics
import types
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p131_preserved", Path(__file__).with_name("verify_table_review_regression_progress.py"))
PRE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PRE)
ROOT, R, require = PRE.ROOT, PRE.R, PRE.require
PARENT = "crates/domain-ir/src/comment_model.rs"
TEST_PARENT = "crates/domain-ir/tests/comment_style_section_protection.rs"
ARCHIVES = {p: "implementation/p09/source-archive/p09-132-pre-comment-catalog-index/" + p for p in (PARENT, TEST_PARENT)}
OVERLAY = "implementation/p09/tests/p09_132_comment_catalog_index.rs"
DRIVER = "tools/p09/run_comment_catalog_regression.ps1"
PREVIOUS = PRE.CURRENT
CURRENT = "implementation/p09/evidence/p09-132-comment-catalog-optimization.source-progress.v1.json"
SUITES = {"Catalog": ("comment_style_section_protection", 15), "Model": ("comment_model", 10),
          "Operation": ("comment_operation", 16), "Stored": ("stored_comment_provider", 24)}
RUNNER_ARCHIVES = [R.RUN + "p132-initial-profile-runner.ps1.txt", R.RUN + "p132-initial-package-runner.ps1.txt"]
FAILED_RUNS = [R.RUN + "p132-catalog-test-a.json", R.RUN + "p132-operation-build-a.json", R.RUN + "p132-operation-build-b.json"]
DELTA = [PARENT, TEST_PARENT, OVERLAY, DRIVER, "tools/p09/verify_comment_catalog_optimization.py",
         "tools/p09/tests/test_comment_catalog_optimization.py", "implementation/p09/P09-132_COMMENT_CATALOG_OPTIMIZATION_REPORT.md"]
APPEND = b'''\n// Current production/baseline equivalence and resource-bounded catalog profiling.
#[path = "../../../implementation/p09/tests/p09_132_comment_catalog_index.rs"]
mod catalog_index;
'''
EDITS = [
    (b"    validate_comment(comment, &target.authors, &target.styles, limits)?;\n", b'''    validate_comment(
        comment,
        |id| target.authors.iter().any(|author| author.author_id == id),
        |id| target.styles.iter().any(|style| style.style_id == id),
        limits,
    )?;
'''),
    (b"        &target.authors,\n", b"        |id| target.authors.iter().any(|author| author.author_id == id),\n"),
    (b"        validate_comment(comment, &state.authors, &state.styles, limits)?;\n", b'''        // Reuse already validated IDs: do not scan both complete catalogs per comment.
        validate_comment(
            comment,
            |id| author_ids.contains(&id),
            |id| style_ids.contains(&id),
            limits,
        )?;
'''),
    (b"    authors: &[CommentAuthor],\n    styles: &[CommentStyle],\n", b"    author_exists: impl Fn(u32) -> bool,\n    style_exists: impl Fn(u32) -> bool,\n"),
    (b'''        || !authors
            .iter()
            .any(|author| author.author_id == comment.author_id)
''', b"        || !author_exists(comment.author_id)\n"),
    (b'''        || !styles
            .iter()
            .any(|style| style.style_id == comment.style_id)
''', b"        || !style_exists(comment.style_id)\n"),
    (b"    validate_resolution(&comment.resolution, comment.created_at, authors)?;\n",
     b"    validate_resolution(&comment.resolution, comment.created_at, author_exists)?;\n"),
    (b"    authors: &[CommentAuthor],\n", b"    author_exists: impl Fn(u32) -> bool,\n"),
    (b"                && authors.iter().any(|author| author.author_id == author_id)\n",
     b"                && author_exists(author_id)\n"),
]


def validate_inverse(before, after):
    expected = before
    for old, new in EDITS:
        require(expected.count(old) == 1, "declared_catalog_edit_not_unique")
        expected = expected.replace(old, new, 1)
    require(expected == after, "undeclared_comment_parent_edit")


class WholePreimageRoot(type(ROOT)):
    def __truediv__(self, path):
        return ROOT / ARCHIVES.get(str(path).replace("\\", "/"), path)


def predecessor():
    require(R.pin(PREVIOUS) == {"path": PREVIOUS, "bytes": 6664,
            "sha256": "dbc5d827ae16ebb9614a9ca6d520603de5efbb65e8b7e55366c4bd0dc6ab93f5"}, "P131_checkpoint_drift")
    for p, size, sha in [(PARENT, 55861, "7e5ff615134ca42c51114a98bf03c462b5812227b4aacac01feef6b271c55462"),
                         (TEST_PARENT, 4943, "0362dde09b32eabcfd2e66db36ae4c85a2c54a6997559c524c586e098b22ed35")]:
        require(R.pin(ARCHIVES[p]) == {"path": ARCHIVES[p], "bytes": size, "sha256": sha}, "whole_comment_preimage_drift")
    validate_inverse((ROOT / ARCHIVES[PARENT]).read_bytes(), (ROOT / PARENT).read_bytes())
    require((ROOT / TEST_PARENT).read_bytes() == (ROOT / ARCHIVES[TEST_PARENT]).read_bytes() + APPEND,
            "undeclared_comment_test_parent_edit")
    pending, visited, roots = [PRE], set(), []
    instruction_dir = Path(__file__).resolve().parent
    while pending:
        module = pending.pop()
        if id(module) in visited:
            continue
        visited.add(id(module))
        if isinstance(getattr(module, "ROOT", None), Path) and module.ROOT == ROOT:
            roots.append((module, module.ROOT))
        for value in vars(module).values():
            if isinstance(value, types.ModuleType) and getattr(value, "__file__", None):
                if Path(value.__file__).resolve().parent == instruction_dir:
                    pending.append(value)
    require(roots, "historical_module_roots_missing")
    original_factory, loaders = importlib.util.module_from_spec, []

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
        importlib.util.module_from_spec = historical_factory
        result = PRE.current()
    finally:
        importlib.util.module_from_spec = original_factory
        for loader, original_exec in loaders:
            loader.exec_module = original_exec
        for module, original in roots:
            module.ROOT = original
    require(result["test_executions"] == 67, "historical_table_coverage_lost")
    return result


def run_path(suite, mode):
    attempt = "c" if (suite, mode) == ("Operation", "Build") else "b" if (suite, mode) == ("Catalog", "Test") else "a"
    return R.RUN + f"p132-{suite.lower()}-{mode.lower()}-{attempt}.json"


def expected_names():
    def names(path):
        return set(re.findall(r"#\[test\]\s*fn\s+([A-Za-z0-9_]+)", (ROOT / path).read_text(encoding="utf-8")))
    result = {"Catalog": names(ARCHIVES[TEST_PARENT]) | {"catalog_index::" + n for n in names(OVERLAY)}
              | {"catalog_index::" + m + "::private_tests::private_plan_tampering_is_rejected" for m in ("baseline", "embedded")},
              "Model": names("crates/domain-ir/tests/comment_model.rs")}
    for suite, stem in (("Operation", "comment_operation"), ("Stored", "stored_comment_provider")):
        result[suite] = names(f"crates/product-cli/tests/{stem}.rs") | {
            "rich_bodies::" + n for n in names(f"crates/product-cli/tests/{stem}/rich_bodies.rs")}
    require(all(len(result[k]) == c for k, (_, c) in SUITES.items()), "current_comment_test_inventory_drift")
    return result


def source_paths():
    return (PRE.source_paths() - {PRE.DRIVER}) | {DRIVER, OVERLAY, *ARCHIVES.values()}


def validate_profile(doc):
    require(doc["schema"] == "hwpx-agent.p09-comment-catalog-profile/v1"
            and doc["scope"] == "isolated_validate_document_state_not_end_to_end"
            and doc["authors"] == doc["styles"] == 4096 and doc["comments"] == 2048 and doc["rounds"] == 7
            and doc["native_verified"] is False and doc["product_complete"] is False, "profile_scope_promoted")
    a, b = doc["before_ns"], doc["after_ns"]
    require(len(a) == len(b) == 7 and all(type(n) is int and n > 0 for n in a + b), "profile_observations_missing")
    require(statistics.median(b) < statistics.median(a), "isolated_validator_speedup_not_observed")
    return {"before_median_ms": round(statistics.median(a) / 1e6, 3),
            "after_median_ms": round(statistics.median(b) / 1e6, 3),
            "observed_isolated_speedup": round(statistics.median(a) / statistics.median(b), 2)}


def validate_run(doc, suite, mode, names):
    stem, count = SUITES[suite]
    require(doc["schema_version"] == "hwpx-agent.p09-comment-catalog-regression/v1"
            and doc["state"] == "PASS_SOURCE_ONLY_NOT_GATE" and doc["mode"] == mode and doc["suite"] == suite
            and doc["expected_test_count"] == count and doc["exit_code"] == 0 and doc["stop_reason"] is None
            and doc["source_freeze_exact_after"] is True and doc["protected_executables_exact_after"] is True, "comment_runtime_not_accepted")
    require(doc["logical_cpu_limit"] == doc["affinity_mask"] == doc["cargo_jobs"] == 1
            and doc["priority"] == "BelowNormal" and doc["sample_seconds"] == 2 and doc["cpu_stop_percent"] == 85
            and doc["cpu_stop_consecutive_samples"] == 3 and doc["minimum_available_ram_mib"] == 4096
            and doc["maximum_root_working_set_mib"] == 2048 and 0 < doc["elapsed_seconds"] <= doc["maximum_seconds"], "comment_resource_policy_drift")
    require(doc["samples"] and doc["samples"][0]["system_cpu_percent"] < 85, "comment_baseline_not_startable")
    hot = 0
    for sample in doc["samples"]:
        cpu = sample["system_cpu_percent"]
        hot = hot + 1 if cpu >= 85 else 0
        require(0 <= cpu <= 100 and hot < 3 and sample["available_ram_mib"] >= 4096
                and 0 <= sample["test_working_set_mib"] <= 2048, "comment_resource_observation_violated")
    paths = source_paths()
    exact = []
    for row in doc["source_freeze"]:
        driver_view = (R.RUN + "p132-initial-profile-runner.ps1.txt" if suite == "Catalog" and mode in ("Build", "List")
                       else R.RUN + "p132-initial-package-runner.ps1.txt" if suite in ("Catalog", "Model") else DRIVER)
        actual = R.pin(driver_view if row["path"] == DRIVER else row["path"])
        actual["path"] = row["path"]
        exact.append(actual == row)
    require(len(paths) == len(doc["source_freeze"]) == 774 and {r["path"] for r in doc["source_freeze"]} == paths
            and all(exact), "current_comment_source_drift")
    protected = R.read(PRE.PRE.RUNS[1])["protected_executables"] + R.read(PREVIOUS)["current_executables"]
    require(len(protected) == 10 and doc["protected_executables"] == protected
            and all(R.pin(r["path"]) == r for r in protected), "prior_executable_changed")
    require(doc["product_complete"] is False and doc["P09_gate"] == "OPEN", "comment_runtime_scope_promoted")
    if mode == "Build":
        require(doc["build_marker"] is True and doc["tests"] is None, "comment_build_receipt_drift")
    else:
        pin = doc["executable_pin"]
        require(pin["path"] == R.RUN + f"debug/deps/{stem}-p132-current.exe" and R.pin(pin["path"]) == pin, "current_comment_executable_drift")
        if mode == "List":
            require(len(doc["inventory"]) == count and set(doc["inventory"]) == names, "comment_compiled_inventory_drift")
        else:
            test, summary = doc["tests"], doc["tests"]["terminal_summary"]
            require(summary["outcome"] == "ok" and summary["passed"] == count
                    and summary["failed"] == summary["ignored"] == summary["filtered"] == summary["measured"] == 0
                    and len(test["passed_test_names"]) == count and set(test["passed_test_names"]) == names
                    and not test["failed_test_names"], "current_comment_runtime_coverage_drift")
    if suite == "Catalog" and mode == "Test":
        validate_profile(doc["catalog_profile"])
    else:
        require(doc["catalog_profile"] is None, "unexpected_profile")
    return count if mode == "Test" else 0


def runtime():
    predecessor()
    validate_runner_transition_and_failures()
    names = expected_names()
    total = sum(validate_run(R.read(run_path(suite, mode)), suite, mode, names[suite])
                for suite in SUITES for mode in ("Build", "List", "Test"))
    require(total == 65, "comment_execution_total_drift")
    return {"state": "PASS_CURRENT_COMMENT_CATALOG_OPTIMIZATION_NOT_NATIVE_OR_GATE", "test_executions": 65,
            "profile": validate_profile(R.read(run_path("Catalog", "Test"))["catalog_profile"]),
            "P09_gate": "OPEN", "product_complete": False}


def validate_runner_transition_and_failures():
    for path, size, sha in zip(RUNNER_ARCHIVES, (13777, 13779),
                             ("11a251b8db6ced516c89ad1ea46e0b4d9a80f6fe23e459d2b987c11ebfad1a71",
                              "1245d65df44fd1d0d4632b71353e45c6e954e1d5739e135355465ee3900a9487")):
        require(R.pin(path) == {"path": path, "bytes": size, "sha256": sha}, "initial_runner_archive_drift")
    a, b, current = [(ROOT / p).read_bytes() for p in [*RUNNER_ARCHIVES, DRIVER]]
    require(a.count(b"'--nocapture'") == 1 and a.replace(b"'--nocapture'", b"'--show-output'") == b,
            "undeclared_profile_runner_transition")
    require(b.count(b"Package='product-cli'") == 2
            and b.replace(b"Package='product-cli'", b"Package='hwpx-agent-cli'") == current,
            "undeclared_package_runner_transition")
    catalog, package, deferred = [R.read(p) for p in FAILED_RUNS]
    require(catalog["state"] == package["state"] == "NOT_ACCEPTED_STOP_OR_FAILURE"
            and catalog["exit_code"] == 0 and catalog["stop_reason"] == "RUNNER_OR_OBSERVATION_FAILURE"
            and package["exit_code"] == 101 and package["stop_reason"] is None
            and catalog["source_freeze_exact_after"] is False and package["source_freeze_exact_after"] is True
            and catalog["catalog_profile"] is None and package["tests"] is None
            and package["build_marker"] is False, "failed_attempt_promoted_or_lost")
    summary = catalog["tests"]["terminal_summary"]
    require(summary["outcome"] == "ok" and summary["passed"] == 15
            and summary["failed"] == summary["ignored"] == summary["filtered"] == summary["measured"] == 0
            and set(catalog["tests"]["passed_test_names"]) == expected_names()["Catalog"] - {
                "catalog_index::isolated_validator_profile_records_actual_before_after_only"}, "initial_profile_collection_failure_lost")
    for doc, archive in ((catalog, RUNNER_ARCHIVES[0]), (package, RUNNER_ARCHIVES[1])):
        require(doc["product_complete"] is False and doc["P09_gate"] == "OPEN", "failed_scope_promoted")
        rows = doc["source_freeze"]
        require(len(rows) == 774 and {r["path"] for r in rows} == source_paths(), "failed_source_coverage_drift")
        for row in rows:
            pin = R.pin(archive if row["path"] == DRIVER else row["path"])
            pin["path"] = row["path"]
            require(pin == row, "failed_source_pin_drift")
    require(deferred["state"] == "DEFERRED_RESOURCE_PRESSURE_NOT_STARTED"
            and len(deferred["samples"]) == 1 and deferred["samples"][0]["system_cpu_percent"] == 100
            and deferred["samples"][0]["test_working_set_mib"] == 0 and "exit_code" not in deferred
            and deferred["P09_gate"] == "OPEN" and deferred["product_complete"] is False, "deferred_start_promoted")


def checkpoint_groups():
    return {"source_delta": DELTA, "predecessor_receipts_added": [PREVIOUS],
            "source_archives": [*ARCHIVES.values(), *RUNNER_ARCHIVES],
            "runtime_runs": [run_path(s, m) for s in SUITES for m in ("Build", "List", "Test")],
            "current_executables": [R.RUN + f"debug/deps/{stem}-p132-current.exe" for stem, _ in SUITES.values()],
            "failed_or_deferred_runs": FAILED_RUNS}


def current():
    result = runtime()
    doc = R.read(CURRENT)
    for key, paths in checkpoint_groups().items():
        rows = doc[key]
        require(len(rows) == len(paths) and {r["path"] for r in rows} == set(paths)
                and all(R.pin(r["path"]) == r for r in rows), "P132_pin_coverage_drift")
    require(doc["schema_version"] == "hwpx-agent.p09-comment-catalog-optimization/v1"
            and doc["state"] == result["state"] and doc["goal_status"] == "active"
            and doc["P09_gate"] == "OPEN" and doc["product_complete"] is False and doc["P10_new_implementation"] is False
            and doc["previous_source_files_count"] == 1155 and doc["current_source_files_count"] == 1160
            and doc["inherited_raw_pin_entries"] == 2909 and doc["runtime_guard_units_passed"] == 16
            and doc["test_executions"] == 65 and doc["current_source_inputs"] == 774
            and doc["failed_or_deferred_attempts_preserved"] == 3 and doc["whole_preimages"] == 2
            and doc["isolated_validator_optimization_observed"] is True
            and doc["current_comment_runtime_accepted"] is True
            and doc["current_whole_workspace_runtime_accepted"] is False
            and doc["current_whole_workspace_lint_accepted"] is False
            and doc["actual_sql_accepted"] is False and doc["native_application_accepted"] is False, "P132_scope_promoted")
    result.update({"current_source_files": 1160, "guard_units": 16, "failed_or_deferred_attempts_preserved": 3})
    return result


if __name__ == "__main__":
    try:
        print(json.dumps(current(), separators=(",", ":")))
    except (OSError, ValueError, KeyError, TypeError) as error:
        code = str(error) if isinstance(error, ValueError) and str(error).replace("_", "").isalnum() else "redacted"
        print(json.dumps({"state": "FAIL_CLOSED", "error_code": code, "error_type": type(error).__name__, "P09_gate": "OPEN"}))
        raise SystemExit(1) from None
