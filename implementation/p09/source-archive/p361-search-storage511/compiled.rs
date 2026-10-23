//! Actual source-owner selectors through the original operation compiler. Not an executable route.
mod projection;
mod owners;
mod build;
mod font_resources;
pub mod catalog_mask;
pub mod routing;
pub mod p02_registry;
use super::{StoredProductRequest, StoredProductOperationError, PreparedStoredProductOperation, request,
    search_mutations::{PreparedStoredSearchMutation, SearchMutationError, SearchMutationLimits}};
use crate::form_stored_provider::{StoredFormProvider,actual_import::{StoredImportedDocumentForms,StoredActualFormImportError}};
use artifact_service::{ArtifactMetadataRepository,ArtifactScanner,EncryptedBlobStore,ArtifactId};
use domain_ir::{CompiledOperationPlan,PlanId,RevisionId,DocumentId};
use hwpx_package::document_import::search::replacement::atoms::styles::intents::SourceStyleSpliceInventory;
use revision_service::RevisionRepository;
use serde::Serialize;
use sha2::{Digest as _,Sha256};
use std::{fmt,collections::BTreeSet};
use thiserror::Error;
pub const COMPILED_SEARCH_PROFILE:&str="hwpx-agent.product-source-search-operation-compiler/v1";
pub(super) const MAX_EDITS:usize=4096;
pub(super) const MAX_METADATA_BYTES:usize=8*1024*1024;
pub(super) const MAX_PLAN_BYTES:usize=16*1024*1024;
pub(crate) struct CompilationView<'a>{
    pub(crate) source:&'a StoredImportedDocumentForms,
    pub(crate) plan_id:&'a PlanId,pub(crate) revision:&'a RevisionId,pub(crate) document:&'a DocumentId,pub(crate) generation:u64,
    pub(crate) capability:&'static str,pub(crate) raw:&'a str,pub(crate) canonical:&'a str,pub(crate) scoped:&'a str,
    pub(crate) splices:Option<&'a SourceStyleSpliceInventory>,
}
impl fmt::Debug for CompilationView<'_>{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("CompilationView(<redacted>; not_authority)")}}

#[derive(Clone,Eq,PartialEq,Serialize)]
pub struct CompiledSearchReceipt{
    pub profile:&'static str,pub request_schema:&'static str,pub capability_id:&'static str,
    pub plan_id:PlanId,pub base_revision:RevisionId,pub head_generation:u64,pub source_artifact:ArtifactId,
    pub source_package_sha256:[u8;32],pub source_graph_sha256:[u8;32],pub output_package_sha256:[u8;32],
    pub mutation_receipt_sha256:[u8;32],pub edit_inventory_sha256:[u8;32],pub compiled_plan_sha256:[u8;32],
    pub raw_request_sha256:String,pub canonical_request_sha256:String,pub scoped_request_sha256:String,
    pub source_edit_operations:usize,pub structural_owner_nodes:usize,pub execution_authority:bool,
}
impl fmt::Debug for CompiledSearchReceipt{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{
    f.debug_struct("CompiledSearchReceipt").field("operations",&self.source_edit_operations).field("owners",&self.structural_owner_nodes).finish_non_exhaustive()}}
