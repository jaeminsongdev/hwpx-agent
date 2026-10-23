//! Current sealed source and one retained exact text-control candidate, not transaction authority.
use super::*;
compiler_source!(PreparedStoredControlCandidate);
use super::product::LiteralSource;
use hwpx_package::{TextAtom,document_import::search::{selector::SourceIndexScopeSelector,reviews::SourceReviewTextPolicy,
    inspection::SourceControlKind,replacement::atoms::controls::{ValidatedTextControlOutput,SourceControlReplacementCandidate,
        SourceControlReplacementReceipt,SourceControlReplacementError,SOURCE_CONTROL_REPLACEMENT_PROFILE}}};
pub const STORED_CONTROL_PROFILE:&str="hwpx-agent.stored-text-control-replacement-candidate/v1";
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct StoredControlReceipt{pub source:StoredActualFormImportReceipt,pub output:SourceControlReplacementReceipt,
    pub profile:&'static str,pub issuer_execution_publication_authority:bool}
pub struct PreparedStoredControlCandidate<'a>{source:LiteralSource<'a>,output:SourceControlReplacementCandidate,receipt:StoredControlReceipt}
impl fmt::Debug for PreparedStoredControlCandidate<'_>{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{
    f.write_str("PreparedStoredControlCandidate(<redacted>; current_access_not_full_control_or_transaction)")}}
