//! Decoded original inline cache snapshots, never recomputed/current/Native values.
use super::{FieldRangeImportReceipt, ImportedDocumentFields, ImportedFieldRange};
use domain_ir::{Flow, Inline, LogicalId, Node, ParagraphNode, ReferenceAuxiliaryLimits};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use std::{collections::BTreeMap, fmt, io};
use thiserror::Error;

pub const PROFILE: &str = "hwpx-agent.source-field-cached-inlines/v1";
const MAX_WORK: usize = 1_000_000;
#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(tag = "snapshot", rename_all = "snake_case")]
pub enum FieldCacheSnapshot {
    DecodedTextNotEvaluated {
        decoded_text_sha256: [u8; 32],
        utf8_bytes: usize,
        text_atoms: usize,
        tabs: usize,
        line_breaks: usize,
    },
    StructuredUnqualified {
        inline_items: usize,
        unsupported_inline_items: usize,
    },
}
impl fmt::Debug for FieldCacheSnapshot {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("FieldCacheSnapshot(<redacted>; not evaluated)")
    }
}
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct FieldCacheObservation {
    pub field_reference_id: LogicalId,
    pub cache: FieldCacheSnapshot,
}
#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct SourceFieldCachedInlines {
    schema_version: &'static str,
    scope: &'static str,
    field_import: FieldRangeImportReceipt,
    observations: Vec<FieldCacheObservation>,
    indexed_paragraphs: usize,
    prefix_events: usize,
    scanned_inline_items: usize,
    hashed_text_bytes: usize,
    additional_document_graph_clones: usize,
    native_display_or_evaluation_qualified: bool,
    cache_currentness_qualified: bool,
    complete_reference_validation_qualified: bool,
}
impl fmt::Debug for SourceFieldCachedInlines {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("SourceFieldCachedInlines")
            .field("fields", &self.observations.len())
            .field("scope", &"source_cache_only")
            .finish()
    }
}
#[derive(Clone, Copy, Debug, Eq, PartialEq, Error)]
pub enum FieldCachedSourceError {
    #[error("FIELD_CACHED_SOURCE_BINDING_REJECTED")]
    Binding,
    #[error("FIELD_CACHED_SOURCE_LIMIT")]
    Limit,
}
type Error = FieldCachedSourceError;
struct Output {
    written: usize,
    maximum: usize,
    bytes: Option<Vec<u8>>,
}
impl io::Write for Output {
    fn write(&mut self, bytes: &[u8]) -> io::Result<usize> {
        self.written = self
            .written
            .checked_add(bytes.len())
            .filter(|n| *n <= self.maximum)
            .ok_or_else(|| io::Error::other("FIELD_CACHED_SOURCE_LIMIT"))?;
        if let Some(out) = &mut self.bytes {
            out.try_reserve(bytes.len())
                .map_err(|_| io::Error::other("FIELD_CACHED_SOURCE_LIMIT"))?;
            out.extend_from_slice(bytes);
        }
        Ok(bytes.len())
    }
    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}
