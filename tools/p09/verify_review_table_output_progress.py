"""Read-only whole source inheritance and review table output evidence; NOT native/SQL/Gate."""
import argparse
import importlib.util
import json
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p103_bytes", Path(__file__).with_name("verify_review_table_context_progress.py"))
P103 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P103)
BASE, ROOT = P103.BASE, P103.ROOT
PREVIOUS = P103.CURRENT
CURRENT = "implementation/p09/evidence/p09-104-review-table-output.source-progress.v1.json"
ARCHIVE = "implementation/p09/source-archive/p09-104-pre-review-table-output/"
PARENTS = (
    "crates/hwpx-package/src/document_import/structure/review/table_create_context.rs",
    "crates/hwpx-package/src/table_ruling_hwpx/create_hwpx.rs",
    "crates/hwpx-package/src/table_ruling_hwpx.rs",
    "crates/hwpx-package/tests/review_table_create_context.rs",
)
NEW_SOURCES = (
    "crates/hwpx-package/src/document_import/structure/review/table_create_context/output.rs",
    "crates/hwpx-package/src/table_ruling_hwpx/create_hwpx/review_output.rs",
    "crates/hwpx-package/tests/review_table_output.rs",
    "tools/p09/verify_review_table_output_progress.py",
    "tools/p09/tests/test_review_table_output_progress.py",
    "implementation/p09/P09-104_REVIEW_TABLE_OUTPUT_POLICY.md",
    "implementation/p09/P09-104_REVIEW_TABLE_OUTPUT_REPORT.md",
    "protocol/migrations/p09-review-table-output-v0-to-v1.md",
    "implementation/p09/evidence/p09-104-review-table-output.initial-failures.v1.json",
    "implementation/p09/evidence/p09-104-review-table-output.preservation.v1.json",
    "implementation/p09/evidence/p09-104-review-table-output.source-regression.v1.json",
)
PREDECESSORS = (PREVIOUS, "implementation/p09/evidence/p09-103-review-table-context.final-audit.v1.json")
EXECUTABLES = [
    "target/p09-104-nested-diagnostic/debug/deps/review_table_output-b0f1a70b4428ad1b.exe",
    "target/p09-104-product/debug/deps/comment_operation-75493e8123c566c8.exe",
    "target/p09-104-product/debug/deps/form_stored_provider-e02d02396d2f2bbd.exe",
    "target/p09-104-product/debug/deps/hwpx_agent_cli.exe",
    "target/p09-104-product/debug/deps/stored_comment_provider-9065c76bcbac10b7.exe",
    "target/p09-104-review-table-output/debug/deps/review_table_output-b0f1a70b4428ad1b.exe",
    "target/p09-104-review-table-output-fixed/debug/deps/document_import_assembly_review-312fc213dbce8bd9.exe",
    "target/p09-104-review-table-output-fixed/debug/deps/document_import_memo_catalog-093bd8d5c2597e35.exe",
    "target/p09-104-review-table-output-fixed/debug/deps/document_import_review_metadata-8537eb795457ed5e.exe",
    "target/p09-104-review-table-output-fixed/debug/deps/document_import_review-67551457d524f20f.exe",
    "target/p09-104-review-table-output-fixed/debug/deps/hwpx_package-a850ad738bc59b10.exe",
    "target/p09-104-review-table-output-fixed/debug/deps/id_index-b06ac4c244093f4c.exe",
    "target/p09-104-review-table-output-fixed/debug/deps/memo_style_output-f87ca3d69966fa82.exe",
    "target/p09-104-review-table-output-fixed/debug/deps/patch_element_content-4a43081747b336ae.exe",
    "target/p09-104-review-table-output-fixed/debug/deps/patch_engine-f16fef8e94eda711.exe",
    "target/p09-104-review-table-output-fixed/debug/deps/review_body_output-8759bbf6453e18f5.exe",
    "target/p09-104-review-table-output-fixed/debug/deps/review_cell_body_output-581a88b7cee111ae.exe",
    "target/p09-104-review-table-output-fixed/debug/deps/review_delete_output-c5dd540b6b40acb8.exe",
    "target/p09-104-review-table-output-fixed/debug/deps/review_locations-64747444168c92b2.exe",
    "target/p09-104-review-table-output-fixed/debug/deps/review_paragraph_output-e7777a91049aeb82.exe",
    "target/p09-104-review-table-output-fixed/debug/deps/review_table_output-b0f1a70b4428ad1b.exe",
    "target/p09-104-review-table-output-fixed/debug/deps/text_flow-511dd1904a1b61b0.exe",
    "target/p09-104-review-table-output-nested-fixed/debug/deps/document_import_assembly_review-312fc213dbce8bd9.exe",
    "target/p09-104-review-table-output-nested-fixed/debug/deps/document_import_memo_catalog-093bd8d5c2597e35.exe",
    "target/p09-104-review-table-output-nested-fixed/debug/deps/document_import_review_metadata-8537eb795457ed5e.exe",
    "target/p09-104-review-table-output-nested-fixed/debug/deps/document_import_review-67551457d524f20f.exe",
    "target/p09-104-review-table-output-nested-fixed/debug/deps/hwpx_package-a850ad738bc59b10.exe",
    "target/p09-104-review-table-output-nested-fixed/debug/deps/id_index-b06ac4c244093f4c.exe",
    "target/p09-104-review-table-output-nested-fixed/debug/deps/memo_style_output-f87ca3d69966fa82.exe",
    "target/p09-104-review-table-output-nested-fixed/debug/deps/patch_element_content-4a43081747b336ae.exe",
    "target/p09-104-review-table-output-nested-fixed/debug/deps/patch_engine-f16fef8e94eda711.exe",
    "target/p09-104-review-table-output-nested-fixed/debug/deps/review_body_output-8759bbf6453e18f5.exe",
    "target/p09-104-review-table-output-nested-fixed/debug/deps/review_cell_body_output-581a88b7cee111ae.exe",
    "target/p09-104-review-table-output-nested-fixed/debug/deps/review_delete_output-c5dd540b6b40acb8.exe",
    "target/p09-104-review-table-output-nested-fixed/debug/deps/review_locations-64747444168c92b2.exe",
    "target/p09-104-review-table-output-nested-fixed/debug/deps/review_paragraph_output-e7777a91049aeb82.exe",
    "target/p09-104-review-table-output-nested-fixed/debug/deps/review_table_output-b0f1a70b4428ad1b.exe",
    "target/p09-104-review-table-output-nested-fixed/debug/deps/text_flow-511dd1904a1b61b0.exe",
    "target/p09-104-unbound-wrapper/debug/deps/review_table_output-b0f1a70b4428ad1b.exe"
]
ARCHIVES = [
    "implementation/p09/source-archive/p09-104-initial-cross-section-test/crates/hwpx-package/tests/review_table_output.rs",
    "implementation/p09/source-archive/p09-104-initial-lint/crates/hwpx-package/src/document_import/structure/review/table_create_context/output.rs",
    "implementation/p09/source-archive/p09-104-initial-lint/crates/hwpx-package/src/table_ruling_hwpx/create_hwpx/review_output.rs",
    "implementation/p09/source-archive/p09-104-initial-writer-api/crates/hwpx-package/src/document_import/structure/review/table_create_context/output.rs",
    "implementation/p09/source-archive/p09-104-nested-diagnostic/crates/hwpx-package/src/document_import/structure/review/table_create_context/output.rs",
    "implementation/p09/source-archive/p09-104-nested-runtime-failure/crates/hwpx-package/src/document_import/structure/review/table_create_context/output.rs",
    "implementation/p09/source-archive/p09-104-nested-runtime-failure/crates/hwpx-package/src/table_ruling_hwpx/create_hwpx/review_output.rs",
    "implementation/p09/source-archive/p09-104-nested-runtime-failure/crates/hwpx-package/tests/review_table_output.rs",
    "implementation/p09/source-archive/p09-104-nested-test-lint/crates/hwpx-package/tests/review_table_output.rs",
    "implementation/p09/source-archive/p09-104-pre-review-table-output/crates/hwpx-package/src/table_ruling_hwpx.rs",
    "implementation/p09/source-archive/p09-104-pre-review-table-output/crates/hwpx-package/src/document_import/structure/review/table_create_context.rs",
    "implementation/p09/source-archive/p09-104-pre-review-table-output/crates/hwpx-package/src/table_ruling_hwpx/create_hwpx.rs",
    "implementation/p09/source-archive/p09-104-pre-review-table-output/crates/hwpx-package/tests/review_table_create_context.rs",
    "implementation/p09/source-archive/p09-104-private-identity-test/crates/hwpx-package/tests/review_table_output.rs",
    "implementation/p09/source-archive/p09-104-test-lint/crates/hwpx-package/tests/review_table_output.rs",
    "implementation/p09/source-archive/p09-104-unbound-wrapper/crates/hwpx-package/src/table_ruling_hwpx/create_hwpx/review_output.rs",
    "implementation/p09/source-archive/p09-104-wrapper-arity/crates/hwpx-package/src/table_ruling_hwpx/create_hwpx/review_output.rs"
]
FALSE_QUALIFICATIONS = (
    "native_executed", "actual_SQL_executed", "SQL_failure_root_cause_proven",
    "full_comment_product_acceptance", "native_author_time_state_binding",
    "product_complete", "P10_new_implementation", "execution_publication_authority",
    "full_document_flow_bound", "native_caret_or_visual_coordinates_verified",
    "full_typed_comment_compiler_route_connected", "whole_package_ID_closure_verified",
    "full_document_protection_qualified", "all_historical_qualification_reexecuted",
)


