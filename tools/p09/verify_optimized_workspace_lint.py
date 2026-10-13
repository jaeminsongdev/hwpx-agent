"""P133 current optimized default-feature workspace lint, not whole-runtime/native/Gate evidence."""
import importlib.util
import json
import subprocess
import types
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p132_preserved", Path(__file__).with_name("verify_comment_catalog_optimization.py"))
PRE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PRE)
ROOT, R, require = PRE.ROOT, PRE.R, PRE.require
DRIVER = "tools/p09/run_optimized_workspace_lint.ps1"
PREVIOUS = PRE.CURRENT
CURRENT = "implementation/p09/evidence/p09-133-optimized-workspace-lint.source-progress.v1.json"
RUN = R.RUN + "p133-workspace-lint-d.json"
CATDRIVER = "tools/p09/run_catalog_lint_regression.ps1"
PARENTS = [PRE.OVERLAY, PRE.TEST_PARENT]
ARCHIVES = {p: "implementation/p09/source-archive/p09-133-pre-catalog-lint/" + p for p in PARENTS}
INTERMEDIATE = R.RUN + "p133-intermediate-catalog-fixture.rs.txt"
LINT_RUNS = [R.RUN + f"p133-workspace-lint-{stage}.json" for stage in "abcd"]
CAT_RUNS = [R.RUN + f"p133-catalog-{mode}-a.json" for mode in ("build", "list", "test")]
EXE = R.RUN + "debug/deps/comment_style_section_protection-p133-current.exe"
DELTA = [*PARENTS, DRIVER, CATDRIVER, "tools/p09/verify_optimized_workspace_lint.py", "tools/p09/tests/test_optimized_workspace_lint.py",
         "implementation/p09/P09-133_OPTIMIZED_WORKSPACE_LINT_REPORT.md"]


def key(item):
    return item["package_id"], item["name"], tuple(item["kind"])


def source_paths():
    return PRE.source_paths() - {PRE.DRIVER} | {DRIVER}


def protected_pins():
    return (R.read(PRE.PRE.PRE.RUNS[1])["protected_executables"]
            + R.read(PRE.PRE.CURRENT)["current_executables"] + R.read(PREVIOUS)["current_executables"])


def validate_fixture_transition(before, intermediate, after):
    helper = '''    pub fn revalidate(s: &CommentDocumentState, l: CommentLimits) -> Result<(), CommentError> {
        validate_document_state(s, l)
    }
'''
    require(before.count(helper) == 2, "fixture_helpers_not_exact")
    expected = before.replace(helper, "").replace("mod baseline {\n", "pub mod baseline {\n" + helper)
    expected = expected.replace("mod embedded {\n", "pub mod embedded {\n" + helper)
    for old, new, count in [
        ("operation: Value)", "operation: &Value)", 1),
        ("request_json(&value, op)?", "request_json(&value, &op)?", 2),
        ("request_json(&original, operations(&original)[1].clone())?", "request_json(&original, &operations(&original)[1])?", 1),
        ("request_json(&original, operations(&original)[4].clone())?", "request_json(&original, &operations(&original)[4])?", 1),
        ('        json!({"kind":"set_visibility","target":original["comments"][0]["identity"],"visibility":"shown"}),\n',
         '        &json!({"kind":"set_visibility","target":original["comments"][0]["identity"],"visibility":"shown"}),\n', 1),
        ("                old_ns.push(elapsed)\n", "                old_ns.push(elapsed);\n", 1),
        ("                new_ns.push(elapsed)\n", "                new_ns.push(elapsed);\n", 1),
    ]:
        require(expected.count(old) == count, "fixture_edit_not_unique")
        expected = expected.replace(old, new)
    require(expected == intermediate, "undeclared_fixture_edit")
    for stage, doc in [("baseline", "baseline"), ("embedded", "current")]:
        old = f"pub mod {stage} {{\n"
        new = old + f'''    /// Revalidates the complete {doc} state without decoding or serializing it.
    /// # Errors
    /// Returns the {'original' if stage == 'baseline' else 'current'} model's exact validation error for the supplied state/limits.
'''
        require(expected.count(old) == 1, "fixture_error_docs_not_unique")
        expected = expected.replace(old, new, 1)
    require(expected == after, "undeclared_fixture_docs_edit")


