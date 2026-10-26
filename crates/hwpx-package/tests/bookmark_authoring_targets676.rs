use domain_ir::{LogicalId, ReferenceAuxiliaryLimitConfig, ReferenceAuxiliaryLimits};
use hwpx_package::cross_reference_sdk::{
    SdkCrossReferenceCandidate, SdkCrossReferenceDisplay as D, SdkCrossReferenceTarget,
};
use hwpx_package::document_import::fields::{
    ImportedDocumentFields,
    block_bookmarks::ImportedBlockBookmarks,
    bookmark_authoring_targets::{
        BookmarkAuthoringTargetError as E, SourceBookmarkAuthoringContext, SourceBookmarkFamily,
    },
};
use hwpx_package::document_import::reference_targets::sdk::SourceCrossReferenceContext;
use sha2::{Digest as _, Sha256};
use std::{error::Error, path::PathBuf};
#[path = "support/document_import_field_fixture.rs"]
#[allow(dead_code)]
mod fixture;
type Result = std::result::Result<(), Box<dyn Error>>;
fn limits() -> ReferenceAuxiliaryLimits {
    ReferenceAuxiliaryLimits::new(Default::default()).expect("finite limits")
}
fn block(id: u32, name: &str, prop: &str, text: &str) -> String {
    format!(
        "<hp:ctrl><hp:fieldBegin id='{id}' type='BOOKMARK' name='{name}' fieldid='777'><hp:parameters cnt='1' name=''><hp:integerParam name='Prop'>{prop}</hp:integerParam></hp:parameters></hp:fieldBegin></hp:ctrl><hp:t>{text}</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='{id}' fieldid='777'/></hp:ctrl>"
    )
}
fn package(body: &str) -> std::result::Result<Vec<u8>, Box<dyn Error>> {
    fixture::package(&format!("<hp:p id='1'><hp:run>{body}</hp:run></hp:p>"))
}
fn point(name: &str) -> String {
    format!("<hp:ctrl><hp:bookmark name='{name}'/></hp:ctrl>")
}

