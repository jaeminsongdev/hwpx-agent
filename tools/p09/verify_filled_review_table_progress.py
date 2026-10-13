"""Read-only new table cell composition evidence; NOT full Flow/native/SQL/publication."""
import argparse
import importlib.util
import json
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p105_bytes", Path(__file__).with_name("verify_stored_review_table_progress.py"))
P105 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P105)
BASE, ROOT = P105.BASE, P105.ROOT
PREVIOUS = P105.CURRENT
CURRENT = "implementation/p09/evidence/p09-106-filled-review-table.source-progress.v1.json"
ARCHIVE = "implementation/p09/source-archive/p09-106-pre-filled-review-table/"
PARENTS = ("crates/hwpx-package/src/document_import/structure/review/table_create_context.rs",)
NEW_SOURCES = (
    "crates/hwpx-package/src/document_import/structure/review/table_create_context/filled_output.rs",
    "crates/hwpx-package/tests/review_filled_table_output.rs",
    "tools/p09/verify_filled_review_table_progress.py",
    "tools/p09/tests/test_filled_review_table_progress.py",
    "implementation/p09/P09-106_FILLED_REVIEW_TABLE_POLICY.md",
    "implementation/p09/P09-106_FILLED_REVIEW_TABLE_REPORT.md",
    "protocol/migrations/p09-filled-review-table-v0-to-v1.md",
    "implementation/p09/evidence/p09-106-filled-review-table.initial-failures.v1.json",
    "implementation/p09/evidence/p09-106-filled-review-table.preservation.v1.json",
    "implementation/p09/evidence/p09-106-filled-review-table.source-regression.v1.json",
)
PREDECESSORS = (PREVIOUS, "implementation/p09/evidence/p09-105-stored-review-table.final-audit.v1.json")
# These inventories are frozen to actual build outputs after tests, not a glob/passing-test count.
EXECUTABLES = [
    "target/p09-106-filled-review-table/debug/deps/document_import_assembly_review-312fc213dbce8bd9.exe",
    "target/p09-106-filled-review-table/debug/deps/document_import_memo_catalog-093bd8d5c2597e35.exe",
    "target/p09-106-filled-review-table/debug/deps/document_import_review_metadata-8537eb795457ed5e.exe",
    "target/p09-106-filled-review-table/debug/deps/document_import_review-67551457d524f20f.exe",
    "target/p09-106-filled-review-table/debug/deps/hwpx_package-a850ad738bc59b10.exe",
    "target/p09-106-filled-review-table/debug/deps/id_index-b06ac4c244093f4c.exe",
    "target/p09-106-filled-review-table/debug/deps/memo_style_output-f87ca3d69966fa82.exe",
    "target/p09-106-filled-review-table/debug/deps/patch_element_content-4a43081747b336ae.exe",
    "target/p09-106-filled-review-table/debug/deps/patch_engine-f16fef8e94eda711.exe",
    "target/p09-106-filled-review-table/debug/deps/review_body_output-8759bbf6453e18f5.exe",
    "target/p09-106-filled-review-table/debug/deps/review_cell_body_output-581a88b7cee111ae.exe",
    "target/p09-106-filled-review-table/debug/deps/review_delete_output-c5dd540b6b40acb8.exe",
    "target/p09-106-filled-review-table/debug/deps/review_filled_table_output-c9fe0a354b64314c.exe",
    "target/p09-106-filled-review-table/debug/deps/review_locations-64747444168c92b2.exe",
    "target/p09-106-filled-review-table/debug/deps/review_paragraph_output-e7777a91049aeb82.exe",
    "target/p09-106-filled-review-table/debug/deps/review_table_output-b0f1a70b4428ad1b.exe",
    "target/p09-106-filled-review-table/debug/deps/text_flow-511dd1904a1b61b0.exe",
    "target/p09-106-product/debug/deps/comment_operation-75493e8123c566c8.exe",
    "target/p09-106-product/debug/deps/form_stored_provider-e02d02396d2f2bbd.exe",
    "target/p09-106-product/debug/deps/hwpx_agent_cli.exe",
    "target/p09-106-product/debug/deps/stored_comment_provider-9065c76bcbac10b7.exe",
    "target/p09-106-pre-lint-regression/debug/deps/review_filled_table_output-c9fe0a354b64314c.exe",
]
ARCHIVES = [
    ARCHIVE + PARENTS[0],
    "implementation/p09/source-archive/p09-106-initial-build/crates/hwpx-package/src/document_import/structure/review/table_create_context/filled_output.rs",
    "implementation/p09/source-archive/p09-106-test-build/crates/hwpx-package/tests/review_filled_table_output.rs",
    "implementation/p09/source-archive/p09-106-initial-lint/crates/hwpx-package/tests/review_filled_table_output.rs",
]
FALSE_QUALIFICATIONS = P105.FALSE_QUALIFICATIONS + ("stored_filled_table_route_qualified",)


