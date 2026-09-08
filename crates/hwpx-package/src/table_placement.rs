use domain_ir::{
    LengthMicrometers, TableAttachmentMode, TableHorizontalAlignment, TableHorizontalReference,
    TableOuterMargins, TablePlacementError, TablePlacementLimits, TablePlacementState,
    TableTextFlow, TableTextWrap, TableVerticalAlignment, TableVerticalReference, UnitError,
};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::preserving_xml::{
    PreservingXmlDocument, PreservingXmlError, XmlAttributeToken, XmlByteSpan, XmlElementToken,
};
use crate::{TableLayoutHwpxError, TableLayoutHwpxLimits, TableLayoutHwpxReader};

pub const TABLE_PLACEMENT_HWPX_PROFILE_ID: &str = "hwpx-agent.table-placement-hwpx.hancom-2020/1";

const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TableOuterMarginsHwpxReadback {
    pub left_hwpunit: u32,
    pub right_hwpunit: u32,
    pub top_hwpunit: u32,
    pub bottom_hwpunit: u32,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TableAttachmentFlagsHwpxReadback {
    pub treat_as_char: bool,
    pub affect_line_spacing: bool,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TableFloatingFlagsHwpxReadback {
    pub flow_with_text: bool,
    pub allow_overlap: bool,
    pub hold_anchor_and_shape: bool,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct TablePlacementHwpxReadback {
    pub attachment_flags: TableAttachmentFlagsHwpxReadback,
    pub horizontal_reference: TableHorizontalReference,
    pub vertical_reference: TableVerticalReference,
    pub horizontal_alignment: TableHorizontalAlignment,
    pub vertical_alignment: TableVerticalAlignment,
    pub horizontal_offset_hwpunit: i64,
    pub vertical_offset_hwpunit: i64,
    pub floating_flags: TableFloatingFlagsHwpxReadback,
    pub text_wrap: TableTextWrap,
    pub text_flow: TableTextFlow,
    pub outer_margins: TableOuterMarginsHwpxReadback,
    pub content_sha256: [u8; 32],
}

#[derive(Clone, Eq, PartialEq)]
pub struct TablePlacementHwpxLoweringReceipt {
    pub profile_id: &'static str,
    pub source_sha256: [u8; 32],
    pub output_sha256: [u8; 32],
    pub source_state_sha256: [u8; 32],
    pub target_state_sha256: [u8; 32],
    pub content_sha256: [u8; 32],
    pub source_bytes: usize,
    pub output_bytes: usize,
    pub modified_attribute_count: usize,
}

impl std::fmt::Debug for TablePlacementHwpxLoweringReceipt {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("TablePlacementHwpxLoweringReceipt")
            .field("profile_id", &self.profile_id)
            .field("source_bytes", &self.source_bytes)
            .field("output_bytes", &self.output_bytes)
            .field("modified_attribute_count", &self.modified_attribute_count)
            .finish_non_exhaustive()
    }
}

#[derive(Debug, Eq, Error, PartialEq)]
pub enum TablePlacementHwpxError {
    #[error("table placement HWPX source and target logical table identities differ")]
    StateIdentityMismatch,
    #[error("table placement HWPX source state differs from native readback")]
    SourceStateMismatch,
    #[error("table placement HWPX enum attribute is outside the reviewed table profile")]
    InvalidEnum,
    #[error("table placement HWPX boolean attribute is not canonical 0 or 1")]
    InvalidBoolean,
    #[error("table placement HWPX signed numeric attribute is invalid")]
    InvalidNumber,
    #[error("table placement HWPX value is outside the finite native bound")]
    OutOfRange,
    #[error("table placement HWPX lowered readback differs")]
    ReadbackMismatch,
    #[error("table placement HWPX output exceeds its finite limit")]
    OutputLimit,
    #[error("table placement HWPX allocation failed")]
    AllocationFailed,
    #[error("table placement HWPX shape is unsupported")]
    UnsupportedShape,
    #[error("table placement state validation failed")]
    State(#[from] TablePlacementError),
    #[error("table placement unit conversion failed")]
    Unit(#[from] UnitError),
    #[error("table placement strict table admission failed")]
    Layout(#[from] TableLayoutHwpxError),
    #[error("table placement preserving XML admission failed")]
    Preserving(#[from] PreservingXmlError),
}

impl TablePlacementHwpxError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::StateIdentityMismatch => "table_placement_hwpx_state_identity_mismatch",
            Self::SourceStateMismatch => "table_placement_hwpx_source_state_mismatch",
            Self::InvalidEnum => "table_placement_hwpx_invalid_enum",
            Self::InvalidBoolean => "table_placement_hwpx_invalid_boolean",
            Self::InvalidNumber => "table_placement_hwpx_invalid_number",
            Self::OutOfRange => "table_placement_hwpx_out_of_range",
            Self::ReadbackMismatch => "table_placement_hwpx_readback_mismatch",
            Self::OutputLimit => "table_placement_hwpx_output_limit",
            Self::AllocationFailed => "table_placement_hwpx_allocation_failed",
            Self::UnsupportedShape => "table_placement_hwpx_unsupported_shape",
            Self::State(_) => "table_placement_hwpx_state_validation",
            Self::Unit(_) => "table_placement_hwpx_unit_conversion",
            Self::Layout(_) => "table_placement_hwpx_table_admission",
            Self::Preserving(_) => "table_placement_hwpx_preserving_xml",
        }
    }
}

#[derive(Debug)]
pub struct TablePlacementHwpxReader;

impl TablePlacementHwpxReader {
    /// Reads all native placement attributes from one strict standalone table fragment.
    ///
    /// # Errors
    ///
    /// Rejects malformed, incomplete, unknown, or over-limit current-profile table XML.
    pub fn read(
        bytes: &[u8],
        limits: TableLayoutHwpxLimits,
    ) -> Result<TablePlacementHwpxReadback, TablePlacementHwpxError> {
        Ok(parse_selected(bytes, None, limits)?.readback)
    }

    /// Reads one table selected by zero-based document order from a strict section part.
    ///
    /// # Errors
    ///
    /// Applies the same checks as [`Self::read`] and rejects an absent selector.
    pub fn read_in_section(
        bytes: &[u8],
        table_ordinal: usize,
        limits: TableLayoutHwpxLimits,
    ) -> Result<TablePlacementHwpxReadback, TablePlacementHwpxError> {
        Ok(parse_selected(bytes, Some(table_ordinal), limits)?.readback)
    }
}

#[derive(Debug)]
pub struct TablePlacementHwpxLowerer;

impl TablePlacementHwpxLowerer {
    /// Lowers one exact source-to-target placement transition into a standalone table fragment.
    ///
    /// # Errors
    ///
    /// Rejects logical identity/state drift, unsupported native shape, unit/limit failure, or
    /// semantic readback drift without publishing partial bytes.
    pub fn lower(
        source: &[u8],
        source_state: &TablePlacementState,
        target_state: &TablePlacementState,
        state_limits: TablePlacementLimits,
        hwpx_limits: TableLayoutHwpxLimits,
    ) -> Result<Vec<u8>, TablePlacementHwpxError> {
        Self::lower_with_receipt(
            source,
            source_state,
            target_state,
            state_limits,
            hwpx_limits,
        )
        .map(|(bytes, _)| bytes)
    }

    /// Lowers a standalone table and returns state and byte integrity evidence.
    ///
    /// # Errors
    ///
    /// Applies the same checks as [`Self::lower`].
    pub fn lower_with_receipt(
        source: &[u8],
        source_state: &TablePlacementState,
        target_state: &TablePlacementState,
        state_limits: TablePlacementLimits,
        hwpx_limits: TableLayoutHwpxLimits,
    ) -> Result<(Vec<u8>, TablePlacementHwpxLoweringReceipt), TablePlacementHwpxError> {
        lower_selected(
            source,
            None,
            source_state,
            target_state,
            state_limits,
            hwpx_limits,
        )
    }

    /// Lowers one table selected by zero-based document order inside a section part.
    ///
    /// # Errors
    ///
    /// Applies the same state, structure, preservation, and readback checks as [`Self::lower`].
    pub fn lower_in_section(
        source: &[u8],
        table_ordinal: usize,
        source_state: &TablePlacementState,
        target_state: &TablePlacementState,
        state_limits: TablePlacementLimits,
        hwpx_limits: TableLayoutHwpxLimits,
    ) -> Result<Vec<u8>, TablePlacementHwpxError> {
        Self::lower_in_section_with_receipt(
            source,
            table_ordinal,
            source_state,
            target_state,
            state_limits,
            hwpx_limits,
        )
        .map(|(bytes, _)| bytes)
    }

    /// Lowers one selected section table and returns state and byte integrity evidence.
    ///
    /// # Errors
    ///
    /// Applies the same checks as [`Self::lower_in_section`].
    pub fn lower_in_section_with_receipt(
        source: &[u8],
        table_ordinal: usize,
        source_state: &TablePlacementState,
        target_state: &TablePlacementState,
        state_limits: TablePlacementLimits,
        hwpx_limits: TableLayoutHwpxLimits,
    ) -> Result<(Vec<u8>, TablePlacementHwpxLoweringReceipt), TablePlacementHwpxError> {
        lower_selected(
            source,
            Some(table_ordinal),
            source_state,
            target_state,
            state_limits,
            hwpx_limits,
        )
    }
}

fn lower_selected(
    source: &[u8],
    table_ordinal: Option<usize>,
    source_state: &TablePlacementState,
    target_state: &TablePlacementState,
    state_limits: TablePlacementLimits,
    hwpx_limits: TableLayoutHwpxLimits,
) -> Result<(Vec<u8>, TablePlacementHwpxLoweringReceipt), TablePlacementHwpxError> {
    if source_state.table_id() != target_state.table_id() {
        return Err(TablePlacementHwpxError::StateIdentityMismatch);
    }
    let source_state_sha256 = validate_state(source_state, state_limits)?;
    let target_state_sha256 = validate_state(target_state, state_limits)?;
    let parsed = parse_selected(source, table_ordinal, hwpx_limits)?;
    let expected_source = native_from_state(&parsed.readback, source_state, hwpx_limits)?;
    if expected_source != parsed.readback {
        return Err(TablePlacementHwpxError::SourceStateMismatch);
    }
    let expected_target = native_from_state(&parsed.readback, target_state, hwpx_limits)?;
    let mut edits = placement_edits(&parsed, &expected_target)?;
    let modified_attribute_count = edits.len();
    let output = apply_edits(source, &mut edits, hwpx_limits)?;
    let output_readback = parse_selected(&output, table_ordinal, hwpx_limits)?.readback;
    if output_readback != expected_target {
        return Err(TablePlacementHwpxError::ReadbackMismatch);
    }
    let receipt = TablePlacementHwpxLoweringReceipt {
        profile_id: TABLE_PLACEMENT_HWPX_PROFILE_ID,
        source_sha256: Sha256::digest(source).into(),
        output_sha256: Sha256::digest(&output).into(),
        source_state_sha256,
        target_state_sha256,
        content_sha256: expected_target.content_sha256,
        source_bytes: source.len(),
        output_bytes: output.len(),
        modified_attribute_count,
    };
    Ok((output, receipt))
}

fn validate_state(
    state: &TablePlacementState,
    limits: TablePlacementLimits,
) -> Result<[u8; 32], TablePlacementHwpxError> {
    let bytes = state.canonical_json(limits)?;
    let reopened = TablePlacementState::from_json(&bytes, limits)?;
    if reopened != *state {
        return Err(TablePlacementHwpxError::SourceStateMismatch);
    }
    Ok(Sha256::digest(bytes).into())
}

struct ParsedPlacement {
    document: PreservingXmlDocument,
    root: usize,
    position: usize,
    outer_margin: usize,
    readback: TablePlacementHwpxReadback,
}

fn parse_selected(
    bytes: &[u8],
    table_ordinal: Option<usize>,
    limits: TableLayoutHwpxLimits,
) -> Result<ParsedPlacement, TablePlacementHwpxError> {
    let layout = match table_ordinal {
        Some(ordinal) => TableLayoutHwpxReader::read_in_section(bytes, ordinal, limits)?,
        None => TableLayoutHwpxReader::read(bytes, limits)?,
    };
    let document = PreservingXmlDocument::parse(bytes)?;
    let root = selected_root(&document, table_ordinal, limits)?;
    let position = unique_child(&document, root, "pos")?;
    let outer_margin = unique_child(&document, root, "outMargin")?;
    let readback = read_native(
        &document,
        root,
        position,
        outer_margin,
        layout.content_sha256,
        limits,
    )?;
    Ok(ParsedPlacement {
        document,
        root,
        position,
        outer_margin,
        readback,
    })
}

fn read_native(
    document: &PreservingXmlDocument,
    root: usize,
    position: usize,
    outer_margin: usize,
    content_sha256: [u8; 32],
    limits: TableLayoutHwpxLimits,
) -> Result<TablePlacementHwpxReadback, TablePlacementHwpxError> {
    let root_element = element(document, root)?;
    let position_element = element(document, position)?;
    let margin_element = element(document, outer_margin)?;
    let bound = i64::from(limits.config().dimension_hwpunit);
    Ok(TablePlacementHwpxReadback {
        attachment_flags: TableAttachmentFlagsHwpxReadback {
            treat_as_char: bool01(position_element, "treatAsChar")?,
            affect_line_spacing: bool01(position_element, "affectLSpacing")?,
        },
        horizontal_reference: parse_horizontal_reference(attribute(
            position_element,
            "horzRelTo",
        )?)?,
        vertical_reference: parse_vertical_reference(attribute(position_element, "vertRelTo")?)?,
        horizontal_alignment: parse_horizontal_alignment(attribute(
            position_element,
            "horzAlign",
        )?)?,
        vertical_alignment: parse_vertical_alignment(attribute(position_element, "vertAlign")?)?,
        horizontal_offset_hwpunit: signed_hwpunit(position_element, "horzOffset", bound)?,
        vertical_offset_hwpunit: signed_hwpunit(position_element, "vertOffset", bound)?,
        floating_flags: TableFloatingFlagsHwpxReadback {
            flow_with_text: bool01(position_element, "flowWithText")?,
            allow_overlap: bool01(position_element, "allowOverlap")?,
            hold_anchor_and_shape: bool01(position_element, "holdAnchorAndSO")?,
        },
        text_wrap: parse_text_wrap(attribute(root_element, "textWrap")?)?,
        text_flow: parse_text_flow(attribute(root_element, "textFlow")?)?,
        outer_margins: TableOuterMarginsHwpxReadback {
            left_hwpunit: unsigned_hwpunit(margin_element, "left", limits)?,
            right_hwpunit: unsigned_hwpunit(margin_element, "right", limits)?,
            top_hwpunit: unsigned_hwpunit(margin_element, "top", limits)?,
            bottom_hwpunit: unsigned_hwpunit(margin_element, "bottom", limits)?,
        },
        content_sha256,
    })
}

fn native_from_state(
    base: &TablePlacementHwpxReadback,
    state: &TablePlacementState,
    limits: TableLayoutHwpxLimits,
) -> Result<TablePlacementHwpxReadback, TablePlacementHwpxError> {
    let mut target = base.clone();
    target.text_wrap = state.text_wrap();
    target.text_flow = state.text_flow();
    target.outer_margins = native_margins(state.outer_margins(), limits)?;
    match state.attachment() {
        TableAttachmentMode::Inline {
            affect_line_spacing,
        } => {
            target.attachment_flags.treat_as_char = true;
            target.attachment_flags.affect_line_spacing = affect_line_spacing;
        }
        TableAttachmentMode::Floating { placement } => {
            target.attachment_flags.treat_as_char = false;
            target.horizontal_reference = placement.horizontal_reference;
            target.vertical_reference = placement.vertical_reference;
            target.horizontal_alignment = placement.horizontal_alignment;
            target.vertical_alignment = placement.vertical_alignment;
            target.horizontal_offset_hwpunit = native_signed(placement.horizontal_offset, limits)?;
            target.vertical_offset_hwpunit = native_signed(placement.vertical_offset, limits)?;
            target.floating_flags = TableFloatingFlagsHwpxReadback {
                flow_with_text: placement.flow_with_text,
                allow_overlap: placement.allow_overlap,
                hold_anchor_and_shape: placement.hold_anchor_and_shape,
            };
        }
    }
    Ok(target)
}

fn native_margins(
    margins: TableOuterMargins,
    limits: TableLayoutHwpxLimits,
) -> Result<TableOuterMarginsHwpxReadback, TablePlacementHwpxError> {
    Ok(TableOuterMarginsHwpxReadback {
        left_hwpunit: native_unsigned(margins.left, limits)?,
        right_hwpunit: native_unsigned(margins.right, limits)?,
        top_hwpunit: native_unsigned(margins.top, limits)?,
        bottom_hwpunit: native_unsigned(margins.bottom, limits)?,
    })
}

fn native_signed(
    value: LengthMicrometers,
    limits: TableLayoutHwpxLimits,
) -> Result<i64, TablePlacementHwpxError> {
    let native = value.to_hwp_unit()?.value().as_i64();
    if native.unsigned_abs() > u64::from(limits.config().dimension_hwpunit) {
        return Err(TablePlacementHwpxError::OutOfRange);
    }
    Ok(native)
}

fn native_unsigned(
    value: LengthMicrometers,
    limits: TableLayoutHwpxLimits,
) -> Result<u32, TablePlacementHwpxError> {
    let native = native_signed(value, limits)?;
    u32::try_from(native).map_err(|_| TablePlacementHwpxError::OutOfRange)
}

fn placement_edits(
    parsed: &ParsedPlacement,
    target: &TablePlacementHwpxReadback,
) -> Result<Vec<ByteEdit>, TablePlacementHwpxError> {
    let mut edits = Vec::new();
    edits
        .try_reserve_exact(17)
        .map_err(|_| TablePlacementHwpxError::AllocationFailed)?;
    root_edits(parsed, target, &mut edits)?;
    attachment_edits(parsed, target, &mut edits)?;
    if !target.attachment_flags.treat_as_char {
        floating_edits(parsed, target, &mut edits)?;
    }
    margin_edits(parsed, target, &mut edits)?;
    Ok(edits)
}

fn root_edits(
    parsed: &ParsedPlacement,
    target: &TablePlacementHwpxReadback,
    edits: &mut Vec<ByteEdit>,
) -> Result<(), TablePlacementHwpxError> {
    push_if_changed(
        &parsed.document,
        parsed.root,
        "textWrap",
        text_wrap(target.text_wrap),
        edits,
    )?;
    push_if_changed(
        &parsed.document,
        parsed.root,
        "textFlow",
        text_flow(target.text_flow),
        edits,
    )
}

fn attachment_edits(
    parsed: &ParsedPlacement,
    target: &TablePlacementHwpxReadback,
    edits: &mut Vec<ByteEdit>,
) -> Result<(), TablePlacementHwpxError> {
    push_if_changed(
        &parsed.document,
        parsed.position,
        "treatAsChar",
        bool_text(target.attachment_flags.treat_as_char),
        edits,
    )?;
    push_if_changed(
        &parsed.document,
        parsed.position,
        "affectLSpacing",
        bool_text(target.attachment_flags.affect_line_spacing),
        edits,
    )
}

fn floating_edits(
    parsed: &ParsedPlacement,
    target: &TablePlacementHwpxReadback,
    edits: &mut Vec<ByteEdit>,
) -> Result<(), TablePlacementHwpxError> {
    let position = parsed.position;
    let document = &parsed.document;
    push_if_changed(
        document,
        position,
        "horzRelTo",
        horizontal_reference(target.horizontal_reference),
        edits,
    )?;
    push_if_changed(
        document,
        position,
        "vertRelTo",
        vertical_reference(target.vertical_reference),
        edits,
    )?;
    push_if_changed(
        document,
        position,
        "horzAlign",
        horizontal_alignment(target.horizontal_alignment),
        edits,
    )?;
    push_if_changed(
        document,
        position,
        "vertAlign",
        vertical_alignment(target.vertical_alignment),
        edits,
    )?;
    push_if_changed(
        document,
        position,
        "horzOffset",
        &target.horizontal_offset_hwpunit.to_string(),
        edits,
    )?;
    push_if_changed(
        document,
        position,
        "vertOffset",
        &target.vertical_offset_hwpunit.to_string(),
        edits,
    )?;
    for (name, value) in [
        ("flowWithText", target.floating_flags.flow_with_text),
        ("allowOverlap", target.floating_flags.allow_overlap),
        (
            "holdAnchorAndSO",
            target.floating_flags.hold_anchor_and_shape,
        ),
    ] {
        push_if_changed(document, position, name, bool_text(value), edits)?;
    }
    Ok(())
}

fn margin_edits(
    parsed: &ParsedPlacement,
    target: &TablePlacementHwpxReadback,
    edits: &mut Vec<ByteEdit>,
) -> Result<(), TablePlacementHwpxError> {
    for (name, value) in [
        ("left", target.outer_margins.left_hwpunit),
        ("right", target.outer_margins.right_hwpunit),
        ("top", target.outer_margins.top_hwpunit),
        ("bottom", target.outer_margins.bottom_hwpunit),
    ] {
        push_if_changed(
            &parsed.document,
            parsed.outer_margin,
            name,
            &value.to_string(),
            edits,
        )?;
    }
    Ok(())
}

#[derive(Debug)]
struct ByteEdit {
    span: XmlByteSpan,
    replacement: Vec<u8>,
}

fn push_if_changed(
    document: &PreservingXmlDocument,
    element_index: usize,
    name: &str,
    replacement: &str,
    edits: &mut Vec<ByteEdit>,
) -> Result<(), TablePlacementHwpxError> {
    let attribute = unique_attribute(element(document, element_index)?, name)?;
    if attribute.semantic_value() != replacement {
        edits
            .try_reserve(1)
            .map_err(|_| TablePlacementHwpxError::AllocationFailed)?;
        edits.push(ByteEdit {
            span: attribute.value_span(),
            replacement: replacement.as_bytes().to_vec(),
        });
    }
    Ok(())
}

fn apply_edits(
    source: &[u8],
    edits: &mut [ByteEdit],
    limits: TableLayoutHwpxLimits,
) -> Result<Vec<u8>, TablePlacementHwpxError> {
    edits.sort_unstable_by_key(|edit| edit.span.start());
    let mut previous_end = 0;
    let mut output_len = source.len();
    for edit in edits.iter() {
        if edit.span.start() < previous_end || edit.span.end() > source.len() {
            return Err(TablePlacementHwpxError::UnsupportedShape);
        }
        previous_end = edit.span.end();
        output_len = output_len
            .checked_sub(edit.span.len())
            .and_then(|value| value.checked_add(edit.replacement.len()))
            .ok_or(TablePlacementHwpxError::OutputLimit)?;
    }
    if output_len > limits.config().output_bytes {
        return Err(TablePlacementHwpxError::OutputLimit);
    }
    let mut output = Vec::new();
    output
        .try_reserve_exact(output_len)
        .map_err(|_| TablePlacementHwpxError::AllocationFailed)?;
    let mut cursor = 0;
    for edit in edits.iter() {
        output.extend_from_slice(&source[cursor..edit.span.start()]);
        output.extend_from_slice(&edit.replacement);
        cursor = edit.span.end();
    }
    output.extend_from_slice(&source[cursor..]);
    if output.len() != output_len {
        return Err(TablePlacementHwpxError::OutputLimit);
    }
    Ok(output)
}

fn selected_root(
    document: &PreservingXmlDocument,
    table_ordinal: Option<usize>,
    limits: TableLayoutHwpxLimits,
) -> Result<usize, TablePlacementHwpxError> {
    if let Some(ordinal) = table_ordinal {
        let mut seen = 0_usize;
        for (index, candidate) in document.elements().iter().enumerate() {
            if has_name(candidate, "tbl") {
                if seen == ordinal {
                    return Ok(index);
                }
                seen = seen
                    .checked_add(1)
                    .ok_or(TablePlacementHwpxError::UnsupportedShape)?;
                if seen > limits.config().tables {
                    return Err(TablePlacementHwpxError::UnsupportedShape);
                }
            }
        }
        Err(TablePlacementHwpxError::UnsupportedShape)
    } else {
        let root = document.root_element();
        if !has_name(element(document, root)?, "tbl") {
            return Err(TablePlacementHwpxError::UnsupportedShape);
        }
        Ok(root)
    }
}

fn unique_child(
    document: &PreservingXmlDocument,
    parent: usize,
    local_name: &str,
) -> Result<usize, TablePlacementHwpxError> {
    let mut found = None;
    let mut child = element(document, parent)?.first_child();
    while let Some(index) = child {
        let value = element(document, index)?;
        if has_name(value, local_name) && found.replace(index).is_some() {
            return Err(TablePlacementHwpxError::UnsupportedShape);
        }
        child = value.next_sibling();
    }
    found.ok_or(TablePlacementHwpxError::UnsupportedShape)
}

fn element(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<&XmlElementToken, TablePlacementHwpxError> {
    document
        .elements()
        .get(index)
        .ok_or(TablePlacementHwpxError::UnsupportedShape)
}

fn has_name(element: &XmlElementToken, local_name: &str) -> bool {
    element.name().namespace() == Some(PARAGRAPH_NS) && element.name().local_name() == local_name
}

fn unique_attribute<'a>(
    element: &'a XmlElementToken,
    name: &str,
) -> Result<&'a XmlAttributeToken, TablePlacementHwpxError> {
    let mut matches = element.attributes().iter().filter(|attribute| {
        !attribute.is_namespace_declaration()
            && attribute.name().namespace().is_none()
            && attribute.name().local_name() == name
    });
    let value = matches
        .next()
        .ok_or(TablePlacementHwpxError::UnsupportedShape)?;
    if matches.next().is_some() {
        return Err(TablePlacementHwpxError::UnsupportedShape);
    }
    Ok(value)
}

fn attribute<'a>(
    element: &'a XmlElementToken,
    name: &str,
) -> Result<&'a str, TablePlacementHwpxError> {
    Ok(unique_attribute(element, name)?.semantic_value())
}

