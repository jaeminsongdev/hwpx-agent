//! Sealed whole-package root-href preparation; never a native acceptance receipt.
use crate::{
    BoundedZipReader, Compression, EntryMetadata, PackageGraph, PackageGraphLimits,
    PackageLimitConfig, PackageLimits, PreservingXmlDocument, RelationshipKind, XmlElementToken,
};
use sha2::{Digest as _, Sha256};
use std::{
    collections::BTreeMap,
    fmt,
    io::{self, Cursor, Seek, SeekFrom, Write},
};
use thiserror::Error;
use zip::{CompressionMethod, ZipWriter, write::SimpleFileOptions};

pub const NATIVE_ROOT_MANIFEST_PROFILE_ID: &str =
    "hwpx-agent.native-root-manifest.complete-package/v1";
const MANIFEST: &str = "Contents/content.hpf";
const MAX_ARCHIVE: usize = 32 * 1024 * 1024;
const MAX_PART: usize = 2 * 1024 * 1024;
const MAX_TOTAL: usize = 16 * 1024 * 1024;
const MAX_ENTRIES: usize = 256;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct NativeRootManifestLimits {
    archive: usize,
    part: usize,
    total: usize,
    entries: usize,
}
impl Default for NativeRootManifestLimits {
    fn default() -> Self {
        Self {
            archive: MAX_ARCHIVE,
            part: MAX_PART,
            total: MAX_TOTAL,
            entries: MAX_ENTRIES,
        }
    }
}
impl NativeRootManifestLimits {
    /// Finite package/output ceilings; invalid inputs are not clamped.
    /// # Errors
    /// Rejects zero, contradictory and over-ceiling values.
    pub fn new(
        archive: usize,
        part: usize,
        total: usize,
        entries: usize,
    ) -> Result<Self, NativeRootManifestError> {
        if archive == 0
            || archive > MAX_ARCHIVE
            || part == 0
            || part > MAX_PART
            || total == 0
            || total > MAX_TOTAL
            || entries == 0
            || entries > MAX_ENTRIES
            || part > total
        {
            return Err(NativeRootManifestError::Limit);
        }
        Ok(Self {
            archive,
            part,
            total,
            entries,
        })
    }
    fn zip(self) -> Result<PackageLimits, NativeRootManifestError> {
        PackageLimits::new(PackageLimitConfig {
            max_archive_bytes: self.archive as u64,
            max_entries: self.entries,
            max_entry_expanded_bytes: self.part as u64,
            max_total_expanded_bytes: self.total as u64,
            ..PackageLimitConfig::default()
        })
        .map_err(|_| NativeRootManifestError::Limit)
    }
}
#[derive(Debug, Error, Eq, PartialEq)]
pub enum NativeRootManifestError {
    #[error("NATIVE_ROOT_MANIFEST_LIMIT")]
    Limit,
    #[error("NATIVE_ROOT_MANIFEST_PACKAGE_REJECTED")]
    Package,
    #[error("NATIVE_ROOT_MANIFEST_GRAPH_REJECTED")]
    Graph,
    #[error("NATIVE_ROOT_MANIFEST_PROFILE_UNSUPPORTED")]
    Unsupported,
    #[error("NATIVE_ROOT_MANIFEST_XML_REJECTED")]
    Xml,
    #[error("NATIVE_ROOT_MANIFEST_SOURCE_CHANGED")]
    Source,
    #[error("NATIVE_ROOT_MANIFEST_OUTPUT_MISMATCH")]
    Output,
    #[error("NATIVE_ROOT_MANIFEST_ALLOCATION_FAILED")]
    Allocation,
}
#[derive(Clone, Eq, PartialEq)]
struct Edit {
    start: usize,
    end: usize,
    replacement: Vec<u8>,
}
#[derive(Clone)]
pub struct NativeRootManifestPlan {
    source_sha256: [u8; 32],
    edits: Vec<Edit>,
}
impl fmt::Debug for NativeRootManifestPlan {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("NativeRootManifestPlan(<redacted>)")
    }
}
impl NativeRootManifestPlan {
    /// Binds every integrity-read source part and the actual closed relationship graph.
    /// # Errors
    /// Rejects unsafe/open graphs, malformed metadata and unsupported package-document location.
    pub fn bind(
        source: &[u8],
        limits: NativeRootManifestLimits,
    ) -> Result<Self, NativeRootManifestError> {
        let snapshot = read(source, limits)?;
        Ok(Self {
            source_sha256: digest(source),
            edits: edits(&snapshot)?,
        })
    }
}
#[derive(Clone, Debug, Eq, PartialEq, serde::Serialize)]
pub struct NativeRootManifestPreservation {
    pub non_manifest_parts_expanded_byte_exact: bool,
    pub manifest_outside_href_edits_byte_exact: bool,
    pub entry_order_and_compression_preserved: bool,
}
#[derive(Clone, Copy, Debug, Eq, PartialEq, serde::Serialize)]
#[serde(rename_all = "snake_case")]
pub enum NativeRootManifestQualification {
    PackagePreparationOnlyNativeAndTypedReferenceUnqualified,
}
#[derive(Clone, Debug, Eq, PartialEq, serde::Serialize)]
pub struct NativeRootManifestReceipt {
    pub profile: &'static str,
    pub source_package_sha256: String,
    pub output_package_sha256: String,
    pub source_manifest_sha256: String,
    pub output_manifest_sha256: String,
    pub entry_count: usize,
    pub changed_href_attributes: usize,
    pub graph_relationships_and_spine_preserved: bool,
    pub preservation: NativeRootManifestPreservation,
    pub zip_header_policy: &'static str,
    pub qualification: NativeRootManifestQualification,
}
pub struct NativeRootManifestOutput {
    bytes: Vec<u8>,
    receipt: NativeRootManifestReceipt,
}
impl fmt::Debug for NativeRootManifestOutput {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("NativeRootManifestOutput")
            .field("bytes", &self.bytes.len())
            .finish_non_exhaustive()
    }
}
impl NativeRootManifestOutput {
    #[must_use]
    pub fn bytes(&self) -> &[u8] {
        &self.bytes
    }
    #[must_use]
    pub const fn receipt(&self) -> &NativeRootManifestReceipt {
        &self.receipt
    }
}
#[derive(Debug)]
pub struct NativeRootManifestPreparer;
impl NativeRootManifestPreparer {
    /// Rewrites only actual manifest-item href value spans, preserving graph meaning.
    /// # Errors
    /// Returns no artifact on stale source, finite-limit or complete preservation failure.
    pub fn prepare(
        source: &[u8],
        plan: &NativeRootManifestPlan,
        limits: NativeRootManifestLimits,
    ) -> Result<NativeRootManifestOutput, NativeRootManifestError> {
        let snapshot = sealed(source, plan, limits)?;
        let target = expected(&snapshot, plan, limits)?;
        let bytes = if plan.edits.is_empty() {
            source.to_vec()
        } else {
            write(&snapshot.entries, &target, limits)?
        };
        let receipt = Self::verify_output(source, plan, &bytes, limits)?;
        Ok(NativeRootManifestOutput { bytes, receipt })
    }
    /// Independently re-reads an external candidate; never trusts a supplied receipt.
    /// # Errors
    /// Rejects altered parts, changed graph, reordered/recompressed entries and stale plans.
    pub fn verify_output(
        source: &[u8],
        plan: &NativeRootManifestPlan,
        output: &[u8],
        limits: NativeRootManifestLimits,
    ) -> Result<NativeRootManifestReceipt, NativeRootManifestError> {
        let before = sealed(source, plan, limits)?;
        let actual = read(output, limits)?;
        let expected = expected(&before, plan, limits)?;
        if actual.parts != expected
            || !same_entries(&before.entries, &actual.entries)
            || before.graph.relationships != actual.graph.relationships
            || before.graph.spine != actual.graph.spine
            || before.graph.package_document != actual.graph.package_document
            || !edits(&actual)?.is_empty()
            || (plan.edits.is_empty() && source != output)
        {
            return Err(NativeRootManifestError::Output);
        }
        let manifest_before = before
            .parts
            .get(MANIFEST)
            .ok_or(NativeRootManifestError::Unsupported)?;
        let manifest_after = actual
            .parts
            .get(MANIFEST)
            .ok_or(NativeRootManifestError::Unsupported)?;
        Ok(NativeRootManifestReceipt {
            profile: NATIVE_ROOT_MANIFEST_PROFILE_ID,
            source_package_sha256: hash(source),
            output_package_sha256: hash(output),
            source_manifest_sha256: hash(manifest_before),
            output_manifest_sha256: hash(manifest_after),
            entry_count: actual.entries.len(),
            changed_href_attributes: plan.edits.len(),
            graph_relationships_and_spine_preserved: true,
            preservation: NativeRootManifestPreservation {
                non_manifest_parts_expanded_byte_exact: true,
                manifest_outside_href_edits_byte_exact: true,
                entry_order_and_compression_preserved: true,
            },
            zip_header_policy: if plan.edits.is_empty() {
                "original_raw_byte_exact"
            } else {
                "rewritten_not_byte_exact"
            },
            qualification: NativeRootManifestQualification::PackagePreparationOnlyNativeAndTypedReferenceUnqualified,
        })
    }
}
struct Snapshot {
    graph: PackageGraph,
    entries: Vec<EntryMetadata>,
    parts: BTreeMap<String, Vec<u8>>,
}
fn read(raw: &[u8], limits: NativeRootManifestLimits) -> Result<Snapshot, NativeRootManifestError> {
    if raw.is_empty() || raw.len() > limits.archive {
        return Err(NativeRootManifestError::Limit);
    }
    let mut reader = BoundedZipReader::open(Cursor::new(raw), limits.zip()?)
        .map_err(|_| NativeRootManifestError::Package)?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())
        .map_err(|_| NativeRootManifestError::Graph)?;
    if graph.package_document.as_str() != MANIFEST {
        return Err(NativeRootManifestError::Unsupported);
    }
    let entries = reader.entries().to_vec();
    let mut parts = BTreeMap::new();
    for entry in &entries {
        parts.insert(
            entry.path.as_str().to_owned(),
            reader
                .read_entry(entry.index)
                .map_err(|_| NativeRootManifestError::Package)?,
        );
    }
    Ok(Snapshot {
        graph,
        entries,
        parts,
    })
}
fn sealed(
    source: &[u8],
    plan: &NativeRootManifestPlan,
    limits: NativeRootManifestLimits,
) -> Result<Snapshot, NativeRootManifestError> {
    if source.is_empty() || source.len() > limits.archive {
        return Err(NativeRootManifestError::Limit);
    }
    if digest(source) != plan.source_sha256 {
        return Err(NativeRootManifestError::Source);
    }
    let snapshot = read(source, limits)?;
    if edits(&snapshot)? != plan.edits {
        return Err(NativeRootManifestError::Source);
    }
    Ok(snapshot)
}
fn attr<'a>(
    source: &[u8],
    node: &'a XmlElementToken,
    name: &str,
) -> Result<(&'a crate::XmlAttributeToken, String), NativeRootManifestError> {
    let mut attributes = node
        .attributes()
        .iter()
        .filter(|a| a.name().namespace().is_none() && a.name().local_name() == name);
    let attribute = attributes.next().ok_or(NativeRootManifestError::Xml)?;
    if attributes.next().is_some() {
        return Err(NativeRootManifestError::Xml);
    }
    let span = attribute.value_span();
    let raw = std::str::from_utf8(&source[span.start()..span.end()])
        .map_err(|_| NativeRootManifestError::Xml)?;
    let value = quick_xml::escape::unescape(raw)
        .map_err(|_| NativeRootManifestError::Xml)?
        .into_owned();
    Ok((attribute, value))
}
fn opf(node: &XmlElementToken, name: &str) -> bool {
    matches!(
        node.name().namespace(),
        Some("http://www.idpf.org/2007/opf" | "http://www.idpf.org/2007/opf/")
    ) && node.name().local_name() == name
}
fn edits(snapshot: &Snapshot) -> Result<Vec<Edit>, NativeRootManifestError> {
    let raw = snapshot
        .parts
        .get(MANIFEST)
        .ok_or(NativeRootManifestError::Unsupported)?;
    let document = PreservingXmlDocument::parse(raw).map_err(|_| NativeRootManifestError::Xml)?;
    let relationships: BTreeMap<_, _> = snapshot
        .graph
        .relationships
        .iter()
        .filter(|r| r.kind == RelationshipKind::ManifestItem)
        .map(|r| (r.id.as_str(), r.target.as_str()))
        .collect();
    let mut count = 0;
    let mut result = Vec::new();
    for node in document.elements().iter().filter(|n| opf(n, "item")) {
        let parent = node
            .parent()
            .and_then(|p| document.elements().get(p))
            .ok_or(NativeRootManifestError::Xml)?;
        if !opf(parent, "manifest") {
            return Err(NativeRootManifestError::Xml);
        }
        let (_, id) = attr(raw, node, "id")?;
        let (href, old) = attr(raw, node, "href")?;
        let target = relationships
            .get(id.as_str())
            .ok_or(NativeRootManifestError::Graph)?;
        count += 1;
        let canonical = target.replace('%', "%25");
        if old != canonical {
            result.push(Edit {
                start: href.value_span().start(),
                end: href.value_span().end(),
                replacement: escaped(&canonical).into_bytes(),
            });
        }
    }
    if count != relationships.len() {
        return Err(NativeRootManifestError::Graph);
    }
    result.sort_unstable_by_key(|e| e.start);
    if result.windows(2).any(|p| p[0].end > p[1].start) {
        return Err(NativeRootManifestError::Xml);
    }
    Ok(result)
}
fn escaped(value: &str) -> String {
    value
        .replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
        .replace('\'', "&apos;")
}
fn expected(
    snapshot: &Snapshot,
    plan: &NativeRootManifestPlan,
    limits: NativeRootManifestLimits,
) -> Result<BTreeMap<String, Vec<u8>>, NativeRootManifestError> {
    let source = snapshot
        .parts
        .get(MANIFEST)
        .ok_or(NativeRootManifestError::Unsupported)?;
    let length = plan
        .edits
        .iter()
        .try_fold(source.len(), |n, e| {
            n.checked_sub(e.end - e.start)
                .and_then(|n| n.checked_add(e.replacement.len()))
        })
        .ok_or(NativeRootManifestError::Limit)?;
    if length > limits.part {
        return Err(NativeRootManifestError::Limit);
    }
    let mut target = Vec::new();
    target
        .try_reserve_exact(length)
        .map_err(|_| NativeRootManifestError::Allocation)?;
    let mut last = 0;
    for edit in &plan.edits {
        target.extend_from_slice(&source[last..edit.start]);
        target.extend_from_slice(&edit.replacement);
        last = edit.end;
    }
    target.extend_from_slice(&source[last..]);
    let total = snapshot
        .parts
        .iter()
        .try_fold(0usize, |n, (p, raw)| {
            n.checked_add(if p == MANIFEST {
                target.len()
            } else {
                raw.len()
            })
        })
        .ok_or(NativeRootManifestError::Limit)?;
    if total > limits.total {
        return Err(NativeRootManifestError::Limit);
    }
    let mut parts = snapshot.parts.clone();
    parts.insert(MANIFEST.into(), target);
    Ok(parts)
}
fn same_entries(before: &[EntryMetadata], after: &[EntryMetadata]) -> bool {
    before.len() == after.len()
        && before
            .iter()
            .zip(after)
            .all(|(a, b)| a.path == b.path && a.compression == b.compression)
}
fn write(
    entries: &[EntryMetadata],
    parts: &BTreeMap<String, Vec<u8>>,
    limits: NativeRootManifestLimits,
) -> Result<Vec<u8>, NativeRootManifestError> {
    let mut writer = ZipWriter::new(Sink {
        bytes: Vec::new(),
        position: 0,
        limit: limits.archive,
    });
    for entry in entries {
        let method = match entry.compression {
            Compression::Stored => CompressionMethod::Stored,
            Compression::Deflated => CompressionMethod::Deflated,
        };
        writer
            .start_file(
                entry.path.as_str(),
                SimpleFileOptions::default().compression_method(method),
            )
            .map_err(|_| NativeRootManifestError::Package)?;
        writer
            .write_all(
                parts
                    .get(entry.path.as_str())
                    .ok_or(NativeRootManifestError::Package)?,
            )
            .map_err(|_| NativeRootManifestError::Limit)?;
    }
    Ok(writer
        .finish()
        .map_err(|_| NativeRootManifestError::Package)?
        .bytes)
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
            .ok_or_else(|| io::Error::new(io::ErrorKind::FileTooLarge, "manifest output limit"))?;
        if end > self.bytes.len() {
            self.bytes
                .try_reserve_exact(end - self.bytes.len())
                .map_err(|_| io::Error::new(io::ErrorKind::OutOfMemory, "manifest allocation"))?;
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
    fn seek(&mut self, to: SeekFrom) -> io::Result<u64> {
        let next = match to {
            SeekFrom::Start(n) => Some(n),
            SeekFrom::Current(n) => add(self.position as u64, n),
            SeekFrom::End(n) => add(self.bytes.len() as u64, n),
        }
        .and_then(|n| usize::try_from(n).ok())
        .filter(|n| *n <= self.limit)
        .ok_or_else(|| io::Error::new(io::ErrorKind::FileTooLarge, "manifest seek limit"))?;
        self.position = next;
        Ok(next as u64)
    }
}
fn add(base: u64, delta: i64) -> Option<u64> {
    if delta >= 0 {
        base.checked_add(delta.unsigned_abs())
    } else {
        base.checked_sub(delta.unsigned_abs())
    }
}
fn digest(raw: &[u8]) -> [u8; 32] {
    Sha256::digest(raw).into()
}
fn hash(raw: &[u8]) -> String {
    const HEX: &[u8; 16] = b"0123456789abcdef";
    let mut result = String::with_capacity(64);
    for byte in digest(raw) {
        result.push(char::from(HEX[usize::from(byte >> 4)]));
        result.push(char::from(HEX[usize::from(byte & 15)]));
    }
    result
}
