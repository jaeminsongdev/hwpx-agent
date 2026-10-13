#!/usr/bin/env python3
"""Actual unchanged legacy negative-case parity plus current public API qualification."""
from __future__ import annotations
import argparse
import importlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.p09 import qualify_form_input_public_export as current
from tools.p09 import run_legacy_domain_contract_view as worker

ROOT = current.ROOT
q, public = current.q, current.public
CAPSULE = "implementation/p09/evidence/p09-38-atomic-form-input-public-export.current-2020.v1.json"
CAPSULE_SHA = "2be9751323aa0d01d9dfcc57a461156df8b80eb201ed2d6e24b6c99fbe9764b0"
WORKER = "tools/p09/run_legacy_domain_contract_view.py"
SOURCES = (WORKER, "tools/p09/qualify_legacy_domain_contract_regression.py",
           "tools/p09/tests/test_legacy_domain_contract_regression.py",
           "implementation/p09/P09-39_LEGACY_DOMAIN_REGRESSION_POLICY.md")
CASE_COUNTS = {
    "citation": ((5,5),(5,5),(1,0),(2,0),(3,3)),
    "comment_model": ((4,4),(4,4),(1,0),(3,0),(2,2)),
    "cross_reference": ((5,5),(4,4),(1,0),(3,0),(2,2)),
    "field_core": ((3,3),(4,4),(1,0),(3,0),(2,2)),
    "form_control": ((4,4),(4,4),(1,0),(3,0),(2,2)),
    "link_reference": ((4,4),(4,4),(1,0),(3,0),(2,2)),
    "mail_merge": ((5,5),(5,5),(1,0),(2,0),(3,3)),
    "note_engine": ((4,4),(4,4),(1,0),(3,0),(2,2)),
    "reference_auxiliary": ((4,4),(5,5),(1,0),(2,0),(3,3)),
    "toc_index": ((5,5),(4,4),(1,0),(3,0),(2,2)),
}


def authority(root=ROOT):
    value = q.shared.lifecycle.checked_json(root / CAPSULE, CAPSULE_SHA)
    for path, digest in value["source_sha256"].items():
        public.checked(root / path, digest)
    current.authority(root)
    return value


