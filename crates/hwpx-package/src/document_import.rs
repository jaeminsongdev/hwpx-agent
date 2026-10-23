//! Actual package-backed source import for the whole-document importer.
//!
//! No caller-supplied graph, native IDs or semantic defaults are accepted here.
//! Every part is retained in the immutable archive; every admitted XML element
//! receives a document/package/part/span-bound anchor. This is the source stage,
//! NOT a complete typed `DocumentGraph`, security attestation or execution permit.
use std::{collections::BTreeMap, fmt, io::Cursor};

use domain_ir::{DocumentId, LogicalId, SourceAnchorHandle};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{
    BoundedZipReader, PackageGraph, PackageGraphLimits, PackageLimitConfig, PackageLimits,
    PackagePath, PartRole, PreservationClass, PreservationReport, PreservationRuleProfile,
    PreservingXmlDocument, XmlByteSpan, XmlElementToken,
};

pub const SOURCE_IMPORT_PROFILE: &str = "hwpx-agent.document-import-source/v1";

pub mod fields;
pub mod forms;
pub mod protection;
pub mod reference_targets;
pub mod search;
pub mod structure;

type AnchorIndex = BTreeMap<LogicalId, (usize, Option<usize>)>;
type BuiltSource = (Vec<ImportedSourcePart>, AnchorIndex, SourceImportReceipt);

/// Caller bounds may only tighten this source-import admission profile.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct SourceImportLimitConfig {
    pub archive_bytes: usize,
    pub expanded_bytes: usize,
    pub parts: usize,
    pub xml_elements: usize,
    pub xml_tokens: usize,
    /// Bounds overlapping subtree hashing too, not just unique XML input bytes.
    pub fingerprint_bytes: usize,
}

impl Default for SourceImportLimitConfig {
    fn default() -> Self {
        Self {
            archive_bytes: 32 * 1024 * 1024,
            expanded_bytes: 16 * 1024 * 1024,
            parts: 256,
            xml_elements: 100_000,
            xml_tokens: 200_000,
            fingerprint_bytes: 256 * 1024 * 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct SourceImportLimits(SourceImportLimitConfig);

impl SourceImportLimits {
    /// # Errors
    /// Rejects zero and above-profile bounds without silently clamping them.
    pub fn new(config: SourceImportLimitConfig) -> Result<Self, SourceImportError> {
        let ceiling = SourceImportLimitConfig::default();
        let pairs = [
            (config.archive_bytes, ceiling.archive_bytes),
            (config.expanded_bytes, ceiling.expanded_bytes),
            (config.parts, ceiling.parts),
            (config.xml_elements, ceiling.xml_elements),
            (config.xml_tokens, ceiling.xml_tokens),
            (config.fingerprint_bytes, ceiling.fingerprint_bytes),
        ];
        if pairs.iter().any(|(value, max)| *value == 0 || value > max) {
            return Err(SourceImportError::Limit);
        }
        Ok(Self(config))
    }

    fn zip(self) -> Result<PackageLimits, SourceImportError> {
        PackageLimits::new(PackageLimitConfig {
            max_archive_bytes: self.0.archive_bytes as u64,
            max_entries: self.0.parts,
            max_entry_expanded_bytes: (2 * 1024 * 1024).min(self.0.expanded_bytes) as u64,
            max_total_expanded_bytes: self.0.expanded_bytes as u64,
            ..PackageLimitConfig::default()
        })
        .map_err(|_| SourceImportError::Limit)
    }
}

/// Private immutable provenance index. Debug never reveals paths, names or values.
#[derive(Eq, PartialEq)]
pub struct ImportedSourcePackage {
    document_id: DocumentId,
    source_sha256: [u8; 32],
    original: Box<[u8]>,
    graph: PackageGraph,
    parts: Vec<ImportedSourcePart>,
    anchors: AnchorIndex,
    limits: SourceImportLimits,
    receipt: SourceImportReceipt,
}

impl fmt::Debug for ImportedSourcePackage {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("ImportedSourcePackage")
            .field("parts", &self.parts.len())
            .field("xml_elements", &self.receipt.xml_elements)
            .finish_non_exhaustive()
    }
}

#[derive(Eq, PartialEq)]
pub struct ImportedSourcePart {
    path: PackagePath,
    role: PartRole,
    anchor: SourceAnchorHandle,
    xml: Option<PreservingXmlDocument>,
    element_anchors: Vec<SourceAnchorHandle>,
}

impl fmt::Debug for ImportedSourcePart {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("ImportedSourcePart")
            .field("xml_elements", &self.element_anchors.len())
            .finish_non_exhaustive()
    }
}

impl ImportedSourcePart {
    #[must_use]
    pub const fn path(&self) -> &PackagePath {
        &self.path
    }
    #[must_use]
    pub const fn role(&self) -> PartRole {
        self.role
    }
    #[must_use]
    pub const fn anchor(&self) -> &SourceAnchorHandle {
        &self.anchor
    }
    #[must_use]
    pub const fn xml(&self) -> Option<&PreservingXmlDocument> {
        self.xml.as_ref()
    }
    #[must_use]
    pub fn element_anchor(&self, element: usize) -> Option<&SourceAnchorHandle> {
        self.element_anchors.get(element)
    }
}

/// A checked location, never a raw XML string or an editable caller locator.
pub struct ResolvedSourceAnchor<'a> {
    part: &'a ImportedSourcePart,
    element_index: Option<usize>,
}

