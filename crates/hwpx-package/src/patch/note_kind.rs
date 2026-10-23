//! Closed native note-tag conversion, not a general XML renaming primitive.
use super::{PatchError, PreservingXmlDocument};
use domain_ir::NoteKind;

pub(crate) struct NoteNameEdit {
    pub start: usize,
    pub end: usize,
    pub bytes: Vec<u8>,
}

pub(crate) fn source_edits(
    xml: &PreservingXmlDocument,
    index: usize,
    kind: NoteKind,
) -> Result<[NoteNameEdit; 2], PatchError> {
    // Reuse the original exact envelope reader, including nesting/WCHAR checks.
    crate::note_hwpx::read_imported_note_envelope(xml, index)
        .map_err(|_| PatchError::ValueInvalid)?;
    let node = xml.elements().get(index).ok_or(PatchError::SelectorStale)?;
    let target = match kind {
        NoteKind::Footnote => "footNote",
        NoteKind::Endnote => "endNote",
    };
    if node.name().local_name() == target {
        return Err(PatchError::ValueInvalid);
    }
    // Retain the actual namespace prefix (or default namespace) and both tags'
    // whitespace, attributes and content. Neither name is caller supplied.
    let name = match node.name().prefix() {
        Some(prefix) => format!("{prefix}:{target}"),
        None => target.to_owned(),
    };
    let end = node.end_name_span().ok_or(PatchError::SelectorStale)?;
    Ok([node.start_name_span(), end].map(|span| NoteNameEdit {
        start: span.start(), end: span.end(), bytes: name.as_bytes().to_vec(),
    }))
}
