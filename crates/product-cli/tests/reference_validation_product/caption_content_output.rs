mod sequence_output_binding {include!("caption_sequence_output.rs");}
mod topology_output_binding {include!("caption_topology_output.rs");}
mod program_output_binding {include!("caption_program_output.rs");}
mod structure_output_binding {include!("caption_structure_output.rs");}
use super::*;
use hwpx_agent_cli::form_stored_provider::actual_import::caption_content_output::StoredCaptionContentError as ContentError;
use hwpx_package::document_import::{reference_targets::{caption_source_state::ImportedCaptionSourceState,
    caption_frames::{CaptionSourceFrame,CaptionStyleFamily as Family,CaptionStyleReferenceStatus as StyleStatus},
    numbering::CaptionNumberingImportError as StateError},structure::caption_style_batch::CaptionStyleReplacement as Style};
use std::{collections::BTreeMap,io::{Cursor,Read,Write},sync::atomic::AtomicUsize};
const HEADER:&str="<hh:head xmlns:hh='http://www.hancom.co.kr/hwpml/2011/head'><hh:beginNum page='0' footnote='1' endnote='1' pic='0' tbl='0' equation='0'/><hh:refList><hh:charProperties><hh:charPr id='4'/><hh:charPr id='5'/></hh:charProperties><hh:paraProperties><hh:paraPr id='6'/><hh:paraPr id='7'/></hh:paraProperties><hh:styles><hh:style id='8'/><hh:style id='9'/></hh:styles></hh:refList></hh:head>";
fn content_body(locked:bool)->String {
    (0..3).map(|i|{
        let text=caption("BOTTOM").replace("id='1'",&format!("id='{}'",1+i)).replace("id='7'",&format!("id='{}'",7+i)).replace("id='99'",&format!("id='{}'",99+i));
        let text=if i<2{text.replace(&format!("<hp:p id='{}'><hp:run>",99+i),&format!("<hp:p id='{}' paraPrIDRef='6' styleIDRef='8'><hp:run charPrIDRef='4'>",99+i))}else{text};
        let text=text.replace("</hp:t>","</hp:t><hp:ctrl><hp:autoNum num='19' numType='PICTURE'><hp:autoNumFormat type='DIGIT' userChar='' prefixChar='' suffixChar='' supscript='0'/></hp:autoNum></hp:ctrl>");
        if locked&&i==2{text.replace("<hp:rect id='9'>","<hp:rect id='9' lock='1'>")}else{text}
    }).collect()
}
fn package_parts(bytes:&[u8])->Result<BTreeMap<String,Vec<u8>>,Box<dyn Error>> {
    let mut input=zip::ZipArchive::new(Cursor::new(bytes))?;let mut parts=BTreeMap::new();
    for i in 0..input.len(){let mut part=input.by_index(i)?;let mut data=Vec::new();part.read_to_end(&mut data)?;parts.insert(part.name().to_owned(),data);}Ok(parts)
}
fn content_rig(locked:bool)->Result<Rig,Box<dyn Error>> {
    let mut rig=Rig::new()?;let input=fixture::package(&content_body(locked))?;let mut source=zip::ZipArchive::new(Cursor::new(input))?;
    let mut output=zip::ZipWriter::new(Cursor::new(Vec::new()));
    for i in 0..source.len(){let mut entry=source.by_index(i)?;let name=entry.name().to_owned();let mut data=Vec::new();entry.read_to_end(&mut data)?;
        output.start_file(&name,zip::write::SimpleFileOptions::default().compression_method(zip::CompressionMethod::Stored))?;
        output.write_all(if name=="Contents/header.xml"{HEADER.as_bytes()}else{&data})?;}
    let bytes=output.finish()?.into_inner();
    // Synthetic setup only. No production candidate path ingests or commits.
    let result=rig.store.ingest(&rig.owner,IngestRequest {bytes:bytes.clone(),media_type:MediaType::parse("application/vnd.hancom.hwpx+zip")?,file_name:FileName::parse("private-caption.hwpx")?,kind:ArtifactKind::Result},3)?;
    rig.store.set_permissions(&rig.owner,result.artifact_id,rig.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),3)?;
    let request=rev::RevisionCommitRequest::new(rev::CommitId::generate(),rig.project,rig.branch,rig.head,rev::RevisionId::generate(),rig.head.revision_id().into_iter().collect(),rig.result,result.artifact_id,None,
        ContentDigest::of(b"caption content fixture setup"),rev::RevisionValidationState::Verified,ContentDigest::of(b"caption content fixture validation"),ContentDigest::of(b"caption content fixture transaction"))?;
    assert!(matches!(rig.revisions.commit(&rig.revision_context,&request)?,rev::CommitOutcome::Committed(_)));
    rig.result=result.artifact_id;rig.head=rig.revisions.head(&rig.revision_context,rig.project,rig.branch)?;rig.bytes=bytes;Ok(rig)
}
fn style_requests(frames:&[CaptionSourceFrame])->Vec<Style<'_>> {
    frames.iter().enumerate().flat_map(|(i,f)|{
        let ids=if i==1{[4,6,8]}else{[5,7,9]};
        [Style {caption_id:&f.logical_caption_id,source_node_id:&f.runs[0].logical_run_id,family:Family::Character,declaration_id:ids[0]},
         Style {caption_id:&f.logical_caption_id,source_node_id:&f.paragraphs[0].logical_paragraph_id,family:Family::Paragraph,declaration_id:ids[1]},
         Style {caption_id:&f.logical_caption_id,source_node_id:&f.paragraphs[0].logical_paragraph_id,family:Family::Named,declaration_id:ids[2]}]
    }).collect()
}
#[test]
fn stored_caption_content_binds_three_families_noops_and_complete_read_only_output() -> TestResult {
    let rig=content_rig(false)?;let provider=rig.provider()?;let audit_before=rig.metadata.audit_events()?.len();
    let source=provider.import_actual_forms(rig.head,4)?;let state=ImportedCaptionSourceState::import(source.imported().body_structure(),limits()?)?;
    let ids=selections(&source)?;let texts=requests(&ids);let values=layouts(&ids);let styles=style_requests(state.frames().frames());
    let candidate=source.prepare_caption_content_candidate(&provider,&texts,&values,&styles,limits()?,WriterLimits::default(),4)?;
    let receipt=candidate.receipt();assert_eq!(&receipt.source,source.receipt());assert_eq!(&receipt.output.source_state,state.receipt());
    assert_eq!((receipt.text_requests.len(),receipt.layout_requests.len(),receipt.style_requests.len()),(3,3,9));
    assert_eq!((receipt.output.output.text_changes.len(),receipt.output.output.layout_changes.len(),receipt.output.style_changes.len()),(2,2,6));
    assert_eq!(receipt.style_requests.iter().map(|r|r.changed).collect::<Vec<_>>(),[true,true,true,false,false,false,true,true,true]);
    for (binding,request) in receipt.style_requests.iter().zip(&styles) {
        assert_eq!((&binding.source_caption_id,&binding.source_node_id,binding.family),(request.caption_id,request.source_node_id,request.family));
        assert_eq!(binding.requested_declaration,state.frames().style_declaration(request.family,request.declaration_id));
        assert_eq!(binding.requested_declaration.status,StyleStatus::UniqueSourceDeclaration);
    }
    assert_eq!(receipt.output.style_changes.iter().filter(|c|c.inserted_attribute).count(),3);
    let bytes=candidate.with_verified_bytes(&provider,5,<[u8]>::to_vec)?;
    assert_eq!(<[u8;32]>::from(Sha256::digest(&bytes)),receipt.output.output.output_package_sha256);
    let output=ImportedDocumentForms::import(ImportedSourcePackage::import(&bytes,DocumentId::parse("stored-literal-document")?,Sha256::digest(&bytes).into(),SourceImportLimits::default())?)?;
    let after=ImportedCaptionSourceState::import(output.body_structure(),limits()?)?;assert_eq!(after.numbering().controls().iter().map(|n|n.stored_number).collect::<Vec<_>>(),[19,19,19]);
    for (i,frame) in after.frames().frames().iter().enumerate() {
        assert_eq!(after.frames().plain_text(&frame.segments[0].logical_source_id),Some(texts[i].replacement));
        let expected=if i==1{[4,6,8]}else{[5,7,9]};
        assert_eq!((frame.runs[0].character_style.reference_id,frame.paragraphs[0].paragraph_style.reference_id,frame.paragraphs[0].named_style.reference_id),(Some(expected[0]),Some(expected[1]),Some(expected[2])));
        assert_eq!(after.numbering().caption_import().envelopes()[i].native_envelope().side,values[i].layout.side);
    }
    let output_parts=package_parts(&bytes)?;for (path,old) in package_parts(&rig.bytes)? {if path!="Contents/section0.xml"{assert_eq!(output_parts[&path],old);}}
    let audits=rig.metadata.audit_events()?.len();assert_eq!(candidate.verify(&provider,6)?,*receipt);candidate.with_verified_bytes(&provider,6,|_|())?;
    assert!(rig.metadata.audit_events()?.len()>audits);assert!(matches!(candidate.require_current_product_route(&provider,7),Err(ContentError::RouteUnqualified)));
    assert_eq!(rig.revisions.head(&rig.revision_context,rig.project,rig.branch)?,rig.head);assert_eq!(rig.store.download(&rig.owner,rig.result,8)?,rig.bytes);
    assert!(rig.metadata.audit_events()?[audit_before..].iter().all(|e|matches!(e.event,"artifact.metadata.read"|"artifact.download")));
    assert!(!receipt.issuer_execution_publication_authority&&!receipt.output.execution_publication_authority&&!receipt.output.effective_style_and_sequence_semantics_qualified&&!receipt.output.output.complete_auxiliary_state_and_protection_verified);
    let safe=format!("{candidate:?}{}",serde_json::to_string(receipt)?);
    for private in ["private-caption.hwpx","private caption service text","private new A","private new B","literal fixture reader"]{assert!(!safe.contains(private));}Ok(())
}
#[test]
fn stored_caption_content_revoked_acl_invalidates_prepared_receipts_and_every_exposure() -> TestResult {
    let rig=content_rig(false)?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;
    let state=ImportedCaptionSourceState::import(source.imported().body_structure(),limits()?)?;let styles=style_requests(state.frames().frames());
    let candidate=source.prepare_caption_content_candidate(&provider,&[],&[],&styles,limits()?,WriterLimits::default(),4)?;
    let _receipt=candidate.verify(&provider,4)?;let _old_proof=source.imported().reconstruct_source_for_verification(&rig.bytes)?;
    rig.store.set_permissions(&rig.owner,rig.result,rig.reader.subject(),BTreeSet::new(),5)?;let called=Cell::new(false);
    assert!(matches!(candidate.with_verified_bytes(&provider,6,|_|called.set(true)),Err(ContentError::Source(_))));assert!(!called.get());
    assert!(matches!(candidate.verify(&provider,6),Err(ContentError::Source(_))));assert!(matches!(candidate.require_current_product_route(&provider,6),Err(ContentError::Source(_))));
    assert!(matches!(source.prepare_caption_content_candidate(&provider,&[],&[],&styles,limits()?,WriterLimits::default(),6),Err(ContentError::Source(_))));Ok(())
}
#[test]
fn stored_caption_content_quarantine_or_aead_tamper_never_calls_consumer_or_reprepares() -> TestResult {
    for quarantine in [false,true] {
        let rig=content_rig(false)?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;
        let state=ImportedCaptionSourceState::import(source.imported().body_structure(),limits()?)?;let styles=style_requests(state.frames().frames());
        let ids=selections(&source)?;let texts=requests(&ids);let values=layouts(&ids);
        let candidate=source.prepare_caption_content_candidate(&provider,&texts,&values,&styles,limits()?,WriterLimits::default(),4)?;
        if quarantine{rig.store.quarantine(&rig.owner,rig.result,QuarantineReason::parse("CAPTION_CONTENT_FIXTURE_QUARANTINE")?,5)?;}else{rig.blob.tamper.store(true,Ordering::SeqCst);}
        let called=Cell::new(false);assert!(matches!(candidate.with_verified_bytes(&provider,6,|_|called.set(true)),Err(ContentError::Source(_))));assert!(!called.get());
        assert!(candidate.verify(&provider,6).is_err());assert!(candidate.require_current_product_route(&provider,6).is_err());
        assert!(source.prepare_caption_content_candidate(&provider,&texts,&values,&styles,limits()?,WriterLimits::default(),6).is_err());
    }Ok(())
}
// Test-only repository: advance the real shared in-memory head at a selected
// read boundary, without weakening any provider or production source check.
struct BoundaryRepo {inner:rev::InMemoryRevisionRepository,calls:AtomicUsize,trigger:AtomicUsize,
    context:rev::RevisionRequestContext,advance:rev::RevisionCommitRequest}
