//! Current sealed source/whole number-stream candidate, not recalculation or revision commit authority.
use super::*;
compiler_source!(PreparedStoredNumberControlCandidate);
use super::product::LiteralSource;
use std::collections::BTreeMap;
use hwpx_package::document_import::{search::{selector::SourceIndexScopeSelector,reviews::SourceReviewTextPolicy,inspection::SourceControlKind,
    replacement::atoms::number_controls::{ValidatedNumberControlValues,SourceNumberControlCandidate,SourceNumberControlReceipt,SourceNumberControlError,SOURCE_NUMBER_CONTROL_PROFILE}},
    structure::caption_numbering_sequence::NativeNumberNodeRole as Role};
pub const STORED_NUMBER_CONTROL_PROFILE:&str="hwpx-agent.stored-number-control-replacement-candidate/v1";
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct StoredNumberControlReceipt{pub source:StoredActualFormImportReceipt,pub output:SourceNumberControlReceipt,pub values_sha256:[u8;32],
    pub profile:&'static str,pub issuer_execution_publication_authority:bool}
pub struct PreparedStoredNumberControlCandidate<'a>{source:LiteralSource<'a>,output:SourceNumberControlCandidate,receipt:StoredNumberControlReceipt}
impl fmt::Debug for PreparedStoredNumberControlCandidate<'_>{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{
    f.write_str("PreparedStoredNumberControlCandidate(<redacted>; current_access_not_native_counter_CAS_or_execution_authority)")}}