class PreviousReadView:
    def __init__(self, root):
        self.root = root

    def __truediv__(self, path):
        return self.root / (ARCHIVE + path if path in PARENTS else path)


def original_sources():
    sources = P103.original_sources()
    sources.update({r["path"]: r for r in json.loads((ROOT / PREVIOUS).read_bytes())["source_delta"]})
    if len(sources) != 900:
        raise ValueError("prior_source_coverage_drift")
    return sources


def restored_parent(path, current):
    if path == PARENTS[0]:
        additions = (b"pub mod output;\n",)
    elif path == PARENTS[1]:
        additions = (b"mod review_output;\n", b"pub(crate) use review_output::{ReviewNativeTableOutput, ReviewTableRenderInput, render_review_table};\n")
    elif path == PARENTS[2]:
        additions = (b"pub(crate) use create_hwpx::{ReviewNativeTableOutput, ReviewTableRenderInput, render_review_table};\n",)
    elif path == PARENTS[3]:
        for name in (b"forms", b"source", b"template", b"anchor"):
            added = b"pub(super) fn " + name + b"("
            if current.count(added) != 1:
                raise ValueError("fixture_visibility_shape_drift")
            current = current.replace(added, b"fn " + name + b"(", 1)
        return current
    else:
        raise ValueError("undeclared_parent")
    for added in additions:
        if current.count(added) != 1:
            raise ValueError("additive_module_shape_drift")
        current = current.replace(added, b"", 1)
    return current


