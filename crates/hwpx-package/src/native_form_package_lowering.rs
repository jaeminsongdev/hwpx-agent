//! Complete document form lowering, with an explicit native reference overlay.
//! Expanded part bytes/order/compression are preserved; ZIP headers are rewritten.
use std::{
    collections::BTreeMap,
    fmt,
    io::{self, Cursor, Seek, SeekFrom, Write},
};

use domain_ir::{
    FormCommonProperties, FormControlBuilder, FormControlIdentity, FormControlLimits,
    FormControlPlan, FormControlState, FormDocumentState,
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use thiserror::Error;
use zip::{CompressionMethod, ZipWriter, write::SimpleFileOptions};

use crate::native_form_package::{
    NativeFormPackageLimits, NativeFormPackageMap, NativeFormPackagePlan, NativeFormPackagePolicy,
    NativeFormPackageReadback, NativeFormPackageReader,
};
use crate::{
    BoundedZipReader, Compression, EntryMetadata, NativeFormHwpxLimits, NativeFormHwpxReadback,
    NativeFormHwpxReader, PackageLimits, PreservingXmlDocument, XmlElementToken,
};

pub const NATIVE_FORM_PACKAGE_OUTPUT_PROFILE_ID: &str =
    "hwpx-agent.native-form-package.global-attribute-output/v1";
const HP: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const MAX_ARCHIVE: usize = 32 * 1024 * 1024;
const MAX_PART: usize = 2 * 1024 * 1024;
const MAX_TOTAL: usize = 16 * 1024 * 1024;
const MAX_ATTRIBUTE: usize = 64 * 1024;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct NativeFormPackageOutputLimits {
    archive: usize,
    part: usize,
    total: usize,
}
impl Default for NativeFormPackageOutputLimits {
    fn default() -> Self {
        Self {
            archive: MAX_ARCHIVE,
            part: MAX_PART,
            total: MAX_TOTAL,
        }
    }
}
impl NativeFormPackageOutputLimits {
    /// Creates finite output bounds without clamping.
    /// # Errors
    /// Rejects zero, contradictory or hard-ceiling-exceeding bounds.
    pub fn new(
        archive_bytes: usize,
        part_bytes: usize,
        total_bytes: usize,
    ) -> Result<Self, NativeFormPackageOutputError> {
        if archive_bytes == 0
            || archive_bytes > MAX_ARCHIVE
            || part_bytes == 0
            || part_bytes > MAX_PART
            || total_bytes == 0
            || total_bytes > MAX_TOTAL
            || part_bytes > total_bytes
        {
            return Err(NativeFormPackageOutputError::Limit);
        }
        Ok(Self {
            archive: archive_bytes,
            part: part_bytes,
            total: total_bytes,
        })
    }
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum NativeFormPackageOutputError {
    #[error("NATIVE_FORM_OUTPUT_LIMIT")]
    Limit,
    #[error("NATIVE_FORM_OUTPUT_BINDING_REJECTED")]
    Binding,
    #[error("NATIVE_FORM_OUTPUT_TRANSITION_NOT_REPRESENTABLE")]
    NonRepresentable,
    #[error("NATIVE_FORM_OUTPUT_XML_REJECTED")]
    Xml,
    #[error("NATIVE_FORM_OUTPUT_ZIP_REJECTED")]
    Zip,
    #[error("NATIVE_FORM_OUTPUT_PRESERVATION_MISMATCH")]
    Preservation,
    #[error("NATIVE_FORM_OUTPUT_TARGET_MISMATCH")]
    Target,
    #[error("NATIVE_FORM_OUTPUT_ALLOCATION_FAILED")]
    Allocation,
}

/// Immutable complete map, observed source and full domain plan; no deserializer.
#[derive(Clone, Serialize)]
pub struct NativeFormPackageOutputPlan {
    profile: &'static str,
    map: NativeFormPackageMap,
    source: NativeFormPackageReadback,
    policies: Vec<NativeFormPackagePolicy>,
    domain: FormControlPlan,
    package_plan_sha256: String,
}
impl fmt::Debug for NativeFormPackageOutputPlan {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("NativeFormPackageOutputPlan(<redacted>)")
    }
}
impl NativeFormPackageOutputPlan {
    /// Binds the real complete source package and a supported global transition.
    /// # Errors
    /// Rejects stale/forged source, policies, flow, protection, catalogs or transitions.
    pub fn bind(
        source: &[u8],
        map: &NativeFormPackageMap,
        policies: &[NativeFormPackagePolicy],
        domain: &FormControlPlan,
        domain_limits: FormControlLimits,
        package_limits: NativeFormPackageLimits,
    ) -> Result<Self, NativeFormPackageOutputError> {
        let observed = NativeFormPackageReader::read(source, map, package_limits)
            .map_err(|_| NativeFormPackageOutputError::Binding)?;
        let seal = NativeFormPackagePlan::bind(
            source,
            &observed,
            policies,
            domain,
            domain_limits,
            package_limits,
        )
        .map_err(|_| NativeFormPackageOutputError::Binding)?;
        transition(domain)?;
        Ok(Self {
            profile: NATIVE_FORM_PACKAGE_OUTPUT_PROFILE_ID,
            map: map.clone(),
            source: observed,
            policies: policies.to_vec(),
            domain: domain.clone(),
            package_plan_sha256: seal
                .plan_sha256()
                .map_err(|_| NativeFormPackageOutputError::Binding)?,
        })
    }
}

/// Contains hashes/counts only. It is not a native execution or product Gate receipt.
#[derive(Clone, Eq, PartialEq, Serialize, Debug)]
pub struct NativeFormPackageOutputReceipt {
    pub profile: &'static str,
    pub source_package_sha256: String,
    pub output_package_sha256: String,
    pub target_state_sha256: String,
    pub document_flow_sha256: String,
    pub changed_sections: usize,
    pub changed_attributes: usize,
    pub non_section_parts_expanded_byte_exact: bool,
    pub outside_declared_edits_byte_exact: bool,
    pub entry_order_and_compression_preserved: bool,
    pub zip_header_policy: &'static str,
    pub legacy_reference_state: String,
    pub verified_native_reference_overlay_issues: usize,
}
pub struct NativeFormPackageOutput {
    bytes: Vec<u8>,
    receipt: NativeFormPackageOutputReceipt,
}
impl fmt::Debug for NativeFormPackageOutput {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("NativeFormPackageOutput")
            .field("bytes", &self.bytes.len())
            .finish_non_exhaustive()
    }
}
impl NativeFormPackageOutput {
    #[must_use]
    pub fn bytes(&self) -> &[u8] {
        &self.bytes
    }
    #[must_use]
    pub const fn receipt(&self) -> &NativeFormPackageOutputReceipt {
        &self.receipt
    }
}