class WholePreimageRoot(type(ROOT)):
    def __truediv__(self, path):
        return ROOT / ARCHIVES.get(str(path).replace("\\", "/"), path)


def predecessor():
    require(R.pin(PREVIOUS) == {"path": PREVIOUS, "bytes": 7250,
            "sha256": "7728ff57230979aa2513943de4d6264fa5ca2ead3bf327b5feb62ecde051a948"}, "P132_checkpoint_drift")
    for p, size, sha in [(PRE.OVERLAY, 16616, "3e250f94571d93a6c5ee75da21e682433a8c93083acc3f5efd3ca2e0e091e97d"),
                         (PRE.TEST_PARENT, 5125, "ac996695bd2cf364f9978ba5be2a062cb8f9236870c229b49ca6ded7331f9da4")]:
        require(R.pin(ARCHIVES[p]) == {"path": ARCHIVES[p], "bytes": size, "sha256": sha}, "lint_fixture_preimage_drift")
    require(R.pin(INTERMEDIATE) == {"path": INTERMEDIATE, "bytes": 16616,
            "sha256": "997900c410aee6b2ac73f33a811a9d8265582d01594874f03119869a7dfd3af9"}, "intermediate_fixture_drift")
    validate_fixture_transition((ROOT / ARCHIVES[PRE.OVERLAY]).read_text(encoding="utf-8"),
                                (ROOT / INTERMEDIATE).read_text(encoding="utf-8"), (ROOT / PRE.OVERLAY).read_text(encoding="utf-8"))
    before, after = [(ROOT / p).read_bytes() for p in (ARCHIVES[PRE.TEST_PARENT], PRE.TEST_PARENT)]
    require(before.count(b"mod catalog_index;\n") == 1
            and before.replace(b"mod catalog_index;\n", b"pub mod catalog_index;\n") == after, "undeclared_test_export_edit")
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
    require(result["test_executions"] == 65, "historical_comment_regression_lost")
    return result


