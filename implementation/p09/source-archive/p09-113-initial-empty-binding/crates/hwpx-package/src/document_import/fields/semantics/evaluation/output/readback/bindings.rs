//! Anchor hashes identify one version only: correlate values by exact source field positions.
use super::{Error, ImportedSourceFormulaEvaluation};
use crate::document_import::{
    ImportedSourcePackage, fields::semantics::ImportedDocumentFieldSemantics,
};
use domain_ir::SourceAnchorHandle;

pub(super) fn verify(
    original: &ImportedSourceFormulaEvaluation<'_, '_, '_>,
    meanings: &ImportedDocumentFieldSemantics<'_, '_>,
    evaluated: &ImportedSourceFormulaEvaluation<'_, '_, '_>,
) -> Result<(), Error> {
    let before = original.meanings.fields.forms.source();
    let after = meanings.fields.forms.source();
    let old_fields = original.meanings.fields.fields();
    let new_fields = meanings.fields.fields();
    if old_fields.len() != new_fields.len() {
        return Err(Error::Readback);
    }
    // Field import independently sorts actual spine and XML element positions.
    // Each pair must prove the same source range, not merely share a coordinate/value.
    for (old, new) in old_fields.iter().zip(new_fields) {
        if old.native_kind != new.native_kind
            || old.native_begin_id != new.native_begin_id
            || old.native_header_attributes != new.native_header_attributes
            || old.native_end_attributes != new.native_end_attributes
            || old.inline_start != new.inline_start
            || old.inline_end != new.inline_end
        {
            return Err(Error::Readback);
        }
        same_position(before, &old.begin_anchor, after, &new.begin_anchor)?;
        same_position(before, &old.end_anchor, after, &new.end_anchor)?;
        match (&old.parameter_anchor, &new.parameter_anchor) {
            (Some(old), Some(new)) => same_position(before, old, after, new)?,
            (None, None) => (),
            _ => return Err(Error::Readback),
        }
        let old_value = original
            .values
            .iter()
            .find(|v| v.reference_id == old.reference_id);
        let new_value = evaluated
            .values
            .iter()
            .find(|v| v.reference_id == new.reference_id);
        match (old_value, new_value) {
            (Some(old), Some(new))
                if old.value == new.value && old.coordinate == new.coordinate =>
            {
                same_position(before, &old.begin_anchor, after, &new.begin_anchor)?;
            }
            (None, None) => (),
            _ => return Err(Error::Readback),
        }
    }
    Ok(())
}
fn same_position(
    before: &ImportedSourcePackage,
    old: &SourceAnchorHandle,
    after: &ImportedSourcePackage,
    new: &SourceAnchorHandle,
) -> Result<(), Error> {
    let old = before.resolve_anchor(old).map_err(|_| Error::Readback)?;
    let new = after.resolve_anchor(new).map_err(|_| Error::Readback)?;
    if old.part().path() != new.part().path()
        || old.element_index().is_none()
        || old.element_index() != new.element_index()
    {
        return Err(Error::Readback);
    }
    Ok(())
}
