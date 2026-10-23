//! Closed dispatch to the existing strict candidate families. No execution authority is issued.
use super::super::stored_literal_replacement as literal;
use literal::{atoms, case, controls, number_controls, paragraph_styles, regex, review, selector,
    styles, text_styles, unicode, whitespace, width, sort, sort_groups, fonts};
use regex::insertions;
use unicode::matches as unicode_matches;
use fonts::options as font_options;
use literal::named_styles;
use named_styles::options as named_options;
use literal::personal_info;
use crate::form_stored_provider::StoredFormProvider;
use artifact_service::{ArtifactMetadataRepository, ArtifactScanner, EncryptedBlobStore};
use domain_ir::{ReferenceAuxiliaryLimitConfig, ReferenceAuxiliaryLimits};
use hwpx_package::{WriterLimits, document_import::search::SourceSearchLimits};
use revision_service::RevisionRepository;
use thiserror::Error;

/// Already validated finite budgets; request JSON cannot supply or enlarge these limits.
#[derive(Clone, Copy, Debug)]
pub struct SearchMutationLimits {
    pub search: SourceSearchLimits,
    pub auxiliary: ReferenceAuxiliaryLimits,
    pub writer: WriterLimits,
}
impl SearchMutationLimits {
    /// # Errors
    /// Fails closed if the default auxiliary configuration is not valid.
    pub fn standard() -> Result<Self, SearchMutationError> {
        Ok(Self {
            search: SourceSearchLimits::default(),
            auxiliary: ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig::default())
                .map_err(|_| SearchMutationError::Limits)?,
            writer: WriterLimits::default(),
        })
    }
}

