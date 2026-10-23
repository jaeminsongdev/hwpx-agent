//! Full source-caption membership -> explicit typed sequence -> actual candidate.
//! Caller document_order is not native/render order; no inferred text split.
use super::{ImportedCaptionSourceState,E,sequence::CaptionSourceStateSequenceOutputCandidate};
use crate::{NumberFormat,PatchLimits,WriterError,WriterLimits,HANCOM_2020_PARAGRAPH_NAMESPACE as HP};
use crate::document_import::{forms::{ImportedDocumentForms,VerifiedFormReconstruction},reference_targets::{
    caption_frames::{CaptionFrameSegmentKind,CaptionStyleFamily,CaptionStyleReferenceStatus},
    numbering::{NativeNumberCategory as Category,NativeNumberControlKind as Kind}},structure::{
    caption_text_batch::CaptionTextReplacement as Text,caption_edit_batch::CaptionLayoutReplacement as Layout,
    caption_style_batch::CaptionStyleReplacement as Style,caption_numbering_sequence::*}};
use domain_ir::{CaptionSequenceDefinition,CaptionNumberFormat,CaptionObjectKind,LogicalId,ReferenceAuxiliaryLimits,
    caption_sequence_program::{CaptionSequenceMember,resolve_caption_sequence_numbers}};
