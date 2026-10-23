//! Synthetic derivatives reuse the original review/native-builder and rich-cell fixtures.
use super::rich;
use domain_ir::SourceAnchorHandle;
use hwpx_package::{
    BoundedZipReader, PackageLimits, TextFlow, document_import::forms::ImportedDocumentForms,
};
use std::{error::Error, io::Cursor};

pub fn package() -> Result<Vec<u8>, Box<dyn Error>> {
    rich::package_variant(|s| {
        s.replacen(
            "</hp:p></hp:subList></hp:fieldBegin>",
            &format!(
                "</hp:p>{}</hp:subList></hp:fieldBegin>",
                rich::paragraph(700, "PLAIN-MEMO-PRIVATE")
            ),
            1,
        )
        .replacen(
            "</hp:p></hp:subList></hp:hiddenComment>",
            &format!(
                "</hp:p>{}</hp:subList></hp:hiddenComment>",
                rich::paragraph(701, "PLAIN-HIDDEN-PRIVATE")
            ),
            1,
        )
    })
}
pub fn target() -> Result<TextFlow, Box<dyn Error>> {
    rich::target()
}
pub fn anchor(
    forms: &ImportedDocumentForms,
    bytes: &[u8],
    id: u32,
) -> Result<SourceAnchorHandle, Box<dyn Error>> {
    forms.source().verify_source(bytes)?;
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let entry = reader
        .entries()
        .iter()
        .position(|e| e.path.as_str() == "Contents/section0.xml")
        .ok_or("entry")?;
    let raw = reader.read_entry(entry)?;
    let part = forms
        .source()
        .parts()
        .iter()
        .find(|p| p.path().as_str() == "Contents/section0.xml")
        .ok_or("part")?;
    let xml = part.xml().ok_or("xml")?;
    let (index, _) = xml
        .elements()
        .iter()
        .enumerate()
        .find(|(_, e)| {
            e.name().namespace() == Some("http://www.hancom.co.kr/hwpml/2011/paragraph")
                && e.name().local_name() == "p"
                && e.attributes().iter().any(|a| {
                    a.name().namespace().is_none()
                        && a.name().local_name() == "id"
                        && raw[a.value_span().start()..a.value_span().end()]
                            == *id.to_string().as_bytes()
                })
        })
        .ok_or("fixture paragraph")?;
    Ok(part.element_anchor(index).ok_or("anchor")?.clone())
}
