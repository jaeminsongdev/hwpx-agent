//! Actual stored candidate boundaries over the Native670-derived block source.
use super::*;
use hwpx_package::document_import::fields::bookmark_crossref::{
    SourceBookmarkCrossReferenceBindings, SourceBookmarkResolution,
};
#[path = "../../../hwpx-package/tests/support/block_bookmark679_fixture.rs"]
mod native;
/// Fixed private files only, with current stored-candidate checks for each case.
/// No Native, revision, result ingestion, scanner issuer or publication authority.
pub(super) fn fixed_block_output_batch681()->Result<Value>{
    let root=Path::new(env!("CARGO_MANIFEST_DIR")).join("../..");
    let relative="implementation/p09/evidence/private/p09-361-block-bookmark681-prepared001";
    let directory=root.join(relative);
    regular_ancestors(directory.parent().ok_or("parent")?)?;
    require(!directory.exists())?;std::fs::create_dir(&directory)?;regular_ancestors(&directory)?;
    let bytes=native::derived_source()?;
    let source_path=directory.join("source.hwpx");
    let mut file=OpenOptions::new().write(true).create_new(true).open(&source_path)?;
    file.write_all(&bytes)?;file.sync_all()?;drop(file);
    let source=json!({"path":format!("{relative}/source.hwpx"),"bytes":bytes.len(),"sha256":hex::encode(Sha256::digest(&bytes))});
    let mut rows=Vec::new();
    for(i,(label,display))in[("page",Display::Page),("bookmark_name",Display::BookmarkName),
        ("content",Display::Content),("relative_position",Display::RelativePosition)].into_iter().enumerate(){
        for hyperlink in[false,true]{
            let case_index=i*2+usize::from(hyperlink)+1;
            let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let ctx=write_context(&s);let p=provider(&s,&ctx)?;
            let metadata=s.metadata.find(s.owner.tenant_id(),s.result)?;
            let imported=p.import_actual_forms(s.head,4)?;let(run,target)=native::select(imported.imported(),&bytes)?;
            let candidate=imported.into_bookmark_insertion_candidate(&p,Request{run:&run,target_id:&target,display,hyperlink},limits()?,WriterLimits::default(),5)?;
            let receipt=&candidate.receipt().output;
            require(receipt.original_fields==8&&receipt.inserted_fields==1&&receipt.outside_insertions_exact
                &&receipt.original_selected_run_exact&&receipt.existing_display_text_is_not_evaluated_or_refreshed
                &&!receipt.native_currentness_execution_or_publication_qualified&&!candidate.receipt().execution_or_publication_authority)?;
            let filename=format!("case-{case_index:02}.hwpx");let path=directory.join(&filename);
            let pin=candidate.with_verified_bytes(&p,6,|output|->Result<Value>{
                require(!output.is_empty()&&output.len()<=4194304)?;
                let mut file=OpenOptions::new().write(true).create_new(true).open(&path)?;
                file.write_all(output)?;file.sync_all()?;
                Ok(json!({"path":format!("{relative}/{filename}"),"bytes":output.len(),"sha256":hex::encode(Sha256::digest(output))}))
            })??;
            require(s.metadata.find(s.owner.tenant_id(),s.result)?==metadata
                &&s.revisions.head(&s.revision_context,s.project,s.branch)?==s.head)?;
            rows.push(json!({"case_index":case_index,"display":label,"hyperlink":hyperlink,
                "output":pin,"output_receipt":receipt,"stored_metadata_and_head_unchanged":true}));
        }
    }
    require(rows.len()==8&&std::fs::read_dir(&directory)?.count()==9&&std::fs::read(&source_path)?==bytes)?;
    Ok(json!({"state":"block_bookmark681_eight_stored_candidate_private_copies_not_Native_or_revision",
        "source":source,"cases":rows,"actual_native_started":false,"source_overwritten":false,
        "head_changed":false,"result_ingested":false,"product_execution_or_publication_qualified":false,
        "initial_display_is_evaluated_or_refreshed":false,"memory_repository_scanner_and_commits_are_fixtures":true,"P09_complete":false}))
}
#[test]
fn current_stored_block_content_candidate_keeps_source_metadata_and_head() -> Result {
    let bytes = native::derived_source()?;
    for link in [false, true] {
        let s = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
        let ctx = write_context(&s);
        let p = provider(&s, &ctx)?;
        let before = s.metadata.find(s.owner.tenant_id(), s.result)?;
        let source = p.import_actual_forms(s.head, 4)?;
        let (run, target) = native::select(source.imported(),&bytes)?;
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
    let (run, target) = native::select(source.imported(),&bytes)?;
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
    let (run, target) = native::select(source.imported(),&bytes)?;
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