def validate_lint(doc):
    require(doc["schema_version"] == "hwpx-agent.p09-current-optimized-workspace-lint/v1"
            and doc["mode"] == "workspace_strict_lint" and doc["state"] == "PASS_SOURCE_ONLY_NOT_GATE"
            and doc["exit_code"] == 0 and doc["stop_reason"] is None and doc["build_finished_success"] is True
            and doc["source_freeze_exact_after"] is True and doc["protected_executables_exact_after"] is True, "optimized_lint_not_accepted")
    expected = ["clippy", "--workspace", "--all-targets", "--locked", "--offline", "--jobs", "1", "--target-dir",
                str(ROOT / "target/p09-121-resource-optimized"), "--message-format", "json", "--", "-D", "warnings"]
    require(doc["cargo_arguments"] == expected, "optimized_strict_arguments_drift")
    require(doc["logical_cpu_limit"] == doc["affinity_mask"] == doc["cargo_jobs"] == 1
            and doc["priority"] == "BelowNormal" and doc["sample_seconds"] == 2 and doc["cpu_stop_percent"] == 85
            and doc["cpu_stop_consecutive_samples"] == 3 and doc["minimum_available_ram_mib"] == 4096
            and doc["maximum_root_working_set_mib"] == 2048 and 0 < doc["elapsed_seconds"] <= doc["maximum_seconds"], "optimized_lint_resource_policy_drift")
    require(doc["samples"] and doc["samples"][0]["system_cpu_percent"] < 85, "optimized_lint_hot_baseline")
    hot = 0
    for sample in doc["samples"]:
        cpu = sample["system_cpu_percent"]
        hot = hot + 1 if cpu >= 85 else 0
        require(0 <= cpu <= 100 and hot < 3 and sample["available_ram_mib"] >= 4096
                and 0 <= sample["test_working_set_mib"] <= 2048, "optimized_lint_resource_observation_violated")
    require(doc["test_or_app_executed"] is False and doc["product_complete"] is False and doc["P09_gate"] == "OPEN",
            "optimized_lint_scope_promoted")
    paths = source_paths()
    rows = doc["source_freeze"]
    require(len(paths) == len(rows) == 774 and {r["path"] for r in rows} == paths
            and all(R.pin(r["path"]) == r for r in rows), "optimized_lint_source_inventory_drift")
    pins = protected_pins()
    require(len(pins) == 14 and doc["protected_executables"] == pins
            and all(R.pin(p["path"]) == p for p in pins), "optimized_lint_prior_executable_drift")
    metadata = json.loads(subprocess.run(["cargo", "metadata", "--format-version", "1", "--no-deps", "--locked", "--offline"],
                          cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=True, timeout=10).stdout)
    inventory = [{"package_id": p["id"], "package": p["name"], "name": t["name"], "kind": t["kind"],
                  "src_path": Path(t["src_path"]).relative_to(ROOT).as_posix()} for p in metadata["packages"] for t in p["targets"]]
    require(doc["workspace_inventory"] == inventory and len(metadata["workspace_members"]) == 32
            and not any("custom-build" in t["kind"] for p in metadata["packages"] for t in p["targets"]), "optimized_workspace_metadata_drift")
    expected_keys = {key(i) for i in inventory}
    artifacts = doc["workspace_artifacts"]
    require(len(inventory) == len(expected_keys) == 358 and len({i["package_id"] for i in inventory}) == 32
            and {key(a) for a in artifacts} == expected_keys, "optimized_whole_workspace_lint_incomplete")
    require(all(set(a) == {"package_id", "name", "kind", "test_profile", "fresh"}
                and type(a["fresh"]) is bool and type(a["test_profile"]) is bool
                and ("test" not in a["kind"] or a["test_profile"] is True) for a in artifacts), "optimized_artifact_profile_drift")
    for diagnostic in doc["diagnostics"]:
        require(set(diagnostic) == {"level", "code", "spans"} and diagnostic["level"] not in ("error", "warning"), "optimized_lint_diagnostic_failure")
        for span in diagnostic["spans"]:
            require(set(span) == {"path", "line_start", "line_end", "column_start", "column_end"}
                    and span["path"] in paths and span["path"].endswith(".rs")
                    and 1 <= span["line_start"] <= span["line_end"] and span["column_start"] >= 1 and span["column_end"] >= 1,
                    "optimized_diagnostic_span_drift")
    return {"workspace_packages": 32, "workspace_targets": 358, "artifact_records": len(artifacts),
            "protected_executables": 14, "source_inputs": 774}


