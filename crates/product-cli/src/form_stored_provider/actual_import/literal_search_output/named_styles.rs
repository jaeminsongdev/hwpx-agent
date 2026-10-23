//! Current sealed source -> named PARA reference batch or discard-on-preview metadata.
pub mod options;
use super::*;
use super::product::LiteralSource;
use std::collections::BTreeSet;
use hwpx_package::document_import::search::{selector::SourceIndexScopeSelector,reviews::SourceReviewTextPolicy,
    replacement::atoms::styles::paragraphs::named::{SourceNamedParagraphStyleQuery,SourceNamedParagraphStyleCandidate,
        SourceNamedParagraphStyleReceipt,SourceNamedParagraphStyleError,NAMED_PARAGRAPH_STYLE_PROFILE}};
pub const STORED_NAMED_STYLE_PROFILE:&str="hwpx-agent.stored-named-paragraph-style-candidate/v1";
pub const STORED_NAMED_STYLE_PREVIEW_PROFILE:&str="hwpx-agent.stored-named-paragraph-style-preview/v1";
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct StoredNamedStyleReceipt{pub profile:&'static str,pub source:StoredActualFormImportReceipt,pub output:SourceNamedParagraphStyleReceipt,
    pub preview_only:bool,pub candidate_output_retained:bool,pub issuer_execution_publication_authority:bool}
