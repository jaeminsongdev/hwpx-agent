//! Current source-bound optional filter and discard-on-preview boundary; never an execution grant.
use super::*;
use hwpx_package::document_import::search::{reviews::selector::styles::SourceReviewStyleFilter,
    replacement::atoms::styles::fonts::filtered::{SourceFontFilteredReplacementCandidate,
        SourceFontFilteredReplacementReceipt,FILTERED_FONT_REPLACEMENT_PROFILE}};
pub const STORED_FONT_OPTIONS_PROFILE:&str="hwpx-agent.stored-scoped-font-options-candidate/v1";
pub const STORED_FONT_PREVIEW_PROFILE:&str="hwpx-agent.stored-scoped-font-preview/v1";
pub const FONT_PREVIEW_MAX_JSON_BYTES:usize=64*1024;

#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
#[serde(tag="kind",content="receipt",rename_all="snake_case")]
pub enum StoredFontOptionsOutputReceipt{Unfiltered(SourceFontReplacementReceipt),Filtered(SourceFontFilteredReplacementReceipt)}
impl StoredFontOptionsOutputReceipt{
    #[must_use]pub const fn source(&self)->&SourceFontReplacementReceipt{match self{Self::Unfiltered(r)=>r,Self::Filtered(r)=>&r.source}}
    #[must_use]pub const fn style_filter_ref(&self)->Option<&SourceReviewStyleFilter>{match self{Self::Unfiltered(_)=>None,Self::Filtered(r)=>Some(&r.style_filter.filter)}}
    #[must_use]pub fn style_filter(&self)->Option<SourceReviewStyleFilter>{self.style_filter_ref().cloned()}
    fn matches(&self,source:[u8;32])->bool{
        let original=self.source();if !font_receipt_matches(original,source){return false;}
        match self{
            Self::Unfiltered(_)=>true,
            Self::Filtered(r)=>{let f=&r.style_filter;
                r.profile==FILTERED_FONT_REPLACEMENT_PROFILE&&r.request_sha256!=[0;32]&&!r.service_execution_or_native_qualified&&f.filter.validate().is_ok()
                    &&f.selected_normalized_units>0&&f.selected_normalized_units.checked_add(f.filtered_normalized_units).is_some_and(|n|n<=original.selector.selected_normalized_scalars)
                    &&f.selected_source_points>=original.changed_source_scalars&&f.inspection.source_index_sha256==original.source_index_sha256
                    &&!f.effective_style_visibility_or_execution_authority&&!f.inspection.effective_style_or_hidden_visibility_qualified
                    &&!f.inspection.control_parameter_or_execution_semantics_qualified
                    &&match(&f.filter,&f.definitions){(SourceReviewStyleFilter::Declared(_),None)=>true,
                        (SourceReviewStyleFilter::Definition(_),Some(d))=>d.source_index_sha256==original.source_index_sha256
                            &&d.inspection_sha256==f.inspection.inspection_sha256&&d.all_present_indexed_references_resolved&&!d.implicit_cascade_or_hidden_visibility_qualified,
                        _=>false}
            }
        }
    }
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct StoredFontOptionsReceipt{pub profile:&'static str,pub source:StoredActualFormImportReceipt,pub output:StoredFontOptionsOutputReceipt,
    pub preview_only:bool,pub candidate_output_retained:bool,pub issuer_execution_publication_authority:bool}
enum Output{Unfiltered(SourceFontReplacementCandidate),Filtered(SourceFontFilteredReplacementCandidate)}
impl Output{
    fn receipt(&self)->StoredFontOptionsOutputReceipt{match self{Self::Unfiltered(c)=>StoredFontOptionsOutputReceipt::Unfiltered(c.receipt().clone()),Self::Filtered(c)=>StoredFontOptionsOutputReceipt::Filtered(c.receipt().clone())}}
    fn with_bytes<T>(&self,consume:impl FnOnce(&[u8])->T)->Result<T,hwpx_package::WriterError>{match self{Self::Unfiltered(c)=>c.with_verified_bytes(consume),Self::Filtered(c)=>c.with_verified_bytes(consume)}}
}
pub struct PreparedStoredFontOptionsCandidate<'a>{source:LiteralSource<'a>,output:Output,receipt:StoredFontOptionsReceipt}
compiler_source!(PreparedStoredFontOptionsCandidate);
pub struct PreparedStoredFontPreview<'a>{source:LiteralSource<'a>,receipt:StoredFontOptionsReceipt}
impl fmt::Debug for PreparedStoredFontOptionsCandidate<'_>{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedStoredFontOptionsCandidate(<redacted>; not_execution)")}}
impl fmt::Debug for PreparedStoredFontPreview<'_>{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedStoredFontPreview(<redacted>; output_discarded)")}}

