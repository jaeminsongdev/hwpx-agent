use super::*;
use hwpx_package::{ElementSplicePosition as Position,PatchError};
fn section(result:&hwpx_package::PatchResult)->Result<Vec<u8>,Box<dyn Error>> {
    let artifact=PreservingWriter::build(result,PackageLimits::default(),PackageGraphLimits::default(),IdIndexLimits::default(),WriterLimits::default())?;
    artifact.with_verified_bytes(|bytes|->Result<Vec<u8>,Box<dyn Error>> {
        let mut reader=BoundedZipReader::open(Cursor::new(bytes),PackageLimits::default())?;
        let i=reader.entries().iter().position(|p|p.path.as_str()=="Contents/section0.xml").ok_or("part")?;Ok(reader.read_entry(i)?)
    })?
}
#[test]
fn splice_all_five_positions_keep_exact_unselected_source_bytes() -> TestResult {
    for position in [Position::Before,Position::After,Position::FirstChild,Position::LastChild,Position::Subtree] {
        let (mut reader,graph,path,xml,index)=opened()?;
        let i=reader.entries().iter().position(|e|e.path==path).ok_or("part")?;let old=reader.read_entry(i)?;
        let fragments=vec![child_id(9)?,child_id(10)?];let selected=&xml.elements()[index];
        let outer=selected.outer_span().ok_or("outer")?;let content=selected.content_span().ok_or("content")?;
        let (start,end)=match position {Position::Before=>(outer.start(),outer.start()),Position::After=>(outer.end(),outer.end()),Position::FirstChild=>(content.start(),content.start()),Position::LastChild=>(content.end(),content.end()),Position::Subtree=>(outer.start(),outer.end())};
        let intent=PatchIntent::SpliceElements {target:XmlElementSelector::bind(&path,&xml,index)?,position,fragments};assert!(!format!("{intent:?}").contains("NEW-PRIVATE"));
        let result=apply(&mut reader,&graph,&[intent],PatchLimits::default())?;let output=section(&result)?;
        assert_eq!(&old[..start],&output[..start]);let tail=old.len()-end;assert_eq!(&old[end..],&output[output.len()-tail..]);
        let output=String::from_utf8(output)?;assert_eq!(output.matches("NEW-PRIVATE").count(),2);assert!(output.contains("OUTSIDE"));
    }Ok(())
}
#[test]
fn splice_empty_parent_keeps_original_attributes_qname_and_namespace_alias() -> TestResult {
    let bytes=fixture::package("<hp:p id='1'><hp:run><a:ctrl xmlns:a='http://www.hancom.co.kr/hwpml/2011/paragraph' u:flag='KEEP' /></hp:run></hp:p>")?;
    for position in [Position::FirstChild,Position::LastChild] {
        let mut reader=BoundedZipReader::open(Cursor::new(bytes.clone()),PackageLimits::default())?;let graph=PackageGraph::build(&mut reader,PackageGraphLimits::default())?;
        let i=reader.entries().iter().position(|p|p.path.as_str()=="Contents/section0.xml").ok_or("part")?;let path=reader.entries()[i].path.clone();let xml=PreservingXmlDocument::parse(&reader.read_entry(i)?)?;
        let index=xml.elements().iter().position(|e|e.name().local_name()=="ctrl").ok_or("ctrl")?;
        let fragment=ValidatedXmlFragment::parse(b"<hp:newNum xmlns:hp='http://www.hancom.co.kr/hwpml/2011/paragraph' num='3' numType='PICTURE'/>",PatchLimits::default())?;
        let result=apply(&mut reader,&graph,&[PatchIntent::SpliceElements {target:XmlElementSelector::bind(&path,&xml,index)?,position,fragments:vec![fragment]}],PatchLimits::default())?;
        let output=String::from_utf8(section(&result)?)?;assert!(output.contains("<a:ctrl xmlns:a='http://www.hancom.co.kr/hwpml/2011/paragraph' u:flag='KEEP' >"));assert!(output.contains("</a:ctrl>"));
    }Ok(())
}
#[test]
fn splice_root_and_empty_forest_rules_do_not_bypass_original_guards() -> TestResult {
    for (position,fragments) in [(Position::Before,vec![child()?]),(Position::After,vec![child()?]),(Position::Subtree,vec![]),(Position::Subtree,vec![child_id(9)?,child_id(10)?])] {
        let (mut reader,graph,path,xml,_)=opened()?;let target=XmlElementSelector::bind(&path,&xml,xml.root_element())?;
        assert!(matches!(apply(&mut reader,&graph,&[PatchIntent::SpliceElements {target,position,fragments}],PatchLimits::default()),Err(PatchError::RootMutation)));
    }
    let (mut reader,graph,path,xml,index)=opened()?;
    assert!(matches!(apply(&mut reader,&graph,&[PatchIntent::SpliceElements {target:XmlElementSelector::bind(&path,&xml,index)?,position:Position::FirstChild,fragments:vec![]}],PatchLimits::default()),Err(PatchError::ValueInvalid)));
    let (mut reader,graph,path,xml,index)=opened()?;
    let result=apply(&mut reader,&graph,&[PatchIntent::SpliceElements {target:XmlElementSelector::bind(&path,&xml,index)?,position:Position::Subtree,fragments:vec![]}],PatchLimits::default())?;
    assert!(!String::from_utf8(section(&result)?)?.contains("subList"));Ok(())
}
#[test]
fn splice_fragment_count_and_aggregate_bytes_are_bounded_before_output() -> TestResult {
    for (config,label) in [(PatchLimitConfig {max_intents:1,..PatchLimitConfig::default()},"splice_fragments"),(PatchLimitConfig {max_fragment_bytes:150,..PatchLimitConfig::default()},"splice_fragment_bytes")] {
        let (mut reader,graph,path,xml,index)=opened()?;
        let intent=PatchIntent::SpliceElements {target:XmlElementSelector::bind(&path,&xml,index)?,position:Position::FirstChild,fragments:vec![child_id(9)?,child_id(10)?]};
        assert!(matches!(apply(&mut reader,&graph,&[intent],PatchLimits::new(config)?),Err(PatchError::LimitExceeded {limit}) if limit==label));
    }Ok(())
}
#[test]
fn splice_overlap_duplicate_ids_and_dangling_references_never_return_partial_result() -> TestResult {
    let (mut reader,graph,path,xml,index)=opened()?;let descendant=xml.elements()[index].first_child().ok_or("child")?;
    let intents=[PatchIntent::SpliceElements {target:XmlElementSelector::bind(&path,&xml,index)?,position:Position::Subtree,fragments:vec![child()?]},PatchIntent::DeleteSubtree {target:XmlElementSelector::bind(&path,&xml,descendant)?}];
    assert!(matches!(apply(&mut reader,&graph,&intents,PatchLimits::default()),Err(PatchError::Conflict)));
    for fragments in [vec![child_id(9)?,child_id(9)?],vec![ValidatedXmlFragment::parse(b"<hp:p xmlns:hp='http://www.hancom.co.kr/hwpml/2011/paragraph' id='9' styleIDRef='987'/>",PatchLimits::default())?]] {
        let (mut reader,graph,path,xml,index)=opened()?;assert!(apply(&mut reader,&graph,&[PatchIntent::SpliceElements {target:XmlElementSelector::bind(&path,&xml,index)?,position:Position::Subtree,fragments}],PatchLimits::default()).is_err());
    }Ok(())
}
#[test]
fn splice_foreign_selector_and_duplicate_zero_width_insertions_are_rejected() -> TestResult {
    let (mut reader,graph,path,xml,index)=opened()?;let target=XmlElementSelector::bind(&path,&xml,index)?;
    let (mut foreign,_,_,_,_)=opened()?;let i=foreign.entries().iter().position(|e|e.path.as_str()=="Contents/header.xml").ok_or("header")?;
    let other_path=foreign.entries()[i].path.clone();let other_xml=PreservingXmlDocument::parse(&foreign.read_entry(i)?)?;
    let stale=XmlElementSelector::bind(&path,&other_xml,other_xml.root_element())?;
    assert!(apply(&mut reader,&graph,&[PatchIntent::SpliceElements {target:stale,position:Position::FirstChild,fragments:vec![child()?]}],PatchLimits::default()).is_err());
    assert_ne!(other_path,path);
    let intents=[PatchIntent::SpliceElements {target:target.clone(),position:Position::FirstChild,fragments:vec![child_id(9)?]},PatchIntent::SpliceElements {target,position:Position::FirstChild,fragments:vec![child_id(10)?]}];
    assert!(matches!(apply(&mut reader,&graph,&intents,PatchLimits::default()),Err(PatchError::Conflict)));Ok(())
}
