use super::*;
use hwpx_agent_cli::form_stored_provider::actual_import::literal_search_output::StoredLiteralSearchError as E;
use hwpx_package::{WriterLimits,WriterLimitConfig,document_import::search::{SourceSearchQuery as Query,SourceSearchMode as Mode,
    SourceSearchLimits,SourceSearchLimitConfig as Config,scope::SourceSearchScope as Scope,
    reviews::SourceReviewTextPolicy as Policy,replacement::SourceReplacementRunPolicy as Run}};
use std::{cell::Cell,io::Cursor,sync::atomic::AtomicUsize};
use revision_service as rev;
#[allow(dead_code)] #[path="../../../../hwpx-package/tests/support/document_import_field_fixture.rs"] mod fixture;
macro_rules! write_provider {($s:ident,$actor:ident,$provider:ident)=>{
    let $actor=RequestContext::new($s.reader.tenant_id(),$s.reader.subject(),[AuthScope::DocumentRead,AuthScope::DocumentWrite]);
    let $provider=StoredFormProvider::bind(&$s.artifacts,&$s.revisions,&$actor,&$s.revision_context,$s.project,$s.branch,DocumentId::parse("actual-form-document")?)?;
}}
fn all()->Policy {Policy {include_hidden_explanations:true,include_memo_bodies:true}}
fn query(q:&str)->Query<'_> {Query {query:q,mode:Mode::Literal,case_sensitive:true,whole_word:false,max_results:100}}
fn body()->&'static str {"<hp:p id='1'><hp:run><hp:t>BODY K</hp:t><hp:ctrl><hp:hiddenComment><hp:subList><hp:p id='11'><hp:run><hp:t>HIDDEN K<hp:lineBreak/></hp:t></hp:run></hp:p></hp:subList></hp:hiddenComment></hp:ctrl><hp:ctrl><hp:fieldBegin id='17' type='MEMO' editable='0'><hp:subList><hp:p id='12'><hp:run><hp:t>MEMO K</hp:t></hp:run></hp:p></hp:subList></hp:fieldBegin></hp:ctrl><hp:t>CACHE FROZEN</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='17'/></hp:ctrl></hp:run></hp:p>"}
fn section(b:&[u8])->Result<String,Box<dyn std::error::Error>> {let mut r=hwpx_package::BoundedZipReader::open(Cursor::new(b),hwpx_package::PackageLimits::default())?;
    let i=r.entries().iter().position(|e|e.path.as_str()=="Contents/section0.xml").ok_or("section")?;Ok(String::from_utf8(r.read_entry(i)?)?)}
