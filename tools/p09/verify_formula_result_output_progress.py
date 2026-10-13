"""Read-only whole original ancestry and computed-result candidate binding, NOT native/Gate."""
import argparse
import importlib.util
import json
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p111_bytes", Path(__file__).with_name("verify_review_mutation_protection_progress.py"))
P111 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P111)
BASE, ROOT = P111.BASE, P111.ROOT
PREVIOUS = P111.CURRENT
CURRENT = "implementation/p09/evidence/p09-112-formula-result-output.source-progress.v1.json"
ARCHIVE = "implementation/p09/source-archive/p09-112-pre-formula-result-output/"
PARENTS = ["crates/hwpx-package/src/patch.rs","crates/hwpx-package/src/table_formula.rs","crates/hwpx-package/src/document_import/fields/semantics/evaluation.rs","crates/product-cli/src/form_stored_provider/actual_import/field_ranges/semantics/evaluation.rs","crates/product-cli/tests/form_stored_provider/actual_import.rs","crates/hwpx-package/src/document_import/structure/review/cell_body_output.rs"]
NEW_SOURCES = ["crates/hwpx-package/src/patch/leaf_text.rs","crates/hwpx-package/src/table_formula/result_output.rs","crates/hwpx-package/src/document_import/fields/semantics/evaluation/output.rs","crates/hwpx-package/src/document_import/fields/semantics/evaluation/output/readback.rs","crates/product-cli/src/form_stored_provider/actual_import/field_ranges/semantics/evaluation/output.rs","crates/hwpx-package/tests/patch_leaf_text.rs","crates/hwpx-package/tests/document_import_formula_output.rs","crates/hwpx-package/tests/support/document_import_formula_output_fixture.rs","crates/product-cli/tests/form_stored_provider/actual_import/formula_output.rs","tools/p09/verify_formula_result_output_progress.py","tools/p09/tests/test_formula_result_output_progress.py","implementation/p09/P09-112_FORMULA_RESULT_OUTPUT_POLICY.md","implementation/p09/P09-112_FORMULA_RESULT_OUTPUT_REPORT.md","protocol/migrations/p09-formula-result-output-v0-to-v1.md","implementation/p09/evidence/p09-112-formula-result-output.initial-failures.v1.json","implementation/p09/evidence/p09-112-formula-result-output.preservation.v1.json","implementation/p09/evidence/p09-112-formula-result-output.source-regression.v1.json"]
EDITS = json.loads(r'''{"crates/hwpx-package/src/patch.rs":[["","\nmod leaf_text;\n"],["","    /// Replace only a leaf's semantic text, including an empty/self-closing leaf.\n    /// Child elements, comments and root replacement are rejected; no raw XML is accepted.\n    ReplaceLeafText {\n        target: XmlElementSelector,\n        value: PatchText,\n    },\n"],["","            Self::ReplaceLeafText { target, value } => formatter\n                .debug_struct(\"ReplaceLeafText\")\n                .field(\"target\", target)\n                .field(\"value\", value)\n                .finish(),\n"],["","                PatchIntent::ReplaceLeafText { target, value } => {\n                    self.plan_leaf_text_edit(target, value, origin, &mut edits)?;\n                }\n"]],"crates/hwpx-package/src/table_formula.rs":[["","pub(crate) mod result_output;\n"]],"crates/hwpx-package/src/document_import/fields/semantics/evaluation.rs":[["","pub mod output;\n"]],"crates/product-cli/src/form_stored_provider/actual_import/field_ranges/semantics/evaluation.rs":[["","pub mod output;\n"]],"crates/product-cli/tests/form_stored_provider/actual_import.rs":[["","#[path = \"actual_import/formula_output.rs\"]\nmod formula_output;\n"]],"crates/hwpx-package/src/document_import/structure/review/cell_body_output.rs":[["pub(super) fn require_no_observed_mutation_protection(\n","pub(crate) fn require_no_observed_mutation_protection(\n"]]}''')
PREDECESSORS = [PREVIOUS, "implementation/p09/evidence/p09-111-review-mutation-protection.final-audit.v1.json"]
# Only newly owned source/archive/executable paths, never inferred native acceptance.
DIAGNOSTIC_ARCHIVES = {
    "p09-112-initial-regression": ["crates/hwpx-package/tests/document_import_formula_output.rs", "crates/hwpx-package/tests/patch_leaf_text.rs"],
    "p09-112-initial-compile": ["crates/hwpx-package/tests/support/document_import_formula_output_fixture.rs"],
    "p09-112-empty-result-readback": ["crates/hwpx-package/src/document_import/fields/semantics/evaluation/output.rs", "crates/hwpx-package/src/document_import/fields/semantics/evaluation/output/readback.rs", "crates/hwpx-package/tests/document_import_formula_output.rs"],
    "p09-112-initial-lint": ["crates/hwpx-package/src/document_import/fields/semantics/evaluation/output.rs", "crates/hwpx-package/src/document_import/fields/semantics/evaluation/output/readback.rs", "crates/hwpx-package/src/table_formula/result_output.rs", "crates/hwpx-package/tests/document_import_formula_output.rs"],
    "p09-112-test-lint": ["crates/hwpx-package/tests/patch_leaf_text.rs"],
    "p09-112-initial-evidence-test": ["tools/p09/verify_formula_result_output_progress.py", "tools/p09/tests/test_formula_result_output_progress.py", "implementation/p09/P09-112_FORMULA_RESULT_OUTPUT_REPORT.md", "implementation/p09/evidence/p09-112-formula-result-output.initial-failures.v1.json", "implementation/p09/evidence/p09-112-formula-result-output.preservation.v1.json", "implementation/p09/evidence/p09-112-formula-result-output.source-progress.v1.json"],
}
ARCHIVES = [ARCHIVE + p for p in PARENTS] + [
    "implementation/p09/source-archive/" + group + "/" + p
    for group, paths in DIAGNOSTIC_ARCHIVES.items() for p in paths
]
STEMS = ["document_import_formula_evaluation-7ce11a20f7395847", "document_import_formula_output-3a092c4eef2e8f0f",
         "form_stored_provider-e02d02396d2f2bbd", "hwpx_agent_cli", "hwpx_package-a850ad738bc59b10",
         "id_index-b06ac4c244093f4c", "patch_element_content-4a43081747b336ae", "patch_engine-f16fef8e94eda711",
         "patch_leaf_text-8e937ccb1f8696d7", "review_cell_body_output-581a88b7cee111ae",
         "review_delete_output-c5dd540b6b40acb8", "table_formula-20f3bf8409a62442", "text_flow-511dd1904a1b61b0"]
