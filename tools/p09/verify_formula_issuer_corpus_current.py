"""Readonly P144 current original/one-leaf RAM Changed SQL22 component audit, not native/Gate."""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import unittest

from idle_resource_admission import IdleResources
from run_formula_issuer_corpus_probe import CHECKS, ROOT_CHECKS
from run_formula_issuer_corpus_unit_probe import EXPECTED
from run_formula_issuer_registry_sql_checks import ROOT, pin as read_pin, require
from tests.test_formula_issuer_corpus_boundary import CorpusBoundary

BASE = "target/p09-121-resource-optimized/"
EVIDENCE = "implementation/p09/evidence/"
MAIN = "crates/product-cli/examples/formula_issuer_product_postgres_probe.rs"
SOURCE = "crates/product-cli/examples/formula_issuer_product_postgres_probe/source.rs"
ARCHIVE = "implementation/p09/source-archive/p09-144-pre-corpus-input-selection/source-preimages.v1.json"
PREVIOUS = EVIDENCE + "p09-143-current-consumer-sql22.progress.v1.json"
REPORT = "implementation/p09/P09-144_CORPUS_CHANGED_SQL22_PROGRESS.md"
SELF = "tools/p09/verify_formula_issuer_corpus_current.py"


def replace_one(text, before, after):
    require(text.count(before) == 1, "declared_delta_boundary")
    return text.replace(before, after, 1)


def remove_block(text, begin, end):
    require(text.count(begin) == text.count(end) == 1, "declared_block_boundary")
    start = text.index(begin)
    finish = text.index(end, start)
    return text[:start] + text[finish:]


def formatted(text):
    child = subprocess.run(["rustfmt", "--edition", "2024", "--emit", "stdout"], input=text,
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=10, check=False)
    require(child.returncode == 0 and not child.stderr, "restored_source_format_failed")
    return child.stdout.replace("\r\n", "\n")


def authenticate_delta(originals):
    current_main = (ROOT / MAIN).read_text(encoding="utf-8")
    for line in (
        "    source_index: Option<usize>,\n", "    source_sha256: Option<String>,\n",
        "    original_source_sha256: Option<String>,\n", "    input_mode: Option<&'static str>,\n",
        "    only_one_numeric_leaf_changed: bool,\n",
        "    p.source_index = Some(input.index);\n", "    p.source_sha256 = Some(ContentDigest::of(&input.raw).hex());\n",
        "    p.original_source_sha256 = Some(input.original_sha.hex());\n", "    p.input_mode = Some(input.mode);\n",
        "    p.only_one_numeric_leaf_changed = input.only_one_numeric_leaf_changed;\n",
        '        "source_index":probe.source_index,"source_sha256":probe.source_sha256,\n',
        '        "original_source_sha256":probe.original_source_sha256,"input_mode":probe.input_mode,\n',
        '        "only_one_numeric_leaf_changed":probe.only_one_numeric_leaf_changed,\n',
    ):
        current_main = replace_one(current_main, line, "")
    require(formatted(current_main) == originals[MAIN].decode("utf-8").replace("\r\n", "\n"), "undeclared_main_delta")
    current = (ROOT / SOURCE).read_text(encoding="utf-8")
    current = replace_one(current, "use domain_ir::{CellCoordinate, DocumentId, FormulaExpression};", "use domain_ir::DocumentId;")
    current = replace_one(current, "    BoundedZipReader, PackageLimits, PreservingXmlDocument, WriterLimits,", "    WriterLimits,")
    for line in ("    collections::BTreeMap,\n", "    io::{Cursor, Write},\n",
        "use zip::{CompressionMethod, ZipWriter, write::SimpleFileOptions};\n",
        "    pub index: usize,\n", "    pub original_sha: ContentDigest,\n", "    pub mode: &'static str,\n",
        "    pub only_one_numeric_leaf_changed: bool,\n"):
        current = replace_one(current, line, "")
    current = remove_block(current, "fn source_index(", "pub(super) fn read()")
    current = replace_one(current, '    let index = configured_index()?;\n    let selected = rows.get(index).ok_or("source_input_index_invalid")?;', "    let selected = &rows[0];")
    current = replace_one(current, "    let original_sha = ContentDigest::of(&raw);\n    let (raw, mode, only_one_numeric_leaf_changed) = configured_input(raw)?;\n", "")
    current = replace_one(current, "        index,\n        original_sha,\n        mode,\n        only_one_numeric_leaf_changed,\n", "")
    current = remove_block(current, "fn configured_input(", "fn ingest(")
    current = remove_block(current, "#[cfg(test)]\nmod source_index_tests", "#[cfg(test)]\nmod route_tests")
    require(formatted(current) == originals[SOURCE].decode("utf-8").replace("\r\n", "\n"), "undeclared_source_delta")


