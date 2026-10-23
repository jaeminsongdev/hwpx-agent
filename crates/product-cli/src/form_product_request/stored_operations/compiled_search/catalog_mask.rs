//! Explicit current-catalog context through the SAME operation compiler/owner resolver. No fallback config or execution.
pub mod routing;
pub mod entry;
use super::*;
use crate::form_product_request::stored_literal_replacement::personal_info::catalog::{StoredPersonalInfoCatalogMaskProductRequest,
    PreparedStoredPersonalInfoCatalogMaskProduct,PersonalInfoCatalogMaskProductError,PERSONAL_INFO_CATALOG_MASK_PRODUCT_SCHEMA};
use crate::form_stored_provider::actual_import::source_search::personal_info_catalog::CurrentPersonalInfoCatalogSource;
#[derive(Debug,Error)]pub enum CatalogMaskCompilationError{
    #[error("CATALOG_MASK_COMPILER_PRODUCT_REJECTED")]Product(#[from]PersonalInfoCatalogMaskProductError),
    #[error("CATALOG_MASK_COMMON_COMPILER_REJECTED")]Compiler(#[from]CompiledSearchError),
}
type E=CatalogMaskCompilationError;
pub struct PreparedCompiledCatalogMask{candidate:PreparedStoredPersonalInfoCatalogMaskProduct,plan:CompiledOperationPlan,receipt:CompiledSearchReceipt}
impl fmt::Debug for PreparedCompiledCatalogMask{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedCompiledCatalogMask(<redacted>; current_catalog_required_route_unqualified)")}}
fn project(candidate:&PreparedStoredPersonalInfoCatalogMaskProduct)->Result<projection::Projection<'_>,E>{
    let i=candidate.compiler_mask_inventory()?;let r=&candidate.receipt().stored.output;
    let mut p=projection::collect(r,i.source_package_sha256(),i.output_package_sha256(),"catalog_matched_mask_text_splices",i.anchors().iter())?;
    if p.receipt_sha!=i.receipt_sha256()||p.source!=r.source_package_sha256||p.output!=r.output_package_sha256{return Err(CompiledSearchError::Binding.into());}
    p.inventory_sha=i.canonical_sha256();Ok(p)
}
impl StoredProductRequest{
    /// # Errors
    /// Explicit trusted catalog source; no config-free dispatch, preview promotion, Native or automatic retry.
    pub fn prepare_compiled_catalog_mask_json<R,B,S,V>(provider:&StoredFormProvider<'_,R,B,S,V>,catalog:&dyn CurrentPersonalInfoCatalogSource,
        raw:&[u8],limits:SearchMutationLimits,now:u64)->Result<PreparedCompiledCatalogMask,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        StoredPersonalInfoCatalogMaskProductRequest::prepare_mutation_json(provider,catalog,raw,limits.search,limits.writer,now)?.compile(provider,catalog,now)
    }
}
impl PreparedStoredPersonalInfoCatalogMaskProduct{
    /// # Errors
    /// Moves the original owner and compiles exact inventory anchors using existing source-owner/plan validation.
    pub fn compile<R,B,S,V>(self,provider:&StoredFormProvider<'_,R,B,S,V>,catalog:&dyn CurrentPersonalInfoCatalogSource,now:u64)->Result<PreparedCompiledCatalogMask,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.compiler_view()?;
        let(plan,receipt)=self.with_verified_bytes(provider,catalog,now,|bytes|->Result<_,E>{
            let p=project(&self)?;if <[u8;32]>::from(Sha256::digest(bytes))!=p.output{return Err(CompiledSearchError::Binding.into());}
            let v=self.compiler_view()?;let plan=build::compile(&v,&p,PERSONAL_INFO_CATALOG_MASK_PRODUCT_SCHEMA)?;
            let receipt=receipt_for_view(&v,PERSONAL_INFO_CATALOG_MASK_PRODUCT_SCHEMA,&plan,&p)?;
            self.check_final_inputs(provider,catalog)?;Ok((plan,receipt))
        })??;Ok(PreparedCompiledCatalogMask{candidate:self,plan,receipt})
    }
}
impl PreparedCompiledCatalogMask{
    #[must_use]pub const fn compiled(&self)->&CompiledOperationPlan{&self.plan}
    #[must_use]pub const fn receipt(&self)->&CompiledSearchReceipt{&self.receipt}
    fn check(&self)->Result<(),E>{
        let p=project(&self.candidate)?;if receipt_for_view(&self.candidate.compiler_view()?,PERSONAL_INFO_CATALOG_MASK_PRODUCT_SCHEMA,&self.plan,&p)?!=self.receipt{
            return Err(CompiledSearchError::Binding.into());}Ok(())
    }
    /// # Errors
    /// Retained plan/source/config/current ACL validation without compiler, source import, regex or masking replay.
    pub fn verify<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,catalog:&dyn CurrentPersonalInfoCatalogSource,now:u64)->Result<&CompiledSearchReceipt,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.check()?;self.candidate.verify(provider,catalog,now)?;Ok(&self.receipt)}
    /// # Errors
    /// The original candidate remains the sole output-byte path, with current config and final head before consumption.
    pub fn with_verified_bytes<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,catalog:&dyn CurrentPersonalInfoCatalogSource,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.check()?;Ok(self.candidate.with_verified_bytes(provider,catalog,now,consume)?)}
    /// # Errors
    /// Plan data is not execution authority. Existing router/manifest/commit methods cannot omit the current catalog.
    pub fn require_current_product_route<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,catalog:&dyn CurrentPersonalInfoCatalogSource,now:u64)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.verify(provider,catalog,now)?;Err(PersonalInfoCatalogMaskProductError::RouteUnqualified.into())}
}
