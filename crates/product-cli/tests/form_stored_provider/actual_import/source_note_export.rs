//! Actual note-file candidates are source/access bound, not CAS or Native grants.
use super::*;
use super::field_ranges::fixture;
use hwpx_agent_cli::form_stored_provider::actual_import::note_export_output::StoredNoteFileError as E;
use hwpx_package::{NoteHwpxLimitConfig,NoteHwpxLimits,WriterLimitConfig,WriterLimits,
    document_import::structure::note_export::{NoteFileSelection as Pick,NoteFileExportError as OutputError,note_file_export_request_sha256}};
use sha2::{Digest as _,Sha256};
use std::{cell::Cell,fs,io::Write as _,path::Path,sync::atomic::AtomicUsize};
use revision_service as rev;
#[path="../../../../hwpx-package/tests/support/document_import_note_fixture.rs"] mod legacy_notes;

fn limits()->NoteHwpxLimits {NoteHwpxLimits::new(Default::default()).expect("finite defaults")}
fn synthetic()->Result<Vec<u8>,Box<dyn std::error::Error>> {
    fixture::package("<hp:p id='1'><hp:run><hp:secPr><hp:startNum pageStartsOn='BOTH' page='0' pic='1' tbl='1' equation='1'/></hp:secPr><hp:t>PRIVATE-MAIN</hp:t><hp:ctrl><hp:footNote instId='101'><hp:subList><hp:p id='11'><hp:run><hp:t>COLLECTED-NOTE</hp:t></hp:run></hp:p></hp:subList></hp:footNote></hp:ctrl></hp:run></hp:p>")
}
fn checked(path:&Path,size:usize,sha:&str)->Result<Vec<u8>,Box<dyn std::error::Error>> {
    for ancestor in path.ancestors() {
        let m=fs::symlink_metadata(ancestor)?;if m.file_type().is_symlink(){return Err("note export input link".into());}
        #[cfg(windows)] {use std::os::windows::fs::MetadataExt as _;if m.file_attributes()&0x400!=0{return Err("note export input reparse".into());}}
    }
    let m=fs::symlink_metadata(path)?;if !m.is_file()||m.len()!=size as u64||size>4*1024*1024{return Err("note export input size".into());}
    let bytes=fs::read(path)?;if hex::encode(Sha256::digest(&bytes))!=sha{return Err("note export input digest".into());}Ok(bytes)
}
fn generated()->Result<Vec<Vec<u8>>,Box<dyn std::error::Error>> {
    let root=Path::new(env!("CARGO_MANIFEST_DIR")).join("../../fixtures/target-build/p09-note-id-allocation-20261019-r01/output");
    let manifest:serde_json::Value=serde_json::from_slice(&checked(&root.join("fixture-manifest.json"),9946,"b6a203872545155952ef925a140d156ca4b37f99372751dde0747a4aed853f48")?)?;
    assert_eq!(manifest["actual_hangul"],false);assert_eq!(manifest["green_rows"],0);
    let cases=manifest["cases"].as_array().ok_or("cases")?;assert_eq!(cases.len(),3);
    cases.iter().zip(["p09-24-c01-footnote.hwpx","p09-24-c02-endnote.hwpx","p09-24-c03-footnote-endnote.hwpx"]).map(|(case,file)|{
        if case["file"]!=file{return Err("fixed note filename".into());}
        checked(&root.join(file),usize::try_from(case["package_bytes"].as_u64().ok_or("size")?)?,case["package_sha256"].as_str().ok_or("sha")?)
    }).collect()
}
#[test]
fn stored_note_export_three_generated_sources_write_reopen_all_families_without_ingest_or_native_promotion()->TestResult {
    for bytes in generated()? {
        let stored=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let provider=stored.provider()?;
        let source=provider.import_actual_forms(stored.head,4)?;
        for pick in [Pick::Footnotes,Pick::Endnotes,Pick::Both] {
            let expected=source.notes().iter().filter(|n|match pick {Pick::Both=>true,Pick::Footnotes=>n.native_kind=="footNote",Pick::Endnotes=>n.native_kind=="endNote"}).count();
            let result=source.prepare_note_file_candidate(&provider,pick,limits(),WriterLimits::default(),4);
            if expected==0 {assert!(matches!(result,Err(E::Output(OutputError::NoNotes))));continue;}
            let candidate=result?;let receipt=candidate.verify(&provider,5)?;assert_eq!(receipt.output.selected_notes,expected);
            assert!(receipt.output.non_body_metadata_and_resources_may_contain_source_data);
            assert!(!receipt.output.execution_publication_authority&&!receipt.output.native_save_reopen_render_qualified&&!receipt.issuer_execution_publication_authority);
            let temp=tempfile::tempdir()?;let path=temp.path().join("notes.hwpx");
            candidate.with_verified_bytes(&provider,5,|data|->TestResult {
                let mut file=fs::OpenOptions::new().write(true).create_new(true).open(&path)?;file.write_all(data)?;file.sync_all()?;Ok(())
            })??;
            let out=fs::read(&path)?;assert!(fixture::forms(&out,"exported")?.notes().is_empty());
            assert_eq!(receipt.output.output_bytes,out.len());
            assert!(matches!(candidate.require_current_product_route(&provider,6),Err(E::RouteUnqualified)));
        }
        assert_eq!(source.verify(&provider,6)?,*source.receipt());
        assert_eq!(stored.revisions.head(&stored.revision_context,stored.project,stored.branch)?,stored.head);
        assert_eq!(stored.metadata.audit_events()?.iter().filter(|a|a.event=="artifact.ingested").count(),2);
    }Ok(())
}
#[test]
fn stored_note_export_request_binds_family_and_source_even_for_identical_collected_bytes()->TestResult {
    let bytes=synthetic()?;let stored=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let provider=stored.provider()?;
    let source=provider.import_actual_forms(stored.head,4)?;
    let a=source.prepare_note_file_candidate(&provider,Pick::Footnotes,limits(),WriterLimits::default(),4)?;
    let b=source.prepare_note_file_candidate(&provider,Pick::Both,limits(),WriterLimits::default(),4)?;
    assert_eq!(a.with_verified_bytes(&provider,5,<[u8]>::to_vec)?,b.with_verified_bytes(&provider,5,<[u8]>::to_vec)?);
    assert_ne!(a.receipt().requested_sha256,b.receipt().requested_sha256);
    let source_sha:[u8;32]=Sha256::digest(&bytes).into();
    assert_eq!(a.receipt().requested_sha256,note_file_export_request_sha256(source_sha,Pick::Footnotes));
    let mut forged=a.receipt().clone();forged.requested_sha256=[0;32];forged.issuer_execution_publication_authority=true;
    assert_ne!(a.verify(&provider,5)?,forged);
    assert!(matches!(source.prepare_note_file_candidate(&provider,Pick::Endnotes,limits(),WriterLimits::default(),4),Err(E::Output(OutputError::NoNotes))));Ok(())
}
#[test]
fn stored_note_export_acl_revoke_and_regrant_reauthorize_every_exposure()->TestResult {
    let stored=StoredFixture::new(&synthetic()?,ArtifactKind::Result,false)?;let provider=stored.provider()?;
    let source=provider.import_actual_forms(stored.head,4)?;let candidate=source.prepare_note_file_candidate(&provider,Pick::Both,limits(),WriterLimits::default(),4)?;
    let _receipt=candidate.verify(&provider,4)?;
    stored.artifacts.set_permissions(&stored.owner,stored.result,stored.reader.subject(),BTreeSet::new(),5)?;
    let called=Cell::new(false);assert!(matches!(candidate.with_verified_bytes(&provider,6,|_|called.set(true)),Err(E::Source(_))));assert!(!called.get());
    assert!(candidate.verify(&provider,6).is_err());assert!(candidate.require_current_product_route(&provider,6).is_err());
    assert!(source.prepare_note_file_candidate(&provider,Pick::Both,limits(),WriterLimits::default(),6).is_err());
    stored.artifacts.set_permissions(&stored.owner,stored.result,stored.reader.subject(),BTreeSet::from([artifact_service::ArtifactPermission::Read]),7)?;
    candidate.verify(&provider,8)?;assert!(matches!(candidate.require_current_product_route(&provider,8),Err(E::RouteUnqualified)));Ok(())
}
#[test]
fn stored_note_export_quarantine_and_aead_tamper_never_invoke_consumer()->TestResult {
    for quarantine in [false,true] {
        let stored=StoredFixture::new(&synthetic()?,ArtifactKind::Result,false)?;let provider=stored.provider()?;
        let source=provider.import_actual_forms(stored.head,4)?;let candidate=source.prepare_note_file_candidate(&provider,Pick::Both,limits(),WriterLimits::default(),4)?;
        if quarantine {stored.artifacts.quarantine(&stored.owner,stored.result,artifact_service::QuarantineReason::parse("NOTE_EXPORT_TEST_QUARANTINE")?,5)?;}
        else {stored.blobs.tamper.store(true,Ordering::SeqCst);}
        let called=Cell::new(false);assert!(matches!(candidate.with_verified_bytes(&provider,6,|_|called.set(true)),Err(E::Source(_))));assert!(!called.get());
        assert!(candidate.verify(&provider,6).is_err());assert!(candidate.require_current_product_route(&provider,6).is_err());
        assert!(source.prepare_note_file_candidate(&provider,Pick::Both,limits(),WriterLimits::default(),6).is_err());
    }Ok(())
}
#[test]
fn stored_note_export_foreign_document_branch_project_subject_tenant_cannot_rebind()->TestResult {
    let stored=StoredFixture::new(&synthetic()?,ArtifactKind::Result,false)?;let provider=stored.provider()?;
    let source=provider.import_actual_forms(stored.head,4)?;let candidate=source.prepare_note_file_candidate(&provider,Pick::Both,limits(),WriterLimits::default(),4)?;
    for variant in 0..5 {
        let tenant=if variant==4 {TenantId::new(uuid::Uuid::from_u128(702))?}else{stored.reader.tenant_id()};
        let subject=if variant==3 {stored.owner.subject()}else{stored.reader.subject()};
        let actor=RequestContext::new(tenant,subject,[AuthScope::DocumentRead]);let context=rev::RevisionRequestContext::new(tenant,subject);
        let project=if variant==2 {rev::ProjectId::parse("prj_70000000000000000000000000000002")?}else{stored.project};
        let branch=if variant==1 {rev::BranchId::parse("brn_70000000000000000000000000000002")?}else{stored.branch};
        let document=DocumentId::parse(if variant==0 {"other-note-export-document"}else{"actual-form-document"})?;
        let other=StoredFormProvider::bind(&stored.artifacts,&stored.revisions,&actor,&context,project,branch,document)?;
        let called=Cell::new(false);assert!(matches!(candidate.with_verified_bytes(&other,5,|_|called.set(true)),Err(E::Source(StoredActualFormImportError::Binding))));assert!(!called.get());
        assert!(candidate.verify(&other,5).is_err());assert!(candidate.require_current_product_route(&other,5).is_err());
        assert!(source.prepare_note_file_candidate(&other,Pick::Both,limits(),WriterLimits::default(),5).is_err());
    }Ok(())
}
struct BoundaryRepo {inner:rev::InMemoryRevisionRepository,calls:AtomicUsize,trigger:AtomicUsize,
    context:rev::RevisionRequestContext,advance:rev::RevisionCommitRequest}
