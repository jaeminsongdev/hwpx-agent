//! Strict common product boundary; repository/scanner/crypto/commits remain isolated fixtures.
use super::*;
use hwpx_agent_cli::form_product_request::stored_operations::{StoredProductRequest as Entry,
    StoredProductOperationError as OE,bookmark_insertion710::{BOOKMARK_INSERTION_PRODUCT_REQUEST_SCHEMA as SCHEMA,
        BookmarkInsertionProductLimits as Limits,BookmarkInsertionRequestEntry}};
use revision_service::{RevisionRepository,RevisionError,RevisionNode,
    postgres::source_formula_policy::issuer_registry::stored_revision_jobs::{
        lifecycle::{StoredJobObservation,StoredJobOutcome,StoredJobState},
        request_lookup::{StoredRequestLookupRepository,StoredRequestLookup,StoredRequestObservation,StoredRequestLookupError}}};
use std::sync::atomic::AtomicUsize;
#[path="../../../hwpx-package/tests/support/block_bookmark679_fixture.rs"]
mod native;
fn budget()->Result<Limits>{Ok(Limits::standard()?)}
fn raw(s:&StoredFixture,source:&StoredImportedDocumentForms)->Result<Value>{
    let(run,target)=selection(source)?;request(s,source,run,target,"bookmark_name",false)
}
fn request(s:&StoredFixture,source:&StoredImportedDocumentForms,run:SourceAnchorHandle,target:LogicalId,display:&str,link:bool)->Result<Value>{
    Ok(json!({"schema_version":SCHEMA,"idempotency_key":"insertion711-key","project_id":s.project.public_id(),"document_id":DOC,
        "base_revision":s.head.revision_id().ok_or("head")?.public_id(),"expected_head_generation":s.head.generation(),
        "expected_source_package_sha256":hex::encode(source.receipt().imported.source_package_sha256),"plan_id":"insertion711-plan",
        "operation":{"kind":"insert_bookmark_crossref","run":run,"target_id":target,"display":display,"hyperlink":link}}))
}
fn wire(v:&Value)->Result<Vec<u8>>{Ok(serde_json::to_vec(v)?)}
fn unchanged(s:&StoredFixture,bytes:&[u8])->Result{
    require(s.revisions.head(&s.revision_context,s.project,s.branch)?==s.head
        &&s.artifacts.download(&s.owner,s.result,20)?==bytes
        &&s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count()==2)
}
pub(super) fn observation()->Result<Value>{
    const INPUT:&str=include_str!("../../../../implementation/p09/evidence/p09-361-block-bookmark693-product-inputs.v1.json");
    let manifest:Value=serde_json::from_str(INPUT)?;let bytes=read_pin(&manifest["source"])?;let mut rows=Vec::new();
    for(i,display)in["page","bookmark_name","content","relative_position"].into_iter().enumerate(){for hyperlink in[false,true]{
        let index=i*2+usize::from(hyperlink);let case=&manifest["cases"][index];
        let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let ctx=write_context(&s);let p=provider(&s,&ctx)?;
        let raw={let source=p.import_actual_forms(s.head,4)?;let(run,target)=native::select(source.imported(),&bytes)?;
            wire(&request(&s,&source,run,target,display,hyperlink)?)?};
        let operation=Entry::prepare_json(&p,&raw,None,5)?;let product=operation.as_bookmark_insertion().ok_or("insertion variant")?;
        let output=operation.with_verified_bytes(&p,None,6,|v|v.to_vec())?;
        require(hex::encode(Sha256::digest(&output))==case["stages"]["candidate"]["pin"]["sha256"]
            &&product.verify(&p,7)?==product.receipt()
            &&product.receipt().raw_request_sha256==hex::encode(Sha256::digest(&raw))
            &&product.receipt().compiled.compiled_plan_sha256==product.compiled().canonical_sha256()?
            &&product.receipt().request_schema==SCHEMA&&!product.receipt().idempotency_key_claimed
            &&!product.receipt().execution_or_publication_authority)?;
        let lookup=Entry::prepare_bookmark_insertion_lookup_json(&p,&raw,budget()?)?;
        require(hex::encode(lookup.canonical_request_sha256())==product.receipt().canonical_request_sha256
            &&hex::encode(lookup.scoped_request_sha256())==product.receipt().scoped_request_sha256
            &&operation.require_current_product_route(&p,None,8).is_err())?;
        unchanged(&s,&bytes)?;
        rows.push(json!({"case_index":index+1,"output_sha256":hex::encode(Sha256::digest(&output)),
            "receipt":product.receipt(),"source_and_head_unchanged":true,"route_qualified":false}));
    }}
    require(rows.len()==8&&read_pin(&manifest["source"])?==bytes)?;
    Ok(json!({"state":"QUALIFIED711_STRICT_OWNED_COMMON_INSERTION_ACTUAL8_NOT_EXECUTION_OR_DURABLE_BACKEND",
        "source":manifest["source"],"cases":rows,"Native_started":false,"head_changed":false,"result_ingested":false,
        "memory_repository_scanner_keys_and_commits_are_fixtures":true,"P09_complete":false}))
}
struct LookupModel{inner:InMemoryRevisionRepository,mode:u8,reads:AtomicUsize,lookups:AtomicUsize,commits:AtomicUsize}
impl LookupModel{fn new(s:&StoredFixture,mode:u8)->Self{Self{inner:s.revisions.repository().clone(),mode,
    reads:AtomicUsize::new(0),lookups:AtomicUsize::new(0),commits:AtomicUsize::new(0)}}}
