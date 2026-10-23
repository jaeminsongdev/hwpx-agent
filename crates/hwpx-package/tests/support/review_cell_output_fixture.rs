//! Synthetic derivative of the original review/table envelope and native package builder.
use super::assembly;
use domain_ir::SourceAnchorHandle;
use hwpx_package::{
    TextFlow, TextFlowLimits, TextFlowReader, document_import::forms::ImportedDocumentForms,
};
use std::{error::Error, fmt::Write as _};

pub fn paragraph(id: u32, text: &str) -> String {
    format!(
        "<hp:p id='{id}' styleIDRef='0' paraPrIDRef='0'><hp:run charPrIDRef='0'><hp:t>{text}</hp:t></hp:run></hp:p>"
    )
}
pub fn target() -> Result<TextFlow, Box<dyn Error>> {
    Ok(TextFlowReader::read("<hp:p xmlns:hp='http://www.hancom.co.kr/hwpml/2011/paragraph' id='901' styleIDRef='0' paraPrIDRef='0'><hp:run charPrIDRef='0'><hp:t>NEW-PRIVATE &amp; 한글<hp:tab width='8000' leader='0' type='0'/><hp:lineBreak/>끝</hp:t></hp:run><hp:run charPrIDRef='0'><hp:t>SECOND RUN</hp:t></hp:run></hp:p>".as_bytes(), TextFlowLimits::default())?)
}
pub fn cell_body(text: &str) -> String {
    format!(
        "<hp:subList id='' textDirection='HORIZONTAL' lineWrap='BREAK' vertAlign='CENTER' linkListIDRef='0' linkListNextIDRef='0' textWidth='0' textHeight='0' hasTextRef='0' hasNumRef='0'>{}</hp:subList>",
        paragraph(0, text)
    )
}
pub fn table(id: u32) -> String {
    let mut cells = String::new();
    for column in 0..2 {
        // fmt::Write for String always succeeds; no input-dependent fallible sink.
        let _ = write!(
            cells,
            "<hp:tc name='' header='0' hasMargin='0' protect='0' editable='0' dirty='0' borderFillIDRef='1'><hp:cellAddr colAddr='{column}' rowAddr='0'/><hp:cellSpan colSpan='1' rowSpan='1'/><hp:cellSz width='2000' height='1000'/><hp:cellMargin left='0' right='0' top='0' bottom='0'/>{}</hp:tc>",
            cell_body(if column == 0 {
                "CELL-OLD"
            } else {
                "OTHER-CELL"
            })
        );
    }
    format!(
        "<hp:tbl id='{id}' zOrder='0' numberingType='TABLE' textWrap='TOP_AND_BOTTOM' textFlow='BOTH_SIDES' lock='0' dropcapstyle='None' pageBreak='CELL' repeatHeader='0' rowCnt='1' colCnt='2' cellSpacing='0' borderFillIDRef='1' noAdjust='0'><hp:sz width='4000' widthRelTo='ABSOLUTE' height='1000' heightRelTo='ABSOLUTE' protect='0'/><hp:pos treatAsChar='1' affectLSpacing='0' flowWithText='1' allowOverlap='0' holdAnchorAndSO='0' vertRelTo='PARA' horzRelTo='COLUMN' vertAlign='TOP' horzAlign='LEFT' vertOffset='0' horzOffset='0'/><hp:outMargin left='0' right='0' top='0' bottom='0'/><hp:inMargin left='0' right='0' top='0' bottom='0'/><hp:tr>{cells}</hp:tr></hp:tbl>"
    )
}
pub fn package() -> Result<Vec<u8>, Box<dyn Error>> {
    package_variant(|markers| markers)
}
pub fn package_variant(change: impl FnOnce(String) -> String) -> Result<Vec<u8>, Box<dyn Error>> {
    let markers = assembly::markers("OLD").replacen("<hp:t>OLD</hp:t>", &format!("<hp:t>BEFORE</hp:t>{}<u:future xmlns:u='urn:future' private='RETAIN-OPAQUE'/><hp:t>AFTER</hp:t>",table(300)), 1)
        .replacen("<hp:t>HIDDEN-REVIEW</hp:t>", &format!("<hp:t>HIDDEN</hp:t>{}",table(301)), 1);
    assembly::package(&change(markers))
}
pub fn cells(forms: &ImportedDocumentForms) -> Result<Vec<SourceAnchorHandle>, Box<dyn Error>> {
    let part = forms
        .source()
        .parts()
        .iter()
        .find(|p| p.path().as_str() == "Contents/section0.xml")
        .ok_or("part")?;
    let xml = part.xml().ok_or("xml")?;
    xml.elements()
        .iter()
        .enumerate()
        .filter(|(_, e)| {
            e.name().namespace() == Some("http://www.hancom.co.kr/hwpml/2011/paragraph")
                && e.name().local_name() == "tc"
        })
        .map(|(i, _)| part.element_anchor(i).cloned().ok_or_else(|| "cell".into()))
        .collect()
}
