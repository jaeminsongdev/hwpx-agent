use std::collections::BTreeSet;
use std::fmt::{self, Debug};

use quick_xml::escape::unescape;
use sha2::{Digest as _, Sha256};
use thiserror::Error;
use unicode_normalization::UnicodeNormalization;

use crate::preserving_xml::{
    PreservingXmlDocument, PreservingXmlError, XmlAttributeToken, XmlElementToken, XmlTokenKind,
};

pub const HANCOM_2020_PARAGRAPH_NAMESPACE: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TextFlowLimitConfig {
    pub input_bytes: usize,
    pub runs: usize,
    pub items: usize,
    pub text_bytes: usize,
    pub field_depth: usize,
}

impl Default for TextFlowLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 2 * 1024 * 1024,
            runs: 4_096,
            items: 16_384,
            text_bytes: 1024 * 1024,
            field_depth: 128,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct TextFlowLimits(TextFlowLimitConfig);

impl TextFlowLimits {
    pub const HARD_MAX_INPUT_BYTES: usize = 2 * 1024 * 1024;
    pub const HARD_MAX_RUNS: usize = 16_384;
    pub const HARD_MAX_ITEMS: usize = 131_072;
    pub const HARD_MAX_TEXT_BYTES: usize = 2 * 1024 * 1024;
    pub const HARD_MAX_FIELD_DEPTH: usize = 1_024;

