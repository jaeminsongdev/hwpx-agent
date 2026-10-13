//! Explicit caller policy bound to immutable actual observations, not issuer authority.
use std::{collections::BTreeMap, fmt, io};

use domain_ir::{
    DocumentGraph, DocumentGraphLimits, DocumentId, Flow, FormButtonValue, FormControlLimitConfig,
    FormControlLimits, FormControlPayload, FormControlState, FormDocumentState,
    FormSelectionValidation, FormTextValidation, LogicalId, NativeFormTag, Node, PropertyValue,
    SourceAnchorHandle,
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use super::{FormImportError, ImportedDocumentForms, actual_map, form_observation};
use crate::{
    NativeFormControlObservation, NativeFormObservedPayload, NativeFormPackageError,
    NativeFormPackageLimits, NativeFormPackagePolicy, NativeFormPackageReader,
    document_import::{ImportedSourcePackage, hex_digest},
};

pub const FORM_POLICY_PROFILE: &str = "hwpx-agent.document-import-explicit-form-policy/partial-v1";
pub const FORM_POLICY_SCOPE: &str =
    "explicit_caller_policy_source_bound_component_not_authoritative_full_document_or_execution";
pub const COMPONENT_IDENTITY_SCOPE: &str =
    "source_local_component_reservation_not_observed_native_id_or_persistent_identity";

/// Version/document-bound envelope. Equality proves binding, not the caller's authority.
#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct FormPolicySourceBinding {
    pub document_id: DocumentId,
    pub source_package_sha256: [u8; 32],
    pub source_provenance_sha256: [u8; 32],
    pub observed_graph_sha256: [u8; 32],
}
impl FormPolicySourceBinding {
    #[must_use]
    pub fn for_imported(imported: &ImportedDocumentForms) -> Self {
        Self {
            document_id: imported.graph().document_id().clone(),
            source_package_sha256: imported.receipt().source_package_sha256,
            source_provenance_sha256: imported.receipt().source_provenance_sha256,
            observed_graph_sha256: imported.receipt().graph_sha256,
        }
    }
}
impl fmt::Debug for FormPolicySourceBinding {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("FormPolicySourceBinding(<redacted>)")
    }
}

