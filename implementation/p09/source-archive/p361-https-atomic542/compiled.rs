//! Original common owner resolver + OperationPlanCompiler; no registry/execution authority.
use super::*;
use crate::form_product_request::stored_operations::compiled_search::{bounded_hash,resolve_original_source_owners};
use domain_ir::{ArgumentDraft,ArgumentKind,ArgumentSpec,CapabilityCatalog,CapabilityDefinitionDraft,CapabilityId,CompiledOperationPlan,
    DefaultPolicy,OperationDraft,OperationId,OperationPlanCompiler,OperationPlanDraft,OperationPlanLimits,PlanId,RevisionId,
    Selector,SelectorDraft,SelectorLimits,SelectorSnapshot,SourceAnchorHandle};
use sha2::{Digest as _,Sha256};
use std::collections::BTreeMap;
pub const HTTPS_EDIT_CAPABILITY:&str="ref.hyperlink_edit";
const PROFILE:&str="hwpx-agent.stored-source-https-target-compiler/v1";
const MAX_EDITS:usize=4096;
const MAX_METADATA:usize=8*1024*1024;
const MAX_PLAN:usize=16*1024*1024;
const ARGUMENTS:[&str;13]=["source_package_sha256","output_package_sha256","stored_receipt_sha256","policy_artifact",
    "policy_raw_sha256","policy_version","policy_generation","source_field_anchor_json","source_reference_id",
    "source_field_sha256","source_meaning_sha256","output_target_sha256","owner_binding_profile"];

pub(super) fn selected_anchors(fields:&ImportedDocumentFields<'_>,output:&SourceHttpsTargetReceipt)->Result<Vec<SourceAnchorHandle>,StoredHttpsTargetError>{
    if output.changes.is_empty()||output.changes.len()>MAX_EDITS{return Err(StoredHttpsTargetError::Meanings);}
    let by_id:BTreeMap<_,_>=fields.fields().iter().map(|f|(&f.reference_id,&f.begin_anchor)).collect();
    let mut selected=Vec::new();selected.try_reserve_exact(output.changes.len()).map_err(|_|StoredHttpsTargetError::Meanings)?;
    for change in &output.changes{
        let anchor=by_id.get(&change.source_reference_id).ok_or(StoredHttpsTargetError::Binding)?;
        if anchor.fingerprint_sha256!=change.source_field_sha256{return Err(StoredHttpsTargetError::Binding);}
        selected.push((**anchor).clone());
    }Ok(selected)
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct CompiledHttpsTargetReceipt{
    pub profile:&'static str,pub capability_id:&'static str,pub plan_id:PlanId,pub base_revision:RevisionId,pub head_generation:u64,
    pub source_graph_sha256:[u8;32],pub source_package_sha256:[u8;32],pub output_package_sha256:[u8;32],
    pub stored_receipt_sha256:[u8;32],pub source_anchors_sha256:[u8;32],pub compiled_plan_sha256:[u8;32],
    pub source_field_operations:usize,pub execution_or_publication_authority:bool,
}
pub struct PreparedCompiledHttpsTargetCandidate<'a>{candidate:PreparedStoredHttpsTargetCandidate<'a>,plan:CompiledOperationPlan,receipt:CompiledHttpsTargetReceipt}
impl fmt::Debug for PreparedCompiledHttpsTargetCandidate<'_>{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{
    f.write_str("PreparedCompiledHttpsTargetCandidate(<redacted>; no_registry_CAS_or_execution_authority)")}}
#[derive(Debug,Error)]
pub enum HttpsTargetCompileError{
    #[error("HTTPS_TARGET_COMPILER_STORED_CANDIDATE_DENIED")]Stored(#[from]StoredHttpsTargetError),
    #[error("HTTPS_TARGET_COMPILER_SOURCE_OWNER_DENIED")]Owner,
    #[error("HTTPS_TARGET_COMPILER_BINDING_DENIED")]Binding,
    #[error("HTTPS_TARGET_COMPILER_LIMIT")]Limit,
    #[error("HTTPS_TARGET_COMPILER_ORIGINAL_COMPILATION_DENIED")]Compilation,
}
type C=HttpsTargetCompileError;
fn digest(value:&impl Serialize,maximum:usize)->Result<[u8;32],C>{bounded_hash(value,maximum).map_err(|_|C::Limit)}
fn limits()->OperationPlanLimits{OperationPlanLimits{max_operations:MAX_EDITS,max_dependencies:MAX_EDITS,max_arguments_per_operation:13,
    max_string_bytes:2048,max_total_argument_bytes:MAX_METADATA,max_serialized_bytes:MAX_PLAN}}
