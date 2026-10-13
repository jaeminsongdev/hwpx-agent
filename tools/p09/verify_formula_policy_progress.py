"""Exact actual-field policy-data/source binding ancestry; NOT issuer, SQL or execution qualification."""
import argparse
import importlib.util
import json
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p115_bytes", Path(__file__).with_name("verify_product_formula_request_progress.py"))
P115 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P115)
BASE, ROOT = P115.BASE, P115.ROOT
PREVIOUS = P115.CURRENT
CURRENT = "implementation/p09/evidence/p09-116-formula-policy.source-progress.v1.json"
PARENTS = ["crates/product-cli/src/form_stored_provider/actual_import/source_policy.rs",
           "crates/product-cli/src/form_product_request/stored_operations.rs",
           "crates/product-cli/src/form_product_request/stored_operations/formula.rs",
           "crates/product-cli/tests/form_stored_provider/actual_import.rs"]
ARCHIVE = "implementation/p09/source-archive/p09-116-pre-formula-policy/"
NEW_SOURCES = ["crates/product-cli/src/form_stored_provider/actual_import/source_policy/formulas.rs",
               "crates/product-cli/src/form_stored_provider/actual_import/source_policy/formulas/wire.rs",
               "crates/product-cli/src/form_stored_provider/actual_import/source_policy/formulas/targets.rs",
               "crates/product-cli/src/form_product_request/stored_operations/policy.rs",
               "crates/product-cli/tests/form_stored_provider/actual_import/formula_policy.rs",
               "tools/p09/verify_formula_policy_progress.py", "tools/p09/tests/test_formula_policy_progress.py",
               "implementation/p09/P09-116_FORMULA_POLICY_POLICY.md", "implementation/p09/P09-116_FORMULA_POLICY_REPORT.md",
               "protocol/migrations/p09-source-formula-policy-v0-to-v1.md",
               "implementation/p09/evidence/p09-116-formula-policy.initial-failures.v1.json",
               "implementation/p09/evidence/p09-116-formula-policy.preservation.v1.json",
               "implementation/p09/evidence/p09-116-formula-policy.source-regression.v1.json"]
ARCHIVES = [ARCHIVE + path for path in PARENTS] + [
    "implementation/p09/source-archive/p09-116-initial-fixture-conflict/" + path for path in NEW_SOURCES[:5]
] + ["implementation/p09/source-archive/p09-116-pre-lint-and-shape-strengthening/" + NEW_SOURCES[4]]
PREDECESSORS = [PREVIOUS, "implementation/p09/evidence/p09-115-product-formula-request.final-audit.v1.json"]
FALSE_QUALIFICATIONS = P115.FALSE_QUALIFICATIONS + ["formula_policy_trusted_issuer_verified", "formula_policy_SQL_repository_verified"]
EXE_ROOT = "target/p09-116-formula-policy/debug/"
TEST_STEMS = P115.TEST_STEMS
EXECUTABLES = [EXE_ROOT + "deps/" + stem + ".exe" for stem in TEST_STEMS] + [
    EXE_ROOT + "deps/hwpx_agent_cli.exe", EXE_ROOT + "hwpx-agent-cli.exe",
    EXE_ROOT + "deps/form_stored_provider-e02d02396d2f2bbd-initial-fixture-conflict.exe"]
ACCESSOR = b"    pub(super) const fn source(&self) -> &StoredImportedDocumentForms {\n        &self.source\n    }\n"
FACTORY = b"""    prepare_from_source(provider, request, raw, source, now)
}
pub(super) fn prepare_from_source<R, B, S, V>(
    provider: &StoredFormProvider<'_, R, B, S, V>,
    request: FormulaRequest,
    raw: &[u8],
    source: StoredImportedDocumentForms,
    now: u64,
) -> Result<PreparedStoredProductFormula, Error>
where
    R: ArtifactMetadataRepository,
    B: EncryptedBlobStore,
    S: ArtifactScanner,
    V: RevisionRepository,
{
    request.check(provider, now)?;
    source.verify(provider, now)?;
"""
EDITS = {PARENTS[0]: [b"pub mod formulas;\n"], PARENTS[1]: [b"pub mod policy;\n"],
         PARENTS[2]: [ACCESSOR, FACTORY],
         PARENTS[3]: [b'#[path = "actual_import/formula_policy.rs"]\nmod formula_policy;\n']}

class PreviousReadView:
    def __init__(self, root):
        self.root = root
    def __truediv__(self, path):
        return self.root / (ARCHIVE + str(path) if str(path) in PARENTS else path)

def original_sources():
    sources = P115.original_sources()
    sources.update({r["path"]: r for r in json.loads((ROOT / PREVIOUS).read_bytes())["source_delta"]})
    if len(sources) != 1034:
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
    if (checkpoint["bytes"], checkpoint["sha256"]) != (18280, "5c3919ff9ab79d74a4eb6c75eb1ba9c047263ac701f7805f909538d050adc4a7"):
        raise ValueError("previous_checkpoint_drift")
    if (final["bytes"], final["sha256"]) != (14873, "ad4eb9e4791996e3b92c45b09b7eec4fc22ffce2919361762709adb0081148dd"):
        raise ValueError("previous_final_audit_drift")
    sources = original_sources()
    for path in PARENTS:
        if not BASE.exact(sources[path], ARCHIVE + path):
            raise ValueError("whole_parent_preimage_drift")
        if restored_parent(path, (ROOT / path).read_bytes()) != (ROOT / (ARCHIVE + path)).read_bytes():
            raise ValueError("undeclared_parent_mutation")
    old_root, old_base = P115.ROOT, BASE.ROOT
    try:
        P115.ROOT = BASE.ROOT = PreviousReadView(ROOT)
        prior = P115.current()
    finally:
        P115.ROOT, BASE.ROOT = old_root, old_base
    raw = prior["inherited_raw_pin_entries"] + sum(prior["current_groups"].values())
    if raw != 2114 or prior["checkpoint"] != checkpoint:
        raise ValueError("inherited_raw_coverage_drift")
    unchanged = sum(BASE.exact(record) for path, record in sources.items() if path not in PARENTS)
    if unchanged != 1030:
        raise ValueError("unrelated_original_source_drift")
    return {"state": "pass_whole_original_ancestry_NOT_native_SQL_issuer_or_Gate",
            "previous_checkpoint": checkpoint, "inherited_raw_pin_entries": raw,
            "previous_source_files": 1034, "unchanged_previous_source_files": unchanged,
            "whole_parent_preimages": 4, "whole_parent_inverse_exact": True,
            "previous_unmodified_audit_on_preimages_passed": True,
            "old_executables_preserved": 440, "all_old_executables_reexecuted": False}

def verify_current_manifest(data, prior):
    if data["inherited_checkpoint"] != prior["previous_checkpoint"] or data["current_source_files_count"] != 1047:
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
    for key in ["actual_source_formula_policy_data_binding_verified", "original_product_formula_policy_data_gating_verified"]:
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
    return {"state": "pass_actual_formula_policy_data_product_gating_NOT_trusted_issuer_execution_native_SQL_or_Gate",
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
