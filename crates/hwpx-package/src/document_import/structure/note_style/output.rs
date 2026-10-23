//! A single source-bound transaction; all non-selected attribute bytes preserved.
use super::{E, NoteStyleValues, attribute, encoded, validate};
use crate::document_import::{ImportedSourcePackage, structure::{ImportedDocumentStructure,
    caption_text_batch::observed_protection, caption_style_batch::subtree_protection}};
use crate::document_import::forms::{ImportedDocumentForms, VerifiedFormReconstruction};
use crate::{BoundedZipReader, IdIndexLimits, IdRuleProfile, NoteHwpxLimits, PackageArtifact,
    PackageGraphLimits, PackagePath, PatchAttributeValue, PatchIntent, PatchLimits, PatchText,
    PreservationRuleProfile, PreservingPatchEngine, PreservingWriter, PreservingXmlDocument,
    WriterError, WriterLimits, XmlAttributeSelector};
use domain_ir::LogicalId;
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use std::{collections::{BTreeMap, BTreeSet}, fmt, io::Cursor};

pub struct NoteStyleReplacement<'a> {
    pub style_id: &'a LogicalId,
    pub source_style_sha256: [u8; 32],
    pub values: &'a NoteStyleValues,
}
impl fmt::Debug for NoteStyleReplacement<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result { f.write_str("NoteStyleReplacement(<redacted>)") }
}
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct NoteStyleReceipt {
    pub profile: &'static str,
    pub capability_id: &'static str,
    pub source_package_sha256: [u8; 32],
    pub output_package_sha256: [u8; 32],
    pub request_sha256: [u8; 32],
    pub replaced_styles: usize,
    pub total_styles_read_back: usize,
    pub changed_attributes: usize,
    pub changed_parts: usize,
    pub output_bytes: usize,
    pub protection_element_visits: usize,
    pub only_selected_attribute_values_changed: bool,
    pub opaque_xml_note_bodies_and_other_parts_preserved: bool,
    pub complete_protection_qualified: bool,
    pub native_layout_and_numbering_qualified: bool,
    pub execution_publication_authority: bool,
}
pub struct NoteStyleCandidate { artifact: PackageArtifact, receipt: NoteStyleReceipt }
impl fmt::Debug for NoteStyleCandidate {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result { f.write_str("NoteStyleCandidate(<redacted>; not_native_or_authority)") }
}
impl NoteStyleCandidate {
    #[must_use] pub const fn receipt(&self) -> &NoteStyleReceipt { &self.receipt }
    /// Writer integrity only, never ACL/head/publication authorization.
    /// # Errors
    /// Rejects integrity failures before exposing bytes.
    pub fn with_verified_bytes<T>(&self, consume: impl FnOnce(&[u8]) -> T) -> Result<T, WriterError> {
        self.artifact.with_verified_bytes(consume)
    }
}
struct Edit { start: usize, end: usize, bytes: Vec<u8> }
struct PartEdits<'a> { xml: &'a PreservingXmlDocument, edits: Vec<Edit> }