def parent_inverses(sources):
    for path in PARENTS:
        if not BASE.exact(sources[path], ARCHIVE + path):
            raise ValueError("parent_whole_preimage_drift")
        if restored_parent(path, (ROOT / path).read_bytes()) != (ROOT / (ARCHIVE + path)).read_bytes():
            raise ValueError("undeclared_original_parent_change")


def previous_audit():
    old_module, old_base = P103.ROOT, BASE.ROOT
    try:
        P103.ROOT = BASE.ROOT = PreviousReadView(ROOT)
        return P103.current()
    finally:
        P103.ROOT, BASE.ROOT = old_module, old_base


def inherited():
    checkpoint = BASE.pin(PREVIOUS)
    if checkpoint["bytes"] != 18075 or checkpoint["sha256"] != "a9beb6b1b3201840573c50603e7e2ea039d63601edf35ec01c706ea830eecdb6":
        raise ValueError("previous_checkpoint_drift")
    final = BASE.pin(PREDECESSORS[1])
    if final["bytes"] != 3868 or final["sha256"] != "65db80953974bd37e7664f56e25e46046bc48c0ec48b53cd6f55c9eb8ea6a380":
        raise ValueError("previous_final_audit_drift")
    sources = original_sources()
    parent_inverses(sources)
    prior = previous_audit()
    raw = prior["inherited_raw_pin_entries"] + sum(prior["current_groups"].values())
    if prior["checkpoint"] != checkpoint or raw != 1544:
        raise ValueError("prior_raw_coverage_drift")
    unchanged, preimages = 0, []
    for record in sources.values():
        if BASE.exact(record):
            unchanged += 1
        elif record["path"] in PARENTS and BASE.exact(record, ARCHIVE + record["path"]):
            preimages.append({**record, "archive_path": ARCHIVE + record["path"]})
        else:
            raise ValueError("prior_source_drift")
    if unchanged != 896 or len(preimages) != 4:
        raise ValueError("prior_source_or_parent_coverage_drift")
    return {
        "state": "pass_prior_raw_and_whole_parent_inverses_NOT_SQL_native_or_Gate",
        "previous_checkpoint": checkpoint, "inherited_raw_pin_entries": raw,
        "previous_current_source_files": 900, "unchanged_previous_source_files": unchanged,
        "whole_parent_preimages": preimages, "parent_inverse_exact": True,
        "previous_unchanged_audit_passed_on_exact_parent_preimages": True,
        "old_executables_preserved_not_reexecuted": 194,
        "all_historical_qualification_reexecuted": False,
    }