macro_rules! prepare_family {
    (text, $module:ident, $request:ident, $provider:ident, $raw:ident, $limits:ident, $now:ident) => {
        $module::$request::prepare_json($provider, $raw, $limits.search, $limits.writer, $now)
    };
    (number, $module:ident, $request:ident, $provider:ident, $raw:ident, $limits:ident, $now:ident) => {
        $module::$request::prepare_json($provider, $raw, $limits.search, $limits.auxiliary, $limits.writer, $now)
    };
}
// One closed table owns schema classification, original typed errors/receipts and dispatch.
// Receipt access only borrows metadata; delivery always calls the original fresh verification.
macro_rules! families {
    ($(($variant:ident, $module:ident, $request:ident, $prepared:ident, $receipt:ident,
        $error:path, $schema:ident, $budget:ident)),+ $(,)?) => {
        #[derive(Clone, Copy, Debug, Eq, PartialEq)]
        pub(super) enum Family { $($variant),+ }
        /// Exact schemas accepted by this mutation dispatcher, not a capability/route claim.
        pub const SEARCH_MUTATION_REQUEST_SCHEMAS: &[&str] = &[$($module::$schema),+];
        pub(super) fn classify(schema: &str) -> Option<Family> {
            match schema { $($module::$schema => Some(Family::$variant),)+ _ => None }
        }
        #[derive(Debug, Error)]
        pub enum SearchMutationError {
            #[error("search_mutation_limits_rejected")]
            Limits,
            $(#[error("search_mutation_family_rejected")]
            $variant(#[source] $error),)+
        }
        /// Owns the original prepared candidate, without cloning or rebuilding its source.
        #[derive(Debug)]
        pub enum PreparedStoredSearchMutation { $($variant(Box<$module::$prepared>)),+ }
        /// Not a proof or execution capability. The reference cannot outlive its candidate.
        pub enum SearchMutationReceiptRef<'a> { $($variant(&'a $module::$receipt)),+ }
        impl PreparedStoredSearchMutation {
            pub(crate) fn compiler_view(&self) -> super::compiled_search::CompilationView<'_> {
                match self { $(Self::$variant(candidate) => candidate.compiler_view()),+ }
            }
            #[must_use]
            pub const fn schema_version(&self) -> &'static str {
                match self { $(Self::$variant(_) => $module::$schema),+ }
            }
            #[must_use]
            pub fn receipt(&self) -> SearchMutationReceiptRef<'_> {
                match self { $(Self::$variant(candidate) => SearchMutationReceiptRef::$variant(candidate.receipt())),+ }
            }
            /// # Errors
            /// Preserves the selected family's current access/source/head and integrity checks.
            pub fn verify<R, B, S, V>(&self, provider: &StoredFormProvider<'_, R, B, S, V>, now: u64)
                -> Result<(), SearchMutationError>
            where R: ArtifactMetadataRepository, B: EncryptedBlobStore, S: ArtifactScanner, V: RevisionRepository {
                match self { $(Self::$variant(candidate) => candidate.verify(provider, now)
                    .map(|_| ()).map_err(SearchMutationError::$variant)),+ }
            }
            /// # Errors
            /// No alternate byte accessor: original checks include the consumer-final head.
            pub fn with_verified_bytes<R, B, S, V, T>(&self, provider: &StoredFormProvider<'_, R, B, S, V>,
                now: u64, consume: impl FnOnce(&[u8]) -> T) -> Result<T, SearchMutationError>
            where R: ArtifactMetadataRepository, B: EncryptedBlobStore, S: ArtifactScanner, V: RevisionRepository {
                match self { $(Self::$variant(candidate) => candidate.with_verified_bytes(provider, now, consume)
                    .map_err(SearchMutationError::$variant)),+ }
            }
            /// # Errors
            /// Delegates the original denial, after fresh verification; never authorizes execution.
            pub fn require_current_product_route<R, B, S, V>(&self, provider: &StoredFormProvider<'_, R, B, S, V>, now: u64)
                -> Result<(), SearchMutationError>
            where R: ArtifactMetadataRepository, B: EncryptedBlobStore, S: ArtifactScanner, V: RevisionRepository {
                match self { $(Self::$variant(candidate) => candidate.require_current_product_route(provider, now)
                    .map_err(SearchMutationError::$variant)),+ }
            }
        }
        pub(super) fn prepare<R, B, S, V>(family: Family, provider: &StoredFormProvider<'_, R, B, S, V>,
            raw: &[u8], limits: SearchMutationLimits, now: u64) -> Result<PreparedStoredSearchMutation, SearchMutationError>
        where R: ArtifactMetadataRepository, B: EncryptedBlobStore, S: ArtifactScanner, V: RevisionRepository {
            match family { $(Family::$variant => prepare_family!($budget, $module, $request, provider, raw, limits, now)
                .map(|candidate| PreparedStoredSearchMutation::$variant(Box::new(candidate)))
                .map_err(SearchMutationError::$variant)),+ }
        }
    }
}
families!(
    (Literal, literal, StoredLiteralReplacementProductRequest, PreparedStoredLiteralReplacementProduct, LiteralReplacementProductReceipt,
        literal::LiteralReplacementProductError, LITERAL_REPLACEMENT_PRODUCT_REQUEST_SCHEMA, text),
    (LiteralAtoms, atoms, StoredLiteralTextAtomProductRequest, PreparedStoredLiteralTextAtomProduct, LiteralTextAtomProductReceipt,
        literal::LiteralReplacementProductError, LITERAL_TEXT_ATOM_PRODUCT_REQUEST_SCHEMA, text),
    (ReviewLiteral, review, StoredReviewLiteralProductRequest, PreparedStoredReviewLiteralProduct, ReviewLiteralProductReceipt,
        literal::LiteralReplacementProductError, REVIEW_LITERAL_PRODUCT_REQUEST_SCHEMA, text),
    (SelectorLiteral, selector, StoredSelectorLiteralProductRequest, PreparedStoredSelectorLiteralProduct, SelectorLiteralProductReceipt,
        literal::LiteralReplacementProductError, SELECTOR_LITERAL_PRODUCT_REQUEST_SCHEMA, text),
    (Regex, regex, StoredRegexReplacementProductRequest, PreparedStoredRegexReplacementProduct, RegexReplacementProductReceipt,
        regex::RegexReplacementProductError, REGEX_REPLACEMENT_PRODUCT_REQUEST_SCHEMA, text),
    (RegexInsertion, insertions, StoredRegexInsertionProductRequest, PreparedStoredRegexInsertionProduct, RegexInsertionProductReceipt,
        regex::RegexReplacementProductError, REGEX_INSERTION_PRODUCT_REQUEST_SCHEMA, text),
    (CharacterStyle, styles, StoredCharacterStyleProductRequest, PreparedStoredCharacterStyleProduct, CharacterStyleProductReceipt,
        styles::CharacterStyleProductError, CHARACTER_STYLE_PRODUCT_REQUEST_SCHEMA, text),
    (TextStyle, text_styles, StoredTextStyleProductRequest, PreparedStoredTextStyleProduct, TextStyleProductReceipt,
        text_styles::TextStyleProductError, TEXT_STYLE_PRODUCT_REQUEST_SCHEMA, text),
    (ParagraphStyle, paragraph_styles, StoredParagraphStyleProductRequest, PreparedStoredParagraphStyleProduct, ParagraphStyleProductReceipt,
        paragraph_styles::ParagraphStyleProductError, PARAGRAPH_STYLE_PRODUCT_REQUEST_SCHEMA, text),
    (UnicodeScope, unicode, StoredUnicodeProductRequest, PreparedStoredUnicodeProduct, UnicodeProductReceipt,
        unicode::UnicodeProductError, UNICODE_PRODUCT_REQUEST_SCHEMA, text),
    (UnicodeMatches, unicode_matches, StoredUnicodeMatchProductRequest, PreparedStoredUnicodeMatchProduct, UnicodeMatchProductReceipt,
        unicode_matches::UnicodeMatchProductError, UNICODE_MATCH_PRODUCT_REQUEST_SCHEMA, text),
    (Case, case, StoredCaseProductRequest, PreparedStoredCaseProduct, CaseProductReceipt,
        case::CaseProductError, CASE_PRODUCT_REQUEST_SCHEMA, text),
    (Width, width, StoredWidthProductRequest, PreparedStoredWidthProduct, WidthProductReceipt,
        width::WidthProductError, WIDTH_PRODUCT_REQUEST_SCHEMA, text),
    (Whitespace, whitespace, StoredWhitespaceProductRequest, PreparedStoredWhitespaceProduct, WhitespaceProductReceipt,
        whitespace::WhitespaceProductError, WHITESPACE_PRODUCT_REQUEST_SCHEMA, text),
    (TextControl, controls, StoredControlProductRequest, PreparedStoredControlProduct, ControlProductReceipt,
        controls::ControlProductError, CONTROL_PRODUCT_REQUEST_SCHEMA, text),
    (NumberControl, number_controls, StoredNumberControlProductRequest, PreparedStoredNumberControlProduct, NumberControlProductReceipt,
        number_controls::NumberControlProductError, NUMBER_CONTROL_PRODUCT_REQUEST_SCHEMA, number),
    (ParagraphSort, sort, StoredParagraphSortProductRequest, PreparedStoredParagraphSortProduct, ParagraphSortProductReceipt,
        sort::ParagraphSortProductError, PARAGRAPH_SORT_PRODUCT_REQUEST_SCHEMA, text),
    (ParagraphSortGroups, sort_groups, StoredParagraphSortGroupsProductRequest, PreparedStoredParagraphSortGroupsProduct, ParagraphSortGroupsProductReceipt,
        sort_groups::ParagraphSortGroupsProductError, PARAGRAPH_SORT_GROUPS_PRODUCT_REQUEST_SCHEMA, text),
    (Font, fonts, StoredFontProductRequest, PreparedStoredFontProduct, FontProductReceipt,
        fonts::FontProductError, FONT_PRODUCT_REQUEST_SCHEMA, text),
    (FontOptions, font_options, StoredFontOptionsMutationRequest, PreparedStoredFontOptionsMutation, FontOptionsProductReceipt,
        font_options::FontOptionsProductError, FONT_OPTIONS_REQUEST_SCHEMA, text),
    (NamedStyle, named_styles, StoredNamedStyleMutationRequest, PreparedStoredNamedStyleMutation, NamedStyleProductReceipt,
        named_styles::NamedStyleProductError, NAMED_STYLE_PRODUCT_REQUEST_SCHEMA, text),
    (NamedStyleOptions, named_options, StoredNamedStyleOptionsMutationRequest, PreparedStoredNamedStyleOptionsMutation, NamedStyleOptionsProductReceipt,
        named_styles::NamedStyleProductError, NAMED_STYLE_OPTIONS_REQUEST_SCHEMA, text),
    (PersonalInfoMask, personal_info, StoredPersonalInfoMaskMutationRequest, PreparedStoredPersonalInfoMaskMutation, PersonalInfoMaskProductReceipt,
        personal_info::PersonalInfoMaskProductError, PERSONAL_INFO_MASK_PRODUCT_SCHEMA, text),
);
impl PreparedStoredSearchMutation {
    pub(crate) fn personal_info_mask_inventory(&self)->Option<&hwpx_package::document_import::search::replacement::atoms::personal_info::SourcePersonalInfoMaskEditInventory>{
        match self{Self::PersonalInfoMask(candidate)=>Some(candidate.compiler_mask_inventory()),_=>None}
    }
    pub(crate) fn font_inventory(&self)->Option<&hwpx_package::document_import::search::replacement::atoms::styles::fonts::inventory::SourceFontEditInventory>{
        match self{Self::Font(candidate)=>Some(candidate.compiler_font_inventory()),Self::FontOptions(candidate)=>Some(candidate.compiler_font_inventory()),_=>None}
    }
    pub(crate) fn sort_splices(&self)->Option<&hwpx_package::document_import::search::replacement::atoms::sort::intents::SourceParagraphSortSpliceInventory> {
        match self {Self::ParagraphSort(candidate)=>Some(candidate.compiler_sort_splices()),Self::ParagraphSortGroups(candidate)=>Some(candidate.compiler_sort_splices()),_=>None}
    }
}
impl std::fmt::Debug for SearchMutationReceiptRef<'_> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str("SearchMutationReceiptRef(<redacted>; candidate_only)")
    }
}