impl fmt::Debug for ResolvedSourceAnchor<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ResolvedSourceAnchor(<redacted>)")
    }
}

impl<'a> ResolvedSourceAnchor<'a> {
    #[must_use]
    pub const fn part(&self) -> &'a ImportedSourcePart {
        self.part
    }
    #[must_use]
    pub const fn element_index(&self) -> Option<usize> {
        self.element_index
    }
    #[must_use]
    pub fn element(&self) -> Option<&'a XmlElementToken> {
        self.part.xml.as_ref()?.elements().get(self.element_index?)
    }
}

/// Closed source-stage evidence. No boolean promises typed/native/Gate acceptance.
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct SourceImportReceipt {
    pub profile: &'static str,
    pub qualification: &'static str,
    pub source_package_sha256: [u8; 32],
    pub provenance_sha256: [u8; 32],
    pub package_bytes: usize,
    pub expanded_bytes: u64,
    pub parts: usize,
    pub xml_parts: usize,
    pub xml_elements: usize,
    pub xml_tokens: usize,
    pub fingerprint_bytes: usize,
}

impl ImportedSourcePackage {
    /// Imports the actual closed package and checks all preservation classes.
    /// IDs identify THIS source version only; they are not native or persistent
    /// cross-revision logical IDs. The caller must supply the admitted package SHA.
    /// # Errors
    /// Fails on source drift, ZIP/closure/media/XML rejection, aggregate budget
    /// exhaustion or inconsistent source topology. It never falls back to opaque
    /// for unsafe XML and never extracts or executes content.
    pub fn import(
        source: &[u8],
        document_id: DocumentId,
        expected_sha256: [u8; 32],
        limits: SourceImportLimits,
    ) -> Result<Self, SourceImportError> {
        // One import call only: fresh ZIP/CRC/digest/profile/round-trip checks
        // still run. Move an already parsed model only after exact fresh bytes
        // match; no source read, service authorization or cross-call cache.
        let mut documents = crate::call_local_xml::CallLocalXmlDocuments::default();
        Self::import_with_documents(
            source,
            document_id,
            expected_sha256,
            limits,
            Some(&mut documents),
        )
    }

