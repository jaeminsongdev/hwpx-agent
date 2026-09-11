use std::collections::BTreeSet;
use std::io::{Read, Seek, SeekFrom};

use thiserror::Error;
use zip::{CompressionMethod, ZipArchive};

use crate::path::insert_unique_path;
use crate::{PackageLimits, PackagePath};

const EOCD_SIGNATURE: [u8; 4] = *b"PK\x05\x06";
const LOCAL_SIGNATURE: [u8; 4] = *b"PK\x03\x04";
const CENTRAL_SIGNATURE: [u8; 4] = *b"PK\x01\x02";
const EOCD_FIXED: usize = 22;
const LOCAL_FIXED: usize = 30;
const CENTRAL_FIXED: usize = 46;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Compression {
    Stored,
    Deflated,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct EntryMetadata {
    pub index: usize,
    pub path: PackagePath,
    pub compression: Compression,
    pub compressed_size: u64,
    pub expanded_size: u64,
    pub crc32: u32,
}

#[derive(Debug, Error)]
pub enum PackageError {
    #[error("invalid finite package limit for {field}: {value} (ceiling {ceiling})")]
    InvalidLimit {
        field: &'static str,
        value: u64,
        ceiling: u64,
    },
    #[error("per-entry expanded limit cannot exceed total expanded limit")]
    InvalidLimitRelation,
    #[error("archive I/O failed")]
    Io(#[source] std::io::Error),
    #[error("ZIP structure is invalid")]
    InvalidZip,
    #[error("archive contains an unexpected leading structure")]
    UnexpectedPreamble,
    #[error("archive contains trailing bytes after EOCD")]
    UnexpectedTrailingData,
    #[error("multi-disk ZIP is not supported")]
    MultiDiskUnsupported,
    #[error("ZIP64 is not supported by the bounded HWPX profile")]
    Zip64Unsupported,
    #[error("archive size {actual} exceeds {limit}")]
    ArchiveTooLarge { actual: u64, limit: u64 },
    #[error("archive has {actual} entries, limit {limit}")]
    TooManyEntries { actual: usize, limit: usize },
    #[error("archive contains no entries")]
    EmptyArchive,
    #[error("archive comment exceeds configured limit")]
    CommentTooLarge,
    #[error("entry {entry_index} name length {actual} is outside limit {limit}")]
    InvalidNameLength {
        entry_index: usize,
        actual: usize,
        limit: usize,
    },
    #[error("entry {entry_index} name is not UTF-8")]
    NameNotUtf8 { entry_index: usize },
    #[error("entry {entry_index} name contains a control character")]
    NameControlCharacter { entry_index: usize },
    #[error("entry {entry_index} name contains a backslash")]
    NameBackslash { entry_index: usize },
    #[error("entry {entry_index} name is absolute")]
    NameAbsolute { entry_index: usize },
    #[error("entry {entry_index} name contains an empty component")]
    NameEmptyComponent { entry_index: usize },
    #[error("entry {entry_index} name contains a dot traversal component")]
    NameTraversal { entry_index: usize },
    #[error("entry {entry_index} path depth {actual} exceeds {limit}")]
    PathTooDeep {
        entry_index: usize,
        actual: usize,
        limit: usize,
    },
    #[error("entry {entry_index} name has an ambiguous Windows suffix")]
    NameAmbiguousSuffix { entry_index: usize },
    #[error("entry {entry_index} name contains a drive or stream separator")]
    NameDriveOrStream { entry_index: usize },
    #[error("entry {entry_index} name is reserved on Windows")]
    NameReserved { entry_index: usize },
    #[error("entry {entry_index} collides after NFC and Unicode case folding")]
    NameCollision { entry_index: usize },
    #[error("entry {entry_index} is encrypted")]
    EncryptedEntry { entry_index: usize },
    #[error("entry {entry_index} uses an unsupported compression method")]
    UnsupportedCompression { entry_index: usize },
    #[error("entry {entry_index} is a symbolic link or unsupported special file")]
    UnsupportedFileType { entry_index: usize },
    #[error("entry {entry_index} uses a data descriptor")]
    DataDescriptorUnsupported { entry_index: usize },
    #[error("entry {entry_index} uses unsupported general-purpose flags")]
    UnsupportedFlags { entry_index: usize },
    #[error("entry {entry_index} extra field exceeds configured limit")]
    ExtraFieldTooLarge { entry_index: usize },
    #[error("entry {entry_index} header metadata is inconsistent")]
    HeaderMismatch { entry_index: usize },
    #[error("entry {entry_index} range is outside the bounded archive")]
    EntryRangeInvalid { entry_index: usize },
    #[error("entry data ranges overlap")]
    OverlappingEntries,
    #[error("entry {entry_index} expanded size {actual} exceeds {limit}")]
    EntryExpandedTooLarge {
        entry_index: usize,
        actual: u64,
        limit: u64,
    },
    #[error("total expanded size {actual} exceeds {limit}")]
    TotalExpandedTooLarge { actual: u64, limit: u64 },
    #[error("entry {entry_index} compression ratio exceeds {limit}")]
    CompressionRatioExceeded { entry_index: usize, limit: u64 },
    #[error("archive-wide compression ratio exceeds {limit}")]
    TotalCompressionRatioExceeded { limit: u64 },
    #[error("entry {entry_index} is a nested archive")]
    NestedArchive { entry_index: usize },
    #[error("entry {entry_index} is a directory")]
    EntryIsDirectory { entry_index: usize },
    #[error("entry {entry_index} failed CRC or decompression integrity validation")]
    EntryIntegrity { entry_index: usize },
    #[error("entry {entry_index} output allocation failed within the configured bound")]
    AllocationFailed { entry_index: usize },
    #[error("bounded ZIP metadata allocation failed")]
    MetadataAllocationFailed,
    #[error("entry {entry_index} streamed size differs from declared size")]
    EntrySizeMismatch { entry_index: usize },
    #[error("entry index is outside the archive")]
    EntryIndexOutOfRange,
}

impl PackageError {
    /// Stable machine-readable failure code. It intentionally excludes archive
    /// names and other untrusted input.
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit { .. } => "invalid_limit",
            Self::InvalidLimitRelation => "invalid_limit_relation",
            Self::Io(_) => "io_error",
            Self::InvalidZip => "invalid_zip",
            Self::UnexpectedPreamble => "unexpected_preamble",
            Self::UnexpectedTrailingData => "unexpected_trailing_data",
            Self::MultiDiskUnsupported => "multi_disk_unsupported",
            Self::Zip64Unsupported => "zip64_unsupported",
            Self::ArchiveTooLarge { .. } => "archive_too_large",
            Self::TooManyEntries { .. } => "too_many_entries",
            Self::EmptyArchive => "empty_archive",
            Self::CommentTooLarge => "comment_too_large",
            Self::InvalidNameLength { .. } => "invalid_name_length",
            Self::NameNotUtf8 { .. } => "name_not_utf8",
            Self::NameControlCharacter { .. } => "name_control_character",
            Self::NameBackslash { .. } => "name_backslash",
            Self::NameAbsolute { .. } => "name_absolute",
            Self::NameEmptyComponent { .. } => "name_empty_component",
            Self::NameTraversal { .. } => "name_traversal",
            Self::PathTooDeep { .. } => "path_too_deep",
            Self::NameAmbiguousSuffix { .. } => "name_ambiguous_suffix",
            Self::NameDriveOrStream { .. } => "name_drive_or_stream",
            Self::NameReserved { .. } => "name_reserved",
            Self::NameCollision { .. } => "name_collision",
            Self::EncryptedEntry { .. } => "encrypted_entry",
            Self::UnsupportedCompression { .. } => "unsupported_compression",
            Self::UnsupportedFileType { .. } => "unsupported_file_type",
            Self::DataDescriptorUnsupported { .. } => "data_descriptor_unsupported",
            Self::UnsupportedFlags { .. } => "unsupported_flags",
            Self::ExtraFieldTooLarge { .. } => "extra_field_too_large",
            Self::HeaderMismatch { .. } => "header_mismatch",
            Self::EntryRangeInvalid { .. } => "entry_range_invalid",
            Self::OverlappingEntries => "overlapping_entries",
            Self::EntryExpandedTooLarge { .. } => "entry_expanded_too_large",
            Self::TotalExpandedTooLarge { .. } => "total_expanded_too_large",
            Self::CompressionRatioExceeded { .. } => "compression_ratio_exceeded",
            Self::TotalCompressionRatioExceeded { .. } => "total_compression_ratio_exceeded",
            Self::NestedArchive { .. } => "nested_archive",
            Self::EntryIsDirectory { .. } => "entry_is_directory",
            Self::EntryIntegrity { .. } => "entry_integrity",
            Self::AllocationFailed { .. } => "allocation_failed",
            Self::MetadataAllocationFailed => "metadata_allocation_failed",
            Self::EntrySizeMismatch { .. } => "entry_size_mismatch",
            Self::EntryIndexOutOfRange => "entry_index_out_of_range",
        }
    }
}

