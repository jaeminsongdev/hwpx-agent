"""Whole ancestry and source-position math-result rebinding; NOT native/SQL/Gate."""
import argparse
import importlib.util
import json
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p112_bytes", Path(__file__).with_name("verify_formula_result_output_progress.py"))
P112 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P112)
BASE, ROOT = P112.BASE, P112.ROOT
PREVIOUS = P112.CURRENT
CURRENT = "implementation/p09/evidence/p09-113-formula-batch.source-progress.v1.json"
PARENT = "crates/hwpx-package/src/document_import/fields/semantics/evaluation/output/readback.rs"
ARCHIVE = "implementation/p09/source-archive/p09-113-pre-value-rebinding/"
NEW_SOURCES = ["crates/hwpx-package/tests/support/document_import_formula_batch_fixture.rs","crates/hwpx-package/tests/document_import_formula_batch.rs","crates/hwpx-package/src/document_import/fields/semantics/evaluation/output/readback/bindings.rs","crates/hwpx-package/src/document_import/fields/semantics/evaluation/output/readback/bindings/tests.rs","tools/p09/verify_formula_batch_progress.py","tools/p09/tests/test_formula_batch_progress.py","implementation/p09/P09-113_FORMULA_BATCH_VALUE_BINDING_POLICY.md","implementation/p09/P09-113_FORMULA_BATCH_VALUE_BINDING_REPORT.md","protocol/migrations/p09-formula-batch-value-binding-v0-to-v1.md","implementation/p09/evidence/p09-113-formula-batch.initial-failures.v1.json","implementation/p09/evidence/p09-113-formula-batch.preservation.v1.json","implementation/p09/evidence/p09-113-formula-batch.source-regression.v1.json"]
ARCHIVES = ["implementation/p09/source-archive/p09-113-initial-fixture/crates/hwpx-package/tests/support/document_import_formula_batch_fixture.rs","implementation/p09/source-archive/p09-113-initial-fixture/crates/hwpx-package/tests/document_import_formula_batch.rs","implementation/p09/source-archive/p09-113-initial-namespace/crates/hwpx-package/tests/document_import_formula_batch.rs","implementation/p09/source-archive/p09-113-initial-package-order/crates/hwpx-package/tests/document_import_formula_batch.rs","implementation/p09/source-archive/p09-113-initial-multi-part-patch/crates/hwpx-package/tests/support/document_import_formula_batch_fixture.rs","implementation/p09/source-archive/p09-113-initial-multi-part-patch/crates/hwpx-package/tests/document_import_formula_batch.rs","implementation/p09/source-archive/p09-113-initial-index/crates/hwpx-package/tests/document_import_formula_batch.rs","implementation/p09/source-archive/p09-113-pre-value-rebinding/crates/hwpx-package/src/document_import/fields/semantics/evaluation/output/readback.rs","implementation/p09/source-archive/p09-113-pre-value-rebinding/crates/hwpx-package/tests/support/document_import_formula_batch_fixture.rs","implementation/p09/source-archive/p09-113-pre-value-rebinding/crates/hwpx-package/tests/document_import_formula_batch.rs","implementation/p09/source-archive/p09-113-initial-empty-binding/crates/hwpx-package/src/document_import/fields/semantics/evaluation/output/readback/bindings.rs","implementation/p09/source-archive/p09-113-initial-empty-binding/crates/hwpx-package/tests/support/document_import_formula_batch_fixture.rs","implementation/p09/source-archive/p09-113-initial-lint/crates/hwpx-package/tests/support/document_import_formula_batch_fixture.rs","implementation/p09/source-archive/p09-113-initial-lint/crates/hwpx-package/tests/document_import_formula_batch.rs"]
PREDECESSORS = [PREVIOUS, "implementation/p09/evidence/p09-112-formula-result-output.final-audit.v1.json"]
EXECUTABLES = ["target/p09-113-formula-batch/debug/deps/document_import_formula_evaluation-7ce11a20f7395847.exe","target/p09-113-formula-batch/debug/deps/document_import_formula_output-3a092c4eef2e8f0f.exe","target/p09-113-formula-batch/debug/deps/document_import_formula_batch-bea22a1ddc584290.exe","target/p09-113-formula-batch/debug/deps/form_stored_provider-e02d02396d2f2bbd.exe","target/p09-113-formula-batch/debug/deps/hwpx_package-a850ad738bc59b10.exe","target/p09-113-formula-batch/debug/deps/id_index-b06ac4c244093f4c.exe","target/p09-113-formula-batch/debug/deps/patch_element_content-4a43081747b336ae.exe","target/p09-113-formula-batch/debug/deps/patch_engine-f16fef8e94eda711.exe","target/p09-113-formula-batch/debug/deps/patch_leaf_text-8e937ccb1f8696d7.exe","target/p09-113-formula-batch/debug/deps/review_cell_body_output-581a88b7cee111ae.exe","target/p09-113-formula-batch/debug/deps/review_delete_output-c5dd540b6b40acb8.exe","target/p09-113-formula-batch/debug/deps/table_formula-20f3bf8409a62442.exe","target/p09-113-formula-batch/debug/deps/text_flow-511dd1904a1b61b0.exe","target/p09-113-formula-batch/debug/deps/hwpx_agent_cli.exe","target/p09-113-formula-batch/debug/hwpx-agent-cli.exe","target/p09-113-formula-batch/debug/deps/document_import_formula_batch-bea22a1ddc584290-initial-fixture-failed.exe","target/p09-113-formula-batch/debug/deps/document_import_formula_batch-bea22a1ddc584290-namespace-failed.exe","target/p09-113-formula-batch/debug/deps/document_import_formula_batch-bea22a1ddc584290-package-order-failed.exe","target/p09-113-formula-batch/debug/deps/document_import_formula_batch-bea22a1ddc584290-multi-part-patch-failed.exe","target/p09-113-formula-batch/debug/deps/document_import_formula_batch-bea22a1ddc584290-index-failed.exe","target/p09-113-formula-batch/debug/deps/document_import_formula_batch-bea22a1ddc584290-readback-failed.exe","target/p09-113-formula-batch/debug/deps/document_import_formula_batch-bea22a1ddc584290-empty-binding-failed.exe","target/p09-113-formula-batch/debug/deps/document_import_formula_batch-bea22a1ddc584290-pre-lint.exe"]
EDITS = [["","mod bindings;\n"],["    for (old, new) in original.values.iter().zip(evaluated.values()) {\n        if old.value != new.value || old.coordinate != new.coordinate {\n            return Err(Error::Readback);\n        }\n    }\n","    bindings::verify(original, &meanings, &evaluated)?;\n"]]
FALSE_QUALIFICATIONS = P112.FALSE_QUALIFICATIONS