fn bool01(element: &XmlElementToken, name: &str) -> Result<bool, TablePlacementHwpxError> {
    match attribute(element, name)? {
        "0" => Ok(false),
        "1" => Ok(true),
        _ => Err(TablePlacementHwpxError::InvalidBoolean),
    }
}

fn unsigned_hwpunit(
    element: &XmlElementToken,
    name: &str,
    limits: TableLayoutHwpxLimits,
) -> Result<u32, TablePlacementHwpxError> {
    let value = attribute(element, name)?;
    if !canonical_unsigned(value) {
        return Err(TablePlacementHwpxError::InvalidNumber);
    }
    let parsed: u32 = value
        .parse()
        .map_err(|_| TablePlacementHwpxError::InvalidNumber)?;
    if parsed > limits.config().dimension_hwpunit {
        return Err(TablePlacementHwpxError::OutOfRange);
    }
    Ok(parsed)
}

fn signed_hwpunit(
    element: &XmlElementToken,
    name: &str,
    maximum: i64,
) -> Result<i64, TablePlacementHwpxError> {
    let value = attribute(element, name)?;
    if !canonical_signed(value) {
        return Err(TablePlacementHwpxError::InvalidNumber);
    }
    let parsed: i64 = value
        .parse()
        .map_err(|_| TablePlacementHwpxError::InvalidNumber)?;
    if parsed.unsigned_abs() > maximum.unsigned_abs() {
        return Err(TablePlacementHwpxError::OutOfRange);
    }
    Ok(parsed)
}

