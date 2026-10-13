"""Read-only P09-100 prior-view/delta verification; never native or product authority."""
import argparse
import importlib.util
import json
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p99_bytes", Path(__file__).with_name("verify_review_locations_progress.py"))
P99 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P99)
BASE, ROOT = P99.BASE, P99.ROOT
PREVIOUS = P99.CURRENT
CURRENT = "implementation/p09/evidence/p09-100-review-cell-body.source-progress.v1.json"
ARCHIVE = "implementation/p09/source-archive/p09-100-pre-review-cell-body/"
PARENTS = tuple(["crates/hwpx-package/src/document_import/structure/review.rs","crates/hwpx-package/src/document_import/structure/review/body_output.rs","crates/product-cli/src/form_stored_provider/actual_import/review.rs","crates/product-cli/tests/form_stored_provider/actual_import.rs","crates/product-cli/tests/form_stored_provider/actual_import/source_review_assembly.rs"])
NEW_SOURCES = tuple(["crates/hwpx-package/src/document_import/structure/review/cell_body_output.rs","crates/product-cli/src/form_stored_provider/actual_import/review/cell_body_output.rs","crates/hwpx-package/tests/review_cell_body_output.rs","crates/product-cli/tests/form_stored_provider/actual_import/source_review_cell_output.rs","crates/hwpx-package/tests/support/review_cell_output_fixture.rs","tools/p09/verify_review_cell_body_progress.py","tools/p09/tests/test_review_cell_body_progress.py","implementation/p09/P09-100_REVIEW_CELL_BODY_POLICY.md","implementation/p09/P09-100_REVIEW_CELL_BODY_REPORT.md","protocol/migrations/p09-review-cell-body-v0-to-v1.md","implementation/p09/evidence/p09-100-review-cell-body.initial-failures.v1.json","implementation/p09/evidence/p09-100-review-cell-body.preservation.v1.json","implementation/p09/evidence/p09-100-review-cell-body.source-regression.v1.json"])
BODY_TRANSFORMS = [["    ) -> Result<ReviewBodyOutput, ReviewBodyOutputError> {\n        self.verify_source(fresh)","    ) -> Result<ReviewBodyOutput, ReviewBodyOutputError> {\n        self.lower_body_content(fresh, marker, &[], paragraphs, writer_limits)\n    }\n\n    // Only actual source-derived descendant paths reach this shared pipeline.\n    // Empty path preserves the original whole-body public API exactly.\n    pub(super) fn lower_body_content(\n        &self,\n        fresh: &[u8],\n        marker: &SourceAnchorHandle,\n        content_path: &[usize],\n        paragraphs: &[TextFlow],\n        writer_limits: WriterLimits,\n    ) -> Result<ReviewBodyOutput, ReviewBodyOutputError> {\n        self.verify_source(fresh)"],["        let content = body\n            .element()\n            .and_then(crate::XmlElementToken::content_span)","        let index = follow_content_path(xml, index, content_path)?;\n        let content = xml.elements()[index]\n            .content_span()"],["            paragraphs,\n            original_part:","            paragraphs,\n            content_path,\n            original_part:"],["    paragraphs: &'a [TextFlow],\n    original_part:","    paragraphs: &'a [TextFlow],\n    content_path: &'a [usize],\n    original_part:"],["        if read_paragraphs(output_xml, output_index)? != self.paragraphs {","        let output_index = follow_content_path(output_xml, output_index, self.content_path)?;\n        if read_paragraphs(output_xml, output_index)? != self.paragraphs {"],["fn read_paragraphs(","fn follow_content_path(\n    xml: &PreservingXmlDocument,\n    mut index: usize,\n    path: &[usize],\n) -> Result<usize, ReviewBodyOutputError> {\n    for &ordinal in path {\n        let mut child = xml.elements()[index].first_child();\n        for _ in 0..ordinal {\n            child = child.and_then(|i| xml.elements()[i].next_sibling());\n        }\n        index = child.ok_or(ReviewBodyOutputError::Selection)?;\n    }\n    Ok(index)\n}\nfn read_paragraphs("]]
PREDECESSORS = (PREVIOUS, "implementation/p09/evidence/p09-99-review-locations.final-audit.v1.json")
EXECUTABLES = tuple(p.replace("target/p09-99-package/", "target/p09-100-package/").replace("target/p09-99-regression/", "target/p09-100-product/") for p in P99.EXECUTABLES) + (
    "target/p09-100-package/debug/deps/review_cell_body_output-581a88b7cee111ae.exe",
)
FAILURES = {
    "implementation/p09/source-archive/p09-100-initial-failure/" + p for p in (
        PARENTS[1], NEW_SOURCES[0], NEW_SOURCES[2], NEW_SOURCES[4],
    )
} | {
    "implementation/p09/source-archive/p09-100-initial-failure/review_cell_body_output-581a88b7cee111ae.exe",
    "implementation/p09/source-archive/p09-100-test-id-compile-failure/" + NEW_SOURCES[2],
    "implementation/p09/source-archive/p09-100-initial-clippy-failure/" + NEW_SOURCES[4],
    "implementation/p09/source-archive/p09-100-clippy-retry-failure/" + NEW_SOURCES[4],
    "implementation/p09/source-archive/p09-100-expect-clippy-failure/" + NEW_SOURCES[4],
}
REQUIRED_GROUPS = {
    "source_delta": set(PARENTS + NEW_SOURCES),
    "source_archives_added": {ARCHIVE + p for p in PARENTS} | FAILURES,
    "predecessor_receipts_added": set(PREDECESSORS),
    "current_executables": set(EXECUTABLES),
}

