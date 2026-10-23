//! Source-bound font reference remapping used by the font replacement compiler.
//! This edits shared declarations, not a SearchScopeSelector or a platform fallback policy.
use super::{ImportedDocumentFonts, ImportedFontLanguage as Language};
use crate::{
    BoundedZipReader, IdIndexLimits, IdRuleProfile, PackageArtifact, PackageGraphLimits,
    PatchAttributeValue, PatchIntent, PatchLimits, PatchText, PreservationRuleProfile,
    PreservingPatchEngine, PreservingWriter, WriterError, WriterLimits, XmlAttributeSelector,
    document_import::{ImportedSourcePackage, fields::{ImportedDocumentFields,
        semantics::{ImportedDocumentFieldSemantics, catalog::ImportedDocumentCatalog}},
        forms::ImportedDocumentForms},
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use std::{collections::{BTreeMap, BTreeSet}, fmt, io::Cursor};
use thiserror::Error;

pub const FONT_REFERENCE_REPLACEMENT_PROFILE: &str = "hwpx-agent.source-font-reference-replacement/v1";
const MAX_MAPPINGS: usize = 128;
const MAX_CHANGES: usize = 4096;

/// IDs are local to the exact original package AND language, never platform font IDs.
#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub struct FontReferenceMapping {
    pub language: Language,
    pub from_native_id: u32,
    pub to_native_id: u32,
}
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct FontReferenceReplacementLimits {
    pub maximum_mappings: usize,
    pub maximum_reference_changes: usize,
}
impl Default for FontReferenceReplacementLimits {
    fn default() -> Self { Self { maximum_mappings: MAX_MAPPINGS, maximum_reference_changes: MAX_CHANGES } }
}
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct FontReferenceReplacementReceipt {
    pub profile: &'static str,
    pub source_package_sha256: [u8; 32],
    pub source_font_links_sha256: [u8; 32],
    pub canonical_mapping_sha256: [u8; 32],
    pub output_font_links_sha256: [u8; 32],
    pub mappings: usize,
    pub changed_references: usize,
    pub changed_character_properties: usize,
    pub output_package_sha256: [u8; 32],
    pub output_bytes: usize,
    pub font_definitions_embedding_substitutes_and_type_info_preserved: bool,
    pub outside_changed_attribute_values_exact: bool,
    pub all_seven_language_references_read_back: bool,
    pub search_scope_name_matching_platform_fallback_or_execution_qualified: bool,
    pub full_protection_native_or_service_authority: bool,
}
pub struct FontReferenceReplacementCandidate {
    artifact: PackageArtifact,
    receipt: FontReferenceReplacementReceipt,
}
impl fmt::Debug for FontReferenceReplacementCandidate {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("FontReferenceReplacementCandidate(<redacted>; shared_source_references_not_scoped_search_or_execution)")
    }
}
impl FontReferenceReplacementCandidate {
    #[must_use] pub const fn receipt(&self) -> &FontReferenceReplacementReceipt { &self.receipt }
    /// # Errors
    /// Package integrity only. Does not authorize stored access, execution or a revision commit.
    pub fn with_verified_bytes<T>(&self, consume: impl FnOnce(&[u8]) -> T) -> Result<T, WriterError> {
        self.artifact.with_verified_bytes(consume)
    }
}
#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum FontReferenceReplacementError {
    #[error("FONT_REFERENCE_REPLACEMENT_SOURCE_REJECTED")] Source,
    #[error("FONT_REFERENCE_REPLACEMENT_MAPPING_REJECTED")] Mapping,
    #[error("FONT_REFERENCE_REPLACEMENT_LIMIT")] Limit,
    #[error("FONT_REFERENCE_REPLACEMENT_NO_MATCHES")] NoMatches,
    #[error("FONT_REFERENCE_REPLACEMENT_NO_CHANGE")] NoChange,
    #[error("FONT_REFERENCE_REPLACEMENT_PROTECTION_REJECTED")] Protection,
    #[error("FONT_REFERENCE_REPLACEMENT_BINARY_RESOURCE_REJECTED")] BinaryReference,
    #[error("FONT_REFERENCE_REPLACEMENT_PATCH_REJECTED:{0}")] Patch(&'static str),
    #[error("FONT_REFERENCE_REPLACEMENT_WRITER_REJECTED")] Writer,
    #[error("FONT_REFERENCE_REPLACEMENT_READBACK_REJECTED")] Readback,
    #[error("FONT_REFERENCE_REPLACEMENT_PRESERVATION_REJECTED")] Preservation,
}
type E = FontReferenceReplacementError;
struct Change { element: usize, attribute: usize, target: u32 }

