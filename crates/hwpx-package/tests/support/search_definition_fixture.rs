//! Whole in-memory packages using the repository's existing typed header specimen.
#[allow(dead_code)]
#[path="document_import_field_fixture.rs"] mod source;
#[allow(dead_code)]
#[path="document_import_catalog_fixture.rs"] mod archive;
use hwpx_package::PreservingXmlDocument;
use std::error::Error;
pub const HEADER:&str=include_str!("../../src/hancom_2020_minimal_header.xml");
pub fn header()->Result<String,Box<dyn Error>> {
    let xml=PreservingXmlDocument::parse(HEADER.as_bytes())?;let mut edits=Vec::new();
    for node in xml.elements() {
        let id=node.attributes().iter().find(|a|a.name().local_name()=="id").map(|a|&HEADER[a.value_span().start()..a.value_span().end()]);
        if node.name().local_name()=="charPr"&&id==Some("1") {
            let mut child=node.first_child();let mut offset=xml.tokens()[node.end_token().ok_or("char end")?].span().start();
            while let Some(i)=child {let element=&xml.elements()[i];child=element.next_sibling();
                if !matches!(element.name().local_name(),"fontRef"|"ratio"|"spacing"|"relSz"|"offset") {
                    offset=xml.tokens()[element.start_token()].span().start();break;
                }
            }
            edits.push((offset..offset,"<hh:italic/><hh:bold/>".to_owned()));
        }
        if node.name().local_name()=="align"&&node.parent().is_some_and(|p| {
            let parent=&xml.elements()[p];parent.name().local_name()=="paraPr"&&parent.attributes().iter().any(|a|
                a.name().local_name()=="id"&&&HEADER[a.value_span().start()..a.value_span().end()]=="1")
        }) {
            let attribute=node.attributes().iter().find(|a|a.name().local_name()=="horizontal").ok_or("alignment")?;
            edits.push((attribute.value_span().start()..attribute.value_span().end(),"RIGHT".to_owned()));
        }
    }
    if edits.len()!=2{return Err("two fixture edits required".into());}
    edits.sort_by_key(|(range,_)|std::cmp::Reverse(range.start));let mut result=HEADER.to_owned();
    for (range,value) in edits {result.replace_range(range,&value);}Ok(result)
}
pub fn package(body:&str)->Result<Vec<u8>,Box<dyn Error>> {package_with_header(body,&header()?)}
pub fn package_with_header(body:&str,header:&str)->Result<Vec<u8>,Box<dyn Error>> {
    archive::mutate_part(&source::package(body)?,"Contents/header.xml",|_|Ok(header.to_owned()))
}
