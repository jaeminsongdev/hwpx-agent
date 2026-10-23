//! Coupled native form foreground/catalog transition. No native or product authority.
//! Preserve complete existing styles and raw parts; never approximate requested RGB.
use crate::{
    BoundedZipReader, CharacterStyleCatalog, CharacterStyleCatalogReader,
    CharacterStyleCatalogWriter, CharacterStyleLimits, Color, Compression, EntryMetadata,
    NativeFormHwpxLimits, NativeFormHwpxReadback, NativeFormHwpxReader, NativeFormPackageLimits,
    NativeFormPackageMap, NativeFormPackagePolicy, NativeFormPackageReadback,
    NativeFormPackageReader, PackageLimitConfig, PackageLimits, PreservingXmlDocument,
    XmlElementToken,
};
use domain_ir::{FormControlIdentity, FormControlLimits};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use std::{
    collections::{BTreeMap, BTreeSet},
    fmt,
    io::{self, Cursor, Seek, SeekFrom, Write},
};
use thiserror::Error;
use zip::{CompressionMethod, ZipWriter, write::SimpleFileOptions};

pub const NATIVE_FORM_COLOR_PROFILE: &str = "hwpx-agent.native-form-package.coupled-foreground/v1";
const HEADER: &str = "Contents/header.xml";
const HH: &str = "http://www.hancom.co.kr/hwpml/2011/head";
const HP: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const ARCHIVE: usize = 32 * 1024 * 1024;
const PART: usize = 2 * 1024 * 1024;
const TOTAL: usize = 16 * 1024 * 1024;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct NativeFormColorLimits {
    archive: usize,
    part: usize,
    total: usize,
}
impl Default for NativeFormColorLimits {
    fn default() -> Self {
        Self {
            archive: ARCHIVE,
            part: PART,
            total: TOTAL,
        }
    }
}
impl NativeFormColorLimits {
    /// Creates finite output bounds without silent clamping.
    /// # Errors
    /// Rejects zero, contradictory or over-ceiling bounds.
    pub fn new(archive: usize, part: usize, total: usize) -> Result<Self, NativeFormColorError> {
        if archive == 0
            || archive > ARCHIVE
            || part == 0
            || part > PART
            || total == 0
            || total > TOTAL
            || part > total
        {
            return Err(NativeFormColorError::Limit);
        }
        Ok(Self {
            archive,
            part,
            total,
        })
    }
    fn zip(self) -> Result<PackageLimits, NativeFormColorError> {
        PackageLimits::new(PackageLimitConfig {
            max_archive_bytes: self.archive as u64,
            max_entry_expanded_bytes: self.part as u64,
            max_total_expanded_bytes: self.total as u64,
            ..PackageLimitConfig::default()
        })
        .map_err(|_| NativeFormColorError::Limit)
    }
}
#[derive(Debug, Error, Eq, PartialEq)]
pub enum NativeFormColorError {
    #[error("NATIVE_FORM_COLOR_LIMIT")]
    Limit,
    #[error("NATIVE_FORM_COLOR_BINDING_REJECTED")]
    Binding,
    #[error("NATIVE_FORM_COLOR_REQUEST_REJECTED")]
    Request,
    #[error("NATIVE_FORM_COLOR_PROTECTION_REJECTED")]
    Protection,
    #[error("NATIVE_FORM_COLOR_CATALOG_REJECTED")]
    Catalog,
    #[error("NATIVE_FORM_COLOR_XML_REJECTED")]
    Xml,
    #[error("NATIVE_FORM_COLOR_ZIP_REJECTED")]
    Zip,
    #[error("NATIVE_FORM_COLOR_PRESERVATION_REJECTED")]
    Preservation,
    #[error("NATIVE_FORM_COLOR_TARGET_REJECTED")]
    Target,
    #[error("NATIVE_FORM_COLOR_ALLOCATION_FAILED")]
    Allocation,
}

