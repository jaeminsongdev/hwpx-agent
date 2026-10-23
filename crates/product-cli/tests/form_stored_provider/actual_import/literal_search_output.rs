use super::*;
use hwpx_agent_cli::form_stored_provider::actual_import::literal_search_output::StoredLiteralSearchError as E;
use hwpx_package::{WriterLimits,document_import::search::{SourceSearchQuery as Query,SourceSearchMode as Mode,SourceSearchLimits,SourceSearchLimitConfig as Config,
    scope::SourceSearchScope as Scope,replacement::SourceReplacementRunPolicy as Policy}};
use std::{cell::Cell,io::Cursor,sync::atomic::AtomicUsize};
use revision_service as rev;
#[allow(dead_code)] #[path="../../../../hwpx-package/tests/support/search_definition_fixture.rs"] mod fixture;
macro_rules! write_provider {($s:ident,$actor:ident,$provider:ident)=>{
    let $actor=RequestContext::new($s.reader.tenant_id(),$s.reader.subject(),[AuthScope::DocumentRead,AuthScope::DocumentWrite]);
    let $provider=StoredFormProvider::bind(&$s.artifacts,&$s.revisions,&$actor,&$s.revision_context,$s.project,$s.branch,DocumentId::parse("actual-form-document")?)?;
}}
fn query(s:&str)->Query<'_> {Query {query:s,mode:Mode::Literal,case_sensitive:true,whole_word:false,max_results:100}}
fn bytes()->Result<Vec<u8>,Box<dyn std::error::Error>> {fixture::package("<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>PRIVATE-</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t>QUERY</hp:t></hp:run></hp:p><hp:p id='2'><hp:run><hp:t>PRIVATE-QUERY</hp:t></hp:run></hp:p>")}
fn section(b:&[u8])->Result<String,Box<dyn std::error::Error>> {let mut r=hwpx_package::BoundedZipReader::open(Cursor::new(b),hwpx_package::PackageLimits::default())?;
    let i=r.entries().iter().position(|e|e.path.as_str()=="Contents/section0.xml").ok_or("section")?;Ok(String::from_utf8(r.read_entry(i)?)?)}
