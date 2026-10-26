//! Actual stored candidate boundaries over the Native670-derived block source.
use super::*;
use hwpx_package::document_import::fields::bookmark_crossref::{
    SourceBookmarkCrossReferenceBindings, SourceBookmarkResolution,
};
#[path = "../../../hwpx-package/tests/support/block_bookmark679_fixture.rs"]
mod native;
#[test]
fn current_stored_block_content_candidate_keeps_source_metadata_and_head() -> Result {
    let bytes = native::derived_source()?;
    for link in [false, true] {
        let s = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
        let ctx = write_context(&s);
        let p = provider(&s, &ctx)?;
        let before = s.metadata.find(s.owner.tenant_id(), s.result)?;
        let source = p.import_actual_forms(s.head, 4)?;
        let (run, target) = native::select(source.imported())?;
        let c = source.into_bookmark_insertion_candidate(
            &p,
            Request {
                run: &run,
                target_id: &target,
                display: Display::Content,
                hyperlink: link,
            },
            limits()?,
            WriterLimits::default(),
            5,
        )?;
        let out = c.with_verified_bytes(&p, 6, |v| v.to_vec())?;
        let forms = base::forms(&out, DOC)?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let binding = SourceBookmarkCrossReferenceBindings::import(&fields, limits()?)?;
        require(
            binding.bindings().len() == 1
                && matches!(
                    binding.bindings()[0].target,
                    SourceBookmarkResolution::Bound { .. }
                ),
        )?;
        require(
            c.receipt().output.original_fields == 8
                && c.receipt().output.inserted_fields == 1
                && !c.receipt().execution_or_publication_authority,
        )?;
        require(
            s.metadata.find(s.owner.tenant_id(), s.result)? == before
                && s.revisions.head(&s.revision_context, s.project, s.branch)? == s.head,
        )?;
    }
    Ok(())
}
#[test]
fn block_candidate_still_requires_write_scope_before_preparation() -> Result {
    let bytes = native::derived_source()?;
    let s = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let p = provider(&s, &s.reader)?;
    let source = p.import_actual_forms(s.head, 4)?;
    let (run, target) = native::select(source.imported())?;
    require(matches!(
        source.into_bookmark_insertion_candidate(
            &p,
            Request {
                run: &run,
                target_id: &target,
                display: Display::Content,
                hyperlink: false
            },
            limits()?,
            WriterLimits::default(),
            5
        ),
        Err(E::Permission)
    ))
}
#[test]
fn block_candidate_does_not_bypass_current_head_on_final_output() -> Result {
    let bytes = native::derived_source()?;
    let s = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let ctx = write_context(&s);
    let p = provider(&s, &ctx)?;
    let source = p.import_actual_forms(s.head, 4)?;
    let (run, target) = native::select(source.imported())?;
    let c = source.into_bookmark_insertion_candidate(
        &p,
        Request {
            run: &run,
            target_id: &target,
            display: Display::Content,
            hyperlink: false,
        },
        limits()?,
        WriterLimits::default(),
        5,
    )?;
    advance(&s)?;
    require(c.with_verified_bytes(&p, 6, |v| v.len()).is_err())?;
    require(matches!(
        c.with_verified_bytes(&p, 7, |v| v.len()),
        Err(E::PreviouslyDenied)
    ))
}
