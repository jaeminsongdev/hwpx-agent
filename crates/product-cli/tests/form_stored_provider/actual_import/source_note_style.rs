//! Stored note-style service tests with in-memory crypto/storage/revision fixtures.
use super::*;
use super::field_ranges::fixture;
use hwpx_agent_cli::form_stored_provider::actual_import::{StoredImportedDocumentForms,
    note_style_output::StoredNoteStyleError as E};
use hwpx_package::{NoteHwpxLimitConfig, NoteHwpxLimits, WriterLimitConfig, WriterLimits,
    document_import::structure::note_style::{ImportedNoteStyle, NoteStyleError as OutputError,
        NoteStyleReplacement, NoteStyleValues, note_style_request_sha256}};
use domain_ir::{LogicalId, NoteKind, NoteNumberingRestart as Restart, NotePlacement as Placement};
use sha2::{Digest as _, Sha256};
use std::{cell::Cell, fs, path::Path, sync::atomic::AtomicUsize};
use revision_service as rev;
#[path = "../../../../hwpx-package/tests/support/document_import_note_fixture.rs"]
mod legacy_notes;

fn limits() -> Result<NoteHwpxLimits, hwpx_package::NoteHwpxError> { NoteHwpxLimits::new(NoteHwpxLimitConfig::default()) }
fn style(kind: &str, place: &str) -> String {
    format!("<hp:{kind}><hp:autoNumFormat type='DIGIT' userChar='' prefixChar='' suffixChar=')' supscript='0'/><hp:noteLine length='-1' type='SOLID' width='0.12 mm' color='#000000'/><hp:noteSpacing betweenNotes='283' belowLine='567' aboveLine='850'/><hp:numbering type='CONTINUOUS' newNum='1'/><hp:placement place='{place}' beneathText='0'/></hp:{kind}>")
}
fn synthetic() -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    fixture::package(&format!("<hp:p id='1'><hp:run><hp:secPr>{}{}</hp:secPr><hp:t>PRIVATE-MAIN</hp:t><hp:ctrl><hp:footNote instId='101'><hp:subList><hp:p id='11'><hp:run><hp:t>PRIVATE-NOTE</hp:t></hp:run></hp:p></hp:subList></hp:footNote></hp:ctrl></hp:run></hp:p>",style("footNotePr","EACH_COLUMN"),style("endNotePr","END_OF_DOCUMENT")))
}
fn selections(source: &StoredImportedDocumentForms) -> Result<Vec<ImportedNoteStyle>, OutputError> {
    source.imported().body_structure().import_note_styles(limits().expect("finite defaults"))
}
fn replacements(styles: &[ImportedNoteStyle]) -> Vec<NoteStyleValues> {
    styles.iter().map(|s| {
        let mut v=s.values().clone();v.new_number=7;v.auto_number_format.prefix_character="P&'<".into();
        v.spacing.between_notes_hwp_units=12;v.beneath_text=true;
        v.numbering_restart=Restart::PerSection;
        v.placement=if s.kind()==NoteKind::Footnote {Placement::MergedColumn}else{Placement::EndOfSection};v
    }).collect()
}
fn requests<'a>(styles: &'a [ImportedNoteStyle], values: &'a [NoteStyleValues]) -> Vec<NoteStyleReplacement<'a>> {
    styles.iter().zip(values).map(|(s,v)|NoteStyleReplacement {style_id:s.style_id(),source_style_sha256:s.source_anchor().fingerprint_sha256,values:v}).collect()
}
fn checked(path: &Path, expected: usize, sha: &str) -> Result<Vec<u8>,Box<dyn std::error::Error>> {
    for ancestor in path.ancestors() {
        let m=fs::symlink_metadata(ancestor)?;
        if m.file_type().is_symlink(){return Err("note style input link".into());}
        #[cfg(windows)] {use std::os::windows::fs::MetadataExt as _;if m.file_attributes() & 0x400 != 0 {return Err("note style input reparse".into());}}
    }
    let m=fs::symlink_metadata(path)?;
    if !m.is_file() || m.len()!=expected as u64 || expected>4*1024*1024{return Err("note style input size".into());}
    let bytes=fs::read(path)?;
    if hex::encode(Sha256::digest(&bytes))!=sha{return Err("note style input digest".into());}Ok(bytes)
}
fn generated() -> Result<Vec<Vec<u8>>,Box<dyn std::error::Error>> {
    let root=Path::new(env!("CARGO_MANIFEST_DIR")).join("../../fixtures/target-build/p09-note-id-allocation-20261019-r01/output");
    let manifest:serde_json::Value=serde_json::from_slice(&checked(&root.join("fixture-manifest.json"),9946,
        "b6a203872545155952ef925a140d156ca4b37f99372751dde0747a4aed853f48")?)?;
    assert_eq!(manifest["actual_hangul"],false);assert_eq!(manifest["green_rows"],0);
    let cases=manifest["cases"].as_array().ok_or("cases")?;assert_eq!(cases.len(),3);
    cases.iter().zip(["p09-24-c01-footnote.hwpx","p09-24-c02-endnote.hwpx","p09-24-c03-footnote-endnote.hwpx"]).map(|(case,file)| {
        if case["file"]!=file{return Err("note style fixed filename".into());}
        checked(&root.join(file),usize::try_from(case["package_bytes"].as_u64().ok_or("size")?)?,case["package_sha256"].as_str().ok_or("digest")?)
    }).collect()
}
#[test]
fn stored_note_style_three_generated_packages_use_original_authorization_and_preserve_notes() -> TestResult {
    for bytes in generated()? {
        let stored=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let provider=stored.provider()?;
        let source=provider.import_actual_forms(stored.head,4)?;let styles=selections(&source)?;assert_eq!(styles.len(),2);
        let values=replacements(&styles);let request=requests(&styles,&values);
        let candidate=source.prepare_note_style_candidate(&provider,&request,limits()?,WriterLimits::default(),5)?;
        let receipt=candidate.verify(&provider,6)?;assert_eq!(&receipt,candidate.receipt());
        assert_eq!(receipt.requested_batch_sha256,note_style_request_sha256(*ContentDigest::of(&bytes).as_bytes(),&request,limits()?)?);
        assert_eq!(receipt.output.replaced_styles,2);
        assert!(!receipt.issuer_execution_publication_authority && !receipt.output.complete_protection_qualified
            && !receipt.output.native_layout_and_numbering_qualified && !receipt.output.execution_publication_authority);
        let output=candidate.with_verified_bytes(&provider,7,<[u8]>::to_vec)?;
        let after=fixture::forms(&output,"actual-form-document")?;let next=after.body_structure().import_note_styles(limits()?)?;
        assert_eq!(next.iter().map(|s|s.values()).collect::<Vec<_>>(),values.iter().collect::<Vec<_>>());
        assert_eq!(after.notes().len(),source.notes().len());
        for (a,b) in source.notes().iter().zip(after.notes()) {
            assert_eq!(a.source_anchor.fingerprint_sha256,b.source_anchor.fingerprint_sha256);assert_eq!(a.native_attributes,b.native_attributes);assert_eq!(a.native_kind,b.native_kind);
        }
        assert!(matches!(candidate.require_current_product_route(&provider,8),Err(E::RouteUnqualified)));
        assert_eq!(source.verify(&provider,9)?,*source.receipt());
        assert_eq!(stored.revisions.head(&stored.revision_context,stored.project,stored.branch)?,stored.head);
        assert_eq!(stored.metadata.audit_events()?.iter().filter(|a|a.event=="artifact.ingested").count(),2);
        assert!(!format!("{candidate:?}").contains("PRIVATE"));
    }Ok(())
}
#[test]
fn stored_note_style_request_order_and_receipt_clones_never_replace_sealed_binding() -> TestResult {
    let bytes=synthetic()?;let stored=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let provider=stored.provider()?;
    let source=provider.import_actual_forms(stored.head,4)?;let styles=selections(&source)?;let values=replacements(&styles);
    let mut request=requests(&styles,&values);
    let first=source.prepare_note_style_candidate(&provider,&request,limits()?,WriterLimits::default(),4)?;
    request.reverse();let reversed=source.prepare_note_style_candidate(&provider,&request,limits()?,WriterLimits::default(),4)?;
    assert_ne!(first.receipt().requested_batch_sha256,reversed.receipt().requested_batch_sha256);
    assert_eq!(first.with_verified_bytes(&provider,5,<[u8]>::to_vec)?,reversed.with_verified_bytes(&provider,5,<[u8]>::to_vec)?);
    let mut forged=first.receipt().clone();forged.output.request_sha256=[0;32];forged.output.native_layout_and_numbering_qualified=true;
    assert_ne!(first.verify(&provider,6)?,forged);
    assert!(matches!(first.require_current_product_route(&provider,6),Err(E::RouteUnqualified)));
    Ok(())
}
#[test]
fn stored_note_style_acl_revocation_and_regrant_require_fresh_access_on_every_exposure() -> TestResult {
    let stored=StoredFixture::new(&synthetic()?,ArtifactKind::Result,false)?;let provider=stored.provider()?;
    let source=provider.import_actual_forms(stored.head,4)?;let styles=selections(&source)?;let values=replacements(&styles);let request=requests(&styles,&values);
    let candidate=source.prepare_note_style_candidate(&provider,&request,limits()?,WriterLimits::default(),4)?;
    let _receipt=candidate.verify(&provider,4)?;
    stored.artifacts.set_permissions(&stored.owner,stored.result,stored.reader.subject(),BTreeSet::new(),5)?;
    let called=Cell::new(false);
    assert!(matches!(candidate.with_verified_bytes(&provider,6,|_|called.set(true)),Err(E::Source(_))));assert!(!called.get());
    assert!(candidate.verify(&provider,6).is_err());assert!(candidate.require_current_product_route(&provider,6).is_err());
    assert!(matches!(source.prepare_note_style_candidate(&provider,&request,limits()?,WriterLimits::default(),6),Err(E::Source(_))));
    stored.artifacts.set_permissions(&stored.owner,stored.result,stored.reader.subject(),BTreeSet::from([artifact_service::ArtifactPermission::Read]),7)?;
    candidate.verify(&provider,8)?;assert!(matches!(candidate.require_current_product_route(&provider,8),Err(E::RouteUnqualified)));
    Ok(())
}
#[test]
fn stored_note_style_quarantine_and_aead_tamper_deny_consumer_and_repreparation() -> TestResult {
    for quarantine in [false,true] {
        let stored=StoredFixture::new(&synthetic()?,ArtifactKind::Result,false)?;let provider=stored.provider()?;
        let source=provider.import_actual_forms(stored.head,4)?;let styles=selections(&source)?;let values=replacements(&styles);let request=requests(&styles,&values);
        let candidate=source.prepare_note_style_candidate(&provider,&request,limits()?,WriterLimits::default(),4)?;
        if quarantine {stored.artifacts.quarantine(&stored.owner,stored.result,artifact_service::QuarantineReason::parse("NOTE_STYLE_TEST_QUARANTINE")?,5)?;}
        else {stored.blobs.tamper.store(true,Ordering::SeqCst);}
        let called=Cell::new(false);assert!(matches!(candidate.with_verified_bytes(&provider,6,|_|called.set(true)),Err(E::Source(_))));assert!(!called.get());
        assert!(candidate.verify(&provider,6).is_err());assert!(candidate.require_current_product_route(&provider,6).is_err());
        assert!(source.prepare_note_style_candidate(&provider,&request,limits()?,WriterLimits::default(),6).is_err());
    }Ok(())
}
#[test]
fn stored_note_style_foreign_document_branch_project_subject_and_tenant_cannot_rebind() -> TestResult {
    let stored=StoredFixture::new(&synthetic()?,ArtifactKind::Result,false)?;let provider=stored.provider()?;
    let source=provider.import_actual_forms(stored.head,4)?;let styles=selections(&source)?;let values=replacements(&styles);let request=requests(&styles,&values);
    let candidate=source.prepare_note_style_candidate(&provider,&request,limits()?,WriterLimits::default(),4)?;
    for variant in 0..5 {
        let tenant=if variant==4 {TenantId::new(uuid::Uuid::from_u128(702))?}else{stored.reader.tenant_id()};
        let subject=if variant==3 {stored.owner.subject()}else{stored.reader.subject()};
        let actor=RequestContext::new(tenant,subject,[AuthScope::DocumentRead]);let context=rev::RevisionRequestContext::new(tenant,subject);
        let project=if variant==2 {rev::ProjectId::parse("prj_70000000000000000000000000000002")?}else{stored.project};
        let branch=if variant==1 {rev::BranchId::parse("brn_70000000000000000000000000000002")?}else{stored.branch};
        let document=DocumentId::parse(if variant==0 {"other-note-style-document"}else{"actual-form-document"})?;
        let other=StoredFormProvider::bind(&stored.artifacts,&stored.revisions,&actor,&context,project,branch,document)?;
        let called=Cell::new(false);assert!(matches!(candidate.with_verified_bytes(&other,5,|_|called.set(true)),Err(E::Source(StoredActualFormImportError::Binding))));assert!(!called.get());
        assert!(candidate.verify(&other,5).is_err());assert!(candidate.require_current_product_route(&other,5).is_err());
        assert!(source.prepare_note_style_candidate(&other,&request,limits()?,WriterLimits::default(),5).is_err());
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
fn stored_note_style_prepare_verify_and_final_writer_head_boundaries_all_reject_races() -> TestResult {
    for stage in 0..3 {
        let stored=StoredFixture::new(&synthetic()?,ArtifactKind::Result,false)?;let provider=stored.provider()?;
        let source=provider.import_actual_forms(stored.head,4)?;let styles=selections(&source)?;let values=replacements(&styles);let request=requests(&styles,&values);
        let candidate=source.prepare_note_style_candidate(&provider,&request,limits()?,WriterLimits::default(),4)?;
        let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),stored.project,stored.branch,stored.head,rev::RevisionId::generate(),stored.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),stored.result,None,
            ContentDigest::of(b"note style boundary"),rev::RevisionValidationState::Verified,ContentDigest::of(b"note style validation"),ContentDigest::of(b"note style transaction"))?;
        let boundary=rev::RevisionService::new(BoundaryRepo {inner:stored.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:stored.revision_context.clone(),advance});
        let bound=StoredFormProvider::bind(&stored.artifacts,&boundary,&stored.reader,&stored.revision_context,stored.project,stored.branch,DocumentId::parse("actual-form-document")?)?;
        boundary.repository().calls.store(0,Ordering::SeqCst);
        match stage {0=>{source.prepare_note_style_candidate(&bound,&request,limits()?,WriterLimits::default(),5)?;},1=>{candidate.verify(&bound,5)?;},_=>{candidate.with_verified_bytes(&bound,5,|_|())?;}}
        let reads=boundary.repository().calls.load(Ordering::SeqCst);assert!(reads>=4);
        boundary.repository().calls.store(0,Ordering::SeqCst);boundary.repository().trigger.store(reads,Ordering::SeqCst);
        let called=Cell::new(false);
        match stage {
            0=>assert!(matches!(source.prepare_note_style_candidate(&bound,&request,limits()?,WriterLimits::default(),6),Err(E::Source(_)))),
            1=>assert!(matches!(candidate.verify(&bound,6),Err(E::Source(_)))),
            _=>assert!(matches!(candidate.with_verified_bytes(&bound,6,|_|called.set(true)),Err(E::Source(_)))),
        }
        assert!(!called.get());assert_eq!(boundary.repository().calls.load(Ordering::SeqCst),reads);
        assert_ne!(stored.revisions.head(&stored.revision_context,stored.project,stored.branch)?,stored.head);
        assert!(candidate.verify(&provider,6).is_err());assert!(candidate.require_current_product_route(&provider,6).is_err());
    }Ok(())
}
#[test]
fn stored_note_style_selection_values_protection_and_limits_remain_original_fail_closed() -> TestResult {
    let stored=StoredFixture::new(&synthetic()?,ArtifactKind::Result,false)?;let provider=stored.provider()?;
    let source=provider.import_actual_forms(stored.head,4)?;let styles=selections(&source)?;let values=replacements(&styles);let request=requests(&styles,&values);
    let a=&styles[0];let v=&values[0];let one=||NoteStyleReplacement {style_id:a.style_id(),source_style_sha256:a.source_anchor().fingerprint_sha256,values:v};
    let foreign=LogicalId::parse("foreign-style")?;
    for bad in [Vec::new(),vec![one(),one()],vec![NoteStyleReplacement {style_id:&foreign,..one()}],vec![NoteStyleReplacement {source_style_sha256:[0;32],..one()}]] {
        assert!(matches!(source.prepare_note_style_candidate(&provider,&bad,limits()?,WriterLimits::default(),4),Err(E::Output(OutputError::Selection))));
    }
    assert!(matches!(source.prepare_note_style_candidate(&provider,&[NoteStyleReplacement {values:a.values(),..one()}],limits()?,WriterLimits::default(),4),Err(E::Output(OutputError::NoChange))));
    let mut incompatible=v.clone();incompatible.placement=Placement::EndOfDocument;
    assert!(matches!(source.prepare_note_style_candidate(&provider,&[NoteStyleReplacement {values:&incompatible,..one()}],limits()?,WriterLimits::default(),4),Err(E::Output(OutputError::Value))));
    let tight=NoteHwpxLimits::new(NoteHwpxLimitConfig {notes:1,..NoteHwpxLimitConfig::default()})?;
    assert!(matches!(source.prepare_note_style_candidate(&provider,&request,tight,WriterLimits::default(),4),Err(E::Output(OutputError::Limit))));
    assert!(matches!(source.prepare_note_style_candidate(&provider,&request,limits()?,WriterLimits::new(WriterLimitConfig {max_output_bytes:1})?,4),Err(E::Output(OutputError::Writer))));
    let locked=fixture::package(&format!("<hp:p id='1'><hp:run><hp:secPr lock='1'>{}</hp:secPr></hp:run></hp:p>",style("footNotePr","EACH_COLUMN")))?;
    let protected=StoredFixture::new(&locked,ArtifactKind::Result,false)?;let access=protected.provider()?;let model=access.import_actual_forms(protected.head,4)?;
    let selected=selections(&model)?;let values=replacements(&selected);let request=requests(&selected,&values);
    assert!(matches!(model.prepare_note_style_candidate(&access,&request,limits()?,WriterLimits::default(),4),Err(E::Output(OutputError::Protection))));
    assert_eq!(stored.metadata.audit_events()?.iter().filter(|a|a.event=="artifact.ingested").count(),2);
    Ok(())
}
#[test]
fn stored_note_style_original_nine_sources_preserve_six_successes_three_id_rejections_and_native_failures() -> TestResult {
    let (mut changed,mut rejected)=(0usize,0usize);let mut lanes=[0usize;3];
    for input in legacy_notes::actual_inputs()? {
        lanes[match input.lane {"generated"=>0,"saved"=>1,"reopened"=>2,_=>return Err("note style lane".into())}]+=1;
        let stored=StoredFixture::new(&input.bytes,ArtifactKind::Result,false)?;let provider=stored.provider()?;let source=provider.import_actual_forms(stored.head,4)?;
        let styles=selections(&source)?;let values=replacements(&styles);let request=requests(&styles,&values);
        let result=source.prepare_note_style_candidate(&provider,&request,limits()?,WriterLimits::default(),4);
        if input.expected_notes==2 {assert!(matches!(result,Err(E::Output(OutputError::Patch("id_index_validation_failed")))));rejected+=1;}
        else {let candidate=result?;let output=candidate.with_verified_bytes(&provider,5,<[u8]>::to_vec)?;
            let after=fixture::forms(&output,"actual-form-document")?;assert_eq!(after.notes().len(),input.expected_notes);changed+=1;}
        assert_eq!(source.verify(&provider,6)?,*source.receipt());
        assert_eq!(stored.revisions.head(&stored.revision_context,stored.project,stored.branch)?,stored.head);
    }
    assert_eq!((changed,rejected),(6,3));assert_eq!(lanes,[3,3,3]);Ok(())
}

