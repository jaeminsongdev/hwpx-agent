use std::fmt::{self, Debug};
use std::fs::File;
use std::io::{self, Cursor, Read, Seek, SeekFrom, Write};
use std::path::{Path, PathBuf};

use hwpx_agent_foundation::workdir::{SecureWorkspace, StagedArtifact, WorkspaceError};
use sha2::{Digest as _, Sha256};
use thiserror::Error;
use zip::write::SimpleFileOptions;
use zip::{CompressionMethod, DateTime, System, ZipWriter};

use crate::patch::VirtualPart;
use crate::{
    BoundedZipReader, Compression, GraphError, IdIndex, IdIndexError, IdIndexLimits, IdRuleProfile,
    PackageError, PackageGraph, PackageGraphLimits, PackageLimits, PackagePath, PatchError,
    PatchPartDisposition, PatchResult, PreservationError, PreservationReport,
    PreservationRuleProfile,
};

const NORMALIZED_DEFLATE_LEVEL: i64 = 6;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct WriterLimitConfig {
    pub max_output_bytes: u64,
}

impl Default for WriterLimitConfig {
    fn default() -> Self {
        Self {
            max_output_bytes: 512 * 1024 * 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct WriterLimits(WriterLimitConfig);

impl WriterLimits {
    pub const HARD_MAX_OUTPUT_BYTES: u64 = PackageLimits::HARD_MAX_ARCHIVE_BYTES;

    /// Validates the output ceiling without clamping it.
    ///
    /// # Errors
    ///
    /// Returns a stable invalid-limit error for zero or over-ceiling values.
    pub fn new(config: WriterLimitConfig) -> Result<Self, WriterError> {
        if config.max_output_bytes == 0 || config.max_output_bytes > Self::HARD_MAX_OUTPUT_BYTES {
            return Err(WriterError::InvalidLimit {
                field: "max_output_bytes",
                value: config.max_output_bytes,
                ceiling: Self::HARD_MAX_OUTPUT_BYTES,
            });
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> WriterLimitConfig {
        self.0
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum WriterMode {
    Preserving,
    Normalized,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum MetadataDisposition {
    PreservedAvailable,
    Normalized,
    NotPreservedUnavailable,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct WriterEntryRecord {
    path: PackagePath,
    disposition: PatchPartDisposition,
    source_order: Option<usize>,
    output_order: usize,
    source_compression: Option<Compression>,
    output_compression: Compression,
    expanded_sha256: [u8; 32],
}

impl WriterEntryRecord {
    #[must_use]
    pub const fn path(&self) -> &PackagePath {
        &self.path
    }

    #[must_use]
    pub const fn disposition(&self) -> PatchPartDisposition {
        self.disposition
    }

    #[must_use]
    pub const fn source_order(&self) -> Option<usize> {
        self.source_order
    }

    #[must_use]
    pub const fn output_order(&self) -> usize {
        self.output_order
    }

    #[must_use]
    pub const fn source_compression(&self) -> Option<Compression> {
        self.source_compression
    }

    #[must_use]
    pub const fn output_compression(&self) -> Compression {
        self.output_compression
    }

    #[must_use]
    pub const fn expanded_sha256(&self) -> [u8; 32] {
        self.expanded_sha256
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct WriterReport {
    mode: WriterMode,
    entries: Vec<WriterEntryRecord>,
    order: MetadataDisposition,
    compression_method: MetadataDisposition,
    timestamp: MetadataDisposition,
    extra_fields: MetadataDisposition,
    raw_compressed_stream: MetadataDisposition,
}

impl WriterReport {
    #[must_use]
    pub const fn mode(&self) -> WriterMode {
        self.mode
    }

    #[must_use]
    pub fn entries(&self) -> &[WriterEntryRecord] {
        &self.entries
    }

    #[must_use]
    pub const fn order(&self) -> MetadataDisposition {
        self.order
    }

    #[must_use]
    pub const fn compression_method(&self) -> MetadataDisposition {
        self.compression_method
    }

    #[must_use]
    pub const fn timestamp(&self) -> MetadataDisposition {
        self.timestamp
    }

    #[must_use]
    pub const fn extra_fields(&self) -> MetadataDisposition {
        self.extra_fields
    }

    #[must_use]
    pub const fn raw_compressed_stream(&self) -> MetadataDisposition {
        self.raw_compressed_stream
    }
}

/// A fully validated private ZIP artifact. Raw bytes are intentionally unavailable publicly.
pub struct PackageArtifact {
    mode: WriterMode,
    bytes: Box<[u8]>,
    sha256: [u8; 32],
    report: WriterReport,
    package_limits: PackageLimits,
    graph_limits: PackageGraphLimits,
    id_limits: IdIndexLimits,
    profile: IdRuleProfile,
    preservation_profile: PreservationRuleProfile,
}

impl Debug for PackageArtifact {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("PackageArtifact")
            .field("mode", &self.mode)
            .field("bytes", &self.bytes.len())
            .field("sha256", &self.sha256)
            .field("report", &self.report)
            .finish_non_exhaustive()
    }
}

impl PackageArtifact {
    #[must_use]
    pub const fn mode(&self) -> WriterMode {
        self.mode
    }

    #[must_use]
    pub const fn size_bytes(&self) -> usize {
        self.bytes.len()
    }

    #[must_use]
    pub const fn sha256(&self) -> [u8; 32] {
        self.sha256
    }

    #[must_use]
    pub const fn report(&self) -> &WriterReport {
        &self.report
    }

    /// Rehashes and fully reopens the private artifact.
    ///
    /// # Errors
    ///
    /// Returns no bytes and fails if digest, package graph, preservation or ID evidence drifts.
    pub fn verify(&self) -> Result<(), WriterError> {
        if <[u8; 32]>::from(Sha256::digest(&self.bytes)) != self.sha256 {
            return Err(WriterError::ArtifactMismatch);
        }
        validate_archive(
            Cursor::new(self.bytes.as_ref()),
            self.package_limits,
            self.graph_limits,
            self.preservation_profile,
            self.profile,
            self.id_limits,
        )?;
        Ok(())
    }

    /// Reopens and verifies the immutable package before a temporary byte callback.
    /// This is artifact integrity only, not fresh service ACL or execution authority.
    /// # Errors
    /// Does not invoke the callback if the original package trust chain rejects it.
    pub fn with_verified_bytes<T>(
        &self,
        consume: impl FnOnce(&[u8]) -> T,
    ) -> Result<T, WriterError> {
        self.verify()?;
        Ok(consume(&self.bytes))
    }
}

#[derive(Debug)]
pub struct PreservingWriter;

impl PreservingWriter {
    /// Packages a validated P03-07 private artifact while retaining available source order,
    /// compression method and exact expanded bytes.
    ///
    /// # Errors
    ///
    /// Returns no artifact unless the output fully reopens through the package trust chain.
    pub fn build(
        patch: &PatchResult,
        package_limits: PackageLimits,
        graph_limits: PackageGraphLimits,
        id_limits: IdIndexLimits,
        writer_limits: WriterLimits,
    ) -> Result<PackageArtifact, WriterError> {
        build_artifact(
            patch,
            WriterMode::Preserving,
            package_limits,
            graph_limits,
            id_limits,
            writer_limits,
        )
    }
}

#[derive(Debug)]
pub struct NormalizedWriter;

impl NormalizedWriter {
    /// Explicitly repackages a fully-owned P03-07 artifact with canonical order, fixed timestamp,
    /// pinned compression method and level. It never runs implicitly in preserving mode.
    ///
    /// # Errors
    ///
    /// Returns no artifact unless the output fully reopens through the package trust chain.
    pub fn build(
        patch: &PatchResult,
        package_limits: PackageLimits,
        graph_limits: PackageGraphLimits,
        id_limits: IdIndexLimits,
        writer_limits: WriterLimits,
    ) -> Result<PackageArtifact, WriterError> {
        build_artifact(
            patch,
            WriterMode::Normalized,
            package_limits,
            graph_limits,
            id_limits,
            writer_limits,
        )
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct PublicationReceipt {
    output_relative: PathBuf,
    mode: WriterMode,
    size_bytes: u64,
    sha256: [u8; 32],
    staged_reopen_verified: bool,
    published_reopen_verified: bool,
}

impl PublicationReceipt {
    #[must_use]
    pub fn output_relative(&self) -> &Path {
        &self.output_relative
    }

    #[must_use]
    pub const fn mode(&self) -> WriterMode {
        self.mode
    }

    #[must_use]
    pub const fn size_bytes(&self) -> u64 {
        self.size_bytes
    }

    #[must_use]
    pub const fn sha256(&self) -> [u8; 32] {
        self.sha256
    }

    #[must_use]
    pub const fn staged_reopen_verified(&self) -> bool {
        self.staged_reopen_verified
    }

    #[must_use]
    pub const fn published_reopen_verified(&self) -> bool {
        self.published_reopen_verified
    }
}

#[derive(Debug)]
pub struct AtomicPackagePublisher;

impl AtomicPackagePublisher {
    /// Publishes through secure create-new staging, file sync, staged reopen, same-volume atomic
    /// no-overwrite link, and published readback.
    ///
    /// # Errors
    ///
    /// Before publication, failures discard the individual staged artifact. After atomic
    /// visibility, readback failures return an explicit ambiguous receipt error and never delete
    /// the complete destination.
    pub fn publish(
        artifact: &PackageArtifact,
        workspace: &SecureWorkspace,
        staging_relative: &Path,
        output_relative: &Path,
    ) -> Result<PublicationReceipt, WriterError> {
        publish_with_hook(
            artifact,
            workspace,
            staging_relative,
            output_relative,
            |_| Ok(()),
        )
    }
}

#[derive(Debug, Error)]
pub enum WriterError {
    #[error("bounded package validation failed while writing")]
    Package(#[from] PackageError),
    #[error("package graph validation failed while writing")]
    Graph(#[from] GraphError),
    #[error("preservation validation failed while writing")]
    Preservation(#[from] PreservationError),
    #[error("ID/reference validation failed while writing")]
    IdIndex(#[from] IdIndexError),
    #[error("patch artifact validation failed while writing")]
    Patch(#[from] PatchError),
    #[error("secure workspace operation failed while writing")]
    Workspace(#[from] WorkspaceError),
    #[error("invalid writer limit {field}: {value} (ceiling {ceiling})")]
    InvalidLimit {
        field: &'static str,
        value: u64,
        ceiling: u64,
    },
    #[error("writer output exceeded the configured limit")]
    OutputLimitExceeded,
    #[error("private writer artifact differs from its evidence")]
    ArtifactMismatch,
    #[error("ZIP construction failed")]
    ZipConstruction,
    #[error("staged artifact hash or size differs before publication")]
    StagedIdentityMismatch,
    #[error("unpublished staged artifact cleanup failed")]
    StagingCleanupFailed,
    #[error("artifact is visible but publication durability or staging cleanup is incomplete")]
    PublishedIncomplete,
    #[error("published artifact readback failed at {stage}")]
    PublishedReadback { stage: &'static str },
    #[error("writer failure was injected at a deterministic checkpoint")]
    FaultInjected,
}

impl WriterError {
    #[must_use]
    pub fn code(&self) -> &'static str {
        match self {
            Self::Package(error) => error.code(),
            Self::Graph(error) => error.code(),
            Self::Preservation(error) => error.code(),
            Self::IdIndex(error) => error.code(),
            Self::Patch(error) => error.code(),
            Self::Workspace(WorkspaceError::ArtifactExists) => "writer_output_exists",
            Self::Workspace(WorkspaceError::ArtifactPublishedIncomplete)
            | Self::PublishedIncomplete => "writer_published_incomplete",
            Self::Workspace(_) => "writer_workspace_failed",
            Self::InvalidLimit { .. } => "writer_invalid_limit",
            Self::OutputLimitExceeded => "writer_output_limit_exceeded",
            Self::ArtifactMismatch => "writer_artifact_mismatch",
            Self::ZipConstruction => "writer_zip_construction_failed",
            Self::StagedIdentityMismatch => "writer_staged_identity_mismatch",
            Self::StagingCleanupFailed => "writer_staging_cleanup_failed",
            Self::PublishedReadback { .. } => "writer_published_readback_failed",
            Self::FaultInjected => "writer_fault_injected",
        }
    }
}

fn build_artifact(
    patch: &PatchResult,
    mode: WriterMode,
    package_limits: PackageLimits,
    graph_limits: PackageGraphLimits,
    id_limits: IdIndexLimits,
    writer_limits: WriterLimits,
) -> Result<PackageArtifact, WriterError> {
    patch.verify_artifact_integrity()?;
    if patch.parts.len() > package_limits.config().max_entries {
        return Err(WriterError::OutputLimitExceeded);
    }
    let mut total_expanded_bytes = 0_u64;
    for part in &patch.parts {
        let expanded_bytes =
            u64::try_from(part.bytes.len()).map_err(|_| WriterError::OutputLimitExceeded)?;
        if expanded_bytes > package_limits.config().max_entry_expanded_bytes {
            return Err(WriterError::OutputLimitExceeded);
        }
        total_expanded_bytes = total_expanded_bytes
            .checked_add(expanded_bytes)
            .ok_or(WriterError::OutputLimitExceeded)?;
        if total_expanded_bytes > package_limits.config().max_total_expanded_bytes {
            return Err(WriterError::OutputLimitExceeded);
        }
    }
    let mut ordered = Vec::new();
    ordered
        .try_reserve_exact(patch.parts.len())
        .map_err(|_| WriterError::ZipConstruction)?;
    ordered.extend(patch.parts.iter());
    order_parts(&mut ordered, mode);
    let output_limit = writer_limits
        .config()
        .max_output_bytes
        .min(package_limits.config().max_archive_bytes);
    let (bytes, report) = write_archive(patch, &ordered, mode, output_limit)?;
    let size = u64::try_from(bytes.len()).map_err(|_| WriterError::OutputLimitExceeded)?;
    if size > writer_limits.config().max_output_bytes
        || size > package_limits.config().max_archive_bytes
    {
        return Err(WriterError::OutputLimitExceeded);
    }
    let validation = validate_archive(
        Cursor::new(bytes.as_slice()),
        package_limits,
        graph_limits,
        patch.preservation_profile,
        patch.profile,
        id_limits,
    )?;
    if validation.parts != ordered.len()
        || validation.declarations != patch.declaration_count()
        || validation.references != patch.reference_count()
    {
        return Err(WriterError::ArtifactMismatch);
    }
    let sha256 = <[u8; 32]>::from(Sha256::digest(&bytes));
    Ok(PackageArtifact {
        mode,
        bytes: bytes.into_boxed_slice(),
        sha256,
        report,
        package_limits,
        graph_limits,
        id_limits,
        profile: patch.profile,
        preservation_profile: patch.preservation_profile,
    })
}

fn order_parts(parts: &mut Vec<&VirtualPart>, mode: WriterMode) {
    parts.sort_by(|left, right| {
        let left_mimetype = left.path.as_str() == "mimetype";
        let right_mimetype = right.path.as_str() == "mimetype";
        right_mimetype.cmp(&left_mimetype).then_with(|| match mode {
            WriterMode::Preserving => left
                .source_order
                .cmp(&right.source_order)
                .then_with(|| left.path.cmp(&right.path)),
            WriterMode::Normalized => left.path.cmp(&right.path),
        })
    });
}

fn write_archive(
    patch: &PatchResult,
    ordered: &[&VirtualPart],
    mode: WriterMode,
    output_limit: u64,
) -> Result<(Vec<u8>, WriterReport), WriterError> {
    let mut writer = ZipWriter::new(BoundedArchiveBuffer::new(output_limit));
    let disposition_by_path = patch
        .parts()
        .iter()
        .map(|record| (record.path().as_str(), record.disposition()))
        .collect::<std::collections::BTreeMap<_, _>>();
    let mut records = Vec::new();
    records
        .try_reserve_exact(ordered.len())
        .map_err(|_| WriterError::ZipConstruction)?;
    for (output_order, part) in ordered.iter().enumerate() {
        let output_compression = output_compression(part, mode);
        let options = zip_options(output_compression);
        writer
            .start_file(part.path.as_str(), options)
            .map_err(|error| map_zip_error(&error))?;
        writer
            .write_all(&part.bytes)
            .map_err(|error| map_buffer_error(&error))?;
        records.push(WriterEntryRecord {
            path: part.path.clone(),
            disposition: disposition_by_path
                .get(part.path.as_str())
                .copied()
                .ok_or(WriterError::ArtifactMismatch)?,
            source_order: part.source_sha256.map(|_| part.source_order),
            output_order,
            source_compression: part.source_sha256.map(|_| part.compression),
            output_compression,
            expanded_sha256: <[u8; 32]>::from(Sha256::digest(&part.bytes)),
        });
    }
    let buffer = writer.finish().map_err(|error| map_zip_error(&error))?;
    let bytes = buffer.into_inner()?;
    let (order, compression_method) = match mode {
        WriterMode::Preserving => (
            MetadataDisposition::PreservedAvailable,
            MetadataDisposition::PreservedAvailable,
        ),
        WriterMode::Normalized => (
            MetadataDisposition::Normalized,
            MetadataDisposition::Normalized,
        ),
    };
    Ok((
        bytes,
        WriterReport {
            mode,
            entries: records,
            order,
            compression_method,
            timestamp: match mode {
                WriterMode::Preserving => MetadataDisposition::NotPreservedUnavailable,
                WriterMode::Normalized => MetadataDisposition::Normalized,
            },
            extra_fields: match mode {
                WriterMode::Preserving => MetadataDisposition::NotPreservedUnavailable,
                WriterMode::Normalized => MetadataDisposition::Normalized,
            },
            raw_compressed_stream: match mode {
                WriterMode::Preserving => MetadataDisposition::NotPreservedUnavailable,
                WriterMode::Normalized => MetadataDisposition::Normalized,
            },
        },
    ))
}

pub(crate) struct BoundedArchiveBuffer {
    bytes: Vec<u8>,
    position: u64,
    limit: u64,
    overflowed: bool,
    allocation_failed: bool,
}

impl BoundedArchiveBuffer {
    pub(crate) const fn new(limit: u64) -> Self {
        Self {
            bytes: Vec::new(),
            position: 0,
            limit,
            overflowed: false,
            allocation_failed: false,
        }
    }

    pub(crate) fn into_inner(self) -> Result<Vec<u8>, WriterError> {
        if self.allocation_failed {
            Err(WriterError::ZipConstruction)
        } else if self.overflowed {
            Err(WriterError::OutputLimitExceeded)
        } else {
            Ok(self.bytes)
        }
    }
}

impl Write for BoundedArchiveBuffer {
    fn write(&mut self, buffer: &[u8]) -> io::Result<usize> {
        let requested = u64::try_from(buffer.len()).map_err(|_| output_limit_io_error())?;
        let end = self
            .position
            .checked_add(requested)
            .ok_or_else(output_limit_io_error)?;
        let stored_end = end.min(self.limit);
        if self.position < stored_end && !self.allocation_failed {
            let start = usize::try_from(self.position).map_err(|_| output_limit_io_error())?;
            let end_index = usize::try_from(stored_end).map_err(|_| output_limit_io_error())?;
            if end_index > self.bytes.len() {
                if self
                    .bytes
                    .try_reserve(end_index - self.bytes.len())
                    .is_err()
                {
                    self.allocation_failed = true;
                }
                if !self.allocation_failed {
                    self.bytes.resize(end_index, 0);
                }
            }
            if !self.allocation_failed {
                self.bytes[start..end_index]
                    .copy_from_slice(&buffer[..end_index.saturating_sub(start)]);
            }
        }
        self.overflowed |= end > self.limit;
        self.position = end;
        Ok(buffer.len())
    }

    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}

impl Seek for BoundedArchiveBuffer {
    fn seek(&mut self, position: SeekFrom) -> io::Result<u64> {
        let next = match position {
            SeekFrom::Start(offset) => Some(offset),
            SeekFrom::End(offset) => checked_seek_offset(
                u64::try_from(self.bytes.len()).map_err(|_| output_limit_io_error())?,
                offset,
            ),
            SeekFrom::Current(offset) => checked_seek_offset(self.position, offset),
        }
        .ok_or_else(output_limit_io_error)?;
        self.overflowed |= next > self.limit;
        self.position = next;
        Ok(next)
    }
}

fn checked_seek_offset(base: u64, offset: i64) -> Option<u64> {
    if offset >= 0 {
        base.checked_add(offset.unsigned_abs())
    } else {
        base.checked_sub(offset.unsigned_abs())
    }
}

fn output_limit_io_error() -> io::Error {
    io::Error::new(io::ErrorKind::FileTooLarge, "writer output limit exceeded")
}

fn map_buffer_error(error: &io::Error) -> WriterError {
    if error.kind() == io::ErrorKind::FileTooLarge {
        WriterError::OutputLimitExceeded
    } else {
        WriterError::ZipConstruction
    }
}

fn map_zip_error(error: &zip::result::ZipError) -> WriterError {
    if matches!(error, zip::result::ZipError::Io(error) if error.kind() == io::ErrorKind::FileTooLarge)
    {
        WriterError::OutputLimitExceeded
    } else {
        WriterError::ZipConstruction
    }
}

fn output_compression(part: &VirtualPart, mode: WriterMode) -> Compression {
    match mode {
        WriterMode::Preserving => part.compression,
        WriterMode::Normalized if part.path.as_str() == "mimetype" => Compression::Stored,
        WriterMode::Normalized => Compression::Deflated,
    }
}

fn zip_options(compression: Compression) -> SimpleFileOptions {
    let method = match compression {
        Compression::Stored => CompressionMethod::Stored,
        Compression::Deflated => CompressionMethod::Deflated,
    };
    let options = SimpleFileOptions::default()
        .compression_method(method)
        .last_modified_time(DateTime::default())
        .system(System::Unix)
        .unix_permissions(0o644);
    if compression == Compression::Deflated {
        options.compression_level(Some(NORMALIZED_DEFLATE_LEVEL))
    } else {
        options
    }
}

#[cfg_attr(test, derive(Debug, Eq, PartialEq))]
struct ValidationCounts {
    parts: usize,
    declarations: usize,
    references: usize,
}

/// Same original writer trust chain for a newly derived note-only package.
/// Not an authorization, signature, Native or publication attestation.
pub(crate) fn validate_note_export_archive(bytes: &[u8], limits: PackageLimits) -> Result<(), WriterError> {
    validate_archive(Cursor::new(bytes), limits, PackageGraphLimits::default(),
        PreservationRuleProfile::Hangul2020PreviewTextV2, IdRuleProfile::hwpml_2011_shape_v6(),
        IdIndexLimits::default()).map(|_| ())
}

fn validate_archive<R: Read + Seek>(
    source: R,
    package_limits: PackageLimits,
    graph_limits: PackageGraphLimits,
    preservation_profile: PreservationRuleProfile,
    profile: IdRuleProfile,
    id_limits: IdIndexLimits,
) -> Result<ValidationCounts, WriterError> {
    let mut reader = BoundedZipReader::open(source, package_limits)?;
    let graph = PackageGraph::build(&mut reader, graph_limits)?;
    // One archive validation only. Keep fresh bounded reads, CRC/size/profile
    // and whole-byte comparisons; never retain source or authorization across calls.
    let mut documents = crate::call_local_xml::CallLocalXmlDocuments::default();
    let preservation = PreservationReport::build_with_call_local_xml(
        &mut reader,
        &graph,
        graph_limits,
        preservation_profile,
        &mut documents,
    )?;
    if !preservation.direct_preserve_ready() {
        return Err(WriterError::ArtifactMismatch);
    }
    let index = IdIndex::build_with_call_local_xml(
        &mut reader,
        &graph,
        graph_limits,
        profile,
        id_limits,
        &mut documents,
    )?;
    Ok(ValidationCounts {
        parts: preservation.parts().len(),
        declarations: index.declarations().len(),
        references: index.references().len(),
    })
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum PublicationCheckpoint {
    AfterStageSync,
    AfterStagedReadback,
    BeforeAtomicPublish,
    AfterAtomicPublish,
    AfterPublishedReadback,
}

fn publish_with_hook(
    artifact: &PackageArtifact,
    workspace: &SecureWorkspace,
    staging_relative: &Path,
    output_relative: &Path,
    mut checkpoint: impl FnMut(PublicationCheckpoint) -> Result<(), WriterError>,
) -> Result<PublicationReceipt, WriterError> {
    artifact.verify()?;
    let staged = workspace.stage_bytes(staging_relative, &artifact.bytes)?;
    if let Err(error) = checkpoint(PublicationCheckpoint::AfterStageSync) {
        return fail_unpublished(workspace, &staged, error);
    }
    if let Err(error) = validate_staged(artifact, workspace, &staged) {
        return fail_unpublished(workspace, &staged, error);
    }
    if let Err(error) = checkpoint(PublicationCheckpoint::AfterStagedReadback) {
        return fail_unpublished(workspace, &staged, error);
    }
    if let Err(error) = checkpoint(PublicationCheckpoint::BeforeAtomicPublish) {
        return fail_unpublished(workspace, &staged, error);
    }
    let published = match workspace.publish(&staged, output_relative) {
        Ok(path) => path,
        Err(WorkspaceError::ArtifactPublishedIncomplete) => {
            return Err(WriterError::PublishedIncomplete);
        }
        Err(error) => return fail_unpublished(workspace, &staged, WriterError::Workspace(error)),
    };
    checkpoint(PublicationCheckpoint::AfterAtomicPublish)?;
    validate_published(artifact, &published)?;
    checkpoint(PublicationCheckpoint::AfterPublishedReadback)?;
    Ok(PublicationReceipt {
        output_relative: output_relative.to_path_buf(),
        mode: artifact.mode,
        size_bytes: u64::try_from(artifact.bytes.len())
            .map_err(|_| WriterError::ArtifactMismatch)?,
        sha256: artifact.sha256,
        staged_reopen_verified: true,
        published_reopen_verified: true,
    })
}

fn validate_staged(
    artifact: &PackageArtifact,
    workspace: &SecureWorkspace,
    staged: &StagedArtifact,
) -> Result<(), WriterError> {
    if staged.size_bytes
        != u64::try_from(artifact.bytes.len()).map_err(|_| WriterError::StagedIdentityMismatch)?
    {
        return Err(WriterError::StagedIdentityMismatch);
    }
    let mut source = workspace.open_staged(staged)?;
    if hash_and_rewind(&mut source)? != artifact.sha256 {
        return Err(WriterError::StagedIdentityMismatch);
    }
    validate_archive(
        source,
        artifact.package_limits,
        artifact.graph_limits,
        artifact.preservation_profile,
        artifact.profile,
        artifact.id_limits,
    )?;
    Ok(())
}

fn validate_published(artifact: &PackageArtifact, published: &Path) -> Result<(), WriterError> {
    let mut source =
        File::open(published).map_err(|_| WriterError::PublishedReadback { stage: "open" })?;
    let digest = hash_and_rewind(&mut source)
        .map_err(|_| WriterError::PublishedReadback { stage: "hash" })?;
    if digest != artifact.sha256 {
        return Err(WriterError::PublishedReadback { stage: "identity" });
    }
    validate_archive(
        source,
        artifact.package_limits,
        artifact.graph_limits,
        artifact.preservation_profile,
        artifact.profile,
        artifact.id_limits,
    )
    .map_err(|_| WriterError::PublishedReadback { stage: "reopen" })?;
    Ok(())
}

fn hash_and_rewind<R: Read + Seek>(source: &mut R) -> Result<[u8; 32], WriterError> {
    source
        .seek(SeekFrom::Start(0))
        .map_err(|_| WriterError::StagedIdentityMismatch)?;
    let mut hasher = Sha256::new();
    let mut buffer = [0_u8; 16 * 1024];
    loop {
        let read = source
            .read(&mut buffer)
            .map_err(|_| WriterError::StagedIdentityMismatch)?;
        if read == 0 {
            break;
        }
        hasher.update(&buffer[..read]);
    }
    source
        .seek(SeekFrom::Start(0))
        .map_err(|_| WriterError::StagedIdentityMismatch)?;
    Ok(<[u8; 32]>::from(hasher.finalize()))
}

fn fail_unpublished<T>(
    workspace: &SecureWorkspace,
    staged: &StagedArtifact,
    error: WriterError,
) -> Result<T, WriterError> {
    workspace
        .discard_staged(staged)
        .map_err(|_| WriterError::StagingCleanupFailed)?;
    Err(error)
}

#[cfg(test)]
mod tests {
    use std::io::Cursor;

    use tempfile::tempdir;
    use zip::write::SimpleFileOptions;

    use super::*;

    const CONTAINER: &str = r#"<?xml version="1.0" encoding="UTF-8"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">
  <rootfiles><rootfile full-path="Contents/content.hpf" media-type="application/oebps-package+xml"/></rootfiles>
</container>"#;

    const OPF: &str = r#"<?xml version="1.0" encoding="UTF-8"?>
<o:package xmlns:o="http://www.idpf.org/2007/opf/" id="pkg" version="2.0">
  <o:manifest><o:item id="section0" href="section0.xml" media-type="application/xml"/></o:manifest>
  <o:spine><o:itemref idref="section0" linear="yes"/></o:spine>
</o:package>"#;

    const SECTION: &str = r#"<q:section xmlns:q="http://www.hancom.co.kr/hwpml/2011/paragraph"/>"#;

    #[test]
    fn checkpoint_failures_leave_destination_absent_or_complete() {
        let artifact = artifact().unwrap_or_else(|error| panic!("artifact: {error}"));
        let source_hash = artifact.sha256;
        for checkpoint in [
            PublicationCheckpoint::AfterStageSync,
            PublicationCheckpoint::AfterStagedReadback,
            PublicationCheckpoint::BeforeAtomicPublish,
        ] {
            let temporary = tempdir().unwrap_or_else(|error| panic!("tempdir: {error}"));
            let workspace = SecureWorkspace::create(temporary.path().join("work"))
                .unwrap_or_else(|error| panic!("workspace: {error}"));
            let result = publish_with_hook(
                &artifact,
                &workspace,
                Path::new("job/artifact.hwpx"),
                Path::new("artifact.hwpx"),
                |actual| {
                    if actual == checkpoint {
                        Err(WriterError::FaultInjected)
                    } else {
                        Ok(())
                    }
                },
            );
            assert!(matches!(result, Err(WriterError::FaultInjected)));
            assert!(!temporary.path().join("work/output/artifact.hwpx").exists());
            assert!(
                !temporary
                    .path()
                    .join("work/staging/job/artifact.hwpx")
                    .exists()
            );
            assert_eq!(artifact.sha256, source_hash);
        }

        for checkpoint in [
            PublicationCheckpoint::AfterAtomicPublish,
            PublicationCheckpoint::AfterPublishedReadback,
        ] {
            let temporary = tempdir().unwrap_or_else(|error| panic!("tempdir: {error}"));
            let workspace = SecureWorkspace::create(temporary.path().join("work"))
                .unwrap_or_else(|error| panic!("workspace: {error}"));
            let result = publish_with_hook(
                &artifact,
                &workspace,
                Path::new("job/artifact.hwpx"),
                Path::new("artifact.hwpx"),
                |actual| {
                    if actual == checkpoint {
                        Err(WriterError::FaultInjected)
                    } else {
                        Ok(())
                    }
                },
            );
            assert!(matches!(result, Err(WriterError::FaultInjected)));
            let output = temporary.path().join("work/output/artifact.hwpx");
            let bytes = std::fs::read(output)
                .unwrap_or_else(|error| panic!("read complete output: {error}"));
            assert_eq!(<[u8; 32]>::from(Sha256::digest(&bytes)), source_hash);
            validate_archive(
                Cursor::new(bytes),
                PackageLimits::default(),
                PackageGraphLimits::default(),
                PreservationRuleProfile::CoreV1,
                IdRuleProfile::current_hancom_2020_core_v1(),
                IdIndexLimits::default(),
            )
            .unwrap_or_else(|error| panic!("reopen complete output: {error}"));
        }
    }

    fn artifact() -> Result<PackageArtifact, WriterError> {
        let bytes = minimal_archive()?;
        validate_archive(
            Cursor::new(bytes.as_slice()),
            PackageLimits::default(),
            PackageGraphLimits::default(),
            PreservationRuleProfile::CoreV1,
            IdRuleProfile::current_hancom_2020_core_v1(),
            IdIndexLimits::default(),
        )?;
        let sha256 = <[u8; 32]>::from(Sha256::digest(&bytes));
        Ok(PackageArtifact {
            mode: WriterMode::Preserving,
            bytes: bytes.into_boxed_slice(),
            sha256,
            report: WriterReport {
                mode: WriterMode::Preserving,
                entries: Vec::new(),
                order: MetadataDisposition::PreservedAvailable,
                compression_method: MetadataDisposition::PreservedAvailable,
                timestamp: MetadataDisposition::NotPreservedUnavailable,
                extra_fields: MetadataDisposition::NotPreservedUnavailable,
                raw_compressed_stream: MetadataDisposition::NotPreservedUnavailable,
            },
            package_limits: PackageLimits::default(),
            graph_limits: PackageGraphLimits::default(),
            id_limits: IdIndexLimits::default(),
            profile: IdRuleProfile::current_hancom_2020_core_v1(),
            preservation_profile: PreservationRuleProfile::CoreV1,
        })
    }

    fn minimal_archive() -> Result<Vec<u8>, WriterError> {
        let cursor = Cursor::new(Vec::new());
        let mut writer = ZipWriter::new(cursor);
        for (path, bytes, compression) in [
            (
                "mimetype",
                b"application/hwp+zip".as_slice(),
                CompressionMethod::Stored,
            ),
            (
                "version.xml",
                b"<version/>".as_slice(),
                CompressionMethod::Stored,
            ),
            (
                "META-INF/container.xml",
                CONTAINER.as_bytes(),
                CompressionMethod::Deflated,
            ),
            (
                "Contents/content.hpf",
                OPF.as_bytes(),
                CompressionMethod::Deflated,
            ),
            (
                "Contents/section0.xml",
                SECTION.as_bytes(),
                CompressionMethod::Deflated,
            ),
        ] {
            writer
                .start_file(
                    path,
                    SimpleFileOptions::default().compression_method(compression),
                )
                .map_err(|_| WriterError::ZipConstruction)?;
            writer
                .write_all(bytes)
                .map_err(|_| WriterError::ZipConstruction)?;
        }
        writer
            .finish()
            .map(Cursor::into_inner)
            .map_err(|_| WriterError::ZipConstruction)
    }
}

// P168 writer call-local XML regression oracles; no product authority.
#[cfg(test)]
#[path = "../tests/support/document_import_settings_inputs.rs"]
mod writer_xml_reuse_inputs;

#[cfg(test)]
mod writer_xml_reuse_tests {
    use super::*;
    use std::{
        cell::{Cell, RefCell},
        io::SeekFrom,
        rc::Rc,
    };

    #[derive(Default, Debug, Eq, PartialEq)]
    struct Reads {
        calls: usize,
        bytes: usize,
        seeks: usize,
    }

    struct ObservedCursor<'a> {
        inner: Cursor<&'a [u8]>,
        reads: Rc<RefCell<Reads>>,
    }
    impl Read for ObservedCursor<'_> {
        fn read(&mut self, buffer: &mut [u8]) -> io::Result<usize> {
            let count = self.inner.read(buffer)?;
            let mut reads = self.reads.borrow_mut();
            reads.calls += 1;
            reads.bytes += count;
            Ok(count)
        }
    }
    impl Seek for ObservedCursor<'_> {
        fn seek(&mut self, position: SeekFrom) -> io::Result<u64> {
            self.reads.borrow_mut().seeks += 1;
            self.inner.seek(position)
        }
    }

    // Exact original validation body, retained only as an independent test oracle.
    fn validate_archive_original<R: Read + Seek>(
        source: R,
        package_limits: PackageLimits,
        graph_limits: PackageGraphLimits,
        preservation_profile: PreservationRuleProfile,
        profile: IdRuleProfile,
        id_limits: IdIndexLimits,
    ) -> Result<ValidationCounts, WriterError> {
        let mut reader = BoundedZipReader::open(source, package_limits)?;
        let graph = PackageGraph::build(&mut reader, graph_limits)?;
        let preservation = PreservationReport::build_with_graph_limits_and_profile(
            &mut reader,
            &graph,
            graph_limits,
            preservation_profile,
        )?;
        if !preservation.direct_preserve_ready() {
            return Err(WriterError::ArtifactMismatch);
        }
        let index = IdIndex::build_with_graph_limits(
            &mut reader,
            &graph,
            graph_limits,
            profile,
            id_limits,
        )?;
        Ok(ValidationCounts {
            parts: preservation.parts().len(),
            declarations: index.declarations().len(),
            references: index.references().len(),
        })
    }

    fn same_result(
        expected: Result<ValidationCounts, WriterError>,
        actual: Result<ValidationCounts, WriterError>,
    ) -> bool {
        match (expected, actual) {
            (Ok(expected), Ok(actual)) => {
                assert_eq!(actual, expected);
                true
            }
            (Err(expected), Err(actual)) => {
                assert_eq!(actual.code(), expected.code());
                if let (WriterError::IdIndex(expected), WriterError::IdIndex(actual)) =
                    (&expected, &actual)
                {
                    assert!(
                        actual.validation() == expected.validation(),
                        "whole ID denial evidence differs"
                    );
                }
                false
            }
            _ => panic!("original Writer acceptance/denial differs"),
        }
    }

    #[test]
    fn all36_original_writer_verdicts_counts_and_fresh_reads_match_both_profiles()
    -> Result<(), Box<dyn std::error::Error>> {
        let mut count = 0;
        for bytes in super::writer_xml_reuse_inputs::actual_corpus()? {
            for (preservation, profile) in [
                (
                    PreservationRuleProfile::CoreV1,
                    IdRuleProfile::current_hancom_2020_core_v1(),
                ),
                (
                    PreservationRuleProfile::Hangul2020PreviewTextV2,
                    IdRuleProfile::current_hancom_2020_formula_v3(),
                ),
            ] {
                let plain_reads = Rc::new(RefCell::new(Reads::default()));
                let shared_reads = Rc::new(RefCell::new(Reads::default()));
                let expected = validate_archive_original(
                    ObservedCursor {
                        inner: Cursor::new(&bytes),
                        reads: plain_reads.clone(),
                    },
                    PackageLimits::default(),
                    PackageGraphLimits::default(),
                    preservation,
                    profile,
                    IdIndexLimits::default(),
                );
                let actual = validate_archive(
                    ObservedCursor {
                        inner: Cursor::new(&bytes),
                        reads: shared_reads.clone(),
                    },
                    PackageLimits::default(),
                    PackageGraphLimits::default(),
                    preservation,
                    profile,
                    IdIndexLimits::default(),
                );
                same_result(expected, actual);
                assert_eq!(*plain_reads.borrow(), *shared_reads.borrow());
            }
            count += 1;
        }
        assert_eq!(count, 36);
        Ok(())
    }

    fn package(section: &[u8]) -> Result<Vec<u8>, WriterError> {
        let container = br#"<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="Contents/content.hpf" media-type="application/oebps-package+xml"/></rootfiles></container>"#;
        let opf = br#"<o:package xmlns:o="http://www.idpf.org/2007/opf/" id="pkg" version="2.0"><o:manifest><o:item id="section0" href="section0.xml" media-type="application/xml"/></o:manifest><o:spine><o:itemref idref="section0" linear="yes"/></o:spine></o:package>"#;
        let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
        for (path, bytes) in [
            ("mimetype", b"application/hwp+zip".as_slice()),
            ("version.xml", b"<version/>".as_slice()),
            ("META-INF/container.xml", container.as_slice()),
            ("Contents/content.hpf", opf.as_slice()),
            ("Contents/section0.xml", section),
        ] {
            writer
                .start_file(
                    path,
                    SimpleFileOptions::default().compression_method(CompressionMethod::Stored),
                )
                .map_err(|_| WriterError::ZipConstruction)?;
            writer
                .write_all(bytes)
                .map_err(|_| WriterError::ZipConstruction)?;
        }
        writer
            .finish()
            .map(Cursor::into_inner)
            .map_err(|_| WriterError::ZipConstruction)
    }

    #[test]
    fn invalid_xml_dangling_reference_and_truncated_archive_keep_original_denial() {
        let mut inputs = Vec::new();
        for section in [
            b"<broken>".as_slice(),
            br#"<!DOCTYPE section><section/>"#,
            br#"<q:section xmlns:q="http://www.hancom.co.kr/hwpml/2011/paragraph"><q:p id="10" paraPrIDRef="999"/></q:section>"#,
        ] { inputs.push(package(section).unwrap()); }
        let truncated = package(b"<section/>").unwrap();
        inputs.push(truncated[..truncated.len() / 2].to_vec());
        for bytes in inputs {
            let expected = validate_archive_original(
                Cursor::new(&bytes),
                PackageLimits::default(),
                PackageGraphLimits::default(),
                PreservationRuleProfile::CoreV1,
                IdRuleProfile::current_hancom_2020_core_v1(),
                IdIndexLimits::default(),
            );
            let actual = validate_archive(
                Cursor::new(&bytes),
                PackageLimits::default(),
                PackageGraphLimits::default(),
                PreservationRuleProfile::CoreV1,
                IdRuleProfile::current_hancom_2020_core_v1(),
                IdIndexLimits::default(),
            );
            assert!(
                !same_result(expected, actual),
                "hostile package unexpectedly accepted"
            );
        }
    }

    #[test]
    fn successful_prior_artifact_read_never_authorizes_changed_bytes_callback() {
        let bytes =
            package(br#"<q:section xmlns:q="http://www.hancom.co.kr/hwpml/2011/paragraph"/>"#)
                .unwrap();
        let mut artifact = PackageArtifact {
            mode: WriterMode::Preserving,
            sha256: Sha256::digest(&bytes).into(),
            bytes: bytes.into_boxed_slice(),
            report: WriterReport {
                mode: WriterMode::Preserving,
                entries: Vec::new(),
                order: MetadataDisposition::PreservedAvailable,
                compression_method: MetadataDisposition::PreservedAvailable,
                timestamp: MetadataDisposition::NotPreservedUnavailable,
                extra_fields: MetadataDisposition::NotPreservedUnavailable,
                raw_compressed_stream: MetadataDisposition::NotPreservedUnavailable,
            },
            package_limits: PackageLimits::default(),
            graph_limits: PackageGraphLimits::default(),
            id_limits: IdIndexLimits::default(),
            profile: IdRuleProfile::current_hancom_2020_core_v1(),
            preservation_profile: PreservationRuleProfile::CoreV1,
        };
        artifact.with_verified_bytes(|_| ()).unwrap();
        let callback_called = Cell::new(false);
        artifact.bytes[0] ^= 1;
        let error = artifact
            .with_verified_bytes(|_| callback_called.set(true))
            .unwrap_err();
        assert_eq!(error.code(), "writer_artifact_mismatch");
        assert!(!callback_called.get());
    }
}