#[derive(Debug)]
pub struct NativeFormPackageLowerer;
impl NativeFormPackageLowerer {
    /// Applies a complete global plan and independently reopens every output part.
    /// # Errors
    /// Returns no artifact on drift, unsupported transition, limit or preservation failure.
    pub fn lower(
        source: &[u8],
        plan: &NativeFormPackageOutputPlan,
        domain_limits: FormControlLimits,
        package_limits: NativeFormPackageLimits,
        output_limits: NativeFormPackageOutputLimits,
    ) -> Result<NativeFormPackageOutput, NativeFormPackageOutputError> {
        let prepared = prepare(source, plan, domain_limits, package_limits, output_limits)?;
        let bytes = write_package(&prepared.parts, output_limits.archive)?;
        let receipt = verify_prepared(
            &bytes,
            plan,
            &prepared,
            domain_limits,
            package_limits,
            output_limits,
        )?;
        Ok(NativeFormPackageOutput { bytes, receipt })
    }
    /// Independently rereads an external output; never trusts a claimed receipt.
    /// # Errors
    /// Rejects stale source/plan, substituted parts, catalogs, inventory, target or metadata.
    pub fn verify_output(
        source: &[u8],
        plan: &NativeFormPackageOutputPlan,
        output: &[u8],
        domain_limits: FormControlLimits,
        package_limits: NativeFormPackageLimits,
        output_limits: NativeFormPackageOutputLimits,
    ) -> Result<NativeFormPackageOutputReceipt, NativeFormPackageOutputError> {
        let prepared = prepare(source, plan, domain_limits, package_limits, output_limits)?;
        verify_prepared(
            output,
            plan,
            &prepared,
            domain_limits,
            package_limits,
            output_limits,
        )
    }
}

