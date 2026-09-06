use std::fmt;
use std::io::{Cursor, Read as _, Write as _};

use sha2::{Digest as _, Sha256};
use thiserror::Error;
use unicode_normalization::UnicodeNormalization;
use zip::write::SimpleFileOptions;
use zip::{CompressionMethod, DateTime, System, ZipArchive, ZipWriter};

use crate::{
    BinaryProperty, BoundedZipReader, CharacterStyleCatalog, CharacterStyleCatalogReader,
    CharacterStyleCatalogWriter, CharacterStyleError, CharacterStyleLimits, Color,
    ColumnDefinition, ColumnLayout, ColumnLineType, ColumnLineWidth, ColumnMetrics,
    ColumnSeparator, ColumnSizing, ColumnType, GraphError, Hancom2020Vs0Builder,
    Hancom2020Vs0Error, HorizontalAlignment, IdIndex, IdIndexError, IdIndexLimits, IdRuleProfile,
    PackageGraph, PackageGraphLimits, PackageLimits, PageDimensions, PageGutterType, PageMargins,
    PageOrientation, PageSetup, PageSetupError, PageSetupLimits, PageSetupLowerer,
    PageSetupMetrics, PageSetupReader, ParagraphChild, ParagraphStyleCatalog,
    ParagraphStyleCatalogReader, ParagraphStyleCatalogWriter, ParagraphStyleError,
    ParagraphStyleLimits, SectionColumnError, SectionColumnLimits, SectionColumnLowerer,
    SectionColumnReader, TextAtom, TextFlow, TextFlowError, TextFlowLimits, TextFlowReader,
    TextFlowWriter, TextParagraphProperties, TextRun, TextRunItem, TextSpan,
};

pub const HANCOM_2020_VS1_LAYOUT_PROFILE_ID: &str = "hwpx-agent.hancom-2020-vs1-layout/v1";
pub const HANCOM_2020_DENSE_COLUMN_FLOW_PROFILE_ID: &str =
    "hwpx-agent.hancom-2020-dense-column-flow/v1";
pub const HANCOM_2020_VS1_LAYOUT_MAX_PARAGRAPHS: usize = 32;
pub const HANCOM_2020_VS1_LAYOUT_MAX_TEXT_BYTES: usize = 32 * 1024;

const MIN_BODY_PARAGRAPHS: usize = 2;
const MAX_ARTIFACT_BYTES: usize = 2 * 1024 * 1024;
const TEMPLATE_TITLE: &str = "__HWPX_AGENT_VS1_LAYOUT_TITLE__";
const TITLE_CHARACTER_STYLE_ID: u32 = 1;
const BODY_CHARACTER_STYLE_ID: u32 = 0;
const TITLE_PARAGRAPH_STYLE_ID: u32 = 1;
const BODY_PARAGRAPH_STYLE_ID: u32 = 0;
const NORMALIZED_DEFLATE_LEVEL: i64 = 6;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Hancom2020ColumnFlowPolicy {
    ExplicitMidpointBreak,
    AutomaticBalanced,
}

#[derive(Clone, Eq, PartialEq)]
pub struct Hancom2020Vs1LayoutDocument {
    title: String,
    body_paragraphs: Vec<String>,
    column_flow_policy: Hancom2020ColumnFlowPolicy,
}

impl Hancom2020Vs1LayoutDocument {
    /// Creates the bounded, NFC-normalized text input for the P05 VS-1 layout slice.
    ///
    /// # Errors
    ///
    /// Rejects empty, multiline, control-bearing, oversized, or insufficient body content.
    pub fn new(
        title: &str,
        body_paragraphs: Vec<String>,
    ) -> Result<Self, Hancom2020Vs1LayoutError> {
        Self::new_with_policy(
            title,
            body_paragraphs,
            Hancom2020ColumnFlowPolicy::ExplicitMidpointBreak,
        )
    }

    /// Creates a bounded layout input whose balanced columns are filled without an explicit
    /// column-break paragraph.
    ///
    /// # Errors
    ///
    /// Rejects the same invalid text and size shapes as [`Self::new`].
    pub fn new_automatic_balanced(
        title: &str,
        body_paragraphs: Vec<String>,
    ) -> Result<Self, Hancom2020Vs1LayoutError> {
        Self::new_with_policy(
            title,
            body_paragraphs,
            Hancom2020ColumnFlowPolicy::AutomaticBalanced,
        )
    }

    fn new_with_policy(
        title: &str,
        body_paragraphs: Vec<String>,
        column_flow_policy: Hancom2020ColumnFlowPolicy,
    ) -> Result<Self, Hancom2020Vs1LayoutError> {
        validate_line(title)?;
        if !(MIN_BODY_PARAGRAPHS..=HANCOM_2020_VS1_LAYOUT_MAX_PARAGRAPHS)
            .contains(&body_paragraphs.len())
        {
            return Err(Hancom2020Vs1LayoutError::InvalidDocument);
        }
        for paragraph in &body_paragraphs {
            validate_line(paragraph)?;
        }
        let total_bytes = body_paragraphs
            .iter()
            .try_fold(title.len(), |total, paragraph| {
                total.checked_add(paragraph.len())
            });
        let total_bytes = total_bytes.ok_or(Hancom2020Vs1LayoutError::InvalidDocument)?;
        if total_bytes > HANCOM_2020_VS1_LAYOUT_MAX_TEXT_BYTES {
            return Err(Hancom2020Vs1LayoutError::InvalidDocument);
        }
        Ok(Self {
            title: title.nfc().collect(),
            body_paragraphs: body_paragraphs
                .into_iter()
                .map(|paragraph| paragraph.nfc().collect())
                .collect(),
            column_flow_policy,
        })
    }