fn build(candidate:&PreparedStoredHttpsTargetCandidate<'_>,plan_id:PlanId)->Result<CompiledOperationPlan,C>{
    let forms=candidate.source.imported();let graph=forms.graph();let source=forms.source();
    let changes=&candidate.receipt.output.changes;
    if changes.is_empty()||changes.len()>MAX_EDITS||changes.len()!=candidate.anchors.len(){return Err(C::Binding);}
    let revision=RevisionId::parse(candidate.version.binding.source_revision.public_id()).map_err(|_|C::Binding)?;
    let snapshot=SelectorSnapshot::build(graph,revision.clone(),SelectorLimits::default()).map_err(|_|C::Owner)?;
    let owners=resolve_original_source_owners(graph,source,&candidate.anchors).map_err(|_|C::Owner)?;
    let capability=CapabilityId::parse(HTTPS_EDIT_CAPABILITY).map_err(|_|C::Compilation)?;
    let mut definition=CapabilityDefinitionDraft::new(capability.clone());
    for name in ARGUMENTS{definition.arguments.insert(name.into(),ArgumentSpec{kind:ArgumentKind::Text{max_bytes:2048},required:true,default:None,default_policy:DefaultPolicy::Locked});}
    let catalog=CapabilityCatalog::from_drafts(vec![definition]).map_err(|_|C::Compilation)?;
    let common=[hex::encode(candidate.receipt.output.source_package_sha256),hex::encode(candidate.receipt.output.output_package_sha256),
        hex::encode(digest(&candidate.receipt,MAX_METADATA)?),candidate.version.artifact.public_id(),hex::encode(candidate.version.digest.as_bytes()),
        candidate.version.binding.policy_version.to_string(),candidate.version.binding.policy_generation.to_string()];
    let mut operations=Vec::new();operations.try_reserve_exact(changes.len()).map_err(|_|C::Limit)?;
    for(n,((change,anchor),owner))in changes.iter().zip(&candidate.anchors).zip(owners).enumerate(){
        if anchor.fingerprint_sha256!=change.source_field_sha256{return Err(C::Binding);}
        let mut arguments:BTreeMap<String,ArgumentDraft>=ARGUMENTS[..7].iter().zip(&common).map(|(name,value)|((*name).into(),ArgumentDraft::Text(value.clone()))).collect();
        let field=[serde_json::to_string(anchor).map_err(|_|C::Limit)?,change.source_reference_id.as_str().to_owned(),hex::encode(change.source_field_sha256),
            hex::encode(change.source_meaning_sha256),change.output_target_sha256.clone(),"actual_structural_owner_with_exact_https_field/v1".into()];
        for(name,value)in ARGUMENTS[7..].iter().zip(field){arguments.insert((*name).into(),ArgumentDraft::Text(value));}
        operations.push(OperationDraft{operation_id:OperationId::parse(format!("https-field-{n:06}")).map_err(|_|C::Compilation)?,capability_id:capability.clone(),
            selector:SelectorDraft::one(Selector::by_logical_id(owner)),arguments,depends_on:vec![]});
    }
    OperationPlanCompiler::new(limits()).map_err(|_|C::Compilation)?.compile(OperationPlanDraft::new(plan_id,revision,operations),&catalog,&snapshot,&snapshot.expectation()).map_err(|_|C::Compilation)
}
fn receipt(candidate:&PreparedStoredHttpsTargetCandidate<'_>,plan:&CompiledOperationPlan)->Result<CompiledHttpsTargetReceipt,C>{
    let graph=candidate.source.imported().graph();let head=candidate.source.compiler_head();
    let graph_sha=graph.canonical_sha256().map_err(|_|C::Binding)?;
    if head.revision_id()!=Some(candidate.version.binding.source_revision)||head.generation()!=candidate.version.binding.source_head_generation
        ||plan.base_revision().as_str()!=candidate.version.binding.source_revision.public_id()||plan.base_graph_sha256()!=graph_sha
        ||plan.operations().len()!=candidate.anchors.len()||plan.operations().len()!=candidate.receipt.output.changes.len()
        ||plan.operations().iter().any(|op|op.capability_id().as_str()!=HTTPS_EDIT_CAPABILITY){return Err(C::Binding);}
    Ok(CompiledHttpsTargetReceipt{profile:PROFILE,capability_id:HTTPS_EDIT_CAPABILITY,plan_id:plan.plan_id().clone(),base_revision:plan.base_revision().clone(),
        head_generation:head.generation(),source_graph_sha256:graph_sha,source_package_sha256:candidate.receipt.output.source_package_sha256,
        output_package_sha256:candidate.receipt.output.output_package_sha256,stored_receipt_sha256:digest(&candidate.receipt,MAX_METADATA)?,
        source_anchors_sha256:digest(&candidate.anchors,MAX_METADATA)?,compiled_plan_sha256:digest(plan,MAX_PLAN)?,source_field_operations:plan.operations().len(),execution_or_publication_authority:false})
}
impl<'a> PreparedStoredHttpsTargetCandidate<'a>{
    /// Moves the original candidate, retaining only selected anchors; no graph/candidate clone or lowering replay.
    /// # Errors
    /// Requires fresh stored policy/source authorization before and after original owner/compiler work.
    pub fn compile<R,B,S,V,P>(self,provider:&StoredFormProvider<'_,R,B,S,V>,repository:&P,plan_id:PlanId,now:u64)
        ->Result<PreparedCompiledHttpsTargetCandidate<'a>,C>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository,P:HttpsTargetPolicyRepository{
        let(plan,receipt)=self.with_verified_bytes(provider,repository,now,|bytes|{
            if <[u8;32]>::from(Sha256::digest(bytes))!=self.receipt.output.output_package_sha256{return Err(C::Binding);}
            let plan=build(&self,plan_id)?;let receipt=receipt(&self,&plan)?;Ok((plan,receipt))
        })??;
        self.fresh(provider,repository,now)?;
        Ok(PreparedCompiledHttpsTargetCandidate{candidate:self,plan,receipt})
    }
}
impl PreparedCompiledHttpsTargetCandidate<'_>{
    pub(crate) fn source(&self)->&StoredImportedDocumentForms{&self.candidate.source}
    #[must_use]pub const fn compiled(&self)->&CompiledOperationPlan{&self.plan}
    #[must_use]pub const fn receipt(&self)->&CompiledHttpsTargetReceipt{&self.receipt}
    fn check(&self)->Result<(),C>{if receipt(&self.candidate,&self.plan)?!=self.receipt{return Err(C::Binding);}Ok(())}
    /// # Errors
    /// No compiler or writer replay; original current service/policy checks and immutable plan integrity only.
    pub fn verify<R,B,S,V,P>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,repository:&P,now:u64)->Result<&CompiledHttpsTargetReceipt,C>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository,P:HttpsTargetPolicyRepository{
        self.check()?;self.candidate.verify(provider,repository,now)?;Ok(&self.receipt)
    }
    /// # Errors
    /// Plan hashing does not bypass the original sole byte-delivery and final current policy/head checks.
    pub fn with_verified_bytes<R,B,S,V,P,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,repository:&P,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,C>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository,P:HttpsTargetPolicyRepository{
        self.check()?;Ok(self.candidate.with_verified_bytes(provider,repository,now,consume)?)
    }
    /// # Errors
    /// A local compiler catalog is plan data, not an attested registry, policy lease, CAS or Native route.
    pub fn require_current_product_route<R,B,S,V,P>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,repository:&P,now:u64)->Result<(),C>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository,P:HttpsTargetPolicyRepository{
        self.check()?;Ok(self.candidate.require_current_product_route(provider,repository,now)?)
    }
}