#[derive(Clone, Copy, Debug)]
struct EndRecord {
    central_offset: u64,
    central_size: u64,
    entries: usize,
    position: u64,
}

#[derive(Clone, Debug)]
struct HeaderRecord {
    local_start: u64,
    data_start: u64,
    data_end: u64,
    central_start: u64,
    raw_name: Vec<u8>,
    flags: u16,
    method: u16,
    crc32: u32,
    compressed_size: u64,
    expanded_size: u64,
}

/// Read-only bounded ZIP facade. It owns the caller's `Read + Seek` source and
/// performs no filesystem writes or extraction.
#[derive(Debug)]
pub struct BoundedZipReader<R> {
    archive: ZipArchive<R>,
    entries: Vec<EntryMetadata>,
    limits: PackageLimits,
}

impl<R: Read + Seek> BoundedZipReader<R> {
    /// Opens and validates an archive without extracting or modifying it.
    ///
    /// # Errors
    ///
    /// Returns a stable [`PackageError`] when any configured bound, portable
    /// path rule, header consistency check, or supported-format rule fails.
    pub fn open(mut reader: R, limits: PackageLimits) -> Result<Self, PackageError> {
        let archive_len = reader.seek(SeekFrom::End(0)).map_err(PackageError::Io)?;
        let config = limits.config();
        if archive_len > config.max_archive_bytes {
            return Err(PackageError::ArchiveTooLarge {
                actual: archive_len,
                limit: config.max_archive_bytes,
            });
        }
        let end = read_end_record(&mut reader, archive_len, limits)?;
        if end.entries == 0 {
            return Err(PackageError::EmptyArchive);
        }
        if end.entries > config.max_entries {
            return Err(PackageError::TooManyEntries {
                actual: end.entries,
                limit: config.max_entries,
            });
        }
        let central_end = end
            .central_offset
            .checked_add(end.central_size)
            .ok_or(PackageError::InvalidZip)?;
        if central_end != end.position {
            return Err(if central_end < end.position {
                PackageError::UnexpectedPreamble
            } else {
                PackageError::InvalidZip
            });
        }
        preflight_central_directory(&mut reader, end, limits)?;

        reader.seek(SeekFrom::Start(0)).map_err(PackageError::Io)?;
        let mut archive = ZipArchive::new(reader).map_err(|_| PackageError::InvalidZip)?;
        if archive.offset() != 0 {
            return Err(PackageError::UnexpectedPreamble);
        }
        if archive.central_directory_start() != end.central_offset || archive.len() != end.entries {
            return Err(PackageError::InvalidZip);
        }
        if archive
            .has_overlapping_files()
            .map_err(|_| PackageError::InvalidZip)?
        {
            return Err(PackageError::OverlappingEntries);
        }

        let (entries, mut headers) = collect_metadata(&mut archive, limits)?;
        let mut reader = archive.into_inner();
        validate_headers(&mut reader, &mut headers, end, limits)?;
        reader.seek(SeekFrom::Start(0)).map_err(PackageError::Io)?;
        let archive = ZipArchive::new(reader).map_err(|_| PackageError::InvalidZip)?;
        Ok(Self {
            archive,
            entries,
            limits,
        })
    }

