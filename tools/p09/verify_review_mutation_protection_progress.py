"""Read-only whole-byte source ancestry qualification; NOT native/full protection/execution/Gate."""
import argparse
import importlib.util
import json
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p110_bytes", Path(__file__).with_name("verify_review_ancestor_protection_progress.py"))
P110 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P110)
BASE, ROOT = P110.BASE, P110.ROOT
PREVIOUS = P110.CURRENT
CURRENT = "implementation/p09/evidence/p09-111-review-mutation-protection.source-progress.v1.json"
ARCHIVE = "implementation/p09/source-archive/p09-111-pre-review-mutation-protection/"
PARENTS = (
    "crates/hwpx-package/src/document_import/structure/review/body_output.rs",
    "crates/hwpx-package/src/document_import/structure/review/cell_body_output.rs",
    "crates/hwpx-package/src/document_import/structure/review/delete_output.rs",
    "crates/hwpx-package/tests/review_cell_body_output.rs",
)
NEW_SOURCES = (
    "crates/hwpx-package/tests/review_cell_body_output/mutation_protection.rs",
    "tools/p09/verify_review_mutation_protection_progress.py",
    "tools/p09/tests/test_review_mutation_protection_progress.py",
    "implementation/p09/P09-111_REVIEW_MUTATION_PROTECTION_POLICY.md",
    "implementation/p09/P09-111_REVIEW_MUTATION_PROTECTION_REPORT.md",
    "protocol/migrations/p09-review-mutation-protection-v0-to-v1.md",
    "implementation/p09/evidence/p09-111-review-mutation-protection.initial-failures.v1.json",
    "implementation/p09/evidence/p09-111-review-mutation-protection.preservation.v1.json",
    "implementation/p09/evidence/p09-111-review-mutation-protection.source-regression.v1.json",
)
PREDECESSORS = (PREVIOUS, "implementation/p09/evidence/p09-110-review-ancestor-protection.final-audit.v1.json")
ARCHIVES = [ARCHIVE + p for p in PARENTS] + [
    "implementation/p09/source-archive/p09-111-prefixed-regression/mutation_protection.rs",
    "implementation/p09/source-archive/p09-111-initial-lint-and-empty-checker/crates/hwpx-package/src/document_import/structure/review/body_output.rs",
    "implementation/p09/source-archive/p09-111-initial-lint-and-empty-checker/crates/hwpx-package/src/document_import/structure/review/cell_body_output.rs",
    "implementation/p09/source-archive/p09-111-initial-lint-and-empty-checker/crates/hwpx-package/src/document_import/structure/review/delete_output.rs",
    "implementation/p09/source-archive/p09-111-initial-lint-and-empty-checker/tools/p09/verify_review_mutation_protection_progress.py",
    "implementation/p09/source-archive/p09-111-initial-lint-and-empty-checker/tools/p09/tests/test_review_mutation_protection_progress.py",
    "implementation/p09/source-archive/p09-111-initial-current-audit/tools/p09/verify_review_mutation_protection_progress.py",
    "implementation/p09/source-archive/p09-111-initial-current-audit/tools/p09/tests/test_review_mutation_protection_progress.py",
    "implementation/p09/source-archive/p09-111-initial-current-audit/implementation/p09/P09-111_REVIEW_MUTATION_PROTECTION_REPORT.md",
    "implementation/p09/source-archive/p09-111-initial-current-audit/implementation/p09/evidence/p09-111-review-mutation-protection.initial-failures.v1.json",
    "implementation/p09/source-archive/p09-111-initial-current-audit/implementation/p09/evidence/p09-111-review-mutation-protection.preservation.v1.json",
    "implementation/p09/source-archive/p09-111-initial-current-audit/implementation/p09/evidence/p09-111-review-mutation-protection.source-regression.v1.json",
    "implementation/p09/source-archive/p09-111-initial-current-audit/implementation/p09/evidence/p09-111-review-mutation-protection.source-progress.v1.json",
]
# Filled only from the ACTUAL new build and preserved failing executable, never old code reuse.
EXECUTABLES = (
    "target/p09-111-review-mutation-protection/debug/deps/comment_operation-75493e8123c566c8-pre-lint-refactor.exe",
    "target/p09-111-review-mutation-protection/debug/deps/comment_operation-75493e8123c566c8.exe",
    "target/p09-111-review-mutation-protection/debug/deps/document_import_assembly_review-312fc213dbce8bd9-pre-lint-refactor.exe",
    "target/p09-111-review-mutation-protection/debug/deps/document_import_assembly_review-312fc213dbce8bd9.exe",
    "target/p09-111-review-mutation-protection/debug/deps/document_import_memo_catalog-093bd8d5c2597e35-pre-lint-refactor.exe",
    "target/p09-111-review-mutation-protection/debug/deps/document_import_memo_catalog-093bd8d5c2597e35.exe",
    "target/p09-111-review-mutation-protection/debug/deps/document_import_review_metadata-8537eb795457ed5e-pre-lint-refactor.exe",
    "target/p09-111-review-mutation-protection/debug/deps/document_import_review_metadata-8537eb795457ed5e.exe",
    "target/p09-111-review-mutation-protection/debug/deps/document_import_review-67551457d524f20f-pre-lint-refactor.exe",
    "target/p09-111-review-mutation-protection/debug/deps/document_import_review-67551457d524f20f.exe",
    "target/p09-111-review-mutation-protection/debug/deps/form_stored_provider-e02d02396d2f2bbd-pre-lint-refactor.exe",
    "target/p09-111-review-mutation-protection/debug/deps/form_stored_provider-e02d02396d2f2bbd.exe",
    "target/p09-111-review-mutation-protection/debug/deps/hwpx_agent_cli-pre-lint-refactor.exe",
    "target/p09-111-review-mutation-protection/debug/deps/hwpx_agent_cli.exe",
    "target/p09-111-review-mutation-protection/debug/deps/hwpx_package-a850ad738bc59b10-pre-lint-refactor.exe",
    "target/p09-111-review-mutation-protection/debug/deps/hwpx_package-a850ad738bc59b10.exe",
    "target/p09-111-review-mutation-protection/debug/deps/id_index-b06ac4c244093f4c-pre-lint-refactor.exe",
    "target/p09-111-review-mutation-protection/debug/deps/id_index-b06ac4c244093f4c.exe",
    "target/p09-111-review-mutation-protection/debug/deps/memo_style_output-f87ca3d69966fa82-pre-lint-refactor.exe",
    "target/p09-111-review-mutation-protection/debug/deps/memo_style_output-f87ca3d69966fa82.exe",
    "target/p09-111-review-mutation-protection/debug/deps/patch_element_content-4a43081747b336ae-pre-lint-refactor.exe",
    "target/p09-111-review-mutation-protection/debug/deps/patch_element_content-4a43081747b336ae.exe",
    "target/p09-111-review-mutation-protection/debug/deps/patch_engine-f16fef8e94eda711-pre-lint-refactor.exe",
    "target/p09-111-review-mutation-protection/debug/deps/patch_engine-f16fef8e94eda711.exe",
    "target/p09-111-review-mutation-protection/debug/deps/review_body_output-8759bbf6453e18f5-pre-lint-refactor.exe",
    "target/p09-111-review-mutation-protection/debug/deps/review_body_output-8759bbf6453e18f5.exe",
    "target/p09-111-review-mutation-protection/debug/deps/review_cell_body_output-581a88b7cee111ae-before-fix.exe",
    "target/p09-111-review-mutation-protection/debug/deps/review_cell_body_output-581a88b7cee111ae-pre-lint-refactor.exe",
    "target/p09-111-review-mutation-protection/debug/deps/review_cell_body_output-581a88b7cee111ae.exe",
    "target/p09-111-review-mutation-protection/debug/deps/review_delete_output-c5dd540b6b40acb8-pre-lint-refactor.exe",
    "target/p09-111-review-mutation-protection/debug/deps/review_delete_output-c5dd540b6b40acb8.exe",
    "target/p09-111-review-mutation-protection/debug/deps/review_filled_table_output-c9fe0a354b64314c-pre-lint-refactor.exe",
    "target/p09-111-review-mutation-protection/debug/deps/review_filled_table_output-c9fe0a354b64314c.exe",
    "target/p09-111-review-mutation-protection/debug/deps/review_locations-64747444168c92b2-pre-lint-refactor.exe",
    "target/p09-111-review-mutation-protection/debug/deps/review_locations-64747444168c92b2.exe",
    "target/p09-111-review-mutation-protection/debug/deps/review_paragraph_output-e7777a91049aeb82-pre-lint-refactor.exe",
    "target/p09-111-review-mutation-protection/debug/deps/review_paragraph_output-e7777a91049aeb82.exe",
    "target/p09-111-review-mutation-protection/debug/deps/review_table_output-b0f1a70b4428ad1b-pre-lint-refactor.exe",
    "target/p09-111-review-mutation-protection/debug/deps/review_table_output-b0f1a70b4428ad1b.exe",
    "target/p09-111-review-mutation-protection/debug/deps/stored_comment_provider-9065c76bcbac10b7-pre-lint-refactor.exe",
    "target/p09-111-review-mutation-protection/debug/deps/stored_comment_provider-9065c76bcbac10b7.exe",
    "target/p09-111-review-mutation-protection/debug/deps/text_flow-511dd1904a1b61b0-pre-lint-refactor.exe",
    "target/p09-111-review-mutation-protection/debug/deps/text_flow-511dd1904a1b61b0.exe",
)
FALSE_QUALIFICATIONS = P110.FALSE_QUALIFICATIONS
EDITS = {
    PARENTS[0]: (("        super::cell_body_output::require_no_observed_protection(xml, index, index)?;\n", "        super::cell_body_output::require_no_observed_mutation_protection(xml, index)?;\n"),),
    PARENTS[1]: (("", "pub(super) fn require_no_observed_mutation_protection(\n    xml: &PreservingXmlDocument,\n    index: usize,\n) -> Result<(), ReviewBodyOutputError> {\n    require_no_observed_protection(xml, index, index)?;\n    // Replacing or deleting a container must not erase protected descendants.\n    // Source-derived spans only; no caller offsets or guessed protection meanings.\n    let selected = xml\n        .elements()\n        .get(index)\n        .and_then(crate::XmlElementToken::outer_span)\n        .ok_or(ReviewBodyOutputError::Selection)?;\n    for node in xml.elements() {\n        let Some(span) = node.outer_span() else {\n            return Err(ReviewBodyOutputError::Selection);\n        };\n        if span.start() < selected.start() || span.end() > selected.end() {\n            continue;\n        }\n        if named(node, \"tc\")\n            || (named(node, \"sz\")\n                && node.parent().is_some_and(|parent| named(&xml.elements()[parent], \"tbl\")))\n        {\n            reject_observed_flag(node, \"protect\")?;\n        }\n        if named(node, \"tbl\") {\n            reject_observed_flag(node, \"lock\")?;\n        }\n    }\n    Ok(())\n}\n"),),
    PARENTS[2]: (("", "        require_unprotected_targets(xml, &indices)?;\n"),("", "fn require_unprotected_targets(\n    xml: &crate::PreservingXmlDocument,\n    indices: &[usize],\n) -> Result<(), ReviewDeleteError> {\n    for &index in indices {\n        super::cell_body_output::require_no_observed_mutation_protection(xml, index)\n            .map_err(|_| ReviewDeleteError::Selection)?;\n    }\n    Ok(())\n}\n"),),
    PARENTS[3]: (("", "#[path = \"review_cell_body_output/mutation_protection.rs\"]\nmod mutation_protection;\n"),),
}


