"""Strict source-only product request and exact mathematical no-op preservation; NOT transport or Gate."""
import argparse
import importlib.util
import json
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p114_bytes", Path(__file__).with_name("verify_stored_formula_compiler_progress.py"))
P114 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P114)
BASE, ROOT = P114.BASE, P114.ROOT
PREVIOUS = P114.CURRENT
CURRENT = "implementation/p09/evidence/p09-115-product-formula-request.source-progress.v1.json"
PARENTS = ["crates/product-cli/src/form_product_request.rs","crates/product-cli/tests/form_stored_provider/actual_import.rs","crates/product-cli/src/form_stored_provider/actual_import/field_ranges/semantics/evaluation/output.rs","crates/product-cli/tests/form_stored_provider/actual_import/formula_compiler.rs"]
ARCHIVE = "implementation/p09/source-archive/p09-115-pre-product-formula-request/"
NEW_SOURCES = ["crates/product-cli/src/form_product_request/stored_operations.rs","crates/product-cli/src/form_product_request/stored_operations/request.rs","crates/product-cli/src/form_product_request/stored_operations/formula.rs","crates/product-cli/src/form_stored_provider/actual_import/field_ranges/semantics/evaluation/output/outcome.rs","crates/product-cli/tests/form_stored_provider/actual_import/formula_product_request.rs","tools/p09/verify_product_formula_request_progress.py","tools/p09/tests/test_product_formula_request_progress.py","implementation/p09/P09-115_PRODUCT_FORMULA_REQUEST_POLICY.md","implementation/p09/P09-115_PRODUCT_FORMULA_REQUEST_REPORT.md","protocol/migrations/p09-product-formula-request-v1-to-v2.md","implementation/p09/evidence/p09-115-product-formula-request.initial-failures.v1.json","implementation/p09/evidence/p09-115-product-formula-request.preservation.v1.json","implementation/p09/evidence/p09-115-product-formula-request.source-regression.v1.json"]
ARCHIVES = ["implementation/p09/source-archive/p09-115-initial-error-trait/crates/product-cli/src/form_product_request/stored_operations.rs","implementation/p09/source-archive/p09-115-initial-error-trait/crates/product-cli/src/form_product_request/stored_operations/formula.rs","implementation/p09/source-archive/p09-115-initial-error-trait/crates/product-cli/src/form_product_request/stored_operations/request.rs","implementation/p09/source-archive/p09-115-initial-strict-and-lint/crates/product-cli/src/form_product_request/stored_operations.rs","implementation/p09/source-archive/p09-115-initial-strict-and-lint/crates/product-cli/src/form_product_request/stored_operations/formula.rs","implementation/p09/source-archive/p09-115-initial-strict-and-lint/crates/product-cli/src/form_product_request/stored_operations/request.rs","implementation/p09/source-archive/p09-115-initial-strict-and-lint/crates/product-cli/src/form_stored_provider/actual_import/field_ranges/semantics/evaluation/output/outcome.rs","implementation/p09/source-archive/p09-115-initial-strict-and-lint/crates/product-cli/tests/form_stored_provider/actual_import/formula_product_request.rs","implementation/p09/source-archive/p09-115-pre-outcome-review/crates/product-cli/src/form_product_request/stored_operations/formula.rs","implementation/p09/source-archive/p09-115-pre-outcome-review/crates/product-cli/src/form_stored_provider/actual_import/field_ranges/semantics/evaluation/output/outcome.rs","implementation/p09/source-archive/p09-115-pre-product-formula-request/crates/product-cli/src/form_product_request.rs","implementation/p09/source-archive/p09-115-pre-product-formula-request/crates/product-cli/src/form_stored_provider/actual_import/field_ranges/semantics/evaluation/output.rs","implementation/p09/source-archive/p09-115-pre-product-formula-request/crates/product-cli/tests/form_stored_provider/actual_import.rs","implementation/p09/source-archive/p09-115-pre-product-formula-request/crates/product-cli/tests/form_stored_provider/actual_import/formula_compiler.rs","implementation/p09/source-archive/p09-115-sequence-admission-failure/crates/product-cli/src/form_product_request/stored_operations.rs","implementation/p09/source-archive/p09-115-sequence-admission-failure/crates/product-cli/src/form_product_request/stored_operations/formula.rs","implementation/p09/source-archive/p09-115-sequence-admission-failure/crates/product-cli/src/form_product_request/stored_operations/request.rs","implementation/p09/source-archive/p09-115-sequence-admission-failure/crates/product-cli/src/form_stored_provider/actual_import/field_ranges/semantics/evaluation/output/outcome.rs","implementation/p09/source-archive/p09-115-sequence-admission-failure/crates/product-cli/tests/form_stored_provider/actual_import/formula_product_request.rs","implementation/p09/source-archive/p09-115-strict-case-index/crates/product-cli/tests/form_stored_provider/actual_import/formula_product_request.rs"]
PREDECESSORS = [PREVIOUS, "implementation/p09/evidence/p09-114-stored-formula-compiler.final-audit.v1.json"]
EDITS = {PARENTS[0]: [b"", b"pub mod stored_operations;\n"],
         PARENTS[1]: [b"", b'#[path = "actual_import/formula_product_request.rs"]\nmod formula_product_request;\n'],
         PARENTS[2]: [b"", b"pub mod outcome;\n"],
         PARENTS[3]: [b"mod fixture;\n", b"pub(super) mod fixture;\n"]}
