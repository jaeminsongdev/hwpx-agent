//! Current sealed source and retained original width candidate; not commit or execution authority.
use super::*;
compiler_source!(PreparedStoredWidthCandidate);
use super::product::LiteralSource;
use hwpx_package::document_import::search::{selector::SourceIndexScopeSelector,reviews::{SourceReviewTextPolicy,
    selector::styles::SourceReviewStyleFilter},replacement::atoms::width::{SourceWidthConversionCandidate,SourceWidthConversionReceipt,
    SourceWidthMode,SourceWidthPolicy,SourceWidthMatchSearch,SOURCE_WIDTH_CONVERSION_PROFILE}};
pub const STORED_WIDTH_PROFILE:&str="hwpx-agent.stored-width-conversion-candidate/v1";
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct StoredWidthReceipt {pub source:StoredActualFormImportReceipt,pub output:SourceWidthConversionReceipt,
    pub profile:&'static str,pub issuer_execution_publication_authority:bool}
pub struct PreparedStoredWidthCandidate<'a> {source:LiteralSource<'a>,output:SourceWidthConversionCandidate,receipt:StoredWidthReceipt}
impl fmt::Debug for PreparedStoredWidthCandidate<'_> {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {
    f.write_str("PreparedStoredWidthCandidate(<redacted>; current_access_not_full_transaction)")}}
#[derive(Debug,Error)]
pub enum StoredWidthError {
    #[error("STORED_WIDTH_SOURCE_REJECTED")] Source(#[from] StoredActualFormImportError),
    #[error("STORED_WIDTH_OUTPUT_REJECTED")] Output(#[from] SourceLiteralReplacementError),
    #[error("STORED_WIDTH_DOCUMENT_WRITE_REQUIRED")] Permission,
    #[error("STORED_WIDTH_BINDING_REJECTED")] Binding,
    #[error("STORED_WIDTH_INTEGRITY_REJECTED")] Integrity,
    #[error("STORED_WIDTH_PRODUCT_ROUTE_UNQUALIFIED")] RouteUnqualified,
}
type C=StoredWidthError;
pub(crate) fn width_receipt_matches(r:&SourceWidthConversionReceipt,source:[u8;32])->bool {
    let search=r.search.search();let result=search.result();
    r.profile==SOURCE_WIDTH_CONVERSION_PROFILE&&r.source_package_sha256==source&&r.width_unicode_version==(17,0,0)
        &&r.policy==SourceWidthPolicy::Unicode17WidthPairsWithKanaPairs&&r.run_policy==SourceReplacementRunPolicy::FirstOriginalRunRetainAllRuns
        &&r.mapping_source_sha256=="2e1efc1dcb59c575eedf5ccae60f95229f706ee6d031835247d843c11d96470c"&&r.width_pair_count==226&&r.kana_pair_count==28
        &&result.index_receipt().source_package_sha256==source&&result.index_receipt().index_sha256==r.source_index_sha256
        &&search.scope_receipt()==&r.selector&&r.selector.index_sha256==r.source_index_sha256
        &&search.match_regions().len()==result.matches().len()&&!result.matches().is_empty()
        &&result.matches().iter().all(|m|!m.zero_width&&m.source_scalar_selection_exact)
        &&matches!((r.filter,&r.search),(None,SourceWidthMatchSearch::Text(_))|(Some(_),SourceWidthMatchSearch::Style(_)))
        &&r.source_review_import.source_package_sha256==source&&r.output_review_import.source_package_sha256==r.output_package_sha256
        &&r.selected_original_scalars>0&&r.converted_text_groups>0&&r.mapped_scalars>0&&r.changed_components>0
        &&r.changed_scalar_ranges>0&&!r.changes.is_empty()&&r.changed_parts>0&&r.output_bytes>0
        &&r.changes.iter().try_fold(0usize,|n,c|n.checked_add(c.changed_scalar_ranges))==Some(r.changed_scalar_ranges)
        &&r.exact_original_selection_verified&&r.original_run_shells_declared_styles_controls_and_references_preserved&&r.composed_output_uses_first_original_contributor
        &&r.unrelated_compatibility_and_canonical_text_unchanged&&r.output_spans_and_outside_slots_verified
        &&!r.selector.whole_document_visibility_native_flow_or_revision_authority&&!r.general_normalization_icu_native_or_service_authority
}
impl StoredImportedDocumentForms {
    /// # Errors
    /// One current write/source reconstruction and one original matcher/width compiler.
    pub fn prepare_width_candidate<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,body:SourceReviewTextPolicy,
        filter:Option<SourceReviewStyleFilter>,mode:SourceWidthMode,policy:SourceWidthPolicy,run:SourceReplacementRunPolicy,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredWidthCandidate<'_>,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(C::Permission);}
        let(fresh,proof)=self.fresh_source_reconstructed(provider,now)?;
        let output=proof.lower_review_selector_width_candidate(&self.imported,query,selector,body,filter,mode,policy,run,limits,writer)?;
        if !width_receipt_matches(output.receipt(),*fresh.digest.as_bytes()){return Err(C::Binding);}
        let receipt=StoredWidthReceipt {source:self.receipt.clone(),output:output.receipt().clone(),profile:STORED_WIDTH_PROFILE,issuer_execution_publication_authority:false};
        provider.check_head(fresh.head).map_err(StoredActualFormImportError::from)?;
        Ok(PreparedStoredWidthCandidate {source:LiteralSource::Borrowed(self),output,receipt})
    }
    /// # Errors
    /// Move the existing imported owner without clone/reimport or another matcher pass.
    pub fn into_width_candidate<Rp,B,S,V>(self,provider:&StoredFormProvider<'_,Rp,B,S,V>,query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,body:SourceReviewTextPolicy,
        filter:Option<SourceReviewStyleFilter>,mode:SourceWidthMode,policy:SourceWidthPolicy,run:SourceReplacementRunPolicy,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredWidthCandidate<'static>,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let(output,receipt)={let prepared=self.prepare_width_candidate(provider,query,selector,body,filter,mode,policy,run,limits,writer,now)?;(prepared.output,prepared.receipt)};
        Ok(PreparedStoredWidthCandidate {source:LiteralSource::Owned(Box::new(self)),output,receipt})
    }
}
impl PreparedStoredWidthCandidate<'_> {
    #[must_use] pub const fn receipt(&self)->&StoredWidthReceipt {&self.receipt}
    fn fresh<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(C::Permission);}
        let fresh=self.source.fresh_source(provider,now)?;
        if self.receipt.source!=self.source.receipt||&self.receipt.output!=self.output.receipt()||self.receipt.profile!=STORED_WIDTH_PROFILE
            ||self.receipt.issuer_execution_publication_authority||!width_receipt_matches(&self.receipt.output,*fresh.digest.as_bytes()){return Err(C::Binding);}Ok(())
    }
    /// # Errors
    /// Current access/source/writer/final head without rerunning the retained query or mapping.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<StoredWidthReceipt,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.fresh(provider,now)?;self.output.with_verified_bytes(|_|()).map_err(|_|C::Integrity)?;
        provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(self.receipt.clone())
    }
    /// # Errors
    /// The final current head stays inside writer verification before the consumer.
    pub fn with_verified_bytes<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.fresh(provider,now)?;self.output.with_verified_bytes(|bytes| {
            provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(consume(bytes))
        }).map_err(|_|C::Integrity)?
    }
    /// # Errors
    /// Candidate integrity is not a dispatcher, durable key claim, revision CAS or publication.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {self.verify(provider,now)?;Err(C::RouteUnqualified)}
}
