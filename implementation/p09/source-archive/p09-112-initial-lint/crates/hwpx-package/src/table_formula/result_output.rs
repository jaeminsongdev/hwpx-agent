//! Existing original formula envelope/AST/cache decoder -> exact three result leaves.
use super::*;

pub(crate) struct ResultTargets {
    pub indices: [usize; 3],
    pub values: [String; 3],
}

pub(crate) fn targets(
    xml: &PreservingXmlDocument,
    begin: usize,
    value: FormulaDecimal,
) -> Result<ResultTargets, TableFormulaHwpxError> {
    // All original owner/grid/native syntax/cache parity guards execute before exposing targets.
    let _ = read_imported_field(xml, begin)?;
    let limits = TableFormulaHwpxLimits::default();
    let envelope = validate_field_envelope(xml, begin, limits)?;
    let params = read_field_parameters(xml, envelope.parameters, limits)?;
    let indices = child_indexes(xml, envelope.parameters)?;
    let text = canonical_cache_text(
        &FormulaCache::Unverified {
            value: FormulaValue::Decimal { value },
        },
        FormulaLimits::default(),
    )?;
    Ok(ResultTargets {
        indices: [indices[1], indices[4], envelope.visible_result],
        values: [
            format!(
                "{}??{NATIVE_GENERAL_FORMAT};;{text}",
                params.native_formula.text
            ),
            text.clone(),
            text,
        ],
    })
}
