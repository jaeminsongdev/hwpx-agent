//! Selected original auto/restart control values, through the complete original stream compiler.
use super::*;
use crate::document_import::{search::{inspection::SourceControlKind,selector::SourceIndexScopeSelector,
    reviews::{SourceReviewTextPolicy,selector::{SourceReviewScopeIndex,controls::SourceReviewSelectorControlResult}}},
    structure::{review::ImportedDocumentReviewBodies,caption_numbering_sequence::*},
    reference_targets::{caption_source_state::{ImportedCaptionSourceState,output::sequence::{CaptionSourceStateSequenceOutputCandidate,CaptionSourceStateSequenceOutputReceipt}},
        numbering::NativeNumberControlKind as Kind}};
use domain_ir::{LogicalId,ReferenceAuxiliaryLimits};
pub const SOURCE_NUMBER_CONTROL_PROFILE:&str="hwpx-agent.source-selector-number-control-replacement/v1";
#[derive(Debug,Error)]
pub enum SourceNumberControlError {
    #[error("SOURCE_NUMBER_CONTROL_KIND_UNQUALIFIED")] UnsupportedKind,
    #[error("SOURCE_NUMBER_CONTROL_REJECTED:{0}")] Output(#[from] SourceLiteralReplacementError),
    #[error("SOURCE_NUMBER_CONTROL_STREAM_REJECTED:{0}")] Stream(#[from] crate::document_import::structure::caption_text::CaptionTextOutputError),
}
type C=SourceNumberControlError;
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceNumberControlChange {pub source_control_anchor:SourceAnchorHandle,pub source_control_id:LogicalId,pub changed_attributes:usize}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceNumberControlReceipt {
    pub profile:&'static str,pub source_package_sha256:[u8;32],pub request_sha256:[u8;32],
    pub search:SourceReviewSelectorControlResult,pub selected_controls:usize,pub changed_controls:usize,pub changes:Vec<SourceNumberControlChange>,
    pub stream:CaptionSourceStateSequenceOutputReceipt,pub source_review_import:crate::document_import::structure::review::ReviewBodyImportReceipt,
    pub output_review_import:crate::document_import::structure::review::ReviewBodyImportReceipt,
    pub observed_protection_parts:usize,pub observed_protection_element_visits:usize,
    pub whole_original_control_ranges_verified:bool,pub all_unselected_control_values_and_reference_bytes_preserved:bool,
    pub native_recalculation_full_search_service_or_execution_authority:bool,
}
pub struct SourceNumberControlCandidate {output:CaptionSourceStateSequenceOutputCandidate,receipt:SourceNumberControlReceipt}
impl fmt::Debug for SourceNumberControlCandidate {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{
    f.write_str("SourceNumberControlCandidate(<redacted>; stored_values_not_native_recalculation_or_service_authority)")}}
impl SourceNumberControlCandidate {
    #[must_use] pub const fn receipt(&self)->&SourceNumberControlReceipt{&self.receipt}
    /// # Errors
    /// Writer integrity only, not current service access or revision commit.
    pub fn with_verified_bytes<T>(&self,consume:impl FnOnce(&[u8])->T)->Result<T,WriterError>{self.output.with_verified_bytes(consume)}
}
fn qualified(kind:SourceControlKind)->Result<Kind,C>{match kind{SourceControlKind::AutoNumber=>Ok(Kind::AutoNumber),SourceControlKind::NewNumber=>Ok(Kind::Restart),_=>Err(C::UnsupportedKind)}}
fn format_digest(format:NativeNumberFormatReplacement<'_>,limits:ReferenceAuxiliaryLimits)->Result<[u8;32],E>{
    let mut digest=Sha256::new();digest.update(b"hwpx-agent.source-number-format/v1\0");
    match format {NativeNumberFormatReplacement::Preserve=>digest.update([0]),
        NativeNumberFormatReplacement::Replace{format,user_character,prefix,suffix,superscript}=>{
            digest.update([1]);digest.update(format.as_str().as_bytes());digest.update([u8::from(superscript)]);let mut total=0usize;
            for text in[user_character,prefix,suffix]{
                if text.len()>limits.config().text_bytes{return Err(E::Limit);}
                total=total.checked_add(text.len()).filter(|n|*n<=limits.config().output_bytes).ok_or(E::Limit)?;
                PatchText::new(text).map_err(|_|E::Value)?;digest.update((text.len()as u64).to_le_bytes());digest.update(text.as_bytes());
            }
        }}Ok(digest.finalize().into())
}
/// Immutable validated values and limits only; never source/access/execution authority.
pub struct ValidatedNumberControlValues<'a>{kind:SourceControlKind,expected:Kind,stored_number:i32,format:NativeNumberFormatReplacement<'a>,
    format_sha:[u8;32],search_limits:SourceSearchLimits,limits:ReferenceAuxiliaryLimits,values_sha:[u8;32]}