    #[must_use]
    pub fn entries(&self) -> &[EntryMetadata] {
        &self.entries
    }

    pub(crate) const fn package_limits(&self) -> PackageLimits {
        self.limits
    }

    /// Reads one non-directory entry and publishes bytes only after streamed
    /// size, decompression, CRC, and nested-archive validation succeed.
    ///
    /// # Errors
    ///
    /// Returns a stable [`PackageError`] for an invalid index, directory,
    /// integrity failure, streamed-size violation, or nested archive.
    pub fn read_entry(&mut self, entry_index: usize) -> Result<Vec<u8>, PackageError> {
        let metadata = self
            .entries
            .get(entry_index)
            .ok_or(PackageError::EntryIndexOutOfRange)?;
        if metadata.path.is_directory() {
            return Err(PackageError::EntryIsDirectory { entry_index });
        }
        let _bounded_size = usize::try_from(metadata.expanded_size).map_err(|_| {
            PackageError::EntryExpandedTooLarge {
                entry_index,
                actual: metadata.expanded_size,
                limit: self.limits.config().max_entry_expanded_bytes,
            }
        })?;
        let mut output = Vec::new();
        let mut file = self
            .archive
            .by_index(entry_index)
            .map_err(|_| PackageError::EntryIntegrity { entry_index })?;
        let mut buffer = [0_u8; 16 * 1024];
        loop {
            let read = file
                .read(&mut buffer)
                .map_err(|_| PackageError::EntryIntegrity { entry_index })?;
            if read == 0 {
                break;
            }
            let new_len = output
                .len()
                .checked_add(read)
                .ok_or(PackageError::EntrySizeMismatch { entry_index })?;
            if u64::try_from(new_len).map_or(true, |len| {
                len > metadata.expanded_size || len > self.limits.config().max_entry_expanded_bytes
            }) {
                return Err(PackageError::EntrySizeMismatch { entry_index });
            }
            output
                .try_reserve_exact(read)
                .map_err(|_| PackageError::AllocationFailed { entry_index })?;
            output.extend_from_slice(&buffer[..read]);
        }
        if output.len() as u64 != metadata.expanded_size {
            return Err(PackageError::EntrySizeMismatch { entry_index });
        }
        if nested_signature(&output) {
            return Err(PackageError::NestedArchive { entry_index });
        }
        Ok(output)
    }
}

