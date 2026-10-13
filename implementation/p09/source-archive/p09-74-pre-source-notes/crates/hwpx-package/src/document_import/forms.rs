//! Actual native form observations in the real body graph, without inferred policy.
pub mod policies;

use std::{collections::BTreeMap, fmt};

use domain_ir::{
    DocumentGraph, DocumentGraphLimits, Flow, FormCommonProperties, FormControlIdentity,
    FormControlNode, LogicalId, NativeFormTag, Node, PropertyValue, SourceAnchorHandle,
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use super::{
    ImportedSourcePackage, SourceImportError,
    structure::{ImportedDocumentStructure, StructureImportError},
};
use crate::{
    NativeFormHwpxMap, NativeFormObservedIdentity, NativeFormObservedPayload,
    NativeFormPackageError, NativeFormPackageLimits, NativeFormPackageMap, NativeFormPackageReader,
    NativeFormPackageSectionMap, NativeFormPhysicalAnchor,
};

const HP: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
pub const FORM_IMPORT_PROFILE: &str = "hwpx-agent.document-import-observed-forms/partial-v1";
pub const FORM_OBSERVATION_SCOPE: &str =
    "observed_native_values_not_default_validation_or_execution_policy";

/// Native fields only. Internal component reservations are deliberately absent:
/// they are not observed native IDs and must not become product identities.
#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ImportedFormObservation {
    pub node_id: LogicalId,
    pub source_anchor: SourceAnchorHandle,
    pub native_identity: NativeFormObservedIdentity,
    pub tag: NativeFormTag,
    pub physical_anchor: NativeFormPhysicalAnchor,
    pub common: FormCommonProperties,
    pub payload: NativeFormObservedPayload,
    pub shape_locked: bool,
    pub geometry_sha256: String,
    pub preserved_opaque_sha256: String,
    pub raw_control_sha256: String,
}

impl fmt::Debug for ImportedFormObservation {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ImportedFormObservation(<redacted>)")
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct FormImportReceipt {
    pub profile: &'static str,
    pub qualification: &'static str,
    pub source_package_sha256: [u8; 32],
    pub source_provenance_sha256: [u8; 32],
    pub body_graph_sha256: [u8; 32],
    pub graph_sha256: [u8; 32],
    pub native_binding_sha256: Option<[u8; 32]>,
    /// Preserve the original legacy verdict, even when the native overlay is
    /// independently accepted. Do not relabel it as a legacy profile PASS.
    pub legacy_reference_state: Option<String>,
    pub verified_native_reference_overlay_issues: usize,
    pub form_controls: usize,
    /// edit/check/radio/combo/list; not a native execution or coverage count.
    pub kinds: [usize; 5],
    pub remaining_opaque_nodes: usize,
}

/// Owns the immutable actual source/body and observation-qualified form graph.
/// There is no deserialization, default-policy inference or route capability.
pub struct ImportedDocumentForms {
    body: ImportedDocumentStructure,
    graph: DocumentGraph,
    forms: Vec<ImportedFormObservation>,
    receipt: FormImportReceipt,
}

impl fmt::Debug for ImportedDocumentForms {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("ImportedDocumentForms")
            .field("form_controls", &self.forms.len())
            .finish_non_exhaustive()
    }
}

