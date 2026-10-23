//! Versioned managed-value output; original native v1 fingerprints remain unchanged.
use crate::{
    BoundedZipReader, Compression, EntryMetadata, NativeFormPackageLimits, NativeFormPackageMap,
    NativeFormPackagePolicy, NativeFormPackageReadback, NativeFormPackageReader,
    PackageLimitConfig, PackageLimits, PreservingXmlDocument,
};
use domain_ir::{
    FormButtonValue, FormControlLimits, FormControlPayload, FormDocumentState,
    FormDocumentStateDraft,
    form_input::{FormInputAccessPolicy, FormInputBuilder, FormInputPlan},
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use std::{
    fmt,
    io::{self, Cursor, Seek, SeekFrom, Write},
};
use thiserror::Error;
use zip::{CompressionMethod, ZipWriter, write::SimpleFileOptions};

pub const NATIVE_FORM_VALUE_PROFILE: &str = "hwpx-agent.native-form-package.managed-values/v2";
const HP: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const ARCHIVE: usize = 32 * 1024 * 1024;
const PART: usize = 2 * 1024 * 1024;
const TOTAL: usize = 16 * 1024 * 1024;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct NativeFormValueLimits {
    archive: usize,
    part: usize,
    total: usize,
}
impl Default for NativeFormValueLimits {
    fn default() -> Self {
        Self {
            archive: ARCHIVE,
            part: PART,
            total: TOTAL,
        }
    }
}
impl NativeFormValueLimits {
    /// Creates finite, non-clamping complete-package output bounds.
    /// # Errors
    /// Rejects zero, contradictory and hard-ceiling-exceeding values.
    pub fn new(archive: usize, part: usize, total: usize) -> Result<Self, NativeFormValueError> {
        if archive == 0
            || archive > ARCHIVE
            || part == 0
            || part > PART
            || total == 0
            || total > TOTAL
            || part > total
        {
            return Err(NativeFormValueError::Limit);
        }
        Ok(Self {
            archive,
            part,
            total,
        })
    }
}
#[derive(Debug, Error, Eq, PartialEq)]
pub enum NativeFormValueError {
    #[error("NATIVE_FORM_VALUE_LIMIT")]
    Limit,
    #[error("NATIVE_FORM_VALUE_BINDING_REJECTED")]
    Binding,
    #[error("NATIVE_FORM_VALUE_CALLER_ACCESS_OR_PROTECTION_REJECTED")]
    Access,
    #[error("NATIVE_FORM_VALUE_UNSUPPORTED_PROFILE")]
    Unsupported,
    #[error("NATIVE_FORM_VALUE_XML_REJECTED")]
    Xml,
    #[error("NATIVE_FORM_VALUE_ZIP_REJECTED")]
    Zip,
    #[error("NATIVE_FORM_VALUE_PRESERVATION_REJECTED")]
    Preservation,
    #[error("NATIVE_FORM_VALUE_TARGET_REJECTED")]
    Target,
    #[error("NATIVE_FORM_VALUE_ALLOCATION_FAILED")]
    Allocation,
}

/// Explicit v2 readback. It is never substituted for a v1 binding in place.
#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct NativeFormValueReadback {
    profile: &'static str,
    native_v1: NativeFormPackageReadback,
    v1_state_sha256: String,
    state: FormDocumentState,
}
impl fmt::Debug for NativeFormValueReadback {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("NativeFormValueReadback(<redacted>)")
    }
}
impl NativeFormValueReadback {
    #[must_use]
    pub const fn state(&self) -> &FormDocumentState {
        &self.state
    }
    #[must_use]
    pub const fn native_v1(&self) -> &NativeFormPackageReadback {
        &self.native_v1
    }
    #[must_use]
    pub fn v1_state_sha256(&self) -> &str {
        &self.v1_state_sha256
    }
}
#[derive(Debug)]
pub struct NativeFormValueReader;
impl NativeFormValueReader {
    /// Rereads every actual package binding, then declares a separate managed-value profile.
    /// # Errors
    /// Rejects invalid packages/maps/policies, unsupported values and ambiguous spans.
    pub fn read(
        source: &[u8],
        map: &NativeFormPackageMap,
        policies: &[NativeFormPackagePolicy],
        domain: FormControlLimits,
        package: NativeFormPackageLimits,
    ) -> Result<NativeFormValueReadback, NativeFormValueError> {
        let native = NativeFormPackageReader::read(source, map, package)
            .map_err(|_| NativeFormValueError::Binding)?;
        let v1 = native
            .bind_policies(policies, domain)
            .map_err(|_| NativeFormValueError::Binding)?;
        let mut draft: FormDocumentStateDraft = serde_json::from_slice(
            &v1.canonical_json(domain)
                .map_err(|_| NativeFormValueError::Limit)?,
        )
        .map_err(|_| NativeFormValueError::Binding)?;
        let parts = load(source)?;
        let mut ordinal = 0;
        for section in &map.sections {
            let part = parts
                .iter()
                .find(|part| part.metadata.path.as_str() == section.part)
                .ok_or(NativeFormValueError::Binding)?;
            let slots = slots(&part.bytes)?;
            if slots.len() != section.map.component_controls.len() {
                return Err(NativeFormValueError::Binding);
            }
            for (slot, identity) in slots.iter().zip(&section.map.component_controls) {
                let control = draft
                    .controls
                    .get_mut(ordinal)
                    .ok_or(NativeFormValueError::Binding)?;
                if &control.identity != identity || !slot.matches(&control.payload) {
                    return Err(NativeFormValueError::Unsupported);
                }
                // Only this explicitly versioned field changes. All other complete
                // state and the original native v1 readback remain independently bound.
                control.opaque_native_payload_sha256 = preserved_control(&part.bytes, slot)?;
                ordinal += 1;
            }
        }
        if ordinal != draft.controls.len() {
            return Err(NativeFormValueError::Binding);
        }
        let state = FormDocumentState::from_draft(draft, domain)
            .map_err(|_| NativeFormValueError::Binding)?;
        Ok(NativeFormValueReadback {
            profile: NATIVE_FORM_VALUE_PROFILE,
            v1_state_sha256: v1
                .canonical_sha256(domain)
                .map_err(|_| NativeFormValueError::Binding)?,
            native_v1: native,
            state,
        })
    }
}

