use super::*;
use domain_ir::SourceAnchorHandle;
use hwpx_package::{ElementSplicePosition as Position,NumberFormat};
use hwpx_package::document_import::{structure::{caption_number_topology::*,caption_numbering_sequence::NativeDocumentStartValues},
    reference_targets::numbering::NativeNumberCategory as Category};
fn run_anchor(state:&ImportedCaptionSourceState<'_>,index:usize)->Result<SourceAnchorHandle,Box<dyn Error>> {
    let run=&state.frames().frames()[index].runs[0];
    Ok(SourceAnchorHandle {opaque_handle:LogicalId::parse(run.logical_run_id.as_str().strip_prefix("caption-run-").ok_or("run")?)?,fingerprint_sha256:run.source_fingerprint_sha256})
}
fn source_anchor(source:&hwpx_agent_cli::form_stored_provider::actual_import::StoredImportedDocumentForms,path:&str,name:&str)->Result<SourceAnchorHandle,Box<dyn Error>> {
    let part=source.imported().body_structure().source().parts().iter().find(|p|p.path().as_str()==path).ok_or("part")?;
    let i=part.xml().ok_or("xml")?.elements().iter().position(|e|e.name().local_name()==name).ok_or("node")?;
    Ok(part.element_anchor(i).ok_or("anchor")?.clone())
}
fn topology<'a>(state:&ImportedCaptionSourceState<'_>,deletions:&'a[NativeNumberDeletion<'a>],insertions:&'a[NativeNumberInsertion<'a>])->NativeNumberTopologyRequest<'a> {
    NativeNumberTopologyRequest {expected_joined_state_sha256:state.receipt().joined_state_sha256,deletions,insertions}
}
fn deletion<'a>(state:&'a ImportedCaptionSourceState<'_>,index:usize,remove:bool)->NativeNumberDeletion<'a> {
    let c=&state.numbering().controls()[index];NativeNumberDeletion {source_control_id:&c.logical_control_id,source_fingerprint_sha256:c.source_fingerprint_sha256,remove_owned_empty_wrapper:remove}
}
fn restart(value:i32)->NativeInsertedNumberControl<'static>{NativeInsertedNumberControl::Restart {category:Category::Picture,stored_number:value,format:None}}
#[test]
fn stored_caption_topology_four_families_complete_inventory_and_read_only_output() -> TestResult {
    let rig=content_rig(false)?;let provider=rig.provider()?;let audit_before=rig.metadata.audit_events()?.len();
    let source=provider.import_actual_forms(rig.head,4)?;let state=ImportedCaptionSourceState::import(source.imported().body_structure(),limits()?)?;
    let a=run_anchor(&state,0)?;let b=source_anchor(&source,"Contents/header.xml","beginNum")?;
    let ids=[LogicalId::parse("private inserted controls")?,LogicalId::parse("document begin replacement")?];
    let controls=[NativeInsertedNumberControl::AutoNumber {category:Category::Picture,stored_number:100,format:NativeInsertedNumberFormat {format:NumberFormat::RomanCapital,user_character:"★",prefix:"private prefix & <\"\t\r\n",suffix:"private suffix",superscript:true}},restart(3)];
    let begin=[NativeInsertedNumberControl::DocumentStart(NativeDocumentStartValues {page:0,footnote:1,endnote:2,picture:42,table:4,equation:5})];
    let start=state.context().document_start().ok_or("document start")?;
    let deletions=[deletion(&state,0,true),NativeNumberDeletion {source_control_id:&start.logical_control_id,source_fingerprint_sha256:start.source_fingerprint_sha256,remove_owned_empty_wrapper:false}];
    let insertions=[NativeNumberInsertion {local_id:&ids[0],target:&a,position:Position::FirstChild,controls:&controls},NativeNumberInsertion {local_id:&ids[1],target:&b,position:Position::Before,controls:&begin}];
    let request=topology(&state,&deletions,&insertions);let selected=selections(&source)?;let texts=requests(&selected);let values=layouts(&selected);let styles=style_requests(state.frames().frames());
    let candidate=source.prepare_caption_topology_candidate(&provider,&texts,&values,&styles,&request,limits()?,WriterLimits::default(),4)?;
    let receipt=candidate.receipt();let r=&receipt.number_topology;
    assert_eq!(receipt.content.source,*source.receipt());assert_eq!(receipt.content.output.source_state,*state.receipt());
    assert_eq!(receipt.requested_topology_sha256,request.canonical_sha256(limits()?)?);assert_eq!(receipt.requested_topology_sha256,r.caller_request_sha256);
    assert_eq!((r.original_controls,r.retained_controls,r.output_controls,r.deleted.len(),r.inserted.len()),(4,2,5,2,3));assert!(r.complete_original_and_inserted_inventory_read_back&&r.deleted[0].owned_empty_wrapper_removed);
    assert_eq!((receipt.content.output.output.text_changes.len(),receipt.content.output.output.layout_changes.len(),receipt.content.output.style_changes.len()),(2,2,6));
    let bytes=candidate.with_verified_bytes(&provider,5,<[u8]>::to_vec)?;assert_eq!(<[u8;32]>::from(Sha256::digest(&bytes)),receipt.content.output.output.output_package_sha256);
    let output=ImportedDocumentForms::import(ImportedSourcePackage::import(&bytes,DocumentId::parse("stored-literal-document")?,Sha256::digest(&bytes).into(),SourceImportLimits::default())?)?;
    let after=ImportedCaptionSourceState::import(output.body_structure(),limits()?)?;
    assert_eq!(after.numbering().controls().iter().map(|c|c.stored_number).collect::<Vec<_>>(),[100,3,19,19]);assert_eq!(after.context().document_start().ok_or("begin")?.picture,42);
    for (i,f) in after.frames().frames().iter().enumerate(){assert!(f.segments.iter().any(|s|after.frames().plain_text(&s.logical_source_id)==Some(texts[i].replacement)));
        let ids=if i==1{[4,6,8]}else{[5,7,9]};assert_eq!((f.runs[0].character_style.reference_id,f.paragraphs[0].paragraph_style.reference_id,f.paragraphs[0].named_style.reference_id),(Some(ids[0]),Some(ids[1]),Some(ids[2])));}
    let output_parts=package_parts(&bytes)?;for (path,old) in package_parts(&rig.bytes)?{if !matches!(path.as_str(),"Contents/header.xml"|"Contents/section0.xml"){assert_eq!(output_parts[&path],old);}}
    let audits=rig.metadata.audit_events()?.len();assert_eq!(candidate.verify(&provider,6)?,*receipt);candidate.with_verified_bytes(&provider,6,|_|())?;assert!(rig.metadata.audit_events()?.len()>audits);
    assert!(matches!(candidate.require_current_product_route(&provider,7),Err(ContentError::RouteUnqualified)));
    assert_eq!(rig.revisions.head(&rig.revision_context,rig.project,rig.branch)?,rig.head);assert_eq!(rig.store.download(&rig.owner,rig.result,8)?,rig.bytes);
    assert!(rig.metadata.audit_events()?[audit_before..].iter().all(|e|matches!(e.event,"artifact.metadata.read"|"artifact.download")));
    assert!(!receipt.issuer_execution_publication_authority&&!r.execution_publication_authority&&!r.native_counter_recalculation_qualified);
    let safe=format!("{request:?}{candidate:?}{}",serde_json::to_string(receipt)?);for private in ["private prefix","private suffix","private inserted controls","private caption service text","literal fixture reader"]{assert!(!safe.contains(private));}Ok(())
}
#[test]
fn stored_caption_topology_digest_binds_join_ids_fingerprints_positions_order_values_and_formats() -> TestResult {
    let rig=content_rig(false)?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;let state=ImportedCaptionSourceState::import(source.imported().body_structure(),limits()?)?;
    let a=run_anchor(&state,0)?;let b=run_anchor(&state,1)?;let ids=[LogicalId::parse("one")?,LogicalId::parse("two")?];
    let controls=[restart(3),restart(4)];let deletions=[deletion(&state,0,true),deletion(&state,1,false)];
    let insertions=[NativeNumberInsertion {local_id:&ids[0],target:&a,position:Position::FirstChild,controls:&controls},NativeNumberInsertion {local_id:&ids[1],target:&b,position:Position::LastChild,controls:&controls}];
    let request=topology(&state,&deletions,&insertions);let baseline=request.canonical_sha256(limits()?)?;
    let candidate=source.prepare_caption_topology_candidate(&provider,&[],&[],&[],&request,limits()?,WriterLimits::default(),4)?;assert_eq!(candidate.receipt().requested_topology_sha256,baseline);
    let mut stale=topology(&state,&deletions,&insertions);stale.expected_joined_state_sha256[0]^=1;assert_ne!(stale.canonical_sha256(limits()?)?,baseline);
    let mut reversed=deletions;reversed.reverse();let mut policy=deletions;policy[0].remove_owned_empty_wrapper=false;let mut fingerprint=deletions;fingerprint[0].source_fingerprint_sha256[0]^=1;let mut identity=deletions;identity[0].source_control_id=&ids[0];
    for changed in [reversed,policy,fingerprint,identity]{assert_ne!(topology(&state,&changed,&insertions).canonical_sha256(limits()?)?,baseline);}
    for changed in [vec![restart(3)],vec![restart(4),restart(3)],vec![restart(3),restart(5)],vec![NativeInsertedNumberControl::Restart {category:Category::Table,stored_number:3,format:None},restart(4)],
        vec![NativeInsertedNumberControl::AutoNumber {category:Category::Picture,stored_number:3,format:NativeInsertedNumberFormat {format:NumberFormat::Digit,user_character:"",prefix:"",suffix:"",superscript:false}},restart(4)]] {
        let changed=[NativeNumberInsertion {controls:&changed,..NativeNumberInsertion {local_id:&ids[0],target:&a,position:Position::FirstChild,controls:&controls}},NativeNumberInsertion {local_id:&ids[1],target:&b,position:Position::LastChild,controls:&controls}];
        assert_ne!(topology(&state,&deletions,&changed).canonical_sha256(limits()?)?,baseline);
    }
    let mut drift=a.clone();drift.fingerprint_sha256[0]^=1;
    for (id,target,position) in [(&ids[1],&a,Position::FirstChild),(&ids[0],&drift,Position::FirstChild),(&ids[0],&b,Position::FirstChild),(&ids[0],&a,Position::LastChild)] {
        let changed=[NativeNumberInsertion {local_id:id,target,position,controls:&controls},NativeNumberInsertion {local_id:&ids[1],target:&b,position:Position::LastChild,controls:&controls}];assert_ne!(topology(&state,&deletions,&changed).canonical_sha256(limits()?)?,baseline);
    }
    let reverse=[NativeNumberInsertion {local_id:&ids[1],target:&b,position:Position::LastChild,controls:&controls},NativeNumberInsertion {local_id:&ids[0],target:&a,position:Position::FirstChild,controls:&controls}];assert_ne!(topology(&state,&deletions,&reverse).canonical_sha256(limits()?)?,baseline);
    let format=NativeInsertedNumberFormat {format:NumberFormat::Digit,user_character:"",prefix:"",suffix:"",superscript:false};
    let mut digests=std::collections::BTreeSet::new();
    for f in [format,NativeInsertedNumberFormat {format:NumberFormat::RomanSmall,..format},NativeInsertedNumberFormat {user_character:"★",..format},NativeInsertedNumberFormat {prefix:"private prefix",..format},NativeInsertedNumberFormat {suffix:"private suffix",..format},NativeInsertedNumberFormat {superscript:true,..format}] {
        let values=[NativeInsertedNumberControl::Restart {category:Category::Picture,stored_number:3,format:Some(f)}];let insertion=[NativeNumberInsertion {local_id:&ids[0],target:&a,position:Position::FirstChild,controls:&values}];digests.insert(topology(&state,&deletions,&insertion).canonical_sha256(limits()?)?);
    }assert_eq!(digests.len(),6);Ok(())
}
#[test]
fn stored_caption_topology_revoked_acl_blocks_saved_receipts_proof_and_all_exposures() -> TestResult {
    let rig=content_rig(false)?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;let state=ImportedCaptionSourceState::import(source.imported().body_structure(),limits()?)?;
    let a=run_anchor(&state,0)?;let id=LogicalId::parse("new-control")?;let controls=[restart(4)];let insertions=[NativeNumberInsertion {local_id:&id,target:&a,position:Position::FirstChild,controls:&controls}];let request=topology(&state,&[],&insertions);
    let candidate=source.prepare_caption_topology_candidate(&provider,&[],&[],&[],&request,limits()?,WriterLimits::default(),4)?;
    let _receipt=candidate.verify(&provider,4)?;let _proof=source.imported().reconstruct_source_for_verification(&rig.bytes)?;
    rig.store.set_permissions(&rig.owner,rig.result,rig.reader.subject(),BTreeSet::new(),5)?;let called=Cell::new(false);
    assert!(matches!(candidate.with_verified_bytes(&provider,6,|_|called.set(true)),Err(ContentError::Source(_))));assert!(!called.get());
    assert!(matches!(candidate.verify(&provider,6),Err(ContentError::Source(_))));assert!(matches!(candidate.require_current_product_route(&provider,6),Err(ContentError::Source(_))));
    assert!(matches!(source.prepare_caption_topology_candidate(&provider,&[],&[],&[],&request,limits()?,WriterLimits::default(),6),Err(ContentError::Source(_))));Ok(())
}
#[test]
fn stored_caption_topology_quarantine_or_aead_tamper_never_calls_consumer_or_reprepares() -> TestResult {
    for quarantine in [false,true] {
        let rig=content_rig(false)?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;let state=ImportedCaptionSourceState::import(source.imported().body_structure(),limits()?)?;
        let a=run_anchor(&state,0)?;let id=LogicalId::parse("new-control")?;let controls=[restart(4)];let insertions=[NativeNumberInsertion {local_id:&id,target:&a,position:Position::FirstChild,controls:&controls}];let request=topology(&state,&[],&insertions);
        let ids=selections(&source)?;let texts=requests(&ids);let styles=style_requests(state.frames().frames());
        let candidate=source.prepare_caption_topology_candidate(&provider,&texts,&[],&styles,&request,limits()?,WriterLimits::default(),4)?;
        if quarantine {rig.store.quarantine(&rig.owner,rig.result,QuarantineReason::parse("CAPTION_TOPOLOGY_FIXTURE_QUARANTINE")?,5)?;}else{rig.blob.tamper.store(true,Ordering::SeqCst);}
        let called=Cell::new(false);assert!(matches!(candidate.with_verified_bytes(&provider,6,|_|called.set(true)),Err(ContentError::Source(_))));assert!(!called.get());
        assert!(candidate.verify(&provider,6).is_err());assert!(candidate.require_current_product_route(&provider,6).is_err());assert!(source.prepare_caption_topology_candidate(&provider,&texts,&[],&styles,&request,limits()?,WriterLimits::default(),6).is_err());
    }Ok(())
}
#[test]
fn stored_caption_topology_foreign_scope_and_final_writer_head_movement_block_consumer() -> TestResult {
    let rig=content_rig(false)?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;let state=ImportedCaptionSourceState::import(source.imported().body_structure(),limits()?)?;
    let a=run_anchor(&state,0)?;let id=LogicalId::parse("new-control")?;let controls=[restart(4)];let insertions=[NativeNumberInsertion {local_id:&id,target:&a,position:Position::FirstChild,controls:&controls}];let request=topology(&state,&[],&insertions);
    let candidate=source.prepare_caption_topology_candidate(&provider,&[],&[],&[],&request,limits()?,WriterLimits::default(),4)?;
    let foreign=StoredFormProvider::bind(&rig.store,&rig.revisions,&rig.reader,&rig.revision_context,rig.project,rig.branch,DocumentId::parse("foreign-caption-topology-document")?)?;
    let called=Cell::new(false);assert!(candidate.with_verified_bytes(&foreign,5,|_|called.set(true)).is_err());assert!(!called.get());assert!(candidate.verify(&foreign,5).is_err());assert!(candidate.require_current_product_route(&foreign,5).is_err());
    assert!(source.prepare_caption_topology_candidate(&foreign,&[],&[],&[],&request,limits()?,WriterLimits::default(),5).is_err());
    let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),rig.project,rig.branch,rig.head,rev::RevisionId::generate(),rig.head.revision_id().into_iter().collect(),StoredArtifactId::generate(),rig.result,None,
        ContentDigest::of(b"topology boundary fixture advance"),rev::RevisionValidationState::Verified,ContentDigest::of(b"topology boundary validation"),ContentDigest::of(b"topology boundary transaction"))?;
    let boundary=rev::RevisionService::new(BoundaryRepo {inner:rig.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:rig.revision_context.clone(),advance});
    let bound=StoredFormProvider::bind(&rig.store,&boundary,&rig.reader,&rig.revision_context,rig.project,rig.branch,DocumentId::parse("stored-literal-document")?)?;
    boundary.repository().calls.store(0,Ordering::SeqCst);candidate.with_verified_bytes(&bound,5,|_|())?;let reads=boundary.repository().calls.load(Ordering::SeqCst);assert!(reads>=4);
    boundary.repository().calls.store(0,Ordering::SeqCst);boundary.repository().trigger.store(reads,Ordering::SeqCst);let called=Cell::new(false);
    assert!(matches!(candidate.with_verified_bytes(&bound,6,|_|called.set(true)),Err(ContentError::Source(_))));assert!(!called.get());assert_eq!(boundary.repository().calls.load(Ordering::SeqCst),reads);
    assert!(candidate.verify(&provider,6).is_err());assert!(candidate.require_current_product_route(&provider,6).is_err());assert!(source.prepare_caption_topology_candidate(&provider,&[],&[],&[],&request,limits()?,WriterLimits::default(),6).is_err());Ok(())
}
#[test]
fn stored_caption_topology_invalid_stale_duplicate_foreign_protected_and_limited_requests_publish_nothing() -> TestResult {
    let rig=content_rig(false)?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;let state=ImportedCaptionSourceState::import(source.imported().body_structure(),limits()?)?;
    let a=run_anchor(&state,0)?;let id=LogicalId::parse("new-control")?;let controls=[restart(4)];let insertions=[NativeNumberInsertion {local_id:&id,target:&a,position:Position::FirstChild,controls:&controls}];let request=topology(&state,&[],&insertions);
    let mut stale=topology(&state,&[],&insertions);stale.expected_joined_state_sha256[0]^=1;assert!(matches!(source.prepare_caption_topology_candidate(&provider,&[],&[],&[],&stale,limits()?,WriterLimits::default(),4),Err(ContentError::Output(CaptionTextOutputError::Source))));
    let mut stale_anchor=a.clone();stale_anchor.fingerprint_sha256[0]^=1;let wrong=source_anchor(&source,"Contents/section0.xml","t")?;
    for (target,position) in [(&stale_anchor,Position::FirstChild),(&wrong,Position::FirstChild),(&a,Position::Subtree)] {
        let bad=[NativeNumberInsertion {local_id:&id,target,position,controls:&controls}];assert!(source.prepare_caption_topology_candidate(&provider,&[],&[],&[],&topology(&state,&[],&bad),limits()?,WriterLimits::default(),4).is_err());
    }
    let d=deletion(&state,0,false);let mut bad_fp=d;bad_fp.source_fingerprint_sha256[0]^=1;let foreign=NativeNumberDeletion {source_control_id:&id,..d};
    for bad in [vec![d,d],vec![bad_fp],vec![foreign]] {assert!(matches!(source.prepare_caption_topology_candidate(&provider,&[],&[],&[],&topology(&state,&bad,&[]),limits()?,WriterLimits::default(),4),Err(ContentError::Output(CaptionTextOutputError::Selection))));}
    let empty=topology(&state,&[],&[]);assert!(matches!(source.prepare_caption_topology_candidate(&provider,&[],&[],&[],&empty,limits()?,WriterLimits::default(),4),Err(ContentError::Output(CaptionTextOutputError::Value))));
    let invalid=[NativeInsertedNumberControl::Restart {category:Category::Picture,stored_number:0,format:Some(NativeInsertedNumberFormat {format:NumberFormat::Digit,user_character:"",prefix:"bad\0",suffix:"",superscript:false})}];
    let bad=[NativeNumberInsertion {local_id:&id,target:&a,position:Position::FirstChild,controls:&invalid}];assert!(matches!(source.prepare_caption_topology_candidate(&provider,&[],&[],&[],&topology(&state,&[],&bad),limits()?,WriterLimits::default(),4),Err(ContentError::Output(CaptionTextOutputError::Value))));
    let tiny=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {items_per_kind:1,..Default::default()})?;assert!(matches!(source.prepare_caption_topology_candidate(&provider,&[],&[],&[],&request,tiny,WriterLimits::default(),4),Err(ContentError::State(StateError::Limit))));
    assert!(matches!(source.prepare_caption_topology_candidate(&provider,&[],&[],&[],&request,limits()?,WriterLimits::new(hwpx_package::WriterLimitConfig {max_output_bytes:1})?,4),Err(ContentError::Output(CaptionTextOutputError::Writer))));
    let other=provider.import_actual_forms(rig.head,4)?;let other_state=ImportedCaptionSourceState::import(other.imported().body_structure(),limits()?)?;let proof=source.imported().reconstruct_source_for_verification(&rig.bytes)?;
    assert!(matches!(proof.lower_caption_state_topology_batch_candidate(source.imported(),&other_state,&rig.bytes,&[],&[],&[],&request,limits()?,WriterLimits::default()),Err(CaptionTextOutputError::Source)));
    assert!(matches!(proof.lower_caption_state_topology_batch_candidate(other.imported(),&state,&rig.bytes,&[],&[],&[],&request,limits()?,WriterLimits::default()),Err(CaptionTextOutputError::Source)));
    let mut drift=rig.bytes.clone();drift[0]^=1;assert!(matches!(proof.lower_caption_state_topology_batch_candidate(source.imported(),&state,&drift,&[],&[],&[],&request,limits()?,WriterLimits::default()),Err(CaptionTextOutputError::Source)));
    let rig=content_rig(true)?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;let state=ImportedCaptionSourceState::import(source.imported().body_structure(),limits()?)?;let deletions=[deletion(&state,2,true)];
    assert!(matches!(source.prepare_caption_topology_candidate(&provider,&[],&[],&[],&topology(&state,&deletions,&[]),limits()?,WriterLimits::default(),4),Err(ContentError::Output(CaptionTextOutputError::Protection))));Ok(())
}