class PreviousReadView:
    def __init__(self, root):
        self.root = root

    def __truediv__(self, path):
        return self.root / (ARCHIVE + path if path in PARENTS else path)


def original_sources():
    sources = P110.original_sources()
    sources.update({r["path"]: r for r in json.loads((ROOT / PREVIOUS).read_bytes())["source_delta"]})
    if len(sources) != 971:
        raise ValueError("prior_source_coverage_drift")
    return sources


def restored_parent(path, current):
    if path not in PARENTS:
        raise ValueError("undeclared_parent")
    for original, added in EDITS[path]:
        original, added = original.encode(), added.encode()
        if current.count(added) != 1:
            raise ValueError("declared_mutation_guard_shape_drift")
        current = current.replace(added, original, 1)
    return current


def parent_inverses(sources):
    for path in PARENTS:
        if not BASE.exact(sources[path], ARCHIVE + path):
            raise ValueError("parent_whole_preimage_drift")
        if restored_parent(path, (ROOT / path).read_bytes()) != (ROOT / (ARCHIVE + path)).read_bytes():
            raise ValueError("undeclared_original_parent_change")


def previous_audit():
    old_module, old_base = P110.ROOT, BASE.ROOT
    try:
        P110.ROOT = BASE.ROOT = PreviousReadView(ROOT)
        return P110.current()
    finally:
        P110.ROOT, BASE.ROOT = old_module, old_base