impl ImportedDocumentFonts<'_, '_, '_, '_> {
    /// Replaces actual seven-language fontRef links simultaneously, not transitively.
    /// Only already declared same-language targets are admitted. Definitions, embedded resources,
    /// substitutes, type metadata and every byte outside edited attribute VALUES remain exact.
    /// Shared character properties affect every use, including unused styles; a scoped search
    /// compiler must clone/rebind selected properties rather than treating this as a scoped edit.
    /// # Errors
    /// Rejects stale whole bytes, invalid/ambiguous mappings, finite limits and observed protection.
    pub fn lower_reference_replacement_candidate(
        &self, fresh: &[u8], mappings: &[FontReferenceMapping],
        limits: FontReferenceReplacementLimits, writer: WriterLimits,
    ) -> Result<FontReferenceReplacementCandidate, E> {
        validate_limits(mappings, limits)?;
        let source = self.catalog.meanings.fields.forms.source();
        // All inputs to this non-deserializable immutable import are private. Compare the complete
        // fresh original once; do not recursively reconstruct its form/field/catalog graph again.
        if fresh != source.original.as_ref() { return Err(E::Source); }
        let declared: BTreeMap<_, _> = self.definitions.iter()
            .map(|d| ((d.language, d.declared.id), &d.font_id)).collect();
        let mut by_source = BTreeMap::new();
        for mapping in mappings {
            if mapping.from_native_id == mapping.to_native_id { return Err(E::NoChange); }
            if !declared.contains_key(&(mapping.language, mapping.from_native_id))
                || !declared.contains_key(&(mapping.language, mapping.to_native_id))
                || by_source.insert((mapping.language, mapping.from_native_id), mapping.to_native_id).is_some()
            { return Err(E::Mapping); }
        }
        let protection = source.observe_protection_signals().map_err(|_| E::Protection)?;
        protection.require_no_observed_document_signals().map_err(|_| E::Protection)?;
        // A shared property may affect a locked use anywhere in the document. No caller-provided
        // Unprotected flag may bypass this conservative global-edit boundary.
        if protection.counts().local_blocked_elements != 0 { return Err(E::Protection); }
        require_binary_resources(self)?;
        let native_by_logical: BTreeMap<_, _> = self.definitions.iter()
            .map(|d| (&d.font_id, (d.language, d.declared.id))).collect();
        let header = source.parts().iter().find(|p| p.path().as_str() == "Contents/header.xml").ok_or(E::Source)?;
        let xml = header.xml().ok_or(E::Source)?;
        let mut changes = Vec::new();
        let mut changed_properties = BTreeSet::new();
        for link in &self.links {
            let &(language, old) = native_by_logical.get(&link.font_id).ok_or(E::Mapping)?;
            if language != link.language { return Err(E::Mapping); }
            let Some(&target) = by_source.get(&(language, old)) else { continue; };
            if changes.len() >= limits.maximum_reference_changes { return Err(E::Limit); }
            let resolved = source.resolve_anchor(&link.font_reference_anchor).map_err(|_| E::Source)?;
            if resolved.part().path() != header.path() { return Err(E::Source); }
            let element = resolved.element_index().ok_or(E::Source)?;
            let attribute = xml.elements()[element].attributes().iter().position(|a|
                a.name().namespace().is_none() && a.name().local_name() == language.name()).ok_or(E::Source)?;
            changes.push(Change { element, attribute, target });
            changed_properties.insert(&link.character_property_id);
        }
        if changes.is_empty() { return Err(E::NoMatches); }
        changes.sort_by_key(|c| xml.elements()[c.element].attributes()[c.attribute].value_span().start());
        let mut previous_end = 0;
        let mut intents = Vec::with_capacity(changes.len());
        for c in &changes {
            let span = xml.elements()[c.element].attributes()[c.attribute].value_span();
            if span.start() < previous_end { return Err(E::Mapping); }
            previous_end = span.end();
            intents.push(PatchIntent::ReplaceAttribute {
                target: XmlAttributeSelector::bind(header.path(), xml, c.element, c.attribute).map_err(|error| E::Patch(error.code()))?,
                value: PatchAttributeValue::Text(PatchText::new(&c.target.to_string()).map_err(|error| E::Patch(error.code()))?),
            });
        }
        let zip = source.limits.zip().map_err(|_| E::Source)?;
        let mut reader = BoundedZipReader::open(Cursor::new(fresh), zip).map_err(|_| E::Source)?;
        let patch = PreservingPatchEngine::apply_with_limits_and_preservation_profile(
            &mut reader, &source.graph, PackageGraphLimits::default(), IdRuleProfile::hwpml_2011_font_binary_v10(),
            IdIndexLimits::default(), PatchLimits::default(), PreservationRuleProfile::Hangul2020PreviewTextV2, &intents,
        ).map_err(|error| E::Patch(error.code()))?;
        if patch.changed_parts() != 1 || patch.added_parts() != 0 || patch.parts().iter().any(|p|
            p.path() != header.path() && p.source_sha256() != Some(p.output_sha256())) { return Err(E::Preservation); }
        let artifact = PreservingWriter::build(&patch, zip, PackageGraphLimits::default(),
            IdIndexLimits::default(), writer).map_err(|_| E::Writer)?;
        let output_links = artifact.with_verified_bytes(|bytes| readback(self, bytes, &changes, &by_source))
            .map_err(|_| E::Writer)??;
        let canonical: Vec<_> = by_source.iter().map(|(&(language, from_native_id), &to_native_id)|
            FontReferenceMapping { language, from_native_id, to_native_id }).collect();
        let request = serde_json::to_vec(&(FONT_REFERENCE_REPLACEMENT_PROFILE, self.receipt(), canonical)).map_err(|_| E::Limit)?;
        let receipt = FontReferenceReplacementReceipt {
            profile: FONT_REFERENCE_REPLACEMENT_PROFILE, source_package_sha256: self.receipt.source_package_sha256,
            source_font_links_sha256: self.receipt.source_links_sha256, canonical_mapping_sha256: Sha256::digest(&request).into(),
            output_font_links_sha256: output_links, mappings: by_source.len(), changed_references: changes.len(),
            changed_character_properties: changed_properties.len(), output_package_sha256: artifact.sha256(), output_bytes: artifact.size_bytes(),
            font_definitions_embedding_substitutes_and_type_info_preserved: true, outside_changed_attribute_values_exact: true,
            all_seven_language_references_read_back: true,
            search_scope_name_matching_platform_fallback_or_execution_qualified: false, full_protection_native_or_service_authority: false,
        };
        Ok(FontReferenceReplacementCandidate { artifact, receipt })
    }
}
fn validate_limits(mappings: &[FontReferenceMapping], limits: FontReferenceReplacementLimits) -> Result<(), E> {
    if limits.maximum_mappings == 0 || limits.maximum_mappings > MAX_MAPPINGS
        || limits.maximum_reference_changes == 0 || limits.maximum_reference_changes > MAX_CHANGES
        || limits.maximum_reference_changes > PatchLimits::default().config().max_intents
        || mappings.is_empty() || mappings.len() > limits.maximum_mappings { return Err(E::Limit); }
    Ok(())
}
pub(in crate::document_import) fn require_binary_resources(fonts: &ImportedDocumentFonts<'_, '_, '_, '_>) -> Result<(), E> {
    use crate::graph::{PartRole, RelationshipKind};
    let source = fonts.catalog.meanings.fields.forms.source();
    // Build each immutable graph index once, not once per font or language link.
    let parts: BTreeMap<_, _> = source.graph.parts.iter().map(|p| (&p.path,p)).collect();
    let admitted_parts: BTreeMap<_, _> = source.parts().iter().map(|p| (p.path(),p)).collect();
    let mut manifest = BTreeMap::new();
    for r in source.graph.relationships.iter().filter(|r| r.kind == RelationshipKind::ManifestItem) {
        if manifest.insert(r.id.as_str(),r).is_some() { return Err(E::BinaryReference); }
    }
    for d in fonts.definitions() {
        for id in [d.declared.binary_item_id_ref.as_deref(),
            d.declared.substitute.as_ref().and_then(|s| s.binary_item_id_ref.as_deref())].into_iter().flatten() {
            let relationship = manifest.get(id).ok_or(E::BinaryReference)?;
            let part = parts.get(&relationship.target).ok_or(E::BinaryReference)?;
            let admitted = admitted_parts.get(&relationship.target).ok_or(E::BinaryReference)?;
            if part.role != PartRole::ManifestListed || part.path == source.graph.package_document
                || admitted.xml().is_some() || part.media_type.as_str().starts_with("text/")
                || part.expanded_size == 0 { return Err(E::BinaryReference); }
        }
    }
    // References are present in a closed binary source graph. No font parser, installation,
    // platform fallback, license assertion or payload activation is implied.
    Ok(())
}
fn readback(
    before: &ImportedDocumentFonts<'_, '_, '_, '_>, bytes: &[u8], changes: &[Change],
    mapping: &BTreeMap<(Language, u32), u32>,
) -> Result<[u8; 32], E> {
    let source = before.catalog.meanings.fields.forms.source();
    let output = ImportedSourcePackage::import(bytes, source.document_id().clone(), Sha256::digest(bytes).into(), source.limits).map_err(|_| E::Readback)?;
    let forms = ImportedDocumentForms::import(output).map_err(|_| E::Readback)?;
    let fields = ImportedDocumentFields::import(&forms).map_err(|_| E::Readback)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields).map_err(|_| E::Readback)?;
    let catalog = ImportedDocumentCatalog::import(&meanings).map_err(|_| E::Readback)?;
    let fonts = ImportedDocumentFonts::import(&catalog).map_err(|_| E::Readback)?;
    if before.definitions.len() != fonts.definitions.len() || before.definitions.iter().zip(&fonts.definitions)
        .any(|(a,b)| a.language != b.language || a.declared != b.declared) { return Err(E::Readback); }
    let mut expected = before.catalog.character_catalog().clone();
    for style in &mut expected.styles {
        for (language, value) in [
            (Language::Hangul, &mut style.font_refs.hangul), (Language::Latin, &mut style.font_refs.latin),
            (Language::Hanja, &mut style.font_refs.hanja), (Language::Japanese, &mut style.font_refs.japanese),
            (Language::Other, &mut style.font_refs.other), (Language::Symbol, &mut style.font_refs.symbol),
            (Language::User, &mut style.font_refs.user),
        ] { if let Some(target) = mapping.get(&(language, *value)) { *value = *target; } }
    }
    if expected != *catalog.character_catalog() { return Err(E::Readback); }
    let a = source.parts().iter().find(|p| p.path().as_str() == "Contents/header.xml").and_then(|p| p.xml()).ok_or(E::Readback)?;
    let b = forms.source().parts().iter().find(|p| p.path().as_str() == "Contents/header.xml").and_then(|p| p.xml()).ok_or(E::Readback)?;
    if a.elements().len() != b.elements().len() { return Err(E::Preservation); }
    let (mut left, mut right) = (0, 0);
    for c in changes {
        let original = &a.elements()[c.element].attributes()[c.attribute];
        let output = b.elements().get(c.element).and_then(|n| n.attributes().get(c.attribute)).ok_or(E::Readback)?;
        let (x,y) = (original.value_span(), output.value_span());
        if original.name() != output.name() || output.semantic_value() != c.target.to_string()
            || !a.with_source_bytes(|a| b.with_source_bytes(|b| a.get(left..x.start()) == b.get(right..y.start())))
        { return Err(E::Preservation); }
        (left,right) = (x.end(),y.end());
    }
    if !a.with_source_bytes(|a| b.with_source_bytes(|b| a.get(left..) == b.get(right..))) { return Err(E::Preservation); }
    Ok(fonts.receipt.source_links_sha256)
}
