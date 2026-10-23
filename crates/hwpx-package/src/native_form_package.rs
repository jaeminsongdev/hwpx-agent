//! Complete package-derived bindings for the observed native-form profile.
use std::{
    collections::{BTreeMap, BTreeSet},
    fmt,
    io::Cursor,
};

use domain_ir::{
    FORM_CONTROL_SCHEMA_VERSION, FormControlAnchor, FormControlBuilder, FormControlIdentity,
    FormControlLimits, FormControlPayload, FormControlPlan, FormControlState, FormDocumentState,
    FormDocumentStateDraft, FormNativeBinding, LogicalId, NativeFormTag,
};
use quick_xml::escape::unescape;
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{
    BoundedZipReader, CharacterStyleCatalogReader, CharacterStyleLimits, IdIndex, IdIndexError,
    IdIndexLimits, IdIssueKind, IdRuleProfile, NativeFormHwpxLimits, NativeFormHwpxMap,
    NativeFormHwpxReadback, NativeFormHwpxReader, NativeFormObservedIdentity, PackageGraph,
    PackageGraphLimits, PackageLimitConfig, PackageLimits, PartRole, PreservingXmlDocument,
    XmlAttributeToken, XmlElementToken,
};

pub const NATIVE_FORM_PACKAGE_BINDING_PROFILE_ID: &str =
    "hwpx-agent.native-form-package.complete-observed-bindings/v1";
const HH: &str = "http://www.hancom.co.kr/hwpml/2011/head";
const HP: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const HEADER: &str = "Contents/header.xml";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct NativeFormPackageLimits {
    archive_bytes: usize,
    entries: usize,
    part_bytes: usize,
    total_bytes: usize,
    sections: usize,
}
impl Default for NativeFormPackageLimits {
    fn default() -> Self {
        Self {
            archive_bytes: 32 * 1024 * 1024,
            entries: 256,
            part_bytes: 2 * 1024 * 1024,
            total_bytes: 16 * 1024 * 1024,
            sections: 64,
        }
    }
}
impl NativeFormPackageLimits {
    /// Creates finite bounds without clamping.
    /// # Errors
    /// Rejects zero, hard-ceiling and contradictory part/total bounds.
    pub fn new(
        archive_bytes: usize,
        entries: usize,
        part_bytes: usize,
        total_bytes: usize,
        sections: usize,
    ) -> Result<Self, NativeFormPackageError> {
        let value = Self {
            archive_bytes,
            entries,
            part_bytes,
            total_bytes,
            sections,
        };
        let max = Self::default();
        if archive_bytes == 0
            || archive_bytes > max.archive_bytes
            || entries == 0
            || entries > max.entries
            || part_bytes == 0
            || part_bytes > max.part_bytes
            || total_bytes == 0
            || total_bytes > max.total_bytes
            || part_bytes > total_bytes
            || sections == 0
            || sections > max.sections
        {
            return Err(NativeFormPackageError::Limit);
        }
        Ok(value)
    }
    fn zip(self) -> Result<PackageLimits, NativeFormPackageError> {
        PackageLimits::new(PackageLimitConfig {
            max_archive_bytes: u64::try_from(self.archive_bytes)
                .map_err(|_| NativeFormPackageError::Limit)?,
            max_entries: self.entries,
            max_entry_expanded_bytes: u64::try_from(self.part_bytes)
                .map_err(|_| NativeFormPackageError::Limit)?,
            max_total_expanded_bytes: u64::try_from(self.total_bytes)
                .map_err(|_| NativeFormPackageError::Limit)?,
            ..PackageLimitConfig::default()
        })
        .map_err(|_| NativeFormPackageError::Limit)
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct NativeFormPackageSectionMap {
    pub part: String,
    pub map: NativeFormHwpxMap,
}
impl fmt::Debug for NativeFormPackageSectionMap {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("NativeFormPackageSectionMap(<redacted>)")
    }
}
#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct NativeFormPackageMap {
    pub sections: Vec<NativeFormPackageSectionMap>,
}
impl fmt::Debug for NativeFormPackageMap {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("NativeFormPackageMap(<redacted>)")
    }
}