    fn import_with_documents(
        source: &[u8],
        document_id: DocumentId,
        expected_sha256: [u8; 32],
        limits: SourceImportLimits,
        mut documents: Option<&mut crate::call_local_xml::CallLocalXmlDocuments>,
    ) -> Result<Self, SourceImportError> {
        if source.len() > limits.0.archive_bytes {
            return Err(SourceImportError::Limit);
        }
        if <[u8; 32]>::from(Sha256::digest(source)) != expected_sha256 {
            return Err(SourceImportError::SourceChanged);
        }
        let mut reader = BoundedZipReader::open(Cursor::new(source), limits.zip()?)
            .map_err(|_| SourceImportError::Package)?;
        let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())
            .map_err(|_| SourceImportError::Graph)?;
        let preservation = match documents.as_deref_mut() {
            Some(documents) => PreservationReport::build_with_call_local_xml(
                &mut reader,
                &graph,
                PackageGraphLimits::default(),
                PreservationRuleProfile::Hangul2020PreviewTextV2,
                documents,
            ),
            None => PreservationReport::build_with_profile(
                &mut reader,
                &graph,
                PreservationRuleProfile::Hangul2020PreviewTextV2,
            ),
        }
        .map_err(|_| SourceImportError::Preservation)?;
        if !preservation.direct_preserve_ready() {
            return Err(SourceImportError::RejectedPart);
        }
        let mut builder = ImportBuilder::new(&document_id, expected_sha256, limits);
        for record in preservation.parts() {
            let bytes = reader
                .read_entry(record.source_entry_index())
                .map_err(|_| SourceImportError::Package)?;
            if bytes.len() as u64 != record.expanded_size()
                || <[u8; 32]>::from(Sha256::digest(&bytes)) != record.raw_sha256()
            {
                return Err(SourceImportError::SourceChanged);
            }
            builder.part(
                record.path(),
                record.role(),
                record.class(),
                &bytes,
                documents.as_deref_mut(),
            )?;
        }
        let (parts, anchors, receipt) = builder.finish(source.len());
        let mut original = Vec::new();
        original
            .try_reserve_exact(source.len())
            .map_err(|_| SourceImportError::Allocation)?;
        original.extend_from_slice(source);
        Ok(Self {
            document_id,
            source_sha256: expected_sha256,
            original: original.into_boxed_slice(),
            graph,
            parts,
            anchors,
            limits,
            receipt,
        })
    }

    #[must_use]
    pub const fn document_id(&self) -> &DocumentId {
        &self.document_id
    }
    #[must_use]
    pub const fn receipt(&self) -> &SourceImportReceipt {
        &self.receipt
    }
    #[must_use]
    pub fn parts(&self) -> &[ImportedSourcePart] {
        &self.parts
    }
    #[must_use]
    pub fn spine(&self) -> &[PackagePath] {
        &self.graph.spine
    }

    /// Resolves only anchors actually generated from this immutable source.
    /// # Errors
    /// Rejects forged fingerprints/handles and other document/package versions.
    pub fn resolve_anchor(
        &self,
        anchor: &SourceAnchorHandle,
    ) -> Result<ResolvedSourceAnchor<'_>, SourceImportError> {
        let &(part_index, element_index) = self
            .anchors
            .get(&anchor.opaque_handle)
            .ok_or(SourceImportError::Anchor)?;
        let part = self
            .parts
            .get(part_index)
            .ok_or(SourceImportError::Anchor)?;
        let expected = match element_index {
            Some(index) => part
                .element_anchor(index)
                .ok_or(SourceImportError::Anchor)?,
            None => &part.anchor,
        };
        if expected != anchor {
            return Err(SourceImportError::Anchor);
        }
        Ok(ResolvedSourceAnchor {
            part,
            element_index,
        })
    }

    /// Fully reimports a fresh source and compares bytes, topology and all anchors.
    /// This is not merely a stored metadata or hash-only replay.
    /// # Errors
    /// Returns a closed source-stage error for changed or inadmissible source.
    pub fn verify_source(&self, fresh: &[u8]) -> Result<SourceImportReceipt, SourceImportError> {
        let rebuilt = Self::import(
            fresh,
            self.document_id.clone(),
            self.source_sha256,
            self.limits,
        )?;
        if &rebuilt != self {
            return Err(SourceImportError::SourceChanged);
        }
        Ok(rebuilt.receipt)
    }
}

struct ImportBuilder<'a> {
    document: &'a DocumentId,
    package: [u8; 32],
    limits: SourceImportLimits,
    parts: Vec<ImportedSourcePart>,
    anchors: AnchorIndex,
    receipt: SourceImportReceipt,
    provenance: Sha256,
}

impl<'a> ImportBuilder<'a> {
    fn new(document: &'a DocumentId, package: [u8; 32], limits: SourceImportLimits) -> Self {
        let mut provenance = Sha256::new();
        frame(&mut provenance, SOURCE_IMPORT_PROFILE.as_bytes());
        frame(&mut provenance, document.as_str().as_bytes());
        frame(&mut provenance, &package);
        Self {
            document,
            package,
            limits,
            parts: vec![],
            anchors: BTreeMap::new(),
            provenance,
            receipt: SourceImportReceipt {
                profile: SOURCE_IMPORT_PROFILE,
                qualification: "whole_package_source_only_typed_ir_security_lineage_route_native_gate_unqualified",
                source_package_sha256: package,
                provenance_sha256: [0; 32],
                package_bytes: 0,
                expanded_bytes: 0,
                parts: 0,
                xml_parts: 0,
                xml_elements: 0,
                xml_tokens: 0,
                fingerprint_bytes: 0,
            },
        }
    }

