//! Explicit v2 text insertions with the original current-source and final-head boundary.
use super::*;
compiler_source!(PreparedStoredSelectorRegexInsertionCandidate);
use hwpx_package::document_import::search::replacement::atoms::regex::{SourceSelectorRegexInsertionCandidate,SourceSelectorRegexInsertionReceipt,
    SourceRegexInsertionPolicy,SOURCE_SELECTOR_REGEX_INSERTION_PROFILE,SOURCE_REGEX_INSERTION_ATOM_PROFILE};
pub const STORED_SELECTOR_REGEX_INSERTION_PROFILE:&str="hwpx-agent.stored-selector-regex-candidate/v2";
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct StoredSelectorRegexInsertionReceipt {pub source:StoredActualFormImportReceipt,pub output:SourceSelectorRegexInsertionReceipt,
    pub profile:&'static str,pub issuer_execution_publication_authority:bool}
pub struct PreparedStoredSelectorRegexInsertionCandidate<'a> {source:LiteralSource<'a>,output:SourceSelectorRegexInsertionCandidate,receipt:StoredSelectorRegexInsertionReceipt}
impl fmt::Debug for PreparedStoredSelectorRegexInsertionCandidate<'_> {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("PreparedStoredSelectorRegexInsertionCandidate(<redacted>; not_CAS_or_product_route)")}}
impl StoredImportedDocumentForms {
    /// # Errors
    /// Current write/source/whole Form proof, explicit insertion policy and one capture compiler.
    pub fn prepare_review_selector_regex_insertion_candidate<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,
        replacement:&str,run_policy:SourceReplacementRunPolicy,insertion_policy:SourceRegexInsertionPolicy,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredSelectorRegexInsertionCandidate<'_>,R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(R::Permission);}
        let(fresh,proof)=self.fresh_source_reconstructed(provider,now)?;
        let output=proof.lower_review_selector_regex_insertion_candidate(&self.imported,query,selector,policy,replacement,run_policy,insertion_policy,limits,writer)?;
        if output.receipt().output.output.source_package_sha256!=*fresh.digest.as_bytes(){return Err(R::Binding);}
        let receipt=StoredSelectorRegexInsertionReceipt {source:self.receipt.clone(),output:output.receipt().clone(),profile:STORED_SELECTOR_REGEX_INSERTION_PROFILE,issuer_execution_publication_authority:false};
        provider.check_head(fresh.head).map_err(StoredActualFormImportError::from)?;
        Ok(PreparedStoredSelectorRegexInsertionCandidate {source:LiteralSource::Borrowed(self),output,receipt})
    }
    /// # Errors
    /// Move the original owner and prepared candidate without an ownership-transfer clone/reimport.
    pub fn into_review_selector_regex_insertion_candidate<Rp,B,S,V>(self,provider:&StoredFormProvider<'_,Rp,B,S,V>,query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,
        replacement:&str,run_policy:SourceReplacementRunPolicy,insertion_policy:SourceRegexInsertionPolicy,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredSelectorRegexInsertionCandidate<'static>,R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let(output,receipt)={let prepared=self.prepare_review_selector_regex_insertion_candidate(provider,query,selector,policy,replacement,run_policy,insertion_policy,limits,writer,now)?;
            (prepared.output,prepared.receipt)};
        Ok(PreparedStoredSelectorRegexInsertionCandidate {source:LiteralSource::Owned(Box::new(self)),output,receipt})
    }
}
impl PreparedStoredSelectorRegexInsertionCandidate<'_> {
    #[must_use] pub const fn receipt(&self)->&StoredSelectorRegexInsertionReceipt {&self.receipt}
    fn fresh<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(R::Permission);}
        let fresh=self.source.fresh_source(provider,now)?;let insertion=&self.receipt.output;let outer=&insertion.output;
        if self.receipt.source!=self.source.receipt||insertion!=self.output.receipt()||self.receipt.profile!=STORED_SELECTOR_REGEX_INSERTION_PROFILE
            ||insertion.profile!=SOURCE_SELECTOR_REGEX_INSERTION_PROFILE||insertion.insertion_policy!=SourceRegexInsertionPolicy::RightOriginalPointElseLeftFirstEmptyText
            ||insertion.zero_width_matches>outer.output.matched_occurrences||!insertion.exact_original_cut_verified
            ||!insertion.text_insertion_next_to_controls_qualified||!insertion.original_empty_text_expansion_qualified
            ||insertion.control_replacement_field_cache_native_or_execution_authority||self.receipt.issuer_execution_publication_authority
            ||!source_receipt_matches(outer,*fresh.digest.as_bytes(),SOURCE_SELECTOR_REGEX_INSERTION_PROFILE,SOURCE_REGEX_INSERTION_ATOM_PROFILE){return Err(R::Binding);}Ok(())
    }
    /// # Errors
    /// Recheck current source/access and final head without replaying matching or lowering.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<StoredSelectorRegexInsertionReceipt,R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.fresh(provider,now)?;self.output.with_verified_bytes(|_|()).map_err(|_|R::Integrity)?;
        provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(self.receipt.clone())
    }
    /// # Errors
    /// Keep the final head check inside the original writer callback, before the consumer.
    pub fn with_verified_bytes<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.fresh(provider,now)?;self.output.with_verified_bytes(|bytes| {
            provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(consume(bytes))
        }).map_err(|_|R::Integrity)?
    }
    /// # Errors
    /// A text insertion candidate is not a durable claim, revision CAS or executable route.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {self.verify(provider,now)?;Err(R::RouteUnqualified)}
}
