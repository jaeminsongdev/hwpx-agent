use super::*;
type Result<T=()>=std::result::Result<T,Box<dyn std::error::Error>>;
fn full(document:&PreservingXmlDocument,index:usize,plain:bool)->bool{
    document.tokens().iter().any(|t|t.element_index()==Some(index)&&if plain{
        !matches!(t.kind(),XmlTokenKind::StartElement|XmlTokenKind::EmptyElement|XmlTokenKind::EndElement|XmlTokenKind::Text|XmlTokenKind::Whitespace|XmlTokenKind::Reference)
    }else{matches!(t.kind(),XmlTokenKind::ByteOrderMark|XmlTokenKind::Declaration|XmlTokenKind::Text|XmlTokenKind::Reference|XmlTokenKind::Comment)})
}
#[test]
fn indexed_guards_equal_original_full_scan_for_every_admitted_element()->Result{
    for xml in ["<root/>","<?xml version='1.0'?><root> \n<a>text&amp;&#65;</a><b><!--private--><c/> </b></root>",
        "<r xmlns:p='urn:p'><p:a x='1'>A</p:a><p:a/><p:a>\t\n</p:a></r>","<r><a><a><!--x-->value</a>tail</a></r>"]{
        let document=PreservingXmlDocument::parse(xml.as_bytes())?;
        for i in 0..document.elements().len(){
            assert_eq!(require_plain_text_tokens(&document,i).is_err(),full(&document,i,true));
            assert_eq!(require_container_whitespace(&document,i).is_err(),full(&document,i,false));
        }
    }Ok(())
}
#[test]
fn windows_include_empty_start_and_complete_end_tokens_and_reject_missing_index()->Result{
    let document=PreservingXmlDocument::parse(b"<r><a/><b>text&amp;value</b></r>")?;
    for(i,e)in document.elements().iter().enumerate(){let tokens=element_tokens(&document,i)?;
        assert_eq!(tokens.first(),document.tokens().get(e.start_token()));
        assert_eq!(tokens.last(),e.end_token().and_then(|n|document.tokens().get(n)));}
    assert_eq!(element_tokens(&document,usize::MAX),Err(HyperlinkHwpxError::UnsupportedStructure));Ok(())
}
#[test]
fn unrelated_siblings_do_not_increase_parameter_window_work()->Result{
    let mut xml=String::from("<r>");for _ in 0..256{xml.push_str("<p><s>A&amp;B</s><s>C</s></p>");}xml.push_str("</r>");
    let document=PreservingXmlDocument::parse(xml.as_bytes())?;let mut visits=0usize;let mut checks=0usize;
    for(i,e)in document.elements().iter().enumerate().filter(|(_,e)|e.name().local_name()=="s"){
        visits+=element_tokens(&document,i)?.len();checks+=1;
        assert_eq!(require_plain_text_tokens(&document,i).is_err(),full(&document,i,true));assert!(e.first_child().is_none());}
    assert_eq!(checks,512);assert!(visits<=checks*5);assert!(visits*100<document.tokens().len()*checks);Ok(())
}