#[test]
fn review_literal_stored_actual_three_regions_preserve_field_cache_controls_and_unqualified_native_state()->TestResult {
    let raw=fixture::package(body())?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let source=provider.import_actual_forms(s.head,4)?;
    let out=source.prepare_review_literal_candidate(&provider,query("K"),Scope::MappedDocument,all(),"NEW<&",Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default(),5)?;
    out.verify(&provider,6)?;let actual=out.with_verified_bytes(&provider,6,section)??;
    assert_eq!(actual,section(&raw)?.replacen(body(),&body().replace('K',"NEW&lt;&amp;"),1));
    assert_eq!(out.receipt().profile,"hwpx-agent.stored-literal-search-candidate/v3");assert_eq!(out.receipt().output.output.matched_occurrences,3);
    assert!(actual.contains("CACHE FROZEN")&&actual.contains("<hp:lineBreak/>"));assert!(!out.receipt().output.output.field_cached_content_edit_qualified);
    assert!(matches!(out.require_current_product_route(&provider,6),Err(E::RouteUnqualified)));
    assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);
    assert!(!out.receipt().output.native_author_visibility_resolution_or_execution_qualified);Ok(())
}
#[test]
fn review_literal_stored_write_scope_foreign_document_acl_revoke_and_regrant_recheck_saved_candidates()->TestResult {
    let raw=fixture::package(body())?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let source=provider.import_actual_forms(s.head,4)?;let reader=s.provider()?;
    assert!(matches!(source.prepare_review_literal_candidate(&reader,query("K"),Scope::MappedDocument,all(),"X",Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default(),5),Err(E::Permission)));
    let out=source.prepare_review_literal_candidate(&provider,query("K"),Scope::MappedDocument,all(),"X",Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default(),5)?;let called=Cell::new(false);
    assert!(out.with_verified_bytes(&reader,6,|_|called.set(true)).is_err());assert!(!called.get());
    let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("foreign-review-literal")?)?;
    assert!(out.verify(&other,6).is_err());assert!(out.with_verified_bytes(&other,6,|_|called.set(true)).is_err());assert!(!called.get());
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),6)?;assert!(out.verify(&provider,7).is_err());assert!(out.with_verified_bytes(&provider,7,|_|called.set(true)).is_err());assert!(!called.get());
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([artifact_service::ArtifactPermission::Read]),8)?;out.verify(&provider,9)?;Ok(())
}
#[test]
fn review_literal_stored_quarantine_and_aead_tamper_deny_all_output_callbacks_and_new_preparation()->TestResult {
    for tamper in [false,true] {let raw=fixture::package(body())?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let source=provider.import_actual_forms(s.head,4)?;
        let out=source.prepare_review_literal_candidate(&provider,query("K"),Scope::MappedDocument,all(),"X",Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default(),5)?;
        if tamper{s.blobs.tamper.store(true,Ordering::SeqCst);}else{s.artifacts.quarantine(&s.owner,s.result,artifact_service::QuarantineReason::parse("REVIEW_LITERAL_TEST")?,6)?;}
        let called=Cell::new(false);assert!(out.verify(&provider,7).is_err());assert!(out.with_verified_bytes(&provider,7,|_|called.set(true)).is_err());assert!(!called.get());
        assert!(source.prepare_review_literal_candidate(&provider,query("K"),Scope::MappedDocument,all(),"X",Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default(),7).is_err());
    }Ok(())
}
struct BoundaryRepo {inner:rev::InMemoryRevisionRepository,calls:AtomicUsize,trigger:AtomicUsize,context:rev::RevisionRequestContext,advance:rev::RevisionCommitRequest}
impl rev::RevisionRepository for BoundaryRepo {
    fn compare_and_swap(&self,c:&rev::RevisionRequestContext,r:&rev::RevisionCommitRequest)->Result<rev::CommitOutcome,rev::RevisionError>{self.inner.compare_and_swap(c,r)}
    fn head(&self,t:TenantId,p:rev::ProjectId,b:rev::BranchId)->Result<rev::RevisionHead,rev::RevisionError>{let call=self.calls.fetch_add(1,Ordering::SeqCst)+1;
        if call==self.trigger.load(Ordering::SeqCst){assert!(matches!(self.inner.compare_and_swap(&self.context,&self.advance)?,rev::CommitOutcome::Committed(_)));}self.inner.head(t,p,b)}
    fn node(&self,t:TenantId,p:rev::ProjectId,r:rev::RevisionId)->Result<rev::RevisionNode,rev::RevisionError>{self.inner.node(t,p,r)}
}
#[test]
fn review_literal_stored_prepare_verify_and_final_consumer_head_races_fail_before_delivery()->TestResult {
    for stage in 0..3 {let raw=fixture::package(body())?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let source=provider.import_actual_forms(s.head,4)?;
        let out=source.prepare_review_literal_candidate(&provider,query("K"),Scope::MappedDocument,all(),"X",Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default(),5)?;
        let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,
            ContentDigest::of(b"review literal race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation"),ContentDigest::of(b"transaction"))?;
        let boundary=rev::RevisionService::new(BoundaryRepo {inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});
        let bound=StoredFormProvider::bind(&s.artifacts,&boundary,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
        match stage {0=>{source.prepare_review_literal_candidate(&bound,query("K"),Scope::MappedDocument,all(),"X",Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default(),6)?;},1=>{out.verify(&bound,6)?;},_=>{out.with_verified_bytes(&bound,6,|_|())?;}}
        let calls=boundary.repository().calls.load(Ordering::SeqCst);assert!(calls>=4);boundary.repository().calls.store(0,Ordering::SeqCst);boundary.repository().trigger.store(calls,Ordering::SeqCst);
        let called=Cell::new(false);match stage {0=>assert!(source.prepare_review_literal_candidate(&bound,query("K"),Scope::MappedDocument,all(),"X",Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default(),7).is_err()),
            1=>assert!(out.verify(&bound,7).is_err()),_=>assert!(out.with_verified_bytes(&bound,7,|_|called.set(true)).is_err())}assert!(!called.get());assert_eq!(boundary.repository().calls.load(Ordering::SeqCst),calls);
    }Ok(())
}
#[test]
fn review_literal_stored_scope_policy_and_request_digests_bind_selected_review_paragraph_only()->TestResult {
    let raw=fixture::package(body())?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let source=provider.import_actual_forms(s.head,4)?;
    let index=source.imported().source_review_text_index(&raw,Default::default())?;let found=index.find(query("HIDDEN K"),Scope::MappedDocument,all())?;let id=found.matches().matches()[0].paragraph_anchor.opaque_handle.clone();
    let out=source.prepare_review_literal_candidate(&provider,query("K"),Scope::Paragraphs(&[id.clone()]),all(),"X",Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default(),5)?;
    let actual=out.with_verified_bytes(&provider,6,section)??;assert_eq!(actual,section(&raw)?.replace("HIDDEN K","HIDDEN X"));assert_eq!(out.receipt().output.output.matched_occurrences,1);
    assert!(source.prepare_review_literal_candidate(&provider,query("K"),Scope::Paragraphs(&[id]),Policy::default(),"X",Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default(),5).is_err());
    let main=source.prepare_review_literal_candidate(&provider,query("K"),Scope::MappedDocument,Policy::default(),"X",Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default(),5)?;
    assert_ne!(out.receipt().output.review_search_request_sha256,main.receipt().output.review_search_request_sha256);Ok(())
}
#[test]
fn review_literal_stored_exclusions_caps_field_caches_and_control_edits_remain_fail_closed()->TestResult {
    let raw=fixture::package(body())?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let source=provider.import_actual_forms(s.head,4)?;
    source.prepare_review_literal_candidate(&provider,Query {max_results:1,..query("K")},Scope::MappedDocument,Policy::default(),"X",Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default(),5)?;
    for q in [Query {max_results:1,..query("K")},Query {mode:Mode::Regex,..query("K")},query("CACHE FROZEN"),query("\n")] {
        assert!(source.prepare_review_literal_candidate(&provider,q,Scope::MappedDocument,all(),"X",Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default(),5).is_err());
    }
    assert!(source.prepare_review_literal_candidate(&provider,query("K"),Scope::MappedDocument,all(),"X",Run::FirstOriginalRunRetainAllRuns,SourceSearchLimits::new(Config {result_bytes:1,..Default::default()})?,Default::default(),5).is_err());
    assert!(source.prepare_review_literal_candidate(&provider,query("K"),Scope::MappedDocument,all(),"X",Run::FirstOriginalRunRetainAllRuns,Default::default(),WriterLimits::new(WriterLimitConfig {max_output_bytes:1})?,5).is_err());
    assert!(source.prepare_review_literal_candidate(&provider,query("K"),Scope::MappedDocument,all(),"\n",Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default(),5).is_err());Ok(())
}
