//! Reuse one output source/structure for strict legacy or exact Form/review-bound number readback.
use super::*;
use crate::document_import::{forms::ImportedDocumentForms,fields::ImportedDocumentFields,
    structure::review::{ImportedDocumentReviewBodies,ReviewBodyImportReceipt}};
pub(super) enum BatchOutputImport{Body(ImportedDocumentStructure),Review(ImportedDocumentForms)}
impl BatchOutputImport{
    pub(super) fn import(source:ImportedSourcePackage,review:bool)->Result<Self,E>{
        if review{Ok(Self::Review(ImportedDocumentForms::import(source).map_err(|_|E::Readback)?))}
        else{Ok(Self::Body(ImportedDocumentStructure::import(source).map_err(|_|E::Readback)?))}
    }
    pub(super) fn structure(&self)->&ImportedDocumentStructure{match self{Self::Body(s)=>s,Self::Review(f)=>f.body_structure()}}
    pub(super) fn numbering(&self,limits:ReferenceAuxiliaryLimits,receipt:&mut Option<ReviewBodyImportReceipt>)->Result<ImportedCaptionNumbering<'_>,E>{
        match self{Self::Body(s)=>ImportedCaptionNumbering::import(s,limits).map_err(|_|E::Readback),Self::Review(forms)=>{
            let fields=ImportedDocumentFields::import(forms).map_err(|_|E::Readback)?;
            let review=ImportedDocumentReviewBodies::import_bound_fields(forms,&fields).map_err(|_|E::Readback)?;
            let numbers=ImportedCaptionNumbering::import_review_bound(forms,&review,limits).map_err(|_|E::Readback)?;
            *receipt=Some(review.receipt().clone());Ok(numbers)
        }}
    }
}