    #[must_use]
    pub fn title(&self) -> &str {
        &self.title
    }

    #[must_use]
    pub fn body_paragraphs(&self) -> &[String] {
        &self.body_paragraphs
    }

    #[must_use]
    pub fn paragraph_count(&self) -> usize {
        self.body_paragraphs.len() + 1
    }

    #[must_use]
    pub const fn column_flow_policy(&self) -> Hancom2020ColumnFlowPolicy {
        self.column_flow_policy
    }

    const fn expected_column_break_count(&self) -> usize {
        match self.column_flow_policy {
            Hancom2020ColumnFlowPolicy::ExplicitMidpointBreak => 1,
            Hancom2020ColumnFlowPolicy::AutomaticBalanced => 0,
        }
    }

    const fn profile_id(&self) -> &'static str {
        profile_id(self.column_flow_policy)
    }

    fn canonical_text(&self) -> String {
        let mut result = self.title.clone();
        for paragraph in &self.body_paragraphs {
            result.push('\n');
            result.push_str(paragraph);
        }
        result
    }
}

impl fmt::Debug for Hancom2020Vs1LayoutDocument {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("Hancom2020Vs1LayoutDocument")
            .field("title_bytes", &self.title.len())
            .field("body_paragraph_count", &self.body_paragraphs.len())
            .field("column_flow_policy", &self.column_flow_policy)
            .field(
                "body_text_bytes",
                &self.body_paragraphs.iter().map(String::len).sum::<usize>(),
            )
            .finish()
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Hancom2020Vs1LayoutInspection {
    pub profile_id: &'static str,
    pub column_flow_policy: Hancom2020ColumnFlowPolicy,
    pub part_count: usize,
    pub paragraph_count: usize,
    pub column_break_count: usize,
    pub character_style_count: usize,
    pub paragraph_style_count: usize,
    pub page_metrics: PageSetupMetrics,
    pub column_metrics: ColumnMetrics,
    pub visible_text_sha256: [u8; 32],
}

/// One deterministic, graph-validated P05 VS-1 layout artifact. Its public inspection proves the
/// custom page, two-column profile, typed title/body styles and complete visible text identity.
pub struct Hancom2020Vs1LayoutArtifact {
    bytes: Box<[u8]>,
    sha256: [u8; 32],
    inspection: Hancom2020Vs1LayoutInspection,
}

impl Hancom2020Vs1LayoutArtifact {
    #[must_use]
    pub const fn size_bytes(&self) -> usize {
        self.bytes.len()
    }

    #[must_use]
    pub const fn sha256(&self) -> [u8; 32] {
        self.sha256
    }

    #[must_use]
    pub const fn inspection(&self) -> &Hancom2020Vs1LayoutInspection {
        &self.inspection
    }

    /// Rehashes and semantically reopens the full package through the P03/P05 trust chain.
    ///
    /// # Errors
    ///
    /// Returns a stable mismatch when bytes or any typed layout evidence drifted.
    pub fn verify(&self) -> Result<(), Hancom2020Vs1LayoutError> {
        if self.bytes.len() > MAX_ARTIFACT_BYTES
            || <[u8; 32]>::from(Sha256::digest(&self.bytes)) != self.sha256
        {
            return Err(Hancom2020Vs1LayoutError::ArtifactMismatch);
        }
        if inspect_package(&self.bytes)? != self.inspection {
            return Err(Hancom2020Vs1LayoutError::ArtifactMismatch);
        }
        Ok(())
    }

    /// Gives a callback temporary access only after the complete artifact is reverified.
    ///
    /// # Errors
    ///
    /// Does not invoke the callback when verification fails.
    pub fn with_verified_bytes<T>(
        &self,
        consume: impl FnOnce(&[u8]) -> T,
    ) -> Result<T, Hancom2020Vs1LayoutError> {
        self.verify()?;
        Ok(consume(&self.bytes))
    }
}

impl fmt::Debug for Hancom2020Vs1LayoutArtifact {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("Hancom2020Vs1LayoutArtifact")
            .field("size_bytes", &self.bytes.len())
            .field("sha256", &self.sha256)
            .field("inspection", &self.inspection)
            .finish()
    }
}

#[derive(Debug)]
pub struct Hancom2020Vs1LayoutBuilder;

impl Hancom2020Vs1LayoutBuilder {
    /// Builds the fixed P05 layout vertical slice from bounded typed text.
    ///
    /// # Errors
    ///
    /// Fails closed on invalid input, component lowering drift, ZIP failure, graph failure, or
    /// semantic readback mismatch.
    pub fn build(
        document: &Hancom2020Vs1LayoutDocument,
    ) -> Result<Hancom2020Vs1LayoutArtifact, Hancom2020Vs1LayoutError> {
        validate_document(document)?;
        let source = Hancom2020Vs0Builder::build(TEMPLATE_TITLE)?;
        let source_bytes = source.with_verified_bytes(ToOwned::to_owned)?;
        let bytes = compose_package(&source_bytes, document)?;
        if bytes.is_empty() || bytes.len() > MAX_ARTIFACT_BYTES {
            return Err(Hancom2020Vs1LayoutError::OutputLimitExceeded);
        }
        let inspection = inspect_package(&bytes)?;
        let expected_text_sha256: [u8; 32] =
            Sha256::digest(document.canonical_text().as_bytes()).into();
        if inspection.paragraph_count != document.paragraph_count()
            || inspection.column_break_count != document.expected_column_break_count()
            || inspection.profile_id != document.profile_id()
            || inspection.column_flow_policy != document.column_flow_policy
            || inspection.visible_text_sha256 != expected_text_sha256
        {
            return Err(Hancom2020Vs1LayoutError::ReadbackMismatch);
        }
        Ok(Hancom2020Vs1LayoutArtifact {
            sha256: Sha256::digest(&bytes).into(),
            bytes: bytes.into_boxed_slice(),
            inspection,
        })
    }

