use std::collections::{BTreeMap, BTreeSet};
use std::fmt::{self, Debug};
use std::io::{Read, Seek};

use thiserror::Error;

use crate::{
    BoundedZipReader, PackageError, PackageGraph, PackageGraphLimits, PackagePath,
    PartPreservationRecord, PartRole, PreservationClass, PreservationError, PreservationReport,
    PreservingXmlDocument, PreservingXmlError, XmlByteSpan,
};

const OPF_NAMESPACE: &str = "http://www.idpf.org/2007/opf";
const OPF_NAMESPACE_HANCOM_2020: &str = "http://www.idpf.org/2007/opf/";
const HWPML_2011_HEAD_NAMESPACE: &str = "http://www.hancom.co.kr/hwpml/2011/head";
const HWPML_2011_PARAGRAPH_NAMESPACE: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const HEADER_PART: &str = "Contents/header.xml";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct IdIndexLimitConfig {
    pub max_parts: usize,
    pub max_declarations: usize,
    pub max_references: usize,
    pub max_value_bytes: usize,
    pub max_issues: usize,
}

impl Default for IdIndexLimitConfig {
    fn default() -> Self {
        Self {
            max_parts: 4_096,
            max_declarations: 65_536,
            max_references: 262_144,
            max_value_bytes: 256,
            max_issues: 4_096,
        }
    }
}

/// Validated finite limits for ID/reference indexing.
#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct IdIndexLimits(IdIndexLimitConfig);

impl IdIndexLimits {
    pub const HARD_MAX_PARTS: usize = 16_384;
    pub const HARD_MAX_DECLARATIONS: usize = 1_000_000;
    pub const HARD_MAX_REFERENCES: usize = 4_000_000;
    pub const HARD_MAX_VALUE_BYTES: usize = 4_096;
    pub const HARD_MAX_ISSUES: usize = 65_536;