impl rev::RevisionRepository for BoundaryRepo {
    fn compare_and_swap(&self,c:&rev::RevisionRequestContext,r:&rev::RevisionCommitRequest)->Result<rev::CommitOutcome,rev::RevisionError>{self.inner.compare_and_swap(c,r)}
    fn head(&self,t:TenantId,p:rev::ProjectId,b:rev::BranchId)->Result<rev::RevisionHead,rev::RevisionError>{
        let call=self.calls.fetch_add(1,Ordering::SeqCst)+1;
        if call==self.trigger.load(Ordering::SeqCst){assert!(matches!(self.inner.compare_and_swap(&self.context,&self.advance)?,rev::CommitOutcome::Committed(_)));}
        self.inner.head(t,p,b)
    }
    fn node(&self,t:TenantId,p:rev::ProjectId,r:rev::RevisionId)->Result<rev::RevisionNode,rev::RevisionError>{self.inner.node(t,p,r)}
}
#[test]
fn stored_note_export_prepare_verify_and_final_writer_head_boundaries_reject_races()->TestResult {
    for stage in 0..3 {
        let stored=StoredFixture::new(&synthetic()?,ArtifactKind::Result,false)?;let provider=stored.provider()?;
        let source=provider.import_actual_forms(stored.head,4)?;let candidate=source.prepare_note_file_candidate(&provider,Pick::Both,limits(),WriterLimits::default(),4)?;
        let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),stored.project,stored.branch,stored.head,rev::RevisionId::generate(),stored.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),stored.result,None,
            ContentDigest::of(b"note export boundary"),rev::RevisionValidationState::Verified,ContentDigest::of(b"note export validation"),ContentDigest::of(b"note export transaction"))?;
        let boundary=rev::RevisionService::new(BoundaryRepo {inner:stored.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:stored.revision_context.clone(),advance});
        let bound=StoredFormProvider::bind(&stored.artifacts,&boundary,&stored.reader,&stored.revision_context,stored.project,stored.branch,DocumentId::parse("actual-form-document")?)?;
        boundary.repository().calls.store(0,Ordering::SeqCst);
        match stage {0=>{source.prepare_note_file_candidate(&bound,Pick::Both,limits(),WriterLimits::default(),5)?;},1=>{candidate.verify(&bound,5)?;},_=>{candidate.with_verified_bytes(&bound,5,|_|())?;}}
        let reads=boundary.repository().calls.load(Ordering::SeqCst);assert!(reads>=4);
        boundary.repository().calls.store(0,Ordering::SeqCst);boundary.repository().trigger.store(reads,Ordering::SeqCst);
        let called=Cell::new(false);
        match stage {
            0=>assert!(matches!(source.prepare_note_file_candidate(&bound,Pick::Both,limits(),WriterLimits::default(),6),Err(E::Source(_)))),
            1=>assert!(matches!(candidate.verify(&bound,6),Err(E::Source(_)))),
            _=>assert!(matches!(candidate.with_verified_bytes(&bound,6,|_|called.set(true)),Err(E::Source(_)))),
        }
        assert!(!called.get());assert_eq!(boundary.repository().calls.load(Ordering::SeqCst),reads);
        assert_ne!(stored.revisions.head(&stored.revision_context,stored.project,stored.branch)?,stored.head);
        assert!(candidate.verify(&provider,6).is_err());assert!(candidate.require_current_product_route(&provider,6).is_err());
    }Ok(())
}
#[test]
fn stored_note_export_empty_selection_protection_and_finite_limits_keep_original_fail_closed()->TestResult {
    let stored=StoredFixture::new(&synthetic()?,ArtifactKind::Result,false)?;let provider=stored.provider()?;let source=provider.import_actual_forms(stored.head,4)?;
    assert!(matches!(source.prepare_note_file_candidate(&provider,Pick::Endnotes,limits(),WriterLimits::default(),4),Err(E::Output(OutputError::NoNotes))));
    let tight=NoteHwpxLimits::new(NoteHwpxLimitConfig {payload_bytes:1,..Default::default()})?;
    assert!(matches!(source.prepare_note_file_candidate(&provider,Pick::Both,tight,WriterLimits::default(),4),Err(E::Output(OutputError::Limit))));
    assert!(source.prepare_note_file_candidate(&provider,Pick::Both,limits(),WriterLimits::new(WriterLimitConfig {max_output_bytes:1})?,4).is_err());
    let locked=fixture::package("<hp:p id='1'><hp:run><hp:ctrl><hp:footNote instId='101'><hp:subList lock='1'><hp:p id='11'><hp:run><hp:t>LOCKED</hp:t></hp:run></hp:p></hp:subList></hp:footNote></hp:ctrl></hp:run></hp:p>")?;
    let protected=StoredFixture::new(&locked,ArtifactKind::Result,false)?;let access=protected.provider()?;let model=access.import_actual_forms(protected.head,4)?;
    assert!(matches!(model.prepare_note_file_candidate(&access,Pick::Both,limits(),WriterLimits::default(),4),Err(E::Output(OutputError::Protection))));
    let empty=fixture::package("<hp:p id='1'><hp:run><hp:t>NO NOTES</hp:t></hp:run></hp:p>")?;
    let store=StoredFixture::new(&empty,ArtifactKind::Result,false)?;let access=store.provider()?;let model=access.import_actual_forms(store.head,4)?;
    assert!(matches!(model.prepare_note_file_candidate(&access,Pick::Both,limits(),WriterLimits::default(),4),Err(E::Output(OutputError::NoNotes))));Ok(())
}
#[test]
fn stored_note_export_nine_original_sources_preserve_six_exports_three_id_rejections_and_native_failures()->TestResult {
    let(mut exported,mut rejected)=(0usize,0usize);let mut lanes=[0usize;3];
    for input in legacy_notes::actual_inputs()? {
        lanes[match input.lane {"generated"=>0,"saved"=>1,"reopened"=>2,_=>return Err("lane".into())}]+=1;
        let stored=StoredFixture::new(&input.bytes,ArtifactKind::Result,false)?;let provider=stored.provider()?;let source=provider.import_actual_forms(stored.head,4)?;
        let result=source.prepare_note_file_candidate(&provider,Pick::Both,limits(),WriterLimits::default(),4);
        if input.expected_notes==2 {assert!(matches!(result,Err(E::Output(OutputError::Trust("id_index_validation_failed")))));rejected+=1;}
        else {let candidate=result?;let out=candidate.with_verified_bytes(&provider,5,<[u8]>::to_vec)?;assert!(fixture::forms(&out,"exported")?.notes().is_empty());exported+=1;}
        assert_eq!(source.verify(&provider,6)?,*source.receipt());assert_eq!(stored.revisions.head(&stored.revision_context,stored.project,stored.branch)?,stored.head);
    }assert_eq!((exported,rejected),(6,3));assert_eq!(lanes,[3,3,3]);Ok(())
}
