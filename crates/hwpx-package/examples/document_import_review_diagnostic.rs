//! Counts only. No raw XML, author, timestamps, memo text or attribute values.
use domain_ir::DocumentId;
use hwpx_package::document_import::{
    ImportedSourcePackage, SourceImportLimits, fields::ImportedDocumentFields,
    forms::ImportedDocumentForms,
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use std::{collections::BTreeSet, error::Error};
#[path = "../tests/support/document_import_settings_inputs.rs"]
mod inputs;
const HH: &str = "http://www.hancom.co.kr/hwpml/2011/head";
const HP: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
#[derive(Default, Serialize)]
struct Shape {
    inputs: usize,
    inputs_with_memo_styles: usize,
    memo_collections: usize,
    memo_style_records: usize,
    section_memo_references: usize,
    memo_field_ranges: usize,
    hidden_comment_elements: usize,
    memo_attribute_names: BTreeSet<String>,
}
fn main() -> Result<(), Box<dyn Error>> {
    let mut result = Shape::default();
    for bytes in inputs::actual_corpus()? {
        let forms = ImportedDocumentForms::import(ImportedSourcePackage::import(
            &bytes,
            DocumentId::parse("review-source-diagnostic")?,
            Sha256::digest(&bytes).into(),
            SourceImportLimits::default(),
        )?)?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let mut styles = 0;
        for part in forms.source().parts() {
            let Some(xml) = part.xml() else {
                continue;
            };
            for e in xml.elements() {
                match (e.name().namespace(), e.name().local_name()) {
                    (Some(HH), "memoProperties") => result.memo_collections += 1,
                    (Some(HH), "memoPr") => {
                        styles += 1;
                        for a in e
                            .attributes()
                            .iter()
                            .filter(|a| !a.is_namespace_declaration())
                        {
                            result
                                .memo_attribute_names
                                .insert(a.name().qualified_name().to_owned());
                        }
                    }
                    (Some(HP), "secPr") => {
                        result.section_memo_references +=
                            usize::from(e.attributes().iter().any(|a| {
                                a.name().namespace().is_none()
                                    && a.name().local_name() == "memoShapeIDRef"
                            }));
                    }
                    (Some(HP), "hiddenComment") => result.hidden_comment_elements += 1,
                    _ => (),
                }
            }
        }
        result.inputs += 1;
        result.inputs_with_memo_styles += usize::from(styles > 0);
        result.memo_style_records += styles;
        result.memo_field_ranges += fields
            .fields()
            .iter()
            .filter(|f| f.native_kind == "MEMO")
            .count();
    }
    println!("{}", serde_json::to_string(&result)?);
    Ok(())
}
