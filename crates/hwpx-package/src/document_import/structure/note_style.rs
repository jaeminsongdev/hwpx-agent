//! REF-023 actual section note-style values. Never native/security/service authority.
mod catalog;
mod output;
pub use output::{NoteStyleCandidate, NoteStyleReceipt, NoteStyleReplacement, note_style_request_sha256};

use super::ImportedDocumentStructure;
use crate::{HANCOM_2020_PARAGRAPH_NAMESPACE as HP, NoteHwpxLimits, PackagePath,
    PreservingXmlDocument, XmlAttributeToken, XmlElementToken};
use domain_ir::{LogicalId, NoteAutoNumberFormat, NoteKind, NoteLineStyle,
    NoteNumberFormat, NoteNumberingRestart as Restart, NotePlacement as Placement,
    NoteSpacing, SourceAnchorHandle};
use serde::Serialize;
use std::fmt;
use thiserror::Error;

/// Observed/editable values only: deliberately no `locked=false` or invented
/// opaque-style digest from a partial import. Not a complete domain NoteStyle.
#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct NoteStyleValues {
    pub auto_number_format: NoteAutoNumberFormat,
    pub note_line: NoteLineStyle,
    pub spacing: NoteSpacing,
    pub numbering_restart: Restart,
    /// Exact native UINT, not a resolved display/start number. Source zero is
    /// preserved only with unchanged numbering; callers cannot create new zero.
    pub new_number: u32,
    pub placement: Placement,
    pub beneath_text: bool,
}
impl fmt::Debug for NoteStyleValues {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result { f.write_str("NoteStyleValues(<redacted>)") }
}
#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ImportedNoteStyle {
    style_id: LogicalId,
    source_anchor: SourceAnchorHandle,
    kind: NoteKind,
    values: NoteStyleValues,
    #[serde(skip)]
    part: PackagePath,
    #[serde(skip)]
    index: usize,
    #[serde(skip)]
    children: [usize; 5],
}
impl fmt::Debug for ImportedNoteStyle {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result { f.write_str("ImportedNoteStyle(<redacted>; observed_only)") }
}
impl ImportedNoteStyle {
    #[must_use] pub const fn style_id(&self) -> &LogicalId { &self.style_id }
    #[must_use] pub const fn source_anchor(&self) -> &SourceAnchorHandle { &self.source_anchor }
    #[must_use] pub const fn kind(&self) -> NoteKind { self.kind }
    #[must_use] pub const fn values(&self) -> &NoteStyleValues { &self.values }
}
#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum NoteStyleError {
    #[error("NOTE_STYLE_SOURCE_REJECTED")] Source,
    #[error("NOTE_STYLE_UNSUPPORTED_SOURCE_SHAPE")] Shape,
    #[error("NOTE_STYLE_VALUE_REJECTED")] Value,
    #[error("NOTE_STYLE_SELECTION_REJECTED")] Selection,
    #[error("NOTE_STYLE_OBSERVED_PROTECTION")] Protection,
    #[error("NOTE_STYLE_NO_CHANGE")] NoChange,
    #[error("NOTE_STYLE_FINITE_LIMIT")] Limit,
    #[error("NOTE_STYLE_PATCH_REJECTED:{0}")] Patch(&'static str),
    #[error("NOTE_STYLE_WRITER_REJECTED")] Writer,
    #[error("NOTE_STYLE_READBACK_REJECTED")] Readback,
    #[error("NOTE_STYLE_PRESERVATION_REJECTED")] Preservation,
}
type E = NoteStyleError;
const CHILDREN: [&str; 5] = ["autoNumFormat", "noteLine", "noteSpacing", "numbering", "placement"];
const SECTION_NS: &str = "http://www.hancom.co.kr/hwpml/2011/section";