/// Explicit caller policy, not an assertion that defaults/validation were observed in XML.
#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct NativeFormPackagePolicy {
    pub identity: FormControlIdentity,
    pub payload: FormControlPayload,
}
impl fmt::Debug for NativeFormPackagePolicy {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("NativeFormPackagePolicy(<redacted>)")
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct NativeFormPackageBindings {
    style_catalog_sha256: String,
    border_catalog_sha256: String,
    resource_inventory_sha256: String,
    reference_inventory_sha256: String,
    document_protection_sha256: String,
    opaque_document_state_sha256: String,
    protection_signal_observed: bool,
}
impl fmt::Debug for NativeFormPackageBindings {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("NativeFormPackageBindings(<redacted>)")
    }
}
impl NativeFormPackageBindings {
    /// Returns a canonical private fingerprint record without document text.
    /// # Errors
    /// Fails if canonical serialization cannot be completed.
    pub fn canonical_json(&self) -> Result<Vec<u8>, NativeFormPackageError> {
        serde_json::to_vec(self).map_err(|_| NativeFormPackageError::Allocation)
    }
    #[must_use]
    pub const fn protection_signal_observed(&self) -> bool {
        self.protection_signal_observed
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
struct ObservedSection {
    part: String,
    observed: Option<NativeFormHwpxReadback>,
    non_form_sha256: String,
}
#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct NativeFormPackageReadback {
    package_sha256: String,
    map: NativeFormPackageMap,
    sections: Vec<ObservedSection>,
    bindings: NativeFormPackageBindings,
    non_form_content_sha256: String,
    document_flow_sha256: String,
    part_sha256: BTreeMap<String, String>,
    character_ids: BTreeSet<u32>,
    legacy_reference_state: String,
    verified_native_reference_overlay_issues: usize,
}
impl fmt::Debug for NativeFormPackageReadback {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("NativeFormPackageReadback")
            .field("sections", &self.sections.len())
            .finish_non_exhaustive()
    }
}
impl NativeFormPackageReadback {
    #[must_use]
    pub fn package_sha256(&self) -> &str {
        &self.package_sha256
    }
    #[must_use]
    pub fn document_flow_sha256(&self) -> &str {
        &self.document_flow_sha256
    }
    #[must_use]
    pub const fn bindings(&self) -> &NativeFormPackageBindings {
        &self.bindings
    }
    pub fn sections(&self) -> impl Iterator<Item = &NativeFormHwpxReadback> {
        self.sections.iter().filter_map(|n| n.observed.as_ref())
    }
    #[must_use]
    pub fn section_count(&self) -> usize {
        self.sections.len()
    }
    /// Original legacy verdict and count of independently verified native overlay issues.
    #[must_use]
    pub fn reference_overlay_status(&self) -> (&str, usize) {
        (
            &self.legacy_reference_state,
            self.verified_native_reference_overlay_issues,
        )
    }