/// Typed provider-side intent; never an arbitrary XML path or public raw action.
#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct NativeFormColorRequest {
    pub target: FormControlIdentity,
    pub foreground_rgb: u32,
}
impl fmt::Debug for NativeFormColorRequest {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("NativeFormColorRequest(<redacted>)")
    }
}
#[derive(Clone)]
pub struct NativeFormColorPlan {
    source: NativeFormPackageReadback,
    map: NativeFormPackageMap,
    policies: Vec<NativeFormPackagePolicy>,
    requests: Vec<NativeFormColorRequest>,
}
impl fmt::Debug for NativeFormColorPlan {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("NativeFormColorPlan(<redacted>)")
    }
}
impl NativeFormColorPlan {
    /// Binds complete observed source, explicit policies and exact RGB intents.
    /// # Errors
    /// Rejects invalid/stale maps, policies, protection, duplicates or absent targets.
    pub fn bind(
        source: &[u8],
        map: &NativeFormPackageMap,
        policies: &[NativeFormPackagePolicy],
        requests: &[NativeFormColorRequest],
        domain: FormControlLimits,
        package: NativeFormPackageLimits,
    ) -> Result<Self, NativeFormColorError> {
        let observed = NativeFormPackageReader::read(source, map, package)
            .map_err(|_| NativeFormColorError::Binding)?;
        validate_requests(&observed, policies, requests, domain)?;
        Ok(Self {
            source: observed,
            map: map.clone(),
            policies: policies.to_vec(),
            requests: requests.to_vec(),
        })
    }
}
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct NativeFormColorPreservation {
    pub existing_styles_and_fonts_preserved: bool,
    pub undeclared_expanded_parts_byte_exact: bool,
    pub outside_declared_xml_edits_byte_exact: bool,
    pub entry_order_and_compression: &'static str,
}
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct NativeFormColorReceipt {
    pub profile: &'static str,
    pub source_package_sha256: String,
    pub output_package_sha256: String,
    pub target_state_sha256: String,
    pub document_flow_sha256: String,
    pub requested_controls: usize,
    pub appended_styles: usize,
    pub reused_styles: usize,
    pub changed_sections: usize,
    pub preservation: NativeFormColorPreservation,
    pub zip_header_policy: &'static str,
    pub actual_native_validation: &'static str,
}
pub struct NativeFormColorOutput {
    bytes: Vec<u8>,
    receipt: NativeFormColorReceipt,
}
impl fmt::Debug for NativeFormColorOutput {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("NativeFormColorOutput")
            .field("bytes", &self.bytes.len())
            .finish_non_exhaustive()
    }
}
impl NativeFormColorOutput {
    #[must_use]
    pub fn bytes(&self) -> &[u8] {
        &self.bytes
    }
    #[must_use]
    pub const fn receipt(&self) -> &NativeFormColorReceipt {
        &self.receipt
    }
}
#[derive(Debug)]
pub struct NativeFormColorPreparer;
impl NativeFormColorPreparer {
    /// Couples exact common foreground and actual complete character styles atomically.
    /// # Errors
    /// Emits no artifact on stale source, malformed catalogs, protection or target/preservation drift.
    pub fn prepare(
        source: &[u8],
        plan: &NativeFormColorPlan,
        domain: FormControlLimits,
        package: NativeFormPackageLimits,
        limits: NativeFormColorLimits,
    ) -> Result<NativeFormColorOutput, NativeFormColorError> {
        let prepared = derive(source, plan, domain, package, limits)?;
        let output = write_package(&prepared.parts, limits.archive)?;
        let receipt = verify(&output, plan, &prepared, domain, package, limits)?;
        Ok(NativeFormColorOutput {
            bytes: output,
            receipt,
        })
    }
    /// Independently derives all expected expanded parts and rereads an external complete output.
    /// # Errors
    /// Rejects substituted metadata, styles, forms, unrequested state or entry inventory/compression.
    pub fn verify_output(
        source: &[u8],
        plan: &NativeFormColorPlan,
        output: &[u8],
        domain: FormControlLimits,
        package: NativeFormPackageLimits,
        limits: NativeFormColorLimits,
    ) -> Result<NativeFormColorReceipt, NativeFormColorError> {
        let prepared = derive(source, plan, domain, package, limits)?;
        verify(output, plan, &prepared, domain, package, limits)
    }
}
fn validate_requests(
    observed: &NativeFormPackageReadback,
    policies: &[NativeFormPackagePolicy],
    requests: &[NativeFormColorRequest],
    domain: FormControlLimits,
) -> Result<(), NativeFormColorError> {
    let state = observed
        .bind_policies(policies, domain)
        .map_err(|_| NativeFormColorError::Binding)?;
    if observed.bindings().protection_signal_observed() {
        return Err(NativeFormColorError::Protection);
    }
    if requests.is_empty() || requests.len() > state.controls().len() {
        return Err(NativeFormColorError::Request);
    }
    let mut seen = BTreeSet::new();
    for request in requests {
        if request.foreground_rgb > 0x00FF_FFFF || !seen.insert(&request.target) {
            return Err(NativeFormColorError::Request);
        }
        let control = state
            .controls()
            .iter()
            .find(|c| c.identity == request.target)
            .ok_or(NativeFormColorError::Request)?;
        if control.shape_locked {
            return Err(NativeFormColorError::Protection);
        }
    }
    Ok(())
}
struct Part {
    metadata: EntryMetadata,
    bytes: Vec<u8>,
}
struct Prepared {
    parts: Vec<Part>,
    catalog: CharacterStyleCatalog,
    assigned: BTreeMap<FormControlIdentity, (u32, u32)>,
    appended: usize,
    reused: usize,
    changed: usize,
}
fn load(source: &[u8], limits: NativeFormColorLimits) -> Result<Vec<Part>, NativeFormColorError> {
    let mut reader = BoundedZipReader::open(Cursor::new(source), limits.zip()?)
        .map_err(|_| NativeFormColorError::Zip)?;
    let entries = reader.entries().to_vec();
    let mut parts = Vec::new();
    parts
        .try_reserve_exact(entries.len())
        .map_err(|_| NativeFormColorError::Allocation)?;
    for metadata in entries {
        let bytes = reader
            .read_entry(metadata.index)
            .map_err(|_| NativeFormColorError::Zip)?;
        parts.push(Part { metadata, bytes });
    }
    Ok(parts)
}
fn derive(
    source: &[u8],
    plan: &NativeFormColorPlan,
    domain: FormControlLimits,
    package: NativeFormPackageLimits,
    limits: NativeFormColorLimits,
) -> Result<Prepared, NativeFormColorError> {
    NativeFormPackageReader::verify(source, &plan.source, package)
        .map_err(|_| NativeFormColorError::Binding)?;
    validate_requests(&plan.source, &plan.policies, &plan.requests, domain)?;
    let mut parts = load(source, limits)?;
    let header = parts
        .iter_mut()
        .find(|p| p.metadata.path.as_str() == HEADER)
        .ok_or(NativeFormColorError::Catalog)?;
    let original =
        CharacterStyleCatalogReader::read(&header.bytes, CharacterStyleLimits::default())
            .map_err(|_| NativeFormColorError::Catalog)?;
    let Assignments {
        catalog,
        assigned,
        additions,
        reused,
    } = assign_styles(&original, &plan.source, &plan.requests)?;
    header.bytes = header_output(&header.bytes, &original, &catalog, &additions, limits.part)?;
    let mut changed = 0;
    for section in &plan.map.sections {
        let part = parts
            .iter_mut()
            .find(|p| p.metadata.path.as_str() == section.part)
            .ok_or(NativeFormColorError::Binding)?;
        if section.map.component_controls.is_empty() {
            continue;
        }
        let observed = NativeFormHwpxReader::read_section(
            &part.bytes,
            &section.map,
            NativeFormHwpxLimits::default(),
        )
        .map_err(|_| NativeFormColorError::Binding)?;
        let output = section_output(&part.bytes, &observed, &assigned, limits.part)?;
        if output != part.bytes {
            changed += 1;
            part.bytes = output;
        }
    }
    let total = parts
        .iter()
        .try_fold(0usize, |n, p| n.checked_add(p.bytes.len()))
        .ok_or(NativeFormColorError::Limit)?;
    if total > limits.total {
        return Err(NativeFormColorError::Limit);
    }
    Ok(Prepared {
        parts,
        catalog,
        assigned,
        appended: additions.len(),
        reused,
        changed,
    })
}
struct Assignments {
    catalog: CharacterStyleCatalog,
    assigned: BTreeMap<FormControlIdentity, (u32, u32)>,
    additions: Vec<(u32, u32, u32)>,
    reused: usize,
}
fn assign_styles(
    original: &CharacterStyleCatalog,
    source: &NativeFormPackageReadback,
    requests: &[NativeFormColorRequest],
) -> Result<Assignments, NativeFormColorError> {
    let mut catalog = original.clone();
    let mut assigned = BTreeMap::new();
    let mut additions = Vec::new();
    let mut reused = 0;
    let controls: BTreeMap<_, _> = source
        .sections()
        .flat_map(NativeFormHwpxReadback::controls)
        .map(|c| (&c.component_identity, c))
        .collect();
    let bases: BTreeMap<_, _> = original.styles.iter().map(|s| (s.id, s)).collect();
    let mut semantic_ids = BTreeMap::new();
    for style in &original.styles {
        let mut semantic = style.clone();
        semantic.id = 0;
        semantic_ids.entry(semantic).or_insert(style.id);
    }
    let mut next_id = original
        .styles
        .iter()
        .map(|s| s.id)
        .max()
        .ok_or(NativeFormColorError::Catalog)?
        .checked_add(1);
    for request in requests {
        let c = controls
            .get(&request.target)
            .ok_or(NativeFormColorError::Request)?;
        let base = *bases
            .get(&c.common.character.char_pr_id_ref)
            .ok_or(NativeFormColorError::Catalog)?;
        let mut wanted = base.clone();
        wanted.id = 0;
        let rgb = request.foreground_rgb;
        wanted.text_color = Color::Rgb(
            ((rgb >> 16) & 255) as u8,
            ((rgb >> 8) & 255) as u8,
            (rgb & 255) as u8,
        );
        let id = if let Some(&id) = semantic_ids.get(&wanted) {
            reused += 1;
            id
        } else {
            let id = next_id.ok_or(NativeFormColorError::Catalog)?;
            next_id = id.checked_add(1);
            semantic_ids.insert(wanted.clone(), id);
            wanted.id = id;
            if catalog.styles.len() >= CharacterStyleLimits::default().config().styles {
                return Err(NativeFormColorError::Limit);
            }
            catalog.styles.push(wanted);
            additions.push((base.id, id, rgb));
            id
        };
        assigned.insert(request.target.clone(), (rgb, id));
    }
    // Validate the complete typed catalog once before extending any bytes; do not
    // serialize it over the original refList, which contains unrelated catalogs.
    CharacterStyleCatalogWriter::lower(&catalog, CharacterStyleLimits::default())
        .map_err(|_| NativeFormColorError::Catalog)?;
    Ok(Assignments {
        catalog,
        assigned,
        additions,
        reused,
    })
}
struct Edit {
    start: usize,
    end: usize,
    replacement: Vec<u8>,
}
fn named(node: &XmlElementToken, namespace: &str, name: &str) -> bool {
    node.name().namespace() == Some(namespace) && node.name().local_name() == name
}
fn attribute<'a>(
    node: &'a XmlElementToken,
    name: &str,
) -> Result<&'a crate::XmlAttributeToken, NativeFormColorError> {
    let mut a = node
        .attributes()
        .iter()
        .filter(|a| a.name().namespace().is_none() && a.name().local_name() == name);
    let value = a.next().ok_or(NativeFormColorError::Xml)?;
    if a.next().is_some() {
        return Err(NativeFormColorError::Xml);
    }
    Ok(value)
}
fn attr_edit(
    node: &XmlElementToken,
    name: &str,
    value: String,
) -> Result<Edit, NativeFormColorError> {
    let a = attribute(node, name)?;
    let span = a.value_span();
    // This internal editor admits only generated decimal and exact six-digit RGB literals.
    if !value.bytes().all(|c| c.is_ascii_hexdigit() || c == b'#') {
        return Err(NativeFormColorError::Xml);
    }
    Ok(Edit {
        start: span.start(),
        end: span.end(),
        replacement: value.into_bytes(),
    })
}
fn apply(raw: &[u8], mut edits: Vec<Edit>, limit: usize) -> Result<Vec<u8>, NativeFormColorError> {
    edits.sort_by_key(|e| (e.start, e.end));
    let mut end = 0;
    let mut length = raw.len();
    for e in &edits {
        if e.start < end || e.end < e.start || e.end > raw.len() {
            return Err(NativeFormColorError::Xml);
        }
        length = length
            .checked_sub(e.end - e.start)
            .and_then(|n| n.checked_add(e.replacement.len()))
            .ok_or(NativeFormColorError::Limit)?;
        end = e.end;
    }
    if length > limit {
        return Err(NativeFormColorError::Limit);
    }
    let mut out = Vec::new();
    out.try_reserve_exact(length)
        .map_err(|_| NativeFormColorError::Allocation)?;
    end = 0;
    for e in edits {
        out.extend_from_slice(&raw[end..e.start]);
        out.extend_from_slice(&e.replacement);
        end = e.end;
    }
    out.extend_from_slice(&raw[end..]);
    Ok(out)
}
fn header_output(
    raw: &[u8],
    original: &CharacterStyleCatalog,
    expected: &CharacterStyleCatalog,
    additions: &[(u32, u32, u32)],
    limit: usize,
) -> Result<Vec<u8>, NativeFormColorError> {
    if additions.is_empty() {
        return Ok(raw.to_vec());
    }
    let doc = PreservingXmlDocument::parse(raw).map_err(|_| NativeFormColorError::Xml)?;
    let parents: Vec<_> = doc
        .elements()
        .iter()
        .enumerate()
        .filter(|(_, n)| named(n, HH, "charProperties"))
        .collect();
    let [(parent_index, parent)] = parents.as_slice() else {
        return Err(NativeFormColorError::Catalog);
    };
    let count = attribute(parent, "itemCnt")?
        .semantic_value()
        .parse::<usize>()
        .map_err(|_| NativeFormColorError::Catalog)?;
    let children: Vec<_> = doc
        .elements()
        .iter()
        .filter(|n| n.parent() == Some(*parent_index))
        .collect();
    if count != original.styles.len()
        || children.len() != count
        || children.iter().any(|n| !named(n, HH, "charPr"))
    {
        return Err(NativeFormColorError::Catalog);
    }
    let mut appended = Vec::new();
    for &(base, id, rgb) in additions {
        let nodes: Vec<_> = children
            .iter()
            .filter(|n| {
                attribute(n, "id").is_ok_and(|a| a.semantic_value().parse::<u32>() == Ok(base))
            })
            .collect();
        let [node] = nodes.as_slice() else {
            return Err(NativeFormColorError::Catalog);
        };
        let span = node.outer_span().ok_or(NativeFormColorError::Xml)?;
        let edits = [
            attr_edit(node, "id", id.to_string())?,
            attr_edit(node, "textColor", format!("#{rgb:06X}"))?,
        ]
        .into_iter()
        .map(|e| Edit {
            start: e.start - span.start(),
            end: e.end - span.start(),
            replacement: e.replacement,
        })
        .collect();
        let fragment = apply(&raw[span.start()..span.end()], edits, limit)?;
        if appended
            .len()
            .checked_add(fragment.len())
            .is_none_or(|n| n > limit)
        {
            return Err(NativeFormColorError::Limit);
        }
        appended.extend_from_slice(&fragment);
    }
    let insertion = parent
        .end_tag_span()
        .ok_or(NativeFormColorError::Xml)?
        .start();
    let output = apply(
        raw,
        vec![
            attr_edit(parent, "itemCnt", expected.styles.len().to_string())?,
            Edit {
                start: insertion,
                end: insertion,
                replacement: appended,
            },
        ],
        limit,
    )?;
    let observed = CharacterStyleCatalogReader::read(&output, CharacterStyleLimits::default())
        .map_err(|_| NativeFormColorError::Catalog)?;
    if observed != *expected
        || observed.font_faces != original.font_faces
        || observed.styles[..original.styles.len()] != original.styles
    {
        return Err(NativeFormColorError::Preservation);
    }
    Ok(output)
}
fn section_output(
    raw: &[u8],
    observed: &NativeFormHwpxReadback,
    assigned: &BTreeMap<FormControlIdentity, (u32, u32)>,
    limit: usize,
) -> Result<Vec<u8>, NativeFormColorError> {
    let doc = PreservingXmlDocument::parse(raw).map_err(|_| NativeFormColorError::Xml)?;
    let roots: Vec<_> = doc
        .elements()
        .iter()
        .enumerate()
        .filter(|(_, n)| {
            n.name().namespace() == Some(HP)
                && matches!(
                    n.name().local_name(),
                    "edit" | "checkBtn" | "radioBtn" | "comboBox" | "listBox"
                )
        })
        .collect();
    if roots.len() != observed.controls().len() {
        return Err(NativeFormColorError::Binding);
    }
    let mut edits = Vec::new();
    for ((index, node), control) in roots.iter().zip(observed.controls()) {
        let Some(&(rgb, id)) = assigned.get(&control.component_identity) else {
            continue;
        };
        if control.common.fore_color_rgb != rgb {
            edits.push(attr_edit(node, "foreColor", format!("#{rgb:06X}"))?);
        }
        if control.common.character.char_pr_id_ref != id {
            let children: Vec<_> = doc
                .elements()
                .iter()
                .filter(|n| n.parent() == Some(*index) && named(n, HP, "formCharPr"))
                .collect();
            let [child] = children.as_slice() else {
                return Err(NativeFormColorError::Xml);
            };
            edits.push(attr_edit(child, "charPrIDRef", id.to_string())?);
        }
    }
    apply(raw, edits, limit)
}
fn verify(
    output: &[u8],
    plan: &NativeFormColorPlan,
    prepared: &Prepared,
    domain: FormControlLimits,
    package: NativeFormPackageLimits,
    limits: NativeFormColorLimits,
) -> Result<NativeFormColorReceipt, NativeFormColorError> {
    let actual = load(output, limits)?;
    if actual.len() != prepared.parts.len() {
        return Err(NativeFormColorError::Preservation);
    }
    for (a, b) in actual.iter().zip(&prepared.parts) {
        if a.metadata.path != b.metadata.path
            || a.metadata.compression != b.metadata.compression
            || a.bytes != b.bytes
        {
            return Err(NativeFormColorError::Preservation);
        }
    }
    let observed = NativeFormPackageReader::read(output, &plan.map, package)
        .map_err(|_| NativeFormColorError::Target)?;
    let state = observed
        .bind_policies(&plan.policies, domain)
        .map_err(|_| NativeFormColorError::Target)?;
    let source_state = plan
        .source
        .bind_policies(&plan.policies, domain)
        .map_err(|_| NativeFormColorError::Binding)?;
    if state.controls().len() != source_state.controls().len()
        || observed.document_flow_sha256() != plan.source.document_flow_sha256()
    {
        return Err(NativeFormColorError::Target);
    }
    for (a, b) in state.controls().iter().zip(source_state.controls()) {
        let mut expected = b.clone();
        if let Some(&(rgb, id)) = prepared.assigned.get(&b.identity) {
            expected.common.fore_color_rgb = rgb;
            expected.common.character.char_pr_id_ref = id;
            let style = prepared
                .catalog
                .styles
                .iter()
                .find(|s| s.id == id)
                .ok_or(NativeFormColorError::Target)?;
            if style.text_color
                != Color::Rgb(
                    ((rgb >> 16) & 255) as u8,
                    ((rgb >> 8) & 255) as u8,
                    (rgb & 255) as u8,
                )
            {
                return Err(NativeFormColorError::Target);
            }
        }
        if *a != expected {
            return Err(NativeFormColorError::Target);
        }
    }
    Ok(NativeFormColorReceipt {
        profile: NATIVE_FORM_COLOR_PROFILE,
        source_package_sha256: plan.source.package_sha256().into(),
        output_package_sha256: sha(output),
        target_state_sha256: state
            .canonical_sha256(domain)
            .map_err(|_| NativeFormColorError::Target)?,
        document_flow_sha256: observed.document_flow_sha256().into(),
        requested_controls: plan.requests.len(),
        appended_styles: prepared.appended,
        reused_styles: prepared.reused,
        changed_sections: prepared.changed,
        preservation: NativeFormColorPreservation {
            existing_styles_and_fonts_preserved: true,
            undeclared_expanded_parts_byte_exact: true,
            outside_declared_xml_edits_byte_exact: true,
            entry_order_and_compression: "preserved",
        },
        zip_header_policy: "rewritten_not_byte_exact",
        actual_native_validation: "not_run",
    })
}
fn sha(raw: &[u8]) -> String {
    use std::fmt::Write as _;
    let hash = Sha256::digest(raw);
    let mut out = String::with_capacity(64);
    for b in hash {
        let _ = write!(&mut out, "{b:02x}");
    }
    out
}
fn write_package(parts: &[Part], limit: usize) -> Result<Vec<u8>, NativeFormColorError> {
    let mut writer = ZipWriter::new(Sink {
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
fn io_error(error: &io::Error) -> NativeFormColorError {
    match error.kind() {
        io::ErrorKind::FileTooLarge => NativeFormColorError::Limit,
        io::ErrorKind::OutOfMemory => NativeFormColorError::Allocation,
        _ => NativeFormColorError::Zip,
    }
}
fn zip_error(error: zip::result::ZipError) -> NativeFormColorError {
    if let zip::result::ZipError::Io(e) = error {
        io_error(&e)
    } else {
        NativeFormColorError::Zip
    }
}
struct Sink {
    bytes: Vec<u8>,
    position: usize,
    limit: usize,
}
impl Write for Sink {
    fn write(&mut self, raw: &[u8]) -> io::Result<usize> {
        let end = self
            .position
            .checked_add(raw.len())
            .filter(|n| *n <= self.limit)
            .ok_or_else(|| {
                io::Error::new(io::ErrorKind::FileTooLarge, "form color output bound")
            })?;
        if end > self.bytes.len() {
            self.bytes
                .try_reserve_exact(end - self.bytes.len())
                .map_err(|_| io::Error::new(io::ErrorKind::OutOfMemory, "form color allocation"))?;
            self.bytes.resize(end, 0);
        }
        self.bytes[self.position..end].copy_from_slice(raw);
        self.position = end;
        Ok(raw.len())
    }
    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}
impl Seek for Sink {
    fn seek(&mut self, from: SeekFrom) -> io::Result<u64> {
        let next = match from {
            SeekFrom::Start(n) => Some(n),
            SeekFrom::Current(n) => offset(self.position as u64, n),
            SeekFrom::End(n) => offset(self.bytes.len() as u64, n),
        }
        .and_then(|n| usize::try_from(n).ok())
        .filter(|n| *n <= self.limit)
        .ok_or_else(|| io::Error::new(io::ErrorKind::FileTooLarge, "form color seek bound"))?;
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
