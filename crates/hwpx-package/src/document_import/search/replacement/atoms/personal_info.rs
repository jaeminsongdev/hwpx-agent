//! Explicit original text masking. Not generic find/replace, package sanitization or Native equivalence.
pub mod catalog;
use super::*;
use crate::document_import::{search::{selector::{SourceIndexScopeSelector,SourceIndexScopeReceipt},reviews::{SourceReviewTextPolicy,selector::SourceReviewScopeIndex}},
    structure::review::{ImportedDocumentReviewBodies,ReviewBodyImportReceipt}};
use serde::Deserialize;
pub const SOURCE_PERSONAL_INFO_MASK_PROFILE:&str="hwpx-agent.source-personal-info-selection-mask/v1";
#[derive(Clone,Copy,Debug,Eq,PartialEq,Deserialize,Serialize)]
#[serde(rename_all="snake_case")]
pub enum SourcePersonalInfoMaskPolicy{
    /// One star per original Unicode scalar in its original text/run slot, not a grapheme/UTF16 count.
    PerOriginalScalarPreserveSlots,
    /// Three literal stars per contiguous selected text group; controls/blocks split groups.
    ThreeAsterisksPerTextGroup,
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourcePersonalInfoMaskReceipt{
    pub profile:&'static str,pub source_package_sha256:[u8;32],pub source_index_sha256:[u8;32],pub selector:SourceIndexScopeReceipt,
    pub body_policy:SourceReviewTextPolicy,pub mask_policy:SourcePersonalInfoMaskPolicy,pub request_sha256:[u8;32],
    pub selected_original_scalars:usize,pub selected_text_groups:usize,pub changed_components:usize,pub changed_scalar_ranges:usize,pub changed_parts:usize,
    pub excluded_hidden_paragraphs:usize,pub excluded_memo_paragraphs:usize,pub observed_protection_parts:usize,pub observed_protection_element_visits:usize,
    pub source_review_import:ReviewBodyImportReceipt,pub output_review_import:ReviewBodyImportReceipt,pub output_package_sha256:[u8;32],pub output_bytes:usize,
    pub exact_original_selection_verified:bool,pub original_run_shells_styles_controls_and_references_preserved:bool,pub output_spans_and_outside_slots_verified:bool,
    pub whole_package_personal_data_removed:bool,pub native_mask_semantics_or_service_execution_qualified:bool,
}
/// Immutable source/output/receipt-bound edit anchors. No text or per-value hashes are exposed.
pub struct SourcePersonalInfoMaskEditInventory{source:[u8;32],output:[u8;32],receipt_sha:[u8;32],anchors:Vec<SourceAnchorHandle>,sha:[u8;32]}
impl SourcePersonalInfoMaskEditInventory{
    #[must_use]pub const fn source_package_sha256(&self)->[u8;32]{self.source}
    #[must_use]pub const fn output_package_sha256(&self)->[u8;32]{self.output}
    #[must_use]pub const fn receipt_sha256(&self)->[u8;32]{self.receipt_sha}
    #[must_use]pub fn anchors(&self)->&[SourceAnchorHandle]{&self.anchors}
    #[must_use]pub const fn canonical_sha256(&self)->[u8;32]{self.sha}
}
impl fmt::Debug for SourcePersonalInfoMaskEditInventory{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("SourcePersonalInfoMaskEditInventory(<redacted>; metadata_only)")}}
pub struct SourcePersonalInfoMaskCandidate{artifact:PackageArtifact,receipt:SourcePersonalInfoMaskReceipt,maximum_bytes:usize,inventory:SourcePersonalInfoMaskEditInventory}
impl fmt::Debug for SourcePersonalInfoMaskCandidate{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("SourcePersonalInfoMaskCandidate(<redacted>; selected_text_only_not_package_sanitization)")}}
impl SourcePersonalInfoMaskCandidate{
    #[must_use]pub const fn receipt(&self)->&SourcePersonalInfoMaskReceipt{&self.receipt}
    #[must_use]pub const fn edit_inventory(&self)->&SourcePersonalInfoMaskEditInventory{&self.inventory}
    /// # Errors
    /// Writer integrity only, not current service authorization, publication or a sanitized document.
    pub fn with_verified_bytes<T>(&self,consume:impl FnOnce(&[u8])->T)->Result<T,WriterError>{self.artifact.with_verified_bytes(consume)}
    /// # Errors
    /// Bounded metadata only: no text, query, original pieces, per-value hashes, key or private replacement.
    pub fn canonical_json(&self)->Result<Vec<u8>,E>{let mut out=Output{bytes:Some(Vec::new()),length:0,maximum:self.maximum_bytes};
        serde_json::to_writer(&mut out,&self.receipt).map_err(|_|E::Limit)?;out.bytes.ok_or(E::Limit)}
}
impl ImportedDocumentForms{
    /// # Errors
    /// Exact original scope and explicit body/masking policy. Source artifact is never changed in place.
    pub fn lower_personal_info_mask_candidate(&self,fresh:&[u8],selector:SourceIndexScopeSelector<'_>,body_policy:SourceReviewTextPolicy,
        mask_policy:SourcePersonalInfoMaskPolicy,limits:SourceSearchLimits,writer:WriterLimits)->Result<SourcePersonalInfoMaskCandidate,E>{
        self.reconstruct_source_for_verification(fresh).map_err(|_|E::Source)?
            .lower_personal_info_mask_candidate(self,selector,body_policy,mask_policy,limits,writer)
    }
}
impl VerifiedFormReconstruction<'_>{
    /// # Errors
    /// One original proof, protection observation, field/review/index, preserving writer and readback.
    pub fn lower_personal_info_mask_candidate(&self,original:&ImportedDocumentForms,selector:SourceIndexScopeSelector<'_>,body_policy:SourceReviewTextPolicy,
        mask_policy:SourcePersonalInfoMaskPolicy,limits:SourceSearchLimits,writer:WriterLimits)->Result<SourcePersonalInfoMaskCandidate,E>{
        let rebuilt=self.for_original(original).map_err(|_|E::Source)?;
        let protection=original.source().observe_protection_signals().map_err(|_|E::Protection)?;
        protection.require_no_observed_document_signals().map_err(|_|E::Protection)?;
        let fields=ImportedDocumentFields::import(original).map_err(|_|E::Source)?;
        let review=ImportedDocumentReviewBodies::import_bound_fields(original,&fields).map_err(|_|E::Source)?;
        let index=SourceReviewScopeIndex::from_review(original,&review,limits)?;
        let(selector,windows,hidden,memo)=index.transformation_windows(selector,body_policy)?;let text=index.source_index();
        let mut selected=BTreeSet::new();let mut groups=Vec::new();
        for(&block,&(start,end))in &windows{
            let units=&text.blocks.get(block).ok_or(E::Selection)?.units;let mut origins=BTreeSet::new();
            for unit in units.get(start..end).ok_or(E::Selection)?{origins.extend(unit.origins.iter().copied());}
            let origins:Vec<_>=origins.into_iter().collect();if origins.windows(2).any(|w|w[0]+1!=w[1]){return Err(E::Selection);}
            for &origin in &origins{let &(a,b)=text.usage.get(origin).ok_or(E::Selection)?;
                if a<start||b>=end||!selected.insert(origin){return Err(E::Selection);}}
            groups.push(origins);
        }
        let context=review::ReviewWriteContext::new(text.original.source(),&fields,&review,body_policy)?;
        let plan=unicode::plan::compile_mapped(text,&fields,&context,groups,selected,|chars,ids,remaining,bytes|mask(text,chars,ids,mask_policy,remaining,bytes))?;
        let artifact=styles::text::output::build(text.original.source(),rebuilt.source().original.as_ref(),&plan.intents,&plan.spans,writer)?;
        let output_review=readback::verify_artifact(text.original.source(),&artifact,&plan.spans,Some(&context))?.ok_or(E::Readback)?;
        let request_sha256=bound_hash(&(SOURCE_PERSONAL_INFO_MASK_PROFILE,text.receipt.index_sha256,&selector,body_policy,mask_policy))?;
        let receipt=SourcePersonalInfoMaskReceipt{profile:SOURCE_PERSONAL_INFO_MASK_PROFILE,source_package_sha256:original.source().receipt().source_package_sha256,
            source_index_sha256:text.receipt.index_sha256,selector,body_policy,mask_policy,request_sha256,selected_original_scalars:plan.selected,selected_text_groups:plan.groups,
            changed_components:plan.components,changed_scalar_ranges:plan.ranges,changed_parts:plan.spans.len(),excluded_hidden_paragraphs:hidden,excluded_memo_paragraphs:memo,
            observed_protection_parts:protection.counts().parts,observed_protection_element_visits:protection.counts().protection_element_visits.checked_add(plan.visits).ok_or(E::Limit)?,
            source_review_import:review.receipt().clone(),output_review_import:output_review,output_package_sha256:artifact.sha256(),output_bytes:artifact.size_bytes(),
            exact_original_selection_verified:true,original_run_shells_styles_controls_and_references_preserved:true,output_spans_and_outside_slots_verified:true,
            whole_package_personal_data_removed:false,native_mask_semantics_or_service_execution_qualified:false};
        let mut count=Output{bytes:None,length:0,maximum:limits.maximum_result_bytes()};serde_json::to_writer(&mut count,&receipt).map_err(|_|E::Limit)?;
        let anchors:Vec<_>=plan.changes.iter().map(|c|c.source_text_anchor.clone()).collect();
        if anchors.len()!=plan.intents.len()||anchors.is_empty(){return Err(E::Selection);}
        let receipt_sha=bound_hash(&receipt)?;
        let sha=bound_hash(&("hwpx-agent.personal-info-mask-edit-inventory/v1",receipt.source_package_sha256,receipt.output_package_sha256,receipt_sha,&anchors))?;
        let inventory=SourcePersonalInfoMaskEditInventory{source:receipt.source_package_sha256,output:receipt.output_package_sha256,receipt_sha,anchors,sha};
        Ok(SourcePersonalInfoMaskCandidate{artifact,receipt,maximum_bytes:limits.maximum_result_bytes(),inventory})
    }
}
fn mask(index:&SourceTextIndex<'_>,chars:&[char],ids:&[usize],policy:SourcePersonalInfoMaskPolicy,remaining:usize,bytes:usize)
    ->Result<(Vec<unicode::transform::Change>,usize),E>{
    if chars.len()!=ids.len(){return Err(E::Selection);}if chars.len()>remaining{return Err(E::Limit);}
    let mut changes=Vec::new();
    match policy{
        SourcePersonalInfoMaskPolicy::ThreeAsterisksPerTextGroup=>{
            if chars!=['*','*','*']{if bytes<3{return Err(E::Limit);}changes.push(unicode::transform::Change{input:0..chars.len(),value:"***".into()});}
        },
        SourcePersonalInfoMaskPolicy::PerOriginalScalarPreserveSlots=>{
            let(mut i,mut used)=(0usize,0usize);
            while i<chars.len(){if chars[i]=='*'{i+=1;continue;}let point=index.points[ids[i]];let mut j=i+1;
                while j<chars.len()&&chars[j]!='*'{let p=index.points[ids[j]];if p.segment!=point.segment||p.atom!=point.atom{break;}j+=1;}
                used=used.checked_add(j-i).filter(|n|*n<=bytes).ok_or(E::Limit)?;
                changes.push(unicode::transform::Change{input:i..j,value:"*".repeat(j-i)});i=j;
            }
        },
    }Ok((changes,chars.len()))
}
fn bound_hash(value:&impl Serialize)->Result<[u8;32],E>{
    struct Hash{state:Sha256,length:usize}
    impl std::io::Write for Hash{fn write(&mut self,b:&[u8])->std::io::Result<usize>{self.length=self.length.checked_add(b.len()).filter(|n|*n<=4*1024*1024).ok_or_else(||std::io::Error::other("personal_info_binding_limit"))?;
        self.state.update(b);Ok(b.len())}fn flush(&mut self)->std::io::Result<()>{Ok(())}}
    let mut out=Hash{state:Sha256::new(),length:0};serde_json::to_writer(&mut out,value).map_err(|_|E::Limit)?;Ok(out.state.finalize().into())
}