pub struct PreparedCompiledSearchMutation{candidate:PreparedStoredSearchMutation,plan:CompiledOperationPlan,receipt:CompiledSearchReceipt}
impl fmt::Debug for PreparedCompiledSearchMutation{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedCompiledSearchMutation(<redacted>; route_unqualified)")}}

impl StoredProductRequest{
    /// # Errors
    /// Original strict schemas/parsers/current source plus actual source-owner operation compilation.
    /// Form/Formula or unknown schemas are rejected before source access; no execution/key claim occurs.
    pub fn prepare_compiled_search_json<R,B,S,V>(provider:&StoredFormProvider<'_,R,B,S,V>,raw:&[u8],limits:SearchMutationLimits,now:u64)
        ->Result<PreparedCompiledSearchMutation,CompiledSearchError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        if !matches!(request::classify(raw)?,request::Kind::SearchMutation(_)){return Err(CompiledSearchError::Kind);}
        let PreparedStoredProductOperation::SearchMutation(candidate)=Self::prepare_json_with_search_limits(provider,raw,None,limits,now)?
            else{return Err(CompiledSearchError::Kind)};
        (*candidate).compile(provider,now)
    }
}
impl PreparedStoredSearchMutation{
    /// # Errors
    /// Compiles every retained source edit against its nearest actual structural owner, never a guessed node.
    /// The original candidate/source owner is moved, without clone/reimport/matcher replay.
    pub fn compile<R,B,S,V>(self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<PreparedCompiledSearchMutation,CompiledSearchError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let(plan,receipt)=self.with_verified_bytes(provider,now,|bytes|->Result<_,CompiledSearchError>{
            let projection=projection::project(&self)?;
            if <[u8;32]>::from(Sha256::digest(bytes))!=projection.output{return Err(CompiledSearchError::Binding);}
            let view=self.compiler_view();let plan=build::compile(&view,&projection,self.schema_version())?;
            let receipt=receipt(&self,&plan,&projection)?;
            view.source.check_compiler_head(provider)?;
            Ok((plan,receipt))
        })??;
        Ok(PreparedCompiledSearchMutation{candidate:self,plan,receipt})
    }
}
impl PreparedCompiledSearchMutation{
    #[must_use] pub const fn compiled(&self)->&CompiledOperationPlan{&self.plan}
    #[must_use] pub const fn receipt(&self)->&CompiledSearchReceipt{&self.receipt}
    fn check(&self)->Result<(),CompiledSearchError>{
        let projection=projection::project(&self.candidate)?;
        if receipt(&self.candidate,&self.plan,&projection)?!=self.receipt{return Err(CompiledSearchError::Binding);}Ok(())
    }
    /// # Errors
    /// Immutable plan/metadata integrity and original current source/access checks, no compiler/search replay.
    pub fn verify<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<&CompiledSearchReceipt,CompiledSearchError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.check()?;self.candidate.verify(provider,now)?;Ok(&self.receipt)
    }
    /// # Errors
    /// The original artifact-integrity and consumer-final head callback remains the sole byte delivery path.
    pub fn with_verified_bytes<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,CompiledSearchError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.check()?;Ok(self.candidate.with_verified_bytes(provider,now,consume)?)
    }
    /// # Errors
    /// A compiled plan is data, not a trusted registry/target route. All original denials remain in force.
    pub fn require_current_product_route<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<(),CompiledSearchError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.check()?;Ok(self.candidate.require_current_product_route(provider,now)?)
    }
}
fn receipt(candidate:&PreparedStoredSearchMutation,plan:&CompiledOperationPlan,p:&projection::Projection<'_>)->Result<CompiledSearchReceipt,CompiledSearchError>{
    receipt_for_view(&candidate.compiler_view(),candidate.schema_version(),plan,p)
}
fn receipt_for_view(v:&CompilationView<'_>,schema:&'static str,plan:&CompiledOperationPlan,p:&projection::Projection<'_>)->Result<CompiledSearchReceipt,CompiledSearchError>{
    let source=v.source.receipt();let graph=v.source.imported().graph();let head=v.source.compiler_head();
    let graph_sha=graph.canonical_sha256().map_err(|_|CompiledSearchError::Binding)?;
    if plan.plan_id()!=v.plan_id||plan.base_revision()!=v.revision||plan.base_graph_sha256()!=graph_sha||graph.document_id()!=v.document
        ||head.revision_id().map(|id|id.public_id())!=Some(v.revision.as_str().to_owned())||head.generation()!=v.generation
        ||p.source!=v.source.imported().receipt().source_package_sha256||plan.operations().len()!=p.edits.len(){return Err(CompiledSearchError::Binding);}
    Ok(CompiledSearchReceipt{profile:COMPILED_SEARCH_PROFILE,request_schema:schema,capability_id:v.capability,
        plan_id:v.plan_id.clone(),base_revision:v.revision.clone(),head_generation:v.generation,source_artifact:source.source_artifact,
        source_package_sha256:p.source,source_graph_sha256:graph_sha,output_package_sha256:p.output,mutation_receipt_sha256:p.receipt_sha,
        edit_inventory_sha256:p.inventory_sha,compiled_plan_sha256:bounded_hash(plan,MAX_PLAN_BYTES)?,raw_request_sha256:v.raw.to_owned(),
        canonical_request_sha256:v.canonical.to_owned(),scoped_request_sha256:v.scoped.to_owned(),source_edit_operations:p.edits.len(),
        structural_owner_nodes:plan.operations().iter().map(|op|op.target().node_id()).collect::<BTreeSet<_>>().len(),execution_authority:false})
}
pub(super) fn bounded_hash(value:&impl Serialize,maximum:usize)->Result<[u8;32],CompiledSearchError>{
    struct Hash{state:Sha256,length:usize,maximum:usize}
    impl std::io::Write for Hash{
        fn write(&mut self,b:&[u8])->std::io::Result<usize>{let n=self.length.checked_add(b.len()).filter(|n|*n<=self.maximum)
            .ok_or_else(||std::io::Error::other("compiled_search_limit"))?;self.state.update(b);self.length=n;Ok(b.len())}
        fn flush(&mut self)->std::io::Result<()>{Ok(())}
    }
    let mut h=Hash{state:Sha256::new(),length:0,maximum};serde_json::to_writer(&mut h,value).map_err(|_|CompiledSearchError::Limit)?;Ok(h.state.finalize().into())
}
#[derive(Debug,Error)]
pub enum CompiledSearchError{
    #[error("compiled_search_request_rejected")] Request(#[from]StoredProductOperationError),
    #[error("compiled_search_product_rejected")] Product(#[from]SearchMutationError),
    #[error("compiled_search_source_rejected")] Source(#[from]StoredActualFormImportError),
    #[error("compiled_search_kind_rejected")] Kind,
    #[error("compiled_search_binding_rejected")] Binding,
    #[error("compiled_search_actual_owner_missing_or_ambiguous")] Target,
    #[error("compiled_search_limit")] Limit,
    #[error("compiled_search_original_operation_compiler_rejected")] Compilation,
}
