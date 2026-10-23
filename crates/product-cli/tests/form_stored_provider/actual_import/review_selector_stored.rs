use super::*;
use domain_ir::LogicalId;
use hwpx_agent_cli::form_stored_provider::actual_import::{source_search::{StoredSourceSearchError as SearchError,review_selector::SourceReviewScopeOperation as Op},
    literal_search_output::StoredLiteralSearchError as LiteralError};
use hwpx_package::{WriterLimits,WriterLimitConfig,document_import::search::{SourceSearchQuery as Query,SourceSearchMode as Mode,SourceSearchLimits,SourceSearchLimitConfig as Config,
    selector::{SourceIndexScopeSelector as Scope,SourceIndexBoundary as Boundary},reviews::SourceReviewTextPolicy as Policy,
    replacement::{SourceReplacementRunPolicy as Run,SourceLiteralReplacementError as CoreError}}};
use serde_json::Value;
use std::{cell::Cell,io::Cursor,sync::atomic::AtomicUsize};
use revision_service as rev;
#[path="../../../../hwpx-package/tests/support/review_scope_fixture.rs"] mod fixture;
macro_rules! write_provider {($s:ident,$actor:ident,$provider:ident)=>{
    let $actor=RequestContext::new($s.reader.tenant_id(),$s.reader.subject(),[AuthScope::DocumentRead,AuthScope::DocumentWrite]);
    let $provider=StoredFormProvider::bind(&$s.artifacts,&$s.revisions,&$actor,&$s.revision_context,$s.project,$s.branch,DocumentId::parse("actual-form-document")?)?;
}}
macro_rules! search {($p:expr,$s:expr,$op:expr)=>{{$p.import_actual_forms($s.head,4)?.into_review_source_scope($p,$op,Default::default(),5)}}}
macro_rules! inventory {($p:expr,$s:expr)=>{{let out=search!($p,$s,Op::Inventory)?;let value:Value=out.with_verified_json($p,6,|b|serde_json::from_slice(b))??;value}}}
macro_rules! literal {($source:expr,$p:expr,$scope:expr,$policy:expr)=>{
    $source.prepare_review_selector_literal_candidate($p,query("K"),$scope,$policy,"NEW<&",Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default(),5)
}}
fn query(q:&str)->Query<'_> {Query {query:q,mode:Mode::Literal,case_sensitive:true,whole_word:false,max_results:100}}
fn all()->Policy {Policy {include_hidden_explanations:true,include_memo_bodies:true}}
fn find(scope:Scope<'_>,policy:Policy)->Op<'_> {Op::Find {query:query("K"),selector:scope,policy}}
fn window(inv:&Value,region:&str,scalar:usize)->Result<([u8;32],Boundary,Boundary),Box<dyn Error>> {
    let n=inv["block_regions"].as_array().ok_or("regions")?.iter().position(|v|v==region).ok_or("region")?;
    let b=&inv["inventory"]["blocks"][n];let start=Boundary {paragraph_handle:serde_json::from_value(b["paragraph_handle"].clone())?,
        block_index:serde_json::from_value(b["block_index"].clone())?,normalized_scalar:scalar};
    Ok((serde_json::from_value(inv["inventory"]["index"]["index_sha256"].clone())?,start.clone(),Boundary {normalized_scalar:scalar+1,..start}))
}
fn node(inv:&Value,handle:&LogicalId)->Result<LogicalId,Box<dyn Error>> {
    let entry=inv["inventory"]["nodes"].as_array().ok_or("nodes")?.iter().find(|n|n["source_handle"]==handle.as_str()).ok_or("node")?;
    Ok(serde_json::from_value(entry["node_id"].clone())?)
}
fn section(raw:&[u8])->Result<String,Box<dyn Error>> {let mut zip=hwpx_package::BoundedZipReader::open(Cursor::new(raw),Default::default())?;
    let i=zip.entries().iter().position(|e|e.path.as_str()=="Contents/section0.xml").ok_or("section")?;Ok(String::from_utf8(zip.read_entry(i)?)?)}
#[test]
fn stored_review_selector_discovery_drives_all_four_scopes_without_caller_form_import()->TestResult {
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let inv=inventory!(&p,&s);
    assert!(!serde_json::to_string(&inv)?.contains("PRIVATE-AUTHOR"));assert_eq!(inv["native_visibility_or_execution_authority"],false);
    let(hash,start,end)=window(&inv,"memo_body",7)?;let nodes=[node(&inv,&start.paragraph_handle)?];
    let sections:Vec<LogicalId>=serde_json::from_value(inv["inventory"]["section_ids"].clone())?;
    for(scope,count)in[(Scope::Document,6),(Scope::Section(&sections),6),(Scope::NodeSet(&nodes),2),(Scope::Selection {index_sha256:hash,start:&start,end:&end},1)] {
        let out=search!(&p,&s,find(scope,all()))?;out.verify(&p,6)?;let value:Value=out.with_verified_json(&p,6,|b|serde_json::from_slice(b))??;
        assert_eq!(value["result"]["matches"].as_array().ok_or("matches")?.len(),count);assert_eq!(out.receipt().profile,"hwpx-agent.stored-source-search/v6");
        assert!(!out.receipt().full_search_product_or_native_qualified&&!out.receipt().issuer_execution_publication_authority);}
    Ok(())
}
#[test]
fn stored_review_selector_policy_exclusions_precede_result_caps_and_bind_requests_not_scope()->TestResult {
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut hashes=BTreeSet::new();let mut scope=None;
    for(hidden,memo,count)in[(false,false,2),(true,false,4),(false,true,4),(true,true,6)] {
        let out=search!(&p,&s,Op::Find {query:Query {max_results:count,..query("K")},selector:Scope::Document,
            policy:Policy {include_hidden_explanations:hidden,include_memo_bodies:memo}})?;
        if let Some(expected)=scope{assert_eq!(out.receipt().scope.scope_sha256,expected);}else{scope=Some(out.receipt().scope.scope_sha256);}
        hashes.insert(out.receipt().query_sha256);let v:Value=out.with_verified_json(&p,6,|b|serde_json::from_slice(b))??;
        assert_eq!(v["result"]["matches"].as_array().ok_or("matches")?.len(),count);}
    assert_eq!(hashes.len(),4);Ok(())
}
#[test]
fn stored_review_selector_second_occurrence_only_bytes_preserve_other_matches_controls_and_cache()->TestResult {
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let inv=inventory!(&p,&s);
    for(region,scalar,old,new)in[("body_and_notes",7,"BODY K K","BODY K NEW&lt;&amp;"),("hidden_explanation",9,"HIDDEN K K","HIDDEN K NEW&lt;&amp;"),("memo_body",7,"MEMO K K","MEMO K NEW&lt;&amp;")] {
        let(hash,start,end)=window(&inv,region,scalar)?;let source=p.import_actual_forms(s.head,4)?;
        let out=literal!(source,&p,Scope::Selection {index_sha256:hash,start:&start,end:&end},all())?;
        out.verify(&p,6)?;let actual=out.with_verified_bytes(&p,6,section)??;assert_eq!(actual,section(&raw)?.replace(old,new));
        assert_eq!(out.receipt().output.body_candidate.output.matched_occurrences,1);assert_eq!(out.receipt().output.selector.scope_sha256,out.receipt().output.body_candidate.output.scope_sha256);
        assert_eq!(out.receipt().profile,"hwpx-agent.stored-selector-literal-candidate/v1");assert!(out.receipt().output.scope_window_enforced);
        assert!(actual.contains("CACHE FROZEN")&&actual.contains("PRIVATE-AUTHOR")&&actual.contains("<hp:lineBreak/>"));}
    Ok(())
}
#[test]
fn stored_review_selector_owned_candidate_moves_source_and_excluded_node_does_not_widen_scope()->TestResult {
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let inv=inventory!(&p,&s);
    let(_,start,_)=window(&inv,"memo_body",7)?;let ids=[node(&inv,&start.paragraph_handle)?];
    let excluded=search!(&p,&s,find(Scope::NodeSet(&ids),Policy::default()))?;
    let v:Value=excluded.with_verified_json(&p,6,|b|serde_json::from_slice(b))??;assert_eq!(v["searched_blocks"],0);assert_eq!(v["excluded_memo_paragraphs"],1);
    let source=p.import_actual_forms(s.head,4)?;assert!(matches!(literal!(source,&p,Scope::NodeSet(&ids),Policy::default()),Err(LiteralError::Output(CoreError::NoMatches))));
    let out={let source=p.import_actual_forms(s.head,4)?;source.into_review_selector_literal_candidate(&p,query("K"),Scope::NodeSet(&ids),all(),"X",
        Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default(),5)?};
    assert_eq!(out.with_verified_bytes(&p,6,section)??,section(&raw)?.replace("MEMO K K","MEMO X X"));
    assert!(matches!(out.require_current_product_route(&p,6),Err(LiteralError::RouteUnqualified)));Ok(())
}
#[test]
fn stored_review_selector_stale_foreign_reversed_and_outside_boundaries_fail_even_for_absent_query()->TestResult {
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let inv=inventory!(&p,&s);
    let(hash,start,end)=window(&inv,"memo_body",7)?;let foreign=Boundary {paragraph_handle:LogicalId::parse("foreign-paragraph")?,..start.clone()};
    let beyond=Boundary {normalized_scalar:9999,..end.clone()};
    for scope in[Scope::Selection {index_sha256:[0;32],start:&start,end:&end},Scope::Selection {index_sha256:hash,start:&foreign,end:&end},
        Scope::Selection {index_sha256:hash,start:&end,end:&start},Scope::Selection {index_sha256:hash,start:&start,end:&beyond}] {
        assert!(search!(&p,&s,Op::Find {query:query("absent"),selector:scope,policy:all()}).is_err());
        let source=p.import_actual_forms(s.head,4)?;assert!(literal!(source,&p,scope,all()).is_err());}
    Ok(())
}
#[test]
fn stored_review_selector_write_and_five_foreign_provider_scopes_deny_metadata_and_bytes()->TestResult {
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let reader=s.provider()?;
    assert!(matches!(search!(&reader,&s,Op::Inventory),Err(SearchError::Permission)));
    let source=p.import_actual_forms(s.head,4)?;assert!(matches!(literal!(source,&reader,Scope::Document,all()),Err(LiteralError::Permission)));
    let searched=search!(&p,&s,Op::Inventory)?;let out=literal!(source,&p,Scope::Document,all())?;let called=Cell::new(false);
    assert!(searched.with_verified_json(&reader,6,|_|called.set(true)).is_err());assert!(out.with_verified_bytes(&reader,6,|_|called.set(true)).is_err());
    for variant in 0..5 {let tenant=if variant==4{TenantId::new(Uuid::from_u128(998))?}else{s.reader.tenant_id()};
        let subject=if variant==3{SubjectDigest::from_authenticated_subject("foreign-review-selector")?}else{s.reader.subject()};
        let actor=RequestContext::new(tenant,subject,[AuthScope::DocumentRead,AuthScope::DocumentWrite]);let context=rev::RevisionRequestContext::new(tenant,subject);
        let project=if variant==2{rev::ProjectId::parse("prj_70000000000000000000000000000002")?}else{s.project};
        let branch=if variant==1{rev::BranchId::parse("brn_70000000000000000000000000000002")?}else{s.branch};
        let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&context,project,branch,DocumentId::parse(if variant==0{"foreign-document"}else{"actual-form-document"})?)?;
        assert!(searched.verify(&other,6).is_err());assert!(searched.with_verified_json(&other,6,|_|called.set(true)).is_err());
        assert!(out.verify(&other,6).is_err());assert!(out.with_verified_bytes(&other,6,|_|called.set(true)).is_err());}
    assert!(!called.get());Ok(())
}
#[test]
fn stored_review_selector_acl_revoke_regrant_freshly_gates_discovery_search_and_candidate()->TestResult {
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);
    let discovery=search!(&p,&s,Op::Inventory)?;let found=search!(&p,&s,find(Scope::Document,all()))?;let source=p.import_actual_forms(s.head,4)?;
    let out=literal!(source,&p,Scope::Document,all())?;s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),6)?;let called=Cell::new(false);
    for result in[&discovery,&found]{assert!(result.verify(&p,7).is_err());assert!(result.with_verified_json(&p,7,|_|called.set(true)).is_err());}
    assert!(out.verify(&p,7).is_err());assert!(out.with_verified_bytes(&p,7,|_|called.set(true)).is_err());assert!(!called.get());
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),8)?;
    discovery.verify(&p,9)?;found.verify(&p,9)?;out.verify(&p,9)?;Ok(())
}
#[test]
fn stored_review_selector_quarantine_or_aead_tamper_deny_retained_results_and_new_candidate()->TestResult {
    for tamper in[false,true]{let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);
        let discovery=search!(&p,&s,Op::Inventory)?;let found=search!(&p,&s,find(Scope::Document,all()))?;let source=p.import_actual_forms(s.head,4)?;
        let out=literal!(source,&p,Scope::Document,all())?;
        if tamper{s.blobs.tamper.store(true,Ordering::SeqCst);}else{s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("REVIEW_SELECTOR_TEST")?,6)?;}
        let called=Cell::new(false);for result in[&discovery,&found]{assert!(result.verify(&p,7).is_err());assert!(result.with_verified_json(&p,7,|_|called.set(true)).is_err());}
        assert!(out.verify(&p,7).is_err());assert!(out.with_verified_bytes(&p,7,|_|called.set(true)).is_err());
        assert!(literal!(source,&p,Scope::Document,all()).is_err());assert!(!called.get());}Ok(())
}
struct BoundaryRepo {inner:rev::InMemoryRevisionRepository,calls:AtomicUsize,trigger:AtomicUsize,context:rev::RevisionRequestContext,advance:rev::RevisionCommitRequest}
impl rev::RevisionRepository for BoundaryRepo {
    fn compare_and_swap(&self,c:&rev::RevisionRequestContext,r:&rev::RevisionCommitRequest)->Result<rev::CommitOutcome,rev::RevisionError>{self.inner.compare_and_swap(c,r)}
    fn head(&self,t:TenantId,p:rev::ProjectId,b:rev::BranchId)->Result<rev::RevisionHead,rev::RevisionError>{let call=self.calls.fetch_add(1,Ordering::SeqCst)+1;
        if call==self.trigger.load(Ordering::SeqCst){assert!(matches!(self.inner.compare_and_swap(&self.context,&self.advance)?,rev::CommitOutcome::Committed(_)));}self.inner.head(t,p,b)}
    fn node(&self,t:TenantId,p:rev::ProjectId,r:rev::RevisionId)->Result<rev::RevisionNode,rev::RevisionError>{self.inner.node(t,p,r)}
}
fn boundary(s:&StoredFixture)->Result<rev::RevisionService<BoundaryRepo>,Box<dyn Error>> {
    let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,
        ContentDigest::of(b"selector race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation"),ContentDigest::of(b"transaction"))?;
    Ok(rev::RevisionService::new(BoundaryRepo {inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance}))
}
#[test]
fn stored_review_selector_discovery_and_search_prepare_verify_final_head_races_block_consumer()->TestResult {
    for searching in[false,true]{for stage in 0..3{let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);
        let operation=if searching{find(Scope::Document,all())}else{Op::Inventory};let out=search!(&p,&s,operation)?;
        let b=boundary(&s)?;let bound=StoredFormProvider::bind(&s.artifacts,&b,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
        match stage{0=>{search!(&bound,&s,operation)?;},1=>{out.verify(&bound,6)?;},_=>{out.with_verified_json(&bound,6,|_|())?;}}
        let calls=b.repository().calls.load(Ordering::SeqCst);assert!(calls>=4);b.repository().calls.store(0,Ordering::SeqCst);b.repository().trigger.store(calls,Ordering::SeqCst);let called=Cell::new(false);
        match stage{0=>assert!(search!(&bound,&s,operation).is_err()),1=>assert!(out.verify(&bound,7).is_err()),_=>assert!(out.with_verified_json(&bound,7,|_|called.set(true)).is_err())}
        assert!(!called.get());assert_eq!(b.repository().calls.load(Ordering::SeqCst),calls);}}Ok(())
}
#[test]
fn stored_review_selector_literal_prepare_verify_and_final_head_races_block_output()->TestResult {
    for stage in 0..3{let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);
        let source=p.import_actual_forms(s.head,4)?;let out=literal!(source,&p,Scope::Document,all())?;let b=boundary(&s)?;
        let bound=StoredFormProvider::bind(&s.artifacts,&b,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
        match stage{0=>{literal!(source,&bound,Scope::Document,all())?;},1=>{out.verify(&bound,6)?;},_=>{out.with_verified_bytes(&bound,6,|_|())?;}}
        let calls=b.repository().calls.load(Ordering::SeqCst);assert!(calls>=4);b.repository().calls.store(0,Ordering::SeqCst);b.repository().trigger.store(calls,Ordering::SeqCst);let called=Cell::new(false);
        match stage{0=>assert!(literal!(source,&bound,Scope::Document,all()).is_err()),1=>assert!(out.verify(&bound,7).is_err()),_=>assert!(out.with_verified_bytes(&bound,7,|_|called.set(true)).is_err())}
        assert!(!called.get());assert_eq!(b.repository().calls.load(Ordering::SeqCst),calls);}Ok(())
}
#[test]
fn stored_review_selector_field_cache_outer_field_controls_and_noop_stay_rejected()->TestResult {
    for outer in[false,true]{let body=if outer{format!("<hp:p id='1'><hp:run><hp:ctrl><hp:fieldBegin id='99' type='DOC_DATE'/></hp:ctrl>{}<hp:ctrl><hp:fieldEnd beginIDRef='99'/></hp:ctrl></hp:run></hp:p>",fixture::run_body())}else{fixture::body()};
        let raw=fixture::with_body(&body)?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let source=p.import_actual_forms(s.head,4)?;
        if outer{assert!(matches!(literal!(source,&p,Scope::Document,all()),Err(LiteralError::Output(CoreError::FieldContent))));continue;}
        for q in[query("CACHE FROZEN"),query("\n"),Query {mode:Mode::Regex,..query("K")},Query {max_results:1,..query("K")}]{
            assert!(source.prepare_review_selector_literal_candidate(&p,q,Scope::Document,all(),"X",Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default(),5).is_err());}
        for replacement in["K","\n"]{assert!(source.prepare_review_selector_literal_candidate(&p,query("K"),Scope::Document,all(),replacement,Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default(),5).is_err());}}
    Ok(())
}
#[test]
fn stored_review_selector_caps_source_preservation_and_redacted_receipts_never_claim_native_or_commit()->TestResult {
    let raw=fixture::package()?;let original=ContentDigest::of(&raw);let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);
    for op in[Op::Inventory,find(Scope::Document,all())]{assert!(p.import_actual_forms(s.head,4)?.into_review_source_scope(&p,op,SourceSearchLimits::new(Config {result_bytes:1,..Default::default()})?,5).is_err());}
    let source=p.import_actual_forms(s.head,4)?;
    assert!(source.prepare_review_selector_literal_candidate(&p,query("K"),Scope::Document,all(),"X",Run::FirstOriginalRunRetainAllRuns,
        SourceSearchLimits::new(Config {result_bytes:1,..Default::default()})?,Default::default(),5).is_err());
    assert!(source.prepare_review_selector_literal_candidate(&p,query("K"),Scope::Document,all(),"X",Run::FirstOriginalRunRetainAllRuns,
        Default::default(),WriterLimits::new(WriterLimitConfig {max_output_bytes:1})?,5).is_err());
    let out=literal!(source,&p,Scope::Document,all())?;let searched=search!(&p,&s,Op::Inventory)?;
    assert!(!format!("{out:?}{:?}{searched:?}{:?}",out.receipt(),searched.receipt()).contains("PRIVATE-AUTHOR"));
    assert!(!out.receipt().issuer_execution_publication_authority&&!out.receipt().output.native_or_execution_authority);
    assert!(!out.receipt().output.body_candidate.output.field_cached_content_edit_qualified);
    assert_eq!(ContentDigest::of(&raw),original);assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);
    assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);Ok(())
}
