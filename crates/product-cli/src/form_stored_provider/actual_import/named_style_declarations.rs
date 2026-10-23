//! Current sealed document -> immutable PARA/CHAR declaration metadata, never body edits.
use super::*;
use artifact_service::AuthScope;
use hwpx_package::document_import::fields::{ImportedDocumentFields,semantics::{ImportedDocumentFieldSemantics,catalog::{ImportedDocumentCatalog,
    named_styles::{SourceNamedStyleNameQuery,SourceNamedStyleNameLimits,SourceNamedStyleNameError,SourceNamedStyleNameResolution,
        SourceNamedStyleNameResolutionReceipt,SourceNamedStyleDeclaration,NAMED_STYLE_NAME_RESOLUTION_PROFILE}}}};
use sha2::{Digest as _,Sha256};

pub const STORED_NAMED_DECLARATIONS_PROFILE:&str="hwpx-agent.stored-named-style-declarations/v1";
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct StoredNamedStyleDeclarationsReceipt{
    pub profile:&'static str,pub source:StoredActualFormImportReceipt,pub resolution:SourceNamedStyleNameResolutionReceipt,
    pub from:Vec<SourceNamedStyleDeclaration>,pub target:SourceNamedStyleDeclaration,pub resolution_sha256:[u8;32],
    pub body_mapping_mutation_native_or_execution_qualified:bool,
}
pub struct PreparedStoredNamedStyleDeclarations{source:StoredImportedDocumentForms,resolution:SourceNamedStyleNameResolution,
    receipt:StoredNamedStyleDeclarationsReceipt,maximum_bytes:usize}
