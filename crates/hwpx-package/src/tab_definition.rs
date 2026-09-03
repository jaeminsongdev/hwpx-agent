use std::collections::{BTreeMap, BTreeSet};

use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::character_style::LineType2;
use crate::paragraph_style::ParagraphStyleCatalog;
use crate::preserving_xml::{
    PreservingXmlDocument, PreservingXmlError, XmlAttributeToken, XmlElementToken, XmlTokenKind,
};

pub const TAB_DEFINITION_PROFILE_ID: &str = "hwpx-agent.tab-definition/1";

const HEAD_NS: &str = "http://www.hancom.co.kr/hwpml/2011/head";
const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const HWPUNIT_CHAR_NS: &str = "http://www.hancom.co.kr/hwpml/2016/HwpUnitChar";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TabDefinitionLimitConfig {
    pub input_bytes: usize,
    pub elements: usize,
    pub definitions: usize,
    pub stops: usize,
}

impl Default for TabDefinitionLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 2 * 1024 * 1024,
            elements: 32_768,
            definitions: 16_384,
            stops: 65_536,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct TabDefinitionLimits(TabDefinitionLimitConfig);

impl TabDefinitionLimits {
    pub const HARD_MAX_INPUT_BYTES: usize = 4 * 1024 * 1024;
    pub const HARD_MAX_ELEMENTS: usize = 131_072;
    pub const HARD_MAX_DEFINITIONS: usize = 32_768;
    pub const HARD_MAX_STOPS: usize = 262_144;

