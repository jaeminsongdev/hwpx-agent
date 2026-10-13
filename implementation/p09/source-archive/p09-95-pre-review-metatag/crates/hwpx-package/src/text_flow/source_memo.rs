//! Source-preserving MEMO body envelope only; author/time/visibility/resolution remain unknown.
use super::{
    PreservingXmlDocument, ReadState, TextFlowError, child_indexes, element, has_name,
    require_only_whitespace_content, validate_parameter_entries,
};

pub(super) fn validate_with_body(
    document: &PreservingXmlDocument,
    payload: &[usize],
    state: &mut ReadState,
) -> Result<(), TextFlowError> {
    let body = match payload {
        [body] if has_name(element(document, *body)?, "subList") => *body,
        [parameters, body]
            if has_name(element(document, *parameters)?, "parameters")
                && has_name(element(document, *body)?, "subList") =>
        {
            validate_parameter_entries(document, *parameters, state)?;
            *body
        }
        _ => return Err(TextFlowError::InvalidField),
    };
    require_only_whitespace_content(document, body)?;
    let paragraphs = child_indexes(document, body)?;
    if paragraphs.is_empty()
        || paragraphs
            .iter()
            .any(|p| !element(document, *p).is_ok_and(|e| has_name(e, "p")))
    {
        return Err(TextFlowError::InvalidField);
    }
    let span = element(document, body)?
        .outer_span()
        .ok_or(TextFlowError::InvalidField)?;
    state.count_text(span.len())?;
    // Preserve every byte, but do not silently accept nested review/field/note
    // semantics in this closed envelope. The typed body importer validates paragraphs.
    // Parser elements are in start-token order. Scan this contiguous subtree,
    // not the whole document again for every MEMO body.
    let last_token = element(document, body)?
        .end_token()
        .ok_or(TextFlowError::InvalidField)?;
    for e in document.elements()[body..]
        .iter()
        .take_while(|e| e.start_token() <= last_token)
    {
        if !e
            .outer_span()
            .is_some_and(|s| span.start() <= s.start() && s.end() <= span.end())
        {
            return Err(TextFlowError::InvalidField);
        }
        state.count_item()?;
        if [
            "fieldBegin",
            "fieldEnd",
            "hiddenComment",
            "footNote",
            "endNote",
        ]
        .iter()
        .any(|name| has_name(e, name))
        {
            return Err(TextFlowError::InvalidField);
        }
    }
    Ok(())
}
