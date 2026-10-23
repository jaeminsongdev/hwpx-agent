use super::*;
use domain_ir::{ArgumentDraft,ArgumentKind,ArgumentSpec,CapabilityCatalog,CapabilityDefinitionDraft,CapabilityId,DefaultPolicy,
    OperationDraft,OperationId,OperationPlanCompiler,OperationPlanDraft,OperationPlanLimits,Selector,SelectorDraft,SelectorLimits,SelectorSnapshot};
use std::collections::BTreeMap;
const OWNER_PROFILE:&str="actual_structural_owner_with_exact_source_edit/v1";
const NAMES:[&str;12]=["request_schema","source_package_sha256","output_package_sha256","mutation_receipt_sha256","edit_inventory_sha256",
    "raw_request_sha256","canonical_request_sha256","scoped_request_sha256","source_anchor_json","source_edit_index","source_edit_domain","owner_binding_profile"];
pub(super) fn compile(v:&CompilationView<'_>,p:&projection::Projection<'_>,schema:&'static str)->Result<CompiledOperationPlan,CompiledSearchError>{
    let snapshot=SelectorSnapshot::build(v.source.imported().graph(),v.revision.clone(),SelectorLimits::default()).map_err(|_|CompiledSearchError::Target)?;
    let owners=owners::resolve(v,p)?;let capability=CapabilityId::parse(v.capability).map_err(|_|CompiledSearchError::Compilation)?;
    let mut definition=CapabilityDefinitionDraft::new(capability.clone());
    for name in NAMES{definition.arguments.insert(name.into(),ArgumentSpec{kind:ArgumentKind::Text{max_bytes:2048},required:true,default:None,default_policy:DefaultPolicy::Locked});}
    let font_arguments=p.font_resources.as_ref().map(super::font_resources::HeaderResources::arguments).transpose()?;
    if let Some(resources)=&font_arguments{let bytes:usize=resources.iter().map(|(name,value)|name.len()+value.len()).sum();bytes.checked_mul(p.edits.len()).filter(|n|*n<=MAX_METADATA_BYTES).ok_or(CompiledSearchError::Limit)?;}
    if let Some(resources)=&font_arguments{for(name,_)in resources{definition.arguments.insert((*name).into(),ArgumentSpec{kind:ArgumentKind::Text{max_bytes:2048},required:true,default:None,default_policy:DefaultPolicy::Locked});}}
    let catalog=CapabilityCatalog::from_drafts(vec![definition]).map_err(|_|CompiledSearchError::Compilation)?;
    let common=[schema.to_owned(),hex::encode(p.source),hex::encode(p.output),hex::encode(p.receipt_sha),hex::encode(p.inventory_sha),
        v.raw.to_owned(),v.canonical.to_owned(),v.scoped.to_owned()];
    let mut operations=Vec::with_capacity(p.edits.len());
    for(n,(edit,owner))in p.edits.iter().zip(owners).enumerate(){
        let mut arguments:BTreeMap<String,ArgumentDraft>=NAMES[..8].iter().zip(&common).map(|(name,value)|((*name).into(),ArgumentDraft::Text(value.clone()))).collect();
        let anchor=serde_json::to_string(edit.anchor).map_err(|_|CompiledSearchError::Compilation)?;
        for(name,value)in NAMES[8..].iter().zip([anchor,n.to_string(),p.domain.to_owned(),OWNER_PROFILE.to_owned()]){arguments.insert((*name).into(),ArgumentDraft::Text(value));}
        if let Some(resources)=&font_arguments{for(name,value)in resources{arguments.insert((*name).into(),ArgumentDraft::Text(value.clone()));}}
        operations.push(OperationDraft{operation_id:OperationId::parse(format!("source-edit-{n:06}")).map_err(|_|CompiledSearchError::Compilation)?,
            capability_id:capability.clone(),selector:SelectorDraft::one(Selector::by_logical_id(owner)),arguments,depends_on:vec![]});
    }
    let limits=OperationPlanLimits{max_operations:MAX_EDITS,max_dependencies:MAX_EDITS,max_arguments_per_operation:if font_arguments.is_some(){15}else{12},max_string_bytes:2048,
        max_total_argument_bytes:8*1024*1024,max_serialized_bytes:MAX_PLAN_BYTES};
    OperationPlanCompiler::new(limits).map_err(|_|CompiledSearchError::Compilation)?
        .compile(OperationPlanDraft::new(v.plan_id.clone(),v.revision.clone(),operations),&catalog,&snapshot,&snapshot.expectation())
        .map_err(|_|CompiledSearchError::Compilation)
}
