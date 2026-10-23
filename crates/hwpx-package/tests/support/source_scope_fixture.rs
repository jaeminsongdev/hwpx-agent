//! Two immutable in-memory source sections with repeated local paragraph IDs.
#[allow(dead_code)] #[path="document_import_field_fixture.rs"] mod source;
use hwpx_package::BoundedZipReader;
use std::{error::Error,io::{Cursor,Write}};
use zip::{ZipWriter,CompressionMethod,write::SimpleFileOptions};
pub fn package()->Result<Vec<u8>,Box<dyn Error>> {
    let raw=source::package("<hp:p id='1'><hp:run><hp:t>xxPRIVATE-sameyy same</hp:t></hp:run></hp:p>")?;
    let mut reader=BoundedZipReader::open(Cursor::new(&raw),Default::default())?;
    let names:Vec<_>=reader.entries().iter().map(|e|e.path.as_str().to_owned()).collect();let mut writer=ZipWriter::new(Cursor::new(Vec::new()));
    for (i,name) in names.iter().enumerate(){let bytes=reader.read_entry(i)?;writer.start_file(name,SimpleFileOptions::default().compression_method(CompressionMethod::Stored))?;
        if name=="Contents/content.hpf"{let text=String::from_utf8(bytes)?.replace("</o:manifest>","<o:item id='s2' href='Contents/section1.xml' media-type='application/xml'/></o:manifest>")
            .replace("</o:spine>","<o:itemref idref='s2'/></o:spine>");writer.write_all(text.as_bytes())?;}else{writer.write_all(&bytes)?;}}
    writer.start_file("Contents/section1.xml",SimpleFileOptions::default().compression_method(CompressionMethod::Stored))?;
    writer.write_all(b"<hs:sec xmlns:hs='http://www.hancom.co.kr/hwpml/2011/section' xmlns:hp='http://www.hancom.co.kr/hwpml/2011/paragraph'><hp:p id='1'><hp:run><hp:t>same same same</hp:t></hp:run></hp:p></hs:sec>")?;
    Ok(writer.finish()?.into_inner())
}