#[test]
fn actual_created_and_reopened_eight_blocks_bind_all_four_displays_and_link_options() -> Result {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join(
        "../../implementation/p09/evidence/private/p09-361-block-bookmark670-source-document001",
    );
    for (name, sha) in [
        (
            "created.hwpx",
            "aa0ae8f3042a0b3be43733deb0196488bdd1bac14e6025f7785915cca5660076",
        ),
        (
            "reopened.hwpx",
            "783ee3372fe44d8c9b6f6f6e65b5088226ea11ac920f97c76915b4c1181b6699",
        ),
    ] {
        let path = root.join(name);
        let meta = std::fs::symlink_metadata(&path)?;
        assert!(meta.is_file() && !meta.file_type().is_symlink() && meta.len() < 4194304);
        let bytes = std::fs::read(path)?;
        assert_eq!(hex::encode(Sha256::digest(&bytes)), sha);
        let forms = fixture::forms(&bytes, "native676")?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let blocks = ImportedBlockBookmarks::import(&fields, limits())?;
        let context = SourceBookmarkAuthoringContext::import(&fields, limits())?;
        assert_eq!(blocks.observations().len(), 8);
        for row in blocks.observations() {
            for display in [D::Page, D::BookmarkName, D::Content, D::RelativePosition] {
                for link in [false, true] {
                    let target = context.prepare(row.field_reference_id(), display, link)?;
                    let expected = SdkCrossReferenceCandidate::build(
                        SdkCrossReferenceTarget::Bookmark {
                            exact_source_name: row.name(),
                        },
                        display,
                        link,
                    )?;
                    assert_eq!(
                        target.command_for_preparation(),
                        expected.command_for_discovery()
                    );
                    assert_eq!(target.receipt().family, SourceBookmarkFamily::Block);
                    assert_eq!(target.receipt().target_state_sha256.len(), 64);
                    assert!(
                        target.receipt().requires_native_target_qualification
                            && !target.receipt().service_or_execution_authority
                    );
                }
            }
        }
        assert_eq!(context.verify_source(&bytes)?, *fields.receipt());
    }
    Ok(())
}
#[test]
fn point_commands_and_target_state_match_the_original_source_context() -> Result {
    let bytes = package(&(point("point") + "<hp:t>unchanged</hp:t>"))?;
    let forms = fixture::forms(&bytes, "points")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let target = &forms.body_structure().bookmarks()[0].reference_id;
    let old = SourceCrossReferenceContext::import(forms.body_structure(), limits())?;
    let current = SourceBookmarkAuthoringContext::import(&fields, limits())?;
    for display in [D::Page, D::BookmarkName, D::RelativePosition] {
        for link in [false, true] {
            let a = old.prepare(target, display, link)?;
            let b = current.prepare(target, display, link)?;
            assert_eq!(a.command_for_discovery(), b.command_for_preparation());
            assert_eq!(
                a.source_target_state_sha256(),
                b.receipt().target_state_sha256
            );
            assert_eq!(b.receipt().family, SourceBookmarkFamily::Point);
        }
    }
    Ok(())
}
#[test]
fn content_option_cannot_reclassify_a_point_target() -> Result {
    let bytes = package(&point("point"))?;
    let forms = fixture::forms(&bytes, "point-content")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let c = SourceBookmarkAuthoringContext::import(&fields, limits())?;
    for link in [false, true] {
        assert_eq!(
            c.prepare(
                &forms.body_structure().bookmarks()[0].reference_id,
                D::Content,
                link
            )
            .unwrap_err(),
            E::ContentRequiresBlockBookmark
        );
    }
    Ok(())
}
#[test]
fn object_number_rejects_for_both_source_families() -> Result {
    let bytes = package(&(point("point") + &block(1, "block", "2", "text")))?;
    let forms = fixture::forms(&bytes, "unsupported-display")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let blocks = ImportedBlockBookmarks::import(&fields, limits())?;
    let c = SourceBookmarkAuthoringContext::import(&fields, limits())?;
    for id in [
        &forms.body_structure().bookmarks()[0].reference_id,
        blocks.observations()[0].field_reference_id(),
    ] {
        assert_eq!(
            c.prepare(id, D::ObjectNumber, false).unwrap_err(),
            E::Unsupported
        );
    }
    Ok(())
}
#[test]
fn cross_family_name_collision_rejects_both_selected_ids() -> Result {
    let bytes = package(&(point("same") + &block(1, "same", "2", "text")))?;
    let forms = fixture::forms(&bytes, "mixed-duplicates")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let blocks = ImportedBlockBookmarks::import(&fields, limits())?;
    let c = SourceBookmarkAuthoringContext::import(&fields, limits())?;
    for id in [
        &forms.body_structure().bookmarks()[0].reference_id,
        blocks.observations()[0].field_reference_id(),
    ] {
        assert_eq!(c.prepare(id, D::Page, false).unwrap_err(), E::Ambiguous);
    }
    Ok(())
}
#[test]
fn repeated_block_name_is_not_resolved_by_selected_id_alone() -> Result {
    let bytes = package(&(block(1, "same", "2", "A") + &block(2, "same", "2", "B")))?;
    let forms = fixture::forms(&bytes, "duplicate-blocks")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let blocks = ImportedBlockBookmarks::import(&fields, limits())?;
    let c = SourceBookmarkAuthoringContext::import(&fields, limits())?;
    for row in blocks.observations() {
        assert_eq!(
            c.prepare(row.field_reference_id(), D::Content, false)
                .unwrap_err(),
            E::Ambiguous
        );
    }
    Ok(())
}
#[test]
fn raw_names_or_foreign_logical_ids_are_not_source_selection() -> Result {
    let bytes = package(&block(1, "name", "2", "text"))?;
    let forms = fixture::forms(&bytes, "bound-source")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let c = SourceBookmarkAuthoringContext::import(&fields, limits())?;
    assert_eq!(
        c.prepare(&LogicalId::parse("name")?, D::Content, false)
            .unwrap_err(),
        E::Missing
    );
    Ok(())
}
#[test]
fn whole_source_reconstruction_rejects_changed_bytes() -> Result {
    let bytes = package(&block(1, "name", "2", "text"))?;
    let forms = fixture::forms(&bytes, "fresh-source")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let c = SourceBookmarkAuthoringContext::import(&fields, limits())?;
    let changed = package(&block(1, "name", "2", "different"))?;
    assert_eq!(c.verify_source(&changed).unwrap_err(), E::Binding);
    Ok(())
}
#[test]
fn target_diagnostics_and_receipt_hide_name_text_and_command() -> Result {
    let bytes = package(&block(1, "PRIVATE_NAME", "2", "PRIVATE_TEXT"))?;
    let forms = fixture::forms(&bytes, "redaction")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let c = SourceBookmarkAuthoringContext::import(&fields, limits())?;
    let target = c.prepare(&fields.fields()[0].reference_id, D::Content, false)?;
    assert!(!format!("{c:?} {target:?} {:?}", target.receipt()).contains("PRIVATE_"));
    assert!(!serde_json::to_string(target.receipt())?.contains("PRIVATE_"));
    Ok(())
}
#[test]
fn finite_limits_apply_to_block_inventory_without_silent_truncation() -> Result {
    let bytes = package(&(block(1, "a", "2", "A") + &block(2, "b", "2", "B")))?;
    let forms = fixture::forms(&bytes, "limits")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let limits = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {
        items_per_kind: 1,
        ..Default::default()
    })?;
    assert_eq!(
        SourceBookmarkAuthoringContext::import(&fields, limits).unwrap_err(),
        E::Limit
    );
    Ok(())
}
#[test]
fn selected_source_text_change_changes_bound_target_state() -> Result {
    let mut states = Vec::new();
    for text in ["original", "changed"] {
        let bytes = package(&block(1, "same_name", "2", text))?;
        let forms = fixture::forms(&bytes, "state")?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let c = SourceBookmarkAuthoringContext::import(&fields, limits())?;
        states.push(
            c.prepare(&fields.fields()[0].reference_id, D::Content, false)?
                .receipt()
                .target_state_sha256
                .clone(),
        );
    }
    assert_ne!(states[0], states[1]);
    Ok(())
}
#[test]
fn unobserved_block_parameter_profile_never_defaults_to_point() -> Result {
    let bytes = package(&block(1, "name", "1", "text"))?;
    let forms = fixture::forms(&bytes, "unsupported-profile")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    assert_eq!(
        SourceBookmarkAuthoringContext::import(&fields, limits()).unwrap_err(),
        E::Unsupported
    );
    Ok(())
}