#[derive(Clone, Serialize)]
pub struct NativeFormValuePlan {
    profile: &'static str,
    map: NativeFormPackageMap,
    policies: Vec<NativeFormPackagePolicy>,
    source: NativeFormValueReadback,
    domain: FormInputPlan,
    access: FormInputAccessPolicy,
    seal: String,
}
impl fmt::Debug for NativeFormValuePlan {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("NativeFormValuePlan(<redacted>)")
    }
}
impl NativeFormValuePlan {
    /// Seals a real complete-package source and the actual v2 typed input transition.
    /// # Errors
    /// Rejects stale/v1-domain bindings, protection, access revocation or invalid plans.
    pub fn bind(
        source: &[u8],
        map: &NativeFormPackageMap,
        policies: &[NativeFormPackagePolicy],
        plan: &FormInputPlan,
        access: &FormInputAccessPolicy,
        domain: FormControlLimits,
        package: NativeFormPackageLimits,
    ) -> Result<Self, NativeFormValueError> {
        let observed = NativeFormValueReader::read(source, map, policies, domain, package)?;
        if observed.native_v1.bindings().protection_signal_observed() {
            return Err(NativeFormValueError::Access);
        }
        FormInputBuilder::build(
            plan,
            observed.state(),
            observed.native_v1.document_flow_sha256(),
            access,
            domain,
        )
        .map_err(|_| NativeFormValueError::Binding)?;
        let mut value = Self {
            profile: NATIVE_FORM_VALUE_PROFILE,
            map: map.clone(),
            policies: policies.to_vec(),
            source: observed,
            domain: plan.clone(),
            access: access.clone(),
            seal: String::new(),
        };
        value.seal = value.digest(domain)?;
        Ok(value)
    }
    fn digest(&self, limits: FormControlLimits) -> Result<String, NativeFormValueError> {
        let mut bytes = BoundedBuffer {
            bytes: Vec::new(),
            position: 0,
            limit: limits.config().output_bytes,
        };
        serde_json::to_writer(
            &mut bytes,
            &(
                self.profile,
                &self.map,
                &self.policies,
                &self.source,
                &self.domain,
                &self.access,
            ),
        )
        .map_err(|_| NativeFormValueError::Limit)?;
        Ok(hash(&bytes.bytes))
    }
}
#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum NativeFormValueQualification {
    CompletePackageComponentOnlyNativeExecutionProtectionDateExternalValidationAndRoutingUnqualified,
}
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct NativeFormValueReceipt {
    pub profile: &'static str,
    pub source_package_sha256: String,
    pub output_package_sha256: String,
    pub source_v1_state_sha256: String,
    pub source_v2_state_sha256: String,
    pub target_v2_state_sha256: String,
    pub document_flow_sha256: String,
    pub typed_input_plan_sha256: String,
    pub package_plan_sha256: String,
    pub changed_controls: usize,
    pub changed_sections: usize,
    pub managed_value_edits: usize,
    pub preservation_policy: &'static str,
    pub zip_header_policy: &'static str,
    pub qualification: NativeFormValueQualification,
}
pub struct NativeFormValueOutput {
    bytes: Vec<u8>,
    receipt: NativeFormValueReceipt,
}
impl fmt::Debug for NativeFormValueOutput {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("NativeFormValueOutput(<redacted>)")
    }
}
impl NativeFormValueOutput {
    #[must_use]
    pub fn bytes(&self) -> &[u8] {
        &self.bytes
    }
    #[must_use]
    pub const fn receipt(&self) -> &NativeFormValueReceipt {
        &self.receipt
    }
}
#[derive(Debug)]
pub struct NativeFormValueLowerer;
impl NativeFormValueLowerer {
    /// Writes all supported native value changes atomically and independently rereads the complete package.
    /// # Errors
    /// Returns no partial artifact on drift, revoked caller access, unsupported dates or preservation errors.
    pub fn lower(
        source: &[u8],
        plan: &NativeFormValuePlan,
        access: &FormInputAccessPolicy,
        domain: FormControlLimits,
        package: NativeFormPackageLimits,
        limits: NativeFormValueLimits,
    ) -> Result<NativeFormValueOutput, NativeFormValueError> {
        let prepared = prepare(source, plan, access, domain, package, limits)?;
        let bytes = write_package(&prepared.parts, limits.archive)?;
        let receipt = verify(&bytes, plan, &prepared, domain, package, limits)?;
        Ok(NativeFormValueOutput { bytes, receipt })
    }
    /// Rereads an external complete output, without trusting receipt claims.
    /// # Errors
    /// Rejects every undeclared byte, catalog, map, target or ZIP inventory/compression change.
    pub fn verify_output(
        source: &[u8],
        plan: &NativeFormValuePlan,
        output: &[u8],
        access: &FormInputAccessPolicy,
        domain: FormControlLimits,
        package: NativeFormPackageLimits,
        limits: NativeFormValueLimits,
    ) -> Result<NativeFormValueReceipt, NativeFormValueError> {
        let prepared = prepare(source, plan, access, domain, package, limits)?;
        verify(output, plan, &prepared, domain, package, limits)
    }
}
struct Part {
    metadata: EntryMetadata,
    bytes: Vec<u8>,
}
struct Prepared {
    parts: Vec<Part>,
    target: FormDocumentState,
    sections: usize,
    edits: usize,
    controls: usize,
}