fn preflight_central_directory<R: Read + Seek>(
    reader: &mut R,
    end: EndRecord,
    limits: PackageLimits,
) -> Result<(), PackageError> {
    let config = limits.config();
    let mut cursor = end.central_offset;
    let mut keys = BTreeSet::new();
    let mut total_expanded = 0_u64;
    let mut total_compressed = 0_u64;
    for entry_index in 0..end.entries {
        let fixed = read_array_at::<CENTRAL_FIXED, _>(reader, cursor)?;
        if fixed[..4] != CENTRAL_SIGNATURE {
            return Err(PackageError::InvalidZip);
        }
        let flags = le_u16(&fixed[8..10]);
        let method = le_u16(&fixed[10..12]);
        validate_flags(entry_index, flags, method)?;
        let compressed = le_u32(&fixed[20..24]);
        let expanded = le_u32(&fixed[24..28]);
        let name_len = usize::from(le_u16(&fixed[28..30]));
        let extra_len = usize::from(le_u16(&fixed[30..32]));
        let comment_len = usize::from(le_u16(&fixed[32..34]));
        let local_start = le_u32(&fixed[42..46]);
        if compressed == u32::MAX || expanded == u32::MAX || local_start == u32::MAX {
            return Err(PackageError::Zip64Unsupported);
        }
        if name_len == 0 || name_len > config.max_name_bytes {
            return Err(PackageError::InvalidNameLength {
                entry_index,
                actual: name_len,
                limit: config.max_name_bytes,
            });
        }
        if extra_len > config.max_extra_field_bytes || comment_len > config.max_comment_bytes {
            return Err(PackageError::ExtraFieldTooLarge { entry_index });
        }
        let variable_len = name_len
            .checked_add(extra_len)
            .and_then(|value| value.checked_add(comment_len))
            .ok_or(PackageError::InvalidZip)?;
        let variable_start = cursor
            .checked_add(CENTRAL_FIXED as u64)
            .ok_or(PackageError::InvalidZip)?;
        let variable = read_vec_at(reader, variable_start, variable_len)?;
        let (name, remainder) = variable.split_at(name_len);
        let (extra, _) = remainder.split_at(extra_len);
        reject_zip64_extra(extra)?;
        let path = PackagePath::parse(name, entry_index, limits)?;
        insert_unique_path(&mut keys, &path, entry_index)?;
        if nested_extension(path.as_str()) {
            return Err(PackageError::NestedArchive { entry_index });
        }
        validate_sizes(
            entry_index,
            u64::from(compressed),
            u64::from(expanded),
            limits,
        )?;
        total_expanded = total_expanded.checked_add(u64::from(expanded)).ok_or(
            PackageError::TotalExpandedTooLarge {
                actual: u64::MAX,
                limit: config.max_total_expanded_bytes,
            },
        )?;
        total_compressed = total_compressed
            .checked_add(u64::from(compressed))
            .ok_or(PackageError::InvalidZip)?;
        if total_expanded > config.max_total_expanded_bytes {
            return Err(PackageError::TotalExpandedTooLarge {
                actual: total_expanded,
                limit: config.max_total_expanded_bytes,
            });
        }
        cursor = variable_start
            .checked_add(variable_len as u64)
            .ok_or(PackageError::InvalidZip)?;
    }
    if cursor != end.position {
        return Err(PackageError::InvalidZip);
    }
    validate_total_ratio(total_compressed, total_expanded, limits)
}