struct OutputPart {
    metadata: EntryMetadata,
    bytes: Vec<u8>,
}
struct Prepared {
    parts: Vec<OutputPart>,
    target: FormDocumentState,
    changed_sections: usize,
    changed_attributes: usize,
}

fn transition(plan: &FormControlPlan) -> Result<(), NativeFormPackageOutputError> {
    let capability = plan.capability_id();
    if !matches!(capability, "ref.form_properties" | "ref.form_tab_order")
        || plan.source_document_flow_sha256() != plan.target_document_flow_sha256()
        || plan.source_state().controls().len() != plan.target_state().controls().len()
    {
        return Err(NativeFormPackageOutputError::NonRepresentable);
    }
    let mut changed = 0;
    for (before, after) in plan
        .source_state()
        .controls()
        .iter()
        .zip(plan.target_state().controls())
    {
        if before == after {
            continue;
        }
        changed += 1;
        let mut admitted = before.clone();
        if capability == "ref.form_properties" {
            if before.common.command_sha256 != after.common.command_sha256 {
                return Err(NativeFormPackageOutputError::NonRepresentable);
            }
            admitted.common = after.common.clone();
        } else {
            admitted.common.tab_stop = after.common.tab_stop;
            admitted.common.tab_order = after.common.tab_order;
        }
        if &admitted != after {
            return Err(NativeFormPackageOutputError::NonRepresentable);
        }
    }
    if changed == 0 || (capability == "ref.form_properties" && changed != 1) {
        return Err(NativeFormPackageOutputError::NonRepresentable);
    }
    Ok(())
}

fn prepare(
    source: &[u8],
    plan: &NativeFormPackageOutputPlan,
    domain_limits: FormControlLimits,
    package_limits: NativeFormPackageLimits,
    output_limits: NativeFormPackageOutputLimits,
) -> Result<Prepared, NativeFormPackageOutputError> {
    if plan.profile != NATIVE_FORM_PACKAGE_OUTPUT_PROFILE_ID {
        return Err(NativeFormPackageOutputError::Binding);
    }
    let fresh = NativeFormPackageReader::read(source, &plan.map, package_limits)
        .map_err(|_| NativeFormPackageOutputError::Binding)?;
    let seal = NativeFormPackagePlan::bind(
        source,
        &fresh,
        &plan.policies,
        &plan.domain,
        domain_limits,
        package_limits,
    )
    .map_err(|_| NativeFormPackageOutputError::Binding)?;
    if fresh != plan.source
        || seal
            .plan_sha256()
            .map_err(|_| NativeFormPackageOutputError::Binding)?
            != plan.package_plan_sha256
    {
        return Err(NativeFormPackageOutputError::Binding);
    }
    transition(&plan.domain)?;
    let target = FormControlBuilder::build(
        &plan.domain,
        plan.domain.source_state(),
        fresh.document_flow_sha256(),
        domain_limits,
    )
    .map_err(|_| NativeFormPackageOutputError::Binding)?
    .state;
    let target_controls: BTreeMap<_, _> =
        target.controls().iter().map(|c| (&c.identity, c)).collect();
    let mut reader = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())
        .map_err(|_| NativeFormPackageOutputError::Zip)?;
    let entries = reader.entries().to_vec();
    let mut parts = Vec::new();
    parts
        .try_reserve_exact(entries.len())
        .map_err(|_| NativeFormPackageOutputError::Allocation)?;
    let mut changed_sections = 0;
    let mut changed_attributes = 0;
    let mut total = 0_usize;
    for metadata in entries {
        let mut bytes = reader
            .read_entry(metadata.index)
            .map_err(|_| NativeFormPackageOutputError::Zip)?;
        if let Some(section) = plan
            .map
            .sections
            .iter()
            .find(|n| n.part == metadata.path.as_str())
            && !section.map.component_controls.is_empty()
        {
            let observed = NativeFormHwpxReader::read_section(
                &bytes,
                &section.map,
                NativeFormHwpxLimits::default(),
            )
            .map_err(|_| NativeFormPackageOutputError::Binding)?;
            let edits = section_edits(&bytes, &observed, &target_controls)?;
            if !edits.is_empty() {
                bytes = apply(&bytes, &edits, output_limits.part)?;
                let reread = NativeFormHwpxReader::read_section(
                    &bytes,
                    &section.map,
                    NativeFormHwpxLimits::default(),
                )
                .map_err(|_| NativeFormPackageOutputError::Target)?;
                preserve_observations(&observed, &reread)?;
                changed_sections += 1;
                changed_attributes += edits.len();
            }
        }
        if bytes.len() > output_limits.part {
            return Err(NativeFormPackageOutputError::Limit);
        }
        total = total
            .checked_add(bytes.len())
            .ok_or(NativeFormPackageOutputError::Limit)?;
        if total > output_limits.total {
            return Err(NativeFormPackageOutputError::Limit);
        }
        parts.push(OutputPart { metadata, bytes });
    }
    if changed_attributes == 0 {
        return Err(NativeFormPackageOutputError::NonRepresentable);
    }
    Ok(Prepared {
        parts,
        target,
        changed_sections,
        changed_attributes,
    })
}