class PreviousReadView:
    """Only declared parent reads use whole preimages; no writes or disk replacement."""
    def __init__(self, root):
        self.root = root
    def __truediv__(self, path):
        return self.root / (ARCHIVE + path if path in PARENTS else path)

def original_sources():
    sources = {p["path"]: p for p in json.loads((ROOT / P99.P98.P96.PREVIOUS).read_bytes())["source_files"]}
    for checkpoint in (P99.P98.P96.CURRENT, P99.P98.P97.CURRENT, P99.P98.CURRENT, PREVIOUS):
        sources.update({p["path"]: p for p in json.loads((ROOT / checkpoint).read_bytes())["source_delta"]})
    if len(sources) != 852:
        raise ValueError("prior_source_coverage_drift")
    return sources

def expected_parent(path, before):
    if path == PARENTS[1]:
        for old, new in BODY_TRANSFORMS:
            old, new = old.encode(), new.encode()
            if before.count(old) != 1:
                raise ValueError("shared_pipeline_preimage_shape_drift")
            before = before.replace(old, new, 1)
        return before
    if path == PARENTS[4]:
        if before.count(b"mod fixture;\n") != 1:
            raise ValueError("original_fixture_declaration_drift")
        return before.replace(b"mod fixture;\n", b"pub(super) mod fixture;\n", 1)
    if path == PARENTS[3]:
        declaration = b'#[path = "actual_import/source_review_cell_output.rs"]\nmod source_review_cell_output;\n'
        return before.replace(b"mod source_review_locations;\n", b"mod source_review_locations;\n" + declaration, 1)
    return before.replace(b"pub mod body_output;\n", b"pub mod body_output;\npub mod cell_body_output;\n", 1)

def parent_inverses(sources):
    for path in PARENTS:
        if not BASE.exact(sources[path], ARCHIVE + path):
            raise ValueError("parent_whole_preimage_drift")
        if expected_parent(path, (ROOT / (ARCHIVE + path)).read_bytes()) != (ROOT / path).read_bytes():
            raise ValueError("undeclared_parent_change")

def previous_audit():
    old_root, old_base_root = P99.ROOT, BASE.ROOT
    try:
        P99.ROOT = BASE.ROOT = PreviousReadView(ROOT)
        return P99.current()
    finally:
        P99.ROOT, BASE.ROOT = old_root, old_base_root

def inherited():
    pin = BASE.pin(PREVIOUS)
    if pin["bytes"] != 9191 or pin["sha256"] != "ccda008d1b2a4605af2a5933e2417281ecd5b61143e34888aca1e4ab95e4fcf9":
        raise ValueError("previous_checkpoint_drift")
    if BASE.pin(PREDECESSORS[1])["sha256"] != "9d816ee0e411e4351c354f0be0d588c094fbf8ce72c250d794816389c4900d10":
        raise ValueError("previous_final_audit_drift")
    sources = original_sources()
    parent_inverses(sources)
    prior = previous_audit()
    raw = prior["inherited_raw_pin_entries"] + sum(prior["current_groups"].values())
    if prior["checkpoint"] != pin or raw != 1347:
        raise ValueError("prior_raw_coverage_drift")
    unchanged, preimages = 0, []
    for record in sources.values():
        if BASE.exact(record):
            unchanged += 1
        elif record["path"] in PARENTS and BASE.exact(record, ARCHIVE + record["path"]):
            preimages.append({**record, "archive_path": ARCHIVE + record["path"]})
        else:
            raise ValueError("prior_source_drift")
    if unchanged != 847 or len(preimages) != 5:
        raise ValueError("prior_parent_coverage_drift")
    return {"state": "pass_original_raw_prior_view_and_exact_declared_parent_transform_NOT_native_or_Gate",
            "previous_checkpoint": pin, "inherited_raw_pin_entries": raw,
            "previous_current_source_files": 852, "unchanged_previous_source_files": unchanged,
            "whole_parent_preimages": preimages, "declared_shared_pipeline_transform_exact": True,
            "previous_unchanged_audit_passed_on_exact_parent_preimages": True,
            "old_executables_preserved_not_reexecuted": 116,
            "all_historical_qualification_reexecuted": False}

def verify_current_manifest(data, prior):
    if data["inherited_checkpoint"] != prior["previous_checkpoint"] or data["current_source_files_count"] != 865:
        raise ValueError("checkpoint_or_source_coverage_drift")
    counts = {}
    for key, expected in REQUIRED_GROUPS.items():
        records = data[key]
        if len(records) != len(expected) or {r["path"] for r in records} != expected:
            raise ValueError("current_group_coverage_drift")
        if not all(BASE.exact(r) for r in records):
            raise ValueError("current_raw_pin_drift")
        counts[key] = len(records)
    for key in ("native_executed", "actual_SQL_executed", "full_comment_product_acceptance",
                "native_author_time_state_binding", "product_complete", "P10_new_implementation",
                "execution_publication_authority", "full_typed_comment_compiler_route_connected",
                "new_table_insertion_implemented"):
        if data["qualification"][key] is not False:
            raise ValueError("unsupported_acceptance_promotion")
    if data["qualification"]["P09_gate"] != "OPEN" or (ROOT / "PLANS.md").exists():
        raise ValueError("gate_or_deleted_plan_changed")
    return counts

def current():
    prior = inherited()
    data = json.loads((ROOT / CURRENT).read_bytes())
    return {"state": "pass_scoped_inheritance_and_delta_NOT_native_or_Gate", "checkpoint": BASE.pin(CURRENT),
            "inherited_raw_pin_entries": prior["inherited_raw_pin_entries"],
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
