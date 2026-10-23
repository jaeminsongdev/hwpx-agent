//! Source-bound batch REF-024 lowering. Not numbering, native or service authority.
use super::{ImportedDocumentStructure, caption_text_batch::observed_protection};
use crate::{
    BoundedZipReader, IdIndexLimits, IdRuleProfile, NoteHwpxLimits, PackageArtifact,
    PackageGraphLimits, PackagePath, PatchIntent, PatchLimits, PreservationRuleProfile,
    PreservingPatchEngine, PreservingWriter, PreservingXmlDocument, WriterError,
    WriterLimits, XmlElementSelector,
    document_import::{ImportedSourcePackage, forms::{ImportedDocumentForms, VerifiedFormReconstruction}},
    patch::note_kind::{NoteNameEdit, source_edits},
};
use domain_ir::{LogicalId, NoteKind};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use std::{collections::{BTreeMap, BTreeSet}, fmt, io::Cursor};
use thiserror::Error;

pub struct NoteKindConversion<'a> {
    pub note_id: &'a LogicalId,
    pub source_note_sha256: [u8; 32],
    pub target_kind: NoteKind,
}
impl fmt::Debug for NoteKindConversion<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("NoteKindConversion(<redacted>)")
    }
}
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct NoteKindConversionReceipt {
    pub profile: &'static str,
    pub capability_id: &'static str,
    pub source_package_sha256: [u8; 32],
    pub output_package_sha256: [u8; 32],
    pub request_sha256: [u8; 32],
    pub converted_notes: usize,
    pub total_notes_read_back: usize,
    pub changed_parts: usize,
    pub output_bytes: usize,
    pub protection_element_visits: usize,
    pub only_selected_note_names_changed: bool,
    pub body_marker_attributes_and_other_parts_preserved: bool,
    pub complete_protection_qualified: bool,
    pub native_number_recalculation_qualified: bool,
    pub execution_publication_authority: bool,
}
pub struct NoteKindConversionCandidate {
    artifact: PackageArtifact,
    receipt: NoteKindConversionReceipt,
}
impl fmt::Debug for NoteKindConversionCandidate {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("NoteKindConversionCandidate(<redacted>; not_native_or_authority)")
    }
}
impl NoteKindConversionCandidate {
    #[must_use]
    pub const fn receipt(&self) -> &NoteKindConversionReceipt { &self.receipt }
    /// Writer integrity only; not a service grant or publication permission.
    /// # Errors
    /// Rejects writer artifact integrity failures.
    pub fn with_verified_bytes<T>(&self, consume: impl FnOnce(&[u8]) -> T) -> Result<T, WriterError> {
        self.artifact.with_verified_bytes(consume)
    }
}
#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum NoteKindConversionError {
    #[error("NOTE_CONVERSION_SOURCE_REJECTED")] Source,
    #[error("NOTE_CONVERSION_SELECTION_REJECTED")] Selection,
    #[error("NOTE_CONVERSION_NO_CHANGE")] NoChange,
    #[error("NOTE_CONVERSION_OBSERVED_PROTECTION")] Protection,
    #[error("NOTE_CONVERSION_FINITE_LIMIT")] Limit,
    #[error("NOTE_CONVERSION_PATCH_REJECTED:{0}")] Patch(&'static str),
    #[error("NOTE_CONVERSION_WRITER_REJECTED")] Writer,
    #[error("NOTE_CONVERSION_READBACK_REJECTED")] Readback,
    #[error("NOTE_CONVERSION_PRESERVATION_REJECTED")] Preservation,
}
type E = NoteKindConversionError;
struct PartChanges<'a> { xml: &'a PreservingXmlDocument, edits: Vec<NoteNameEdit> }

