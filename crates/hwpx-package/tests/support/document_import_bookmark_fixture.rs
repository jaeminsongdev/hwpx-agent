//! Generated whole packages only; these are not captured native bookmark inputs.
use super::base;
use std::{
    error::Error,
    io::{Cursor, Read, Write},
};
use zip::{CompressionMethod, ZipArchive, ZipWriter, write::SimpleFileOptions};

pub fn marker(name: &str) -> String {
    format!("<hp:ctrl><hp:bookmark name='{name}'/></hp:ctrl>")
}
pub fn paragraph(body: &str) -> String {
    format!("<hp:p id='1'><hp:run>{body}</hp:run></hp:p>")
}
pub fn field() -> &'static str {
    "<hp:ctrl><hp:fieldBegin id='7' type='DATE'/></hp:ctrl><hp:t>cache</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='7'/></hp:ctrl>"
}
pub fn note(body: &str) -> String {
    format!(
        "<hp:ctrl><hp:footNote instId='101'><hp:subList>{}</hp:subList></hp:footNote></hp:ctrl>",
        paragraph(body)
    )
}
pub fn generated() -> Result<Vec<Vec<u8>>, Box<dyn Error>> {
    let mut packages: Vec<_> = [
        paragraph(&marker("point")),
        paragraph(&format!(
            "<hp:t>before</hp:t>{}<hp:t>after</hp:t>",
            marker("한글&amp;자료")
        )),
        paragraph(&format!("{}{}", marker("same"), marker("same"))),
        paragraph(&format!("{}{}", marker("point"), field())),
        paragraph(&note(&format!("{}{}", marker("in-note"), field()))),
        paragraph(&table(&marker("in-table"))),
        paragraph(&note(&table(&marker("note-table")))),
    ]
    .iter()
    .map(|body| base::package(body))
    .collect::<Result<_, _>>()?;
    packages.push(two_sections()?);
    Ok(packages)
}

pub fn two_sections() -> Result<Vec<u8>, Box<dyn Error>> {
    let bytes = base::package(&paragraph(&marker("same-across-sections")))?;
    let mut source = ZipArchive::new(Cursor::new(&bytes))?;
    let mut target = ZipWriter::new(Cursor::new(Vec::new()));
    let mut second = None;
    for index in 0..source.len() {
        let mut entry = source.by_index(index)?;
        let name = entry.name().to_owned();
        let mut data = Vec::new();
        entry.read_to_end(&mut data)?;
        if name == "Contents/content.hpf" {
            data=String::from_utf8(data)?.replace("</o:manifest>","<o:item id='s1' href='Contents/section1.xml' media-type='application/xml'/></o:manifest>").replace("</o:spine>","<o:itemref idref='s1'/></o:spine>").into_bytes();
        }
        if name == "Contents/section0.xml" {
            second = Some(data.clone());
        }
        target.start_file(
            name,
            SimpleFileOptions::default().compression_method(CompressionMethod::Stored),
        )?;
        target.write_all(&data)?;
    }
    target.start_file(
        "Contents/section1.xml",
        SimpleFileOptions::default().compression_method(CompressionMethod::Stored),
    )?;
    target.write_all(&second.ok_or("section")?)?;
    Ok(target.finish()?.into_inner())
}

pub fn table(body: &str) -> String {
    format!(
        r#"<hp:tbl id="9" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="CELL" repeatHeader="0" rowCnt="1" colCnt="1" cellSpacing="0" borderFillIDRef="1" noAdjust="0"><hp:sz width="2000" widthRelTo="ABSOLUTE" height="1000" heightRelTo="ABSOLUTE" protect="0"/><hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" horzAlign="LEFT" vertOffset="0" horzOffset="0"/><hp:outMargin left="0" right="0" top="0" bottom="0"/><hp:inMargin left="510" right="511" top="141" bottom="142"/><hp:tr><hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="0" borderFillIDRef="1"><hp:cellAddr colAddr="0" rowAddr="0"/><hp:cellSpan colSpan="1" rowSpan="1"/><hp:cellSz width="2000" height="1000"/><hp:cellMargin left="0" right="0" top="0" bottom="0"/><hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">{}</hp:subList></hp:tc></hp:tr></hp:tbl>"#,
        paragraph(body)
    )
}
