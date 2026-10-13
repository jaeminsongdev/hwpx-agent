// In-memory derivatives of the original builder/review fixture. No captured source writes.
#[path = "document_import_review_assembly_fixture.rs"]
mod original;
use hwpx_package::{BoundedZipReader, PackageLimits, PreservingXmlDocument};
use std::{error::Error, io::{Cursor, Write}};
use zip::{CompressionMethod, ZipWriter, write::SimpleFileOptions};
pub fn style(id: u32) -> String {
    format!("<hh:memoPr id='{id}' width='55' lineWidth='1' lineType='SOLID' lineColor='#010203' fillColor='#CCFF99' activeColor='none' memoType='NOMAL' xmlns:x='urn:memo-private' x:opaque='PRIVATE-MEMO-STYLE'/>")
}
pub fn package(styles: &str, reference: Option<&str>) -> Result<Vec<u8>, Box<dyn Error>> {
    let base = original::package(&original::markers("PRIVATE-MEMO-BODY"))?;
    let mut reader = BoundedZipReader::open(Cursor::new(&base), PackageLimits::default())?;
    let names: Vec<_> = reader.entries().iter().map(|e|e.path.as_str().to_owned()).collect();
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    for (i,name) in names.into_iter().enumerate() {
        let old = reader.read_entry(i)?;
        let mut changed = old.clone();
        if name == "Contents/header.xml" && !styles.is_empty() {
            let xml = PreservingXmlDocument::parse(&old)?;
            let refs = xml.elements().iter().find(|e| e.name().local_name()=="refList").ok_or("refList")?;
            let at = refs.content_span().ok_or("refList content")?.end();
            let mut text = std::str::from_utf8(&old)?.to_owned();
            text.insert_str(at, styles);
            changed = text.into_bytes();
        } else if name == "Contents/section0.xml" {
            let text = std::str::from_utf8(&old)?;
            if text.matches("memoShapeIDRef=\"0\"").count()!=1 {return Err("exact original secPr reference".into());}
            changed = text.replacen("memoShapeIDRef=\"0\"", &reference.map_or_else(String::new, |v|format!("memoShapeIDRef='{v}'")),1).into_bytes();
        }
        if name!="Contents/header.xml" && name!="Contents/section0.xml" {assert_eq!(changed,old);}
        writer.start_file(name,SimpleFileOptions::default().compression_method(CompressionMethod::Stored))?;
        writer.write_all(&changed)?;
    }
    Ok(writer.finish()?.into_inner())
}
pub fn table(styles: &str, count: usize) -> String {
    format!("<hh:memoProperties itemCnt='{count}'>{styles}</hh:memoProperties>")
}
