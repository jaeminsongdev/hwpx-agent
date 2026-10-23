//! In-memory whole-package derivatives; no captured original or filesystem writes.
#[allow(dead_code)]
#[path="search_definition_fixture.rs"]mod definition;
use hwpx_package::{BoundedZipReader,PackageLimits};
use std::{collections::BTreeMap,error::Error,io::{Cursor,Write}};
use zip::{CompressionMethod,ZipWriter,write::SimpleFileOptions};
type Result<T>=std::result::Result<T,Box<dyn Error>>;
pub fn package(body:&str)->Result<Vec<u8>>{definition::package(body)}
fn parts(bytes:&[u8])->Result<BTreeMap<String,Vec<u8>>>{
    let mut reader=BoundedZipReader::open(Cursor::new(bytes),PackageLimits::default())?;let mut parts=BTreeMap::new();
    for i in 0..reader.entries().len(){let name=reader.entries()[i].path.as_str().to_owned();parts.insert(name,reader.read_entry(i)?);}Ok(parts)
}
fn pack(parts:BTreeMap<String,Vec<u8>>)->Result<Vec<u8>>{
    let mut writer=ZipWriter::new(Cursor::new(Vec::new()));let first=parts.get_key_value("mimetype").ok_or("mimetype")?;
    for(name,bytes)in std::iter::once(first).chain(parts.iter().filter(|(name,_)|name.as_str()!="mimetype")){
        writer.start_file(name,SimpleFileOptions::default().compression_method(CompressionMethod::Stored))?;writer.write_all(bytes)?;
    }Ok(writer.finish()?.into_inner())
}
pub fn header_xml(bytes:&[u8],addition:&str)->Result<Vec<u8>>{
    let mut parts=parts(bytes)?;let text=std::str::from_utf8(parts.get("Contents/header.xml").ok_or("header")?)?;
    let end=text.rfind("</").ok_or("header end")?;let mut changed=text.to_owned();changed.insert_str(end,addition);
    parts.insert("Contents/header.xml".into(),changed.into_bytes());pack(parts)
}
pub fn header_signal(bytes:&[u8],name:&str,value:&str)->Result<Vec<u8>>{
    header_xml(bytes,&format!("<hh:probe {name}='{value}'/>"))
}
pub fn add_xml(bytes:&[u8],path:&str,xml:&str)->Result<Vec<u8>>{
    let mut parts=parts(bytes)?;if parts.contains_key(path){return Err("duplicate fixture part".into());}
    let opf=std::str::from_utf8(parts.get("Contents/content.hpf").ok_or("opf")?)?;
    let entry=format!("<o:item id='security-extra-{}' href='{path}' media-type='application/xml'/></o:manifest>",parts.len());
    if opf.matches("</o:manifest>").count()!=1{return Err("one manifest end".into());}
    let changed=opf.replace("</o:manifest>",&entry);parts.insert("Contents/content.hpf".into(),changed.into_bytes());
    parts.insert(path.into(),xml.as_bytes().to_vec());pack(parts)
}