fn collect_metadata<R: Read + Seek>(
    archive: &mut ZipArchive<R>,
    limits: PackageLimits,
) -> Result<(Vec<EntryMetadata>, Vec<HeaderRecord>), PackageError> {
    let config = limits.config();
    let mut entries = Vec::with_capacity(archive.len());
    let mut headers = Vec::with_capacity(archive.len());
    let mut keys = BTreeSet::new();
    let mut total_expanded = 0_u64;
    let mut total_compressed = 0_u64;
    for index in 0..archive.len() {
        let file = archive
            .by_index(index)
            .map_err(|_| PackageError::InvalidZip)?;
        let path = PackagePath::parse(file.name_raw(), index, limits)?;
        insert_unique_path(&mut keys, &path, index)?;
        if nested_extension(path.as_str()) {
            return Err(PackageError::NestedArchive { entry_index: index });
        }
        if file.encrypted() {
            return Err(PackageError::EncryptedEntry { entry_index: index });
        }
        if file.is_symlink() || (!file.is_file() && !file.is_dir()) {
            return Err(PackageError::UnsupportedFileType { entry_index: index });
        }
        if file.is_dir() != path.is_directory() {
            return Err(PackageError::HeaderMismatch { entry_index: index });
        }
        if file
            .extra_data()
            .is_some_and(|data| data.len() > config.max_extra_field_bytes)
        {
            return Err(PackageError::ExtraFieldTooLarge { entry_index: index });
        }
        let compression = match file.compression() {
            CompressionMethod::Stored => Compression::Stored,
            CompressionMethod::Deflated => Compression::Deflated,
            _ => return Err(PackageError::UnsupportedCompression { entry_index: index }),
        };
        let expanded_size = file.size();
        let compressed_size = file.compressed_size();
        validate_sizes(index, compressed_size, expanded_size, limits)?;
        total_expanded = total_expanded.checked_add(expanded_size).ok_or(
            PackageError::TotalExpandedTooLarge {
                actual: u64::MAX,
                limit: config.max_total_expanded_bytes,
            },
        )?;
        total_compressed = total_compressed
            .checked_add(compressed_size)
            .ok_or(PackageError::InvalidZip)?;
        if total_expanded > config.max_total_expanded_bytes {
            return Err(PackageError::TotalExpandedTooLarge {
                actual: total_expanded,
                limit: config.max_total_expanded_bytes,
            });
        }
        let data_start = file
            .data_start()
            .ok_or(PackageError::EntryRangeInvalid { entry_index: index })?;
        let data_end = data_start
            .checked_add(compressed_size)
            .ok_or(PackageError::EntryRangeInvalid { entry_index: index })?;
        headers.push(HeaderRecord {
            local_start: file.header_start(),
            data_start,
            data_end,
            central_start: file.central_header_start(),
            raw_name: file.name_raw().to_vec(),
            flags: 0,
            method: compression_code(compression),
            crc32: file.crc32(),
            compressed_size,
            expanded_size,
        });
        entries.push(EntryMetadata {
            index,
            path,
            compression,
            compressed_size,
            expanded_size,
            crc32: file.crc32(),
        });
    }
    validate_total_ratio(total_compressed, total_expanded, limits)?;
    Ok((entries, headers))
}

