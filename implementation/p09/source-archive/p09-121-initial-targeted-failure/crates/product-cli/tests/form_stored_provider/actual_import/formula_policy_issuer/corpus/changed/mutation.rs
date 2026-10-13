//! Independent one-leaf expanded package reconstruction; originals never written or values printed.
use super::super::super::super::formula_evaluation::fixture as source;
use super::*;
use hwpx_package::PreservingXmlDocument;
const HP: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";

pub(super) fn numeric_derivative(original: &[u8]) -> AnyResult<Vec<u8>> {
    let changed = source::mutate_first_cell(original, |cell| {
        let begin = cell.find("<hp:t>").ok_or("numeric leaf start")? + "<hp:t>".len();
        let end = begin + cell[begin..].find("</hp:t>").ok_or("numeric leaf end")?;
        let number = cell[begin..end].parse::<i64>()?;
        let next = number
            .checked_add(101)
            .ok_or("numeric derivative overflow")?
            .to_string();
        source::replace_first_text(cell, &next)
    })?;
    verify_one_leaf(original, &changed)?;
    Ok(changed)
}

fn verify_one_leaf(original: &[u8], changed: &[u8]) -> TestResult {
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
    let cell = xml
        .elements()
        .iter()
        .find(|e| e.name().namespace() == Some(HP) && e.name().local_name() == "tc")
        .ok_or("first numeric cell")?;
    let cell_span = cell.outer_span().ok_or("numeric cell span")?;
    let index = xml
        .elements()
        .iter()
        .position(|e| {
            e.name().namespace() == Some(HP)
                && e.name().local_name() == "t"
                && e.outer_span()
                    .is_some_and(|s| s.start() >= cell_span.start() && s.end() <= cell_span.end())
        })
        .ok_or("first numeric text")?;
    let a = &xml.elements()[index];
    let b = &newer.elements()[index];
    assert!(
        a.name() == b.name()
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