/// Original v1 ordered request binding, not source validation or authorization.
/// # Errors
/// Rejects empty/over-limit collections and total request text before encoding.
pub fn note_style_request_sha256(source_package_sha256: [u8; 32], requests: &[NoteStyleReplacement<'_>],
    limits: NoteHwpxLimits) -> Result<[u8; 32], E> {
    if requests.is_empty() { return Err(E::Selection); }
    if requests.len() > limits.config().notes
        || requests.len().checked_mul(16).filter(|n| *n <= PatchLimits::default().config().max_intents).is_none() {
        return Err(E::Limit);
    }
    let mut text_bytes = 0usize;
    for request in requests {
        let format = &request.values.auto_number_format;
        for text in [&format.user_character, &format.prefix_character, &format.suffix_character] {
            text_bytes = text_bytes.checked_add(text.len()).filter(|n| *n <= limits.config().text_bytes).ok_or(E::Limit)?;
        }
    }
    let mut digest = Sha256::new();
    digest.update(b"hwpx-agent.source-note-style-replacement/v1\0");
    digest.update(source_package_sha256);
    digest.update((requests.len() as u64).to_le_bytes());
    for request in requests {
        digest.update(Sha256::digest(request.style_id.as_str().as_bytes()));
        digest.update(request.source_style_sha256);
        for (_, _, value) in encoded(request.values) {
            digest.update((value.len() as u64).to_le_bytes()); digest.update(value.as_bytes());
        }
    }
    Ok(digest.finalize().into())
}

impl ImportedDocumentStructure {
    /// Lowers selected section styles, preserving all other bytes. No source
    /// overwrite, default synthesis, note-kind conversion or native renumbering.
    /// # Errors
    /// Rejects fresh-source drift, unsupported/missing styles, invalid values,
    /// duplicate/foreign/stale/no-op selections, protection and bounded failures.
    pub fn lower_note_style_batch_candidate(&self, fresh: &[u8], requests: &[NoteStyleReplacement<'_>],
        limits: NoteHwpxLimits, writer: WriterLimits) -> Result<NoteStyleCandidate, E> {
        self.lower_note_style_checked(fresh, requests, limits, writer,
            || self.verify_source(fresh).map(|_| ()).map_err(|_| E::Source))
    }
    fn lower_note_style_checked(&self, fresh: &[u8], requests: &[NoteStyleReplacement<'_>],
        limits: NoteHwpxLimits, writer: WriterLimits, check_source: impl FnOnce() -> Result<(), E>) -> Result<NoteStyleCandidate, E> {
        if requests.is_empty() { return Err(E::Selection); }
        if requests.len() > limits.config().notes
            || requests.len().checked_mul(16).filter(|n| *n <= PatchLimits::default().config().max_intents).is_none() {
            return Err(E::Limit);
        }
        check_source()?;
        self.lower_note_style_verified(fresh, requests, limits, writer)
    }
    // Non-generic compiler shared by direct source and operation-local Form proof.
    fn lower_note_style_verified(&self, fresh: &[u8], requests: &[NoteStyleReplacement<'_>],
        limits: NoteHwpxLimits, writer: WriterLimits) -> Result<NoteStyleCandidate, E> {
        let styles = self.import_note_styles(limits)?;
        let index: BTreeMap<_, _> = styles.iter().map(|s| (s.style_id(), s)).collect();
        if index.len() != styles.len() { return Err(E::Source); }
        let (mut seen, mut wanted, mut parts, mut guards) = (BTreeSet::new(), BTreeMap::new(),
            BTreeMap::<&PackagePath, PartEdits<'_>>::new(), BTreeMap::new());
        let (mut visits, mut text_bytes, mut edit_bytes) = (0usize, 0usize, 0usize);
        let mut intents = Vec::new();
        let request_sha256 = note_style_request_sha256(self.source().receipt().source_package_sha256, requests, limits)?;
        for request in requests {
            if !seen.insert(request.style_id) { return Err(E::Selection); }
            let before = index.get(request.style_id).copied().ok_or(E::Selection)?;
            if before.source_anchor().fingerprint_sha256 != request.source_style_sha256 { return Err(E::Selection); }
            validate(request.values, before.kind(), limits)?;
            // Native readback can contain UINT zero. Preserve its exact existing
            // numbering only; never infer its semantics, create it or reinterpret
            // it under a different restart mode. Full domain NoteStyle stays positive.
            if request.values.new_number == 0 && (before.values().new_number != 0
                || request.values.numbering_restart != before.values().numbering_restart) { return Err(E::Value); }
            if before.values() == request.values { return Err(E::NoChange); }
            for text in [&request.values.auto_number_format.user_character, &request.values.auto_number_format.prefix_character,
                &request.values.auto_number_format.suffix_character] {
                text_bytes = text_bytes.checked_add(text.len()).filter(|n| *n <= limits.config().text_bytes).ok_or(E::Limit)?;
            }
            let resolved = self.source().resolve_anchor(before.source_anchor()).map_err(|_| E::Selection)?;
            let part = resolved.part(); let xml = part.xml().ok_or(E::Source)?;
            if part.path() != &before.part || resolved.element_index() != Some(before.index) { return Err(E::Source); }
            if !guards.contains_key(part.path()) {
                visits = visits.checked_add(xml.elements().len().checked_mul(4).ok_or(E::Limit)?).ok_or(E::Limit)?;
                guards.insert(part.path(), (observed_protection(xml).map_err(|_| E::Protection)?,
                    subtree_protection(xml).map_err(|_| E::Protection)?));
            }
            let (ancestor, subtree) = guards.get(part.path()).ok_or(E::Source)?;
            if ancestor.get(before.index).copied().ok_or(E::Source)?
                || subtree.get(before.index).copied().ok_or(E::Source)? { return Err(E::Protection); }
            let old = encoded(before.values());
            for ((slot, name, value), (_, _, previous)) in encoded(request.values).into_iter().zip(old) {
                if value == previous { continue; } // Preserve original lexical bool/color/number forms.
                let node_index = before.children[slot];
                let (ordinal, attr) = attribute(&xml.elements()[node_index], name)?;
                let escaped = crate::patch::escape_attribute(&value, attr.quote_style()).map_err(|_| E::Value)?;
                edit_bytes = edit_bytes.checked_add(escaped.len()).filter(|n| *n <= limits.config().plan_bytes.min(limits.config().output_bytes)).ok_or(E::Limit)?;
                let span = attr.value_span();
                parts.entry(part.path()).or_insert_with(|| PartEdits { xml, edits: Vec::new() }).edits
                    .push(Edit { start: span.start(), end: span.end(), bytes: escaped.into_bytes() });
                intents.push(PatchIntent::ReplaceAttribute {
                    target: XmlAttributeSelector::bind(part.path(), xml, node_index, ordinal).map_err(|_| E::Selection)?,
                    value: PatchAttributeValue::Text(PatchText::new(&value).map_err(|_| E::Value)?),
                });
            }
            wanted.insert((before.part.clone(), before.index), request.values);
        }
        for edits in parts.values_mut() {
            edits.edits.sort_by_key(|e| e.start);
            if edits.edits.windows(2).any(|w| w[0].end > w[1].start) { return Err(E::Selection); }
            edits.edits.iter().try_fold(edits.xml.original_len(), |n, e|
                n.checked_sub(e.end - e.start).and_then(|n| n.checked_add(e.bytes.len())))
                .filter(|n| *n <= limits.config().section_bytes.min(limits.config().output_bytes)).ok_or(E::Limit)?;
        }
        let source = self.source(); let zip = source.limits.zip().map_err(|_| E::Source)?;
        let mut reader = BoundedZipReader::open(Cursor::new(fresh), zip).map_err(|_| E::Source)?;
        let patch = PreservingPatchEngine::apply_with_limits_and_preservation_profile(
            &mut reader, &source.graph, PackageGraphLimits::default(), IdRuleProfile::hwpml_2011_shape_v6(),
            IdIndexLimits::default(), PatchLimits::default(), PreservationRuleProfile::Hangul2020PreviewTextV2, &intents,
        ).map_err(|e| E::Patch(e.code()))?;
        if patch.changed_parts() != parts.len() || patch.added_parts() != 0
            || patch.parts().iter().any(|p| !parts.contains_key(p.path()) && p.source_sha256() != Some(p.output_sha256())) {
            return Err(E::Preservation);
        }
        let artifact = PreservingWriter::build(&patch, zip, PackageGraphLimits::default(), IdIndexLimits::default(), writer).map_err(|_| E::Writer)?;
        if artifact.size_bytes() > limits.config().output_bytes { return Err(E::Limit); }
        artifact.with_verified_bytes(|bytes| -> Result<(), E> {
            let imported = ImportedSourcePackage::import(bytes, source.document_id().clone(), Sha256::digest(bytes).into(), source.limits).map_err(|_| E::Readback)?;
            let output = ImportedDocumentStructure::import(imported).map_err(|_| E::Readback)?;
            let after = output.import_note_styles(limits).map_err(|_| E::Readback)?;
            if styles.len() != after.len() || self.notes().len() != output.notes().len() { return Err(E::Readback); }
            for (old, next) in styles.iter().zip(&after) {
                if old.part != next.part || old.index != next.index || old.kind() != next.kind()
                    || next.values() != wanted.get(&(old.part.clone(), old.index)).copied().unwrap_or(old.values()) {
                    return Err(E::Readback);
                }
            }
            let output_parts: BTreeMap<_, _> = output.source().parts().iter().map(|p| (p.path(), p)).collect();
            for (path, changes) in &parts {
                let next = output_parts.get(path).and_then(|p| p.xml()).ok_or(E::Readback)?;
                if !changes.xml.with_source_bytes(|old| next.with_source_bytes(|new| exact_edits(old, new, &changes.edits))) {
                    return Err(E::Preservation);
                }
            }
            Ok(())
        }).map_err(|_| E::Writer)??;
        let receipt = NoteStyleReceipt {
            profile: "hwpx-agent.source-note-style-replacement/v1", capability_id: "ref.note_style",
            source_package_sha256: source.receipt().source_package_sha256, output_package_sha256: artifact.sha256(),
            request_sha256, replaced_styles: requests.len(), total_styles_read_back: styles.len(),
            changed_attributes: intents.len(), changed_parts: parts.len(), output_bytes: artifact.size_bytes(),
            protection_element_visits: visits, only_selected_attribute_values_changed: true,
            opaque_xml_note_bodies_and_other_parts_preserved: true, complete_protection_qualified: false,
            native_layout_and_numbering_qualified: false, execution_publication_authority: false,
        };
        Ok(NoteStyleCandidate { artifact, receipt })
    }
}
impl VerifiedFormReconstruction<'_> {
    /// Uses this operation's whole Form reconstruction, never cached authority.
    /// # Errors
    /// Rejects a foreign original/proof, fresh-byte drift and compiler failures.
    pub fn lower_note_style_batch_candidate(&self, original: &ImportedDocumentForms, fresh: &[u8],
        requests: &[NoteStyleReplacement<'_>], limits: NoteHwpxLimits, writer: WriterLimits) -> Result<NoteStyleCandidate, E> {
        original.body_structure().lower_note_style_checked(fresh, requests, limits, writer, || {
            let rebuilt = self.for_original(original).map_err(|_| E::Source)?;
            if fresh != rebuilt.source().original.as_ref() { return Err(E::Source); }
            Ok(())
        })
    }
}
fn exact_edits(old: &[u8], new: &[u8], edits: &[Edit]) -> bool {
    let (mut before, mut after) = (0usize, 0usize);
    for e in edits {
        let Some(same) = old.get(before..e.start) else { return false };
        let Some(end) = after.checked_add(same.len()) else { return false };
        if new.get(after..end) != Some(same) { return false; } after = end;
        let Some(end) = after.checked_add(e.bytes.len()) else { return false };
        if new.get(after..end) != Some(e.bytes.as_slice()) { return false; }
        before = e.end; after = end;
    }
    new.get(after..) == old.get(before..)
}