class PreviousReadView:
    def __init__(self, root):
        self.root = root
    def __truediv__(self, path):
        return self.root / (ARCHIVE + str(path) if str(path) == PARENT else path)

def original_sources():
    sources = P112.original_sources()
    sources.update({r["path"]: r for r in json.loads((ROOT / PREVIOUS).read_bytes())["source_delta"]})
    if len(sources) != 997:
        raise ValueError("prior_source_coverage_drift")
    return sources

def restored_parent(data):
    for old, new in EDITS:
        new = new.encode()
        if data.count(new) != 1:
            raise ValueError("declared_value_binding_edit_shape_drift")
        data = data.replace(new, old.encode(), 1)
    return data

def inherited():
    checkpoint = BASE.pin(PREVIOUS)
    if checkpoint["bytes"] != 21806 or checkpoint["sha256"] != "865619a8c97e63e42b47a599b63c11d888e4225575ef554343263b5b1b3b5053":
        raise ValueError("previous_checkpoint_drift")
    final = BASE.pin(PREDECESSORS[1])
    if final["bytes"] != 7839 or final["sha256"] != "3570b132da693790efce0b3e4d55c27d73dba10ad48fd4fa8deb5e8e8f19e2f5":
        raise ValueError("previous_final_audit_drift")
    sources = original_sources()
    if not BASE.exact(sources[PARENT], ARCHIVE + PARENT):
        raise ValueError("whole_original_parent_archive_drift")
    if restored_parent((ROOT / PARENT).read_bytes()) != (ROOT / (ARCHIVE + PARENT)).read_bytes():
        raise ValueError("undeclared_parent_mutation")
    old_root, old_base = P112.ROOT, BASE.ROOT
    try:
        P112.ROOT = BASE.ROOT = PreviousReadView(ROOT)
        prior = P112.current()
    finally:
        P112.ROOT, BASE.ROOT = old_root, old_base
    raw = prior["inherited_raw_pin_entries"] + sum(prior["current_groups"].values())
    if raw != 1958 or prior["checkpoint"] != checkpoint:
        raise ValueError("inherited_raw_coverage_drift")
    unchanged = 0
    for path, record in sources.items():
        if path != PARENT:
            if not BASE.exact(record):
                raise ValueError("unrelated_original_source_drift")
            unchanged += 1
    if unchanged != 996:
        raise ValueError("unchanged_prior_source_coverage_drift")
    return {"state": "pass_whole_original_ancestry_NOT_native_SQL_or_Gate",
            "previous_checkpoint": checkpoint, "inherited_raw_pin_entries": raw,
            "previous_source_files": 997, "unchanged_previous_source_files": unchanged,
            "whole_parent_preimages": 1, "whole_parent_inverse_exact": True,
            "previous_unmodified_audit_on_preimages_passed": True,
            "old_executables_preserved": 378, "all_old_executables_reexecuted": False}

def verify_current_manifest(data, prior):
    if data["inherited_checkpoint"] != prior["previous_checkpoint"] or data["current_source_files_count"] != 1009:
        raise ValueError("current_source_coverage_drift")
    required = {"source_delta": set([PARENT] + NEW_SOURCES), "source_archives_added": set(ARCHIVES),
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
    if data["qualification"]["actual_source_position_value_rebinding_verified"] is not True:
        raise ValueError("missing_value_rebinding")
    if data["P09_gate"] != "OPEN" or data["P10_new_implementation"] is not False or data["product_complete"] is not False:
        raise ValueError("gate_or_product_promotion")
    return counts

def current():
    prior = inherited()
    data = json.loads((ROOT / CURRENT).read_bytes())
    return {"state": "pass_source_position_value_rebinding_NOT_native_execution_publication_SQL_or_Gate",
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
        raise SystemExit(1) from None