fn api_owned_style_selectors(value:&serde_json::Value)->Result<Vec<(LogicalId,[u8;32],NoteKind)>,Box<dyn std::error::Error>> {
    value["note_style_selections"].as_array().ok_or("API style selectors")?.iter().map(|entry|Ok((
        LogicalId::parse(entry["style_id"].as_str().ok_or("API style ID")?)?,
        serde_json::from_value(entry["source_style_sha256"].clone())?,serde_json::from_value(entry["kind"].clone())?))).collect()
}
fn explicit_api_style(kind:NoteKind)->NoteStyleValues {
    // Full caller-chosen replacement, not values/defaults inferred from source.
    NoteStyleValues {
        auto_number_format:domain_ir::NoteAutoNumberFormat {format:domain_ir::NoteNumberFormat::RomanSmall,
            user_character:String::new(),prefix_character:"PRIVATE-EXPLICIT-PREFIX".into(),suffix_character:"]".into(),superscript:true},
        note_line:domain_ir::NoteLineStyle {length_hwp_units:200,line_type:domain_ir::NoteLineType::Dot,
            width:domain_ir::NoteLineWidth::Mm0_25,color_rgb:0x123456},
        spacing:domain_ir::NoteSpacing {between_notes_hwp_units:100,below_line_hwp_units:200,above_line_hwp_units:300},
        numbering_restart:Restart::PerSection,new_number:9,
        placement:if kind==NoteKind::Footnote {Placement::RightMostColumn}else{Placement::EndOfSection},beneath_text:true,
    }
}
fn api_style_requests<'a>(selected:&'a [(LogicalId,[u8;32],NoteKind)],values:&'a [NoteStyleValues])->Vec<NoteStyleReplacement<'a>> {
    selected.iter().zip(values).map(|((id,fingerprint,_),values)|NoteStyleReplacement {style_id:id,source_style_sha256:*fingerprint,values}).collect()
}
#[test]
fn stored_note_style_v12_api_json_alone_builds_requests_and_rejects_foreign_stale_tampered_or_revoked_access() -> TestResult {
    use hwpx_agent_cli::reference_validation_product::ReferenceValidationProductOperation as Product;
    let bytes=synthetic()?;let stored=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;
    let provider=stored.provider()?;let source=provider.import_actual_forms(stored.head,4)?;
    let reference_limits=domain_ir::ReferenceAuxiliaryLimits::new(Default::default())?;
    let assess=|data:&[u8],document:&str|Product::assess_package_source(data,DocumentId::parse(document).expect("fixed document"),
        Sha256::digest(data).into(),SourceImportLimits::default(),reference_limits);
    let response:serde_json::Value=serde_json::from_slice(&assess(&bytes,"actual-form-document")?.canonical_json(reference_limits)?)?;
    assert_eq!(response["schema_version"],"hwpx-agent.product.reference-source-assessment/v13");
    let selected=api_owned_style_selectors(&response)?;assert_eq!(selected.len(),2);
    let values:Vec<_>=selected.iter().map(|(_,_,kind)|explicit_api_style(*kind)).collect();
    let request=api_style_requests(&selected,&values);
    // No caller-side Form/Note/style import: selector identity is API JSON only.
    let candidate=source.prepare_note_style_candidate(&provider,&request,limits()?,WriterLimits::default(),4)?;
    let output=candidate.with_verified_bytes(&provider,5,<[u8]>::to_vec)?;
    let after=assess(&output,"actual-form-document")?;assert_eq!(after.note_style_selections().len(),2);
    for ((id,fingerprint,kind),next) in selected.iter().zip(after.note_style_selections()) {
        assert_ne!(id,next.style_id());assert_ne!(*fingerprint,next.source_style_sha256());assert_eq!(*kind,next.kind());
    }
    assert!(after.validation_report().is_none());
    assert!(!String::from_utf8(after.canonical_json(reference_limits)?)?.contains("PRIVATE"));
    let changed=fixture::package(&format!("<hp:p id='1'><hp:run><hp:secPr>{}{}</hp:secPr><hp:t>DIFFERENT-PRIVATE-MAIN</hp:t></hp:run></hp:p>",style("footNotePr","EACH_COLUMN"),style("endNotePr","END_OF_DOCUMENT")))?;
    for report in [assess(&bytes,"foreign-style-api-document")?,assess(&changed,"actual-form-document")?] {
        let value:serde_json::Value=serde_json::from_slice(&report.canonical_json(reference_limits)?)?;
        let wrong=api_owned_style_selectors(&value)?;let request=api_style_requests(&wrong,&values);
        assert!(matches!(source.prepare_note_style_candidate(&provider,&request,limits()?,WriterLimits::default(),5),Err(E::Output(OutputError::Selection))));
    }
    let mut tampered=selected.clone();tampered[0].1[0]^=1;let wrong=api_style_requests(&tampered,&values);
    assert!(matches!(source.prepare_note_style_candidate(&provider,&wrong,limits()?,WriterLimits::default(),5),Err(E::Output(OutputError::Selection))));
    assert!(matches!(candidate.require_current_product_route(&provider,5),Err(E::RouteUnqualified)));
    assert_eq!(stored.revisions.head(&stored.revision_context,stored.project,stored.branch)?,stored.head);
    assert_eq!(stored.metadata.audit_events()?.iter().filter(|a|a.event=="artifact.ingested").count(),2);
    stored.artifacts.set_permissions(&stored.owner,stored.result,stored.reader.subject(),BTreeSet::new(),6)?;
    let called=Cell::new(false);assert!(matches!(candidate.with_verified_bytes(&provider,7,|_|called.set(true)),Err(E::Source(_))));assert!(!called.get());
    assert!(matches!(source.prepare_note_style_candidate(&provider,&request,limits()?,WriterLimits::default(),7),Err(E::Source(_))));
    Ok(())
}

