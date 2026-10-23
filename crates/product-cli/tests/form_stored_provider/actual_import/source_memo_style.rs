use super::source_memo_catalog::fixture;
use super::*;
use domain_ir::{CommentLineType, CommentLineWidth, CommentMemoType};
use hwpx_package::{
    WriterLimits,
    document_import::fields::semantics::catalog::{
        ImportedCatalogKind,
        memo_style::{MemoStyleColor, MemoStyleValues},
    },
};
fn values() -> MemoStyleValues {
    MemoStyleValues {
        width_native_units: 77,
        line_width: CommentLineWidth::Mm0_3,
        line_type: CommentLineType::Wave,
        line_color: MemoStyleColor::Rgb(0x00AA_BBCC),
        fill_color: MemoStyleColor::None,
        active_color: MemoStyleColor::Rgb(0x0011_2233),
        memo_type: CommentMemoType::UserUpdate,
    }
}
#[test]
fn original_authenticated_catalog_lowers_actual_style_bytes_without_publishing_or_metadata_defaults()
-> TestResult {
    let bytes = fixture::package(&fixture::table(&fixture::style(12), 1), Some("12"))?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let fields = source.import_field_ranges(&provider, 5)?;
    let meanings = fields.import_semantics(&provider, 6)?;
    let catalog = meanings.import_catalog(&provider, 7)?;
    let selector = catalog
        .definitions()
        .iter()
        .find(|d| d.kind == ImportedCatalogKind::MemoProperty)
        .ok_or("memo style")?
        .source_anchor
        .clone();
    let prepared =
        catalog.prepare_memo_style(&provider, selector, values(), WriterLimits::default(), 8)?;
    assert_eq!(prepared.verify(&provider, 9)?, *prepared.receipt());
    let result = prepared.with_verified_bytes(&provider, 10, <[u8]>::to_vec)?;
    assert_ne!(result, bytes);
    assert!(!prepared.receipt().native_author_time_state_binding_verified);
    assert!(!prepared.receipt().execution_publication_authority);
    assert!(
        prepared
            .require_current_product_route(&provider, 11)
            .is_err()
    );
    assert_eq!(
        stored
            .revisions
            .head(&stored.revision_context, stored.project, stored.branch)?,
        stored.head
    );
    assert_eq!(
        stored
            .metadata
            .audit_events()?
            .iter()
            .filter(|e| e.event == "artifact.ingested")
            .count(),
        2
    );
    assert!(!format!("{prepared:?} {:?}", prepared.receipt()).contains("PRIVATE-MEMO"));
    Ok(())
}
#[test]
fn cached_output_callback_rechecks_original_aead_acl_and_head_before_exposing_any_bytes()
-> TestResult {
    let bytes = fixture::package(&fixture::table(&fixture::style(12), 1), Some("12"))?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let fields = source.import_field_ranges(&provider, 5)?;
    let meanings = fields.import_semantics(&provider, 6)?;
    let catalog = meanings.import_catalog(&provider, 7)?;
    let selector = catalog
        .definitions()
        .iter()
        .find(|d| d.kind == ImportedCatalogKind::MemoProperty)
        .ok_or("style")?
        .source_anchor
        .clone();
    let prepared =
        catalog.prepare_memo_style(&provider, selector, values(), WriterLimits::default(), 8)?;
    let mut called = false;
    stored.blobs.tamper.store(true, Ordering::SeqCst);
    assert!(
        prepared
            .with_verified_bytes(&provider, 9, |_| called = true)
            .is_err()
    );
    assert!(!called);
    stored.blobs.tamper.store(false, Ordering::SeqCst);
    stored.artifacts.set_permissions(
        &stored.owner,
        stored.result,
        stored.reader.subject(),
        BTreeSet::new(),
        10,
    )?;
    assert!(
        prepared
            .with_verified_bytes(&provider, 11, |_| called = true)
            .is_err()
    );
    assert!(!called);
    stored.artifacts.set_permissions(
        &stored.owner,
        stored.result,
        stored.reader.subject(),
        BTreeSet::from([artifact_service::ArtifactPermission::Read]),
        12,
    )?;
    assert_eq!(prepared.verify(&provider, 13)?, *prepared.receipt());
    stored.advance()?;
    assert!(
        prepared
            .with_verified_bytes(&provider, 14, |_| called = true)
            .is_err()
    );
    assert!(!called);
    Ok(())
}
