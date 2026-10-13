"""P146 current approval SQL evidence audit; never builds or starts DB/native work."""
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
from run_formula_issuer_corpus_unit_probe import EXPECTED
from run_formula_issuer_live_sql_probe import CHECKS, ROOT_CHECKS
from run_formula_issuer_registry_sql_checks import ROOT, require
from audit_evidence_io import AuditEvidenceReader
from run_resource_bounded_python import observed_limits
from tests.test_live_sql_consumer_boundary import LiveSQLConsumerBoundary
from bounded_audit_tools import run_audit_tool
from bounded_container_absence import inspect_absence

BASE = "target/p09-121-resource-optimized/"
EVIDENCE = "implementation/p09/evidence/"
SOURCE = "crates/product-cli/examples/formula_issuer_product_postgres_probe/source.rs"
SELF = "tools/p09/verify_formula_issuer_live_current.py"
REPORT = "implementation/p09/P09-147_CURRENT_APPROVAL_SQL_REVALIDATION_REPORT.md"
PRIOR = EVIDENCE + "p09-145-resource-bootstrap.progress.v1.json"
ARCHIVES = ["p09-146-pre-live-sql-consumer", "p09-146-pre-timeout-diagnostics",
    "p09-146-pre-unit4-and-marker-normalization", "p09-146-pre-strict-lint-corrections",
    "p09-149-pre-bounded-audit-integration", "p09-149-pre-live-audit-bound-io",
    "p09-149-pre-live-bounded-absence"]


def replace_one(text, before, after):
    require(text.count(before) == 1, "declared_delta_boundary")
    return text.replace(before, after, 1)


def remove_block(text, begin, end):
    require(text.count(begin) == text.count(end) == 1, "declared_block_boundary")
    start = text.index(begin)
    return text[:start] + text[text.index(end, start):]


def authenticate_baseline(current, original, checkpoint=None):
    """Remove only the declared opt-in extension; preserve all original consumer code."""
    current = remove_block(current, "    postgres::source_formula_policy::{", "};\nuse std::{")
    current = replace_one(current, "};\nuse std::{", "    postgres::source_formula_policy::issuer_registry::LocalPostgresFormulaIssuerRegistryRepository,\n};\nuse std::{")
    current = remove_block(current, "    verify_consumer(\n", "type Provider<'a>")
    current = replace_one(current, "type Provider<'a>", "    verify_consumer(probe, p, input, &provider, head)\n}\ntype Provider<'a>")
    current = remove_block(current, "fn live_denial_matches<T>(", "fn route_denial_matches(")
    current = replace_one(current, "    binding: &LiveApprovalBinding,\n", "")
    current = replace_one(current,
        '    )?;\n    verify_live_approval(probe, p, provider, &prepared, &raw, &wanted, binding)\n}',
        '    )\n}')
    for stage in ("source_begin", "consumer_begin"):
        current = replace_one(current, f'    eprintln!("P146_STAGE:{stage}");\n', "")
    formatted = run_audit_tool("rustfmt-stdin", current, checkpoint=checkpoint)
    require(formatted.returncode == 0 and not formatted.stderr
        and formatted.stdout.replace("\r\n", "\n") == original.decode("utf-8").replace("\r\n", "\n"),
        "original_consumer_undeclared_delta")
    return formatted.audit_limits