/// Only unobserved policy fields are accepted. Current values, names, items,
/// native identities, positions, styles and opaque state cannot be overridden.
#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum ExplicitFormPolicy {
    Text {
        default_value: String,
        validation: FormTextValidation,
    },
    Checkbox {
        default_value: FormButtonValue,
        must_be_checked: bool,
    },
    Radio {
        default_value: FormButtonValue,
        group_required: bool,
    },
    Combo {
        default_selected_value: Option<String>,
        validation: FormSelectionValidation,
    },
    List {
        default_selected_value: Option<String>,
        validation: FormSelectionValidation,
    },
}
impl fmt::Debug for ExplicitFormPolicy {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ExplicitFormPolicy(<redacted>)")
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct SourceFormPolicy {
    pub node_id: LogicalId,
    pub source_anchor: SourceAnchorHandle,
    pub values: ExplicitFormPolicy,
}
impl fmt::Debug for SourceFormPolicy {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("SourceFormPolicy(<redacted>)")
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct FormPolicyBindingReceipt {
    pub profile: &'static str,
    pub qualification: &'static str,
    pub component_identity_scope: &'static str,
    pub source: FormPolicySourceBinding,
    pub native_binding_sha256: [u8; 32],
    pub policy_sha256: [u8; 32],
    pub state_sha256: [u8; 32],
    pub graph_sha256: [u8; 32],
    pub form_controls: usize,
    pub kinds: [usize; 5],
    pub legacy_reference_state: String,
    pub verified_native_reference_overlay_issues: usize,
}

/// Owns complete form COMPONENT state alongside the still-partial actual body
/// graph. Not deserializable, not a full importer, persisted issuer or route.
pub struct PolicyBoundDocumentForms<'a> {
    imported: &'a ImportedDocumentForms,
    policies: Vec<SourceFormPolicy>,
    state: FormDocumentState,
    graph: DocumentGraph,
    receipt: FormPolicyBindingReceipt,
}
impl fmt::Debug for PolicyBoundDocumentForms<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("PolicyBoundDocumentForms(<redacted>)")
    }
}
impl<'a> PolicyBoundDocumentForms<'a> {
    /// Binds an exact ordered policy set to actual original native observations.
    /// No caller graph/map/current-value fields or silent policy defaults.
    /// # Errors
    /// Rejects stale document/source/graph/anchors, incomplete/reordered policy,
    /// unsupported kinds, invalid domain defaults/groups and finite budgets.
    pub fn bind(
        imported: &'a ImportedDocumentForms,
        binding: &FormPolicySourceBinding,
        policies: &[SourceFormPolicy],
    ) -> Result<Self, FormPolicyBindingError> {
        let limits = form_limits()?;
        validate_bindings(imported, binding, policies, limits)?;
        let policy_sha256 = bounded_policy_digest(policies, limits)?;
        let map = actual_map(imported.source())?;
        let readback = NativeFormPackageReader::read(
            &imported.source().original,
            &map,
            NativeFormPackageLimits::default(),
        )?;
        let native_binding_sha256: [u8; 32] =
            Sha256::digest(readback.bindings().canonical_json()?).into();
        if readback.package_sha256() != hex_digest(binding.source_package_sha256)
            || Some(native_binding_sha256) != imported.receipt().native_binding_sha256
        {
            return Err(FormPolicyBindingError::Binding);
        }
        let by_node: BTreeMap<_, _> = policies.iter().map(|p| (&p.node_id, p)).collect();
        let actual_observations: BTreeMap<_, _> =
            imported.forms().iter().map(|o| (&o.node_id, o)).collect();
        let mut native_policies = Vec::new();
        for section in readback.sections() {
            for observed in section.controls() {
                let observation = form_observation(imported.source(), observed)?;
                if actual_observations.get(&observation.node_id).copied() != Some(&observation) {
                    return Err(FormPolicyBindingError::Binding);
                }
                let policy = by_node
                    .get(&observation.node_id)
                    .ok_or(FormPolicyBindingError::Binding)?;
                native_policies.push(NativeFormPackagePolicy {
                    identity: observed.component_identity.clone(),
                    payload: merge_policy(observed, &policy.values)?,
                });
            }
        }
        let state = readback.bind_policies(&native_policies, limits)?;
        readback.verify_domain_state(&state, &native_policies, limits)?;
        let state_sha256 = Sha256::digest(
            state
                .canonical_json(limits)
                .map_err(|_| FormPolicyBindingError::Budget)?,
        )
        .into();
        let graph = policy_graph(imported, &state, policy_sha256, state_sha256)?;
        let (legacy, issues) = readback.reference_overlay_status();
        let receipt = FormPolicyBindingReceipt {
            profile: FORM_POLICY_PROFILE,
            qualification: FORM_POLICY_SCOPE,
            component_identity_scope: COMPONENT_IDENTITY_SCOPE,
            source: binding.clone(),
            native_binding_sha256,
            policy_sha256,
            state_sha256,
            graph_sha256: graph
                .canonical_sha256()
                .map_err(|_| FormPolicyBindingError::Graph)?,
            form_controls: state.controls().len(),
            kinds: imported.receipt().kinds,
            legacy_reference_state: legacy.into(),
            verified_native_reference_overlay_issues: issues,
        };
        Ok(Self {
            imported,
            policies: policies.to_vec(),
            state,
            graph,
            receipt,
        })
    }

    /// Contains source-local COMPONENT reservations from the original domain
    /// API, never observed XML IDs or stable cross-version document identities.
    #[must_use]
    pub const fn state(&self) -> &FormDocumentState {
        &self.state
    }
    #[must_use]
    pub const fn graph(&self) -> &DocumentGraph {
        &self.graph
    }
    #[must_use]
    pub const fn receipt(&self) -> &FormPolicyBindingReceipt {
        &self.receipt
    }

