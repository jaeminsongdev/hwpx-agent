//! Current sealed source and retained original case candidate; not commit or execution authority.
use super::*;
compiler_source!(PreparedStoredCaseCandidate);
use super::product::LiteralSource;
use hwpx_package::document_import::search::{selector::SourceIndexScopeSelector,reviews::{SourceReviewTextPolicy,
    selector::styles::SourceReviewStyleFilter},replacement::atoms::case::{SourceCaseConversionCandidate,SourceCaseConversionReceipt,
    SourceCaseMode,SourceCasePolicy,SourceCaseMatchSearch,SOURCE_CASE_CONVERSION_PROFILE}};
pub const STORED_CASE_PROFILE:&str="hwpx-agent.stored-case-conversion-candidate/v1";
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct StoredCaseReceipt {pub source:StoredActualFormImportReceipt,pub output:SourceCaseConversionReceipt,
    pub profile:&'static str,pub issuer_execution_publication_authority:bool}
pub struct PreparedStoredCaseCandidate<'a> {source:LiteralSource<'a>,output:SourceCaseConversionCandidate,receipt:StoredCaseReceipt}
impl fmt::Debug for PreparedStoredCaseCandidate<'_> {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {
    f.write_str("PreparedStoredCaseCandidate(<redacted>; current_access_not_full_transaction)")}}
#[derive(Debug,Error)]
pub enum StoredCaseError {
    #[error("STORED_CASE_SOURCE_REJECTED")] Source(#[from] StoredActualFormImportError),
    #[error("STORED_CASE_OUTPUT_REJECTED")] Output(#[from] SourceLiteralReplacementError),
    #[error("STORED_CASE_DOCUMENT_WRITE_REQUIRED")] Permission,
    #[error("STORED_CASE_BINDING_REJECTED")] Binding,
    #[error("STORED_CASE_INTEGRITY_REJECTED")] Integrity,
    #[error("STORED_CASE_PRODUCT_ROUTE_UNQUALIFIED")] RouteUnqualified,
}
type C=StoredCaseError;
pub(crate) fn case_receipt_matches(r:&SourceCaseConversionReceipt,source:[u8;32])->bool {
    let search=r.search.search();let result=search.result();
    r.profile==SOURCE_CASE_CONVERSION_PROFILE&&r.source_package_sha256==source&&r.case_unicode_version==(17,0,0)
        &&r.case_unicode_version==char::UNICODE_VERSION&&r.policy==SourceCasePolicy::UnicodeDefaultEachMatchedTextGroup
        &&result.index_receipt().source_package_sha256==source&&result.index_receipt().index_sha256==r.source_index_sha256
        &&search.scope_receipt()==&r.selector&&r.selector.index_sha256==r.source_index_sha256
        &&search.match_regions().len()==result.matches().len()&&!result.matches().is_empty()
        &&result.matches().iter().all(|m|!m.zero_width&&m.source_scalar_selection_exact)
        &&matches!((r.filter,&r.search),(None,SourceCaseMatchSearch::Text(_))|(Some(_),SourceCaseMatchSearch::Style(_)))
        &&r.source_review_import.source_package_sha256==source&&r.output_review_import.source_package_sha256==r.output_package_sha256
        &&r.selected_original_scalars>0&&r.converted_text_groups>0&&r.mapped_scalars>0&&r.changed_components>0
        &&r.changed_scalar_ranges>0&&!r.changes.is_empty()&&r.changed_parts>0&&r.output_bytes>0
        &&r.changes.iter().try_fold(0usize,|n,c|n.checked_add(c.changed_scalar_ranges))==Some(r.changed_scalar_ranges)
        &&r.exact_original_selection_verified&&r.every_original_scalar_retains_its_text_atom_style&&r.original_controls_and_reference_shells_preserved
        &&r.whole_string_mapping_and_scalar_partition_verified&&r.output_spans_and_outside_slots_verified
        &&!r.selector.whole_document_visibility_native_flow_or_revision_authority
        &&!r.locale_tailoring_titlecase_casefold_normalization_native_or_service_authority
}
impl StoredImportedDocumentForms {
    /// # Errors
    /// One current write/source reconstruction and one original matcher/case compiler.
    pub fn prepare_case_candidate<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,body:SourceReviewTextPolicy,
        filter:Option<SourceReviewStyleFilter>,mode:SourceCaseMode,policy:SourceCasePolicy,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredCaseCandidate<'_>,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(C::Permission);}
        let(fresh,proof)=self.fresh_source_reconstructed(provider,now)?;
        let output=proof.lower_review_selector_case_candidate(&self.imported,query,selector,body,filter,mode,policy,limits,writer)?;
        if !case_receipt_matches(output.receipt(),*fresh.digest.as_bytes()){return Err(C::Binding);}
        let receipt=StoredCaseReceipt {source:self.receipt.clone(),output:output.receipt().clone(),profile:STORED_CASE_PROFILE,issuer_execution_publication_authority:false};
        provider.check_head(fresh.head).map_err(StoredActualFormImportError::from)?;
        Ok(PreparedStoredCaseCandidate {source:LiteralSource::Borrowed(self),output,receipt})
    }
    /// # Errors
    /// Move the existing imported owner without clone/reimport or another matcher pass.
    pub fn into_case_candidate<Rp,B,S,V>(self,provider:&StoredFormProvider<'_,Rp,B,S,V>,query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,body:SourceReviewTextPolicy,
        filter:Option<SourceReviewStyleFilter>,mode:SourceCaseMode,policy:SourceCasePolicy,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredCaseCandidate<'static>,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let(output,receipt)={let prepared=self.prepare_case_candidate(provider,query,selector,body,filter,mode,policy,limits,writer,now)?;(prepared.output,prepared.receipt)};
        Ok(PreparedStoredCaseCandidate {source:LiteralSource::Owned(Box::new(self)),output,receipt})
    }
}
impl PreparedStoredCaseCandidate<'_> {
    #[must_use] pub const fn receipt(&self)->&StoredCaseReceipt {&self.receipt}
    fn fresh<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(C::Permission);}
        let fresh=self.source.fresh_source(provider,now)?;
        if self.receipt.source!=self.source.receipt||&self.receipt.output!=self.output.receipt()||self.receipt.profile!=STORED_CASE_PROFILE
            ||self.receipt.issuer_execution_publication_authority||!case_receipt_matches(&self.receipt.output,*fresh.digest.as_bytes()){return Err(C::Binding);}Ok(())
    }
    /// # Errors
    /// Current access/source/writer/final head without rerunning the retained query or mapping.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<StoredCaseReceipt,C>
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
