"""P130 strict workspace lint and whole preimage preservation, not runtime/Gate acceptance."""
import argparse
import importlib.util
import json
import subprocess
import types
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p129_preserved", Path(__file__).with_name("verify_current_stored_regression.py"))
OLD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(OLD)
ROOT = OLD.ROOT
PARENTS = ["crates/hwpx-package/tests/review_table_create_context.rs", "crates/hwpx-package/tests/table_create_hwpx.rs"]
ARCHIVES = {p: "implementation/p09/source-archive/p09-130-pre-test-root-visibility/" + p for p in PARENTS}
PREVIOUS = OLD.CURRENT
CURRENT = "implementation/p09/evidence/p09-130-workspace-strict-lint.source-progress.v1.json"
RUNS = [OLD.R.RUN + f"p130-workspace-lint-{stage}.json" for stage in ("a", "b")]
DELTA = PARENTS + ["tools/p09/run_resource_bounded_workspace_lint.ps1", "tools/p09/verify_workspace_lint_progress.py",
                   "tools/p09/tests/test_workspace_lint_progress.py", "implementation/p09/P09-130_WORKSPACE_STRICT_LINT_REPORT.md"]


def require(value, code):
    if not value:
        raise ValueError(code)


def validate_inverse(before, after):
    require(before.count(b"pub(super) fn ") == 4 and after.count(b"pub(crate) fn ") == 4
            and after.replace(b"pub(crate) fn ", b"pub(super) fn ") == before, "undeclared_test_parent_edit")


class WholePreimageRoot(type(ROOT)):
    """Path-compatible cwd; exactly two explicit file reads map to complete originals."""
    def __truediv__(self, path):
        normalized = str(path).replace("\\", "/")
        return ROOT / ARCHIVES.get(normalized, path)


def predecessor():
    require(OLD.R.pin(PREVIOUS) == {"path": PREVIOUS, "bytes": 52630,
            "sha256": "9ff1849bf9bfbab571b045d92259f7384fb62283d6d45be0aebf1c155e33c09a"}, "P129_checkpoint_drift")
    old_pins = [(18535, "bcb2f5dd92a7e1b66654b67d4d548002ff675f346563d825c16bf3b75d082b07"),
                (28561, "e72301a5b231ebeb097d5bf87d0c633ddd360e340ec52fa2aebe016dcb6a689d")]
    for parent, (size, digest) in zip(PARENTS, old_pins):
        archive = ARCHIVES[parent]
        require(OLD.R.pin(archive) == {"path": archive, "bytes": size, "sha256": digest}, "whole_preimage_drift")
        validate_inverse((ROOT / archive).read_bytes(), (ROOT / parent).read_bytes())
    pending, visited, roots = [OLD], set(), []
    while pending:
        module = pending.pop()
        if id(module) in visited:
            continue
        visited.add(id(module))
        if isinstance(getattr(module, "ROOT", None), Path) and module.ROOT == ROOT:
            roots.append((module, module.ROOT))
        for value in vars(module).values():
            if isinstance(value, types.ModuleType) and getattr(value, "__file__", None):
                if Path(value.__file__).resolve().parent == Path(__file__).resolve().parent:
                    pending.append(value)
    require(roots, "historical_module_roots_missing")
    original_factory = importlib.util.module_from_spec
    loaders = []

    def historical_factory(spec):
        module = original_factory(spec)
        # R.historical() imports P128 locally. Apply the same declared read view
        # after those fresh P09 modules initialize; no audit function is replaced.
        if spec.origin and Path(spec.origin).resolve().parent == Path(__file__).resolve().parent:
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
        result = OLD.audit()
    finally:
        importlib.util.module_from_spec = original_factory
        for loader, original_exec in loaders:
            loader.exec_module = original_exec
        for module, original in roots:
            module.ROOT = original
    return {"state": "PASS_P129_HISTORICAL_ON_TWO_WHOLE_PREIMAGES_NOT_NEW_RUNTIME",
            "historical_scoped_cases": result["actual_import"] + result["documents"] + result["roots"],
            "whole_preimages": 2, "inverse_bytes_exact": True, "old_guard_functions_unmodified": True,
            "P09_gate": "OPEN", "product_complete": False}