def validate_failed_lint():
    success = R.read(RUN)
    expected_keys = {key(i) for i in success["workspace_inventory"]}
    for stage, expected_codes, overlay_view in [
        ("a", ["clippy::items_after_test_module"] * 2 + ["clippy::struct_field_names"] * 4
         + ["clippy::needless_pass_by_value"] + ["clippy::semicolon_if_nothing_returned"] * 2, ARCHIVES[PRE.OVERLAY]),
        ("b", ["clippy::missing_errors_doc"] * 2, INTERMEDIATE),
    ]:
        doc = R.read(R.RUN + f"p133-workspace-lint-{stage}.json")
        require(doc["state"] == "NOT_ACCEPTED_STOP_OR_FAILURE" and doc["exit_code"] == 101
                and doc["stop_reason"] is None and doc["build_finished_success"] is False
                and doc["source_freeze_exact_after"] is True and doc["protected_executables_exact_after"] is True
                and doc["cargo_arguments"] == success["cargo_arguments"] and doc["workspace_inventory"] == success["workspace_inventory"]
                and doc["test_or_app_executed"] is False and doc["product_complete"] is False and doc["P09_gate"] == "OPEN",
                "failed_lint_promoted_or_lost")
        require(doc["logical_cpu_limit"] == doc["affinity_mask"] == doc["cargo_jobs"] == 1
                and doc["priority"] == "BelowNormal" and doc["minimum_available_ram_mib"] == 4096
                and doc["cpu_stop_percent"] == 85 and doc["cpu_stop_consecutive_samples"] == 3, "failed_lint_policy_drift")
        rows = doc["source_freeze"]
        require(len(rows) == 774 and {r["path"] for r in rows} == source_paths(), "failed_lint_source_coverage_drift")
        for row in rows:
            path = (overlay_view if row["path"] == PRE.OVERLAY else ARCHIVES[PRE.TEST_PARENT]
                    if stage == "a" and row["path"] == PRE.TEST_PARENT else row["path"])
            pin = R.pin(path)
            pin["path"] = row["path"]
            require(pin == row, "failed_lint_preimage_pin_drift")
        require(doc["protected_executables"] == protected_pins()
                and {key(i) for i in doc["workspace_artifacts"]} <= expected_keys, "failed_lint_inventory_drift")
        diagnostics = doc["diagnostics"]
        require(sorted(d["code"] for d in diagnostics) == sorted(expected_codes)
                and all(set(d) == {"level", "code", "spans"} and d["level"] == "error" for d in diagnostics), "initial_lint_errors_lost")
        for diagnostic in diagnostics:
            for span in diagnostic["spans"]:
                normalized = (ROOT / span["path"]).resolve().relative_to(ROOT).as_posix()
                require(set(span) == {"path", "line_start", "line_end", "column_start", "column_end"}
                        and normalized in source_paths() and normalized.endswith(".rs")
                        and 1 <= span["line_start"] <= span["line_end"], "failed_lint_diagnostic_scope_drift")
    deferred = R.read(LINT_RUNS[2])
    require(deferred["state"] == "DEFERRED_RESOURCE_PRESSURE_NOT_STARTED" and len(deferred["samples"]) == 1
            and deferred["samples"][0]["system_cpu_percent"] == 97 and deferred["samples"][0]["test_working_set_mib"] == 0
            and "exit_code" not in deferred and deferred["P09_gate"] == "OPEN" and deferred["product_complete"] is False,
            "deferred_lint_start_promoted")


def validate_catalog(doc, mode):
    names = PRE.expected_names()["Catalog"]
    require(doc["schema_version"] == "hwpx-agent.p09-comment-catalog-regression/v1" and doc["state"] == "PASS_SOURCE_ONLY_NOT_GATE"
            and doc["mode"] == mode and doc["suite"] == "Catalog" and doc["expected_test_count"] == 15
            and doc["exit_code"] == 0 and doc["stop_reason"] is None and doc["source_freeze_exact_after"] is True
            and doc["protected_executables_exact_after"] is True, "current_lint_catalog_not_accepted")
    require(doc["logical_cpu_limit"] == doc["affinity_mask"] == doc["cargo_jobs"] == 1
            and doc["priority"] == "BelowNormal" and doc["minimum_available_ram_mib"] == 4096
            and doc["maximum_root_working_set_mib"] == 2048 and doc["cpu_stop_percent"] == 85
            and doc["cpu_stop_consecutive_samples"] == 3 and doc["sample_seconds"] == 2
            and 0 < doc["elapsed_seconds"] <= doc["maximum_seconds"], "catalog_resource_policy_drift")
    require(doc["samples"] and doc["samples"][0]["system_cpu_percent"] < 85, "catalog_hot_baseline")
    hot = 0
    for sample in doc["samples"]:
        cpu = sample["system_cpu_percent"]
        hot = hot + 1 if cpu >= 85 else 0
        require(0 <= cpu <= 100 and hot < 3 and sample["available_ram_mib"] >= 4096
                and 0 <= sample["test_working_set_mib"] <= 2048, "catalog_resource_observation_violated")
    paths = source_paths() - {DRIVER} | {CATDRIVER}
    require(len(paths) == len(doc["source_freeze"]) == 774 and {r["path"] for r in doc["source_freeze"]} == paths
            and all(R.pin(r["path"]) == r for r in doc["source_freeze"]), "current_catalog_source_drift")
    require(doc["protected_executables"] == protected_pins() and doc["product_complete"] is False and doc["P09_gate"] == "OPEN",
            "current_catalog_scope_promoted")
    if mode == "Build":
        require(doc["build_marker"] is True and doc["tests"] is None, "catalog_build_marker_missing")
    else:
        require(doc["executable_pin"] == R.pin(EXE), "current_catalog_executable_drift")
        if mode == "List":
            require(len(doc["inventory"]) == 15 and set(doc["inventory"]) == names, "current_catalog_list_drift")
        else:
            summary = doc["tests"]["terminal_summary"]
            require(summary["outcome"] == "ok" and summary["passed"] == 15
                    and summary["failed"] == summary["ignored"] == summary["measured"] == summary["filtered"] == 0
                    and len(doc["tests"]["passed_test_names"]) == 15 and set(doc["tests"]["passed_test_names"]) == names
                    and not doc["tests"]["failed_test_names"], "current_catalog_runtime_incomplete")
            return PRE.validate_profile(doc["catalog_profile"])
    require(doc["catalog_profile"] is None, "unexpected_catalog_profile")
    return None