def validate_case(run, build, manifest, mode, outcome):
    result = run["product_probe"]["result"]
    require(run["state"] == "PASS_ORIGINAL_SIGNATURE_CONSUMER_SQL22_COMPONENT_NOT_NATIVE_OR_GATE"
        and run["product_probe"]["exit_code"] == 0 and result["failed_stage"] is None
        and result["checks"] == ROOT_CHECKS and len(ROOT_CHECKS) == len(set(ROOT_CHECKS)) == 27
        and run["product_executable_pin"] == build["executable_pin"] and run["container_removed"] is True
        and run["source_freeze_exact_after"] is True and run["protected_executables_exact_after"] is True
        and run["input_mode"] == result["input_mode"] == mode and run["live_case"] == "approval"
        and run["source_index"] == result["source_index"] == 0
        and run["expected_formula_outcome"] == result["formula_outcome"] == outcome
        and run["frozen_original_source_pin"] == manifest["actual_inputs"][0]
        and result["original_source_sha256"] == manifest["actual_inputs"][0]["sha256"],
        "current_case_identity_or_outcome_drift")
    require((mode == "original" and result["source_sha256"] == result["original_source_sha256"]
            and result["only_one_numeric_leaf_changed"] is False)
        or (mode == "numeric_derivative" and re.fullmatch(r"[0-9a-f]{64}", result["source_sha256"])
            and result["source_sha256"] != result["original_source_sha256"]
            and result["only_one_numeric_leaf_changed"] is True), "original_derivative_boundary")
    require(all(run[key] is True for key in ("original_product_consumer_executed",
        "real_Ed25519_approval_signature_executed", "actual_SQL_executed", "actual_Rust_DB_adapter_executed",
        "actual_consumer_SQL_approval_revocation_and_duplicate_race_executed"))
        and run["probe_runs"][0]["result"]["checks"] == CHECKS and len(CHECKS) == 42
        and len(run["probe_runs"]) == 3 and run["original_full_ir_assertions"] == 25
        and len(set(run["original_SQL22_checks_committed"])) == 37
        and run["final_history"] == {"root_history": 4, "root_max": 4, "approval_history": 4,
            "approval_max": 3, "root_revocations": 2, "approval_revocations": 3}
        and run["resource_stop_reason"] is None, "current_SQL_history_or_checks_drift")
    require(all(run[key] is False for key in ("native_application_executed", "product_complete",
        "all_36_source_inputs_qualified", "durable_blob_store_qualified", "production_key_custody_qualified",
        "atomic_product_publication_qualified", "observed_graph_native_fidelity_qualified",
        "issuer_provisioning_generation_race_qualified", "trust_revocation_consumer_qualified"))
        and run["P09_gate"] == run["A12_gate"] == run["A13_gate"] == "OPEN", "component_scope_promoted")


