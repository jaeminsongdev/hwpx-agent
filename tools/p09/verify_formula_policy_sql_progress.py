"""Exact field-specific SQL source/bridge ancestry; NOT actual SQL, issuer or execution qualification."""
import argparse
import importlib.util
import json
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p116_bytes", Path(__file__).with_name("verify_formula_policy_progress.py"))
P116 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P116)
BASE, ROOT = P116.BASE, P116.ROOT
PREVIOUS = P116.CURRENT
CURRENT = "implementation/p09/evidence/p09-117-formula-policy-sql.source-progress.v1.json"
PARENTS = ["crates/revision-service/src/postgres.rs","crates/artifact-service/src/store/postgres_repository.rs","crates/product-cli/src/form_stored_provider/actual_import/source_policy/formulas.rs"]
ARCHIVE = "implementation/p09/source-archive/p09-117-pre-formula-policy-sql/"
NEW_SOURCES = ["crates/revision-service/src/postgres/source_formula_policy.rs","crates/revision-service/src/postgres/source_formula_policy/registration.rs","crates/artifact-service/src/store/postgres_repository/source_formula_policy.rs","crates/product-cli/src/form_stored_provider/actual_import/source_policy/formulas/postgres.rs","migrations/postgres/0021_p09_source_formula_policy.up.sql","migrations/postgres/0021_p09_source_formula_policy.down.sql","tools/p09/tests/test_formula_policy_sql_source.py","tools/p09/verify_formula_policy_sql_progress.py","tools/p09/tests/test_formula_policy_sql_progress.py","implementation/p09/P09-117_FORMULA_POLICY_SQL_POLICY.md","implementation/p09/P09-117_FORMULA_POLICY_SQL_REPORT.md","protocol/migrations/p09-source-formula-policy-sql20-to-sql21.md","implementation/p09/evidence/p09-117-formula-policy-sql.initial-failures.v1.json","implementation/p09/evidence/p09-117-formula-policy-sql.preservation.v1.json","implementation/p09/evidence/p09-117-formula-policy-sql.source-regression.v1.json"]
ARCHIVES = [ARCHIVE + path for path in PARENTS] + [
    "implementation/p09/source-archive/p09-117-initial-api-name-review/" + path for path in NEW_SOURCES[:5]
] + ["implementation/p09/source-archive/p09-117-pre-lint-fix/" + NEW_SOURCES[1],
     "implementation/p09/source-archive/p09-117-pre-unit-test-layout-fix/" + NEW_SOURCES[1]]
PREDECESSORS = [PREVIOUS, "implementation/p09/evidence/p09-116-formula-policy.final-audit.v1.json"]
FALSE_QUALIFICATIONS = P116.FALSE_QUALIFICATIONS
EXE_ROOT = "target/p09-117-formula-policy-sql/debug/"
TEST_STEMS = ["hwpx_agent_cli-0dbeda1edae1a540", "form_stored_provider-e02d02396d2f2bbd",
              "form_product_request-b9b309ced3b4e156", "form_value_operation-899bdd52f412e0da",
              "artifact_service-c722486ab67dc904", "revision_service-1b137e63992c86e2"]
EXECUTABLES = [EXE_ROOT + "deps/" + stem + ".exe" for stem in TEST_STEMS] + [
    EXE_ROOT + "deps/hwpx_agent_cli.exe", EXE_ROOT + "hwpx-agent-cli.exe"] + [
    EXE_ROOT + "deps/" + stem + "-pre-test-module-layout.exe" for stem in TEST_STEMS]
EDITS = {PARENTS[0]: [b"pub mod source_formula_policy;\n"], PARENTS[1]: [b"pub mod source_formula_policy;\n"],
         PARENTS[2]: [b"pub mod postgres;\n"]}

class PreviousReadView:
    def __init__(self, root):
        self.root = root
    def __truediv__(self, path):
        return self.root / (ARCHIVE + str(path) if str(path) in PARENTS else path)