def validate_lint(doc, successful):
    require(doc["schema_version"] == "hwpx-agent.p09-workspace-strict-lint/v1"
            and doc["mode"] == "workspace_strict_lint" and doc["stop_reason"] is None
            and doc["source_freeze_exact_after"] is True and doc["protected_executables_exact_after"] is True,
            "lint_receipt_not_accepted")
    require(doc["logical_cpu_limit"] == doc["affinity_mask"] == doc["cargo_jobs"] == 1
            and doc["priority"] == "BelowNormal" and doc["sample_seconds"] == 2
            and doc["cpu_stop_percent"] == 85 and doc["cpu_stop_consecutive_samples"] == 3
            and doc["minimum_available_ram_mib"] == 4096 and doc["maximum_root_working_set_mib"] == 2048
            and 0 < doc["elapsed_seconds"] <= doc["maximum_seconds"], "lint_resource_policy_drift")
    require(doc["samples"] and doc["samples"][0]["system_cpu_percent"] < 85, "lint_baseline_not_startable")
    hot = 0
    for sample in doc["samples"]:
        cpu = sample["system_cpu_percent"]
        hot = hot + 1 if cpu >= 85 else 0
        require(0 <= cpu <= 100 and hot < 3 and sample["available_ram_mib"] >= 4096
                and 0 <= sample["test_working_set_mib"] <= 2048, "lint_observed_resource_violation")
    require(doc["test_or_app_executed"] is False and doc["product_complete"] is False
            and doc["P09_gate"] == "OPEN", "lint_scope_promoted")
    expected = ["clippy", "--workspace", "--all-targets", "--locked", "--offline", "--jobs", "1", "--target-dir",
                str(ROOT / "target/p09-121-resource-optimized"), "--message-format", "json", "--", "-D", "warnings"]
    require(doc["cargo_arguments"] == expected, "strict_lint_arguments_drift")
    listed = subprocess.run(["rg", "--files", "crates", "protocol/generated/rust", "tools/xtask"], cwd=ROOT,
                            capture_output=True, text=True, check=True, timeout=10).stdout.splitlines()
    expected_sources = {p.replace("\\", "/") for p in listed} | {
        "Cargo.toml", "Cargo.lock", "implementation/p04/trust/p04-direct-route-attestation.json",
        "implementation/p04/trust/p04-direct-route-attestation.sig", "tools/p09/run_resource_bounded_workspace_lint.ps1",
        "tools/p09/resource_bounded_test_support.ps1"}
    require(len(expected_sources) == 770 and {r["path"] for r in doc["source_freeze"]} == expected_sources,
            "lint_source_inventory_drift")
    for row in doc["source_freeze"]:
        if not successful and row["path"] in ARCHIVES:
            actual = OLD.R.pin(ARCHIVES[row["path"]])
            actual["path"] = row["path"]
        else:
            actual = OLD.R.pin(row["path"])
        require(row == actual, "lint_source_drift")
    require(len(doc["source_freeze"]) == 770 and len({r["path"] for r in doc["source_freeze"]}) == 770
            and len(doc["protected_executables"]) == 6
            and all(OLD.R.pin(r["path"]) == r for r in doc["protected_executables"]), "lint_input_or_executable_coverage_drift")
    def key(item):
        return item["package_id"], item["name"], tuple(item["kind"])
    inventory = doc["workspace_inventory"]
    metadata = json.loads(subprocess.run(["cargo", "metadata", "--format-version", "1", "--no-deps", "--locked", "--offline"],
                          cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=True, timeout=10).stdout)
    expected_inventory = [{"package_id": p["id"], "package": p["name"], "name": t["name"], "kind": t["kind"],
                           "src_path": Path(t["src_path"]).relative_to(ROOT).as_posix()}
                          for p in metadata["packages"] for t in p["targets"]]
    require(inventory == expected_inventory and not any("custom-build" in t["kind"] for p in metadata["packages"] for t in p["targets"]),
            "current_workspace_metadata_drift")
    expected_keys = {key(item) for item in inventory}
    require(len(inventory) == len(expected_keys) == 358 and len({r["package_id"] for r in inventory}) == 32,
            "workspace_inventory_drift")
    observed = {key(item) for item in doc["workspace_artifacts"]}
    require(observed <= expected_keys, "unexpected_workspace_artifact")
    require(all(type(item["fresh"]) is bool and type(item["test_profile"]) is bool
                and ("test" not in item["kind"] or item["test_profile"] is True) for item in doc["workspace_artifacts"]),
            "artifact_profile_drift")
    for diagnostic in doc["diagnostics"]:
        require(set(diagnostic) == {"level", "code", "spans"}, "diagnostic_raw_payload_forbidden")
        for span in diagnostic["spans"]:
            require(set(span) == {"path", "line_start", "line_end", "column_start", "column_end"}
                    and span["path"] in expected_sources and span["path"].endswith(".rs")
                    and 1 <= span["line_start"] <= span["line_end"] and span["column_start"] >= 1 and span["column_end"] >= 1,
                    "diagnostic_span_drift")
    if successful:
        require(doc["state"] == "PASS_SOURCE_ONLY_NOT_GATE" and doc["exit_code"] == 0
                and doc["build_finished_success"] is True and observed == expected_keys
                and not any(d["level"] in ("error", "warning") for d in doc["diagnostics"]), "whole_workspace_lint_incomplete")
    else:
        errors = [d for d in doc["diagnostics"] if d["level"] == "error"]
        require(doc["state"] == "NOT_ACCEPTED_STOP_OR_FAILURE" and doc["exit_code"] == 101
                and doc["build_finished_success"] is False and len(errors) == 4
                and all(d["code"] == "E0433" for d in errors)
                and {s["line_start"] for d in errors for s in d["spans"]} == {23, 40, 47, 54}, "initial_compile_failure_lost")
    return {"successful": successful, "workspace_targets": len(expected_keys), "observed_targets": len(observed)}


