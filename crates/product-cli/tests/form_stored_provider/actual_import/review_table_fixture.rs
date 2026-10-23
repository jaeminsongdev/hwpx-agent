//! Test-only derivative: original native builder and one shared assembly fixture.
//! No captured document, author, scope or native acceptance is fabricated.
use super::super::source_review_assembly::fixture as assembly;
#[path = "../../../../hwpx-package/tests/table_create_hwpx.rs"]
mod native;
use domain_ir::SourceAnchorHandle;
use hwpx_package::{
    BoundedZipReader, PackageLimits, document_import::forms::ImportedDocumentForms,
};
use std::io::Cursor;
type FixtureResult<T> = Result<T, Box<dyn std::error::Error>>;

pub(super) fn source() -> FixtureResult<Vec<u8>> {
    let markers = assembly::markers("").replace("<hp:t>HIDDEN-REVIEW</hp:t>", "<hp:t/>");
    let section = format!(
        "<hs:sec xmlns:hs='http://www.hancom.co.kr/hwpml/2011/section' xmlns:hp='http://www.hancom.co.kr/hwpml/2011/paragraph'><hp:p id='10' paraPrIDRef='0' styleIDRef='0'><hp:run charPrIDRef='0'>{markers}</hp:run></hp:p>{}</hs:sec>",
        native::empty_paragraph(11)
    );
    native::package(
        &native::header()?,
        section.as_bytes(),
        b"OPAQUE-SOURCE-PRIVATE",
    )
}
pub(super) fn template(nonempty: bool) -> FixtureResult<Vec<u8>> {
    native::package(
        &native::header()?,
        &native::template_section(nonempty),
        b"OPAQUE-TEMPLATE-PRIVATE",
    )
}
pub(super) fn anchor(
    forms: &ImportedDocumentForms,
    bytes: &[u8],
    local: &str,
    id: &str,
) -> FixtureResult<SourceAnchorHandle> {
    forms.source().verify_source(bytes)?;
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let entry = reader
        .entries()
        .iter()
        .find(|e| e.path.as_str() == "Contents/section0.xml")
        .ok_or("entry")?
        .index;
    let raw = reader.read_entry(entry)?;
    let part = forms
        .source()
        .parts()
        .iter()
        .find(|p| p.path().as_str() == "Contents/section0.xml")
        .ok_or("section")?;
    let xml = part.xml().ok_or("xml")?;
    let (index, _) = xml
        .elements()
        .iter()
        .enumerate()
        .find(|(_, e)| {
            e.name().namespace() == Some("http://www.hancom.co.kr/hwpml/2011/paragraph")
                && e.name().local_name() == local
                && e.attributes().iter().any(|a| {
                    a.name().namespace().is_none()
                        && a.name().local_name() == "id"
                        && raw[a.value_span().start()..a.value_span().end()] == *id.as_bytes()
                })
        })
        .ok_or("anchor")?;
    Ok(part.element_anchor(index).ok_or("identity")?.clone())
}