def audit(resources):
    originals = {}
    readonly_tool_profiles = []

    def checkpoint():
        require(not resources.stop.is_set(), resources.reason or "resource_stop")

    reader = AuditEvidenceReader(ROOT, checkpoint)
    snapshots = reader.snapshots
    pin, load = reader.pin, reader.json

    for path in ("tools/p09/bounded_audit_tools.py", "tools/p09/tests/test_bounded_audit_tools.py",
                 "tools/p09/conservative_maintenance.py", "tools/p09/verify_audit_evidence_io.py",
                 "tools/p09/verify_bounded_audit_tools_light.py", "tools/p09/tests/test_bounded_audit_tool_integration.py",
                 "tools/p09/verify_bounded_audit_tool_integration_light.py",
                 "implementation/p09/source-archive/p09-149-pre-bounded-audit-integration/source-preimages.v1.json",
                 "implementation/p09/source-archive/p09-149-pre-integration-setup-repair/source-preimages.v1.json",
                 "tools/p09/audit_evidence_io.py", "tools/p09/tests/test_audit_evidence_io.py",
                 "tools/p09/tests/test_live_audit_io_integration.py", "tools/p09/verify_live_audit_io_light.py",
                 "implementation/p09/source-archive/p09-149-pre-live-audit-bound-io/source-preimages.v1.json",
                 "tools/p09/bounded_container_absence.py", "tools/p09/tests/test_bounded_container_absence.py",
                 "tools/p09/bounded_process_progress.py", "tools/p09/tests/test_live_absence_integration.py",
                 "tools/p09/verify_live_absence_light.py",
                 "implementation/p09/source-archive/p09-149-pre-live-bounded-absence/source-preimages.v1.json"):
        pin(path)
    for path in ("rustfmt.toml", ".rustfmt.toml", "rust-toolchain.toml", "rust-toolchain"):
        if (ROOT / path).exists():
            pin(path)

    def exact(rows, historical=False):
        for row in rows:
            actual = pin(row["path"])
            identity = (row["path"], row["bytes"], row["sha256"])
            require(actual == row or (historical and identity in originals), "current_or_historical_pin_drift")

    for name in ARCHIVES:
        archive = load(f"implementation/p09/source-archive/{name}/source-preimages.v1.json")
        require(archive["schema_version"] == "hwpx-agent.source-preimages/v1", "archive_schema_drift")
        for row in archive["files"]:
            raw = base64.b64decode("".join(row["base64_chunks"]), validate=True)
            require(len(raw) == row["bytes"] and hashlib.sha256(raw).hexdigest() == row["sha256"], "archive_bytes_drift")
            originals[(row["path"], row["bytes"], row["sha256"])] = raw
    prior = load(PRIOR)
    require(prior["state"] == "CURRENT_PRE_HASH_LIMIT_AND_SECOND_ORIGINAL_SQL22_COMPONENT_PASS_NOT_NATIVE_OR_GATE"
        and prior["unique_files_freshly_double_hashed"] == len(prior["verified_direct_pins"]) == 988
        and len({r["path"] for r in prior["verified_direct_pins"]}) == 988
        and prior["P09_gate"] == "OPEN" and prior["product_complete"] is False, "prior_checkpoint_scope_drift")
    exact(prior["verified_direct_pins"], historical=True)
    old_source = next(row for row in prior["verified_direct_pins"] if row["path"] == SOURCE)
    original = originals[(SOURCE, old_source["bytes"], old_source["sha256"])]
    readonly_tool_profiles.append(authenticate_baseline(reader.text(SOURCE),
        original, checkpoint=checkpoint))

    for number in range(1, 5):
        run = load(EVIDENCE + f"p09-146-corpus-consumer-run{number:02}.v1.json")
        exact(run.get("source_freeze", []), historical=True)
        exact(run.get("protected_executables", []))
        require(run["container_removed"] is True, "historical_owned_cleanup_missing")
        require((number == 1 and run["state"] == "FAIL_CLOSED")
            or (number > 1 and run["state"] == "PASS_ORIGINAL_SIGNATURE_CONSUMER_SQL22_COMPONENT_NOT_NATIVE_OR_GATE"),
            "historical_failure_or_component_status_changed")
    failed_lint = load(BASE + "p146-workspace-lint-r2.json")
    require(failed_lint["state"] == "NOT_ACCEPTED_STOP_OR_FAILURE" and failed_lint["exit_code"] == 101
        and len(failed_lint["diagnostics"]) == 4, "failed_lint_not_preserved")
    exact(failed_lint["source_freeze"], historical=True)
    exact(failed_lint["protected_executables"])
    load(BASE + "p146-workspace-lint-r1.json")
    load(EVIDENCE + "p09-146-source-guards-initial-failure.v1.json")
    load(EVIDENCE + "p09-146-live-approval.partial-checkpoint.v1.json")

    build = load(BASE + "p143-issuer-product-build-r11.json")
    unit_build = load(BASE + "p143-typed-route-unit-build-r5.json")
    unit = load(BASE + "p144-corpus-unit-run4.json")
    require(build["state"] == "PASS_PROBE_BUILD_ONLY_NOT_DB_OR_GATE" and build["catalog_profile"]["test"] is False
        and unit_build["state"] == "PASS_TYPED_ROUTE_UNIT_BUILD_ONLY_NOT_EXECUTION" and unit_build["catalog_profile"]["test"] is True
        and all(r["exit_code"] == 0 and not r["diagnostics"] and r["source_freeze_exact_after"]
            and r["protected_executables_exact_after"] and r["logical_cpu_limit"] == r["cargo_jobs"] == 1
            and r["priority"] == "BelowNormal" for r in (build, unit_build))
        and len(build["source_freeze"]) == 842 and len(unit_build["source_freeze"]) == 843,
        "current_build_evidence_not_accepted")
    require(unit["state"] == "PASS_TYPED_ROUTE_AND_SOURCE_INDEX_UNIT11_NOT_DB_NATIVE_OR_GATE"
        and unit["test_process_started"] is True and unit["tests"] == EXPECTED
        and unit["executable_pin"] == unit_build["executable_pin"] and unit["actual_DB_or_native_executed"] is False,
        "current_unit11_not_accepted")
    for receipt in (build, unit_build, unit):
        exact(receipt["source_freeze"])
        exact(receipt["protected_executables"] + [receipt["executable_pin"]])
    manifest = load(EVIDENCE + "p09-77-document-import-active-security.source-progress.v1.json")
    require(len(manifest["actual_inputs"]) == 36, "original_manifest_inventory")
    cases, absence = [], []
    current_references = []
    docker = shutil.which("docker")
    require(docker is not None, "owned_absence_tool_missing")
    for number, mode, outcome in ((5, "original", "unchanged"), (6, "numeric_derivative", "changed")):
        path = EVIDENCE + f"p09-146-corpus-consumer-run{number:02}.v1.json"
        run = load(path)
        validate_case(run, build, manifest, mode, outcome)
        exact(run["source_freeze"])
        exact(run["protected_executables"])
        require(len(run["source_freeze"]) == 862 and len(run["protected_executables"]) == 53, "current_case_pin_inventory")
        current_references.extend((run["container_id"], run["container_name"]))
        cases.append({"receipt": pin(path), "source_index": 0, "input_mode": mode, "formula_outcome": outcome})
    absence = inspect_absence(docker, current_references, checkpoint, "owned_container_present")
    lint_path = BASE + "p146-workspace-lint-r3.json"
    lint = load(lint_path)
    key = lambda row: (row["package_id"], row["name"], tuple(sorted(row["kind"])))
    wanted, actual = {key(r) for r in lint["workspace_inventory"]}, {key(r) for r in lint["workspace_artifacts"]}
    require(lint["state"] == "PASS_SOURCE_ONLY_NOT_GATE" and lint["exit_code"] == 0 and not lint["diagnostics"]
        and lint["source_freeze_exact_after"] and lint["protected_executables_exact_after"]
        and lint["workspace_target_coverage_exact"] and len(wanted) == len(actual) == 361 and wanted == actual
        and len({r["package_id"] for r in lint["workspace_inventory"]}) == 32
        and len(lint["source_freeze"]) == 858 and len(lint["protected_executables"]) == 53
        and not lint["missing_targets"] and not lint["unexpected_targets"]
        and lint["cargo_arguments"][-2:] == ["-D", "warnings"], "current_strict_workspace_lint_not_accepted")
    exact(lint["source_freeze"])
    exact(lint["protected_executables"])
    indexed = run_audit_tool("rust-input-inventory", checkpoint=checkpoint)
    readonly_tool_profiles.append(indexed.audit_limits)
    require(indexed.returncode == 0 and not indexed.stderr and set(indexed.stdout.replace("\\", "/").splitlines()).issubset(
        {r["path"] for r in build["source_freeze"]}), "whole_Rust_input_coverage")
    guards = unittest.TextTestRunner(stream=io.StringIO()).run(unittest.defaultTestLoader.loadTestsFromTestCase(LiveSQLConsumerBoundary))
    require(guards.testsRun == 6 and guards.wasSuccessful() and not guards.skipped, "source_guards_failed")
    from tests.test_live_sql_current_audit import LiveCurrentAudit
    negatives = unittest.TextTestRunner(stream=io.StringIO()).run(unittest.defaultTestLoader.loadTestsFromTestCase(LiveCurrentAudit))
    require(negatives.testsRun == 7 and negatives.wasSuccessful() and not negatives.skipped, "evidence_negative_checks_failed")
    from tests.test_bounded_audit_tools import BoundedAuditToolsTests
    from tests.test_bounded_audit_tool_integration import BoundedAuditToolIntegrationTests
    from tests.test_audit_evidence_io import AuditEvidenceIOTests
    from tests.test_live_audit_io_integration import LiveAuditIOIntegrationTests
    from tests.test_bounded_container_absence import BoundedContainerAbsenceTests
    from tests.test_live_absence_integration import LiveAbsenceIntegrationTests
    for cls, count in ((BoundedAuditToolsTests, 20), (BoundedAuditToolIntegrationTests, 8),
                       (AuditEvidenceIOTests, 17), (LiveAuditIOIntegrationTests, 6),
                       (BoundedContainerAbsenceTests, 21), (LiveAbsenceIntegrationTests, 5)):
        checked = unittest.TextTestRunner(stream=io.StringIO()).run(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
        require(checked.testsRun == count and checked.wasSuccessful() and not checked.skipped, "bounded_readonly_tools_failed")
    for path in (SELF, REPORT, "tools/p09/tests/test_live_sql_consumer_boundary.py",
        "tools/p09/tests/test_live_sql_current_audit.py", EVIDENCE + "p09-145-resource-bootstrap-run05.v1.json",
        "tools/p09/bounded_audit_tools.py", "tools/p09/tests/test_bounded_audit_tools.py",
        "tools/p09/conservative_maintenance.py", "tools/p09/verify_audit_evidence_io.py",
        "tools/p09/verify_bounded_audit_tools_light.py", "tools/p09/tests/test_bounded_audit_tool_integration.py",
        "tools/p09/verify_bounded_audit_tool_integration_light.py",
        "implementation/p09/source-archive/p09-149-pre-bounded-audit-integration/source-preimages.v1.json"):
        pin(path)
    try:
        reader.finish()
    except ValueError as error:
        if str(error) == "input_changed_during_audit":
            raise ValueError("input_changed_during_current_audit") from None
        raise
    return {"schema_version": "hwpx-agent.p09-147-current-approval-sql-audit/v1",
        "state": "CURRENT_APPROVAL_SQL27_AND_STRICT_LINT_COMPONENT_PASS_NOT_NATIVE_OR_GATE",
        "verified_direct_pins": list(snapshots.values()), "unique_files_freshly_double_hashed": len(snapshots),
        "evidence_read_profile": {"hash_chunk_bytes": 65536, "single_read_json_byte_binding": True,
            "parsed_inputs_cached": False, "read_passes": reader.read_passes, "bytes_read": reader.bytes_read,
            "final_fresh_hashes": reader.final_fresh_hashes,
            "maximum_parse_bytes": reader.maximum_parse_bytes,
            "io_pacing_bytes_per_second": 8388608, "io_pacing_burst_bytes": 65536,
            "io_pacing_charged_bytes": reader.pacer.bytes_paced,
            "requested_pacing_sleep_seconds": reader.pacer.requested_sleep_seconds},
        "historical_P145_pins_preserved": 988, "historical_receipts_not_rerun_as_current": True,
        "original_consumer_declared_delta_authenticated": True, "cross_turn_hash_cache_used": False,
        "readonly_tool_profiles": readonly_tool_profiles,
        "bounded_readonly_tool_checks": 20, "bounded_readonly_integration_checks": 8,
        "current_cases": cases, "protected_executables": lint["protected_executables"],
        "current_owned_container_absence": absence, "actual_Rust_unit_tests": 11, "source_guards": 6, "evidence_negative_checks": 7,
        "packages": 32, "targets": 361, "original_source_indices_currently_covered": [0],
        "RAM_derivative_indices_currently_covered": [0], "approval_revocation_and_duplicate_race_component_executed": True,
        "issuer_provisioning_generation_race_qualified": False, "trust_revocation_consumer_qualified": False,
        "all_36_original_sources_qualified": False, "native_application_executed": False,
        "durable_blob_store_qualified": False, "production_key_custody_qualified": False,
        "atomic_product_publication_qualified": False, "observed_graph_native_fidelity_qualified": False,
        "P09_gate": "OPEN", "A12_gate": "OPEN", "A13_gate": "OPEN", "product_complete": False, "goal_status": "active"}


if __name__ == "__main__":
    resources = None
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("--receipt", required=True)
        args = parser.parse_args()
        require(Path.cwd().resolve() == ROOT.resolve(), "wrong_root")
        require(re.fullmatch(r"implementation/p09/evidence/p09-147-current-approval\.progress\.v[1-9][0-9]*\.json", args.receipt), "receipt_scope")
        destination = ROOT / args.receipt
        require(not destination.exists() and destination.parent.is_dir() and not destination.parent.is_symlink()
            and not destination.parent.is_junction(), "fresh_progress_required")
        resources = IdleResources()
        observed_limits(resources)
        resources.start()
        result = audit(resources)
        result["resource_samples"], result["resource_stop_reason"] = resources.samples, resources.reason
        with destination.open("x", encoding="utf-8", newline="\n") as output:
            output.write(json.dumps(result, indent=2) + "\n")
        print(json.dumps({"state": result["state"], "receipt": args.receipt,
            "unique_files_freshly_double_hashed": result["unique_files_freshly_double_hashed"]}))
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
        code = str(error) if isinstance(error, ValueError) and re.fullmatch(r"[A-Za-z0-9_]+", str(error)) else "redacted"
        failure = {"state": "FAIL_CLOSED", "error_code": code, "P09_gate": "OPEN"}
        tool_profile = getattr(error, "audit_limits", None)
        if tool_profile is not None:
            failure["readonly_tool_failure_profile"] = tool_profile
        print(json.dumps(failure))
        raise SystemExit(1) from None
    finally:
        if resources is not None:
            resources.done.set()
            if resources.thread.is_alive():
                resources.thread.join(timeout=3)