impl ImportedDocumentStructure {
    /// Reads every actual style in body-spine sections without reopening ZIP/XML.
    /// Missing styles remain absent; no native defaults or protection grants.
    /// # Errors
    /// Rejects hidden/nested/duplicate declarations, missing required attributes,
    /// unsupported native spellings, incompatible families and finite limits.
    pub fn import_note_styles(&self, limits: NoteHwpxLimits) -> Result<Vec<ImportedNoteStyle>, E> {
        let mut result = Vec::new();
        let (mut visits, mut text_bytes) = (0usize, 0usize);
        for path in self.source().spine() {
            let part = self.source().parts().iter().find(|p| p.path() == path).ok_or(E::Source)?;
            let xml = part.xml().ok_or(E::Source)?;
            let root = &xml.elements()[xml.root_element()];
            if root.name().namespace() != Some(SECTION_NS) || root.name().local_name() != "sec" { continue; }
            visits = visits.checked_add(xml.elements().len()).filter(|n| *n <= limits.config().elements).ok_or(E::Limit)?;
            if xml.original_len() > limits.config().section_bytes { return Err(E::Limit); }
            let mut sec_pr = None;
            let mut kinds = [false; 2];
            for (index, node) in xml.elements().iter().enumerate() {
                if named(node, "secPr") {
                    let run = node.parent().ok_or(E::Shape)?;
                    let p = xml.elements()[run].parent().ok_or(E::Shape)?;
                    if sec_pr.replace(index).is_some() || !named(&xml.elements()[run], "run")
                        || !named(&xml.elements()[p], "p") || xml.elements()[p].parent() != Some(xml.root_element()) {
                        return Err(E::Shape);
                    }
                }
                let (kind, slot) = if named(node, "footNotePr") { (NoteKind::Footnote, 0) }
                    else if named(node, "endNotePr") { (NoteKind::Endnote, 1) } else { continue };
                if node.parent() != sec_pr || sec_pr.is_none() || kinds[slot] { return Err(E::Shape); }
                kinds[slot] = true;
                if result.len() >= limits.config().notes { return Err(E::Limit); }
                let mut children = [usize::MAX; 5];
                let mut child = node.first_child();
                while let Some(i) = child {
                    let item = xml.elements().get(i).ok_or(E::Shape)?;
                    if let Some(slot) = CHILDREN.iter().position(|name| named(item, name)) {
                        if children[slot] != usize::MAX || item.first_child().is_some() { return Err(E::Shape); }
                        children[slot] = i;
                    }
                    child = item.next_sibling();
                }
                if children.contains(&usize::MAX) { return Err(E::Shape); }
                let values = parse(xml, children, kind, limits)?;
                for text in [&values.auto_number_format.user_character, &values.auto_number_format.prefix_character,
                    &values.auto_number_format.suffix_character] {
                    text_bytes = text_bytes.checked_add(text.len()).filter(|n| *n <= limits.config().text_bytes).ok_or(E::Limit)?;
                }
                let source_anchor = part.element_anchor(index).ok_or(E::Source)?.clone();
                let style_id = LogicalId::parse(format!("note-style-{}", source_anchor.opaque_handle.as_str())).map_err(|_| E::Source)?;
                result.try_reserve(1).map_err(|_| E::Limit)?;
                result.push(ImportedNoteStyle { style_id, source_anchor, kind, values,
                    part: path.clone(), index, children });
            }
        }
        Ok(result)
    }
}
fn named(node: &XmlElementToken, name: &str) -> bool {
    node.name().namespace() == Some(HP) && node.name().local_name() == name
}
fn attribute<'a>(node: &'a XmlElementToken, name: &str) -> Result<(usize, &'a XmlAttributeToken), E> {
    let mut attrs = node.attributes().iter().enumerate().filter(|(_, a)| !a.is_namespace_declaration()
        && a.name().namespace().is_none() && a.name().local_name() == name);
    let result = attrs.next().ok_or(E::Shape)?;
    if attrs.next().is_some() { return Err(E::Shape); }
    Ok(result)
}
fn boolean(text: &str) -> Result<bool, E> {
    match text { "true" | "1" => Ok(true), "false" | "0" => Ok(false), _ => Err(E::Value) }
}
fn parse(xml: &PreservingXmlDocument, children: [usize; 5], kind: NoteKind, limits: NoteHwpxLimits) -> Result<NoteStyleValues, E> {
    let [a, l, s, n, p] = children.map(|i| &xml.elements()[i]);
    let get = |node, name| attribute(node, name).map(|(_, a)| a.semantic_value());
    let text = |node, name| -> Result<String, E> {
        let value = get(node, name)?;
        if value.len() > limits.config().text_bytes { return Err(E::Limit); }
        Ok(value.to_owned())
    };
    let color = get(l, "color")?.strip_prefix('#').filter(|c| c.len() == 6 && c.bytes().all(|b| b.is_ascii_hexdigit())).ok_or(E::Value)?;
    let values = NoteStyleValues {
        auto_number_format: NoteAutoNumberFormat {
            format: catalog::read(catalog::NUMBERS, get(a, "type")?).ok_or(E::Value)?,
            user_character: text(a, "userChar")?, prefix_character: text(a, "prefixChar")?,
            suffix_character: text(a, "suffixChar")?, superscript: boolean(get(a, "supscript")?)?,
        },
        note_line: NoteLineStyle {
            length_hwp_units: get(l, "length")?.parse().map_err(|_| E::Value)?,
            line_type: catalog::read(catalog::LINES, get(l, "type")?).ok_or(E::Value)?,
            width: catalog::read(catalog::WIDTHS, get(l, "width")?).ok_or(E::Value)?,
            color_rgb: u32::from_str_radix(color, 16).map_err(|_| E::Value)?,
        },
        spacing: NoteSpacing {
            between_notes_hwp_units: get(s, "betweenNotes")?.parse().map_err(|_| E::Value)?,
            below_line_hwp_units: get(s, "belowLine")?.parse().map_err(|_| E::Value)?,
            above_line_hwp_units: get(s, "aboveLine")?.parse().map_err(|_| E::Value)?,
        },
        numbering_restart: match get(n, "type")? {
            "CONTINUOUS" => Restart::Continuous, "ON_SECTION" => Restart::PerSection,
            "ON_PAGE" => Restart::PerPage, _ => return Err(E::Value),
        },
        new_number: get(n, "newNum")?.parse().map_err(|_| E::Value)?,
        placement: match get(p, "place")? {
            "EACH_COLUMN" => Placement::EachColumn, "MERGED_COLUMN" => Placement::MergedColumn,
            "RIGHT_MOST_COLUMN" => Placement::RightMostColumn, "END_OF_DOCUMENT" => Placement::EndOfDocument,
            "END_OF_SECTION" => Placement::EndOfSection, _ => return Err(E::Value),
        },
        beneath_text: boolean(get(p, "beneathText")?)?,
    };
    validate(&values, kind, limits)?;
    Ok(values)
}
fn validate(values: &NoteStyleValues, kind: NoteKind, limits: NoteHwpxLimits) -> Result<(), E> {
    let f = &values.auto_number_format;
    for text in [&f.user_character, &f.prefix_character, &f.suffix_character] {
        if text.len() > limits.config().text_bytes { return Err(E::Limit); }
        if text.chars().any(|ch| !(matches!(ch, '\t' | '\n' | '\r') || ch >= ' ' && ch != '\u{fffe}' && ch != '\u{ffff}')) {
            return Err(E::Value);
        }
    }
    if f.format == NoteNumberFormat::UserChar && f.user_character.is_empty()
        || values.note_line.color_rgb > 0x00ff_ffff { return Err(E::Value); }
    match kind {
        NoteKind::Footnote if !matches!(values.placement, Placement::EachColumn | Placement::MergedColumn | Placement::RightMostColumn) => Err(E::Value),
        NoteKind::Endnote if values.numbering_restart == Restart::PerPage
            || !matches!(values.placement, Placement::EndOfDocument | Placement::EndOfSection) => Err(E::Value),
        _ => Ok(()),
    }
}