fn preserve_observations(
    before: &NativeFormHwpxReadback,
    after: &NativeFormHwpxReadback,
) -> Result<(), NativeFormPackageOutputError> {
    if before.non_form_content_sha256() != after.non_form_content_sha256()
        || before.controls().len() != after.controls().len()
    {
        return Err(NativeFormPackageOutputError::Preservation);
    }
    for (b, a) in before.controls().iter().zip(after.controls()) {
        if b.component_identity != a.component_identity
            || b.native_identity != a.native_identity
            || b.tag != a.tag
            || b.anchor != a.anchor
            || b.payload != a.payload
            || b.shape_locked != a.shape_locked
            || b.geometry_sha256 != a.geometry_sha256
            || b.preserved_opaque_sha256 != a.preserved_opaque_sha256
        {
            return Err(NativeFormPackageOutputError::Preservation);
        }
    }
    Ok(())
}

fn verify_prepared(
    output: &[u8],
    plan: &NativeFormPackageOutputPlan,
    prepared: &Prepared,
    domain_limits: FormControlLimits,
    package_limits: NativeFormPackageLimits,
    output_limits: NativeFormPackageOutputLimits,
) -> Result<NativeFormPackageOutputReceipt, NativeFormPackageOutputError> {
    if output.is_empty() || output.len() > output_limits.archive {
        return Err(NativeFormPackageOutputError::Limit);
    }
    let observed = NativeFormPackageReader::read(output, &plan.map, package_limits)
        .map_err(|_| NativeFormPackageOutputError::Target)?;
    observed
        .verify_domain_state(&prepared.target, &plan.policies, domain_limits)
        .map_err(|_| NativeFormPackageOutputError::Target)?;
    if observed.document_flow_sha256() != plan.source.document_flow_sha256()
        || observed.bindings() != plan.source.bindings()
    {
        return Err(NativeFormPackageOutputError::Preservation);
    }
    let mut reader = BoundedZipReader::open(Cursor::new(output), PackageLimits::default())
        .map_err(|_| NativeFormPackageOutputError::Zip)?;
    let actual_entries = reader.entries().to_vec();
    if actual_entries.len() != prepared.parts.len() {
        return Err(NativeFormPackageOutputError::Preservation);
    }
    for (entry, expected) in actual_entries.iter().zip(&prepared.parts) {
        if entry.path != expected.metadata.path
            || entry.compression != expected.metadata.compression
            || reader
                .read_entry(entry.index)
                .map_err(|_| NativeFormPackageOutputError::Zip)?
                != expected.bytes
        {
            return Err(NativeFormPackageOutputError::Preservation);
        }
    }
    for (before, after) in plan.source.sections().zip(observed.sections()) {
        preserve_observations(before, after)?;
    }
    let (legacy, overlay) = observed.reference_overlay_status();
    Ok(NativeFormPackageOutputReceipt {
        profile: NATIVE_FORM_PACKAGE_OUTPUT_PROFILE_ID,
        source_package_sha256: plan.source.package_sha256().into(),
        output_package_sha256: hex(&Sha256::digest(output)),
        target_state_sha256: prepared
            .target
            .canonical_sha256(domain_limits)
            .map_err(|_| NativeFormPackageOutputError::Target)?,
        document_flow_sha256: observed.document_flow_sha256().into(),
        changed_sections: prepared.changed_sections,
        changed_attributes: prepared.changed_attributes,
        non_section_parts_expanded_byte_exact: true,
        outside_declared_edits_byte_exact: true,
        entry_order_and_compression_preserved: true,
        zip_header_policy: "rewritten_not_byte_exact",
        legacy_reference_state: legacy.into(),
        verified_native_reference_overlay_issues: overlay,
    })
}