    /// Creates a finite current-Hangul-2020 tab-definition limit set.
    ///
    /// # Errors
    ///
    /// Rejects zero values and values above their hard ceilings.
    pub fn new(config: TabDefinitionLimitConfig) -> Result<Self, TabDefinitionError> {
        let values = [
            (config.input_bytes, Self::HARD_MAX_INPUT_BYTES),
            (config.elements, Self::HARD_MAX_ELEMENTS),
            (config.definitions, Self::HARD_MAX_DEFINITIONS),
            (config.stops, Self::HARD_MAX_STOPS),
        ];
        if values
            .into_iter()
            .any(|(value, ceiling)| value == 0 || value > ceiling)
        {
            return Err(TabDefinitionError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> TabDefinitionLimitConfig {
        self.0
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum TabStopAlignment {
    Left,
    Right,
    Center,
    Decimal,
}

impl TabStopAlignment {
    fn parse(value: &str) -> Result<Self, TabDefinitionError> {
        match value {
            "LEFT" => Ok(Self::Left),
            "RIGHT" => Ok(Self::Right),
            "CENTER" => Ok(Self::Center),
            "DECIMAL" => Ok(Self::Decimal),
            _ => Err(TabDefinitionError::InvalidEnum),
        }
    }

    const fn as_str(self) -> &'static str {
        match self {
            Self::Left => "LEFT",
            Self::Right => "RIGHT",
            Self::Center => "CENTER",
            Self::Decimal => "DECIMAL",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum TabPositionUnit {
    Character,
    HwpUnit,
}

impl TabPositionUnit {
    fn parse(value: &str) -> Result<Self, TabDefinitionError> {
        match value {
            "CHAR" => Ok(Self::Character),
            "HWPUNIT" => Ok(Self::HwpUnit),
            _ => Err(TabDefinitionError::InvalidEnum),
        }
    }

    const fn as_str(self) -> &'static str {
        match self {
            Self::Character => "CHAR",
            Self::HwpUnit => "HWPUNIT",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct TabItem {
    pub position: i32,
    pub alignment: TabStopAlignment,
    pub leader: LineType2,
    pub unit: Option<TabPositionUnit>,
}

#[derive(Clone, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum TabStop {
    Direct(TabItem),
    HwpUnitChar { current: TabItem, fallback: TabItem },
}

impl TabStop {
    #[must_use]
    pub const fn effective_position(&self) -> i32 {
        match self {
            Self::Direct(item) => item.position,
            Self::HwpUnitChar { fallback, .. } => fallback.position,
        }
    }

    const fn effective_unit(&self) -> TabPositionUnit {
        match self {
            Self::Direct(item) => match item.unit {
                Some(unit) => unit,
                None => TabPositionUnit::HwpUnit,
            },
            Self::HwpUnitChar { .. } => TabPositionUnit::HwpUnit,
        }
    }
}

#[derive(Clone, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct TabDefinition {
    pub id: u32,
    pub auto_tab_left: bool,
    pub auto_tab_right: bool,
    pub stops: Vec<TabStop>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct TabDefinitionCatalog {
    pub definitions: Vec<TabDefinition>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct DeduplicatedTabDefinitions {
    pub definitions: Vec<TabDefinition>,
    pub old_to_new: Vec<u32>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct TabDefinitionLoweringReceipt {
    pub profile_id: &'static str,
    pub sha256: [u8; 32],
    pub output_bytes: usize,
    pub definition_count: usize,
    pub stop_count: usize,
}

#[derive(Debug, Eq, Error, PartialEq)]
pub enum TabDefinitionError {
    #[error("tab-definition limits are invalid")]
    InvalidLimit,
    #[error("tab-definition input exceeds its finite limit")]
    InputLimit,
    #[error("tab-definition XML failed preserving admission")]
    Preserving(#[from] PreservingXmlError),
    #[error("tab-definition root is not the current Hangul 2020 head profile")]
    WrongRoot,
    #[error("tab-definition element or attribute shape is unsupported")]
    UnsupportedShape,
    #[error("tab-definition count does not match content")]
    CountMismatch,
    #[error("tab-definition identifier is invalid")]
    InvalidId,
    #[error("tab-definition paragraph reference is dangling")]
    DanglingReference,
    #[error("tab-definition paragraph reference count exceeds its finite limit")]
    ReferenceLimit,
    #[error("tab-definition numeric attribute is invalid")]
    InvalidNumber,
    #[error("tab-definition boolean attribute is invalid")]
    InvalidBoolean,
    #[error("tab-definition enum attribute is invalid")]
    InvalidEnum,
    #[error("tab-definition position is outside the current-2020 range")]
    OutOfRange,
    #[error("tab-definition stops are not in strict position order")]
    InvalidOrder,
    #[error("tab-definition stops mix incomparable position units")]
    MixedUnits,
    #[error("tab-definition count exceeds its finite limit")]
    DefinitionLimit,
    #[error("tab-definition stop count exceeds its finite limit")]
    StopLimit,
    #[error("tab-definition element count exceeds its finite limit")]
    ElementLimit,
    #[error("tab-definition output exceeds its finite limit")]
    OutputLimit,
    #[error("tab-definition allocation failed")]
    AllocationFailed,
    #[error("tab-definition lowered readback differs")]
    ReadbackMismatch,
}

impl TabDefinitionError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "tab_definition_invalid_limit",
            Self::InputLimit => "tab_definition_input_limit",
            Self::Preserving(_) => "tab_definition_preserving_xml",
            Self::WrongRoot => "tab_definition_wrong_root",
            Self::UnsupportedShape => "tab_definition_unsupported_shape",
            Self::CountMismatch => "tab_definition_count_mismatch",
            Self::InvalidId => "tab_definition_invalid_id",
            Self::DanglingReference => "tab_definition_dangling_reference",
            Self::ReferenceLimit => "tab_definition_reference_limit",
            Self::InvalidNumber => "tab_definition_invalid_number",
            Self::InvalidBoolean => "tab_definition_invalid_boolean",
            Self::InvalidEnum => "tab_definition_invalid_enum",
            Self::OutOfRange => "tab_definition_out_of_range",
            Self::InvalidOrder => "tab_definition_invalid_order",
            Self::MixedUnits => "tab_definition_mixed_units",
            Self::DefinitionLimit => "tab_definition_definition_limit",
            Self::StopLimit => "tab_definition_stop_limit",
            Self::ElementLimit => "tab_definition_element_limit",
            Self::OutputLimit => "tab_definition_output_limit",
            Self::AllocationFailed => "tab_definition_allocation_failed",
            Self::ReadbackMismatch => "tab_definition_readback_mismatch",
        }
    }
}

#[derive(Debug)]
pub struct TabDefinitionCatalogReader;

impl TabDefinitionCatalogReader {
    /// Lifts the tabProperties slice from a current-2020 header or refList fragment.
    ///
    /// # Errors
    ///
    /// Rejects malformed, unsupported, unbounded, non-dense or unordered typed content.
    pub fn read(
        bytes: &[u8],
        limits: TabDefinitionLimits,
    ) -> Result<TabDefinitionCatalog, TabDefinitionError> {
        if bytes.is_empty() || bytes.len() > limits.config().input_bytes {
            return Err(TabDefinitionError::InputLimit);
        }
        let document = PreservingXmlDocument::parse(bytes)?;
        if document.elements().len() > limits.config().elements {
            return Err(TabDefinitionError::ElementLimit);
        }
        validate_document_envelope(&document)?;
        let ref_list = find_ref_list(&document)?;
        let tab_properties = exactly_one_child(&document, ref_list, HEAD_NS, "tabProperties")?;
        let catalog = read_catalog(&document, tab_properties, limits)?;
        validate_catalog(&catalog, limits)?;
        Ok(catalog)
    }
}

#[derive(Debug)]
pub struct TabDefinitionCatalogWriter;

impl TabDefinitionCatalogWriter {
    /// Lowers a typed catalog to deterministic current-2020 refList XML and reparses it.
    ///
    /// # Errors
    ///
    /// Rejects invalid public values, limit violations or readback drift.
    pub fn lower(
        catalog: &TabDefinitionCatalog,
        limits: TabDefinitionLimits,
    ) -> Result<Vec<u8>, TabDefinitionError> {
        let (bytes, _) = Self::lower_with_receipt(catalog, limits)?;
        Ok(bytes)
    }

    /// Lowers a typed catalog and returns a deterministic integrity receipt.
    ///
    /// # Errors
    ///
    /// Applies the same checks as [`Self::lower`].
    pub fn lower_with_receipt(
        catalog: &TabDefinitionCatalog,
        limits: TabDefinitionLimits,
    ) -> Result<(Vec<u8>, TabDefinitionLoweringReceipt), TabDefinitionError> {
        validate_catalog(catalog, limits)?;
        let mut output = BoundedXml::new(limits.config().input_bytes)?;
        output.push("<?xml version=\"1.0\" encoding=\"UTF-8\"?>")?;
        output.push("<hh:refList xmlns:hh=\"")?;
        output.push(HEAD_NS)?;
        output.push("\" xmlns:hp=\"")?;
        output.push(PARAGRAPH_NS)?;
        output.push("\"><hh:tabProperties itemCnt=\"")?;
        output.push_usize(catalog.definitions.len())?;
        output.push("\">")?;
        for definition in &catalog.definitions {
            write_definition(&mut output, definition)?;
        }
        output.push("</hh:tabProperties></hh:refList>")?;
        let bytes = output.finish();
        let readback = TabDefinitionCatalogReader::read(&bytes, limits)?;
        if readback != *catalog {
            return Err(TabDefinitionError::ReadbackMismatch);
        }
        let receipt = TabDefinitionLoweringReceipt {
            profile_id: TAB_DEFINITION_PROFILE_ID,
            sha256: <[u8; 32]>::from(Sha256::digest(&bytes)),
            output_bytes: bytes.len(),
            definition_count: catalog.definitions.len(),
            stop_count: catalog
                .definitions
                .iter()
                .map(|definition| definition.stops.len())
                .sum(),
        };
        Ok((bytes, receipt))
    }
}

impl TabDefinitionCatalog {
    /// Deduplicates semantic tab definitions in deterministic first-occurrence order.
    ///
    /// # Errors
    ///
    /// Rejects an invalid catalog or allocation/identifier overflow.
    pub fn deduplicate(
        &self,
        limits: TabDefinitionLimits,
    ) -> Result<DeduplicatedTabDefinitions, TabDefinitionError> {
        validate_catalog(self, limits)?;
        let mut seen = BTreeMap::<TabDefinition, u32>::new();
        let mut definitions = Vec::new();
        let mut old_to_new = Vec::new();
        definitions
            .try_reserve(self.definitions.len())
            .map_err(|_| TabDefinitionError::AllocationFailed)?;
        old_to_new
            .try_reserve(self.definitions.len())
            .map_err(|_| TabDefinitionError::AllocationFailed)?;
        for definition in &self.definitions {
            let mut semantic = definition.clone();
            semantic.id = 0;
            let new_id = if let Some(existing) = seen.get(&semantic) {
                *existing
            } else {
                let allocated =
                    u32::try_from(definitions.len()).map_err(|_| TabDefinitionError::InvalidId)?;
                let mut canonical = definition.clone();
                canonical.id = allocated;
                definitions.push(canonical);
                seen.insert(semantic, allocated);
                allocated
            };
            old_to_new.push(new_id);
        }
        Ok(DeduplicatedTabDefinitions {
            definitions,
            old_to_new,
        })
    }

    /// Verifies that a P05-03 paragraph catalog names exactly this tab ID domain.
    ///
    /// # Errors
    ///
    /// Returns a stable reference error for domain drift or a dangling paragraph reference.
    pub fn validate_paragraph_references(
        &self,
        paragraphs: &ParagraphStyleCatalog,
        limits: TabDefinitionLimits,
    ) -> Result<(), TabDefinitionError> {
        validate_catalog(self, limits)?;
        validate_paragraph_reference_count(paragraphs)?;
        let expected = dense_ids(self.definitions.len())?;
        if paragraphs.references.tab_property_ids != expected
            || paragraphs.styles.iter().any(|style| {
                usize::try_from(style.tab_property_id_ref)
                    .ok()
                    .is_none_or(|id| id >= self.definitions.len())
            })
        {
            return Err(TabDefinitionError::DanglingReference);
        }
        Ok(())
    }
}

impl DeduplicatedTabDefinitions {
    /// Atomically rewrites only typed P05-03 paragraph tab-property references and their domain.
    ///
    /// # Errors
    ///
    /// Rejects malformed maps, source-domain drift or dangling references before any mutation.
    pub fn rewrite_paragraph_styles(
        &self,
        paragraphs: &mut ParagraphStyleCatalog,
    ) -> Result<(), TabDefinitionError> {
        self.validate_mapping()?;
        validate_paragraph_reference_count(paragraphs)?;
        let old_domain = dense_ids(self.old_to_new.len())?;
        if paragraphs.references.tab_property_ids != old_domain {
            return Err(TabDefinitionError::DanglingReference);
        }
        let mut rewritten = Vec::new();
        rewritten
            .try_reserve(paragraphs.styles.len())
            .map_err(|_| TabDefinitionError::AllocationFailed)?;
        for style in &paragraphs.styles {
            let index = usize::try_from(style.tab_property_id_ref)
                .map_err(|_| TabDefinitionError::DanglingReference)?;
            rewritten.push(
                self.old_to_new
                    .get(index)
                    .copied()
                    .ok_or(TabDefinitionError::DanglingReference)?,
            );
        }
        let new_domain = dense_ids(self.definitions.len())?;
        for (style, mapped) in paragraphs.styles.iter_mut().zip(rewritten) {
            style.tab_property_id_ref = mapped;
        }
        paragraphs.references.tab_property_ids = new_domain;
        Ok(())
    }

    fn validate_mapping(&self) -> Result<(), TabDefinitionError> {
        if self.definitions.len() > TabDefinitionLimits::HARD_MAX_DEFINITIONS
            || self.old_to_new.len() > TabDefinitionLimits::HARD_MAX_DEFINITIONS
        {
            return Err(TabDefinitionError::DefinitionLimit);
        }
        for (position, definition) in self.definitions.iter().enumerate() {
            let expected = u32::try_from(position).map_err(|_| TabDefinitionError::InvalidId)?;
            if definition.id != expected {
                return Err(TabDefinitionError::InvalidId);
            }
        }
        let count =
            u32::try_from(self.definitions.len()).map_err(|_| TabDefinitionError::InvalidId)?;
        if self.old_to_new.len() < self.definitions.len()
            || self.old_to_new.iter().any(|mapped| *mapped >= count)
        {
            return Err(TabDefinitionError::InvalidId);
        }
        Ok(())
    }
}

fn validate_paragraph_reference_count(
    paragraphs: &ParagraphStyleCatalog,
) -> Result<(), TabDefinitionError> {
    if paragraphs.styles.len() > TabDefinitionLimits::HARD_MAX_DEFINITIONS
        || paragraphs.references.tab_property_ids.len() > TabDefinitionLimits::HARD_MAX_DEFINITIONS
    {
        return Err(TabDefinitionError::ReferenceLimit);
    }
    Ok(())
}

fn read_catalog(
    document: &PreservingXmlDocument,
    index: usize,
    limits: TabDefinitionLimits,
) -> Result<TabDefinitionCatalog, TabDefinitionError> {
    let container = element(document, index)?;
    require_name(container, HEAD_NS, "tabProperties")?;
    validate_attributes(container, &["itemCnt"])?;
    require_only_whitespace_content(document, index)?;
    let children = child_indexes(document, index)?;
    if children.len() != required_usize(container, "itemCnt")? {
        return Err(TabDefinitionError::CountMismatch);
    }
    if children.len() > limits.config().definitions {
        return Err(TabDefinitionError::DefinitionLimit);
    }
    let mut definitions = Vec::new();
    definitions
        .try_reserve(children.len())
        .map_err(|_| TabDefinitionError::AllocationFailed)?;
    let mut stop_count = 0usize;
    for (expected, child) in children.into_iter().enumerate() {
        let remaining_stops = limits
            .config()
            .stops
            .checked_sub(stop_count)
            .ok_or(TabDefinitionError::StopLimit)?;
        let definition = read_definition(document, child, remaining_stops)?;
        let expected = u32::try_from(expected).map_err(|_| TabDefinitionError::InvalidId)?;
        if definition.id != expected {
            return Err(TabDefinitionError::InvalidId);
        }
        stop_count = stop_count
            .checked_add(definition.stops.len())
            .ok_or(TabDefinitionError::StopLimit)?;
        if stop_count > limits.config().stops {
            return Err(TabDefinitionError::StopLimit);
        }
        definitions.push(definition);
    }
    Ok(TabDefinitionCatalog { definitions })
}

fn read_definition(
    document: &PreservingXmlDocument,
    index: usize,
    remaining_stops: usize,
) -> Result<TabDefinition, TabDefinitionError> {
    let value = element(document, index)?;
    require_name(value, HEAD_NS, "tabPr")?;
    validate_attributes(value, &["id", "autoTabLeft", "autoTabRight"])?;
    require_only_whitespace_content(document, index)?;
    let children = child_indexes(document, index)?;
    if children.len() > remaining_stops {
        return Err(TabDefinitionError::StopLimit);
    }
    let mut stops = Vec::new();
    stops
        .try_reserve(children.len())
        .map_err(|_| TabDefinitionError::AllocationFailed)?;
    for child in children {
        let value = element(document, child)?;
        let stop = if has_name(value, HEAD_NS, "tabItem") {
            TabStop::Direct(read_item(document, child)?)
        } else if has_name(value, PARAGRAPH_NS, "switch") {
            read_compatible_stop(document, child)?
        } else {
            return Err(TabDefinitionError::UnsupportedShape);
        };
        stops.push(stop);
    }
    let definition = TabDefinition {
        id: required_u32(value, "id")?,
        auto_tab_left: optional_bool(value, "autoTabLeft")?.unwrap_or(false),
        auto_tab_right: optional_bool(value, "autoTabRight")?.unwrap_or(false),
        stops,
    };
    validate_definition(&definition)?;
    Ok(definition)
}

fn read_compatible_stop(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<TabStop, TabDefinitionError> {
    let value = element(document, index)?;
    require_name(value, PARAGRAPH_NS, "switch")?;
    validate_attributes(value, &[])?;
    require_only_whitespace_content(document, index)?;
    let children = child_indexes(document, index)?;
    if children.len() != 2 {
        return Err(TabDefinitionError::UnsupportedShape);
    }
    let case = element(document, children[0])?;
    require_name(case, PARAGRAPH_NS, "case")?;
    validate_attributes_with_namespace(case, &[(Some(PARAGRAPH_NS), "required-namespace")])?;
    if required_attribute_ns(case, PARAGRAPH_NS, "required-namespace")? != HWPUNIT_CHAR_NS {
        return Err(TabDefinitionError::UnsupportedShape);
    }
    require_only_whitespace_content(document, children[0])?;
    let current_index = exactly_one_child(document, children[0], HEAD_NS, "tabItem")?;
    if child_indexes(document, children[0])?.len() != 1 {
        return Err(TabDefinitionError::UnsupportedShape);
    }

    let fallback = element(document, children[1])?;
    require_name(fallback, PARAGRAPH_NS, "default")?;
    validate_attributes(fallback, &[])?;
    require_only_whitespace_content(document, children[1])?;
    let fallback_index = exactly_one_child(document, children[1], HEAD_NS, "tabItem")?;
    if child_indexes(document, children[1])?.len() != 1 {
        return Err(TabDefinitionError::UnsupportedShape);
    }
    let current = read_item(document, current_index)?;
    let fallback = read_item(document, fallback_index)?;
    validate_compatible_pair(current, fallback)?;
    Ok(TabStop::HwpUnitChar { current, fallback })
}

fn read_item(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<TabItem, TabDefinitionError> {
    let value = element(document, index)?;
    require_name(value, HEAD_NS, "tabItem")?;
    validate_attributes(value, &["pos", "type", "leader", "unit"])?;
    require_no_children(document, index)?;
    let item = TabItem {
        position: required_i32(value, "pos")?,
        alignment: TabStopAlignment::parse(required_attribute(value, "type")?)?,
        leader: parse_line_type(required_attribute(value, "leader")?)?,
        unit: optional_attribute(value, "unit")
            .map(TabPositionUnit::parse)
            .transpose()?,
    };
    validate_item(item)?;
    Ok(item)
}

fn validate_catalog(
    catalog: &TabDefinitionCatalog,
    limits: TabDefinitionLimits,
) -> Result<(), TabDefinitionError> {
    if catalog.definitions.len() > limits.config().definitions {
        return Err(TabDefinitionError::DefinitionLimit);
    }
    let mut total_stops = 0usize;
    for (position, definition) in catalog.definitions.iter().enumerate() {
        let expected = u32::try_from(position).map_err(|_| TabDefinitionError::InvalidId)?;
        if definition.id != expected {
            return Err(TabDefinitionError::InvalidId);
        }
        validate_definition(definition)?;
        total_stops = total_stops
            .checked_add(definition.stops.len())
            .ok_or(TabDefinitionError::StopLimit)?;
        if total_stops > limits.config().stops {
            return Err(TabDefinitionError::StopLimit);
        }
    }
    Ok(())
}

fn validate_definition(definition: &TabDefinition) -> Result<(), TabDefinitionError> {
    let mut previous = None;
    let mut common_unit = None;
    for stop in &definition.stops {
        match stop {
            TabStop::Direct(item) => validate_item(*item)?,
            TabStop::HwpUnitChar { current, fallback } => {
                validate_compatible_pair(*current, *fallback)?;
            }
        }
        let position = stop.effective_position();
        let unit = stop.effective_unit();
        if common_unit.is_some_and(|expected| unit != expected) {
            return Err(TabDefinitionError::MixedUnits);
        }
        common_unit = Some(unit);
        if previous.is_some_and(|value| position <= value) {
            return Err(TabDefinitionError::InvalidOrder);
        }
        previous = Some(position);
    }
    Ok(())
}

fn validate_item(item: TabItem) -> Result<(), TabDefinitionError> {
    if item.position < 0 {
        return Err(TabDefinitionError::OutOfRange);
    }
    Ok(())
}

fn validate_compatible_pair(current: TabItem, fallback: TabItem) -> Result<(), TabDefinitionError> {
    validate_item(current)?;
    validate_item(fallback)?;
    if current.alignment != fallback.alignment
        || current.leader != fallback.leader
        || current.unit != Some(TabPositionUnit::HwpUnit)
        || fallback.unit.is_some()
    {
        return Err(TabDefinitionError::UnsupportedShape);
    }
    let doubled = current
        .position
        .checked_mul(2)
        .ok_or(TabDefinitionError::OutOfRange)?;
    if fallback.position != doubled
        && fallback.position
            != doubled
                .checked_add(1)
                .ok_or(TabDefinitionError::OutOfRange)?
    {
        return Err(TabDefinitionError::UnsupportedShape);
    }
    Ok(())
}

fn write_definition(
    output: &mut BoundedXml,
    definition: &TabDefinition,
) -> Result<(), TabDefinitionError> {
    output.push("<hh:tabPr id=\"")?;
    output.push_u32(definition.id)?;
    output.push("\" autoTabLeft=\"")?;
    output.push_bool(definition.auto_tab_left)?;
    output.push("\" autoTabRight=\"")?;
    output.push_bool(definition.auto_tab_right)?;
    if definition.stops.is_empty() {
        output.push("\"/>")?;
        return Ok(());
    }
    output.push("\">")?;
    for stop in &definition.stops {
        match stop {
            TabStop::Direct(item) => write_item(output, *item)?,
            TabStop::HwpUnitChar { current, fallback } => {
                output.push("<hp:switch><hp:case hp:required-namespace=\"")?;
                output.push(HWPUNIT_CHAR_NS)?;
                output.push("\">")?;
                write_item(output, *current)?;
                output.push("</hp:case><hp:default>")?;
                write_item(output, *fallback)?;
                output.push("</hp:default></hp:switch>")?;
            }
        }
    }
    output.push("</hh:tabPr>")?;
    Ok(())
}

fn write_item(output: &mut BoundedXml, item: TabItem) -> Result<(), TabDefinitionError> {
    output.push("<hh:tabItem pos=\"")?;
    output.push_i32(item.position)?;
    output.push("\" type=\"")?;
    output.push(item.alignment.as_str())?;
    output.push("\" leader=\"")?;
    output.push(line_type_str(item.leader))?;
    if let Some(unit) = item.unit {
        output.push("\" unit=\"")?;
        output.push(unit.as_str())?;
    }
    output.push("\"/>")?;
    Ok(())
}

fn dense_ids(count: usize) -> Result<Vec<u32>, TabDefinitionError> {
    let mut ids = Vec::new();
    ids.try_reserve(count)
        .map_err(|_| TabDefinitionError::AllocationFailed)?;
    for position in 0..count {
        ids.push(u32::try_from(position).map_err(|_| TabDefinitionError::InvalidId)?);
    }
    Ok(ids)
}

fn find_ref_list(document: &PreservingXmlDocument) -> Result<usize, TabDefinitionError> {
    let root_index = document.root_element();
    let root = element(document, root_index)?;
    if has_name(root, HEAD_NS, "refList") {
        Ok(root_index)
    } else if has_name(root, HEAD_NS, "head") {
        exactly_one_child(document, root_index, HEAD_NS, "refList")
    } else {
        Err(TabDefinitionError::WrongRoot)
    }
}

fn element(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<&XmlElementToken, TabDefinitionError> {
    document
        .elements()
        .get(index)
        .ok_or(TabDefinitionError::UnsupportedShape)
}

fn has_name(element: &XmlElementToken, namespace: &str, local_name: &str) -> bool {
    element.name().namespace() == Some(namespace) && element.name().local_name() == local_name
}

fn require_name(
    element: &XmlElementToken,
    namespace: &str,
    local_name: &str,
) -> Result<(), TabDefinitionError> {
    if has_name(element, namespace, local_name) {
        Ok(())
    } else {
        Err(TabDefinitionError::UnsupportedShape)
    }
}

fn child_indexes(
    document: &PreservingXmlDocument,
    parent: usize,
) -> Result<Vec<usize>, TabDefinitionError> {
    let mut children = Vec::new();
    let mut current = element(document, parent)?.first_child();
    while let Some(index) = current {
        children
            .try_reserve(1)
            .map_err(|_| TabDefinitionError::AllocationFailed)?;
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
) -> Result<usize, TabDefinitionError> {
    let mut found = None;
    for index in child_indexes(document, parent)? {
        let child = element(document, index)?;
        if child.name().local_name() != local_name {
            continue;
        }
        if !has_name(child, namespace, local_name) || found.replace(index).is_some() {
            return Err(TabDefinitionError::UnsupportedShape);
        }
    }
    found.ok_or(TabDefinitionError::UnsupportedShape)
}

fn validate_attributes(
    element: &XmlElementToken,
    allowed: &[&str],
) -> Result<(), TabDefinitionError> {
    let expected = allowed.iter().map(|name| (None, *name)).collect::<Vec<_>>();
    validate_attributes_with_namespace(element, &expected)
}

fn validate_attributes_with_namespace(
    element: &XmlElementToken,
    allowed: &[(Option<&str>, &str)],
) -> Result<(), TabDefinitionError> {
    let mut seen = BTreeSet::<(Option<&str>, &str)>::new();
    for attribute in element.attributes() {
        if attribute.is_namespace_declaration() {
            continue;
        }
        let key = (attribute.name().namespace(), attribute.name().local_name());
        if !allowed.contains(&key) || !seen.insert(key) {
            return Err(TabDefinitionError::UnsupportedShape);
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
) -> Result<&'a str, TabDefinitionError> {
    optional_attribute(element, name).ok_or(TabDefinitionError::UnsupportedShape)
}

fn required_attribute_ns<'a>(
    element: &'a XmlElementToken,
    namespace: &str,
    name: &str,
) -> Result<&'a str, TabDefinitionError> {
    element
        .attributes()
        .iter()
        .find(|attribute| {
            !attribute.is_namespace_declaration()
                && attribute.name().namespace() == Some(namespace)
                && attribute.name().local_name() == name
        })
        .map(XmlAttributeToken::semantic_value)
        .ok_or(TabDefinitionError::UnsupportedShape)
}

fn parse_u32(value: &str) -> Result<u32, TabDefinitionError> {
    if value.is_empty() || !value.bytes().all(|byte| byte.is_ascii_digit()) {
        return Err(TabDefinitionError::InvalidNumber);
    }
    value.parse().map_err(|_| TabDefinitionError::InvalidNumber)
}

fn parse_i32(value: &str) -> Result<i32, TabDefinitionError> {
    let digits = value.strip_prefix('-').unwrap_or(value);
    if digits.is_empty() || !digits.bytes().all(|byte| byte.is_ascii_digit()) {
        return Err(TabDefinitionError::InvalidNumber);
    }
    value.parse().map_err(|_| TabDefinitionError::InvalidNumber)
}

fn required_u32(element: &XmlElementToken, name: &str) -> Result<u32, TabDefinitionError> {
    parse_u32(required_attribute(element, name)?)
}

fn required_usize(element: &XmlElementToken, name: &str) -> Result<usize, TabDefinitionError> {
    usize::try_from(required_u32(element, name)?).map_err(|_| TabDefinitionError::InvalidNumber)
}

fn required_i32(element: &XmlElementToken, name: &str) -> Result<i32, TabDefinitionError> {
    parse_i32(required_attribute(element, name)?)
}

fn optional_bool(
    element: &XmlElementToken,
    name: &str,
) -> Result<Option<bool>, TabDefinitionError> {
    optional_attribute(element, name)
        .map(|value| match value {
            "1" | "true" => Ok(true),
            "0" | "false" => Ok(false),
            _ => Err(TabDefinitionError::InvalidBoolean),
        })
        .transpose()
}

fn parse_line_type(value: &str) -> Result<LineType2, TabDefinitionError> {
    match value {
        "NONE" => Ok(LineType2::None),
        "SOLID" => Ok(LineType2::Solid),
        "DOT" => Ok(LineType2::Dot),
        "DASH" => Ok(LineType2::Dash),
        "DASH_DOT" => Ok(LineType2::DashDot),
        "DASH_DOT_DOT" => Ok(LineType2::DashDotDot),
        "LONG_DASH" => Ok(LineType2::LongDash),
        "CIRCLE" => Ok(LineType2::Circle),
        "DOUBLE_SLIM" => Ok(LineType2::DoubleSlim),
        "SLIM_THICK" => Ok(LineType2::SlimThick),
        "THICK_SLIM" => Ok(LineType2::ThickSlim),
        "SLIM_THICK_SLIM" => Ok(LineType2::SlimThickSlim),
        _ => Err(TabDefinitionError::InvalidEnum),
    }
}

const fn line_type_str(value: LineType2) -> &'static str {
    match value {
        LineType2::None => "NONE",
        LineType2::Solid => "SOLID",
        LineType2::Dot => "DOT",
        LineType2::Dash => "DASH",
        LineType2::DashDot => "DASH_DOT",
        LineType2::DashDotDot => "DASH_DOT_DOT",
        LineType2::LongDash => "LONG_DASH",
        LineType2::Circle => "CIRCLE",
        LineType2::DoubleSlim => "DOUBLE_SLIM",
        LineType2::SlimThick => "SLIM_THICK",
        LineType2::ThickSlim => "THICK_SLIM",
        LineType2::SlimThickSlim => "SLIM_THICK_SLIM",
    }
}

fn require_no_children(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<(), TabDefinitionError> {
    require_only_whitespace_content(document, index)?;
    if element(document, index)?.first_child().is_some() {
        return Err(TabDefinitionError::UnsupportedShape);
    }
    Ok(())
}

fn require_only_whitespace_content(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<(), TabDefinitionError> {
    let value = element(document, index)?;
    if value.is_empty() {
        return Ok(());
    }
    let end = value
        .end_token()
        .ok_or(TabDefinitionError::UnsupportedShape)?;
    for token in &document.tokens()[(value.start_token() + 1)..end] {
        if token.element_index() != Some(index) {
            continue;
        }
        if matches!(
            token.kind(),
            XmlTokenKind::Text | XmlTokenKind::Reference | XmlTokenKind::Comment
        ) {
            return Err(TabDefinitionError::UnsupportedShape);
        }
    }
    Ok(())
}

fn validate_document_envelope(document: &PreservingXmlDocument) -> Result<(), TabDefinitionError> {
    for token in document
        .tokens()
        .iter()
        .filter(|token| token.element_index().is_none())
    {
        if !matches!(
            token.kind(),
            XmlTokenKind::ByteOrderMark | XmlTokenKind::Declaration | XmlTokenKind::Whitespace
        ) {
            return Err(TabDefinitionError::UnsupportedShape);
        }
    }
    Ok(())
}

struct BoundedXml {
    bytes: Vec<u8>,
    limit: usize,
}

impl BoundedXml {
    fn new(limit: usize) -> Result<Self, TabDefinitionError> {
        let mut bytes = Vec::new();
        bytes
            .try_reserve(limit.min(4096))
            .map_err(|_| TabDefinitionError::AllocationFailed)?;
        Ok(Self { bytes, limit })
    }

    fn push(&mut self, value: &str) -> Result<(), TabDefinitionError> {
        let next = self
            .bytes
            .len()
            .checked_add(value.len())
            .ok_or(TabDefinitionError::OutputLimit)?;
        if next > self.limit {
            return Err(TabDefinitionError::OutputLimit);
        }
        self.bytes
            .try_reserve(value.len())
            .map_err(|_| TabDefinitionError::AllocationFailed)?;
        self.bytes.extend_from_slice(value.as_bytes());
        Ok(())
    }

    fn push_u32(&mut self, value: u32) -> Result<(), TabDefinitionError> {
        self.push(&value.to_string())
    }

    fn push_i32(&mut self, value: i32) -> Result<(), TabDefinitionError> {
        self.push(&value.to_string())
    }

    fn push_usize(&mut self, value: usize) -> Result<(), TabDefinitionError> {
        self.push(&value.to_string())
    }

    fn push_bool(&mut self, value: bool) -> Result<(), TabDefinitionError> {
        self.push(if value { "1" } else { "0" })
    }

    fn finish(self) -> Vec<u8> {
        self.bytes
    }
}
