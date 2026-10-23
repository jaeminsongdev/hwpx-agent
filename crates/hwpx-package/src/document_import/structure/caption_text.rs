//! One source-bound plain caption text leaf edit. Not a sequence compiler or service grant.
use super::ImportedDocumentStructure;
use crate::{BoundedZipReader, IdIndexLimits, IdRuleProfile, PackageArtifact, PackageGraphLimits,
    PatchIntent, PatchLimits, PatchText, PreservationRuleProfile, PreservingPatchEngine,
    PreservingWriter, WriterError, WriterLimits, XmlElementSelector};
use crate::document_import::{ImportedSourcePackage, reference_targets::numbering::ImportedCaptionNumbering};
use domain_ir::{LogicalId, ReferenceAuxiliaryLimits};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use std::{fmt,io::Cursor};
use thiserror::Error;

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct CaptionTextOutputReceipt {
    pub qualification: &'static str,
    pub source_package_sha256: [u8;32],
    pub output_package_sha256: [u8;32],
    pub source_caption_sha256: [u8;32],
    pub output_caption_sha256: [u8;32],
    pub source_text_sha256: [u8;32],
    pub output_text_sha256: [u8;32],
    pub output_text_bytes: usize,
    pub output_bytes: usize,
    pub id_rule_profile: &'static str,
    pub outside_selected_leaf_edit_exact: bool,
    pub numbering_style_and_other_caption_content_preserved: bool,
    pub complete_auxiliary_state_and_protection_verified: bool,
    pub execution_publication_authority: bool,
}
pub struct CaptionTextOutputCandidate {artifact:PackageArtifact,receipt:CaptionTextOutputReceipt}
impl fmt::Debug for CaptionTextOutputCandidate {
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("CaptionTextOutputCandidate(<redacted>; one_plain_leaf_not_sequence_or_authority)")}
}
impl CaptionTextOutputCandidate {
    #[must_use] pub const fn receipt(&self)->&CaptionTextOutputReceipt {&self.receipt}
    /// Writer integrity only; never fresh service/ACL/head or publication authority.
    /// # Errors
    /// Rejects writer artifact integrity failures before exposing candidate bytes.
    pub fn with_verified_bytes<T>(&self,consume:impl FnOnce(&[u8])->T)->Result<T,WriterError> {self.artifact.with_verified_bytes(consume)}
}
#[derive(Clone,Copy,Debug,Eq,Error,PartialEq)]
pub enum CaptionTextOutputError {
    #[error("CAPTION_TEXT_SOURCE_REJECTED")] Source,
    #[error("CAPTION_TEXT_SELECTION_REJECTED")] Selection,
    #[error("CAPTION_TEXT_OBSERVED_PROTECTION")] Protection,
    #[error("CAPTION_TEXT_VALUE_REJECTED")] Value,
    #[error("CAPTION_TEXT_NO_CHANGE")] NoChange,
    #[error("CAPTION_TEXT_FINITE_LIMIT")] Limit,
    #[error("CAPTION_TEXT_PATCH_REJECTED:{0}")] Patch(&'static str),
    #[error("CAPTION_TEXT_WRITER_REJECTED")] Writer,
    #[error("CAPTION_TEXT_READBACK_REJECTED")] Readback,
    #[error("CAPTION_TEXT_PRESERVATION_REJECTED")] Preservation,
}
impl ImportedDocumentStructure {
    /// Changes one exact imported plain hp:t leaf, never guessed label/suffix spans
    /// or native numeric IDs. Preserves all other expanded bytes, styles and controls.
    /// # Errors
    /// Rejects stale source, foreign/opaque selectors, observed protection, invalid
    /// text, finite limits, no-op, original patch/writer and full output drift.
    pub fn lower_caption_text_candidate(&self,fresh:&[u8],caption_id:&LogicalId,text_id:&LogicalId,
        replacement:&str,limits:ReferenceAuxiliaryLimits,writer:WriterLimits,
    )->Result<CaptionTextOutputCandidate,CaptionTextOutputError> {
        self.lower_caption_text_checked(fresh,caption_id,text_id,replacement,limits,writer,
            ||self.verify_source(fresh).map(|_|()).map_err(|_|CaptionTextOutputError::Source))
    }
    fn lower_caption_text_checked(&self,fresh:&[u8],caption_id:&LogicalId,text_id:&LogicalId,
        replacement:&str,limits:ReferenceAuxiliaryLimits,writer:WriterLimits,
        check_source:impl FnOnce()->Result<(),CaptionTextOutputError>,
    )->Result<CaptionTextOutputCandidate,CaptionTextOutputError> {
        use CaptionTextOutputError as E;
        if replacement.len()>limits.config().text_bytes {return Err(E::Limit);}
        let value=PatchText::new(replacement).map_err(|_|E::Value)?;
        check_source()?;
        let map=|error|match error {crate::document_import::reference_targets::numbering::CaptionNumberingImportError::Limit=>E::Limit,_=>E::Source};
        let numbering=ImportedCaptionNumbering::import(self,limits).map_err(map)?;
        let frames=numbering.import_frames(limits).map_err(map)?;
        let frame_index=frames.frames().iter().position(|f|&f.logical_caption_id==caption_id).ok_or(E::Selection)?;
        let frame=&frames.frames()[frame_index];let segment_index=frame.segments.iter().position(|s|&s.logical_source_id==text_id).ok_or(E::Selection)?;
        let before=frames.plain_text(text_id).ok_or(E::Selection)?;
        if before==replacement {return Err(E::NoChange);}
        let mut selected=None;
        for part in self.source().parts() {let Some(xml)=part.xml() else {continue};
            for (i,node) in xml.elements().iter().enumerate() {
                if !super::named(node,"t"){continue;}
                let anchor=part.element_anchor(i).ok_or(E::Selection)?;
                if text_id.as_str()==format!("caption-segment-{}",anchor.opaque_handle.as_str()) {
                    if selected.replace((part,xml,i)).is_some(){return Err(E::Selection);}
                }
            }
        }
        let (part,xml,index)=selected.ok_or(E::Selection)?;
        super::review::cell_body_output::require_no_observed_mutation_protection(xml,index).map_err(|_|E::Protection)?;
        let mut ancestor=Some(index);
        while let Some(current)=ancestor {let node=&xml.elements()[current];
            if node.name().namespace()==Some(crate::HANCOM_2020_PARAGRAPH_NAMESPACE)&&node.attributes().iter().any(|a|a.name().namespace().is_none()&&a.name().local_name()=="lock"&&!matches!(a.semantic_value(),"0"|"false")){return Err(E::Protection);}
            ancestor=node.parent();
        }
        let node=&xml.elements()[index];
        let escaped=escaped_expected(replacement,limits.config().output_bytes)?;
        let (start,end,changed)=if node.is_empty() {
            let name=xml.source_text(node.start_name_span()).map_err(|_|E::Selection)?;
            (node.start_tag_span().end().checked_sub(2).ok_or(E::Selection)?,node.start_tag_span().end(),format!(">{escaped}</{name}>").into_bytes())
        } else {let content=node.content_span().ok_or(E::Selection)?;(content.start(),content.end(),escaped.into_bytes())};
        let output_len=xml.original_len().checked_sub(end-start).and_then(|n|n.checked_add(changed.len())).filter(|n|*n<=limits.config().output_bytes).ok_or(E::Limit)?;
        let intent=PatchIntent::ReplaceLeafText {target:XmlElementSelector::bind(part.path(),xml,index).map_err(|_|E::Selection)?,value};
        let source=self.source();let zip=source.limits.zip().map_err(|_|E::Source)?;
        let mut reader=BoundedZipReader::open(Cursor::new(fresh),zip).map_err(|_|E::Source)?;let profile=IdRuleProfile::hwpml_2011_shape_v6();
        let patch=PreservingPatchEngine::apply_with_limits_and_preservation_profile(&mut reader,&source.graph,PackageGraphLimits::default(),profile,IdIndexLimits::default(),PatchLimits::default(),PreservationRuleProfile::Hangul2020PreviewTextV2,&[intent]).map_err(|error| {
            let code=if let crate::PatchError::IdIndex(ref ids)=error {ids.validation().and_then(|r|r.issues().first()).map_or(error.code(),|issue|issue.code())} else {error.code()};E::Patch(code)
        })?;
        if patch.changed_parts()!=1||patch.added_parts()!=0||patch.parts().iter().any(|p|p.path()!=part.path()&&p.source_sha256()!=Some(p.output_sha256())) {return Err(E::Preservation);}
        let artifact=PreservingWriter::build(&patch,zip,PackageGraphLimits::default(),IdIndexLimits::default(),writer).map_err(|_|E::Writer)?;
        let output_caption=artifact.with_verified_bytes(|bytes|->Result<[u8;32],E> {
            let output=ImportedSourcePackage::import(bytes,source.document_id().clone(),Sha256::digest(bytes).into(),source.limits).map_err(|_|E::Readback)?;
            let rebuilt=ImportedDocumentStructure::import(output).map_err(|_|E::Readback)?;
            let after_numbers=ImportedCaptionNumbering::import(&rebuilt,limits).map_err(|_|E::Readback)?;
            let after=after_numbers.import_frames(limits).map_err(|_|E::Readback)?;
            if after.frames().len()!=frames.frames().len(){return Err(E::Readback);}
            let output_frame=after.frames().get(frame_index).ok_or(E::Readback)?;
            let output_segment=output_frame.segments.get(segment_index).ok_or(E::Readback)?;
            if after.plain_text(&output_segment.logical_source_id)!=Some(replacement)
                ||output_segment.decoded_text_sha256!=Some(Sha256::digest(replacement.as_bytes()).into()) {return Err(E::Readback);}
            let output_part=rebuilt.source().parts().iter().find(|p|p.path()==part.path()).and_then(|p|p.xml()).ok_or(E::Readback)?;
            if !xml.with_source_bytes(|old|output_part.with_source_bytes(|new| {
                new.len()==output_len&&new.get(..start)==old.get(..start)
                    &&new.get(start..start+changed.len())==Some(changed.as_slice())
                    &&new.get(start+changed.len()..)==old.get(end..)
            })){return Err(E::Preservation);}
            Ok(output_frame.source_fingerprint_sha256)
        }).map_err(|_|E::Writer)??;
        let receipt=CaptionTextOutputReceipt {qualification:"source_bound_one_plain_caption_leaf_only_not_sequence_native_or_authority",
            source_package_sha256:source.receipt().source_package_sha256,output_package_sha256:artifact.sha256(),
            source_caption_sha256:frame.source_fingerprint_sha256,output_caption_sha256:output_caption,
            source_text_sha256:Sha256::digest(before.as_bytes()).into(),output_text_sha256:Sha256::digest(replacement.as_bytes()).into(),
            output_text_bytes:replacement.len(),output_bytes:artifact.size_bytes(),id_rule_profile:profile.version(),outside_selected_leaf_edit_exact:true,
            numbering_style_and_other_caption_content_preserved:true,complete_auxiliary_state_and_protection_verified:false,execution_publication_authority:false};
        Ok(CaptionTextOutputCandidate {artifact,receipt})
    }
}
impl crate::document_import::forms::VerifiedFormReconstruction<'_> {
    /// Reuses the exact operation-local whole-source form reconstruction; never
    /// a cached ACL/head grant. Full candidate output readback is still required.
    /// # Errors
    /// Rejects a foreign proof/original, byte drift and every pure-path rejection.
    pub fn lower_caption_text_candidate(&self,original:&crate::document_import::forms::ImportedDocumentForms,
        fresh:&[u8],caption_id:&LogicalId,text_id:&LogicalId,replacement:&str,limits:ReferenceAuxiliaryLimits,writer:WriterLimits,
    )->Result<CaptionTextOutputCandidate,CaptionTextOutputError> {
        original.body_structure().lower_caption_text_checked(fresh,caption_id,text_id,replacement,limits,writer,|| {
            let rebuilt=self.for_original(original).map_err(|_|CaptionTextOutputError::Source)?;
            if fresh!=rebuilt.source().original.as_ref(){return Err(CaptionTextOutputError::Source);}Ok(())
        })
    }
}
pub(super) fn escaped_expected(text:&str,maximum:usize)->Result<String,CaptionTextOutputError> {
    use CaptionTextOutputError as E;
    let length=text.chars().try_fold(0_usize,|n,c|n.checked_add(match c {'&'=>5,'<'=>4,'>'=>4,'\r'=>5,_=>c.len_utf8()})).filter(|n|*n<=maximum).ok_or(E::Limit)?;
    let mut result=String::new();result.try_reserve_exact(length).map_err(|_|E::Limit)?;
    for ch in text.chars(){match ch {'&'=>result.push_str("&amp;"),'<'=>result.push_str("&lt;"),'>'=>result.push_str("&gt;"),'\r'=>result.push_str("&#13;"),_=>result.push(ch)}}Ok(result)
}
