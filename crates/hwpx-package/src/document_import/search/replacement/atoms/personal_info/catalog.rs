//! Whole original catalog search -> exact matched scalar masking, not masking the entire selected scope.
use super::*;
use crate::document_import::search::personal_info::catalog::{SourcePersonalInfoCatalog,PersonalInfoCatalogFamily,
    PersonalInfoCatalogReceipt,PersonalInfoCatalogError};
use thiserror::Error;
pub const SOURCE_PERSONAL_INFO_CATALOG_MASK_PROFILE:&str="hwpx-agent.source-personal-info-catalog-mask/v1";
#[derive(Clone,Copy,Debug,Eq,PartialEq,Error)]
pub enum SourcePersonalInfoCatalogMaskError{
    #[error("PERSONAL_INFO_CATALOG_MASK_FORMAT_REJECTED")]Catalog(#[from]PersonalInfoCatalogError),
    #[error("PERSONAL_INFO_CATALOG_MASK_LOWERING_REJECTED")]Replacement(#[from]SourceLiteralReplacementError),
}
type M=SourcePersonalInfoCatalogMaskError;
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourcePersonalInfoCatalogMaskReceipt{
    pub profile:&'static str,pub source_package_sha256:[u8;32],pub source_index_sha256:[u8;32],pub scope:SourceIndexScopeReceipt,
    pub catalog:PersonalInfoCatalogReceipt,pub catalog_policy_sha256:[u8;32],pub detection_request_sha256:[u8;32],pub detection_result_sha256:[u8;32],
    pub body_policy:SourceReviewTextPolicy,pub mask_policy:SourcePersonalInfoMaskPolicy,pub request_sha256:[u8;32],
    pub selected_patterns:usize,pub matched_formats:usize,pub matched_original_scalars:usize,pub matched_text_groups:usize,
    pub changed_components:usize,pub changed_scalar_ranges:usize,pub changed_parts:usize,
    pub excluded_hidden_paragraphs:usize,pub excluded_memo_paragraphs:usize,pub observed_protection_parts:usize,pub observed_protection_element_visits:usize,
    pub source_review_import:ReviewBodyImportReceipt,pub output_review_import:ReviewBodyImportReceipt,pub output_package_sha256:[u8;32],pub output_bytes:usize,
    pub exact_original_match_selections_verified:bool,pub original_run_shells_styles_controls_and_references_preserved:bool,pub output_spans_and_outside_slots_verified:bool,
    pub whole_package_personal_data_removed:bool,pub native_catalog_mask_semantics_or_service_execution_qualified:bool,
}
pub struct SourcePersonalInfoCatalogMaskCandidate{artifact:PackageArtifact,receipt:SourcePersonalInfoCatalogMaskReceipt,
    maximum_bytes:usize,inventory:SourcePersonalInfoMaskEditInventory}