fn canonical_unsigned(value: &str) -> bool {
    !value.is_empty()
        && value.bytes().all(|byte| byte.is_ascii_digit())
        && (value == "0" || !value.starts_with('0'))
}

fn canonical_signed(value: &str) -> bool {
    if let Some(rest) = value.strip_prefix('-') {
        !rest.is_empty() && rest.bytes().all(|byte| byte.is_ascii_digit()) && !rest.starts_with('0')
    } else {
        canonical_unsigned(value)
    }
}

fn parse_horizontal_reference(
    value: &str,
) -> Result<TableHorizontalReference, TablePlacementHwpxError> {
    match value {
        "PAPER" => Ok(TableHorizontalReference::Paper),
        "PAGE" => Ok(TableHorizontalReference::Page),
        "COLUMN" => Ok(TableHorizontalReference::Column),
        "PARA" => Ok(TableHorizontalReference::Paragraph),
        _ => Err(TablePlacementHwpxError::InvalidEnum),
    }
}

fn horizontal_reference(value: TableHorizontalReference) -> &'static str {
    match value {
        TableHorizontalReference::Paper => "PAPER",
        TableHorizontalReference::Page => "PAGE",
        TableHorizontalReference::Column => "COLUMN",
        TableHorizontalReference::Paragraph => "PARA",
    }
}