def original_sources():
    sources = P116.original_sources()
    sources.update({r["path"]: r for r in json.loads((ROOT / PREVIOUS).read_bytes())["source_delta"]})
    if len(sources) != 1047:
        raise ValueError("prior_source_coverage_drift")
    return sources

def restored_parent(path, data):
    for edit in EDITS[path]:
        if data.count(edit) != 1:
            raise ValueError("declared_policy_parent_edit_shape_drift")
        data = data.replace(edit, b"", 1)
    return data

def inherited():
    checkpoint, final = [BASE.pin(path) for path in PREDECESSORS]
    if (checkpoint["bytes"], checkpoint["sha256"]) != (12155, "ec18119dd57c08567d28fc3acff9dc25691fc991a61f27c45e4a836d3efc02a9"):
        raise ValueError("previous_checkpoint_drift")
    if (final["bytes"], final["sha256"]) != (12185, "bd1ef0b39e5c1ffe9dbb847d5c20db3d7e1ab8f2f728591f12b44c4e6f3600bc"):
        raise ValueError("previous_final_audit_drift")
    sources = original_sources()
    for path in PARENTS:
        if not BASE.exact(sources[path], ARCHIVE + path):
            raise ValueError("whole_parent_preimage_drift")
        if restored_parent(path, (ROOT / path).read_bytes()) != (ROOT / (ARCHIVE + path)).read_bytes():
            raise ValueError("undeclared_parent_mutation")
    old_root, old_base = P116.ROOT, BASE.ROOT
    try:
        P116.ROOT = BASE.ROOT = PreviousReadView(ROOT)
        prior = P116.current()
    finally:
        P116.ROOT, BASE.ROOT = old_root, old_base
    raw = prior["inherited_raw_pin_entries"] + sum(prior["current_groups"].values())
    if raw != 2162 or prior["checkpoint"] != checkpoint:
        raise ValueError("inherited_raw_coverage_drift")
    unchanged = sum(BASE.exact(record) for path, record in sources.items() if path not in PARENTS)
    if unchanged != 1044:
        raise ValueError("unrelated_original_source_drift")
    return {"state": "pass_whole_original_ancestry_NOT_native_SQL_issuer_or_Gate",
            "previous_checkpoint": checkpoint, "inherited_raw_pin_entries": raw,
            "previous_source_files": 1047, "unchanged_previous_source_files": unchanged,
            "whole_parent_preimages": 3, "whole_parent_inverse_exact": True,
            "previous_unmodified_audit_on_preimages_passed": True,
            "old_executables_preserved": 459, "all_old_executables_reexecuted": False}

def verify_current_manifest(data, prior):
    if data["inherited_checkpoint"] != prior["previous_checkpoint"] or data["current_source_files_count"] != 1062:
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
    for key in ["source_formula_SQL_repository_and_bridge_implemented", "separate_formula_SQL_domain_and_original_guards_source_verified"]:
        if data["qualification"][key] is not True:
            raise ValueError("missing_actual_formula_policy_data_binding")
    if data["P09_gate"] != "OPEN" or data["P10_new_implementation"] is not False or data["product_complete"] is not False:
        raise ValueError("gate_or_product_promotion")
    if data["remaining_coarse_groups_minimum"] != 6 or data["remaining_coarse_groups_closed_by_slice"] != 0:
        raise ValueError("unsupported_remaining_reduction")
    return counts

def current():
    prior = inherited()
    data = json.loads((ROOT / CURRENT).read_bytes())
    return {"state": "pass_formula_SQL_source_bridge_NOT_actual_SQL_trusted_issuer_execution_native_or_Gate",
            "checkpoint": BASE.pin(CURRENT), "inherited_raw_pin_entries": prior["inherited_raw_pin_entries"],
            "current_groups": verify_current_manifest(data, prior), "P09_gate": "OPEN", "product_complete": False}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(current() if args.current else inherited(), separators=(",", ":")))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"state": "fail", "error_type": type(error).__name__, "scope": "bytes_NOT_issuer_native_or_Gate"}))
        raise SystemExit(1) from None