/// Original ordered request digest, not source verification or an access grant.
/// # Errors
/// Rejects empty and over-limit request collections before hashing them.
pub fn note_kind_conversion_request_sha256(
    source_package_sha256: [u8; 32], requests: &[NoteKindConversion<'_>], limits: NoteHwpxLimits,
) -> Result<[u8; 32], E> {
    if requests.is_empty() { return Err(E::Selection); }
    if requests.len() > limits.config().notes.min(PatchLimits::default().config().max_intents) { return Err(E::Limit); }
    let mut binding = Sha256::new();
    binding.update(b"hwpx-agent.source-note-kind-conversion/v1\0");
    binding.update(source_package_sha256);
    binding.update((requests.len() as u64).to_le_bytes());
    for request in requests {
        binding.update(Sha256::digest(request.note_id.as_str().as_bytes()));
        binding.update(request.source_note_sha256);
        binding.update([u8::from(request.target_kind == NoteKind::Endnote)]);
    }
    Ok(binding.finalize().into())
}

impl ImportedDocumentStructure {
    /// Atomically converts selected actual source notes in memory. No raw XML,
    /// numeric-ID selector, source overwrite, native defaults or renumbering.
    /// # Errors
    /// Rejects source drift, foreign/duplicate/stale/no-op selections, observed
    /// protection, finite limits, and any patch/writer/full readback drift.
    pub fn lower_note_kind_batch_candidate(
        &self, fresh: &[u8], requests: &[NoteKindConversion<'_>],
        limits: NoteHwpxLimits, writer: WriterLimits,
    ) -> Result<NoteKindConversionCandidate, E> {
        self.lower_note_kind_checked(fresh, requests, limits, writer,
            || self.verify_source(fresh).map(|_| ()).map_err(|_| E::Source))
    }
    fn lower_note_kind_checked(
        &self, fresh: &[u8], requests: &[NoteKindConversion<'_>],
        limits: NoteHwpxLimits, writer: WriterLimits,
        check_source: impl FnOnce() -> Result<(), E>,
    ) -> Result<NoteKindConversionCandidate, E> {
        if requests.is_empty() { return Err(E::Selection); }
        if requests.len() > limits.config().notes.min(PatchLimits::default().config().max_intents)
            || self.notes().len() > limits.config().notes { return Err(E::Limit); }
        check_source()?;
        self.lower_note_kind_verified(fresh, requests, limits, writer)
    }
    // One non-generic compiler, one whole-package transaction and one output
    // import per batch; no full XML/protection scan for every selected note.
    fn lower_note_kind_verified(
        &self, fresh: &[u8], requests: &[NoteKindConversion<'_>],
        limits: NoteHwpxLimits, writer: WriterLimits,
    ) -> Result<NoteKindConversionCandidate, E> {
        let source = self.source();
        let index: BTreeMap<_, _> = self.notes().iter().map(|n| (&n.note_id, n)).collect();
        if index.len() != self.notes().len() { return Err(E::Source); }
        let mut seen = BTreeSet::new();
        let mut wanted = BTreeMap::new();
        let mut parts = BTreeMap::<&PackagePath, PartChanges<'_>>::new();
        let mut protection = BTreeMap::new();
        let mut protection_element_visits = 0usize;
        let mut intents = Vec::new();
        let request_sha256 = note_kind_conversion_request_sha256(source.receipt().source_package_sha256, requests, limits)?;
        for request in requests {
            if !seen.insert(request.note_id) { return Err(E::Selection); }
            let note = *index.get(request.note_id).ok_or(E::Selection)?;
            if note.source_anchor.fingerprint_sha256 != request.source_note_sha256 {
                return Err(E::Selection);
            }
            let kind = match request.target_kind { NoteKind::Footnote => "footNote", NoteKind::Endnote => "endNote" };
            if note.native_kind == kind { return Err(E::NoChange); }
            let selected = source.resolve_anchor(&note.source_anchor).map_err(|_| E::Selection)?;
            let part = selected.part();
            let xml = part.xml().ok_or(E::Selection)?;
            let element = selected.element_index().ok_or(E::Selection)?;
            if xml.original_len() > limits.config().section_bytes { return Err(E::Limit); }
            if !protection.contains_key(part.path()) {
                protection_element_visits = protection_element_visits.checked_add(
                    xml.elements().len().checked_mul(2).ok_or(E::Limit)?).ok_or(E::Limit)?;
                protection.insert(part.path(), observed_protection(xml).map_err(|_| E::Protection)?);
            }
            if protection.get(part.path()).and_then(|p| p.get(element)).copied().ok_or(E::Source)? {
                return Err(E::Protection);
            }
            let edits = source_edits(xml, element, request.target_kind).map_err(|_| E::Selection)?;
            parts.entry(part.path()).or_insert_with(|| PartChanges { xml, edits: vec![] }).edits.extend(edits);
            wanted.insert((part.path().clone(), element), kind);
            intents.push(PatchIntent::ConvertNoteKind {
                target: XmlElementSelector::bind(part.path(), xml, element).map_err(|_| E::Selection)?,
                kind: request.target_kind,
            });
        }
        for part in parts.values_mut() {
            part.edits.sort_by_key(|e| e.start);
            if part.edits.windows(2).any(|w| w[0].end > w[1].start) { return Err(E::Selection); }
            part.edits.iter().try_fold(part.xml.original_len(), |n, e|
                n.checked_sub(e.end - e.start).and_then(|n| n.checked_add(e.bytes.len())))
                .filter(|n| *n <= limits.config().output_bytes).ok_or(E::Limit)?;
        }
        let zip = source.limits.zip().map_err(|_| E::Source)?;
        let mut reader = BoundedZipReader::open(Cursor::new(fresh), zip).map_err(|_| E::Source)?;
        let patch = PreservingPatchEngine::apply_with_limits_and_preservation_profile(
            &mut reader, &source.graph, PackageGraphLimits::default(), IdRuleProfile::hwpml_2011_shape_v6(),
            IdIndexLimits::default(), PatchLimits::default(), PreservationRuleProfile::Hangul2020PreviewTextV2,
            &intents,
        ).map_err(|e| {
            let code = if let crate::PatchError::IdIndex(ref ids) = e {
                ids.validation().and_then(|r| r.issues().first()).map_or(e.code(), |i| i.code())
            } else { e.code() };
            E::Patch(code)
        })?;
        if patch.changed_parts() != parts.len() || patch.added_parts() != 0
            || patch.parts().iter().any(|p| !parts.contains_key(p.path()) && p.source_sha256() != Some(p.output_sha256())) {
            return Err(E::Preservation);
        }
        let artifact = PreservingWriter::build(&patch, zip, PackageGraphLimits::default(),
            IdIndexLimits::default(), writer).map_err(|_| E::Writer)?;
        if artifact.size_bytes() > limits.config().output_bytes { return Err(E::Limit); }
        artifact.with_verified_bytes(|bytes| -> Result<(), E> {
            let imported = ImportedSourcePackage::import(bytes, source.document_id().clone(),
                Sha256::digest(bytes).into(), source.limits).map_err(|_| E::Readback)?;
            let output = ImportedDocumentStructure::import(imported).map_err(|_| E::Readback)?;
            if output.notes().len() != self.notes().len() { return Err(E::Readback); }
            // XML element topology is unchanged. Compare actual source positions,
            // not native instId (which can legitimately collide) or regenerated IDs.
            for (before, after) in self.notes().iter().zip(output.notes()) {
                let old = source.resolve_anchor(&before.source_anchor).map_err(|_| E::Readback)?;
                let new = output.source().resolve_anchor(&after.source_anchor).map_err(|_| E::Readback)?;
                let old_index = old.element_index().ok_or(E::Readback)?;
                if new.part().path() != old.part().path() || new.element_index() != Some(old_index)
                    || before.native_attributes != after.native_attributes
                    || before.native_instance_id != after.native_instance_id
                    || after.native_kind != wanted.get(&(old.part().path().clone(), old_index)).copied().unwrap_or(before.native_kind.as_str()) {
                    return Err(E::Readback);
                }
            }
            let output_parts: BTreeMap<_, _> = output.source().parts().iter().map(|p| (p.path(), p)).collect();
            for (path, changes) in &parts {
                let next = output_parts.get(path).and_then(|p| p.xml()).ok_or(E::Readback)?;
                if !changes.xml.with_source_bytes(|old| next.with_source_bytes(|new| exact_names(old, new, &changes.edits))) {
                    return Err(E::Preservation);
                }
            }
            Ok(())
        }).map_err(|_| E::Writer)??;
        let receipt = NoteKindConversionReceipt {
            profile: "hwpx-agent.source-note-kind-conversion/v1", capability_id: "ref.note_convert",
            source_package_sha256: source.receipt().source_package_sha256,
            output_package_sha256: artifact.sha256(), request_sha256,
            converted_notes: requests.len(), total_notes_read_back: self.notes().len(), changed_parts: parts.len(),
            output_bytes: artifact.size_bytes(), protection_element_visits,
            only_selected_note_names_changed: true, body_marker_attributes_and_other_parts_preserved: true,
            complete_protection_qualified: false, native_number_recalculation_qualified: false,
            execution_publication_authority: false,
        };
        Ok(NoteKindConversionCandidate { artifact, receipt })
    }
}
impl VerifiedFormReconstruction<'_> {
    /// Uses the original operation-local reconstruction; never cached service authority.
    /// # Errors
    /// Rejects a foreign proof, fresh-byte drift and all original compiler errors.
    pub fn lower_note_kind_batch_candidate(
        &self, original: &ImportedDocumentForms, fresh: &[u8], requests: &[NoteKindConversion<'_>],
        limits: NoteHwpxLimits, writer: WriterLimits,
    ) -> Result<NoteKindConversionCandidate, E> {
        original.body_structure().lower_note_kind_checked(fresh, requests, limits, writer, || {
            let rebuilt = self.for_original(original).map_err(|_| E::Source)?;
            if fresh != rebuilt.source().original.as_ref() { return Err(E::Source); }
            Ok(())
        })
    }
}
fn exact_names(old: &[u8], new: &[u8], edits: &[NoteNameEdit]) -> bool {
    let (mut before, mut after) = (0usize, 0usize);
    for edit in edits {
        let Some(same) = old.get(before..edit.start) else { return false };
        let Some(end) = after.checked_add(same.len()) else { return false };
        if new.get(after..end) != Some(same) { return false; }
        after = end;
        let Some(end) = after.checked_add(edit.bytes.len()) else { return false };
        if new.get(after..end) != Some(edit.bytes.as_slice()) { return false; }
        before = edit.end; after = end;
    }
    new.get(after..) == old.get(before..)
}