impl fmt::Debug for PreparedStoredNamedStyleDeclarations{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedStoredNamedStyleDeclarations(<redacted>; declaration_metadata_only)")}}
#[derive(Debug,Error)]
pub enum StoredNamedStyleDeclarationsError{
    #[error("STORED_NAMED_DECLARATIONS_SOURCE_REJECTED")]Source(#[from]StoredActualFormImportError),
    #[error("STORED_NAMED_DECLARATIONS_CATALOG_REJECTED")]Catalog,
    #[error("STORED_NAMED_DECLARATIONS_RESOLUTION_REJECTED")]Resolution(#[from]SourceNamedStyleNameError),
    #[error("STORED_NAMED_DECLARATIONS_WRITE_SCOPE_REQUIRED")]Permission,
    #[error("STORED_NAMED_DECLARATIONS_BINDING_REJECTED")]Binding,
    #[error("STORED_NAMED_DECLARATIONS_RESPONSE_LIMIT")]Limit,
    #[error("STORED_NAMED_DECLARATIONS_ROUTE_UNQUALIFIED")]RouteUnqualified,
}
type E=StoredNamedStyleDeclarationsError;
impl StoredImportedDocumentForms{
    /// # Errors
    /// Validates current write/access/head/AEAD, then imports one original catalog and resolves once.
    pub fn into_named_style_declarations<R,B,S,V>(self,provider:&StoredFormProvider<'_,R,B,S,V>,query:SourceNamedStyleNameQuery<'_>,
        limits:SourceNamedStyleNameLimits,now:u64)->Result<PreparedStoredNamedStyleDeclarations,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(E::Permission);}
        query.validate(limits)?;let fresh=self.fresh_source(provider,now)?;
        let resolution={let fields=ImportedDocumentFields::import(&self.imported).map_err(|_|E::Catalog)?;
            let semantics=ImportedDocumentFieldSemantics::import(&fields).map_err(|_|E::Catalog)?;
            let catalog=ImportedDocumentCatalog::import(&semantics).map_err(|_|E::Catalog)?;
            catalog.resolve_named_style_replacements(query,limits)?};
        if resolution.receipt().source_package_sha256!=*fresh.digest.as_bytes(){return Err(E::Binding);}
        let receipt=StoredNamedStyleDeclarationsReceipt{profile:STORED_NAMED_DECLARATIONS_PROFILE,source:self.receipt.clone(),
            resolution:resolution.receipt().clone(),from:resolution.from_declarations().to_vec(),target:resolution.target_declaration().clone(),
            resolution_sha256:Sha256::digest(resolution.canonical_json()?).into(),body_mapping_mutation_native_or_execution_qualified:false};
        let _=bounded_metadata(&receipt,limits.maximum_result_bytes())?;
        provider.check_head(fresh.head).map_err(StoredActualFormImportError::from)?;
        Ok(PreparedStoredNamedStyleDeclarations{source:self,resolution,receipt,maximum_bytes:limits.maximum_result_bytes()})
    }
}
impl PreparedStoredNamedStyleDeclarations{
    #[must_use]pub const fn receipt(&self)->&StoredNamedStyleDeclarationsReceipt{&self.receipt}
    pub(crate) fn check_head<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(())
    }
    fn fresh<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(E::Permission);}
        let current=self.source.fresh_source(provider,now)?;let r=&self.receipt;let core=self.resolution.receipt();
        if r.profile!=STORED_NAMED_DECLARATIONS_PROFILE||r.source!=self.source.receipt||&r.resolution!=core
            ||core.profile!=NAMED_STYLE_NAME_RESOLUTION_PROFILE||core.source_package_sha256!=*current.digest.as_bytes()
            ||core.source_catalog_sha256==[0;32]||core.request_sha256==[0;32]||!core.all_original_declaration_resources_bound
            ||core.body_occurrences_or_target_semantics_qualified||core.current_access_execution_or_publication_authority
            ||r.from!=self.resolution.from_declarations()||&r.target!=self.resolution.target_declaration()
            ||r.resolution_sha256!=<[u8;32]>::from(Sha256::digest(self.resolution.canonical_json()?))
            ||r.body_mapping_mutation_native_or_execution_qualified{return Err(E::Binding);}Ok(())
    }
    /// # Errors
    /// Rechecks original current source without replaying the catalog import or name matcher.
    pub fn verify<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<StoredNamedStyleDeclarationsReceipt,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.with_verified_metadata(provider,now,Clone::clone)
    }
    pub(crate) fn with_verified_metadata<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64,consume:impl FnOnce(&StoredNamedStyleDeclarationsReceipt)->T)->Result<T,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.fresh(provider,now)?;self.check_head(provider)?;Ok(consume(&self.receipt))
    }
    /// # Errors
    /// Bounded metadata is delivered only after fresh authorization and a consumer-final head check.
    pub fn with_verified_json<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let bytes=bounded_metadata(&self.receipt,self.maximum_bytes)?;
        self.with_verified_metadata(provider,now,|_|consume(&bytes))
    }
    /// # Errors
    /// A declaration mapping is not a qualified replacement, mutation, Native result or execution route.
    pub fn require_current_product_route<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.verify(provider,now)?;Err(E::RouteUnqualified)}
}
// Storage owns its finite serializer; no reverse dependency on a private product-request helper.
fn bounded_metadata(value:&impl Serialize,maximum:usize)->Result<Vec<u8>,E>{
    struct Bound{bytes:Vec<u8>,maximum:usize}
    impl std::io::Write for Bound{
        fn write(&mut self,raw:&[u8])->std::io::Result<usize>{
            let length=self.bytes.len().checked_add(raw.len()).filter(|n|*n<=self.maximum).ok_or_else(||std::io::Error::other("named_declaration_metadata_limit"))?;
            self.bytes.try_reserve(raw.len()).map_err(|_|std::io::Error::other("named_declaration_metadata_allocation"))?;
            self.bytes.extend_from_slice(raw);debug_assert_eq!(self.bytes.len(),length);Ok(raw.len())
        }
        fn flush(&mut self)->std::io::Result<()>{Ok(())}
    }
    let mut out=Bound{bytes:Vec::new(),maximum};serde_json::to_writer(&mut out,value).map_err(|_|E::Limit)?;Ok(out.bytes)
}