def inherited():
    checkpoint = BASE.pin(PREVIOUS)
    if checkpoint["bytes"] != 13390 or checkpoint["sha256"] != "936785caee1b37965ed75cf895518004e1407e5d94beaa07b5a0cea39bdfe3d1":
        raise ValueError("previous_checkpoint_drift")
    final = BASE.pin(PREDECESSORS[1])
    if final["bytes"] != 5585 or final["sha256"] != "f5d4575db8bbb807fb664ad1f6a6a961ea6d1156ed3185c4406750a909ed3293":
        raise ValueError("previous_final_audit_drift")
    sources = original_sources()
    parent_inverses(sources)
    prior = previous_audit()
    raw = prior["inherited_raw_pin_entries"] + sum(prior["current_groups"].values())
    if prior["checkpoint"] != checkpoint or raw != 1806:
        raise ValueError("prior_raw_coverage_drift")
    unchanged, preimages = 0, []
    for record in sources.values():
        if BASE.exact(record):
            unchanged += 1
        elif record["path"] in PARENTS and BASE.exact(record, ARCHIVE + record["path"]):
            preimages.append({**record, "archive_path": ARCHIVE + record["path"]})
        else:
            raise ValueError("prior_source_drift")
    if unchanged != 967 or len(preimages) != 4:
        raise ValueError("prior_source_or_parent_coverage_drift")
    return {
        "state": "pass_prior_raw_and_whole_guard_inverse_NOT_full_protection_native_or_Gate",
        "previous_checkpoint": checkpoint, "inherited_raw_pin_entries": raw,
        "previous_current_source_files": 971, "unchanged_previous_source_files": unchanged,
        "whole_parent_preimages": preimages, "parent_inverse_exact": True,
        "previous_unchanged_audit_passed_on_exact_parent_preimages": True,
        "old_executables_preserved": 306, "old_executables_all_reexecuted": False,
        "all_historical_qualification_reexecuted": False,
    }


def verify_current_manifest(data, prior):
    if data["inherited_checkpoint"] != prior["previous_checkpoint"] or data["current_source_files_count"] != 980:
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
    if data["qualification"]["observed_review_mutation_ancestors_and_consumed_subtree_protection_enforced"] is not True:
        raise ValueError("ancestor_guard_evidence_missing")
    if data["qualification"]["P09_gate"] != "OPEN" or (ROOT / "PLANS.md").exists():
        raise ValueError("gate_or_deleted_plan_changed")
    return counts


def current():
    prior = inherited()
    data = json.loads((ROOT / CURRENT).read_bytes())
    return {"state": "pass_actual_observed_review_mutation_guard_NOT_full_protection_native_execution_publication_or_Gate",
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
