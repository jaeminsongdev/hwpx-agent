"""Exact mandatory Ed25519 formula component and whole ancestry; not production trust/SQL/native/Gate."""
import argparse
import importlib.util
import json
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p118_bytes", Path(__file__).with_name("verify_formula_policy_registration_progress.py"))
P118 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P118)
BASE, ROOT = P118.BASE, P118.ROOT
PREVIOUS = P118.CURRENT
CURRENT = "implementation/p09/evidence/p09-119-formula-policy-issuer.source-progress.v1.json"
PARENTS = ["Cargo.lock", "crates/product-cli/Cargo.toml",
           "crates/product-cli/src/form_stored_provider/actual_import/source_policy/formulas.rs",
           "crates/product-cli/tests/form_stored_provider/actual_import.rs"]
ARCHIVE = "implementation/p09/source-archive/p09-119-pre-formula-policy-issuer/"
NEW_SOURCES = [
    "crates/product-cli/src/form_stored_provider/actual_import/source_policy/formulas/issuer.rs",
    "crates/product-cli/src/form_stored_provider/actual_import/source_policy/formulas/issuer/wire.rs",
    "crates/product-cli/src/form_stored_provider/actual_import/source_policy/formulas/issuer/provider.rs",
    "crates/product-cli/src/form_stored_provider/actual_import/source_policy/formulas/issuer/product.rs",
    "crates/product-cli/tests/form_stored_provider/actual_import/formula_policy_issuer.rs",
    "tools/p09/verify_formula_policy_issuer_progress.py",
    "tools/p09/tests/test_formula_policy_issuer_progress.py",
    "implementation/p09/P09-119_FORMULA_POLICY_ISSUER_REPORT.md",
    "protocol/migrations/p09-source-formula-approval-v0-to-v1.md",
    "implementation/p09/evidence/p09-119-formula-policy-issuer.source-regression.v1.json",
]
ARCHIVES = [ARCHIVE + p for p in PARENTS] + [
    "implementation/p09/source-archive/" + folder + "/" + NEW_SOURCES[4]
    for folder in ["p09-119-initial-test-compile", "p09-119-pre-lint-and-strengthening",
                   "p09-119-positional-test-lint", "p09-119-approval-only-aead-failure"]]
PREDECESSORS = [PREVIOUS, "implementation/p09/evidence/p09-118-formula-policy-registration.final-audit.v1.json"]
EXE_ROOT = "target/p09-119-formula-policy-issuer/debug/"
TEST_STEMS = ["hwpx_agent_cli-2e652378818f9b3c", "form_stored_provider-9df9b9ece65a1dfd",
              "form_product_request-705fd2bcec70396c", "form_value_operation-7cdd3d0f9fe6622c",
              "artifact_service-c722486ab67dc904", "revision_service-1b137e63992c86e2"]
EXECUTABLES = [EXE_ROOT + "deps/" + stem + ".exe" for stem in TEST_STEMS] + [
    EXE_ROOT + "deps/hwpx_agent_cli.exe", EXE_ROOT + "hwpx-agent-cli.exe",
    EXE_ROOT + "deps/form_stored_provider-9df9b9ece65a1dfd-pre-lint-and-strengthening.exe"] + [
    EXE_ROOT + "deps/" + stem + "-initial-full-regression.exe" for stem in TEST_STEMS]
EDITS = {PARENTS[1]: b"ring.workspace = true\n", PARENTS[2]: b"pub mod issuer;\n",
         PARENTS[3]: b'#[path = "actual_import/formula_policy_issuer.rs"]\nmod formula_policy_issuer;\n'}
FALSE_QUALIFICATIONS = list(P118.FALSE_QUALIFICATIONS) + [
    "production_formula_issuer_configured", "actual_formula_approval_registry_verified",
    "production_formula_key_custody_verified", "all_original_formula_sources_signed_qualified"]

class PreviousReadView:
    def __init__(self, root):
        self.root = root
    def __truediv__(self, path):
        return self.root / (ARCHIVE + str(path) if str(path) in PARENTS else path)

