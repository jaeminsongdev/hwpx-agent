//! Current sealed source -> private explicit text-style candidate, not revision execution.
use super::*;
compiler_source!(PreparedStoredTextStyleCandidate, style);
use super::product::LiteralSource;
use hwpx_package::document_import::search::{selector::SourceIndexScopeSelector,reviews::{SourceReviewTextPolicy,selector::styles::SourceReviewStyleFilter},
    replacement::atoms::styles::{SourceStyleReplacementError,text::{SourceTextStyleReplacementCandidate,SourceTextStyleReplacementReceipt,SOURCE_TEXT_STYLE_REPLACEMENT_PROFILE}}};
pub const STORED_TEXT_STYLE_PROFILE:&str="hwpx-agent.stored-text-style-candidate/v1";
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct StoredTextStyleReceipt {pub source:StoredActualFormImportReceipt,pub output:SourceTextStyleReplacementReceipt,
    pub profile:&'static str,pub issuer_execution_publication_authority:bool}
pub struct PreparedStoredTextStyleCandidate<'a> {source:LiteralSource<'a>,output:SourceTextStyleReplacementCandidate,receipt:StoredTextStyleReceipt}
impl fmt::Debug for PreparedStoredTextStyleCandidate<'_> {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("PreparedStoredTextStyleCandidate(<redacted>; not_CAS_or_product_route)")}}
#[derive(Debug,Error)]
pub enum StoredTextStyleError {
    #[error("STORED_TEXT_STYLE_SOURCE_REJECTED")] Source(#[from] StoredActualFormImportError),
    #[error("STORED_TEXT_STYLE_OUTPUT_REJECTED")] Output(#[from] SourceStyleReplacementError),
    #[error("STORED_TEXT_STYLE_DOCUMENT_WRITE_REQUIRED")] Permission,
    #[error("STORED_TEXT_STYLE_BINDING_REJECTED")] Binding,
    #[error("STORED_TEXT_STYLE_INTEGRITY_REJECTED")] Integrity,
    #[error("STORED_TEXT_STYLE_PRODUCT_ROUTE_UNQUALIFIED")] RouteUnqualified,
}
type R=StoredTextStyleError;
pub(crate) fn source_receipt_matches(r:&SourceTextStyleReplacementReceipt,source_sha256:[u8;32])->bool {
    r.profile==SOURCE_TEXT_STYLE_REPLACEMENT_PROFILE&&r.source_package_sha256==source_sha256
        &&r.selector.index_sha256==r.source_index_sha256&&r.source_review_import.source_package_sha256==source_sha256
        &&r.output_review_import.source_package_sha256==r.output_package_sha256&&r.match_regions.len()==r.matched_occurrences
        &&r.matched_occurrences>0&&r.original_changed_text_elements>0&&r.generated_text_fragments>=r.original_changed_text_elements
        &&r.changed_source_scalar_ranges>0&&r.changed_parts>0&&r.compiled_fragment_bytes>0&&r.output_bytes>0
        &&r.original_scalars_controls_and_run_references_preserved&&r.every_original_scalar_text_style_read_back
        &&r.outside_original_text_edits_exact&&r.original_run_boundaries_preserved
        &&!r.selector.whole_document_visibility_native_flow_or_revision_authority&&!r.effective_paragraph_named_style_native_or_service_authority
}
impl StoredImportedDocumentForms {
    /// # Errors
    /// Current write/scope/source and one original Form proof for the complete text-style batch.
    pub fn prepare_text_style_candidate<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,
        filter:SourceReviewStyleFilter,text_character_style:u32,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredTextStyleCandidate<'_>,R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(R::Permission);}
        let(fresh,proof)=self.fresh_source_reconstructed(provider,now)?;
        let output=proof.lower_review_selector_text_style_candidate(&self.imported,query,selector,policy,filter,text_character_style,limits,writer)?;
        if !source_receipt_matches(output.receipt(),*fresh.digest.as_bytes()){return Err(R::Binding);}
        let receipt=StoredTextStyleReceipt {source:self.receipt.clone(),output:output.receipt().clone(),profile:STORED_TEXT_STYLE_PROFILE,issuer_execution_publication_authority:false};
        provider.check_head(fresh.head).map_err(StoredActualFormImportError::from)?;
        Ok(PreparedStoredTextStyleCandidate {source:LiteralSource::Borrowed(self),output,receipt})
    }
    /// # Errors
    /// Move the original owner using the existing Borrowed/Owned boundary without clone/reimport.
    pub fn into_text_style_candidate<Rp,B,S,V>(self,provider:&StoredFormProvider<'_,Rp,B,S,V>,query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,
        filter:SourceReviewStyleFilter,text_character_style:u32,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredTextStyleCandidate<'static>,R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let(output,receipt)={let prepared=self.prepare_text_style_candidate(provider,query,selector,policy,filter,text_character_style,limits,writer,now)?;
            (prepared.output,prepared.receipt)};
        Ok(PreparedStoredTextStyleCandidate {source:LiteralSource::Owned(Box::new(self)),output,receipt})
    }
}
impl PreparedStoredTextStyleCandidate<'_> {
    /// # Errors
    /// Reuses original fresh source/integrity/consumer-final head checks, without replaying the search.
    pub fn with_verified_splice_inventory<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,
        consume:impl FnOnce(&hwpx_package::document_import::search::replacement::atoms::styles::intents::SourceStyleSpliceInventory)->T)->Result<T,R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.with_verified_bytes(provider,now,|_|consume(self.output.splice_inventory()))
    }
    #[must_use] pub const fn receipt(&self)->&StoredTextStyleReceipt {&self.receipt}
    fn fresh<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(R::Permission);}
        let fresh=self.source.fresh_source(provider,now)?;
        if self.receipt.source!=self.source.receipt||&self.receipt.output!=self.output.receipt()||self.receipt.profile!=STORED_TEXT_STYLE_PROFILE
            ||self.receipt.issuer_execution_publication_authority||!source_receipt_matches(&self.receipt.output,*fresh.digest.as_bytes()){return Err(R::Binding);}Ok(())
    }
    /// # Errors
    /// Current access/source, original writer integrity and final head, not a repeated source lowering.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<StoredTextStyleReceipt,R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.fresh(provider,now)?;self.output.with_verified_bytes(|_|()).map_err(|_|R::Integrity)?;
        provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(self.receipt.clone())
    }
    /// # Errors
    /// The final head check is inside the original integrity callback, before the consumer.
    pub fn with_verified_bytes<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.fresh(provider,now)?;self.output.with_verified_bytes(|bytes| {
            provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(consume(bytes))
        }).map_err(|_|R::Integrity)?
    }
    /// # Errors
    /// No dispatcher, revision CAS, durable idempotency claim, Native or publication route.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {self.verify(provider,now)?;Err(R::RouteUnqualified)}
}
