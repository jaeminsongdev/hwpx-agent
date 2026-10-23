//! Current sealed source -> explicit whole-paragraph reference candidate, not a revision commit.
use super::*;
compiler_source!(PreparedStoredParagraphStyleCandidate);
use super::product::LiteralSource;
use hwpx_package::document_import::search::{selector::SourceIndexScopeSelector,reviews::{SourceReviewTextPolicy,selector::styles::SourceReviewStyleFilter},
    replacement::atoms::styles::paragraphs::{SourceParagraphStyleReplacementCandidate,SourceParagraphStyleReplacementReceipt,SourceParagraphStyleReplacementError,
        SourceParagraphStyleTarget,SourceParagraphStyleExtent,SOURCE_PARAGRAPH_STYLE_REPLACEMENT_PROFILE}};
pub const STORED_PARAGRAPH_STYLE_PROFILE:&str="hwpx-agent.stored-paragraph-style-candidate/v1";
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct StoredParagraphStyleReceipt {pub source:StoredActualFormImportReceipt,pub output:SourceParagraphStyleReplacementReceipt,
    pub profile:&'static str,pub issuer_execution_publication_authority:bool}
pub struct PreparedStoredParagraphStyleCandidate<'a> {source:LiteralSource<'a>,output:SourceParagraphStyleReplacementCandidate,receipt:StoredParagraphStyleReceipt}
impl fmt::Debug for PreparedStoredParagraphStyleCandidate<'_> {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("PreparedStoredParagraphStyleCandidate(<redacted>; not_CAS_or_product_route)")}}
#[derive(Debug,Error)]
pub enum StoredParagraphStyleError {
    #[error("STORED_PARAGRAPH_STYLE_SOURCE_REJECTED")] Source(#[from] StoredActualFormImportError),
    #[error("STORED_PARAGRAPH_STYLE_OUTPUT_REJECTED")] Output(#[from] SourceParagraphStyleReplacementError),
    #[error("STORED_PARAGRAPH_STYLE_DOCUMENT_WRITE_REQUIRED")] Permission,
    #[error("STORED_PARAGRAPH_STYLE_BINDING_REJECTED")] Binding,
    #[error("STORED_PARAGRAPH_STYLE_INTEGRITY_REJECTED")] Integrity,
    #[error("STORED_PARAGRAPH_STYLE_PRODUCT_ROUTE_UNQUALIFIED")] RouteUnqualified,
}
type R=StoredParagraphStyleError;
pub(crate) fn source_receipt_matches(r:&SourceParagraphStyleReplacementReceipt,source_sha256:[u8;32])->bool {
    r.profile==SOURCE_PARAGRAPH_STYLE_REPLACEMENT_PROFILE&&r.source_package_sha256==source_sha256
        &&r.selector.index_sha256==r.source_index_sha256&&r.source_review_import.source_package_sha256==source_sha256
        &&r.output_review_import.source_package_sha256==r.output_package_sha256&&r.match_regions.len()==r.matched_occurrences
        &&r.matched_occurrences>0&&r.matched_paragraphs>0&&r.matched_paragraphs<=r.matched_occurrences
        &&!r.changes.is_empty()&&r.changes.len()<=r.matched_paragraphs&&r.changed_parts>0&&r.compiled_attribute_bytes>0&&r.output_bytes>0
        &&r.changes.iter().all(|c|c.target_reference==r.target.declaration_id()&&c.previous_reference!=Some(c.target_reference))
        &&r.extent==SourceParagraphStyleExtent::WholeMatchedParagraphWithinScope&&r.whole_paragraph_scope_verified
        &&r.all_original_scalars_controls_run_and_text_references_preserved&&r.every_paragraph_reference_read_back&&r.outside_selected_attribute_edits_exact
        &&!r.selector.whole_document_visibility_native_flow_or_revision_authority&&!r.effective_style_native_or_service_authority
}
impl StoredImportedDocumentForms {
    /// # Errors
    /// Current write/source and one original Form proof for both explicit paragraph axes.
    pub fn prepare_paragraph_style_candidate<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,
        filter:SourceReviewStyleFilter,target:SourceParagraphStyleTarget,extent:SourceParagraphStyleExtent,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredParagraphStyleCandidate<'_>,R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(R::Permission);}
        let(fresh,proof)=self.fresh_source_reconstructed(provider,now)?;
        let output=proof.lower_review_selector_paragraph_style_candidate(&self.imported,query,selector,policy,filter,target,extent,limits,writer)?;
        if !source_receipt_matches(output.receipt(),*fresh.digest.as_bytes()){return Err(R::Binding);}
        let receipt=StoredParagraphStyleReceipt {source:self.receipt.clone(),output:output.receipt().clone(),profile:STORED_PARAGRAPH_STYLE_PROFILE,issuer_execution_publication_authority:false};
        provider.check_head(fresh.head).map_err(StoredActualFormImportError::from)?;
        Ok(PreparedStoredParagraphStyleCandidate {source:LiteralSource::Borrowed(self),output,receipt})
    }
    /// # Errors
    /// Move the original owner using the existing Borrowed/Owned boundary without clone/reimport.
    pub fn into_paragraph_style_candidate<Rp,B,S,V>(self,provider:&StoredFormProvider<'_,Rp,B,S,V>,query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,
        filter:SourceReviewStyleFilter,target:SourceParagraphStyleTarget,extent:SourceParagraphStyleExtent,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredParagraphStyleCandidate<'static>,R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let(output,receipt)={let prepared=self.prepare_paragraph_style_candidate(provider,query,selector,policy,filter,target,extent,limits,writer,now)?;
            (prepared.output,prepared.receipt)};
        Ok(PreparedStoredParagraphStyleCandidate {source:LiteralSource::Owned(Box::new(self)),output,receipt})
    }
}
impl PreparedStoredParagraphStyleCandidate<'_> {
    #[must_use] pub const fn receipt(&self)->&StoredParagraphStyleReceipt {&self.receipt}
    fn fresh<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(R::Permission);}
        let fresh=self.source.fresh_source(provider,now)?;
        if self.receipt.source!=self.source.receipt||&self.receipt.output!=self.output.receipt()||self.receipt.profile!=STORED_PARAGRAPH_STYLE_PROFILE
            ||self.receipt.issuer_execution_publication_authority||!source_receipt_matches(&self.receipt.output,*fresh.digest.as_bytes()){return Err(R::Binding);}Ok(())
    }
    /// # Errors
    /// Current access/source, original writer integrity and final head, not repeated search/lowering.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<StoredParagraphStyleReceipt,R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.fresh(provider,now)?;self.output.with_verified_bytes(|_|()).map_err(|_|R::Integrity)?;
        provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(self.receipt.clone())
    }
    /// # Errors
    /// The final head check is inside the original writer-integrity callback, before the consumer.
    pub fn with_verified_bytes<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.fresh(provider,now)?;self.output.with_verified_bytes(|bytes| {
            provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(consume(bytes))
        }).map_err(|_|R::Integrity)?
    }
    /// # Errors
    /// No durable key claim, revision CAS, Native execution or publication route.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {self.verify(provider,now)?;Err(R::RouteUnqualified)}
}