def blueprint(root=ROOT):
    authority(root)
    paths = {WORKER, "tools/p09/__init__.py", "tools/p09/tests/__init__.py"}
    tests, validators, expected = [], [], []
    for name, digest in current.LEGACY_P09.items():
        public.checked(root / "tools/p09" / name, digest)
        module_name = "tools.p09." + name[:-3]
        module = importlib.import_module(module_name)
        if Path(module.__file__).resolve() != ROOT / "tools/p09" / name:
            raise ValueError("legacy_regression_validator_import_outside_repository")
        validator_path = "tools/p09/" + name
        test_path = "tools/p09/tests/test_" + name.removeprefix("validate_")
        test_module = test_path.removesuffix(".py").replace("/", ".")
        validators.append(module_name); tests.append(test_module)
        expected.extend(worker.test_names(public.bounded_bytes(root / test_path, 2*1024*1024), test_module))
        paths.update((validator_path, test_path, module.CONTRACT, module.MIGRATION, module.POLICY,
                      module.REPORT, module.QUALIFICATION, *module.SOURCE_SHA256, *module.IMPLEMENTATION_SHA256))
        for path, pinned in {**module.SOURCE_SHA256, **module.IMPLEMENTATION_SHA256}.items():
            original = current.ARCHIVE if path == current.LIB else path
            raw = public.bounded_bytes(root / original, 2*1024*1024)
            if q.sha(raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")) != pinned:
                raise ValueError("legacy_regression_original_contract_source_lock_changed")
    copied = {path: public.bounded_bytes(root / (current.ARCHIVE if path == current.LIB else path), 2*1024*1024) for path in sorted(paths)}
    if len(copied) > 128 or sum(map(len, copied.values())) > 4*1024*1024:
        raise ValueError("legacy_regression_view_size_limit")
    manifest = {"schema_version": worker.SCHEMA, "scope": "archived_domain_library_not_current_workspace_or_native_pass",
                "source_sha256": {path: q.sha(raw) for path, raw in copied.items()},
                "validator_modules": validators, "test_modules": tests, "test_names": sorted(expected)}
    if len(expected) != 50 or len(set(expected)) != 50:
        raise ValueError("legacy_regression_complete_original_test_inventory_changed")
    return copied, manifest


def prepare_view(root, copied, manifest):
    if root.is_symlink() or root.is_junction() or list(root.iterdir()):
        raise ValueError("legacy_regression_view_root_not_empty_regular_directory")
    if set(copied) != set(manifest["source_sha256"]):
        raise ValueError("legacy_regression_copy_inventory_invalid")
    for path, raw in copied.items():
        worker.relative(path)
        if q.sha(raw) != manifest["source_sha256"][path]:
            raise ValueError("legacy_regression_copy_digest_invalid")
        destination = root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as stream:
            stream.write(raw)
    (root / "scratch").mkdir()
    with (root / worker.MANIFEST).open("xb") as stream:
        stream.write(q.shared.lifecycle.canonical_bytes(manifest))
    worker.snapshot(manifest, root)


def verify_result(value, manifest):
    expected_keys = {"schema_version", "scope", "manifest_sha256", "baselines", "tests", "passed", "failed", "skipped",
                     "positive_methods", "negative_methods", "validation_calls_observed", "subtests_observed",
                     "original_sources_unchanged", "validator_functions_or_defaults_replaced", "current_workspace_legacy_aggregate_pass",
                     "cargo_or_native_session_started", "raw_document_values_or_absolute_paths_present", "green_rows"}
    if type(value) is not dict or set(value) != expected_keys:
        raise ValueError("legacy_regression_actual_result_shape_invalid")
    static = {"schema_version": worker.SCHEMA, "scope": manifest["scope"],
              "manifest_sha256": q.sha(q.shared.lifecycle.canonical_bytes(manifest)), "passed": 50, "failed": 0, "skipped": 0,
              "positive_methods": 10, "negative_methods": 40, "original_sources_unchanged": True,
              "validator_functions_or_defaults_replaced": False, "current_workspace_legacy_aggregate_pass": False,
              "cargo_or_native_session_started": False, "raw_document_values_or_absolute_paths_present": False, "green_rows": 0}
    q.exact({key: value[key] for key in static}, static, "legacy_regression_actual_result_claims_invalid")
    baselines = value["baselines"]
    if type(baselines) is not list or len(baselines) != 10 or any(type(row) is not dict for row in baselines) or [row.get("module") for row in baselines] != manifest["validator_modules"]:
        raise ValueError("legacy_regression_actual_baseline_inventory_invalid")
    for row in baselines:
        if set(row) != {"module", "schema_version", "state", "errors"} or row["state"] != "pass" or row["errors"] != [] or type(row["schema_version"]) is not str or not re.fullmatch(r"hwpx-agent\.p09-[a-z-]+-validation/v1", row["schema_version"]):
            raise ValueError("legacy_regression_actual_positive_baseline_invalid")
    records = value["tests"]
    if type(records) is not list or len(records) != 50 or any(type(row) is not dict for row in records) or [row.get("name") for row in records] != manifest["test_names"]:
        raise ValueError("legacy_regression_actual_test_inventory_invalid")
    for row in records:
        if type(row) is not dict or set(row) != {"name", "state", "validation_calls", "observed_validator_state", "observed_original_library_sha256", "subtests_observed"}:
            raise ValueError("legacy_regression_actual_test_shape_invalid")
        expected = "pass" if ".test_current_contract_" in row["name"] else "fail"
        q.exact({key: row[key] for key in ("state", "observed_validator_state", "observed_original_library_sha256")},
                {"state": "pass", "observed_validator_state": expected, "observed_original_library_sha256": current.OLD_LIB},
                "legacy_regression_actual_validation_observation_invalid")
        if type(row["validation_calls"]) is not int or not 1 <= row["validation_calls"] <= 32 or type(row["subtests_observed"]) is not int or not 0 <= row["subtests_observed"] <= 32:
            raise ValueError("legacy_regression_actual_case_count_invalid")
    q.exact(value["validation_calls_observed"], sum(row["validation_calls"] for row in records), "legacy_regression_actual_call_count_mismatch")
    q.exact(value["subtests_observed"], sum(row["subtests_observed"] for row in records), "legacy_regression_actual_subtest_count_mismatch")
    q.exact(value["validation_calls_observed"], 146, "legacy_regression_full_original_call_count_changed")
    q.exact(value["subtests_observed"], 109, "legacy_regression_full_original_subtest_count_changed")
    for key, expected in CASE_COUNTS.items():
        prefix = "tools.p09.tests.test_" + key + "_contract."
        actual = [(row["validation_calls"], row["subtests_observed"]) for row in records if row["name"].startswith(prefix)]
        if actual != list(expected):
            raise ValueError("legacy_regression_exact_original_per_case_counts_changed")


def run_view(root=ROOT):
    copied, manifest = blueprint(root)
    parent = root / "fixtures/target-build"
    if any(path.is_symlink() or path.is_junction() for path in (parent, *parent.parents)) or not parent.is_dir():
        raise ValueError("legacy_regression_disposable_parent_invalid")
    with tempfile.TemporaryDirectory(prefix="p09-39-archived-contract-", dir=parent) as temporary:
        view = Path(temporary).resolve(); view.relative_to(parent.resolve())
        prepare_view(view, copied, manifest)
        env = dict(os.environ)
        for key in ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP"):
            env.pop(key, None)
        env.update({key: str(view / "scratch") for key in ("TMP", "TEMP", "TMPDIR")})
        process = subprocess.run([sys.executable, "-I", "-S", "-B", WORKER], cwd=view, env=env,
                                 capture_output=True, timeout=60,
                                 creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
        if process.returncode or not 0 < len(process.stdout) <= 256*1024 or len(process.stderr) > 128*1024:
            error_code = "legacy_regression_actual_isolated_worker_failed"
            try:
                failure = json.loads(process.stdout, object_pairs_hook=worker.duplicate_guard)
                if set(failure) == {"state", "error_code"} and failure["state"] == "fail" and re.fullmatch(r"[a-z_]+", failure["error_code"]):
                    error_code = failure["error_code"]
            except (ValueError, TypeError, UnicodeError):
                pass
            raise ValueError(error_code)
        value = json.loads(process.stdout, object_pairs_hook=worker.duplicate_guard)
        verify_result(value, manifest)
        worker.snapshot(manifest, view)
    fresh, fresh_manifest = blueprint(root)
    if copied != fresh or manifest != fresh_manifest:
        raise ValueError("legacy_regression_original_sources_changed_during_view")
    return {"source_sha256": manifest["source_sha256"], "original_library_source_origin": current.ARCHIVE,
            "copied_files": len(copied), "copied_bytes": sum(map(len, copied.values())), "manifest": manifest,
            "actual_isolated_test_result": value, "temporary_view_cleaned": True,
            "cargo_node_modules_git_or_private_evidence_copied": False, "python_isolated_no_site_no_bytecode": True}


def qualify(root=ROOT):
    before = {path: q.sha(public.bounded_bytes(root / path, 2*1024*1024)) for path in SOURCES}
    capsule = authority(root)
    public_replay = current.qualify(root)
    if q.shared.lifecycle.canonical_bytes(public_replay) != public.checked(root / CAPSULE, CAPSULE_SHA, 512*1024):
        raise ValueError("legacy_regression_current_public_capsule_not_reproduced")
    archived = run_view(root)
    q.exact(archived["manifest"]["test_names"], [row["name"] for row in archived["actual_isolated_test_result"]["tests"]], "legacy_regression_named_original_tests_changed")
    q.exact(capsule, authority(root), "legacy_regression_predecessor_changed")
    q.exact(before, {path: q.sha(public.bounded_bytes(root / path, 2*1024*1024)) for path in SOURCES}, "legacy_regression_new_sources_changed")
    return {"schema_version": "hwpx-agent.p09-39-legacy-domain-regression-successor/v1", "task": "P09-39",
            "state": "archived_contract_negative_parity_and_actual_current_public_api_qualified_non_green",
            "source_sha256": before, "predecessor_capsule_sha256": CAPSULE_SHA,
            "actual_current_public_capsule_byte_exact_reproduction": True,
            "actual_current_public_compiled_test_suites": public_replay["compiled_test_suites"],
            "actual_current_legacy_failures_preserved": public_replay["actual_legacy_current_validators"],
            "actual_current_predecessor_failures_preserved": public_replay["actual_predecessor_current_failures"],
            "archived_contract_regression": archived,
            "claims": {"complete_ten_unchanged_original_contract_suites_executed": True,
                       "every_negative_actual_validation_return_and_original_library_observed": True,
                       "current_public_input_api_compiled_and_reproduced": True,
                       "current_workspace_legacy_aggregate_pass": False, "original_tests_or_validators_rewritten": False,
                       "source_locks_refreshed_or_validator_functions_replaced": False,
                       "archived_view_is_current_full_workspace_or_native_pass": False,
                       "native_input_output_qualified": False, "production_routing_qualified": False,
                       "new_native_execution": False, "render": "not_run", "product_differential": "not_run", "green_rows": 0, "p09_complete": False},
            "future_native_diagnostic_batch": public_replay["future_native_diagnostic_batch"],
            "privacy": {"raw_document_text_present": False, "absolute_private_paths_present": False,
                        "native_session_started": False, "trust_or_registry_changed": False}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(); group.add_argument("--output", type=Path); group.add_argument("--verify", type=Path)
    args = parser.parse_args()
    try:
        value = qualify(); raw = q.shared.lifecycle.canonical_bytes(value)
        if args.output:
            path = args.output.absolute(); q.shared.within(path.parent, ROOT / "implementation/p09/evidence")
            if "private" in path.relative_to(ROOT).parts or path.is_symlink() or path.is_junction():
                raise ValueError("legacy_regression_public_evidence_boundary_invalid")
            with path.open("xb") as stream: stream.write(raw)
        if args.verify and public.bounded_bytes(args.verify, 512*1024) != raw:
            raise ValueError("legacy_regression_capsule_reproduction_mismatch")
    except (OSError, ValueError, KeyError, TypeError, UnicodeError, subprocess.SubprocessError) as error:
        code = str(error) if type(error) is ValueError and re.fullmatch(r"[a-z_]+", str(error)) else "legacy_regression_verification_failed"
        print(json.dumps({"state": "fail", "error_code": code})); return 2
    print(json.dumps({"state": "pass", "qualification_sha256": q.sha(raw), "archived_original_contract_tests_passed": 50,
                      "actual_current_public_tests_passed": 18, "native_session_started": False, "green_rows": 0})); return 0


if __name__ == "__main__":
    raise SystemExit(main())