fn size(value: &impl Serialize, maximum: usize) -> Result<usize, Error> {
    let mut out = Output {
        written: 0,
        maximum,
        bytes: None,
    };
    serde_json::to_writer(&mut out, value).map_err(|_| Error::Limit)?;
    Ok(out.written)
}
#[derive(Clone, Copy, Default)]
struct Prefix {
    bytes: usize,
    texts: usize,
    tabs: usize,
    breaks: usize,
    unsupported: usize,
}
fn add(a: usize, b: usize) -> Result<usize, Error> {
    a.checked_add(b).ok_or(Error::Limit)
}
impl Prefix {
    fn advance(&mut self, value: &Inline) -> Result<(), Error> {
        match value {
            Inline::Text { text } => {
                self.bytes = add(self.bytes, text.len())?;
                self.texts = add(self.texts, 1)?;
            }
            Inline::Tab => {
                self.bytes = add(self.bytes, 1)?;
                self.tabs = add(self.tabs, 1)?;
            }
            Inline::LineBreak => {
                self.bytes = add(self.bytes, 1)?;
                self.breaks = add(self.breaks, 1)?;
            }
            _ => self.unsupported = add(self.unsupported, 1)?,
        }
        Ok(())
    }
    fn since(self, prior: Self) -> Result<Self, Error> {
        fn sub(a: usize, b: usize) -> Result<usize, Error> {
            a.checked_sub(b).ok_or(Error::Binding)
        }
        Ok(Self {
            bytes: sub(self.bytes, prior.bytes)?,
            texts: sub(self.texts, prior.texts)?,
            tabs: sub(self.tabs, prior.tabs)?,
            breaks: sub(self.breaks, prior.breaks)?,
            unsupported: sub(self.unsupported, prior.unsupported)?,
        })
    }
}
#[derive(Clone, Copy)]
struct Event {
    position: usize,
    range: usize,
    end: bool,
}
fn collect<'a>(
    flow: &'a Flow,
    wanted: &BTreeMap<&LogicalId, Vec<(usize, &ImportedFieldRange)>>,
    found: &mut BTreeMap<&'a LogicalId, &'a ParagraphNode>,
    work: &mut usize,
    depth: usize,
) -> Result<(), Error> {
    if depth > 64 {
        return Err(Error::Limit);
    }
    for node in &flow.children {
        *work = add(*work, 1)?;
        if *work > MAX_WORK {
            return Err(Error::Limit);
        }
        match node {
            Node::Paragraph(p) if wanted.contains_key(&p.common.node_id) => {
                if found.insert(&p.common.node_id, p).is_some() {
                    return Err(Error::Binding);
                }
            }
            Node::Table(t) => {
                for cell in &t.cells {
                    collect(&cell.body, wanted, found, work, depth + 1)?;
                }
            }
            Node::Drawing(d) => collect(&d.children, wanted, found, work, depth + 1)?,
            _ => (),
        }
    }
    Ok(())
}
impl SourceFieldCachedInlines {
    #[must_use]
    pub const fn field_import(&self) -> &FieldRangeImportReceipt {
        &self.field_import
    }
    #[must_use]
    pub fn observations(&self) -> &[FieldCacheObservation] {
        &self.observations
    }
    /// One node walk + sorted endpoint events per paragraph. Parent caches with
    /// nested controls are explicitly structured; plain leaf ranges are disjoint,
    /// so their decoded text is hashed once, without concatenating private text.
    /// # Errors
    /// Rejects original ranges, finite work/text/output limits and missing owners.
    pub fn import(
        fields: &ImportedDocumentFields<'_>,
        limits: ReferenceAuxiliaryLimits,
    ) -> Result<Self, Error> {
        let config = limits.config();
        let count = fields.fields().len();
        if count > config.items_per_kind
            || fields.graph().sections().len() > config.sections
            || count
                .checked_mul(64)
                .is_none_or(|n| n > config.output_bytes)
        {
            return Err(Error::Limit);
        }
        let mut result = Self {
            schema_version: PROFILE,
            scope: "decoded_source_inline_cache_only_not_recomputed_native_display_or_currentness",
            field_import: fields.receipt().clone(),
            observations: Vec::new(),
            indexed_paragraphs: 0,
            prefix_events: 0,
            scanned_inline_items: 0,
            hashed_text_bytes: 0,
            additional_document_graph_clones: 0,
            native_display_or_evaluation_qualified: false,
            cache_currentness_qualified: false,
            complete_reference_validation_qualified: false,
        };
        let mut output_bytes = size(&result, config.output_bytes)?;
        let mut retained_rows = 0usize;
        let mut groups: BTreeMap<&LogicalId, Vec<(usize, &ImportedFieldRange)>> = BTreeMap::new();
        for (index, range) in fields.fields().iter().enumerate() {
            let rows = groups.entry(&range.paragraph_id).or_default();
            rows.try_reserve(1).map_err(|_| Error::Limit)?;
            rows.push((index, range));
        }
        let mut paragraphs = BTreeMap::new();
        let mut work = 0usize;
        if count > 0 {
            for section in fields.graph().sections() {
                collect(&section.body, &groups, &mut paragraphs, &mut work, 0)?;
            }
            for note in fields.graph().notes() {
                collect(&note.body, &groups, &mut paragraphs, &mut work, 0)?;
            }
        }
        if paragraphs.len() != groups.len() {
            return Err(Error::Binding);
        }
        result.indexed_paragraphs = paragraphs.len();
        let mut slots: Vec<Option<FieldCacheObservation>> = Vec::new();
        slots.try_reserve_exact(count).map_err(|_| Error::Limit)?;
        slots.resize_with(count, || None);
        for (paragraph_id, ranges) in groups {
            let paragraph = paragraphs.get(paragraph_id).ok_or(Error::Binding)?;
            let mut events = Vec::new();
            events
                .try_reserve_exact(ranges.len().checked_mul(2).ok_or(Error::Limit)?)
                .map_err(|_| Error::Limit)?;
            for (local, (_, range)) in ranges.iter().enumerate() {
                if range.inline_start > range.inline_end
                    || range.inline_end > paragraph.inlines.len()
                {
                    return Err(Error::Binding);
                }
                events.push(Event {
                    position: range.inline_start,
                    range: local,
                    end: false,
                });
                events.push(Event {
                    position: range.inline_end,
                    range: local,
                    end: true,
                });
            }
            events.sort_unstable_by_key(|v| (v.position, v.end));
            result.prefix_events = add(result.prefix_events, events.len())?;
            let mut starts = Vec::new();
            starts
                .try_reserve_exact(ranges.len())
                .map_err(|_| Error::Limit)?;
            starts.resize(ranges.len(), Prefix::default());
            let mut prefix = Prefix::default();
            let mut position = 0usize;
            for event in events {
                while position < event.position {
                    result.scanned_inline_items = add(result.scanned_inline_items, 1)?;
                    if result.scanned_inline_items > MAX_WORK {
                        return Err(Error::Limit);
                    }
                    prefix.advance(&paragraph.inlines[position])?;
                    position += 1;
                }
                if !event.end {
                    starts[event.range] = prefix;
                    continue;
                }
                let counts = prefix.since(starts[event.range])?;
                let (index, range) = ranges[event.range];
                let cache = if counts.unsupported > 0 {
                    FieldCacheSnapshot::StructuredUnqualified {
                        inline_items: range.inline_end - range.inline_start,
                        unsupported_inline_items: counts.unsupported,
                    }
                } else {
                    if counts.bytes > config.text_bytes {
                        return Err(Error::Limit);
                    }
                    result.hashed_text_bytes = add(result.hashed_text_bytes, counts.bytes)?;
                    if result.hashed_text_bytes > config.input_bytes {
                        return Err(Error::Limit);
                    }
                    let mut sha = Sha256::new();
                    for inline in &paragraph.inlines[range.inline_start..range.inline_end] {
                        match inline {
                            Inline::Text { text } => sha.update(text.as_bytes()),
                            Inline::Tab => sha.update(b"\t"),
                            Inline::LineBreak => sha.update(b"\n"),
                            _ => return Err(Error::Binding),
                        }
                    }
                    FieldCacheSnapshot::DecodedTextNotEvaluated {
                        decoded_text_sha256: sha.finalize().into(),
                        utf8_bytes: counts.bytes,
                        text_atoms: counts.texts,
                        tabs: counts.tabs,
                        line_breaks: counts.breaks,
                    }
                };
                let observation = FieldCacheObservation {
                    field_reference_id: range.reference_id.clone(),
                    cache,
                };
                output_bytes = add(
                    add(output_bytes, size(&observation, config.output_bytes)?)?,
                    usize::from(retained_rows > 0),
                )?;
                retained_rows = add(retained_rows, 1)?;
                if output_bytes > config.output_bytes {
                    return Err(Error::Limit);
                }
                if slots[index].replace(observation).is_some() {
                    return Err(Error::Binding);
                }
            }
        }
        result
            .observations
            .try_reserve_exact(count)
            .map_err(|_| Error::Limit)?;
        for slot in slots {
            result.observations.push(slot.ok_or(Error::Binding)?);
        }
        size(&result, config.output_bytes)?;
        Ok(result)
    }
    /// # Errors
    /// Bounded output contains hashes/counts only, never raw cache/command text.
    pub fn canonical_json(&self, limits: ReferenceAuxiliaryLimits) -> Result<Vec<u8>, Error> {
        let mut out = Output {
            written: 0,
            maximum: limits.config().output_bytes,
            bytes: Some(Vec::new()),
        };
        serde_json::to_writer(&mut out, self).map_err(|_| Error::Limit)?;
        out.bytes.ok_or(Error::Limit)
    }
}
