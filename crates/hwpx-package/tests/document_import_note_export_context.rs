//! Source XML context survives detachment; native container geometry is not inferred.
use hwpx_package::{BoundedZipReader,NoteHwpxLimits,NoteHwpxLimitConfig,PackageLimits,PreservingXmlDocument as Xml,
    TextFlowReader,TextFlowLimits,WriterLimits,document_import::structure::note_export::{NoteFileSelection as Pick,NoteFileExportError as E}};
use std::{collections::BTreeMap,error::Error,io::Cursor};
#[allow(dead_code)]
#[path="support/document_import_field_fixture.rs"] mod fixture;
type TestResult=Result<(),Box<dyn Error>>;
const HP:&str="http://www.hancom.co.kr/hwpml/2011/paragraph";
const XML:&str="http://www.w3.org/XML/1998/namespace";
fn limits()->NoteHwpxLimits {NoteHwpxLimits::new(Default::default()).expect("finite defaults")}
fn note(kind:&str,id:u32,attrs:&str,children:&str)->String {format!("<hp:ctrl><hp:{kind} instId='101'><hp:subList {attrs}><hp:p id='{id}'>{children}</hp:p></hp:subList></hp:{kind}></hp:ctrl>")}
fn raw_section(bytes:&[u8])->Result<Vec<u8>,Box<dyn Error>> {
    let mut reader=BoundedZipReader::open(Cursor::new(bytes),PackageLimits::default())?;
    let i=reader.entries().iter().position(|e|e.path.as_str()=="Contents/section0.xml").ok_or("section")?;Ok(reader.read_entry(i)?)
}
fn inherited(xml:&Xml,raw:&[u8],index:usize)->BTreeMap<String,String> {
    let mut result=BTreeMap::new();let mut current=Some(index);
    while let Some(i)=current {let n=&xml.elements()[i];for a in n.attributes().iter().filter(|a|a.name().namespace()==Some(XML)&&matches!(a.name().local_name(),"lang"|"space")) {
        result.entry(a.name().local_name().to_owned()).or_insert_with(||{
            let span=a.value_span();let text=std::str::from_utf8(&raw[span.start()..span.end()]).expect("admitted XML UTF-8");
            quick_xml::escape::unescape(text).expect("admitted XML attribute").into_owned()
        });
    }current=n.parent();}result
}
fn contexts(xml:&Xml,raw:&[u8],local:&str)->Vec<BTreeMap<String,String>> {xml.elements().iter().enumerate().filter(|(_,n)|n.name().namespace()==Some(HP)&&n.name().local_name()==local).map(|(i,_)|inherited(xml,raw,i)).collect()}
#[test]
fn inherited_note_language_space_and_original_section_property_contexts_survive_detachment()->TestResult {
    let first=note("footNote",11,"xml:lang='fr' xml:space='default'", "<hp:run xml:lang='ja'><hp:t>  FIRST  </hp:t><x:future xmlns:x='urn:opaque' x:value='untouched'/></hp:run>");
    let second=note("endNote",12,"xml:lang='ko' xml:space='preserve'", "<hp:run><hp:t> SECOND </hp:t></hp:run>");
    let bytes=fixture::package(&format!("<hp:p id='1' xml:lang='en'><hp:run xml:lang='de' xml:space='preserve'><hp:secPr><hp:startNum pageStartsOn='BOTH' page='0' pic='1' tbl='1' equation='1'/></hp:secPr>{first}{second}</hp:run></hp:p>"))?;
    let source=fixture::forms(&bytes,"contexts")?;let original_raw=raw_section(&bytes)?;let before=Xml::parse(&original_raw)?;
    let candidate=source.body_structure().export_note_file_candidate(&bytes,Pick::Both,limits(),WriterLimits::default())?;
    let output=candidate.with_verified_bytes(<[u8]>::to_vec)?;let raw=raw_section(&output)?;let after=Xml::parse(&raw)?;
    assert_eq!(contexts(&before,&original_raw,"t"),contexts(&after,&raw,"t"));assert_eq!(contexts(&before,&original_raw,"secPr"),contexts(&after,&raw,"secPr"));
    assert!(String::from_utf8(raw)?.contains("x:value='untouched'"));assert!(fixture::forms(&output,"collected")?.notes().is_empty());
    assert_eq!(source.verify_source(&bytes)?,*source.receipt());assert!(!candidate.receipt().note_container_layout_and_native_numbering_qualified);Ok(())
}
#[test]
fn empty_language_reset_local_overrides_and_default_space_are_not_replaced_by_outer_values()->TestResult {
    let n=note("footNote",11,"xml:lang='' xml:space='default'", "<hp:run><hp:t>A</hp:t></hp:run><hp:run xml:lang='ko' xml:space='preserve'><hp:t>B</hp:t></hp:run>");
    let bytes=fixture::package(&format!("<hp:p id='1' xml:lang='en' ><hp:run xml:space='preserve'>{n}</hp:run></hp:p>"))?;
    let source=fixture::forms(&bytes,"reset")?;let before_raw=raw_section(&bytes)?;let before=Xml::parse(&before_raw)?;
    let candidate=source.body_structure().export_note_file_candidate(&bytes,Pick::Footnotes,limits(),WriterLimits::default())?;
    let after_raw=raw_section(&candidate.with_verified_bytes(<[u8]>::to_vec)?)?;let after=Xml::parse(&after_raw)?;
    let expected=contexts(&before,&before_raw,"t");assert_eq!(expected,contexts(&after,&after_raw,"t"));assert_eq!(expected[0].get("lang").map(String::as_str),Some(""));
    assert_eq!(expected[0].get("space").map(String::as_str),Some("default"));assert_eq!(expected[1].get("lang").map(String::as_str),Some("ko"));Ok(())
}
#[test]
fn removed_intermediate_xml_base_rejects_without_inventing_uri_resolution_or_affecting_other_family()->TestResult {
    let a=note("footNote",11,"xml:base='assets/'", "<hp:run><hp:t>A</hp:t></hp:run>");
    let b=note("endNote",12,"", "<hp:run><hp:t>B</hp:t></hp:run>");
    let bytes=fixture::package(&format!("<hp:p id='1'><hp:run>{a}{b}</hp:run></hp:p>"))?;let source=fixture::forms(&bytes,"base")?;
    for pick in [Pick::Both,Pick::Footnotes] {assert!(matches!(source.body_structure().export_note_file_candidate(&bytes,pick,limits(),WriterLimits::default()),Err(E::InheritedContext)));}
    let end=source.body_structure().export_note_file_candidate(&bytes,Pick::Endnotes,limits(),WriterLimits::default())?;assert_eq!(end.receipt().selected_notes,1);
    assert_eq!(source.verify_source(&bytes)?,*source.receipt());Ok(())
}
#[test]
fn only_source_graph_mapping_admits_xml_language_space_and_typed_lowering_boundary_stays_strict()->TestResult {
    let paragraph=format!("<hp:p xmlns:hp='{HP}' id='1' xml:lang='ko' xml:space='preserve'><hp:run xml:lang='en'><hp:t>A</hp:t></hp:run></hp:p>");
    assert!(TextFlowReader::read(paragraph.as_bytes(),TextFlowLimits::default()).is_err());
    assert!(fixture::forms(&fixture::package(&paragraph)?,"source-context").is_ok());
    for extra in ["xml:space='bogus'","xml:id='unsupported'","xmlns:z='urn:unrecognized' z:lang='ko'"] {
        let bytes=fixture::package(&format!("<hp:p id='1' {extra}><hp:run><hp:t>A</hp:t></hp:run></hp:p>"))?;
        assert!(fixture::forms(&bytes,"invalid-context").is_err());
    }
    let source=fixture::package("<hp:p id='1'><hp:run xml:space='bogus'><hp:t>A</hp:t></hp:run></hp:p>")?;
    assert!(fixture::forms(&source,"invalid-run").is_err());Ok(())
}
#[test]
fn fifty_notes_keep_each_effective_context_and_native_container_attributes_bound_to_original()->TestResult {
    let mut notes=String::new();
    for i in 0..50 {notes.push_str(&note("footNote",100+i,&format!("textDirection='HORIZONTAL' lineWrap='BREAK' vertAlign='TOP' textWidth='0' textHeight='0' hasTextRef='0' hasNumRef='0' linkListIDRef='0' linkListNextIDRef='0' xml:lang='x-note-{i}' xml:space='preserve'"),"<hp:run><hp:t>BODY</hp:t></hp:run>"));}
    let bytes=fixture::package(&format!("<hp:p id='1'><hp:run>{notes}</hp:run></hp:p>"))?;let source=fixture::forms(&bytes,"fifty")?;
    let original_raw=raw_section(&bytes)?;let original=Xml::parse(&original_raw)?;let candidate=source.body_structure().export_note_file_candidate(&bytes,Pick::Both,limits(),WriterLimits::default())?;
    let output=candidate.with_verified_bytes(<[u8]>::to_vec)?;let after_raw=raw_section(&output)?;let after=Xml::parse(&after_raw)?;
    assert_eq!(candidate.receipt().selected_notes,50);assert_eq!(contexts(&original,&original_raw,"t"),contexts(&after,&after_raw,"t"));
    assert!(!candidate.receipt().note_container_layout_and_native_numbering_qualified);
    assert_eq!(source.verify_source(&bytes)?,*source.receipt());Ok(())
}
#[test]
fn inherited_attribute_materialization_is_charged_to_the_existing_payload_byte_limit()->TestResult {
    let body="<hp:run><hp:t>A</hp:t></hp:run>";
    let tight=NoteHwpxLimits::new(NoteHwpxLimitConfig {payload_bytes:1024,..Default::default()})?;
    for (attrs,large) in [(String::new(),false),(format!("xml:lang='x{}'","-a".repeat(1100)),true)] {
        let n=note("footNote",11,&attrs,body);let bytes=fixture::package(&format!("<hp:p id='1'><hp:run>{n}</hp:run></hp:p>"))?;let source=fixture::forms(&bytes,"bounded-context")?;
        let result=source.body_structure().export_note_file_candidate(&bytes,Pick::Both,tight,WriterLimits::default());
        if large {assert!(matches!(result,Err(E::Limit)));}else{result?;}
    }Ok(())
}
