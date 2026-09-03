#![forbid(unsafe_code)]

//! Fail-closed, bounded ZIP reading for HWPX package inspection.
//!
//! This crate never extracts files. [`BoundedZipReader::read_entry`] returns a
//! fully verified in-memory value only after metadata, streaming size, CRC and
//! nested-package checks have succeeded.

mod character_style;
mod graph;
mod id_index;
mod limits;
mod paragraph_style;
mod patch;
mod path;
mod preservation;
mod preserving_xml;
mod reader;
mod roundtrip;
mod safe_xml;
mod text_flow;
mod vs0;
mod writer;

pub use character_style::{
    BinaryProperty, CHARACTER_STYLE_PROFILE_ID, CharacterEffects, CharacterStyle,
    CharacterStyleCatalog, CharacterStyleCatalogReader, CharacterStyleCatalogWriter,
    CharacterStyleError, CharacterStyleLimitConfig, CharacterStyleLimits,
    CharacterStyleLoweringReceipt, Color, DeduplicatedCharacterStyles, EmphasisMark, FontFace,
    FontFaceGroup, FontFamily, FontType, FontTypeInfo, HANCOM_2020_HEAD_NAMESPACE, LanguageSlot,
    LanguageValues, LineType1, LineType2, Shadow, ShadowType, Strikeout, SubstituteFont, Underline,
    UnderlinePosition,
};
pub use graph::{
    GraphError, MediaType, PackageGraph, PackageGraphLimitConfig, PackageGraphLimits, PartRecord,
    PartRole, Relationship, RelationshipKind,
};
pub use id_index::{
    IdDeclaration, IdIndex, IdIndexError, IdIndexLimitConfig, IdIndexLimits, IdIssueKind, IdKind,
    IdLocation, IdReference, IdRuleProfile, IdValidationIssue, IdValidationReport,
};
pub use limits::{PackageLimitConfig, PackageLimits};
pub use paragraph_style::{
    AutoSpacing, BorderFill, BorderLine, BorderWidth, BreakSettings, CenterLine, CompatibleHeading,
    CompatibleParagraphLayout, DeduplicatedParagraphStyles, FillBrush, HatchStyle, Heading,
    HeadingType, HorizontalAlignment, HwpValue, LineSpacing, LineSpacingType, LineWrap, Margin,
    MeasurementUnit, PARAGRAPH_STYLE_PROFILE_ID, ParagraphBorder, ParagraphLayout,
    ParagraphReferenceDomains, ParagraphStyle, ParagraphStyleCatalog, ParagraphStyleCatalogReader,
    ParagraphStyleCatalogWriter, ParagraphStyleError, ParagraphStyleLimitConfig,
    ParagraphStyleLimits, ParagraphStyleLoweringReceipt, Slash, SlashType, TextDirection,
    VerticalAlignment, WindowBrush, WordBreak,
};
pub use patch::{
    AddedPart, AllocationHandle, PatchAttributeValue, PatchError, PatchIntent, PatchLimitConfig,
    PatchLimits, PatchPartDisposition, PatchPartRecord, PatchResult, PatchText,
    PreservingPatchEngine, RelationshipAddition, RelationshipSpine, SiblingPosition,
    ValidatedXmlFragment, XmlAttributeSelector, XmlElementSelector, XmlTextSelector,
};
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
pub use roundtrip::{
    DiagnosticLayer, RecommendedAction, RepairDiagnostic, Repairability, RoundTripError,
    RoundTripEvidence, RoundTripLimits, RoundTripVerifier,
};
pub use safe_xml::SafeXmlError;
pub use text_flow::{
    FieldBegin, FieldEnd, FieldType, HANCOM_2020_PARAGRAPH_NAMESPACE, OpaqueTextElement,
    ParagraphChild, TabAlignment, TextAtom, TextFlow, TextFlowError, TextFlowLimitConfig,
    TextFlowLimits, TextFlowReader, TextFlowWriter, TextParagraphProperties, TextRun, TextRunItem,
    TextSpan,
};
pub use vs0::{
    HANCOM_2020_VS0_MAX_TEXT_BYTES, Hancom2020Vs0Artifact, Hancom2020Vs0Builder, Hancom2020Vs0Error,
};
pub use writer::{
    AtomicPackagePublisher, MetadataDisposition, NormalizedWriter, PackageArtifact,
    PreservingWriter, PublicationReceipt, WriterEntryRecord, WriterError, WriterLimitConfig,
    WriterLimits, WriterMode, WriterReport,
};
