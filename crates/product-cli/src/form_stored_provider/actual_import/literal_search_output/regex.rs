//! Current source proof -> private regex candidate; original source and writer/head boundaries stay intact.
pub mod insertions;
use super::*;
compiler_source!(PreparedStoredSelectorRegexCandidate);
use super::product::LiteralSource;
use hwpx_package::document_import::search::{selector::SourceIndexScopeSelector,reviews::SourceReviewTextPolicy,
    replacement::atoms::regex::{SourceSelectorRegexCandidate,SourceSelectorRegexReceipt,SourceRegexReplacementError,SOURCE_SELECTOR_REGEX_PROFILE,SOURCE_REGEX_TEXT_ATOM_PROFILE}};
pub const STORED_SELECTOR_REGEX_PROFILE:&str="hwpx-agent.stored-selector-regex-candidate/v1";
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct StoredSelectorRegexReceipt {pub source:StoredActualFormImportReceipt,pub output:SourceSelectorRegexReceipt,
    pub profile:&'static str,pub issuer_execution_publication_authority:bool}
pub struct PreparedStoredSelectorRegexCandidate<'a> {source:LiteralSource<'a>,output:SourceSelectorRegexCandidate,receipt:StoredSelectorRegexReceipt}
impl fmt::Debug for PreparedStoredSelectorRegexCandidate<'_> {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("PreparedStoredSelectorRegexCandidate(<redacted>; not_CAS_or_product_route)")}}
#[derive(Debug,Error)]
pub enum StoredRegexReplacementError {
    #[error("STORED_REGEX_REPLACEMENT_SOURCE_REJECTED")] Source(#[from] StoredActualFormImportError),
    #[error("STORED_REGEX_REPLACEMENT_OUTPUT_REJECTED")] Output(#[from] SourceRegexReplacementError),
    #[error("STORED_REGEX_REPLACEMENT_DOCUMENT_WRITE_REQUIRED")] Permission,
    #[error("STORED_REGEX_REPLACEMENT_BINDING_REJECTED")] Binding,
    #[error("STORED_REGEX_REPLACEMENT_INTEGRITY_REJECTED")] Integrity,
    #[error("STORED_REGEX_REPLACEMENT_PRODUCT_ROUTE_UNQUALIFIED")] RouteUnqualified,
}
type R=StoredRegexReplacementError;
pub(crate) fn source_receipt_matches(outer:&SourceSelectorRegexReceipt,source_sha256:[u8;32],profile:&str,atom_profile:&str)->bool {
    let output=&outer.output;
    !(outer.profile!=profile||output.profile!=atom_profile||output.source_package_sha256!=source_sha256
        ||outer.selector.index_sha256!=output.source_index_sha256||outer.selector.scope_sha256!=output.scope_sha256
        ||outer.expansion_sha256!=output.replacement_sha256||outer.expanded_replacement_bytes!=output.replacement_bytes
        ||outer.match_regions.len()!=output.matched_occurrences||outer.expansion_work_limit==0||outer.expansion_work_units>outer.expansion_work_limit
        ||!outer.captures_from_one_original_match_pass||!outer.capture_values_are_index_nfc_text||!outer.scope_window_enforced
        ||outer.zero_width_control_or_field_cache_edit_qualified||outer.native_or_execution_authority||outer.selector.whole_document_visibility_native_flow_or_revision_authority
        ||output.full_protection_native_or_execution_authority||output.field_cached_content_edit_qualified
        ||output.control_atom_replacement_qualified||!output.original_control_bytes_preserved||!output.original_selection_contiguity_verified
        ||!output.outside_selected_text_atoms_exact||!output.output_text_span_values_verified)
}
impl StoredImportedDocumentForms {
    /// # Errors
    /// Current write access and one complete original proof for all capture-dependent edits.
    pub fn prepare_review_selector_regex_candidate<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,
        replacement:&str,run_policy:SourceReplacementRunPolicy,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredSelectorRegexCandidate<'_>,R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(R::Permission);}
        let(fresh,proof)=self.fresh_source_reconstructed(provider,now)?;
        let output=proof.lower_review_selector_regex_candidate(&self.imported,query,selector,policy,replacement,run_policy,limits,writer)?;
        if output.receipt().output.source_package_sha256!=*fresh.digest.as_bytes(){return Err(R::Binding);}
        let receipt=StoredSelectorRegexReceipt {source:self.receipt.clone(),output:output.receipt().clone(),profile:STORED_SELECTOR_REGEX_PROFILE,issuer_execution_publication_authority:false};
        provider.check_head(fresh.head).map_err(StoredActualFormImportError::from)?;
        Ok(PreparedStoredSelectorRegexCandidate {source:LiteralSource::Borrowed(self),output,receipt})
    }
    /// # Errors
    /// Transfer the original owner and prepared output; no clone or ownership-transfer reimport.
    pub fn into_review_selector_regex_candidate<Rp,B,S,V>(self,provider:&StoredFormProvider<'_,Rp,B,S,V>,query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,
        replacement:&str,run_policy:SourceReplacementRunPolicy,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredSelectorRegexCandidate<'static>,R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let(output,receipt)={let prepared=self.prepare_review_selector_regex_candidate(provider,query,selector,policy,replacement,run_policy,limits,writer,now)?;
            (prepared.output,prepared.receipt)};
        Ok(PreparedStoredSelectorRegexCandidate {source:LiteralSource::Owned(Box::new(self)),output,receipt})
    }
}
impl PreparedStoredSelectorRegexCandidate<'_> {
    #[must_use] pub const fn receipt(&self)->&StoredSelectorRegexReceipt {&self.receipt}
    fn fresh<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(R::Permission);}
        let fresh=self.source.fresh_source(provider,now)?;let outer=&self.receipt.output;
        if self.receipt.source!=self.source.receipt||outer!=self.output.receipt()||self.receipt.profile!=STORED_SELECTOR_REGEX_PROFILE
            ||!source_receipt_matches(outer,*fresh.digest.as_bytes(),SOURCE_SELECTOR_REGEX_PROFILE,SOURCE_REGEX_TEXT_ATOM_PROFILE)
            ||self.receipt.issuer_execution_publication_authority{return Err(R::Binding);}Ok(())
    }
    /// # Errors
    /// Current access/source, writer integrity and final head without query/capture/lowering replay.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<StoredSelectorRegexReceipt,R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.fresh(provider,now)?;self.output.with_verified_bytes(|_|()).map_err(|_|R::Integrity)?;
        provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(self.receipt.clone())
    }
    /// # Errors
    /// Final head stays inside the writer-integrity callback before consumer access.
    pub fn with_verified_bytes<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.fresh(provider,now)?;self.output.with_verified_bytes(|bytes| {
            provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(consume(bytes))
        }).map_err(|_|R::Integrity)?
    }
    /// # Errors
    /// A generated candidate is not a durable claim, revision CAS or executable route.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {self.verify(provider,now)?;Err(R::RouteUnqualified)}
}