use serde::Serialize;
use sha2::{Digest as _,Sha256};
use std::{collections::{BTreeMap,BTreeSet},fmt};
pub struct SourceCaptionSequenceAssignment<'a> {
    pub caption_id:&'a LogicalId,pub object_id:&'a LogicalId,pub sequence_id:&'a LogicalId,
    /// Exact whole plain hp:t leaf replaced with label + separator. No slicing.
    pub label_text_id:&'a LogicalId,pub number_control_id:&'a LogicalId,
    /// Explicit caller order; never asserted to be the native counter order.
    pub document_order:u64,
}
pub struct SourceCaptionSequenceRequest<'a> {
    pub expected_joined_state_sha256:[u8;32],pub sequences:&'a[CaptionSequenceDefinition],
    /// Exactly one assignment for every original caption; no implicit omission.
    pub assignments:&'a[SourceCaptionSequenceAssignment<'a>],
}
impl fmt::Debug for SourceCaptionSequenceAssignment<'_>{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("SourceCaptionSequenceAssignment(<redacted>; caller_order)")}}
impl fmt::Debug for SourceCaptionSequenceRequest<'_>{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("SourceCaptionSequenceRequest(<redacted>; not_native_or_service_authority)")}}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceCaptionSequenceBinding {
    pub source_caption_id:LogicalId,pub source_object_id:LogicalId,pub source_caption_sha256:[u8;32],pub source_object_state_sha256:[u8;32],
    pub source_label_text_id:LogicalId,pub source_number_control_id:LogicalId,pub sequence_id_sha256:[u8;32],
    pub caller_document_order:u64,pub resolved_number:u32,pub requested_label_sha256:[u8;32],pub declared_number_style_sha256:[u8;32],
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceCaptionSequenceOutputReceipt {
    pub profile:&'static str,pub caller_request_sha256:[u8;32],pub lowered_number_request_sha256:[u8;32],
    pub output:super::sequence::CaptionSourceStateSequenceOutputReceipt,pub sequences:usize,pub bindings:Vec<SourceCaptionSequenceBinding>,
    pub complete_original_caption_membership_checked:bool,pub labels_stored_numbers_and_declared_styles_read_back:bool,
    pub caller_order_not_native_counter_order:bool,pub native_counter_recalculation_qualified:bool,pub execution_publication_authority:bool,
}
pub struct SourceCaptionSequenceOutputCandidate {output:CaptionSourceStateSequenceOutputCandidate,receipt:SourceCaptionSequenceOutputReceipt}
impl fmt::Debug for SourceCaptionSequenceOutputCandidate {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("SourceCaptionSequenceOutputCandidate(<redacted>; not_native_counter_or_service_authority)")}}
impl SourceCaptionSequenceOutputCandidate {
    #[must_use] pub const fn receipt(&self)->&SourceCaptionSequenceOutputReceipt{&self.receipt}
    /// Writer integrity only, never current service access or publication.
    /// # Errors
    /// Rejects artifact integrity failures before exposing candidate bytes.
    pub fn with_verified_bytes<T>(&self,consume:impl FnOnce(&[u8])->T)->Result<T,WriterError>{self.output.with_verified_bytes(consume)}
}
fn hash(value:&impl Serialize,limits:ReferenceAuxiliaryLimits)->Result<[u8;32],E>{
    let bytes=serde_json::to_vec(value).map_err(|_|E::Limit)?;if bytes.len()>limits.config().output_bytes{return Err(E::Limit);}Ok(Sha256::digest(bytes).into())
}
fn format(kind:CaptionNumberFormat)->NumberFormat{match kind {
    CaptionNumberFormat::Decimal=>NumberFormat::Digit,CaptionNumberFormat::CircledDecimal=>NumberFormat::CircledDigit,
    CaptionNumberFormat::RomanUpper=>NumberFormat::RomanCapital,CaptionNumberFormat::RomanLower=>NumberFormat::RomanSmall,
    CaptionNumberFormat::LatinUpper=>NumberFormat::LatinCapital,CaptionNumberFormat::LatinLower=>NumberFormat::LatinSmall,CaptionNumberFormat::HangulSyllable=>NumberFormat::HangulSyllable,
}}
fn category(kind:CaptionObjectKind)->Category{match kind{CaptionObjectKind::Picture=>Category::Picture,CaptionObjectKind::Table=>Category::Table,CaptionObjectKind::Equation=>Category::Equation}}
impl SourceCaptionSequenceRequest<'_> {
    /// Binds every definition/member including no-ops; no plaintext label output.
    /// # Errors
    /// Rejects finite counts/text/output limits. Not source or access validation.
    pub fn canonical_sha256(&self,limits:ReferenceAuxiliaryLimits)->Result<[u8;32],E> {
        let maximum=limits.config().items_per_kind.min(PatchLimits::default().config().max_intents);
        if self.sequences.len().checked_add(self.assignments.len()).filter(|n|*n<=maximum).is_none(){return Err(E::Limit);}
        let mut bytes=0usize;
        for sequence in self.sequences {for text in [&sequence.label,&sequence.separator] {
            if text.len()>limits.config().text_bytes{return Err(E::Limit);}bytes=bytes.checked_add(text.len()).filter(|n|*n<=limits.config().output_bytes).ok_or(E::Limit)?;
        }}
        let sequences=self.sequences.iter().map(|s|(&s.logical_sequence_id,s.object_kind,Sha256::digest(s.label.as_bytes()).to_vec(),Sha256::digest(s.separator.as_bytes()).to_vec(),s.number_format,s.restart_policy,s.start_at,&s.number_style_sha256,&s.opaque_properties,s.locked)).collect::<Vec<_>>();
        let members=self.assignments.iter().map(|m|(m.caption_id,m.object_id,m.sequence_id,m.label_text_id,m.number_control_id,m.document_order)).collect::<Vec<_>>();
        hash(&(self.expected_joined_state_sha256,sequences,members),limits)
    }
}
struct Program<'a>{labels:Vec<String>,text_ids:Vec<(&'a LogicalId,&'a LogicalId)>,events:Vec<NativeNumberEventReplacement<'a>>,begin:Option<NativeDocumentStartReplacement<'a>>,
    caller_sha:[u8;32],bindings:Vec<SourceCaptionSequenceBinding>,sequences:usize}