fn encoded(values: &NoteStyleValues) -> [(usize, &'static str, String); 16] {
    let f = &values.auto_number_format; let l = &values.note_line; let s = &values.spacing;
    [
        (0,"type",catalog::write(catalog::NUMBERS,f.format).into()),
        (0,"userChar",f.user_character.clone()), (0,"prefixChar",f.prefix_character.clone()),
        (0,"suffixChar",f.suffix_character.clone()), (0,"supscript",u8::from(f.superscript).to_string()),
        (1,"length",l.length_hwp_units.to_string()), (1,"type",catalog::write(catalog::LINES,l.line_type).into()),
        (1,"width",catalog::write(catalog::WIDTHS,l.width).into()), (1,"color",format!("#{:06X}",l.color_rgb)),
        (2,"betweenNotes",s.between_notes_hwp_units.to_string()), (2,"belowLine",s.below_line_hwp_units.to_string()),
        (2,"aboveLine",s.above_line_hwp_units.to_string()),
        (3,"type",match values.numbering_restart { Restart::Continuous => "CONTINUOUS", Restart::PerSection => "ON_SECTION", Restart::PerPage => "ON_PAGE" }.into()),
        (3,"newNum",values.new_number.to_string()),
        (4,"place",match values.placement { Placement::EachColumn => "EACH_COLUMN", Placement::MergedColumn => "MERGED_COLUMN",
            Placement::RightMostColumn => "RIGHT_MOST_COLUMN", Placement::EndOfDocument => "END_OF_DOCUMENT", Placement::EndOfSection => "END_OF_SECTION" }.into()),
        (4,"beneathText",u8::from(values.beneath_text).to_string()),
    ]
}
