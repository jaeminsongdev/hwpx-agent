//! Current source-bound scoped font candidate. No operation compiler, route, commit or publication.
pub mod options;
use super::*;
compiler_source!(PreparedStoredFontCandidate);
use super::product::LiteralSource;
use hwpx_package::document_import::{fields::semantics::catalog::fonts::names::{FontNameReplacementQuery,FONT_NAME_RESOLUTION_PROFILE},
    search::{selector::SourceIndexScopeSelector,reviews::SourceReviewTextPolicy,replacement::atoms::styles::fonts::{
        SourceFontReplacementCandidate,SourceFontReplacementReceipt,SourceFontReplacementError,SourceFontStyleAxis,SCOPED_FONT_REPLACEMENT_PROFILE}}};
pub const STORED_FONT_PROFILE:&str="hwpx-agent.stored-scoped-font-candidate/v1";
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct StoredFontReceipt {pub profile:&'static str,pub source:StoredActualFormImportReceipt,pub output:SourceFontReplacementReceipt,
    pub issuer_execution_publication_authority:bool}
pub struct PreparedStoredFontCandidate<'a>{source:LiteralSource<'a>,output:SourceFontReplacementCandidate,receipt:StoredFontReceipt}
impl fmt::Debug for PreparedStoredFontCandidate<'_>{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedStoredFontCandidate(<redacted>; current_access_not_route_or_commit)")}}
#[derive(Debug,Error)]
pub enum StoredFontError {
    #[error("STORED_FONT_SOURCE_REJECTED")]Source(#[from]StoredActualFormImportError),
    #[error("STORED_FONT_OUTPUT_REJECTED")]Output(#[from]SourceFontReplacementError),
    #[error("STORED_FONT_WRITE_SCOPE_REQUIRED")]Permission,
    #[error("STORED_FONT_BINDING_REJECTED")]Binding,
    #[error("STORED_FONT_INTEGRITY_REJECTED")]Integrity,
    #[error("STORED_FONT_PRODUCT_ROUTE_UNQUALIFIED")]RouteUnqualified,
}
type C=StoredFontError;
pub(crate) fn font_receipt_matches(r:&SourceFontReplacementReceipt,source:[u8;32])->bool{
    r.profile==SCOPED_FONT_REPLACEMENT_PROFILE&&r.names.profile==FONT_NAME_RESOLUTION_PROFILE&&r.names.source_package_sha256==source
        &&r.names.source_font_graph_sha256!=[0;32]&&r.names.request_sha256!=[0;32]&&r.request_sha256!=[0;32]
        &&r.source_index_sha256==r.selector.index_sha256&&r.source_index_sha256!=[0;32]
        &&r.names.changed_mappings>0&&r.names.changed_mappings<=128&&r.names.matched_declarations>=r.names.changed_mappings
        &&r.cloned_character_properties>0&&r.changed_source_scalars>=r.cloned_character_properties&&r.selector.selected_normalized_scalars>0
        &&r.changed_parts>=2&&r.compiled_edits_sha256!=[0;32]&&r.output_package_sha256!=source&&r.output_package_sha256!=[0;32]&&r.output_bytes>0
        &&r.original_text_controls_and_nonselected_references_preserved&&r.original_declarations_and_font_resources_preserved
        &&!r.names.platform_fallback_availability_or_execution_qualified&&!r.native_cascade_fallback_visibility_or_service_execution_qualified
        &&!r.selector.whole_document_visibility_native_flow_or_revision_authority
}
impl StoredImportedDocumentForms {
    /// # Errors
    /// Current write/read/ACL/head/AEAD and one exact reconstruction precede font selection/lowering.
    pub fn prepare_font_candidate<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,query:FontNameReplacementQuery<'_>,selector:SourceIndexScopeSelector<'_>,
        body:SourceReviewTextPolicy,axis:SourceFontStyleAxis,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredFontCandidate<'_>,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(C::Permission);}
        let(fresh,proof)=self.fresh_source_reconstructed(provider,now)?;
        let output=proof.lower_scoped_font_candidate(&self.imported,query,selector,body,axis,limits,writer)?;
        if !font_receipt_matches(output.receipt(),*fresh.digest.as_bytes()){return Err(C::Binding);}
        let receipt=StoredFontReceipt{profile:STORED_FONT_PROFILE,source:self.receipt.clone(),output:output.receipt().clone(),issuer_execution_publication_authority:false};
        provider.check_head(fresh.head).map_err(StoredActualFormImportError::from)?;
        Ok(PreparedStoredFontCandidate{source:LiteralSource::Borrowed(self),output,receipt})
    }
    /// # Errors
    /// Move the original owner after shared preparation; no original clone, query or compiler replay.
    pub fn into_font_candidate<Rp,B,S,V>(self,provider:&StoredFormProvider<'_,Rp,B,S,V>,query:FontNameReplacementQuery<'_>,selector:SourceIndexScopeSelector<'_>,
        body:SourceReviewTextPolicy,axis:SourceFontStyleAxis,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredFontCandidate<'static>,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let(output,receipt)={let prepared=self.prepare_font_candidate(provider,query,selector,body,axis,limits,writer,now)?;(prepared.output,prepared.receipt)};
        Ok(PreparedStoredFontCandidate{source:LiteralSource::Owned(Box::new(self)),output,receipt})
    }
}
impl PreparedStoredFontCandidate<'_> {
    pub(crate) fn compiler_font_inventory(&self)->&hwpx_package::document_import::search::replacement::atoms::styles::fonts::inventory::SourceFontEditInventory{self.output.edit_inventory()}
    /// # Errors
    /// Metadata delivery shares the original fresh source/integrity/consumer-final head checks.
    pub fn with_verified_edit_inventory<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,
        consume:impl FnOnce(&hwpx_package::document_import::search::replacement::atoms::styles::fonts::inventory::SourceFontEditInventory)->T)->Result<T,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.with_verified_bytes(provider,now,|_|consume(self.output.edit_inventory()))
    }
    #[must_use]pub const fn receipt(&self)->&StoredFontReceipt{&self.receipt}
    fn fresh<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(C::Permission);}
        let fresh=self.source.fresh_source(provider,now)?;
        if self.receipt.profile!=STORED_FONT_PROFILE||self.receipt.source!=self.source.receipt||&self.receipt.output!=self.output.receipt()
            ||self.receipt.issuer_execution_publication_authority||!font_receipt_matches(self.output.receipt(),*fresh.digest.as_bytes()){return Err(C::Binding);}Ok(())
    }
    /// # Errors
    /// Current source and writer integrity, then final head; never reruns font names or lowering.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<StoredFontReceipt,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.fresh(provider,now)?;self.output.with_verified_bytes(|_|()).map_err(|_|C::Integrity)?;
        provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(self.receipt.clone())
    }
    /// # Errors
    /// Fresh current authority and head inside writer verification immediately before the consumer.
    pub fn with_verified_bytes<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.fresh(provider,now)?;self.output.with_verified_bytes(|bytes|{
            provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(consume(bytes))
        }).map_err(|_|C::Integrity)?
    }
    /// # Errors
    /// Stored preparation does not qualify the operation compiler, actual route or publication.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.verify(provider,now)?;Err(C::RouteUnqualified)}
}