    fn part(
        &mut self,
        path: &PackagePath,
        role: PartRole,
        class: PreservationClass,
        bytes: &[u8],
        documents: Option<&mut crate::call_local_xml::CallLocalXmlDocuments>,
    ) -> Result<(), SourceImportError> {
        let part_index = self.parts.len();
        let digest = <[u8; 32]>::from(Sha256::digest(bytes));
        let anchor_prefix = self.anchor_prefix(path, digest);
        let anchor = self.anchor(&anchor_prefix, None, bytes)?;
        self.record(&anchor, part_index, None)?;
        let xml = if class == PreservationClass::TokenStable {
            let xml = match documents {
                Some(documents) => documents.take_document(path.collision_key(), bytes),
                None => PreservingXmlDocument::parse(bytes),
            }
            .map_err(|_| SourceImportError::Xml)?;
            xml.verify_untouched_round_trip()
                .map_err(|_| SourceImportError::Xml)?;
            add_budget(
                &mut self.receipt.xml_elements,
                xml.elements().len(),
                self.limits.0.xml_elements,
            )?;
            add_budget(
                &mut self.receipt.xml_tokens,
                xml.tokens().len(),
                self.limits.0.xml_tokens,
            )?;
            self.receipt.xml_parts += 1;
            Some(xml)
        } else {
            None
        };
        let mut element_anchors = Vec::new();
        if let Some(xml) = &xml {
            element_anchors
                .try_reserve_exact(xml.elements().len())
                .map_err(|_| SourceImportError::Allocation)?;
            for (index, element) in xml.elements().iter().enumerate() {
                let span = element.outer_span().ok_or(SourceImportError::Topology)?;
                let raw = bytes
                    .get(span.start()..span.end())
                    .ok_or(SourceImportError::Topology)?;
                let element_anchor = self.anchor(&anchor_prefix, Some(span), raw)?;
                self.record(&element_anchor, part_index, Some(index))?;
                // Preserve actual hierarchy and sibling order; native numeric IDs
                // are not identities and may be absent/repeated across parts.
                frame(
                    &mut self.provenance,
                    element.name().namespace().unwrap_or("").as_bytes(),
                );
                frame(&mut self.provenance, element.name().local_name().as_bytes());
                for link in [
                    element.parent(),
                    element.first_child(),
                    element.next_sibling(),
                ] {
                    frame(
                        &mut self.provenance,
                        &(link.map_or(u64::MAX, |v| v as u64)).to_le_bytes(),
                    );
                }
                element_anchors.push(element_anchor);
            }
        }
        self.receipt.expanded_bytes += bytes.len() as u64;
        self.parts
            .try_reserve(1)
            .map_err(|_| SourceImportError::Allocation)?;
        self.parts.push(ImportedSourcePart {
            path: path.clone(),
            role,
            anchor,
            xml,
            element_anchors,
        });
        Ok(())
    }

    // Immutable same-part prefix only. Every original frame and raw fingerprint
    // remains; no cross-part/read cache or change to source admission budgets.
    fn anchor_prefix(&self, path: &PackagePath, part_sha: [u8; 32]) -> Sha256 {
        let mut hash = Sha256::new();
        frame(&mut hash, SOURCE_IMPORT_PROFILE.as_bytes());
        frame(&mut hash, self.document.as_str().as_bytes());
        frame(&mut hash, &self.package);
        frame(&mut hash, path.as_str().as_bytes());
        frame(&mut hash, &part_sha);
        hash
    }

