use super::*;
use hwpx_package::document_import::{structure::caption_numbering_sequence::*,reference_targets::numbering::{NativeNumberCategory as Category,NativeNumberControlKind as Kind}};
use hwpx_package::NumberFormat;
fn sequence_rig(locked:bool)->Result<Rig,Box<dyn Error>> {
    let mut rig=content_rig(locked)?;let mut source=zip::ZipArchive::new(Cursor::new(&rig.bytes))?;let mut output=zip::ZipWriter::new(Cursor::new(Vec::new()));
    for i in 0..source.len(){let mut entry=source.by_index(i)?;let name=entry.name().to_owned();let mut data=Vec::new();entry.read_to_end(&mut data)?;
        if name=="Contents/section0.xml"{data=String::from_utf8(data)?.replacen("<hp:run>","<hp:run><hp:secPr><hp:startNum pageStartsOn='BOTH' page='0' pic='0' tbl='3' equation='4'/></hp:secPr><hp:ctrl><hp:newNum num='5' numType='PICTURE'/></hp:ctrl>",1).into_bytes();}
        output.start_file(name,zip::write::SimpleFileOptions::default().compression_method(zip::CompressionMethod::Stored))?;output.write_all(&data)?;}
    let bytes=output.finish()?.into_inner();drop(source);
    // Test-only fixture installation, never a production prepare/verify effect.
    let result=rig.store.ingest(&rig.owner,IngestRequest {bytes:bytes.clone(),media_type:MediaType::parse("application/vnd.hancom.hwpx+zip")?,file_name:FileName::parse("private-caption.hwpx")?,kind:ArtifactKind::Result},3)?;
    rig.store.set_permissions(&rig.owner,result.artifact_id,rig.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),3)?;
    let request=rev::RevisionCommitRequest::new(rev::CommitId::generate(),rig.project,rig.branch,rig.head,rev::RevisionId::generate(),rig.head.revision_id().into_iter().collect(),rig.result,result.artifact_id,None,
        ContentDigest::of(b"sequence fixture setup"),rev::RevisionValidationState::Verified,ContentDigest::of(b"sequence fixture validation"),ContentDigest::of(b"sequence fixture transaction"))?;
    assert!(matches!(rig.revisions.commit(&rig.revision_context,&request)?,rev::CommitOutcome::Committed(_)));
    rig.result=result.artifact_id;rig.head=rig.revisions.head(&rig.revision_context,rig.project,rig.branch)?;rig.bytes=bytes;Ok(rig)
}
fn snapshot<'a>(state:&'a ImportedCaptionSourceState<'_>)->Result<Vec<NativeNumberEventReplacement<'a>>,Box<dyn Error>> {
    let controls:BTreeMap<_,_>=state.numbering().controls().iter().map(|c|(&c.logical_control_id,c)).collect();
    let starts:BTreeMap<_,_>=state.numbering().section_starts().iter().map(|c|(&c.logical_control_id,c)).collect();
    state.context().ordered_controls().iter().map(|ordered|{
        if let Some(&c)=controls.get(&ordered.logical_control_id) {
            let values=match c.kind {Kind::AutoNumber=>NativeNumberEventValues::AutoNumber {category:c.category,stored_number:c.stored_number,format:NativeNumberFormatReplacement::Preserve},
                Kind::Restart=>NativeNumberEventValues::Restart {category:c.category,stored_number:c.stored_number,format:NativeNumberFormatReplacement::Preserve}};
            return Ok(NativeNumberEventReplacement {source_control_id:&c.logical_control_id,source_fingerprint_sha256:c.source_fingerprint_sha256,values});
        }
        let c=*starts.get(&ordered.logical_control_id).ok_or("section start")?;
        let page_starts_on=match c.page_starts_on {"BOTH"=>NativePageStartsOn::Both,"EVEN"=>NativePageStartsOn::Even,"ODD"=>NativePageStartsOn::Odd,_=>return Err("source enum".into())};
        Ok(NativeNumberEventReplacement {source_control_id:&c.logical_control_id,source_fingerprint_sha256:c.source_fingerprint_sha256,
            values:NativeNumberEventValues::SectionStart {page_starts_on,page:c.page,picture:c.picture,table:c.table,equation:c.equation}})
    }).collect()
}
fn request<'a>(state:&'a ImportedCaptionSourceState<'_>,events:&'a[NativeNumberEventReplacement<'a>])->NativeNumberSequenceReplacement<'a> {
    NativeNumberSequenceReplacement {expected_joined_state_sha256:state.receipt().joined_state_sha256,events,
        document_start:state.context().document_start().map(|c|NativeDocumentStartReplacement {source_control_id:&c.logical_control_id,source_fingerprint_sha256:c.source_fingerprint_sha256,
            values:NativeDocumentStartValues {page:c.page,footnote:c.footnote,endnote:c.endnote,picture:c.picture,table:c.table,equation:c.equation}})}
}
fn change(event:NativeNumberEventReplacement<'_>,value:i32)->NativeNumberEventReplacement<'_> {
    NativeNumberEventReplacement {values:match event.values {
        NativeNumberEventValues::AutoNumber {category,format,..}=>NativeNumberEventValues::AutoNumber {category,stored_number:value,format},
        NativeNumberEventValues::Restart {category,format,..}=>NativeNumberEventValues::Restart {category,stored_number:value,format},value=>value,
    },..event}
}
#[test]
fn stored_caption_sequence_complete_request_binds_all_four_families_and_read_only_output() -> TestResult {
    let rig=sequence_rig(false)?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;let audit_start=rig.metadata.audit_events()?.len();
    let state=ImportedCaptionSourceState::import(source.imported().body_structure(),limits()?)?;let mut events=snapshot(&state)?;assert_eq!(events.len(),5);
    for (i,event) in events.iter_mut().enumerate(){*event=change(*event,20+i as i32);}
    events[0].values=NativeNumberEventValues::SectionStart {page_starts_on:NativePageStartsOn::Odd,page:0,picture:5,table:6,equation:7};
    let prefix="private sequence prefix & <\"'>\t\r\n";
    events[2].values=NativeNumberEventValues::AutoNumber {category:Category::Picture,stored_number:22,format:NativeNumberFormatReplacement::Replace {format:NumberFormat::RomanCapital,user_character:"★",prefix,suffix:".",superscript:true}};
    let mut numbers=request(&state,&events);numbers.document_start.as_mut().ok_or("begin")?.values.picture=20;
    let expected_hash=numbers.canonical_sha256(limits()?)?;let ids=selections(&source)?;let texts=requests(&ids);let values=layouts(&ids);let styles=style_requests(state.frames().frames());
    let candidate=source.prepare_caption_sequence_candidate(&provider,&texts,&values,&styles,&numbers,limits()?,WriterLimits::default(),4)?;
    let receipt=candidate.receipt();assert_eq!(&receipt.content.source,source.receipt());assert_eq!(receipt.requested_sequence_sha256,expected_hash);assert_eq!(receipt.number_sequence.caller_request_sha256,expected_hash);
    assert_eq!(receipt.number_sequence.profile,"hwpx-agent.caption-native-number-stream/output-v2");assert_eq!(receipt.number_sequence.requested_events,5);assert!(receipt.number_sequence.document_start_bound);
    assert_eq!((receipt.content.output.output.changed_parts,receipt.content.output.output.text_changes.len(),receipt.content.output.output.layout_changes.len(),receipt.content.output.style_changes.len()),(2,2,2,6));
    let bytes=candidate.with_verified_bytes(&provider,5,<[u8]>::to_vec)?;
    let output=ImportedDocumentForms::import(ImportedSourcePackage::import(&bytes,DocumentId::parse("stored-literal-document")?,Sha256::digest(&bytes).into(),SourceImportLimits::default())?)?;
    let after=ImportedCaptionSourceState::import(output.body_structure(),limits()?)?;
    assert_eq!(after.numbering().controls().iter().map(|c|c.stored_number).collect::<Vec<_>>(),[21,22,23,24]);
    assert_eq!(after.context().document_start().ok_or("begin")?.picture,20);assert_eq!(after.numbering().section_starts()[0].table,6);
    assert_eq!(after.numbering().controls()[1].format.as_ref().ok_or("format")?.prefix_sha256,<[u8;32]>::from(Sha256::digest(prefix.as_bytes())));
    for (i,frame) in after.frames().frames().iter().enumerate(){assert_eq!(after.frames().plain_text(&frame.segments[0].logical_source_id),Some(texts[i].replacement));}
    let parts=package_parts(&bytes)?;for (path,old) in package_parts(&rig.bytes)?{if !matches!(path.as_str(),"Contents/header.xml"|"Contents/section0.xml"){assert_eq!(parts[&path],old);}}
    let audits=rig.metadata.audit_events()?.len();assert_eq!(candidate.verify(&provider,6)?,*receipt);candidate.with_verified_bytes(&provider,6,|_|())?;assert!(rig.metadata.audit_events()?.len()>audits);
    assert!(matches!(candidate.require_current_product_route(&provider,7),Err(ContentError::RouteUnqualified)));
    assert_eq!(rig.revisions.head(&rig.revision_context,rig.project,rig.branch)?,rig.head);assert_eq!(rig.store.download(&rig.owner,rig.result,8)?,rig.bytes);
    assert!(rig.metadata.audit_events()?[audit_start..].iter().all(|e|matches!(e.event,"artifact.metadata.read"|"artifact.download")));
    assert!(!receipt.issuer_execution_publication_authority&&!receipt.number_sequence.execution_publication_authority&&!receipt.number_sequence.native_counter_interpretation_and_recalculation_qualified);
    let safe=format!("{candidate:?}{numbers:?}{}",serde_json::to_string(receipt)?);for private in ["private-caption.hwpx","private sequence prefix","private new A","private caption service text","literal fixture reader"]{assert!(!safe.contains(private));}Ok(())
}
#[test]
fn stored_caption_sequence_request_digest_binds_noops_values_identity_order_and_format_choice() -> TestResult {
    let rig=sequence_rig(false)?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;
    let state=ImportedCaptionSourceState::import(source.imported().body_structure(),limits()?)?;let events=snapshot(&state)?;let numbers=request(&state,&events);let baseline=numbers.canonical_sha256(limits()?)?;
    let ids=selections(&source)?;let texts=requests(&ids);let candidate=source.prepare_caption_sequence_candidate(&provider,&texts,&[],&[],&numbers,limits()?,WriterLimits::default(),4)?;
    assert!(candidate.receipt().number_sequence.nodes.iter().all(|n|n.changed_attributes==0));assert_eq!(candidate.receipt().requested_sequence_sha256,baseline);
    let mut reversed=events.clone();reversed.reverse();let mut duplicate=events.clone();duplicate[1]=duplicate[0];let mut changed=events.clone();changed[1]=change(changed[1],8);
    let foreign=LogicalId::parse("foreign-sequence-control")?;let mut foreign_id=events.clone();foreign_id[1].source_control_id=&foreign;
    let mut fingerprint=events.clone();fingerprint[1].source_fingerprint_sha256[0]^=1;
    let mut format=events.clone();format[2].values=NativeNumberEventValues::AutoNumber {category:Category::Picture,stored_number:19,format:NativeNumberFormatReplacement::Replace {format:NumberFormat::Digit,user_character:"",prefix:"",suffix:"",superscript:false}};
    let mut category=events.clone();category[2].values=NativeNumberEventValues::AutoNumber {category:Category::Equation,stored_number:19,format:NativeNumberFormatReplacement::Preserve};
    let mut kind=events.clone();kind[2].values=NativeNumberEventValues::Restart {category:Category::Picture,stored_number:19,format:NativeNumberFormatReplacement::Preserve};
    for variant in [reversed,duplicate,changed,foreign_id,fingerprint,format,category,kind] {assert_ne!(request(&state,&variant).canonical_sha256(limits()?)?,baseline);}
    let mut explicit=events.clone();explicit[2].values=NativeNumberEventValues::AutoNumber {category:Category::Picture,stored_number:19,format:NativeNumberFormatReplacement::Replace {format:NumberFormat::Digit,user_character:"",prefix:"",suffix:"",superscript:false}};
    let explicit_hash=request(&state,&explicit).canonical_sha256(limits()?)?;
    for format in [NativeNumberFormatReplacement::Replace {format:NumberFormat::RomanCapital,user_character:"",prefix:"",suffix:"",superscript:false},
        NativeNumberFormatReplacement::Replace {format:NumberFormat::Digit,user_character:"★",prefix:"",suffix:"",superscript:false},
        NativeNumberFormatReplacement::Replace {format:NumberFormat::Digit,user_character:"",prefix:"private prefix",suffix:"",superscript:false},
        NativeNumberFormatReplacement::Replace {format:NumberFormat::Digit,user_character:"",prefix:"",suffix:"private suffix",superscript:false},
        NativeNumberFormatReplacement::Replace {format:NumberFormat::Digit,user_character:"",prefix:"",suffix:"",superscript:true}] {
        let mut variant=explicit.clone();variant[2].values=NativeNumberEventValues::AutoNumber {category:Category::Picture,stored_number:19,format};
        assert_ne!(request(&state,&variant).canonical_sha256(limits()?)?,explicit_hash);
    }
    for values in [NativeNumberEventValues::SectionStart {page_starts_on:NativePageStartsOn::Even,page:0,picture:0,table:3,equation:4},
        NativeNumberEventValues::SectionStart {page_starts_on:NativePageStartsOn::Both,page:1,picture:0,table:3,equation:4},
        NativeNumberEventValues::SectionStart {page_starts_on:NativePageStartsOn::Both,page:0,picture:1,table:3,equation:4},
        NativeNumberEventValues::SectionStart {page_starts_on:NativePageStartsOn::Both,page:0,picture:0,table:4,equation:4},
        NativeNumberEventValues::SectionStart {page_starts_on:NativePageStartsOn::Both,page:0,picture:0,table:3,equation:5}] {
        let mut variant=events.clone();variant[0].values=values;assert_ne!(request(&state,&variant).canonical_sha256(limits()?)?,baseline);
    }
    let mut begin=request(&state,&events);begin.document_start.as_mut().ok_or("begin")?.values.picture=1;assert_ne!(begin.canonical_sha256(limits()?)?,baseline);
    let original=request(&state,&events).document_start.ok_or("begin")?.values;
    for values in [NativeDocumentStartValues {page:original.page+1,..original},NativeDocumentStartValues {footnote:original.footnote+1,..original},
        NativeDocumentStartValues {endnote:original.endnote+1,..original},NativeDocumentStartValues {picture:original.picture+1,..original},
        NativeDocumentStartValues {table:original.table+1,..original},NativeDocumentStartValues {equation:original.equation+1,..original}] {
        let mut variant=request(&state,&events);variant.document_start.as_mut().ok_or("begin")?.values=values;assert_ne!(variant.canonical_sha256(limits()?)?,baseline);
    }
    let mut begin_id=request(&state,&events);begin_id.document_start.as_mut().ok_or("begin")?.source_control_id=&foreign;assert_ne!(begin_id.canonical_sha256(limits()?)?,baseline);
    let mut begin_fp=request(&state,&events);begin_fp.document_start.as_mut().ok_or("begin")?.source_fingerprint_sha256[0]^=1;assert_ne!(begin_fp.canonical_sha256(limits()?)?,baseline);
    let mut stale=request(&state,&events);stale.expected_joined_state_sha256[0]^=1;assert_ne!(stale.canonical_sha256(limits()?)?,baseline);
    let absent=NativeNumberSequenceReplacement {document_start:None,..request(&state,&events)};assert_ne!(absent.canonical_sha256(limits()?)?,baseline);
    let too_many=vec![events[0];hwpx_package::PatchLimits::default().config().max_intents+1];
    assert!(matches!(request(&state,&too_many).canonical_sha256(limits()?),Err(CaptionTextOutputError::Limit)));Ok(())
}
#[test]
fn stored_caption_sequence_acl_revocation_blocks_saved_receipts_proof_and_every_exposure() -> TestResult {
    let rig=sequence_rig(false)?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;let state=ImportedCaptionSourceState::import(source.imported().body_structure(),limits()?)?;
    let mut events=snapshot(&state)?;events[2]=change(events[2],7);let numbers=request(&state,&events);
    let candidate=source.prepare_caption_sequence_candidate(&provider,&[],&[],&[],&numbers,limits()?,WriterLimits::default(),4)?;
    let _receipt=candidate.verify(&provider,4)?;let _proof=source.imported().reconstruct_source_for_verification(&rig.bytes)?;
    rig.store.set_permissions(&rig.owner,rig.result,rig.reader.subject(),BTreeSet::new(),5)?;let called=Cell::new(false);
    assert!(matches!(candidate.with_verified_bytes(&provider,6,|_|called.set(true)),Err(ContentError::Source(_))));assert!(!called.get());
    assert!(matches!(candidate.verify(&provider,6),Err(ContentError::Source(_))));assert!(matches!(candidate.require_current_product_route(&provider,6),Err(ContentError::Source(_))));
    assert!(matches!(source.prepare_caption_sequence_candidate(&provider,&[],&[],&[],&numbers,limits()?,WriterLimits::default(),6),Err(ContentError::Source(_))));Ok(())
}
#[test]
fn stored_caption_sequence_quarantine_or_ciphertext_tamper_never_exposes_partial_output() -> TestResult {
    for quarantine in [false,true] {
        let rig=sequence_rig(false)?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;let state=ImportedCaptionSourceState::import(source.imported().body_structure(),limits()?)?;
        let mut events=snapshot(&state)?;events[2]=change(events[2],7);let numbers=request(&state,&events);let ids=selections(&source)?;let texts=requests(&ids);let styles=style_requests(state.frames().frames());
        let candidate=source.prepare_caption_sequence_candidate(&provider,&texts,&[],&styles,&numbers,limits()?,WriterLimits::default(),4)?;
        if quarantine {rig.store.quarantine(&rig.owner,rig.result,QuarantineReason::parse("CAPTION_SEQUENCE_FIXTURE_QUARANTINE")?,5)?;}else{rig.blob.tamper.store(true,Ordering::SeqCst);}
        let called=Cell::new(false);assert!(matches!(candidate.with_verified_bytes(&provider,6,|_|called.set(true)),Err(ContentError::Source(_))));assert!(!called.get());
        assert!(candidate.verify(&provider,6).is_err());assert!(candidate.require_current_product_route(&provider,6).is_err());
        assert!(source.prepare_caption_sequence_candidate(&provider,&texts,&[],&styles,&numbers,limits()?,WriterLimits::default(),6).is_err());
    }Ok(())
}
#[test]
fn stored_caption_sequence_foreign_scope_and_last_writer_head_boundary_block_consumer() -> TestResult {
    let rig=sequence_rig(false)?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;let state=ImportedCaptionSourceState::import(source.imported().body_structure(),limits()?)?;
    let mut events=snapshot(&state)?;events[2]=change(events[2],7);let numbers=request(&state,&events);
    let candidate=source.prepare_caption_sequence_candidate(&provider,&[],&[],&[],&numbers,limits()?,WriterLimits::default(),4)?;
    let foreign=StoredFormProvider::bind(&rig.store,&rig.revisions,&rig.reader,&rig.revision_context,rig.project,rig.branch,DocumentId::parse("foreign-caption-sequence-document")?)?;
    let called=Cell::new(false);assert!(candidate.with_verified_bytes(&foreign,5,|_|called.set(true)).is_err());assert!(!called.get());assert!(candidate.verify(&foreign,5).is_err());assert!(candidate.require_current_product_route(&foreign,5).is_err());
    assert!(source.prepare_caption_sequence_candidate(&foreign,&[],&[],&[],&numbers,limits()?,WriterLimits::default(),5).is_err());
    let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),rig.project,rig.branch,rig.head,rev::RevisionId::generate(),rig.head.revision_id().into_iter().collect(),StoredArtifactId::generate(),rig.result,None,
        ContentDigest::of(b"sequence boundary fixture advance"),rev::RevisionValidationState::Verified,ContentDigest::of(b"sequence boundary validation"),ContentDigest::of(b"sequence boundary transaction"))?;
    let boundary=rev::RevisionService::new(BoundaryRepo {inner:rig.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:rig.revision_context.clone(),advance});
    let bound=StoredFormProvider::bind(&rig.store,&boundary,&rig.reader,&rig.revision_context,rig.project,rig.branch,DocumentId::parse("stored-literal-document")?)?;
    boundary.repository().calls.store(0,Ordering::SeqCst);candidate.with_verified_bytes(&bound,5,|_|())?;let reads=boundary.repository().calls.load(Ordering::SeqCst);assert!(reads>=4);
    boundary.repository().calls.store(0,Ordering::SeqCst);boundary.repository().trigger.store(reads,Ordering::SeqCst);let called=Cell::new(false);
    assert!(matches!(candidate.with_verified_bytes(&bound,6,|_|called.set(true)),Err(ContentError::Source(_))));assert!(!called.get());assert_eq!(boundary.repository().calls.load(Ordering::SeqCst),reads);
    assert!(candidate.verify(&provider,6).is_err());assert!(candidate.require_current_product_route(&provider,6).is_err());
    assert!(source.prepare_caption_sequence_candidate(&provider,&[],&[],&[],&numbers,limits()?,WriterLimits::default(),6).is_err());Ok(())
}
#[test]
fn stored_caption_sequence_incomplete_stale_invalid_noop_protected_and_limited_requests_reject() -> TestResult {
    let rig=sequence_rig(false)?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;let state=ImportedCaptionSourceState::import(source.imported().body_structure(),limits()?)?;
    let events=snapshot(&state)?;let mut duplicate=events.clone();duplicate[1]=duplicate[0];let mut reverse=events.clone();reverse.reverse();let mut stale=events.clone();stale[2].source_fingerprint_sha256[0]^=1;
    let mut wrong_kind=events.clone();wrong_kind[2].values=NativeNumberEventValues::Restart {category:Category::Picture,stored_number:7,format:NativeNumberFormatReplacement::Preserve};
    for variant in [events[..4].to_vec(),duplicate,reverse,stale,wrong_kind] {
        assert!(matches!(source.prepare_caption_sequence_candidate(&provider,&[],&[],&[],&request(&state,&variant),limits()?,WriterLimits::default(),4),Err(ContentError::Output(CaptionTextOutputError::Selection))));
    }
    let numbers=request(&state,&events);assert!(matches!(source.prepare_caption_sequence_candidate(&provider,&[],&[],&[],&numbers,limits()?,WriterLimits::default(),4),Err(ContentError::Output(CaptionTextOutputError::NoChange))));
    let mut stale_join=request(&state,&events);stale_join.expected_joined_state_sha256[0]^=1;
    assert!(matches!(source.prepare_caption_sequence_candidate(&provider,&[],&[],&[],&stale_join,limits()?,WriterLimits::default(),4),Err(ContentError::Output(CaptionTextOutputError::Source))));
    let mut invalid=events.clone();invalid[2].values=NativeNumberEventValues::AutoNumber {category:Category::Picture,stored_number:7,format:NativeNumberFormatReplacement::Replace {format:NumberFormat::Digit,user_character:"",prefix:"bad\0",suffix:"",superscript:false}};
    assert!(matches!(source.prepare_caption_sequence_candidate(&provider,&[],&[],&[],&request(&state,&invalid),limits()?,WriterLimits::default(),4),Err(ContentError::Output(CaptionTextOutputError::Value))));
    let mut changed=events.clone();changed[2]=change(changed[2],7);let numbers=request(&state,&changed);
    let tiny=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {items_per_kind:1,..Default::default()})?;
    assert!(matches!(source.prepare_caption_sequence_candidate(&provider,&[],&[],&[],&numbers,tiny,WriterLimits::default(),4),Err(ContentError::State(StateError::Limit))));
    assert!(matches!(source.prepare_caption_sequence_candidate(&provider,&[],&[],&[],&numbers,limits()?,WriterLimits::new(hwpx_package::WriterLimitConfig {max_output_bytes:1})?,4),Err(ContentError::Output(CaptionTextOutputError::Writer))));
    let rig=sequence_rig(true)?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;let state=ImportedCaptionSourceState::import(source.imported().body_structure(),limits()?)?;let mut events=snapshot(&state)?;
    events[4]=change(events[4],7);let numbers=request(&state,&events);
    assert!(matches!(source.prepare_caption_sequence_candidate(&provider,&[],&[],&[],&numbers,limits()?,WriterLimits::default(),4),Err(ContentError::Output(CaptionTextOutputError::Protection))));Ok(())
}
