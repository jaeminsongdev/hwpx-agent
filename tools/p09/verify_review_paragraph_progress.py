"""Read-only P09-102 source preservation; no DB, native, cause or Gate acceptance."""
import argparse
import importlib.util
import json
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p101_bytes", Path(__file__).with_name("verify_source_policy_oracle_progress.py"))
P101 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P101)
BASE, ROOT = P101.BASE, P101.ROOT
PREVIOUS = P101.CURRENT
CURRENT = "implementation/p09/evidence/p09-102-review-paragraph.source-progress.v1.json"
ARCHIVE = "implementation/p09/source-archive/p09-102-pre-review-paragraph/"
PARENTS = tuple(["crates/hwpx-package/src/document_import/structure/review.rs","crates/hwpx-package/src/document_import/structure/review/body_output.rs","crates/hwpx-package/src/document_import/structure/review/cell_body_output.rs","crates/product-cli/src/form_stored_provider/actual_import/review.rs","crates/product-cli/tests/form_stored_provider/actual_import.rs","crates/product-cli/tests/form_stored_provider/actual_import/source_review_cell_output.rs"])
TRANSFORMS = {"crates/hwpx-package/src/document_import/structure/review.rs":[["pub mod cell_body_output;\npub mod delete_output;\npub mod locations;\nuse super::{\n    Mapper, StructureImportError, attributes, children, element, id, named, properties_object,\n};\n","pub mod cell_body_output;\npub mod delete_output;\npub mod locations;\npub mod paragraph_output;\nuse super::{\n    Mapper, StructureImportError, attributes, children, element, id, named, properties_object,\n};\n"]],"crates/hwpx-package/src/document_import/structure/review/body_output.rs":[["    artifact: PackageArtifact,\n    receipt: ReviewBodyOutputReceipt,\n}\nimpl fmt::Debug for ReviewBodyOutput {\n    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {\n        f.write_str(\"ReviewBodyOutput(<redacted>)\")\n","    artifact: PackageArtifact,\n    receipt: ReviewBodyOutputReceipt,\n}\n#[derive(Clone, Copy)]\npub(super) enum ReviewBodyTarget {\n    Content,\n    Paragraph,\n}\nimpl fmt::Debug for ReviewBodyOutput {\n    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {\n        f.write_str(\"ReviewBodyOutput(<redacted>)\")\n"],["        content_path: &[usize],\n        paragraphs: &[TextFlow],\n        writer_limits: WriterLimits,\n    ) -> Result<ReviewBodyOutput, ReviewBodyOutputError> {\n        self.verify_source(fresh)\n            .map_err(|_| ReviewBodyOutputError::Source)?;\n","        content_path: &[usize],\n        paragraphs: &[TextFlow],\n        writer_limits: WriterLimits,\n    ) -> Result<ReviewBodyOutput, ReviewBodyOutputError> {\n        self.lower_body_target(\n            fresh,\n            marker,\n            content_path,\n            paragraphs,\n            writer_limits,\n            ReviewBodyTarget::Content,\n        )\n    }\n\n    pub(super) fn lower_body_target(\n        &self,\n        fresh: &[u8],\n        marker: &SourceAnchorHandle,\n        content_path: &[usize],\n        paragraphs: &[TextFlow],\n        writer_limits: WriterLimits,\n        target_kind: ReviewBodyTarget,\n    ) -> Result<ReviewBodyOutput, ReviewBodyOutputError> {\n        self.verify_source(fresh)\n            .map_err(|_| ReviewBodyOutputError::Source)?;\n"],["            .element_index()\n            .ok_or(ReviewBodyOutputError::Selection)?;\n        let index = follow_content_path(xml, index, content_path)?;\n        let content = xml.elements()[index]\n            .content_span()\n            .ok_or(ReviewBodyOutputError::Selection)?;\n        if read_paragraphs(xml, index)? == paragraphs {\n            return Err(ReviewBodyOutputError::NoChange);\n        }\n        let children = lower_paragraphs(paragraphs)?;\n        let intent = PatchIntent::ReplaceElementContent {\n            target: XmlElementSelector::bind(body.part().path(), xml, index)\n                .map_err(|_| ReviewBodyOutputError::Selection)?,\n            children,\n        };\n        let limits = source\n            .limits\n","            .element_index()\n            .ok_or(ReviewBodyOutputError::Selection)?;\n        let index = follow_content_path(xml, index, content_path)?;\n        let content = target_span(xml, index, target_kind)?;\n        if read_target(xml, index, target_kind)? == paragraphs {\n            return Err(ReviewBodyOutputError::NoChange);\n        }\n        let children = lower_paragraphs(paragraphs)?;\n        let target = XmlElementSelector::bind(body.part().path(), xml, index)\n            .map_err(|_| ReviewBodyOutputError::Selection)?;\n        let intent = match target_kind {\n            ReviewBodyTarget::Content => PatchIntent::ReplaceElementContent { target, children },\n            ReviewBodyTarget::Paragraph if children.len() == 1 => PatchIntent::ReplaceSubtree {\n                target,\n                fragment: children\n                    .into_iter()\n                    .next()\n                    .ok_or(ReviewBodyOutputError::Values)?,\n            },\n            ReviewBodyTarget::Paragraph => return Err(ReviewBodyOutputError::Values),\n        };\n        let limits = source\n            .limits\n"],["            content_path,\n            original_part: xml.with_source_bytes(<[u8]>::to_vec),\n            content,\n        };\n        let output_receipt = artifact\n            .with_verified_bytes(|bytes| check.verify(bytes))\n","            content_path,\n            original_part: xml.with_source_bytes(<[u8]>::to_vec),\n            content,\n            target_kind,\n        };\n        let output_receipt = artifact\n            .with_verified_bytes(|bytes| check.verify(bytes))\n"],["    content_path: &'a [usize],\n    original_part: Vec<u8>,\n    content: crate::XmlByteSpan,\n}\nimpl BodyReadback<'_> {\n    fn verify(&self, bytes: &[u8]) -> Result<ReviewBodyImportReceipt, ReviewBodyOutputError> {\n","    content_path: &'a [usize],\n    original_part: Vec<u8>,\n    content: crate::XmlByteSpan,\n    target_kind: ReviewBodyTarget,\n}\nimpl BodyReadback<'_> {\n    fn verify(&self, bytes: &[u8]) -> Result<ReviewBodyImportReceipt, ReviewBodyOutputError> {\n"],["            .element_index()\n            .ok_or(ReviewBodyOutputError::Readback)?;\n        let output_index = follow_content_path(output_xml, output_index, self.content_path)?;\n        if read_paragraphs(output_xml, output_index)? != self.paragraphs {\n            return Err(ReviewBodyOutputError::Readback);\n        }\n        check_outside(&self.original_part, self.content, output_xml, output_index)?;\n        Ok(result.receipt.clone())\n    }\n}\n","            .element_index()\n            .ok_or(ReviewBodyOutputError::Readback)?;\n        let output_index = follow_content_path(output_xml, output_index, self.content_path)?;\n        if read_target(output_xml, output_index, self.target_kind)? != self.paragraphs {\n            return Err(ReviewBodyOutputError::Readback);\n        }\n        check_outside(\n            &self.original_part,\n            self.content,\n            output_xml,\n            output_index,\n            self.target_kind,\n        )?;\n        Ok(result.receipt.clone())\n    }\n}\n"],["    }\n    Ok(index)\n}\nfn read_paragraphs(\n    xml: &PreservingXmlDocument,\n    body: usize,\n","    }\n    Ok(index)\n}\nfn target_span(\n    xml: &PreservingXmlDocument,\n    index: usize,\n    kind: ReviewBodyTarget,\n) -> Result<crate::XmlByteSpan, ReviewBodyOutputError> {\n    match kind {\n        ReviewBodyTarget::Content => xml.elements()[index].content_span(),\n        ReviewBodyTarget::Paragraph => xml.elements()[index].outer_span(),\n    }\n    .ok_or(ReviewBodyOutputError::Selection)\n}\nfn read_target(\n    xml: &PreservingXmlDocument,\n    index: usize,\n    kind: ReviewBodyTarget,\n) -> Result<Vec<TextFlow>, ReviewBodyOutputError> {\n    match kind {\n        ReviewBodyTarget::Content => read_paragraphs(xml, index),\n        ReviewBodyTarget::Paragraph => Ok(vec![\n            TextFlowReader::read_preserving_source(xml, index, TextFlowLimits::default())\n                .map_err(|_| ReviewBodyOutputError::Readback)?,\n        ]),\n    }\n}\nfn read_paragraphs(\n    xml: &PreservingXmlDocument,\n    body: usize,\n"],["    old: crate::XmlByteSpan,\n    xml: &PreservingXmlDocument,\n    index: usize,\n) -> Result<(), ReviewBodyOutputError> {\n    let new = xml.elements()[index]\n        .content_span()\n        .ok_or(ReviewBodyOutputError::Readback)?;\n    if !xml.with_source_bytes(|bytes| {\n        original[..old.start()] == bytes[..new.start()]\n            && original[old.end()..] == bytes[new.end()..]\n","    old: crate::XmlByteSpan,\n    xml: &PreservingXmlDocument,\n    index: usize,\n    kind: ReviewBodyTarget,\n) -> Result<(), ReviewBodyOutputError> {\n    let new = target_span(xml, index, kind)?;\n    if !xml.with_source_bytes(|bytes| {\n        original[..old.start()] == bytes[..new.start()]\n            && original[old.end()..] == bytes[new.end()..]\n"]],"crates/hwpx-package/src/document_import/structure/review/cell_body_output.rs":[["        })\n    }\n}\nfn require_no_observed_protection(\n    xml: &PreservingXmlDocument,\n    body: usize,\n    mut index: usize,\n","        })\n    }\n}\npub(super) fn require_no_observed_protection(\n    xml: &PreservingXmlDocument,\n    body: usize,\n    mut index: usize,\n"],["    }\n    Ok(())\n}\nfn named(node: &crate::XmlElementToken, local: &str) -> bool {\n    node.name().namespace() == Some(\"http://www.hancom.co.kr/hwpml/2011/paragraph\")\n        && node.name().local_name() == local\n}\nfn descendant_path(\n    xml: &PreservingXmlDocument,\n    ancestor: usize,\n    mut index: usize,\n","    }\n    Ok(())\n}\npub(super) fn named(node: &crate::XmlElementToken, local: &str) -> bool {\n    node.name().namespace() == Some(\"http://www.hancom.co.kr/hwpml/2011/paragraph\")\n        && node.name().local_name() == local\n}\npub(super) fn descendant_path(\n    xml: &PreservingXmlDocument,\n    ancestor: usize,\n    mut index: usize,\n"]],"crates/product-cli/src/form_stored_provider/actual_import/review.rs":[["pub mod cell_body_output;\npub mod delete_output;\npub mod locations;\nuse super::{\n    StoredActualFormImportError, StoredActualFormImportReceipt, StoredImportedDocumentForms,\n};\n","pub mod cell_body_output;\npub mod delete_output;\npub mod locations;\npub mod paragraph_output;\nuse super::{\n    StoredActualFormImportError, StoredActualFormImportReceipt, StoredImportedDocumentForms,\n};\n"]],"crates/product-cli/tests/form_stored_provider/actual_import.rs":[["mod source_review_locations;\n#[path = \"actual_import/source_review_cell_output.rs\"]\nmod source_review_cell_output;\n\nuse super::{StoredFixture, TestResult};\nuse artifact_service::{\n","mod source_review_locations;\n#[path = \"actual_import/source_review_cell_output.rs\"]\nmod source_review_cell_output;\n#[path = \"actual_import/source_review_paragraph_output.rs\"]\nmod source_review_paragraph_output;\n\nuse super::{StoredFixture, TestResult};\nuse artifact_service::{\n"]],"crates/product-cli/tests/form_stored_provider/actual_import/source_review_cell_output.rs":[["#[path = \"../../../../hwpx-package/tests/support/review_cell_output_fixture.rs\"]\nmod fixture;\n","#[path = \"../../../../hwpx-package/tests/support/review_cell_output_fixture.rs\"]\npub(super) mod fixture;\n"]]}
NEW_SOURCES = tuple(["crates/hwpx-package/src/document_import/structure/review/paragraph_output.rs","crates/product-cli/src/form_stored_provider/actual_import/review/paragraph_output.rs","crates/hwpx-package/tests/review_paragraph_output.rs","crates/product-cli/tests/form_stored_provider/actual_import/source_review_paragraph_output.rs","crates/hwpx-package/tests/support/review_paragraph_output_fixture.rs","tools/p09/verify_review_paragraph_progress.py","tools/p09/tests/test_review_paragraph_progress.py","implementation/p09/P09-102_REVIEW_PARAGRAPH_POLICY.md","implementation/p09/P09-102_REVIEW_PARAGRAPH_REPORT.md","protocol/migrations/p09-review-paragraph-v0-to-v1.md","implementation/p09/evidence/p09-102-review-paragraph.initial-failures.v1.json","implementation/p09/evidence/p09-102-review-paragraph.preservation.v1.json","implementation/p09/evidence/p09-102-review-paragraph.source-regression.v1.json"])
PREDECESSORS = (PREVIOUS, "implementation/p09/evidence/p09-101-oracle-diagnostics.final-audit.v1.json")
EXECUTABLES = tuple(["target/p09-102-package/debug/deps/review_paragraph_output-e7777a91049aeb82.exe","target/p09-102-package/debug/deps/review_cell_body_output-581a88b7cee111ae.exe","target/p09-102-package/debug/deps/review_body_output-8759bbf6453e18f5.exe","target/p09-102-product/debug/deps/comment_operation-75493e8123c566c8.exe","target/p09-102-product/debug/deps/hwpx_agent_cli.exe","target/p09-102-product/debug/deps/form_stored_provider-e02d02396d2f2bbd.exe","target/p09-102-package-fixed/debug/deps/document_import_review_metadata-8537eb795457ed5e.exe","target/p09-102-package-fixed/debug/deps/document_import_review-67551457d524f20f.exe","target/p09-102-package-fixed/debug/deps/document_import_memo_catalog-093bd8d5c2597e35.exe","target/p09-102-package-fixed/debug/deps/document_import_assembly_review-312fc213dbce8bd9.exe","target/p09-102-package-fixed/debug/deps/id_index-b06ac4c244093f4c.exe","target/p09-102-package-fixed/debug/deps/hwpx_package-a850ad738bc59b10.exe","target/p09-102-package-fixed/debug/deps/memo_style_output-f87ca3d69966fa82.exe","target/p09-102-package-fixed/debug/deps/patch_engine-f16fef8e94eda711.exe","target/p09-102-package-fixed/debug/deps/patch_element_content-4a43081747b336ae.exe","target/p09-102-package-fixed/debug/deps/review_body_output-8759bbf6453e18f5.exe","target/p09-102-package-fixed/debug/deps/review_cell_body_output-581a88b7cee111ae.exe","target/p09-102-package-fixed/debug/deps/review_delete_output-c5dd540b6b40acb8.exe","target/p09-102-package-fixed/debug/deps/review_locations-64747444168c92b2.exe","target/p09-102-package-fixed/debug/deps/review_paragraph_output-e7777a91049aeb82.exe","target/p09-102-package-fixed/debug/deps/text_flow-511dd1904a1b61b0.exe","target/p09-102-product/debug/deps/stored_comment_provider-9065c76bcbac10b7.exe"])
REQUIRED_GROUPS = {
    "source_delta": set(PARENTS + NEW_SOURCES),
    "source_archives_added": {ARCHIVE + p for p in PARENTS} | {
        "implementation/p09/source-archive/p09-102-initial-private-test/crates/hwpx-package/tests/review_paragraph_output.rs",
        "implementation/p09/source-archive/p09-102-initial-private-test/crates/hwpx-package/tests/support/review_paragraph_output_fixture.rs",
        "implementation/p09/source-archive/p09-102-second-private-test/crates/hwpx-package/tests/support/review_paragraph_output_fixture.rs",
        "implementation/p09/source-archive/p09-102-initial-selection-test/crates/hwpx-package/tests/review_paragraph_output.rs",
        "implementation/p09/source-archive/p09-102-unintended-format/crates/hwpx-package/tests/support/document_import_field_fixture.rs",
        "implementation/p09/source-archive/p09-102-unintended-format/crates/hwpx-package/tests/support/document_import_review_assembly_fixture.rs",
        "implementation/p09/source-archive/p09-102-unintended-format/crates/hwpx-package/tests/support/review_cell_output_fixture.rs",
        "implementation/p09/source-archive/p09-102-duplicate-module-failure/crates/product-cli/tests/form_stored_provider/actual_import/source_review_paragraph_output.rs",
        "implementation/p09/source-archive/p09-102-unused-import-failure/crates/product-cli/tests/form_stored_provider/actual_import/source_review_paragraph_output.rs",
    },
    "predecessor_receipts_added": set(PREDECESSORS), "current_executables": set(EXECUTABLES),
}

