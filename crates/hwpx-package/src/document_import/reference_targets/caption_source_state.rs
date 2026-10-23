//! Lossless joins of original caption models; no inferred native sequence or authority.
use super::{hash_json,ImportedDocumentStructure};
use super::numbering::{ImportedCaptionNumbering,CaptionNumberingImportError as E,
    CaptionNumberingImportReceipt,NativeNumberControlKind,context::{ImportedNumberingContext,
    NumberingContextImportReceipt,NumberingSourcePosition}};
use super::caption_frames::{ImportedCaptionFrames,CaptionFrameImportReceipt};
use super::caption_object_state::{ImportedCaptionObjectStates,CaptionObjectStateReceipt};
use domain_ir::{LogicalId,ReferenceAuxiliaryLimits};
use serde::Serialize;
use std::{collections::{BTreeMap,BTreeSet},fmt};
pub mod output;

#[derive(Clone,Copy,Debug,Eq,PartialEq,Serialize)]
pub struct CaptionStateCaptionLink {pub envelope_index:usize,pub frame_index:usize}
#[derive(Clone,Copy,Debug,Eq,PartialEq,Serialize)]
pub struct CaptionStateOwnerLink {
    pub owner_index:usize,pub object_state_index:usize,pub caption:Option<CaptionStateCaptionLink>,
}
#[derive(Clone,Copy,Debug,Eq,PartialEq,Serialize)]
#[serde(tag="kind",rename_all="snake_case")]
pub enum CaptionNumberingSourceEventKind {
    Owner {owner_index:usize},
    AutoNumber {control_index:usize,owner_index:Option<usize>},
    Restart {control_index:usize,owner_index:Option<usize>},
    SectionStart {section_start_index:usize},
}
#[derive(Clone,Eq,PartialEq,Serialize)]
pub struct CaptionNumberingSourceEvent {
    pub section_id:LogicalId,pub source_position:NumberingSourcePosition,
    pub event:CaptionNumberingSourceEventKind,
}
impl fmt::Debug for CaptionNumberingSourceEvent {
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("CaptionNumberingSourceEvent(<redacted>; XML_order_not_native_counter_order)")}
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct CaptionSourceStateReceipt {
    pub profile:&'static str,
    pub numbering:CaptionNumberingImportReceipt,pub context:NumberingContextImportReceipt,
    pub frames:CaptionFrameImportReceipt,pub object_states:CaptionObjectStateReceipt,
    pub joined_state_sha256:[u8;32],
    pub owner_links:usize,pub caption_links:usize,pub source_events:usize,
    pub sequence_interpretation_and_recalculation_qualified:bool,
    pub complete_auxiliary_state_and_protection_qualified:bool,pub execution_publication_authority:bool,
}
pub struct ImportedCaptionSourceState<'a> {
    source:&'a ImportedDocumentStructure,limits:ReferenceAuxiliaryLimits,
    numbering:ImportedCaptionNumbering<'a>,context:ImportedNumberingContext<'a>,
    frames:ImportedCaptionFrames<'a>,object_states:ImportedCaptionObjectStates<'a>,
    owners:Vec<CaptionStateOwnerLink>,events:Vec<CaptionNumberingSourceEvent>,receipt:CaptionSourceStateReceipt,
}
impl fmt::Debug for ImportedCaptionSourceState<'_> {
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("ImportedCaptionSourceState(<redacted>; source_assembly_not_complete_sequence_or_service_authority)")}
}
impl<'a> ImportedCaptionSourceState<'a> {
    /// Creates all constituent models from one original numbering/caption model.
    /// Does not reimport ZIP/XML/graph, infer labels/styles/start values, or replace
    /// missing/zero/stored numbers with resolved sequence values.
    /// # Errors
    /// Preserves constituent import errors and finite bounds; rejects incomplete,
    /// ambiguous or inconsistent joins without returning partial state.
    pub fn import(source:&'a ImportedDocumentStructure,limits:ReferenceAuxiliaryLimits)->Result<Self,E> {
        ImportedCaptionNumbering::import(source,limits)?.assemble_source_state(limits)
    }
    /// # Errors
    /// The actual immutable Form/review pair, never caller-created paragraph IDs or inferred visibility.
    pub fn import_review_bound(forms:&'a crate::document_import::forms::ImportedDocumentForms,
        review:&crate::document_import::structure::review::ImportedDocumentReviewBodies<'_>,limits:ReferenceAuxiliaryLimits)->Result<Self,E> {
        ImportedCaptionNumbering::import_review_bound(forms,review,limits)?.assemble_source_state(limits)
    }
    pub(in crate::document_import) fn validate_compiler_input(&self,original:&ImportedDocumentStructure,limits:ReferenceAuxiliaryLimits)
        ->Result<(),crate::document_import::structure::caption_text::CaptionTextOutputError> {
        use crate::document_import::structure::caption_text::CaptionTextOutputError as Error;
        if !std::ptr::eq(self.source,original){return Err(Error::Source);}
        if self.limits!=limits{return Err(Error::Limit);}Ok(())
    }
    #[must_use] pub const fn numbering(&self)->&ImportedCaptionNumbering<'a> {&self.numbering}
    #[must_use] pub const fn context(&self)->&ImportedNumberingContext<'a> {&self.context}
    #[must_use] pub const fn frames(&self)->&ImportedCaptionFrames<'a> {&self.frames}
    #[must_use] pub const fn object_states(&self)->&ImportedCaptionObjectStates<'a> {&self.object_states}
    #[must_use] pub fn owner_links(&self)->&[CaptionStateOwnerLink] {&self.owners}
    #[must_use] pub fn source_events(&self)->&[CaptionNumberingSourceEvent] {&self.events}
    #[must_use] pub const fn receipt(&self)->&CaptionSourceStateReceipt {&self.receipt}
    /// Whole original/graph reconstruction, not retained service authorization.
    /// # Errors
    /// Rejects source drift even inside a caption excluded from the body projection.
    pub fn verify_source(&self,fresh:&[u8])->Result<CaptionSourceStateReceipt,E> {
        if self.numbering.verify_source(fresh)?!=self.receipt.numbering{return Err(E::Binding);}Ok(self.receipt.clone())
    }
}
impl<'a> ImportedCaptionNumbering<'a> {
    /// Consumes this original model without rebuilding its retained caption import.
    /// # Errors
    /// Rejects constituent import failures, bounds and any incomplete exact join.
    pub fn assemble_source_state(self,limits:ReferenceAuxiliaryLimits)->Result<ImportedCaptionSourceState<'a>,E> {
        let source=self.original_structure();
        let context=self.import_context(limits)?;
        let object_states=context.project_object_states(limits)?;
        let frames=self.import_frames(limits)?;
        let envelopes=self.caption_import().envelopes();
        let envelope_ids:BTreeMap<_,_>=envelopes.iter().enumerate().map(|(i,c)|(c.logical_caption_id(),i)).collect();
        let frame_ids:BTreeMap<_,_>=frames.frames().iter().enumerate().map(|(i,c)|(&c.logical_caption_id,i)).collect();
        let object_ids:BTreeMap<_,_>=object_states.objects().iter().enumerate().map(|(i,c)|(&c.logical_object_id,i)).collect();
        let owner_ids:BTreeMap<_,_>=context.owners().iter().enumerate().map(|(i,c)|(&c.logical_object_id,i)).collect();
        if envelope_ids.len()!=envelopes.len()||frame_ids.len()!=frames.frames().len()
            ||object_ids.len()!=object_states.objects().len()||owner_ids.len()!=context.owners().len()
            ||object_ids.len()!=owner_ids.len()||envelope_ids.len()!=frame_ids.len(){return Err(E::Binding);}
        let event_count=context.owners().len().checked_add(context.ordered_controls().len()).ok_or(E::Limit)?;
        let maximum=limits.config().items_per_kind.checked_mul(2).and_then(|n|n.checked_add(limits.config().sections)).ok_or(E::Limit)?;
        if context.owners().len()>limits.config().items_per_kind||event_count>maximum{return Err(E::Limit);}
        let mut owners=Vec::new();owners.try_reserve_exact(context.owners().len()).map_err(|_|E::Limit)?;
        let mut events=Vec::new();events.try_reserve_exact(event_count).map_err(|_|E::Limit)?;
        let mut caption_owners=BTreeMap::new();
        for (i,owner) in context.owners().iter().enumerate() {
            let object_state_index=*object_ids.get(&owner.logical_object_id).ok_or(E::Binding)?;
            let body=&object_states.objects()[object_state_index];
            if body.section_id!=owner.section_id||body.object_kind!=owner.structural_kind||body.source_position!=owner.source_position
                ||body.source_fingerprint_sha256!=owner.source_fingerprint_sha256{return Err(E::Binding);}
            let caption=if let Some(id)=&owner.logical_caption_id {
                let envelope_index=*envelope_ids.get(id).ok_or(E::Binding)?;
                let frame_index=*frame_ids.get(id).ok_or(E::Binding)?;
                let envelope=&envelopes[envelope_index];let frame=&frames.frames()[frame_index];
                if envelope.logical_object_id()!=&owner.logical_object_id||frame.logical_object_id!=owner.logical_object_id
                    ||frame.source_position.spine_ordinal!=owner.source_position.spine_ordinal
                    ||frame.source_position.xml_element_ordinal<=owner.source_position.xml_element_ordinal
                    ||caption_owners.insert(id,i).is_some(){return Err(E::Binding);}
                Some(CaptionStateCaptionLink {envelope_index,frame_index})
            }else{None};
            owners.push(CaptionStateOwnerLink {owner_index:i,object_state_index,caption});
            events.push(CaptionNumberingSourceEvent {section_id:owner.section_id.clone(),source_position:owner.source_position,
                event:CaptionNumberingSourceEventKind::Owner {owner_index:i}});
        }
        if caption_owners.len()!=envelopes.len(){return Err(E::Coverage);}
        let controls:BTreeMap<_,_>=self.controls().iter().enumerate().map(|(i,c)|(&c.logical_control_id,(i,c))).collect();
        let starts:BTreeMap<_,_>=self.section_starts().iter().enumerate().map(|(i,c)|(&c.logical_control_id,(i,c))).collect();
        if controls.len()!=self.controls().len()||starts.len()!=self.section_starts().len()
            ||controls.len().checked_add(starts.len())!=Some(context.ordered_controls().len()){return Err(E::Binding);}
        let mut seen=BTreeSet::new();
        for ordered in context.ordered_controls() {
            if !seen.insert(&ordered.logical_control_id){return Err(E::Binding);}
            let event=match (controls.get(&ordered.logical_control_id),starts.get(&ordered.logical_control_id)) {
                (Some(&(control_index,control)),None)=>{
                    if control.section_id!=ordered.section_id{return Err(E::Binding);}
                    let owner_index=control.logical_caption_id.as_ref().map(|id|caption_owners.get(id).copied().ok_or(E::Binding)).transpose()?;
                    match control.kind {
                        NativeNumberControlKind::AutoNumber=>CaptionNumberingSourceEventKind::AutoNumber {control_index,owner_index},
                        NativeNumberControlKind::Restart=>CaptionNumberingSourceEventKind::Restart {control_index,owner_index},
                    }
                }
                (None,Some(&(section_start_index,start)))=>{
                    if start.section_id!=ordered.section_id{return Err(E::Binding);}
                    CaptionNumberingSourceEventKind::SectionStart {section_start_index}
                }
                _=>return Err(E::Binding),
            };
            events.push(CaptionNumberingSourceEvent {section_id:ordered.section_id.clone(),source_position:ordered.source_position,event});
        }
        if events.len()!=event_count{return Err(E::Coverage);}
        events.sort_by_key(|e|e.source_position);
        if events.windows(2).any(|pair|pair[0].source_position>=pair[1].source_position){return Err(E::Binding);}
        let joined_state_sha256=hash_json(&(&owners,&events,self.receipt(),context.receipt(),frames.receipt(),object_states.receipt()),
            limits.config().output_bytes).map_err(|_|E::Limit)?;
        let receipt=CaptionSourceStateReceipt {profile:"hwpx-agent.caption-source-state/exact-joined-input-v1",
            numbering:self.receipt().clone(),context:context.receipt().clone(),frames:frames.receipt().clone(),object_states:object_states.receipt().clone(),
            joined_state_sha256,owner_links:owners.len(),caption_links:caption_owners.len(),source_events:events.len(),
            sequence_interpretation_and_recalculation_qualified:false,complete_auxiliary_state_and_protection_qualified:false,
            execution_publication_authority:false};
        drop(caption_owners);drop(envelope_ids);drop(frame_ids);drop(object_ids);drop(owner_ids);drop(controls);drop(starts);drop(seen);
        Ok(ImportedCaptionSourceState {source,limits,numbering:self,context,frames,object_states,owners,events,receipt})
    }
}