class PreviousReadView:
    def __init__(self, root):
        self.root = root

    def __truediv__(self, path):
        return self.root / (ARCHIVE + path if path in PARENTS else path)


def original_sources():
    sources = P105.original_sources()
    sources.update({r["path"]: r for r in json.loads((ROOT / PREVIOUS).read_bytes())["source_delta"]})
    if len(sources) != 922:
        raise ValueError("prior_source_coverage_drift")
    return sources


def restored_parent(path, current):
    if path not in PARENTS:
        raise ValueError("undeclared_parent")
    added = b"pub mod filled_output;\n"
    if current.count(added) != 1:
        raise ValueError("additive_module_shape_drift")
    return current.replace(added, b"", 1)


def parent_inverses(sources):
    for path in PARENTS:
        if not BASE.exact(sources[path], ARCHIVE + path):
            raise ValueError("parent_whole_preimage_drift")
        if restored_parent(path, (ROOT / path).read_bytes()) != (ROOT / (ARCHIVE + path)).read_bytes():
            raise ValueError("undeclared_original_parent_change")


def previous_audit():
    old_module, old_base = P105.ROOT, BASE.ROOT
    try:
        P105.ROOT = BASE.ROOT = PreviousReadView(ROOT)
        return P105.current()
    finally:
        P105.ROOT, BASE.ROOT = old_module, old_base


def inherited():
    checkpoint = BASE.pin(PREVIOUS)
    if checkpoint["bytes"] != 9161 or checkpoint["sha256"] != "ec0eb27ba415403d374124935215663a00e8ff534f7248745e61ba4183726a53":
        raise ValueError("previous_checkpoint_drift")
    final = BASE.pin(PREDECESSORS[1])
    if final["bytes"] != 4268 or final["sha256"] != "32e79045cf52a54da0de48cd629b041df805ee042f19e6f537ed34f15325c188":
        raise ValueError("previous_final_audit_drift")
    sources = original_sources()
    parent_inverses(sources)
    prior = previous_audit()
    raw = prior["inherited_raw_pin_entries"] + sum(prior["current_groups"].values())
    if prior["checkpoint"] != checkpoint or raw != 1644:
        raise ValueError("prior_raw_coverage_drift")
    unchanged, preimages = 0, []
    for record in sources.values():
        if BASE.exact(record):
            unchanged += 1
        elif record["path"] in PARENTS and BASE.exact(record, ARCHIVE + record["path"]):
            preimages.append({**record, "archive_path": ARCHIVE + record["path"]})
        else:
            raise ValueError("prior_source_drift")
    if unchanged != 921 or len(preimages) != 1:
        raise ValueError("prior_source_or_parent_coverage_drift")
    return {
        "state": "pass_prior_raw_and_whole_parent_inverse_NOT_full_Flow_SQL_native_or_Gate",
        "previous_checkpoint": checkpoint, "inherited_raw_pin_entries": raw,
        "previous_current_source_files": 922, "unchanged_previous_source_files": unchanged,
        "whole_parent_preimages": preimages, "parent_inverse_exact": True,
        "previous_unchanged_audit_passed_on_exact_parent_preimages": True,
        "old_executables_preserved": 239,
        "old_executables_all_reexecuted": False, "all_historical_qualification_reexecuted": False,
    }


def verify_current_manifest(data, prior):
    if data["inherited_checkpoint"] != prior["previous_checkpoint"] or data["current_source_files_count"] != 932:
        raise ValueError("checkpoint_or_source_coverage_drift")
    required = {"source_delta": set(PARENTS + NEW_SOURCES), "source_archives_added": set(ARCHIVES),
                "predecessor_receipts_added": set(PREDECESSORS), "current_executables": set(EXECUTABLES)}
    if not EXECUTABLES:
        raise ValueError("unfrozen_executable_inventory")
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
    if data["qualification"]["actual_new_table_typed_cells_source_output"] is not True:
        raise ValueError("filled_output_evidence_missing")
    if data["qualification"]["P09_gate"] != "OPEN" or (ROOT / "PLANS.md").exists():
        raise ValueError("gate_or_deleted_plan_changed")
    return counts


def current():
    prior = inherited()
    data = json.loads((ROOT / CURRENT).read_bytes())
    return {"state": "pass_scoped_inheritance_and_filled_review_table_delta_NOT_full_Flow_SQL_native_product_or_Gate",
            "checkpoint": BASE.pin(CURRENT), "inherited_raw_pin_entries": prior["inherited_raw_pin_entries"],
            "current_groups": verify_current_manifest(data, prior), "P09_gate": "OPEN", "product_complete": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(current() if args.current else inherited(), separators=(",", ":")))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"state": "fail", "error_type": type(error).__name__, "scope": "bytes_NOT_full_Flow_SQL_native_or_Gate"}))
        raise SystemExit(1) from error
