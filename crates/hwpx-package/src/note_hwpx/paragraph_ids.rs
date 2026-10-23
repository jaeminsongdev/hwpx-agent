//! Numeric ID allocation/admission only; no mutation or inferred note-local scope.
use super::{NoteHwpxError as E, NoteHwpxLimits, PARAGRAPH_NS, PreservingXmlDocument};
use std::collections::BTreeSet;

pub(super) struct Inventory { values: BTreeSet<u32>, count: usize }

pub(super) fn inventory(xml: &PreservingXmlDocument, limits: NoteHwpxLimits) -> Result<Inventory, E> {
    if xml.elements().len() > limits.config().elements { return Err(E::InputLimit); }
    let mut result = Inventory { values: BTreeSet::new(), count: 0 };
    for node in xml.elements() {
        if node.name().namespace() != Some(PARAGRAPH_NS) || node.name().local_name() != "p" { continue; }
        result.count = result.count.checked_add(1).filter(|n| *n <= limits.config().paragraphs).ok_or(E::InputLimit)?;
        // The original low-level section profile permits absent paragraph IDs.
        // Index only declarations actually present, just like the unchanged
        // IdIndex. Do not invent an ID or reject old source solely for absence.
        let Some(attribute) = node.attributes().iter().find(|a| a.name().namespace().is_none() && a.name().local_name() == "id") else { continue };
        let value = attribute.semantic_value();
        if value.is_empty() || !value.bytes().all(|b| b.is_ascii_digit()) { return Err(E::ParagraphIdentityCollision); }
        let value = value.parse::<u32>().map_err(|_| E::ParagraphIdentityCollision)?;
        // Preserve the original IdIndex's zero sentinel. All nonzero IDs remain
        // unique across the entire section, including every nested note body.
        if value != 0 && !result.values.insert(value) { return Err(E::ParagraphIdentityCollision); }
    }
    Ok(result)
}
pub(super) fn require_disjoint(source: &PreservingXmlDocument, payload: &Inventory, limits: NoteHwpxLimits) -> Result<(), E> {
    let source = inventory(source, limits)?;
    if source.count.checked_add(payload.count).filter(|n| *n <= limits.config().paragraphs).is_none() { return Err(E::InputLimit); }
    if !source.values.is_disjoint(&payload.values) { return Err(E::ParagraphIdentityCollision); }
    Ok(())
}
pub(super) fn allocate(source: &PreservingXmlDocument, count: usize, limits: NoteHwpxLimits) -> Result<Vec<u32>, E> {
    if count == 0 || count > limits.config().paragraphs { return Err(E::InputLimit); }
    let source = inventory(source, limits)?;
    if source.count.checked_add(count).filter(|n| *n <= limits.config().paragraphs).is_none() { return Err(E::InputLimit); }
    let maximum = source.values.last().copied().unwrap_or(0);
    let count = u32::try_from(count).map_err(|_| E::InputLimit)?;
    let last = maximum.checked_add(count).ok_or(E::ParagraphIdentityCollision)?;
    let first = maximum.checked_add(1).ok_or(E::ParagraphIdentityCollision)?;
    let mut result = Vec::new();
    result.try_reserve_exact(count as usize).map_err(|_| E::AllocationFailed)?;
    result.extend(first..=last);
    Ok(result)
}
