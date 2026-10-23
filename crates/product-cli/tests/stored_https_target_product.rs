//! Synthetic repository/scanner authority; real service ACL/AEAD, source parsing and writer.
#[path="support/stored_https_compiler.rs"]mod compiled;
#[path="support/stored_https_request.rs"]mod requests;
#[path="support/stored_https_storage.rs"]mod storage;
#[path="support/stored_https_coordinator.rs"]mod coordinator;
#[path="support/stored_https_dispatch.rs"]mod dispatch;
use domain_ir::{DocumentId,ExternalLinkPolicy};
use std::{error::Error,sync::{Mutex,atomic::AtomicUsize}};
type TestResult=Result<(),Box<dyn Error>>;
include!("support/stored_source_fixture.rs");
#[path="../../hwpx-package/tests/source_https_target_changes.rs"]mod source_support;
use source_support::{fixture,limits,target_limits,target,policy,link,output_uris};
use hwpx_agent_cli::{form_stored_provider::actual_import::{StoredImportedDocumentForms,https_target_output::*},
    reference_validation_product::{ReferenceValidationProductOperation as Product,source_field_semantics::ReferenceSourceMeaningSelection}};
use hwpx_agent_cli::form_stored_provider::actual_import::source_policy::SourcePolicyBinding;
use hwpx_package::{WriterLimits,document_import::{SourceImportLimits,fields::semantics::source_index::https_targets::{SourceHttpsTargetChange,SourceHttpsTargetError}}};
use sha2::{Digest as _,Sha256};
type E=StoredHttpsTargetError;
struct Repository{row:Mutex<HttpsTargetPolicyVersion>,subject:SubjectDigest,calls:AtomicUsize,deny_after:AtomicUsize,tamper:Option<Arc<AtomicBool>>}
impl HttpsTargetPolicyRepository for Repository{
    fn read_current(&self,s:&HttpsTargetPolicyScope)->Result<HttpsTargetPolicyVersion,E>{
        let n=self.calls.fetch_add(1,Ordering::SeqCst);
        if n>=self.deny_after.load(Ordering::SeqCst)||s.subject()!=self.subject{return Err(E::Repository);}
        let row=self.row.lock().map_err(|_|E::Repository)?.clone();
        // Deliberately return foreign bindings in the binding matrix to test the consumer.
        assert_eq!(s.tenant(),TenantId::new(Uuid::from_u128(451)).map_err(|_|E::Repository)?);
        if let Some(flag)=&self.tamper{flag.store(true,Ordering::SeqCst);}
        Ok(row)
    }
}
fn write_context(f:&StoredFixture)->RequestContext{RequestContext::new(f.reader.tenant_id(),f.reader.subject(),[AuthScope::DocumentRead,AuthScope::DocumentWrite])}
fn writable<'a>(f:&'a StoredFixture,c:&'a RequestContext)->Result<Provider<'a>,StoredFormError>{
    StoredFormProvider::bind(&f.artifacts,&f.revisions,c,&f.revision_context,f.project,f.branch,DocumentId::parse("actual-form-document").map_err(|_|StoredFormError::Scope)?)
}
fn binding(f:&StoredFixture,source:&StoredImportedDocumentForms)->Result<SourcePolicyBinding,Box<dyn Error>>{
    let r=&source.receipt().imported;
    Ok(SourcePolicyBinding{tenant:f.reader.tenant_id(),project:f.project,branch:f.branch,document:DocumentId::parse("actual-form-document")?,
        source_revision:f.head.revision_id().ok_or("head")?,source_head_generation:f.head.generation(),source_result_artifact:f.result,
        source_package_sha256:ContentDigest::parse(&hex::encode(r.source_package_sha256))?,source_provenance_sha256:ContentDigest::parse(&hex::encode(r.source_provenance_sha256))?,
        observed_graph_sha256:ContentDigest::parse(&hex::encode(r.graph_sha256))?,policy_version:Uuid::from_u128(527),policy_generation:1,creator_subject:f.owner.subject()})
}
fn payload(b:&SourcePolicyBinding,p:&ExternalLinkPolicy)->serde_json::Value{serde_json::json!({"schema_version":HTTPS_TARGET_POLICY_SCHEMA,"binding":b,"policy":p})}
fn repository(f:&StoredFixture,b:SourcePolicyBinding,bytes:Vec<u8>,kind:ArtifactKind,media:&str)->Result<Repository,Box<dyn Error>>{
    let d=f.artifacts.ingest(&f.owner,IngestRequest{bytes,media_type:MediaType::parse(media)?,file_name:FileName::parse("https-policy.json")?,kind},7)?;
    f.artifacts.set_permissions(&f.owner,d.artifact_id,f.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),8)?;
    Ok(Repository{row:Mutex::new(HttpsTargetPolicyVersion{binding:b,artifact:d.artifact_id,digest:d.sha256}),subject:f.reader.subject(),
        calls:AtomicUsize::new(0),deny_after:AtomicUsize::new(usize::MAX),tamper:None})
}
fn repo(f:&StoredFixture,s:&StoredImportedDocumentForms,p:&ExternalLinkPolicy)->Result<Repository,Box<dyn Error>>{
    let b=binding(f,s)?;repository(f,b.clone(),serde_json::to_vec(&payload(&b,p))?,ArtifactKind::Evidence,HTTPS_TARGET_POLICY_MEDIA_TYPE)
}
fn selections(bytes:&[u8])->Result<Vec<ReferenceSourceMeaningSelection>,Box<dyn Error>>{
    Ok(Product::assess_package_field_semantics(bytes,DocumentId::parse("actual-form-document")?,Sha256::digest(bytes).into(),SourceImportLimits::default(),limits()?)?.selections().to_vec())
}
fn request<'a>(s:&'a ReferenceSourceMeaningSelection,t:&'a domain_ir::HyperlinkTarget)->SourceHttpsTargetChange<'a>{
    SourceHttpsTargetChange{reference_id:&s.reference_id,expected_source_field_sha256:s.source_field_sha256,expected_meaning_sha256:s.meaning_sha256,target:t}
}
#[test]
fn captured_source_actual_encrypted_policy_and_output_readback_do_not_publish()->TestResult{
    let bytes=fixture::captured()?;let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let c=write_context(&f);let provider=writable(&f,&c)?;
    let source=provider.import_actual_forms(f.head,9)?;let t=target("https://example.org/stored?x=1&y=2");let selected=selections(&bytes)?;
    let repository=repo(&f,&source,&policy(&[&t])?)?;
    let candidate=source.prepare_https_target_candidate(&provider,&repository,&[request(&selected[0],&t)],limits()?,target_limits()?,WriterLimits::default(),10)?;
    assert_eq!(candidate.verify(&provider,&repository,11)?,candidate.receipt());
    let output=candidate.with_verified_bytes(&provider,&repository,12,|b|b.to_vec())?;
    assert_eq!(output_uris(&output,"actual-form-document")?,vec![Some("https://example.org/stored?x=1&y=2".into())]);
    assert!(!candidate.receipt().execution_or_publication_authority);
    assert!(matches!(candidate.require_current_product_route(&provider,&repository,13),Err(E::RouteUnqualified)));
    assert_eq!(f.artifacts.download(&f.reader,f.result,14)?,bytes);
    assert_eq!(f.revisions.head(&f.revision_context,f.project,f.branch)?,f.head);
    assert_eq!(f.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),3);
    for s in [serde_json::to_string(candidate.receipt())?,format!("{candidate:?}"),format!("{:?}",repository.row.lock().map_err(|_|"row")?) ]{assert!(!s.contains("https://")&&!s.contains("PRIVATE"));}
    Ok(())
}
#[test]
fn stored_batch_preserves_unselected_field_and_rejects_one_unapproved_member_atomically()->TestResult{
    let bytes=fixture::package(&(link(1,"https://example.org/old1")+&link(2,"https://example.org/keep")+&link(3,"https://example.org/old3")))?;
    let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let c=write_context(&f);let provider=writable(&f,&c)?;let source=provider.import_actual_forms(f.head,9)?;
    let selected=selections(&bytes)?;let a=target("https://example.org/new1");let b=target("https://example.org/new3");let requests=[request(&selected[0],&a),request(&selected[2],&b)];
    let denied=repo(&f,&source,&policy(&[&a])?)?;
    assert!(matches!(source.prepare_https_target_candidate(&provider,&denied,&requests,limits()?,target_limits()?,WriterLimits::default(),10),Err(E::Lower(SourceHttpsTargetError::Policy))));
    let allowed=repo(&f,&source,&policy(&[&a,&b])?)?;
    let out=source.prepare_https_target_candidate(&provider,&allowed,&requests,limits()?,target_limits()?,WriterLimits::default(),11)?;
    let bytes=out.with_verified_bytes(&provider,&allowed,12,|b|b.to_vec())?;
    assert_eq!(output_uris(&bytes,"actual-form-document")?,vec![Some("https://example.org/new1".into()),Some("https://example.org/keep".into()),Some("https://example.org/new3".into())]);Ok(())
}
#[test]
fn no_write_scope_or_current_source_read_is_denied_before_policy_repository()->TestResult{
    let bytes=fixture::package(&link(1,"https://example.org/old"))?;let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;
    let read=f.provider()?;let c=write_context(&f);let provider=writable(&f,&c)?;let source=provider.import_actual_forms(f.head,9)?;
    let t=target("https://example.org/new");let s=selections(&bytes)?;let repository=repo(&f,&source,&policy(&[&t])?)?;
    assert!(matches!(source.prepare_https_target_candidate(&read,&repository,&[request(&s[0],&t)],limits()?,target_limits()?,WriterLimits::default(),10),Err(E::Permission)));
    f.artifacts.set_permissions(&f.owner,f.result,f.reader.subject(),BTreeSet::new(),11)?;
    assert!(matches!(source.prepare_https_target_candidate(&provider,&repository,&[request(&s[0],&t)],limits()?,target_limits()?,WriterLimits::default(),12),Err(E::Source(_))));
    assert_eq!(repository.calls.load(Ordering::SeqCst),0);Ok(())
}
#[test]
fn every_foreign_or_stale_policy_binding_is_denied_before_output()->TestResult{
    let bytes=fixture::package(&link(1,"https://example.org/old"))?;let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;
    let c=write_context(&f);let provider=writable(&f,&c)?;let source=provider.import_actual_forms(f.head,9)?;let t=target("https://example.org/new");let selected=selections(&bytes)?;
    for i in 0..15{
        let repository=repo(&f,&source,&policy(&[&t])?)?;
        {let mut row=repository.row.lock().map_err(|_|"row")?;match i{
            0=>row.binding.tenant=TenantId::new(Uuid::from_u128(999))?,1=>row.binding.project=revision_service::ProjectId::generate(),2=>row.binding.branch=BranchId::generate(),
            3=>row.binding.document=DocumentId::parse("foreign-document")?,4=>row.binding.source_revision=revision_service::RevisionId::generate(),5=>row.binding.source_head_generation+=1,
            6=>row.binding.source_result_artifact=artifact_service::ArtifactId::generate(),7=>row.binding.source_package_sha256=ContentDigest::of(b"bad"),
            8=>row.binding.source_provenance_sha256=ContentDigest::of(b"bad"),9=>row.binding.observed_graph_sha256=ContentDigest::of(b"bad"),10=>row.binding.policy_version=Uuid::nil(),
            11=>row.binding.policy_generation=0,12=>row.binding.policy_generation=u64::MAX,13=>row.artifact=f.result,14=>row.digest=ContentDigest::of(b"bad"),_=>unreachable!()}}
        let result=source.prepare_https_target_candidate(&provider,&repository,&[request(&selected[0],&t)],limits()?,target_limits()?,WriterLimits::default(),10);
        assert!(matches!(result,Err(E::Binding|E::Artifact)),"matrix {i}");
    }Ok(())
}
#[test]
fn strict_policy_payload_rejects_unknown_missing_foreign_duplicate_or_trailing_fields()->TestResult{
    let bytes=fixture::package(&link(1,"https://example.org/old"))?;let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;
    let c=write_context(&f);let provider=writable(&f,&c)?;let source=provider.import_actual_forms(f.head,9)?;let t=target("https://example.org/new");let selected=selections(&bytes)?;
    let b=binding(&f,&source)?;let original=payload(&b,&policy(&[&t])?);
    for i in 0..9{let mut value=original.clone();match i{
        0=>value["unknown"]=true.into(),1=>{value.as_object_mut().ok_or("object")?.remove("binding");},2=>value["binding"]["document"]="foreign".into(),
        3=>value["schema_version"]="hwpx-agent.source-form-policy/v1".into(),4=>value["policy"]["unknown"]=true.into(),
        5=>{value["policy"].as_object_mut().ok_or("policy")?.remove("approvals");},6=>value["policy"]["policy_revision_sha256"]="bad".into(),_=>{}}
        let mut raw=serde_json::to_vec(&value)?;if i==7{raw.extend_from_slice(b" {}");}if i==8{let mut duplicate=b"{\"schema_version\":\"duplicate\",".to_vec();duplicate.extend_from_slice(&raw[1..]);raw=duplicate;}
        let repository=repository(&f,b.clone(),raw,ArtifactKind::Evidence,HTTPS_TARGET_POLICY_MEDIA_TYPE)?;
        assert!(source.prepare_https_target_candidate(&provider,&repository,&[request(&selected[0],&t)],limits()?,target_limits()?,WriterLimits::default(),10).is_err(),"payload {i}");
    }Ok(())
}
#[test]
fn policy_wrong_media_kind_size_and_ciphertext_are_denied()->TestResult{
    for i in 0..5{let bytes=fixture::package(&link(1,"https://example.org/old"))?;let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;
        let c=write_context(&f);let provider=writable(&f,&c)?;let source=provider.import_actual_forms(f.head,9)?;let t=target("https://example.org/new");let selected=selections(&bytes)?;
        let b=binding(&f,&source)?;let raw=if i==2{vec![b' ';1024*1024+1]}else{serde_json::to_vec(&payload(&b,&policy(&[&t])?))?};
        let mut repository=repository(&f,b,raw,if i==1{ArtifactKind::Source}else{ArtifactKind::Evidence},if i==0{"application/json"}else{HTTPS_TARGET_POLICY_MEDIA_TYPE})?;
        if i==3{repository.tamper=Some(f.blobs.tamper.clone());}
        if i==4{f.artifacts.quarantine(&f.owner,repository.row.lock().map_err(|_|"row")?.artifact,QuarantineReason::parse("FIXTURE_REVOKED")?,9)?;}
        assert!(matches!(source.prepare_https_target_candidate(&provider,&repository,&[request(&selected[0],&t)],limits()?,target_limits()?,WriterLimits::default(),10),Err(E::Artifact)),"artifact {i}");
    }Ok(())
}
#[test]
fn candidate_delivery_rechecks_both_acls_repository_revocation_scope_and_latest_version()->TestResult{
    for i in 0..6{let bytes=fixture::package(&link(1,"https://example.org/old"))?;let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;
        let c=write_context(&f);let provider=writable(&f,&c)?;let source=provider.import_actual_forms(f.head,9)?;let t=target("https://example.org/new");let selected=selections(&bytes)?;
        let repository=repo(&f,&source,&policy(&[&t])?)?;let candidate=source.prepare_https_target_candidate(&provider,&repository,&[request(&selected[0],&t)],limits()?,target_limits()?,WriterLimits::default(),10)?;
        match i{
            0=>{f.artifacts.set_permissions(&f.owner,f.result,f.reader.subject(),BTreeSet::new(),11)?;},
            1=>{f.artifacts.set_permissions(&f.owner,repository.row.lock().map_err(|_|"row")?.artifact,f.reader.subject(),BTreeSet::new(),11)?;},
            2=>repository.deny_after.store(0,Ordering::SeqCst),3=>repository.row.lock().map_err(|_|"row")?.binding.policy_generation+=1,
            4=>{f.artifacts.quarantine(&f.owner,repository.row.lock().map_err(|_|"row")?.artifact,QuarantineReason::parse("FIXTURE_REVOKED")?,11)?;},_=>{}}
        let read=f.provider()?;let mut consumed=false;
        let out=candidate.with_verified_bytes(if i==5{&read}else{&provider},&repository,12,|_|consumed=true);
        assert!(out.is_err(),"delivery {i}");assert!(!consumed);
    }Ok(())
}
#[test]
fn policy_revocation_during_preparation_or_final_delivery_never_exposes_bytes()->TestResult{
    for i in 0..2{let bytes=fixture::package(&link(1,"https://example.org/old"))?;let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;
        let c=write_context(&f);let provider=writable(&f,&c)?;let source=provider.import_actual_forms(f.head,9)?;let t=target("https://example.org/new");let selected=selections(&bytes)?;
        let repository=repo(&f,&source,&policy(&[&t])?)?;
        if i==0{repository.deny_after.store(1,Ordering::SeqCst);assert!(matches!(source.prepare_https_target_candidate(&provider,&repository,&[request(&selected[0],&t)],limits()?,target_limits()?,WriterLimits::default(),10),Err(E::Repository)));}
        else{let candidate=source.prepare_https_target_candidate(&provider,&repository,&[request(&selected[0],&t)],limits()?,target_limits()?,WriterLimits::default(),10)?;
            repository.calls.store(0,Ordering::SeqCst);repository.deny_after.store(2,Ordering::SeqCst);let mut consumed=false;
            assert!(matches!(candidate.with_verified_bytes(&provider,&repository,11,|_|consumed=true),Err(E::Repository)));assert!(!consumed);}
    }Ok(())
}
#[test]
fn changed_stored_head_denies_delivery_and_does_not_replace_newer_revision()->TestResult{
    let bytes=fixture::package(&link(1,"https://example.org/old"))?;let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;
    let c=write_context(&f);let provider=writable(&f,&c)?;let source=provider.import_actual_forms(f.head,9)?;let t=target("https://example.org/new");let selected=selections(&bytes)?;
    let repository=repo(&f,&source,&policy(&[&t])?)?;let candidate=source.prepare_https_target_candidate(&provider,&repository,&[request(&selected[0],&t)],limits()?,target_limits()?,WriterLimits::default(),10)?;
    // Independent fixture revision: never commit this candidate or reuse source/result IDs.
    let newer=f.artifacts.ingest(&f.owner,IngestRequest{bytes:fixture::package(&link(1,"https://example.org/independent-newer-source"))?,media_type:MediaType::parse("application/vnd.hancom.hwpx+zip")?,
        file_name:FileName::parse("newer-fixture.hwpx")?,kind:ArtifactKind::Result},11)?;
    let request=RevisionCommitRequest::new(CommitId::generate(),f.project,f.branch,f.head,revision_service::RevisionId::generate(),vec![f.head.revision_id().ok_or("head")?],
        f.result,newer.artifact_id,None,ContentDigest::of(b"new fixture operation"),RevisionValidationState::Verified,ContentDigest::of(b"new validation"),ContentDigest::of(b"new transaction"))?;
    assert!(matches!(f.revisions.commit(&f.revision_context,&request)?,CommitOutcome::Committed(_)));let new_head=f.revisions.head(&f.revision_context,f.project,f.branch)?;
    let mut consumed=false;assert!(matches!(candidate.with_verified_bytes(&provider,&repository,11,|_|consumed=true),Err(E::Source(_))));assert!(!consumed);
    assert_eq!(f.revisions.head(&f.revision_context,f.project,f.branch)?,new_head);assert_ne!(new_head,f.head);Ok(())
}
