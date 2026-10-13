"""Read-only whole-byte source ancestry qualification; NOT native/full protection/execution/Gate."""
import argparse
import importlib.util
import json
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p109_bytes", Path(__file__).with_name("verify_stored_rich_comment_progress.py"))
P109 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P109)
BASE, ROOT = P109.BASE, P109.ROOT
PREVIOUS = P109.CURRENT
CURRENT = "implementation/p09/evidence/p09-110-review-ancestor-protection.source-progress.v1.json"
ARCHIVE = "implementation/p09/source-archive/p09-110-pre-review-ancestor-protection/"
PARENTS = (
    "crates/hwpx-package/src/document_import/structure/review/body_output.rs",
    "crates/hwpx-package/src/document_import/structure/review/cell_body_output.rs",
    "crates/hwpx-package/tests/review_cell_body_output.rs",
)
NEW_SOURCES = (
    "crates/hwpx-package/tests/review_cell_body_output/ancestor_protection.rs",
    "tools/p09/verify_review_ancestor_protection_progress.py",
    "tools/p09/tests/test_review_ancestor_protection_progress.py",
    "implementation/p09/P09-110_REVIEW_ANCESTOR_PROTECTION_POLICY.md",
    "implementation/p09/P09-110_REVIEW_ANCESTOR_PROTECTION_REPORT.md",
    "protocol/migrations/p09-review-ancestor-protection-v0-to-v1.md",
    "implementation/p09/evidence/p09-110-review-ancestor-protection.initial-failures.v1.json",
    "implementation/p09/evidence/p09-110-review-ancestor-protection.preservation.v1.json",
    "implementation/p09/evidence/p09-110-review-ancestor-protection.source-regression.v1.json",
)
PREDECESSORS = (PREVIOUS, "implementation/p09/evidence/p09-109-stored-rich-comment.final-audit.v1.json")
ARCHIVES = [ARCHIVE + p for p in PARENTS] + [
    "implementation/p09/source-archive/p09-110-failed-test-compilation/ancestor_protection.rs",
    "implementation/p09/source-archive/p09-110-failed-private-xml-access/ancestor_protection.rs",
    "implementation/p09/source-archive/p09-110-prefixed-regression/ancestor_protection.rs",
]
# Filled only from the ACTUAL new build and preserved failing executable, never old code reuse.
EXECUTABLES = (
    "target/p09-110-review-ancestor-protection/debug/deps/comment_operation-75493e8123c566c8.exe",
    "target/p09-110-review-ancestor-protection/debug/deps/document_import_assembly_review-312fc213dbce8bd9.exe",
    "target/p09-110-review-ancestor-protection/debug/deps/document_import_memo_catalog-093bd8d5c2597e35.exe",
    "target/p09-110-review-ancestor-protection/debug/deps/document_import_review_metadata-8537eb795457ed5e.exe",
    "target/p09-110-review-ancestor-protection/debug/deps/document_import_review-67551457d524f20f.exe",
    "target/p09-110-review-ancestor-protection/debug/deps/form_stored_provider-e02d02396d2f2bbd.exe",
    "target/p09-110-review-ancestor-protection/debug/deps/hwpx_agent_cli.exe",
    "target/p09-110-review-ancestor-protection/debug/deps/hwpx_package-a850ad738bc59b10.exe",
    "target/p09-110-review-ancestor-protection/debug/deps/id_index-b06ac4c244093f4c.exe",
    "target/p09-110-review-ancestor-protection/debug/deps/memo_style_output-f87ca3d69966fa82.exe",
    "target/p09-110-review-ancestor-protection/debug/deps/patch_element_content-4a43081747b336ae.exe",
    "target/p09-110-review-ancestor-protection/debug/deps/patch_engine-f16fef8e94eda711.exe",
    "target/p09-110-review-ancestor-protection/debug/deps/review_body_output-8759bbf6453e18f5.exe",
    "target/p09-110-review-ancestor-protection/debug/deps/review_cell_body_output-581a88b7cee111ae-before-fix.exe",
    "target/p09-110-review-ancestor-protection/debug/deps/review_cell_body_output-581a88b7cee111ae-original-validator-mismatch.exe",
    "target/p09-110-review-ancestor-protection/debug/deps/review_cell_body_output-581a88b7cee111ae.exe",
    "target/p09-110-review-ancestor-protection/debug/deps/review_delete_output-c5dd540b6b40acb8.exe",
    "target/p09-110-review-ancestor-protection/debug/deps/review_filled_table_output-c9fe0a354b64314c.exe",
    "target/p09-110-review-ancestor-protection/debug/deps/review_locations-64747444168c92b2.exe",
    "target/p09-110-review-ancestor-protection/debug/deps/review_paragraph_output-e7777a91049aeb82.exe",
    "target/p09-110-review-ancestor-protection/debug/deps/review_table_output-b0f1a70b4428ad1b.exe",
    "target/p09-110-review-ancestor-protection/debug/deps/stored_comment_provider-9065c76bcbac10b7.exe",
    "target/p09-110-review-ancestor-protection/debug/deps/text_flow-511dd1904a1b61b0.exe",
)
FALSE_QUALIFICATIONS = P109.FALSE_QUALIFICATIONS
ADDITIONS = {
    PARENTS[0]: b"        super::cell_body_output::require_no_observed_protection(xml, index, index)?;\n",
    PARENTS[1]: (
        b"    // A review boundary must not hide protection on its containing MAIN table/cell.\n"
        b"    // Keep the original selected-to-body ancestry check above, then scan body-to-root.\n"
        b"    if body != xml.root_element() {\n"
        b"        require_no_observed_protection(xml, xml.root_element(), body)?;\n"
        b"    }\n"
    ),
    PARENTS[2]: b'#[path = "review_cell_body_output/ancestor_protection.rs"]\nmod ancestor_protection;\n',
}


