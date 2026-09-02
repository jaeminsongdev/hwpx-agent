#![forbid(unsafe_code)]

//! Fail-closed, bounded ZIP reading for HWPX package inspection.
//!
//! This crate never extracts files. [`BoundedZipReader::read_entry`] returns a
//! fully verified in-memory value only after metadata, streaming size, CRC and
//! nested-package checks have succeeded.

mod limits;
mod path;
mod reader;

pub use limits::{PackageLimitConfig, PackageLimits};
pub use path::PackagePath;
pub use reader::{BoundedZipReader, Compression, EntryMetadata, PackageError};