fn parse_vertical_reference(
    value: &str,
) -> Result<TableVerticalReference, TablePlacementHwpxError> {
    match value {
        "PAPER" => Ok(TableVerticalReference::Paper),
        "PAGE" => Ok(TableVerticalReference::Page),
        "PARA" => Ok(TableVerticalReference::Paragraph),
        _ => Err(TablePlacementHwpxError::InvalidEnum),
    }
}

fn vertical_reference(value: TableVerticalReference) -> &'static str {
    match value {
        TableVerticalReference::Paper => "PAPER",
        TableVerticalReference::Page => "PAGE",
        TableVerticalReference::Paragraph => "PARA",
    }
}

fn parse_horizontal_alignment(
    value: &str,
) -> Result<TableHorizontalAlignment, TablePlacementHwpxError> {
    match value {
        "LEFT" => Ok(TableHorizontalAlignment::Left),
        "CENTER" => Ok(TableHorizontalAlignment::Center),
        "RIGHT" => Ok(TableHorizontalAlignment::Right),
        "INSIDE" => Ok(TableHorizontalAlignment::Inside),
        "OUTSIDE" => Ok(TableHorizontalAlignment::Outside),
        _ => Err(TablePlacementHwpxError::InvalidEnum),
    }
}

fn horizontal_alignment(value: TableHorizontalAlignment) -> &'static str {
    match value {
        TableHorizontalAlignment::Left => "LEFT",
        TableHorizontalAlignment::Center => "CENTER",
        TableHorizontalAlignment::Right => "RIGHT",
        TableHorizontalAlignment::Inside => "INSIDE",
        TableHorizontalAlignment::Outside => "OUTSIDE",
    }
}