def verify_current_manifest(data, prior):
    if data["inherited_checkpoint"] != prior["previous_checkpoint"] or data["current_source_files_count"] != 911:
        raise ValueError("checkpoint_or_source_coverage_drift")
    required = {"source_delta": set(PARENTS + NEW_SOURCES),
                "source_archives_added": set(ARCHIVES),
                "predecessor_receipts_added": set(PREDECESSORS),
                "current_executables": set(EXECUTABLES)}
    counts = {}
    for key, paths in required.items():
        records = data[key]
        if len(records) != len(paths) or {r["path"] for r in records} != paths:
            raise ValueError("current_group_coverage_drift")
        if not all(BASE.exact(r) for r in records):
            raise ValueError("current_raw_pin_drift")
        counts[key] = len(records)
    for key in FALSE_QUALIFICATIONS:
        if data["qualification"][key] is not False:
            raise ValueError("unsupported_acceptance_promotion")
    if data["qualification"]["source_review_blank_table_output_implemented"] is not True:
        raise ValueError("source_output_evidence_missing")
    if data["qualification"]["P09_gate"] != "OPEN" or (ROOT / "PLANS.md").exists():
        raise ValueError("gate_or_deleted_plan_changed")
    return counts


def current():
    prior = inherited()
    data = json.loads((ROOT / CURRENT).read_bytes())
    return {"state": "pass_scoped_inheritance_and_source_table_output_delta_NOT_SQL_native_full_product_or_Gate",
            "checkpoint": BASE.pin(CURRENT), "inherited_raw_pin_entries": prior["inherited_raw_pin_entries"],
            "current_groups": verify_current_manifest(data, prior), "P09_gate": "OPEN", "product_complete": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(current() if args.current else inherited(), separators=(",", ":")))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"state": "fail", "error_type": type(error).__name__, "scope": "bytes_NOT_SQL_native_or_Gate"}))
        raise SystemExit(1) from error