fn read_end_record<R: Read + Seek>(
    reader: &mut R,
    archive_len: u64,
    limits: PackageLimits,
) -> Result<EndRecord, PackageError> {
    if archive_len < EOCD_FIXED as u64 {
        return Err(PackageError::InvalidZip);
    }
    let search_len = archive_len.min((EOCD_FIXED + u16::MAX as usize) as u64);
    let start = archive_len - search_len;
    reader
        .seek(SeekFrom::Start(start))
        .map_err(PackageError::Io)?;
    let size = usize::try_from(search_len).map_err(|_| PackageError::InvalidZip)?;
    let mut tail = Vec::new();
    tail.try_reserve_exact(size)
        .map_err(|_| PackageError::MetadataAllocationFailed)?;
    tail.resize(size, 0);
    reader.read_exact(&mut tail).map_err(PackageError::Io)?;
    let mut saw_trailing = false;
    for position in (0..=tail.len() - EOCD_FIXED).rev() {
        if tail[position..position + 4] != EOCD_SIGNATURE {
            continue;
        }
        let comment_length = usize::from(le_u16(&tail[position + 20..position + 22]));
        let record_end = position
            .checked_add(EOCD_FIXED)
            .and_then(|value| value.checked_add(comment_length))
            .ok_or(PackageError::InvalidZip)?;
        if record_end != tail.len() {
            if record_end < tail.len() {
                saw_trailing = true;
            }
            continue;
        }
        if comment_length > limits.config().max_comment_bytes {
            return Err(PackageError::CommentTooLarge);
        }
        let disk = le_u16(&tail[position + 4..position + 6]);
        let central_disk = le_u16(&tail[position + 6..position + 8]);
        let disk_entries = le_u16(&tail[position + 8..position + 10]);
        let total_entries = le_u16(&tail[position + 10..position + 12]);
        let central_size = le_u32(&tail[position + 12..position + 16]);
        let central_offset = le_u32(&tail[position + 16..position + 20]);
        if disk != 0 || central_disk != 0 || disk_entries != total_entries {
            return Err(PackageError::MultiDiskUnsupported);
        }
        if total_entries == u16::MAX || central_size == u32::MAX || central_offset == u32::MAX {
            return Err(PackageError::Zip64Unsupported);
        }
        return Ok(EndRecord {
            central_offset: u64::from(central_offset),
            central_size: u64::from(central_size),
            entries: usize::from(total_entries),
            position: start + position as u64,
        });
    }
    Err(if saw_trailing {
        PackageError::UnexpectedTrailingData
    } else {
        PackageError::InvalidZip
    })
}

fn validate_headers<R: Read + Seek>(
    reader: &mut R,
    records: &mut [HeaderRecord],
    end: EndRecord,
    limits: PackageLimits,
) -> Result<(), PackageError> {
    validate_central_headers(reader, records, end, limits)?;
    validate_local_headers(reader, records, end, limits)
}

fn validate_central_headers<R: Read + Seek>(
    reader: &mut R,
    records: &mut [HeaderRecord],
    end: EndRecord,
    limits: PackageLimits,
) -> Result<(), PackageError> {
    let mut central_ranges = Vec::with_capacity(records.len());
    for (index, record) in records.iter_mut().enumerate() {
        let fixed = read_array_at::<CENTRAL_FIXED, _>(reader, record.central_start)?;
        if fixed[..4] != CENTRAL_SIGNATURE {
            return Err(PackageError::HeaderMismatch { entry_index: index });
        }
        let flags = le_u16(&fixed[8..10]);
        let method = le_u16(&fixed[10..12]);
        validate_flags(index, flags, method)?;
        let crc32 = le_u32(&fixed[16..20]);
        let compressed_size = le_u32(&fixed[20..24]);
        let expanded_size = le_u32(&fixed[24..28]);
        let name_len = usize::from(le_u16(&fixed[28..30]));
        let extra_len = usize::from(le_u16(&fixed[30..32]));
        let comment_len = usize::from(le_u16(&fixed[32..34]));
        let disk_start = le_u16(&fixed[34..36]);
        let local_start = le_u32(&fixed[42..46]);
        if compressed_size == u32::MAX || expanded_size == u32::MAX || local_start == u32::MAX {
            return Err(PackageError::Zip64Unsupported);
        }
        if disk_start != 0 {
            return Err(PackageError::MultiDiskUnsupported);
        }
        if name_len > limits.config().max_name_bytes
            || extra_len > limits.config().max_extra_field_bytes
            || comment_len > limits.config().max_comment_bytes
        {
            return Err(PackageError::ExtraFieldTooLarge { entry_index: index });
        }
        let variable_len = name_len
            .checked_add(extra_len)
            .and_then(|value| value.checked_add(comment_len))
            .ok_or(PackageError::HeaderMismatch { entry_index: index })?;
        let variable_start = record
            .central_start
            .checked_add(CENTRAL_FIXED as u64)
            .ok_or(PackageError::HeaderMismatch { entry_index: index })?;
        let variable = read_vec_at(reader, variable_start, variable_len)?;
        let central_end = variable_start
            .checked_add(variable_len as u64)
            .ok_or(PackageError::HeaderMismatch { entry_index: index })?;
        if record.central_start < end.central_offset || central_end > end.position {
            return Err(PackageError::EntryRangeInvalid { entry_index: index });
        }
        let (name, remainder) = variable.split_at(name_len);
        let (extra, _) = remainder.split_at(extra_len);
        reject_zip64_extra(extra)?;
        if name != record.raw_name
            || method != record.method
            || crc32 != record.crc32
            || u64::from(compressed_size) != record.compressed_size
            || u64::from(expanded_size) != record.expanded_size
            || u64::from(local_start) != record.local_start
        {
            return Err(PackageError::HeaderMismatch { entry_index: index });
        }
        record.flags = flags;
        central_ranges.push((record.central_start, central_end, index));
    }
    validate_contiguous_ranges(&mut central_ranges, end.central_offset, end.position)
}