    /// Fresh whole-source import and complete reconstruction, not hash refresh.
    /// # Errors
    /// Rejects any source, supplied policy envelope/value, complete graph or state drift.
    pub fn verify_source(
        &self,
        fresh: &[u8],
        binding: &FormPolicySourceBinding,
        policies: &[SourceFormPolicy],
    ) -> Result<FormPolicyBindingReceipt, FormPolicyBindingError> {
        if binding != &self.receipt.source || policies != self.policies {
            return Err(FormPolicyBindingError::Binding);
        }
        self.imported.verify_source(fresh)?;
        let imported = ImportedDocumentForms::import(
            ImportedSourcePackage::import(
                fresh,
                binding.document_id.clone(),
                binding.source_package_sha256,
                self.imported.source().limits,
            )
            .map_err(FormImportError::from)?,
        )?;
        let rebuilt = PolicyBoundDocumentForms::bind(&imported, binding, policies)?;
        if rebuilt.state != self.state
            || rebuilt.graph != self.graph
            || rebuilt.receipt != self.receipt
            || imported.graph() != self.imported.graph()
        {
            return Err(FormPolicyBindingError::Binding);
        }
        Ok(rebuilt.receipt)
    }
}

fn form_limits() -> Result<FormControlLimits, FormPolicyBindingError> {
    FormControlLimits::new(FormControlLimitConfig::default())
        .map_err(|_| FormPolicyBindingError::Budget)
}
fn validate_bindings(
    imported: &ImportedDocumentForms,
    binding: &FormPolicySourceBinding,
    policies: &[SourceFormPolicy],
    limits: FormControlLimits,
) -> Result<(), FormPolicyBindingError> {
    if binding != &FormPolicySourceBinding::for_imported(imported)
        || policies.len() != imported.forms().len()
    {
        return Err(FormPolicyBindingError::Binding);
    }
    // Do not invent empty native catalog/protection attestations for a no-form
    // source accepted by the earlier body importer.
    if policies.is_empty() {
        return Err(FormPolicyBindingError::NoForms);
    }
    if policies.len() > limits.config().controls {
        return Err(FormPolicyBindingError::Budget);
    }
    for (policy, observed) in policies.iter().zip(imported.forms()) {
        if policy.node_id != observed.node_id || policy.source_anchor != observed.source_anchor {
            return Err(FormPolicyBindingError::Binding);
        }
        imported
            .source()
            .resolve_anchor(&policy.source_anchor)
            .map_err(FormImportError::from)?;
    }
    Ok(())
}

/// Hash while streaming through the original default input-byte ceiling BEFORE
/// converting/cloning caller policy strings or creating the complete state.
fn bounded_policy_digest(
    policies: &[SourceFormPolicy],
    limits: FormControlLimits,
) -> Result<[u8; 32], FormPolicyBindingError> {
    let mut writer = PolicyBudget {
        seen: 0,
        limit: limits.config().input_bytes,
        sha: Sha256::new(),
    };
    serde_json::to_writer(&mut writer, policies).map_err(|_| FormPolicyBindingError::Budget)?;
    Ok(writer.sha.finalize().into())
}
struct PolicyBudget {
    seen: usize,
    limit: usize,
    sha: Sha256,
}
impl io::Write for PolicyBudget {
    fn write(&mut self, bytes: &[u8]) -> io::Result<usize> {
        let seen = self
            .seen
            .checked_add(bytes.len())
            .ok_or_else(|| io::Error::other("policy budget"))?;
        if seen > self.limit {
            return Err(io::Error::other("policy budget"));
        }
        self.seen = seen;
        self.sha.update(bytes);
        Ok(bytes.len())
    }
    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}