    /// Reconstructs the complete global state from observations and explicit policies.
    /// # Errors
    /// Rejects missing/reordered policy bindings, invalid defaults/validation and native-value drift.
    pub fn bind_policies(
        &self,
        policies: &[NativeFormPackagePolicy],
        limits: FormControlLimits,
    ) -> Result<FormDocumentState, NativeFormPackageError> {
        let count: usize = self.sections().map(|n| n.controls().len()).sum();
        if policies.len() != count {
            return Err(NativeFormPackageError::Policy);
        }
        let mut controls = Vec::new();
        controls
            .try_reserve_exact(count)
            .map_err(|_| NativeFormPackageError::Allocation)?;
        let mut offset = 0;
        for section in &self.sections {
            let Some(section_observation) = &section.observed else {
                continue;
            };
            for observed in section_observation.controls() {
                let policy = policies.get(offset).ok_or(NativeFormPackageError::Policy)?;
                if policy.identity != observed.component_identity
                    || !native_policy_matches(observed, &policy.payload)?
                {
                    return Err(NativeFormPackageError::Policy);
                }
                controls.push(FormControlState {
                    identity: observed.component_identity.clone(),
                    anchor: FormControlAnchor {
                        paragraph_id: observed.anchor.paragraph_id.clone(),
                        run_ordinal: observed.anchor.run_ordinal,
                        inline_ordinal: observed.anchor.inline_ordinal,
                    },
                    native_binding: FormNativeBinding::Exact { tag: observed.tag },
                    common: observed.common.clone(),
                    payload: policy.payload.clone(),
                    shape_locked: observed.shape_locked,
                    shape_state_sha256: observed.geometry_sha256.clone(),
                    opaque_native_payload_sha256: observed.preserved_opaque_sha256.clone(),
                    opaque_properties: Vec::new(),
                });
                offset += 1;
            }
        }
        self.state(controls, &self.non_form_content_sha256, limits)
    }
    fn state(
        &self,
        controls: Vec<FormControlState>,
        non_form: &str,
        limits: FormControlLimits,
    ) -> Result<FormDocumentState, NativeFormPackageError> {
        let b = &self.bindings;
        FormDocumentState::from_draft(
            FormDocumentStateDraft {
                schema_version: FORM_CONTROL_SCHEMA_VERSION.into(),
                controls,
                non_form_content_sha256: non_form.into(),
                style_catalog_sha256: b.style_catalog_sha256.clone(),
                border_catalog_sha256: b.border_catalog_sha256.clone(),
                resource_inventory_sha256: b.resource_inventory_sha256.clone(),
                reference_inventory_sha256: b.reference_inventory_sha256.clone(),
                document_protection_sha256: b.document_protection_sha256.clone(),
                opaque_document_state_sha256: b.opaque_document_state_sha256.clone(),
            },
            limits,
        )
        .map_err(|_| NativeFormPackageError::Policy)
    }
    /// Compares every complete domain-state field to independently read package bindings.
    /// # Errors
    /// Rejects forged metadata/anchors/native payload/common state or changed policy bindings.
    pub fn verify_domain_state(
        &self,
        state: &FormDocumentState,
        policies: &[NativeFormPackagePolicy],
        limits: FormControlLimits,
    ) -> Result<(), NativeFormPackageError> {
        if self.bind_policies(policies, limits)? != *state {
            return Err(NativeFormPackageError::State);
        }
        Ok(())
    }
}

#[derive(Debug, Error)]
pub enum NativeFormPackageError {
    #[error("NATIVE_FORM_PACKAGE_LIMIT")]
    Limit,
    #[error("NATIVE_FORM_PACKAGE_ZIP_REJECTED")]
    Zip,
    #[error("NATIVE_FORM_PACKAGE_GRAPH_REJECTED")]
    Graph,
    #[error("NATIVE_FORM_PACKAGE_REFERENCE_REJECTED")]
    Reference,
    #[error("NATIVE_FORM_PACKAGE_XML_REJECTED")]
    Xml,
    #[error("NATIVE_FORM_PACKAGE_MAP_REJECTED")]
    Map,
    #[error("NATIVE_FORM_PACKAGE_CATALOG_REJECTED")]
    Catalog,
    #[error("NATIVE_FORM_PACKAGE_SECTION_REJECTED")]
    Section,
    #[error("NATIVE_FORM_PACKAGE_POLICY_REJECTED")]
    Policy,
    #[error("NATIVE_FORM_PACKAGE_STATE_REJECTED")]
    State,
    #[error("NATIVE_FORM_PACKAGE_SOURCE_OR_PLAN_DRIFT")]
    Binding,
    #[error("NATIVE_FORM_PACKAGE_PROTECTION_SIGNAL")]
    Protection,
    #[error("NATIVE_FORM_PACKAGE_ALLOCATION_FAILED")]
    Allocation,
}