struct Edit {
    start: usize,
    end: usize,
    replacement: Vec<u8>,
}
fn named(node: &XmlElementToken, name: &str) -> bool {
    node.name().namespace() == Some(HP) && node.name().local_name() == name
}
fn native_root(node: &XmlElementToken) -> bool {
    node.name().namespace() == Some(HP)
        && matches!(
            node.name().local_name(),
            "edit" | "checkBtn" | "radioBtn" | "comboBox" | "listBox"
        )
}
fn common_values(c: &FormCommonProperties) -> [String; 11] {
    [
        c.name.clone(),
        format!("#{:06X}", c.fore_color_rgb),
        format!("#{:06X}", c.back_color_rgb),
        c.group_name.clone().unwrap_or_default(),
        bit(c.tab_stop),
        bit(c.editable),
        c.tab_order.map_or_else(|| "-1".into(), |n| n.to_string()),
        bit(c.enabled),
        c.border_type_id_ref.to_string(),
        bit(c.draw_frame),
        bit(c.printable),
    ]
}
fn bit(value: bool) -> String {
    if value { "1".into() } else { "0".into() }
}
fn section_edits(
    source: &[u8],
    observed: &NativeFormHwpxReadback,
    target: &BTreeMap<&FormControlIdentity, &FormControlState>,
) -> Result<Vec<Edit>, NativeFormPackageOutputError> {
    let document =
        PreservingXmlDocument::parse(source).map_err(|_| NativeFormPackageOutputError::Xml)?;
    let roots: Vec<_> = document
        .elements()
        .iter()
        .enumerate()
        .filter(|(_, n)| native_root(n))
        .collect();
    if roots.len() != observed.controls().len() {
        return Err(NativeFormPackageOutputError::Binding);
    }
    let names = [
        "name",
        "foreColor",
        "backColor",
        "groupName",
        "tabStop",
        "editable",
        "tabOrder",
        "enabled",
        "borderTypeIDRef",
        "drawFrame",
        "printable",
    ];
    let mut edits = Vec::new();
    for ((root_index, node), before) in roots.iter().zip(observed.controls()) {
        let after = target
            .get(&before.component_identity)
            .ok_or(NativeFormPackageOutputError::Binding)?;
        for ((name, old), new) in names
            .iter()
            .zip(common_values(&before.common))
            .zip(common_values(&after.common))
        {
            if old != new {
                push_edit(source, node, name, &new, &mut edits)?;
            }
        }
        let b = &before.common.character;
        let a = &after.common.character;
        if b != a {
            let mut children = document
                .elements()
                .iter()
                .filter(|n| n.parent() == Some(*root_index) && named(n, "formCharPr"));
            let child = children.next().ok_or(NativeFormPackageOutputError::Xml)?;
            if children.next().is_some() {
                return Err(NativeFormPackageOutputError::Xml);
            }
            let old = [
                b.char_pr_id_ref.to_string(),
                bit(b.follow_context),
                bit(b.auto_size),
                bit(b.word_wrap),
            ];
            let new = [
                a.char_pr_id_ref.to_string(),
                bit(a.follow_context),
                bit(a.auto_size),
                bit(a.word_wrap),
            ];
            for ((name, old), new) in ["charPrIDRef", "followContext", "autoSz", "wordWrap"]
                .iter()
                .zip(old)
                .zip(new)
            {
                if old != new {
                    push_edit(source, child, name, &new, &mut edits)?;
                }
            }
        }
    }
    edits.sort_by_key(|e| (e.start, e.end));
    Ok(edits)
}
fn escape(value: &str) -> Result<String, NativeFormPackageOutputError> {
    if value.len() > MAX_ATTRIBUTE {
        return Err(NativeFormPackageOutputError::Limit);
    }
    let mut output = String::new();
    output
        .try_reserve(value.len())
        .map_err(|_| NativeFormPackageOutputError::Allocation)?;
    for c in value.chars() {
        if !matches!(c as u32, 0x9 | 0xA | 0xD | 0x20..=0xD7FF | 0xE000..=0xFFFD | 0x0001_0000..=0x0010_FFFF)
        {
            return Err(NativeFormPackageOutputError::Xml);
        }
        let replacement = match c {
            '&' => "&amp;",
            '<' => "&lt;",
            '>' => "&gt;",
            '"' => "&quot;",
            '\'' => "&apos;",
            '\t' => "&#9;",
            '\n' => "&#10;",
            '\r' => "&#13;",
            _ => "",
        };
        output
            .try_reserve(if replacement.is_empty() {
                c.len_utf8()
            } else {
                replacement.len()
            })
            .map_err(|_| NativeFormPackageOutputError::Allocation)?;
        if replacement.is_empty() {
            output.push(c);
        } else {
            output.push_str(replacement);
        }
    }
    Ok(output)
}
fn push_edit(
    source: &[u8],
    node: &XmlElementToken,
    name: &str,
    value: &str,
    edits: &mut Vec<Edit>,
) -> Result<(), NativeFormPackageOutputError> {
    let escaped = escape(value)?;
    let attributes: Vec<_> = node
        .attributes()
        .iter()
        .filter(|a| a.name().local_name() == name && a.name().namespace().is_none())
        .collect();
    let edit = match attributes.as_slice() {
        [attribute] => {
            let span = attribute.value_span();
            Edit {
                start: span.start(),
                end: span.end(),
                replacement: escaped.into_bytes(),
            }
        }
        [] if name == "groupName" => {
            let end = node.start_tag_span().end();
            let start = end
                .checked_sub(if source.get(end.saturating_sub(2)..end) == Some(b"/>") {
                    2
                } else {
                    1
                })
                .ok_or(NativeFormPackageOutputError::Xml)?;
            Edit {
                start,
                end: start,
                replacement: format!(" groupName=\"{escaped}\"").into_bytes(),
            }
        }
        _ => return Err(NativeFormPackageOutputError::Xml),
    };
    edits
        .try_reserve(1)
        .map_err(|_| NativeFormPackageOutputError::Allocation)?;
    edits.push(edit);
    Ok(())
}
fn apply(
    source: &[u8],
    edits: &[Edit],
    limit: usize,
) -> Result<Vec<u8>, NativeFormPackageOutputError> {
    let mut length = source.len();
    let mut cursor = 0;
    for e in edits {
        if e.start < cursor || e.start > e.end || e.end > source.len() {
            return Err(NativeFormPackageOutputError::Preservation);
        }
        length = length
            .checked_sub(e.end - e.start)
            .and_then(|n| n.checked_add(e.replacement.len()))
            .ok_or(NativeFormPackageOutputError::Limit)?;
        cursor = e.end;
    }
    if length > limit {
        return Err(NativeFormPackageOutputError::Limit);
    }
    let mut output = Vec::new();
    output
        .try_reserve_exact(length)
        .map_err(|_| NativeFormPackageOutputError::Allocation)?;
    cursor = 0;
    for e in edits {
        output.extend_from_slice(&source[cursor..e.start]);
        output.extend_from_slice(&e.replacement);
        cursor = e.end;
    }
    output.extend_from_slice(&source[cursor..]);
    // Independent gap comparison, including all form payload/geometry and final suffix.
    cursor = 0;
    let mut offset = 0;
    for e in edits {
        let unchanged = e.start - cursor;
        if output.get(offset..offset + unchanged) != source.get(cursor..e.start) {
            return Err(NativeFormPackageOutputError::Preservation);
        }
        offset += unchanged;
        if output.get(offset..offset + e.replacement.len()) != Some(e.replacement.as_slice()) {
            return Err(NativeFormPackageOutputError::Preservation);
        }
        offset += e.replacement.len();
        cursor = e.end;
    }
    if output.len() != length || output.get(offset..) != source.get(cursor..) {
        return Err(NativeFormPackageOutputError::Preservation);
    }
    Ok(output)
}

