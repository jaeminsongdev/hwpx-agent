mod bindings;
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
    bindings::verify(original, &meanings, &evaluated)?;
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
        let selected: Vec<_> = edits.iter().filter(|e| e.part == path).collect();
        let wanted = expected_part(old, selected)?;
        if output.read_entry(j).map_err(|_| Error::Preservation)? != wanted {
            return Err(Error::Preservation);
        }
    }
    Ok(())
}

fn expected_part(mut wanted: Vec<u8>, mut selected: Vec<&LeafEdit>) -> Result<Vec<u8>, Error> {
    // Move only this fresh bounded read's buffer, never the immutable source package.
    // Bounds stay tied to the ORIGINAL length even when earlier splices resize it.
    let original_len = wanted.len();
    selected.sort_by_key(|e| e.start);
    if selected.windows(2).any(|w| w[0].end > w[1].start) {
        return Err(Error::Preservation);
    }
    // Numbers/native commands are exact validated ASCII; no raw XML or escaping aliases.
    for edit in selected.into_iter().rev() {
        if !edit.value.is_ascii() || edit.value.contains(['&', '<', '>']) || edit.end > original_len
        {
            return Err(Error::Preservation);
        }
        let replacement = match &edit.empty_name {
            Some(name) => format!(">{}</{name}>", edit.value),
            None => edit.value.clone(),
        };
        wanted.splice(edit.start..edit.end, replacement.bytes());
    }
    Ok(wanted)
}

#[cfg(test)]
mod tests {
    use super::*;

    // Independent pre-r7 allocating algorithm; retain original checks and their order.
    fn allocating_oracle(old: &[u8], mut selected: Vec<&LeafEdit>) -> Result<Vec<u8>, Error> {
        let mut wanted = old.to_vec();
        selected.sort_by_key(|e| e.start);
        if selected.windows(2).any(|w| w[0].end > w[1].start) {
            return Err(Error::Preservation);
        }
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
        Ok(wanted)
    }

    fn edit(start: usize, end: usize, value: &str, empty_name: Option<&str>) -> LeafEdit {
        LeafEdit {
            part: "Contents/section0.xml".into(),
            start,
            end,
            value: value.into(),
            empty_name: empty_name.map(str::to_owned),
        }
    }

    #[test]
    fn unchanged_large_part_reuses_fresh_buffer_and_keeps_all_bytes() {
        for size in [0, 1, 32769, 131072] {
            let input: Vec<_> = (0..size).map(|i| (i % 251) as u8).collect();
            let expected = allocating_oracle(&input, vec![]).unwrap();
            let pointer = input.as_ptr();
            let capacity = input.capacity();
            let actual = expected_part(input, vec![]).unwrap();
            assert_eq!(actual, expected);
            assert_eq!(actual.as_ptr(), pointer);
            assert_eq!(actual.capacity(), capacity);
        }
    }

    #[test]
    fn all_valid_spans_values_and_empty_names_match_allocating_oracle() {
        let original = b"<hp:t>123456789</hp:t>";
        for start in 0..=original.len() {
            for end in start..=original.len() {
                for value in ["", "0", "-900001.25", "SUM(A1:B1)"] {
                    for empty_name in [None, Some("hp:t")] {
                        let e = edit(start, end, value, empty_name);
                        assert_eq!(
                            expected_part(original.to_vec(), vec![&e]),
                            allocating_oracle(original, vec![&e])
                        );
                    }
                }
            }
        }
    }

    #[test]
    fn reverse_edits_use_original_offsets_and_length_after_growth_and_shrink() {
        let original = b"abcdefghi";
        for value in ["", "000000000000000000000", "-9"] {
            let first = edit(1, 3, value, None);
            let last = edit(7, 9, "", None);
            let insertion = edit(4, 4, "42", Some("hp:t"));
            for selected in [
                vec![&first, &last, &insertion],
                vec![&last, &insertion, &first],
            ] {
                assert_eq!(
                    expected_part(original.to_vec(), selected.clone()),
                    allocating_oracle(original, selected)
                );
            }
        }
    }

    #[test]
    fn original_ascii_bounds_and_overlap_failures_are_not_weakened() {
        let original = b"123456789";
        for value in ["\u{ac00}", "1&2", "<1", "1>"] {
            let e = edit(0, 1, value, None);
            assert_eq!(
                expected_part(original.to_vec(), vec![&e]),
                Err(Error::Preservation)
            );
            assert_eq!(
                allocating_oracle(original, vec![&e]),
                Err(Error::Preservation)
            );
        }
        let outside = edit(8, 10, "1", None);
        let first = edit(1, 4, "2", None);
        let overlap = edit(3, 5, "3", None);
        for selected in [
            vec![&outside],
            vec![&first, &overlap],
            vec![&overlap, &first, &outside],
        ] {
            assert_eq!(
                expected_part(original.to_vec(), selected.clone()),
                Err(Error::Preservation)
            );
            assert_eq!(
                allocating_oracle(original, selected),
                Err(Error::Preservation)
            );
        }
    }
}