#[derive(Debug)]
pub struct NativeFormPackageReader;
impl NativeFormPackageReader {
    /// Reads every integrity-checked part, all complete spine maps and actual metadata.
    /// # Errors
    /// Rejects malformed/open/unsafe packages, unknown references, catalogs, aliases and incomplete maps.
    pub fn read(
        package: &[u8],
        map: &NativeFormPackageMap,
        limits: NativeFormPackageLimits,
    ) -> Result<NativeFormPackageReadback, NativeFormPackageError> {
        if package.is_empty() || package.len() > limits.archive_bytes {
            return Err(NativeFormPackageError::Limit);
        }
        let mut reader = BoundedZipReader::open(Cursor::new(package), limits.zip()?)
            .map_err(|_| NativeFormPackageError::Zip)?;
        let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())
            .map_err(|_| NativeFormPackageError::Graph)?;
        let legacy_index = IdIndex::build(
            &mut reader,
            &graph,
            IdRuleProfile::hwpml_2011_shape_v6(),
            IdIndexLimits::default(),
        );
        // Native OPF may include the header as a non-linear spine item; it is
        // metadata, not a paragraph section. It remains fully parsed and bound.
        let body_spine: Vec<_> = graph
            .spine
            .iter()
            .filter(|p| p.as_str() != HEADER)
            .collect();
        if body_spine.len() > limits.sections
            || body_spine.len() != map.sections.len()
            || graph
                .spine
                .iter()
                .filter(|p| p.as_str() != HEADER)
                .map(crate::PackagePath::as_str)
                .ne(map.sections.iter().map(|n| n.part.as_str()))
        {
            return Err(NativeFormPackageError::Map);
        }
        global_map(map)?;
        let entries = reader.entries().to_vec();
        let mut parts = BTreeMap::new();
        for entry in entries {
            parts.insert(
                entry.path.as_str().to_owned(),
                reader
                    .read_entry(entry.index)
                    .map_err(|_| NativeFormPackageError::Zip)?,
            );
        }
        let header = parts.get(HEADER).ok_or(NativeFormPackageError::Catalog)?;
        let (character_ids, border_sha) = header_catalog(header, map.sections.len())?;
        let mut sections = Vec::new();
        sections
            .try_reserve_exact(map.sections.len())
            .map_err(|_| NativeFormPackageError::Allocation)?;
        let mut global_ids = BTreeSet::new();
        let mut global_instances = BTreeSet::new();
        let mut non_form = Sha256::new();
        let mut flow = Sha256::new();
        frame(&mut non_form, b"native-form-package-non-form/v1");
        frame(&mut flow, b"native-form-package-flow/v1");
        for section in &map.sections {
            let raw = parts
                .get(&section.part)
                .ok_or(NativeFormPackageError::Map)?;
            let observed = observe_section(
                raw,
                section,
                &character_ids,
                &mut global_ids,
                &mut global_instances,
            )?;
            for hash in [&mut non_form, &mut flow] {
                frame(hash, section.part.as_bytes());
                frame(hash, observed.non_form_sha256.as_bytes());
            }
            sections.push(observed);
        }
        let (reference, protection, opaque, resources, signal) = fingerprints(&parts, map, &graph)?;
        let (legacy_reference_state, verified_native_reference_overlay_issues) =
            reference_overlay(legacy_index, &parts, map)?;
        Ok(NativeFormPackageReadback {
            package_sha256: sha(package),
            map: map.clone(),
            sections,
            bindings: NativeFormPackageBindings {
                style_catalog_sha256: sha(header),
                border_catalog_sha256: border_sha,
                resource_inventory_sha256: resources,
                reference_inventory_sha256: reference,
                document_protection_sha256: protection,
                opaque_document_state_sha256: opaque,
                protection_signal_observed: signal,
            },
            non_form_content_sha256: hex(non_form.finalize()),
            document_flow_sha256: hex(flow.finalize()),
            part_sha256: parts.iter().map(|(p, b)| (p.clone(), sha(b))).collect(),
            character_ids,
            legacy_reference_state,
            verified_native_reference_overlay_issues,
        })
    }
    /// Rereads the complete real package with the sealed map.
    /// # Errors
    /// Rejects any package, part, map, metadata, section or observation drift.
    pub fn verify(
        package: &[u8],
        observed: &NativeFormPackageReadback,
        limits: NativeFormPackageLimits,
    ) -> Result<(), NativeFormPackageError> {
        if Self::read(package, &observed.map, limits)? != *observed {
            return Err(NativeFormPackageError::Binding);
        }
        Ok(())
    }
}