impl fmt::Debug for ValidatedNumberControlValues<'_>{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{
    f.write_str("ValidatedNumberControlValues(<redacted>; parameters_not_source_or_execution_authority)")}}
impl<'a> ValidatedNumberControlValues<'a>{
    /// # Errors
    /// Bind one borrowed immutable typed format and both limit sets before source access.
    pub fn new(kind:SourceControlKind,stored_number:i32,format:NativeNumberFormatReplacement<'a>,search_limits:SourceSearchLimits,limits:ReferenceAuxiliaryLimits)->Result<Self,C>{
        let expected=qualified(kind)?;let format_sha=format_digest(format,limits)?;let mut hash=Sha256::new();
        hash.update(b"hwpx-agent.number-control-values/v1\0");hash.update([if expected==Kind::AutoNumber{0}else{1}]);hash.update(stored_number.to_le_bytes());hash.update(format_sha);
        Ok(Self{kind,expected,stored_number,format,format_sha,search_limits,limits,values_sha:hash.finalize().into()})
    }
    #[must_use] pub const fn kind(&self)->SourceControlKind{self.kind}
    #[must_use] pub const fn values_sha256(&self)->[u8;32]{self.values_sha}
    /// # Errors
    /// Same bounded request binding as the original compiler, not source or request authority.
    pub fn request_sha256(&self,search:[u8;32])->Result<[u8;32],C>{
        let mut out=Output{bytes:Some(Vec::new()),length:0,maximum:self.search_limits.0.result_bytes};
        serde_json::to_writer(&mut out,&(SOURCE_NUMBER_CONTROL_PROFILE,search,self.stored_number,self.format_sha)).map_err(|_|E::Limit)?;
        Ok(Sha256::digest(out.bytes.ok_or(E::Limit)?).into())
    }
    /// # Errors
    /// The exact original model proof and all original guards/readback are still required.
    pub fn lower(&self,proof:&VerifiedFormReconstruction<'_>,original:&ImportedDocumentForms,selector:SourceIndexScopeSelector<'_>,body:SourceReviewTextPolicy,
        max_results:usize,writer:WriterLimits)->Result<SourceNumberControlCandidate,C>{
        proof.lower_number_control_validated(original,selector,body,self.kind,self.expected,max_results,self.stored_number,self.format,self.format_sha,self.search_limits,self.limits,writer)
    }
}
impl ImportedDocumentForms {
    /// # Errors
    /// Exact source selection and explicit stored number/format. Category and original IDs stay unchanged.
    pub fn lower_review_selector_number_control_candidate(&self,fresh:&[u8],selector:SourceIndexScopeSelector<'_>,body:SourceReviewTextPolicy,
        kind:SourceControlKind,max_results:usize,stored_number:i32,format:NativeNumberFormatReplacement<'_>,
        search_limits:SourceSearchLimits,limits:ReferenceAuxiliaryLimits,writer:WriterLimits)->Result<SourceNumberControlCandidate,C>{
        let expected=qualified(kind)?;let format_sha=format_digest(format,limits)?;
        self.reconstruct_source_for_verification(fresh).map_err(|_|E::Source)?.lower_number_control_validated(self,selector,body,kind,
            expected,max_results,stored_number,format,format_sha,search_limits,limits,writer)
    }
}
impl VerifiedFormReconstruction<'_> {
    /// # Errors
    /// This operation-local original proof is not retained service or Native authority.
    pub fn lower_review_selector_number_control_candidate(&self,original:&ImportedDocumentForms,selector:SourceIndexScopeSelector<'_>,body:SourceReviewTextPolicy,
        kind:SourceControlKind,max_results:usize,stored_number:i32,format:NativeNumberFormatReplacement<'_>,
        search_limits:SourceSearchLimits,limits:ReferenceAuxiliaryLimits,writer:WriterLimits)->Result<SourceNumberControlCandidate,C>{
        let expected=qualified(kind)?;let format_sha=format_digest(format,limits)?;
        self.lower_number_control_validated(original,selector,body,kind,expected,max_results,stored_number,format,format_sha,search_limits,limits,writer)
    }
    fn lower_number_control_validated(&self,original:&ImportedDocumentForms,selector:SourceIndexScopeSelector<'_>,body:SourceReviewTextPolicy,
        kind:SourceControlKind,expected:Kind,max_results:usize,stored_number:i32,format:NativeNumberFormatReplacement<'_>,format_sha:[u8;32],
        search_limits:SourceSearchLimits,limits:ReferenceAuxiliaryLimits,writer:WriterLimits)->Result<SourceNumberControlCandidate,C>{
        let rebuilt=self.for_original(original).map_err(|_|E::Source)?;let fresh=rebuilt.source().original.as_ref();
        let fields=ImportedDocumentFields::import(original).map_err(|_|E::Source)?;
        let review=ImportedDocumentReviewBodies::import_bound_fields(original,&fields).map_err(|_|E::Source)?;
        let index=SourceReviewScopeIndex::from_review(original,&review,search_limits).map_err(E::from)?;
        let(search,_windows,geometry)=index.find_control_with_geometry(selector,body,kind,max_results).map_err(E::from)?;
        if search.controls().is_empty(){return Err(E::NoMatches.into());}
        if search.controls().len()>limits.config().items_per_kind.min(PatchLimits::default().config().max_intents){return Err(E::Limit.into());}
        let text=index.source_index();let source=original.source();
        let context=review::ReviewWriteContext::new(source,&fields,&review,body)?;let intervals=context.field_intervals(source,&fields)?;
        // Guard every selected subtree BEFORE semantic no-op elimination. One inherited guard and
        // prefix count per part, not an ancestor/subtree walk per selected control.
        let mut guards:BTreeMap<&PackagePath,Vec<usize>>=BTreeMap::new();let mut visits=0usize;let mut selected=BTreeMap::new();
        for m in search.controls(){
            if !geometry.contains_whole(text,&m.control_anchor).map_err(E::from)?{return Err(E::Selection.into());}
            let resolved=source.resolve_anchor(&m.control_anchor).map_err(|_|E::Selection)?;let part=resolved.part();let path=part.path();let xml=part.xml().ok_or(E::Selection)?;
            let i=resolved.element_index().ok_or(E::Selection)?;let outer=xml.elements()[i].outer_span().ok_or(E::Selection)?;
            if !guards.contains_key(path){let guard=unicode::plan::guard(xml)?;let mut prefix=Vec::with_capacity(guard.len()+1);prefix.push(0usize);
                for value in guard{prefix.push(prefix.last().copied().ok_or(E::Source)?.checked_add(usize::from(value)).ok_or(E::Limit)?);}
                visits=visits.checked_add(xml.elements().len().checked_mul(4).ok_or(E::Limit)?).ok_or(E::Limit)?;guards.insert(path,prefix);}
            let end=xml.elements().partition_point(|n|n.start_tag_span().start()<outer.end());let prefix=guards.get(path).ok_or(E::Source)?;
            if prefix.get(end).ok_or(E::Selection)?!=prefix.get(i).ok_or(E::Selection)?{return Err(E::Protection.into());}
            if let Some(ranges)=intervals.get(path){let n=ranges.partition_point(|(a,_)|*a<outer.end());if n>0&&outer.start()<ranges[n-1].1{return Err(E::FieldContent.into());}}
            let id=LogicalId::parse(format!("native-number-{}",m.control_anchor.opaque_handle.as_str())).map_err(|_|E::Selection)?;
            if selected.insert(id,m.control_anchor.clone()).is_some(){return Err(E::Selection.into());}
        }
        let state=ImportedCaptionSourceState::import_review_bound(original,&review,limits).map_err(|_|E::Source)?;
        // Index once; do not search all source events for each selected control.
        let controls:BTreeMap<_,_>=state.numbering().controls().iter().map(|c|(&c.logical_control_id,c)).collect();
        let starts:BTreeMap<_,_>=state.numbering().section_starts().iter().map(|c|(&c.logical_control_id,c)).collect();
        for(id,anchor)in &selected{let c=*controls.get(id).ok_or(E::Selection)?;if c.kind!=expected||c.source_fingerprint_sha256!=anchor.fingerprint_sha256{return Err(E::Selection.into());}}
        let mut events=Vec::new();events.try_reserve_exact(state.context().ordered_controls().len()).map_err(|_|E::Limit)?;
        for ordered in state.context().ordered_controls(){
            let(id,fingerprint,values)=if let Some(c)=controls.get(&ordered.logical_control_id){
                let is_selected=selected.contains_key(&c.logical_control_id);let number=if is_selected{stored_number}else{c.stored_number};
                let format=if is_selected{format}else{NativeNumberFormatReplacement::Preserve};
                let values=match c.kind{Kind::AutoNumber=>NativeNumberEventValues::AutoNumber{category:c.category,stored_number:number,format},
                    Kind::Restart=>NativeNumberEventValues::Restart{category:c.category,stored_number:number,format}};
                (&c.logical_control_id,c.source_fingerprint_sha256,values)
            }else{let c=*starts.get(&ordered.logical_control_id).ok_or(E::Source)?;
                let page_starts_on=match c.page_starts_on{"BOTH"=>NativePageStartsOn::Both,"EVEN"=>NativePageStartsOn::Even,"ODD"=>NativePageStartsOn::Odd,_=>return Err(E::Source.into())};
                (&c.logical_control_id,c.source_fingerprint_sha256,NativeNumberEventValues::SectionStart{page_starts_on,page:c.page,picture:c.picture,table:c.table,equation:c.equation})};
            events.push(NativeNumberEventReplacement{source_control_id:id,source_fingerprint_sha256:fingerprint,values});
        }
        let document_start=state.context().document_start().map(|c|NativeDocumentStartReplacement{source_control_id:&c.logical_control_id,source_fingerprint_sha256:c.source_fingerprint_sha256,
            values:NativeDocumentStartValues{page:c.page,footnote:c.footnote,endnote:c.endnote,picture:c.picture,table:c.table,equation:c.equation}});
        let request=NativeNumberSequenceReplacement{expected_joined_state_sha256:state.receipt().joined_state_sha256,document_start,events:&events};
        let output=self.lower_caption_state_sequence_batch_candidate(original,&state,fresh,&[],&[],&[],&request,limits,writer)?;
        let stream=output.receipt();let mut counts:BTreeMap<&LogicalId,usize>=BTreeMap::new();
        for node in &stream.number_sequence.nodes{if node.changed_attributes>0{
            if !selected.contains_key(&node.source_control_id){return Err(E::Readback.into());}
            let count=counts.entry(&node.source_control_id).or_default();*count=count.checked_add(node.changed_attributes).ok_or(E::Limit)?;}}
        let mut changes=Vec::new();
        for m in search.controls(){let id=LogicalId::parse(format!("native-number-{}",m.control_anchor.opaque_handle.as_str())).map_err(|_|E::Readback)?;
            if let Some(n)=counts.remove(&id){changes.push(SourceNumberControlChange{source_control_anchor:m.control_anchor.clone(),source_control_id:id,changed_attributes:n});}}
        if !counts.is_empty()||changes.is_empty(){return Err(E::Readback.into());}
        let output_review=context.readback_receipt(stream.content.output.output_review_import.as_ref().ok_or(E::Readback)?)?;
        let mut binding=Output{bytes:Some(Vec::new()),length:0,maximum:search_limits.0.result_bytes};
        serde_json::to_writer(&mut binding,&(SOURCE_NUMBER_CONTROL_PROFILE,search.request_sha256(),stored_number,format_sha)).map_err(|_|E::Limit)?;
        let receipt=SourceNumberControlReceipt{profile:SOURCE_NUMBER_CONTROL_PROFILE,source_package_sha256:source.receipt().source_package_sha256,
            request_sha256:Sha256::digest(binding.bytes.ok_or(E::Limit)?).into(),selected_controls:search.controls().len(),changed_controls:changes.len(),search,changes,stream:stream.clone(),
            source_review_import:review.receipt().clone(),output_review_import:output_review,observed_protection_parts:guards.len(),observed_protection_element_visits:visits,
            whole_original_control_ranges_verified:true,all_unselected_control_values_and_reference_bytes_preserved:true,native_recalculation_full_search_service_or_execution_authority:false};
        let mut bound=Output{bytes:None,length:0,maximum:search_limits.0.result_bytes};serde_json::to_writer(&mut bound,&receipt).map_err(|_|E::Limit)?;
        Ok(SourceNumberControlCandidate{output,receipt})
    }
}
