use super::*;

#[test]
fn stored_caption_structure_prepares_from_actual_source_api_join_without_caller_state_import() -> TestResult {
    let rig=structure_rig(false)?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;
    let discover=|document|hwpx_agent_cli::reference_validation_product::ReferenceValidationProductOperation::assess_package_source(
        &rig.bytes,DocumentId::parse(document).unwrap(),Sha256::digest(&rig.bytes).into(),SourceImportLimits::default(),limits().unwrap());
    let report=discover("stored-literal-document")?;let id=LogicalId::parse("private discovered new caption")?;
    let creates=[create(&report.numbering_owners()[0],&id)];let deletes=[delete(&report.caption_frames()[0])];
    let topology=SourceCaptionTopologyRequest {expected_joined_state_sha256:report.caption_source_state_receipt().joined_state_sha256,deletions:&deletes,creations:&creates};
    let candidate=source.prepare_caption_structure_candidate(&provider,&topology,&[],&[],&[],limits()?,WriterLimits::default(),4)?;
    assert_eq!(candidate.receipt().content.output.source_state,*report.caption_source_state_receipt());assert_eq!(candidate.receipt().requested_structure_sha256,topology.canonical_sha256(limits()?)?);
    assert_eq!(candidate.receipt().caption_topology.original_captions,report.caption_frames().len());assert_eq!((candidate.receipt().caption_topology.created.len(),candidate.receipt().caption_topology.deleted.len()),(1,1));
    let output=candidate.with_verified_bytes(&provider,5,<[u8]>::to_vec)?;
    let after=hwpx_agent_cli::reference_validation_product::ReferenceValidationProductOperation::assess_package_source(
        &output,DocumentId::parse("stored-literal-document")?,Sha256::digest(&output).into(),SourceImportLimits::default(),limits()?)?;
    assert_eq!(after.caption_frames().len(),3);assert_ne!(after.caption_source_state_receipt().joined_state_sha256,report.caption_source_state_receipt().joined_state_sha256);
    assert!(!after.caption_source_state_receipt().complete_auxiliary_state_and_protection_qualified&&after.validation_report().is_none());
    let foreign=discover("foreign-discovery-document")?;let foreign_creates=[create(&foreign.numbering_owners()[0],&id)];let foreign_request=SourceCaptionTopologyRequest {
        expected_joined_state_sha256:foreign.caption_source_state_receipt().joined_state_sha256,deletions:&[],creations:&foreign_creates};
    assert!(matches!(source.prepare_caption_structure_candidate(&provider,&foreign_request,&[],&[],&[],limits()?,WriterLimits::default(),5),Err(ContentError::Output(CaptionTextOutputError::Source))));
    let mut stale=SourceCaptionTopologyRequest {expected_joined_state_sha256:topology.expected_joined_state_sha256,deletions:&deletes,creations:&creates};stale.expected_joined_state_sha256[0]^=1;
    assert!(matches!(source.prepare_caption_structure_candidate(&provider,&stale,&[],&[],&[],limits()?,WriterLimits::default(),5),Err(ContentError::Output(CaptionTextOutputError::Source))));
    assert!(matches!(candidate.require_current_product_route(&provider,6),Err(ContentError::RouteUnqualified)));
    assert_eq!(rig.revisions.head(&rig.revision_context,rig.project,rig.branch)?,rig.head);assert_eq!(rig.store.download(&rig.owner,rig.result,6)?,rig.bytes);Ok(())
}
use hwpx_package::{NumberFormat,document_import::{structure::{caption_topology::*,caption_number_topology::{NativeInsertedNumberControl as Number,NativeInsertedNumberFormat as Format}},
    reference_targets::numbering::{NativeNumberCategory as Category,context::NativeNumberingOwnerObservation as Owner}}};