#[derive(Clone, Serialize)]
pub struct NativeFormPackagePlan {
    profile: &'static str,
    source: NativeFormPackageReadback,
    policies: Vec<NativeFormPackagePolicy>,
    domain: FormControlPlan,
}
impl fmt::Debug for NativeFormPackagePlan {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("NativeFormPackagePlan(<redacted>)")
    }
}
impl NativeFormPackagePlan {
    /// Validates and seals a full-document typed plan against independently read source bindings.
    /// # Errors
    /// Rejects package/state/flow/plan drift, invalid policies and observed protection/signature signals.
    pub fn bind(
        package: &[u8],
        observed: &NativeFormPackageReadback,
        policies: &[NativeFormPackagePolicy],
        plan: &FormControlPlan,
        domain_limits: FormControlLimits,
        limits: NativeFormPackageLimits,
    ) -> Result<Self, NativeFormPackageError> {
        NativeFormPackageReader::verify(package, observed, limits)?;
        if observed.bindings.protection_signal_observed {
            return Err(NativeFormPackageError::Protection);
        }
        observed.verify_domain_state(plan.source_state(), policies, domain_limits)?;
        let target = FormControlBuilder::build(
            plan,
            plan.source_state(),
            &observed.document_flow_sha256,
            domain_limits,
        )
        .map_err(|_| NativeFormPackageError::Binding)?;
        if target.state.controls().iter().any(|c| {
            !observed
                .character_ids
                .contains(&c.common.character.char_pr_id_ref)
                || c.common.border_type_id_ref != 0
        }) {
            return Err(NativeFormPackageError::Catalog);
        }
        Ok(Self {
            profile: NATIVE_FORM_PACKAGE_BINDING_PROFILE_ID,
            source: observed.clone(),
            policies: policies.to_vec(),
            domain: plan.clone(),
        })
    }
    /// Returns the canonical private plan fingerprint, never document text.
    /// # Errors
    /// Rejects serialization or a finite 16 MiB plan limit.
    pub fn plan_sha256(&self) -> Result<String, NativeFormPackageError> {
        let raw = serde_json::to_vec(self).map_err(|_| NativeFormPackageError::Allocation)?;
        if raw.len() > 16 * 1024 * 1024 {
            return Err(NativeFormPackageError::Limit);
        }
        Ok(sha(&raw))
    }
}