fn prepare(
    source: &[u8],
    plan: &NativeFormValuePlan,
    access: &FormInputAccessPolicy,
    domain: FormControlLimits,
    package: NativeFormPackageLimits,
    limits: NativeFormValueLimits,
) -> Result<Prepared, NativeFormValueError> {
    if plan.profile != NATIVE_FORM_VALUE_PROFILE || plan.digest(domain)? != plan.seal {
        return Err(NativeFormValueError::Binding);
    }
    if access != &plan.access || !access.input_allowed {
        return Err(NativeFormValueError::Access);
    }
    let fresh = NativeFormValueReader::read(source, &plan.map, &plan.policies, domain, package)?;
    if fresh != plan.source {
        return Err(NativeFormValueError::Binding);
    }
    if fresh.native_v1.bindings().protection_signal_observed() {
        return Err(NativeFormValueError::Access);
    }
    let target = FormInputBuilder::build(
        &plan.domain,
        fresh.state(),
        fresh.native_v1.document_flow_sha256(),
        access,
        domain,
    )
    .map_err(|_| NativeFormValueError::Binding)?
    .state;
    let mut parts = load(source)?;
    let mut sections = 0;
    let mut edit_count = 0;
    let mut ordinal = 0;
    let mut changed = 0;
    for section in &plan.map.sections {
        let part = parts
            .iter_mut()
            .find(|part| part.metadata.path.as_str() == section.part)
            .ok_or(NativeFormValueError::Binding)?;
        let value_slots = slots(&part.bytes)?;
        let mut edits = Vec::new();
        for slot in &value_slots {
            let before = fresh
                .state
                .controls()
                .get(ordinal)
                .ok_or(NativeFormValueError::Binding)?;
            let after = target
                .controls()
                .get(ordinal)
                .ok_or(NativeFormValueError::Binding)?;
            if before != after {
                let mut admitted = before.clone();
                admitted.payload = after.payload.clone();
                if admitted != *after {
                    return Err(NativeFormValueError::Unsupported);
                }
                edits.push(slot.edit(&part.bytes, &before.payload, &after.payload, limits.part)?);
                changed += 1;
            }
            ordinal += 1;
        }
        if !edits.is_empty() {
            edits.sort_by_key(|edit| edit.start);
            part.bytes = apply(&part.bytes, &edits, limits.part)?;
            sections += 1;
            edit_count += edits.len();
        }
    }
    if ordinal != target.controls().len() || changed == 0 {
        return Err(NativeFormValueError::Binding);
    }
    let total = parts.iter().try_fold(0usize, |sum, part| {
        if part.bytes.len() > limits.part {
            return Err(NativeFormValueError::Limit);
        }
        sum.checked_add(part.bytes.len())
            .ok_or(NativeFormValueError::Limit)
    })?;
    if total > limits.total {
        return Err(NativeFormValueError::Limit);
    }
    Ok(Prepared {
        parts,
        target,
        sections,
        edits: edit_count,
        controls: changed,
    })
}
fn verify(
    output: &[u8],
    plan: &NativeFormValuePlan,
    prepared: &Prepared,
    domain: FormControlLimits,
    package: NativeFormPackageLimits,
    limits: NativeFormValueLimits,
) -> Result<NativeFormValueReceipt, NativeFormValueError> {
    if output.is_empty() || output.len() > limits.archive {
        return Err(NativeFormValueError::Limit);
    }
    let actual = load(output)?;
    if actual.len() != prepared.parts.len() {
        return Err(NativeFormValueError::Preservation);
    }
    for (actual, expected) in actual.iter().zip(&prepared.parts) {
        if actual.metadata.path != expected.metadata.path
            || actual.metadata.compression != expected.metadata.compression
            || actual.bytes != expected.bytes
        {
            return Err(NativeFormValueError::Preservation);
        }
    }
    let policies: Vec<_> = prepared
        .target
        .controls()
        .iter()
        .map(|control| NativeFormPackagePolicy {
            identity: control.identity.clone(),
            payload: control.payload.clone(),
        })
        .collect();
    let fresh = NativeFormValueReader::read(output, &plan.map, &policies, domain, package)?;
    if fresh.state != prepared.target
        || fresh.native_v1.document_flow_sha256() != plan.source.native_v1.document_flow_sha256()
        || fresh.native_v1.bindings() != plan.source.native_v1.bindings()
    {
        return Err(NativeFormValueError::Target);
    }
    Ok(NativeFormValueReceipt {profile: NATIVE_FORM_VALUE_PROFILE,
        source_package_sha256: plan.source.native_v1.package_sha256().into(), output_package_sha256: hash(output),
        source_v1_state_sha256: plan.source.v1_state_sha256.clone(),
        source_v2_state_sha256: plan.source.state.canonical_sha256(domain).map_err(|_| NativeFormValueError::Target)?,
        target_v2_state_sha256: prepared.target.canonical_sha256(domain).map_err(|_| NativeFormValueError::Target)?,
        document_flow_sha256: fresh.native_v1.document_flow_sha256().into(), typed_input_plan_sha256: plan.domain.plan_sha256().into(),
        package_plan_sha256: plan.seal.clone(), changed_controls: prepared.controls, changed_sections: prepared.sections,
        managed_value_edits: prepared.edits, preservation_policy: "all_expanded_parts_and_non_value_gaps_byte_exact_order_compression_preserved_text_empty_expansion_declared",
        zip_header_policy: "rewritten_not_byte_exact", qualification: NativeFormValueQualification::CompletePackageComponentOnlyNativeExecutionProtectionDateExternalValidationAndRoutingUnqualified })
}
fn load(source: &[u8]) -> Result<Vec<Part>, NativeFormValueError> {
    let limits = PackageLimits::new(PackageLimitConfig {
        max_archive_bytes: ARCHIVE as u64,
        max_entries: 256,
        max_entry_expanded_bytes: PART as u64,
        max_total_expanded_bytes: TOTAL as u64,
        ..PackageLimitConfig::default()
    })
    .map_err(|_| NativeFormValueError::Limit)?;
    let mut reader = BoundedZipReader::open(Cursor::new(source), limits)
        .map_err(|_| NativeFormValueError::Zip)?;
    let metadata = reader.entries().to_vec();
    let mut parts = Vec::new();
    parts
        .try_reserve_exact(metadata.len())
        .map_err(|_| NativeFormValueError::Allocation)?;
    for metadata in metadata {
        let bytes = reader
            .read_entry(metadata.index)
            .map_err(|_| NativeFormValueError::Zip)?;
        parts.push(Part { metadata, bytes });
    }
    Ok(parts)
}
enum SlotKind {
    Text {
        empty: bool,
        content: Option<(usize, usize)>,
        head: Vec<u8>,
        name: String,
    },
    Button,
    Selection,
}
struct Slot {
    root_start: usize,
    root_end: usize,
    start: usize,
    end: usize,
    kind: SlotKind,
}
impl Slot {
    fn matches(&self, value: &FormControlPayload) -> bool {
        matches!(
            (&self.kind, value),
            (SlotKind::Text { .. }, FormControlPayload::Text { .. })
                | (
                    SlotKind::Button,
                    FormControlPayload::Checkbox { .. } | FormControlPayload::Radio { .. }
                )
                | (
                    SlotKind::Selection,
                    FormControlPayload::Combo { .. } | FormControlPayload::List { .. }
                )
        )
    }
    fn edit(
        &self,
        source: &[u8],
        before: &FormControlPayload,
        after: &FormControlPayload,
        limit: usize,
    ) -> Result<Edit, NativeFormValueError> {
        if !self.matches(before) || !self.matches(after) {
            return Err(NativeFormValueError::Unsupported);
        }
        let text = value_only(before, after)?;
        let replacement = escape(&text, limit)?;
        match &self.kind {
            SlotKind::Text {
                empty: true,
                head,
                name,
                ..
            } => {
                let mut bytes = Vec::new();
                let close = format!("</{name}>");
                let length = head
                    .len()
                    .checked_add(replacement.len())
                    .and_then(|n| n.checked_add(1 + close.len()))
                    .ok_or(NativeFormValueError::Limit)?;
                if length > limit {
                    return Err(NativeFormValueError::Limit);
                }
                bytes
                    .try_reserve_exact(length)
                    .map_err(|_| NativeFormValueError::Allocation)?;
                bytes.extend_from_slice(head);
                bytes.push(b'>');
                bytes.extend_from_slice(&replacement);
                bytes.extend_from_slice(close.as_bytes());
                Ok(Edit {
                    start: self.start,
                    end: self.end,
                    replacement: bytes,
                })
            }
            SlotKind::Text {
                content: Some((start, end)),
                ..
            } => Ok(Edit {
                start: *start,
                end: *end,
                replacement,
            }),
            SlotKind::Text { .. } => Err(NativeFormValueError::Xml),
            _ => {
                if source.get(self.start..self.end).is_none() {
                    return Err(NativeFormValueError::Xml);
                }
                Ok(Edit {
                    start: self.start,
                    end: self.end,
                    replacement,
                })
            }
        }
    }
}
fn value_only(
    before: &FormControlPayload,
    after: &FormControlPayload,
) -> Result<String, NativeFormValueError> {
    let text = match after {
        FormControlPayload::Text { value, .. } => value.clone(),
        FormControlPayload::Checkbox { value, .. } | FormControlPayload::Radio { value, .. } => {
            match value {
                FormButtonValue::Unchecked => "UNCHECKED",
                FormButtonValue::Checked => "CHECKED",
                FormButtonValue::Indeterminate => "INDETERMINATE",
            }
            .into()
        }
        FormControlPayload::Combo { selected_value, .. }
        | FormControlPayload::List { selected_value, .. } => {
            selected_value.clone().unwrap_or_default()
        }
        FormControlPayload::Date { .. } => return Err(NativeFormValueError::Unsupported),
    };
    // Prove value-only intent by replacing just the corresponding current value
    // in the old payload, then comparing the COMPLETE payload, not its kind.
    let mut admitted = before.clone();
    match (&mut admitted, after) {
        (FormControlPayload::Text { value, .. }, FormControlPayload::Text { value: new, .. }) => {
            value.clone_from(new);
        }
        (
            FormControlPayload::Checkbox { value, .. },
            FormControlPayload::Checkbox { value: new, .. },
        )
        | (FormControlPayload::Radio { value, .. }, FormControlPayload::Radio { value: new, .. }) =>
        {
            *value = *new;
        }
        (
            FormControlPayload::Combo { selected_value, .. },
            FormControlPayload::Combo {
                selected_value: new,
                ..
            },
        )
        | (
            FormControlPayload::List { selected_value, .. },
            FormControlPayload::List {
                selected_value: new,
                ..
            },
        ) => selected_value.clone_from(new),
        _ => return Err(NativeFormValueError::Unsupported),
    }
    if &admitted != after {
        return Err(NativeFormValueError::Unsupported);
    }
    Ok(text)
}
fn slots(source: &[u8]) -> Result<Vec<Slot>, NativeFormValueError> {
    let doc = PreservingXmlDocument::parse(source).map_err(|_| NativeFormValueError::Xml)?;
    let mut result = Vec::new();
    for (index, node) in doc.elements().iter().enumerate().filter(|(_, n)| {
        n.name().namespace() == Some(HP)
            && matches!(
                n.name().local_name(),
                "edit" | "checkBtn" | "radioBtn" | "comboBox" | "listBox"
            )
    }) {
        let root = node.outer_span().ok_or(NativeFormValueError::Xml)?;
        let (start, end, kind) = if node.name().local_name() == "edit" {
            let children: Vec<_> = doc
                .elements()
                .iter()
                .filter(|n| {
                    n.parent() == Some(index)
                        && n.name().namespace() == Some(HP)
                        && n.name().local_name() == "text"
                })
                .collect();
            if children.len() != 1
                || children[0].name().namespace() != Some(HP)
                || children[0].first_child().is_some()
            {
                return Err(NativeFormValueError::Unsupported);
            }
            let child = children[0];
            let outer = child.outer_span().ok_or(NativeFormValueError::Xml)?;
            let tag = child.start_tag_span();
            let raw = source
                .get(tag.start()..tag.end())
                .ok_or(NativeFormValueError::Xml)?;
            let remove = if child.is_empty() { 2 } else { 1 };
            let head = raw
                .get(
                    ..raw
                        .len()
                        .checked_sub(remove)
                        .ok_or(NativeFormValueError::Xml)?,
                )
                .ok_or(NativeFormValueError::Xml)?
                .to_vec();
            (
                outer.start(),
                outer.end(),
                SlotKind::Text {
                    empty: child.is_empty(),
                    content: child.content_span().map(|s| (s.start(), s.end())),
                    head,
                    name: child.name().qualified_name().into(),
                },
            )
        } else {
            let name = if matches!(node.name().local_name(), "checkBtn" | "radioBtn") {
                "value"
            } else {
                "selectedValue"
            };
            let attrs: Vec<_> = node
                .attributes()
                .iter()
                .filter(|a| {
                    a.name().namespace().is_none()
                        && a.name().local_name() == name
                        && !a.is_namespace_declaration()
                })
                .collect();
            if attrs.len() != 1 {
                return Err(NativeFormValueError::Unsupported);
            }
            let span = attrs[0].value_span();
            (
                span.start(),
                span.end(),
                if name == "value" {
                    SlotKind::Button
                } else {
                    SlotKind::Selection
                },
            )
        };
        if start < root.start() || end > root.end() || start > end {
            return Err(NativeFormValueError::Xml);
        }
        result.push(Slot {
            root_start: root.start(),
            root_end: root.end(),
            start,
            end,
            kind,
        });
    }
    Ok(result)
}
fn preserved_control(source: &[u8], slot: &Slot) -> Result<String, NativeFormValueError> {
    let mut digest = Sha256::new();
    for bytes in [
        NATIVE_FORM_VALUE_PROFILE.as_bytes(),
        source
            .get(slot.root_start..slot.start)
            .ok_or(NativeFormValueError::Xml)?,
        source
            .get(slot.end..slot.root_end)
            .ok_or(NativeFormValueError::Xml)?,
    ] {
        frame(&mut digest, bytes)?;
    }
    // Text attributes/prefix spelling are unknown-preserved, even when an empty
    // text container is expanded. Only its declared delimiter/value grammar normalizes.
    if let SlotKind::Text { head, name, .. } = &slot.kind {
        frame(&mut digest, head)?;
        frame(&mut digest, name.as_bytes())?;
    }
    Ok(hex(digest.finalize()))
}
struct Edit {
    start: usize,
    end: usize,
    replacement: Vec<u8>,
}
fn apply(source: &[u8], edits: &[Edit], limit: usize) -> Result<Vec<u8>, NativeFormValueError> {
    let mut length = source.len();
    let mut cursor = 0;
    for edit in edits {
        if edit.start < cursor || edit.start > edit.end || edit.end > source.len() {
            return Err(NativeFormValueError::Preservation);
        }
        length = length
            .checked_sub(edit.end - edit.start)
            .and_then(|n| n.checked_add(edit.replacement.len()))
            .ok_or(NativeFormValueError::Limit)?;
        cursor = edit.end;
    }
    if length > limit {
        return Err(NativeFormValueError::Limit);
    }
    let mut output = Vec::new();
    output
        .try_reserve_exact(length)
        .map_err(|_| NativeFormValueError::Allocation)?;
    cursor = 0;
    for edit in edits {
        output.extend_from_slice(&source[cursor..edit.start]);
        output.extend_from_slice(&edit.replacement);
        cursor = edit.end;
    }
    output.extend_from_slice(&source[cursor..]);
    cursor = 0;
    let mut offset = 0;
    for edit in edits {
        let gap = edit.start - cursor;
        if output.get(offset..offset + gap) != source.get(cursor..edit.start) {
            return Err(NativeFormValueError::Preservation);
        }
        offset += gap;
        if output.get(offset..offset + edit.replacement.len()) != Some(edit.replacement.as_slice())
        {
            return Err(NativeFormValueError::Preservation);
        }
        offset += edit.replacement.len();
        cursor = edit.end;
    }
    if output.len() != length || output.get(offset..) != source.get(cursor..) {
        return Err(NativeFormValueError::Preservation);
    }
    Ok(output)
}
fn escape(value: &str, limit: usize) -> Result<Vec<u8>, NativeFormValueError> {
    let length = value.chars().try_fold(0usize, |sum, c| {
        let mut utf8 = [0; 4];
        sum.checked_add(escaped(c, &mut utf8)?.len())
            .filter(|n| *n <= limit && *n <= PART)
            .ok_or(NativeFormValueError::Limit)
    })?;
    let mut bytes = Vec::new();
    bytes
        .try_reserve_exact(length)
        .map_err(|_| NativeFormValueError::Allocation)?;
    for c in value.chars() {
        let mut utf8 = [0; 4];
        bytes.extend_from_slice(escaped(c, &mut utf8)?.as_bytes());
    }
    Ok(bytes)
}
fn escaped(c: char, utf8: &mut [u8; 4]) -> Result<&str, NativeFormValueError> {
    Ok(match c {
        '&' => "&amp;",
        '<' => "&lt;",
        '>' => "&gt;",
        '\'' => "&apos;",
        '"' => "&quot;",
        '\n' => "&#10;",
        '\r' => "&#13;",
        '\t' => "&#9;",
        c if c < ' ' || matches!(c, '\u{fffe}' | '\u{ffff}') => {
            return Err(NativeFormValueError::Unsupported);
        }
        c => c.encode_utf8(utf8),
    })
}
fn write_package(parts: &[Part], limit: usize) -> Result<Vec<u8>, NativeFormValueError> {
    let mut writer = ZipWriter::new(BoundedBuffer {
        bytes: Vec::new(),
        position: 0,
        limit,
    });
    for part in parts {
        let method = match part.metadata.compression {
            Compression::Stored => CompressionMethod::Stored,
            Compression::Deflated => CompressionMethod::Deflated,
        };
        writer
            .start_file(
                part.metadata.path.as_str(),
                SimpleFileOptions::default().compression_method(method),
            )
            .map_err(zip_error)?;
        writer
            .write_all(&part.bytes)
            .map_err(|error| io_error(&error))?;
    }
    Ok(writer.finish().map_err(zip_error)?.bytes)
}
struct BoundedBuffer {
    bytes: Vec<u8>,
    position: usize,
    limit: usize,
}
impl Write for BoundedBuffer {
    fn write(&mut self, input: &[u8]) -> io::Result<usize> {
        let end = self
            .position
            .checked_add(input.len())
            .filter(|n| *n <= self.limit)
            .ok_or_else(|| {
                io::Error::new(io::ErrorKind::FileTooLarge, "native value output limit")
            })?;
        if end > self.bytes.len() {
            self.bytes
                .try_reserve_exact(end - self.bytes.len())
                .map_err(|_| {
                    io::Error::new(io::ErrorKind::OutOfMemory, "native value allocation")
                })?;
            self.bytes.resize(end, 0);
        }
        self.bytes[self.position..end].copy_from_slice(input);
        self.position = end;
        Ok(input.len())
    }
    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}