EXE_ROOT = "target/p09-112-formula-result-output/debug/"
EXECUTABLES = [EXE_ROOT + "deps/" + name + suffix + ".exe" for name in STEMS for suffix in ["", "-pre-lint-refactor"]] + [
    EXE_ROOT + "hwpx-agent-cli.exe", EXE_ROOT + "deps/document_import_formula_output-3a092c4eef2e8f0f-initial-failed.exe",
    EXE_ROOT + "deps/document_import_formula_output-3a092c4eef2e8f0f-empty-result-failed.exe"
]
FALSE_QUALIFICATIONS = ["native_recalculation_verified", "full_field_policy_qualified", "issuer_verified",
                        "atomic_execution_publication_verified", "actual_SQL_verified", "P09_complete", "product_complete"]

class PreviousReadView:
    def __init__(self, root):
        self.root = root
    def __truediv__(self, path):
        return self.root / (ARCHIVE + str(path) if str(path) in PARENTS else path)

def original_sources():
    sources = P111.original_sources()
    sources.update({r["path"]: r for r in json.loads((ROOT / PREVIOUS).read_bytes())["source_delta"]})
    if len(sources) != 980:
        raise ValueError("prior_source_coverage_drift")
    return sources

def restored_parent(path, data):
    if path not in PARENTS:
        raise ValueError("undeclared_parent")
    for old, addition in EDITS[path]:
        addition = addition.encode()
        if data.count(addition) != 1:
            raise ValueError("declared_formula_result_addition_shape_drift")
        data = data.replace(addition, old.encode(), 1)
    return data

def inherited():
    checkpoint = BASE.pin(PREVIOUS)
    if checkpoint["bytes"] != 21977 or checkpoint["sha256"] != "1c64001f27f9de08ea13d4ae39be76fa8b8f152cc576790708d7b38adf2d84c0":
        raise ValueError("previous_checkpoint_drift")
    final = BASE.pin(PREDECESSORS[1])
    if final["bytes"] != 6702 or final["sha256"] != "962b0d65d857c4a4a9234016a1199d27616e125a50eaa3d08c93d3da51badf63":
        raise ValueError("previous_final_audit_drift")
    sources = original_sources()
    for path in PARENTS:
        if not BASE.exact(sources[path], ARCHIVE + path):
            raise ValueError("original_parent_archive_drift")
        if restored_parent(path, (ROOT / path).read_bytes()) != (ROOT / (ARCHIVE + path)).read_bytes():
            raise ValueError("undeclared_parent_mutation")
    old_root, old_base = P111.ROOT, BASE.ROOT
    try:
        P111.ROOT = BASE.ROOT = PreviousReadView(ROOT)
        prior = P111.current()
    finally:
        P111.ROOT, BASE.ROOT = old_root, old_base
    raw = prior["inherited_raw_pin_entries"] + sum(prior["current_groups"].values())
    if raw != 1881 or prior["checkpoint"] != checkpoint:
        raise ValueError("inherited_raw_coverage_drift")
    unchanged = 0
    for path, record in sources.items():
        if path not in PARENTS:
            if not BASE.exact(record):
                raise ValueError("unrelated_original_source_drift")
            unchanged += 1
    if unchanged != 974:
        raise ValueError("unchanged_prior_source_coverage_drift")
    return {"state": "pass_whole_original_ancestry_NOT_native_SQL_or_Gate", "previous_checkpoint": checkpoint,
            "inherited_raw_pin_entries": raw, "previous_source_files": 980, "unchanged_previous_source_files": unchanged,
            "whole_parent_preimages": 6, "whole_parent_inverse_exact": True,
            "previous_unmodified_audit_on_preimages_passed": True, "old_executables_preserved": 349,
            "all_old_executables_reexecuted": False}

def verify_current_manifest(data, prior):
    if data["inherited_checkpoint"] != prior["previous_checkpoint"] or data["current_source_files_count"] != 997:
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
    if data["qualification"]["original_computed_results_preserving_candidate_bound"] is not True:
        raise ValueError("missing_result_binding")
    if data["P09_gate"] != "OPEN" or data["P10_new_implementation"] is not False or data["product_complete"] is not False:
        raise ValueError("gate_or_product_promotion")
    return counts

def current():
    prior = inherited()
    data = json.loads((ROOT / CURRENT).read_bytes())
    return {"state": "pass_source_math_result_candidate_NOT_native_execution_publication_SQL_or_Gate",
            "checkpoint": BASE.pin(CURRENT), "inherited_raw_pin_entries": prior["inherited_raw_pin_entries"],
            "current_groups": verify_current_manifest(data, prior), "P09_gate": "OPEN", "product_complete": False}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(current() if args.current else inherited(), separators=(",", ":")))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"state": "fail", "error_type": type(error).__name__, "scope": "bytes_NOT_native_or_Gate"}))
        raise SystemExit(1) from error

