#![forbid(unsafe_code)]

//! Fail-closed, bounded ZIP reading for HWPX package inspection.
//!
//! This crate never extracts files. [`BoundedZipReader::read_entry`] returns a
//! fully verified in-memory value only after metadata, streaming size, CRC and
//! nested-package checks have succeeded.

mod graph;
mod id_index;
mod limits;
mod path;
mod preservation;
mod preserving_xml;
mod reader;
mod safe_xml;

pub use graph::{
    GraphError, MediaType, PackageGraph, PackageGraphLimitConfig, PackageGraphLimits, PartRecord,
    PartRole, Relationship, RelationshipKind,
};
pub use id_index::{
    IdDeclaration, IdIndex, IdIndexError, IdIndexLimitConfig, IdIndexLimits, IdIssueKind, IdKind,
    IdLocation, IdReference, IdRuleProfile, IdValidationIssue, IdValidationReport,
};
pub use limits::{PackageLimitConfig, PackageLimits};
pub use path::PackagePath;
pub use preservation::{
    PartPreservationRecord, PreservationClass, PreservationCounts, PreservationError,
    PreservationReason, PreservationReport, TokenPreservationEvidence,
};
pub use preserving_xml::{
    PreservingXmlDocument, PreservingXmlError, XmlAttributeToken, XmlByteSpan, XmlElementToken,
    XmlName, XmlQuoteStyle, XmlToken, XmlTokenKind,
};
pub use reader::{BoundedZipReader, Compression, EntryMetadata, PackageError};
pub use safe_xml::SafeXmlError;
