//! Current optional original predicates and output-discarded preview. No execution authority.
use super::*;
use hwpx_package::document_import::search::{reviews::selector::styles::SourceReviewStyleFilter,
    replacement::atoms::styles::paragraphs::named::filtered::{SourceFilteredNamedParagraphStyleCandidate,
        SourceFilteredNamedParagraphStyleReceipt,FILTERED_NAMED_PARAGRAPH_STYLE_PROFILE}};
pub const STORED_NAMED_STYLE_OPTIONS_PROFILE:&str="hwpx-agent.stored-named-paragraph-style-options-candidate/v1";
pub const STORED_NAMED_STYLE_OPTIONS_PREVIEW_PROFILE:&str="hwpx-agent.stored-named-paragraph-style-options-preview/v1";
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
#[serde(tag="kind",content="receipt",rename_all="snake_case")]
pub enum StoredNamedStyleOptionsOutputReceipt{Unfiltered(SourceNamedParagraphStyleReceipt),Filtered(SourceFilteredNamedParagraphStyleReceipt)}
impl StoredNamedStyleOptionsOutputReceipt{
    #[must_use]pub const fn source(&self)->&SourceNamedParagraphStyleReceipt{match self{Self::Unfiltered(r)=>r,Self::Filtered(r)=>&r.source}}
    #[must_use]pub const fn style_filter_ref(&self)->Option<&SourceReviewStyleFilter>{match self{Self::Unfiltered(_)=>None,Self::Filtered(r)=>Some(&r.style_filter.filter)}}
    #[must_use]pub fn style_filter(&self)->Option<SourceReviewStyleFilter>{self.style_filter_ref().cloned()}
    pub(crate) fn matches(&self,source:[u8;32])->bool{
        let original=self.source();if !named_receipt_matches(original,source){return false;}
        match self{Self::Unfiltered(_)=>true,Self::Filtered(r)=>{let f=&r.style_filter;
            r.profile==FILTERED_NAMED_PARAGRAPH_STYLE_PROFILE&&r.request_sha256!=[0;32]&&!r.full_style_native_or_service_authority&&f.filter.validate().is_ok()
                &&f.extent=="all_indexed_source_units_of_whole_paragraph"&&f.selected_paragraphs>=original.matched_paragraphs
                &&f.selected_paragraphs.checked_add(f.filtered_paragraphs).and_then(|n|n.checked_add(f.empty_paragraphs)).is_some_and(|n|n<=original.selector.selected_paragraphs)
                &&f.examined_normalized_units>0&&f.examined_normalized_units<=original.selector.selected_normalized_scalars
                &&f.examined_source_segments>0&&f.examined_source_segments<=f.inspection.text_segments
                &&f.inspection.source_index_sha256==original.source_index_sha256&&f.inspection.inspection_sha256!=[0;32]
                &&!f.effective_style_visibility_or_execution_authority&&!f.inspection.effective_style_or_hidden_visibility_qualified
                &&!f.inspection.control_parameter_or_execution_semantics_qualified
                &&match(&f.filter,&f.definitions){(SourceReviewStyleFilter::Declared(_),None)=>true,
                    (SourceReviewStyleFilter::Definition(_),Some(d))=>d.source_index_sha256==original.source_index_sha256&&d.inspection_sha256==f.inspection.inspection_sha256
                        &&d.all_present_indexed_references_resolved&&!d.implicit_cascade_or_hidden_visibility_qualified,_=>false}
        }}
    }
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct StoredNamedStyleOptionsReceipt{pub profile:&'static str,pub source:StoredActualFormImportReceipt,pub output:StoredNamedStyleOptionsOutputReceipt,
    pub preview_only:bool,pub candidate_output_retained:bool,pub issuer_execution_publication_authority:bool}
enum Output{Unfiltered(SourceNamedParagraphStyleCandidate),Filtered(SourceFilteredNamedParagraphStyleCandidate)}
impl Output{
    fn receipt(&self)->StoredNamedStyleOptionsOutputReceipt{match self{Self::Unfiltered(c)=>StoredNamedStyleOptionsOutputReceipt::Unfiltered(c.receipt().clone()),Self::Filtered(c)=>StoredNamedStyleOptionsOutputReceipt::Filtered(c.receipt().clone())}}
    fn with_bytes<T>(&self,consume:impl FnOnce(&[u8])->T)->Result<T,hwpx_package::WriterError>{match self{Self::Unfiltered(c)=>c.with_verified_bytes(consume),Self::Filtered(c)=>c.with_verified_bytes(consume)}}
}
pub struct PreparedStoredNamedStyleOptionsCandidate<'a>{source:LiteralSource<'a>,output:Output,receipt:StoredNamedStyleOptionsReceipt}
compiler_source!(PreparedStoredNamedStyleOptionsCandidate);
pub struct PreparedStoredNamedStyleOptionsPreview<'a>{source:LiteralSource<'a>,receipt:StoredNamedStyleOptionsReceipt}
impl fmt::Debug for PreparedStoredNamedStyleOptionsCandidate<'_>{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedStoredNamedStyleOptionsCandidate(<redacted>; not_execution)")}}
impl fmt::Debug for PreparedStoredNamedStyleOptionsPreview<'_>{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedStoredNamedStyleOptionsPreview(<redacted>; output_discarded)")}}
impl StoredImportedDocumentForms{
    /// # Errors
    /// One current write/source proof and original filtered or unfiltered output; final head retained.
    pub fn prepare_named_style_options_candidate<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,query:SourceNamedParagraphStyleQuery<'_>,selector:SourceIndexScopeSelector<'_>,
        policy:SourceReviewTextPolicy,filter:Option<SourceReviewStyleFilter>,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredNamedStyleOptionsCandidate<'_>,N>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(N::Permission);}
        if let Some(f)=&filter{f.validate().map_err(SourceNamedParagraphStyleError::from)?;}query.validate()?;
        if query.query.len()>limits.maximum_query_bytes()||query.replacement.len()>limits.maximum_query_bytes(){return Err(SourceNamedParagraphStyleError::Limit.into());}
        let(fresh,proof)=self.fresh_source_reconstructed(provider,now)?;
        let output=match filter{None=>Output::Unfiltered(proof.lower_named_paragraph_style_candidate(&self.imported,query,selector,policy,limits,writer)?),
            Some(f)=>Output::Filtered(proof.lower_filtered_named_paragraph_style_candidate(&self.imported,query,selector,policy,f,limits,writer)?)};
        let metadata=output.receipt();if !metadata.matches(*fresh.digest.as_bytes()){return Err(N::Binding);}
        let receipt=StoredNamedStyleOptionsReceipt{profile:STORED_NAMED_STYLE_OPTIONS_PROFILE,source:self.receipt.clone(),output:metadata,preview_only:false,candidate_output_retained:true,issuer_execution_publication_authority:false};
        provider.check_head(fresh.head).map_err(StoredActualFormImportError::from)?;Ok(PreparedStoredNamedStyleOptionsCandidate{source:LiteralSource::Borrowed(self),output,receipt})
    }
    /// # Errors
    /// Moves the original owner after shared preparation, without cloning or rerunning matching/writer.
    pub fn into_named_style_options_candidate<Rp,B,S,V>(self,provider:&StoredFormProvider<'_,Rp,B,S,V>,query:SourceNamedParagraphStyleQuery<'_>,selector:SourceIndexScopeSelector<'_>,
        policy:SourceReviewTextPolicy,filter:Option<SourceReviewStyleFilter>,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredNamedStyleOptionsCandidate<'static>,N>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let(output,receipt)={let c=self.prepare_named_style_options_candidate(provider,query,selector,policy,filter,limits,writer,now)?;(c.output,c.receipt)};
        Ok(PreparedStoredNamedStyleOptionsCandidate{source:LiteralSource::Owned(Box::new(self)),output,receipt})
    }
}
fn fresh<Rp,B,S,V>(source:&StoredImportedDocumentForms,receipt:&StoredNamedStyleOptionsReceipt,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,preview:bool)->Result<(),N>
where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
    if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(N::Permission);}let current=source.fresh_source(provider,now)?;
    let profile=if preview{STORED_NAMED_STYLE_OPTIONS_PREVIEW_PROFILE}else{STORED_NAMED_STYLE_OPTIONS_PROFILE};
    if receipt.profile!=profile||receipt.source!=source.receipt||receipt.preview_only!=preview||receipt.candidate_output_retained==preview
        ||receipt.issuer_execution_publication_authority||!receipt.output.matches(*current.digest.as_bytes()){return Err(N::Binding);}Ok(())
}
impl<'a> PreparedStoredNamedStyleOptionsCandidate<'a>{
    #[must_use]pub const fn receipt(&self)->&StoredNamedStyleOptionsReceipt{&self.receipt}
    /// Consumes the candidate and drops the artifact. No bytes/inventory/compiler API exists on preview.
    #[must_use]pub fn into_preview(self)->PreparedStoredNamedStyleOptionsPreview<'a>{let Self{source,output,mut receipt}=self;drop(output);
        receipt.profile=STORED_NAMED_STYLE_OPTIONS_PREVIEW_PROFILE;receipt.preview_only=true;receipt.candidate_output_retained=false;PreparedStoredNamedStyleOptionsPreview{source,receipt}}
    /// # Errors
    /// Same current source/ACL/head/AEAD and retained writer integrity; consumer-final head is inside callback.
    pub fn with_verified_bytes<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,N>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        fresh(&self.source,&self.receipt,provider,now,false)?;if self.receipt.output!=self.output.receipt(){return Err(N::Binding);}
        self.output.with_bytes(|bytes|{provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(consume(bytes))}).map_err(|_|N::Integrity)?
    }
    /// # Errors
    /// No reconstruction, query, filter or writer replay on retained verification.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<StoredNamedStyleOptionsReceipt,N>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.with_verified_bytes(provider,now,|_|())?;Ok(self.receipt.clone())}
    /// # Errors
    /// A current valid candidate is not a qualified route, CAS or publication capability.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),N>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.verify(provider,now)?;Err(N::RouteUnqualified)}
}
impl PreparedStoredNamedStyleOptionsPreview<'_>{
    #[must_use]pub const fn receipt(&self)->&StoredNamedStyleOptionsReceipt{&self.receipt}
    /// # Errors
    /// Metadata only after current source/access and the last head, not retained output verification.
    pub fn with_verified_metadata<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&StoredNamedStyleOptionsReceipt)->T)->Result<T,N>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        fresh(&self.source,&self.receipt,provider,now,true)?;provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(consume(&self.receipt))
    }
    /// # Errors
    /// Current source only; predicted output is not a saved or executed artifact.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<StoredNamedStyleOptionsReceipt,N>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.with_verified_metadata(provider,now,Clone::clone)}
    /// # Errors
    /// A preview never authorizes execution, commit or publication.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),N>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.verify(provider,now)?;Err(N::RouteUnqualified)}
}