impl ImportedDocumentForms {
    /// Derives source IDs/maps itself and invokes the unchanged complete native
    /// package reader. Only observed values become typed form nodes. The body
    /// profile/scope remains explicitly PARTIAL and full-product input denied.
    /// # Errors
    /// Rejects supported body failures, bad native catalogs/identities/values,
    /// missing actual source positions, unrepresented forms or graph budgets.
    pub fn import(source: ImportedSourcePackage) -> Result<Self, FormImportError> {
        let body = ImportedDocumentStructure::import(source)?;
        let map = actual_map(body.source())?;
        let control_count: usize = map
            .sections
            .iter()
            .map(|s| s.map.component_controls.len())
            .sum();
        let mut forms = BTreeMap::new();
        let mut draft = body.graph().clone().into_draft();
        let mut native_binding_sha256 = None;
        let mut legacy_reference_state = None;
        let mut verified_native_reference_overlay_issues = 0;
        if control_count != 0 {
            let readback = NativeFormPackageReader::read(
                &body.source().original,
                &map,
                NativeFormPackageLimits::default(),
            )?;
            if readback.package_sha256() != super::hex_digest(body.source().source_sha256) {
                return Err(FormImportError::Binding);
            }
            let binding = readback.bindings().canonical_json()?;
            native_binding_sha256 = Some(Sha256::digest(&binding).into());
            let (legacy, issues) = readback.reference_overlay_status();
            legacy_reference_state = Some(legacy.into());
            verified_native_reference_overlay_issues = issues;
            draft.metadata.insert(
                "native_form_binding_sha256",
                PropertyValue::Text(super::hex_digest(
                    native_binding_sha256.ok_or(FormImportError::Binding)?,
                )),
            );
            draft.security_state.properties.insert(
                "native_form_protection_signal_observed",
                PropertyValue::Boolean(readback.bindings().protection_signal_observed()),
            );
            for section in readback.sections() {
                for observed in section.controls() {
                    let node_id = observed.component_identity.logical_control_id.clone();
                    let value = form_observation(body.source(), observed)?;
                    if forms.insert(node_id, value).is_some() {
                        return Err(FormImportError::Binding);
                    }
                }
            }
        }
        if forms.len() != control_count {
            return Err(FormImportError::Binding);
        }
        let mut imported_forms = Vec::new();
        for section in &mut draft.sections {
            replace_forms(&mut section.body, &mut forms, &mut imported_forms)?;
        }
        if !forms.is_empty() || imported_forms.len() != control_count {
            return Err(FormImportError::Unrepresented);
        }
        draft.metadata.insert(
            "native_form_import_profile",
            PropertyValue::Text(FORM_IMPORT_PROFILE.into()),
        );
        draft.metadata.insert(
            "native_form_import_scope",
            PropertyValue::Text(FORM_OBSERVATION_SCOPE.into()),
        );
        let graph = DocumentGraph::from_draft(draft, DocumentGraphLimits::default())
            .map_err(|_| FormImportError::Graph)?;
        let mut kinds = [0; 5];
        for form in &imported_forms {
            kinds[kind_index(form.tag)] += 1;
        }
        let receipt = FormImportReceipt {
            profile: FORM_IMPORT_PROFILE,
            qualification: FORM_OBSERVATION_SCOPE,
            source_package_sha256: body.source().source_sha256,
            source_provenance_sha256: body.source().receipt().provenance_sha256,
            body_graph_sha256: body.receipt().graph_sha256,
            graph_sha256: graph
                .canonical_sha256()
                .map_err(|_| FormImportError::Graph)?,
            native_binding_sha256,
            legacy_reference_state,
            verified_native_reference_overlay_issues,
            form_controls: imported_forms.len(),
            kinds,
            remaining_opaque_nodes: body
                .receipt()
                .opaque_nodes
                .checked_sub(control_count)
                .ok_or(FormImportError::Binding)?,
        };
        Ok(Self {
            body,
            graph,
            forms: imported_forms,
            receipt,
        })
    }

    #[must_use]
    pub const fn source(&self) -> &ImportedSourcePackage {
        self.body.source()
    }
    #[must_use]
    pub const fn graph(&self) -> &DocumentGraph {
        &self.graph
    }
    #[must_use]
    pub fn forms(&self) -> &[ImportedFormObservation] {
        &self.forms
    }
    #[must_use]
    pub const fn receipt(&self) -> &FormImportReceipt {
        &self.receipt
    }

    /// Rebuilds the complete actual source/body/form graph and observations.
    /// # Errors
    /// Rejects source or any full graph/observation/receipt drift, not just hashes.
    pub fn verify_source(&self, fresh: &[u8]) -> Result<FormImportReceipt, FormImportError> {
        let source = ImportedSourcePackage::import(
            fresh,
            self.source().document_id.clone(),
            self.source().source_sha256,
            self.source().limits,
        )?;
        if &source != self.source() {
            return Err(FormImportError::Binding);
        }
        let rebuilt = Self::import(source)?;
        if rebuilt.graph != self.graph
            || rebuilt.forms != self.forms
            || rebuilt.body.graph() != self.body.graph()
            || rebuilt.receipt != self.receipt
        {
            return Err(FormImportError::Binding);
        }
        Ok(rebuilt.receipt)
    }
}

fn form_observation(
    source: &ImportedSourcePackage,
    observed: &crate::NativeFormControlObservation,
) -> Result<ImportedFormObservation, FormImportError> {
    let node_id = observed.component_identity.logical_control_id.clone();
    let anchor = actual_anchor(source, &node_id)?;
    if observed.raw_control_sha256 != super::hex_digest(anchor.fingerprint_sha256) {
        return Err(FormImportError::Binding);
    }
    Ok(ImportedFormObservation {
        node_id,
        source_anchor: anchor,
        native_identity: observed.native_identity.clone(),
        tag: observed.tag,
        physical_anchor: observed.anchor.clone(),
        common: observed.common.clone(),
        payload: observed.payload.clone(),
        shape_locked: observed.shape_locked,
        geometry_sha256: observed.geometry_sha256.clone(),
        preserved_opaque_sha256: observed.preserved_opaque_sha256.clone(),
        raw_control_sha256: observed.raw_control_sha256.clone(),
    })
}