    /// Inspects an existing bounded package against the P05 VS-1 layout profile.
    ///
    /// # Errors
    ///
    /// Rejects incomplete, malformed, unbounded, graph-invalid, or semantically drifting output.
    pub fn inspect(
        bytes: &[u8],
    ) -> Result<Hancom2020Vs1LayoutInspection, Hancom2020Vs1LayoutError> {
        inspect_package(bytes)
    }
}

#[derive(Debug, Error)]
pub enum Hancom2020Vs1LayoutError {
    #[error("VS-1 layout document is invalid")]
    InvalidDocument,
    #[error("VS-1 layout source template failed")]
    SourceTemplate(#[from] Hancom2020Vs0Error),
    #[error("VS-1 character style failed")]
    CharacterStyle(#[from] CharacterStyleError),
    #[error("VS-1 paragraph style failed")]
    ParagraphStyle(#[from] ParagraphStyleError),
    #[error("VS-1 page setup failed")]
    PageSetup(#[from] PageSetupError),
    #[error("VS-1 column setup failed")]
    SectionColumns(#[from] SectionColumnError),
    #[error("VS-1 text flow failed")]
    TextFlow(#[from] TextFlowError),
    #[error("VS-1 template shape is unsupported")]
    TemplateMismatch,
    #[error("VS-1 ZIP construction failed")]
    ZipConstruction,
    #[error("VS-1 package validation failed")]
    PackageValidation,
    #[error("VS-1 package graph validation failed")]
    GraphValidation(#[source] GraphError),
    #[error("VS-1 package identifier validation failed")]
    IdValidation(#[source] IdIndexError),
    #[error("VS-1 semantic readback differs")]
    ReadbackMismatch,
    #[error("VS-1 output exceeds its finite limit")]
    OutputLimitExceeded,
    #[error("VS-1 artifact identity mismatch")]
    ArtifactMismatch,
}

impl Hancom2020Vs1LayoutError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidDocument => "hancom_2020_vs1_layout_invalid_document",
            Self::SourceTemplate(_) => "hancom_2020_vs1_layout_source_template",
            Self::CharacterStyle(_) => "hancom_2020_vs1_layout_character_style",
            Self::ParagraphStyle(_) => "hancom_2020_vs1_layout_paragraph_style",
            Self::PageSetup(_) => "hancom_2020_vs1_layout_page_setup",
            Self::SectionColumns(_) => "hancom_2020_vs1_layout_section_columns",
            Self::TextFlow(_) => "hancom_2020_vs1_layout_text_flow",
            Self::TemplateMismatch => "hancom_2020_vs1_layout_template_mismatch",
            Self::ZipConstruction => "hancom_2020_vs1_layout_zip_construction",
            Self::PackageValidation => "hancom_2020_vs1_layout_package_validation",
            Self::GraphValidation(_) => "hancom_2020_vs1_layout_graph_validation",
            Self::IdValidation(_) => "hancom_2020_vs1_layout_id_validation",
            Self::ReadbackMismatch => "hancom_2020_vs1_layout_readback_mismatch",
            Self::OutputLimitExceeded => "hancom_2020_vs1_layout_output_limit_exceeded",
            Self::ArtifactMismatch => "hancom_2020_vs1_layout_artifact_mismatch",
        }
    }
}

fn validate_line(value: &str) -> Result<(), Hancom2020Vs1LayoutError> {
    if value.is_empty()
        || value.chars().any(|character| {
            character.is_control() || matches!(character as u32 & 0xffff, 0xfffe | 0xffff)
        })
    {
        return Err(Hancom2020Vs1LayoutError::InvalidDocument);
    }
    Ok(())
}

fn validate_document(
    document: &Hancom2020Vs1LayoutDocument,
) -> Result<(), Hancom2020Vs1LayoutError> {
    let normalized = Hancom2020Vs1LayoutDocument::new_with_policy(
        &document.title,
        document.body_paragraphs.clone(),
        document.column_flow_policy,
    )?;
    if normalized != *document {
        return Err(Hancom2020Vs1LayoutError::InvalidDocument);
    }
    Ok(())
}

fn expected_page_setup() -> Result<PageSetup, Hancom2020Vs1LayoutError> {
    Ok(PageSetup {
        orientation: PageOrientation::Landscape,
        dimensions: PageDimensions::from_milli_mm(230_000, 310_000)?,
        gutter_type: PageGutterType::TopBottom,
        margins: PageMargins {
            header: 2_835,
            footer: 2_268,
            gutter: 1_417,
            left: 4_252,
            right: 3_402,
            top: 5_669,
            bottom: 4_252,
        },
    })
}

const fn profile_id(policy: Hancom2020ColumnFlowPolicy) -> &'static str {
    match policy {
        Hancom2020ColumnFlowPolicy::ExplicitMidpointBreak => HANCOM_2020_VS1_LAYOUT_PROFILE_ID,
        Hancom2020ColumnFlowPolicy::AutomaticBalanced => HANCOM_2020_DENSE_COLUMN_FLOW_PROFILE_ID,
    }
}

fn expected_columns(policy: Hancom2020ColumnFlowPolicy) -> ColumnDefinition {
    ColumnDefinition {
        // The current Hangul 2020 target serializes section-column backend IDs as empty. Logical
        // identity is carried above this value model, so the fixed VS-1 artifact uses the exact
        // target form instead of creating a backend identifier that SaveAs will erase.
        control_id: String::new(),
        column_type: match policy {
            Hancom2020ColumnFlowPolicy::ExplicitMidpointBreak => ColumnType::Newspaper,
            Hancom2020ColumnFlowPolicy::AutomaticBalanced => ColumnType::BalancedNewspaper,
        },
        layout: ColumnLayout::Left,
        sizing: ColumnSizing::Equal {
            count: 2,
            gap: 1_700,
        },
        separator: Some(ColumnSeparator {
            line_type: ColumnLineType::Solid,
            width: ColumnLineWidth::Mm0_12,
            color: 0x0033_6699,
        }),
    }
}

fn apply_profile_styles(
    header: &[u8],
) -> Result<(Vec<u8>, CharacterStyleCatalog, ParagraphStyleCatalog), Hancom2020Vs1LayoutError> {
    let mut characters =
        CharacterStyleCatalogReader::read(header, CharacterStyleLimits::default())?;
    let body = characters
        .styles
        .get_mut(BODY_CHARACTER_STYLE_ID as usize)
        .ok_or(Hancom2020Vs1LayoutError::TemplateMismatch)?;
    body.height = 1_000;
    body.text_color = Color::Rgb(0x20, 0x20, 0x20);
    body.effects.bold = BinaryProperty::Off;
    let title = characters
        .styles
        .get_mut(TITLE_CHARACTER_STYLE_ID as usize)
        .ok_or(Hancom2020Vs1LayoutError::TemplateMismatch)?;
    title.height = 1_800;
    title.text_color = Color::Rgb(0x1f, 0x4e, 0x79);
    title.effects.bold = BinaryProperty::On;

    let mut paragraphs =
        ParagraphStyleCatalogReader::read(header, ParagraphStyleLimits::default())?;
    let body = paragraphs
        .styles
        .get_mut(BODY_PARAGRAPH_STYLE_ID as usize)
        .ok_or(Hancom2020Vs1LayoutError::TemplateMismatch)?;
    body.horizontal_alignment = HorizontalAlignment::Justify;
    body.break_settings.keep_with_next = false;
    let title = paragraphs
        .styles
        .get_mut(TITLE_PARAGRAPH_STYLE_ID as usize)
        .ok_or(Hancom2020Vs1LayoutError::TemplateMismatch)?;
    title.horizontal_alignment = HorizontalAlignment::Center;
    title.break_settings.keep_with_next = true;
    paragraphs.validate_character_style_references(&characters)?;

    let character_fragment =
        CharacterStyleCatalogWriter::lower(&characters, CharacterStyleLimits::default())?;
    let paragraph_fragment =
        ParagraphStyleCatalogWriter::lower(&paragraphs, ParagraphStyleLimits::default())?;
    let mut output = header.to_vec();
    for (name, fragment) in [
        ("fontfaces", character_fragment.as_slice()),
        ("charProperties", character_fragment.as_slice()),
        ("borderFills", paragraph_fragment.as_slice()),
        ("paraProperties", paragraph_fragment.as_slice()),
    ] {
        let replacement = extract_named_element(fragment, name)?;
        output = replace_named_element(&output, name, replacement)?;
    }
    if CharacterStyleCatalogReader::read(&output, CharacterStyleLimits::default())? != characters
        || ParagraphStyleCatalogReader::read(&output, ParagraphStyleLimits::default())?
            != paragraphs
    {
        return Err(Hancom2020Vs1LayoutError::ReadbackMismatch);
    }
    Ok((output, characters, paragraphs))
}

fn compose_section(
    section: &[u8],
    document: &Hancom2020Vs1LayoutDocument,
) -> Result<Vec<u8>, Hancom2020Vs1LayoutError> {
    let page_setup = expected_page_setup()?;
    let page_metrics = page_setup.metrics(PageSetupLimits::default())?;
    let (section, _) =
        PageSetupLowerer::replace_in_section(section, &page_setup, PageSetupLimits::default())?;
    let (mut section, _) = SectionColumnLowerer::replace_in_section(
        &section,
        0,
        &expected_columns(document.column_flow_policy),
        page_metrics.body_width,
        SectionColumnLimits::default(),
    )?;
    section = replace_exact_once(
        &section,
        br#"<hp:p id="1" paraPrIDRef="0" styleIDRef="0""#,
        br#"<hp:p id="1" paraPrIDRef="1" styleIDRef="0""#,
    )?;
    let old_title = format!(r#"<hp:run charPrIDRef="0"><hp:t>{TEMPLATE_TITLE}</hp:t></hp:run>"#);
    let new_title = format!(
        r#"<hp:run charPrIDRef="1"><hp:t>{}</hp:t></hp:run>"#,
        escape_xml_text(&document.title),
    );
    section = replace_exact_once(&section, old_title.as_bytes(), new_title.as_bytes())?;
    section = replace_exact_once(&section, b"horzsize=\"42520\"", b"horzsize=\"39260\"")?;

    let column_break_index = document.body_paragraphs.len() / 2;
    let mut body_xml = Vec::new();
    for (index, paragraph) in document.body_paragraphs.iter().enumerate() {
        let id = u32::try_from(index)
            .ok()
            .and_then(|value| value.checked_add(2))
            .ok_or(Hancom2020Vs1LayoutError::InvalidDocument)?;
        let column_break = document.column_flow_policy
            == Hancom2020ColumnFlowPolicy::ExplicitMidpointBreak
            && index == column_break_index;
        let flow = typed_paragraph(id, paragraph, column_break);
        let lowered = TextFlowWriter::lower(&flow, TextFlowLimits::default())?;
        body_xml.extend_from_slice(&nested_paragraph(&lowered)?);
    }
    replace_exact_once(
        &section,
        b"</hs:sec>",
        &[body_xml.as_slice(), b"</hs:sec>"].concat(),
    )
}

fn typed_paragraph(id: u32, text: &str, column_break: bool) -> TextFlow {
    TextFlow {
        paragraph: TextParagraphProperties {
            id,
            paragraph_property_id_ref: Some(BODY_PARAGRAPH_STYLE_ID),
            style_id_ref: Some(0),
            page_break: false,
            column_break,
            merged: false,
            paragraph_change_id: None,
        },
        children: vec![ParagraphChild::Run(TextRun {
            character_property_id_ref: Some(BODY_CHARACTER_STYLE_ID),
            character_change_id: None,
            items: vec![TextRunItem::Text(TextSpan {
                character_style_id_ref: None,
                atoms: vec![TextAtom::Text(text.to_owned())],
            })],
        })],
    }
}

fn nested_paragraph(lowered: &[u8]) -> Result<Vec<u8>, Hancom2020Vs1LayoutError> {
    let prefix = concat!(
        r#"<?xml version="1.0" encoding="UTF-8"?>"#,
        r#"<hp:p xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" "#,
    );
    if !lowered.starts_with(prefix.as_bytes()) {
        return Err(Hancom2020Vs1LayoutError::TemplateMismatch);
    }
    let mut output = b"<hp:p ".to_vec();
    output.extend_from_slice(&lowered[prefix.len()..]);
    Ok(output)
}

fn compose_package(
    source: &[u8],
    document: &Hancom2020Vs1LayoutDocument,
) -> Result<Vec<u8>, Hancom2020Vs1LayoutError> {
    let mut archive = ZipArchive::new(Cursor::new(source))
        .map_err(|_| Hancom2020Vs1LayoutError::ZipConstruction)?;
    let mut parts = Vec::new();
    parts
        .try_reserve_exact(archive.len())
        .map_err(|_| Hancom2020Vs1LayoutError::OutputLimitExceeded)?;
    let mut replaced = 0_u8;
    for index in 0..archive.len() {
        let mut entry = archive
            .by_index(index)
            .map_err(|_| Hancom2020Vs1LayoutError::ZipConstruction)?;
        let path = entry.name().to_owned();
        let method = entry.compression();
        let mut bytes = Vec::new();
        entry
            .read_to_end(&mut bytes)
            .map_err(|_| Hancom2020Vs1LayoutError::ZipConstruction)?;
        match path.as_str() {
            "Contents/header.xml" => {
                bytes = apply_profile_styles(&bytes)?.0;
                replaced += 1;
            }
            "Contents/section0.xml" => {
                bytes = compose_section(&bytes, document)?;
                replaced += 1;
            }
            "Preview/PrvText.txt" => {
                bytes = format!(
                    "HWPX Agent P05-09 VS-1 Layout\r\n{}\r\n",
                    document.canonical_text().replace('\n', "\r\n")
                )
                .into_bytes();
                replaced += 1;
            }
            _ => {}
        }
        parts.push((path, method, bytes));
    }
    if replaced != 3 {
        return Err(Hancom2020Vs1LayoutError::TemplateMismatch);
    }
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    for (path, method, bytes) in parts {
        let mut options = SimpleFileOptions::default()
            .compression_method(method)
            .last_modified_time(DateTime::default())
            .system(System::Unix)
            .unix_permissions(0o644);
        if method == CompressionMethod::Deflated {
            options = options.compression_level(Some(NORMALIZED_DEFLATE_LEVEL));
        }
        writer
            .start_file(path, options)
            .map_err(|_| Hancom2020Vs1LayoutError::ZipConstruction)?;
        writer
            .write_all(&bytes)
            .map_err(|_| Hancom2020Vs1LayoutError::ZipConstruction)?;
    }
    writer
        .finish()
        .map(Cursor::into_inner)
        .map_err(|_| Hancom2020Vs1LayoutError::ZipConstruction)
}

fn inspect_package(
    bytes: &[u8],
) -> Result<Hancom2020Vs1LayoutInspection, Hancom2020Vs1LayoutError> {
    if bytes.is_empty() || bytes.len() > MAX_ARTIFACT_BYTES {
        return Err(Hancom2020Vs1LayoutError::OutputLimitExceeded);
    }
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())
        .map_err(|_| Hancom2020Vs1LayoutError::PackageValidation)?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())
        .map_err(Hancom2020Vs1LayoutError::GraphValidation)?;
    let _index = IdIndex::build(
        &mut reader,
        &graph,
        IdRuleProfile::current_hancom_2020_core_v1(),
        IdIndexLimits::default(),
    )
    .map_err(Hancom2020Vs1LayoutError::IdValidation)?;
    if graph.parts.len() != reader.entries().len() {
        return Err(Hancom2020Vs1LayoutError::PackageValidation);
    }
    let header = read_part(&mut reader, "Contents/header.xml")?;
    let section = read_part(&mut reader, "Contents/section0.xml")?;
    let characters = CharacterStyleCatalogReader::read(&header, CharacterStyleLimits::default())?;
    let paragraphs = ParagraphStyleCatalogReader::read(&header, ParagraphStyleLimits::default())?;
    paragraphs.validate_character_style_references(&characters)?;
    validate_profile_styles(&characters, &paragraphs)?;

    let setup = PageSetupReader::read(&section, PageSetupLimits::default())?;
    if setup != expected_page_setup()? {
        return Err(Hancom2020Vs1LayoutError::ReadbackMismatch);
    }
    let page_metrics = setup.metrics(PageSetupLimits::default())?;
    let columns = SectionColumnReader::read_section(
        &section,
        page_metrics.body_width,
        SectionColumnLimits::default(),
    )?;
    let flows = read_paragraphs(&section)?;
    if !(MIN_BODY_PARAGRAPHS + 1..=HANCOM_2020_VS1_LAYOUT_MAX_PARAGRAPHS + 1).contains(&flows.len())
    {
        return Err(Hancom2020Vs1LayoutError::ReadbackMismatch);
    }
    let mut visible = String::new();
    let mut visible_bytes = 0_usize;
    let mut column_break_count = 0;
    for (index, flow) in flows.iter().enumerate() {
        validate_flow_references(flow, &characters, &paragraphs)?;
        if index == 0 {
            if flow.paragraph.paragraph_property_id_ref != Some(TITLE_PARAGRAPH_STYLE_ID) {
                return Err(Hancom2020Vs1LayoutError::ReadbackMismatch);
            }
            validate_visible_character_style(flow, TITLE_CHARACTER_STYLE_ID)?;
        } else if flow.paragraph.paragraph_property_id_ref != Some(BODY_PARAGRAPH_STYLE_ID) {
            return Err(Hancom2020Vs1LayoutError::ReadbackMismatch);
        } else {
            validate_visible_character_style(flow, BODY_CHARACTER_STYLE_ID)?;
        }
        if flow.paragraph.column_break {
            column_break_count += 1;
        }
        let line = flow.visible_text_nfc()?;
        if line.is_empty()
            || line.chars().any(|character| {
                character.is_control() || matches!(character as u32 & 0xffff, 0xfffe | 0xffff)
            })
        {
            return Err(Hancom2020Vs1LayoutError::ReadbackMismatch);
        }
        visible_bytes = visible_bytes
            .checked_add(line.len())
            .ok_or(Hancom2020Vs1LayoutError::OutputLimitExceeded)?;
        if visible_bytes > HANCOM_2020_VS1_LAYOUT_MAX_TEXT_BYTES {
            return Err(Hancom2020Vs1LayoutError::OutputLimitExceeded);
        }
        if index != 0 {
            visible.push('\n');
        }
        visible.push_str(&line);
    }
    let column_flow_policy = match column_break_count {
        0 => Hancom2020ColumnFlowPolicy::AutomaticBalanced,
        1 => Hancom2020ColumnFlowPolicy::ExplicitMidpointBreak,
        _ => return Err(Hancom2020Vs1LayoutError::ReadbackMismatch),
    };
    let expected_columns = expected_columns(column_flow_policy);
    if columns.spans != vec![expected_columns.clone()] {
        return Err(Hancom2020Vs1LayoutError::ReadbackMismatch);
    }
    let column_metrics =
        expected_columns.metrics(page_metrics.body_width, SectionColumnLimits::default())?;
    Ok(Hancom2020Vs1LayoutInspection {
        profile_id: profile_id(column_flow_policy),
        column_flow_policy,
        part_count: graph.parts.len(),
        paragraph_count: flows.len(),
        column_break_count,
        character_style_count: characters.styles.len(),
        paragraph_style_count: paragraphs.styles.len(),
        page_metrics,
        column_metrics,
        visible_text_sha256: Sha256::digest(visible.as_bytes()).into(),
    })
}

fn validate_profile_styles(
    characters: &CharacterStyleCatalog,
    paragraphs: &ParagraphStyleCatalog,
) -> Result<(), Hancom2020Vs1LayoutError> {
    let body = characters
        .styles
        .get(BODY_CHARACTER_STYLE_ID as usize)
        .ok_or(Hancom2020Vs1LayoutError::ReadbackMismatch)?;
    let title = characters
        .styles
        .get(TITLE_CHARACTER_STYLE_ID as usize)
        .ok_or(Hancom2020Vs1LayoutError::ReadbackMismatch)?;
    let body_paragraph = paragraphs
        .styles
        .get(BODY_PARAGRAPH_STYLE_ID as usize)
        .ok_or(Hancom2020Vs1LayoutError::ReadbackMismatch)?;
    let title_paragraph = paragraphs
        .styles
        .get(TITLE_PARAGRAPH_STYLE_ID as usize)
        .ok_or(Hancom2020Vs1LayoutError::ReadbackMismatch)?;
    if body.height != 1_000
        || body.text_color != Color::Rgb(0x20, 0x20, 0x20)
        || body.effects.bold != BinaryProperty::Off
        || title.height != 1_800
        || title.text_color != Color::Rgb(0x1f, 0x4e, 0x79)
        || title.effects.bold != BinaryProperty::On
        || body_paragraph.horizontal_alignment != HorizontalAlignment::Justify
        || body_paragraph.break_settings.keep_with_next
        || title_paragraph.horizontal_alignment != HorizontalAlignment::Center
        || !title_paragraph.break_settings.keep_with_next
    {
        return Err(Hancom2020Vs1LayoutError::ReadbackMismatch);
    }
    Ok(())
}

fn validate_flow_references(
    flow: &TextFlow,
    characters: &CharacterStyleCatalog,
    paragraphs: &ParagraphStyleCatalog,
) -> Result<(), Hancom2020Vs1LayoutError> {
    if flow
        .paragraph
        .paragraph_property_id_ref
        .is_some_and(|id| id as usize >= paragraphs.styles.len())
    {
        return Err(Hancom2020Vs1LayoutError::ReadbackMismatch);
    }
    for child in &flow.children {
        let ParagraphChild::Run(run) = child else {
            continue;
        };
        if run
            .character_property_id_ref
            .is_some_and(|id| id as usize >= characters.styles.len())
        {
            return Err(Hancom2020Vs1LayoutError::ReadbackMismatch);
        }
        for item in &run.items {
            if let TextRunItem::Text(span) = item
                && span
                    .character_style_id_ref
                    .is_some_and(|id| id as usize >= characters.styles.len())
            {
                return Err(Hancom2020Vs1LayoutError::ReadbackMismatch);
            }
        }
    }
    Ok(())
}

fn validate_visible_character_style(
    flow: &TextFlow,
    expected_id: u32,
) -> Result<(), Hancom2020Vs1LayoutError> {
    let mut visible_run_found = false;
    for child in &flow.children {
        let ParagraphChild::Run(run) = child else {
            continue;
        };
        let has_visible_text = run
            .items
            .iter()
            .any(|item| matches!(item, TextRunItem::Text(span) if !span.atoms.is_empty()));
        if !has_visible_text {
            continue;
        }
        if run.character_property_id_ref != Some(expected_id)
            || run.items.iter().any(|item| {
                matches!(
                    item,
                    TextRunItem::Text(span)
                        if span.character_style_id_ref.is_some_and(|id| id != expected_id)
                )
            })
        {
            return Err(Hancom2020Vs1LayoutError::ReadbackMismatch);
        }
        visible_run_found = true;
    }
    if !visible_run_found {
        return Err(Hancom2020Vs1LayoutError::ReadbackMismatch);
    }
    Ok(())
}

fn read_paragraphs(section: &[u8]) -> Result<Vec<TextFlow>, Hancom2020Vs1LayoutError> {
    let ranges = element_ranges(section, b"<hp:p ", b"</hp:p>")?;
    let mut flows = Vec::new();
    flows
        .try_reserve_exact(ranges.len())
        .map_err(|_| Hancom2020Vs1LayoutError::OutputLimitExceeded)?;
    for (start, end) in ranges {
        let paragraph = &section[start..end];
        let start_tag_end = paragraph
            .iter()
            .position(|byte| *byte == b'>')
            .ok_or(Hancom2020Vs1LayoutError::TemplateMismatch)?;
        let namespaced = if paragraph[..=start_tag_end]
            .windows(b"xmlns:hp=".len())
            .any(|window| window == b"xmlns:hp=")
        {
            paragraph.to_vec()
        } else {
            replace_exact_once(
                paragraph,
                b"<hp:p ",
                br#"<hp:p xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" "#,
            )?
        };
        flows.push(TextFlowReader::read(
            &namespaced,
            TextFlowLimits::default(),
        )?);
    }
    Ok(flows)
}

fn read_part(
    reader: &mut BoundedZipReader<Cursor<&[u8]>>,
    path: &str,
) -> Result<Vec<u8>, Hancom2020Vs1LayoutError> {
    let index = reader
        .entries()
        .iter()
        .find(|entry| entry.path.as_str() == path)
        .map(|entry| entry.index)
        .ok_or(Hancom2020Vs1LayoutError::PackageValidation)?;
    reader
        .read_entry(index)
        .map_err(|_| Hancom2020Vs1LayoutError::PackageValidation)
}

fn extract_named_element<'a>(
    source: &'a [u8],
    name: &str,
) -> Result<&'a [u8], Hancom2020Vs1LayoutError> {
    let start = format!("<hh:{name}");
    let end = format!("</hh:{name}>");
    let ranges = element_ranges(source, start.as_bytes(), end.as_bytes())?;
    if ranges.len() != 1 {
        return Err(Hancom2020Vs1LayoutError::TemplateMismatch);
    }
    Ok(&source[ranges[0].0..ranges[0].1])
}

fn replace_named_element(
    source: &[u8],
    name: &str,
    replacement: &[u8],
) -> Result<Vec<u8>, Hancom2020Vs1LayoutError> {
    let start = format!("<hh:{name}");
    let end = format!("</hh:{name}>");
    let ranges = element_ranges(source, start.as_bytes(), end.as_bytes())?;
    if ranges.len() != 1 {
        return Err(Hancom2020Vs1LayoutError::TemplateMismatch);
    }
    let (begin, finish) = ranges[0];
    let mut output = Vec::with_capacity(source.len() - (finish - begin) + replacement.len());
    output.extend_from_slice(&source[..begin]);
    output.extend_from_slice(replacement);
    output.extend_from_slice(&source[finish..]);
    Ok(output)
}

fn element_ranges(
    source: &[u8],
    start: &[u8],
    end: &[u8],
) -> Result<Vec<(usize, usize)>, Hancom2020Vs1LayoutError> {
    if start.is_empty() || end.is_empty() {
        return Err(Hancom2020Vs1LayoutError::TemplateMismatch);
    }
    let mut ranges = Vec::new();
    let mut cursor = 0;
    while let Some(relative_start) = source[cursor..]
        .windows(start.len())
        .position(|window| window == start)
    {
        let begin = cursor + relative_start;
        let search_from = begin + start.len();
        let relative_end = source[search_from..]
            .windows(end.len())
            .position(|window| window == end)
            .ok_or(Hancom2020Vs1LayoutError::TemplateMismatch)?;
        let finish = search_from + relative_end + end.len();
        ranges.push((begin, finish));
        cursor = finish;
    }
    if ranges.is_empty() {
        return Err(Hancom2020Vs1LayoutError::TemplateMismatch);
    }
    Ok(ranges)
}

fn replace_exact_once(
    source: &[u8],
    from: &[u8],
    to: &[u8],
) -> Result<Vec<u8>, Hancom2020Vs1LayoutError> {
    if from.is_empty() {
        return Err(Hancom2020Vs1LayoutError::TemplateMismatch);
    }
    let indexes: Vec<_> = source
        .windows(from.len())
        .enumerate()
        .filter_map(|(index, window)| (window == from).then_some(index))
        .collect();
    if indexes.len() != 1 {
        return Err(Hancom2020Vs1LayoutError::TemplateMismatch);
    }
    let index = indexes[0];
    let output_len = source
        .len()
        .checked_sub(from.len())
        .and_then(|value| value.checked_add(to.len()))
        .ok_or(Hancom2020Vs1LayoutError::OutputLimitExceeded)?;
    if output_len > MAX_ARTIFACT_BYTES {
        return Err(Hancom2020Vs1LayoutError::OutputLimitExceeded);
    }
    let mut output = Vec::with_capacity(output_len);
    output.extend_from_slice(&source[..index]);
    output.extend_from_slice(to);
    output.extend_from_slice(&source[index + from.len()..]);
    Ok(output)
}

fn escape_xml_text(text: &str) -> String {
    let mut escaped = String::with_capacity(text.len());
    for character in text.chars() {
        match character {
            '&' => escaped.push_str("&amp;"),
            '<' => escaped.push_str("&lt;"),
            '>' => escaped.push_str("&gt;"),
            '"' => escaped.push_str("&quot;"),
            '\'' => escaped.push_str("&apos;"),
            _ => escaped.push(character),
        }
    }
    escaped
}

#[cfg(test)]
mod tests {
    use super::*;