#[derive(Debug,Error)]
pub enum StoredControlError{
    #[error("STORED_CONTROL_SOURCE_REJECTED")] Source(#[from] StoredActualFormImportError),
    #[error("STORED_CONTROL_OUTPUT_REJECTED")] Output(#[from] SourceControlReplacementError),
    #[error("STORED_CONTROL_DOCUMENT_WRITE_REQUIRED")] Permission,
    #[error("STORED_CONTROL_BINDING_REJECTED")] Binding,
    #[error("STORED_CONTROL_INTEGRITY_REJECTED")] Integrity,
    #[error("STORED_CONTROL_PRODUCT_ROUTE_UNQUALIFIED")] RouteUnqualified,
}
type C=StoredControlError;
pub(crate) fn control_receipt_matches(r:&SourceControlReplacementReceipt,source:[u8;32])->bool{
    let search=&r.search;
    if r.profile!=SOURCE_CONTROL_REPLACEMENT_PROFILE||r.source_package_sha256!=source||!matches!(r.kind,SourceControlKind::Tab|SourceControlKind::LineBreak)
        ||search.index_receipt().source_package_sha256!=source||search.index_receipt().index_sha256!=r.source_index_sha256
        ||search.scope_receipt()!=&r.selector||r.selector.index_sha256!=r.source_index_sha256
        ||search.controls().len()!=r.selected_controls||search.match_regions().len()!=r.selected_controls||r.selected_controls==0
        ||search.controls().iter().any(|m|m.kind!=r.kind)||r.changed_controls==0||r.changed_controls>r.selected_controls
        ||r.changes.len()!=r.changed_controls||r.span_changes.is_empty()||r.changed_parts==0||r.output_bytes==0
        ||r.source_review_import.source_package_sha256!=source||r.output_review_import.source_package_sha256!=r.output_package_sha256
        ||r.span_changes.iter().any(|s|s.changed_original_text_atoms!=0)
        ||r.span_changes.iter().try_fold(0usize,|n,s|n.checked_add(s.changed_scalar_ranges))!=Some(r.changed_controls)
        ||!r.whole_atomic_control_selection_verified||!r.original_text_run_shells_styles_references_and_outside_control_bytes_preserved
        ||!r.output_spans_and_exact_outside_edits_verified||r.selector.whole_document_visibility_native_flow_or_revision_authority
        ||r.full_control_contract_native_service_or_execution_authority{return false;}
    // One forward subset check, not an O(changes * selected controls) anchor lookup.
    let mut selected=search.controls().iter();
    r.changes.iter().all(|c|c.original_kind==r.kind&&c.output_atoms==r.replacement_atoms&&c.output_semantic_sha256==r.replacement_sha256
        &&selected.any(|m|m.control_anchor==c.source_control_anchor))
}
impl StoredImportedDocumentForms{
    /// # Errors
    /// Validate parameters once before fresh source access, then call one original compiler.
    pub fn prepare_control_candidate<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,selector:SourceIndexScopeSelector<'_>,body:SourceReviewTextPolicy,
        kind:SourceControlKind,max_results:usize,output:&[TextAtom],limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredControlCandidate<'_>,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let input=ValidatedTextControlOutput::new(kind,output,limits)?;self.prepare_control_input(provider,selector,body,max_results,&input,writer,now)
    }
    fn prepare_control_input<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,selector:SourceIndexScopeSelector<'_>,body:SourceReviewTextPolicy,
        max_results:usize,input:&ValidatedTextControlOutput<'_>,writer:WriterLimits,now:u64)->Result<PreparedStoredControlCandidate<'_>,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(C::Permission);}
        let(fresh,proof)=self.fresh_source_reconstructed(provider,now)?;
        let output=input.lower(&proof,&self.imported,selector,body,max_results,writer)?;
        let r=output.receipt();if !control_receipt_matches(r,*fresh.digest.as_bytes())||r.kind!=input.kind()||r.replacement_sha256!=input.replacement_sha256()
            ||r.replacement_atoms!=input.output_atoms()||r.replacement_text_bytes!=input.text_bytes(){return Err(C::Binding);}
        let receipt=StoredControlReceipt{source:self.receipt.clone(),output:r.clone(),profile:STORED_CONTROL_PROFILE,issuer_execution_publication_authority:false};
        provider.check_head(fresh.head).map_err(StoredActualFormImportError::from)?;
        Ok(PreparedStoredControlCandidate{source:LiteralSource::Borrowed(self),output,receipt})
    }
    /// # Errors
    /// Move the existing source owner without cloning, reimporting or revalidating the payload.
    pub fn into_control_candidate<Rp,B,S,V>(self,provider:&StoredFormProvider<'_,Rp,B,S,V>,selector:SourceIndexScopeSelector<'_>,body:SourceReviewTextPolicy,
        kind:SourceControlKind,max_results:usize,output:&[TextAtom],limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredControlCandidate<'static>,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let input=ValidatedTextControlOutput::new(kind,output,limits)?;self.into_control_input(provider,selector,body,max_results,&input,writer,now)
    }
    pub(crate) fn into_control_input<Rp,B,S,V>(self,provider:&StoredFormProvider<'_,Rp,B,S,V>,selector:SourceIndexScopeSelector<'_>,body:SourceReviewTextPolicy,
        max_results:usize,input:&ValidatedTextControlOutput<'_>,writer:WriterLimits,now:u64)->Result<PreparedStoredControlCandidate<'static>,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let(output,receipt)={let p=self.prepare_control_input(provider,selector,body,max_results,input,writer,now)?;(p.output,p.receipt)};
        Ok(PreparedStoredControlCandidate{source:LiteralSource::Owned(Box::new(self)),output,receipt})
    }
}
impl PreparedStoredControlCandidate<'_>{
    #[must_use] pub const fn receipt(&self)->&StoredControlReceipt{&self.receipt}
    fn fresh<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(C::Permission);}let fresh=self.source.fresh_source(provider,now)?;
        if self.receipt.source!=self.source.receipt||&self.receipt.output!=self.output.receipt()||self.receipt.profile!=STORED_CONTROL_PROFILE
            ||self.receipt.issuer_execution_publication_authority||!control_receipt_matches(&self.receipt.output,*fresh.digest.as_bytes()){return Err(C::Binding);}Ok(())
    }
    /// # Errors
    /// Current access/source/writer/final head; no second control search or replacement.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<StoredControlReceipt,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.fresh(provider,now)?;self.output.with_verified_bytes(|_|()).map_err(|_|C::Integrity)?;
        provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(self.receipt.clone())
    }
    /// # Errors
    /// Keep the final current head inside writer verification before the consumer.
    pub fn with_verified_bytes<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.fresh(provider,now)?;self.output.with_verified_bytes(|bytes|{
            provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(consume(bytes))
        }).map_err(|_|C::Integrity)?
    }
    /// # Errors
    /// Candidate integrity is not a dispatcher, durable key claim, CAS, Native or publication.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.verify(provider,now)?;Err(C::RouteUnqualified)}
}