def runtime():
    predecessor()
    result = validate_lint(R.read(RUN))
    validate_failed_lint()
    for path, mode in zip(CAT_RUNS, ("Build", "List", "Test")):
        profile = validate_catalog(R.read(path), mode)
    return {"state": "PASS_CURRENT_OPTIMIZED_WORKSPACE_LINT_NOT_RUNTIME_OR_GATE", **result,
            "preserved_P132_comment_executions": 65, "current_catalog_executions": 15, "profile": profile,
            "P09_gate": "OPEN", "product_complete": False}


def checkpoint_groups():
    return {"source_delta": DELTA, "predecessor_receipts_added": [PREVIOUS],
            "source_archives": [*ARCHIVES.values(), INTERMEDIATE], "runtime_runs": LINT_RUNS + CAT_RUNS,
            "current_executables": [EXE]}


def current():
    result = runtime()
    doc = R.read(CURRENT)
    for k, paths in checkpoint_groups().items():
        rows = doc[k]
        require(len(rows) == len(paths) and {r["path"] for r in rows} == set(paths)
                and all(R.pin(r["path"]) == r for r in rows), "P133_pin_coverage_drift")
    require(doc["schema_version"] == "hwpx-agent.p09-current-optimized-workspace-lint/v1"
            and doc["state"] == result["state"] and doc["goal_status"] == "active"
            and doc["previous_source_files_count"] == 1160 and doc["current_source_files_count"] == 1165
            and doc["inherited_raw_pin_entries"] == 2940 and doc["runtime_guard_units_passed"] == 16
            and doc["workspace_packages"] == 32 and doc["workspace_targets"] == 358
            and doc["current_workspace_strict_lint_accepted"] is True and doc["preserved_P132_comment_executions"] == 65
            and doc["current_catalog_executions"] == 15 and doc["failed_lint_attempts_preserved"] == 2
            and doc["deferred_lint_starts_preserved"] == 1
            and doc["current_whole_workspace_runtime_accepted"] is False and doc["actual_sql_accepted"] is False
            and doc["native_application_accepted"] is False and doc["product_complete"] is False
            and doc["P09_gate"] == "OPEN" and doc["P10_new_implementation"] is False, "P133_scope_promoted")
    result.update({"current_source_files": 1165, "guard_units": 16})
    return result


if __name__ == "__main__":
    try:
        print(json.dumps(current(), separators=(",", ":")))
    except (OSError, ValueError, KeyError, TypeError) as error:
        code = str(error) if isinstance(error, ValueError) and str(error).replace("_", "").isalnum() else "redacted"
        print(json.dumps({"state": "FAIL_CLOSED", "error_code": code, "error_type": type(error).__name__, "P09_gate": "OPEN"}))
        raise SystemExit(1) from None
