//! Atomic source-bound CROSSREF command updates; never cache/native evaluation.
use super::super::super::bookmark_crossref::SourceBookmarkResolution;
use super::*;
use crate::cross_reference_sdk::SdkCrossReferenceDisplay;
use crate::document_import::{
    ImportedSourcePackage, forms::ImportedDocumentForms,
    reference_targets::sdk::SourceCrossReferenceContext,
};
use crate::{
    BoundedZipReader, IdIndexLimits, IdRuleProfile, PackageArtifact, PackageGraphLimits,
    PackagePath, PatchIntent, PatchLimits, PatchText, PreservationRuleProfile,
    PreservingPatchEngine, PreservingWriter, WriterError, WriterLimits, XmlElementSelector,
};
use std::{collections::BTreeSet, io::Cursor};

pub struct SourceBookmarkCommandChange<'a> {
    pub reference_id: &'a LogicalId,
    pub expected_source_field_sha256: [u8; 32],
    pub expected_meaning_sha256: [u8; 32],
    pub target_id: &'a LogicalId,
    pub display: SdkCrossReferenceDisplay,
    pub hyperlink: bool,
}
impl fmt::Debug for SourceBookmarkCommandChange<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("SourceBookmarkCommandChange(<redacted>)")
    }
}
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct SourceBookmarkCommandChangeReceipt {
    pub source_reference_id: LogicalId,
    pub source_field_sha256: [u8; 32],
    pub source_meaning_sha256: [u8; 32],
    pub output_command_sha256: [u8; 32],
    pub selected_target_id_sha256: [u8; 32],
    pub selected_target_state_sha256: String,
}
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct SourceBookmarkCommandReceipt {
    pub profile: &'static str,
    pub source_package_sha256: [u8; 32],
    pub output_package_sha256: [u8; 32],
    pub output_bytes: usize,
    pub request_sha256: [u8; 32],
    pub changes: Vec<SourceBookmarkCommandChangeReceipt>,
    pub changed_parts: usize,
    pub changed_command_leaves: usize,
    pub outside_selected_command_contents_exact: bool,
    pub cached_values_preserved_not_refreshed: bool,
    pub native_protection_currentness_execution_or_publication_qualified: bool,
}
pub struct SourceBookmarkCommandCandidate {
    artifact: PackageArtifact,
    receipt: SourceBookmarkCommandReceipt,
}
impl fmt::Debug for SourceBookmarkCommandCandidate {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("SourceBookmarkCommandCandidate(<redacted>; no_execution_authority)")
    }
}
impl SourceBookmarkCommandCandidate {
    #[must_use]
    pub const fn receipt(&self) -> &SourceBookmarkCommandReceipt {
        &self.receipt
    }
    /// # Errors
    /// Artifact integrity only; never permission to store, publish or execute.
    pub fn with_verified_bytes<T>(
        &self,
        consume: impl FnOnce(&[u8]) -> T,
    ) -> Result<T, WriterError> {
        self.artifact.with_verified_bytes(consume)
    }
}
#[derive(Clone, Copy, Debug, Eq, PartialEq, Error)]
pub enum SourceBookmarkCommandError {
    #[error("SOURCE_BOOKMARK_UPDATE_SOURCE_REJECTED")]
    Source,
    #[error("SOURCE_BOOKMARK_UPDATE_SELECTION_REJECTED")]
    Selection,
    #[error("SOURCE_BOOKMARK_UPDATE_TARGET_REJECTED")]
    Target,
    #[error("SOURCE_BOOKMARK_UPDATE_PROTECTION_REJECTED")]
    Protection,
    #[error("SOURCE_BOOKMARK_UPDATE_NO_CHANGE")]
    NoChange,
    #[error("SOURCE_BOOKMARK_UPDATE_LIMIT")]
    Limit,
    #[error("SOURCE_BOOKMARK_UPDATE_PATCH_REJECTED")]
    Patch,
    #[error("SOURCE_BOOKMARK_UPDATE_WRITER_REJECTED")]
    Writer,
    #[error("SOURCE_BOOKMARK_UPDATE_PRESERVATION_REJECTED")]
    Preservation,
    #[error("SOURCE_BOOKMARK_UPDATE_READBACK_REJECTED")]
    Readback,
}
type E = SourceBookmarkCommandError;
struct Leaf {
    element: usize,
    value: String,
}
impl SourceFieldMeaningIndex<'_, '_> {
    /// A whole batch edits only exact Command leaf contents. Destination names
    /// come from an original source target index, not a caller string/map.
    /// # Errors
    /// Rejects stale/foreign/duplicate/no-op/unsupported selections, source or
    /// field/ancestor protection, incomplete coverage and any preservation drift.
    pub fn lower_bookmark_command_changes(
        &self,
        proof: &VerifiedFormReconstruction<'_>,
        requests: &[SourceBookmarkCommandChange<'_>],
        writer: WriterLimits,
    ) -> Result<SourceBookmarkCommandCandidate, E> {
        let config = self.limits.config();
        if requests.is_empty()
            || requests.len() > config.items_per_kind
            || requests.len() > PatchLimits::default().config().max_intents
        {
            return Err(E::Limit);
        }
        let rebuilt = proof
            .for_original(self.fields.forms)
            .map_err(|_| E::Source)?;
        let source = self.fields.forms.source();
        let fresh = rebuilt.source().original.as_ref();
        source
            .observe_protection_signals()
            .map_err(|_| E::Protection)?
            .require_no_observed_document_signals()
            .map_err(|_| E::Protection)?;
        let context =
            SourceCrossReferenceContext::import(self.fields.forms.body_structure(), self.limits)
                .map_err(|_| E::Target)?;
        let mut counts = [0usize; 2];
        for part in source.parts() {
            if let Some(xml) = part.xml() {
                for node in xml.elements() {
                    if node.name().namespace() == Some(crate::HANCOM_2020_PARAGRAPH_NAMESPACE) {
                        let i = match node.name().local_name() {
                            "fieldBegin" => 0,
                            "fieldEnd" => 1,
                            _ => continue,
                        };
                        counts[i] = counts[i]
                            .checked_add(1)
                            .filter(|n| *n <= config.items_per_kind)
                            .ok_or(E::Limit)?;
                    }
                }
            }
        }
        if counts != [self.fields.fields().len(); 2] {
            return Err(E::Source);
        }
        let by_id: BTreeMap<_, _> = self
            .fields
            .fields()
            .iter()
            .enumerate()
            .map(|(i, f)| (&f.reference_id, i))
            .collect();
        let mut selected = BTreeMap::new();
        let mut plans: BTreeMap<&PackagePath, Vec<Leaf>> = BTreeMap::new();
        let mut guards: BTreeMap<&PackagePath, Vec<usize>> = BTreeMap::new();
        let mut seen = BTreeSet::new();
        let mut intents = Vec::new();
        let mut changes = Vec::new();
        let mut work = 0usize;
        let mut command_bytes = 0usize;
        for request in requests {
            if !seen.insert(request.reference_id) {
                return Err(E::Selection);
            }
            let i = *by_id.get(request.reference_id).ok_or(E::Selection)?;
            let range = &self.fields.fields()[i];
            if range.begin_anchor.fingerprint_sha256 != request.expected_source_field_sha256
                || self.meaning_sha256(i).map_err(|_| E::Limit)? != request.expected_meaning_sha256
            {
                return Err(E::Selection);
            }
            let ImportedFieldMeaning::BookmarkCrossReference { command: old } =
                &self.observations[i].meaning
            else {
                return Err(E::Selection);
            };
            let destination = context
                .prepare(request.target_id, request.display, request.hyperlink)
                .map_err(|_| E::Target)?;
            let new = destination.command_for_discovery();
            if new.len() > config.text_bytes {
                return Err(E::Limit);
            }
            command_bytes = command_bytes
                .checked_add(new.len())
                .filter(|n| *n <= config.input_bytes)
                .ok_or(E::Limit)?;
            let sha: [u8; 32] = Sha256::digest(new.as_bytes()).into();
            if sha == old.command_sha256 {
                return Err(E::NoChange);
            }
            let begin = source
                .resolve_anchor(&range.begin_anchor)
                .map_err(|_| E::Source)?;
            let end = source
                .resolve_anchor(&range.end_anchor)
                .map_err(|_| E::Source)?;
            let param = source
                .resolve_anchor(range.parameter_anchor.as_ref().ok_or(E::Selection)?)
                .map_err(|_| E::Source)?;
            let part = begin.part();
            let xml = part.xml().ok_or(E::Source)?;
            if end.part().path() != part.path() || param.part().path() != part.path() {
                return Err(E::Source);
            }
            let start = begin.element_index().ok_or(E::Source)?;
            let stop = end
                .element_index()
                .and_then(|n| n.checked_add(1))
                .ok_or(E::Source)?;
            if !guards.contains_key(part.path()) {
                work = work
                    .checked_add(xml.elements().len())
                    .filter(|n| *n <= 1_000_000)
                    .ok_or(E::Limit)?;
                let mut flags =
                    crate::document_import::search::replacement::atoms::unicode::plan::guard(xml)
                        .map_err(|_| E::Protection)?;
                // Native review markers are siblings, not XML ancestors.
                // Preserve their matching spans; malformed marker streams do
                // not become implicit permission to change a command.
                let mut reviewing = BTreeSet::new();
                for (at, node) in xml.elements().iter().enumerate() {
                    flags[at] |= !reviewing.is_empty();
                    if node.name().namespace() != Some(crate::HANCOM_2020_PARAGRAPH_NAMESPACE) {
                        continue;
                    }
                    let (kind, begin) = match node.name().local_name() {
                        "insertBegin" => (true, true),
                        "insertEnd" => (true, false),
                        "deleteBegin" => (false, true),
                        "deleteEnd" => (false, false),
                        _ => continue,
                    };
                    let id = node
                        .attributes()
                        .iter()
                        .find(|a| a.name().namespace().is_none() && a.name().local_name() == "id")
                        .map(|a| a.semantic_value())
                        .filter(|v| !v.is_empty())
                        .ok_or(E::Protection)?;
                    if begin {
                        if !reviewing.insert((kind, id)) {
                            return Err(E::Protection);
                        }
                    } else if !reviewing.remove(&(kind, id)) {
                        return Err(E::Protection);
                    }
                    flags[at] = true;
                }
                if !reviewing.is_empty() {
                    return Err(E::Protection);
                }
                let mut prefix = Vec::new();
                prefix
                    .try_reserve_exact(flags.len() + 1)
                    .map_err(|_| E::Limit)?;
                prefix.push(0usize);
                for flag in flags {
                    prefix.push(
                        prefix
                            .last()
                            .copied()
                            .ok_or(E::Protection)?
                            .checked_add(usize::from(flag))
                            .ok_or(E::Limit)?,
                    );
                }
                guards.insert(part.path(), prefix);
            }
            let prefix = guards.get(part.path()).ok_or(E::Protection)?;
            if start >= stop
                || prefix
                    .get(stop)
                    .zip(prefix.get(start))
                    .is_none_or(|(a, b)| a != b)
            {
                return Err(E::Protection);
            }
            // Range parents are semantic siblings in XML. An outer locked
            // field must still protect this selected nested field's command.
            let mut parent = range.parent_reference_id.as_ref();
            while let Some(id) = parent {
                work = work
                    .checked_add(1)
                    .filter(|n| *n <= 1_000_000)
                    .ok_or(E::Limit)?;
                let outer = &self.fields.fields()[*by_id.get(id).ok_or(E::Source)?];
                let anchor = source
                    .resolve_anchor(&outer.begin_anchor)
                    .map_err(|_| E::Source)?;
                if anchor.part().path() != part.path() {
                    return Err(E::Source);
                }
                let at = anchor.element_index().ok_or(E::Source)?;
                if prefix
                    .get(at + 1)
                    .zip(prefix.get(at))
                    .is_none_or(|(a, b)| a != b)
                {
                    return Err(E::Protection);
                }
                parent = outer.parent_reference_id.as_ref();
            }
            let p = param.element_index().ok_or(E::Source)?;
            let node = xml.elements().get(p).ok_or(E::Source)?;
            if node.parent() != Some(start) {
                return Err(E::Source);
            }
            let mut child = node.first_child();
            let mut leaf = None;
            while let Some(at) = child {
                work = work
                    .checked_add(1)
                    .filter(|n| *n <= 1_000_000)
                    .ok_or(E::Limit)?;
                let n = xml.elements().get(at).ok_or(E::Source)?;
                child = n.next_sibling();
                if n.attributes().iter().any(|a| {
                    a.name().namespace().is_none()
                        && a.name().local_name() == "name"
                        && a.semantic_value() == "Command"
                }) {
                    if leaf.is_some()
                        || n.name().namespace() != Some(crate::HANCOM_2020_PARAGRAPH_NAMESPACE)
                        || n.name().local_name() != "stringParam"
                        || n.first_child().is_some()
                        || at < start
                        || at >= stop
                    {
                        return Err(E::Selection);
                    }
                    leaf = Some(at);
                }
            }
            let element = leaf.ok_or(E::Selection)?;
            intents.push(PatchIntent::ReplaceLeafText {
                target: XmlElementSelector::bind(part.path(), xml, element)
                    .map_err(|_| E::Selection)?,
                value: PatchText::new(new).map_err(|_| E::Limit)?,
            });
            plans.entry(part.path()).or_default().push(Leaf {
                element,
                value: new.into(),
            });
            selected.insert(i, sha);
            changes.push(SourceBookmarkCommandChangeReceipt {
                source_reference_id: range.reference_id.clone(),
                source_field_sha256: range.begin_anchor.fingerprint_sha256,
                source_meaning_sha256: request.expected_meaning_sha256,
                output_command_sha256: sha,
                selected_target_id_sha256: destination.receipt().logical_target_id_sha256,
                selected_target_state_sha256: destination.receipt().target_state_sha256.clone(),
            });
        }
        for leaves in plans.values_mut() {
            leaves.sort_by_key(|l| l.element);
            if leaves.windows(2).any(|w| w[0].element == w[1].element) {
                return Err(E::Selection);
            }
        }
        let request_sha256 = bounded_digest(
            &(
                "source-bookmark-command-update/v1",
                self.receipt.meaning_inventory_sha256,
                &changes,
            ),
            config.output_bytes,
        )
        .map_err(|_| E::Limit)?;
        let zip = source.limits.zip().map_err(|_| E::Source)?;
        let mut reader = BoundedZipReader::open(Cursor::new(fresh), zip).map_err(|_| E::Source)?;
        let profile = crate::document_import::search::replacement::font_profile::select(
            source,
            IdRuleProfile::hwpml_2011_shape_v6(),
        );
        let patch = PreservingPatchEngine::apply_with_limits_and_preservation_profile(
            &mut reader,
            &source.graph,
            PackageGraphLimits::default(),
            profile,
            IdIndexLimits::default(),
            PatchLimits::default(),
            PreservationRuleProfile::Hangul2020PreviewTextV2,
            &intents,
        )
        .map_err(|_| E::Patch)?;
        if patch.added_parts() != 0
            || patch.changed_parts() != plans.len()
            || patch.parts().iter().any(|p| {
                !plans.contains_key(p.path()) && p.source_sha256() != Some(p.output_sha256())
            })
        {
            return Err(E::Preservation);
        }
        let artifact = PreservingWriter::build(
            &patch,
            zip,
            PackageGraphLimits::default(),
            IdIndexLimits::default(),
            writer,
        )
        .map_err(|_| E::Writer)?;
        artifact.with_verified_bytes(|bytes|->Result<(),E>{
            let output=ImportedSourcePackage::import(bytes,source.document_id().clone(),Sha256::digest(bytes).into(),source.limits).map_err(|_|E::Readback)?;
            let forms=ImportedDocumentForms::import(output).map_err(|_|E::Readback)?;let fields=ImportedDocumentFields::import(&forms).map_err(|_|E::Readback)?;
            let meanings=SourceFieldMeaningIndex::import(&fields,self.limits).map_err(|_|E::Readback)?;
            if meanings.observations.len()!=self.observations.len(){return Err(E::Readback);}
            for(i,(old,new))in self.observations.iter().zip(&meanings.observations).enumerate(){
                if let Some(sha)=selected.get(&i){if !matches!(&new.meaning,ImportedFieldMeaning::BookmarkCrossReference{command}if command.command_sha256==*sha&&matches!(command.target,SourceBookmarkResolution::Bound{..})){return Err(E::Readback);}}
                else if !same_unselected(&old.meaning,&new.meaning){return Err(E::Readback);}
                let a=&self.fields.fields()[i];let b=&fields.fields()[i];if a.native_kind!=b.native_kind||a.native_begin_id!=b.native_begin_id||a.inline_start!=b.inline_start||a.inline_end!=b.inline_end{return Err(E::Readback);}
                for(a,b)in [(&a.begin_anchor,&b.begin_anchor),(&a.end_anchor,&b.end_anchor)]{let x=source.resolve_anchor(a).map_err(|_|E::Readback)?;let y=forms.source().resolve_anchor(b).map_err(|_|E::Readback)?;if x.part().path()!=y.part().path()||x.element_index()!=y.element_index(){return Err(E::Readback);}}
            }
            for(path,leaves)in &plans{
                let old=source.parts().iter().find(|p|p.path()==*path).and_then(|p|p.xml()).ok_or(E::Readback)?;let new=forms.source().parts().iter().find(|p|p.path()==*path).and_then(|p|p.xml()).ok_or(E::Readback)?;
                if old.elements().len()!=new.elements().len(){return Err(E::Readback);}let(mut before,mut after)=(0,0);
                for leaf in leaves{let a=old.elements()[leaf.element].content_span().ok_or(E::Readback)?;let b=new.elements()[leaf.element].content_span().ok_or(E::Readback)?;
                    if !old.with_source_bytes(|x|new.with_source_bytes(|y|x.get(before..a.start())==y.get(after..b.start()))){return Err(E::Preservation);}
                    let node=&new.elements()[leaf.element];if node.first_child().is_some()||quick_xml::escape::unescape(new.source_text(b).map_err(|_|E::Readback)?).map_err(|_|E::Readback)?.as_ref()!=leaf.value{return Err(E::Readback);}before=a.end();after=b.end();
                }
                if !old.with_source_bytes(|x|new.with_source_bytes(|y|x.get(before..)==y.get(after..))){return Err(E::Preservation);}
            }Ok(())
        }).map_err(|_|E::Writer)??;
        let receipt = SourceBookmarkCommandReceipt {
            profile: "hwpx-agent.source-bookmark-command-update/v1",
            source_package_sha256: source.receipt().source_package_sha256,
            output_package_sha256: artifact.sha256(),
            output_bytes: artifact.size_bytes(),
            request_sha256,
            changes,
            changed_parts: plans.len(),
            changed_command_leaves: intents.len(),
            outside_selected_command_contents_exact: true,
            cached_values_preserved_not_refreshed: true,
            native_protection_currentness_execution_or_publication_qualified: false,
        };
        let _ = bounded_digest(&receipt, config.output_bytes).map_err(|_| E::Limit)?;
        Ok(SourceBookmarkCommandCandidate { artifact, receipt })
    }
}
fn same_unselected(a: &ImportedFieldMeaning, b: &ImportedFieldMeaning) -> bool {
    if let (
        ImportedFieldMeaning::BookmarkCrossReference { command: a },
        ImportedFieldMeaning::BookmarkCrossReference { command: b },
    ) = (a, b)
    {
        a.command_sha256 == b.command_sha256
            && a.exact_target_name_sha256 == b.exact_target_name_sha256
            && a.display == b.display
            && a.hyperlink == b.hyperlink
            && std::mem::discriminant(&a.target) == std::mem::discriminant(&b.target)
    } else {
        a == b
    }
}