    /// Validates caller limits without clamping them.
    ///
    /// # Errors
    ///
    /// Returns a stable invalid-limit error for zero or over-ceiling values.
    pub fn new(config: IdIndexLimitConfig) -> Result<Self, IdIndexError> {
        let values = [
            ("max_parts", config.max_parts, Self::HARD_MAX_PARTS),
            (
                "max_declarations",
                config.max_declarations,
                Self::HARD_MAX_DECLARATIONS,
            ),
            (
                "max_references",
                config.max_references,
                Self::HARD_MAX_REFERENCES,
            ),
            (
                "max_value_bytes",
                config.max_value_bytes,
                Self::HARD_MAX_VALUE_BYTES,
            ),
            ("max_issues", config.max_issues, Self::HARD_MAX_ISSUES),
        ];
        for (field, value, ceiling) in values {
            if value == 0 || value > ceiling {
                return Err(IdIndexError::InvalidLimit {
                    field,
                    value,
                    ceiling,
                });
            }
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> IdIndexLimitConfig {
        self.0
    }
}

/// A source-locked rule profile. Other Hancom versions require independent
/// qualification instead of silently reusing this profile.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct IdRuleProfile(ProfileKind);

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum ProfileKind {
    CurrentHancom2020CoreV1,
}

impl IdRuleProfile {
    #[must_use]
    pub const fn current_hancom_2020_core_v1() -> Self {
        Self(ProfileKind::CurrentHancom2020CoreV1)
    }

    #[must_use]
    pub const fn version(self) -> &'static str {
        match self.0 {
            ProfileKind::CurrentHancom2020CoreV1 => "hancom-2020-hwpml-2011-core/v1",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum IdKind {
    PackageIdentifier,
    ManifestItem,
    FontHangul,
    FontLatin,
    FontHanja,
    FontJapanese,
    FontOther,
    FontSymbol,
    FontUser,
    BorderFill,
    CharacterProperties,
    TabProperties,
    Numbering,
    Bullet,
    ParagraphProperties,
    Style,
    MemoShape,
    Paragraph,
    SectionProperties,
    ColumnProperties,
}

#[derive(Clone, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct IdLocation {
    part: PackagePath,
    element_index: usize,
    attribute_index: usize,
    value_span: XmlByteSpan,
}

impl IdLocation {
    #[must_use]
    pub const fn part(&self) -> &PackagePath {
        &self.part
    }

    #[must_use]
    pub const fn element_index(&self) -> usize {
        self.element_index
    }

    #[must_use]
    pub const fn attribute_index(&self) -> usize {
        self.attribute_index
    }

    #[must_use]
    pub const fn value_span(&self) -> XmlByteSpan {
        self.value_span
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct IdDeclaration {
    location: IdLocation,
    kind: IdKind,
    value: IdValue,
}

impl Debug for IdDeclaration {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("IdDeclaration")
            .field("location", &self.location)
            .field("kind", &self.kind)
            .finish_non_exhaustive()
    }
}

impl IdDeclaration {
    #[must_use]
    pub const fn location(&self) -> &IdLocation {
        &self.location
    }

    #[must_use]
    pub const fn kind(&self) -> IdKind {
        self.kind
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct IdReference {
    location: IdLocation,
    target_part: PackagePath,
    expected_kind: IdKind,
    declaration_index: usize,
    value: IdValue,
}

impl Debug for IdReference {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("IdReference")
            .field("location", &self.location)
            .field("target_part", &self.target_part)
            .field("expected_kind", &self.expected_kind)
            .field("declaration_index", &self.declaration_index)
            .finish_non_exhaustive()
    }
}

impl IdReference {
    #[must_use]
    pub const fn location(&self) -> &IdLocation {
        &self.location
    }

    #[must_use]
    pub const fn target_part(&self) -> &PackagePath {
        &self.target_part
    }

    #[must_use]
    pub const fn expected_kind(&self) -> IdKind {
        self.expected_kind
    }

    #[must_use]
    pub const fn declaration_index(&self) -> usize {
        self.declaration_index
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct IdIndex {
    profile_version: &'static str,
    parts_scanned: usize,
    declarations: Vec<IdDeclaration>,
    references: Vec<IdReference>,
}

impl Debug for IdIndex {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("IdIndex")
            .field("profile_version", &self.profile_version)
            .field("parts_scanned", &self.parts_scanned)
            .field("declaration_count", &self.declarations.len())
            .field("reference_count", &self.references.len())
            .finish()
    }
}

impl IdIndex {
    /// Rebuilds P03-05 evidence, scans only token-stable XML, and returns no
    /// index unless every supported reference resolves uniquely and by type.
    ///
    /// # Errors
    ///
    /// Returns a stable package/preservation/token/limit error or a complete
    /// non-sensitive validation report for duplicate, dangling, wrong-type,
    /// malformed, unknown or unindexable references.
    pub fn build<R: Read + Seek>(
        reader: &mut BoundedZipReader<R>,
        graph: &PackageGraph,
        profile: IdRuleProfile,
        limits: IdIndexLimits,
    ) -> Result<Self, IdIndexError> {
        Self::build_with_graph_limits(
            reader,
            graph,
            PackageGraphLimits::default(),
            profile,
            limits,
        )
    }

    /// Same as [`Self::build`] with the graph limits used to validate the
    /// supplied graph.
    ///
    /// # Errors
    ///
    /// Returns the same fail-closed errors as [`Self::build`].
    pub fn build_with_graph_limits<R: Read + Seek>(
        reader: &mut BoundedZipReader<R>,
        graph: &PackageGraph,
        graph_limits: PackageGraphLimits,
        profile: IdRuleProfile,
        limits: IdIndexLimits,
    ) -> Result<Self, IdIndexError> {
        let preservation =
            PreservationReport::build_with_graph_limits(reader, graph, graph_limits)?;
        if !preservation.direct_preserve_ready() {
            return Err(IdIndexError::PreservationRejected);
        }
        IndexBuilder::new(graph, &preservation, profile, limits)?.build(reader)
    }

    #[must_use]
    pub const fn profile_version(&self) -> &'static str {
        self.profile_version
    }

    #[must_use]
    pub const fn parts_scanned(&self) -> usize {
        self.parts_scanned
    }

    #[must_use]
    pub fn declarations(&self) -> &[IdDeclaration] {
        &self.declarations
    }

    #[must_use]
    pub fn references(&self) -> &[IdReference] {
        &self.references
    }

    #[must_use]
    pub fn declaration_for(&self, reference: &IdReference) -> Option<&IdDeclaration> {
        self.declarations.get(reference.declaration_index)
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum IdIssueKind {
    DuplicateDeclaration,
    DanglingReference,
    WrongTypeReference,
    MalformedValue,
    UnknownIdLikeAttribute,
    TargetPartMissing,
    TargetPartNotTokenStable,
}

impl IdIssueKind {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::DuplicateDeclaration => "id_index_duplicate_declaration",
            Self::DanglingReference => "id_index_dangling_reference",
            Self::WrongTypeReference => "id_index_wrong_type_reference",
            Self::MalformedValue => "id_index_malformed_value",
            Self::UnknownIdLikeAttribute => "id_index_unknown_id_like_attribute",
            Self::TargetPartMissing => "id_index_target_part_missing",
            Self::TargetPartNotTokenStable => "id_index_target_part_not_token_stable",
        }
    }
}

#[derive(Clone, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct IdValidationIssue {
    kind: IdIssueKind,
    source: IdLocation,
    related: Option<IdLocation>,
    expected_kind: Option<IdKind>,
    actual_kind: Option<IdKind>,
}

impl IdValidationIssue {
    #[must_use]
    pub const fn kind(&self) -> IdIssueKind {
        self.kind
    }

    #[must_use]
    pub const fn code(&self) -> &'static str {
        self.kind.code()
    }

    #[must_use]
    pub const fn source(&self) -> &IdLocation {
        &self.source
    }

    #[must_use]
    pub const fn related(&self) -> Option<&IdLocation> {
        self.related.as_ref()
    }

    #[must_use]
    pub const fn expected_kind(&self) -> Option<IdKind> {
        self.expected_kind
    }

    #[must_use]
    pub const fn actual_kind(&self) -> Option<IdKind> {
        self.actual_kind
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct IdValidationReport {
    issues: Vec<IdValidationIssue>,
}

impl IdValidationReport {
    #[must_use]
    pub fn issues(&self) -> &[IdValidationIssue] {
        &self.issues
    }
}

#[derive(Debug, Error)]
pub enum IdIndexError {
    #[error("bounded package read failed while indexing IDs")]
    Package(#[from] PackageError),
    #[error("preservation evidence failed while indexing IDs")]
    Preservation(#[from] PreservationError),
    #[error("preserving XML token model failed while indexing IDs")]
    Token(#[from] PreservingXmlError),
    #[error("ID index limit {limit} was exceeded")]
    LimitExceeded { limit: &'static str },
    #[error("invalid ID index limit {field}: {value} (ceiling {ceiling})")]
    InvalidLimit {
        field: &'static str,
        value: usize,
        ceiling: usize,
    },
    #[error("package contains a rejected preservation part")]
    PreservationRejected,
    #[error("ID index token identity differs from preservation evidence")]
    IdentityMismatch,
    #[error("ID rule profile matched an attribute ambiguously")]
    AmbiguousRule,
    #[error("ID index allocation failed")]
    AllocationFailed,
    #[error("ID/reference validation failed with {} issue(s)", .0.issues.len())]
    Validation(IdValidationReport),
}

impl IdIndexError {
    #[must_use]
    pub fn code(&self) -> &'static str {
        match self {
            Self::Package(error) => error.code(),
            Self::Preservation(error) => error.code(),
            Self::Token(error) => error.code(),
            Self::LimitExceeded { .. } => "id_index_limit_exceeded",
            Self::InvalidLimit { .. } => "id_index_invalid_limit",
            Self::PreservationRejected => "id_index_preservation_rejected",
            Self::IdentityMismatch => "id_index_identity_mismatch",
            Self::AmbiguousRule => "id_index_ambiguous_rule",
            Self::AllocationFailed => "id_index_allocation_failed",
            Self::Validation(_) => "id_index_validation_failed",
        }
    }

    #[must_use]
    pub const fn validation(&self) -> Option<&IdValidationReport> {
        match self {
            Self::Validation(report) => Some(report),
            _ => None,
        }
    }
}

#[derive(Clone, Debug, Eq, Ord, PartialEq, PartialOrd)]
enum IdValue {
    Decimal(u64),
    Text(String),
}

#[derive(Clone, Copy)]
enum PartSelector {
    PackageDocument,
    Exact(&'static str),
    SpineDocument,
}

#[derive(Clone, Copy)]
enum TargetSelector {
    SamePart,
    Exact(&'static str),
}

#[derive(Clone, Copy)]
enum ValueSyntax {
    Decimal,
    Text,
}

#[derive(Clone, Copy)]
struct DeclarationRule {
    part: PartSelector,
    namespace: &'static str,
    element: &'static str,
    attribute: &'static str,
    kind: DeclarationKind,
    syntax: ValueSyntax,
}

#[derive(Clone, Copy)]
enum DeclarationKind {
    Fixed(IdKind),
    FontByParentLanguage,
}

#[derive(Clone, Copy)]
struct ReferenceRule {
    part: PartSelector,
    namespace: &'static str,
    element: &'static str,
    attribute: &'static str,
    target: TargetSelector,
    kind: IdKind,
    syntax: ValueSyntax,
    sentinel: Option<u64>,
}

const DECLARATION_RULES: &[DeclarationRule] = &[
    declaration(
        PartSelector::PackageDocument,
        OPF_NAMESPACE,
        "package",
        "id",
        IdKind::PackageIdentifier,
        ValueSyntax::Text,
    ),
    declaration(
        PartSelector::PackageDocument,
        OPF_NAMESPACE,
        "item",
        "id",
        IdKind::ManifestItem,
        ValueSyntax::Text,
    ),
    font_declaration(
        PartSelector::Exact(HEADER_PART),
        HWPML_2011_HEAD_NAMESPACE,
        "font",
        "id",
        ValueSyntax::Decimal,
    ),
    declaration(
        PartSelector::Exact(HEADER_PART),
        HWPML_2011_HEAD_NAMESPACE,
        "borderFill",
        "id",
        IdKind::BorderFill,
        ValueSyntax::Decimal,
    ),
    declaration(
        PartSelector::Exact(HEADER_PART),
        HWPML_2011_HEAD_NAMESPACE,
        "charPr",
        "id",
        IdKind::CharacterProperties,
        ValueSyntax::Decimal,
    ),
    declaration(
        PartSelector::Exact(HEADER_PART),
        HWPML_2011_HEAD_NAMESPACE,
        "tabPr",
        "id",
        IdKind::TabProperties,
        ValueSyntax::Decimal,
    ),
    declaration(
        PartSelector::Exact(HEADER_PART),
        HWPML_2011_HEAD_NAMESPACE,
        "numbering",
        "id",
        IdKind::Numbering,
        ValueSyntax::Decimal,
    ),
    declaration(
        PartSelector::Exact(HEADER_PART),
        HWPML_2011_HEAD_NAMESPACE,
        "bullet",
        "id",
        IdKind::Bullet,
        ValueSyntax::Decimal,
    ),
    declaration(
        PartSelector::Exact(HEADER_PART),
        HWPML_2011_HEAD_NAMESPACE,
        "paraPr",
        "id",
        IdKind::ParagraphProperties,
        ValueSyntax::Decimal,
    ),
    declaration(
        PartSelector::Exact(HEADER_PART),
        HWPML_2011_HEAD_NAMESPACE,
        "style",
        "id",
        IdKind::Style,
        ValueSyntax::Decimal,
    ),
    declaration(
        PartSelector::Exact(HEADER_PART),
        HWPML_2011_HEAD_NAMESPACE,
        "memoShape",
        "id",
        IdKind::MemoShape,
        ValueSyntax::Decimal,
    ),
    declaration(
        PartSelector::SpineDocument,
        HWPML_2011_PARAGRAPH_NAMESPACE,
        "p",
        "id",
        IdKind::Paragraph,
        ValueSyntax::Decimal,
    ),
    declaration(
        PartSelector::SpineDocument,
        HWPML_2011_PARAGRAPH_NAMESPACE,
        "secPr",
        "id",
        IdKind::SectionProperties,
        ValueSyntax::Text,
    ),
    declaration(
        PartSelector::SpineDocument,
        HWPML_2011_PARAGRAPH_NAMESPACE,
        "colPr",
        "id",
        IdKind::ColumnProperties,
        ValueSyntax::Text,
    ),
];

const REFERENCE_RULES: &[ReferenceRule] = &[
    reference(
        PartSelector::PackageDocument,
        OPF_NAMESPACE,
        "itemref",
        "idref",
        TargetSelector::SamePart,
        IdKind::ManifestItem,
        ValueSyntax::Text,
    ),
    reference(
        PartSelector::Exact(HEADER_PART),
        HWPML_2011_HEAD_NAMESPACE,
        "fontRef",
        "hangul",
        TargetSelector::SamePart,
        IdKind::FontHangul,
        ValueSyntax::Decimal,
    ),
    reference(
        PartSelector::Exact(HEADER_PART),
        HWPML_2011_HEAD_NAMESPACE,
        "fontRef",
        "latin",
        TargetSelector::SamePart,
        IdKind::FontLatin,
        ValueSyntax::Decimal,
    ),
    reference(
        PartSelector::Exact(HEADER_PART),
        HWPML_2011_HEAD_NAMESPACE,
        "fontRef",
        "hanja",
        TargetSelector::SamePart,
        IdKind::FontHanja,
        ValueSyntax::Decimal,
    ),
    reference(
        PartSelector::Exact(HEADER_PART),
        HWPML_2011_HEAD_NAMESPACE,
        "fontRef",
        "japanese",
        TargetSelector::SamePart,
        IdKind::FontJapanese,
        ValueSyntax::Decimal,
    ),
    reference(
        PartSelector::Exact(HEADER_PART),
        HWPML_2011_HEAD_NAMESPACE,
        "fontRef",
        "other",
        TargetSelector::SamePart,
        IdKind::FontOther,
        ValueSyntax::Decimal,
    ),
    reference(
        PartSelector::Exact(HEADER_PART),
        HWPML_2011_HEAD_NAMESPACE,
        "fontRef",
        "symbol",
        TargetSelector::SamePart,
        IdKind::FontSymbol,
        ValueSyntax::Decimal,
    ),
    reference(
        PartSelector::Exact(HEADER_PART),
        HWPML_2011_HEAD_NAMESPACE,
        "fontRef",
        "user",
        TargetSelector::SamePart,
        IdKind::FontUser,
        ValueSyntax::Decimal,
    ),
    reference(
        PartSelector::Exact(HEADER_PART),
        HWPML_2011_HEAD_NAMESPACE,
        "border",
        "borderFillIDRef",
        TargetSelector::SamePart,
        IdKind::BorderFill,
        ValueSyntax::Decimal,
    ),
    reference(
        PartSelector::Exact(HEADER_PART),
        HWPML_2011_HEAD_NAMESPACE,
        "charPr",
        "borderFillIDRef",
        TargetSelector::SamePart,
        IdKind::BorderFill,
        ValueSyntax::Decimal,
    ),
    reference_optional_u32_max(
        PartSelector::Exact(HEADER_PART),
        HWPML_2011_HEAD_NAMESPACE,
        "paraHead",
        "charPrIDRef",
        TargetSelector::SamePart,
        IdKind::CharacterProperties,
        ValueSyntax::Decimal,
    ),
    reference(
        PartSelector::Exact(HEADER_PART),
        HWPML_2011_HEAD_NAMESPACE,
        "paraPr",
        "tabPrIDRef",
        TargetSelector::SamePart,
        IdKind::TabProperties,
        ValueSyntax::Decimal,
    ),
    reference(
        PartSelector::Exact(HEADER_PART),
        HWPML_2011_HEAD_NAMESPACE,
        "style",
        "charPrIDRef",
        TargetSelector::SamePart,
        IdKind::CharacterProperties,
        ValueSyntax::Decimal,
    ),
    reference(
        PartSelector::Exact(HEADER_PART),
        HWPML_2011_HEAD_NAMESPACE,
        "style",
        "paraPrIDRef",
        TargetSelector::SamePart,
        IdKind::ParagraphProperties,
        ValueSyntax::Decimal,
    ),
    reference(
        PartSelector::Exact(HEADER_PART),
        HWPML_2011_HEAD_NAMESPACE,
        "style",
        "nextStyleIDRef",
        TargetSelector::SamePart,
        IdKind::Style,
        ValueSyntax::Decimal,
    ),
    reference(
        PartSelector::SpineDocument,
        HWPML_2011_PARAGRAPH_NAMESPACE,
        "p",
        "paraPrIDRef",
        TargetSelector::Exact(HEADER_PART),
        IdKind::ParagraphProperties,
        ValueSyntax::Decimal,
    ),
    reference(
        PartSelector::SpineDocument,
        HWPML_2011_PARAGRAPH_NAMESPACE,
        "p",
        "styleIDRef",
        TargetSelector::Exact(HEADER_PART),
        IdKind::Style,
        ValueSyntax::Decimal,
    ),
    reference(
        PartSelector::SpineDocument,
        HWPML_2011_PARAGRAPH_NAMESPACE,
        "run",
        "charPrIDRef",
        TargetSelector::Exact(HEADER_PART),
        IdKind::CharacterProperties,
        ValueSyntax::Decimal,
    ),
    reference(
        PartSelector::SpineDocument,
        HWPML_2011_PARAGRAPH_NAMESPACE,
        "pageBorderFill",
        "borderFillIDRef",
        TargetSelector::Exact(HEADER_PART),
        IdKind::BorderFill,
        ValueSyntax::Decimal,
    ),
    reference_optional_zero(
        PartSelector::SpineDocument,
        HWPML_2011_PARAGRAPH_NAMESPACE,
        "secPr",
        "memoShapeIDRef",
        TargetSelector::Exact(HEADER_PART),
        IdKind::MemoShape,
        ValueSyntax::Decimal,
    ),
    reference_optional_zero(
        PartSelector::SpineDocument,
        HWPML_2011_PARAGRAPH_NAMESPACE,
        "secPr",
        "outlineShapeIDRef",
        TargetSelector::Exact(HEADER_PART),
        IdKind::Numbering,
        ValueSyntax::Decimal,
    ),
];

const fn declaration(
    part: PartSelector,
    namespace: &'static str,
    element: &'static str,
    attribute: &'static str,
    kind: IdKind,
    syntax: ValueSyntax,
) -> DeclarationRule {
    DeclarationRule {
        part,
        namespace,
        element,
        attribute,
        kind: DeclarationKind::Fixed(kind),
        syntax,
    }
}

const fn font_declaration(
    part: PartSelector,
    namespace: &'static str,
    element: &'static str,
    attribute: &'static str,
    syntax: ValueSyntax,
) -> DeclarationRule {
    DeclarationRule {
        part,
        namespace,
        element,
        attribute,
        kind: DeclarationKind::FontByParentLanguage,
        syntax,
    }
}

const fn reference(
    part: PartSelector,
    namespace: &'static str,
    element: &'static str,
    attribute: &'static str,
    target: TargetSelector,
    kind: IdKind,
    syntax: ValueSyntax,
) -> ReferenceRule {
    ReferenceRule {
        part,
        namespace,
        element,
        attribute,
        target,
        kind,
        syntax,
        sentinel: None,
    }
}

const fn reference_optional_zero(
    part: PartSelector,
    namespace: &'static str,
    element: &'static str,
    attribute: &'static str,
    target: TargetSelector,
    kind: IdKind,
    syntax: ValueSyntax,
) -> ReferenceRule {
    ReferenceRule {
        part,
        namespace,
        element,
        attribute,
        target,
        kind,
        syntax,
        sentinel: Some(0),
    }
}

const fn reference_optional_u32_max(
    part: PartSelector,
    namespace: &'static str,
    element: &'static str,
    attribute: &'static str,
    target: TargetSelector,
    kind: IdKind,
    syntax: ValueSyntax,
) -> ReferenceRule {
    ReferenceRule {
        part,
        namespace,
        element,
        attribute,
        target,
        kind,
        syntax,
        sentinel: Some(u32::MAX as u64),
    }
}

struct PendingReference {
    location: IdLocation,
    target: TargetSelector,
    expected_kind: IdKind,
    value: IdValue,
}

type DeclarationKey = (String, IdKind, IdValue);
type ValueKey = (String, IdValue);

struct DeclarationMaps {
    by_key: BTreeMap<DeclarationKey, usize>,
    duplicate_keys: BTreeSet<DeclarationKey>,
    by_value: BTreeMap<ValueKey, Vec<(IdKind, usize)>>,
}

struct IndexBuilder<'a> {
    graph: &'a PackageGraph,
    preservation: &'a PreservationReport,
    profile: IdRuleProfile,
    limits: IdIndexLimits,
    token_stable_keys: BTreeSet<String>,
    declarations: Vec<IdDeclaration>,
    pending_references: Vec<PendingReference>,
    issues: Vec<IdValidationIssue>,
    parts_scanned: usize,
}

impl<'a> IndexBuilder<'a> {
    fn new(
        graph: &'a PackageGraph,
        preservation: &'a PreservationReport,
        profile: IdRuleProfile,
        limits: IdIndexLimits,
    ) -> Result<Self, IdIndexError> {
        let mut token_stable_keys = BTreeSet::new();
        for record in preservation.parts() {
            if record.class() == PreservationClass::TokenStable
                && !token_stable_keys.insert(record.path().collision_key().to_owned())
            {
                return Err(IdIndexError::IdentityMismatch);
            }
        }
        Ok(Self {
            graph,
            preservation,
            profile,
            limits,
            token_stable_keys,
            declarations: Vec::new(),
            pending_references: Vec::new(),
            issues: Vec::new(),
            parts_scanned: 0,
        })
    }

    fn build<R: Read + Seek>(
        mut self,
        reader: &mut BoundedZipReader<R>,
    ) -> Result<IdIndex, IdIndexError> {
        for record in self.preservation.parts() {
            if record.class() != PreservationClass::TokenStable {
                continue;
            }
            self.parts_scanned = self
                .parts_scanned
                .checked_add(1)
                .ok_or(IdIndexError::LimitExceeded { limit: "parts" })?;
            if self.parts_scanned > self.limits.config().max_parts {
                return Err(IdIndexError::LimitExceeded { limit: "parts" });
            }
            let bytes = reader.read_entry(record.source_entry_index())?;
            let document = PreservingXmlDocument::parse(&bytes)?;
            if document.original_sha256() != record.raw_sha256() {
                return Err(IdIndexError::IdentityMismatch);
            }
            self.scan_document(record, &document)?;
        }
        self.resolve()
    }

    fn scan_document(
        &mut self,
        part: &PartPreservationRecord,
        document: &PreservingXmlDocument,
    ) -> Result<(), IdIndexError> {
        for element_index in 0..document.elements().len() {
            let attribute_count = document.elements()[element_index].attributes().len();
            for attribute_index in 0..attribute_count {
                self.scan_attribute(part, document, element_index, attribute_index)?;
            }
        }
        Ok(())
    }

    fn scan_attribute(
        &mut self,
        part: &PartPreservationRecord,
        document: &PreservingXmlDocument,
        element_index: usize,
        attribute_index: usize,
    ) -> Result<(), IdIndexError> {
        let element = &document.elements()[element_index];
        let attribute = &element.attributes()[attribute_index];
        if attribute.is_namespace_declaration() {
            return Ok(());
        }
        let declaration_rule = matching_declaration_rule(
            self.graph,
            part,
            element.name().namespace(),
            element.name().local_name(),
            attribute.name().namespace(),
            attribute.name().local_name(),
        )?;
        let reference_rule = matching_reference_rule(
            self.graph,
            part,
            element.name().namespace(),
            element.name().local_name(),
            attribute.name().namespace(),
            attribute.name().local_name(),
        )?;
        if declaration_rule.is_some() && reference_rule.is_some() {
            return Err(IdIndexError::AmbiguousRule);
        }
        let location = IdLocation {
            part: part.path().clone(),
            element_index,
            attribute_index,
            value_span: attribute.value_span(),
        };
        if let Some(rule) = declaration_rule {
            self.scan_declaration(part, document, element_index, attribute, location, rule)
        } else if let Some(rule) = reference_rule {
            self.scan_reference(attribute.semantic_value(), location, rule)
        } else if !known_zero_sentinel(
            part,
            element.name().namespace(),
            element.name().local_name(),
            attribute.name().namespace(),
            attribute.name().local_name(),
            attribute.semantic_value(),
        ) && supported_namespace(element.name().namespace())
            && is_id_like(attribute.name().local_name())
        {
            self.push_issue(IdValidationIssue {
                kind: IdIssueKind::UnknownIdLikeAttribute,
                source: location,
                related: None,
                expected_kind: None,
                actual_kind: None,
            })
        } else {
            Ok(())
        }
    }

    fn scan_declaration(
        &mut self,
        part: &PartPreservationRecord,
        document: &PreservingXmlDocument,
        element_index: usize,
        attribute: &crate::XmlAttributeToken,
        location: IdLocation,
        rule: &DeclarationRule,
    ) -> Result<(), IdIndexError> {
        if known_declaration_sentinel(
            part,
            document.elements()[element_index].name().namespace(),
            document.elements()[element_index].name().local_name(),
            attribute.name().namespace(),
            attribute.name().local_name(),
            attribute.semantic_value(),
        ) {
            return Ok(());
        }
        let Some(kind) = declaration_kind(document, element_index, rule) else {
            return self.push_issue(IdValidationIssue {
                kind: IdIssueKind::MalformedValue,
                source: location,
                related: None,
                expected_kind: None,
                actual_kind: None,
            });
        };
        if let Some(value) = self.parse_value(
            &location,
            attribute.semantic_value(),
            rule.syntax,
            Some(kind),
        )? {
            self.push_declaration(IdDeclaration {
                location,
                kind,
                value,
            })?;
        }
        Ok(())
    }

    fn scan_reference(
        &mut self,
        raw: &str,
        location: IdLocation,
        rule: &ReferenceRule,
    ) -> Result<(), IdIndexError> {
        if rule
            .sentinel
            .is_some_and(|sentinel| decimal_equals(raw, sentinel))
        {
            return Ok(());
        }
        if let Some(value) = self.parse_value(&location, raw, rule.syntax, Some(rule.kind))? {
            self.push_reference(PendingReference {
                location,
                target: rule.target,
                expected_kind: rule.kind,
                value,
            })?;
        }
        Ok(())
    }

    fn parse_value(
        &mut self,
        location: &IdLocation,
        raw: &str,
        syntax: ValueSyntax,
        expected_kind: Option<IdKind>,
    ) -> Result<Option<IdValue>, IdIndexError> {
        if raw.len() > self.limits.config().max_value_bytes {
            return Err(IdIndexError::LimitExceeded {
                limit: "id_value_bytes",
            });
        }
        let value = match syntax {
            ValueSyntax::Decimal
                if !raw.is_empty() && raw.bytes().all(|byte| byte.is_ascii_digit()) =>
            {
                raw.parse::<u64>().ok().map(IdValue::Decimal)
            }
            ValueSyntax::Text if valid_text_id(raw) => Some(IdValue::Text(raw.to_owned())),
            ValueSyntax::Decimal | ValueSyntax::Text => None,
        };
        if value.is_none() {
            self.push_issue(IdValidationIssue {
                kind: IdIssueKind::MalformedValue,
                source: location.clone(),
                related: None,
                expected_kind,
                actual_kind: None,
            })?;
        }
        Ok(value)
    }

    fn push_declaration(&mut self, declaration: IdDeclaration) -> Result<(), IdIndexError> {
        if self.declarations.len() >= self.limits.config().max_declarations {
            return Err(IdIndexError::LimitExceeded {
                limit: "declarations",
            });
        }
        self.declarations
            .try_reserve(1)
            .map_err(|_| IdIndexError::AllocationFailed)?;
        self.declarations.push(declaration);
        Ok(())
    }

    fn push_reference(&mut self, reference: PendingReference) -> Result<(), IdIndexError> {
        if self.pending_references.len() >= self.limits.config().max_references {
            return Err(IdIndexError::LimitExceeded {
                limit: "references",
            });
        }
        self.pending_references
            .try_reserve(1)
            .map_err(|_| IdIndexError::AllocationFailed)?;
        self.pending_references.push(reference);
        Ok(())
    }

    fn push_issue(&mut self, issue: IdValidationIssue) -> Result<(), IdIndexError> {
        if self.issues.len() >= self.limits.config().max_issues {
            return Err(IdIndexError::LimitExceeded { limit: "issues" });
        }
        self.issues
            .try_reserve(1)
            .map_err(|_| IdIndexError::AllocationFailed)?;
        self.issues.push(issue);
        Ok(())
    }

    fn resolve(mut self) -> Result<IdIndex, IdIndexError> {
        let maps = self.build_declaration_maps()?;
        let references = self.resolve_references(&maps)?;
        if !self.issues.is_empty() {
            self.issues.sort_unstable();
            return Err(IdIndexError::Validation(IdValidationReport {
                issues: self.issues,
            }));
        }
        Ok(IdIndex {
            profile_version: self.profile.version(),
            parts_scanned: self.parts_scanned,
            declarations: self.declarations,
            references,
        })
    }

    fn build_declaration_maps(&mut self) -> Result<DeclarationMaps, IdIndexError> {
        let mut by_key = BTreeMap::new();
        let mut duplicate_keys = BTreeSet::new();
        let mut by_value: BTreeMap<ValueKey, Vec<(IdKind, usize)>> = BTreeMap::new();
        for index in 0..self.declarations.len() {
            let declaration = &self.declarations[index];
            let location = declaration.location.clone();
            let kind = declaration.kind;
            let value = declaration.value.clone();
            let key = (
                location.part.collision_key().to_owned(),
                kind,
                value.clone(),
            );
            if let Some(previous) = by_key.insert(key.clone(), index) {
                duplicate_keys.insert(key);
                let related = self.declarations[previous].location.clone();
                self.push_issue(IdValidationIssue {
                    kind: IdIssueKind::DuplicateDeclaration,
                    source: location.clone(),
                    related: Some(related),
                    expected_kind: Some(kind),
                    actual_kind: Some(kind),
                })?;
            }
            let value_key = (location.part.collision_key().to_owned(), value);
            by_value.entry(value_key).or_default().push((kind, index));
        }
        Ok(DeclarationMaps {
            by_key,
            duplicate_keys,
            by_value,
        })
    }

    fn resolve_references(
        &mut self,
        maps: &DeclarationMaps,
    ) -> Result<Vec<IdReference>, IdIndexError> {
        let pending = std::mem::take(&mut self.pending_references);
        let mut references = Vec::new();
        references
            .try_reserve_exact(pending.len())
            .map_err(|_| IdIndexError::AllocationFailed)?;
        for reference in pending {
            let target_part = match self.target_part(&reference) {
                Ok(path) => path,
                Err(kind) => {
                    self.push_issue(IdValidationIssue {
                        kind,
                        source: reference.location,
                        related: None,
                        expected_kind: Some(reference.expected_kind),
                        actual_kind: None,
                    })?;
                    continue;
                }
            };
            let key = (
                target_part.collision_key().to_owned(),
                reference.expected_kind,
                reference.value.clone(),
            );
            if maps.duplicate_keys.contains(&key) {
                continue;
            }
            if let Some(declaration_index) = maps.by_key.get(&key).copied() {
                references.push(IdReference {
                    location: reference.location,
                    target_part,
                    expected_kind: reference.expected_kind,
                    declaration_index,
                    value: reference.value,
                });
                continue;
            }
            let value_key = (target_part.collision_key().to_owned(), reference.value);
            let wrong_type = maps
                .by_value
                .get(&value_key)
                .and_then(|matches| matches.first().copied());
            let (kind, actual_kind, related) = wrong_type.map_or(
                (IdIssueKind::DanglingReference, None, None),
                |(actual_kind, declaration_index)| {
                    (
                        IdIssueKind::WrongTypeReference,
                        Some(actual_kind),
                        Some(self.declarations[declaration_index].location.clone()),
                    )
                },
            );
            self.push_issue(IdValidationIssue {
                kind,
                source: reference.location,
                related,
                expected_kind: Some(reference.expected_kind),
                actual_kind,
            })?;
        }
        Ok(references)
    }

    fn target_part(&self, reference: &PendingReference) -> Result<PackagePath, IdIssueKind> {
        let path = match reference.target {
            TargetSelector::SamePart => reference.location.part.clone(),
            TargetSelector::Exact(expected) => self
                .graph
                .parts
                .iter()
                .find(|part| part.path.as_str() == expected)
                .map(|part| part.path.clone())
                .ok_or(IdIssueKind::TargetPartMissing)?,
        };
        if !self.token_stable_keys.contains(path.collision_key()) {
            return Err(IdIssueKind::TargetPartNotTokenStable);
        }
        Ok(path)
    }
}

fn matching_declaration_rule(
    graph: &PackageGraph,
    part: &PartPreservationRecord,
    element_namespace: Option<&str>,
    element_local: &str,
    attribute_namespace: Option<&str>,
    attribute_local: &str,
) -> Result<Option<&'static DeclarationRule>, IdIndexError> {
    let mut matched = None;
    for rule in DECLARATION_RULES {
        if part_matches(rule.part, graph, part)
            && rule_namespace_matches(element_namespace, rule.namespace)
            && element_local == rule.element
            && attribute_namespace.is_none()
            && attribute_local == rule.attribute
            && matched.replace(rule).is_some()
        {
            return Err(IdIndexError::AmbiguousRule);
        }
    }
    Ok(matched)
}

fn matching_reference_rule(
    graph: &PackageGraph,
    part: &PartPreservationRecord,
    element_namespace: Option<&str>,
    element_local: &str,
    attribute_namespace: Option<&str>,
    attribute_local: &str,
) -> Result<Option<&'static ReferenceRule>, IdIndexError> {
    let mut matched = None;
    for rule in REFERENCE_RULES {
        if part_matches(rule.part, graph, part)
            && rule_namespace_matches(element_namespace, rule.namespace)
            && element_local == rule.element
            && attribute_namespace.is_none()
            && attribute_local == rule.attribute
            && matched.replace(rule).is_some()
        {
            return Err(IdIndexError::AmbiguousRule);
        }
    }
    Ok(matched)
}

fn part_matches(
    selector: PartSelector,
    graph: &PackageGraph,
    part: &PartPreservationRecord,
) -> bool {
    match selector {
        PartSelector::PackageDocument => part.path() == &graph.package_document,
        PartSelector::Exact(path) => part.path().as_str() == path,
        PartSelector::SpineDocument => part.role() == PartRole::SpineDocument,
    }
}

fn supported_namespace(namespace: Option<&str>) -> bool {
    matches!(
        namespace,
        Some(
            OPF_NAMESPACE
                | OPF_NAMESPACE_HANCOM_2020
                | HWPML_2011_HEAD_NAMESPACE
                | HWPML_2011_PARAGRAPH_NAMESPACE
        )
    )
}

fn rule_namespace_matches(actual: Option<&str>, expected: &str) -> bool {
    actual == Some(expected)
        || (expected == OPF_NAMESPACE && actual == Some(OPF_NAMESPACE_HANCOM_2020))
}

fn is_id_like(local_name: &str) -> bool {
    local_name == "id"
        || local_name == "Id"
        || local_name == "idref"
        || local_name == "idRef"
        || local_name.ends_with("IDRef")
}

fn known_zero_sentinel(
    part: &PartPreservationRecord,
    element_namespace: Option<&str>,
    element_local: &str,
    attribute_namespace: Option<&str>,
    attribute_local: &str,
    value: &str,
) -> bool {
    part.path().as_str() == HEADER_PART
        && element_namespace == Some(HWPML_2011_HEAD_NAMESPACE)
        && element_local == "heading"
        && attribute_namespace.is_none()
        && attribute_local == "idRef"
        && decimal_is_zero(value)
}

fn decimal_is_zero(value: &str) -> bool {
    decimal_equals(value, 0)
}

fn decimal_equals(value: &str, expected: u64) -> bool {
    !value.is_empty()
        && value.bytes().all(|byte| byte.is_ascii_digit())
        && value.parse::<u64>() == Ok(expected)
}

fn known_declaration_sentinel(
    part: &PartPreservationRecord,
    element_namespace: Option<&str>,
    element_local: &str,
    attribute_namespace: Option<&str>,
    attribute_local: &str,
    value: &str,
) -> bool {
    let paragraph_zero = part.role() == PartRole::SpineDocument
        && element_namespace == Some(HWPML_2011_PARAGRAPH_NAMESPACE)
        && element_local == "p"
        && attribute_namespace.is_none()
        && attribute_local == "id"
        && decimal_is_zero(value);
    let empty_package = part.path().as_str() == "Contents/content.hpf"
        && rule_namespace_matches(element_namespace, OPF_NAMESPACE)
        && element_local == "package"
        && attribute_namespace.is_none()
        && attribute_local == "id"
        && value.is_empty();
    let empty_section_metadata = part.role() == PartRole::SpineDocument
        && element_namespace == Some(HWPML_2011_PARAGRAPH_NAMESPACE)
        && matches!(element_local, "secPr" | "colPr")
        && attribute_namespace.is_none()
        && attribute_local == "id"
        && value.is_empty();
    paragraph_zero || empty_package || empty_section_metadata
}

fn valid_text_id(raw: &str) -> bool {
    !raw.is_empty()
        && !raw
            .chars()
            .any(|character| character.is_control() || character.is_whitespace())
        && !raw.contains([':', '/', '\\', '?', '#', '&'])
}

fn declaration_kind(
    document: &PreservingXmlDocument,
    element_index: usize,
    rule: &DeclarationRule,
) -> Option<IdKind> {
    match rule.kind {
        DeclarationKind::Fixed(kind) => Some(kind),
        DeclarationKind::FontByParentLanguage => {
            let parent_index = document.elements().get(element_index)?.parent()?;
            let parent = document.elements().get(parent_index)?;
            if parent.name().namespace() != Some(HWPML_2011_HEAD_NAMESPACE)
                || parent.name().local_name() != "fontface"
            {
                return None;
            }
            let language = parent.attributes().iter().find(|attribute| {
                attribute.name().namespace().is_none() && attribute.name().local_name() == "lang"
            })?;
            match language.semantic_value() {
                "HANGUL" => Some(IdKind::FontHangul),
                "LATIN" => Some(IdKind::FontLatin),
                "HANJA" => Some(IdKind::FontHanja),
                "JAPANESE" => Some(IdKind::FontJapanese),
                "OTHER" => Some(IdKind::FontOther),
                "SYMBOL" => Some(IdKind::FontSymbol),
                "USER" => Some(IdKind::FontUser),
                _ => None,
            }
        }
    }
}
