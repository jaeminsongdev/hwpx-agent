"""Read-only source/table-context inheritance. NOT output, SQL/native or Gate proof."""
import argparse
import importlib.util
import json
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p102_bytes", Path(__file__).with_name("verify_review_paragraph_progress.py"))
P102 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P102)
BASE, ROOT = P102.BASE, P102.ROOT
PREVIOUS = P102.CURRENT
CURRENT = "implementation/p09/evidence/p09-103-review-table-context.source-progress.v1.json"
ARCHIVE = "implementation/p09/source-archive/p09-103-pre-review-table-context/"
PARENTS = (
    "crates/hwpx-package/src/document_import/structure/review.rs",
    "crates/hwpx-package/src/table_ruling_hwpx.rs",
    "crates/hwpx-package/src/table_ruling_hwpx/create_hwpx.rs",
    "crates/hwpx-package/tests/table_create_hwpx.rs",
)
NEW_SOURCES = (
    "crates/hwpx-package/src/document_import/structure/review/table_create_context.rs",
    "crates/hwpx-package/tests/review_table_create_context.rs",
    "tools/p09/verify_review_table_context_progress.py",
    "tools/p09/tests/test_review_table_context_progress.py",
    "implementation/p09/P09-103_REVIEW_TABLE_CONTEXT_POLICY.md",
    "implementation/p09/P09-103_REVIEW_TABLE_CONTEXT_REPORT.md",
    "protocol/migrations/p09-review-table-context-v0-to-v1.md",
    "implementation/p09/evidence/p09-103-review-table-context.initial-failures.v1.json",
    "implementation/p09/evidence/p09-103-review-table-context.preservation.v1.json",
    "implementation/p09/evidence/p09-103-review-table-context.source-regression.v1.json",
)
PREDECESSORS = (PREVIOUS, "implementation/p09/evidence/p09-102-review-paragraph.final-audit.v1.json")
EXECUTABLES = (
    "target/p09-103-product/debug/deps/comment_operation-75493e8123c566c8.exe",
    "target/p09-103-product/debug/deps/form_stored_provider-e02d02396d2f2bbd.exe",
    "target/p09-103-product/debug/deps/hwpx_agent_cli.exe",
    "target/p09-103-product/debug/deps/stored_comment_provider-9065c76bcbac10b7.exe",
    "target/p09-103-review-table-fixed/debug/deps/document_import_assembly_review-312fc213dbce8bd9.exe",
    "target/p09-103-review-table-fixed/debug/deps/document_import_memo_catalog-093bd8d5c2597e35.exe",
    "target/p09-103-review-table-fixed/debug/deps/document_import_review-67551457d524f20f.exe",
    "target/p09-103-review-table-fixed/debug/deps/document_import_review_metadata-8537eb795457ed5e.exe",
    "target/p09-103-review-table-fixed/debug/deps/hwpx_package-a850ad738bc59b10.exe",
    "target/p09-103-review-table-fixed/debug/deps/id_index-b06ac4c244093f4c.exe",
    "target/p09-103-review-table-fixed/debug/deps/memo_style_output-f87ca3d69966fa82.exe",
    "target/p09-103-review-table-fixed/debug/deps/patch_element_content-4a43081747b336ae.exe",
    "target/p09-103-review-table-fixed/debug/deps/patch_engine-f16fef8e94eda711.exe",
    "target/p09-103-review-table-fixed/debug/deps/review_body_output-8759bbf6453e18f5.exe",
    "target/p09-103-review-table-fixed/debug/deps/review_cell_body_output-581a88b7cee111ae.exe",
    "target/p09-103-review-table-fixed/debug/deps/review_delete_output-c5dd540b6b40acb8.exe",
    "target/p09-103-review-table-fixed/debug/deps/review_locations-64747444168c92b2.exe",
    "target/p09-103-review-table-fixed/debug/deps/review_paragraph_output-e7777a91049aeb82.exe",
    "target/p09-103-review-table-fixed/debug/deps/review_table_create_context-2793d29784bd572c.exe",
    "target/p09-103-review-table-fixed/debug/deps/text_flow-511dd1904a1b61b0.exe",
    "target/p09-103-review-table/debug/deps/document_import_assembly_review-312fc213dbce8bd9.exe",
    "target/p09-103-review-table/debug/deps/document_import_memo_catalog-093bd8d5c2597e35.exe",
    "target/p09-103-review-table/debug/deps/document_import_review-67551457d524f20f.exe",
    "target/p09-103-review-table/debug/deps/document_import_review_metadata-8537eb795457ed5e.exe",
    "target/p09-103-review-table/debug/deps/hwpx_package-a850ad738bc59b10.exe",
    "target/p09-103-review-table/debug/deps/id_index-b06ac4c244093f4c.exe",
    "target/p09-103-review-table/debug/deps/memo_style_output-f87ca3d69966fa82.exe",
    "target/p09-103-review-table/debug/deps/patch_element_content-4a43081747b336ae.exe",
    "target/p09-103-review-table/debug/deps/patch_engine-f16fef8e94eda711.exe",
    "target/p09-103-review-table/debug/deps/review_body_output-8759bbf6453e18f5.exe",
    "target/p09-103-review-table/debug/deps/review_cell_body_output-581a88b7cee111ae.exe",
    "target/p09-103-review-table/debug/deps/review_delete_output-c5dd540b6b40acb8.exe",
    "target/p09-103-review-table/debug/deps/review_locations-64747444168c92b2.exe",
    "target/p09-103-review-table/debug/deps/review_paragraph_output-e7777a91049aeb82.exe",
    "target/p09-103-review-table/debug/deps/review_table_create_context-2793d29784bd572c.exe",
    "target/p09-103-review-table/debug/deps/text_flow-511dd1904a1b61b0.exe",
)
FAILURE_ARCHIVES = {
    "implementation/p09/source-archive/p09-103-initial-build/" + PARENTS[2],
    "implementation/p09/source-archive/p09-103-initial-build/" + NEW_SOURCES[0],
    "implementation/p09/source-archive/p09-103-second-build/" + PARENTS[2],
    "implementation/p09/source-archive/p09-103-private-test/" + NEW_SOURCES[1],
    "implementation/p09/source-archive/p09-103-initial-lint/" + PARENTS[2],
    "implementation/p09/source-archive/p09-103-initial-lint/" + NEW_SOURCES[0],
    "implementation/p09/source-archive/p09-103-invalid-boolean-test/" + NEW_SOURCES[1],
    "implementation/p09/source-archive/p09-103-large-packet-lint/" + PARENTS[2],
    "implementation/p09/source-archive/p09-103-large-packet-lint/" + NEW_SOURCES[0],
}
FALSE_QUALIFICATIONS = (
    "native_executed", "actual_SQL_executed", "SQL_failure_root_cause_proven",
    "full_comment_product_acceptance", "native_author_time_state_binding",
    "product_complete", "P10_new_implementation", "execution_publication_authority",
    "new_table_insertion_implemented", "full_document_flow_bound",
    "native_caret_or_visual_coordinates_verified", "full_typed_comment_compiler_route_connected",
    "whole_package_ID_closure_verified", "full_document_protection_qualified",
)


