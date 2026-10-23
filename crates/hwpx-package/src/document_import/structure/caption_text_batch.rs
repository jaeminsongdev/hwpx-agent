//! One transaction for multiple exact plain caption leaves; no per-leaf package import.
mod review_output;
use super::{ImportedDocumentStructure,caption_text::{CaptionTextOutputError as E,escaped_expected}};
use crate::{BoundedZipReader,IdIndexLimits,IdRuleProfile,PackageArtifact,PackageGraphLimits,
    PackagePath,PatchIntent,PatchLimits,PatchText,PreservationRuleProfile,PreservingPatchEngine,
    PreservingWriter,PreservingXmlDocument,WriterError,WriterLimits,XmlElementSelector};
use crate::document_import::{ImportedSourcePackage,reference_targets::numbering::ImportedCaptionNumbering};
use domain_ir::{LogicalId,ReferenceAuxiliaryLimits,SourceAnchorHandle};
use serde::Serialize;
use sha2::{Digest as _,Sha256};
use std::{collections::{BTreeMap,BTreeSet},fmt,io::Cursor};
use super::caption_edit_batch::{CaptionLayoutReplacement,CaptionLayoutBatchChange,
    CaptionEditBatchOutputCandidate,CaptionEditBatchOutputReceipt};
use crate::{PatchAttributeValue,XmlAttributeSelector};
use domain_ir::NativeCaptionSide;
use super::caption_style_batch::{self,CaptionStyleReplacement};
use super::caption_numbering_sequence::{self,NativeNumberSequenceReplacement};
use super::caption_edit_map::OutputEditMap;
use super::caption_number_topology::{self,NativeNumberTopologyRequest};
use super::caption_topology::{self,SourceCaptionTopologyRequest};

pub struct CaptionTextReplacement<'a> {pub caption_id:&'a LogicalId,pub text_id:&'a LogicalId,pub replacement:&'a str}
impl fmt::Debug for CaptionTextReplacement<'_> {
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("CaptionTextReplacement(<redacted>)")}
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct CaptionTextBatchChange {
    pub source_caption_id:LogicalId,pub source_text_id:LogicalId,
    pub source_text_sha256:[u8;32],pub output_text_sha256:[u8;32],pub output_text_bytes:usize,
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct CaptionTextBatchOutputReceipt {
    pub qualification:&'static str,
    pub source_package_sha256:[u8;32],pub output_package_sha256:[u8;32],pub output_bytes:usize,
    pub requested_leaves:usize,pub changed_leaves:usize,pub changed_parts:usize,
    pub changes:Vec<CaptionTextBatchChange>,
    pub observed_protection_parts:usize,pub observed_protection_element_visits:usize,
    pub id_rule_profile:&'static str,
    pub outside_selected_leaf_edits_exact:bool,
    pub complete_auxiliary_state_and_protection_verified:bool,pub execution_publication_authority:bool,
}
pub struct CaptionTextBatchOutputCandidate {artifact:PackageArtifact,receipt:CaptionTextBatchOutputReceipt}
impl fmt::Debug for CaptionTextBatchOutputCandidate {
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("CaptionTextBatchOutputCandidate(<redacted>; not_sequence_or_service_authority)")}
}
impl CaptionTextBatchOutputCandidate {
    #[must_use] pub const fn receipt(&self)->&CaptionTextBatchOutputReceipt {&self.receipt}
    /// Writer integrity only, not service/ACL/head or publication authorization.
    /// # Errors
    /// Rejects artifact integrity failures before exposing candidate bytes.
    pub fn with_verified_bytes<T>(&self,consume:impl FnOnce(&[u8])->T)->Result<T,WriterError> {self.artifact.with_verified_bytes(consume)}
}
pub(super) struct Edit {pub start:usize,pub end:usize,pub bytes:Vec<u8>}
pub(super) struct PartEdits<'a> {pub xml:&'a PreservingXmlDocument,pub edits:Vec<Edit>}

