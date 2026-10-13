"""Whole preserved ancestry and generated formula registration bytes; not SQL/issuer/native/Gate."""
import argparse
import importlib.util
import json
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p117_bytes", Path(__file__).with_name("verify_formula_policy_sql_progress.py"))
P117 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P117)
BASE, ROOT = P117.BASE, P117.ROOT
PREVIOUS = P117.CURRENT
CURRENT = "implementation/p09/evidence/p09-118-formula-policy-registration.source-progress.v1.json"
PARENTS = ["crates/product-cli/src/form_stored_provider/actual_import/source_policy/formulas.rs",
           "crates/product-cli/tests/form_stored_provider/actual_import.rs"]
ARCHIVE = "implementation/p09/source-archive/p09-118-pre-formula-policy-registration/"
NEW_SOURCES = [
    "crates/product-cli/src/form_stored_provider/actual_import/source_policy/formulas/registration.rs",
    "crates/product-cli/src/form_stored_provider/actual_import/source_policy/formulas/registration/generation.rs",
    "crates/product-cli/src/form_stored_provider/actual_import/source_policy/formulas/registration/postgres.rs",
    "crates/product-cli/tests/form_stored_provider/actual_import/formula_policy_registration.rs",
    "tools/p09/verify_formula_policy_registration_progress.py",
    "tools/p09/tests/test_formula_policy_registration_progress.py",
    "implementation/p09/P09-118_FORMULA_POLICY_REGISTRATION_REPORT.md",
    "protocol/migrations/p09-generated-formula-policy-registration-v0-to-v1.md",
    "implementation/p09/evidence/p09-118-formula-policy-registration.source-regression.v1.json",
]
ARCHIVES = [ARCHIVE + p for p in PARENTS] + [
    "implementation/p09/source-archive/p09-118-initial-test-compile/" + NEW_SOURCES[3],
    "implementation/p09/source-archive/p09-118-initial-regression-and-lint/" + NEW_SOURCES[3]]
PREDECESSORS = [PREVIOUS, "implementation/p09/evidence/p09-117-formula-policy-sql.final-audit.v1.json"]
EXE_ROOT = "target/p09-118-formula-policy-registration/debug/"
EXECUTABLES = [EXE_ROOT + "deps/" + stem + ".exe" for stem in P117.TEST_STEMS] + [
    EXE_ROOT + "deps/hwpx_agent_cli.exe", EXE_ROOT + "hwpx-agent-cli.exe",
    EXE_ROOT + "deps/form_stored_provider-e02d02396d2f2bbd-initial-regression.exe"]
EDITS = {PARENTS[0]: b"pub mod registration;\n", PARENTS[1]:
         b'#[path = "actual_import/formula_policy_registration.rs"]\nmod formula_policy_registration;\n'}
FALSE_QUALIFICATIONS = list(P117.FALSE_QUALIFICATIONS) + [
    "trusted_formula_issuer_verified", "actual_SQL21_registration_verified"]

class PreviousReadView:
    def __init__(self, root):
        self.root = root
    def __truediv__(self, path):
        return self.root / (ARCHIVE + str(path) if str(path) in PARENTS else path)

def original_sources():
    sources = P117.original_sources()
    sources.update({r["path"]: r for r in json.loads((ROOT / PREVIOUS).read_bytes())["source_delta"]})
    if len(sources) != 1062:
        raise ValueError("prior_source_coverage_drift")
    return sources

def restored_parent(path, data):
    edit = EDITS[path]
    if data.count(edit) != 1:
        raise ValueError("declared_parent_edit_shape_drift")
    return data.replace(edit, b"", 1)

def inherited():
    checkpoint, final = [BASE.pin(p) for p in PREDECESSORS]
    if (checkpoint["bytes"], checkpoint["sha256"]) != (11263, "5b8a666378b17d6ddafee1b741d18b1bc64ee1da81ca3398435e3630f8249ea3"):
        raise ValueError("previous_checkpoint_drift")
    if (final["bytes"], final["sha256"]) != (11477, "52e6f4405c3eb5c4773045985403814d3be3d1a9bab893f3c0e1a8dfec4243cc"):
        raise ValueError("previous_final_audit_drift")
    sources = original_sources()
    for path in PARENTS:
        if not BASE.exact(sources[path], ARCHIVE + path):
            raise ValueError("whole_parent_preimage_drift")
        if restored_parent(path, (ROOT / path).read_bytes()) != (ROOT / (ARCHIVE + path)).read_bytes():
            raise ValueError("undeclared_parent_mutation")
    old_root, old_base = P117.ROOT, BASE.ROOT
    try:
        P117.ROOT = BASE.ROOT = PreviousReadView(ROOT)
        prior = P117.current()
    finally:
        P117.ROOT, BASE.ROOT = old_root, old_base
    raw = prior["inherited_raw_pin_entries"] + sum(prior["current_groups"].values())
    if raw != 2206 or prior["checkpoint"] != checkpoint:
        raise ValueError("inherited_raw_coverage_drift")
    unchanged = sum(BASE.exact(r) for p, r in sources.items() if p not in PARENTS)
    if unchanged != 1060:
        raise ValueError("unrelated_original_source_drift")
    return {"state": "pass_whole_previous_source_and_evidence_NOT_SQL_issuer_native_or_Gate",
            "previous_checkpoint": checkpoint, "inherited_raw_pin_entries": raw,
            "previous_source_files": 1062, "unchanged_previous_source_files": unchanged,
            "whole_parent_preimages": 2, "whole_parent_inverse_exact": True,
            "previous_unmodified_audit_on_preimages_passed": True,
            "old_executables_preserved": 473, "all_old_executables_reexecuted": False}

def verify_current_manifest(data, prior):
    if data["inherited_checkpoint"] != prior["previous_checkpoint"] or data["current_source_files_count"] != 1071:
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
    if data["qualification"]["source_derived_formula_policy_generation_registration_implemented"] is not True:
        raise ValueError("missing_actual_registration_implementation")
    if data["P09_gate"] != "OPEN" or data["P10_new_implementation"] is not False or data["product_complete"] is not False:
        raise ValueError("gate_or_product_promotion")
    if data["remaining_coarse_groups_minimum"] != 6 or data["remaining_coarse_groups_closed_by_slice"] != 0:
        raise ValueError("unsupported_remaining_reduction")
    return counts

def current():
    prior = inherited()
    data = json.loads((ROOT / CURRENT).read_bytes())
    return {"state": "pass_generated_formula_registration_and_preservation_NOT_actual_SQL_issuer_native_or_Gate",
            "checkpoint": BASE.pin(CURRENT), "inherited_raw_pin_entries": prior["inherited_raw_pin_entries"],
            "current_groups": verify_current_manifest(data, prior), "P09_gate": "OPEN", "product_complete": False}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(current() if args.current else inherited(), separators=(",", ":")))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"state": "fail", "error_type": type(error).__name__, "scope": "bytes_NOT_SQL_issuer_native_or_Gate"}))
        raise SystemExit(1) from None