fn parse_vertical_alignment(
    value: &str,
) -> Result<TableVerticalAlignment, TablePlacementHwpxError> {
    match value {
        "TOP" => Ok(TableVerticalAlignment::Top),
        "CENTER" => Ok(TableVerticalAlignment::Center),
        "BOTTOM" => Ok(TableVerticalAlignment::Bottom),
        "INSIDE" => Ok(TableVerticalAlignment::Inside),
        "OUTSIDE" => Ok(TableVerticalAlignment::Outside),
        _ => Err(TablePlacementHwpxError::InvalidEnum),
    }
}

fn vertical_alignment(value: TableVerticalAlignment) -> &'static str {
    match value {
        TableVerticalAlignment::Top => "TOP",
        TableVerticalAlignment::Center => "CENTER",
        TableVerticalAlignment::Bottom => "BOTTOM",
        TableVerticalAlignment::Inside => "INSIDE",
        TableVerticalAlignment::Outside => "OUTSIDE",
    }
}

fn parse_text_wrap(value: &str) -> Result<TableTextWrap, TablePlacementHwpxError> {
    match value {
        "SQUARE" => Ok(TableTextWrap::Square),
        "TOP_AND_BOTTOM" => Ok(TableTextWrap::TopAndBottom),
        "BEHIND_TEXT" => Ok(TableTextWrap::BehindText),
        "IN_FRONT_OF_TEXT" => Ok(TableTextWrap::InFrontOfText),
        _ => Err(TablePlacementHwpxError::InvalidEnum),
    }
}