impl ImportedDocumentStructure {
    /// Verifies one original source, applies one bounded transaction, then fully
    /// imports one output. One invalid/protected selection rejects the whole batch.
    /// # Errors
    /// Keeps original source/value/selection/protection/ID/writer/readback limits;
    /// rejects empty/duplicate requests and batches with no semantic change.
    pub fn lower_caption_text_batch_candidate(&self,fresh:&[u8],requests:&[CaptionTextReplacement<'_>],
        limits:ReferenceAuxiliaryLimits,writer:WriterLimits,
    )->Result<CaptionTextBatchOutputCandidate,E> {
        self.lower_caption_text_batch_checked(fresh,requests,limits,writer,
            ||self.verify_source(fresh).map(|_|()).map_err(|_|E::Source))
    }
    fn lower_caption_text_batch_checked(&self,fresh:&[u8],requests:&[CaptionTextReplacement<'_>],
        limits:ReferenceAuxiliaryLimits,writer:WriterLimits,check_source:impl FnOnce()->Result<(),E>,
    )->Result<CaptionTextBatchOutputCandidate,E> {
        let combined=self.lower_caption_edit_batch_checked(fresh,requests,&[],limits,writer,check_source)?;
        let r=combined.receipt;
        let receipt=CaptionTextBatchOutputReceipt {
            qualification:"source_bound_atomic_plain_caption_leaf_batch_not_sequence_full_protection_native_or_service_authority",
            source_package_sha256:r.source_package_sha256,output_package_sha256:r.output_package_sha256,output_bytes:r.output_bytes,
            requested_leaves:r.requested_text_leaves,changed_leaves:r.text_changes.len(),changed_parts:r.changed_parts,changes:r.text_changes,
            observed_protection_parts:r.observed_protection_parts,observed_protection_element_visits:r.observed_protection_element_visits,
            id_rule_profile:r.id_rule_profile,outside_selected_leaf_edits_exact:r.outside_selected_edits_exact,
            complete_auxiliary_state_and_protection_verified:r.complete_auxiliary_state_and_protection_verified,
            execution_publication_authority:r.execution_publication_authority};
        Ok(CaptionTextBatchOutputCandidate {artifact:combined.artifact,receipt})
    }
    pub(super) fn lower_caption_edit_batch_checked(&self,fresh:&[u8],requests:&[CaptionTextReplacement<'_>],
        layouts:&[CaptionLayoutReplacement<'_>],limits:ReferenceAuxiliaryLimits,writer:WriterLimits,
        check_source:impl FnOnce()->Result<(),E>,
    )->Result<CaptionEditBatchOutputCandidate,E> {
        self.lower_caption_edit_batch_using_state(fresh,requests,layouts,limits,writer,None,check_source)
    }
    pub(in crate::document_import) fn lower_caption_edit_batch_using_state(&self,fresh:&[u8],requests:&[CaptionTextReplacement<'_>],
        layouts:&[CaptionLayoutReplacement<'_>],limits:ReferenceAuxiliaryLimits,writer:WriterLimits,
        state:Option<&crate::document_import::reference_targets::caption_source_state::ImportedCaptionSourceState<'_>>,
        check_source:impl FnOnce()->Result<(),E>,
    )->Result<CaptionEditBatchOutputCandidate,E> {
        self.lower_caption_content_batch_using_state(fresh,requests,layouts,&[],limits,writer,state,check_source)
    }
    pub(in crate::document_import) fn lower_caption_content_batch_using_state(&self,fresh:&[u8],requests:&[CaptionTextReplacement<'_>],
        layouts:&[CaptionLayoutReplacement<'_>],styles:&[CaptionStyleReplacement<'_>],limits:ReferenceAuxiliaryLimits,writer:WriterLimits,
        state:Option<&crate::document_import::reference_targets::caption_source_state::ImportedCaptionSourceState<'_>>,
        check_source:impl FnOnce()->Result<(),E>,
    )->Result<CaptionEditBatchOutputCandidate,E> {
        self.lower_caption_sequence_batch_using_state(fresh,requests,layouts,styles,None,limits,writer,state,check_source)
    }
    pub(in crate::document_import) fn lower_caption_sequence_batch_using_state(&self,fresh:&[u8],requests:&[CaptionTextReplacement<'_>],
        layouts:&[CaptionLayoutReplacement<'_>],styles:&[CaptionStyleReplacement<'_>],sequence:Option<&NativeNumberSequenceReplacement<'_>>,
        limits:ReferenceAuxiliaryLimits,writer:WriterLimits,
        state:Option<&crate::document_import::reference_targets::caption_source_state::ImportedCaptionSourceState<'_>>,
        check_source:impl FnOnce()->Result<(),E>,
    )->Result<CaptionEditBatchOutputCandidate,E> {
        self.lower_caption_topology_batch_using_state(fresh,requests,layouts,styles,sequence,None,limits,writer,state,check_source)
    }
    pub(in crate::document_import) fn lower_caption_topology_batch_using_state(&self,fresh:&[u8],requests:&[CaptionTextReplacement<'_>],
        layouts:&[CaptionLayoutReplacement<'_>],styles:&[CaptionStyleReplacement<'_>],sequence:Option<&NativeNumberSequenceReplacement<'_>>,topology:Option<&NativeNumberTopologyRequest<'_>>,
        limits:ReferenceAuxiliaryLimits,writer:WriterLimits,
        state:Option<&crate::document_import::reference_targets::caption_source_state::ImportedCaptionSourceState<'_>>,
        check_source:impl FnOnce()->Result<(),E>,
    )->Result<CaptionEditBatchOutputCandidate,E> {
        self.lower_caption_structure_batch_using_state(fresh,requests,layouts,styles,sequence,topology,None,limits,writer,state,check_source)
    }
    pub(in crate::document_import) fn lower_caption_structure_batch_using_state(&self,fresh:&[u8],requests:&[CaptionTextReplacement<'_>],
        layouts:&[CaptionLayoutReplacement<'_>],styles:&[CaptionStyleReplacement<'_>],sequence:Option<&NativeNumberSequenceReplacement<'_>>,topology:Option<&NativeNumberTopologyRequest<'_>>,captions:Option<&SourceCaptionTopologyRequest<'_>>,
        limits:ReferenceAuxiliaryLimits,writer:WriterLimits,
        state:Option<&crate::document_import::reference_targets::caption_source_state::ImportedCaptionSourceState<'_>>,
        check_source:impl FnOnce()->Result<(),E>,
    )->Result<CaptionEditBatchOutputCandidate,E> {
        if let Some(state)=state {state.validate_compiler_input(self,limits)?;}
        if sequence.is_some()&&topology.is_some(){return Err(E::Value);}
        if captions.is_some()&&(sequence.is_some()||topology.is_some()){return Err(E::Value);}
        if requests.is_empty()&&layouts.is_empty()&&styles.is_empty()&&sequence.is_none()&&topology.is_none()&&captions.is_none(){return Err(E::Value);}
        let number_requests=if let Some(sequence)=sequence {
            if state.is_none(){return Err(E::Source);}caption_numbering_sequence::preflight(sequence,limits)?
        }else if let Some(topology)=topology {if state.is_none(){return Err(E::Source);}caption_number_topology::preflight(topology,limits)?}
        else if let Some(captions)=captions {if state.is_none(){return Err(E::Source);}caption_topology::reject_deleted_selections(captions,requests,layouts,styles)?;caption_topology::preflight(captions,limits)?}else{0};
        let maximum=limits.config().items_per_kind.min(PatchLimits::default().config().max_intents);
        if requests.len().checked_add(layouts.len()).and_then(|n|n.checked_add(styles.len())).and_then(|n|n.checked_add(number_requests)).filter(|n|*n<=maximum).is_none(){return Err(E::Limit);}
        for request in layouts {
            let layout=request.layout;
            if layout.width_hwpunit < -1 {return Err(E::Value);}
            if layout.width_hwpunit.max(0) as u32>limits.config().extent_hwpunit
                ||layout.gap_hwpunit>limits.config().extent_hwpunit||layout.last_width_hwpunit>limits.config().extent_hwpunit{return Err(E::Limit);}
        }
        let mut values=Vec::new();values.try_reserve_exact(requests.len()).map_err(|_|E::Limit)?;
        let mut requested_bytes=0_usize;
        for request in requests {
            if request.replacement.len()>limits.config().text_bytes{return Err(E::Limit);}
            requested_bytes=requested_bytes.checked_add(request.replacement.len()).filter(|n|*n<=limits.config().output_bytes).ok_or(E::Limit)?;
            values.push(PatchText::new(request.replacement).map_err(|_|E::Value)?);
        }
        check_source()?;
        self.lower_caption_edit_batch_verified(fresh,requests,layouts,styles,sequence,topology,captions,limits,writer,state,values)
    }
    // Large lowering body is non-generic: source-proof callbacks do not duplicate
    // the patch/writer/readback implementation for each public entry point.
    fn lower_caption_edit_batch_verified(&self,fresh:&[u8],requests:&[CaptionTextReplacement<'_>],
        layouts:&[CaptionLayoutReplacement<'_>],styles:&[CaptionStyleReplacement<'_>],sequence:Option<&NativeNumberSequenceReplacement<'_>>,topology:Option<&NativeNumberTopologyRequest<'_>>,captions:Option<&SourceCaptionTopologyRequest<'_>>,
        limits:ReferenceAuxiliaryLimits,writer:WriterLimits,
        state:Option<&crate::document_import::reference_targets::caption_source_state::ImportedCaptionSourceState<'_>>,
        values:Vec<PatchText>,
    )->Result<CaptionEditBatchOutputCandidate,E> {
        let owned_numbering;let owned_frames;
        let (numbering,frames)=if let Some(state)=state {(state.numbering(),state.frames())}else{
            let map=|error|match error {crate::document_import::reference_targets::numbering::CaptionNumberingImportError::Limit=>E::Limit,_=>E::Source};
            owned_numbering=ImportedCaptionNumbering::import(self,limits).map_err(map)?;
            owned_frames=owned_numbering.import_frames(limits).map_err(map)?;
            (&owned_numbering,&owned_frames)
        };
        let mut text_index=BTreeMap::new();
        for (f,frame) in frames.frames().iter().enumerate(){for (s,segment) in frame.segments.iter().enumerate(){
            if text_index.insert(&segment.logical_source_id,(f,s)).is_some(){return Err(E::Selection);}
        }}
        let mut seen=BTreeSet::new();let mut intents=Vec::new();let mut changes=Vec::new();let mut expected=Vec::new();
        let mut parts=BTreeMap::<&PackagePath,PartEdits<'_>>::new();let mut guards=BTreeMap::new();
        let mut protection_visits=0_usize;let mut escaped_bytes=0_usize;
        for (request,value) in requests.iter().zip(values) {
            if !seen.insert(request.text_id){return Err(E::Selection);}
            let &(f,s)=text_index.get(request.text_id).ok_or(E::Selection)?;let frame=&frames.frames()[f];let segment=&frame.segments[s];
            if &frame.logical_caption_id!=request.caption_id{return Err(E::Selection);}
            let before=frames.plain_text(request.text_id).ok_or(E::Selection)?;
            if before==request.replacement {continue;}
            let opaque=request.text_id.as_str().strip_prefix("caption-segment-").ok_or(E::Selection)?;
            let anchor=SourceAnchorHandle {opaque_handle:LogicalId::parse(opaque).map_err(|_|E::Selection)?,fingerprint_sha256:segment.source_fingerprint_sha256};
            let resolved=self.source().resolve_anchor(&anchor).map_err(|_|E::Selection)?;
            let part=resolved.part();let xml=part.xml().ok_or(E::Selection)?;let index=resolved.element_index().ok_or(E::Selection)?;let node=&xml.elements()[index];
            if !super::named(node,"t")||node.first_child().is_some()
                ||!node.parent().is_some_and(|p|super::named(&xml.elements()[p],"run")){return Err(E::Selection);}
            if !guards.contains_key(part.path()) {
                protection_visits=protection_visits.checked_add(xml.elements().len().checked_mul(2).ok_or(E::Limit)?).ok_or(E::Limit)?;
                guards.insert(part.path(),observed_protection(xml)?);
            }
            if guards.get(part.path()).and_then(|g|g.get(index)).copied().ok_or(E::Selection)?{return Err(E::Protection);}
            let escaped=escaped_expected(request.replacement,limits.config().output_bytes)?;
            let edit=if node.is_empty(){
                let name=xml.source_text(node.start_name_span()).map_err(|_|E::Selection)?;
                Edit {start:node.start_tag_span().end().checked_sub(2).ok_or(E::Selection)?,end:node.start_tag_span().end(),bytes:format!(">{escaped}</{name}>").into_bytes()}
            }else{let span=node.content_span().ok_or(E::Selection)?;Edit {start:span.start(),end:span.end(),bytes:escaped.into_bytes()}};
            escaped_bytes=escaped_bytes.checked_add(edit.bytes.len()).filter(|n|*n<=limits.config().output_bytes).ok_or(E::Limit)?;
            parts.entry(part.path()).or_insert_with(||PartEdits {xml,edits:Vec::new()}).edits.push(edit);
            intents.push(PatchIntent::ReplaceLeafText {target:XmlElementSelector::bind(part.path(),xml,index).map_err(|_|E::Selection)?,value});
            changes.push(CaptionTextBatchChange {source_caption_id:request.caption_id.clone(),source_text_id:request.text_id.clone(),
                source_text_sha256:Sha256::digest(before.as_bytes()).into(),output_text_sha256:Sha256::digest(request.replacement.as_bytes()).into(),output_text_bytes:request.replacement.len()});
            let caption=xml.elements().get(frame.source_position.xml_element_ordinal).ok_or(E::Selection)?;
            if !super::named(caption,"caption"){return Err(E::Selection);}
            expected.push((part.path().clone(),node.start_tag_span().start(),caption.start_tag_span().start(),request.replacement));
        }
        let mut layout_changes=Vec::new();let mut expected_layouts=Vec::new();let mut seen_layouts=BTreeSet::new();
        let mut layout_subtree_guards=BTreeMap::new();
        if !layouts.is_empty() {
            let frame_index:BTreeMap<_,_>=frames.frames().iter().map(|f|(&f.logical_caption_id,f)).collect();
            let envelopes=numbering.caption_import().envelopes();
            let envelope_index:BTreeMap<_,_>=envelopes.iter().enumerate().map(|(i,c)|(c.logical_caption_id(),i)).collect();
            for request in layouts {
                if !seen_layouts.insert(request.caption_id){return Err(E::Selection);}
                let frame=*frame_index.get(request.caption_id).ok_or(E::Selection)?;
                let ordinal=*envelope_index.get(request.caption_id).ok_or(E::Selection)?;
                let before=envelopes[ordinal].native_envelope();let layout=request.layout;
                let opaque=request.caption_id.as_str().strip_prefix("caption-").ok_or(E::Selection)?;
                let anchor=SourceAnchorHandle {opaque_handle:LogicalId::parse(opaque).map_err(|_|E::Selection)?,fingerprint_sha256:frame.source_fingerprint_sha256};
                let resolved=self.source().resolve_anchor(&anchor).map_err(|_|E::Selection)?;
                let part=resolved.part();let xml=part.xml().ok_or(E::Selection)?;let index=resolved.element_index().ok_or(E::Selection)?;
                let node=&xml.elements()[index];if !super::named(node,"caption"){return Err(E::Selection);}
                if !guards.contains_key(part.path()) {
                    protection_visits=protection_visits.checked_add(xml.elements().len().checked_mul(2).ok_or(E::Limit)?).ok_or(E::Limit)?;
                    guards.insert(part.path(),observed_protection(xml)?);
                }
                if guards.get(part.path()).and_then(|g|g.get(index)).copied().ok_or(E::Selection)?{return Err(E::Protection);}
                if !layout_subtree_guards.contains_key(part.path()) {
                    protection_visits=protection_visits.checked_add(xml.elements().len().checked_mul(2).ok_or(E::Limit)?).ok_or(E::Limit)?;
                    layout_subtree_guards.insert(part.path(),observed_layout_subtree_protection(xml)?);
                }
                if layout_subtree_guards.get(part.path()).and_then(|g|g.get(index)).copied().ok_or(E::Selection)?{return Err(E::Protection);}
                let values=[("side",match layout.side {NativeCaptionSide::Left=>"LEFT",NativeCaptionSide::Right=>"RIGHT",NativeCaptionSide::Top=>"TOP",NativeCaptionSide::Bottom=>"BOTTOM"}.to_owned(),before.side==layout.side),
                    ("fullSz",if layout.full_size {"1"}else{"0"}.to_owned(),before.full_size==layout.full_size),
                    ("width",layout.width_hwpunit.to_string(),before.width_hwpunit==layout.width_hwpunit),
                    ("gap",layout.gap_hwpunit.to_string(),before.gap_hwpunit==layout.gap_hwpunit),
                    ("lastWidth",layout.last_width_hwpunit.to_string(),before.last_width_hwpunit==layout.last_width_hwpunit)];
                let initial=intents.len();
                for (name,value,same) in values {
                    let (attribute,attr)=node.attributes().iter().enumerate().find(|(_,a)|!a.is_namespace_declaration()
                        &&a.name().namespace().is_none()&&a.name().local_name()==name).ok_or(E::Source)?;
                    if same{continue;}
                    escaped_bytes=escaped_bytes.checked_add(value.len()).filter(|n|*n<=limits.config().output_bytes).ok_or(E::Limit)?;
                    let span=attr.value_span();
                    parts.entry(part.path()).or_insert_with(||PartEdits {xml,edits:Vec::new()}).edits.push(Edit {start:span.start(),end:span.end(),bytes:value.as_bytes().to_vec()});
                    intents.push(PatchIntent::ReplaceAttribute {target:XmlAttributeSelector::bind(part.path(),xml,index,attribute).map_err(|_|E::Selection)?,
                        value:PatchAttributeValue::Text(PatchText::new(&value).map_err(|_|E::Value)?)});
                }
                if intents.len()!=initial {
                    layout_changes.push(CaptionLayoutBatchChange {source_caption_id:request.caption_id.clone(),
                        source_caption_sha256:before.opaque_native_state_sha256.clone(),requested_layout:layout,changed_attributes:intents.len()-initial});
                    expected_layouts.push((part.path().clone(),node.start_tag_span().start(),layout));
                }
            }
        }
        let mut content_subtree_guards=BTreeMap::new();
        let style_plan=caption_style_batch::plan(self,frames,styles,limits,&mut parts,&mut guards,&mut content_subtree_guards,
            &mut protection_visits,&mut escaped_bytes,&mut intents)?;
        let number_plan=caption_numbering_sequence::plan(self,state,sequence,limits,&mut parts,&mut guards,&mut content_subtree_guards,
            &mut protection_visits,&mut escaped_bytes,&mut intents)?;
        let mut topology_plan=caption_number_topology::plan(self,state,topology,limits,&mut parts,&mut guards,&mut content_subtree_guards,
            &mut protection_visits,&mut escaped_bytes,&mut intents)?;
        let mut caption_plan=caption_topology::plan(self,state,captions,limits,&mut parts,&mut guards,&mut content_subtree_guards,
            &mut protection_visits,&mut escaped_bytes,&mut intents)?;
        if intents.is_empty(){return Err(E::NoChange);}
        if intents.len()>PatchLimits::default().config().max_intents{return Err(E::Limit);}
        for part in parts.values_mut(){
            part.edits.sort_by_key(|edit|edit.start);
            if part.edits.windows(2).any(|w|w[0].end>w[1].start){return Err(E::Selection);}
            part.edits.iter().try_fold(part.xml.original_len(),|n,e|n.checked_sub(e.end-e.start).and_then(|n|n.checked_add(e.bytes.len()))).filter(|n|*n<=limits.config().output_bytes).ok_or(E::Limit)?;
        }
        let source=self.source();let zip=source.limits.zip().map_err(|_|E::Source)?;
        let profile=if captions.is_some(){IdRuleProfile::hwpml_2011_caption_owner_v8()}else{IdRuleProfile::hwpml_2011_shape_v6()};
        let mut reader=BoundedZipReader::open(Cursor::new(fresh),zip).map_err(|_|E::Source)?;
        let patch=PreservingPatchEngine::apply_with_limits_and_preservation_profile(&mut reader,&source.graph,PackageGraphLimits::default(),profile,IdIndexLimits::default(),PatchLimits::default(),PreservationRuleProfile::Hangul2020PreviewTextV2,&intents).map_err(|error| {
            let code=if let crate::PatchError::IdIndex(ref ids)=error {ids.validation().and_then(|r|r.issues().first()).map_or(error.code(),|i|i.code())}else{error.code()};E::Patch(code)
        })?;
        if patch.changed_parts()!=parts.len()||patch.added_parts()!=0||patch.parts().iter().any(|p|!parts.contains_key(p.path())&&p.source_sha256()!=Some(p.output_sha256())){return Err(E::Preservation);}
        let artifact=PreservingWriter::build(&patch,zip,PackageGraphLimits::default(),IdIndexLimits::default(),writer).map_err(|_|E::Writer)?;
        let mut output_review_import=None;
        artifact.with_verified_bytes(|bytes|->Result<(),E>{
            let output=ImportedSourcePackage::import(bytes,source.document_id().clone(),Sha256::digest(bytes).into(),source.limits).map_err(|_|E::Readback)?;
            let output_model=review_output::BatchOutputImport::import(output,numbering.receipt().review_body_inventory_sha256.is_some())?;
            let rebuilt=output_model.structure();
            let after_numbers=output_model.numbering(limits,&mut output_review_import)?;
            let after=after_numbers.import_frames(limits).map_err(|_|E::Readback)?;
            let expected_frames=caption_plan.expected_count(frames.frames().len());
            if after.frames().len()!=expected_frames{return Err(E::Readback);}
            number_plan.verify(&rebuilt,&after_numbers,limits)?;
            let edit_map=OutputEditMap::new(&rebuilt,&parts)?;
            style_plan.verify(&after,&edit_map)?;
            topology_plan.verify(&rebuilt,&after_numbers,&edit_map,limits)?;
            caption_plan.verify(&rebuilt,&after_numbers,&after,&edit_map,limits)?;
            let mut after_text=BTreeMap::new();
            if !expected.is_empty(){for frame in after.frames(){for segment in &frame.segments {
                if after_text.insert(&segment.logical_source_id,(&frame.logical_caption_id,segment)).is_some(){return Err(E::Readback);}
            }}}
            for (path,point,caption_point,text) in &expected {
                let (part,index)=edit_map.original_element(path,*point)?;
                let (caption_part,caption_index)=edit_map.original_element(path,*caption_point)?;
                let id=LogicalId::parse(format!("caption-segment-{}",part.element_anchor(index).ok_or(E::Readback)?.opaque_handle.as_str())).map_err(|_|E::Readback)?;
                let caption_id=LogicalId::parse(format!("caption-{}",caption_part.element_anchor(caption_index).ok_or(E::Readback)?.opaque_handle.as_str())).map_err(|_|E::Readback)?;
                let &(owner,segment)=after_text.get(&id).ok_or(E::Readback)?;
                if owner!=&caption_id||after.plain_text(&id)!=Some(*text)||segment.decoded_text_sha256!=Some(Sha256::digest(text.as_bytes()).into()){return Err(E::Readback);}
            }
            let envelopes=after_numbers.caption_import().envelopes();
            if envelopes.len()!=expected_frames{return Err(E::Readback);}
            let envelope_index:BTreeMap<_,_>=envelopes.iter().map(|e|(e.logical_caption_id(),e)).collect();
            for (path,point,layout) in &expected_layouts {
                let (part,index)=edit_map.original_element(path,*point)?;
                let id=LogicalId::parse(format!("caption-{}",part.element_anchor(index).ok_or(E::Readback)?.opaque_handle.as_str())).map_err(|_|E::Readback)?;
                let after=envelope_index.get(&id).ok_or(E::Readback)?.native_envelope();
                if after.side!=layout.side||after.full_size!=layout.full_size||after.width_hwpunit!=layout.width_hwpunit
                    ||after.gap_hwpunit!=layout.gap_hwpunit||after.last_width_hwpunit!=layout.last_width_hwpunit{return Err(E::Readback);}
            }
            for (path,part) in &parts {
                let new=rebuilt.source().parts().iter().find(|p|p.path()==*path).and_then(|p|p.xml()).ok_or(E::Readback)?;
                if !part.xml.with_source_bytes(|old|new.with_source_bytes(|new|exact_edits(old,new,&part.edits))){return Err(E::Preservation);}
            }Ok(())
        }).map_err(|_|E::Writer)??;
        let receipt=CaptionEditBatchOutputReceipt {qualification:if captions.is_some(){"source_bound_atomic_caption_creation_deletion_and_retained_content_not_counter_full_protection_native_CAS_or_service_authority"}
            else if topology.is_some(){"source_bound_atomic_caption_content_and_number_control_topology_not_counter_full_protection_native_CAS_or_service_authority"}
            else if sequence.is_some(){"source_bound_atomic_caption_content_and_complete_observed_number_stream_not_counter_interpretation_full_protection_native_CAS_or_service_authority"}
            else if styles.is_empty(){"source_bound_atomic_caption_text_and_layout_batch_not_sequence_full_protection_native_CAS_or_service_authority"}
            else{"source_bound_atomic_caption_text_layout_and_style_references_not_effective_style_sequence_full_protection_native_CAS_or_service_authority"},
            source_package_sha256:source.receipt().source_package_sha256,output_package_sha256:artifact.sha256(),output_bytes:artifact.size_bytes(),
            requested_text_leaves:requests.len(),requested_layouts:layouts.len(),changed_parts:parts.len(),text_changes:changes,layout_changes,
            observed_protection_parts:guards.len(),observed_protection_element_visits:protection_visits,
            id_rule_profile:profile.version(),outside_selected_edits_exact:true,output_review_import,complete_auxiliary_state_and_protection_verified:false,execution_publication_authority:false};
        Ok(CaptionEditBatchOutputCandidate {artifact,receipt,style_changes:style_plan.changes,number_sequence:number_plan.receipt,number_topology:topology_plan.receipt,caption_topology:caption_plan.receipt})
    }
}
impl crate::document_import::forms::VerifiedFormReconstruction<'_> {
    /// Exact operation-local original proof reuse; not cached service authorization.
    /// # Errors
    /// Rejects foreign original/proof/bytes and every pure batch-path failure.
    pub fn lower_caption_text_batch_candidate(&self,original:&crate::document_import::forms::ImportedDocumentForms,
        fresh:&[u8],requests:&[CaptionTextReplacement<'_>],limits:ReferenceAuxiliaryLimits,writer:WriterLimits,
    )->Result<CaptionTextBatchOutputCandidate,E> {
        original.body_structure().lower_caption_text_batch_checked(fresh,requests,limits,writer,||{
            let rebuilt=self.for_original(original).map_err(|_|E::Source)?;
            if fresh!=rebuilt.source().original.as_ref(){return Err(E::Source);}Ok(())
        })
    }
}
pub(in crate::document_import) fn observed_protection(xml:&PreservingXmlDocument)->Result<Vec<bool>,E> {
    let mut blocked=Vec::new();blocked.try_reserve_exact(xml.elements().len()).map_err(|_|E::Limit)?;blocked.resize(xml.elements().len(),false);
    // Match the original leaf guard: HP lock on any ancestor, TC protect and
    // direct table SZ protect. Missing flags remain unknown, not authorization.
    for (i,node) in xml.elements().iter().enumerate(){
        if node.name().namespace()!=Some(crate::HANCOM_2020_PARAGRAPH_NAMESPACE){continue;}
        blocked[i]|=node.attributes().iter().any(|a|a.name().namespace().is_none()
            &&(a.name().local_name()=="lock"||(super::named(node,"tc")&&a.name().local_name()=="protect"))&&!matches!(a.semantic_value(),"0"|"false"));
        if super::named(node,"sz")&&node.attributes().iter().any(|a|a.name().namespace().is_none()&&a.name().local_name()=="protect"&&!matches!(a.semantic_value(),"0"|"false")) {
            if let Some(parent)=node.parent().filter(|p|super::named(&xml.elements()[*p],"tbl")){blocked[parent]=true;}
        }
    }
    for (i,node) in xml.elements().iter().enumerate(){if let Some(parent)=node.parent(){if parent>=i{return Err(E::Source);}let inherited=blocked[parent];blocked[i]|=inherited;}}
    Ok(blocked)
}
// Preserve the original container guard as well: a layout change cannot bypass
// a protected table/cell inside its caption. One reverse propagation per part,
// not the original full descendant scan for every selected caption.
fn observed_layout_subtree_protection(xml:&PreservingXmlDocument)->Result<Vec<bool>,E> {
    let mut blocked=Vec::new();blocked.try_reserve_exact(xml.elements().len()).map_err(|_|E::Limit)?;
    for node in xml.elements() {
        let flag=if super::named(node,"tc")||super::named(node,"sz")&&node.parent().is_some_and(|p|super::named(&xml.elements()[p],"tbl")) {Some("protect")}
            else if super::named(node,"tbl"){Some("lock")}else{None};
        blocked.push(flag.is_some_and(|name|node.attributes().iter().any(|a|a.name().namespace().is_none()
            &&a.name().local_name()==name&&!matches!(a.semantic_value(),"0"|"false"))));
    }
    for i in (0..xml.elements().len()).rev() {
        if let Some(parent)=xml.elements()[i].parent(){if parent>=i{return Err(E::Source);}let child=blocked[i];blocked[parent]|=child;}
    }
    Ok(blocked)
}
fn exact_edits(old:&[u8],new:&[u8],edits:&[Edit])->bool {
    let(mut before,mut after)=(0_usize,0_usize);
    for edit in edits {
        let Some(same)=old.get(before..edit.start)else{return false};let Some(end)=after.checked_add(same.len())else{return false};
        if new.get(after..end)!=Some(same){return false;}after=end;
        let Some(end)=after.checked_add(edit.bytes.len())else{return false};if new.get(after..end)!=Some(edit.bytes.as_slice()){return false;}
        before=edit.end;after=end;
    }new.get(after..)==old.get(before..)
}
