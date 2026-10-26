//! Native670 Prop2 block fieldid is an exact paired scalar. Legacy profiles
//! never call this validator. Begin IDs remain ordinary unique identifiers.
use super::{
    HWPML_2011_PARAGRAPH_NAMESPACE as HP, IdIndexError as Error, IdIndexLimits,
    PreservingXmlDocument,
};
use crate::XmlElementToken;
use std::collections::{BTreeMap, BTreeSet};
fn fail() -> Error {
    Error::BlockBookmarkProfileRejected
}
fn named(e: &XmlElementToken, name: &str) -> bool {
    e.name().namespace() == Some(HP) && e.name().local_name() == name
}
fn attr<'a>(e: &'a XmlElementToken, key: &str) -> Result<(usize, &'a str), Error> {
    let mut rows = e
        .attributes()
        .iter()
        .enumerate()
        .filter(|(_, a)| a.name().namespace().is_none() && a.name().local_name() == key);
    let (index, row) = rows.next().ok_or_else(fail)?;
    if rows.next().is_some() {
        return Err(fail());
    }
    Ok((index, row.semantic_value()))
}
fn number(e: &XmlElementToken, key: &str, limits: IdIndexLimits) -> Result<(usize, u32), Error> {
    let (index, text) = attr(e, key)?;
    if text.len() > limits.config().max_value_bytes
        || text.is_empty()
        || !text.bytes().all(|b| b.is_ascii_digit())
    {
        return Err(fail());
    }
    let value = text.parse().map_err(|_| fail())?;
    Ok((index, value))
}
fn paragraph(xml: &PreservingXmlDocument, index: usize) -> Result<usize, Error> {
    let marker = &xml.elements()[index];
    let ctrl = marker.parent().ok_or_else(fail)?;
    let wrapper = &xml.elements()[ctrl];
    if !named(wrapper, "ctrl")
        || wrapper.first_child() != Some(index)
        || marker.next_sibling().is_some()
    {
        return Err(fail());
    }
    let run = wrapper.parent().ok_or_else(fail)?;
    if !named(&xml.elements()[run], "run") {
        return Err(fail());
    }
    let p = xml.elements()[run].parent().ok_or_else(fail)?;
    if !named(&xml.elements()[p], "p") {
        return Err(fail());
    }
    Ok(p)
}
pub(super) fn validated_scalars(
    xml: &PreservingXmlDocument,
    limits: IdIndexLimits,
) -> Result<BTreeSet<(usize, usize)>, Error> {
    let mut beginnings = BTreeMap::new();
    let mut scalars = BTreeSet::new();
    for (index, begin) in xml.elements().iter().enumerate() {
        if !named(begin, "fieldBegin") || !attr(begin, "type").is_ok_and(|(_, v)| v == "BOOKMARK") {
            continue;
        }
        if beginnings.len() >= limits.config().max_declarations {
            return Err(Error::LimitExceeded {
                limit: "block_bookmark_scalars",
            });
        }
        let (_, id) = number(begin, "id", limits)?;
        let (field_attribute, field) = number(begin, "fieldid", limits)?;
        let p = paragraph(xml, index)?;
        if attr(begin, "name")?.1.is_empty() {
            return Err(fail());
        }
        let parameters = xml
            .elements()
            .get(begin.first_child().ok_or_else(fail)?)
            .ok_or_else(fail)?;
        if !named(parameters, "parameters")
            || parameters.next_sibling().is_some()
            || attr(parameters, "cnt")?.1 != "1"
            || attr(parameters, "name")?.1 != ""
        {
            return Err(fail());
        }
        let prop = xml
            .elements()
            .get(parameters.first_child().ok_or_else(fail)?)
            .ok_or_else(fail)?;
        if !named(prop, "integerParam")
            || prop.next_sibling().is_some()
            || prop.first_child().is_some()
            || attr(prop, "name")?.1 != "Prop"
            || xml
                .source_text(prop.content_span().ok_or_else(fail)?)
                .map_err(|_| fail())?
                != "2"
        {
            return Err(fail());
        }
        if beginnings.insert(id, (field, p, index, false)).is_some() {
            return Err(fail());
        }
        scalars.insert((index, field_attribute));
    }
    for (index, end) in xml.elements().iter().enumerate() {
        if !named(end, "fieldEnd") {
            continue;
        }
        let (_, id) = number(end, "beginIDRef", limits)?;
        if let Some((field, p, begin, closed)) = beginnings.get_mut(&id) {
            let (attribute, value) = number(end, "fieldid", limits)?;
            if *closed
                || index <= *begin
                || value != *field
                || paragraph(xml, index)? != *p
                || end.first_child().is_some()
            {
                return Err(fail());
            }
            *closed = true;
            scalars.insert((index, attribute));
        }
    }
    if beginnings.values().any(|v| !v.3) {
        return Err(fail());
    }
    Ok(scalars)
}
