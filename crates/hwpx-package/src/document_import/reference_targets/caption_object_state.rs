//! Mutation-stable non-caption object projections for the future typed compiler.
//! Complete caption envelopes remain separate. No counter/protection authority.
use super::{hash_json, ImportedDocumentStructure};
use super::numbering::{CaptionNumberingImportError as Error, context::{
    NativeNumberingOwnerObservation, NumberingContextImportReceipt, NumberingSourcePosition,
}};
use crate::{PreservingXmlDocument, XmlElementToken};
use domain_ir::{CaptionObjectKind, LogicalId, ReferenceAuxiliaryLimits};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use std::{collections::{BTreeMap, BTreeSet}, fmt};

const HP: &str = crate::HANCOM_2020_PARAGRAPH_NAMESPACE;
const PROFILE: &str = "hwpx-agent.caption-object-state/existing-caption-mask-merkle-v1";

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct CaptionObjectStateProjection {
    pub logical_object_id: LogicalId,
    pub section_id: LogicalId,
    pub object_kind: CaptionObjectKind,
    pub source_position: NumberingSourcePosition,
    /// Excludes only admitted existing caption subtrees, including nested owners'
    /// captions. A fixed marker retains their positions/presence. All other raw
    /// bytes and resolved element/attribute namespaces remain in the projection.
    pub object_state_sha256: [u8; 32],
    pub source_fingerprint_sha256: [u8; 32],
    pub excluded_caption_subtrees: usize,
}
impl fmt::Debug for CaptionObjectStateProjection {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("CaptionObjectStateProjection(<redacted>; not_complete_auxiliary_state)")
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct CaptionObjectStateReceipt {
    pub profile: &'static str,
    pub source_context: NumberingContextImportReceipt,
    pub object_states_sha256: [u8; 32],
    pub owners: usize,
    pub masked_caption_subtrees: usize,
    pub projected_parts: usize,
    /// Actual unique raw byte slices fed into element hashes. Parent nodes use
    /// child digests rather than rehashing overlapping subtrees.
    pub raw_bytes_hashed: usize,
    pub xml_elements_visited: usize,
    pub child_edges_hashed: usize,
    pub complete_auxiliary_state_and_protection_qualified: bool,
    pub execution_publication_authority: bool,
}

pub struct ImportedCaptionObjectStates<'a> {
    source: &'a ImportedDocumentStructure,
    objects: Vec<CaptionObjectStateProjection>,
    receipt: CaptionObjectStateReceipt,
}
impl fmt::Debug for ImportedCaptionObjectStates<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ImportedCaptionObjectStates(<redacted>; non_caption_state_only)")
    }
}
impl<'a> ImportedCaptionObjectStates<'a> {
    pub(super) fn import(source: &'a ImportedDocumentStructure,
        owners: &[NativeNumberingOwnerObservation], context: &NumberingContextImportReceipt,
        limits: ReferenceAuxiliaryLimits,
    ) -> Result<Self, Error> {
        if owners.len() > limits.config().items_per_kind
            || source.graph().sections().len() > limits.config().sections {
            return Err(Error::Limit);
        }
        let mut groups = BTreeMap::<usize, Vec<&NativeNumberingOwnerObservation>>::new();
        for owner in owners { groups.entry(owner.source_position.spine_ordinal).or_default().push(owner); }
        let parts: BTreeMap<_, _> = source.source().parts().iter().map(|part| (part.path(), part)).collect();
        let mut objects = Vec::new();
        objects.try_reserve_exact(owners.len()).map_err(|_| Error::Limit)?;
        let mut receipt = CaptionObjectStateReceipt {
            profile: PROFILE, source_context: context.clone(), object_states_sha256: [0; 32],
            owners: owners.len(), masked_caption_subtrees: 0, projected_parts: 0,
            raw_bytes_hashed: 0, xml_elements_visited: 0, child_edges_hashed: 0,
            complete_auxiliary_state_and_protection_qualified: false, execution_publication_authority: false,
        };
        for (spine, group) in groups {
            let path = source.source().spine().get(spine).ok_or(Error::Binding)?;
            let part = *parts.get(path).ok_or(Error::Binding)?;
            let xml = part.xml().ok_or(Error::Binding)?;
            let mut expected_captions = BTreeMap::new();
            for owner in &group {
                let index = owner.source_position.xml_element_ordinal;
                let anchor = part.element_anchor(index).ok_or(Error::Binding)?;
                if anchor.fingerprint_sha256 != owner.source_fingerprint_sha256 { return Err(Error::Binding); }
                if let Some(id) = &owner.logical_caption_id {
                    if expected_captions.insert(id.as_str(), index).is_some() { return Err(Error::Binding); }
                }
            }
            let mut masked = BTreeSet::new();
            for (index, node) in xml.elements().iter().enumerate() {
                if node.name().namespace() != Some(HP) || node.name().local_name() != "caption" { continue; }
                let anchor = part.element_anchor(index).ok_or(Error::Binding)?;
                let id = format!("caption-{}", anchor.opaque_handle.as_str());
                let parent = *expected_captions.get(id.as_str()).ok_or(Error::Coverage)?;
                if node.parent() != Some(parent) { return Err(Error::Coverage); }
                masked.insert(index);
            }
            if masked.len() != expected_captions.len() { return Err(Error::Coverage); }
            let hashes = xml.with_source_bytes(|raw| project_part(xml, raw, &masked, &mut receipt))?;
            for owner in group {
                let (digest, count) = *hashes.get(owner.source_position.xml_element_ordinal).ok_or(Error::Binding)?;
                objects.push(CaptionObjectStateProjection {
                    logical_object_id: owner.logical_object_id.clone(), section_id: owner.section_id.clone(),
                    object_kind: owner.structural_kind, source_position: owner.source_position,
                    object_state_sha256: digest, source_fingerprint_sha256: owner.source_fingerprint_sha256,
                    excluded_caption_subtrees: count,
                });
            }
            add(&mut receipt.projected_parts, 1)?;
            add(&mut receipt.masked_caption_subtrees, masked.len())?;
        }
        objects.sort_by_key(|object| object.source_position);
        receipt.object_states_sha256 = hash_json(&objects, limits.config().output_bytes).map_err(|_| Error::Limit)?;
        Ok(Self { source, objects, receipt })
    }
    #[must_use] pub fn objects(&self) -> &[CaptionObjectStateProjection] { &self.objects }
    #[must_use] pub const fn receipt(&self) -> &CaptionObjectStateReceipt { &self.receipt }
    /// Whole-source/graph reconstruction; a projection is never fresh service access.
    /// # Errors
    /// Rejects source drift, including changes inside an excluded caption subtree.
    pub fn verify_source(&self, fresh: &[u8]) -> Result<CaptionObjectStateReceipt, Error> {
        if self.source.verify_source(fresh).map_err(|_| Error::Binding)? != *self.source.receipt() {
            return Err(Error::Binding);
        }
        Ok(self.receipt.clone())
    }
}