#[test]
fn literal_search_stored_actual_source_cross_run_candidate_keeps_authorization_and_never_ingests_or_commits()->TestResult {
    let raw=bytes()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let source=provider.import_actual_forms(s.head,4)?;
    let output=source.prepare_literal_search_candidate(&provider,query("PRIVATE-QUERY"),Scope::MappedDocument,"REPLACED<&",Policy::FirstOriginalRunRetainAllRuns,Default::default(),Default::default(),5)?;
    output.verify(&provider,6)?;let bytes=output.with_verified_bytes(&provider,6,<[u8]>::to_vec)?;
    let text=section(&bytes)?;assert!(text.contains("<hp:t>REPLACED&lt;&amp;</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t></hp:t>"));
    assert_eq!(output.receipt().output.matched_occurrences,2);assert_eq!(output.receipt().output.changes.len(),3);
    assert!(matches!(output.require_current_product_route(&provider,6),Err(E::RouteUnqualified)));
    assert!(!format!("{output:?}{:?}",output.receipt()).contains("PRIVATE-QUERY"));assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);
    assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);assert!(section(&raw)?.contains("PRIVATE-"));Ok(())
}
#[test]
fn literal_search_stored_write_scope_foreign_provider_and_acl_revocation_deny_retained_bytes()->TestResult {
    let raw=bytes()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let source=provider.import_actual_forms(s.head,4)?;let reader=s.provider()?;
    assert!(matches!(source.prepare_literal_search_candidate(&reader,query("PRIVATE-QUERY"),Scope::MappedDocument,"X",Policy::FirstOriginalRunRetainAllRuns,Default::default(),Default::default(),5),Err(E::Permission)));
    let output=source.prepare_literal_search_candidate(&provider,query("PRIVATE-QUERY"),Scope::MappedDocument,"X",Policy::FirstOriginalRunRetainAllRuns,Default::default(),Default::default(),5)?;let called=Cell::new(false);
    assert!(output.with_verified_bytes(&reader,6,|_|called.set(true)).is_err());assert!(!called.get());
    let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("foreign-literal")?)?;
    assert!(output.with_verified_bytes(&other,6,|_|called.set(true)).is_err());assert!(!called.get());
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),6)?;assert!(output.with_verified_bytes(&provider,7,|_|called.set(true)).is_err());assert!(!called.get());Ok(())
}
#[test]
fn literal_search_stored_quarantine_and_aead_tamper_reject_all_retained_candidate_exposures()->TestResult {
    for tamper in [false,true] {let raw=bytes()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let source=provider.import_actual_forms(s.head,4)?;
        let output=source.prepare_literal_search_candidate(&provider,query("PRIVATE-QUERY"),Scope::MappedDocument,"X",Policy::FirstOriginalRunRetainAllRuns,Default::default(),Default::default(),5)?;
        if tamper{s.blobs.tamper.store(true,Ordering::SeqCst);}else{s.artifacts.quarantine(&s.owner,s.result,artifact_service::QuarantineReason::parse("LITERAL_SEARCH_TEST")?,6)?;}
        let called=Cell::new(false);assert!(output.with_verified_bytes(&provider,7,|_|called.set(true)).is_err());assert!(!called.get());assert!(output.verify(&provider,7).is_err());
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
fn literal_search_stored_prepare_verify_and_final_consumer_head_races_reject_candidates()->TestResult {
    for stage in 0..3 {let raw=bytes()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let source=provider.import_actual_forms(s.head,4)?;
        let output=source.prepare_literal_search_candidate(&provider,query("PRIVATE-QUERY"),Scope::MappedDocument,"X",Policy::FirstOriginalRunRetainAllRuns,Default::default(),Default::default(),5)?;
        let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,
            ContentDigest::of(b"literal race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation"),ContentDigest::of(b"transaction"))?;
        let boundary=rev::RevisionService::new(BoundaryRepo {inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});
        let bound=StoredFormProvider::bind(&s.artifacts,&boundary,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
        match stage {0=>{source.prepare_literal_search_candidate(&bound,query("PRIVATE-QUERY"),Scope::MappedDocument,"X",Policy::FirstOriginalRunRetainAllRuns,Default::default(),Default::default(),6)?;},1=>{output.verify(&bound,6)?;},_=>{output.with_verified_bytes(&bound,6,|_|())?;}}
        let calls=boundary.repository().calls.load(Ordering::SeqCst);assert!(calls>=4);boundary.repository().calls.store(0,Ordering::SeqCst);boundary.repository().trigger.store(calls,Ordering::SeqCst);
        let called=Cell::new(false);match stage {0=>assert!(source.prepare_literal_search_candidate(&bound,query("PRIVATE-QUERY"),Scope::MappedDocument,"X",Policy::FirstOriginalRunRetainAllRuns,Default::default(),Default::default(),7).is_err()),
            1=>assert!(output.verify(&bound,7).is_err()),_=>assert!(output.with_verified_bytes(&bound,7,|_|called.set(true)).is_err())}assert!(!called.get());assert_eq!(boundary.repository().calls.load(Ordering::SeqCst),calls);
    }Ok(())
}
#[test]
fn literal_search_stored_finite_match_output_scope_and_invalid_mode_never_return_partial_success()->TestResult {
    let raw=bytes()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let source=provider.import_actual_forms(s.head,4)?;
    for q in [Query {max_results:1,..query("PRIVATE-QUERY")},Query {mode:Mode::Regex,..query("PRIVATE-QUERY")},query("absent")] {
        assert!(source.prepare_literal_search_candidate(&provider,q,Scope::MappedDocument,"X",Policy::FirstOriginalRunRetainAllRuns,Default::default(),Default::default(),5).is_err());}
    assert!(source.prepare_literal_search_candidate(&provider,query("PRIVATE-QUERY"),Scope::Paragraphs(&[domain_ir::LogicalId::parse("foreign")?]),"X",Policy::FirstOriginalRunRetainAllRuns,Default::default(),Default::default(),5).is_err());
    assert!(source.prepare_literal_search_candidate(&provider,query("PRIVATE-QUERY"),Scope::MappedDocument,"X",Policy::FirstOriginalRunRetainAllRuns,SourceSearchLimits::new(Config {result_bytes:1,..Default::default()})?,WriterLimits::default(),5).is_err());Ok(())
}
#[test]
fn literal_search_stored_selected_paragraph_only_changes_its_source_and_receipt_digests_bind_request()->TestResult {
    let raw=bytes()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let source=provider.import_actual_forms(s.head,4)?;
    let search=source.imported().body_structure().source_text_index(&raw,Default::default())?;let found=search.find(query("PRIVATE-QUERY"))?;
    let id=found.matches()[0].paragraph_anchor.opaque_handle.clone();
    let selected=source.prepare_literal_search_candidate(&provider,query("PRIVATE-QUERY"),Scope::Paragraphs(&[id]),"X",Policy::FirstOriginalRunRetainAllRuns,Default::default(),Default::default(),5)?;
    let text=selected.with_verified_bytes(&provider,6,section)??;assert!(text.contains("<hp:t>PRIVATE-QUERY</hp:t>"));assert_eq!(selected.receipt().output.matched_occurrences,1);
    let all=source.prepare_literal_search_candidate(&provider,query("PRIVATE-QUERY"),Scope::MappedDocument,"Y",Policy::FirstOriginalRunRetainAllRuns,Default::default(),Default::default(),5)?;
    assert_ne!(selected.receipt().output.scope_sha256,all.receipt().output.scope_sha256);assert_ne!(selected.receipt().output.replacement_sha256,all.receipt().output.replacement_sha256);
    assert_ne!(selected.receipt().output.output_package_sha256,all.receipt().output.output_package_sha256);Ok(())
}
