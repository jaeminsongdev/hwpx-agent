//! Strict public note-file envelopes over real in-memory services, not Native.
use super::*;
use super::field_ranges::fixture;
use hwpx_agent_cli::form_product_request::stored_note_file::{StoredNoteFileProductRequest as Product,
    NoteFileProductError as E,NOTE_FILE_PRODUCT_REQUEST_SCHEMA,NOTE_FILE_PRODUCT_MAX_REQUEST_BYTES};
use hwpx_agent_cli::form_stored_provider::actual_import::note_export_output::StoredNoteFileError;
use hwpx_package::{NoteHwpxLimits,NoteHwpxLimitConfig,WriterLimits,WriterLimitConfig};
use serde_json::{json,Value};
use std::{cell::Cell,fs,io::Write as _,sync::atomic::AtomicUsize};
use revision_service as rev;
#[path="../../../../hwpx-package/tests/support/document_import_note_fixture.rs"] mod legacy_notes;

macro_rules! write_provider {($s:ident,$actor:ident,$provider:ident)=>{
    let $actor=RequestContext::new($s.reader.tenant_id(),$s.reader.subject(),[AuthScope::DocumentRead,AuthScope::DocumentWrite]);
    let $provider=StoredFormProvider::bind(&$s.artifacts,&$s.revisions,&$actor,&$s.revision_context,$s.project,$s.branch,DocumentId::parse("actual-form-document")?)?;
}}
fn limits()->NoteHwpxLimits {NoteHwpxLimits::new(Default::default()).expect("finite defaults")}
fn bytes(families:&[&str])->Result<Vec<u8>,Box<dyn std::error::Error>> {
    let notes:String=families.iter().enumerate().map(|(i,kind)|format!("<hp:ctrl><hp:{kind} instId='101'><hp:subList><hp:p id='{}'><hp:run><hp:t>COLLECTED-{i}</hp:t></hp:run></hp:p></hp:subList></hp:{kind}></hp:ctrl>",i+11)).collect();
    fixture::package(&format!("<hp:p id='1'><hp:run><hp:secPr><hp:startNum pageStartsOn='BOTH' page='0' pic='1' tbl='1' equation='1'/></hp:secPr><hp:t>PRIVATE-NOT-COLLECTED</hp:t>{notes}</hp:run></hp:p>"))
}
fn envelope(s:&StoredFixture,bytes:&[u8],selection:&str)->Result<Value,Box<dyn std::error::Error>> {
    Ok(json!({"schema_version":NOTE_FILE_PRODUCT_REQUEST_SCHEMA,"idempotency_key":"PRIVATE-NOTE-REQUEST-KEY",
        "project_id":s.project.public_id(),"document_id":"actual-form-document","base_revision":s.head.revision_id().ok_or("head")?.public_id(),
        "expected_head_generation":s.head.generation(),"expected_source_package_sha256":ContentDigest::of(bytes).hex(),
        "plan_id":"note-file-request-plan","operation":{"kind":"export_note_file","selection":selection}}))
}
#[test]
fn note_file_product_api_source_json_prepares_owned_files_for_all_families_without_caller_import_or_commit()->TestResult {
    use hwpx_agent_cli::reference_validation_product::ReferenceValidationProductOperation as SourceApi;
    for kinds in [&["footNote"][..],&["endNote"][..],&["endNote","footNote"][..]] {
        let raw=bytes(kinds)?;let stored=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(stored,actor,provider);
        let cap=domain_ir::ReferenceAuxiliaryLimits::new(Default::default())?;
        let assessment=SourceApi::assess_package_source(&raw,DocumentId::parse("actual-form-document")?,*ContentDigest::of(&raw).as_bytes(),SourceImportLimits::default(),cap)?;
        let api:Value=serde_json::from_slice(&assessment.canonical_json(cap)?)?;
        assert_eq!(api["schema_version"],"hwpx-agent.product.reference-source-assessment/v13");assert!(assessment.validation_report().is_none());
        let sha:[u8;32]=serde_json::from_value(api["source"]["source_package_sha256"].clone())?;
        for selection in ["footnotes","endnotes","both"] {
            let expected=kinds.iter().filter(|k|selection=="both"||selection=="footnotes"&&**k=="footNote"||selection=="endnotes"&&**k=="endNote").count();
            let mut request=envelope(&stored,&raw,selection)?;request["expected_source_package_sha256"]=json!(hex::encode(sha));
            let result=Product::prepare_json(&provider,&serde_json::to_vec(&request)?,limits(),WriterLimits::default(),4);
            if expected==0 {assert!(result.is_err());continue;}
            let candidate=result?;assert_eq!(candidate.verify(&provider,5)?.stored.output.selected_notes,expected);
            assert!(!candidate.receipt().idempotency_key_claimed&&!candidate.receipt().issuer_native_cas_execution_publication_authority);
            assert!(candidate.receipt().stored.output.non_body_metadata_and_resources_may_contain_source_data);
            let temp=tempfile::tempdir()?;let path=temp.path().join("collected.hwpx");
            candidate.with_verified_bytes(&provider,5,|output|->TestResult {let mut file=fs::OpenOptions::new().write(true).create_new(true).open(&path)?;file.write_all(output)?;file.sync_all()?;Ok(())})??;
            assert!(fixture::forms(&fs::read(path)?,"collected")?.notes().is_empty());
            assert!(!format!("{candidate:?}").contains("PRIVATE"));assert!(matches!(candidate.require_current_product_route(&provider,5),Err(E::RouteUnqualified)));
        }
        assert_eq!(stored.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);
        assert_eq!(stored.revisions.head(&stored.revision_context,stored.project,stored.branch)?,stored.head);
    }Ok(())
}
#[test]
fn note_file_product_canonical_raw_key_plan_family_and_scope_bindings_are_not_idempotency_claims()->TestResult {
    let raw=bytes(&["footNote"])?;let stored=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(stored,actor,provider);
    let request=envelope(&stored,&raw,"footnotes")?;
    let a=Product::prepare_json(&provider,&serde_json::to_vec(&request)?,limits(),WriterLimits::default(),4)?;
    let b=Product::prepare_json(&provider,&serde_json::to_vec_pretty(&request)?,limits(),WriterLimits::default(),4)?;
    assert_ne!(a.receipt().raw_request_sha256,b.receipt().raw_request_sha256);
    assert_eq!(a.receipt().canonical_request_sha256,b.receipt().canonical_request_sha256);assert_eq!(a.receipt().scoped_request_sha256,b.receipt().scoped_request_sha256);
    for (key,value) in [("idempotency_key",json!("PRIVATE-OTHER-KEY")),("plan_id",json!("another-note-plan"))] {
        let mut other=request.clone();other[key]=value;let c=Product::prepare_json(&provider,&serde_json::to_vec(&other)?,limits(),WriterLimits::default(),4)?;
        assert_ne!(a.receipt().canonical_request_sha256,c.receipt().canonical_request_sha256);assert_ne!(a.receipt().scoped_request_sha256,c.receipt().scoped_request_sha256);
        assert_eq!(a.receipt().stored.output.output_package_sha256,c.receipt().stored.output.output_package_sha256);assert!(!c.receipt().idempotency_key_claimed);
    }
    let mut both=request.clone();both["operation"]["selection"]=json!("both");let c=Product::prepare_json(&provider,&serde_json::to_vec(&both)?,limits(),WriterLimits::default(),4)?;
    assert_eq!(a.with_verified_bytes(&provider,5,<[u8]>::to_vec)?,c.with_verified_bytes(&provider,5,<[u8]>::to_vec)?);
    assert_ne!(a.receipt().stored.requested_sha256,c.receipt().stored.requested_sha256);
    let mut forged=a.receipt().clone();forged.idempotency_key_claimed=true;forged.issuer_native_cas_execution_publication_authority=true;
    assert_ne!(a.verify(&provider,5)?,forged);assert_eq!(stored.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);Ok(())
}
#[test]
fn note_file_product_malformed_duplicate_unknown_and_nonobject_envelopes_fail_before_artifact_reads()->TestResult {
    let raw=bytes(&["footNote"])?;let stored=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(stored,actor,provider);
    let request=envelope(&stored,&raw,"both")?;let good=serde_json::to_string(&request)?;let before=stored.metadata.audit_events()?.len();
    let mut invalid=vec!["null".into(),"[]".into(),format!("{good} {{}}"),format!("{{\"schema_version\":\"bad\",{}",&good[1..]),good.replace("\"selection\":\"both\"","\"selection\":\"both\",\"select\\u0069on\":\"both\"")];
    for key in ["schema_version","idempotency_key","project_id","document_id","base_revision","expected_head_generation","expected_source_package_sha256","plan_id","operation"] {
        let mut v=request.clone();v.as_object_mut().ok_or("map")?.remove(key);invalid.push(serde_json::to_string(&v)?);
    }
    for (key,value) in [("schema_version",json!("hwpx-agent.product-operation-request/v2")),("expected_head_generation",json!(0)),
        ("expected_source_package_sha256",json!("A".repeat(64))),("operation",json!(["export_note_file","both"])),("output_path",json!("D:/do-not-write.hwpx")),
        ("approved",json!(true)),("limits",json!({})),("document_id",json!("x".repeat(1025)))] {
        let mut v=request.clone();v[key]=value;invalid.push(serde_json::to_string(&v)?);
    }
    for op in [json!({"kind":"prepare_export","selection":"both"}),json!({"kind":"export_note_file","selection":"all"}),
        json!({"kind":"export_note_file","selection":"both","native_qualified":true}),json!({"kind":"export_note_file"})] {
        let mut v=request.clone();v["operation"]=op;invalid.push(serde_json::to_string(&v)?);
    }
    let seq=Value::Array(request.as_object().ok_or("request")?.values().cloned().collect());invalid.push(serde_json::to_string(&seq)?);
    for bad in invalid {assert!(matches!(Product::prepare_json(&provider,bad.as_bytes(),limits(),WriterLimits::default(),4),Err(E::Request)));}
    assert_eq!(stored.metadata.audit_events()?.len(),before);
    let mut exact=good.into_bytes();exact.resize(NOTE_FILE_PRODUCT_MAX_REQUEST_BYTES,b' ');Product::prepare_json(&provider,&exact,limits(),WriterLimits::default(),4)?;
    exact.push(b' ');assert!(matches!(Product::prepare_json(&provider,&exact,limits(),WriterLimits::default(),4),Err(E::Limit)));
    assert!(matches!(Product::prepare_json(&provider,b"",limits(),WriterLimits::default(),4),Err(E::Limit)));Ok(())
}
#[test]
fn note_file_product_requires_write_scope_and_rejects_foreign_bindings_head_and_source()->TestResult {
    let raw=bytes(&["footNote"])?;let stored=StoredFixture::new(&raw,ArtifactKind::Result,false)?;let reader=stored.provider()?;
    let request=envelope(&stored,&raw,"both")?;let wire=serde_json::to_vec(&request)?;let before=stored.metadata.audit_events()?.len();
    assert!(matches!(Product::prepare_json(&reader,&wire,limits(),WriterLimits::default(),4),Err(E::Stored(StoredNoteFileError::Permission))));assert_eq!(stored.metadata.audit_events()?.len(),before);
    write_provider!(stored,actor,provider);let candidate=Product::prepare_json(&provider,&wire,limits(),WriterLimits::default(),4)?;
    let called=Cell::new(false);assert!(matches!(candidate.with_verified_bytes(&reader,5,|_|called.set(true)),Err(E::Stored(StoredNoteFileError::Permission))));assert!(!called.get());assert!(candidate.verify(&reader,5).is_err());
    for (key,value) in [("project_id",json!("prj_70000000000000000000000000000002")),("document_id",json!("other-document")),
        ("base_revision",json!(rev::RevisionId::generate().public_id())),("expected_head_generation",json!(stored.head.generation()+1)),("expected_source_package_sha256",json!("0".repeat(64)))] {
        let mut wrong=request.clone();wrong[key]=value;assert!(Product::prepare_json(&provider,&serde_json::to_vec(&wrong)?,limits(),WriterLimits::default(),5).is_err());
    }
    for variant in 0..5 {
        let tenant=if variant==4 {TenantId::new(uuid::Uuid::from_u128(702))?}else{stored.reader.tenant_id()};let subject=if variant==3 {stored.owner.subject()}else{stored.reader.subject()};
        let actor=RequestContext::new(tenant,subject,[AuthScope::DocumentRead,AuthScope::DocumentWrite]);let context=rev::RevisionRequestContext::new(tenant,subject);
        let project=if variant==2 {rev::ProjectId::parse("prj_70000000000000000000000000000002")?}else{stored.project};
        let branch=if variant==1 {rev::BranchId::parse("brn_70000000000000000000000000000002")?}else{stored.branch};
        let document=DocumentId::parse(if variant==0 {"other-document"}else{"actual-form-document"})?;
        let other=StoredFormProvider::bind(&stored.artifacts,&stored.revisions,&actor,&context,project,branch,document)?;
        assert!(candidate.with_verified_bytes(&other,5,|_|called.set(true)).is_err());assert!(!called.get());assert!(candidate.verify(&other,5).is_err());
    }Ok(())
}
#[test]
fn note_file_product_revoked_acl_quarantine_aead_and_retained_receipts_do_not_grant_output()->TestResult {
    for mode in 0..3 {
        let raw=bytes(&["footNote"])?;let stored=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(stored,actor,provider);
        let wire=serde_json::to_vec(&envelope(&stored,&raw,"both")?)?;let candidate=Product::prepare_json(&provider,&wire,limits(),WriterLimits::default(),4)?;let _receipt=candidate.verify(&provider,4)?;
        match mode {0=>{stored.artifacts.set_permissions(&stored.owner,stored.result,stored.reader.subject(),BTreeSet::new(),5)?;},
            1=>{stored.artifacts.quarantine(&stored.owner,stored.result,artifact_service::QuarantineReason::parse("NOTE_FILE_PRODUCT_TEST_QUARANTINE")?,5)?;},
            _=>stored.blobs.tamper.store(true,Ordering::SeqCst)};
        let called=Cell::new(false);assert!(candidate.with_verified_bytes(&provider,6,|_|called.set(true)).is_err());assert!(!called.get());assert!(candidate.verify(&provider,6).is_err());
        assert!(candidate.require_current_product_route(&provider,6).is_err());assert!(Product::prepare_json(&provider,&wire,limits(),WriterLimits::default(),6).is_err());
        if mode==0 {stored.artifacts.set_permissions(&stored.owner,stored.result,stored.reader.subject(),BTreeSet::from([artifact_service::ArtifactPermission::Read]),7)?;candidate.verify(&provider,8)?;}
    }Ok(())
}
struct BoundaryRepo {inner:rev::InMemoryRevisionRepository,calls:AtomicUsize,trigger:AtomicUsize,context:rev::RevisionRequestContext,advance:rev::RevisionCommitRequest}
impl rev::RevisionRepository for BoundaryRepo {
    fn compare_and_swap(&self,c:&rev::RevisionRequestContext,r:&rev::RevisionCommitRequest)->Result<rev::CommitOutcome,rev::RevisionError>{self.inner.compare_and_swap(c,r)}
    fn head(&self,t:TenantId,p:rev::ProjectId,b:rev::BranchId)->Result<rev::RevisionHead,rev::RevisionError>{let call=self.calls.fetch_add(1,Ordering::SeqCst)+1;if call==self.trigger.load(Ordering::SeqCst){assert!(matches!(self.inner.compare_and_swap(&self.context,&self.advance)?,rev::CommitOutcome::Committed(_)));}self.inner.head(t,p,b)}
    fn node(&self,t:TenantId,p:rev::ProjectId,r:rev::RevisionId)->Result<rev::RevisionNode,rev::RevisionError>{self.inner.node(t,p,r)}
}
#[test]
fn note_file_product_prepare_verify_and_final_consumer_head_races_discard_candidates()->TestResult {
    for stage in 0..3 {
        let raw=bytes(&["footNote"])?;let stored=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(stored,actor,provider);
        let wire=serde_json::to_vec(&envelope(&stored,&raw,"both")?)?;let candidate=Product::prepare_json(&provider,&wire,limits(),WriterLimits::default(),4)?;
        let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),stored.project,stored.branch,stored.head,rev::RevisionId::generate(),stored.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),stored.result,None,ContentDigest::of(b"note request race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation fixture"),ContentDigest::of(b"transaction fixture"))?;
        let boundary=rev::RevisionService::new(BoundaryRepo {inner:stored.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:stored.revision_context.clone(),advance});
        let bound=StoredFormProvider::bind(&stored.artifacts,&boundary,&actor,&stored.revision_context,stored.project,stored.branch,DocumentId::parse("actual-form-document")?)?;
        boundary.repository().calls.store(0,Ordering::SeqCst);
        match stage {0=>{Product::prepare_json(&bound,&wire,limits(),WriterLimits::default(),5)?;},1=>{candidate.verify(&bound,5)?;},_=>{candidate.with_verified_bytes(&bound,5,|_|())?;}}
        let reads=boundary.repository().calls.load(Ordering::SeqCst);assert!(reads>=4);boundary.repository().calls.store(0,Ordering::SeqCst);boundary.repository().trigger.store(reads,Ordering::SeqCst);
        let called=Cell::new(false);match stage {0=>assert!(Product::prepare_json(&bound,&wire,limits(),WriterLimits::default(),6).is_err()),1=>assert!(candidate.verify(&bound,6).is_err()),_=>assert!(candidate.with_verified_bytes(&bound,6,|_|called.set(true)).is_err())}
        assert!(!called.get());assert_eq!(boundary.repository().calls.load(Ordering::SeqCst),reads);assert!(candidate.verify(&provider,7).is_err());
    }Ok(())
}
#[test]
fn note_file_product_empty_protected_and_bounded_outputs_keep_original_fail_closed()->TestResult {
    let raw=bytes(&["footNote"])?;let stored=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(stored,actor,provider);
    let wire=serde_json::to_vec(&envelope(&stored,&raw,"both")?)?;let tight=NoteHwpxLimits::new(NoteHwpxLimitConfig {payload_bytes:1,..Default::default()})?;
    assert!(Product::prepare_json(&provider,&wire,tight,WriterLimits::default(),4).is_err());assert!(Product::prepare_json(&provider,&wire,limits(),WriterLimits::new(WriterLimitConfig {max_output_bytes:1})?,4).is_err());
    for data in [bytes(&[])?,fixture::package("<hp:p id='1'><hp:run><hp:ctrl><hp:footNote instId='101'><hp:subList lock='1'><hp:p id='11'><hp:run><hp:t>LOCKED</hp:t></hp:run></hp:p></hp:subList></hp:footNote></hp:ctrl></hp:run></hp:p>")?] {
        let store=StoredFixture::new(&data,ArtifactKind::Result,false)?;write_provider!(store,actor,access);let wire=serde_json::to_vec(&envelope(&store,&data,"both")?)?;
        assert!(Product::prepare_json(&access,&wire,limits(),WriterLimits::default(),4).is_err());
    }Ok(())
}
#[test]
fn note_file_product_historical_nine_keep_six_exports_three_original_id_failures_and_native_status()->TestResult {
    let(mut exported,mut rejected)=(0usize,0usize);let mut lanes=[0usize;3];
    for input in legacy_notes::actual_inputs()? {
        lanes[match input.lane {"generated"=>0,"saved"=>1,"reopened"=>2,_=>return Err("lane".into())}]+=1;
        let stored=StoredFixture::new(&input.bytes,ArtifactKind::Result,false)?;write_provider!(stored,actor,provider);
        let result=Product::prepare_json(&provider,&serde_json::to_vec(&envelope(&stored,&input.bytes,"both")?)?,limits(),WriterLimits::default(),4);
        if input.expected_notes==2 {assert!(matches!(result,Err(E::Stored(StoredNoteFileError::Output(hwpx_package::document_import::structure::note_export::NoteFileExportError::Trust("id_index_validation_failed"))))));rejected+=1;}
        else {let candidate=result?;assert!(fixture::forms(&candidate.with_verified_bytes(&provider,5,<[u8]>::to_vec)?,"exported")?.notes().is_empty());exported+=1;}
        assert_eq!(stored.revisions.head(&stored.revision_context,stored.project,stored.branch)?,stored.head);
    }assert_eq!((exported,rejected),(6,3));assert_eq!(lanes,[3,3,3]);Ok(())
}
#[test]
fn note_file_product_inherited_xml_context_reaches_guarded_output_and_acl_revocation_still_blocks()->TestResult {
    let raw=fixture::package("<hp:p id='1' xml:lang='en'><hp:run xml:space='preserve'><hp:ctrl><hp:footNote instId='101'><hp:subList xml:lang='fr' xml:space='default'><hp:p id='11'><hp:run><hp:t>BODY</hp:t></hp:run></hp:p></hp:subList></hp:footNote></hp:ctrl></hp:run></hp:p>")?;
    let stored=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(stored,actor,provider);
    let candidate=Product::prepare_json(&provider,&serde_json::to_vec(&envelope(&stored,&raw,"both")?)?,limits(),WriterLimits::default(),4)?;
    let output=candidate.with_verified_bytes(&provider,5,<[u8]>::to_vec)?;
    let mut zip=hwpx_package::BoundedZipReader::open(std::io::Cursor::new(&output),hwpx_package::PackageLimits::default())?;
    let i=zip.entries().iter().position(|e|e.path.as_str()=="Contents/section0.xml").ok_or("section")?;
    let section=zip.read_entry(i)?;let xml=hwpx_package::PreservingXmlDocument::parse(&section)?;
    let p=xml.elements().iter().find(|n|n.name().local_name()=="p").ok_or("paragraph")?;
    for (name,value) in [("lang","fr"),("space","default")] {
        let attribute=p.attributes().iter().find(|a|a.name().namespace()==Some("http://www.w3.org/XML/1998/namespace")&&a.name().local_name()==name).ok_or("XML context attribute")?;
        let span=attribute.value_span();assert_eq!(section.get(span.start()..span.end()),Some(value.as_bytes()));
    }
    assert!(fixture::forms(&output,"collected")?.notes().is_empty());assert!(!candidate.receipt().stored.output.note_container_layout_and_native_numbering_qualified);
    stored.artifacts.set_permissions(&stored.owner,stored.result,stored.reader.subject(),BTreeSet::new(),6)?;
    let called=Cell::new(false);assert!(candidate.with_verified_bytes(&provider,7,|_|called.set(true)).is_err());assert!(!called.get());Ok(())
}
#[test]
fn note_file_product_inherited_intermediate_base_remains_explicitly_unqualified()->TestResult {
    let raw=fixture::package("<hp:p id='1'><hp:run><hp:ctrl><hp:footNote instId='101'><hp:subList xml:base='assets/'><hp:p id='11'><hp:run><hp:t>BODY</hp:t></hp:run></hp:p></hp:subList></hp:footNote></hp:ctrl></hp:run></hp:p>")?;
    let stored=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(stored,actor,provider);
    assert!(matches!(Product::prepare_json(&provider,&serde_json::to_vec(&envelope(&stored,&raw,"both")?)?,limits(),WriterLimits::default(),4),
        Err(E::Stored(StoredNoteFileError::Output(hwpx_package::document_import::structure::note_export::NoteFileExportError::InheritedContext)))));
    assert_eq!(stored.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);
    assert_eq!(stored.revisions.head(&stored.revision_context,stored.project,stored.branch)?,stored.head);Ok(())
}
