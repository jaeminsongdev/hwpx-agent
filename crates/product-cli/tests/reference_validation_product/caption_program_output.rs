use super::*;
use domain_ir::{CaptionSequenceDefinition as Definition,CaptionNumberFormat as Format,CaptionObjectKind as ObjectKind,CaptionRestartPolicy as Restart};
use hwpx_package::document_import::reference_targets::{caption_source_state::output::program::*,caption_frames::CaptionFrameSegmentKind};
fn program_rig(locked:bool)->Result<Rig,Box<dyn Error>> {
    let mut rig=Rig::new()?;let bytes=fixture::package(&content_body(locked).replace("</hp:ctrl>","</hp:ctrl><hp:t>private old tail</hp:t>"))?;
    let mut input=zip::ZipArchive::new(Cursor::new(bytes))?;let mut output=zip::ZipWriter::new(Cursor::new(Vec::new()));
    for i in 0..input.len(){let mut entry=input.by_index(i)?;let name=entry.name().to_owned();let mut data=Vec::new();entry.read_to_end(&mut data)?;
        output.start_file(&name,zip::write::SimpleFileOptions::default().compression_method(zip::CompressionMethod::Stored))?;output.write_all(if name=="Contents/header.xml"{HEADER.as_bytes()}else{&data})?;}
    let bytes=output.finish()?.into_inner();
    // Synthetic test-only setup; no production prepare/verify ingest or commit.
    let result=rig.store.ingest(&rig.owner,IngestRequest {bytes:bytes.clone(),media_type:MediaType::parse("application/vnd.hancom.hwpx+zip")?,file_name:FileName::parse("private-caption.hwpx")?,kind:ArtifactKind::Result},3)?;
    rig.store.set_permissions(&rig.owner,result.artifact_id,rig.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),3)?;
    let commit=rev::RevisionCommitRequest::new(rev::CommitId::generate(),rig.project,rig.branch,rig.head,rev::RevisionId::generate(),rig.head.revision_id().into_iter().collect(),rig.result,result.artifact_id,None,
        ContentDigest::of(b"caption program fixture setup"),rev::RevisionValidationState::Verified,ContentDigest::of(b"program fixture validation"),ContentDigest::of(b"program fixture transaction"))?;
    assert!(matches!(rig.revisions.commit(&rig.revision_context,&commit)?,rev::CommitOutcome::Committed(_)));
    rig.result=result.artifact_id;rig.head=rig.revisions.head(&rig.revision_context,rig.project,rig.branch)?;rig.bytes=bytes;Ok(rig)
}
fn definition(state:&ImportedCaptionSourceState<'_>,id:&str,style:u32,start:u32)->Definition {
    Definition {logical_sequence_id:LogicalId::parse(id).unwrap(),object_kind:ObjectKind::Picture,label:"private generated <label> &".into(),separator:" ".into(),number_format:Format::Decimal,
        restart_policy:Restart::Continuous,start_at:start,number_style_sha256:hex::encode(state.frames().style_declaration(Family::Character,style).declaration_sha256.unwrap()),opaque_properties:vec![],locked:false}
}
fn assignments<'a>(state:&'a ImportedCaptionSourceState<'_>,sequence:&'a LogicalId)->Result<Vec<SourceCaptionSequenceAssignment<'a>>,Box<dyn Error>> {
    state.frames().frames().iter().enumerate().map(|(i,f)|Ok(SourceCaptionSequenceAssignment {caption_id:&f.logical_caption_id,object_id:&f.logical_object_id,sequence_id:sequence,
        label_text_id:&f.segments.iter().find(|s|s.kind==CaptionFrameSegmentKind::PlainText).ok_or("text")?.logical_source_id,
        number_control_id:f.segments.iter().find(|s|s.kind==CaptionFrameSegmentKind::AutoNumber).and_then(|s|s.number_control_id.as_ref()).ok_or("auto")?,document_order:i as u64})).collect()
}
fn request<'a>(state:&ImportedCaptionSourceState<'_>,sequences:&'a[Definition],assignments:&'a[SourceCaptionSequenceAssignment<'a>])->SourceCaptionSequenceRequest<'a> {
    SourceCaptionSequenceRequest {expected_joined_state_sha256:state.receipt().joined_state_sha256,sequences,assignments}
}
fn uniform_styles<'a>(state:&'a ImportedCaptionSourceState<'_>)->Vec<Style<'a>> {
    state.frames().frames().iter().map(|f|Style {caption_id:&f.logical_caption_id,source_node_id:&f.runs[0].logical_run_id,family:Family::Character,declaration_id:4}).collect()
}
#[test]
fn stored_caption_program_generated_labels_noops_and_all_families_share_read_only_output() -> TestResult {
    let rig=program_rig(false)?;let provider=rig.provider()?;let audit_before=rig.metadata.audit_events()?.len();let source=provider.import_actual_forms(rig.head,4)?;
    let state=ImportedCaptionSourceState::import(source.imported().body_structure(),limits()?)?;let frames=state.frames().frames();
    let mut sequences=[definition(&state,"private sequence one",5,4),definition(&state,"private sequence two",4,19)];sequences[0].number_format=Format::RomanUpper;
    sequences[1].label=state.frames().plain_text(&frames[1].segments[0].logical_source_id).ok_or("old label")?.into();sequences[1].separator.clear();
    let mut members=assignments(&state,&sequences[0].logical_sequence_id)?;members[1].sequence_id=&sequences[1].logical_sequence_id;
    for (member,order) in members.iter_mut().zip([20,10,30]){member.document_order=order;}
    let program=request(&state,&sequences,&members);let styles=style_requests(frames);let ids=selections(&source)?;let caption_ids=[ids[0].clone(),ids[2].clone(),ids[4].clone()];let values=layouts(&caption_ids);
    let texts=frames.iter().enumerate().map(|(i,f)|Request {caption_id:&f.logical_caption_id,text_id:&f.segments.last().unwrap().logical_source_id,replacement:if i==1{"private old tail"}else{"private changed tail"}}).collect::<Vec<_>>();
    let candidate=source.prepare_caption_program_candidate(&provider,&program,&texts,&values,&styles,limits()?,WriterLimits::default(),4)?;let r=candidate.receipt();
    assert_eq!(r.requested_program_sha256,program.canonical_sha256(limits()?)?);assert_eq!(r.program.caller_request_sha256,r.requested_program_sha256);
    assert_eq!((r.content.text_requests.len(),r.content.layout_requests.len(),r.content.style_requests.len()),(6,3,9));
    assert_eq!(r.content.text_requests.iter().map(|b|b.changed).collect::<Vec<_>>(),[true,false,true,true,false,true]);
    for (i,binding) in r.content.text_requests[..3].iter().enumerate(){let sequence=&sequences[usize::from(i==1)];let label=format!("{}{}",sequence.label,sequence.separator);
        assert_eq!((&binding.source_caption_id,&binding.source_text_id),(members[i].caption_id,members[i].label_text_id));assert_eq!(binding.requested_text_sha256,<[u8;32]>::from(Sha256::digest(label.as_bytes())));assert_eq!(binding.requested_text_bytes,label.len());}
    assert_eq!((r.content.output.output.text_changes.len(),r.content.output.output.layout_changes.len(),r.content.output.style_changes.len()),(4,2,6));
    assert_eq!(r.program.bindings.iter().map(|b|b.resolved_number).collect::<Vec<_>>(),[4,19,5]);
    let bytes=candidate.with_verified_bytes(&provider,5,<[u8]>::to_vec)?;let output=ImportedDocumentForms::import(ImportedSourcePackage::import(&bytes,DocumentId::parse("stored-literal-document")?,Sha256::digest(&bytes).into(),SourceImportLimits::default())?)?;
    let after=ImportedCaptionSourceState::import(output.body_structure(),limits()?)?;assert_eq!(after.numbering().controls().iter().map(|n|n.stored_number).collect::<Vec<_>>(),[4,19,5]);
    for (i,f) in after.frames().frames().iter().enumerate(){let definition=&sequences[usize::from(i==1)];let label=format!("{}{}",definition.label,definition.separator);assert_eq!(after.frames().plain_text(&f.segments[0].logical_source_id),Some(label.as_str()));
        assert_eq!(after.frames().plain_text(&f.segments.last().unwrap().logical_source_id),Some(texts[i].replacement));assert_eq!(f.runs[0].character_style.reference_id,Some(if i==1{4}else{5}));}
    let parts=package_parts(&bytes)?;for (path,old) in package_parts(&rig.bytes)?{if path!="Contents/section0.xml"{assert_eq!(parts[&path],old);}}
    let audits=rig.metadata.audit_events()?.len();assert_eq!(candidate.verify(&provider,6)?,*r);candidate.with_verified_bytes(&provider,6,|_|())?;assert!(rig.metadata.audit_events()?.len()>audits);
    assert!(matches!(candidate.require_current_product_route(&provider,7),Err(ContentError::RouteUnqualified)));
    assert_eq!(rig.revisions.head(&rig.revision_context,rig.project,rig.branch)?,rig.head);assert_eq!(rig.store.download(&rig.owner,rig.result,8)?,rig.bytes);
    assert!(rig.metadata.audit_events()?[audit_before..].iter().all(|e|matches!(e.event,"artifact.metadata.read"|"artifact.download")));
    assert!(!r.issuer_execution_publication_authority&&!r.program.native_counter_recalculation_qualified&&!r.program.execution_publication_authority);
    let safe=format!("{program:?}{candidate:?}{}",serde_json::to_string(r)?);for raw in ["private sequence one","private sequence two","private generated","private changed tail","literal fixture reader"]{assert!(!safe.contains(raw));}Ok(())
}
#[test]
fn stored_caption_program_noop_generated_labels_and_every_definition_member_field_remain_bound() -> TestResult {
    let rig=program_rig(false)?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;let state=ImportedCaptionSourceState::import(source.imported().body_structure(),limits()?)?;
    let mut sequences=[definition(&state,"private active sequence",4,19),definition(&state,"private unused sequence",4,7)];sequences[0].label=state.frames().plain_text(&state.frames().frames()[0].segments[0].logical_source_id).unwrap().into();sequences[0].separator.clear();
    let members=assignments(&state,&sequences[0].logical_sequence_id)?;let program=request(&state,&sequences,&members);let styles=uniform_styles(&state);
    let candidate=source.prepare_caption_program_candidate(&provider,&program,&[],&[],&styles,limits()?,WriterLimits::default(),4)?;assert!(candidate.receipt().content.text_requests.iter().all(|b|!b.changed));
    assert_eq!(candidate.receipt().content.text_requests.len(),3);let baseline=candidate.receipt().requested_program_sha256;
    let mut stale=request(&state,&sequences,&members);stale.expected_joined_state_sha256[0]^=1;assert_ne!(stale.canonical_sha256(limits()?)?,baseline);
    for mode in 0..9 {let mut definitions=sequences.clone();match mode {0=>definitions[0].start_at+=1,1=>definitions[0].label="other".into(),2=>definitions[0].separator="_".into(),3=>definitions[0].number_format=Format::RomanLower,
        4=>definitions[0].restart_policy=Restart::PerSection,5=>definitions[0].number_style_sha256="a".repeat(64),6=>definitions[0].locked=true,7=>definitions[1].label="unused changed".into(),_=>definitions[1].logical_sequence_id=LogicalId::parse("unused renamed")?};
        assert_ne!(request(&state,&definitions,&members).canonical_sha256(limits()?)?,baseline);
    }
    for mode in 0..7 {let mut bad=assignments(&state,&sequences[0].logical_sequence_id)?;match mode {0=>bad[0].caption_id=bad[1].caption_id,1=>bad[0].object_id=bad[1].object_id,2=>bad[0].label_text_id=bad[1].label_text_id,
        3=>bad[0].number_control_id=bad[1].number_control_id,4=>bad[0].document_order+=100,5=>bad[0].sequence_id=&sequences[1].logical_sequence_id,_=>bad.reverse()};assert_ne!(request(&state,&sequences,&bad).canonical_sha256(limits()?)?,baseline);}
    let mut reordered=sequences.clone();reordered.reverse();assert_ne!(request(&state,&reordered,&members).canonical_sha256(limits()?)?,baseline);Ok(())
}
#[test]
fn stored_caption_program_acl_revocation_invalidates_saved_receipt_proof_and_all_exposures() -> TestResult {
    let rig=program_rig(false)?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;let state=ImportedCaptionSourceState::import(source.imported().body_structure(),limits()?)?;
    let sequences=[definition(&state,"sequence",4,1)];let members=assignments(&state,&sequences[0].logical_sequence_id)?;let program=request(&state,&sequences,&members);let styles=uniform_styles(&state);
    let candidate=source.prepare_caption_program_candidate(&provider,&program,&[],&[],&styles,limits()?,WriterLimits::default(),4)?;let _receipt=candidate.verify(&provider,4)?;let _proof=source.imported().reconstruct_source_for_verification(&rig.bytes)?;
    rig.store.set_permissions(&rig.owner,rig.result,rig.reader.subject(),BTreeSet::new(),5)?;let called=Cell::new(false);
    assert!(matches!(candidate.with_verified_bytes(&provider,6,|_|called.set(true)),Err(ContentError::Source(_))));assert!(!called.get());
    assert!(matches!(candidate.verify(&provider,6),Err(ContentError::Source(_))));assert!(matches!(candidate.require_current_product_route(&provider,6),Err(ContentError::Source(_))));
    assert!(matches!(source.prepare_caption_program_candidate(&provider,&program,&[],&[],&styles,limits()?,WriterLimits::default(),6),Err(ContentError::Source(_))));Ok(())
}
#[test]
fn stored_caption_program_quarantine_or_ciphertext_tamper_blocks_consumer_and_reprepare() -> TestResult {
    for quarantine in [false,true] {let rig=program_rig(false)?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;let state=ImportedCaptionSourceState::import(source.imported().body_structure(),limits()?)?;
        let sequences=[definition(&state,"sequence",4,1)];let members=assignments(&state,&sequences[0].logical_sequence_id)?;let program=request(&state,&sequences,&members);let styles=uniform_styles(&state);
        let candidate=source.prepare_caption_program_candidate(&provider,&program,&[],&[],&styles,limits()?,WriterLimits::default(),4)?;
        if quarantine{rig.store.quarantine(&rig.owner,rig.result,QuarantineReason::parse("CAPTION_PROGRAM_FIXTURE_QUARANTINE")?,5)?;}else{rig.blob.tamper.store(true,Ordering::SeqCst);}
        let called=Cell::new(false);assert!(matches!(candidate.with_verified_bytes(&provider,6,|_|called.set(true)),Err(ContentError::Source(_))));assert!(!called.get());
        assert!(candidate.verify(&provider,6).is_err());assert!(candidate.require_current_product_route(&provider,6).is_err());assert!(source.prepare_caption_program_candidate(&provider,&program,&[],&[],&styles,limits()?,WriterLimits::default(),6).is_err());
    }Ok(())
}
#[test]
fn stored_caption_program_foreign_scope_and_final_callback_head_movement_block_all_outputs() -> TestResult {
    let rig=program_rig(false)?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;let state=ImportedCaptionSourceState::import(source.imported().body_structure(),limits()?)?;
    let sequences=[definition(&state,"sequence",4,1)];let members=assignments(&state,&sequences[0].logical_sequence_id)?;let program=request(&state,&sequences,&members);let styles=uniform_styles(&state);
    let candidate=source.prepare_caption_program_candidate(&provider,&program,&[],&[],&styles,limits()?,WriterLimits::default(),4)?;
    let foreign=StoredFormProvider::bind(&rig.store,&rig.revisions,&rig.reader,&rig.revision_context,rig.project,rig.branch,DocumentId::parse("foreign-caption-program-document")?)?;let called=Cell::new(false);
    assert!(candidate.with_verified_bytes(&foreign,5,|_|called.set(true)).is_err());assert!(!called.get());assert!(candidate.verify(&foreign,5).is_err());assert!(candidate.require_current_product_route(&foreign,5).is_err());assert!(source.prepare_caption_program_candidate(&foreign,&program,&[],&[],&styles,limits()?,WriterLimits::default(),5).is_err());
    let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),rig.project,rig.branch,rig.head,rev::RevisionId::generate(),rig.head.revision_id().into_iter().collect(),StoredArtifactId::generate(),rig.result,None,
        ContentDigest::of(b"program boundary fixture advance"),rev::RevisionValidationState::Verified,ContentDigest::of(b"program boundary validation"),ContentDigest::of(b"program boundary transaction"))?;
    let boundary=rev::RevisionService::new(BoundaryRepo {inner:rig.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:rig.revision_context.clone(),advance});
    let bound=StoredFormProvider::bind(&rig.store,&boundary,&rig.reader,&rig.revision_context,rig.project,rig.branch,DocumentId::parse("stored-literal-document")?)?;
    boundary.repository().calls.store(0,Ordering::SeqCst);candidate.with_verified_bytes(&bound,5,|_|())?;let reads=boundary.repository().calls.load(Ordering::SeqCst);assert!(reads>=4);
    boundary.repository().calls.store(0,Ordering::SeqCst);boundary.repository().trigger.store(reads,Ordering::SeqCst);let called=Cell::new(false);
    assert!(matches!(candidate.with_verified_bytes(&bound,6,|_|called.set(true)),Err(ContentError::Source(_))));assert!(!called.get());assert_eq!(boundary.repository().calls.load(Ordering::SeqCst),reads);
    assert!(candidate.verify(&provider,6).is_err());assert!(candidate.require_current_product_route(&provider,6).is_err());assert!(source.prepare_caption_program_candidate(&provider,&program,&[],&[],&styles,limits()?,WriterLimits::default(),6).is_err());Ok(())
}
#[test]
fn stored_caption_program_invalid_members_metadata_proof_protection_and_limits_publish_nothing() -> TestResult {
    let rig=program_rig(false)?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;let state=ImportedCaptionSourceState::import(source.imported().body_structure(),limits()?)?;
    let sequences=[definition(&state,"sequence",4,1)];let members=assignments(&state,&sequences[0].logical_sequence_id)?;let program=request(&state,&sequences,&members);let styles=uniform_styles(&state);
    assert!(source.prepare_caption_program_candidate(&provider,&request(&state,&sequences,&members[..2]),&[],&[],&styles,limits()?,WriterLimits::default(),4).is_err());
    let mut stale=request(&state,&sequences,&members);stale.expected_joined_state_sha256[0]^=1;assert!(matches!(source.prepare_caption_program_candidate(&provider,&stale,&[],&[],&styles,limits()?,WriterLimits::default(),4),Err(ContentError::Output(CaptionTextOutputError::Source))));
    for mode in 0..5 {let mut bad=assignments(&state,&sequences[0].logical_sequence_id)?;match mode {0=>bad[0].caption_id=bad[1].caption_id,1=>bad[0].object_id=bad[1].object_id,2=>bad[0].number_control_id=bad[1].number_control_id,3=>bad[0].label_text_id=bad[1].label_text_id,_=>bad[0].document_order=bad[1].document_order};
        assert!(source.prepare_caption_program_candidate(&provider,&request(&state,&sequences,&bad),&[],&[],&styles,limits()?,WriterLimits::default(),4).is_err());}
    for mode in 0..6 {let mut bad=sequences.clone();match mode {0=>bad[0].object_kind=ObjectKind::Table,1=>bad[0].number_style_sha256="a".repeat(64),2=>bad[0].start_at=0,3=>bad[0].start_at=i32::MAX as u32+1,4=>bad[0].label="bad\0".into(),_=>bad[0].locked=true};
        assert!(source.prepare_caption_program_candidate(&provider,&request(&state,&bad,&members),&[],&[],&styles,limits()?,WriterLimits::default(),4).is_err());}
    let duplicate=[Request {caption_id:members[0].caption_id,text_id:members[0].label_text_id,replacement:"other"}];assert!(matches!(source.prepare_caption_program_candidate(&provider,&program,&duplicate,&[],&styles,limits()?,WriterLimits::default(),4),Err(ContentError::Output(CaptionTextOutputError::Selection))));
    let tiny=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {items_per_kind:1,..Default::default()})?;assert!(source.prepare_caption_program_candidate(&provider,&program,&[],&[],&styles,tiny,WriterLimits::default(),4).is_err());
    assert!(matches!(source.prepare_caption_program_candidate(&provider,&program,&[],&[],&styles,limits()?,WriterLimits::new(hwpx_package::WriterLimitConfig {max_output_bytes:1})?,4),Err(ContentError::Output(CaptionTextOutputError::Writer))));
    let other=provider.import_actual_forms(rig.head,4)?;let other_state=ImportedCaptionSourceState::import(other.imported().body_structure(),limits()?)?;let proof=source.imported().reconstruct_source_for_verification(&rig.bytes)?;
    assert!(matches!(proof.lower_caption_state_program_candidate(source.imported(),&other_state,&rig.bytes,&program,&[],&[],&styles,limits()?,WriterLimits::default()),Err(CaptionTextOutputError::Source)));
    let mut drift=rig.bytes.clone();drift[0]^=1;assert!(matches!(proof.lower_caption_state_program_candidate(source.imported(),&state,&drift,&program,&[],&[],&styles,limits()?,WriterLimits::default()),Err(CaptionTextOutputError::Source)));
    let rig=program_rig(true)?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;let state=ImportedCaptionSourceState::import(source.imported().body_structure(),limits()?)?;
    let sequences=[definition(&state,"sequence",4,1)];let members=assignments(&state,&sequences[0].logical_sequence_id)?;let styles=uniform_styles(&state);
    assert!(matches!(source.prepare_caption_program_candidate(&provider,&request(&state,&sequences,&members),&[],&[],&styles,limits()?,WriterLimits::default(),4),Err(ContentError::Output(CaptionTextOutputError::Protection))));Ok(())
}
