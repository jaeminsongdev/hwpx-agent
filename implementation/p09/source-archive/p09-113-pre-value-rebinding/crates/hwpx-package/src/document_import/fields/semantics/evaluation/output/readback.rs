use super::{FormulaResultOutputError as Error, ImportedSourceFormulaEvaluation, LeafEdit};
use crate::{
    BoundedZipReader,
    document_import::{
        ImportedSourcePackage,
        fields::{
            ImportedDocumentFields,
            semantics::{ImportedDocumentFieldSemantics, ImportedFieldMeaning},
        },
        forms::ImportedDocumentForms,
    },
};
use domain_ir::{FormulaCache, FormulaValue};
use sha2::{Digest as _, Sha256};
use std::io::Cursor;

pub(super) fn verify(
    original: &ImportedSourceFormulaEvaluation<'_, '_, '_>,
    bytes: &[u8],
    edits: &[LeafEdit],
) -> Result<(), Error> {
    let source = original.meanings.fields.forms.source();
    let forms = ImportedDocumentForms::import(
        ImportedSourcePackage::import(
            bytes,
            source.document_id.clone(),
            Sha256::digest(bytes).into(),
            source.limits,
        )
        .map_err(|_| Error::Readback)?,
    )
    .map_err(|_| Error::Readback)?;
    let fields = ImportedDocumentFields::import(&forms).map_err(|_| Error::Readback)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields).map_err(|_| Error::Readback)?;
    let evaluated =
        ImportedSourceFormulaEvaluation::import(&meanings).map_err(|_| Error::Readback)?;
    if fields.fields().len() != original.meanings.fields.fields().len()
        || meanings.observations().len() != original.meanings.observations().len()
        || evaluated.values().len() != original.values.len()
        || evaluated.source_bindings().len() != original.bindings.len()
    {
        return Err(Error::Readback);
    }
    for (old, new) in original.values.iter().zip(evaluated.values()) {
        if old.value != new.value || old.coordinate != new.coordinate {
            return Err(Error::Readback);
        }
    }
    for (old, new) in original
        .meanings
        .observations()
        .iter()
        .zip(meanings.observations())
    {
        match (&old.meaning, &new.meaning) {
            (
                ImportedFieldMeaning::TableFormula {
                    dimensions: od,
                    formula: of,
                },
                ImportedFieldMeaning::TableFormula {
                    dimensions: nd,
                    formula: nf,
                },
            ) => {
                if od != nd
                    || of.owner() != nf.owner()
                    || of.ast() != nf.ast()
                    || of.number_format() != nf.number_format()
                {
                    return Err(Error::Readback);
                }
                let value = original
                    .values
                    .iter()
                    .find(|v| v.reference_id == old.reference_id)
                    .ok_or(Error::Readback)?;
                if !matches!(nf.cache(), FormulaCache::Unverified { value: FormulaValue::Decimal { value: cached } } if cached == &value.value)
                {
                    return Err(Error::Readback);
                }
            }
            (old, new) if old == new => (),
            _ => return Err(Error::Readback),
        }
    }
    verify_parts(source, bytes, edits)
}
fn verify_parts(
    source: &ImportedSourcePackage,
    bytes: &[u8],
    edits: &[LeafEdit],
) -> Result<(), Error> {
    let mut input = BoundedZipReader::open(
        Cursor::new(source.original.as_ref()),
        source.limits.zip().map_err(|_| Error::Readback)?,
    )
    .map_err(|_| Error::Readback)?;
    let mut output = BoundedZipReader::open(
        Cursor::new(bytes),
        source.limits.zip().map_err(|_| Error::Readback)?,
    )
    .map_err(|_| Error::Readback)?;
    if input.entries().len() != output.entries().len() {
        return Err(Error::Preservation);
    }
    for i in 0..input.entries().len() {
        let path = input.entries()[i].path.as_str().to_owned();
        let j = output
            .entries()
            .iter()
            .position(|p| p.path.as_str() == path)
            .ok_or(Error::Preservation)?;
        let old = input.read_entry(i).map_err(|_| Error::Preservation)?;
        let mut wanted = old.clone();
        let mut selected: Vec<_> = edits.iter().filter(|e| e.part == path).collect();
        selected.sort_by_key(|e| e.start);
        if selected.windows(2).any(|w| w[0].end > w[1].start) {
            return Err(Error::Preservation);
        }
        // Numbers/native commands are exact validated ASCII; no raw XML or escaping aliases.
        for edit in selected.into_iter().rev() {
            if !edit.value.is_ascii()
                || edit.value.contains(['&', '<', '>'])
                || edit.end > old.len()
            {
                return Err(Error::Preservation);
            }
            let replacement = match &edit.empty_name {
                Some(name) => format!(">{}</{name}>", edit.value),
                None => edit.value.clone(),
            };
            wanted.splice(edit.start..edit.end, replacement.bytes());
        }
        if output.read_entry(j).map_err(|_| Error::Preservation)? != wanted {
            return Err(Error::Preservation);
        }
    }
    Ok(())
}