    fn anchor(
        &mut self,
        prefix: &Sha256,
        span: Option<XmlByteSpan>,
        raw: &[u8],
    ) -> Result<SourceAnchorHandle, SourceImportError> {
        add_budget(
            &mut self.receipt.fingerprint_bytes,
            raw.len(),
            self.limits.0.fingerprint_bytes,
        )?;
        let fingerprint_sha256 = Sha256::digest(raw).into();
        let mut hash = prefix.clone();
        match span {
            Some(span) => {
                frame(&mut hash, b"xml-element");
                frame(&mut hash, &(span.start() as u64).to_le_bytes());
                frame(&mut hash, &(span.end() as u64).to_le_bytes());
            }
            None => frame(&mut hash, b"whole-part"),
        }
        let hex = hex_digest(hash.finalize().into());
        let opaque_handle =
            LogicalId::parse(format!("source-{hex}")).map_err(|_| SourceImportError::Anchor)?;
        Ok(SourceAnchorHandle {
            opaque_handle,
            fingerprint_sha256,
        })
    }

    fn record(
        &mut self,
        anchor: &SourceAnchorHandle,
        part: usize,
        element: Option<usize>,
    ) -> Result<(), SourceImportError> {
        if self
            .anchors
            .insert(anchor.opaque_handle.clone(), (part, element))
            .is_some()
        {
            return Err(SourceImportError::Topology);
        }
        frame(
            &mut self.provenance,
            anchor.opaque_handle.as_str().as_bytes(),
        );
        frame(&mut self.provenance, &anchor.fingerprint_sha256);
        Ok(())
    }

    fn finish(mut self, package_bytes: usize) -> BuiltSource {
        self.receipt.package_bytes = package_bytes;
        self.receipt.parts = self.parts.len();
        self.receipt.provenance_sha256 = self.provenance.finalize().into();
        (self.parts, self.anchors, self.receipt)
    }
}

fn frame(hash: &mut Sha256, bytes: &[u8]) {
    hash.update((bytes.len() as u64).to_le_bytes());
    hash.update(bytes);
}

fn add_budget(count: &mut usize, more: usize, max: usize) -> Result<(), SourceImportError> {
    *count = count
        .checked_add(more)
        .filter(|value| *value <= max)
        .ok_or(SourceImportError::Limit)?;
    Ok(())
}

fn hex_digest(bytes: [u8; 32]) -> String {
    const HEX: &[u8; 16] = b"0123456789abcdef";
    let mut output = String::with_capacity(64);
    for byte in bytes {
        output.push(char::from(HEX[usize::from(byte >> 4)]));
        output.push(char::from(HEX[usize::from(byte & 15)]));
    }
    output
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Error)]
pub enum SourceImportError {
    #[error("source import finite limit exceeded")]
    Limit,
    #[error("source import package identity changed")]
    SourceChanged,
    #[error("source import bounded ZIP rejected")]
    Package,
    #[error("source import closed package graph rejected")]
    Graph,
    #[error("source import preservation validation failed")]
    Preservation,
    #[error("source import contains a rejected part")]
    RejectedPart,
    #[error("source import preserving XML failed")]
    Xml,
    #[error("source import anchor is not bound to this source")]
    Anchor,
    #[error("source import topology is inconsistent")]
    Topology,
    #[error("source import bounded allocation failed")]
    Allocation,
}

#[cfg(test)]
#[path = "../tests/support/document_import_settings_inputs.rs"]
mod source_xml_reuse_inputs;

#[cfg(test)]
mod source_xml_reuse_tests {
    use super::*;
    use crate::call_local_xml::CallLocalXmlDocuments;

    #[test]
    fn all36_whole_source_models_match_uncached_original_path()
    -> Result<(), Box<dyn std::error::Error>> {
        let inputs = super::source_xml_reuse_inputs::actual_corpus()?;
        let mut count = 0;
        for bytes in inputs {
            let document = DocumentId::parse("source-xml-reuse-parity")?;
            let digest = Sha256::digest(&bytes).into();
            let original = ImportedSourcePackage::import_with_documents(
                &bytes,
                document.clone(),
                digest,
                SourceImportLimits::default(),
                None,
            )?;
            let reused = ImportedSourcePackage::import(
                &bytes,
                document,
                digest,
                SourceImportLimits::default(),
            )?;
            // Includes full original bytes, closed package graph, all XML
            // tokens/elements, anchors/indexes, provenance, limits and receipt.
            assert!(reused == original, "whole source model differs");
            count += 1;
        }
        assert_eq!(count, 36);
        Ok(())
    }

