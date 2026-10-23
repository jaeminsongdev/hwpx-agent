//! Actual package meaning assessment. No URL execution, field update, flow inference or complete validation.
use domain_ir::{DocumentId,LogicalId,ReferenceAuxiliaryLimits};
use hwpx_package::document_import::{ImportedSourcePackage,SourceImportLimits,forms::ImportedDocumentForms,
    fields::{ImportedDocumentFields,semantics::{ImportedFieldMeaning,FieldSemanticImportError,
        source_index::{SourceFieldMeaningIndex,SourceFieldMeaningReceipt}}}};
use serde::Serialize;
use std::io;
use super::{ReferenceValidationProductOperation,source::{ReferenceSourceError,ReferenceSourceStatus}};

#[derive(Clone,Copy,Debug,Eq,PartialEq,Serialize)]
#[serde(rename_all="snake_case")]
pub enum ReferenceSourceMeaningKind{HttpsTarget,TableFormulaAst,BookmarkCrossReference,Unsupported}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct ReferenceSourceMeaningSelection{
    pub reference_id:LogicalId,pub source_field_sha256:[u8;32],pub meaning_sha256:[u8;32],pub kind:ReferenceSourceMeaningKind,
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct ReferenceSourceFieldMeaningAssessment{
    schema_version:&'static str,status:ReferenceSourceStatus,meaning_import:SourceFieldMeaningReceipt,
    selections:Vec<ReferenceSourceMeaningSelection>,reference_validation_or_external_approval:bool,
}
struct Output{bytes:Vec<u8>,maximum:usize}
impl io::Write for Output{
    fn write(&mut self,bytes:&[u8])->io::Result<usize>{
        self.bytes.len().checked_add(bytes.len()).filter(|n|*n<=self.maximum).ok_or_else(||io::Error::other("SOURCE_MEANING_OUTPUT_LIMIT"))?;
        self.bytes.try_reserve(bytes.len()).map_err(|_|io::Error::other("SOURCE_MEANING_ALLOCATION_LIMIT"))?;
        self.bytes.extend_from_slice(bytes);Ok(bytes.len())}
    fn flush(&mut self)->io::Result<()>{Ok(())}
}
impl ReferenceSourceFieldMeaningAssessment{
    #[must_use]pub const fn receipt(&self)->&SourceFieldMeaningReceipt{&self.meaning_import}
    #[must_use]pub fn selections(&self)->&[ReferenceSourceMeaningSelection]{&self.selections}
    /// # Errors
    /// Refuses truncation. Selection metadata contains hashes and kinds, never URI/formula/cache text.
    pub fn canonical_json(&self,limits:ReferenceAuxiliaryLimits)->Result<Vec<u8>,ReferenceSourceError>{
        let mut out=Output{bytes:Vec::new(),maximum:limits.config().output_bytes};
        serde_json::to_writer(&mut out,self).map_err(|_|ReferenceSourceError::Output)?;Ok(out.bytes)
    }
}
impl ReferenceValidationProductOperation{
    /// Produces an owned candidate only, using the existing source-derived field selectors and policy data.
    /// # Errors
    /// No source overwrite, URL access, storage/Native execution or issuer qualification occurs.
    pub fn prepare_package_https_target_changes(bytes:&[u8],document:DocumentId,expected_sha256:[u8;32],
        source_limits:SourceImportLimits,limits:ReferenceAuxiliaryLimits,
        requests:&[hwpx_package::document_import::fields::semantics::source_index::https_targets::SourceHttpsTargetChange<'_>],
        policy:&domain_ir::ExternalLinkPolicy,target_limits:domain_ir::LinkReferenceLimits,writer:hwpx_package::WriterLimits)
        ->Result<hwpx_package::document_import::fields::semantics::source_index::https_targets::SourceHttpsTargetCandidate,
            hwpx_package::document_import::fields::semantics::source_index::https_targets::SourceHttpsTargetError>{
        use hwpx_package::document_import::fields::semantics::source_index::https_targets::SourceHttpsTargetError as E;
        let source=ImportedSourcePackage::import(bytes,document,expected_sha256,source_limits).map_err(|_|E::Source)?;
        let forms=ImportedDocumentForms::import(source).map_err(|_|E::Source)?;
        let fields=ImportedDocumentFields::import(&forms).map_err(|_|E::Source)?;
        let index=SourceFieldMeaningIndex::import(&fields,limits).map_err(|error|match error{FieldSemanticImportError::Limit=>E::Limit,_=>E::Source})?;
        let proof=forms.reconstruct_source_for_verification(bytes).map_err(|_|E::Source)?;
        index.lower_https_target_candidates(&proof,requests,policy,target_limits,writer)
    }
    /// Reads exact source-derived supported meanings once and keeps unknown kinds explicit.
    /// # Errors
    /// Rejects bad source, malformed supported meanings, field coverage or finite budgets. Never opens a destination.
    pub fn assess_package_field_semantics(bytes:&[u8],document:DocumentId,expected_sha256:[u8;32],
        source_limits:SourceImportLimits,limits:ReferenceAuxiliaryLimits)->Result<ReferenceSourceFieldMeaningAssessment,ReferenceSourceError>{
        let source=ImportedSourcePackage::import(bytes,document,expected_sha256,source_limits)
            .map_err(|error|match error{hwpx_package::document_import::SourceImportError::SourceChanged=>ReferenceSourceError::Binding,
                hwpx_package::document_import::SourceImportError::Limit=>ReferenceSourceError::InputLimit,_=>ReferenceSourceError::Package})?;
        let forms=ImportedDocumentForms::import(source).map_err(|_|ReferenceSourceError::Forms)?;
        let fields=ImportedDocumentFields::import(&forms).map_err(|_|ReferenceSourceError::FieldRanges)?;
        super::source::check_whole_source_field_coverage(forms.body_structure(),&fields,limits)?;
        let index=SourceFieldMeaningIndex::import(&fields,limits).map_err(|error|match error{
            FieldSemanticImportError::Limit=>ReferenceSourceError::InputLimit,_=>ReferenceSourceError::FieldRanges})?;
        let mut selections=Vec::new();selections.try_reserve_exact(index.observations().len()).map_err(|_|ReferenceSourceError::InputLimit)?;
        for(i,(range,meaning))in fields.fields().iter().zip(index.observations()).enumerate(){
            if range.reference_id!=meaning.reference_id{return Err(ReferenceSourceError::Binding);}
            selections.push(ReferenceSourceMeaningSelection{reference_id:range.reference_id.clone(),source_field_sha256:range.begin_anchor.fingerprint_sha256,
                meaning_sha256:index.meaning_sha256(i).map_err(|_|ReferenceSourceError::InputLimit)?,kind:match meaning.meaning{
                    ImportedFieldMeaning::HttpsTarget{..}=>ReferenceSourceMeaningKind::HttpsTarget,
                    ImportedFieldMeaning::TableFormula{..}=>ReferenceSourceMeaningKind::TableFormulaAst,
                    ImportedFieldMeaning::BookmarkCrossReference{..}=>ReferenceSourceMeaningKind::BookmarkCrossReference,
                    ImportedFieldMeaning::Unsupported{..}=>ReferenceSourceMeaningKind::Unsupported}});
        }
        let result=ReferenceSourceFieldMeaningAssessment{schema_version:"hwpx-agent.product.reference-source-field-meanings/v2",
            status:ReferenceSourceStatus::Incomplete,meaning_import:index.receipt().clone(),selections,reference_validation_or_external_approval:false};
        let _=result.canonical_json(limits)?;Ok(result)
    }
}