impl Seek for BoundedBuffer {
    fn seek(&mut self, to: SeekFrom) -> io::Result<u64> {
        let base = match to {
            SeekFrom::Start(n) => Some(n),
            SeekFrom::Current(n) => offset(self.position as u64, n),
            SeekFrom::End(n) => offset(self.bytes.len() as u64, n),
        };
        let next = base
            .and_then(|n| usize::try_from(n).ok())
            .filter(|n| *n <= self.limit)
            .ok_or_else(|| {
                io::Error::new(io::ErrorKind::FileTooLarge, "native value seek limit")
            })?;
        self.position = next;
        Ok(next as u64)
    }
}
fn offset(base: u64, n: i64) -> Option<u64> {
    if n >= 0 {
        base.checked_add(n.unsigned_abs())
    } else {
        base.checked_sub(n.unsigned_abs())
    }
}
fn io_error(error: &io::Error) -> NativeFormValueError {
    match error.kind() {
        io::ErrorKind::FileTooLarge => NativeFormValueError::Limit,
        io::ErrorKind::OutOfMemory => NativeFormValueError::Allocation,
        _ => NativeFormValueError::Zip,
    }
}
fn zip_error(error: zip::result::ZipError) -> NativeFormValueError {
    if let zip::result::ZipError::Io(error) = error {
        io_error(&error)
    } else {
        NativeFormValueError::Zip
    }
}
fn frame(digest: &mut Sha256, raw: &[u8]) -> Result<(), NativeFormValueError> {
    let length = u64::try_from(raw.len()).map_err(|_| NativeFormValueError::Limit)?;
    digest.update(length.to_le_bytes());
    digest.update(raw);
    Ok(())
}
fn hash(raw: &[u8]) -> String {
    hex(Sha256::digest(raw))
}
fn hex(raw: impl AsRef<[u8]>) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let mut out = String::with_capacity(raw.as_ref().len() * 2);
    for &byte in raw.as_ref() {
        out.push(char::from(DIGITS[usize::from(byte >> 4)]));
        out.push(char::from(DIGITS[usize::from(byte & 15)]));
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{NativeFormHwpxMap, NativeFormObservedPayload, NativeFormPackageSectionMap};
    use domain_ir::{
        FormControlIdentity, FormTextValidation, LogicalId,
        form_input::{
            FORM_INPUT_SCHEMA_VERSION, FormInputAssignment, FormInputOperation, FormInputRequest,
            FormInputRequestDraft, FormInputValue,
        },
    };
    type AnyError = Box<dyn std::error::Error>;

    fn capture() -> Result<Vec<u8>, AnyError> {
        let path = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../..").join("implementation/p08/evidence/private/p08-20-object-target-20260915-18/obj-012-form-insert.hancom-2020-readback.hwpx");
        for ancestor in path.ancestors() {
            let metadata = std::fs::symlink_metadata(ancestor)?;
            #[cfg(windows)]
            {
                use std::os::windows::fs::MetadataExt as _;
                if metadata.file_attributes() & 0x400 != 0 {
                    return Err("capture reparse rejected".into());
                }
            }
            if metadata.file_type().is_symlink() {
                return Err("capture link rejected".into());
            }
        }
        if std::fs::metadata(&path)?.len() != 14556 {
            return Err("capture size rejected".into());
        }
        let source = std::fs::read(path)?;
        if source.len() != 14556
            || hash(&source) != "02e9b5acef95877b6934a6a3131069402138cc2190eff2e68db79aa7e9ac9ce7"
        {
            return Err("capture hash rejected".into());
        }
        Ok(source)
    }
    fn policy(
        control: &crate::NativeFormControlObservation,
    ) -> Result<Vec<NativeFormPackagePolicy>, AnyError> {
        let NativeFormObservedPayload::Text {
            value,
            multi_line,
            password_character,
            native_max_length,
            scroll_bars,
            tab_key_behavior,
            number_only,
            read_only,
            alignment,
        } = &control.payload
        else {
            return Err("kind".into());
        };
        Ok(vec![NativeFormPackagePolicy {
            identity: control.component_identity.clone(),
            payload: FormControlPayload::Text {
                value: value.clone(),
                default_value: value.clone(),
                validation: FormTextValidation {
                    required: false,
                    minimum_characters: 0,
                    maximum_characters: None,
                    external_validator_sha256: None,
                },
                multi_line: *multi_line,
                password_character: password_character.clone(),
                native_max_length: *native_max_length,
                scroll_bars: *scroll_bars,
                tab_key_behavior: *tab_key_behavior,
                number_only: *number_only,
                read_only: *read_only,
                alignment: *alignment,
            },
        }])
    }
    fn real_plan() -> Result<
        (
            Vec<u8>,
            NativeFormValuePlan,
            FormInputAccessPolicy,
            FormControlLimits,
        ),
        AnyError,
    > {
        let source = capture()?;
        let domain = FormControlLimits::new(domain_ir::FormControlLimitConfig::default())?;
        let map = NativeFormPackageMap {
            sections: vec![NativeFormPackageSectionMap {
                part: "Contents/section0.xml".into(),
                map: NativeFormHwpxMap {
                    paragraph_ids: vec![
                        LogicalId::parse("private-p0")?,
                        LogicalId::parse("private-p1")?,
                    ],
                    component_controls: vec![FormControlIdentity {
                        logical_control_id: LogicalId::parse("private-component")?,
                        native_object_id: 90001,
                    }],
                },
            }],
        };
        let native =
            NativeFormPackageReader::read(&source, &map, NativeFormPackageLimits::default())?;
        let control = &native.sections().next().ok_or("section")?.controls()[0];
        let policies = policy(control)?;
        let observed = NativeFormValueReader::read(
            &source,
            &map,
            &policies,
            domain,
            NativeFormPackageLimits::default(),
        )?;
        let draft: FormDocumentStateDraft =
            serde_json::from_slice(&observed.state.canonical_json(domain)?)?;
        let access = FormInputAccessPolicy {
            document_protection_sha256: draft.document_protection_sha256,
            input_allowed: true,
        };
        let request = FormInputRequest::from_draft(
            FormInputRequestDraft {
                schema_version: FORM_INPUT_SCHEMA_VERSION.into(),
                request_id: LogicalId::parse("private-value-request")?,
                expected_source_state_sha256: observed.state.canonical_sha256(domain)?,
                expected_document_flow_sha256: observed.native_v1.document_flow_sha256().into(),
                access: access.clone(),
                operation: FormInputOperation::SetValues {
                    assignments: vec![FormInputAssignment {
                        target: policies[0].identity.clone(),
                        value: FormInputValue::Text {
                            value: "private-seal-test-value".into(),
                        },
                    }],
                },
            },
            &observed.state,
            observed.native_v1.document_flow_sha256(),
            domain,
        )?;
        let typed = FormInputBuilder::plan(
            &observed.state,
            &request,
            observed.native_v1.document_flow_sha256(),
            domain,
        )?;
        let plan = NativeFormValuePlan::bind(
            &source,
            &map,
            &policies,
            &typed,
            &access,
            domain,
            NativeFormPackageLimits::default(),
        )?;
        Ok((source, plan, access, domain))
    }
    #[test]
    fn private_seal_rejects_profile_map_policy_source_access_and_seal_mutations()
    -> Result<(), AnyError> {
        let (source, plan, access, domain) = real_plan()?;
        let original = source.clone();
        let baseline = NativeFormValueLowerer::lower(
            &source,
            &plan,
            &access,
            domain,
            NativeFormPackageLimits::default(),
            NativeFormValueLimits::default(),
        )?;
        for index in 0..7 {
            let mut altered = plan.clone();
            match index {
                0 => altered.profile = "not-v2",
                1 => altered.map.sections[0].map.component_controls[0].native_object_id += 1,
                2 => altered.policies[0].identity.native_object_id += 1,
                3 => altered.source.v1_state_sha256 = "0".repeat(64),
                4 => altered.source.profile = "not-v2",
                5 => altered.access.input_allowed = false,
                _ => altered.seal = "0".repeat(64),
            }
            assert!(matches!(
                NativeFormValueLowerer::lower(
                    &source,
                    &altered,
                    &access,
                    domain,
                    NativeFormPackageLimits::default(),
                    NativeFormValueLimits::default()
                ),
                Err(NativeFormValueError::Binding)
            ));
            assert_eq!(
                NativeFormValueLowerer::verify_output(
                    &source,
                    &altered,
                    baseline.bytes(),
                    &access,
                    domain,
                    NativeFormPackageLimits::default(),
                    NativeFormValueLimits::default()
                ),
                Err(NativeFormValueError::Binding)
            );
        }
        let mut forged = plan.clone();
        forged.source.v1_state_sha256 = "0".repeat(64);
        forged.seal = forged.digest(domain)?;
        assert!(matches!(
            NativeFormValueLowerer::lower(
                &source,
                &forged,
                &access,
                domain,
                NativeFormPackageLimits::default(),
                NativeFormValueLimits::default()
            ),
            Err(NativeFormValueError::Binding)
        ));
        assert_eq!(source, original);
        Ok(())
    }
    #[test]
    fn private_bounded_write_seek_and_escaped_value_reject_before_allocation()
    -> Result<(), AnyError> {
        let mut buffer = BoundedBuffer {
            bytes: Vec::new(),
            position: 0,
            limit: 8,
        };
        assert!(buffer.write_all(&[0; 9]).is_err());
        assert_eq!(buffer.bytes.capacity(), 0);
        assert!(buffer.seek(SeekFrom::Start(u64::MAX)).is_err());
        assert!(buffer.seek(SeekFrom::Current(-1)).is_err());
        assert_eq!(buffer.position, 0);
        buffer.write_all(b"ab")?;
        let capacity = buffer.bytes.capacity();
        assert!(buffer.write_all(b"1234567").is_err());
        assert_eq!(buffer.bytes, b"ab");
        assert_eq!(buffer.bytes.capacity(), capacity);
        buffer.seek(SeekFrom::Start(7))?;
        buffer.write_all(b"z")?;
        assert_eq!(buffer.bytes, b"ab\0\0\0\0\0z");
        assert!(buffer.seek(SeekFrom::End(1)).is_err());
        assert!(buffer.write_all(b"x").is_err());
        assert_eq!(escape("&&", 9), Err(NativeFormValueError::Limit));
        assert_eq!(escape("&&", 10)?, b"&amp;&amp;");
        assert_eq!(escape("🚀", 3), Err(NativeFormValueError::Limit));
        assert_eq!(escape("🚀", 4)?, "🚀".as_bytes());
        assert_eq!(escape("\0", 10), Err(NativeFormValueError::Unsupported));
        Ok(())
    }
    #[test]
    fn private_gap_patch_rejects_overlap_invalid_ranges_and_small_limit() -> Result<(), AnyError> {
        let one = Edit {
            start: 2,
            end: 4,
            replacement: b"XYZ".to_vec(),
        };
        assert_eq!(apply(b"abcdef", &[one], 7)?, b"abXYZef");
        let overlap = vec![
            Edit {
                start: 1,
                end: 3,
                replacement: vec![0],
            },
            Edit {
                start: 2,
                end: 4,
                replacement: vec![0],
            },
        ];
        assert_eq!(
            apply(b"abcdef", &overlap, 8),
            Err(NativeFormValueError::Preservation)
        );
        for (start, end) in [(4, 3), (0, 7), (usize::MAX, usize::MAX)] {
            assert_eq!(
                apply(
                    b"abcdef",
                    &[Edit {
                        start,
                        end,
                        replacement: Vec::new()
                    }],
                    8
                ),
                Err(NativeFormValueError::Preservation)
            );
        }
        assert_eq!(
            apply(
                b"abcdef",
                &[Edit {
                    start: 0,
                    end: 0,
                    replacement: b"xx".to_vec()
                }],
                7
            ),
            Err(NativeFormValueError::Limit)
        );
        Ok(())
    }
}
