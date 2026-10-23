//! Source-bound bookmark command edits through the original common compiler.
//! This is editing an existing CROSSREF, not insertion or Native evaluation.
use super::*;
use crate::form_product_request::stored_operations::compiled_search::{
    bounded_hash, resolve_original_source_owners,
};
use domain_ir::{
    ArgumentDraft, ArgumentKind, ArgumentSpec, CapabilityCatalog, CapabilityDefinitionDraft,
    CapabilityId, CompiledOperationPlan, DefaultPolicy, OperationDraft, OperationId,
    OperationPlanCompiler, OperationPlanDraft, OperationPlanLimits, PlanId, RevisionId, Selector,
    SelectorDraft, SelectorLimits, SelectorSnapshot, SourceAnchorHandle,
};
use sha2::{Digest as _, Sha256};
use std::collections::BTreeMap;

/// Deliberately separate from REF-035's insertion capability. Local catalog
/// presence does not register or qualify an executable product route.
pub const BOOKMARK_COMMAND_EDIT_CAPABILITY: &str = "ref.crossref_command_edit";
const PROFILE: &str = "hwpx-agent.stored-source-bookmark-command-compiler/v1";
const MAX_EDITS: usize = 4096;
const MAX_METADATA: usize = 8 * 1024 * 1024;
const MAX_PLAN: usize = 16 * 1024 * 1024;
const ARGUMENTS: [&str; 12] = [
    "source_package_sha256",
    "output_package_sha256",
    "stored_receipt_sha256",
    "source_field_anchor_json",
    "source_reference_id",
    "source_field_sha256",
    "source_meaning_sha256",
    "output_command_sha256",
    "selected_target_id_sha256",
    "selected_target_state_sha256",
    "request_sha256",
    "owner_binding_profile",
];