class PreviousReadView:
    def __init__(self, root):
        self.root = root

    def __truediv__(self, path):
        return self.root / (ARCHIVE + path if path in PARENTS else path)


def original_sources():
    sources = P102.original_sources()
    sources.update({r["path"]: r for r in json.loads((ROOT / PREVIOUS).read_bytes())["source_delta"]})
    if len(sources) != 890:
        raise ValueError("prior_source_coverage_drift")
    return sources


def restored_parent(path, current):
    if path == PARENTS[0]:
        added = b"pub mod table_create_context;\n"
        if current.count(added) != 1:
            raise ValueError("module_transform_shape_drift")
        return current.replace(added, b"", 1)
    if path == PARENTS[1]:
        added = b"pub(crate) use create_hwpx::ReviewCreateContextInput;\n"
        if current.count(added) != 1:
            raise ValueError("internal_export_transform_shape_drift")
        return current.replace(added, b"", 1)
    if path == PARENTS[2]:
        begin = b"// BEGIN source-bound review context. The original public reader/lowerer stays unchanged.\n"
        end = b"// END source-bound review context.\n\n"
        if current.count(begin) != 1 or current.count(end) != 1:
            raise ValueError("new_block_transform_shape_drift")
        left, right = current.index(begin), current.index(end) + len(end)
        if left >= right:
            raise ValueError("new_block_order_drift")
        return current[:left] + current[right:]
    if path == PARENTS[3]:
        for name in (b"header", b"empty_paragraph", b"template_section", b"package"):
            added = b"pub(super) fn " + name + b"("
            if current.count(added) != 1:
                raise ValueError("fixture_visibility_transform_shape_drift")
            current = current.replace(added, b"fn " + name + b"(", 1)
        return current
    raise ValueError("undeclared_parent")


