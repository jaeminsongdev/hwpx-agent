//! New source-bound field insertion using an exact same-command source envelope.
//! This deliberately does not invent unqualified RefPath/RefType parameters.
//! The output is inert, its existing display text is NOT a computed result,
//! and no Native/currentness/service execution authority is granted.
use super::bookmark_crossref::SourceBookmarkResolution;
use super::semantics::{ImportedFieldMeaning, source_index::SourceFieldMeaningIndex};
use super::*;
use crate::cross_reference_sdk::SdkCrossReferenceDisplay;
use crate::document_import::reference_targets::sdk::SourceCrossReferenceContext;
use crate::{
    BoundedZipReader, ElementSplicePosition, IdIndexLimits, IdRuleProfile, PackageArtifact,
    PackageGraphLimits, PatchIntent, PatchLimits, PreservationRuleProfile, PreservingPatchEngine,
    PreservingWriter, ValidatedXmlFragment, WriterError, WriterLimits, XmlElementSelector,
};
use domain_ir::ReferenceAuxiliaryLimits;
use sha2::{Digest as _, Sha256};
use std::{collections::BTreeSet, io::Cursor};

pub struct SourceBookmarkInsertion<'a> {
    /// Exact original plain run, not a byte offset, caller XML or field result.
    pub run: &'a SourceAnchorHandle,
    pub target_id: &'a LogicalId,
    pub display: SdkCrossReferenceDisplay,
    pub hyperlink: bool,
}
impl fmt::Debug for SourceBookmarkInsertion<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("SourceBookmarkInsertion(<redacted>)")
    }
}
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct SourceBookmarkInsertionReceipt {
    pub profile: &'static str,
    pub source_package_sha256: [u8; 32],
    pub output_package_sha256: [u8; 32],
    pub source_run_sha256: [u8; 32],
    pub source_envelope_sha256: [u8; 32],
    pub command_sha256: [u8; 32],
    pub inserted_fields: usize,
    pub original_fields: usize,
    pub outside_insertions_exact: bool,
    pub original_selected_run_exact: bool,
    pub same_command_source_envelope_only: bool,
    pub existing_display_text_is_not_evaluated_or_refreshed: bool,
    pub native_currentness_execution_or_publication_qualified: bool,
}
pub struct SourceBookmarkInsertionCandidate {
    artifact: PackageArtifact,
    receipt: SourceBookmarkInsertionReceipt,
}
impl fmt::Debug for SourceBookmarkInsertionCandidate {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("SourceBookmarkInsertionCandidate(<redacted>; inert)")
    }
}
impl SourceBookmarkInsertionCandidate {
    #[must_use]
    pub const fn receipt(&self) -> &SourceBookmarkInsertionReceipt {
        &self.receipt
    }
    /// # Errors
    /// Artifact integrity only; not permission to save, publish or execute.
    pub fn with_verified_bytes<T>(
        &self,
        consume: impl FnOnce(&[u8]) -> T,
    ) -> Result<T, WriterError> {
        self.artifact.with_verified_bytes(consume)
    }
}
#[derive(Clone, Copy, Debug, Eq, PartialEq, Error)]
pub enum SourceBookmarkInsertionError {
    #[error("SOURCE_BOOKMARK_INSERT_SOURCE_REJECTED")]
    Source,
    #[error("SOURCE_BOOKMARK_INSERT_SELECTION_REJECTED")]
    Selection,
    #[error("SOURCE_BOOKMARK_INSERT_TARGET_REJECTED")]
    Target,
    #[error("SOURCE_BOOKMARK_INSERT_PROTECTION_REJECTED")]
    Protection,
    #[error("SOURCE_BOOKMARK_INSERT_SAME_COMMAND_ENVELOPE_UNAVAILABLE")]
    EnvelopeUnavailable,
    #[error("SOURCE_BOOKMARK_INSERT_LIMIT")]
    Limit,
    #[error("SOURCE_BOOKMARK_INSERT_PATCH_REJECTED")]
    Patch,
    #[error("SOURCE_BOOKMARK_INSERT_WRITER_REJECTED")]
    Writer,
    #[error("SOURCE_BOOKMARK_INSERT_READBACK_REJECTED")]
    Readback,
    #[error("SOURCE_BOOKMARK_INSERT_PRESERVATION_REJECTED")]
    Preservation,
}
type E = SourceBookmarkInsertionError;
fn named(n: &XmlElementToken, name: &str) -> bool {
    n.name().namespace() == Some(HP) && n.name().local_name() == name
}
fn attr<'a>(n: &'a XmlElementToken, name: &str) -> Option<&'a XmlAttributeToken> {
    n.attributes()
        .iter()
        .find(|a| a.name().namespace().is_none() && a.name().local_name() == name)
}
fn number(n: &XmlElementToken, name: &str) -> Result<u32, E> {
    attr(n, name)
        .ok_or(E::Source)?
        .semantic_value()
        .parse()
        .map_err(|_| E::Source)
}
// Copy one original, namespace-checked envelope, changing ONLY numeric identity
// values and dirty. Other private parameters are never guessed or accepted from
// callers. The matching command/target/display is checked before this function.
fn envelope(
    xml: &PreservingXmlDocument,
    index: usize,
    changes: &[(&str, u32)],
    maximum: usize,
) -> Result<String, E> {
    let node = xml.elements().get(index).ok_or(E::Source)?;
    let span = node.outer_span().ok_or(E::Source)?;
    if span.len() > maximum {
        return Err(E::Limit);
    }
    for child in xml
        .elements()
        .iter()
        .skip(index)
        .take_while(|n| n.start_tag_span().start() < span.end())
    {
        if child.name().namespace() != Some(HP)
            || !xml
                .source_text(child.start_name_span())
                .map_err(|_| E::Source)?
                .starts_with("hp:")
            || child
                .attributes()
                .iter()
                .any(|a| a.name().namespace().is_some() || a.name().local_name().contains(':'))
        {
            return Err(E::EnvelopeUnavailable);
        }
    }
    let mut edits = Vec::new();
    for &(name, value) in changes {
        let a = attr(node, name).ok_or(E::EnvelopeUnavailable)?;
        let _ = number(node, name)?;
        edits.push((a.value_span(), value.to_string()));
    }
    edits.sort_by_key(|(s, _)| s.start());
    let mut result = String::new();
    let mut at = span.start();
    for (s, value) in edits {
        result.push_str(
            xml.with_source_bytes(|b| std::str::from_utf8(&b[at..s.start()]).map(str::to_owned))
                .map_err(|_| E::Source)?
                .as_str(),
        );
        result.push_str(&value);
        at = s.end();
    }
    result.push_str(
        xml.with_source_bytes(|b| std::str::from_utf8(&b[at..span.end()]).map(str::to_owned))
            .map_err(|_| E::Source)?
            .as_str(),
    );
    if result.len() > maximum {
        return Err(E::Limit);
    }
    Ok(result)
}
impl ImportedDocumentFields<'_> {
    /// Insert a NEW CROSSREF range around one unchanged plain run. The template
    /// must be a fully parsed, bound, same-command field from this exact source.
    /// No matching envelope means explicit unsupported preparation, not a guessed
    /// native parameter mapping. Arbitrary ranges/new targets remain unqualified.
    /// # Errors
    /// Rejects foreign/stale proof/anchors, protection/review, existing field
    /// overlap, missing envelopes, duplicate/overflow IDs, limits and any drift.
    pub fn insert_bookmark_reference_from_source_envelope(
        &self,
        proof: &VerifiedFormReconstruction<'_>,
        request: SourceBookmarkInsertion<'_>,
        limits: ReferenceAuxiliaryLimits,
        writer: WriterLimits,
    ) -> Result<SourceBookmarkInsertionCandidate, E> {
        let rebuilt = proof.for_original(self.forms).map_err(|_| E::Source)?;
        // The proof already rebuilt and compared the complete immutable forms
        // against THIS original. Fields below are private deterministic imports
        // of that same source; rebuilding another full field graph here repeats
        // work without obtaining any fresher bytes or service authorization.
        let source = self.forms.source();
        let fresh = rebuilt.source().original.as_ref();
        source
            .observe_protection_signals()
            .map_err(|_| E::Protection)?
            .require_no_observed_document_signals()
            .map_err(|_| E::Protection)?;
        if self.fields.len() >= limits.config().items_per_kind {
            return Err(E::Limit);
        }
        let context = SourceCrossReferenceContext::import(self.forms.body_structure(), limits)
            .map_err(|_| E::Target)?;
        let target = context
            .prepare(request.target_id, request.display, request.hyperlink)
            .map_err(|_| E::Target)?;
        let expected: [u8; 32] = Sha256::digest(target.command_for_discovery().as_bytes()).into();
        let selected = source
            .resolve_anchor(request.run)
            .map_err(|_| E::Selection)?;
        let part = selected.part();
        let xml = part.xml().ok_or(E::Selection)?;
        let run_index = selected.element_index().ok_or(E::Selection)?;
        let run = &xml.elements()[run_index];
        if !named(run, "run")
            || run
                .attributes()
                .iter()
                .any(|a| a.name().namespace().is_some() || a.name().local_name() != "charPrIDRef")
        {
            return Err(E::Selection);
        }
        let parent = run
            .parent()
            .and_then(|i| xml.elements().get(i))
            .ok_or(E::Selection)?;
        if !named(parent, "p") {
            return Err(E::Selection);
        }
        let text = run
            .first_child()
            .and_then(|i| xml.elements().get(i))
            .ok_or(E::Selection)?;
        if !named(text, "t") || text.first_child().is_some() || text.next_sibling().is_some() {
            return Err(E::Selection);
        }
        let run_span = run.outer_span().ok_or(E::Selection)?;
        let mut ids = BTreeSet::new();
        let mut fieldids = BTreeSet::new();
        let (mut maxid, mut maxfield) = (0u32, 0u32);
        let (mut starts, mut ends, mut visits) = (0usize, 0usize, 0usize);
        // One bounded whole-source pass, not a source/ZIP scan per native ID.
        for p in source.parts() {
            if let Some(x) = p.xml() {
                visits = visits
                    .checked_add(x.elements().len())
                    .filter(|n| *n <= 1_000_000)
                    .ok_or(E::Limit)?;
                let flags =
                    crate::document_import::search::replacement::atoms::unicode::plan::guard(x)
                        .map_err(|_| E::Protection)?;
                if flags.iter().any(|v| *v)
                    || x.elements().iter().any(|n| {
                        n.name().namespace() == Some(HP)
                            && matches!(
                                n.name().local_name(),
                                "insertBegin" | "insertEnd" | "deleteBegin" | "deleteEnd"
                            )
                    })
                {
                    return Err(E::Protection);
                }
                for n in x.elements() {
                    if named(n, "fieldBegin") {
                        starts += 1;
                        let id = number(n, "id")?;
                        if !ids.insert(id) {
                            return Err(E::Source);
                        }
                        maxid = maxid.max(id);
                        if attr(n, "fieldid").is_some() {
                            let id = number(n, "fieldid")?;
                            if !fieldids.insert(id) {
                                return Err(E::Source);
                            }
                            maxfield = maxfield.max(id);
                        }
                    } else if named(n, "fieldEnd") {
                        ends += 1;
                        maxid = maxid.max(number(n, "beginIDRef")?);
                        if attr(n, "fieldid").is_some() {
                            maxfield = maxfield.max(number(n, "fieldid")?);
                        }
                    }
                }
            }
        }
        if starts != self.fields.len() || ends != starts {
            return Err(E::Source);
        }
        let id = maxid.checked_add(1).ok_or(E::Limit)?;
        let fieldid = maxfield.checked_add(1).ok_or(E::Limit)?;
        for f in &self.fields {
            let a = source
                .resolve_anchor(&f.begin_anchor)
                .map_err(|_| E::Source)?;
            let b = source
                .resolve_anchor(&f.end_anchor)
                .map_err(|_| E::Source)?;
            if a.part().path() == part.path() {
                let begin = a.element().ok_or(E::Source)?.start_tag_span().start();
                let end = b
                    .element()
                    .ok_or(E::Source)?
                    .outer_span()
                    .ok_or(E::Source)?
                    .end();
                if begin < run_span.end() && run_span.start() < end {
                    return Err(E::Selection);
                }
            }
        }
        let meanings = SourceFieldMeaningIndex::import(self, limits).map_err(|_| E::Source)?;
        let template=meanings.observations().iter().zip(&self.fields).find_map(|(m,f)| {
            match &m.meaning {ImportedFieldMeaning::BookmarkCrossReference{command}
                if command.command_sha256==expected&&matches!(&command.target,SourceBookmarkResolution::Bound{logical_target_id,..} if logical_target_id==request.target_id)=>Some(f),_=>None}
        }).ok_or(E::EnvelopeUnavailable)?;
        let a = source
            .resolve_anchor(&template.begin_anchor)
            .map_err(|_| E::Source)?;
        let b = source
            .resolve_anchor(&template.end_anchor)
            .map_err(|_| E::Source)?;
        if a.part().path() != b.part().path() {
            return Err(E::Source);
        }
        let tx = a.part().xml().ok_or(E::Source)?;
        let bn = a.element().ok_or(E::Source)?;
        let en = b.element().ok_or(E::Source)?;
        if number(bn, "fieldid")? != number(en, "fieldid")? {
            return Err(E::Source);
        }
        let begin = envelope(
            tx,
            a.element_index().ok_or(E::Source)?,
            &[("id", id), ("fieldid", fieldid), ("dirty", 1)],
            limits.config().text_bytes,
        )?;
        let end = envelope(
            tx,
            b.element_index().ok_or(E::Source)?,
            &[("beginIDRef", id), ("fieldid", fieldid)],
            limits.config().text_bytes,
        )?;
        let style = match attr(run, "charPrIDRef") {
            Some(_) => format!(" charPrIDRef=\"{}\"", number(run, "charPrIDRef")?),
            None => String::new(),
        };
        let wrap = |body: &str| {
            format!("<hp:run xmlns:hp=\"{HP}\"{style}><hp:ctrl>{body}</hp:ctrl></hp:run>")
        };
        let (before, after) = (wrap(&begin), wrap(&end));
        if before
            .len()
            .checked_add(after.len())
            .is_none_or(|n| n > limits.config().output_bytes)
        {
            return Err(E::Limit);
        }
        let selector =
            XmlElementSelector::bind(part.path(), xml, run_index).map_err(|_| E::Selection)?;
        let intents = [
            PatchIntent::SpliceElements {
                target: selector.clone(),
                position: ElementSplicePosition::Before,
                fragments: vec![
                    ValidatedXmlFragment::parse(before.as_bytes(), PatchLimits::default())
                        .map_err(|_| E::Patch)?,
                ],
            },
            PatchIntent::SpliceElements {
                target: selector,
                position: ElementSplicePosition::After,
                fragments: vec![
                    ValidatedXmlFragment::parse(after.as_bytes(), PatchLimits::default())
                        .map_err(|_| E::Patch)?,
                ],
            },
        ];
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
            || patch.changed_parts() != 1
            || patch
                .parts()
                .iter()
                .any(|p| p.path() != part.path() && p.source_sha256() != Some(p.output_sha256()))
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
            let output=super::super::ImportedSourcePackage::import(bytes,source.document_id().clone(),Sha256::digest(bytes).into(),source.limits).map_err(|_|E::Readback)?;
            let forms=ImportedDocumentForms::import(output).map_err(|_|E::Readback)?;
            let fields=ImportedDocumentFields::import(&forms).map_err(|_|E::Readback)?;
            if fields.fields.len()!=self.fields.len()+1 {return Err(E::Readback);}
            let index=SourceFieldMeaningIndex::import(&fields,limits).map_err(|_|E::Readback)?;
            let (new,meaning)=fields.fields.iter().zip(index.observations()).find(|(f,_)|f.native_begin_id==id).ok_or(E::Readback)?;
            if new.native_kind!="CROSSREF"||!matches!(&meaning.meaning,ImportedFieldMeaning::BookmarkCrossReference{command} if command.command_sha256==expected&&matches!(command.target,SourceBookmarkResolution::Bound{..})) {return Err(E::Readback);}
            let out=forms.source().parts().iter().find(|p|p.path()==part.path()).and_then(|p|p.xml()).ok_or(E::Readback)?;
            let exact=xml.with_source_bytes(|x|out.with_source_bytes(|y|{
                let (a,b)=(run_span.start(),run_span.end());let i=a+before.len();let j=i+(b-a);let k=j+after.len();
                y.len()==x.len()+before.len()+after.len()&&y.get(..a)==x.get(..a)&&y.get(a..i)==Some(before.as_bytes())
                    &&y.get(i..j)==x.get(a..b)&&y.get(j..k)==Some(after.as_bytes())&&y.get(k..)==x.get(b..)
            }));
            if !exact{return Err(E::Preservation);}Ok(())
        }).map_err(|_|E::Writer)??;
        let receipt = SourceBookmarkInsertionReceipt {
            profile: "hwpx-agent.source-bookmark-new-insertion/same-command-envelope-v1",
            source_package_sha256: source.receipt().source_package_sha256,
            output_package_sha256: artifact.sha256(),
            source_run_sha256: request.run.fingerprint_sha256,
            source_envelope_sha256: template.begin_anchor.fingerprint_sha256,
            command_sha256: expected,
            inserted_fields: 1,
            original_fields: self.fields.len(),
            outside_insertions_exact: true,
            original_selected_run_exact: true,
            same_command_source_envelope_only: true,
            existing_display_text_is_not_evaluated_or_refreshed: true,
            native_currentness_execution_or_publication_qualified: false,
        };
        let _ =
            super::semantics::source_index::bounded_digest(&receipt, limits.config().output_bytes)
                .map_err(|_| E::Limit)?;
        Ok(SourceBookmarkInsertionCandidate { artifact, receipt })
    }
}