def original_sources():
    sources = P118.original_sources()
    sources.update({r["path"]: r for r in json.loads((ROOT / PREVIOUS).read_bytes())["source_delta"]})
    if len(sources) != 1071:
        raise ValueError("prior_source_coverage_drift")
    return sources

def restored_parent(path, data):
    if path == "Cargo.lock":
        # Only the exact CLI block: never remove other original ring dependencies.
        start = b'[[package]]\nname = "hwpx-agent-cli"\n'
        if data.count(start) != 1:
            raise ValueError("lock_cli_block_drift")
        prefix, rest = data.split(start, 1)
        block, separator, suffix = rest.partition(b"\n[[package]]\n")
        edit = b' "revision-service",\n "ring",\n "serde",\n'
        if block.count(edit) != 1:
            raise ValueError("lock_declared_dependency_drift")
        return prefix + start + block.replace(edit, b' "revision-service",\n "serde",\n', 1) + separator + suffix
    edit = EDITS[path]
    if data.count(edit) != 1:
        raise ValueError("declared_parent_edit_shape_drift")
    return data.replace(edit, b"", 1)

def inherited():
    checkpoint, final = [BASE.pin(p) for p in PREDECESSORS]
    if (checkpoint["bytes"], checkpoint["sha256"]) != (8036, "e07d41a6f2da50bab2241a08e23058dfdffdb91b8063a7b06630120010b6d046"):
        raise ValueError("previous_checkpoint_drift")
    if (final["bytes"], final["sha256"]) != (9845, "dc235eb14aedeb9b9b57ed35d086aecaa3451a1989fadec5fb4f0865e8637fa9"):
        raise ValueError("previous_final_audit_drift")
    sources = original_sources()
    for path in PARENTS:
        if not BASE.exact(sources[path], ARCHIVE + path):
            raise ValueError("whole_parent_preimage_drift")
        if restored_parent(path, (ROOT / path).read_bytes()) != (ROOT / (ARCHIVE + path)).read_bytes():
            raise ValueError("undeclared_parent_mutation")
    old_root, old_base = P118.ROOT, BASE.ROOT
    try:
        P118.ROOT = BASE.ROOT = PreviousReadView(ROOT)
        prior = P118.current()
    finally:
        P118.ROOT, BASE.ROOT = old_root, old_base
    raw = prior["inherited_raw_pin_entries"] + sum(prior["current_groups"].values())
    if raw != 2232 or prior["checkpoint"] != checkpoint:
        raise ValueError("inherited_raw_coverage_drift")
    unchanged = sum(BASE.exact(r) for p, r in sources.items() if p not in PARENTS)
    if unchanged != 1067:
        raise ValueError("unrelated_original_source_drift")
    return {"state": "pass_whole_previous_source_and_evidence_NOT_production_trust_SQL_native_or_Gate",
            "previous_checkpoint": checkpoint, "inherited_raw_pin_entries": raw,
            "previous_source_files": 1071, "unchanged_previous_source_files": unchanged,
            "whole_parent_preimages": 4, "whole_parent_inverse_exact": True,
            "previous_unmodified_audit_on_preimages_passed": True,
            "old_executables_preserved": 482, "all_old_executables_reexecuted": False}

