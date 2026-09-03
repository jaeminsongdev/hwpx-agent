use std::collections::{BTreeMap, BTreeSet};

use quick_xml::escape::{escape, unescape};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::paragraph_style::{CompatibleHeading, Heading, HeadingType, ParagraphStyleCatalog};
use crate::preserving_xml::{
    PreservingXmlDocument, PreservingXmlError, XmlAttributeToken, XmlElementToken, XmlTokenKind,
};

pub const LIST_DEFINITION_PROFILE_ID: &str = "hwpx-agent.list-definition/1";

const HEAD_NS: &str = "http://www.hancom.co.kr/hwpml/2011/head";
const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const LEVEL_COUNT: usize = 10;
const BULLET_XML_LEVEL: u8 = 0;
const NO_CHARACTER_STYLE: u32 = u32::MAX;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ListDefinitionLimitConfig {
    pub input_bytes: usize,
    pub elements: usize,
    pub numberings: usize,
    pub bullets: usize,
    pub levels: usize,
    pub sequence_items: usize,
    pub reference_items: usize,
    pub text_bytes: usize,
}

impl Default for ListDefinitionLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 2 * 1024 * 1024,
            elements: 32_768,
            numberings: 4_096,
            bullets: 4_096,
            levels: 40_960,
            sequence_items: 65_536,
            reference_items: 65_536,
            text_bytes: 256,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct ListDefinitionLimits(ListDefinitionLimitConfig);

impl ListDefinitionLimits {
    pub const HARD_MAX_INPUT_BYTES: usize = 4 * 1024 * 1024;
    pub const HARD_MAX_ELEMENTS: usize = 131_072;
    pub const HARD_MAX_NUMBERINGS: usize = 8_192;
    pub const HARD_MAX_BULLETS: usize = 8_192;
    pub const HARD_MAX_LEVELS: usize = 81_920;
    pub const HARD_MAX_SEQUENCE_ITEMS: usize = 262_144;
    pub const HARD_MAX_REFERENCE_ITEMS: usize = 262_144;
    pub const HARD_MAX_TEXT_BYTES: usize = 1_024;

