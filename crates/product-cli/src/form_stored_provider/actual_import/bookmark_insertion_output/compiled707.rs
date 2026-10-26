//! Original first-insertion candidate -> original owner resolver and common compiler.
//! A plan does not grant execution, registry, storage, Native or complete-graph authority.
use super::*;
use crate::form_product_request::stored_operations::compiled_search::{bounded_hash,resolve_original_source_owners};
use domain_ir::{ArgumentDraft,ArgumentKind,ArgumentSpec,CapabilityCatalog,CapabilityDefinitionDraft,CapabilityId,
    CompiledOperationPlan,DefaultPolicy,OperationDraft,OperationId,OperationPlanCompiler,OperationPlanDraft,OperationPlanLimits,
    PlanId,RevisionId,Selector,SelectorDraft,SelectorLimits,SelectorSnapshot};
use sha2::{Digest as _,Sha256};
use std::collections::BTreeMap;
pub const BOOKMARK_INSERTION_CAPABILITY:&str="ref.crossref_insert";
const PROFILE:&str="hwpx-agent.stored-source-bookmark-insertion-compiler/v1";
const MAX_METADATA:usize=8*1024*1024;
const MAX_PLAN:usize=16*1024*1024;
const ARGUMENTS:[&str;10]=["source_package_sha256","output_package_sha256","stored_receipt_sha256",
    "source_run_anchor_json","source_run_sha256","selected_target_id_sha256","output_command_sha256",
    "source_selection_sha256","parameter_profile","owner_binding_profile"];
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct CompiledBookmarkInsertionReceipt{
    pub profile:&'static str,pub capability_id:&'static str,pub plan_id:PlanId,pub base_revision:RevisionId,
    pub head_generation:u64,pub source_artifact:artifact_service::ArtifactId,pub source_graph_sha256:[u8;32],
    pub source_package_sha256:[u8;32],pub output_package_sha256:[u8;32],pub stored_receipt_sha256:[u8;32],
    pub source_selection_sha256:[u8;32],pub compiled_plan_sha256:[u8;32],pub inserted_fields:usize,
    pub display_text_preserved_not_evaluated_or_refreshed:bool,pub execution_or_publication_authority:bool,
}
pub struct PreparedCompiledBookmarkInsertionCandidate{
    candidate:PreparedStoredBookmarkInsertionCandidate,plan:CompiledOperationPlan,receipt:CompiledBookmarkInsertionReceipt,
}
impl fmt::Debug for PreparedCompiledBookmarkInsertionCandidate{
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedCompiledBookmarkInsertionCandidate(<redacted>; no_registry_CAS_or_execution_authority)")}
}
#[derive(Debug,Error)]
pub enum BookmarkInsertionCompileError{
    #[error("BOOKMARK_INSERTION_COMPILER_CURRENT_SOURCE_DENIED")]Stored(#[from]StoredBookmarkInsertionError),
    #[error("BOOKMARK_INSERTION_COMPILER_OWNER_DENIED")]Owner,
    #[error("BOOKMARK_INSERTION_COMPILER_BINDING_DENIED")]Binding,
    #[error("BOOKMARK_INSERTION_COMPILER_LIMIT")]Limit,
    #[error("BOOKMARK_INSERTION_COMPILATION_DENIED")]Compilation,
}
type C=BookmarkInsertionCompileError;
fn digest(value:&impl Serialize,maximum:usize)->Result<[u8;32],C>{bounded_hash(value,maximum).map_err(|_|C::Limit)}
fn selection(candidate:&PreparedStoredBookmarkInsertionCandidate)->Result<[u8;32],C>{
    digest(&(&candidate.run,&candidate.target_id,candidate.receipt.output.command_sha256),MAX_METADATA)
}
fn build(candidate:&PreparedStoredBookmarkInsertionCandidate,plan_id:PlanId)->Result<CompiledOperationPlan,C>{
    let forms=candidate.source.imported();let graph=forms.graph();let r=&candidate.receipt.output;
    if candidate.run.fingerprint_sha256!=r.source_run_sha256||r.inserted_fields!=1
        ||r.requires_existing_crossref_envelope||!r.inserted_parameter_envelope_readback_verified
        ||!r.original_selected_run_exact||!r.outside_insertions_exact{return Err(C::Binding);}
    let anchors=std::slice::from_ref(&candidate.run);
    let owner=resolve_original_source_owners(graph,forms.source(),anchors).map_err(|_|C::Owner)?
        .into_iter().next().ok_or(C::Owner)?;
    let revision=RevisionId::parse(candidate.source.compiler_head().revision_id().ok_or(C::Binding)?.public_id()).map_err(|_|C::Binding)?;
    let snapshot=SelectorSnapshot::build(graph,revision.clone(),SelectorLimits::default()).map_err(|_|C::Owner)?;
    let capability=CapabilityId::parse(BOOKMARK_INSERTION_CAPABILITY).map_err(|_|C::Compilation)?;
    let mut definition=CapabilityDefinitionDraft::new(capability.clone());
    for name in ARGUMENTS{definition.arguments.insert(name.into(),ArgumentSpec{kind:ArgumentKind::Text{max_bytes:2048},
        required:true,default:None,default_policy:DefaultPolicy::Locked});}
    let catalog=CapabilityCatalog::from_drafts(vec![definition]).map_err(|_|C::Compilation)?;
    let values=[hex::encode(r.source_package_sha256),hex::encode(r.output_package_sha256),hex::encode(digest(&candidate.receipt,MAX_METADATA)?),
        serde_json::to_string(&candidate.run).map_err(|_|C::Limit)?,hex::encode(r.source_run_sha256),
        hex::encode(Sha256::digest(candidate.target_id.as_str().as_bytes())),hex::encode(r.command_sha256),
        hex::encode(selection(candidate)?),r.parameter_profile.into(),"actual_structural_owner_with_exact_plain_run_and_bookmark_target/v1".into()];
    let arguments:BTreeMap<_,_>=ARGUMENTS.into_iter().zip(values).map(|(key,value)|(key.into(),ArgumentDraft::Text(value))).collect();
    let operation=OperationDraft{operation_id:OperationId::parse("bookmark-first-insertion").map_err(|_|C::Compilation)?,
        capability_id:capability,selector:SelectorDraft::one(Selector::by_logical_id(owner)),arguments,depends_on:vec![]};
    OperationPlanCompiler::new(OperationPlanLimits{max_operations:1,max_dependencies:1,max_arguments_per_operation:ARGUMENTS.len(),
        max_string_bytes:2048,max_total_argument_bytes:MAX_METADATA,max_serialized_bytes:MAX_PLAN}).map_err(|_|C::Compilation)?
        .compile(OperationPlanDraft::new(plan_id,revision,vec![operation]),&catalog,&snapshot,&snapshot.expectation()).map_err(|_|C::Compilation)
}
fn receipt(candidate:&PreparedStoredBookmarkInsertionCandidate,plan:&CompiledOperationPlan)->Result<CompiledBookmarkInsertionReceipt,C>{
    let graph_sha=candidate.source.imported().graph().canonical_sha256().map_err(|_|C::Binding)?;
    let head=candidate.source.compiler_head();let r=&candidate.receipt.output;
    if head.revision_id().map(|id|id.public_id())!=Some(plan.base_revision().as_str().to_owned())
        ||head.generation()!=candidate.receipt.source.head_generation||plan.base_graph_sha256()!=graph_sha
        ||plan.operations().len()!=1||plan.operations()[0].capability_id().as_str()!=BOOKMARK_INSERTION_CAPABILITY
        ||r.inserted_fields!=1||candidate.run.fingerprint_sha256!=r.source_run_sha256
        ||!r.existing_display_text_is_not_evaluated_or_refreshed||r.native_currentness_execution_or_publication_qualified
        ||candidate.receipt.execution_or_publication_authority{return Err(C::Binding);}
    Ok(CompiledBookmarkInsertionReceipt{profile:PROFILE,capability_id:BOOKMARK_INSERTION_CAPABILITY,plan_id:plan.plan_id().clone(),
        base_revision:plan.base_revision().clone(),head_generation:head.generation(),source_artifact:candidate.receipt.source.source_artifact,
        source_graph_sha256:graph_sha,source_package_sha256:r.source_package_sha256,output_package_sha256:r.output_package_sha256,
        stored_receipt_sha256:digest(&candidate.receipt,MAX_METADATA)?,source_selection_sha256:selection(candidate)?,
        compiled_plan_sha256:digest(plan,MAX_PLAN)?,inserted_fields:1,display_text_preserved_not_evaluated_or_refreshed:true,
        execution_or_publication_authority:false})
}
impl PreparedStoredBookmarkInsertionCandidate{
    /// Consumes the candidate, retaining just its original selected run and target.
    /// # Errors
    /// Checks current source access before and after compilation. No lowerer or import replay.
    pub fn compile<R,B,S,V>(self,provider:&StoredFormProvider<'_,R,B,S,V>,plan_id:PlanId,now:u64)
        ->Result<PreparedCompiledBookmarkInsertionCandidate,C>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let(plan,receipt)=self.with_verified_bytes(provider,now,|bytes|{
            if <[u8;32]>::from(Sha256::digest(bytes))!=self.receipt.output.output_package_sha256{return Err(C::Binding);}
            let plan=build(&self,plan_id)?;let receipt=receipt(&self,&plan)?;Ok((plan,receipt))
        })??;
        self.verify(provider,now)?;
        Ok(PreparedCompiledBookmarkInsertionCandidate{candidate:self,plan,receipt})
    }
}
impl PreparedCompiledBookmarkInsertionCandidate{
    #[must_use]pub const fn compiled(&self)->&CompiledOperationPlan{&self.plan}
    #[must_use]pub const fn receipt(&self)->&CompiledBookmarkInsertionReceipt{&self.receipt}
    fn check(&self)->Result<(),C>{if receipt(&self.candidate,&self.plan)?!=self.receipt{return Err(C::Binding);}Ok(())}
    /// # Errors
    /// Immutable plan binding and the original fresh ACL/head/AEAD/whole-source check.
    pub fn verify<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<&CompiledBookmarkInsertionReceipt,C>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.check()?;self.candidate.verify(provider,now)?;Ok(&self.receipt)
    }
    /// # Errors
    /// Original final writer callback; failed candidates cannot be revived by regrant.
    pub fn with_verified_bytes<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,C>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.check()?;Ok(self.candidate.with_verified_bytes(provider,now,consume)?)
    }
    /// # Errors
    /// A compiled source insertion has no independently qualified execution route yet.
    pub fn require_current_product_route<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<(),C>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.check()?;Ok(self.candidate.require_current_product_route(provider,now)?)
    }
}