    type TestResult = Result<(), Box<dyn std::error::Error>>;

    fn sample() -> Result<Hancom2020Vs1LayoutDocument, Hancom2020Vs1LayoutError> {
        Hancom2020Vs1LayoutDocument::new(
            "VS-1 레이아웃",
            vec![
                "첫 번째 단락 & 안전한 XML".to_owned(),
                "두 번째 단락은 둘째 단에서 시작합니다.".to_owned(),
                "세 번째 단락 <끝>과 xmlns:hp= 문자열".to_owned(),
            ],
        )
    }

    #[test]
    fn deterministic_layout_artifact_reopens_semantically() -> TestResult {
        let document = sample()?;
        let first = Hancom2020Vs1LayoutBuilder::build(&document)?;
        let second = Hancom2020Vs1LayoutBuilder::build(&document)?;
        assert_eq!(first.sha256(), second.sha256());
        assert_eq!(first.size_bytes(), second.size_bytes());
        assert_eq!(first.inspection(), second.inspection());
        assert_eq!(first.inspection().paragraph_count, 4);
        assert_eq!(first.inspection().column_break_count, 1);
        assert_eq!(first.inspection().page_metrics.body_width, 80_220);
        assert_eq!(first.inspection().column_metrics.column_count, 2);
        first.verify()?;
        Ok(())
    }