def verify_current_manifest(data, prior):
    if data["inherited_checkpoint"] != prior["previous_checkpoint"] or data["current_source_files_count"] != 1081:
        raise ValueError("current_source_coverage_drift")
    required = {"source_delta": set(PARENTS + NEW_SOURCES), "source_archives_added": set(ARCHIVES),
                "predecessor_receipts_added": set(PREDECESSORS), "current_executables": set(EXECUTABLES)}
    counts = {}
    for key, paths in required.items():
        rows = data[key]
        if len(rows) != len(paths) or {r["path"] for r in rows} != paths:
            raise ValueError("current_group_coverage_drift")
        if not all(BASE.exact(row) for row in rows):
            raise ValueError("current_raw_pin_drift")
        counts[key] = len(rows)
    if any(data["qualification"][key] is not False for key in FALSE_QUALIFICATIONS):
        raise ValueError("unsupported_qualification_promotion")
    if data["qualification"]["mandatory_live_ed25519_formula_approval_product_component_implemented"] is not True:
        raise ValueError("missing_actual_signed_component_implementation")
    if data["P09_gate"] != "OPEN" or data["P10_new_implementation"] is not False or data["product_complete"] is not False:
        raise ValueError("gate_or_product_promotion")
    if data["remaining_coarse_groups_minimum"] != 6 or data["remaining_coarse_groups_closed_by_slice"] != 0:
        raise ValueError("unsupported_remaining_reduction")
    if data["conversation_minimum_30_conditions_not_exhaustive_or_decremented"] is not True:
        raise ValueError("unsupported_granular_remaining_reduction")
    regression = json.loads((ROOT / NEW_SOURCES[-1]).read_bytes())
    verify_regression(regression, data)
    return counts

def verify_regression(regression, manifest):
    """Receipt consistency with actual frozen code/test binaries, not a substitute for terminal execution."""
    if regression["state"] != "PASS_scoped_signed_formula_component_NOT_production_trust_SQL_native_or_Gate":
        raise ValueError("regression_not_terminal_pass")
    source_rows = {r["path"]: r for r in manifest["source_delta"]}
    expected_code = set(PARENTS + NEW_SOURCES[:5])
    freeze = regression["source_freeze"]
    if len(freeze) != 9 or {r["path"] for r in freeze} != expected_code:
        raise ValueError("tested_source_coverage_drift")
    if any(r != source_rows[r["path"]] or not BASE.exact(r) for r in freeze):
        raise ValueError("tested_source_pin_drift")
    runtime = regression["runtime"]
    if (runtime["exit_code"], runtime["passed"], runtime["failed"], runtime["ignored"], runtime["filtered"]) != (0, 301, 0, 0, 0):
        raise ValueError("regression_counter_drift")
    if runtime["suites"] != {"artifact_lib": 25, "cli_lib": 6, "form_product_request": 10,
                            "form_stored_provider": 222, "form_value_operation": 18, "revision_lib": 20}:
        raise ValueError("regression_suite_coverage_drift")
    if runtime["new_issuer_tests_included"] != 14 or not runtime["terminal"]:
        raise ValueError("regression_identity_drift")
    listed = regression["test_inventory"]["test_executables"]
    expected_exes = {EXE_ROOT + "deps/" + stem + ".exe" for stem in TEST_STEMS}
    if len(listed) != 6 or {r["path"] for r in listed} != expected_exes:
        raise ValueError("tested_executable_coverage_drift")
    exe_rows = {r["path"]: r for r in manifest["current_executables"]}
    for row in listed:
        pin = {k: row[k] for k in ["path", "bytes", "sha256"]}
        if pin != exe_rows[row["path"]] or not BASE.exact(pin):
            raise ValueError("tested_executable_pin_drift")
    if sum(r["listed_test_count"] for r in listed) != 301:
        raise ValueError("test_listing_counter_drift")
    if regression["source_freeze_verified_in_run"]["code_freeze_9_exact"] is not True:
        raise ValueError("tested_source_freeze_unverified")
    for key in ["performance_acceptance", "full_workspace_run", "hwpx_package_136_rerun"]:
        if runtime[key] is not False:
            raise ValueError("unsupported_runtime_scope_promotion")

def current():
    prior = inherited()
    data = json.loads((ROOT / CURRENT).read_bytes())
    return {"state": "pass_signed_formula_component_and_preservation_NOT_production_trust_actual_SQL_native_or_Gate",
            "checkpoint": BASE.pin(CURRENT), "inherited_raw_pin_entries": prior["inherited_raw_pin_entries"],
            "current_groups": verify_current_manifest(data, prior), "P09_gate": "OPEN", "product_complete": False}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(current() if args.current else inherited(), separators=(",", ":")))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"state": "fail", "error_type": type(error).__name__, "scope": "bytes_NOT_production_trust_SQL_native_or_Gate"}))
        raise SystemExit(1) from None