    /// Creates a finite current-Hangul-2020 list-definition limit set.
    ///
    /// # Errors
    ///
    /// Rejects zero values and values above their hard ceilings.
    pub fn new(config: ListDefinitionLimitConfig) -> Result<Self, ListDefinitionError> {
        let values = [
            (config.input_bytes, Self::HARD_MAX_INPUT_BYTES),
            (config.elements, Self::HARD_MAX_ELEMENTS),
            (config.numberings, Self::HARD_MAX_NUMBERINGS),
            (config.bullets, Self::HARD_MAX_BULLETS),
            (config.levels, Self::HARD_MAX_LEVELS),
            (config.sequence_items, Self::HARD_MAX_SEQUENCE_ITEMS),
            (config.reference_items, Self::HARD_MAX_REFERENCE_ITEMS),
            (config.text_bytes, Self::HARD_MAX_TEXT_BYTES),
        ];
        if values
            .into_iter()
            .any(|(value, ceiling)| value == 0 || value > ceiling)
        {
            return Err(ListDefinitionError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> ListDefinitionLimitConfig {
        self.0
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum ListAlignment {
    Left,
    Center,
    Right,
}

impl ListAlignment {
    fn parse(value: &str) -> Result<Self, ListDefinitionError> {
        match value {
            "LEFT" => Ok(Self::Left),
            "CENTER" => Ok(Self::Center),
            "RIGHT" => Ok(Self::Right),
            _ => Err(ListDefinitionError::InvalidEnum),
        }
    }

    const fn as_str(self) -> &'static str {
        match self {
            Self::Left => "LEFT",
            Self::Center => "CENTER",
            Self::Right => "RIGHT",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum TextOffsetUnit {
    Percent,
    HwpUnit,
}

impl TextOffsetUnit {
    fn parse(value: &str) -> Result<Self, ListDefinitionError> {
        match value {
            "PERCENT" => Ok(Self::Percent),
            "HWPUNIT" => Ok(Self::HwpUnit),
            _ => Err(ListDefinitionError::InvalidEnum),
        }
    }

    const fn as_str(self) -> &'static str {
        match self {
            Self::Percent => "PERCENT",
            Self::HwpUnit => "HWPUNIT",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum NumberFormat {
    Digit,
    CircledDigit,
    RomanCapital,
    RomanSmall,
    LatinCapital,
    LatinSmall,
    CircledLatinCapital,
    CircledLatinSmall,
    HangulSyllable,
    CircledHangulSyllable,
    HangulJamo,
    CircledHangulJamo,
    HangulPhonetic,
    Ideograph,
    CircledIdeograph,
    DecagonCircle,
    DecagonCircleHanja,
    Symbol,
    UserChar,
    Symbol2,
    Image,
    TwoDigit,
}

impl NumberFormat {
    pub(crate) fn parse(value: &str) -> Result<Self, ListDefinitionError> {
        match value {
            "DIGIT" => Ok(Self::Digit),
            "CIRCLED_DIGIT" => Ok(Self::CircledDigit),
            "ROMAN_CAPITAL" => Ok(Self::RomanCapital),
            "ROMAN_SMALL" => Ok(Self::RomanSmall),
            "LATIN_CAPITAL" => Ok(Self::LatinCapital),
            "LATIN_SMALL" => Ok(Self::LatinSmall),
            "CIRCLED_LATIN_CAPITAL" => Ok(Self::CircledLatinCapital),
            "CIRCLED_LATIN_SMALL" => Ok(Self::CircledLatinSmall),
            "HANGUL_SYLLABLE" => Ok(Self::HangulSyllable),
            "CIRCLED_HANGUL_SYLLABLE" => Ok(Self::CircledHangulSyllable),
            "HANGUL_JAMO" => Ok(Self::HangulJamo),
            "CIRCLED_HANGUL_JAMO" => Ok(Self::CircledHangulJamo),
            "HANGUL_PHONETIC" => Ok(Self::HangulPhonetic),
            "IDEOGRAPH" => Ok(Self::Ideograph),
            "CIRCLED_IDEOGRAPH" => Ok(Self::CircledIdeograph),
            "DECAGON_CIRCLE" => Ok(Self::DecagonCircle),
            "DECAGON_CIRCLE_HANJA" => Ok(Self::DecagonCircleHanja),
            "SYMBOL" => Ok(Self::Symbol),
            "USER_CHAR" => Ok(Self::UserChar),
            "SYMBOL2" => Ok(Self::Symbol2),
            "IMAGE" => Ok(Self::Image),
            "2DIGIT" => Ok(Self::TwoDigit),
            _ => Err(ListDefinitionError::InvalidEnum),
        }
    }

    pub(crate) const fn as_str(self) -> &'static str {
        match self {
            Self::Digit => "DIGIT",
            Self::CircledDigit => "CIRCLED_DIGIT",
            Self::RomanCapital => "ROMAN_CAPITAL",
            Self::RomanSmall => "ROMAN_SMALL",
            Self::LatinCapital => "LATIN_CAPITAL",
            Self::LatinSmall => "LATIN_SMALL",
            Self::CircledLatinCapital => "CIRCLED_LATIN_CAPITAL",
            Self::CircledLatinSmall => "CIRCLED_LATIN_SMALL",
            Self::HangulSyllable => "HANGUL_SYLLABLE",
            Self::CircledHangulSyllable => "CIRCLED_HANGUL_SYLLABLE",
            Self::HangulJamo => "HANGUL_JAMO",
            Self::CircledHangulJamo => "CIRCLED_HANGUL_JAMO",
            Self::HangulPhonetic => "HANGUL_PHONETIC",
            Self::Ideograph => "IDEOGRAPH",
            Self::CircledIdeograph => "CIRCLED_IDEOGRAPH",
            Self::DecagonCircle => "DECAGON_CIRCLE",
            Self::DecagonCircleHanja => "DECAGON_CIRCLE_HANJA",
            Self::Symbol => "SYMBOL",
            Self::UserChar => "USER_CHAR",
            Self::Symbol2 => "SYMBOL2",
            Self::Image => "IMAGE",
            Self::TwoDigit => "2DIGIT",
        }
    }
}

#[derive(Clone, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct ParagraphHeadStyle {
    pub alignment: ListAlignment,
    pub use_instance_width: bool,
    pub auto_indent: bool,
    pub width_adjust: i32,
    pub text_offset_unit: TextOffsetUnit,
    pub text_offset: i32,
    pub number_format: NumberFormat,
    pub character_style_id_ref: Option<u32>,
    pub checkable: bool,
    pub template: String,
}

#[derive(Clone, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct NumberingLevel {
    pub level: u8,
    pub start: u32,
    pub head: ParagraphHeadStyle,
}

#[derive(Clone, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct NumberingDefinition {
    pub id: u32,
    pub start: u32,
    pub levels: Vec<NumberingLevel>,
}

#[derive(Clone, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct BulletDefinition {
    pub id: u32,
    pub mark: char,
    pub checked_mark: Option<char>,
    pub head: ParagraphHeadStyle,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ListDefinitionCatalog {
    pub numberings: Vec<NumberingDefinition>,
    pub bullets: Vec<BulletDefinition>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct DeduplicatedListDefinitions {
    pub catalog: ListDefinitionCatalog,
    pub numbering_old_to_new: Vec<u32>,
    pub bullet_old_to_new: Vec<u32>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ListDefinitionLoweringReceipt {
    pub profile_id: &'static str,
    pub sha256: [u8; 32],
    pub output_bytes: usize,
    pub numbering_count: usize,
    pub bullet_count: usize,
    pub level_count: usize,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct OutlineDefinitionBinding {
    pub numbering_definition_id: u32,
}

#[derive(Debug)]
pub struct OutlineDefinitionBindingReader;

impl OutlineDefinitionBindingReader {
    /// Reads the section outlineShapeIDRef and closes it against the typed numbering catalog.
    ///
    /// # Errors
    ///
    /// Rejects malformed, duplicate, out-of-profile, unbounded or dangling section bindings.
    pub fn read(
        bytes: &[u8],
        catalog: &ListDefinitionCatalog,
        character_style_ids: &[u32],
        limits: ListDefinitionLimits,
    ) -> Result<OutlineDefinitionBinding, ListDefinitionError> {
        if bytes.is_empty() || bytes.len() > limits.config().input_bytes {
            return Err(ListDefinitionError::InputLimit);
        }
        let character_styles = validate_character_style_domain(character_style_ids, limits)?;
        validate_catalog(catalog, &character_styles, limits)?;
        let document = PreservingXmlDocument::parse(bytes)?;
        if document.elements().len() > limits.config().elements {
            return Err(ListDefinitionError::ElementLimit);
        }
        validate_document_envelope(&document)?;
        let mut found = None;
        for (index, value) in document.elements().iter().enumerate() {
            if value.name().local_name() != "secPr" {
                continue;
            }
            if !has_name(value, PARAGRAPH_NS, "secPr") || found.replace(index).is_some() {
                return Err(ListDefinitionError::UnsupportedShape);
            }
        }
        let section = element(
            &document,
            found.ok_or(ListDefinitionError::UnsupportedShape)?,
        )?;
        let numbering_definition_id = required_u32(section, "outlineShapeIDRef")?;
        get_numbering(catalog, numbering_definition_id)?;
        Ok(OutlineDefinitionBinding {
            numbering_definition_id,
        })
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum ListBinding {
    None,
    Outline { level: u8 },
    Number { definition_id: u32, level: u8 },
    Bullet { definition_id: u32, level: u8 },
}

impl ListBinding {
    /// Converts a public list binding to the P05-03 paragraph heading representation.
    ///
    /// # Errors
    ///
    /// Rejects zero definition IDs and levels outside 0..=9.
    pub fn to_heading(self) -> Result<Heading, ListDefinitionError> {
        let (heading_type, id_ref, level) = match self {
            Self::None => (HeadingType::None, 0, 0),
            Self::Outline { level } => (HeadingType::Outline, 0, level),
            Self::Number {
                definition_id,
                level,
            } => (HeadingType::Number, definition_id, level),
            Self::Bullet {
                definition_id,
                level,
            } => (HeadingType::Bullet, definition_id, level),
        };
        if usize::from(level) >= LEVEL_COUNT
            || matches!(
                self,
                Self::Number {
                    definition_id: 0,
                    ..
                } | Self::Bullet {
                    definition_id: 0,
                    ..
                }
            )
        {
            return Err(ListDefinitionError::OutOfRange);
        }
        Ok(Heading {
            heading_type,
            id_ref,
            level,
        })
    }

    /// Builds a typed binding from a P05-03 paragraph heading.
    ///
    /// # Errors
    ///
    /// Rejects malformed NONE/OUTLINE IDs or out-of-range levels.
    pub fn from_heading(heading: Heading) -> Result<Self, ListDefinitionError> {
        if usize::from(heading.level) >= LEVEL_COUNT {
            return Err(ListDefinitionError::OutOfRange);
        }
        match heading.heading_type {
            HeadingType::None if heading.id_ref == 0 && heading.level == 0 => Ok(Self::None),
            HeadingType::Outline if heading.id_ref == 0 => Ok(Self::Outline {
                level: heading.level,
            }),
            HeadingType::Number if heading.id_ref != 0 => Ok(Self::Number {
                definition_id: heading.id_ref,
                level: heading.level,
            }),
            HeadingType::Bullet if heading.id_ref != 0 => Ok(Self::Bullet {
                definition_id: heading.id_ref,
                level: heading.level,
            }),
            _ => Err(ListDefinitionError::OutOfRange),
        }
    }

    /// Increases the numeric level by one, corresponding to one deeper nesting level.
    ///
    /// # Errors
    ///
    /// Rejects NONE and level 9.
    pub fn increase_level(self) -> Result<Self, ListDefinitionError> {
        self.with_level_delta(true)
    }

    /// Decreases the numeric level by one, corresponding to one shallower nesting level.
    ///
    /// # Errors
    ///
    /// Rejects NONE and level 0.
    pub fn decrease_level(self) -> Result<Self, ListDefinitionError> {
        self.with_level_delta(false)
    }

    #[must_use]
    pub const fn remove() -> Self {
        Self::None
    }

    fn with_level_delta(self, increase: bool) -> Result<Self, ListDefinitionError> {
        let next = |level: u8| {
            if increase {
                level
                    .checked_add(1)
                    .filter(|value| usize::from(*value) < LEVEL_COUNT)
            } else {
                level.checked_sub(1)
            }
            .ok_or(ListDefinitionError::InvalidSequence)
        };
        match self {
            Self::None => Err(ListDefinitionError::InvalidSequence),
            Self::Outline { level } => Ok(Self::Outline {
                level: next(level)?,
            }),
            Self::Number {
                definition_id,
                level,
            } => Ok(Self::Number {
                definition_id,
                level: next(level)?,
            }),
            Self::Bullet {
                definition_id,
                level,
            } => Ok(Self::Bullet {
                definition_id,
                level: next(level)?,
            }),
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum ListSequenceKind {
    Number,
    Outline,
    Bullet,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ListSequenceItem {
    pub sequence_id: u32,
    pub kind: ListSequenceKind,
    pub definition_id: u32,
    pub level: u8,
    pub restart: Option<u32>,
    pub checked: bool,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ListSequenceResult {
    pub sequence_id: u32,
    pub kind: ListSequenceKind,
    pub definition_id: u32,
    pub level: u8,
    pub restart_applied: bool,
    pub counters: [Option<u32>; LEVEL_COUNT],
    pub number_format: Option<NumberFormat>,
    pub template: String,
    pub bullet_mark: Option<char>,
}

#[derive(Debug, Eq, Error, PartialEq)]
pub enum ListDefinitionError {
    #[error("list-definition limits are invalid")]
    InvalidLimit,
    #[error("list-definition input exceeds its finite limit")]
    InputLimit,
    #[error("list-definition XML failed preserving admission")]
    Preserving(#[from] PreservingXmlError),
    #[error("list-definition root is not the current Hangul 2020 head profile")]
    WrongRoot,
    #[error("list-definition element or attribute shape is unsupported")]
    UnsupportedShape,
    #[error("list-definition count does not match content")]
    CountMismatch,
    #[error("list-definition identifier is invalid")]
    InvalidId,
    #[error("list-definition reference is dangling")]
    DanglingReference,
    #[error("list-definition reference count exceeds its finite limit")]
    ReferenceLimit,
    #[error("list-definition numeric attribute is invalid")]
    InvalidNumber,
    #[error("list-definition boolean attribute is invalid")]
    InvalidBoolean,
    #[error("list-definition enum attribute is invalid")]
    InvalidEnum,
    #[error("list-definition text is invalid")]
    InvalidText,
    #[error("list-definition value is outside the current-2020 range")]
    OutOfRange,
    #[error("list-definition count exceeds its finite limit")]
    DefinitionLimit,
    #[error("list-definition level count exceeds its finite limit")]
    LevelLimit,
    #[error("list-definition element count exceeds its finite limit")]
    ElementLimit,
    #[error("list-definition sequence is invalid")]
    InvalidSequence,
    #[error("list-definition sequence item count exceeds its finite limit")]
    SequenceLimit,
    #[error("list-definition sequence counter overflowed")]
    CounterOverflow,
    #[error("list-definition output exceeds its finite limit")]
    OutputLimit,
    #[error("list-definition allocation failed")]
    AllocationFailed,
    #[error("list-definition lowered readback differs")]
    ReadbackMismatch,
}

impl ListDefinitionError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "list_definition_invalid_limit",
            Self::InputLimit => "list_definition_input_limit",
            Self::Preserving(_) => "list_definition_preserving_xml",
            Self::WrongRoot => "list_definition_wrong_root",
            Self::UnsupportedShape => "list_definition_unsupported_shape",
            Self::CountMismatch => "list_definition_count_mismatch",
            Self::InvalidId => "list_definition_invalid_id",
            Self::DanglingReference => "list_definition_dangling_reference",
            Self::ReferenceLimit => "list_definition_reference_limit",
            Self::InvalidNumber => "list_definition_invalid_number",
            Self::InvalidBoolean => "list_definition_invalid_boolean",
            Self::InvalidEnum => "list_definition_invalid_enum",
            Self::InvalidText => "list_definition_invalid_text",
            Self::OutOfRange => "list_definition_out_of_range",
            Self::DefinitionLimit => "list_definition_definition_limit",
            Self::LevelLimit => "list_definition_level_limit",
            Self::ElementLimit => "list_definition_element_limit",
            Self::InvalidSequence => "list_definition_invalid_sequence",
            Self::SequenceLimit => "list_definition_sequence_limit",
            Self::CounterOverflow => "list_definition_counter_overflow",
            Self::OutputLimit => "list_definition_output_limit",
            Self::AllocationFailed => "list_definition_allocation_failed",
            Self::ReadbackMismatch => "list_definition_readback_mismatch",
        }
    }
}

#[derive(Debug)]
pub struct ListDefinitionCatalogReader;

impl ListDefinitionCatalogReader {
    /// Lifts numberings and optional bullets from a current-2020 header or refList fragment.
    ///
    /// # Errors
    ///
    /// Rejects malformed, unsupported, unbounded, non-dense or dangling typed content.
    pub fn read(
        bytes: &[u8],
        limits: ListDefinitionLimits,
    ) -> Result<ListDefinitionCatalog, ListDefinitionError> {
        read_catalog_document(bytes, None, limits)
    }

    /// Lifts a fragment using an explicitly supplied dense character-style domain.
    ///
    /// # Errors
    ///
    /// Applies the same checks as [`Self::read`] and requires the supplied domain to match any domain
    /// present in a full header.
    pub fn read_with_character_style_domain(
        bytes: &[u8],
        character_style_ids: &[u32],
        limits: ListDefinitionLimits,
    ) -> Result<ListDefinitionCatalog, ListDefinitionError> {
        read_catalog_document(bytes, Some(character_style_ids), limits)
    }
}

#[derive(Debug)]
pub struct ListDefinitionCatalogWriter;

impl ListDefinitionCatalogWriter {
    /// Lowers a typed catalog to deterministic current-2020 refList XML and reparses it.
    ///
    /// # Errors
    ///
    /// Rejects invalid public values, character references, limits or readback drift.
    pub fn lower(
        catalog: &ListDefinitionCatalog,
        character_style_ids: &[u32],
        limits: ListDefinitionLimits,
    ) -> Result<Vec<u8>, ListDefinitionError> {
        let (bytes, _) = Self::lower_with_receipt(catalog, character_style_ids, limits)?;
        Ok(bytes)
    }

    /// Lowers a typed catalog and returns a deterministic integrity receipt.
    ///
    /// # Errors
    ///
    /// Applies the same checks as [`Self::lower`].
    pub fn lower_with_receipt(
        catalog: &ListDefinitionCatalog,
        character_style_ids: &[u32],
        limits: ListDefinitionLimits,
    ) -> Result<(Vec<u8>, ListDefinitionLoweringReceipt), ListDefinitionError> {
        let character_styles = validate_character_style_domain(character_style_ids, limits)?;
        validate_catalog(catalog, &character_styles, limits)?;
        let mut output = BoundedXml::new(limits.config().input_bytes)?;
        output.push("<?xml version=\"1.0\" encoding=\"UTF-8\"?>")?;
        output.push("<hh:refList xmlns:hh=\"")?;
        output.push(HEAD_NS)?;
        output.push("\" xmlns:hp=\"")?;
        output.push(PARAGRAPH_NS)?;
        output.push("\"><hh:numberings itemCnt=\"")?;
        output.push_usize(catalog.numberings.len())?;
        output.push("\">")?;
        for definition in &catalog.numberings {
            write_numbering(&mut output, definition)?;
        }
        output.push("</hh:numberings>")?;
        if !catalog.bullets.is_empty() {
            output.push("<hh:bullets itemCnt=\"")?;
            output.push_usize(catalog.bullets.len())?;
            output.push("\">")?;
            for definition in &catalog.bullets {
                write_bullet(&mut output, definition)?;
            }
            output.push("</hh:bullets>")?;
        }
        output.push("</hh:refList>")?;
        let bytes = output.finish();
        let readback = ListDefinitionCatalogReader::read_with_character_style_domain(
            &bytes,
            character_style_ids,
            limits,
        )?;
        if readback != *catalog {
            return Err(ListDefinitionError::ReadbackMismatch);
        }
        let receipt = ListDefinitionLoweringReceipt {
            profile_id: LIST_DEFINITION_PROFILE_ID,
            sha256: <[u8; 32]>::from(Sha256::digest(&bytes)),
            output_bytes: bytes.len(),
            numbering_count: catalog.numberings.len(),
            bullet_count: catalog.bullets.len(),
            level_count: total_level_count(catalog)?,
        };
        Ok((bytes, receipt))
    }
}

impl ListDefinitionCatalog {
    /// Validates P05-03 paragraph heading domains and the section outline binding.
    ///
    /// # Errors
    ///
    /// Rejects malformed catalogs, domains, headings, levels or dangling definitions.
    pub fn validate_paragraph_references(
        &self,
        paragraphs: &ParagraphStyleCatalog,
        outline_definition_id: u32,
        character_style_ids: &[u32],
        limits: ListDefinitionLimits,
    ) -> Result<(), ListDefinitionError> {
        let character_styles = validate_character_style_domain(character_style_ids, limits)?;
        validate_catalog(self, &character_styles, limits)?;
        validate_paragraph_reference_limit(paragraphs, limits)?;
        validate_source_domain(&paragraphs.references.numbering_ids, self.numberings.len())?;
        validate_source_domain(&paragraphs.references.bullet_ids, self.bullets.len())?;
        get_numbering(self, outline_definition_id)?;
        for style in &paragraphs.styles {
            match style.heading {
                CompatibleHeading::Direct(heading) => {
                    validate_paragraph_heading(self, heading, outline_definition_id)?;
                }
                CompatibleHeading::MetaTag { current, fallback } => {
                    validate_paragraph_heading(self, current, outline_definition_id)?;
                    validate_paragraph_heading(self, fallback, outline_definition_id)?;
                }
            }
        }
        Ok(())
    }

    /// Deduplicates semantic definitions in deterministic first-occurrence order.
    ///
    /// # Errors
    ///
    /// Rejects invalid catalogs, character references or allocation/identifier overflow.
    pub fn deduplicate(
        &self,
        character_style_ids: &[u32],
        limits: ListDefinitionLimits,
    ) -> Result<DeduplicatedListDefinitions, ListDefinitionError> {
        let character_styles = validate_character_style_domain(character_style_ids, limits)?;
        validate_catalog(self, &character_styles, limits)?;
        let (numberings, numbering_old_to_new) = deduplicate_numberings(&self.numberings)?;
        let (bullets, bullet_old_to_new) = deduplicate_bullets(&self.bullets)?;
        Ok(DeduplicatedListDefinitions {
            catalog: Self {
                numberings,
                bullets,
            },
            numbering_old_to_new,
            bullet_old_to_new,
        })
    }
}

fn validate_paragraph_heading(
    catalog: &ListDefinitionCatalog,
    heading: Heading,
    outline_definition_id: u32,
) -> Result<(), ListDefinitionError> {
    match ListBinding::from_heading(heading)? {
        ListBinding::None => Ok(()),
        ListBinding::Outline { .. } => get_numbering(catalog, outline_definition_id).map(|_| ()),
        ListBinding::Number { definition_id, .. } => {
            get_numbering(catalog, definition_id).map(|_| ())
        }
        ListBinding::Bullet { definition_id, .. } => get_bullet(catalog, definition_id).map(|_| ()),
    }
}

impl DeduplicatedListDefinitions {
    /// Atomically rewrites P05-03 NUMBER/BULLET heading references and their external domains.
    ///
    /// # Errors
    ///
    /// Rejects malformed maps, source domains or dangling typed references before mutation.
    pub fn rewrite_paragraph_references(
        &self,
        paragraphs: &mut ParagraphStyleCatalog,
        character_style_ids: &[u32],
        limits: ListDefinitionLimits,
    ) -> Result<(), ListDefinitionError> {
        let character_styles = validate_character_style_domain(character_style_ids, limits)?;
        validate_catalog(&self.catalog, &character_styles, limits)?;
        validate_paragraph_reference_limit(paragraphs, limits)?;
        validate_mapping(&self.numbering_old_to_new, self.catalog.numberings.len())?;
        validate_mapping(&self.bullet_old_to_new, self.catalog.bullets.len())?;
        validate_source_domain(
            &paragraphs.references.numbering_ids,
            self.numbering_old_to_new.len(),
        )?;
        validate_source_domain(
            &paragraphs.references.bullet_ids,
            self.bullet_old_to_new.len(),
        )?;

        let mut rewritten = paragraphs.clone();
        for style in &mut rewritten.styles {
            style.heading = rewrite_compatible_heading(
                style.heading,
                &self.numbering_old_to_new,
                &self.bullet_old_to_new,
            )?;
        }
        rewritten.references.numbering_ids = dense_one_based(self.catalog.numberings.len())?;
        rewritten.references.bullet_ids = dense_one_based(self.catalog.bullets.len())?;
        *paragraphs = rewritten;
        Ok(())
    }

    /// Remaps a section outlineShapeIDRef through the complete numbering map.
    ///
    /// # Errors
    ///
    /// Rejects malformed maps and zero or dangling source IDs.
    pub fn remap_outline_definition_id(&self, source_id: u32) -> Result<u32, ListDefinitionError> {
        validate_mapping(&self.numbering_old_to_new, self.catalog.numberings.len())?;
        map_one_based(&self.numbering_old_to_new, source_id)
    }
}

#[derive(Debug)]
pub struct ListSequenceEngine;

impl ListSequenceEngine {
    /// Evaluates explicit list sequences into checked counter paths and selected bullet marks.
    ///
    /// # Errors
    ///
    /// Rejects malformed catalogs, sequence conflicts, invalid nesting/restarts and overflow.
    pub fn evaluate(
        catalog: &ListDefinitionCatalog,
        character_style_ids: &[u32],
        items: &[ListSequenceItem],
        limits: ListDefinitionLimits,
    ) -> Result<Vec<ListSequenceResult>, ListDefinitionError> {
        let character_styles = validate_character_style_domain(character_style_ids, limits)?;
        validate_catalog(catalog, &character_styles, limits)?;
        if items.len() > limits.config().sequence_items {
            return Err(ListDefinitionError::SequenceLimit);
        }
        let mut states = BTreeMap::<u32, SequenceState>::new();
        let mut results = Vec::new();
        results
            .try_reserve(items.len())
            .map_err(|_| ListDefinitionError::AllocationFailed)?;
        for item in items {
            if item.sequence_id == 0
                || item.definition_id == 0
                || usize::from(item.level) >= LEVEL_COUNT
            {
                return Err(ListDefinitionError::InvalidSequence);
            }
            let binding = SequenceBinding::from_item(*item);
            let state = states
                .entry(item.sequence_id)
                .or_insert_with(|| SequenceState::new(binding));
            if state.binding != binding {
                return Err(ListDefinitionError::InvalidSequence);
            }
            let result = evaluate_item(catalog, state, *item)?;
            results.push(result);
        }
        Ok(results)
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum SequenceBinding {
    Number(u32),
    Outline(u32),
    Bullet(u32),
}

impl SequenceBinding {
    const fn from_item(item: ListSequenceItem) -> Self {
        match item.kind {
            ListSequenceKind::Number => Self::Number(item.definition_id),
            ListSequenceKind::Outline => Self::Outline(item.definition_id),
            ListSequenceKind::Bullet => Self::Bullet(item.definition_id),
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
struct SequenceState {
    binding: SequenceBinding,
    counters: [Option<u32>; LEVEL_COUNT],
    last_level: Option<u8>,
}

impl SequenceState {
    const fn new(binding: SequenceBinding) -> Self {
        Self {
            binding,
            counters: [None; LEVEL_COUNT],
            last_level: None,
        }
    }
}

fn read_catalog_document(
    bytes: &[u8],
    supplied_character_style_ids: Option<&[u32]>,
    limits: ListDefinitionLimits,
) -> Result<ListDefinitionCatalog, ListDefinitionError> {
    if bytes.is_empty() || bytes.len() > limits.config().input_bytes {
        return Err(ListDefinitionError::InputLimit);
    }
    let document = PreservingXmlDocument::parse(bytes)?;
    if document.elements().len() > limits.config().elements {
        return Err(ListDefinitionError::ElementLimit);
    }
    validate_document_envelope(&document)?;
    let ref_list = find_ref_list(&document)?;
    let embedded_character_style_ids =
        optional_one_child(&document, ref_list, HEAD_NS, "charProperties")?
            .map(|container| read_dense_id_domain(&document, container, "charPr", 0, limits))
            .transpose()?;
    let character_style_ids = match (
        embedded_character_style_ids.as_deref(),
        supplied_character_style_ids,
    ) {
        (Some(embedded), Some(supplied)) if embedded != supplied => {
            return Err(ListDefinitionError::DanglingReference);
        }
        (Some(embedded), _) => embedded,
        (None, Some(supplied)) => supplied,
        (None, None) => &[],
    };
    let character_styles = validate_character_style_domain(character_style_ids, limits)?;

    let numberings = exactly_one_child(&document, ref_list, HEAD_NS, "numberings")?;
    let bullets = optional_one_child(&document, ref_list, HEAD_NS, "bullets")?;
    let catalog = ListDefinitionCatalog {
        numberings: read_numberings(&document, numberings, &character_styles, limits)?,
        bullets: bullets
            .map(|index| read_bullets(&document, index, &character_styles, limits))
            .transpose()?
            .unwrap_or_default(),
    };
    validate_catalog(&catalog, &character_styles, limits)?;
    Ok(catalog)
}

fn read_numberings(
    document: &PreservingXmlDocument,
    index: usize,
    character_styles: &BTreeSet<u32>,
    limits: ListDefinitionLimits,
) -> Result<Vec<NumberingDefinition>, ListDefinitionError> {
    let container = element(document, index)?;
    require_name(container, HEAD_NS, "numberings")?;
    validate_attributes(container, &["itemCnt"])?;
    require_only_whitespace_content(document, index)?;
    let expected_count = required_usize(container, "itemCnt")?;
    let children = child_indexes(document, index)?;
    if children.len() != expected_count {
        return Err(ListDefinitionError::CountMismatch);
    }
    if children.len() > limits.config().numberings {
        return Err(ListDefinitionError::DefinitionLimit);
    }
    let mut definitions = Vec::new();
    definitions
        .try_reserve(children.len())
        .map_err(|_| ListDefinitionError::AllocationFailed)?;
    for (position, child_index) in children.into_iter().enumerate() {
        let expected_id = one_based_id(position)?;
        definitions.push(read_numbering(
            document,
            child_index,
            expected_id,
            character_styles,
            limits,
        )?);
    }
    Ok(definitions)
}

fn read_numbering(
    document: &PreservingXmlDocument,
    index: usize,
    expected_id: u32,
    character_styles: &BTreeSet<u32>,
    limits: ListDefinitionLimits,
) -> Result<NumberingDefinition, ListDefinitionError> {
    let value = element(document, index)?;
    require_name(value, HEAD_NS, "numbering")?;
    validate_attributes(value, &["id", "start"])?;
    require_only_whitespace_content(document, index)?;
    let id = required_u32(value, "id")?;
    if id != expected_id {
        return Err(ListDefinitionError::InvalidId);
    }
    let children = child_indexes(document, index)?;
    if children.len() != LEVEL_COUNT {
        return Err(ListDefinitionError::CountMismatch);
    }
    if children.len() > limits.config().levels {
        return Err(ListDefinitionError::LevelLimit);
    }
    let mut levels = Vec::new();
    levels
        .try_reserve(LEVEL_COUNT)
        .map_err(|_| ListDefinitionError::AllocationFailed)?;
    for (position, child_index) in children.into_iter().enumerate() {
        levels.push(read_numbering_level(
            document,
            child_index,
            position,
            character_styles,
            limits,
        )?);
    }
    Ok(NumberingDefinition {
        id,
        start: required_u32(value, "start")?,
        levels,
    })
}

fn read_numbering_level(
    document: &PreservingXmlDocument,
    index: usize,
    position: usize,
    character_styles: &BTreeSet<u32>,
    limits: ListDefinitionLimits,
) -> Result<NumberingLevel, ListDefinitionError> {
    let value = element(document, index)?;
    require_name(value, HEAD_NS, "paraHead")?;
    validate_attributes(
        value,
        &[
            "start",
            "level",
            "align",
            "useInstWidth",
            "autoIndent",
            "widthAdjust",
            "textOffsetType",
            "textOffset",
            "numFormat",
            "charPrIDRef",
            "checkable",
        ],
    )?;
    let level = required_u8(value, "level")?;
    if usize::from(level) != position + 1 {
        return Err(ListDefinitionError::InvalidId);
    }
    let result = NumberingLevel {
        level,
        start: required_u32(value, "start")?,
        head: read_head_style(document, index, character_styles, limits)?,
    };
    validate_numbering_level(&result, character_styles, limits)?;
    Ok(result)
}

fn read_bullets(
    document: &PreservingXmlDocument,
    index: usize,
    character_styles: &BTreeSet<u32>,
    limits: ListDefinitionLimits,
) -> Result<Vec<BulletDefinition>, ListDefinitionError> {
    let container = element(document, index)?;
    require_name(container, HEAD_NS, "bullets")?;
    validate_attributes(container, &["itemCnt"])?;
    require_only_whitespace_content(document, index)?;
    let expected_count = required_usize(container, "itemCnt")?;
    let children = child_indexes(document, index)?;
    if children.len() != expected_count {
        return Err(ListDefinitionError::CountMismatch);
    }
    if children.len() > limits.config().bullets {
        return Err(ListDefinitionError::DefinitionLimit);
    }
    let mut definitions = Vec::new();
    definitions
        .try_reserve(children.len())
        .map_err(|_| ListDefinitionError::AllocationFailed)?;
    for (position, child_index) in children.into_iter().enumerate() {
        definitions.push(read_bullet(
            document,
            child_index,
            one_based_id(position)?,
            character_styles,
            limits,
        )?);
    }
    Ok(definitions)
}

fn read_bullet(
    document: &PreservingXmlDocument,
    index: usize,
    expected_id: u32,
    character_styles: &BTreeSet<u32>,
    limits: ListDefinitionLimits,
) -> Result<BulletDefinition, ListDefinitionError> {
    let value = element(document, index)?;
    require_name(value, HEAD_NS, "bullet")?;
    validate_attributes(value, &["id", "char", "checkedChar", "useImage"])?;
    require_only_whitespace_content(document, index)?;
    let id = required_u32(value, "id")?;
    if id != expected_id {
        return Err(ListDefinitionError::InvalidId);
    }
    if required_bool(value, "useImage")? {
        return Err(ListDefinitionError::UnsupportedShape);
    }
    let children = child_indexes(document, index)?;
    if children.len() != 1 {
        return Err(ListDefinitionError::CountMismatch);
    }
    let head_element = element(document, children[0])?;
    require_name(head_element, HEAD_NS, "paraHead")?;
    validate_attributes(
        head_element,
        &[
            "level",
            "align",
            "useInstWidth",
            "autoIndent",
            "widthAdjust",
            "textOffsetType",
            "textOffset",
            "numFormat",
            "charPrIDRef",
            "checkable",
        ],
    )?;
    if required_u8(head_element, "level")? != BULLET_XML_LEVEL {
        return Err(ListDefinitionError::OutOfRange);
    }
    let definition = BulletDefinition {
        id,
        mark: parse_scalar(required_attribute(value, "char")?)?,
        checked_mark: optional_attribute(value, "checkedChar")
            .map(parse_scalar)
            .transpose()?,
        head: read_head_style(document, children[0], character_styles, limits)?,
    };
    validate_bullet(&definition, character_styles, limits)?;
    Ok(definition)
}

fn read_head_style(
    document: &PreservingXmlDocument,
    index: usize,
    character_styles: &BTreeSet<u32>,
    limits: ListDefinitionLimits,
) -> Result<ParagraphHeadStyle, ListDefinitionError> {
    let value = element(document, index)?;
    let character_style_id_ref = match required_u32(value, "charPrIDRef")? {
        NO_CHARACTER_STYLE => None,
        id => Some(id),
    };
    let head = ParagraphHeadStyle {
        alignment: ListAlignment::parse(required_attribute(value, "align")?)?,
        use_instance_width: required_bool(value, "useInstWidth")?,
        auto_indent: required_bool(value, "autoIndent")?,
        width_adjust: required_i32(value, "widthAdjust")?,
        text_offset_unit: TextOffsetUnit::parse(required_attribute(value, "textOffsetType")?)?,
        text_offset: required_i32(value, "textOffset")?,
        number_format: NumberFormat::parse(required_attribute(value, "numFormat")?)?,
        character_style_id_ref,
        checkable: required_bool(value, "checkable")?,
        template: direct_text(document, index, limits)?,
    };
    validate_head_style(&head, character_styles, limits)?;
    Ok(head)
}

fn validate_catalog(
    catalog: &ListDefinitionCatalog,
    character_styles: &BTreeSet<u32>,
    limits: ListDefinitionLimits,
) -> Result<(), ListDefinitionError> {
    if catalog.numberings.is_empty()
        || catalog.numberings.len() > limits.config().numberings
        || catalog.bullets.len() > limits.config().bullets
    {
        return Err(ListDefinitionError::DefinitionLimit);
    }
    if total_level_count(catalog)? > limits.config().levels {
        return Err(ListDefinitionError::LevelLimit);
    }
    for (position, definition) in catalog.numberings.iter().enumerate() {
        if definition.id != one_based_id(position)? || definition.levels.len() != LEVEL_COUNT {
            return Err(ListDefinitionError::InvalidId);
        }
        for (level_position, level) in definition.levels.iter().enumerate() {
            if usize::from(level.level) != level_position + 1 {
                return Err(ListDefinitionError::InvalidId);
            }
            validate_numbering_level(level, character_styles, limits)?;
        }
    }
    for (position, definition) in catalog.bullets.iter().enumerate() {
        if definition.id != one_based_id(position)? {
            return Err(ListDefinitionError::InvalidId);
        }
        validate_bullet(definition, character_styles, limits)?;
    }
    Ok(())
}

fn validate_numbering_level(
    level: &NumberingLevel,
    character_styles: &BTreeSet<u32>,
    limits: ListDefinitionLimits,
) -> Result<(), ListDefinitionError> {
    if level.head.number_format == NumberFormat::Image {
        return Err(ListDefinitionError::UnsupportedShape);
    }
    if level.level == 0 || usize::from(level.level) > LEVEL_COUNT || level.start == 0 {
        return Err(ListDefinitionError::OutOfRange);
    }
    validate_head_style(&level.head, character_styles, limits)
}

fn validate_bullet(
    definition: &BulletDefinition,
    character_styles: &BTreeSet<u32>,
    limits: ListDefinitionLimits,
) -> Result<(), ListDefinitionError> {
    validate_scalar(definition.mark)?;
    if let Some(mark) = definition.checked_mark {
        validate_scalar(mark)?;
    }
    if definition.head.checkable != definition.checked_mark.is_some()
        || definition.head.number_format == NumberFormat::Image
    {
        return Err(ListDefinitionError::UnsupportedShape);
    }
    validate_head_style(&definition.head, character_styles, limits)
}

fn validate_head_style(
    head: &ParagraphHeadStyle,
    character_styles: &BTreeSet<u32>,
    limits: ListDefinitionLimits,
) -> Result<(), ListDefinitionError> {
    if !(-1_000_000..=1_000_000).contains(&head.width_adjust)
        || !(-1_000_000..=1_000_000).contains(&head.text_offset)
        || (head.text_offset_unit == TextOffsetUnit::Percent
            && !(0..=1_000).contains(&head.text_offset))
    {
        return Err(ListDefinitionError::OutOfRange);
    }
    if let Some(id) = head.character_style_id_ref
        && !character_styles.contains(&id)
    {
        return Err(ListDefinitionError::DanglingReference);
    }
    validate_text(&head.template, limits)
}

fn validate_text(value: &str, limits: ListDefinitionLimits) -> Result<(), ListDefinitionError> {
    if value.len() > limits.config().text_bytes
        || value.chars().any(|value| !is_xml_character(value))
    {
        return Err(ListDefinitionError::InvalidText);
    }
    Ok(())
}

fn validate_scalar(value: char) -> Result<(), ListDefinitionError> {
    if is_xml_character(value) && !value.is_whitespace() {
        Ok(())
    } else {
        Err(ListDefinitionError::InvalidText)
    }
}

fn is_xml_character(value: char) -> bool {
    matches!(value, '\u{9}' | '\u{A}' | '\u{D}')
        || ('\u{20}'..='\u{D7FF}').contains(&value)
        || ('\u{E000}'..='\u{FFFD}').contains(&value)
        || ('\u{10000}'..='\u{10FFFF}').contains(&value)
}

fn validate_character_style_domain(
    ids: &[u32],
    limits: ListDefinitionLimits,
) -> Result<BTreeSet<u32>, ListDefinitionError> {
    if ids.len() > limits.config().levels {
        return Err(ListDefinitionError::LevelLimit);
    }
    let mut result = BTreeSet::new();
    for (position, id) in ids.iter().copied().enumerate() {
        let expected = u32::try_from(position).map_err(|_| ListDefinitionError::InvalidId)?;
        if id != expected || !result.insert(id) {
            return Err(ListDefinitionError::InvalidId);
        }
    }
    Ok(result)
}

fn total_level_count(catalog: &ListDefinitionCatalog) -> Result<usize, ListDefinitionError> {
    catalog
        .numberings
        .len()
        .checked_mul(LEVEL_COUNT)
        .and_then(|value| value.checked_add(catalog.bullets.len()))
        .ok_or(ListDefinitionError::LevelLimit)
}

fn deduplicate_numberings(
    source: &[NumberingDefinition],
) -> Result<(Vec<NumberingDefinition>, Vec<u32>), ListDefinitionError> {
    let mut seen = BTreeMap::<NumberingDefinition, u32>::new();
    let mut definitions = Vec::new();
    let mut mapping = Vec::new();
    definitions
        .try_reserve(source.len())
        .map_err(|_| ListDefinitionError::AllocationFailed)?;
    mapping
        .try_reserve(source.len())
        .map_err(|_| ListDefinitionError::AllocationFailed)?;
    for definition in source {
        let mut semantic = definition.clone();
        semantic.id = 0;
        let mapped = if let Some(existing) = seen.get(&semantic) {
            *existing
        } else {
            let id = one_based_id(definitions.len())?;
            let mut allocated = definition.clone();
            allocated.id = id;
            definitions.push(allocated);
            seen.insert(semantic, id);
            id
        };
        mapping.push(mapped);
    }
    Ok((definitions, mapping))
}

fn deduplicate_bullets(
    source: &[BulletDefinition],
) -> Result<(Vec<BulletDefinition>, Vec<u32>), ListDefinitionError> {
    let mut seen = BTreeMap::<BulletDefinition, u32>::new();
    let mut definitions = Vec::new();
    let mut mapping = Vec::new();
    definitions
        .try_reserve(source.len())
        .map_err(|_| ListDefinitionError::AllocationFailed)?;
    mapping
        .try_reserve(source.len())
        .map_err(|_| ListDefinitionError::AllocationFailed)?;
    for definition in source {
        let mut semantic = definition.clone();
        semantic.id = 0;
        let mapped = if let Some(existing) = seen.get(&semantic) {
            *existing
        } else {
            let id = one_based_id(definitions.len())?;
            let mut allocated = definition.clone();
            allocated.id = id;
            definitions.push(allocated);
            seen.insert(semantic, id);
            id
        };
        mapping.push(mapped);
    }
    Ok((definitions, mapping))
}

fn rewrite_compatible_heading(
    heading: CompatibleHeading,
    numbering_map: &[u32],
    bullet_map: &[u32],
) -> Result<CompatibleHeading, ListDefinitionError> {
    match heading {
        CompatibleHeading::Direct(value) => Ok(CompatibleHeading::Direct(rewrite_heading(
            value,
            numbering_map,
            bullet_map,
        )?)),
        CompatibleHeading::MetaTag { current, fallback } => Ok(CompatibleHeading::MetaTag {
            current: rewrite_heading(current, numbering_map, bullet_map)?,
            fallback: rewrite_heading(fallback, numbering_map, bullet_map)?,
        }),
    }
}

fn rewrite_heading(
    mut heading: Heading,
    numbering_map: &[u32],
    bullet_map: &[u32],
) -> Result<Heading, ListDefinitionError> {
    if usize::from(heading.level) >= LEVEL_COUNT {
        return Err(ListDefinitionError::OutOfRange);
    }
    match heading.heading_type {
        HeadingType::None if heading.id_ref == 0 && heading.level == 0 => {}
        HeadingType::Outline if heading.id_ref == 0 => {}
        HeadingType::Number => heading.id_ref = map_one_based(numbering_map, heading.id_ref)?,
        HeadingType::Bullet => heading.id_ref = map_one_based(bullet_map, heading.id_ref)?,
        HeadingType::None | HeadingType::Outline => return Err(ListDefinitionError::OutOfRange),
    }
    Ok(heading)
}

fn validate_mapping(mapping: &[u32], target_count: usize) -> Result<(), ListDefinitionError> {
    if mapping.is_empty() && target_count != 0 {
        return Err(ListDefinitionError::InvalidId);
    }
    let target_count = u32::try_from(target_count).map_err(|_| ListDefinitionError::InvalidId)?;
    let mut covered = BTreeSet::new();
    for value in mapping.iter().copied() {
        if value == 0 || value > target_count {
            return Err(ListDefinitionError::InvalidId);
        }
        covered.insert(value);
    }
    if covered.len() != usize::try_from(target_count).map_err(|_| ListDefinitionError::InvalidId)? {
        return Err(ListDefinitionError::InvalidId);
    }
    Ok(())
}

fn validate_source_domain(ids: &[u32], count: usize) -> Result<(), ListDefinitionError> {
    if ids.len() != count {
        return Err(ListDefinitionError::DanglingReference);
    }
    for (position, id) in ids.iter().copied().enumerate() {
        if id != one_based_id(position)? {
            return Err(ListDefinitionError::DanglingReference);
        }
    }
    Ok(())
}

fn validate_paragraph_reference_limit(
    paragraphs: &ParagraphStyleCatalog,
    limits: ListDefinitionLimits,
) -> Result<(), ListDefinitionError> {
    let domain_count = paragraphs
        .references
        .numbering_ids
        .len()
        .checked_add(paragraphs.references.bullet_ids.len())
        .ok_or(ListDefinitionError::ReferenceLimit)?;
    if paragraphs.styles.len() > limits.config().reference_items
        || domain_count > limits.config().reference_items
    {
        return Err(ListDefinitionError::ReferenceLimit);
    }
    Ok(())
}

fn map_one_based(mapping: &[u32], source_id: u32) -> Result<u32, ListDefinitionError> {
    let position = source_id
        .checked_sub(1)
        .and_then(|value| usize::try_from(value).ok())
        .ok_or(ListDefinitionError::DanglingReference)?;
    mapping
        .get(position)
        .copied()
        .ok_or(ListDefinitionError::DanglingReference)
}

fn dense_one_based(count: usize) -> Result<Vec<u32>, ListDefinitionError> {
    let mut ids = Vec::new();
    ids.try_reserve(count)
        .map_err(|_| ListDefinitionError::AllocationFailed)?;
    for position in 0..count {
        ids.push(one_based_id(position)?);
    }
    Ok(ids)
}

fn one_based_id(position: usize) -> Result<u32, ListDefinitionError> {
    position
        .checked_add(1)
        .and_then(|value| u32::try_from(value).ok())
        .ok_or(ListDefinitionError::InvalidId)
}

fn evaluate_item(
    catalog: &ListDefinitionCatalog,
    state: &mut SequenceState,
    item: ListSequenceItem,
) -> Result<ListSequenceResult, ListDefinitionError> {
    match item.kind {
        ListSequenceKind::Bullet => evaluate_bullet_item(catalog, state, item),
        ListSequenceKind::Number | ListSequenceKind::Outline => {
            evaluate_numbering_item(catalog, state, item)
        }
    }
}

fn evaluate_bullet_item(
    catalog: &ListDefinitionCatalog,
    state: &mut SequenceState,
    item: ListSequenceItem,
) -> Result<ListSequenceResult, ListDefinitionError> {
    if item.restart.is_some() {
        return Err(ListDefinitionError::InvalidSequence);
    }
    let level = usize::from(item.level);
    match state.last_level {
        None if level != 0 => return Err(ListDefinitionError::InvalidSequence),
        Some(previous) if level > usize::from(previous) + 1 => {
            return Err(ListDefinitionError::InvalidSequence);
        }
        _ => {}
    }
    let definition = get_bullet(catalog, item.definition_id)?;
    let mark = if item.checked {
        definition
            .checked_mark
            .filter(|_| definition.head.checkable)
            .ok_or(ListDefinitionError::InvalidSequence)?
    } else {
        definition.mark
    };
    state.last_level = Some(item.level);
    Ok(ListSequenceResult {
        sequence_id: item.sequence_id,
        kind: item.kind,
        definition_id: item.definition_id,
        level: item.level,
        restart_applied: false,
        counters: [None; LEVEL_COUNT],
        number_format: None,
        template: definition.head.template.clone(),
        bullet_mark: Some(mark),
    })
}

fn evaluate_numbering_item(
    catalog: &ListDefinitionCatalog,
    state: &mut SequenceState,
    item: ListSequenceItem,
) -> Result<ListSequenceResult, ListDefinitionError> {
    if item.checked {
        return Err(ListDefinitionError::InvalidSequence);
    }
    let definition = get_numbering(catalog, item.definition_id)?;
    let level = usize::from(item.level);
    match state.last_level {
        None if level != 0 => return Err(ListDefinitionError::InvalidSequence),
        Some(previous) if level > usize::from(previous) + 1 => {
            return Err(ListDefinitionError::InvalidSequence);
        }
        _ => {}
    }
    if let Some(restart) = item.restart {
        if restart == 0 {
            return Err(ListDefinitionError::InvalidSequence);
        }
        state.counters[level] = Some(restart);
    } else {
        match state.last_level {
            None => state.counters[0] = Some(definition.levels[0].start),
            Some(previous) if level > usize::from(previous) => {
                state.counters[level] = Some(definition.levels[level].start);
            }
            Some(_) => {
                state.counters[level] = Some(
                    state.counters[level]
                        .ok_or(ListDefinitionError::InvalidSequence)?
                        .checked_add(1)
                        .ok_or(ListDefinitionError::CounterOverflow)?,
                );
            }
        }
    }
    for counter in &mut state.counters[(level + 1)..] {
        *counter = None;
    }
    if state.counters[..=level].iter().any(Option::is_none) {
        return Err(ListDefinitionError::InvalidSequence);
    }
    state.last_level = Some(item.level);
    let head = &definition.levels[level].head;
    Ok(ListSequenceResult {
        sequence_id: item.sequence_id,
        kind: item.kind,
        definition_id: item.definition_id,
        level: item.level,
        restart_applied: item.restart.is_some(),
        counters: state.counters,
        number_format: Some(head.number_format),
        template: head.template.clone(),
        bullet_mark: None,
    })
}

fn get_numbering(
    catalog: &ListDefinitionCatalog,
    id: u32,
) -> Result<&NumberingDefinition, ListDefinitionError> {
    let position = id
        .checked_sub(1)
        .and_then(|value| usize::try_from(value).ok())
        .ok_or(ListDefinitionError::DanglingReference)?;
    catalog
        .numberings
        .get(position)
        .filter(|definition| definition.id == id)
        .ok_or(ListDefinitionError::DanglingReference)
}

fn get_bullet(
    catalog: &ListDefinitionCatalog,
    id: u32,
) -> Result<&BulletDefinition, ListDefinitionError> {
    let position = id
        .checked_sub(1)
        .and_then(|value| usize::try_from(value).ok())
        .ok_or(ListDefinitionError::DanglingReference)?;
    catalog
        .bullets
        .get(position)
        .filter(|definition| definition.id == id)
        .ok_or(ListDefinitionError::DanglingReference)
}

fn write_numbering(
    output: &mut BoundedXml,
    definition: &NumberingDefinition,
) -> Result<(), ListDefinitionError> {
    output.push("<hh:numbering id=\"")?;
    output.push_u32(definition.id)?;
    output.push("\" start=\"")?;
    output.push_u32(definition.start)?;
    output.push("\">")?;
    for level in &definition.levels {
        write_head(output, Some(level.start), level.level, &level.head)?;
    }
    output.push("</hh:numbering>")
}

fn write_bullet(
    output: &mut BoundedXml,
    definition: &BulletDefinition,
) -> Result<(), ListDefinitionError> {
    output.push("<hh:bullet id=\"")?;
    output.push_u32(definition.id)?;
    output.push("\" char=\"")?;
    output.push_escaped(&definition.mark.to_string())?;
    if let Some(mark) = definition.checked_mark {
        output.push("\" checkedChar=\"")?;
        output.push_escaped(&mark.to_string())?;
    }
    output.push("\" useImage=\"0\">")?;
    write_head(output, None, BULLET_XML_LEVEL, &definition.head)?;
    output.push("</hh:bullet>")
}

fn write_head(
    output: &mut BoundedXml,
    start: Option<u32>,
    level: u8,
    head: &ParagraphHeadStyle,
) -> Result<(), ListDefinitionError> {
    output.push("<hh:paraHead")?;
    if let Some(start) = start {
        output.push(" start=\"")?;
        output.push_u32(start)?;
        output.push("\"")?;
    }
    output.push(" level=\"")?;
    output.push_u8(level)?;
    output.push("\" align=\"")?;
    output.push(head.alignment.as_str())?;
    output.push("\" useInstWidth=\"")?;
    output.push_bool(head.use_instance_width)?;
    output.push("\" autoIndent=\"")?;
    output.push_bool(head.auto_indent)?;
    output.push("\" widthAdjust=\"")?;
    output.push_i32(head.width_adjust)?;
    output.push("\" textOffsetType=\"")?;
    output.push(head.text_offset_unit.as_str())?;
    output.push("\" textOffset=\"")?;
    output.push_i32(head.text_offset)?;
    output.push("\" numFormat=\"")?;
    output.push(head.number_format.as_str())?;
    output.push("\" charPrIDRef=\"")?;
    output.push_u32(head.character_style_id_ref.unwrap_or(NO_CHARACTER_STYLE))?;
    output.push("\" checkable=\"")?;
    output.push_bool(head.checkable)?;
    if head.template.is_empty() {
        output.push("\"/>")
    } else {
        output.push("\">")?;
        output.push_escaped(&head.template)?;
        output.push("</hh:paraHead>")
    }
}

fn find_ref_list(document: &PreservingXmlDocument) -> Result<usize, ListDefinitionError> {
    let root_index = document.root_element();
    let root = element(document, root_index)?;
    if has_name(root, HEAD_NS, "refList") {
        Ok(root_index)
    } else if has_name(root, HEAD_NS, "head") {
        exactly_one_child(document, root_index, HEAD_NS, "refList")
    } else {
        Err(ListDefinitionError::WrongRoot)
    }
}

fn element(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<&XmlElementToken, ListDefinitionError> {
    document
        .elements()
        .get(index)
        .ok_or(ListDefinitionError::UnsupportedShape)
}

fn has_name(element: &XmlElementToken, namespace: &str, local_name: &str) -> bool {
    element.name().namespace() == Some(namespace) && element.name().local_name() == local_name
}

fn require_name(
    element: &XmlElementToken,
    namespace: &str,
    local_name: &str,
) -> Result<(), ListDefinitionError> {
    if has_name(element, namespace, local_name) {
        Ok(())
    } else {
        Err(ListDefinitionError::UnsupportedShape)
    }
}

fn child_indexes(
    document: &PreservingXmlDocument,
    parent: usize,
) -> Result<Vec<usize>, ListDefinitionError> {
    let mut children = Vec::new();
    let mut current = element(document, parent)?.first_child();
    while let Some(index) = current {
        children
            .try_reserve(1)
            .map_err(|_| ListDefinitionError::AllocationFailed)?;
        children.push(index);
        current = element(document, index)?.next_sibling();
    }
    Ok(children)
}

fn exactly_one_child(
    document: &PreservingXmlDocument,
    parent: usize,
    namespace: &str,
    local_name: &str,
) -> Result<usize, ListDefinitionError> {
    optional_one_child(document, parent, namespace, local_name)?
        .ok_or(ListDefinitionError::UnsupportedShape)
}

fn optional_one_child(
    document: &PreservingXmlDocument,
    parent: usize,
    namespace: &str,
    local_name: &str,
) -> Result<Option<usize>, ListDefinitionError> {
    let mut found = None;
    for index in child_indexes(document, parent)? {
        let child = element(document, index)?;
        if child.name().local_name() != local_name {
            continue;
        }
        if !has_name(child, namespace, local_name) || found.replace(index).is_some() {
            return Err(ListDefinitionError::UnsupportedShape);
        }
    }
    Ok(found)
}

fn validate_attributes(
    element: &XmlElementToken,
    allowed: &[&str],
) -> Result<(), ListDefinitionError> {
    let mut seen = BTreeSet::<&str>::new();
    for attribute in element.attributes() {
        if attribute.is_namespace_declaration() {
            continue;
        }
        let name = attribute.name().local_name();
        if attribute.name().namespace().is_some() || !allowed.contains(&name) || !seen.insert(name)
        {
            return Err(ListDefinitionError::UnsupportedShape);
        }
    }
    Ok(())
}

fn optional_attribute<'a>(element: &'a XmlElementToken, name: &str) -> Option<&'a str> {
    element
        .attributes()
        .iter()
        .find(|attribute| {
            !attribute.is_namespace_declaration()
                && attribute.name().namespace().is_none()
                && attribute.name().local_name() == name
        })
        .map(XmlAttributeToken::semantic_value)
}

fn required_attribute<'a>(
    element: &'a XmlElementToken,
    name: &str,
) -> Result<&'a str, ListDefinitionError> {
    optional_attribute(element, name).ok_or(ListDefinitionError::UnsupportedShape)
}

fn parse_u32(value: &str) -> Result<u32, ListDefinitionError> {
    if value.is_empty() || !value.bytes().all(|byte| byte.is_ascii_digit()) {
        return Err(ListDefinitionError::InvalidNumber);
    }
    value
        .parse()
        .map_err(|_| ListDefinitionError::InvalidNumber)
}

fn parse_i32(value: &str) -> Result<i32, ListDefinitionError> {
    let digits = value.strip_prefix('-').unwrap_or(value);
    if digits.is_empty() || !digits.bytes().all(|byte| byte.is_ascii_digit()) {
        return Err(ListDefinitionError::InvalidNumber);
    }
    value
        .parse()
        .map_err(|_| ListDefinitionError::InvalidNumber)
}

fn required_u32(element: &XmlElementToken, name: &str) -> Result<u32, ListDefinitionError> {
    parse_u32(required_attribute(element, name)?)
}

fn required_u8(element: &XmlElementToken, name: &str) -> Result<u8, ListDefinitionError> {
    u8::try_from(required_u32(element, name)?).map_err(|_| ListDefinitionError::InvalidNumber)
}

fn required_usize(element: &XmlElementToken, name: &str) -> Result<usize, ListDefinitionError> {
    usize::try_from(required_u32(element, name)?).map_err(|_| ListDefinitionError::InvalidNumber)
}

fn required_i32(element: &XmlElementToken, name: &str) -> Result<i32, ListDefinitionError> {
    parse_i32(required_attribute(element, name)?)
}

fn required_bool(element: &XmlElementToken, name: &str) -> Result<bool, ListDefinitionError> {
    match required_attribute(element, name)? {
        "1" | "true" => Ok(true),
        "0" | "false" => Ok(false),
        _ => Err(ListDefinitionError::InvalidBoolean),
    }
}

fn parse_scalar(value: &str) -> Result<char, ListDefinitionError> {
    let mut chars = value.chars();
    let scalar = chars.next().ok_or(ListDefinitionError::InvalidText)?;
    if chars.next().is_some() {
        return Err(ListDefinitionError::InvalidText);
    }
    validate_scalar(scalar)?;
    Ok(scalar)
}

fn direct_text(
    document: &PreservingXmlDocument,
    index: usize,
    limits: ListDefinitionLimits,
) -> Result<String, ListDefinitionError> {
    let value = element(document, index)?;
    if value.first_child().is_some() {
        return Err(ListDefinitionError::UnsupportedShape);
    }
    if value.is_empty() {
        return Ok(String::new());
    }
    let end = value
        .end_token()
        .ok_or(ListDefinitionError::UnsupportedShape)?;
    let mut result = String::new();
    for token in &document.tokens()[(value.start_token() + 1)..end] {
        if token.element_index() != Some(index) {
            continue;
        }
        match token.kind() {
            XmlTokenKind::Text | XmlTokenKind::Whitespace | XmlTokenKind::Reference => {
                let source = document.source_text(token.span())?;
                let normalized = source.replace("\r\n", "\n").replace('\r', "\n");
                let decoded =
                    unescape(&normalized).map_err(|_| ListDefinitionError::InvalidText)?;
                let next = result
                    .len()
                    .checked_add(decoded.len())
                    .ok_or(ListDefinitionError::InvalidText)?;
                if next > limits.config().text_bytes {
                    return Err(ListDefinitionError::InvalidText);
                }
                result
                    .try_reserve(decoded.len())
                    .map_err(|_| ListDefinitionError::AllocationFailed)?;
                result.push_str(&decoded);
            }
            XmlTokenKind::Comment => return Err(ListDefinitionError::UnsupportedShape),
            _ => {}
        }
    }
    validate_text(&result, limits)?;
    Ok(result)
}

fn require_only_whitespace_content(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<(), ListDefinitionError> {
    let value = element(document, index)?;
    if value.is_empty() {
        return Ok(());
    }
    let end = value
        .end_token()
        .ok_or(ListDefinitionError::UnsupportedShape)?;
    for token in &document.tokens()[(value.start_token() + 1)..end] {
        if token.element_index() != Some(index) {
            continue;
        }
        match token.kind() {
            XmlTokenKind::Text | XmlTokenKind::Reference | XmlTokenKind::Comment => {
                return Err(ListDefinitionError::UnsupportedShape);
            }
            XmlTokenKind::Whitespace if !document.source_text(token.span())?.trim().is_empty() => {
                return Err(ListDefinitionError::UnsupportedShape);
            }
            _ => {}
        }
    }
    Ok(())
}

fn read_dense_id_domain(
    document: &PreservingXmlDocument,
    container: usize,
    child_name: &str,
    base: u32,
    limits: ListDefinitionLimits,
) -> Result<Vec<u32>, ListDefinitionError> {
    let value = element(document, container)?;
    validate_attributes(value, &["itemCnt"])?;
    require_only_whitespace_content(document, container)?;
    let expected_count = required_usize(value, "itemCnt")?;
    let children = child_indexes(document, container)?;
    if children.len() != expected_count || children.len() > limits.config().levels {
        return Err(ListDefinitionError::CountMismatch);
    }
    let mut ids = Vec::new();
    ids.try_reserve(children.len())
        .map_err(|_| ListDefinitionError::AllocationFailed)?;
    for (position, index) in children.into_iter().enumerate() {
        let child = element(document, index)?;
        require_name(child, HEAD_NS, child_name)?;
        let id = required_u32(child, "id")?;
        let expected = base
            .checked_add(u32::try_from(position).map_err(|_| ListDefinitionError::InvalidId)?)
            .ok_or(ListDefinitionError::InvalidId)?;
        if id != expected {
            return Err(ListDefinitionError::InvalidId);
        }
        ids.push(id);
    }
    Ok(ids)
}

fn validate_document_envelope(document: &PreservingXmlDocument) -> Result<(), ListDefinitionError> {
    for token in document
        .tokens()
        .iter()
        .filter(|token| token.element_index().is_none())
    {
        if !matches!(
            token.kind(),
            XmlTokenKind::ByteOrderMark | XmlTokenKind::Declaration | XmlTokenKind::Whitespace
        ) {
            return Err(ListDefinitionError::UnsupportedShape);
        }
    }
    Ok(())
}

struct BoundedXml {
    bytes: Vec<u8>,
    limit: usize,
}

impl BoundedXml {
    fn new(limit: usize) -> Result<Self, ListDefinitionError> {
        let mut bytes = Vec::new();
        bytes
            .try_reserve(limit.min(4096))
            .map_err(|_| ListDefinitionError::AllocationFailed)?;
        Ok(Self { bytes, limit })
    }

    fn push(&mut self, value: &str) -> Result<(), ListDefinitionError> {
        let next = self
            .bytes
            .len()
            .checked_add(value.len())
            .ok_or(ListDefinitionError::OutputLimit)?;
        if next > self.limit {
            return Err(ListDefinitionError::OutputLimit);
        }
        self.bytes
            .try_reserve(value.len())
            .map_err(|_| ListDefinitionError::AllocationFailed)?;
        self.bytes.extend_from_slice(value.as_bytes());
        Ok(())
    }

    fn push_escaped(&mut self, value: &str) -> Result<(), ListDefinitionError> {
        self.push(&escape(value))
    }

    fn push_u8(&mut self, value: u8) -> Result<(), ListDefinitionError> {
        self.push(&value.to_string())
    }

    fn push_u32(&mut self, value: u32) -> Result<(), ListDefinitionError> {
        self.push(&value.to_string())
    }

    fn push_i32(&mut self, value: i32) -> Result<(), ListDefinitionError> {
        self.push(&value.to_string())
    }

    fn push_usize(&mut self, value: usize) -> Result<(), ListDefinitionError> {
        self.push(&value.to_string())
    }

    fn push_bool(&mut self, value: bool) -> Result<(), ListDefinitionError> {
        self.push(if value { "1" } else { "0" })
    }

    fn finish(self) -> Vec<u8> {
        self.bytes
    }
}