def parent_inverses(sources):
    for path in PARENTS:
        if not BASE.exact(sources[path], ARCHIVE + path):
            raise ValueError("parent_whole_preimage_drift")
        if restored_parent(path, (ROOT / path).read_bytes()) != (ROOT / (ARCHIVE + path)).read_bytes():
            raise ValueError("undeclared_original_parent_change")


def previous_audit():
    old_module, old_base = P102.ROOT, BASE.ROOT
    try:
        P102.ROOT = BASE.ROOT = PreviousReadView(ROOT)
        return P102.current()
    finally:
        P102.ROOT, BASE.ROOT = old_module, old_base


def inherited():
    checkpoint = BASE.pin(PREVIOUS)
    if checkpoint["bytes"] != 14128 or checkpoint["sha256"] != "afafcd454d908767dd59041a4d4ce7179fd5c677c652b9075df1c81c92012863":
        raise ValueError("previous_checkpoint_drift")
    final = BASE.pin(PREDECESSORS[1])
    if final["bytes"] != 8248 or final["sha256"] != "1f8d4cea58917e1c1c8ebe5d752293123ac115ab977b497d6bb3e35677978287":
        raise ValueError("previous_final_audit_drift")
    sources = original_sources()
    parent_inverses(sources)
    prior = previous_audit()
    raw = prior["inherited_raw_pin_entries"] + sum(prior["current_groups"].values())
    if prior["checkpoint"] != checkpoint or raw != 1479:
        raise ValueError("prior_raw_coverage_drift")
    preimages, unchanged = [], 0
    for record in sources.values():
        if BASE.exact(record):
            unchanged += 1
        elif record["path"] in PARENTS and BASE.exact(record, ARCHIVE + record["path"]):
            preimages.append({**record, "archive_path": ARCHIVE + record["path"]})
        else:
            raise ValueError("prior_source_drift")
    if unchanged != 886 or len(preimages) != 4:
        raise ValueError("prior_source_or_parent_coverage_drift")
    return {"state": "pass_original_raw_prior_view_and_whole_parent_inverses_NOT_table_output_SQL_native_or_Gate",
            "previous_checkpoint": checkpoint, "inherited_raw_pin_entries": raw,
            "previous_current_source_files": 890, "unchanged_previous_source_files": unchanged,
            "whole_parent_preimages": preimages, "parent_inverse_exact": True,
            "previous_unchanged_audit_passed_on_exact_parent_preimages": True,
            "old_executables_preserved_not_reexecuted": 158,
            "all_historical_qualification_reexecuted": False}


def verify_current_manifest(data, prior):
    if data["inherited_checkpoint"] != prior["previous_checkpoint"] or data["current_source_files_count"] != 900:
        raise ValueError("checkpoint_or_source_coverage_drift")
    required = {"source_delta": set(PARENTS + NEW_SOURCES),
                "source_archives_added": {ARCHIVE + p for p in PARENTS} | FAILURE_ARCHIVES,
                "predecessor_receipts_added": set(PREDECESSORS)}
    counts = {}
    for key, paths in required.items():
        records = data[key]
        if len(records) != len(paths) or {r["path"] for r in records} != paths:
            raise ValueError("current_group_coverage_drift")
        if not all(BASE.exact(r) for r in records):
            raise ValueError("current_raw_pin_drift")
        counts[key] = len(records)
    expected = EXECUTABLES
    records = data["current_executables"]
    if len(records) != len(expected) or {r["path"] for r in records} != set(expected):
        raise ValueError("executable_coverage_drift")
    if not all(BASE.exact(r) for r in records):
        raise ValueError("executable_raw_pin_drift")
    counts["current_executables"] = len(records)
    for key in FALSE_QUALIFICATIONS:
        if data["qualification"][key] is not False:
            raise ValueError("unsupported_acceptance_promotion")
    if data["qualification"]["P09_gate"] != "OPEN" or (ROOT / "PLANS.md").exists():
        raise ValueError("gate_or_deleted_plan_changed")
    return counts


def current():
    prior = inherited()
    data = json.loads((ROOT / CURRENT).read_bytes())
    return {"state": "pass_scoped_inheritance_and_table_context_delta_NOT_output_SQL_native_or_Gate",
            "checkpoint": BASE.pin(CURRENT), "inherited_raw_pin_entries": prior["inherited_raw_pin_entries"],
            "current_groups": verify_current_manifest(data, prior), "P09_gate": "OPEN", "product_complete": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(current() if args.current else inherited(), separators=(",", ":")))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"state": "fail", "error_type": type(error).__name__, "scope": "bytes_NOT_output_SQL_native_or_Gate"}))
        raise SystemExit(1) from error