// Called while the original field import is already borrowed. Retain only
// selected anchors, never another full field import/graph/candidate clone.
pub(super) fn selected_anchors(
    fields: &ImportedDocumentFields<'_>,
    output: &SourceBookmarkCommandReceipt,
) -> Result<Vec<SourceAnchorHandle>, E> {
    if output.changes.is_empty() || output.changes.len() > MAX_EDITS {
        return Err(E::Binding);
    }
    let by_id: BTreeMap<_, _> = fields
        .fields()
        .iter()
        .map(|f| (&f.reference_id, &f.begin_anchor))
        .collect();
    let mut selected = Vec::new();
    selected
        .try_reserve_exact(output.changes.len())
        .map_err(|_| E::Binding)?;
    for change in &output.changes {
        let anchor = by_id.get(&change.source_reference_id).ok_or(E::Binding)?;
        if anchor.fingerprint_sha256 != change.source_field_sha256 {
            return Err(E::Binding);
        }
        selected.push((**anchor).clone());
    }
    Ok(selected)
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct CompiledBookmarkCommandReceipt {
    pub profile: &'static str,
    pub capability_id: &'static str,
    pub plan_id: PlanId,
    pub base_revision: RevisionId,
    pub head_generation: u64,
    pub source_artifact: artifact_service::ArtifactId,
    pub source_graph_sha256: [u8; 32],
    pub source_package_sha256: [u8; 32],
    pub output_package_sha256: [u8; 32],
    pub stored_receipt_sha256: [u8; 32],
    pub source_anchors_sha256: [u8; 32],
    pub compiled_plan_sha256: [u8; 32],
    pub source_field_operations: usize,
    pub cached_values_preserved_not_refreshed: bool,
    pub execution_or_publication_authority: bool,
}
pub struct PreparedCompiledBookmarkCommandCandidate<'a> {
    candidate: PreparedStoredBookmarkCommandCandidate<'a>,
    plan: CompiledOperationPlan,
    receipt: CompiledBookmarkCommandReceipt,
}
impl fmt::Debug for PreparedCompiledBookmarkCommandCandidate<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("PreparedCompiledBookmarkCommandCandidate(<redacted>; no_registry_CAS_or_execution_authority)")
    }
}
#[derive(Debug, Error)]
pub enum BookmarkCommandCompileError {
    #[error("BOOKMARK_COMMAND_COMPILER_STORED_CANDIDATE_DENIED")]
    Stored(#[from] StoredBookmarkCommandError),
    #[error("BOOKMARK_COMMAND_COMPILER_SOURCE_OWNER_DENIED")]
    Owner,
    #[error("BOOKMARK_COMMAND_COMPILER_BINDING_DENIED")]
    Binding,
    #[error("BOOKMARK_COMMAND_COMPILER_LIMIT")]
    Limit,
    #[error("BOOKMARK_COMMAND_ORIGINAL_COMPILATION_DENIED")]
    Compilation,
}
type C = BookmarkCommandCompileError;
fn digest(value: &impl Serialize, maximum: usize) -> Result<[u8; 32], C> {
    bounded_hash(value, maximum).map_err(|_| C::Limit)
}
fn build(
    candidate: &PreparedStoredBookmarkCommandCandidate<'_>,
    plan_id: PlanId,
) -> Result<CompiledOperationPlan, C> {
    let forms = candidate.source.imported();
    let graph = forms.graph();
    let changes = &candidate.receipt.output.changes;
    if changes.is_empty() || changes.len() > MAX_EDITS || changes.len() != candidate.anchors.len() {
        return Err(C::Binding);
    }
    let head = candidate.source.compiler_head();
    let revision = RevisionId::parse(head.revision_id().ok_or(C::Binding)?.public_id())
        .map_err(|_| C::Binding)?;
    let snapshot = SelectorSnapshot::build(graph, revision.clone(), SelectorLimits::default())
        .map_err(|_| C::Owner)?;
    let owners = resolve_original_source_owners(graph, forms.source(), &candidate.anchors)
        .map_err(|_| C::Owner)?;
    let capability =
        CapabilityId::parse(BOOKMARK_COMMAND_EDIT_CAPABILITY).map_err(|_| C::Compilation)?;
    let mut definition = CapabilityDefinitionDraft::new(capability.clone());
    for name in ARGUMENTS {
        definition.arguments.insert(
            name.into(),
            ArgumentSpec {
                kind: ArgumentKind::Text { max_bytes: 2048 },
                required: true,
                default: None,
                default_policy: DefaultPolicy::Locked,
            },
        );
    }
    let catalog = CapabilityCatalog::from_drafts(vec![definition]).map_err(|_| C::Compilation)?;
    let common = [
        hex::encode(candidate.receipt.output.source_package_sha256),
        hex::encode(candidate.receipt.output.output_package_sha256),
        hex::encode(digest(&candidate.receipt, MAX_METADATA)?),
    ];
    let mut operations = Vec::new();
    operations
        .try_reserve_exact(changes.len())
        .map_err(|_| C::Limit)?;
    for (n, ((change, anchor), owner)) in changes
        .iter()
        .zip(&candidate.anchors)
        .zip(owners)
        .enumerate()
    {
        if anchor.fingerprint_sha256 != change.source_field_sha256 {
            return Err(C::Binding);
        }
        let mut arguments: BTreeMap<String, ArgumentDraft> = ARGUMENTS[..3]
            .iter()
            .zip(&common)
            .map(|(name, value)| ((*name).into(), ArgumentDraft::Text(value.clone())))
            .collect();
        let field = [
            serde_json::to_string(anchor).map_err(|_| C::Limit)?,
            change.source_reference_id.as_str().to_owned(),
            hex::encode(change.source_field_sha256),
            hex::encode(change.source_meaning_sha256),
            hex::encode(change.output_command_sha256),
            hex::encode(change.selected_target_id_sha256),
            change.selected_target_state_sha256.clone(),
            hex::encode(candidate.receipt.output.request_sha256),
            "actual_structural_owner_with_exact_bookmark_crossref_field/v1".into(),
        ];
        for (name, value) in ARGUMENTS[3..].iter().zip(field) {
            arguments.insert((*name).into(), ArgumentDraft::Text(value));
        }
        operations.push(OperationDraft {
            operation_id: OperationId::parse(format!("bookmark-command-{n:06}"))
                .map_err(|_| C::Compilation)?,
            capability_id: capability.clone(),
            selector: SelectorDraft::one(Selector::by_logical_id(owner)),
            arguments,
            depends_on: vec![],
        });
    }
    let limits = OperationPlanLimits {
        max_operations: MAX_EDITS,
        max_dependencies: MAX_EDITS,
        max_arguments_per_operation: ARGUMENTS.len(),
        max_string_bytes: 2048,
        max_total_argument_bytes: MAX_METADATA,
        max_serialized_bytes: MAX_PLAN,
    };
    OperationPlanCompiler::new(limits)
        .map_err(|_| C::Compilation)?
        .compile(
            OperationPlanDraft::new(plan_id, revision, operations),
            &catalog,
            &snapshot,
            &snapshot.expectation(),
        )
        .map_err(|_| C::Compilation)
}
fn receipt(
    candidate: &PreparedStoredBookmarkCommandCandidate<'_>,
    plan: &CompiledOperationPlan,
) -> Result<CompiledBookmarkCommandReceipt, C> {
    let graph_sha = candidate
        .source
        .imported()
        .graph()
        .canonical_sha256()
        .map_err(|_| C::Binding)?;
    let head = candidate.source.compiler_head();
    if head.revision_id().map(|id| id.public_id()) != Some(plan.base_revision().as_str().to_owned())
        || head.generation() != candidate.receipt.source.head_generation
        || plan.base_graph_sha256() != graph_sha
        || plan.operations().len() != candidate.anchors.len()
        || plan.operations().len() != candidate.receipt.output.changes.len()
        || plan
            .operations()
            .iter()
            .any(|op| op.capability_id().as_str() != BOOKMARK_COMMAND_EDIT_CAPABILITY)
        || !candidate
            .receipt
            .output
            .cached_values_preserved_not_refreshed
        || candidate.receipt.execution_or_publication_authority
    {
        return Err(C::Binding);
    }
    Ok(CompiledBookmarkCommandReceipt {
        profile: PROFILE,
        capability_id: BOOKMARK_COMMAND_EDIT_CAPABILITY,
        plan_id: plan.plan_id().clone(),
        base_revision: plan.base_revision().clone(),
        head_generation: head.generation(),
        source_artifact: candidate.receipt.source.source_artifact,
        source_graph_sha256: graph_sha,
        source_package_sha256: candidate.receipt.output.source_package_sha256,
        output_package_sha256: candidate.receipt.output.output_package_sha256,
        stored_receipt_sha256: digest(&candidate.receipt, MAX_METADATA)?,
        source_anchors_sha256: digest(&candidate.anchors, MAX_METADATA)?,
        compiled_plan_sha256: digest(plan, MAX_PLAN)?,
        source_field_operations: plan.operations().len(),
        cached_values_preserved_not_refreshed: true,
        execution_or_publication_authority: false,
    })
}
impl<'a> PreparedStoredBookmarkCommandCandidate<'a> {
    /// Move the original candidate into an original-compiler plan without
    /// re-importing meanings, re-lowering commands or cloning graph/output.
    /// # Errors
    /// Requires original current source checks before work and again after
    /// compilation, so a revocation during compilation cannot escape the gate.
    pub fn compile<R, B, S, V>(
        self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        plan_id: PlanId,
        now: u64,
    ) -> Result<PreparedCompiledBookmarkCommandCandidate<'a>, C>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        let (plan, receipt) = self.with_verified_bytes(provider, now, |bytes| {
            if <[u8; 32]>::from(Sha256::digest(bytes)) != self.receipt.output.output_package_sha256
            {
                return Err(C::Binding);
            }
            let plan = build(&self, plan_id)?;
            let receipt = receipt(&self, &plan)?;
            Ok((plan, receipt))
        })??;
        // Original byte-delivery boundary includes its final raw ACL/head read.
        // Repeat that authorization after compiler work, not merely before it.
        self.verify(provider, now)?;
        Ok(PreparedCompiledBookmarkCommandCandidate {
            candidate: self,
            plan,
            receipt,
        })
    }
}
impl PreparedCompiledBookmarkCommandCandidate<'_> {
    #[must_use]
    pub const fn compiled(&self) -> &CompiledOperationPlan {
        &self.plan
    }
    #[must_use]
    pub const fn receipt(&self) -> &CompiledBookmarkCommandReceipt {
        &self.receipt
    }
    fn check(&self) -> Result<(), C> {
        if receipt(&self.candidate, &self.plan)? != self.receipt {
            return Err(C::Binding);
        }
        Ok(())
    }
    /// # Errors
    /// Current stored source authorization and immutable plan integrity only;
    /// no compiler/lowerer replay, registration or write authority.
    pub fn verify<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<&CompiledBookmarkCommandReceipt, C>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.check()?;
        self.candidate.verify(provider, now)?;
        Ok(&self.receipt)
    }
    /// # Errors
    /// Retains the sole original current ACL/AEAD/head + writer callback. A
    /// denied underlying candidate remains denied even after later restoration.
    pub fn with_verified_bytes<R, B, S, V, T>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
        consume: impl FnOnce(&[u8]) -> T,
    ) -> Result<T, C>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.check()?;
        Ok(self.candidate.with_verified_bytes(provider, now, consume)?)
    }
    /// # Errors
    /// Compilation does not turn the original unqualified route into a grant.
    pub fn require_current_product_route<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<(), C>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.check()?;
        Ok(self
            .candidate
            .require_current_product_route(provider, now)?)
    }
}