def audit(resources):
    require(Path.cwd().resolve() == ROOT.resolve(), "wrong_root")
    snapshots = {}

    def pin(path):
        require(not resources.stop.is_set(), resources.reason or "resource_stop")
        if path not in snapshots:
            snapshots[path] = read_pin(path)
        return snapshots[path]

    def load(path):
        pin(path)
        return json.loads((ROOT / path).read_text(encoding="utf-8-sig"))

    rows = load(ARCHIVE)["files"]
    require({row["path"] for row in rows} == {MAIN, SOURCE} and len(rows) == 2, "whole_original_archive_scope")
    originals, archived = {}, set()
    for row in rows:
        raw = base64.b64decode("".join(row["base64_chunks"]), validate=True)
        require(len(raw) == row["bytes"] and hashlib.sha256(raw).hexdigest() == row["sha256"], "whole_original_archive_drift")
        originals[row["path"]] = raw
        archived.add((row["path"], row["bytes"], row["sha256"]))
    previous = load(PREVIOUS)
    require(previous["state"] == "CURRENT_ORIGINAL_SIGNATURE_CONSUMER_COMPONENT_PASS_NOT_NATIVE_OR_GATE"
        and len(previous["verified_direct_pins"]) == 959 and previous["P09_gate"] == "OPEN" and not previous["product_complete"], "historical_current_checkpoint_drift")
    for row in previous["verified_direct_pins"]:
        require(pin(row["path"]) == row or (row["path"], row["bytes"], row["sha256"]) in archived, "historical_pin_not_preserved")
    authenticate_delta(originals)

    def exact(rows):
        for row in rows:
            require(pin(row["path"]) == row, "current_source_or_executable_drift")

    build_path = BASE + "p143-issuer-product-build-r8.json"
    build = load(build_path)
    require(build["state"] == "PASS_PROBE_BUILD_ONLY_NOT_DB_OR_GATE" and build["exit_code"] == 0
        and not build["catalog_profile"]["test"] and not build["diagnostics"]
        and build["source_freeze_exact_after"] and build["protected_executables_exact_after"]
        and len(build["source_freeze"]) == 842 and build["whole_workspace_Rust_input_coverage_enforced"], "current_build_not_accepted")
    exact(build["source_freeze"])
    exact(build["protected_executables"] + [build["executable_pin"]])
    unit_build_path = BASE + "p143-typed-route-unit-build-r3.json"
    unit_path = BASE + "p144-corpus-unit-run1.json"
    unit_build, unit = load(unit_build_path), load(unit_path)
    require(unit_build["state"] == "PASS_TYPED_ROUTE_UNIT_BUILD_ONLY_NOT_EXECUTION" and unit_build["catalog_profile"]["test"]
        and unit_build["exit_code"] == 0 and not unit_build["diagnostics"]
        and unit["state"] == "PASS_TYPED_ROUTE_AND_SOURCE_INDEX_UNIT11_NOT_DB_NATIVE_OR_GATE"
        and unit["test_process_started"] and unit["tests"] == EXPECTED
        and unit["executable_pin"] == unit_build["executable_pin"] and not unit["actual_DB_or_native_executed"], "actual_Rust_unit11_not_accepted")
    exact(unit_build["source_freeze"])
    exact(unit["source_freeze"])
    exact(unit["protected_executables"])

    cases, absence = [], []
    docker = shutil.which("docker")
    require(docker is not None, "owned_absence_tool_missing")
    manifest = load("implementation/p09/evidence/p09-77-document-import-active-security.source-progress.v1.json")
    for number, mode, outcome in ((1, "numeric_derivative", "changed"), (2, "original", "unchanged")):
        path = EVIDENCE + f"p09-144-corpus-consumer-run{number:02}.v1.json"
        run = load(path)
        result = run["product_probe"]["result"]
        require(run["state"] == "PASS_ORIGINAL_SIGNATURE_CONSUMER_SQL22_COMPONENT_NOT_NATIVE_OR_GATE"
            and run["product_probe"]["exit_code"] == 0 and result["failed_stage"] is None and result["checks"] == ROOT_CHECKS
            and run["product_executable_pin"] == build["executable_pin"] and run["container_removed"]
            and run["source_freeze_exact_after"] and run["protected_executables_exact_after"]
            and run["input_mode"] == result["input_mode"] == mode
            and run["source_index"] == result["source_index"] == 0
            and run["expected_formula_outcome"] == result["formula_outcome"] == outcome
            and run["frozen_original_source_pin"] == manifest["actual_inputs"][0]
            and result["original_source_sha256"] == manifest["actual_inputs"][0]["sha256"], "current_case_identity_or_outcome_drift")
        require((mode == "original" and result["source_sha256"] == result["original_source_sha256"] and result["only_one_numeric_leaf_changed"] is False)
            or (mode == "numeric_derivative" and re.fullmatch(r"[0-9a-f]{64}", result["source_sha256"])
                and result["source_sha256"] != result["original_source_sha256"] and result["only_one_numeric_leaf_changed"] is True), "current_original_derivative_boundary")
        require(run["original_product_consumer_executed"] and run["real_Ed25519_approval_signature_executed"]
            and run["probe_runs"][0]["result"]["checks"] == CHECKS and len(run["probe_runs"]) == 3
            and run["original_full_ir_assertions"] == 25 and len(run["original_SQL22_checks_committed"]) == 37
            and run["final_history"] == {"root_history": 4, "root_max": 4, "approval_history": 4, "approval_max": 3,
                "root_revocations": 2, "approval_revocations": 2}, "current_DB_history_drift")
        require(not any(run[key] for key in ("native_application_executed", "product_complete", "all_36_source_inputs_qualified",
            "durable_blob_store_qualified", "production_key_custody_qualified", "atomic_product_publication_qualified",
            "observed_graph_native_fidelity_qualified")) and run["P09_gate"] == run["A12_gate"] == run["A13_gate"] == "OPEN", "component_scope_promoted")
        exact(run["source_freeze"])
        exact(run["protected_executables"])
        for reference in (run["container_id"], run["container_name"]):
            child = subprocess.run([docker, "inspect", reference], cwd=ROOT, capture_output=True, text=True, timeout=10, check=False)
            require(child.returncode != 0 and re.search(r"no such (object|container)", child.stderr, re.IGNORECASE), "owned_container_present")
            absence.append({"reference": reference, "absent": True})
        cases.append({"receipt": pin(path), "source_index": 0, "input_mode": mode, "formula_outcome": outcome,
            "original_source_sha256": result["original_source_sha256"], "actual_input_sha256": result["source_sha256"],
            "only_one_numeric_leaf_changed": result["only_one_numeric_leaf_changed"]})

    lint_path = BASE + "p144-workspace-lint-r1.json"
    lint = load(lint_path)
    target_key = lambda row: (row["package_id"], row["name"], tuple(sorted(row["kind"])))
    wanted = {target_key(row) for row in lint["workspace_inventory"]}
    actual = {target_key(row) for row in lint["workspace_artifacts"]}
    require(lint["state"] == "PASS_SOURCE_ONLY_NOT_GATE" and lint["exit_code"] == 0 and not lint["diagnostics"]
        and lint["source_freeze_exact_after"] and lint["protected_executables_exact_after"]
        and lint["workspace_target_coverage_exact"] and len(wanted) == len(actual) == 361 and wanted == actual
        and len({row["package_id"] for row in lint["workspace_inventory"]}) == 32
        and len(lint["protected_executables"]) == 48 and len(lint["source_freeze"]) == 855
        and not lint["missing_targets"] and not lint["unexpected_targets"]
        and lint["cargo_arguments"][-2:] == ["-D", "warnings"], "current_workspace_lint_not_accepted")
    exact(lint["source_freeze"])
    exact(lint["protected_executables"])
    for row in previous["protected_executables"] + [build["executable_pin"], unit_build["executable_pin"]]:
        require(row in lint["protected_executables"], "earlier_executable_not_protected")
    indexed = subprocess.run(["rg", "--threads", "1", "--files", "crates", "protocol/generated/rust", "tools/xtask",
        "-g", "*.rs", "-g", "Cargo.toml"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=10, check=False)
    require(indexed.returncode == 0 and not indexed.stderr and set(indexed.stdout.replace("\\", "/").splitlines()).issubset(
        {row["path"] for row in build["source_freeze"]}), "whole_Rust_input_coverage")
    guards = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(unittest.defaultTestLoader.loadTestsFromTestCase(CorpusBoundary))
    require(guards.testsRun == 6 and guards.wasSuccessful() and not guards.skipped, "lightweight_source_guards_failed")
    for path in (SELF, REPORT, "tools/p09/tests/test_formula_issuer_corpus_boundary.py", BASE + "p143-idle-preflight-r7.json", BASE + "p143-idle-preflight-r8.json"):
        pin(path)
    for path, expected in snapshots.items():
        require(not resources.stop.is_set(), resources.reason or "resource_stop")
        require(read_pin(path) == expected, "input_changed_during_readonly_audit")
    return {
        "schema_version": "hwpx-agent.p09-144-corpus-consumer-current-progress/v1",
        "state": "CURRENT_ORIGINAL_AND_RAM_DERIVATIVE_CHANGED_SQL22_COMPONENT_PASS_NOT_NATIVE_OR_GATE",
        "verified_direct_pins": list(snapshots.values()), "unique_files_freshly_double_hashed": len(snapshots),
        "cross_turn_hash_cache_used": False, "whole_prior_source_and_declared_delta_authenticated": True,
        "historical_P143_checkpoint": pin(PREVIOUS), "historical_P143_pins_preserved": 959,
        "current_main_build": pin(build_path), "current_Rust_unit_build": pin(unit_build_path), "current_Rust_unit_run": pin(unit_path),
        "current_strict_workspace_lint": pin(lint_path), "current_cases": cases,
        "protected_executables": lint["protected_executables"], "protected_executables_exact": True,
        "actual_Rust_tests": 11, "source_guards": 6, "packages": 32, "targets": 361,
        "current_DB_checks_per_case": {"original_full_IR": 25, "original_SQL22": 37, "metadata": 42, "consumer": 18, "fingerprint_controls": 2},
        "current_owned_container_absence": absence, "original_source_indices_covered": [0], "RAM_derivative_indices_covered": [0],
        "all_36_original_sources_qualified": False, "consumer_live_SQL_revocation_CAS_race_qualified": False,
        "durable_blob_store_qualified": False, "production_key_custody_qualified": False, "atomic_product_publication_qualified": False,
        "native_application_executed": False, "P09_gate": "OPEN", "A12_gate": "OPEN", "A13_gate": "OPEN", "product_complete": False,
        "goal_status": "active", "coarse_remaining_minimum": 6, "coarse_closed_this_turn": 0,
    }


if __name__ == "__main__":
    resources = None
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("--receipt", required=True)
        args = parser.parse_args()
        require(re.fullmatch(r"implementation/p09/evidence/p09-144-corpus-consumer\.progress\.v[1-9][0-9]*\.json", args.receipt), "fresh_progress_scope")
        destination = ROOT / args.receipt
        require(not destination.exists() and destination.parent.is_dir() and not destination.parent.is_symlink()
            and not destination.parent.is_junction(), "fresh_progress_required")
        resources = IdleResources()
        resources.start()
        result = audit(resources)
        result["audit_resource_samples"], result["audit_resource_stop_reason"] = resources.samples, resources.reason
        with destination.open("x", encoding="utf-8", newline="\n") as output:
            output.write(json.dumps(result, indent=2) + "\n")
        print(json.dumps({"state": result["state"], "receipt": args.receipt, "unique_files_freshly_double_hashed": result["unique_files_freshly_double_hashed"],
            "protected_executables": len(result["protected_executables"]), "current_cases": len(result["current_cases"])}))
    except (OSError, ValueError, KeyError, json.JSONDecodeError, subprocess.SubprocessError) as error:
        code = str(error) if isinstance(error, ValueError) and re.fullmatch(r"[A-Za-z0-9_]+", str(error)) else "redacted"
        print(json.dumps({"state": "FAIL_CLOSED", "error_code": code, "P09_gate": "OPEN"}))
        raise SystemExit(1) from None
    finally:
        if resources is not None:
            resources.done.set()
            if resources.thread.is_alive():
                resources.thread.join(timeout=3)
