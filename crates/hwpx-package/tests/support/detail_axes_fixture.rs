//! Merge the two already validated detail declaration fixtures, preserving every other header subtree.
#[allow(dead_code)] #[path="character_detail_fixture.rs"] pub mod characters;
#[allow(dead_code)] #[path="paragraph_detail_fixture.rs"] pub mod paragraphs;
use hwpx_package::PreservingXmlDocument;
use std::error::Error;
pub fn package(body:&str)->Result<Vec<u8>,Box<dyn Error>> {
    fn range(text:&str)->Result<std::ops::Range<usize>,Box<dyn Error>> {
        let xml=PreservingXmlDocument::parse(text.as_bytes())?;
        let node=xml.elements().iter().find(|node|node.name().local_name()=="charProperties").ok_or("character catalog")?;
        Ok(xml.tokens()[node.start_token()].span().start()..xml.tokens()[node.end_token().ok_or("character end")?].span().end())
    }
    let character_header=characters::header()?;let mut paragraph_header=paragraphs::header()?;
    let source=range(&character_header)?;let target=range(&paragraph_header)?;paragraph_header.replace_range(target,&character_header[source]);
    paragraphs::definition::package_with_header(body,&paragraph_header)
}
pub fn p(id:u32,text:&str)->String {paragraphs::p(id,text)}