impl StoredImportedDocumentForms{
    /// # Errors
    /// Same current write/source proof and final head as v1; a filter never supplies authority.
    pub fn prepare_font_options_candidate<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,query:FontNameReplacementQuery<'_>,selector:SourceIndexScopeSelector<'_>,
        body:SourceReviewTextPolicy,axis:SourceFontStyleAxis,filter:Option<SourceReviewStyleFilter>,limits:SourceSearchLimits,writer:WriterLimits,now:u64)
        ->Result<PreparedStoredFontOptionsCandidate<'_>,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(C::Permission);}
        if let Some(f)=&filter{f.validate().map_err(SourceFontReplacementError::from)?;}
        let(fresh,proof)=self.fresh_source_reconstructed(provider,now)?;
        let output=match filter{
            None=>Output::Unfiltered(proof.lower_scoped_font_candidate(&self.imported,query,selector,body,axis,limits,writer)?),
            Some(f)=>Output::Filtered(proof.lower_scoped_font_filtered_candidate(&self.imported,query,selector,body,axis,f,limits,writer)?),
        };let metadata=output.receipt();if !metadata.matches(*fresh.digest.as_bytes()){return Err(C::Binding);}
        let receipt=StoredFontOptionsReceipt{profile:STORED_FONT_OPTIONS_PROFILE,source:self.receipt.clone(),output:metadata,preview_only:false,candidate_output_retained:true,issuer_execution_publication_authority:false};
        provider.check_head(fresh.head).map_err(StoredActualFormImportError::from)?;
        Ok(PreparedStoredFontOptionsCandidate{source:LiteralSource::Borrowed(self),output,receipt})
    }
    /// # Errors
    /// Move original owner after shared preparation; no matcher, source or writer replay.
    pub fn into_font_options_candidate<Rp,B,S,V>(self,provider:&StoredFormProvider<'_,Rp,B,S,V>,query:FontNameReplacementQuery<'_>,selector:SourceIndexScopeSelector<'_>,
        body:SourceReviewTextPolicy,axis:SourceFontStyleAxis,filter:Option<SourceReviewStyleFilter>,limits:SourceSearchLimits,writer:WriterLimits,now:u64)
        ->Result<PreparedStoredFontOptionsCandidate<'static>,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let(output,receipt)={let prepared=self.prepare_font_options_candidate(provider,query,selector,body,axis,filter,limits,writer,now)?;(prepared.output,prepared.receipt)};
        Ok(PreparedStoredFontOptionsCandidate{source:LiteralSource::Owned(Box::new(self)),output,receipt})
    }
}
fn fresh<Rp,B,S,V>(source:&StoredImportedDocumentForms,receipt:&StoredFontOptionsReceipt,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,preview:bool)->Result<(),C>
where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
    if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(C::Permission);}
    let current=source.fresh_source(provider,now)?;
    if receipt.profile!=if preview{STORED_FONT_PREVIEW_PROFILE}else{STORED_FONT_OPTIONS_PROFILE}||receipt.source!=source.receipt
        ||receipt.preview_only!=preview||receipt.candidate_output_retained==preview||receipt.issuer_execution_publication_authority
        ||!receipt.output.matches(*current.digest.as_bytes()){return Err(C::Binding);}Ok(())
}
impl<'a> PreparedStoredFontOptionsCandidate<'a>{
    pub(crate) fn compiler_font_inventory(&self)->&hwpx_package::document_import::search::replacement::atoms::styles::fonts::inventory::SourceFontEditInventory{
        match &self.output{Output::Unfiltered(c)=>c.edit_inventory(),Output::Filtered(c)=>c.edit_inventory()}
    }
    #[must_use]pub const fn receipt(&self)->&StoredFontOptionsReceipt{&self.receipt}
    /// Consumes and drops the output artifact. The resulting type has no bytes/inventory/compiler API.
    #[must_use]pub fn into_preview(self)->PreparedStoredFontPreview<'a>{
        let Self{source,output,mut receipt}=self;drop(output);receipt.profile=STORED_FONT_PREVIEW_PROFILE;receipt.preview_only=true;receipt.candidate_output_retained=false;
        PreparedStoredFontPreview{source,receipt}
    }
    /// # Errors
    /// Fresh current source and retained writer integrity; never repeats font selection/lowering.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<StoredFontOptionsReceipt,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.with_verified_bytes(provider,now,|_|())?;Ok(self.receipt.clone())
    }
    /// # Errors
    /// Final head is checked inside writer integrity verification immediately before the consumer.
    pub fn with_verified_bytes<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        fresh(&self.source,&self.receipt,provider,now,false)?;if self.receipt.output!=self.output.receipt(){return Err(C::Binding);}
        self.output.with_bytes(|bytes|{provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(consume(bytes))}).map_err(|_|C::Integrity)?
    }
    /// # Errors
    /// Candidate integrity is not qualified product execution, CAS or publication.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.verify(provider,now)?;Err(C::RouteUnqualified)}
}
impl PreparedStoredFontPreview<'_>{
    #[must_use]pub const fn receipt(&self)->&StoredFontOptionsReceipt{&self.receipt}
    /// # Errors
    /// Verifies current source access and head, not a retained output artifact or executed mutation.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<StoredFontOptionsReceipt,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.with_verified_metadata(provider,now,|r|r.clone())
    }
    /// # Errors
    /// Predicted metadata only, with original current-source and final consumer-head checks.
    pub fn with_verified_metadata<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&StoredFontOptionsReceipt)->T)->Result<T,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        fresh(&self.source,&self.receipt,provider,now,true)?;provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(consume(&self.receipt))
    }
    /// # Errors
    /// A preview has no retained output, execution, CAS or publication path.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.verify(provider,now)?;Err(C::RouteUnqualified)}
}