impl RevisionRepository for LookupModel{
    fn authorize_context(&self,c:&RevisionRequestContext)->Result<(),RevisionError>{self.inner.authorize_context(c)}
    fn head(&self,t:TenantId,p:revision_service::ProjectId,b:BranchId)->Result<RevisionHead,RevisionError>{
        self.reads.fetch_add(1,Ordering::SeqCst);if self.mode==0{self.inner.head(t,p,b)}else{Err(RevisionError::RepositoryFailure)}
    }
    fn node(&self,t:TenantId,p:revision_service::ProjectId,r:revision_service::RevisionId)->Result<RevisionNode,RevisionError>{
        self.reads.fetch_add(1,Ordering::SeqCst);if self.mode==0{self.inner.node(t,p,r)}else{Err(RevisionError::RepositoryFailure)}
    }
    fn compare_and_swap(&self,_:&RevisionRequestContext,_:&RevisionCommitRequest)->Result<CommitOutcome,RevisionError>{
        self.commits.fetch_add(1,Ordering::SeqCst);Err(RevisionError::InvalidRequest)
    }
}
impl StoredRequestLookupRepository for LookupModel{
    fn observe_request(&self,c:&RevisionRequestContext,q:&StoredRequestLookup)->Result<StoredRequestObservation,StoredRequestLookupError>{
        self.authorize_context(c)?;self.lookups.fetch_add(1,Ordering::SeqCst);match self.mode{
            0=>Ok(StoredRequestObservation::NotObserved),
            1=>Ok(StoredRequestObservation::Existing(StoredJobObservation::observed(StoredJobOutcome::Replay,q.job_id(),
                StoredJobState::InProgress,1,1,None,None,None,None)?)),
            2=>Err(StoredRequestLookupError::KeyConflict),3=>Err(RevisionError::CommitOutcomeUnknown.into()),
            _=>Err(RevisionError::RepositoryFailure.into()),
        }
    }
}
#[test]
fn owned_standalone_and_common_requests_match_compiler_bytes_receipts_and_redacted_metadata()->Result{
    let bytes=sample()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let ctx=write_context(&s);let p=provider(&s,&ctx)?;
    let raw={let source=p.import_actual_forms(s.head,4)?;wire(&raw(&s,&source)?)?};
    let direct=Entry::prepare_bookmark_insertion_json(&p,&raw,budget()?,5)?;
    let common=Entry::prepare_json(&p,&raw,None,6)?;let product=common.as_bookmark_insertion().ok_or("variant")?;
    assert_eq!(direct.compiled(),product.compiled());assert_eq!(direct.receipt(),product.receipt());
    assert_eq!(direct.with_verified_bytes(&p,7,|v|v.to_vec())?,common.with_verified_bytes(&p,None,8,|v|v.to_vec())?);
    for value in[serde_json::to_string(product.receipt())?,String::from_utf8(product.compiled().canonical_json()?)?,format!("{common:?}")]{
        for secret in["private-target","private-display","原文","<hp:"]{require(!value.contains(secret))?;}}
    require(common.as_bookmark_commands().is_none()&&common.with_verified_preview_json(&p,None,9,|_|()).is_err())?;
    unchanged(&s,&bytes)
}
#[test]
fn malformed_shapes_unknown_fields_duplicate_keys_and_privilege_inputs_never_read_source()->Result{
    let bytes=sample()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let ctx=write_context(&s);let p=provider(&s,&ctx)?;
    let original={let source=p.import_actual_forms(s.head,4)?;raw(&s,&source)?};
    let revisions=RevisionService::new(LookupModel::new(&s,4));
    let p=StoredFormProvider::bind(&s.artifacts,&revisions,&ctx,&s.revision_context,s.project,s.branch,DocumentId::parse(DOC)?)?;
    let mut bad=Vec::new();
    for i in 0..18{let mut v=original.clone();match i{
        0=>v["operation"]["Command"]="?private;6;1;0;0".into(),1=>v["native_execution_authorized"]=true.into(),
        2=>v["operation"]["compiled_plan"]=json!({}),3=>v["operation"]["output_bytes"]=json!([]),
        4=>v["operation"]["kind"]="change_bookmark_crossref_commands".into(),5=>v["operation"]["hyperlink"]=1.into(),
        6=>v["operation"]["display"]="object_number".into(),7=>v["expected_head_generation"]=0.into(),
        8=>v["expected_source_package_sha256"]="A".repeat(64).into(),9=>v["operation"]["run"]["offset"]=0.into(),
        10=>v["operation"]["run"]=json!([v["operation"]["run"]["opaque_handle"],v["operation"]["run"]["fingerprint_sha256"]]),
        11=>v["operation"]=json!(["insert_bookmark_crossref"]),12=>v=json!([]),
        13=>{v.as_object_mut().ok_or("object")?.remove("idempotency_key");},
        14=>v["operation"]["run"]["fingerprint_sha256"]=json!(vec![256_u16;32]),
        15=>v["operation"]["target_id"]="".into(),16=>v["expected_head_generation"]=json!(i64::MAX as u64+1),
        _=>v["base_revision"]="not-a-revision".into(),
    }bad.push(wire(&v)?);}
    let text=String::from_utf8(wire(&original)?)?;
    bad.push(text.replacen("\"hyperlink\":false","\"hyperlink\":false,\"hyperlink\":true",1).into_bytes());
    bad.push(text.replacen("{","{\"schema_version\":\"duplicate\",",1).into_bytes());
    bad.push([wire(&original)?,b" {}".to_vec()].concat());bad.push(vec![b' ';2*1024*1024+1]);
    let audits=s.metadata.audit_events()?.len();
    for raw in bad{assert!(Entry::prepare_json(&p,&raw,None,5).is_err());}
    assert_eq!(revisions.repository().reads.load(Ordering::SeqCst),0);assert_eq!(revisions.repository().commits.load(Ordering::SeqCst),0);
    assert_eq!(s.metadata.audit_events()?.len(),audits);Ok(())
}
#[test]
fn stale_scope_head_source_run_fingerprint_and_target_cannot_prepare_output()->Result{
    let bytes=sample()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let ctx=write_context(&s);let p=provider(&s,&ctx)?;
    let original={let source=p.import_actual_forms(s.head,4)?;raw(&s,&source)?};
    for i in 0..7{let mut v=original.clone();match i{
        0=>v["project_id"]=revision_service::ProjectId::generate().public_id().into(),1=>v["document_id"]="foreign711".into(),
        2=>v["expected_head_generation"]=(s.head.generation()+1).into(),3=>v["expected_source_package_sha256"]="0".repeat(64).into(),
        4=>v["operation"]["run"]["fingerprint_sha256"]=json!(vec![0_u8;32]),
        5=>v["operation"]["run"]["opaque_handle"]="missing-run".into(),_=>v["operation"]["target_id"]="missing-target".into(),
    }require(Entry::prepare_json(&p,&wire(&v)?,None,5).is_err())?;}unchanged(&s,&bytes)
}
#[test]
fn canonical_lookup_ignores_formatting_and_binds_every_semantic_selection_and_head()->Result{
    let bytes=sample()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let ctx=write_context(&s);let p=provider(&s,&ctx)?;
    let v={let source=p.import_actual_forms(s.head,4)?;raw(&s,&source)?};
    let base=Entry::prepare_bookmark_insertion_lookup_json(&p,&wire(&v)?,budget()?)?;
    let pretty=Entry::prepare_bookmark_insertion_lookup_json(&p,&serde_json::to_vec_pretty(&v)?,budget()?)?;
    assert_eq!(base.canonical_request_sha256(),pretty.canonical_request_sha256());assert_eq!(base.scoped_request_sha256(),pretty.scoped_request_sha256());
    for i in 0..9{let mut changed=v.clone();match i{
        0=>changed["operation"]["hyperlink"]=true.into(),1=>changed["operation"]["display"]="page".into(),
        2=>changed["idempotency_key"]="different711".into(),3=>changed["plan_id"]="different711".into(),
        4=>changed["operation"]["run"]["fingerprint_sha256"]=json!(vec![0_u8;32]),5=>changed["operation"]["target_id"]="different711".into(),
        6=>changed["base_revision"]=revision_service::RevisionId::generate().public_id().into(),
        7=>changed["expected_head_generation"]=(s.head.generation()+1).into(),_=>changed["expected_source_package_sha256"]=hex::encode(Sha256::digest(b"different nonzero source digest711")).into(),
    }let after=Entry::prepare_bookmark_insertion_lookup_json(&p,&wire(&changed)?,budget()?)?;
        assert_ne!(base.canonical_request_sha256(),after.canonical_request_sha256());assert_ne!(base.scoped_request_sha256(),after.scoped_request_sha256());}
    // The shared request-lookup contract rejects the all-zero digest sentinel.
    let mut zero=v.clone();zero["expected_source_package_sha256"]="0".repeat(64).into();
    require(Entry::prepare_bookmark_insertion_lookup_json(&p,&wire(&zero)?,budget()?).is_err())?;
    unchanged(&s,&bytes)
}
#[test]
fn existing_conflict_unknown_or_failed_lookup_never_falls_back_to_source_or_compiler()->Result{
    let bytes=sample()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let ctx=write_context(&s);let p=provider(&s,&ctx)?;
    let raw={let source=p.import_actual_forms(s.head,4)?;wire(&raw(&s,&source)?)?};
    for mode in 1..5{let revisions=RevisionService::new(LookupModel::new(&s,mode));
        let p=StoredFormProvider::bind(&s.artifacts,&revisions,&ctx,&s.revision_context,s.project,s.branch,DocumentId::parse(DOC)?)?;
        let audits=s.metadata.audit_events()?.len();let entry=Entry::prepare_bookmark_insertion_or_observe_json(&p,&raw,budget()?,5);
        if mode==1{require(matches!(entry,Ok(BookmarkInsertionRequestEntry::Existing(_))))?;}else{require(entry.is_err())?;}
        assert_eq!(revisions.repository().lookups.load(Ordering::SeqCst),1);assert_eq!(revisions.repository().reads.load(Ordering::SeqCst),0);
        assert_eq!(revisions.repository().commits.load(Ordering::SeqCst),0);assert_eq!(s.metadata.audit_events()?.len(),audits);}
    Ok(())
}
#[test]
fn not_observed_only_prepares_owned_request_without_claim_or_commit()->Result{
    let bytes=sample()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let ctx=write_context(&s);let p=provider(&s,&ctx)?;
    let raw={let source=p.import_actual_forms(s.head,4)?;wire(&raw(&s,&source)?)?};
    let revisions=RevisionService::new(LookupModel::new(&s,0));
    let p=StoredFormProvider::bind(&s.artifacts,&revisions,&ctx,&s.revision_context,s.project,s.branch,DocumentId::parse(DOC)?)?;
    let BookmarkInsertionRequestEntry::Prepared(product)=Entry::prepare_bookmark_insertion_or_observe_json(&p,&raw,budget()?,5)? else{return Err("prepared".into())};
    product.verify(&p,6)?;require(!product.receipt().idempotency_key_claimed)?;
    assert_eq!(revisions.repository().lookups.load(Ordering::SeqCst),1);assert_eq!(revisions.repository().commits.load(Ordering::SeqCst),0);unchanged(&s,&bytes)
}
#[test]
fn common_delivery_rechecks_acl_and_regrant_cannot_revive_failed_candidate()->Result{
    let bytes=sample()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let ctx=write_context(&s);let p=provider(&s,&ctx)?;
    let raw={let source=p.import_actual_forms(s.head,4)?;wire(&raw(&s,&source)?)?};let op=Entry::prepare_json(&p,&raw,None,5)?;
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),6)?;
    let mut called=false;require(op.with_verified_bytes(&p,None,7,|_|called=true).is_err()&&!called)?;
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),8)?;
    require(op.with_verified_bytes(&p,None,9,|_|called=true).is_err()&&!called)
}
#[test]
fn common_delivery_rejects_aead_restoration_and_head_changes_without_callback()->Result{
    for head in[false,true]{let bytes=sample()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let ctx=write_context(&s);let p=provider(&s,&ctx)?;
        let raw={let source=p.import_actual_forms(s.head,4)?;wire(&raw(&s,&source)?)?};let op=Entry::prepare_json(&p,&raw,None,5)?;
        if head{advance(&s)?;}else{s.blobs.tamper.store(true,Ordering::SeqCst);}
        let mut called=false;require(op.with_verified_bytes(&p,None,6,|_|called=true).is_err()&&!called)?;
        s.blobs.tamper.store(false,Ordering::SeqCst);require(op.with_verified_bytes(&p,None,7,|_|called=true).is_err()&&!called)?;}Ok(())
}
#[test]
fn strict_wrapper_keeps_write_scope_point_content_and_foreign_provider_denials()->Result{
    let bytes=sample()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let ctx=write_context(&s);let p=provider(&s,&ctx)?;
    let v={let source=p.import_actual_forms(s.head,4)?;raw(&s,&source)?};let readonly=provider(&s,&s.reader)?;
    require(Entry::prepare_json(&readonly,&wire(&v)?,None,5).is_err())?;
    let mut content=v.clone();content["operation"]["display"]="content".into();require(Entry::prepare_json(&p,&wire(&content)?,None,5).is_err())?;
    let op=Entry::prepare_json(&p,&wire(&v)?,None,5)?;
    let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&ctx,&s.revision_context,s.project,s.branch,DocumentId::parse("foreign711")?)?;
    let mut called=false;require(op.with_verified_bytes(&other,None,6,|_|called=true).is_err()&&!called)?;unchanged(&s,&bytes)
}
#[test]
fn finite_server_budget_rejects_before_source_lookup_and_route_denial_never_grants_execution()->Result{
    let bytes=sample()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let ctx=write_context(&s);let p=provider(&s,&ctx)?;
    let raw={let source=p.import_actual_forms(s.head,4)?;wire(&raw(&s,&source)?)?};
    let limits=Limits{auxiliary:ReferenceAuxiliaryLimits::new(domain_ir::ReferenceAuxiliaryLimitConfig{text_bytes:1,..Default::default()})?,writer:WriterLimits::default()};
    let revisions=RevisionService::new(LookupModel::new(&s,4));
    let probe=StoredFormProvider::bind(&s.artifacts,&revisions,&ctx,&s.revision_context,s.project,s.branch,DocumentId::parse(DOC)?)?;
    require(Entry::prepare_bookmark_insertion_or_observe_json(&probe,&raw,limits,5).is_err())?;
    assert_eq!(revisions.repository().reads.load(Ordering::SeqCst),0);assert_eq!(revisions.repository().lookups.load(Ordering::SeqCst),0);
    let op=Entry::prepare_json(&p,&raw,None,5)?;require(matches!(op.require_current_product_route(&p,None,6),Err(OE::BookmarkInsertion(_))))?;
    let product=op.as_bookmark_insertion().ok_or("variant")?;product.verify(&p,7)?;
    require(!product.receipt().idempotency_key_claimed&&!product.receipt().execution_or_publication_authority)?;unchanged(&s,&bytes)
}