class PreviousReadView:
    def __init__(self, root):
        self.root = root
    def __truediv__(self, path):
        return self.root / (ARCHIVE + path if path in PARENTS else path)

def original_sources():
    sources = P101.original_sources()
    sources.update({p["path"]: p for p in json.loads((ROOT / PREVIOUS).read_bytes())["source_delta"]})
    if len(sources) != 877:
        raise ValueError("prior_source_coverage_drift")
    return sources

def expected_parent(path, before):
    for old, new in TRANSFORMS[path]:
        old, new = old.encode(), new.encode()
        if before.count(old) != 1:
            raise ValueError("parent_transform_preimage_shape_drift")
        before = before.replace(old, new, 1)
    return before

def parent_inverses(sources):
    for path in PARENTS:
        if not BASE.exact(sources[path], ARCHIVE + path):
            raise ValueError("parent_whole_preimage_drift")
        if expected_parent(path, (ROOT / (ARCHIVE + path)).read_bytes()) != (ROOT / path).read_bytes():
            raise ValueError("undeclared_parent_change")

def previous_audit():
    old_root, old_base_root = P101.ROOT, BASE.ROOT
    try:
        P101.ROOT = BASE.ROOT = PreviousReadView(ROOT)
        return P101.current()
    finally:
        P101.ROOT, BASE.ROOT = old_root, old_base_root