/// Only the explicitly typed policy fields are merged; the entire resulting
/// payload is checked by the unchanged native-policy comparator and domain.
fn merge_policy(
    observed: &NativeFormControlObservation,
    policy: &ExplicitFormPolicy,
) -> Result<FormControlPayload, FormPolicyBindingError> {
    let kind = match (observed.tag, policy) {
        (NativeFormTag::Edit, ExplicitFormPolicy::Text { .. }) => "text",
        (NativeFormTag::CheckBtn, ExplicitFormPolicy::Checkbox { .. }) => "checkbox",
        (NativeFormTag::RadioBtn, ExplicitFormPolicy::Radio { .. }) => "radio",
        (NativeFormTag::ComboBox, ExplicitFormPolicy::Combo { .. }) => "combo",
        (NativeFormTag::ListBox, ExplicitFormPolicy::List { .. }) => "list",
        _ => return Err(FormPolicyBindingError::Kind),
    };
    let mut native =
        serde_json::to_value(&observed.payload).map_err(|_| FormPolicyBindingError::Graph)?;
    let explicit = serde_json::to_value(policy).map_err(|_| FormPolicyBindingError::Graph)?;
    let target = native
        .as_object_mut()
        .ok_or(FormPolicyBindingError::Graph)?;
    for (key, value) in explicit.as_object().ok_or(FormPolicyBindingError::Graph)? {
        if key != "kind" {
            target.insert(key.clone(), value.clone());
        }
    }
    target.insert("kind".into(), serde_json::Value::String(kind.into()));
    // A radio group's actual observed Some(name) is decoded by the domain's
    // required String field. Missing/invalid names are not invented here.
    if matches!(&observed.payload, NativeFormObservedPayload::Button { .. })
        && kind == "radio"
        && target
            .get("radio_group_name")
            .is_none_or(serde_json::Value::is_null)
    {
        return Err(FormPolicyBindingError::Kind);
    }
    serde_json::from_value(native).map_err(|_| FormPolicyBindingError::Kind)
}

fn policy_graph(
    imported: &ImportedDocumentForms,
    state: &FormDocumentState,
    policy_sha: [u8; 32],
    state_sha: [u8; 32],
) -> Result<DocumentGraph, FormPolicyBindingError> {
    let mut states: BTreeMap<_, _> = state
        .controls()
        .iter()
        .map(|c| (c.identity.logical_control_id.clone(), c))
        .collect();
    let mut draft = imported.graph().clone().into_draft();
    for section in &mut draft.sections {
        attach_state(&mut section.body, &mut states)?;
    }
    if !states.is_empty() {
        return Err(FormPolicyBindingError::Binding);
    }
    for (key, value) in [
        ("native_form_policy_profile", FORM_POLICY_PROFILE.into()),
        ("native_form_policy_scope", FORM_POLICY_SCOPE.into()),
        ("native_form_policy_sha256", hex_digest(policy_sha)),
        ("native_form_policy_state_sha256", hex_digest(state_sha)),
    ] {
        draft.metadata.insert(key, PropertyValue::Text(value));
    }
    DocumentGraph::from_draft(draft, DocumentGraphLimits::default())
        .map_err(|_| FormPolicyBindingError::Graph)
}
fn attach_state(
    flow: &mut Flow,
    states: &mut BTreeMap<LogicalId, &FormControlState>,
) -> Result<(), FormPolicyBindingError> {
    for node in &mut flow.children {
        match node {
            Node::Table(table) => {
                for cell in &mut table.cells {
                    attach_state(&mut cell.body, states)?;
                }
            }
            Node::Drawing(drawing) => attach_state(&mut drawing.children, states)?,
            Node::FormControl(form) => {
                let state = states
                    .remove(&form.common.node_id)
                    .ok_or(FormPolicyBindingError::Binding)?;
                if form.control_kind != state.payload.capability_id() {
                    return Err(FormPolicyBindingError::Binding);
                }
                let json =
                    serde_json::to_string(state).map_err(|_| FormPolicyBindingError::Graph)?;
                form.properties
                    .insert("complete_control_state_json", PropertyValue::Text(json));
                form.properties.insert(
                    "component_identity_scope",
                    PropertyValue::Text(COMPONENT_IDENTITY_SCOPE.into()),
                );
                form.properties.insert(
                    "policy_qualification",
                    PropertyValue::Text(FORM_POLICY_SCOPE.into()),
                );
            }
            _ => {}
        }
    }
    Ok(())
}

#[derive(Debug, Error)]
pub enum FormPolicyBindingError {
    #[error("form policy source or observation rejected")]
    Import(#[from] FormImportError),
    #[error("form policy native/domain validation rejected: {0}")]
    Native(#[from] NativeFormPackageError),
    #[error("form policy document/source/order/anchor binding rejected")]
    Binding,
    #[error("form policy kind rejected")]
    Kind,
    #[error("form policy budget rejected")]
    Budget,
    #[error("form policy graph rejected")]
    Graph,
    #[error("no-form source has no native form policy attestation")]
    NoForms,
}