fn write_package(
    parts: &[OutputPart],
    limit: usize,
) -> Result<Vec<u8>, NativeFormPackageOutputError> {
    let mut writer = ZipWriter::new(BoundedOutputBuffer {
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
        writer.write_all(&part.bytes).map_err(|e| io_error(&e))?;
    }
    Ok(writer.finish().map_err(zip_error)?.bytes)
}
// Seekable ZIP output is bounded before allocation, including the central directory.
struct BoundedOutputBuffer {
    bytes: Vec<u8>,
    position: usize,
    limit: usize,
}
impl Write for BoundedOutputBuffer {
    fn write(&mut self, input: &[u8]) -> io::Result<usize> {
        let end = self
            .position
            .checked_add(input.len())
            .filter(|n| *n <= self.limit)
            .ok_or_else(|| {
                io::Error::new(io::ErrorKind::FileTooLarge, "native form output limit")
            })?;
        if end > self.bytes.len() {
            self.bytes
                .try_reserve_exact(end - self.bytes.len())
                .map_err(|_| {
                    io::Error::new(io::ErrorKind::OutOfMemory, "native form output allocation")
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
impl Seek for BoundedOutputBuffer {
    fn seek(&mut self, to: SeekFrom) -> io::Result<u64> {
        let next = match to {
            SeekFrom::Start(n) => Some(n),
            SeekFrom::Current(n) => offset(
                u64::try_from(self.position)
                    .map_err(|_| io::Error::other("native form output position"))?,
                n,
            ),
            SeekFrom::End(n) => offset(
                u64::try_from(self.bytes.len())
                    .map_err(|_| io::Error::other("native form output position"))?,
                n,
            ),
        }
        .and_then(|n| usize::try_from(n).ok())
        .filter(|n| *n <= self.limit)
        .ok_or_else(|| {
            io::Error::new(io::ErrorKind::FileTooLarge, "native form output seek limit")
        })?;
        self.position = next;
        u64::try_from(next).map_err(|_| io::Error::other("native form output position"))
    }
}
fn offset(base: u64, n: i64) -> Option<u64> {
    if n >= 0 {
        base.checked_add(n.unsigned_abs())
    } else {
        base.checked_sub(n.unsigned_abs())
    }
}
fn io_error(error: &io::Error) -> NativeFormPackageOutputError {
    match error.kind() {
        io::ErrorKind::FileTooLarge => NativeFormPackageOutputError::Limit,
        io::ErrorKind::OutOfMemory => NativeFormPackageOutputError::Allocation,
        _ => NativeFormPackageOutputError::Zip,
    }
}
fn zip_error(error: zip::result::ZipError) -> NativeFormPackageOutputError {
    if let zip::result::ZipError::Io(error) = error {
        io_error(&error)
    } else {
        NativeFormPackageOutputError::Zip
    }
}
fn hex(raw: &[u8]) -> String {
    use std::fmt::Write as _;
    let mut value = String::with_capacity(raw.len() * 2);
    for byte in raw {
        let _ = write!(&mut value, "{byte:02x}");
    }
    value
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn bounded_zip_sink_checks_write_seek_and_negative_offsets_before_allocation()
    -> Result<(), Box<dyn std::error::Error>> {
        let mut sink = BoundedOutputBuffer {
            bytes: Vec::new(),
            position: 0,
            limit: 4,
        };
        sink.write_all(b"1234")?;
        assert_eq!(
            sink.write(b"5").err().map(|e| e.kind()),
            Some(io::ErrorKind::FileTooLarge)
        );
        assert_eq!(sink.bytes, b"1234");
        assert!(sink.seek(SeekFrom::Current(1)).is_err());
        assert!(sink.seek(SeekFrom::End(-5)).is_err());
        sink.seek(SeekFrom::End(-2))?;
        sink.write_all(b"ab")?;
        assert_eq!(sink.bytes, b"12ab");
        assert_eq!(sink.seek(SeekFrom::Start(4))?, 4);
        assert_eq!(sink.bytes.len(), 4);
        Ok(())
    }
    #[test]
    fn attribute_escape_preserves_literal_whitespace_and_xml_metacharacters()
    -> Result<(), NativeFormPackageOutputError> {
        assert_eq!(
            escape("한글 &<>'\"\t\r\n")?,
            "한글 &amp;&lt;&gt;&apos;&quot;&#9;&#13;&#10;"
        );
        assert_eq!(escape("\u{1}"), Err(NativeFormPackageOutputError::Xml));
        assert_eq!(
            escape(&"x".repeat(MAX_ATTRIBUTE + 1)),
            Err(NativeFormPackageOutputError::Limit)
        );
        Ok(())
    }
}