#[test]
fn stored_note_style_existing_zero_number_is_preserved_but_new_zero_or_restart_reinterpretation_is_denied() -> TestResult {
    let bytes=fixture::package(&format!("<hp:p id='1'><hp:run><hp:secPr>{}</hp:secPr><hp:t>PRIVATE-ZERO-MAIN</hp:t></hp:run></hp:p>",
        style("footNotePr","EACH_COLUMN").replace("newNum='1'","newNum='0'")))?;
    let stored=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let provider=stored.provider()?;
    let source=provider.import_actual_forms(stored.head,4)?;let styles=selections(&source)?;
    let mut values=styles[0].values().clone();values.spacing.above_line_hwp_units+=1;
    let mut request=[NoteStyleReplacement {style_id:styles[0].style_id(),source_style_sha256:styles[0].source_anchor().fingerprint_sha256,values:&values}];
    let candidate=source.prepare_note_style_candidate(&provider,&request,limits()?,WriterLimits::default(),4)?;
    let output=candidate.with_verified_bytes(&provider,5,<[u8]>::to_vec)?;
    let after=fixture::forms(&output,"actual-form-document")?.body_structure().import_note_styles(limits()?)?;
    assert_eq!(after[0].values().new_number,0);assert_eq!(after[0].values().numbering_restart,styles[0].values().numbering_restart);
    let mut changed=values.clone();changed.numbering_restart=Restart::PerSection;request[0].values=&changed;
    assert!(matches!(source.prepare_note_style_candidate(&provider,&request,limits()?,WriterLimits::default(),5),Err(E::Output(OutputError::Value))));
    let positive_bytes=synthetic()?;let positive=StoredFixture::new(&positive_bytes,ArtifactKind::Result,false)?;let access=positive.provider()?;
    let model=access.import_actual_forms(positive.head,4)?;let original=selections(&model)?;
    let request=[NoteStyleReplacement {style_id:original[0].style_id(),source_style_sha256:original[0].source_anchor().fingerprint_sha256,values:&values}];
    assert!(matches!(model.prepare_note_style_candidate(&access,&request,limits()?,WriterLimits::default(),5),Err(E::Output(OutputError::Value))));
    assert!(matches!(candidate.require_current_product_route(&provider,6),Err(E::RouteUnqualified)));
    assert_eq!(stored.revisions.head(&stored.revision_context,stored.project,stored.branch)?,stored.head);Ok(())
}