fn native_policy_matches(
    observed: &crate::NativeFormControlObservation,
    policy: &FormControlPayload,
) -> Result<bool, NativeFormPackageError> {
    let policy_fields: &[&str] = match (observed.tag, policy) {
        (NativeFormTag::Edit, FormControlPayload::Text { .. }) => &["default_value", "validation"],
        (NativeFormTag::CheckBtn, FormControlPayload::Checkbox { .. }) => {
            &["default_value", "must_be_checked"]
        }
        (NativeFormTag::RadioBtn, FormControlPayload::Radio { .. }) => {
            &["default_value", "group_required"]
        }
        (NativeFormTag::ComboBox, FormControlPayload::Combo { .. })
        | (NativeFormTag::ListBox, FormControlPayload::List { .. }) => {
            &["default_selected_value", "validation"]
        }
        _ => return Ok(false),
    };
    let native =
        serde_json::to_value(&observed.payload).map_err(|_| NativeFormPackageError::Allocation)?;
    let mut typed = serde_json::to_value(policy).map_err(|_| NativeFormPackageError::Allocation)?;
    let object = typed
        .as_object_mut()
        .ok_or(NativeFormPackageError::Policy)?;
    for key in policy_fields {
        object.remove(*key);
    }
    object.insert("kind".into(), native["kind"].clone());
    // Only non-observed, explicitly supplied policy fields are removed for this
    // native-value comparison. The complete policies and cross-section groups
    // are subsequently validated once by the full global domain-state builder.
    Ok(native == typed)
}
fn header_catalog(
    header: &[u8],
    count: usize,
) -> Result<(BTreeSet<u32>, String), NativeFormPackageError> {
    let doc = xml(header)?;
    let root = &doc.elements()[doc.root_element()];
    if root.name().namespace() != Some(HH)
        || root.name().local_name() != "head"
        || value(header, attr(root, "secCnt")?)? != count.to_string()
    {
        return Err(NativeFormPackageError::Catalog);
    }
    let catalog = CharacterStyleCatalogReader::read(header, CharacterStyleLimits::default())
        .map_err(|_| NativeFormPackageError::Catalog)?;
    let ids = catalog.styles.iter().map(|n| n.id).collect();
    let borders: Vec<_> = doc
        .elements()
        .iter()
        .filter(|n| named(n, HH, "borderFills"))
        .collect();
    if borders.len() != 1 {
        return Err(NativeFormPackageError::Catalog);
    }
    let span = borders[0]
        .outer_span()
        .ok_or(NativeFormPackageError::Catalog)?;
    Ok((ids, sha(&header[span.start()..span.end()])))
}
fn observe_section(
    raw: &[u8],
    section: &NativeFormPackageSectionMap,
    character_ids: &BTreeSet<u32>,
    native_ids: &mut BTreeSet<u32>,
    instances: &mut BTreeSet<u32>,
) -> Result<ObservedSection, NativeFormPackageError> {
    let observed = if section.map.component_controls.is_empty() {
        let doc = xml(raw)?;
        let root = &doc.elements()[doc.root_element()];
        let paragraphs = doc.elements().iter().filter(|n| named(n, HP, "p")).count();
        if root.name().namespace() != Some("http://www.hancom.co.kr/hwpml/2011/section")
            || root.name().local_name() != "sec"
            || paragraphs != section.map.paragraph_ids.len()
            || doc.elements().iter().any(|n| {
                ["edit", "checkBtn", "radioBtn", "comboBox", "listBox"]
                    .contains(&n.name().local_name())
            })
        {
            return Err(NativeFormPackageError::Section);
        }
        None
    } else {
        Some(
            NativeFormHwpxReader::read_section(raw, &section.map, NativeFormHwpxLimits::default())
                .map_err(|_| NativeFormPackageError::Section)?,
        )
    };
    if let Some(source) = &observed {
        for control in source.controls() {
            if !character_ids.contains(&control.common.character.char_pr_id_ref)
                || control.common.border_type_id_ref != 0
            {
                return Err(NativeFormPackageError::Catalog);
            }
            if let NativeFormObservedIdentity::Observed {
                object_id,
                instance_id,
                ..
            } = control.native_identity
                && (object_id.is_some_and(|n| !native_ids.insert(n))
                    || instance_id.is_some_and(|n| !instances.insert(n)))
            {
                return Err(NativeFormPackageError::Map);
            }
        }
    }
    let non_form_sha256 = if let Some(source) = &observed {
        source.non_form_content_sha256().to_owned()
    } else {
        let mut hash = Sha256::new();
        frame(&mut hash, raw);
        hex(hash.finalize())
    };
    Ok(ObservedSection {
        part: section.part.clone(),
        observed,
        non_form_sha256,
    })
}
fn reference_overlay(
    index: Result<IdIndex, IdIndexError>,
    parts: &BTreeMap<String, Vec<u8>>,
    map: &NativeFormPackageMap,
) -> Result<(String, usize), NativeFormPackageError> {
    match index {
        Ok(_) => Ok(("pass".into(), 0)),
        Err(IdIndexError::Validation(report)) => {
            if report.issues().is_empty() {
                return Err(NativeFormPackageError::Reference);
            }
            for issue in report.issues() {
                if issue.kind() != IdIssueKind::UnknownIdLikeAttribute {
                    return Err(NativeFormPackageError::Reference);
                }
                let location = issue.source();
                if !map
                    .sections
                    .iter()
                    .any(|s| s.part == location.part().as_str())
                {
                    return Err(NativeFormPackageError::Reference);
                }
                let raw = parts
                    .get(location.part().as_str())
                    .ok_or(NativeFormPackageError::Reference)?;
                let doc = xml(raw)?;
                let node = doc
                    .elements()
                    .get(location.element_index())
                    .ok_or(NativeFormPackageError::Reference)?;
                let a = node
                    .attributes()
                    .get(location.attribute_index())
                    .ok_or(NativeFormPackageError::Reference)?;
                if a.is_namespace_declaration() || a.name().namespace().is_some() {
                    return Err(NativeFormPackageError::Reference);
                }
                let root_attribute = named_form(node)
                    && ["borderTypeIDRef", "id", "instid", "instId"]
                        .contains(&a.name().local_name());
                let character_attribute = named(node, HP, "formCharPr")
                    && a.name().local_name() == "charPrIDRef"
                    && node
                        .parent()
                        .is_some_and(|p| named_form(&doc.elements()[p]));
                if !root_attribute && !character_attribute {
                    return Err(NativeFormPackageError::Reference);
                }
            }
            // These exact unknown declarations/references have already been validated by
            // the complete native reader, real character catalog and global native ID checks.
            // Do not claim the legacy profile itself passed or discard any other issue.
            Ok(("id_index_validation_failed".into(), report.issues().len()))
        }
        Err(_) => Err(NativeFormPackageError::Reference),
    }
}
fn global_map(map: &NativeFormPackageMap) -> Result<(), NativeFormPackageError> {
    let mut paragraphs = BTreeSet::<&LogicalId>::new();
    let mut controls = BTreeSet::new();
    let mut reservations = BTreeSet::new();
    for section in &map.sections {
        for p in &section.map.paragraph_ids {
            if !paragraphs.insert(p) {
                return Err(NativeFormPackageError::Map);
            }
        }
        for c in &section.map.component_controls {
            if !controls.insert(&c.logical_control_id) || !reservations.insert(c.native_object_id) {
                return Err(NativeFormPackageError::Map);
            }
        }
    }
    Ok(())
}
fn fingerprints(
    parts: &BTreeMap<String, Vec<u8>>,
    map: &NativeFormPackageMap,
    graph: &PackageGraph,
) -> Result<(String, String, String, String, bool), NativeFormPackageError> {
    let mut refs = Sha256::new();
    let mut protection = Sha256::new();
    let mut opaque = Sha256::new();
    let mut resources = Sha256::new();
    let mut signal = false;
    for (path, raw) in parts {
        let in_spine = map.sections.iter().any(|s| s.part == *path);
        if !in_spine {
            frame(&mut opaque, path.as_bytes());
            frame(&mut opaque, raw);
        }
        let lower = path.to_ascii_lowercase();
        let resource = lower.starts_with("bindata/")
            || (!in_spine
                && path != HEADER
                && path != "settings.xml"
                && path != "version.xml"
                && !lower.starts_with("preview/")
                && !lower.starts_with("meta-inf/")
                && graph
                    .parts
                    .iter()
                    .any(|p| p.path.as_str() == path && p.role == PartRole::ManifestListed));
        if resource {
            frame(&mut resources, path.as_bytes());
            frame(&mut resources, raw);
        }
        let sensitive_part = [
            "meta-inf/encryption.xml",
            "meta-inf/signatures.xml",
            "meta-inf/rights.xml",
        ]
        .contains(&lower.as_str());
        if sensitive_part || path.eq_ignore_ascii_case("settings.xml") || path == HEADER {
            frame(&mut protection, path.as_bytes());
            frame(&mut protection, raw);
            signal |= sensitive_part;
        }
        if std::path::Path::new(path).extension().is_some_and(|ext| {
            ["xml", "hpf", "rdf"]
                .iter()
                .any(|s| ext.eq_ignore_ascii_case(s))
        }) {
            let doc = xml(raw)?;
            for (index, node) in doc.elements().iter().enumerate() {
                let form = named_form(node) || form_ancestor(&doc, node);
                if form && !in_spine {
                    return Err(NativeFormPackageError::Map);
                }
                if (path == HEADER || path.eq_ignore_ascii_case("settings.xml") || sensitive_part)
                    && (sensitive(node.name().local_name())
                        || node.attributes().iter().any(|a| {
                            !a.is_namespace_declaration() && sensitive(a.name().local_name())
                        }))
                {
                    signal = true;
                }
                if form {
                    continue;
                }
                for a in node
                    .attributes()
                    .iter()
                    .filter(|a| !a.is_namespace_declaration())
                {
                    let name = a.name().local_name();
                    if name.ends_with("IDRef")
                        || ["id", "instid", "instId", "fieldid"].contains(&name)
                    {
                        frame(&mut refs, path.as_bytes());
                        frame(
                            &mut refs,
                            &u64::try_from(index)
                                .map_err(|_| NativeFormPackageError::Limit)?
                                .to_le_bytes(),
                        );
                        frame(&mut refs, node.name().namespace().unwrap_or("").as_bytes());
                        frame(&mut refs, node.name().local_name().as_bytes());
                        frame(&mut refs, a.name().namespace().unwrap_or("").as_bytes());
                        frame(&mut refs, name.as_bytes());
                        let span = a.value_span();
                        frame(&mut refs, &raw[span.start()..span.end()]);
                    }
                }
            }
        }
    }
    Ok((
        hex(refs.finalize()),
        hex(protection.finalize()),
        hex(opaque.finalize()),
        hex(resources.finalize()),
        signal,
    ))
}
pub(crate) fn sensitive(name: &str) -> bool {
    let n = name.to_ascii_lowercase();
    [
        "protect",
        "password",
        "encrypt",
        "signature",
        "rights",
        "readonly",
    ]
    .iter()
    .any(|p| n.contains(p))
}
fn form_ancestor(doc: &PreservingXmlDocument, node: &XmlElementToken) -> bool {
    let mut parent = node.parent();
    while let Some(index) = parent {
        let n = &doc.elements()[index];
        if named_form(n) {
            return true;
        }
        parent = n.parent();
    }
    false
}
fn named_form(n: &XmlElementToken) -> bool {
    named(n, HP, "edit")
        || named(n, HP, "checkBtn")
        || named(n, HP, "radioBtn")
        || named(n, HP, "comboBox")
        || named(n, HP, "listBox")
}
fn named(n: &XmlElementToken, namespace: &str, local: &str) -> bool {
    n.name().namespace() == Some(namespace) && n.name().local_name() == local
}
fn xml(raw: &[u8]) -> Result<PreservingXmlDocument, NativeFormPackageError> {
    PreservingXmlDocument::parse(raw).map_err(|_| NativeFormPackageError::Xml)
}
fn attr<'a>(
    node: &'a XmlElementToken,
    local: &str,
) -> Result<&'a XmlAttributeToken, NativeFormPackageError> {
    let a: Vec<_> = node
        .attributes()
        .iter()
        .filter(|n| !n.is_namespace_declaration() && n.name().local_name() == local)
        .collect();
    if a.len() != 1 || a[0].name().namespace().is_some() {
        return Err(NativeFormPackageError::Catalog);
    }
    Ok(a[0])
}
fn value(raw: &[u8], a: &XmlAttributeToken) -> Result<String, NativeFormPackageError> {
    let s = a.value_span();
    let text =
        std::str::from_utf8(&raw[s.start()..s.end()]).map_err(|_| NativeFormPackageError::Xml)?;
    Ok(unescape(text)
        .map_err(|_| NativeFormPackageError::Xml)?
        .into_owned())
}
fn frame(hash: &mut Sha256, raw: &[u8]) {
    hash.update((raw.len() as u64).to_le_bytes());
    hash.update(raw);
}
fn sha(raw: &[u8]) -> String {
    hex(Sha256::digest(raw))
}
fn hex(raw: impl AsRef<[u8]>) -> String {
    {
        const DIGITS: &[u8; 16] = b"0123456789abcdef";
        let mut out = String::with_capacity(raw.as_ref().len() * 2);
        for n in raw.as_ref() {
            out.push(char::from(DIGITS[usize::from(n >> 4)]));
            out.push(char::from(DIGITS[usize::from(n & 15)]));
        }
        out
    }
}
