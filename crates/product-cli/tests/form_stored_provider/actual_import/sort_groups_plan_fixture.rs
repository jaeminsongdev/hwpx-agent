//! Shared in-memory two-part specimen for the new compiler and synthetic manifest checks.
use super::*;
use std::io::Write as _;
pub fn two_parts(first:&str,second:&str)->Result<Vec<u8>,Box<dyn Error>>{
    use zip::{ZipWriter,CompressionMethod,write::SimpleFileOptions};
    let raw=definition::package(first)?;let mut reader=hwpx_package::BoundedZipReader::open(Cursor::new(&raw),Default::default())?;
    let names:Vec<_>=reader.entries().iter().map(|e|e.path.as_str().to_owned()).collect();let mut writer=ZipWriter::new(Cursor::new(Vec::new()));
    for(i,name)in names.iter().enumerate(){let data=reader.read_entry(i)?;writer.start_file(name,SimpleFileOptions::default().compression_method(CompressionMethod::Stored))?;
        if name=="Contents/content.hpf"{let text=String::from_utf8(data)?.replace("</o:manifest>","<o:item id='s2' href='Contents/section1.xml' media-type='application/xml'/></o:manifest>")
            .replace("</o:spine>","<o:itemref idref='s2'/></o:spine>");writer.write_all(text.as_bytes())?;}else{writer.write_all(&data)?;}}
    writer.start_file("Contents/section1.xml",SimpleFileOptions::default().compression_method(CompressionMethod::Stored))?;
    writer.write_all(format!("<hs:sec xmlns:hs='http://www.hancom.co.kr/hwpml/2011/section' xmlns:hp='http://www.hancom.co.kr/hwpml/2011/paragraph'>{second}</hs:sec>").as_bytes())?;
    Ok(writer.finish()?.into_inner())
}
pub fn source()->Result<Vec<u8>,Box<dyn Error>>{two_parts(&(para(1,"Z-PRIVATE")+&para(2,"B")+&para(3,"A")),&(para(1,"Y")+&para(2,"C")+&para(3,"B")))}
pub fn request(s:&StoredFixture,bytes:&[u8])->Result<Value,Box<dyn Error>>{
    let mut v=envelope(s,bytes)?;v["schema_version"]=json!(hwpx_agent_cli::form_product_request::stored_literal_replacement::sort_groups::PARAGRAPH_SORT_GROUPS_PRODUCT_REQUEST_SCHEMA);
    v["operation"]=json!({"kind":"sort_paragraph_groups","sort_spec":{"direction":"ascending","comparison":"nfc_unicode_scalar_lexicographic","max_comparison_bytes":1048576},"review_policy":policy(false,false)});Ok(v)
}