fn plan<'a>(state:&'a ImportedCaptionSourceState<'_>,request:&SourceCaptionSequenceRequest<'_>,styles:&[Style<'_>],limits:ReferenceAuxiliaryLimits)->Result<Program<'a>,E> {
    state.validate_compiler_input(state.source,limits)?;
    if request.expected_joined_state_sha256!=state.receipt().joined_state_sha256{return Err(E::Source);}
    let caller_sha=request.canonical_sha256(limits)?;
    if request.assignments.len()!=state.frames().frames().len()||request.assignments.is_empty(){return Err(E::Selection);}
    // This lowering profile applies known declared style references, not opaque
    // properties or sequence-lock semantics that have no native mapping yet.
    if request.sequences.iter().any(|s|s.locked||!s.opaque_properties.is_empty()){return Err(E::Value);}
    let definitions:BTreeMap<_,_>=request.sequences.iter().map(|s|(&s.logical_sequence_id,s)).collect();
    if definitions.len()!=request.sequences.len(){return Err(E::Selection);}
    let frames=state.frames().frames();let mut frame_index=BTreeMap::new();
    for link in state.owner_links(){if let Some(caption)=link.caption {
        let frame=&frames[caption.frame_index];let owner=&state.context().owners()[link.owner_index];let object=&state.object_states().objects()[link.object_state_index];
        if frame_index.insert(&frame.logical_caption_id,(frame,owner,object)).is_some(){return Err(E::Selection);}
    }}
    let controls:BTreeMap<_,_>=state.numbering().controls().iter().map(|c|(&c.logical_control_id,c)).collect();
    let starts:BTreeMap<_,_>=state.numbering().section_starts().iter().map(|c|(&c.logical_control_id,c)).collect();
    let mut style_index=BTreeMap::new();for style in styles{if style_index.insert((style.source_node_id,style.family),style).is_some(){return Err(E::Selection);}}
    let mut seen=BTreeSet::new();let mut members=Vec::new();let mut selected=Vec::new();
    for assignment in request.assignments {
        if !seen.insert(assignment.caption_id){return Err(E::Selection);}
        let &(frame,owner,object)=frame_index.get(assignment.caption_id).ok_or(E::Selection)?;
        if assignment.object_id!=&owner.logical_object_id{return Err(E::Selection);}
        let sequence=*definitions.get(assignment.sequence_id).ok_or(E::Selection)?;
        let label=frame.segments.iter().find(|s|&s.logical_source_id==assignment.label_text_id).ok_or(E::Selection)?;
        if label.kind!=CaptionFrameSegmentKind::PlainText||state.frames().plain_text(&label.logical_source_id).is_none(){return Err(E::Selection);}
        let selected_number=frame.segments.iter().find(|s|s.number_control_id.as_ref()==Some(assignment.number_control_id)).ok_or(E::Selection)?;
        let number=*controls.get(assignment.number_control_id).ok_or(E::Selection)?;
        if selected_number.kind!=CaptionFrameSegmentKind::AutoNumber||number.kind!=Kind::AutoNumber||number.category!=category(owner.structural_kind)
            ||selected_number.logical_run_id!=label.logical_run_id{return Err(E::Selection);}
        let run=frame.runs.iter().find(|r|Some(&r.logical_run_id)==selected_number.logical_run_id.as_ref()).ok_or(E::Selection)?;
        let declared=if let Some(style)=style_index.get(&(&run.logical_run_id,CaptionStyleFamily::Character)) {
            if style.caption_id!=&frame.logical_caption_id{return Err(E::Selection);}state.frames().style_declaration(CaptionStyleFamily::Character,style.declaration_id)
        }else{run.character_style.clone()};
        let style_sha=declared.declaration_sha256.ok_or(E::Selection)?;
        if declared.status!=CaptionStyleReferenceStatus::UniqueSourceDeclaration||sequence.number_style_sha256!=crate::document_import::hex_digest(style_sha){return Err(E::Selection);}
        members.push(CaptionSequenceMember {logical_caption_id:&frame.logical_caption_id,logical_object_id:&frame.logical_object_id,logical_sequence_id:assignment.sequence_id,
            section_id:&owner.section_id,object_kind:owner.structural_kind,document_order:assignment.document_order});
        selected.push((assignment,frame,object,label,number,sequence,style_sha));
    }
    let resolved=resolve_caption_sequence_numbers(request.sequences,&members,limits).map_err(|_|E::Value)?;
    let resolved:BTreeMap<_,_>=resolved.iter().map(|r|(&r.logical_caption_id,r.resolved_number)).collect();
    let mut changed=BTreeMap::new();let mut labels=Vec::new();let mut text_ids=Vec::new();let mut bindings=Vec::new();let mut bytes=0usize;
    for (assignment,frame,object,label,number,sequence,style_sha) in selected {
        let value=*resolved.get(&frame.logical_caption_id).ok_or(E::Selection)?;let signed=i32::try_from(value).map_err(|_|E::Value)?;
        let text=format!("{}{}",sequence.label,sequence.separator);if text.len()>limits.config().text_bytes{return Err(E::Limit);}
        bytes=bytes.checked_add(text.len()).filter(|n|*n<=limits.config().output_bytes).ok_or(E::Limit)?;
        let observed=number.format.as_ref().ok_or(E::Selection)?;
        let opaque=number.logical_control_id.as_str().strip_prefix("native-number-").ok_or(E::Selection)?;
        let anchor=domain_ir::SourceAnchorHandle {opaque_handle:LogicalId::parse(opaque).map_err(|_|E::Selection)?,fingerprint_sha256:number.source_fingerprint_sha256};
        let source=state.source.source().resolve_anchor(&anchor).map_err(|_|E::Selection)?;let xml=source.part().xml().ok_or(E::Selection)?;let index=source.element_index().ok_or(E::Selection)?;
        let mut child=xml.elements()[index].first_child();let mut node=None;
        while let Some(i)=child{let n=&xml.elements()[i];child=n.next_sibling();if n.name().namespace()==Some(HP)&&n.name().local_name()=="autoNumFormat"{if node.replace(i).is_some(){return Err(E::Selection);}}}
        let node=node.ok_or(E::Selection)?;
        if source.part().element_anchor(node).ok_or(E::Selection)?.fingerprint_sha256!=observed.source_fingerprint_sha256{return Err(E::Selection);}
        let attribute=|name:&str|xml.elements()[node].attributes().iter().find(|a|!a.is_namespace_declaration()&&a.name().namespace().is_none()&&a.name().local_name()==name).map(|a|a.semantic_value()).ok_or(E::Selection);
        let replacement=NativeNumberFormatReplacement::Replace {format:format(sequence.number_format),user_character:attribute("userChar")?,prefix:attribute("prefixChar")?,suffix:attribute("suffixChar")?,superscript:observed.superscript};
        if changed.insert(&number.logical_control_id,NativeNumberEventValues::AutoNumber {category:number.category,stored_number:signed,format:replacement}).is_some(){return Err(E::Selection);}
        bindings.push(SourceCaptionSequenceBinding {source_caption_id:frame.logical_caption_id.clone(),source_object_id:frame.logical_object_id.clone(),source_caption_sha256:frame.source_fingerprint_sha256,
            source_object_state_sha256:object.object_state_sha256,source_label_text_id:label.logical_source_id.clone(),source_number_control_id:number.logical_control_id.clone(),
            sequence_id_sha256:Sha256::digest(sequence.logical_sequence_id.as_str().as_bytes()).into(),caller_document_order:assignment.document_order,resolved_number:value,
            requested_label_sha256:Sha256::digest(text.as_bytes()).into(),declared_number_style_sha256:style_sha});
        labels.push(text);text_ids.push((&frame.logical_caption_id,&label.logical_source_id));
    }
    let mut events=Vec::new();
    for ordered in state.context().ordered_controls(){
        let (fingerprint,values)=if let Some(&c)=controls.get(&ordered.logical_control_id){
            let values=changed.remove(&c.logical_control_id).unwrap_or(match c.kind {
                Kind::AutoNumber=>NativeNumberEventValues::AutoNumber {category:c.category,stored_number:c.stored_number,format:NativeNumberFormatReplacement::Preserve},
                Kind::Restart=>NativeNumberEventValues::Restart {category:c.category,stored_number:c.stored_number,format:NativeNumberFormatReplacement::Preserve}});
            (c.source_fingerprint_sha256,values)
        }else {let c=*starts.get(&ordered.logical_control_id).ok_or(E::Selection)?;let page_starts_on=match c.page_starts_on {"BOTH"=>NativePageStartsOn::Both,"EVEN"=>NativePageStartsOn::Even,"ODD"=>NativePageStartsOn::Odd,_=>return Err(E::Selection)};
            (c.source_fingerprint_sha256,NativeNumberEventValues::SectionStart {page_starts_on,page:c.page,picture:c.picture,table:c.table,equation:c.equation})};
        events.push(NativeNumberEventReplacement {source_control_id:&ordered.logical_control_id,source_fingerprint_sha256:fingerprint,values});
    }
    if !changed.is_empty(){return Err(E::Selection);}
    let begin=state.context().document_start().map(|c|NativeDocumentStartReplacement {source_control_id:&c.logical_control_id,source_fingerprint_sha256:c.source_fingerprint_sha256,
        values:NativeDocumentStartValues {page:c.page,footnote:c.footnote,endnote:c.endnote,picture:c.picture,table:c.table,equation:c.equation}});
    Ok(Program {labels,text_ids,events,begin,caller_sha,bindings,sequences:request.sequences.len()})
}
fn lower(state:&ImportedCaptionSourceState<'_>,request:&SourceCaptionSequenceRequest<'_>,texts:&[Text<'_>],styles:&[Style<'_>],limits:ReferenceAuxiliaryLimits,
    consume:impl FnOnce(&[Text<'_>],&NativeNumberSequenceReplacement<'_>)->Result<CaptionSourceStateSequenceOutputCandidate,E>)->Result<SourceCaptionSequenceOutputCandidate,E> {
    let maximum=limits.config().items_per_kind.min(PatchLimits::default().config().max_intents);
    if request.assignments.len().checked_add(texts.len()).and_then(|n|n.checked_add(styles.len())).filter(|n|*n<=maximum).is_none(){return Err(E::Limit);}
    let planned=plan(state,request,styles,limits)?;
    let mut combined=planned.text_ids.iter().zip(&planned.labels).map(|(&(caption_id,text_id),replacement)|Text {caption_id,text_id,replacement}).collect::<Vec<_>>();
    combined.extend(texts.iter().map(|r|Text {caption_id:r.caption_id,text_id:r.text_id,replacement:r.replacement}));
    let numbers=NativeNumberSequenceReplacement {expected_joined_state_sha256:request.expected_joined_state_sha256,document_start:planned.begin,events:&planned.events};
    let number_sha=numbers.canonical_sha256(limits)?;let output=consume(&combined,&numbers)?;
    if output.receipt().number_sequence.caller_request_sha256!=number_sha||output.receipt().content.source_state.joined_state_sha256!=request.expected_joined_state_sha256{return Err(E::Readback);}
    let receipt=SourceCaptionSequenceOutputReceipt {profile:"hwpx-agent.source-caption-sequence/explicit-caller-program-output-v1",caller_request_sha256:planned.caller_sha,
        lowered_number_request_sha256:number_sha,output:output.receipt().clone(),sequences:planned.sequences,bindings:planned.bindings,
        complete_original_caption_membership_checked:true,labels_stored_numbers_and_declared_styles_read_back:true,caller_order_not_native_counter_order:true,
        native_counter_recalculation_qualified:false,execution_publication_authority:false};
    Ok(SourceCaptionSequenceOutputCandidate {output,receipt})
}
impl ImportedCaptionSourceState<'_> {
    /// Complete membership and caller order; the number-style SHA denotes the
    /// selected run's unique declared character style, never inherited formatting.
    /// Selected whole label leaves are overwritten, all other content preserved.
    /// # Errors
    /// Rejects incomplete/foreign/ambiguous selections, unsupported metadata,
    /// invalid values/overflow, protection, limits, drift and any readback failure.
    pub fn lower_caption_program_candidate(&self,fresh:&[u8],request:&SourceCaptionSequenceRequest<'_>,texts:&[Text<'_>],layouts:&[Layout<'_>],styles:&[Style<'_>],
        limits:ReferenceAuxiliaryLimits,writer:WriterLimits)->Result<SourceCaptionSequenceOutputCandidate,E> {
        lower(self,request,texts,styles,limits,|combined,numbers|self.lower_sequence_batch_candidate(fresh,combined,layouts,styles,numbers,limits,writer))
    }
}
impl VerifiedFormReconstruction<'_> {
    /// Exact original/state/whole proof/fresh bytes remain operation-local.
    /// # Errors
    /// Rejects foreign original/state/proof/bytes and every program/compiler error.
    pub fn lower_caption_state_program_candidate(&self,original:&ImportedDocumentForms,state:&ImportedCaptionSourceState<'_>,fresh:&[u8],request:&SourceCaptionSequenceRequest<'_>,
        texts:&[Text<'_>],layouts:&[Layout<'_>],styles:&[Style<'_>],limits:ReferenceAuxiliaryLimits,writer:WriterLimits)->Result<SourceCaptionSequenceOutputCandidate,E> {
        state.validate_compiler_input(original.body_structure(),limits)?;
        lower(state,request,texts,styles,limits,|combined,numbers|self.lower_caption_state_sequence_batch_candidate(original,state,fresh,combined,layouts,styles,numbers,limits,writer))
    }
}