    #[test]
    fn automatic_balanced_profile_has_no_explicit_column_break() -> TestResult {
        let source = sample()?;
        let document = Hancom2020Vs1LayoutDocument::new_automatic_balanced(
            source.title(),
            source.body_paragraphs().to_vec(),
        )?;
        let artifact = Hancom2020Vs1LayoutBuilder::build(&document)?;
        assert_eq!(
            artifact.inspection().profile_id,
            HANCOM_2020_DENSE_COLUMN_FLOW_PROFILE_ID
        );
        assert_eq!(
            artifact.inspection().column_flow_policy,
            Hancom2020ColumnFlowPolicy::AutomaticBalanced
        );
        assert_eq!(artifact.inspection().column_break_count, 0);
        artifact.verify()?;
        Ok(())
    }

    #[test]
    fn explicit_and_automatic_profiles_keep_distinct_current_target_column_types() {
        let explicit = expected_columns(Hancom2020ColumnFlowPolicy::ExplicitMidpointBreak);
        assert!(explicit.control_id.is_empty());
        assert_eq!(explicit.column_type, ColumnType::Newspaper);

        let automatic = expected_columns(Hancom2020ColumnFlowPolicy::AutomaticBalanced);
        assert!(automatic.control_id.is_empty());
        assert_eq!(automatic.column_type, ColumnType::BalancedNewspaper);
    }

