//! Exact final preserving splices, retained before the original patch consumes them.
//! This inventory is compiler input, never a source/access/route/commit proof.
use super::*;
use crate::document_import::ImportedSourcePart;
pub const STYLE_SPLICE_INVENTORY_PROFILE: &str = "hwpx-agent.source-style-splice-inventory/v1";
const MAX_INVENTORY_BYTES: usize = 8 * 1024 * 1024;

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum StyleSpliceAxis { RunCharacterProperty, TextCharacterStyle }

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct SourceStyleSubtreeSplice {
    source_anchor: SourceAnchorHandle,
    source_start: usize,
    source_end: usize,
    replacement_sha256: [u8; 32],
    replacement_bytes: usize,
    fragments: usize,
}
impl fmt::Debug for SourceStyleSubtreeSplice {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result { f.write_str("SourceStyleSubtreeSplice(<redacted>)") }
}
impl SourceStyleSubtreeSplice {
    #[must_use] pub const fn source_anchor(&self) -> &SourceAnchorHandle { &self.source_anchor }
    #[must_use] pub const fn source_start(&self) -> usize { self.source_start }
    #[must_use] pub const fn source_end(&self) -> usize { self.source_end }
    #[must_use] pub const fn replacement_sha256(&self) -> [u8; 32] { self.replacement_sha256 }
    #[must_use] pub const fn replacement_bytes(&self) -> usize { self.replacement_bytes }
    #[must_use] pub const fn fragments(&self) -> usize { self.fragments }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct SourceStyleSpliceInventory {
    profile: &'static str,
    axis: StyleSpliceAxis,
    source_package_sha256: [u8; 32],
    output_package_sha256: [u8; 32],
    legacy_receipt_sha256: [u8; 32],
    splices: Vec<SourceStyleSubtreeSplice>,
    #[serde(skip)] canonical_sha256: [u8; 32],
}
impl fmt::Debug for SourceStyleSpliceInventory {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("SourceStyleSpliceInventory").field("axis", &self.axis)
            .field("splices", &self.splices.len()).finish_non_exhaustive()
    }
}
impl SourceStyleSpliceInventory {
    #[must_use] pub const fn profile(&self) -> &'static str { self.profile }
    #[must_use] pub const fn axis(&self) -> StyleSpliceAxis { self.axis }
    #[must_use] pub const fn source_package_sha256(&self) -> [u8; 32] { self.source_package_sha256 }
    #[must_use] pub const fn output_package_sha256(&self) -> [u8; 32] { self.output_package_sha256 }
    #[must_use] pub const fn legacy_receipt_sha256(&self) -> [u8; 32] { self.legacy_receipt_sha256 }
    #[must_use] pub fn splices(&self) -> &[SourceStyleSubtreeSplice] { &self.splices }
    #[must_use] pub const fn canonical_sha256(&self) -> [u8; 32] { self.canonical_sha256 }
}

pub(super) struct Builder { axis: StyleSpliceAxis, splices: Vec<SourceStyleSubtreeSplice> }
impl Builder {
    pub(super) fn new(axis: StyleSpliceAxis) -> Self { Self { axis, splices: Vec::new() } }
    pub(super) fn observe(&mut self, part: &ImportedSourcePart, element: usize, edit: &Edit) -> Result<(), E> {
        if self.splices.len() >= PatchLimits::default().config().max_intents { return Err(E::Limit); }
        let xml = part.xml().ok_or(E::Source)?;
        let outer = xml.elements().get(element).and_then(|n| n.outer_span()).ok_or(E::Selection)?;
        if outer.end() != edit.end || edit.bytes.is_empty() || edit.fragments.is_empty() { return Err(E::Selection); }
        self.splices.push(SourceStyleSubtreeSplice {
            source_anchor: part.element_anchor(element).ok_or(E::Selection)?.clone(),
            source_start: outer.start(), source_end: outer.end(),
            replacement_sha256: Sha256::digest(&edit.bytes).into(), replacement_bytes: edit.bytes.len(), fragments: edit.fragments.len(),
        });
        Ok(())
    }
    pub(super) fn finish(self, source: [u8; 32], output: [u8; 32], receipt: &impl Serialize,
        expected_intents: usize, receipt_limit: usize) -> Result<SourceStyleSpliceInventory, E> {
        if self.splices.is_empty() || self.splices.len() != expected_intents || source == [0; 32] || output == [0; 32] { return Err(E::Selection); }
        let mut inventory = SourceStyleSpliceInventory {
            profile: STYLE_SPLICE_INVENTORY_PROFILE, axis: self.axis, source_package_sha256: source,
            output_package_sha256: output, legacy_receipt_sha256: bounded_hash(receipt, receipt_limit)?,
            splices: self.splices, canonical_sha256: [0; 32],
        };
        inventory.canonical_sha256 = bounded_hash(&inventory, MAX_INVENTORY_BYTES)?;
        Ok(inventory)
    }
}
// Stream both hashes. Never allocate another serialized receipt/inventory or retain fragment XML.
fn bounded_hash(value: &impl Serialize, maximum: usize) -> Result<[u8; 32], E> {
    struct Hash { state: Sha256, bytes: usize, maximum: usize }
    impl std::io::Write for Hash {
        fn write(&mut self, bytes: &[u8]) -> std::io::Result<usize> {
            let length = self.bytes.checked_add(bytes.len()).filter(|n| *n <= self.maximum)
                .ok_or_else(|| std::io::Error::other("style_inventory_limit"))?;
            self.state.update(bytes); self.bytes = length; Ok(bytes.len())
        }
        fn flush(&mut self) -> std::io::Result<()> { Ok(()) }
    }
    let mut writer = Hash { state: Sha256::new(), bytes: 0, maximum };
    serde_json::to_writer(&mut writer, value).map_err(|_| E::Limit)?;
    Ok(writer.state.finalize().into())
}