class PreviousReadView:
    def __init__(self, root):
        self.root = root

    def __truediv__(self, path):
        return self.root / (ARCHIVE + path if path in PARENTS else path)


def original_sources():
    sources = P109.original_sources()
    sources.update({r["path"]: r for r in json.loads((ROOT / PREVIOUS).read_bytes())["source_delta"]})
    if len(sources) != 962:
        raise ValueError("prior_source_coverage_drift")
    return sources


def restored_parent(path, current):
    if path not in PARENTS or current.count(ADDITIONS[path]) != 1:
        raise ValueError("additive_protection_guard_shape_drift")
    return current.replace(ADDITIONS[path], b"", 1)


def parent_inverses(sources):
    for path in PARENTS:
        if not BASE.exact(sources[path], ARCHIVE + path):
            raise ValueError("parent_whole_preimage_drift")
        if restored_parent(path, (ROOT / path).read_bytes()) != (ROOT / (ARCHIVE + path)).read_bytes():
            raise ValueError("undeclared_original_parent_change")


def previous_audit():
    old_module, old_base = P109.ROOT, BASE.ROOT
    try:
        P109.ROOT = BASE.ROOT = PreviousReadView(ROOT)
        return P109.current()
    finally:
        P109.ROOT, BASE.ROOT = old_module, old_base


def inherited():
    checkpoint = BASE.pin(PREVIOUS)
    if checkpoint["bytes"] != 8496 or checkpoint["sha256"] != "cb5c9a6ef664de952a91289ed44a131309551fabba8f5e1f0dccbd575cdfc41e":
        raise ValueError("previous_checkpoint_drift")
    final = BASE.pin(PREDECESSORS[1])
    if final["bytes"] != 5879 or final["sha256"] != "454e2756e9bce73fe8f611f6ee659f5b256c69ff0c904822e89f3c4bd851a729":
        raise ValueError("previous_final_audit_drift")
    sources = original_sources()
    parent_inverses(sources)
    prior = previous_audit()
    raw = prior["inherited_raw_pin_entries"] + sum(prior["current_groups"].values())
    if prior["checkpoint"] != checkpoint or raw != 1763:
        raise ValueError("prior_raw_coverage_drift")
    unchanged, preimages = 0, []
    for record in sources.values():
        if BASE.exact(record):
            unchanged += 1
        elif record["path"] in PARENTS and BASE.exact(record, ARCHIVE + record["path"]):
            preimages.append({**record, "archive_path": ARCHIVE + record["path"]})
        else:
            raise ValueError("prior_source_drift")
    if unchanged != 959 or len(preimages) != 3:
        raise ValueError("prior_source_or_parent_coverage_drift")
    return {
        "state": "pass_prior_raw_and_whole_guard_inverse_NOT_full_protection_native_or_Gate",
        "previous_checkpoint": checkpoint, "inherited_raw_pin_entries": raw,
        "previous_current_source_files": 962, "unchanged_previous_source_files": unchanged,
        "whole_parent_preimages": preimages, "parent_inverse_exact": True,
        "previous_unchanged_audit_passed_on_exact_parent_preimages": True,
        "old_executables_preserved": 283, "old_executables_all_reexecuted": False,
        "all_historical_qualification_reexecuted": False,
    }


def verify_current_manifest(data, prior):
    if data["inherited_checkpoint"] != prior["previous_checkpoint"] or data["current_source_files_count"] != 971:
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
    if data["qualification"]["observed_main_ancestor_protection_enforced"] is not True:
        raise ValueError("ancestor_guard_evidence_missing")
    if data["qualification"]["P09_gate"] != "OPEN" or (ROOT / "PLANS.md").exists():
        raise ValueError("gate_or_deleted_plan_changed")
    return counts


def current():
    prior = inherited()
    data = json.loads((ROOT / CURRENT).read_bytes())
    return {"state": "pass_actual_observed_main_ancestor_guard_NOT_full_protection_native_execution_publication_or_Gate",
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