FALSE_QUALIFICATIONS = P114.FALSE_QUALIFICATIONS + ["CLI_transport_verified", "full_product_execution_verified"]
EXE_ROOT = "target/p09-115-product-formula-request/debug/"
TEST_STEMS = ["hwpx_agent_cli-0dbeda1edae1a540", "form_stored_provider-e02d02396d2f2bbd", "form_product_request-b9b309ced3b4e156",
              "form_value_operation-899bdd52f412e0da", "document_import_formula_evaluation-7ce11a20f7395847",
              "document_import_formula_output-3a092c4eef2e8f0f", "document_import_formula_batch-bea22a1ddc584290",
              "hwpx_package-a850ad738bc59b10", "id_index-b06ac4c244093f4c", "patch_element_content-4a43081747b336ae",
              "patch_engine-f16fef8e94eda711", "patch_leaf_text-8e937ccb1f8696d7", "review_cell_body_output-581a88b7cee111ae",
              "review_delete_output-c5dd540b6b40acb8", "table_formula-20f3bf8409a62442", "text_flow-511dd1904a1b61b0"]
EXECUTABLES = [EXE_ROOT + "deps/" + stem + ".exe" for stem in TEST_STEMS] + [
    EXE_ROOT + "deps/hwpx_agent_cli.exe", EXE_ROOT + "hwpx-agent-cli.exe",
    EXE_ROOT + "deps/form_stored_provider-e02d02396d2f2bbd-initial-strict-failed.exe",
    EXE_ROOT + "deps/form_stored_provider-e02d02396d2f2bbd-case-index-failed.exe",
    EXE_ROOT + "deps/form_stored_provider-e02d02396d2f2bbd-sequence-failed.exe"]

class PreviousReadView:
    def __init__(self, root):
        self.root = root
    def __truediv__(self, path):
        return self.root / (ARCHIVE + str(path) if str(path) in PARENTS else path)

def original_sources():
    sources = P114.original_sources()
    sources.update({r["path"]: r for r in json.loads((ROOT / PREVIOUS).read_bytes())["source_delta"]})
    if len(sources) != 1021:
        raise ValueError("prior_source_coverage_drift")
    return sources

def restored_parent(path, data):
    old, edit = EDITS[path]
    if data.count(edit) != 1:
        raise ValueError("declared_compiler_module_edit_shape_drift")
    return data.replace(edit, old, 1)

def inherited():
    checkpoint = BASE.pin(PREVIOUS)
    final = BASE.pin(PREDECESSORS[1])
    if (checkpoint["bytes"], checkpoint["sha256"]) != (13401, "6b36343cbd40d522f51aea69f24c01f1350db635167484d36b43950ceddae96d"):
        raise ValueError("previous_checkpoint_drift")
    if (final["bytes"], final["sha256"]) != (14039, "726895b115ae6bc795ed76a420605c8ff3d1b2ce1c515260b028dce1384e3aa1"):
        raise ValueError("previous_final_audit_drift")
    sources = original_sources()
    for path in PARENTS:
        if not BASE.exact(sources[path], ARCHIVE + path):
            raise ValueError("whole_parent_preimage_drift")
        if restored_parent(path, (ROOT / path).read_bytes()) != (ROOT / (ARCHIVE + path)).read_bytes():
            raise ValueError("undeclared_parent_mutation")
    old_root, old_base = P114.ROOT, BASE.ROOT
    try:
        P114.ROOT = BASE.ROOT = PreviousReadView(ROOT)
        prior = P114.current()
    finally:
        P114.ROOT, BASE.ROOT = old_root, old_base
    raw = prior["inherited_raw_pin_entries"] + sum(prior["current_groups"].values())
    if raw != 2054 or prior["checkpoint"] != checkpoint:
        raise ValueError("inherited_raw_coverage_drift")
    unchanged = sum(BASE.exact(record) for path, record in sources.items() if path not in PARENTS)
    if unchanged != 1017:
        raise ValueError("unrelated_original_source_drift")
    return {"state": "pass_whole_original_ancestry_NOT_native_SQL_or_Gate",
            "previous_checkpoint": checkpoint, "inherited_raw_pin_entries": raw,
            "previous_source_files": 1021, "unchanged_previous_source_files": unchanged,
            "whole_parent_preimages": 4, "whole_parent_inverse_exact": True,
            "previous_unmodified_audit_on_preimages_passed": True,
            "old_executables_preserved": 419, "all_old_executables_reexecuted": False}

def verify_current_manifest(data, prior):
    if data["inherited_checkpoint"] != prior["previous_checkpoint"] or data["current_source_files_count"] != 1034:
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
    if (data["qualification"]["actual_strict_product_request_dispatch_verified"] is not True
            or data["qualification"]["exact_original_protected_no_change_verified"] is not True):
        raise ValueError("missing_actual_product_request_dispatch")
    if data["P09_gate"] != "OPEN" or data["P10_new_implementation"] is not False or data["product_complete"] is not False:
        raise ValueError("gate_or_product_promotion")
    if data["remaining_coarse_groups_minimum"] != 6 or data["remaining_coarse_groups_closed_by_slice"] != 0:
        raise ValueError("unsupported_remaining_reduction")
    return counts

def current():
    prior = inherited()
    data = json.loads((ROOT / CURRENT).read_bytes())
    return {"state": "pass_strict_product_request_source_formula_noop_dispatch_NOT_transport_execution_native_SQL_or_Gate",
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
