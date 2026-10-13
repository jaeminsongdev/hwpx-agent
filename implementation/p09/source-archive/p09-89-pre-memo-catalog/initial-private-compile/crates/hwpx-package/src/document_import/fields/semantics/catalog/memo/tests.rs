use super::super::*;
use crate::document_import::{ImportedSourcePackage, SourceImportLimits, forms::ImportedDocumentForms,
    fields::{ImportedDocumentFields,semantics::ImportedDocumentFieldSemantics}};
use domain_ir::DocumentId;
use sha2::{Digest as _,Sha256};
mod fixture {use crate as hwpx_package;include!(concat!(env!("CARGO_MANIFEST_DIR"),"/tests/support/document_import_memo_catalog_fixture.rs"));}
type TestResult=Result<(),Box<dyn std::error::Error>>;
#[test]
fn cached_memo_section_reference_binding_and_receipt_mutations_are_rejected() -> TestResult {
    let bytes=fixture::package(&fixture::table(&fixture::style(12),1),Some("12"))?;
    let forms=ImportedDocumentForms::import(ImportedSourcePackage::import(&bytes,DocumentId::parse("memo-private")?,Sha256::digest(&bytes).into(),SourceImportLimits::default())?)?;
    let fields=ImportedDocumentFields::import(&forms)?;let meanings=ImportedDocumentFieldSemantics::import(&fields)?;
    for fault in 0..5 {
        let mut catalog=ImportedDocumentCatalog::import(&meanings)?;
        match fault {
            0=>catalog.memo_uses[0].native_reference=Some(999),
            1=>catalog.memo_uses[0].binding=MemoCatalogBinding::UnresolvedMissingDefinition,
            2=>catalog.receipt.memo_properties=0,
            3=>{catalog.memo_uses.clear();}
            _=>{catalog.memo_uses[0].section_properties_anchor=None;}
        }
        assert!(catalog.verify_source(&bytes).is_err());
    }
    Ok(())
}