    #[test]
    fn moved_xml_model_keeps_source_allocation_and_full_builder_evidence()
    -> Result<(), Box<dyn std::error::Error>> {
        let bytes = b"<r xmlns='urn:test'><n>123&amp;4</n></r>";
        let path = PackagePath::parse(b"Contents/reuse.xml", 0, PackageLimits::default())?;
        let document = DocumentId::parse("source-xml-move")?;
        let mut models = CallLocalXmlDocuments::default();
        let pointer = models
            .document(path.collision_key(), bytes)?
            .with_source_bytes(|b| b.as_ptr());
        let mut original = ImportBuilder::new(&document, [1; 32], SourceImportLimits::default());
        original.part(
            &path,
            PartRole::SpineDocument,
            PreservationClass::TokenStable,
            bytes,
            None,
        )?;
        let mut reused = ImportBuilder::new(&document, [1; 32], SourceImportLimits::default());
        reused.part(
            &path,
            PartRole::SpineDocument,
            PreservationClass::TokenStable,
            bytes,
            Some(&mut models),
        )?;
        assert_eq!(
            reused.parts[0]
                .xml()
                .unwrap()
                .with_source_bytes(|b| b.as_ptr()),
            pointer
        );
        let (old_parts, old_anchors, old_receipt) = original.finish(bytes.len());
        let (new_parts, new_anchors, new_receipt) = reused.finish(bytes.len());
        assert!(old_parts == new_parts);
        assert!(old_anchors == new_anchors);
        assert_eq!(old_receipt, new_receipt);
        Ok(())
    }

    #[test]
    fn same_length_changed_or_malformed_fresh_xml_never_replays_old_model()
    -> Result<(), Box<dyn std::error::Error>> {
        let path = PackagePath::parse(b"Contents/reuse.xml", 0, PackageLimits::default())?;
        let document = DocumentId::parse("source-xml-fresh")?;
        for fresh in [
            b"<r><n>999</n></r>".as_slice(),
            b"<r>",
            b"<!DOCTYPE r><r/>",
            b"<r>&unknown;</r>",
        ] {
            let mut models = CallLocalXmlDocuments::default();
            models.document(path.collision_key(), b"<r><n>123</n></r>")?;
            let mut original =
                ImportBuilder::new(&document, [1; 32], SourceImportLimits::default());
            let old = original.part(
                &path,
                PartRole::SpineDocument,
                PreservationClass::TokenStable,
                fresh,
                None,
            );
            let mut reused = ImportBuilder::new(&document, [1; 32], SourceImportLimits::default());
            let new = reused.part(
                &path,
                PartRole::SpineDocument,
                PreservationClass::TokenStable,
                fresh,
                Some(&mut models),
            );
            assert_eq!(new, old);
            if new.is_ok() {
                assert!(reused.parts == original.parts);
                assert_eq!(reused.receipt, original.receipt);
            }
        }
        Ok(())
    }

    #[test]
    fn source_identity_and_aggregate_limit_denials_match_original_path()
    -> Result<(), Box<dyn std::error::Error>> {
        let bytes = super::source_xml_reuse_inputs::actual_corpus()?.remove(0);
        let document = DocumentId::parse("source-xml-limits")?;
        let digest: [u8; 32] = Sha256::digest(&bytes).into();
        let mut wrong = digest;
        wrong[0] ^= 1;
        for config in [
            SourceImportLimitConfig {
                archive_bytes: bytes.len() - 1,
                ..Default::default()
            },
            SourceImportLimitConfig {
                xml_elements: 1,
                ..Default::default()
            },
            SourceImportLimitConfig {
                xml_tokens: 1,
                ..Default::default()
            },
            SourceImportLimitConfig {
                fingerprint_bytes: 1,
                ..Default::default()
            },
            SourceImportLimitConfig::default(),
        ] {
            let limits = SourceImportLimits::new(config)?;
            for expected in [digest, wrong] {
                let old = ImportedSourcePackage::import_with_documents(
                    &bytes,
                    document.clone(),
                    expected,
                    limits,
                    None,
                );
                let new = ImportedSourcePackage::import(&bytes, document.clone(), expected, limits);
                match (old, new) {
                    (Ok(old), Ok(new)) => assert!(old == new),
                    (Err(old), Err(new)) => assert_eq!(old, new),
                    _ => return Err("source acceptance or denial differs".into()),
                }
            }
        }
        Ok(())
    }
}
