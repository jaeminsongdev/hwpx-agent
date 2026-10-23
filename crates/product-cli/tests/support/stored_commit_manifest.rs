use super::*;
// TEST ONLY. Construct synthetic graph/route evidence without touching actual P02 trust.
pub(super) fn manifest(f: &StoredFixture, tx: &str) -> Result<ExecutionManifest, Box<dyn Error>> {
    use domain_ir::*;
    let graph = DocumentGraph::from_draft(DocumentGraphDraft::new(DocumentId::parse("storage-component-fixture")?, vec![Section {
        section_id: LogicalId::parse("section")?, properties: Properties::new(), master_pages: vec![], headers_footers: vec![],
        body: Flow { children: vec![Node::Paragraph(ParagraphNode { common: NodeCommon::new(LogicalId::parse("p")?),
            inlines: vec![Inline::Text { text: "synthetic storage fixture".into() }], paragraph_properties: Properties::new() })] },
    }]), DocumentGraphLimits::default())?;
    let revision = RevisionId::parse(f.head.revision_id().ok_or("head")?.public_id())?;
    let snapshot = SelectorSnapshot::build(&graph, revision.clone(), SelectorLimits::default())?;
    let capability = CapabilityId::parse("edit.storage-fixture")?;
    let catalog = CapabilityCatalog::from_drafts(vec![CapabilityDefinitionDraft::new(capability.clone())])?;
    let plan = OperationPlanCompiler::new(OperationPlanLimits::default())?.compile(OperationPlanDraft::new(PlanId::parse("storage-plan")?, revision,
        vec![OperationDraft { operation_id: OperationId::parse("op")?, capability_id: capability.clone(),
            selector: SelectorDraft::one(Selector::by_logical_id(LogicalId::parse("p")?)),
            arguments: std::collections::BTreeMap::new(), depends_on: vec![] }]), &catalog, &snapshot, &snapshot.expectation())?;
    let profile = ExactTargetProfile::new(TargetProfileId::parse("storage-synthetic")?, "synthetic-only", Architecture::X86)?;
    let backend = BackendId::parse("storage-direct")?;
    let routes = CapabilityRouteCatalog::from_bindings(vec![RouteBinding::new(capability, backend.clone(), BackendKind::DirectHwpx,
        SupportState::Verified, profile.clone(), [9; 32], 7, 10, 10, PreservationImpact::Exact, SignatureImpact::Preserved)])?;
    let context = RouteContext::new(profile, [9; 32], 7, RegistryTrustState::SignatureVerified,
        PolicyScope::CurrentPcPersonalLocalDevelopment, PreservationRequirement::Exact, ProtectionState::Unprotected,
        1000, vec![BackendHealth::new(backend, BackendHealthState::Healthy, 3, 900, 500)])?;
    let route = CapabilityRouter::new(CapabilityRouterLimits::default())?.route(&plan.operations()[0], &context, &routes)?;
    Ok(ExecutionManifest::from_receipts(TransactionId::parse(tx)?, ArtifactId::parse(f.result.public_id())?,
        Sha256::digest(SOURCE).into(), SOURCE.len() as u64, &plan, &[route])?)
}