def current():
    previous = predecessor()
    lint_runs = [validate_lint(OLD.R.read(path), i == 1) for i, path in enumerate(RUNS)]
    doc = OLD.R.read(CURRENT)
    groups = {"source_delta": DELTA, "predecessor_receipts_added": [PREVIOUS],
              "source_archives": [*ARCHIVES.values(), "target/p09-121-resource-optimized/p130-initial-preimage-audit.py.txt"],
              "runtime_runs": RUNS}
    for key, paths in groups.items():
        rows = doc[key]
        require(len(rows) == len(paths) and {r["path"] for r in rows} == set(paths)
                and all(OLD.R.pin(r["path"]) == r for r in rows), "P130_pin_coverage_drift")
    require(doc["schema_version"] == "hwpx-agent.p09-workspace-strict-lint/v1"
            and doc["state"] == "PASS_CURRENT_WORKSPACE_STRICT_LINT_NOT_RUNTIME_OR_GATE"
            and doc["previous_source_files_count"] == 1147 and doc["current_source_files_count"] == 1151
            and doc["inherited_raw_pin_entries"] == 2869 and doc["runtime_guard_units_passed"] == 19
            and doc["workspace_packages"] == 32 and doc["workspace_targets"] == 358
            and doc["current_workspace_strict_lint_accepted"] is True
            and doc["current_whole_workspace_runtime_accepted"] is False
            and doc["product_complete"] is False and doc["P09_gate"] == "OPEN"
            and doc["P10_new_implementation"] is False and doc["goal_status"] == "active", "P130_scope_promoted")
    return {"state": "PASS_CURRENT_WORKSPACE_STRICT_LINT_NOT_RUNTIME_OR_GATE", "workspace_packages": 32,
            "workspace_targets": 358, "whole_preimages": 2, "inverse_bytes_exact": True,
            "historical_scoped228_preserved": previous["historical_scoped_cases"] == 228,
            "lint_runs": lint_runs, "current_source_files": 1151, "P09_gate": "OPEN", "product_complete": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--historical", action="store_true")
    args = parser.parse_args()
    try:
        result = predecessor() if args.historical else current()
        print(json.dumps(result, separators=(",", ":")))
    except (OSError, ValueError, KeyError, TypeError) as error:
        code = str(error) if isinstance(error, ValueError) and str(error).replace("_", "").isalnum() else "redacted"
        print(json.dumps({"state": "FAIL_CLOSED", "error_type": type(error).__name__, "error_code": code, "P09_gate": "OPEN"}))
        raise SystemExit(1) from None