fn validate_local_headers<R: Read + Seek>(
    reader: &mut R,
    records: &[HeaderRecord],
    end: EndRecord,
    limits: PackageLimits,
) -> Result<(), PackageError> {
    let mut local_ranges = Vec::with_capacity(records.len());
    for (index, record) in records.iter().enumerate() {
        let fixed = read_array_at::<LOCAL_FIXED, _>(reader, record.local_start)?;
        if fixed[..4] != LOCAL_SIGNATURE {
            return Err(PackageError::HeaderMismatch { entry_index: index });
        }
        let flags = le_u16(&fixed[6..8]);
        let method = le_u16(&fixed[8..10]);
        validate_flags(index, flags, method)?;
        let crc32 = le_u32(&fixed[14..18]);
        let compressed_size = le_u32(&fixed[18..22]);
        let expanded_size = le_u32(&fixed[22..26]);
        let name_len = usize::from(le_u16(&fixed[26..28]));
        let extra_len = usize::from(le_u16(&fixed[28..30]));
        if compressed_size == u32::MAX || expanded_size == u32::MAX {
            return Err(PackageError::Zip64Unsupported);
        }
        if name_len > limits.config().max_name_bytes
            || extra_len > limits.config().max_extra_field_bytes
        {
            return Err(PackageError::ExtraFieldTooLarge { entry_index: index });
        }
        let variable_len = name_len
            .checked_add(extra_len)
            .ok_or(PackageError::HeaderMismatch { entry_index: index })?;
        let variable_start = record
            .local_start
            .checked_add(LOCAL_FIXED as u64)
            .ok_or(PackageError::HeaderMismatch { entry_index: index })?;
        let variable = read_vec_at(reader, variable_start, variable_len)?;
        let (name, extra) = variable.split_at(name_len);
        reject_zip64_extra(extra)?;
        let expected_data_start = variable_start
            .checked_add(variable_len as u64)
            .ok_or(PackageError::HeaderMismatch { entry_index: index })?;
        if flags != record.flags
            || method != record.method
            || crc32 != record.crc32
            || u64::from(compressed_size) != record.compressed_size
            || u64::from(expanded_size) != record.expanded_size
            || name != record.raw_name
            || expected_data_start != record.data_start
            || record.data_end > end.central_offset
        {
            return Err(PackageError::HeaderMismatch { entry_index: index });
        }
        local_ranges.push((record.local_start, record.data_end, index));
    }
    validate_contiguous_ranges(&mut local_ranges, 0, end.central_offset)
}

fn validate_flags(entry_index: usize, flags: u16, method: u16) -> Result<(), PackageError> {
    if flags & 0x0001 != 0 || flags & 0x0040 != 0 {
        return Err(PackageError::EncryptedEntry { entry_index });
    }
    if flags & 0x0008 != 0 {
        return Err(PackageError::DataDescriptorUnsupported { entry_index });
    }
    let compression_flags = if method == 8 { 0x0006 } else { 0 };
    let allowed = 0x0800 | compression_flags;
    if flags & !allowed != 0 {
        return Err(PackageError::UnsupportedFlags { entry_index });
    }
    if !matches!(method, 0 | 8) {
        return Err(PackageError::UnsupportedCompression { entry_index });
    }
    Ok(())
}

