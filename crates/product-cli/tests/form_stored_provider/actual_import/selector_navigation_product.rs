use super::*;
use hwpx_agent_cli::form_product_request::stored_source_search::{SourceSearchProductError as E,SourceSearchProductReceipt,
    navigation::SOURCE_SEARCH_NEXT_REQUEST_SCHEMA as NEXT,selector::{StoredSourceScopeProductRequest as S5,PreparedStoredSourceScopeProduct as P5,
        review::{StoredReviewScopeProductRequest as S6,PreparedStoredReviewScopeProduct as P6}}};
use serde_json::{json,Value};
use std::{cell::Cell,sync::atomic::AtomicUsize};
use revision_service as rev;
#[path="../../../../hwpx-package/tests/support/review_scope_fixture.rs"] mod fixture;
macro_rules! write_provider{($s:ident,$actor:ident,$p:ident)=>{
    let $actor=RequestContext::new($s.reader.tenant_id(),$s.reader.subject(),[AuthScope::DocumentRead,AuthScope::DocumentWrite]);
    let $p=StoredFormProvider::bind(&$s.artifacts,&$s.revisions,&$actor,&$s.revision_context,$s.project,$s.branch,DocumentId::parse("actual-form-document")?)?;
}}
macro_rules! prepare{($p:expr,$v:expr)=>{{let v=$v;if v["schema_version"]=="hwpx-agent.product-source-search-request/v5"{S5::prepare_json($p,&wire(v)?,Default::default(),4).map(Prepared::Plain)}else{S6::prepare_json($p,&wire(v)?,Default::default(),4).map(Prepared::Review)}}}}
enum Prepared{Plain(P5),Review(P6)}
impl Prepared{
    fn receipt(&self)->&SourceSearchProductReceipt{match self{Self::Plain(p)=>p.receipt(),Self::Review(p)=>p.receipt()}}
    fn digest(&self)->Result<String,E>{match self{Self::Plain(p)=>p.navigation_receipt_sha256(),Self::Review(p)=>p.navigation_receipt_sha256()}}
    fn json(&self,p:&Provider<'_>)->Result<Value,Box<dyn Error>>{Ok(match self{Self::Plain(s)=>s.with_verified_json(p,5,|b|serde_json::from_slice(b))??,Self::Review(s)=>s.with_verified_json(p,5,|b|serde_json::from_slice(b))??})}
    fn next<R,B,S,V,T>(&self,p:&StoredFormProvider<'_,R,B,S,V>,raw:&[u8],now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:rev::RevisionRepository{
        match self{Self::Plain(s)=>s.with_next_verified_json(p,raw,now,consume),Self::Review(s)=>s.with_next_verified_json(p,raw,now,consume)}
    }
}
fn wire(v:&Value)->Result<Vec<u8>,serde_json::Error>{serde_json::to_vec(v)}
fn envelope(s:&StoredFixture,raw:&[u8],version:u8)->Result<Value,Box<dyn Error>>{let revision=s.head.revision_id().ok_or("head")?.public_id();Ok(json!({
    "schema_version":format!("hwpx-agent.product-source-search-request/v{version}"),"idempotency_key":"PRIVATE-SELECTOR-NAV-KEY","plan_id":"selector-nav-plan","project_id":s.project.public_id(),
    "document_id":"actual-form-document","base_revision":revision,"expected_head_generation":s.head.generation(),"expected_source_package_sha256":ContentDigest::of(raw).hex(),
    "selector":{"revision_id":revision,"scope":"document"},"operation":{"kind":"scope_inventory"}}))}
fn find(base:&Value)->Value{let mut v=base.clone();v["operation"]=json!({"kind":"find_literal","query":"K","case_sensitive":true,"whole_word":false,"max_results":100});
    if v["schema_version"]=="hwpx-agent.product-source-search-request/v6"{v["operation"]["review_policy"]=json!({"include_hidden_explanations":true,"include_memo_bodies":true});}v}
fn next(p:&Prepared,cursor:Value,direction:&str,wrap:bool)->Result<Value,Box<dyn Error>>{Ok(json!({"schema_version":NEXT,"search_receipt_sha256":p.digest()?,"navigation":{"direction":direction,"wrap":wrap,"cursor":cursor}}))}
fn step(p:&Prepared,provider:&Provider<'_>,cursor:Value,direction:&str,wrap:bool)->Result<Value,Box<dyn Error>>{Ok(p.next(provider,&wire(&next(p,cursor,direction,wrap)?)?,5,|b|serde_json::from_slice(b))??)}
#[test]
fn selector_navigation_product_all_four_scopes_and_both_versions_advance_wrap_and_keep_global_matches()->TestResult{
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);
    for version in[5,6]{let base=envelope(&s,&raw,version)?;let inv=prepare!(&p,&base)?.json(&p)?;let inv=if version==5{inv}else{inv["inventory"].clone()};let b=&inv["blocks"][0];
        let node=inv["nodes"].as_array().ok_or("nodes")?.iter().find(|n|n["source_handle"]==b["paragraph_handle"]).ok_or("node")?;
        let hash:[u8;32]=serde_json::from_value(inv["index"]["index_sha256"].clone())?;
        for scope in["document","section","node_set","selection"]{let mut v=find(&base);v["selector"]["scope"]=json!(scope);
            match scope{"section"=>v["selector"]["section_ids"]=inv["section_ids"].clone(),"node_set"=>v["selector"]["range"]=json!({"node_ids":[node["node_id"].clone()]}),
                "selection"=>v["selector"]["range"]=json!({"coordinate_space":"index_nfc_unicode_scalars","index_sha256":hex::encode(hash),"start":{"paragraph_handle":b["paragraph_handle"],"block_index":b["block_index"],"normalized_scalar":7},"end":{"paragraph_handle":b["paragraph_handle"],"block_index":b["block_index"],"normalized_scalar":8}}),_=>{}}
            let out=prepare!(&p,&v)?;let original=out.json(&p)?;let matches=original["result"]["matches"].as_array().ok_or("matches")?;let mut cursor=Value::Null;
            for(i,m)in matches.iter().enumerate(){let n=step(&out,&p,cursor,"forward",false)?;assert_eq!(n["match_index"],i);assert_eq!(&n["selection"]["match"],m);assert_eq!(n["full_search_native_or_execution_authority"],false);cursor=n["cursor"].clone();}
            let exhausted=step(&out,&p,cursor.clone(),"forward",false)?;assert_eq!(exhausted["exhausted"],true);assert_eq!(exhausted["cursor"],cursor);
            let wrapped=step(&out,&p,cursor,"forward",true)?;assert_eq!(wrapped["match_index"],0);assert_eq!(wrapped["wrapped"],true);
            let last=step(&out,&p,wrapped["cursor"].clone(),"backward",true)?;assert_eq!(last["match_index"],matches.len()-1);assert_eq!(last["wrapped"],true);}}
    Ok(())
}
#[test]
fn selector_navigation_product_review_regions_empty_sets_and_zero_width_selection_remain_explicit()->TestResult{
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let base=envelope(&s,&raw,6)?;let out=prepare!(&p,&find(&base))?;let mut cursor=Value::Null;
    for i in 0..6{let n=step(&out,&p,cursor,"forward",false)?;assert_eq!(n["region"],["body_and_notes","hidden_explanation","memo_body"][i/2]);cursor=n["cursor"].clone();}
    let inv=prepare!(&p,&base)?.json(&p)?;let b=&inv["inventory"]["blocks"][0];let hash:[u8;32]=serde_json::from_value(inv["inventory"]["index"]["index_sha256"].clone())?;
    let mut v=find(&base);v["selector"]["scope"]=json!("selection");v["selector"]["range"]=json!({"coordinate_space":"index_nfc_unicode_scalars","index_sha256":hex::encode(hash),
        "start":{"paragraph_handle":b["paragraph_handle"],"block_index":b["block_index"],"normalized_scalar":7},"end":{"paragraph_handle":b["paragraph_handle"],"block_index":b["block_index"],"normalized_scalar":8}});
    v["operation"]["kind"]=json!("find_regex");v["operation"]["query"]=json!("^|$");let out=prepare!(&p,&v)?;let mut cursor=Value::Null;
    for i in 0..2{let n=step(&out,&p,cursor,"forward",false)?;assert_eq!(n["match_index"],i);assert_eq!(n["selection"]["match"]["zero_width"],true);cursor=n["cursor"].clone();}
    assert_eq!(step(&out,&p,cursor.clone(),"forward",false)?["exhausted"],true);v["operation"]["query"]=json!("PRIVATE-NO-MATCH");let empty=prepare!(&p,&v)?;
    let n=step(&empty,&p,Value::Null,"backward",true)?;assert_eq!(n["total_matches"],0);assert_eq!(n["exhausted"],true);assert!(n["cursor"].is_null());assert!(!serde_json::to_string(&n)?.contains("PRIVATE"));
    let called=Cell::new(false);assert!(empty.next(&p,&wire(&next(&empty,cursor,"forward",false)?)?,5,|_|called.set(true)).is_err());assert!(!called.get());Ok(())
}
#[test]
fn selector_navigation_product_cursor_binds_key_plan_raw_query_scope_policy_and_profile_context()->TestResult{
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);
    for version in[5,6]{let base=envelope(&s,&raw,version)?;let v=find(&base);let original=prepare!(&p,&v)?;let first=step(&original,&p,Value::Null,"forward",false)?;
        let inv=prepare!(&p,&base)?.json(&p)?;let sections=if version==5{inv["section_ids"].clone()}else{inv["inventory"]["section_ids"].clone()};
        for mode in 0..6{if mode==5&&version==5{continue;}let mut changed=v.clone();match mode{0=>changed["idempotency_key"]=json!("OTHER-KEY"),1=>changed["plan_id"]=json!("other-plan"),2=>changed["operation"]["case_sensitive"]=json!(false),
            3=>{changed["selector"]["scope"]=json!("section");changed["selector"]["section_ids"]=sections.clone();},5=>changed["operation"]["review_policy"]["include_memo_bodies"]=json!(false),_=>{}}
            let bytes=if mode==4{serde_json::to_vec_pretty(&changed)?}else{wire(&changed)?};let other=if version==5{Prepared::Plain(S5::prepare_json(&p,&bytes,Default::default(),4)?)}else{Prepared::Review(S6::prepare_json(&p,&bytes,Default::default(),4)?)};
            let called=Cell::new(false);assert!(other.next(&p,&wire(&next(&other,first["cursor"].clone(),"forward",false)?)?,5,|_|called.set(true)).is_err());assert!(!called.get());}}
    let v5=prepare!(&p,&find(&envelope(&s,&raw,5)?))?;let v6=prepare!(&p,&find(&envelope(&s,&raw,6)?))?;let first=step(&v5,&p,Value::Null,"forward",false)?;
    assert!(v6.next(&p,&wire(&next(&v6,first["cursor"].clone(),"forward",false)?)?,5,|_|()).is_err());Ok(())
}
#[test]
fn selector_navigation_product_strict_next_requests_and_foreign_receipts_fail_before_reads()->TestResult{
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);
    for version in[5,6]{let out=prepare!(&p,&find(&envelope(&s,&raw,version)?))?;let good=next(&out,Value::Null,"forward",false)?;let before=s.metadata.audit_events()?.len();let mut bad=vec![b"".to_vec(),b"null".to_vec(),b"[]".to_vec()];
        for key in["schema_version","search_receipt_sha256","navigation"]{let mut v=good.clone();v.as_object_mut().ok_or("object")?.remove(key);bad.push(wire(&v)?);}
        for(key,value)in[("schema_version",json!("other")),("search_receipt_sha256",json!("A".repeat(64))),("navigation",json!([])),("approved",json!(true)),("query",json!("K")),("output_path",json!("D:/do-not-write"))]{let mut v=good.clone();v[key]=value;bad.push(wire(&v)?);}
        for nav in[json!({"direction":"all","wrap":false}),json!({"direction":"forward","wrap":0}),json!({"direction":"forward"}),json!({"direction":"forward","wrap":false,"cursor":[]}),json!({"direction":"forward","wrap":false,"cursor":{},"native_verified":true})]{let mut v=good.clone();v["navigation"]=nav;bad.push(wire(&v)?);}
        bad.push(serde_json::to_string(&good)?.replace("\"wrap\":false","\"wrap\":false,\"wr\\u0061p\":true").into_bytes());for raw in bad{assert!(out.next(&p,&raw,5,|_|()).is_err());}
        let mut foreign=good.clone();foreign["search_receipt_sha256"]=json!("0".repeat(64));assert!(matches!(out.next(&p,&wire(&foreign)?,5,|_|()),Err(E::Binding)));assert_eq!(s.metadata.audit_events()?.len(),before);
        let mut exact=wire(&good)?;exact.resize(16*1024,b' ');out.next(&p,&exact,5,|_|())?;exact.push(b' ');assert!(matches!(out.next(&p,&exact,5,|_|()),Err(E::Limit)));}
    Ok(())
}
#[test]
fn selector_navigation_product_tampered_cursor_cannot_select_another_ordinal_or_occurrence()->TestResult{
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);
    for version in[5,6]{let out=prepare!(&p,&find(&envelope(&s,&raw,version)?))?;let first=step(&out,&p,Value::Null,"forward",false)?;
        for(key,value)in[("profile",json!("other")),("binding_sha256",json!(vec![1u8;32])),("match_index",json!(1)),("match_index",json!(9999)),("occurrence_sha256",json!(vec![0u8;32]))]{let mut cursor=first["cursor"].clone();cursor[key]=value;let called=Cell::new(false);
            assert!(out.next(&p,&wire(&next(&out,cursor,"forward",false)?)?,5,|_|called.set(true)).is_err());assert!(!called.get());}}
    Ok(())
}
#[test]
fn selector_navigation_product_write_and_five_foreign_scopes_reject_current_cursor_output()->TestResult{
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);
    for version in[5,6]{let out=prepare!(&p,&find(&envelope(&s,&raw,version)?))?;let request=wire(&next(&out,Value::Null,"forward",false)?)?;let called=Cell::new(false);let reader=s.provider()?;
        assert!(out.next(&reader,&request,5,|_|called.set(true)).is_err());for variant in 0..5{let tenant=if variant==4{TenantId::new(Uuid::from_u128(994))?}else{s.reader.tenant_id()};let subject=if variant==3{SubjectDigest::from_authenticated_subject("foreign-selector-nav")?}else{s.reader.subject()};
            let actor=RequestContext::new(tenant,subject,[AuthScope::DocumentRead,AuthScope::DocumentWrite]);let context=rev::RevisionRequestContext::new(tenant,subject);let project=if variant==2{rev::ProjectId::parse("prj_70000000000000000000000000000002")?}else{s.project};let branch=if variant==1{rev::BranchId::parse("brn_70000000000000000000000000000002")?}else{s.branch};
            let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&context,project,branch,DocumentId::parse(if variant==0{"foreign-document"}else{"actual-form-document"})?)?;
            assert!(out.next(&other,&request,5,|_|called.set(true)).is_err());}assert!(!called.get());}
    Ok(())
}
#[test]
fn selector_navigation_product_acl_revoke_regrant_quarantine_and_aead_recheck_retained_cursor()->TestResult{
    for version in[5,6]{for mode in 0..3{let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let out=prepare!(&p,&find(&envelope(&s,&raw,version)?))?;let first=step(&out,&p,Value::Null,"forward",false)?;let request=wire(&next(&out,first["cursor"].clone(),"forward",false)?)?;
        match mode{0=>{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;},1=>{s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("SELECTOR_NAV_TEST")?,5)?;},_=>s.blobs.tamper.store(true,Ordering::SeqCst)}
        let called=Cell::new(false);assert!(out.next(&p,&request,6,|_|called.set(true)).is_err());assert!(!called.get());if mode==0{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),7)?;out.next(&p,&request,8,|_|())?;}}}
    Ok(())
}
struct BoundaryRepo{inner:rev::InMemoryRevisionRepository,calls:AtomicUsize,trigger:AtomicUsize,context:rev::RevisionRequestContext,advance:rev::RevisionCommitRequest}
impl rev::RevisionRepository for BoundaryRepo{
    fn compare_and_swap(&self,c:&rev::RevisionRequestContext,r:&rev::RevisionCommitRequest)->Result<rev::CommitOutcome,rev::RevisionError>{self.inner.compare_and_swap(c,r)}
    fn head(&self,t:TenantId,p:rev::ProjectId,b:rev::BranchId)->Result<rev::RevisionHead,rev::RevisionError>{let n=self.calls.fetch_add(1,Ordering::SeqCst)+1;if n==self.trigger.load(Ordering::SeqCst){assert!(matches!(self.inner.compare_and_swap(&self.context,&self.advance)?,rev::CommitOutcome::Committed(_)));}self.inner.head(t,p,b)}
    fn node(&self,t:TenantId,p:rev::ProjectId,r:rev::RevisionId)->Result<rev::RevisionNode,rev::RevisionError>{self.inner.node(t,p,r)}
}
#[test]
fn selector_navigation_product_last_head_race_blocks_both_versions_before_consumer_selection()->TestResult{
    for version in[5,6]{let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let out=prepare!(&p,&find(&envelope(&s,&raw,version)?))?;let request=wire(&next(&out,Value::Null,"forward",false)?)?;
        let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,ContentDigest::of(b"selector nav race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation"),ContentDigest::of(b"transaction"))?;
        let b=rev::RevisionService::new(BoundaryRepo{inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});let bound=StoredFormProvider::bind(&s.artifacts,&b,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
        out.next(&bound,&request,5,|_|())?;let n=b.repository().calls.load(Ordering::SeqCst);assert!(n>=4);b.repository().calls.store(0,Ordering::SeqCst);b.repository().trigger.store(n,Ordering::SeqCst);let called=Cell::new(false);
        assert!(out.next(&bound,&request,6,|_|called.set(true)).is_err());assert!(!called.get());assert_eq!(b.repository().calls.load(Ordering::SeqCst),n);}
    Ok(())
}
#[test]
fn selector_navigation_product_inventory_is_not_a_search_and_rejects_before_artifact_reads()->TestResult{
    use sha2::{Digest as _,Sha256};let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);
    for version in[5,6]{let out=prepare!(&p,&envelope(&s,&raw,version)?)?;assert!(matches!(out.digest(),Err(E::Request)));let before=s.metadata.audit_events()?.len();
        let request=json!({"schema_version":NEXT,"search_receipt_sha256":hex::encode(Sha256::digest(serde_json::to_vec(out.receipt())?)),"navigation":{"direction":"forward","wrap":false,"cursor":null}});
        let called=Cell::new(false);assert!(matches!(out.next(&p,&wire(&request)?,5,|_|called.set(true)),Err(E::Request)));assert!(!called.get());assert_eq!(s.metadata.audit_events()?.len(),before);}
    Ok(())
}
#[test]
fn selector_navigation_product_retained_positions_do_not_ingest_commit_or_disclose_query_and_metadata()->TestResult{
    let raw=fixture::package()?;let original=ContentDigest::of(&raw);let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);
    for version in[5,6]{let out=prepare!(&p,&find(&envelope(&s,&raw,version)?))?;let mut cursor=Value::Null;for _ in 0..8{let value=step(&out,&p,cursor,"forward",true)?;let text=serde_json::to_string(&value)?;
        assert!(!text.contains("PRIVATE-AUTHOR")&&!text.contains("PRIVATE-SELECTOR-NAV-KEY")&&!text.contains("BODY K"));assert_eq!(value["full_search_native_or_execution_authority"],false);cursor=value["cursor"].clone();}}
    assert_eq!(ContentDigest::of(&raw),original);assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);Ok(())
}