#[derive(Debug,Error)]
pub enum StoredNumberControlError{
    #[error("STORED_NUMBER_CONTROL_SOURCE_REJECTED")] Source(#[from] StoredActualFormImportError),
    #[error("STORED_NUMBER_CONTROL_OUTPUT_REJECTED")] Output(#[from] SourceNumberControlError),
    #[error("STORED_NUMBER_CONTROL_DOCUMENT_WRITE_REQUIRED")] Permission,
    #[error("STORED_NUMBER_CONTROL_BINDING_REJECTED")] Binding,
    #[error("STORED_NUMBER_CONTROL_INTEGRITY_REJECTED")] Integrity,
    #[error("STORED_NUMBER_CONTROL_PRODUCT_ROUTE_UNQUALIFIED")] RouteUnqualified,
}
type C=StoredNumberControlError;
pub(crate) fn number_control_receipt_matches(r:&SourceNumberControlReceipt,source:[u8;32])->bool{
    let search=&r.search;let stream=&r.stream;let content=&stream.content;let output=&content.output;let sequence=&stream.number_sequence;
    if r.profile!=SOURCE_NUMBER_CONTROL_PROFILE||r.source_package_sha256!=source||!matches!(search.kind(),SourceControlKind::AutoNumber|SourceControlKind::NewNumber)
        ||search.index_receipt().source_package_sha256!=source||search.scope_receipt().index_sha256!=search.index_receipt().index_sha256
        ||search.scope_receipt().whole_document_visibility_native_flow_or_revision_authority||r.selected_controls==0||r.selected_controls!=search.controls().len()
        ||r.selected_controls!=search.match_regions().len()||r.selected_controls>search.max_results()||search.controls().iter().any(|m|m.kind!=search.kind())
        ||r.changed_controls==0||r.changed_controls>r.selected_controls||r.changes.len()!=r.changed_controls||sequence.requested_events<r.selected_controls
        ||r.source_review_import.source_package_sha256!=source||r.output_review_import.source_package_sha256!=output.output_package_sha256
        ||output.output_review_import.as_ref()!=Some(&r.output_review_import)||output.source_package_sha256!=source||output.output_bytes==0||output.changed_parts==0
        ||content.source_state.numbering.source_package_sha256!=source||content.source_state.numbering.review_body_inventory_sha256!=Some(r.source_review_import.body_observations_sha256)
        ||!output.outside_selected_edits_exact||!r.whole_original_control_ranges_verified||!r.all_unselected_control_values_and_reference_bytes_preserved
        ||!sequence.complete_original_control_order_checked||!sequence.all_requested_values_read_back||sequence.native_counter_interpretation_and_recalculation_qualified
        ||sequence.execution_publication_authority||stream.execution_publication_authority||content.execution_publication_authority||output.execution_publication_authority
        ||r.native_recalculation_full_search_service_or_execution_authority{return false;}
    // Ordered subset in one forward search, then one bounded node aggregation; no N*M lookup.
    let mut selected=search.controls().iter();let mut counts=BTreeMap::new();
    for change in &r.changes{
        if !(1..=6).contains(&change.changed_attributes)||!selected.any(|m|m.control_anchor==change.source_control_anchor)
            ||change.source_control_id.as_str().strip_prefix("native-number-")!=Some(change.source_control_anchor.opaque_handle.as_str())
            ||counts.insert(&change.source_control_id,0usize).is_some(){return false;}
    }
    for node in &sequence.nodes{if node.changed_attributes>0{
        if !matches!(node.role,Role::Control|Role::Format)||(node.role==Role::Control&&node.changed_attributes>1)||(node.role==Role::Format&&node.changed_attributes>5){return false;}
        let Some(count)=counts.get_mut(&node.source_control_id)else{return false;};let Some(n)=count.checked_add(node.changed_attributes)else{return false;};*count=n;
    }}
    r.changes.iter().all(|c|counts.get(&c.source_control_id)==Some(&c.changed_attributes))
}
impl StoredImportedDocumentForms{
    /// # Errors
    /// Current access and one source proof/compiler. Validated values alone grant no access.
    pub fn prepare_number_control_candidate<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,selector:SourceIndexScopeSelector<'_>,body:SourceReviewTextPolicy,
        max_results:usize,input:&ValidatedNumberControlValues<'_>,writer:WriterLimits,now:u64)->Result<PreparedStoredNumberControlCandidate<'_>,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(C::Permission);}
        let(fresh,proof)=self.fresh_source_reconstructed(provider,now)?;let output=input.lower(&proof,&self.imported,selector,body,max_results,writer)?;
        let r=output.receipt();if !number_control_receipt_matches(r,*fresh.digest.as_bytes())||r.search.kind()!=input.kind()||r.search.policy()!=body||r.search.max_results()!=max_results
            ||r.request_sha256!=input.request_sha256(r.search.request_sha256())?{return Err(C::Binding);}
        let receipt=StoredNumberControlReceipt{source:self.receipt.clone(),output:r.clone(),values_sha256:input.values_sha256(),profile:STORED_NUMBER_CONTROL_PROFILE,issuer_execution_publication_authority:false};
        provider.check_head(fresh.head).map_err(StoredActualFormImportError::from)?;
        Ok(PreparedStoredNumberControlCandidate{source:LiteralSource::Borrowed(self),output,receipt})
    }
    /// # Errors
    /// Move the original source owner without cloning, reimporting or revalidating values.
    pub fn into_number_control_candidate<Rp,B,S,V>(self,provider:&StoredFormProvider<'_,Rp,B,S,V>,selector:SourceIndexScopeSelector<'_>,body:SourceReviewTextPolicy,
        max_results:usize,input:&ValidatedNumberControlValues<'_>,writer:WriterLimits,now:u64)->Result<PreparedStoredNumberControlCandidate<'static>,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let(output,receipt)={let p=self.prepare_number_control_candidate(provider,selector,body,max_results,input,writer,now)?;(p.output,p.receipt)};
        Ok(PreparedStoredNumberControlCandidate{source:LiteralSource::Owned(Box::new(self)),output,receipt})
    }
}
impl PreparedStoredNumberControlCandidate<'_>{
    #[must_use] pub const fn receipt(&self)->&StoredNumberControlReceipt{&self.receipt}
    fn fresh<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(C::Permission);}let fresh=self.source.fresh_source(provider,now)?;
        if self.receipt.source!=self.source.receipt||&self.receipt.output!=self.output.receipt()||self.receipt.profile!=STORED_NUMBER_CONTROL_PROFILE
            ||self.receipt.issuer_execution_publication_authority||!number_control_receipt_matches(&self.receipt.output,*fresh.digest.as_bytes()){return Err(C::Binding);}Ok(())
    }
    /// # Errors
    /// Current source/access, writer integrity and final head without replaying the compiler.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<StoredNumberControlReceipt,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.fresh(provider,now)?;self.output.with_verified_bytes(|_|()).map_err(|_|C::Integrity)?;
        provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(self.receipt.clone())
    }
    /// # Errors
    /// Current head is checked inside writer verification immediately before the consumer.
    pub fn with_verified_bytes<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.fresh(provider,now)?;self.output.with_verified_bytes(|bytes|{
            provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(consume(bytes))
        }).map_err(|_|C::Integrity)?
    }
    /// # Errors
    /// No Native recalculation, durable key claim, commit, CAS, dispatcher or publication.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.verify(provider,now)?;Err(C::RouteUnqualified)}
}