def inherited():
    pin = BASE.pin(PREVIOUS)
    if pin["bytes"] != 5919 or pin["sha256"] != "b6ac74a884f51fff1479af9ae3239986f72f910bf30650fd7b2040399826aca7":
        raise ValueError("previous_checkpoint_drift")
    if BASE.pin(PREDECESSORS[1])["sha256"] != "ad8c4902521c6c6eeea72301116249377ff85f0e6bd987d59140a6f837a44c29":
        raise ValueError("previous_final_audit_drift")
    sources = original_sources()
    parent_inverses(sources)
    prior = previous_audit()
    raw = prior["inherited_raw_pin_entries"] + sum(prior["current_groups"].values())
    if prior["checkpoint"] != pin or raw != 1421:
        raise ValueError("prior_raw_coverage_drift")
    unchanged, preimages = 0, []
    for record in sources.values():
        if BASE.exact(record):
            unchanged += 1
        elif record["path"] in PARENTS and BASE.exact(record, ARCHIVE + record["path"]):
            preimages.append({**record, "archive_path": ARCHIVE + record["path"]})
        else:
            raise ValueError("prior_source_drift")
    if unchanged != 871 or len(preimages) != 6:
        raise ValueError("prior_parent_coverage_drift")
    return {"state": "pass_original_raw_prior_view_and_exact_declared_paragraph_changes_NOT_DB_native_cause_or_Gate",
            "previous_checkpoint": pin, "inherited_raw_pin_entries": raw, "previous_current_source_files": 877,
            "unchanged_previous_source_files": unchanged, "whole_parent_preimages": preimages,
            "parent_inverse_exact": True, "previous_unchanged_audit_passed_on_exact_parent_preimages": True,
            "old_executables_preserved_not_reexecuted": 136, "all_historical_qualification_reexecuted": False}