impl fmt::Debug for SourcePersonalInfoCatalogMaskCandidate{
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("SourcePersonalInfoCatalogMaskCandidate(<redacted>; matched_scalars_not_package_sanitization)")}
}
impl SourcePersonalInfoCatalogMaskCandidate{
    #[must_use]pub const fn receipt(&self)->&SourcePersonalInfoCatalogMaskReceipt{&self.receipt}
    #[must_use]pub const fn edit_inventory(&self)->&SourcePersonalInfoMaskEditInventory{&self.inventory}
    /// # Errors
    /// Immutable writer integrity only. No current source/config/access, commit or Native permission is granted.
    pub fn with_verified_bytes<T>(&self,consume:impl FnOnce(&[u8])->T)->Result<T,WriterError>{self.artifact.with_verified_bytes(consume)}
    /// # Errors
    /// Metadata only: catalog/config binding, not pattern bodies, source values or per-value hashes.
    pub fn canonical_json(&self)->Result<Vec<u8>,M>{let mut out=Output{bytes:Some(Vec::new()),length:0,maximum:self.maximum_bytes};
        serde_json::to_writer(&mut out,&self.receipt).map_err(|_|E::Limit)?;Ok(out.bytes.ok_or(E::Limit)?)}
}
impl ImportedDocumentForms{
    /// # Errors
    /// Exact whole original proof and explicitly selected full catalog families. The source is never edited in place.
    pub fn lower_personal_info_catalog_mask_candidate(&self,fresh:&[u8],catalog:&SourcePersonalInfoCatalog,families:&[PersonalInfoCatalogFamily],
        selector:SourceIndexScopeSelector<'_>,body:SourceReviewTextPolicy,policy:SourcePersonalInfoMaskPolicy,limits:SourceSearchLimits,writer:WriterLimits)
        ->Result<SourcePersonalInfoCatalogMaskCandidate,M>{
        Ok(self.reconstruct_source_for_verification(fresh).map_err(|_|E::Source)?
            .lower_personal_info_catalog_mask_candidate(self,catalog,families,selector,body,policy,limits,writer)?)
    }
}
impl VerifiedFormReconstruction<'_>{
    /// # Errors
    /// One fields/review/index, one full selected-catalog scan, one preserving writer and one whole-output readback.
    /// Every matched scalar is checked; no no-match, protected or inexact occurrence is silently omitted.
    pub fn lower_personal_info_catalog_mask_candidate(&self,original:&ImportedDocumentForms,catalog:&SourcePersonalInfoCatalog,
        families:&[PersonalInfoCatalogFamily],selector:SourceIndexScopeSelector<'_>,body:SourceReviewTextPolicy,policy:SourcePersonalInfoMaskPolicy,
        limits:SourceSearchLimits,writer:WriterLimits)->Result<SourcePersonalInfoCatalogMaskCandidate,M>{
        let rebuilt=self.for_original(original).map_err(|_|E::Source)?;
        let protection=original.source().observe_protection_signals().map_err(|_|E::Protection)?;
        protection.require_no_observed_document_signals().map_err(|_|E::Protection)?;
        let fields=ImportedDocumentFields::import(original).map_err(|_|E::Source)?;
        let review=ImportedDocumentReviewBodies::import_bound_fields(original,&fields).map_err(|_|E::Source)?;
        let index=SourceReviewScopeIndex::from_review(original,&review,limits).map_err(E::from)?;
        let prepared=catalog.prepare(families,limits)?;let found=index.find_personal_info_catalog(&prepared,selector,body)?;
        let text=index.source_index();let matches=found.search().result();
        if matches.index_receipt()!=&text.receipt{return Err(E::Source.into());}
        if matches.matches().is_empty(){return Err(E::NoMatches.into());}
        let mut selected=BTreeSet::new();let mut groups=Vec::new();
        for matched in matches.matches(){
            let origins=selected_origins(text,matched)?;
            for &origin in &origins{
                let &(a,b)=text.usage.get(origin).ok_or(E::Selection)?;
                if a<matched.start_normalized_scalar||b>=matched.end_normalized_scalar||!selected.insert(origin){return Err(E::Selection.into());}
            }
            // Adjacent pattern matches remain different mask groups; controls split groups in the shared compiler.
            groups.push(origins.into_iter().collect());
        }
        let context=review::ReviewWriteContext::new(text.original.source(),&fields,&review,body)?;
        let plan=unicode::plan::compile_mapped(text,&fields,&context,groups,selected,
            |chars,ids,remaining,bytes|mask(text,chars,ids,policy,remaining,bytes))?;
        let artifact=styles::text::output::build(text.original.source(),rebuilt.source().original.as_ref(),&plan.intents,&plan.spans,writer)?;
        let output_review=readback::verify_artifact(text.original.source(),&artifact,&plan.spans,Some(&context))?.ok_or(E::Readback)?;
        let detection_result_sha256=bound_hash(&found)?;
        let request_sha256=bound_hash(&(SOURCE_PERSONAL_INFO_CATALOG_MASK_PROFILE,text.receipt.index_sha256,prepared.request_sha256(),
            found.search().request_sha256(),detection_result_sha256,body,policy))?;
        let(hidden,memo)=found.search().transformation_exclusions();
        let receipt=SourcePersonalInfoCatalogMaskReceipt{profile:SOURCE_PERSONAL_INFO_CATALOG_MASK_PROFILE,
            source_package_sha256:original.source().receipt().source_package_sha256,source_index_sha256:text.receipt.index_sha256,
            scope:found.search().scope_receipt().clone(),catalog:catalog.receipt().clone(),catalog_policy_sha256:prepared.request_sha256(),
            detection_request_sha256:found.search().request_sha256(),detection_result_sha256,body_policy:body,mask_policy:policy,request_sha256,
            selected_patterns:prepared.selected_pattern_count(),matched_formats:matches.matches().len(),matched_original_scalars:plan.selected,matched_text_groups:plan.groups,
            changed_components:plan.components,changed_scalar_ranges:plan.ranges,changed_parts:plan.spans.len(),excluded_hidden_paragraphs:hidden,excluded_memo_paragraphs:memo,
            observed_protection_parts:protection.counts().parts,
            observed_protection_element_visits:protection.counts().protection_element_visits.checked_add(plan.visits).ok_or(E::Limit)?,
            source_review_import:review.receipt().clone(),output_review_import:output_review,output_package_sha256:artifact.sha256(),output_bytes:artifact.size_bytes(),
            exact_original_match_selections_verified:true,original_run_shells_styles_controls_and_references_preserved:true,output_spans_and_outside_slots_verified:true,
            whole_package_personal_data_removed:false,native_catalog_mask_semantics_or_service_execution_qualified:false};
        let mut count=Output{bytes:None,length:0,maximum:limits.maximum_result_bytes()};serde_json::to_writer(&mut count,&receipt).map_err(|_|E::Limit)?;
        let anchors:Vec<_>=plan.changes.iter().map(|c|c.source_text_anchor.clone()).collect();
        if anchors.len()!=plan.intents.len()||anchors.is_empty(){return Err(E::Selection.into());}
        let receipt_sha=bound_hash(&receipt)?;
        let sha=bound_hash(&("hwpx-agent.personal-info-catalog-mask-edit-inventory/v1",receipt.source_package_sha256,receipt.output_package_sha256,receipt_sha,&anchors))?;
        let inventory=SourcePersonalInfoMaskEditInventory{source:receipt.source_package_sha256,output:receipt.output_package_sha256,receipt_sha,anchors,sha};
        Ok(SourcePersonalInfoCatalogMaskCandidate{artifact,receipt,maximum_bytes:limits.maximum_result_bytes(),inventory})
    }
}