const CONTENT:&[CaptionContent<'static>]=&[CaptionContent::Text("private created caption & <x>\r\n"),CaptionContent::Number(Number::AutoNumber {category:Category::Picture,stored_number:12,
    format:Format {format:NumberFormat::RomanCapital,user_character:"★",prefix:"[",suffix:"]",superscript:true}}),CaptionContent::Number(Number::Restart {category:Category::Picture,stored_number:3,format:None})];
const TAIL:&[CaptionContent<'static>]=&[CaptionContent::Text("private created tail")];
const RUNS:&[CaptionRun<'static>]=&[CaptionRun {character_style:4,content:CONTENT}];
const TAIL_RUNS:&[CaptionRun<'static>]=&[CaptionRun {character_style:5,content:TAIL}];
const BODY:&[CaptionParagraph<'static>]=&[CaptionParagraph {paragraph_style:6,named_style:8,runs:RUNS},CaptionParagraph {paragraph_style:7,named_style:9,runs:TAIL_RUNS}];
fn structure_rig(locked:bool)->Result<Rig,Box<dyn Error>> {
    let mut rig=Rig::new()?;let body=content_body(locked).replacen("<hp:rect id='7'>","<hp:arc id='500' instid='600' lock='0'/><hp:connectLine id='501' instid='601' lock='0'/><hp:rect id='7'>",1);
    let bytes=fixture::package(&body)?;let mut input=zip::ZipArchive::new(Cursor::new(bytes))?;let mut output=zip::ZipWriter::new(Cursor::new(Vec::new()));
    for i in 0..input.len(){let mut entry=input.by_index(i)?;let name=entry.name().to_owned();let mut data=Vec::new();entry.read_to_end(&mut data)?;
        output.start_file(&name,zip::write::SimpleFileOptions::default().compression_method(zip::CompressionMethod::Stored))?;output.write_all(if name=="Contents/header.xml"{HEADER.as_bytes()}else{&data})?;}
    let bytes=output.finish()?.into_inner();
    // Synthetic setup only; production preparation/verification never ingest or commit.
    let result=rig.store.ingest(&rig.owner,IngestRequest {bytes:bytes.clone(),media_type:MediaType::parse("application/vnd.hancom.hwpx+zip")?,file_name:FileName::parse("private-caption-structure.hwpx")?,kind:ArtifactKind::Result},3)?;
    rig.store.set_permissions(&rig.owner,result.artifact_id,rig.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),3)?;
    let commit=rev::RevisionCommitRequest::new(rev::CommitId::generate(),rig.project,rig.branch,rig.head,rev::RevisionId::generate(),rig.head.revision_id().into_iter().collect(),rig.result,result.artifact_id,None,
        ContentDigest::of(b"caption structure fixture setup"),rev::RevisionValidationState::Verified,ContentDigest::of(b"structure fixture validation"),ContentDigest::of(b"structure fixture transaction"))?;
    assert!(matches!(rig.revisions.commit(&rig.revision_context,&commit)?,rev::CommitOutcome::Committed(_)));
    rig.result=result.artifact_id;rig.head=rig.revisions.head(&rig.revision_context,rig.project,rig.branch)?;rig.bytes=bytes;Ok(rig)
}
fn create<'a>(owner:&'a Owner,id:&'a LogicalId)->CaptionCreation<'a> {CaptionCreation {local_id:id,object_id:&owner.logical_object_id,object_fingerprint_sha256:owner.source_fingerprint_sha256,
    layout:hwpx_package::document_import::structure::caption_layout::CaptionLayout {side:NativeCaptionSide::Bottom,full_size:false,width_hwpunit:1000,gap_hwpunit:20,last_width_hwpunit:900},paragraphs:BODY}}
fn delete<'a>(frame:&'a CaptionSourceFrame)->CaptionDeletion<'a>{CaptionDeletion {caption_id:&frame.logical_caption_id,caption_fingerprint_sha256:frame.source_fingerprint_sha256}}
fn request<'a>(state:&ImportedCaptionSourceState<'_>,deletions:&'a[CaptionDeletion<'a>],creations:&'a[CaptionCreation<'a>])->SourceCaptionTopologyRequest<'a>{SourceCaptionTopologyRequest {expected_joined_state_sha256:state.receipt().joined_state_sha256,deletions,creations}}
#[test]
fn stored_caption_structure_mixed_reversed_creation_deletion_replacement_and_retained_edits_are_read_only() -> TestResult {
    let rig=structure_rig(false)?;let provider=rig.provider()?;let audits=rig.metadata.audit_events()?.len();let source=provider.import_actual_forms(rig.head,4)?;
    let state=ImportedCaptionSourceState::import(source.imported().body_structure(),limits()?)?;let frames=state.frames().frames();let owners=state.context().owners();assert_eq!((owners.len(),frames.len()),(5,3));
    let ids=[LogicalId::parse("private new connector")?,LogicalId::parse("private new arc")?,LogicalId::parse("private replacement")?];
    let creates=[create(&owners[1],&ids[0]),create(&owners[0],&ids[1]),create(&owners[4],&ids[2])];let deletes=[delete(&frames[2]),delete(&frames[0])];let topology=request(&state,&deletes,&creates);
    let frame=&frames[1];let texts=[Request {caption_id:&frame.logical_caption_id,text_id:&frame.segments[0].logical_source_id,replacement:"private retained new caption"}];
    let layout=[Layout {caption_id:&frame.logical_caption_id,layout:hwpx_package::document_import::structure::caption_layout::CaptionLayout {side:NativeCaptionSide::Left,..creates[0].layout}}];
    let styles=[Style {caption_id:&frame.logical_caption_id,source_node_id:&frame.runs[0].logical_run_id,family:Family::Character,declaration_id:5},
        Style {caption_id:&frame.logical_caption_id,source_node_id:&frame.paragraphs[0].logical_paragraph_id,family:Family::Paragraph,declaration_id:7},
        Style {caption_id:&frame.logical_caption_id,source_node_id:&frame.paragraphs[0].logical_paragraph_id,family:Family::Named,declaration_id:9}];
    let candidate=source.prepare_caption_structure_candidate(&provider,&topology,&texts,&layout,&styles,limits()?,WriterLimits::default(),4)?;let receipt=candidate.receipt();let r=&receipt.caption_topology;
    assert_eq!(receipt.content.source,*source.receipt());assert_eq!(receipt.content.output.source_state,*state.receipt());assert_eq!(receipt.requested_structure_sha256,topology.canonical_sha256(limits()?)?);
    assert_eq!(r.caller_request_sha256,receipt.requested_structure_sha256);assert_eq!((r.original_captions,r.output_captions,r.created.len(),r.deleted.len(),r.retained_native_controls,r.created_native_controls),(3,4,3,2,2,6));
    assert_eq!(r.created[0].source_object_id,owners[0].logical_object_id);assert_eq!(r.created[0].local_id_sha256,<[u8;32]>::from(Sha256::digest(ids[1].as_str().as_bytes())));assert_eq!(r.created[0].allocated_paragraph_ids,[104,105]);
    let bytes=candidate.with_verified_bytes(&provider,5,<[u8]>::to_vec)?;assert_eq!(<[u8;32]>::from(Sha256::digest(&bytes)),receipt.content.output.output.output_package_sha256);
    let output=ImportedDocumentForms::import(ImportedSourcePackage::import(&bytes,DocumentId::parse("stored-literal-document")?,Sha256::digest(&bytes).into(),SourceImportLimits::default())?)?;
    let after=ImportedCaptionSourceState::import(output.body_structure(),limits()?)?;assert_eq!(after.frames().frames().len(),4);assert_eq!(after.numbering().controls().iter().map(|c|c.stored_number).collect::<Vec<_>>(),[12,3,12,3,19,12,3]);
    let retained=&after.frames().frames()[2];assert_eq!(after.frames().plain_text(&retained.segments[0].logical_source_id),Some(texts[0].replacement));
    assert_eq!((retained.runs[0].character_style.reference_id,retained.paragraphs[0].paragraph_style.reference_id,retained.paragraphs[0].named_style.reference_id),(Some(5),Some(7),Some(9)));
    assert_eq!(after.numbering().caption_import().envelopes()[2].native_envelope().side,NativeCaptionSide::Left);
    let n=source.imported().body_structure().source().parts().iter().find(|p|p.path().as_str()=="Contents/section0.xml").and_then(|p|p.xml()).ok_or("xml")?.elements().len();
    // Ancestor, layout-subtree and content-subtree maps each make two passes.
    assert_eq!(r.paragraph_id_elements_scanned,n);assert_eq!(receipt.content.output.output.observed_protection_element_visits,6*n);assert_eq!(receipt.content.output.output.id_rule_profile,"hwpml-2011-caption-owner-static/v8");
    let output_parts=package_parts(&bytes)?;for (path,old) in package_parts(&rig.bytes)?{if path!="Contents/section0.xml"{assert_eq!(output_parts[&path],old);}}
    let audit_count=rig.metadata.audit_events()?.len();assert_eq!(candidate.verify(&provider,6)?,*receipt);candidate.with_verified_bytes(&provider,6,|_|())?;assert!(rig.metadata.audit_events()?.len()>audit_count);
    assert!(matches!(candidate.require_current_product_route(&provider,7),Err(ContentError::RouteUnqualified)));assert_eq!(rig.revisions.head(&rig.revision_context,rig.project,rig.branch)?,rig.head);assert_eq!(rig.store.download(&rig.owner,rig.result,8)?,rig.bytes);
    assert!(rig.metadata.audit_events()?[audits..].iter().all(|e|matches!(e.event,"artifact.metadata.read"|"artifact.download")));
    assert!(r.complete_owner_caption_and_native_control_inventory_read_back&&!r.native_counter_recalculation_qualified&&!r.execution_publication_authority&&!receipt.issuer_execution_publication_authority);
    let safe=format!("{topology:?}{candidate:?}{}",serde_json::to_string(receipt)?);for private in ["private created caption","private created tail","private new arc","private retained new caption","private-caption-structure.hwpx","literal fixture reader"]{assert!(!safe.contains(private));}Ok(())
}
#[test]
fn stored_caption_structure_digest_binds_complete_typed_body_identity_order_styles_and_layout() -> TestResult {
    let rig=structure_rig(false)?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;let state=ImportedCaptionSourceState::import(source.imported().body_structure(),limits()?)?;
    let ids=[LogicalId::parse("first")?,LogicalId::parse("second")?];let creates=[create(&state.context().owners()[0],&ids[0]),create(&state.context().owners()[1],&ids[1])];let deletes=[delete(&state.frames().frames()[0]),delete(&state.frames().frames()[1])];
    let topology=request(&state,&deletes,&creates);let digest=topology.canonical_sha256(limits()?)?;let candidate=source.prepare_caption_structure_candidate(&provider,&topology,&[],&[],&[],limits()?,WriterLimits::default(),4)?;assert_eq!(candidate.receipt().requested_structure_sha256,digest);
    let mut stale=request(&state,&deletes,&creates);stale.expected_joined_state_sha256[0]^=1;assert_ne!(stale.canonical_sha256(limits()?)?,digest);
    let reverse=[deletes[1],deletes[0]];let mut bad_fp=deletes[0];bad_fp.caption_fingerprint_sha256[0]^=1;let foreign=CaptionDeletion {caption_id:&ids[0],..deletes[0]};
    for changed in [reverse,[bad_fp,deletes[1]],[foreign,deletes[1]]]{assert_ne!(request(&state,&changed,&creates).canonical_sha256(limits()?)?,digest);}
    let changed=[create(&state.context().owners()[1],&ids[1]),create(&state.context().owners()[0],&ids[0])];assert_ne!(request(&state,&deletes,&changed).canonical_sha256(limits()?)?,digest);
    let mut changed=create(&state.context().owners()[0],&ids[0]);changed.object_fingerprint_sha256[0]^=1;assert_ne!(request(&state,&deletes,&[changed,create(&state.context().owners()[1],&ids[1])]).canonical_sha256(limits()?)?,digest);
    for changed in [CaptionCreation {local_id:&ids[1],..create(&state.context().owners()[0],&ids[0])},CaptionCreation {object_id:&state.context().owners()[1].logical_object_id,..create(&state.context().owners()[0],&ids[0])},
        CaptionCreation {layout:hwpx_package::document_import::structure::caption_layout::CaptionLayout {gap_hwpunit:21,..creates[0].layout},..create(&state.context().owners()[0],&ids[0])}] {
        assert_ne!(request(&state,&deletes,&[changed,create(&state.context().owners()[1],&ids[1])]).canonical_sha256(limits()?)?,digest);
    }
    let changed_content=[CaptionContent::Text("private changed body"),CONTENT[1],CONTENT[2]];let runs=[CaptionRun {character_style:5,content:&changed_content}];
    for body in [vec![CaptionParagraph {paragraph_style:7,named_style:8,runs:RUNS},CaptionParagraph {paragraph_style:7,named_style:9,runs:TAIL_RUNS}],
        vec![CaptionParagraph {paragraph_style:6,named_style:9,runs:RUNS},CaptionParagraph {paragraph_style:7,named_style:9,runs:TAIL_RUNS}],
        vec![CaptionParagraph {paragraph_style:6,named_style:8,runs:&runs},CaptionParagraph {paragraph_style:7,named_style:9,runs:TAIL_RUNS}],
        vec![CaptionParagraph {paragraph_style:7,named_style:9,runs:TAIL_RUNS},CaptionParagraph {paragraph_style:6,named_style:8,runs:RUNS}]] {
        let changed=[CaptionCreation {paragraphs:&body,..create(&state.context().owners()[0],&ids[0])},create(&state.context().owners()[1],&ids[1])];assert_ne!(request(&state,&deletes,&changed).canonical_sha256(limits()?)?,digest);
    }Ok(())
}
#[test]
fn stored_caption_structure_revoked_acl_blocks_saved_receipt_proof_and_all_exposures() -> TestResult {
    let rig=structure_rig(false)?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;let state=ImportedCaptionSourceState::import(source.imported().body_structure(),limits()?)?;let id=LogicalId::parse("new")?;
    let creates=[create(&state.context().owners()[0],&id)];let deletes=[delete(&state.frames().frames()[0])];let topology=request(&state,&deletes,&creates);let candidate=source.prepare_caption_structure_candidate(&provider,&topology,&[],&[],&[],limits()?,WriterLimits::default(),4)?;
    let _receipt=candidate.verify(&provider,4)?;let _proof=source.imported().reconstruct_source_for_verification(&rig.bytes)?;rig.store.set_permissions(&rig.owner,rig.result,rig.reader.subject(),BTreeSet::new(),5)?;
    let called=Cell::new(false);assert!(matches!(candidate.with_verified_bytes(&provider,6,|_|called.set(true)),Err(ContentError::Source(_))));assert!(!called.get());
    assert!(matches!(candidate.verify(&provider,6),Err(ContentError::Source(_))));assert!(matches!(candidate.require_current_product_route(&provider,6),Err(ContentError::Source(_))));
    assert!(matches!(source.prepare_caption_structure_candidate(&provider,&topology,&[],&[],&[],limits()?,WriterLimits::default(),6),Err(ContentError::Source(_))));Ok(())
}
#[test]
fn stored_caption_structure_quarantine_or_aead_tamper_blocks_consumer_and_repreparation() -> TestResult {
    for quarantine in [false,true] {
        let rig=structure_rig(false)?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;let state=ImportedCaptionSourceState::import(source.imported().body_structure(),limits()?)?;let id=LogicalId::parse("new")?;
        let creates=[create(&state.context().owners()[0],&id)];let deletes=[delete(&state.frames().frames()[0])];let topology=request(&state,&deletes,&creates);let candidate=source.prepare_caption_structure_candidate(&provider,&topology,&[],&[],&[],limits()?,WriterLimits::default(),4)?;
        if quarantine{rig.store.quarantine(&rig.owner,rig.result,QuarantineReason::parse("CAPTION_STRUCTURE_FIXTURE_QUARANTINE")?,5)?;}else{rig.blob.tamper.store(true,Ordering::SeqCst);}
        let called=Cell::new(false);assert!(matches!(candidate.with_verified_bytes(&provider,6,|_|called.set(true)),Err(ContentError::Source(_))));assert!(!called.get());
        assert!(candidate.verify(&provider,6).is_err());assert!(candidate.require_current_product_route(&provider,6).is_err());assert!(source.prepare_caption_structure_candidate(&provider,&topology,&[],&[],&[],limits()?,WriterLimits::default(),6).is_err());
    }Ok(())
}
#[test]
fn stored_caption_structure_foreign_scope_and_final_writer_head_movement_block_consumer() -> TestResult {
    let rig=structure_rig(false)?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;let state=ImportedCaptionSourceState::import(source.imported().body_structure(),limits()?)?;let id=LogicalId::parse("new")?;
    let creates=[create(&state.context().owners()[0],&id)];let topology=request(&state,&[],&creates);let candidate=source.prepare_caption_structure_candidate(&provider,&topology,&[],&[],&[],limits()?,WriterLimits::default(),4)?;
    let foreign=StoredFormProvider::bind(&rig.store,&rig.revisions,&rig.reader,&rig.revision_context,rig.project,rig.branch,DocumentId::parse("foreign-caption-structure-document")?)?;
    let called=Cell::new(false);assert!(candidate.with_verified_bytes(&foreign,5,|_|called.set(true)).is_err());assert!(!called.get());assert!(candidate.verify(&foreign,5).is_err());assert!(candidate.require_current_product_route(&foreign,5).is_err());
    assert!(source.prepare_caption_structure_candidate(&foreign,&topology,&[],&[],&[],limits()?,WriterLimits::default(),5).is_err());
    let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),rig.project,rig.branch,rig.head,rev::RevisionId::generate(),rig.head.revision_id().into_iter().collect(),StoredArtifactId::generate(),rig.result,None,
        ContentDigest::of(b"structure boundary fixture advance"),rev::RevisionValidationState::Verified,ContentDigest::of(b"structure boundary validation"),ContentDigest::of(b"structure boundary transaction"))?;
    let boundary=rev::RevisionService::new(BoundaryRepo {inner:rig.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:rig.revision_context.clone(),advance});
    let bound=StoredFormProvider::bind(&rig.store,&boundary,&rig.reader,&rig.revision_context,rig.project,rig.branch,DocumentId::parse("stored-literal-document")?)?;
    boundary.repository().calls.store(0,Ordering::SeqCst);candidate.with_verified_bytes(&bound,5,|_|())?;let reads=boundary.repository().calls.load(Ordering::SeqCst);assert!(reads>=4);
    boundary.repository().calls.store(0,Ordering::SeqCst);boundary.repository().trigger.store(reads,Ordering::SeqCst);let called=Cell::new(false);
    assert!(matches!(candidate.with_verified_bytes(&bound,6,|_|called.set(true)),Err(ContentError::Source(_))));assert!(!called.get());assert_eq!(boundary.repository().calls.load(Ordering::SeqCst),reads);
    assert!(candidate.verify(&provider,6).is_err());assert!(candidate.require_current_product_route(&provider,6).is_err());assert!(source.prepare_caption_structure_candidate(&provider,&topology,&[],&[],&[],limits()?,WriterLimits::default(),6).is_err());Ok(())
}
#[test]
fn stored_caption_structure_invalid_stale_duplicate_protected_limited_and_deleted_noops_publish_nothing() -> TestResult {
    let rig=structure_rig(false)?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;let state=ImportedCaptionSourceState::import(source.imported().body_structure(),limits()?)?;let id=LogicalId::parse("new")?;
    let owner=&state.context().owners()[0];let frame=&state.frames().frames()[0];let creates=[create(owner,&id)];let topology=request(&state,&[],&creates);
    let mut stale=request(&state,&[],&creates);stale.expected_joined_state_sha256[0]^=1;assert!(matches!(source.prepare_caption_structure_candidate(&provider,&stale,&[],&[],&[],limits()?,WriterLimits::default(),4),Err(ContentError::Output(CaptionTextOutputError::Source))));
    let mut drift=create(owner,&id);drift.object_fingerprint_sha256[0]^=1;let dup=[create(owner,&id),create(owner,&id)];let foreign=[CaptionCreation {object_id:&id,..create(owner,&id)}];
    for bad in [&[drift][..],&dup[..],&foreign[..]]{assert!(matches!(source.prepare_caption_structure_candidate(&provider,&request(&state,&[],bad),&[],&[],&[],limits()?,WriterLimits::default(),4),Err(ContentError::Output(CaptionTextOutputError::Selection))));}
    let deletion=delete(frame);let mut drift=deletion;drift.caption_fingerprint_sha256[0]^=1;
    for bad in [vec![drift],vec![deletion,deletion],vec![CaptionDeletion {caption_id:&id,..deletion}]]{assert!(matches!(source.prepare_caption_structure_candidate(&provider,&request(&state,&bad,&[]),&[],&[],&[],limits()?,WriterLimits::default(),4),Err(ContentError::Output(CaptionTextOutputError::Selection))));}
    let deletes=[deletion];let text=[Request {caption_id:&frame.logical_caption_id,text_id:&frame.segments[0].logical_source_id,replacement:"private caption service text"}];
    assert!(matches!(source.prepare_caption_structure_candidate(&provider,&request(&state,&deletes,&[]),&text,&[],&[],limits()?,WriterLimits::default(),4),Err(ContentError::Output(CaptionTextOutputError::Selection))));
    assert!(source.prepare_caption_structure_candidate(&provider,&request(&state,&[],&[]),&[],&[],&[],limits()?,WriterLimits::default(),4).is_err());
    let tiny=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {items_per_kind:1,..Default::default()})?;assert!(matches!(source.prepare_caption_structure_candidate(&provider,&topology,&[],&[],&[],tiny,WriterLimits::default(),4),Err(ContentError::State(StateError::Limit))));
    assert!(matches!(source.prepare_caption_structure_candidate(&provider,&topology,&[],&[],&[],limits()?,WriterLimits::new(hwpx_package::WriterLimitConfig {max_output_bytes:1})?,4),Err(ContentError::Output(CaptionTextOutputError::Writer))));
    let removed=source.prepare_caption_structure_candidate(&provider,&request(&state,&deletes,&[]),&[],&[],&[],limits()?,WriterLimits::default(),4)?;assert_eq!((removed.receipt().caption_topology.created.len(),removed.receipt().caption_topology.output_captions),(0,2));removed.with_verified_bytes(&provider,4,|_|())?;
    assert_eq!(rig.store.download(&rig.owner,rig.result,5)?,rig.bytes);assert_eq!(rig.revisions.head(&rig.revision_context,rig.project,rig.branch)?,rig.head);
    let rig=structure_rig(true)?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;let state=ImportedCaptionSourceState::import(source.imported().body_structure(),limits()?)?;let deletes=[delete(&state.frames().frames()[2])];
    assert!(matches!(source.prepare_caption_structure_candidate(&provider,&request(&state,&deletes,&[]),&[],&[],&[],limits()?,WriterLimits::default(),4),Err(ContentError::Output(CaptionTextOutputError::Protection))));Ok(())
}