    #[test]
    fn visible_text_and_styles_are_bound_to_the_receipt() -> TestResult {
        let document = sample()?;
        let artifact = Hancom2020Vs1LayoutBuilder::build(&document)?;
        assert_eq!(
            artifact.inspection().visible_text_sha256,
            <[u8; 32]>::from(Sha256::digest(document.canonical_text().as_bytes()))
        );
        assert!(artifact.inspection().character_style_count >= 2);
        assert!(artifact.inspection().paragraph_style_count >= 2);
        let inspected = artifact.with_verified_bytes(Hancom2020Vs1LayoutBuilder::inspect)??;
        assert_eq!(inspected, *artifact.inspection());
        Ok(())
    }

    #[test]
    fn invalid_inputs_fail_closed_and_debug_redacts_text() -> TestResult {
        let Err(error) = Hancom2020Vs1LayoutDocument::new("", vec!["a".into(), "b".into()]) else {
            return Err("empty title was accepted".into());
        };
        assert_eq!(error.code(), "hancom_2020_vs1_layout_invalid_document");
        assert!(
            Hancom2020Vs1LayoutDocument::new("title", vec!["only one paragraph".into()]).is_err()
        );
        assert!(
            Hancom2020Vs1LayoutDocument::new("title", vec!["line\nbreak".into(), "other".into()])
                .is_err()
        );
        let document = sample()?;
        let diagnostic = format!("{document:?}");
        assert!(!diagnostic.contains("첫 번째"));
        assert!(!diagnostic.contains("둘째 단"));
        Ok(())
    }

    #[test]
    fn mutated_artifact_is_not_released_to_a_consumer() -> TestResult {
        let document = sample()?;
        let mut artifact = Hancom2020Vs1LayoutBuilder::build(&document)?;
        artifact.bytes[0] ^= 0xff;
        let Err(error) = artifact.verify() else {
            return Err("mutated artifact verified".into());
        };
        assert_eq!(error.code(), "hancom_2020_vs1_layout_artifact_mismatch");
        let mut invoked = false;
        assert!(artifact.with_verified_bytes(|_| invoked = true).is_err());
        assert!(!invoked);
        Ok(())
    }
}
