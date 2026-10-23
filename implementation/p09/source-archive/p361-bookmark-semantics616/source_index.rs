//! Borrow the original fields and read typed meanings once; no additional document graph clone.
use super::*;
use domain_ir::ReferenceAuxiliaryLimits;
use sha2::{Digest as _,Sha256};
use std::io;
pub mod https_targets;

#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceFieldMeaningReceipt {
    pub profile:&'static str,pub source_package_sha256:[u8;32],pub field_graph_sha256:[u8;32],
    pub meaning_inventory_sha256:[u8;32],pub ranges:usize,pub https_targets:usize,pub table_formula_asts:usize,
    pub unsupported_meanings:usize,pub additional_document_graph_clones:usize,
    pub complete_reference_state_or_external_approval:bool,
}

pub struct SourceFieldMeaningIndex<'a,'source> {
    fields:&'a ImportedDocumentFields<'source>,observations:Vec<ImportedFieldSemantic>,
    receipt:SourceFieldMeaningReceipt,limits:ReferenceAuxiliaryLimits,
}
impl fmt::Debug for SourceFieldMeaningIndex<'_,'_>{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{
    f.debug_struct("SourceFieldMeaningIndex").field("ranges",&self.observations.len()).finish_non_exhaustive()}}

struct HashOutput{sha:Sha256,bytes:usize,maximum:usize}
impl io::Write for HashOutput{
    fn write(&mut self,bytes:&[u8])->io::Result<usize>{
        let n=self.bytes.checked_add(bytes.len()).filter(|n|*n<=self.maximum).ok_or_else(||io::Error::other("SOURCE_MEANING_OUTPUT_LIMIT"))?;
        self.sha.update(bytes);self.bytes=n;Ok(bytes.len())}
    fn flush(&mut self)->io::Result<()>{Ok(())}
}
pub(crate) fn bounded_digest(value:&impl Serialize,maximum:usize)->Result<[u8;32],FieldSemanticImportError>{
    let mut output=HashOutput{sha:Sha256::new(),bytes:0,maximum};
    serde_json::to_writer(&mut output,value).map_err(|_|FieldSemanticImportError::Limit)?;Ok(output.sha.finalize().into())
}
impl<'a,'source> SourceFieldMeaningIndex<'a,'source>{
    /// Uses the unchanged HTTPS six-parameter and table formula readers and original aggregate work ceiling.
    /// # Errors
    /// Rejects invalid supported meanings, requested budgets or source bindings. Unknown kinds stay explicit.
    pub fn import(fields:&'a ImportedDocumentFields<'source>,limits:ReferenceAuxiliaryLimits)->Result<Self,FieldSemanticImportError>{
        if fields.fields().len()>limits.config().items_per_kind||fields.forms.graph().sections().len()>limits.config().sections{return Err(FieldSemanticImportError::Limit);}
        let observations=read_meanings(fields)?;
        let meaning_inventory_sha256=bounded_digest(&observations,limits.config().output_bytes)?;
        for observation in &observations {
            if let ImportedFieldMeaning::HttpsTarget{target:HyperlinkTarget::Https{uri}}=&observation.meaning
                &&uri.len()>limits.config().text_bytes{return Err(FieldSemanticImportError::Limit);}
        }
        let receipt=SourceFieldMeaningReceipt{profile:"hwpx-agent.source-field-meaning-index/partial-v1",
            source_package_sha256:fields.receipt().source_package_sha256,field_graph_sha256:fields.receipt().graph_sha256,
            meaning_inventory_sha256,ranges:observations.len(),
            https_targets:observations.iter().filter(|o|matches!(o.meaning,ImportedFieldMeaning::HttpsTarget{..})).count(),
            table_formula_asts:observations.iter().filter(|o|matches!(o.meaning,ImportedFieldMeaning::TableFormula{..})).count(),
            unsupported_meanings:observations.iter().filter(|o|matches!(o.meaning,ImportedFieldMeaning::Unsupported{..})).count(),
            additional_document_graph_clones:0,complete_reference_state_or_external_approval:false};
        Ok(Self{fields,observations,receipt,limits})
    }
    #[must_use]pub const fn receipt(&self)->&SourceFieldMeaningReceipt{&self.receipt}
    #[must_use]pub fn observations(&self)->&[ImportedFieldSemantic]{&self.observations}
    /// Hashes typed meaning data without exposing URI/formula/private text in a selection receipt.
    /// # Errors
    /// Rejects an out-of-range selection or finite serialization budget.
    pub fn meaning_sha256(&self,index:usize)->Result<[u8;32],FieldSemanticImportError>{
        bounded_digest(self.observations.get(index).ok_or(FieldSemanticImportError::Binding)?,self.limits.config().output_bytes)
    }
    /// # Errors
    /// Fresh whole-source reconstruction, exact original identity and full range/meaning comparisons remain required.
    pub fn verify_reconstruction(&self,reconstruction:&VerifiedFormReconstruction<'_>)->Result<SourceFieldMeaningReceipt,FieldSemanticImportError>{
        let forms=reconstruction.for_original(self.fields.forms).map_err(FieldRangeImportError::from)?;
        let fields=ImportedDocumentFields::import(forms)?;self.fields.verify_rebuilt(&fields)?;
        let rebuilt=Self::import_for_verification(&fields,self.limits)?;
        if self.observations!=rebuilt.0||self.receipt!=rebuilt.1{return Err(FieldSemanticImportError::Binding);}Ok(rebuilt.1)
    }
    fn import_for_verification(fields:&ImportedDocumentFields<'_>,limits:ReferenceAuxiliaryLimits)
        ->Result<(Vec<ImportedFieldSemantic>,SourceFieldMeaningReceipt),FieldSemanticImportError>{
        let fresh=SourceFieldMeaningIndex::import(fields,limits)?;Ok((fresh.observations,fresh.receipt))
    }
}