pub struct PreparedStoredNamedStyleCandidate<'a>{source:LiteralSource<'a>,output:SourceNamedParagraphStyleCandidate,receipt:StoredNamedStyleReceipt}
pub struct PreparedStoredNamedStylePreview<'a>{source:LiteralSource<'a>,receipt:StoredNamedStyleReceipt}
impl fmt::Debug for PreparedStoredNamedStyleCandidate<'_>{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedStoredNamedStyleCandidate(<redacted>; not_execution)")}}
impl fmt::Debug for PreparedStoredNamedStylePreview<'_>{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedStoredNamedStylePreview(<redacted>; output_discarded)")}}
#[derive(Debug,Error)]
pub enum StoredNamedStyleError{
    #[error("STORED_NAMED_STYLE_SOURCE_REJECTED")]Source(#[from]StoredActualFormImportError),
    #[error("STORED_NAMED_STYLE_OUTPUT_REJECTED")]Output(#[from]SourceNamedParagraphStyleError),
    #[error("STORED_NAMED_STYLE_WRITE_SCOPE_REQUIRED")]Permission,
    #[error("STORED_NAMED_STYLE_BINDING_REJECTED")]Binding,
    #[error("STORED_NAMED_STYLE_INTEGRITY_REJECTED")]Integrity,
    #[error("STORED_NAMED_STYLE_ROUTE_UNQUALIFIED")]RouteUnqualified,
}
type N=StoredNamedStyleError;
compiler_source!(PreparedStoredNamedStyleCandidate);
pub(crate) fn named_receipt_matches(r:&SourceNamedParagraphStyleReceipt,source:[u8;32])->bool{
    r.profile==NAMED_PARAGRAPH_STYLE_PROFILE&&r.source_package_sha256==source&&source!=[0;32]
        &&r.source_catalog_sha256!=[0;32]&&r.source_index_sha256!=[0;32]&&r.query_sha256!=[0;32]&&r.request_sha256!=[0;32]
        &&r.selector.index_sha256==r.source_index_sha256&&r.selector.scope_sha256!=[0;32]&&r.selector.selected_paragraphs>=r.matched_paragraphs
        &&r.source_review_import.source_package_sha256==source&&r.output_review_import.source_package_sha256==r.output_package_sha256
        &&r.matched_declarations>0&&r.matched_declarations<=128&&!r.from_style_ids.is_empty()&&r.from_style_ids.len()<=r.matched_declarations
        &&r.from_style_ids.windows(2).all(|p|p[0]<p[1])&&r.from_style_ids.binary_search(&r.target_style_id).is_err()
        &&r.matched_paragraphs>0&&r.changes.len()==r.matched_paragraphs&&r.changed_parts>0&&r.changed_parts<=r.changes.len()&&r.compiled_attribute_bytes>0
        &&r.changes.iter().all(|c|c.target_reference==r.target_style_id&&c.previous_reference.is_some_and(|v|r.from_style_ids.binary_search(&v).is_ok()))
        &&r.changes.iter().map(|c|&c.paragraph_anchor.opaque_handle).collect::<BTreeSet<_>>().len()==r.changes.len()
        &&r.output_package_sha256!=source&&r.output_package_sha256!=[0;32]&&r.output_bytes>0
        &&r.original_declarations_and_nonselected_references_preserved&&r.original_text_controls_run_and_text_references_preserved
        &&!r.full_style_filter_character_style_native_or_execution_qualified&&!r.selector.whole_document_visibility_native_flow_or_revision_authority
}
impl StoredImportedDocumentForms{
    /// # Errors
    /// Current write/ACL/head/AEAD and one source reconstruction precede the original named batch.
    pub fn prepare_named_style_candidate<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,query:SourceNamedParagraphStyleQuery<'_>,selector:SourceIndexScopeSelector<'_>,
        policy:SourceReviewTextPolicy,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredNamedStyleCandidate<'_>,N>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(N::Permission);}
        query.validate()?;if query.query.len()>limits.maximum_query_bytes()||query.replacement.len()>limits.maximum_query_bytes(){return Err(SourceNamedParagraphStyleError::Limit.into());}
        let(fresh,proof)=self.fresh_source_reconstructed(provider,now)?;
        let output=proof.lower_named_paragraph_style_candidate(&self.imported,query,selector,policy,limits,writer)?;
        if !named_receipt_matches(output.receipt(),*fresh.digest.as_bytes()){return Err(N::Binding);}
        let receipt=StoredNamedStyleReceipt{profile:STORED_NAMED_STYLE_PROFILE,source:self.receipt.clone(),output:output.receipt().clone(),preview_only:false,
            candidate_output_retained:true,issuer_execution_publication_authority:false};
        provider.check_head(fresh.head).map_err(StoredActualFormImportError::from)?;
        Ok(PreparedStoredNamedStyleCandidate{source:LiteralSource::Borrowed(self),output,receipt})
    }
    /// # Errors
    /// Move the original owner after shared preparation, without a source clone or matcher replay.
    pub fn into_named_style_candidate<Rp,B,S,V>(self,provider:&StoredFormProvider<'_,Rp,B,S,V>,query:SourceNamedParagraphStyleQuery<'_>,selector:SourceIndexScopeSelector<'_>,
        policy:SourceReviewTextPolicy,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredNamedStyleCandidate<'static>,N>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let(output,receipt)={let prepared=self.prepare_named_style_candidate(provider,query,selector,policy,limits,writer,now)?;(prepared.output,prepared.receipt)};
        Ok(PreparedStoredNamedStyleCandidate{source:LiteralSource::Owned(Box::new(self)),output,receipt})
    }
}
fn fresh<Rp,B,S,V>(source:&StoredImportedDocumentForms,receipt:&StoredNamedStyleReceipt,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,preview:bool)->Result<(),N>
where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
    if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(N::Permission);}
    let current=source.fresh_source(provider,now)?;
    let profile=if preview{STORED_NAMED_STYLE_PREVIEW_PROFILE}else{STORED_NAMED_STYLE_PROFILE};
    if receipt.profile!=profile||receipt.source!=source.receipt||receipt.preview_only!=preview||receipt.candidate_output_retained==preview
        ||receipt.issuer_execution_publication_authority||!named_receipt_matches(&receipt.output,*current.digest.as_bytes()){return Err(N::Binding);}Ok(())
}
impl<'a> PreparedStoredNamedStyleCandidate<'a>{
    #[must_use]pub const fn receipt(&self)->&StoredNamedStyleReceipt{&self.receipt}
    /// Discards the output artifact. The result has no bytes/inventory/compiler API or reverse conversion.
    #[must_use]pub fn into_preview(self)->PreparedStoredNamedStylePreview<'a>{
        let Self{source,output,mut receipt}=self;drop(output);receipt.profile=STORED_NAMED_STYLE_PREVIEW_PROFILE;receipt.preview_only=true;receipt.candidate_output_retained=false;
        PreparedStoredNamedStylePreview{source,receipt}
    }
    /// # Errors
    /// Current source and retained writer integrity with a consumer-final head check.
    pub fn with_verified_bytes<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,N>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        fresh(&self.source,&self.receipt,provider,now,false)?;if &self.receipt.output!=self.output.receipt(){return Err(N::Binding);}
        self.output.with_verified_bytes(|bytes|{provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(consume(bytes))}).map_err(|_|N::Integrity)?
    }
    /// # Errors
    /// No source reconstruction, name matching or lowering replay on retained verification.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<StoredNamedStyleReceipt,N>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.with_verified_bytes(provider,now,|_|())?;Ok(self.receipt.clone())}
    /// # Errors
    /// Current candidate integrity is not qualified execution/CAS/publication.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),N>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.verify(provider,now)?;Err(N::RouteUnqualified)}
}
impl PreparedStoredNamedStylePreview<'_>{
    #[must_use]pub const fn receipt(&self)->&StoredNamedStyleReceipt{&self.receipt}
    /// # Errors
    /// Predicted metadata only, after current source/write/ACL/AEAD and the final head.
    pub fn with_verified_metadata<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&StoredNamedStyleReceipt)->T)->Result<T,N>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        fresh(&self.source,&self.receipt,provider,now,true)?;provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(consume(&self.receipt))
    }
    /// # Errors
    /// Verifies current source, not a retained output artifact or executed mutation.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<StoredNamedStyleReceipt,N>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.with_verified_metadata(provider,now,Clone::clone)}
    /// # Errors
    /// A preview can never execute, commit or publish.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),N>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.verify(provider,now)?;Err(N::RouteUnqualified)}
}