fn add(total: &mut usize, amount: usize) -> Result<(), Error> {
    *total = total.checked_add(amount).ok_or(Error::Limit)?;
    Ok(())
}
fn frame(hash: &mut Sha256, tag: u8, bytes: &[u8]) -> Result<(), Error> {
    hash.update([tag]);
    hash.update(u64::try_from(bytes.len()).map_err(|_| Error::Limit)?.to_le_bytes());
    hash.update(bytes);
    Ok(())
}
fn namespace(hash: &mut Sha256, node: &XmlElementToken) -> Result<(), Error> {
    // Raw prefixes are not enough when their declarations are inherited from
    // outside the owner. Resolve namespace identities without copying the XML.
    frame(hash, 1, node.name().namespace().unwrap_or("").as_bytes())?;
    for attr in node.attributes() { frame(hash, 2, attr.name().namespace().unwrap_or("").as_bytes())?; }
    frame(hash, 3, &[])
}
fn project_part(xml: &PreservingXmlDocument, raw: &[u8], masked: &BTreeSet<usize>,
    receipt: &mut CaptionObjectStateReceipt,
) -> Result<Vec<([u8; 32], usize)>, Error> {
    // One fixed-size slot per source-admitted element (at most 100,000 in the
    // admission profile). No object-count times subtree-size buffer/hash work.
    let mut hashes = Vec::new();
    hashes.try_reserve_exact(xml.elements().len()).map_err(|_| Error::Limit)?;
    hashes.resize(xml.elements().len(), ([0; 32], 0_usize));
    for index in (0..xml.elements().len()).rev() {
        add(&mut receipt.xml_elements_visited, 1)?;
        if masked.contains(&index) {
            hashes[index] = (Sha256::digest(b"hwpx-agent.caption-object-state/excluded-existing-caption-v1").into(), 1);
            continue;
        }
        let node = &xml.elements()[index];
        let span = node.outer_span().ok_or(Error::Binding)?;
        let mut cursor = span.start();
        let mut hash = Sha256::new();
        hash.update(PROFILE.as_bytes());
        namespace(&mut hash, node)?;
        let mut count = 0;
        let mut child = node.first_child();
        while let Some(current) = child {
            let nested = xml.elements().get(current).ok_or(Error::Binding)?;
            if current <= index || nested.parent() != Some(index) { return Err(Error::Binding); }
            let child_span = nested.outer_span().ok_or(Error::Binding)?;
            if child_span.end() > span.end() { return Err(Error::Binding); }
            let bytes = raw.get(cursor..child_span.start()).ok_or(Error::Binding)?;
            frame(&mut hash, 4, bytes)?;
            add(&mut receipt.raw_bytes_hashed, bytes.len())?;
            frame(&mut hash, 5, &hashes[current].0)?;
            add(&mut count, hashes[current].1)?;
            add(&mut receipt.child_edges_hashed, 1)?;
            cursor = child_span.end();
            child = nested.next_sibling();
        }
        let bytes = raw.get(cursor..span.end()).ok_or(Error::Binding)?;
        frame(&mut hash, 4, bytes)?;
        add(&mut receipt.raw_bytes_hashed, bytes.len())?;
        hashes[index] = (hash.finalize().into(), count);
    }
    Ok(hashes)
}