impl rev::RevisionRepository for BoundaryRepo {
    fn compare_and_swap(&self,context:&rev::RevisionRequestContext,request:&rev::RevisionCommitRequest)->Result<rev::CommitOutcome,rev::RevisionError>{self.inner.compare_and_swap(context,request)}
    fn head(&self,tenant:TenantId,project:rev::ProjectId,branch:rev::BranchId)->Result<rev::RevisionHead,rev::RevisionError>{
        let call=self.calls.fetch_add(1,Ordering::SeqCst)+1;
        if call==self.trigger.load(Ordering::SeqCst){assert!(matches!(self.inner.compare_and_swap(&self.context,&self.advance)?,rev::CommitOutcome::Committed(_)));}
        self.inner.head(tenant,project,branch)
    }
    fn node(&self,tenant:TenantId,project:rev::ProjectId,revision:rev::RevisionId)->Result<rev::RevisionNode,rev::RevisionError>{self.inner.node(tenant,project,revision)}
}
#[test]
fn stored_caption_content_head_movement_including_final_callback_boundary_rejects_old_candidate() -> TestResult {
    let rig=content_rig(false)?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;
    let state=ImportedCaptionSourceState::import(source.imported().body_structure(),limits()?)?;let styles=style_requests(state.frames().frames());
    let candidate=source.prepare_caption_content_candidate(&provider,&[],&[],&styles,limits()?,WriterLimits::default(),4)?;
    let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),rig.project,rig.branch,rig.head,rev::RevisionId::generate(),rig.head.revision_id().into_iter().collect(),StoredArtifactId::generate(),rig.result,None,
        ContentDigest::of(b"content boundary fixture advance"),rev::RevisionValidationState::Verified,ContentDigest::of(b"boundary validation"),ContentDigest::of(b"boundary transaction"))?;
    let boundary=rev::RevisionService::new(BoundaryRepo {inner:rig.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:rig.revision_context.clone(),advance});
    let bound=StoredFormProvider::bind(&rig.store,&boundary,&rig.reader,&rig.revision_context,rig.project,rig.branch,DocumentId::parse("stored-literal-document")?)?;
    boundary.repository().calls.store(0,Ordering::SeqCst);candidate.with_verified_bytes(&bound,5,|_|())?;
    let reads=boundary.repository().calls.load(Ordering::SeqCst);assert!(reads>=4);
    boundary.repository().calls.store(0,Ordering::SeqCst);boundary.repository().trigger.store(reads,Ordering::SeqCst);let called=Cell::new(false);
    assert!(matches!(candidate.with_verified_bytes(&bound,6,|_|called.set(true)),Err(ContentError::Source(_))));assert!(!called.get());
    assert_eq!(boundary.repository().calls.load(Ordering::SeqCst),reads);assert_ne!(rig.revisions.head(&rig.revision_context,rig.project,rig.branch)?,rig.head);
    assert!(candidate.verify(&provider,6).is_err());assert!(candidate.require_current_product_route(&provider,6).is_err());
    assert!(source.prepare_caption_content_candidate(&provider,&[],&[],&styles,limits()?,WriterLimits::default(),6).is_err());Ok(())
}
#[test]
fn stored_caption_content_foreign_scope_original_state_proof_and_fresh_bytes_are_rejected() -> TestResult {
    let rig=content_rig(false)?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;
    let state=ImportedCaptionSourceState::import(source.imported().body_structure(),limits()?)?;let styles=style_requests(state.frames().frames());
    let candidate=source.prepare_caption_content_candidate(&provider,&[],&[],&styles,limits()?,WriterLimits::default(),4)?;
    let foreign=StoredFormProvider::bind(&rig.store,&rig.revisions,&rig.reader,&rig.revision_context,rig.project,rig.branch,DocumentId::parse("foreign-caption-content-document")?)?;
    let called=Cell::new(false);assert!(candidate.with_verified_bytes(&foreign,6,|_|called.set(true)).is_err());assert!(!called.get());
    assert!(candidate.verify(&foreign,6).is_err());assert!(candidate.require_current_product_route(&foreign,6).is_err());
    assert!(source.prepare_caption_content_candidate(&foreign,&[],&[],&styles,limits()?,WriterLimits::default(),6).is_err());
    let other=provider.import_actual_forms(rig.head,6)?;let other_state=ImportedCaptionSourceState::import(other.imported().body_structure(),limits()?)?;
    let proof=source.imported().reconstruct_source_for_verification(&rig.bytes)?;
    assert!(matches!(proof.lower_caption_state_content_batch_candidate(source.imported(),&other_state,&rig.bytes,&[],&[],&styles,limits()?,WriterLimits::default()),Err(CaptionTextOutputError::Source)));
    assert!(matches!(proof.lower_caption_state_content_batch_candidate(other.imported(),&state,&rig.bytes,&[],&[],&styles,limits()?,WriterLimits::default()),Err(CaptionTextOutputError::Source)));
    let mut drift=rig.bytes.clone();drift[0]^=1;
    assert!(matches!(proof.lower_caption_state_content_batch_candidate(source.imported(),&state,&drift,&[],&[],&styles,limits()?,WriterLimits::default()),Err(CaptionTextOutputError::Source)));Ok(())
}
#[test]
fn stored_caption_content_invalid_mixed_requests_protection_noops_and_limits_publish_nothing() -> TestResult {
    let rig=content_rig(false)?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;
    let state=ImportedCaptionSourceState::import(source.imported().body_structure(),limits()?)?;let styles=style_requests(state.frames().frames());
    let ids=selections(&source)?;let texts=requests(&ids);let values=layouts(&ids);let foreign=LogicalId::parse("foreign-content-node")?;
    for invalid in [vec![styles[0],styles[0]],vec![Style {source_node_id:&foreign,..styles[0]}],vec![Style {family:Family::Paragraph,..styles[0]}],
        vec![Style {caption_id:&state.frames().frames()[1].logical_caption_id,..styles[0]}],vec![Style {declaration_id:123456,..styles[0]}]] {
        assert!(matches!(source.prepare_caption_content_candidate(&provider,&texts,&values,&invalid,limits()?,WriterLimits::default(),4),Err(ContentError::Output(CaptionTextOutputError::Selection))));
    }
    let bad=[Request {caption_id:&ids[0].0,text_id:&ids[0].1,replacement:"bad\0"}];
    assert!(matches!(source.prepare_caption_content_candidate(&provider,&bad,&values,&styles,limits()?,WriterLimits::default(),4),Err(ContentError::Output(CaptionTextOutputError::Value))));
    let noop=[Request {caption_id:&ids[1].0,text_id:&ids[1].1,replacement:"private caption service text"}];
    assert!(matches!(source.prepare_caption_content_candidate(&provider,&noop,&values[1..2],&styles[3..6],limits()?,WriterLimits::default(),4),Err(ContentError::Output(CaptionTextOutputError::NoChange))));
    let tiny=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {items_per_kind:1,..Default::default()})?;
    assert!(matches!(source.prepare_caption_content_candidate(&provider,&texts,&values,&styles,tiny,WriterLimits::default(),4),Err(ContentError::State(StateError::Limit))));
    assert!(matches!(source.prepare_caption_content_candidate(&provider,&texts,&values,&styles,limits()?,WriterLimits::new(hwpx_package::WriterLimitConfig {max_output_bytes:1})?,4),Err(ContentError::Output(CaptionTextOutputError::Writer))));
    let rig=content_rig(true)?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;
    let state=ImportedCaptionSourceState::import(source.imported().body_structure(),limits()?)?;let styles=style_requests(state.frames().frames());
    assert!(matches!(source.prepare_caption_content_candidate(&provider,&[],&[],&styles,limits()?,WriterLimits::default(),4),Err(ContentError::Output(CaptionTextOutputError::Protection))));Ok(())
}