def verify_current_manifest(data, prior):
    if data["inherited_checkpoint"] != prior["previous_checkpoint"] or data["current_source_files_count"] != 890:
        raise ValueError("checkpoint_or_source_coverage_drift")
    counts = {}
    for key, expected in REQUIRED_GROUPS.items():
        records = data[key]
        if len(records) != len(expected) or {r["path"] for r in records} != expected:
            raise ValueError("current_group_coverage_drift")
        if not all(BASE.exact(r) for r in records):
            raise ValueError("current_raw_pin_drift")
        counts[key] = len(records)
    for key in ("native_executed", "actual_SQL_executed", "SQL_failure_root_cause_proven",
                "original_atomic_oracle_verified", "full_comment_product_acceptance",
                "native_author_time_state_binding", "product_complete", "P10_new_implementation",
                "execution_publication_authority", "new_table_insertion_implemented",
                "native_caret_or_visual_coordinates_verified", "full_typed_comment_compiler_route_connected"):
        if data["qualification"][key] is not False:
            raise ValueError("unsupported_acceptance_promotion")
    if data["qualification"]["P09_gate"] != "OPEN" or (ROOT / "PLANS.md").exists():
        raise ValueError("gate_or_deleted_plan_changed")
    return counts

def current():
    prior = inherited()
    data = json.loads((ROOT / CURRENT).read_bytes())
    return {"state": "pass_scoped_inheritance_and_delta_NOT_DB_native_cause_or_Gate", "checkpoint": BASE.pin(CURRENT),
            "inherited_raw_pin_entries": prior["inherited_raw_pin_entries"],
            "current_groups": verify_current_manifest(data, prior), "P09_gate": "OPEN", "product_complete": False}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(current() if args.current else inherited(), separators=(",", ":")))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"state": "fail", "error_type": type(error).__name__, "scope": "bytes_NOT_DB_native_cause_or_Gate"}))
        raise SystemExit(1) from error