fn actual_map(source: &ImportedSourcePackage) -> Result<NativeFormPackageMap, FormImportError> {
    let mut sections = Vec::new();
    let mut reservation: u32 = 0;
    for path in source.spine() {
        if path.as_str() == "Contents/header.xml" {
            continue;
        }
        let part = source
            .parts()
            .iter()
            .find(|p| p.path() == path)
            .ok_or(FormImportError::Binding)?;
        let xml = part.xml().ok_or(FormImportError::Binding)?;
        let mut paragraph_ids = Vec::new();
        let mut component_controls = Vec::new();
        for (index, element) in xml.elements().iter().enumerate() {
            if element.name().namespace() != Some(HP) {
                continue;
            }
            let anchor = part.element_anchor(index).ok_or(FormImportError::Binding)?;
            if element.name().local_name() == "p" {
                paragraph_ids.push(node_id(anchor)?);
            } else if native_tag(element.name().local_name()).is_some() {
                reservation = reservation.checked_add(1).ok_or(FormImportError::Binding)?;
                component_controls.push(FormControlIdentity {
                    logical_control_id: node_id(anchor)?,
                    // Original reader's COMPONENT reservation, not observed native
                    // object identity. Observed-form IR/API excludes it; explicit
                    // policy state may retain it only as a qualified source-local
                    // COMPONENT identity, never an observed or persistent ID.
                    native_object_id: reservation,
                });
            }
        }
        sections.push(NativeFormPackageSectionMap {
            part: path.as_str().into(),
            map: NativeFormHwpxMap {
                paragraph_ids,
                component_controls,
            },
        });
    }
    Ok(NativeFormPackageMap { sections })
}

fn node_id(anchor: &SourceAnchorHandle) -> Result<LogicalId, FormImportError> {
    LogicalId::parse(format!("node-{}", anchor.opaque_handle.as_str()))
        .map_err(|_| FormImportError::Binding)
}

fn actual_anchor(
    source: &ImportedSourcePackage,
    id: &LogicalId,
) -> Result<SourceAnchorHandle, FormImportError> {
    let handle = id
        .as_str()
        .strip_prefix("node-")
        .ok_or(FormImportError::Binding)?;
    let handle = LogicalId::parse(handle).map_err(|_| FormImportError::Binding)?;
    let (part, element) = source
        .anchors
        .get(&handle)
        .ok_or(FormImportError::Binding)?;
    let anchor = source.parts[*part]
        .element_anchor(element.ok_or(FormImportError::Binding)?)
        .ok_or(FormImportError::Binding)?;
    source.resolve_anchor(anchor)?;
    Ok(anchor.clone())
}

fn replace_forms(
    flow: &mut Flow,
    forms: &mut BTreeMap<LogicalId, ImportedFormObservation>,
    output: &mut Vec<ImportedFormObservation>,
) -> Result<(), FormImportError> {
    for node in &mut flow.children {
        if let Node::Table(table) = node {
            for cell in &mut table.cells {
                replace_forms(&mut cell.body, forms, output)?;
            }
        }
        let Some(observed) = forms.remove(&node.common().node_id) else {
            continue;
        };
        let Node::EmbeddedObject(object) = node else {
            return Err(FormImportError::Binding);
        };
        if object.common.source_anchor.as_ref() != Some(&observed.source_anchor) {
            return Err(FormImportError::Binding);
        }
        let mut properties = object.properties.clone();
        properties.insert(
            "semantic_qualification",
            PropertyValue::Text(FORM_OBSERVATION_SCOPE.into()),
        );
        properties.insert(
            "source_resource_id",
            PropertyValue::Id(object.resource_id.clone()),
        );
        properties.insert(
            "observed_form_json",
            PropertyValue::Text(
                serde_json::to_string(&observed).map_err(|_| FormImportError::Graph)?,
            ),
        );
        *node = Node::FormControl(FormControlNode {
            common: object.common.clone(),
            control_kind: capability(observed.tag).into(),
            properties,
        });
        output.push(observed);
    }
    Ok(())
}

fn native_tag(name: &str) -> Option<NativeFormTag> {
    match name {
        "edit" => Some(NativeFormTag::Edit),
        "checkBtn" => Some(NativeFormTag::CheckBtn),
        "radioBtn" => Some(NativeFormTag::RadioBtn),
        "comboBox" => Some(NativeFormTag::ComboBox),
        "listBox" => Some(NativeFormTag::ListBox),
        _ => None,
    }
}
fn kind_index(tag: NativeFormTag) -> usize {
    match tag {
        NativeFormTag::Edit => 0,
        NativeFormTag::CheckBtn => 1,
        NativeFormTag::RadioBtn => 2,
        NativeFormTag::ComboBox => 3,
        NativeFormTag::ListBox => 4,
    }
}
fn capability(tag: NativeFormTag) -> &'static str {
    match tag {
        NativeFormTag::Edit => "ref.form_text",
        NativeFormTag::CheckBtn => "ref.form_checkbox",
        NativeFormTag::RadioBtn => "ref.form_radio",
        NativeFormTag::ComboBox => "ref.form_combo",
        NativeFormTag::ListBox => "ref.form_list",
    }
}

#[derive(Debug, Error)]
pub enum FormImportError {
    #[error("form import source rejected")]
    Source(#[from] SourceImportError),
    #[error("form import body rejected")]
    Body(#[from] StructureImportError),
    #[error("form import native package rejected: {0}")]
    Native(#[from] NativeFormPackageError),
    #[error("form import source binding rejected")]
    Binding,
    #[error("form import contains forms outside the qualified body mapping")]
    Unrepresented,
    #[error("form import graph or budget rejected")]
    Graph,
}
