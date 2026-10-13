#!/usr/bin/env python3
"""Execute unchanged legacy Python contracts in a declared archived-source view."""
from __future__ import annotations
import ast
import hashlib
import importlib
import io
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = "legacy-view-manifest.json"
LIB = "crates/domain-ir/src/lib.rs"
OLD_LIB = "b4726732a47175205a7e35f3aa8e018e66b2a0fbada144bebeac3f395540c058"
SCHEMA = "hwpx-agent.p09-39-archived-domain-contract-view/v1"


def duplicate_guard(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("legacy_view_duplicate_json_key")
        value[key] = item
    return value


def relative(value):
    if type(value) is not str or not value or "\\" in value or ":" in value or any(part in ("", ".", "..") for part in value.split("/")):
        raise ValueError("legacy_view_relative_path_invalid")
    path = Path(value)
    if path.is_absolute() or path.as_posix() != value:
        raise ValueError("legacy_view_relative_path_invalid")
    return value


def read(path, maximum=2*1024*1024):
    if any(item.is_symlink() or item.is_junction() for item in (path, *path.parents)):
        raise ValueError("legacy_view_reparse_path_rejected")
    if not path.is_file() or not 0 < path.stat().st_size <= maximum:
        raise ValueError("legacy_view_file_size_invalid")
    with path.open("rb") as stream:
        raw = stream.read(maximum+1)
    if not 0 < len(raw) <= maximum:
        raise ValueError("legacy_view_file_size_invalid")
    return raw


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def test_names(raw, module_name):
    tree = ast.parse(raw.decode("utf-8"))
    names = [module_name + "." + node.name + "." + method.name for node in tree.body
             if isinstance(node, ast.ClassDef) for method in node.body
             if isinstance(method, ast.FunctionDef) and method.name.startswith("test_")]
    if len(names) != 5 or len(set(names)) != 5 or sum(".test_current_contract_" in name for name in names) != 1:
        raise ValueError("legacy_view_original_test_inventory_invalid")
    return sorted(names)


def snapshot(manifest, root=ROOT):
    if type(manifest) is not dict or set(manifest) != {"schema_version", "source_sha256", "validator_modules", "test_modules", "test_names", "scope"}:
        raise ValueError("legacy_view_manifest_shape_invalid")
    if manifest["schema_version"] != SCHEMA or manifest["scope"] != "archived_domain_library_not_current_workspace_or_native_pass":
        raise ValueError("legacy_view_scope_invalid")
    mapping = manifest["source_sha256"]
    if type(mapping) is not dict or not 1 <= len(mapping) <= 128:
        raise ValueError("legacy_view_source_inventory_invalid")
    for path, digest in mapping.items():
        relative(path)
        if type(digest) is not str or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise ValueError("legacy_view_source_digest_invalid")
        if sha(read(root / path)) != digest:
            raise ValueError("legacy_view_source_digest_changed")
    if mapping.get(LIB) != OLD_LIB:
        raise ValueError("legacy_view_archived_library_identity_invalid")
    allowed_files = set(mapping) | {MANIFEST}
    found = set()
    for path in root.rglob("*"):
        if path.is_symlink() or path.is_junction():
            raise ValueError("legacy_view_reparse_path_rejected")
        if path.is_file():
            found.add(path.relative_to(root).as_posix())
    if found != allowed_files or sum((root/path).stat().st_size for path in found) > 4*1024*1024:
        raise ValueError("legacy_view_complete_file_inventory_changed")
    for key in ("validator_modules", "test_modules", "test_names"):
        values = manifest[key]
        if type(values) is not list or any(type(value) is not str for value in values) or len(set(values)) != len(values):
            raise ValueError("legacy_view_named_inventory_invalid")
    if len(manifest["validator_modules"]) != 10 or len(manifest["test_modules"]) != 10 or len(manifest["test_names"]) != 50:
        raise ValueError("legacy_view_complete_test_inventory_invalid")
    names = []
    for module in [*manifest["validator_modules"], *manifest["test_modules"]]:
        if not re.fullmatch(r"tools\.p09\.(?:tests\.test_|validate_)[a-z_]+_contract", module):
            raise ValueError("legacy_view_module_inventory_invalid")
        raw = read(root / (module.replace(".", "/") + ".py"))
        if module in manifest["test_modules"]:
            names.extend(test_names(raw, module))
    if sorted(names) != manifest["test_names"]:
        raise ValueError("legacy_view_named_test_inventory_changed")
    return sha(read(root / MANIFEST, 128*1024))


class ObservedResult(unittest.TestResult):
    def __init__(self, code_inventory):
        super().__init__()
        self.codes = code_inventory
        self.active = None
        self.tests = []
        self.observations = {}
        self.subtests = {}
        self.pending = {}

    def startTest(self, test):
        super().startTest(test)
        self.active = test.id()
        self.observations[self.active] = []
        self.subtests[self.active] = 0

    def stopTest(self, test):
        super().stopTest(test)
        self.active = None

    def addSuccess(self, test):
        super().addSuccess(test)
        self.tests.append(test.id())

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        self.subtests[test.id()] += 1

    def profile(self, frame, event, arg):
        if frame.f_code not in self.codes or self.active is None:
            return
        if event == "call":
            try:
                root = frame.f_locals["root"]
                root.resolve().relative_to(ROOT)
                source = sha(read(root / LIB, 128*1024))
            except (OSError, ValueError, KeyError, AttributeError, TypeError):
                source = "invalid_or_outside_view"
            self.pending[id(frame)] = (self.active, source)
        elif event == "return":
            active, source = self.pending.pop(id(frame), (self.active, "unobserved_call"))
            state = arg.get("state") if type(arg) is dict else "invalid_return"
            self.observations[active].append({"source_library_sha256": source, "state": state})


def execute():
    if not sys.flags.isolated or not sys.flags.no_site or not sys.dont_write_bytecode:
        raise ValueError("legacy_view_python_isolation_required")
    manifest_raw = read(ROOT / MANIFEST, 128*1024)
    manifest = json.loads(manifest_raw, object_pairs_hook=duplicate_guard)
    digest = snapshot(manifest)
    sys.path.insert(0, str(ROOT))
    modules = [importlib.import_module(name) for name in [*manifest["validator_modules"], *manifest["test_modules"]]]
    for module in modules:
        actual = Path(module.__file__).resolve()
        if actual != ROOT / (module.__name__.replace(".", "/") + ".py"):
            raise ValueError("legacy_view_import_outside_view")
    validators = modules[:10]
    baselines = []
    for module in validators:
        if module.ROOT != ROOT:
            raise ValueError("legacy_view_original_validator_root_changed")
        value = module.validate()
        if value.get("state") != "pass" or value.get("errors") != []:
            raise ValueError("legacy_view_original_positive_baseline_failed")
        baselines.append({"module": module.__name__, "schema_version": value["schema_version"], "state": "pass", "errors": []})
    suite = unittest.defaultTestLoader.loadTestsFromNames(manifest["test_modules"])
    result = ObservedResult({module.validate.__code__ for module in validators})
    # Read-only standard profiling observes actual returns. No function, root,
    # default argument, test body, source hash or expected result is replaced.
    before_profile = sys.getprofile()
    try:
        sys.setprofile(result.profile)
        with __import__("contextlib").redirect_stdout(io.StringIO()), __import__("contextlib").redirect_stderr(io.StringIO()):
            suite.run(result)
    finally:
        sys.setprofile(before_profile)
    if result.testsRun != 50 or sorted(result.tests) != manifest["test_names"] or not result.wasSuccessful() or result.skipped or result.expectedFailures or result.unexpectedSuccesses or result.pending:
        raise ValueError("legacy_view_original_complete_test_run_failed")
    records = []
    for name in manifest["test_names"]:
        expected = "pass" if ".test_current_contract_" in name else "fail"
        calls = result.observations[name]
        if not calls or any(item != {"source_library_sha256": OLD_LIB, "state": expected} for item in calls):
            raise ValueError("legacy_view_validation_call_or_baseline_contaminated")
        records.append({"name": name, "state": "pass", "validation_calls": len(calls),
                        "observed_validator_state": expected, "observed_original_library_sha256": OLD_LIB,
                        "subtests_observed": result.subtests[name]})
    if sha(read(ROOT / MANIFEST, 128*1024)) != digest or snapshot(manifest) != digest:
        raise ValueError("legacy_view_sources_changed_during_run")
    return {"schema_version": SCHEMA, "scope": manifest["scope"], "manifest_sha256": digest,
            "baselines": baselines, "tests": records, "passed": 50, "failed": 0, "skipped": 0,
            "positive_methods": 10, "negative_methods": 40, "validation_calls_observed": sum(row["validation_calls"] for row in records),
            "subtests_observed": sum(row["subtests_observed"] for row in records),
            "original_sources_unchanged": True, "validator_functions_or_defaults_replaced": False,
            "current_workspace_legacy_aggregate_pass": False, "cargo_or_native_session_started": False,
            "raw_document_values_or_absolute_paths_present": False, "green_rows": 0}


def main():
    try:
        value = execute()
    except (OSError, ValueError, KeyError, TypeError, UnicodeError, ImportError, SyntaxError) as error:
        code = str(error) if type(error) is ValueError and re.fullmatch(r"[a-z_]+", str(error)) else "legacy_view_execution_failed"
        print(json.dumps({"state": "fail", "error_code": code})); return 2
    print(json.dumps(value, sort_keys=True, separators=(",", ":"))); return 0


if __name__ == "__main__":
    raise SystemExit(main())