    /// Creates a finite P05-01 limit set.
    ///
    /// # Errors
    ///
    /// Rejects zero, over-ceiling, or internally inconsistent values.
    pub fn new(config: TextFlowLimitConfig) -> Result<Self, TextFlowError> {
        let values = [
            (config.input_bytes, Self::HARD_MAX_INPUT_BYTES),
            (config.runs, Self::HARD_MAX_RUNS),
            (config.items, Self::HARD_MAX_ITEMS),
            (config.text_bytes, Self::HARD_MAX_TEXT_BYTES),
            (config.field_depth, Self::HARD_MAX_FIELD_DEPTH),
        ];
        if values
            .into_iter()
            .any(|(value, ceiling)| value == 0 || value > ceiling)
            || config.text_bytes > config.input_bytes
            || config.runs > config.items
            || config.field_depth > config.items
        {
            return Err(TextFlowError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> TextFlowLimitConfig {
        self.0
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct TextParagraphProperties {
    pub id: u32,
    pub paragraph_property_id_ref: Option<u32>,
    pub style_id_ref: Option<u32>,
    pub page_break: bool,
    pub column_break: bool,
    pub merged: bool,
    pub paragraph_change_id: Option<u32>,
}

#[derive(Clone, Eq, PartialEq)]
pub struct TextFlow {
    pub paragraph: TextParagraphProperties,
    pub children: Vec<ParagraphChild>,
}

impl Debug for TextFlow {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TextFlow")
            .field("paragraph", &self.paragraph)
            .field("children", &self.children)
            .finish()
    }
}

impl TextFlow {
    /// Returns visible text in the cross-module semantic comparison form.
    /// Run and text-span boundaries remain present in the model and are not merged.
    /// # Errors
    ///
    /// Refuses to claim complete visible text if an opaque element may contain text.
    pub fn visible_text_nfc(&self) -> Result<String, TextFlowError> {
        let mut visible = String::new();
        for child in &self.children {
            let run = match child {
                ParagraphChild::Run(run) => run,
                ParagraphChild::Opaque(opaque) => {
                    if opaque.may_contain_visible_text {
                        return Err(TextFlowError::OpaqueSemanticForbidden);
                    }
                    continue;
                }
            };
            for item in &run.items {
                let TextRunItem::Text(span) = item else {
                    if let TextRunItem::Opaque(opaque) = item
                        && opaque.may_contain_visible_text
                    {
                        return Err(TextFlowError::OpaqueSemanticForbidden);
                    }
                    continue;
                };
                for atom in &span.atoms {
                    match atom {
                        TextAtom::Text(text) => push_string(&mut visible, text)?,
                        TextAtom::Tab { .. } => push_character(&mut visible, '\t')?,
                        TextAtom::LineBreak => push_character(&mut visible, '\n')?,
                    }
                }
            }
        }
        let mut normalized = String::new();
        normalized
            .try_reserve(visible.len())
            .map_err(|_| TextFlowError::AllocationFailed)?;
        for character in visible.nfc() {
            push_character(&mut normalized, character)?;
        }
        Ok(normalized)
    }

    #[must_use]
    pub fn run_count(&self) -> usize {
        self.children
            .iter()
            .filter(|child| matches!(child, ParagraphChild::Run(_)))
            .count()
    }

    #[must_use]
    pub fn opaque_count(&self) -> usize {
        let mut count = 0;
        for child in &self.children {
            match child {
                ParagraphChild::Opaque(_) => count += 1,
                ParagraphChild::Run(run) => {
                    count += run
                        .items
                        .iter()
                        .filter(|item| matches!(item, TextRunItem::Opaque(_)))
                        .count();
                }
            }
        }
        count
    }
}

#[derive(Clone, Eq, PartialEq)]
pub enum ParagraphChild {
    Run(TextRun),
    Opaque(OpaqueTextElement),
}

impl Debug for ParagraphChild {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Run(run) => run.fmt(formatter),
            Self::Opaque(opaque) => opaque.fmt(formatter),
        }
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TextRun {
    pub character_property_id_ref: Option<u32>,
    pub character_change_id: Option<u32>,
    pub items: Vec<TextRunItem>,
}

impl Debug for TextRun {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TextRun")
            .field("character_property_id_ref", &self.character_property_id_ref)
            .field("character_change_id", &self.character_change_id)
            .field("items", &self.items)
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub enum TextRunItem {
    Text(TextSpan),
    FieldBegin(FieldBegin),
    FieldEnd(FieldEnd),
    Opaque(OpaqueTextElement),
}

impl Debug for TextRunItem {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Text(span) => span.fmt(formatter),
            Self::FieldBegin(begin) => begin.fmt(formatter),
            Self::FieldEnd(end) => end.fmt(formatter),
            Self::Opaque(opaque) => opaque.fmt(formatter),
        }
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TextSpan {
    pub character_style_id_ref: Option<u32>,
    pub atoms: Vec<TextAtom>,
}

impl Debug for TextSpan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TextSpan")
            .field("character_style_id_ref", &self.character_style_id_ref)
            .field("atoms", &self.atoms)
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub enum TextAtom {
    Text(String),
    Tab {
        alignment: TabAlignment,
        width: Option<u32>,
        leader: Option<String>,
    },
    LineBreak,
}

impl Debug for TextAtom {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Text(text) => formatter
                .debug_struct("Text")
                .field("utf8_bytes", &text.len())
                .finish(),
            Self::Tab {
                alignment,
                width,
                leader,
            } => formatter
                .debug_struct("Tab")
                .field("alignment", alignment)
                .field("width", width)
                .field("leader_present", &leader.is_some())
                .finish(),
            Self::LineBreak => formatter.write_str("LineBreak"),
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum TabAlignment {
    Left,
    Right,
    Center,
    Decimal,
}

impl TabAlignment {
    const fn as_xml(self) -> &'static str {
        match self {
            Self::Left => "LEFT",
            Self::Right => "RIGHT",
            Self::Center => "CENTER",
            Self::Decimal => "DECIMAL",
        }
    }

    fn parse(value: &str) -> Result<Self, TextFlowError> {
        match value {
            "LEFT" => Ok(Self::Left),
            "RIGHT" => Ok(Self::Right),
            "CENTER" => Ok(Self::Center),
            "DECIMAL" => Ok(Self::Decimal),
            _ => Err(TextFlowError::InvalidTab),
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum FieldType {
    ClickHere,
    Hyperlink,
    Bookmark,
    Formula,
    Summery,
    UserInfo,
    Date,
    DocumentDate,
    Path,
    CrossReference,
    MailMerge,
    Memo,
    ProofreadingMarks,
    PrivateInfo,
    MetaTag,
}

impl FieldType {
    const fn as_xml(self) -> &'static str {
        match self {
            Self::ClickHere => "CLICK_HERE",
            Self::Hyperlink => "HYPERLINK",
            Self::Bookmark => "BOOKMARK",
            Self::Formula => "FORMULA",
            Self::Summery => "SUMMERY",
            Self::UserInfo => "USER_INFO",
            Self::Date => "DATE",
            Self::DocumentDate => "DOC_DATE",
            Self::Path => "PATH",
            Self::CrossReference => "CROSSREF",
            Self::MailMerge => "MAILMERGE",
            Self::Memo => "MEMO",
            Self::ProofreadingMarks => "PROOFREADING_MARKS",
            Self::PrivateInfo => "PRIVATE_INFO",
            Self::MetaTag => "METATAG",
        }
    }

    fn parse(value: &str) -> Result<Self, TextFlowError> {
        match value {
            "CLICK_HERE" => Ok(Self::ClickHere),
            "HYPERLINK" => Ok(Self::Hyperlink),
            "BOOKMARK" => Ok(Self::Bookmark),
            "FORMULA" => Ok(Self::Formula),
            "SUMMERY" => Ok(Self::Summery),
            "USER_INFO" => Ok(Self::UserInfo),
            "DATE" => Ok(Self::Date),
            "DOC_DATE" => Ok(Self::DocumentDate),
            "PATH" => Ok(Self::Path),
            "CROSSREF" => Ok(Self::CrossReference),
            "MAILMERGE" => Ok(Self::MailMerge),
            "MEMO" => Ok(Self::Memo),
            "PROOFREADING_MARKS" => Ok(Self::ProofreadingMarks),
            "PRIVATE_INFO" => Ok(Self::PrivateInfo),
            "METATAG" => Ok(Self::MetaTag),
            _ => Err(TextFlowError::InvalidField),
        }
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct FieldBegin {
    pub id: u32,
    pub field_type: FieldType,
    pub name: Option<String>,
    pub editable: bool,
    pub dirty: bool,
    pub z_order: Option<i32>,
    pub field_id: Option<u32>,
}

impl Debug for FieldBegin {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("FieldBegin")
            .field("id", &self.id)
            .field("field_type", &self.field_type)
            .field("name_present", &self.name.is_some())
            .field("editable", &self.editable)
            .field("dirty", &self.dirty)
            .field("z_order", &self.z_order)
            .field("field_id", &self.field_id)
            .finish()
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct FieldEnd {
    pub begin_id_ref: u32,
    pub field_id: Option<u32>,
}

#[derive(Clone, Eq, PartialEq)]
pub struct OpaqueTextElement {
    namespace: Option<String>,
    local_name: String,
    sha256: [u8; 32],
    source_bytes: usize,
    may_contain_visible_text: bool,
}

impl OpaqueTextElement {
    #[must_use]
    pub fn namespace(&self) -> Option<&str> {
        self.namespace.as_deref()
    }

    #[must_use]
    pub fn local_name(&self) -> &str {
        &self.local_name
    }

    #[must_use]
    pub const fn sha256(&self) -> [u8; 32] {
        self.sha256
    }

    #[must_use]
    pub const fn source_bytes(&self) -> usize {
        self.source_bytes
    }

    #[must_use]
    pub const fn may_contain_visible_text(&self) -> bool {
        self.may_contain_visible_text
    }
}

impl Debug for OpaqueTextElement {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("OpaqueTextElement")
            .field("namespace_present", &self.namespace.is_some())
            .field("sha256", &self.sha256)
            .field("source_bytes", &self.source_bytes)
            .field("may_contain_visible_text", &self.may_contain_visible_text)
            .finish_non_exhaustive()
    }
}

#[derive(Debug, Eq, Error, PartialEq)]
pub enum TextFlowError {
    #[error("text-flow limits are invalid")]
    InvalidLimit,
    #[error("text-flow input exceeds its finite limit")]
    InputLimit,
    #[error("text-flow XML failed preserving admission")]
    Preserving(#[from] PreservingXmlError),
    #[error("text-flow root is not the current Hangul 2020 paragraph profile")]
    WrongRoot,
    #[error("text-flow element or attribute shape is unsupported")]
    UnsupportedShape,
    #[error("text-flow numeric attribute is invalid")]
    InvalidNumber,
    #[error("text-flow boolean attribute is invalid")]
    InvalidBoolean,
    #[error("text-flow run count exceeds its finite limit")]
    RunLimit,
    #[error("text-flow item count exceeds its finite limit")]
    ItemLimit,
    #[error("text-flow text exceeds its finite limit")]
    TextLimit,
    #[error("text-flow text is invalid")]
    InvalidText,
    #[error("text-flow tab is invalid")]
    InvalidTab,
    #[error("text-flow field boundary is invalid")]
    InvalidField,
    #[error("text-flow field identifier is duplicated")]
    DuplicateField,
    #[error("text-flow field end does not match the active begin")]
    FieldMismatch,
    #[error("text-flow field depth exceeds its finite limit")]
    FieldDepth,
    #[error("text-flow has an unclosed field")]
    UnclosedField,
    #[error("opaque text-flow content cannot be normalized")]
    OpaqueLoweringForbidden,
    #[error("opaque text-flow content prevents complete semantic text")]
    OpaqueSemanticForbidden,
    #[error("text-flow output exceeds its finite limit")]
    OutputLimit,
    #[error("text-flow allocation failed")]
    AllocationFailed,
}

impl TextFlowError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "text_flow_invalid_limit",
            Self::InputLimit => "text_flow_input_limit",
            Self::Preserving(_) => "text_flow_preserving_xml",
            Self::WrongRoot => "text_flow_wrong_root",
            Self::UnsupportedShape => "text_flow_unsupported_shape",
            Self::InvalidNumber => "text_flow_invalid_number",
            Self::InvalidBoolean => "text_flow_invalid_boolean",
            Self::RunLimit => "text_flow_run_limit",
            Self::ItemLimit => "text_flow_item_limit",
            Self::TextLimit => "text_flow_text_limit",
            Self::InvalidText => "text_flow_invalid_text",
            Self::InvalidTab => "text_flow_invalid_tab",
            Self::InvalidField => "text_flow_invalid_field",
            Self::DuplicateField => "text_flow_duplicate_field",
            Self::FieldMismatch => "text_flow_field_mismatch",
            Self::FieldDepth => "text_flow_field_depth",
            Self::UnclosedField => "text_flow_unclosed_field",
            Self::OpaqueLoweringForbidden => "text_flow_opaque_lowering_forbidden",
            Self::OpaqueSemanticForbidden => "text_flow_opaque_semantic_forbidden",
            Self::OutputLimit => "text_flow_output_limit",
            Self::AllocationFailed => "text_flow_allocation_failed",
        }
    }
}

#[derive(Debug)]
pub struct TextFlowReader;

impl TextFlowReader {
    /// Lifts one standalone current-2020 `hp:p` element after P03 preserving admission.
    ///
    /// # Errors
    ///
    /// Returns a stable error for malformed XML, a non-profile root, invalid supported content,
    /// unmatched fields, or a finite-limit violation. Unknown non-text elements are represented as
    /// opaque digests and never silently discarded.
    pub fn read(bytes: &[u8], limits: TextFlowLimits) -> Result<TextFlow, TextFlowError> {
        if bytes.is_empty() || bytes.len() > limits.config().input_bytes {
            return Err(TextFlowError::InputLimit);
        }
        let document = PreservingXmlDocument::parse(bytes)?;
        if document.elements().len() > limits.config().items {
            return Err(TextFlowError::ItemLimit);
        }
        let root_index = document.root_element();
        validate_document_envelope(&document)?;
        let root = element(&document, root_index)?;
        require_name(root, "p")?;
        validate_attributes(
            root,
            &[
                "id",
                "paraPrIDRef",
                "styleIDRef",
                "pageBreak",
                "columnBreak",
                "merged",
                "paraTcId",
            ],
        )?;
        let paragraph = TextParagraphProperties {
            id: required_u32(root, "id")?,
            paragraph_property_id_ref: optional_u32(root, "paraPrIDRef")?,
            style_id_ref: optional_u32(root, "styleIDRef")?,
            page_break: optional_bool(root, "pageBreak")?.unwrap_or(false),
            column_break: optional_bool(root, "columnBreak")?.unwrap_or(false),
            merged: optional_bool(root, "merged")?.unwrap_or(false),
            paragraph_change_id: optional_u32(root, "paraTcId")?,
        };
        require_only_whitespace_content(&document, root_index)?;

        let mut state = ReadState::new(limits);
        let mut children = Vec::new();
        for child_index in child_indexes(&document, root_index)? {
            state.count_item()?;
            let child = element(&document, child_index)?;
            reserve_one(&mut children)?;
            if has_name(child, "run") {
                state.count_run()?;
                children.push(ParagraphChild::Run(read_run(
                    &document,
                    child_index,
                    &mut state,
                )?));
            } else {
                children.push(ParagraphChild::Opaque(opaque(
                    &document,
                    child_index,
                    is_potentially_visible(&document, child_index)?,
                )?));
            }
        }
        if state.runs == 0 {
            return Err(TextFlowError::UnsupportedShape);
        }
        if !state.fields.is_empty() {
            return Err(TextFlowError::UnclosedField);
        }
        Ok(TextFlow {
            paragraph,
            children,
        })
    }
}

#[derive(Debug)]
pub struct TextFlowWriter;

impl TextFlowWriter {
    /// Lowers a fully typed, non-opaque flow to deterministic current-2020 paragraph XML and
    /// reparses it before returning bytes.
    ///
    /// # Errors
    ///
    /// Rejects opaque content, invalid fields/text/attributes, finite-limit violations, and any
    /// output that does not lift back into the exact same typed flow.
    pub fn lower(flow: &TextFlow, limits: TextFlowLimits) -> Result<Vec<u8>, TextFlowError> {
        validate_flow(flow, limits)?;
        let mut output = BoundedXml::new(limits.config().input_bytes)?;
        output.push(r#"<?xml version="1.0" encoding="UTF-8"?>"#)?;
        output.push(r#"<hp:p xmlns:hp=""#)?;
        output.push(HANCOM_2020_PARAGRAPH_NAMESPACE)?;
        output.push(r#"" id=""#)?;
        output.push_u32(flow.paragraph.id)?;
        output.push("\"")?;
        output.optional_u32(" paraPrIDRef=\"", flow.paragraph.paragraph_property_id_ref)?;
        output.optional_u32(" styleIDRef=\"", flow.paragraph.style_id_ref)?;
        output.bool_attribute(" pageBreak=\"", flow.paragraph.page_break)?;
        output.bool_attribute(" columnBreak=\"", flow.paragraph.column_break)?;
        output.bool_attribute(" merged=\"", flow.paragraph.merged)?;
        output.optional_u32(" paraTcId=\"", flow.paragraph.paragraph_change_id)?;
        output.push(">")?;

        for child in &flow.children {
            let ParagraphChild::Run(run) = child else {
                return Err(TextFlowError::OpaqueLoweringForbidden);
            };
            output.push("<hp:run")?;
            output.optional_u32(" charPrIDRef=\"", run.character_property_id_ref)?;
            output.optional_u32(" charTcId=\"", run.character_change_id)?;
            output.push(">")?;
            for item in &run.items {
                match item {
                    TextRunItem::Text(span) => lower_text_span(&mut output, span)?,
                    TextRunItem::FieldBegin(begin) => lower_field_begin(&mut output, begin)?,
                    TextRunItem::FieldEnd(end) => lower_field_end(&mut output, end)?,
                    TextRunItem::Opaque(_) => {
                        return Err(TextFlowError::OpaqueLoweringForbidden);
                    }
                }
            }
            output.push("</hp:run>")?;
        }
        output.push("</hp:p>")?;
        let bytes = output.finish();
        let reparsed = TextFlowReader::read(&bytes, limits)?;
        if reparsed != *flow {
            return Err(TextFlowError::UnsupportedShape);
        }
        Ok(bytes)
    }
}

struct ReadState {
    limits: TextFlowLimits,
    runs: usize,
    items: usize,
    text_bytes: usize,
    fields: Vec<u32>,
    seen_fields: BTreeSet<u32>,
}

impl ReadState {
    fn new(limits: TextFlowLimits) -> Self {
        Self {
            limits,
            runs: 0,
            items: 0,
            text_bytes: 0,
            fields: Vec::new(),
            seen_fields: BTreeSet::new(),
        }
    }

    fn count_run(&mut self) -> Result<(), TextFlowError> {
        self.runs = self.runs.checked_add(1).ok_or(TextFlowError::RunLimit)?;
        if self.runs > self.limits.config().runs {
            return Err(TextFlowError::RunLimit);
        }
        Ok(())
    }

    fn count_item(&mut self) -> Result<(), TextFlowError> {
        self.items = self.items.checked_add(1).ok_or(TextFlowError::ItemLimit)?;
        if self.items > self.limits.config().items {
            return Err(TextFlowError::ItemLimit);
        }
        Ok(())
    }

    fn count_text(&mut self, bytes: usize) -> Result<(), TextFlowError> {
        self.text_bytes = self
            .text_bytes
            .checked_add(bytes)
            .ok_or(TextFlowError::TextLimit)?;
        if self.text_bytes > self.limits.config().text_bytes {
            return Err(TextFlowError::TextLimit);
        }
        Ok(())
    }

    fn begin_field(&mut self, id: u32) -> Result<(), TextFlowError> {
        if !self.seen_fields.insert(id) {
            return Err(TextFlowError::DuplicateField);
        }
        self.fields
            .try_reserve(1)
            .map_err(|_| TextFlowError::AllocationFailed)?;
        self.fields.push(id);
        if self.fields.len() > self.limits.config().field_depth {
            return Err(TextFlowError::FieldDepth);
        }
        Ok(())
    }

    fn end_field(&mut self, begin_id_ref: u32) -> Result<(), TextFlowError> {
        if self.fields.pop() != Some(begin_id_ref) {
            return Err(TextFlowError::FieldMismatch);
        }
        Ok(())
    }
}

fn read_run(
    document: &PreservingXmlDocument,
    index: usize,
    state: &mut ReadState,
) -> Result<TextRun, TextFlowError> {
    let run = element(document, index)?;
    if validate_attributes(run, &["charPrIDRef", "charTcId"]).is_err() {
        return Err(TextFlowError::UnsupportedShape);
    }
    require_only_whitespace_content(document, index)?;
    let mut items = Vec::new();
    for child_index in child_indexes(document, index)? {
        state.count_item()?;
        let child = element(document, child_index)?;
        let item = if has_name(child, "t") {
            read_text_span(document, child_index, state)?
        } else if has_name(child, "ctrl") {
            read_control(document, child_index, state)?
        } else {
            TextRunItem::Opaque(opaque(
                document,
                child_index,
                is_potentially_visible(document, child_index)?,
            )?)
        };
        reserve_one(&mut items)?;
        items.push(item);
    }
    Ok(TextRun {
        character_property_id_ref: optional_u32(run, "charPrIDRef")?,
        character_change_id: optional_u32(run, "charTcId")?,
        items,
    })
}

fn read_text_span(
    document: &PreservingXmlDocument,
    index: usize,
    state: &mut ReadState,
) -> Result<TextRunItem, TextFlowError> {
    let span = element(document, index)?;
    if validate_attributes(span, &["charStyleIDRef"]).is_err() {
        return Ok(TextRunItem::Opaque(opaque(document, index, true)?));
    }
    let child_indexes = child_indexes(document, index)?;
    if child_indexes.iter().any(|child_index| {
        element(document, *child_index).map_or(true, |child| {
            !has_name(child, "tab") && !has_name(child, "lineBreak")
        })
    }) {
        return Ok(TextRunItem::Opaque(opaque(document, index, true)?));
    }

    let mut atoms = Vec::new();
    let end_token = span.end_token().ok_or(TextFlowError::UnsupportedShape)?;
    for token_index in (span.start_token() + 1)..end_token {
        let token = document
            .tokens()
            .get(token_index)
            .ok_or(TextFlowError::UnsupportedShape)?;
        if token.element_index() == Some(index) {
            match token.kind() {
                XmlTokenKind::Text | XmlTokenKind::Whitespace | XmlTokenKind::Reference => {
                    let raw = document.source_text(token.span())?;
                    let normalized = normalize_xml_newlines(raw);
                    let decoded = unescape(&normalized)
                        .map_err(|_| TextFlowError::InvalidText)?
                        .into_owned();
                    if !decoded.is_empty() {
                        validate_text(&decoded)?;
                        state.count_text(decoded.len())?;
                        push_text_atom(&mut atoms, decoded)?;
                    }
                }
                XmlTokenKind::Comment => {
                    return Ok(TextRunItem::Opaque(opaque(document, index, true)?));
                }
                _ => {}
            }
        }
        if matches!(
            token.kind(),
            XmlTokenKind::StartElement | XmlTokenKind::EmptyElement
        ) {
            let child_index = token
                .element_index()
                .ok_or(TextFlowError::UnsupportedShape)?;
            let child = element(document, child_index)?;
            if child.parent() == Some(index) {
                state.count_item()?;
                if has_name(child, "tab") {
                    reserve_one(&mut atoms)?;
                    atoms.push(read_tab(document, child_index)?);
                } else if has_name(child, "lineBreak") {
                    read_empty_element(document, child_index, &[])?;
                    reserve_one(&mut atoms)?;
                    atoms.push(TextAtom::LineBreak);
                }
            }
        }
    }
    Ok(TextRunItem::Text(TextSpan {
        character_style_id_ref: optional_u32(span, "charStyleIDRef")?,
        atoms,
    }))
}

fn read_tab(document: &PreservingXmlDocument, index: usize) -> Result<TextAtom, TextFlowError> {
    let tab = element(document, index)?;
    read_empty_element(document, index, &["width", "leader", "type"])?;
    let alignment = TabAlignment::parse(required_attribute(tab, "type")?)?;
    let width = optional_u32(tab, "width")?;
    let leader = optional_attribute(tab, "leader").map(ToOwned::to_owned);
    if leader
        .as_deref()
        .is_some_and(|value| !valid_token(value, 64))
    {
        return Err(TextFlowError::InvalidTab);
    }
    Ok(TextAtom::Tab {
        alignment,
        width,
        leader,
    })
}

fn read_control(
    document: &PreservingXmlDocument,
    index: usize,
    state: &mut ReadState,
) -> Result<TextRunItem, TextFlowError> {
    let control = element(document, index)?;
    if validate_attributes(control, &[]).is_err() {
        return Ok(TextRunItem::Opaque(opaque(document, index, true)?));
    }
    require_only_whitespace_content(document, index)?;
    let children = child_indexes(document, index)?;
    if children.len() != 1 {
        if children.iter().any(|child_index| {
            element(document, *child_index)
                .is_ok_and(|child| has_name(child, "fieldBegin") || has_name(child, "fieldEnd"))
        }) {
            return Err(TextFlowError::InvalidField);
        }
        return Ok(TextRunItem::Opaque(opaque(document, index, true)?));
    }
    let child_index = children[0];
    let child = element(document, child_index)?;
    if has_name(child, "fieldBegin") {
        read_empty_element(
            document,
            child_index,
            &[
                "id", "type", "name", "editable", "dirty", "zorder", "fieldid",
            ],
        )?;
        let id = required_u32(child, "id")?;
        let name = optional_attribute(child, "name").map(ToOwned::to_owned);
        if name
            .as_deref()
            .is_some_and(|value| value.len() > 256 || !valid_attribute_text(value))
        {
            return Err(TextFlowError::InvalidField);
        }
        let begin = FieldBegin {
            id,
            field_type: FieldType::parse(required_attribute(child, "type")?)?,
            name,
            editable: optional_bool(child, "editable")?.unwrap_or(true),
            dirty: optional_bool(child, "dirty")?.unwrap_or(false),
            z_order: optional_i32(child, "zorder")?,
            field_id: optional_u32(child, "fieldid")?,
        };
        state.begin_field(id)?;
        Ok(TextRunItem::FieldBegin(begin))
    } else if has_name(child, "fieldEnd") {
        read_empty_element(document, child_index, &["beginIDRef", "fieldid"])?;
        let end = FieldEnd {
            begin_id_ref: required_u32(child, "beginIDRef")?,
            field_id: optional_u32(child, "fieldid")?,
        };
        state.end_field(end.begin_id_ref)?;
        Ok(TextRunItem::FieldEnd(end))
    } else {
        Ok(TextRunItem::Opaque(opaque(
            document,
            index,
            is_potentially_visible(document, child_index)?,
        )?))
    }
}

fn read_empty_element(
    document: &PreservingXmlDocument,
    index: usize,
    allowed_attributes: &[&str],
) -> Result<(), TextFlowError> {
    let element = element(document, index)?;
    validate_attributes(element, allowed_attributes)?;
    if element.first_child().is_some() {
        return Err(TextFlowError::UnsupportedShape);
    }
    require_only_whitespace_content(document, index)
}

fn validate_flow(flow: &TextFlow, limits: TextFlowLimits) -> Result<(), TextFlowError> {
    let mut state = ReadState::new(limits);
    if flow.children.is_empty() {
        return Err(TextFlowError::UnsupportedShape);
    }
    for child in &flow.children {
        state.count_item()?;
        let ParagraphChild::Run(run) = child else {
            return Err(TextFlowError::OpaqueLoweringForbidden);
        };
        state.count_run()?;
        for item in &run.items {
            state.count_item()?;
            match item {
                TextRunItem::Text(span) => {
                    for atom in &span.atoms {
                        state.count_item()?;
                        match atom {
                            TextAtom::Text(text) => {
                                if text.is_empty() {
                                    return Err(TextFlowError::InvalidText);
                                }
                                validate_text(text)?;
                                state.count_text(text.len())?;
                            }
                            TextAtom::Tab { leader, .. } => {
                                if leader
                                    .as_deref()
                                    .is_some_and(|value| !valid_token(value, 64))
                                {
                                    return Err(TextFlowError::InvalidTab);
                                }
                            }
                            TextAtom::LineBreak => {}
                        }
                    }
                }
                TextRunItem::FieldBegin(begin) => {
                    if begin
                        .name
                        .as_deref()
                        .is_some_and(|value| value.len() > 256 || !valid_attribute_text(value))
                    {
                        return Err(TextFlowError::InvalidField);
                    }
                    state.begin_field(begin.id)?;
                }
                TextRunItem::FieldEnd(end) => state.end_field(end.begin_id_ref)?,
                TextRunItem::Opaque(_) => {
                    return Err(TextFlowError::OpaqueLoweringForbidden);
                }
            }
        }
    }
    if !state.fields.is_empty() {
        return Err(TextFlowError::UnclosedField);
    }
    Ok(())
}

fn lower_text_span(output: &mut BoundedXml, span: &TextSpan) -> Result<(), TextFlowError> {
    output.push("<hp:t")?;
    output.optional_u32(" charStyleIDRef=\"", span.character_style_id_ref)?;
    if span.atoms.is_empty() {
        return output.push("/>");
    }
    output.push(">")?;
    for atom in &span.atoms {
        match atom {
            TextAtom::Text(text) => output.escaped(text)?,
            TextAtom::Tab {
                alignment,
                width,
                leader,
            } => {
                output.push("<hp:tab")?;
                output.optional_u32(" width=\"", *width)?;
                if let Some(leader) = leader {
                    output.push(" leader=\"")?;
                    output.escaped(leader)?;
                    output.push("\"")?;
                }
                output.push(" type=\"")?;
                output.push(alignment.as_xml())?;
                output.push("\"/>")?;
            }
            TextAtom::LineBreak => output.push("<hp:lineBreak/>")?,
        }
    }
    output.push("</hp:t>")
}

fn lower_field_begin(output: &mut BoundedXml, begin: &FieldBegin) -> Result<(), TextFlowError> {
    output.push("<hp:ctrl><hp:fieldBegin id=\"")?;
    output.push_u32(begin.id)?;
    output.push("\" type=\"")?;
    output.push(begin.field_type.as_xml())?;
    output.push("\"")?;
    if let Some(name) = &begin.name {
        output.push(" name=\"")?;
        output.escaped(name)?;
        output.push("\"")?;
    }
    output.bool_attribute(" editable=\"", begin.editable)?;
    output.bool_attribute(" dirty=\"", begin.dirty)?;
    output.optional_i32(" zorder=\"", begin.z_order)?;
    output.optional_u32(" fieldid=\"", begin.field_id)?;
    output.push("/></hp:ctrl>")
}

fn lower_field_end(output: &mut BoundedXml, end: &FieldEnd) -> Result<(), TextFlowError> {
    output.push("<hp:ctrl><hp:fieldEnd beginIDRef=\"")?;
    output.push_u32(end.begin_id_ref)?;
    output.push("\"")?;
    output.optional_u32(" fieldid=\"", end.field_id)?;
    output.push("/></hp:ctrl>")
}

struct BoundedXml {
    value: String,
    maximum: usize,
}

impl BoundedXml {
    fn new(maximum: usize) -> Result<Self, TextFlowError> {
        let mut value = String::new();
        value
            .try_reserve(maximum.min(64 * 1024))
            .map_err(|_| TextFlowError::AllocationFailed)?;
        Ok(Self { value, maximum })
    }

    fn push(&mut self, value: impl AsRef<str>) -> Result<(), TextFlowError> {
        let value = value.as_ref();
        let length = self
            .value
            .len()
            .checked_add(value.len())
            .ok_or(TextFlowError::OutputLimit)?;
        if length > self.maximum {
            return Err(TextFlowError::OutputLimit);
        }
        self.value
            .try_reserve(value.len())
            .map_err(|_| TextFlowError::AllocationFailed)?;
        self.value.push_str(value);
        Ok(())
    }

    fn push_u32(&mut self, value: u32) -> Result<(), TextFlowError> {
        self.push(value.to_string())
    }

    fn optional_u32(&mut self, prefix: &str, value: Option<u32>) -> Result<(), TextFlowError> {
        if let Some(value) = value {
            self.push(prefix)?;
            self.push_u32(value)?;
            self.push("\"")?;
        }
        Ok(())
    }

    fn optional_i32(&mut self, prefix: &str, value: Option<i32>) -> Result<(), TextFlowError> {
        if let Some(value) = value {
            self.push(prefix)?;
            self.push(value.to_string())?;
            self.push("\"")?;
        }
        Ok(())
    }

    fn bool_attribute(&mut self, prefix: &str, value: bool) -> Result<(), TextFlowError> {
        self.push(prefix)?;
        self.push(if value { "1\"" } else { "0\"" })
    }

    fn escaped(&mut self, value: &str) -> Result<(), TextFlowError> {
        let mut start = 0;
        for (index, character) in value.char_indices() {
            let replacement = match character {
                '&' => "&amp;",
                '<' => "&lt;",
                '>' => "&gt;",
                '"' => "&quot;",
                '\'' => "&apos;",
                _ => continue,
            };
            self.push(&value[start..index])?;
            self.push(replacement)?;
            start = index + character.len_utf8();
        }
        self.push(&value[start..])
    }

    fn finish(self) -> Vec<u8> {
        self.value.into_bytes()
    }
}

fn element(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<&XmlElementToken, TextFlowError> {
    document
        .elements()
        .get(index)
        .ok_or(TextFlowError::UnsupportedShape)
}

fn has_name(element: &XmlElementToken, local_name: &str) -> bool {
    element.name().namespace() == Some(HANCOM_2020_PARAGRAPH_NAMESPACE)
        && element.name().local_name() == local_name
}

fn require_name(element: &XmlElementToken, local_name: &str) -> Result<(), TextFlowError> {
    if has_name(element, local_name) {
        Ok(())
    } else {
        Err(TextFlowError::WrongRoot)
    }
}

fn child_indexes(
    document: &PreservingXmlDocument,
    parent: usize,
) -> Result<Vec<usize>, TextFlowError> {
    let mut children = Vec::new();
    let mut current = element(document, parent)?.first_child();
    while let Some(index) = current {
        children
            .try_reserve(1)
            .map_err(|_| TextFlowError::AllocationFailed)?;
        children.push(index);
        current = element(document, index)?.next_sibling();
    }
    Ok(children)
}

fn validate_attributes(element: &XmlElementToken, allowed: &[&str]) -> Result<(), TextFlowError> {
    for attribute in element.attributes() {
        if attribute.is_namespace_declaration() {
            continue;
        }
        if attribute.name().namespace().is_some()
            || !allowed.contains(&attribute.name().local_name())
        {
            return Err(TextFlowError::UnsupportedShape);
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
) -> Result<&'a str, TextFlowError> {
    optional_attribute(element, name).ok_or(TextFlowError::UnsupportedShape)
}

fn parse_u32(value: &str) -> Result<u32, TextFlowError> {
    if value.is_empty() || !value.bytes().all(|byte| byte.is_ascii_digit()) {
        return Err(TextFlowError::InvalidNumber);
    }
    value.parse().map_err(|_| TextFlowError::InvalidNumber)
}

fn required_u32(element: &XmlElementToken, name: &str) -> Result<u32, TextFlowError> {
    parse_u32(required_attribute(element, name)?)
}

fn optional_u32(element: &XmlElementToken, name: &str) -> Result<Option<u32>, TextFlowError> {
    optional_attribute(element, name).map(parse_u32).transpose()
}

fn optional_i32(element: &XmlElementToken, name: &str) -> Result<Option<i32>, TextFlowError> {
    optional_attribute(element, name)
        .map(|value| {
            if value.is_empty()
                || !value
                    .strip_prefix('-')
                    .unwrap_or(value)
                    .bytes()
                    .all(|byte| byte.is_ascii_digit())
            {
                return Err(TextFlowError::InvalidNumber);
            }
            value.parse().map_err(|_| TextFlowError::InvalidNumber)
        })
        .transpose()
}

fn optional_bool(element: &XmlElementToken, name: &str) -> Result<Option<bool>, TextFlowError> {
    optional_attribute(element, name)
        .map(|value| match value {
            "1" | "true" => Ok(true),
            "0" | "false" => Ok(false),
            _ => Err(TextFlowError::InvalidBoolean),
        })
        .transpose()
}

fn require_only_whitespace_content(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<(), TextFlowError> {
    let element = element(document, index)?;
    if element.is_empty() {
        return Ok(());
    }
    let end = element.end_token().ok_or(TextFlowError::UnsupportedShape)?;
    for token in &document.tokens()[(element.start_token() + 1)..end] {
        if token.element_index() != Some(index) {
            continue;
        }
        match token.kind() {
            XmlTokenKind::Text | XmlTokenKind::Reference | XmlTokenKind::Comment => {
                return Err(TextFlowError::UnsupportedShape);
            }
            _ => {}
        }
    }
    Ok(())
}

fn validate_document_envelope(document: &PreservingXmlDocument) -> Result<(), TextFlowError> {
    for token in document
        .tokens()
        .iter()
        .filter(|token| token.element_index().is_none())
    {
        if !matches!(
            token.kind(),
            XmlTokenKind::ByteOrderMark | XmlTokenKind::Declaration | XmlTokenKind::Whitespace
        ) {
            return Err(TextFlowError::UnsupportedShape);
        }
    }
    Ok(())
}

fn opaque(
    document: &PreservingXmlDocument,
    index: usize,
    may_contain_visible_text: bool,
) -> Result<OpaqueTextElement, TextFlowError> {
    let element = element(document, index)?;
    let span = element
        .outer_span()
        .ok_or(TextFlowError::UnsupportedShape)?;
    let source = document.source_text(span)?.as_bytes();
    Ok(OpaqueTextElement {
        namespace: element.name().namespace().map(ToOwned::to_owned),
        local_name: element.name().local_name().to_owned(),
        sha256: Sha256::digest(source).into(),
        source_bytes: source.len(),
        may_contain_visible_text,
    })
}

fn is_potentially_visible(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<bool, TextFlowError> {
    let root = element(document, index)?;
    if root.name().namespace() != Some(HANCOM_2020_PARAGRAPH_NAMESPACE)
        || !matches!(
            root.name().local_name(),
            "secPr" | "colPr" | "linesegarray" | "lineseg"
        )
    {
        return Ok(true);
    }
    let end = root.end_token().unwrap_or(root.start_token());
    for token in &document.tokens()[root.start_token()..=end] {
        match token.kind() {
            XmlTokenKind::Reference => return Ok(true),
            XmlTokenKind::Text => {
                if !document.source_text(token.span())?.trim().is_empty() {
                    return Ok(true);
                }
            }
            XmlTokenKind::StartElement | XmlTokenKind::EmptyElement => {
                let child_index = token
                    .element_index()
                    .ok_or(TextFlowError::UnsupportedShape)?;
                if child_index != index && has_name(element(document, child_index)?, "t") {
                    return Ok(true);
                }
            }
            _ => {}
        }
    }
    Ok(false)
}

fn normalize_xml_newlines(value: &str) -> String {
    value.replace("\r\n", "\n").replace('\r', "\n")
}

fn push_text_atom(atoms: &mut Vec<TextAtom>, value: String) -> Result<(), TextFlowError> {
    if let Some(TextAtom::Text(existing)) = atoms.last_mut() {
        existing
            .try_reserve(value.len())
            .map_err(|_| TextFlowError::AllocationFailed)?;
        existing.push_str(&value);
    } else {
        atoms
            .try_reserve(1)
            .map_err(|_| TextFlowError::AllocationFailed)?;
        atoms.push(TextAtom::Text(value));
    }
    Ok(())
}

fn reserve_one<T>(values: &mut Vec<T>) -> Result<(), TextFlowError> {
    values
        .try_reserve(1)
        .map_err(|_| TextFlowError::AllocationFailed)
}

fn push_string(target: &mut String, value: &str) -> Result<(), TextFlowError> {
    target
        .try_reserve(value.len())
        .map_err(|_| TextFlowError::AllocationFailed)?;
    target.push_str(value);
    Ok(())
}

fn push_character(target: &mut String, character: char) -> Result<(), TextFlowError> {
    target
        .try_reserve(character.len_utf8())
        .map_err(|_| TextFlowError::AllocationFailed)?;
    target.push(character);
    Ok(())
}

fn validate_text(value: &str) -> Result<(), TextFlowError> {
    if value.chars().any(|character| {
        character.is_control() || matches!(character as u32 & 0xffff, 0xfffe | 0xffff)
    }) {
        return Err(TextFlowError::InvalidText);
    }
    Ok(())
}

fn valid_attribute_text(value: &str) -> bool {
    !value.chars().any(|character| {
        character.is_control() || matches!(character as u32 & 0xffff, 0xfffe | 0xffff)
    })
}

fn valid_token(value: &str, maximum: usize) -> bool {
    !value.is_empty()
        && value.len() <= maximum
        && value
            .bytes()
            .all(|byte| byte.is_ascii_uppercase() || byte.is_ascii_digit() || byte == b'_')
}