fn validate_contiguous_ranges(
    ranges: &mut [(u64, u64, usize)],
    expected_start: u64,
    expected_end: u64,
) -> Result<(), PackageError> {
    ranges.sort_unstable_by_key(|range| range.0);
    let mut cursor = expected_start;
    for &(start, end, entry_index) in ranges.iter() {
        if start < cursor {
            return Err(PackageError::OverlappingEntries);
        }
        if start != cursor || end < start || end > expected_end {
            return Err(PackageError::EntryRangeInvalid { entry_index });
        }
        cursor = end;
    }
    if cursor != expected_end {
        return Err(PackageError::InvalidZip);
    }
    Ok(())
}

fn reject_zip64_extra(extra: &[u8]) -> Result<(), PackageError> {
    let mut cursor = 0_usize;
    while cursor < extra.len() {
        if extra.len() - cursor < 4 {
            return Err(PackageError::InvalidZip);
        }
        let tag = le_u16(&extra[cursor..cursor + 2]);
        let size = usize::from(le_u16(&extra[cursor + 2..cursor + 4]));
        cursor = cursor.checked_add(4).ok_or(PackageError::InvalidZip)?;
        let next = cursor.checked_add(size).ok_or(PackageError::InvalidZip)?;
        if next > extra.len() {
            return Err(PackageError::InvalidZip);
        }
        if tag == 0x0001 {
            return Err(PackageError::Zip64Unsupported);
        }
        cursor = next;
    }
    Ok(())
}

fn read_array_at<const N: usize, R: Read + Seek>(
    reader: &mut R,
    position: u64,
) -> Result<[u8; N], PackageError> {
    reader
        .seek(SeekFrom::Start(position))
        .map_err(PackageError::Io)?;
    let mut bytes = [0_u8; N];
    reader
        .read_exact(&mut bytes)
        .map_err(|_| PackageError::InvalidZip)?;
    Ok(bytes)
}

fn read_vec_at<R: Read + Seek>(
    reader: &mut R,
    position: u64,
    length: usize,
) -> Result<Vec<u8>, PackageError> {
    reader
        .seek(SeekFrom::Start(position))
        .map_err(PackageError::Io)?;
    let mut bytes = Vec::new();
    bytes
        .try_reserve_exact(length)
        .map_err(|_| PackageError::MetadataAllocationFailed)?;
    bytes.resize(length, 0);
    reader
        .read_exact(&mut bytes)
        .map_err(|_| PackageError::InvalidZip)?;
    Ok(bytes)
}

fn validate_sizes(
    index: usize,
    compressed: u64,
    expanded: u64,
    limits: PackageLimits,
) -> Result<(), PackageError> {
    let config = limits.config();
    if expanded > config.max_entry_expanded_bytes {
        return Err(PackageError::EntryExpandedTooLarge {
            entry_index: index,
            actual: expanded,
            limit: config.max_entry_expanded_bytes,
        });
    }
    if expanded > 0 {
        let allowed = u128::from(compressed.max(1)) * u128::from(config.max_compression_ratio);
        if u128::from(expanded) > allowed {
            return Err(PackageError::CompressionRatioExceeded {
                entry_index: index,
                limit: config.max_compression_ratio,
            });
        }
    }
    Ok(())
}

fn validate_total_ratio(
    compressed: u64,
    expanded: u64,
    limits: PackageLimits,
) -> Result<(), PackageError> {
    if expanded > 0
        && u128::from(expanded)
            > u128::from(compressed.max(1)) * u128::from(limits.config().max_compression_ratio)
    {
        return Err(PackageError::TotalCompressionRatioExceeded {
            limit: limits.config().max_compression_ratio,
        });
    }
    Ok(())
}

fn compression_code(compression: Compression) -> u16 {
    match compression {
        Compression::Stored => 0,
        Compression::Deflated => 8,
    }
}

fn nested_extension(path: &str) -> bool {
    let lowercase = path.trim_end_matches('/').to_ascii_lowercase();
    [
        ".zip", ".hwpx", ".hwp", ".docx", ".xlsx", ".pptx", ".jar", ".odt", ".ods", ".odp",
    ]
    .iter()
    .any(|extension| lowercase.ends_with(extension))
}

fn nested_signature(bytes: &[u8]) -> bool {
    bytes.starts_with(b"PK\x03\x04")
        || bytes.starts_with(b"PK\x05\x06")
        || bytes.starts_with(b"PK\x07\x08")
}

fn le_u16(bytes: &[u8]) -> u16 {
    u16::from_le_bytes([bytes[0], bytes[1]])
}

fn le_u32(bytes: &[u8]) -> u32 {
    u32::from_le_bytes([bytes[0], bytes[1], bytes[2], bytes[3]])
}
