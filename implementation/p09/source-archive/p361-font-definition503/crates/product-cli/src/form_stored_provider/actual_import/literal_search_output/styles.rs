//! Current sealed original -> private partial character-property candidate, not revision execution.
use super::*;
compiler_source!(PreparedStoredCharacterStyleCandidate, style);
use super::product::LiteralSource;
use hwpx_package::document_import::search::{selector::SourceIndexScopeSelector,reviews::{SourceReviewTextPolicy,selector::styles::SourceReviewStyleFilter},
    replacement::atoms::styles::{SourceStyleReplacementCandidate,SourceStyleReplacementReceipt,SourceStyleReplacementError,SOURCE_SELECTOR_STYLE_REPLACEMENT_PROFILE}};
pub const STORED_CHARACTER_STYLE_PROFILE:&str="hwpx-agent.stored-character-style-candidate/v1";
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct StoredCharacterStyleReceipt {pub source:StoredActualFormImportReceipt,pub output:SourceStyleReplacementReceipt,
    pub profile:&'static str,pub issuer_execution_publication_authority:bool}
pub struct PreparedStoredCharacterStyleCandidate<'a> {source:LiteralSource<'a>,output:SourceStyleReplacementCandidate,receipt:StoredCharacterStyleReceipt}
impl fmt::Debug for PreparedStoredCharacterStyleCandidate<'_> {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("PreparedStoredCharacterStyleCandidate(<redacted>; not_CAS_or_product_route)")}}
#[derive(Debug,Error)]
pub enum StoredCharacterStyleError {
    #[error("STORED_CHARACTER_STYLE_SOURCE_REJECTED")] Source(#[from] StoredActualFormImportError),
    #[error("STORED_CHARACTER_STYLE_OUTPUT_REJECTED")] Output(#[from] SourceStyleReplacementError),
    #[error("STORED_CHARACTER_STYLE_DOCUMENT_WRITE_REQUIRED")] Permission,
    #[error("STORED_CHARACTER_STYLE_BINDING_REJECTED")] Binding,
    #[error("STORED_CHARACTER_STYLE_INTEGRITY_REJECTED")] Integrity,
    #[error("STORED_CHARACTER_STYLE_PRODUCT_ROUTE_UNQUALIFIED")] RouteUnqualified,
}
type R=StoredCharacterStyleError;
pub(crate) fn source_receipt_matches(r:&SourceStyleReplacementReceipt,source_sha256:[u8;32])->bool {
    r.profile==SOURCE_SELECTOR_STYLE_REPLACEMENT_PROFILE&&r.source_package_sha256==source_sha256
        &&r.selector.index_sha256==r.source_index_sha256&&r.source_review_import.source_package_sha256==source_sha256
        &&r.output_review_import.source_package_sha256==r.output_package_sha256&&r.match_regions.len()==r.matched_occurrences
        &&r.matched_occurrences>0&&r.original_changed_runs>0&&r.generated_run_fragments>=r.original_changed_runs
        &&r.changed_source_scalar_ranges>0&&r.changed_parts>0&&r.compiled_fragment_bytes>0&&r.output_bytes>0
        &&r.all_original_scalars_and_control_values_preserved&&r.every_original_scalar_style_read_back&&r.outside_original_run_edits_exact&&r.original_run_boundaries_not_merged
        &&!r.selector.whole_document_visibility_native_flow_or_revision_authority
        &&!r.paragraph_named_text_style_effective_visibility_or_execution_qualified&&!r.full_protection_native_or_service_authority
}
impl StoredImportedDocumentForms {
    /// # Errors
    /// Current write/scope/source and one exact whole Form proof for the whole source style batch.
    pub fn prepare_character_style_candidate<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,
        filter:SourceReviewStyleFilter,character_property:u32,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredCharacterStyleCandidate<'_>,R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(R::Permission);}
        let(fresh,proof)=self.fresh_source_reconstructed(provider,now)?;
        let output=proof.lower_review_selector_style_candidate(&self.imported,query,selector,policy,filter,character_property,limits,writer)?;
        if !source_receipt_matches(output.receipt(),*fresh.digest.as_bytes()){return Err(R::Binding);}
        let receipt=StoredCharacterStyleReceipt {source:self.receipt.clone(),output:output.receipt().clone(),profile:STORED_CHARACTER_STYLE_PROFILE,issuer_execution_publication_authority:false};
        provider.check_head(fresh.head).map_err(StoredActualFormImportError::from)?;
        Ok(PreparedStoredCharacterStyleCandidate {source:LiteralSource::Borrowed(self),output,receipt})
    }
    /// # Errors
    /// Move the original owner and candidate, not a clone/reimport to transfer ownership.
    pub fn into_character_style_candidate<Rp,B,S,V>(self,provider:&StoredFormProvider<'_,Rp,B,S,V>,query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,
        filter:SourceReviewStyleFilter,character_property:u32,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredCharacterStyleCandidate<'static>,R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let(output,receipt)={let prepared=self.prepare_character_style_candidate(provider,query,selector,policy,filter,character_property,limits,writer,now)?;
            (prepared.output,prepared.receipt)};
        Ok(PreparedStoredCharacterStyleCandidate {source:LiteralSource::Owned(Box::new(self)),output,receipt})
    }
}
impl PreparedStoredCharacterStyleCandidate<'_> {
    /// # Errors
    /// Reuses original fresh source/integrity/consumer-final head checks, without replaying the search.
    pub fn with_verified_splice_inventory<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,
        consume:impl FnOnce(&hwpx_package::document_import::search::replacement::atoms::styles::intents::SourceStyleSpliceInventory)->T)->Result<T,R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.with_verified_bytes(provider,now,|_|consume(self.output.splice_inventory()))
    }
    #[must_use] pub const fn receipt(&self)->&StoredCharacterStyleReceipt {&self.receipt}
    fn fresh<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(R::Permission);}
        let fresh=self.source.fresh_source(provider,now)?;
        if self.receipt.source!=self.source.receipt||&self.receipt.output!=self.output.receipt()||self.receipt.profile!=STORED_CHARACTER_STYLE_PROFILE
            ||self.receipt.issuer_execution_publication_authority||!source_receipt_matches(&self.receipt.output,*fresh.digest.as_bytes()){return Err(R::Binding);}Ok(())
    }
    /// # Errors
    /// Current access/source, original writer integrity and final head; never replay the mutation.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<StoredCharacterStyleReceipt,R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.fresh(provider,now)?;self.output.with_verified_bytes(|_|()).map_err(|_|R::Integrity)?;
        provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(self.receipt.clone())
    }
    /// # Errors
    /// Final head check remains inside the integrity callback and precedes consumer access.
    pub fn with_verified_bytes<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.fresh(provider,now)?;self.output.with_verified_bytes(|bytes| {
            provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(consume(bytes))
        }).map_err(|_|R::Integrity)?
    }
    /// # Errors
    /// No durable key claim, revision CAS, full style dispatcher or executable route is added.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {self.verify(provider,now)?;Err(R::RouteUnqualified)}
}