fn text_wrap(value: TableTextWrap) -> &'static str {
    match value {
        TableTextWrap::Square => "SQUARE",
        TableTextWrap::TopAndBottom => "TOP_AND_BOTTOM",
        TableTextWrap::BehindText => "BEHIND_TEXT",
        TableTextWrap::InFrontOfText => "IN_FRONT_OF_TEXT",
    }
}

fn parse_text_flow(value: &str) -> Result<TableTextFlow, TablePlacementHwpxError> {
    match value {
        "BOTH_SIDES" => Ok(TableTextFlow::BothSides),
        "LEFT_ONLY" => Ok(TableTextFlow::LeftOnly),
        "RIGHT_ONLY" => Ok(TableTextFlow::RightOnly),
        "LARGEST_ONLY" => Ok(TableTextFlow::LargestOnly),
        _ => Err(TablePlacementHwpxError::InvalidEnum),
    }
}

fn text_flow(value: TableTextFlow) -> &'static str {
    match value {
        TableTextFlow::BothSides => "BOTH_SIDES",
        TableTextFlow::LeftOnly => "LEFT_ONLY",
        TableTextFlow::RightOnly => "RIGHT_ONLY",
        TableTextFlow::LargestOnly => "LARGEST_ONLY",
    }
}

const fn bool_text(value: bool) -> &'static str {
    if value { "1" } else { "0" }
}
