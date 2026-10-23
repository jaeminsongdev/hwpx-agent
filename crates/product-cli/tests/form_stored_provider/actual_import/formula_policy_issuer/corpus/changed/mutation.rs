//! Independent one-leaf expanded package reconstruction; originals never written or values printed.
use super::*;
use domain_ir::{CellCoordinate, FormulaExpression};
use hwpx_package::PreservingXmlDocument;
use hwpx_package::document_import::fields::{
    ImportedDocumentFields,
    semantics::{
        ImportedDocumentFieldSemantics, ImportedFieldMeaning,
        evaluation::ImportedSourceFormulaEvaluation,
    },
};
const HP: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";

pub(super) fn numeric_derivative(original: &[u8]) -> AnyResult<Vec<u8>> {
    // Bind the input to the ORIGINAL AST and original source anchor, not table order.
    let index = referenced_numeric_leaf(original)?;
    let mut parts = fixture::entries(original)?;
    let bytes = parts
        .get_mut("Contents/section0.xml")
        .ok_or("numeric source section")?;
    let xml = PreservingXmlDocument::parse(bytes)?;
    let span = xml.elements()[index]
        .content_span()
        .ok_or("numeric input span")?;
    let number = std::str::from_utf8(&bytes[span.start()..span.end()])?.parse::<i64>()?;
    let replacement = number
        .checked_add(101)
        .ok_or("numeric derivative overflow")?
        .to_string();
    bytes.splice(span.start()..span.end(), replacement.bytes());
    let changed = fixture::pack(&parts)?;
    verify_one_leaf(original, &changed, index)?;
    Ok(changed)
}

fn referenced_numeric_leaf(original: &[u8]) -> AnyResult<usize> {
    let forms =
        super::super::super::super::field_ranges::fixture::forms(original, "actual-form-document")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let evaluated = ImportedSourceFormulaEvaluation::import(&meanings)?;
    let [target] = evaluated.values() else {
        return Err("one formula target required".into());
    };
    let formula = meanings
        .observations()
        .iter()
        .find_map(|m| {
            if m.reference_id == target.reference_id
                && let ImportedFieldMeaning::TableFormula { formula, .. } = &m.meaning
            {
                return Some(formula);
            }
            None
        })
        .ok_or("original formula AST")?;
    let binding = evaluated
        .source_bindings()
        .iter()
        .find(|b| {
            b.table_id == target.table_id
                && b.interpretation == "observed_canonical_decimal_text"
                && references(formula.ast().expression(), b.coordinate)
        })
        .ok_or("referenced numeric source binding")?;
    let resolved = forms.source().resolve_anchor(&binding.source_anchor)?;
    if resolved.part().path().as_str() != "Contents/section0.xml" {
        return Err("numeric source section outside derivative scope".into());
    }
    let xml = resolved.part().xml().ok_or("numeric source XML")?;
    let cell = resolved.element().ok_or("numeric bound cell")?;
    let span = cell.outer_span().ok_or("numeric bound span")?;
    xml.elements()
        .iter()
        .position(|e| {
            e.name().namespace() == Some(HP)
                && e.name().local_name() == "t"
                && e.outer_span()
                    .is_some_and(|s| s.start() >= span.start() && s.end() <= span.end())
        })
        .ok_or("referenced numeric text".into())
}

fn references(expression: &FormulaExpression, cell: CellCoordinate) -> bool {
    match expression {
        FormulaExpression::Decimal { .. } => false,
        FormulaExpression::Cell { reference } => {
            reference.row == cell.row && reference.column == cell.column
        }
        FormulaExpression::Range { range } => {
            cell.row >= range.start.row
                && cell.row <= range.end.row
                && cell.column >= range.start.column
                && cell.column <= range.end.column
        }
        FormulaExpression::Unary { operand, .. } => references(operand, cell),
        FormulaExpression::Binary { left, right, .. } => {
            references(left, cell) || references(right, cell)
        }
        FormulaExpression::Function { arguments, .. } => {
            arguments.iter().any(|a| references(a, cell))
        }
    }
}

fn verify_one_leaf(original: &[u8], changed: &[u8], index: usize) -> TestResult {
    let old = fixture::entries(original)?;
    let next = fixture::entries(changed)?;
    assert!(
        old.keys().eq(next.keys()),
        "numeric_derivative_inventory_changed"
    );
    let part = "Contents/section0.xml";
    for (path, bytes) in &old {
        if path != part {
            assert!(
                next.get(path) == Some(bytes),
                "numeric_derivative_other_part_changed"
            );
        }
    }
    let old_bytes = old.get(part).ok_or("original section")?;
    let next_bytes = next.get(part).ok_or("derived section")?;
    let xml = PreservingXmlDocument::parse(old_bytes)?;
    let newer = PreservingXmlDocument::parse(next_bytes)?;
    assert_eq!(xml.elements().len(), newer.elements().len());
    let a = &xml.elements()[index];
    let b = &newer.elements()[index];
    assert!(
        a.name().namespace() == Some(HP)
            && a.name().local_name() == "t"
            && a.name() == b.name()
            && a.parent() == b.parent()
            && a.first_child().is_none()
            && b.first_child().is_none()
    );
    let old_span = a.content_span().ok_or("numeric original span")?;
    let new_span = b.content_span().ok_or("numeric derived span")?;
    let mut reconstructed = old_bytes.clone();
    reconstructed.splice(
        old_span.start()..old_span.end(),
        next_bytes[new_span.start()..new_span.end()].iter().copied(),
    );
    assert!(
        reconstructed == *next_bytes,
        "outside_numeric_input_leaf_changed"
    );
    assert!(
        old_bytes[old_span.start()..old_span.end()] != next_bytes[new_span.start()..new_span.end()]
    );
    Ok(())
}
