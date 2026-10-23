use hwpx_package::{BoundedZipReader,NoteHwpxLimitConfig,NoteHwpxLimits,PackageLimits,
    PreservingXmlDocument,WriterLimitConfig,WriterLimits,
    document_import::structure::note_export::{NoteFileExportError as E,NoteFileSelection as Pick}};
use std::{collections::BTreeMap,error::Error,io::{Cursor,Write as _}};
#[allow(dead_code)]
#[path="support/document_import_field_fixture.rs"] mod fixture;
#[path="support/document_import_note_fixture.rs"] mod historical;
type TestResult=Result<(),Box<dyn Error>>;
fn limits()->NoteHwpxLimits{NoteHwpxLimits::new(Default::default()).expect("finite limits")}
fn note(kind:&str,id:u32,text:&str)->String {
    format!("<hp:ctrl><hp:{kind} instId='101'><hp:subList><hp:p id='{id}'><hp:run><hp:t>{text}</hp:t></hp:run></hp:p></hp:subList></hp:{kind}></hp:ctrl>")
}
fn source()->Result<Vec<u8>,Box<dyn Error>>{
    fixture::package(&format!("<hp:p id='1'><hp:run><hp:secPr><hp:startNum pageStartsOn='BOTH' page='0' pic='1' tbl='1' equation='1'/></hp:secPr><hp:t>PRIVATE-MAIN-NOT-EXPORTED</hp:t>{}{}{}</hp:run></hp:p>",
        note("endNote",11,"END-FIRST"),note("footNote",12,"FOOT-SECOND"),note("endNote",13,"END-THIRD")))
}
fn expanded(bytes:&[u8])->Result<BTreeMap<String,Vec<u8>>,Box<dyn Error>>{
    let mut reader=BoundedZipReader::open(Cursor::new(bytes),PackageLimits::default())?;
    (0..reader.entries().len()).map(|i|Ok((reader.entries()[i].path.as_str().to_owned(),reader.read_entry(i)?))).collect()
}
fn rebuild(parts:BTreeMap<String,Vec<u8>>)->Result<Vec<u8>,Box<dyn Error>>{
    let mut zip=zip::ZipWriter::new(Cursor::new(Vec::new()));
    let method=zip::write::SimpleFileOptions::default().compression_method(zip::CompressionMethod::Stored);
    zip.start_file("mimetype",method)?;zip.write_all(parts.get("mimetype").ok_or("mimetype")?)?;
    for (name,data) in parts.iter().filter(|(n,_)|n.as_str()!="mimetype") {zip.start_file(name,method)?;zip.write_all(data)?;}
    Ok(zip.finish()?.into_inner())
}
#[test]
fn actual_hwpx_file_collects_families_in_insertion_order_and_preserves_original_source()->TestResult{
    let bytes=source()?;let saved=bytes.clone();let forms=fixture::forms(&bytes,"export-source")?;
    for (selection,words) in [(Pick::Both,vec!["END-FIRST","FOOT-SECOND","END-THIRD"]),
        (Pick::Footnotes,vec!["FOOT-SECOND"]),(Pick::Endnotes,vec!["END-FIRST","END-THIRD"])] {
        let candidate=forms.body_structure().export_note_file_candidate(&bytes,selection,limits(),WriterLimits::default())?;
        let temp=tempfile::tempdir()?;let path=temp.path().join("collected-notes.hwpx");
        candidate.with_verified_bytes(|output|->Result<(),Box<dyn Error>> {
            let mut file=std::fs::OpenOptions::new().write(true).create_new(true).open(&path)?;file.write_all(output)?;file.sync_all()?;Ok(())
        })??;
        let output=std::fs::read(&path)?;let after=fixture::forms(&output,"export-result")?;assert!(after.notes().is_empty());
        let part=expanded(&output)?.remove("Contents/section0.xml").ok_or("section")?;let text=String::from_utf8(part)?;
        assert!(!text.contains("PRIVATE-MAIN-NOT-EXPORTED"));let mut previous=0;
        for word in &words {let at=text.find(word).ok_or("expected exported note")?;assert!(at>=previous);previous=at;}
        for excluded in ["END-FIRST","FOOT-SECOND","END-THIRD"].into_iter().filter(|w|!words.contains(w)){assert!(!text.contains(excluded));}
        assert_eq!(candidate.receipt().selected_notes,words.len());assert!(text.contains("startNum"));
        assert!(!candidate.receipt().native_save_reopen_render_qualified&&!candidate.receipt().execution_publication_authority);
        assert_eq!(std::fs::OpenOptions::new().write(true).create_new(true).open(&path).err().map(|e|e.kind()),Some(std::io::ErrorKind::AlreadyExists));
    }
    assert_eq!(bytes,saved);assert_eq!(forms.verify_source(&bytes)?,*forms.receipt());Ok(())
}
#[test]
fn namespace_shadowing_default_namespaces_and_nested_rich_body_are_closed_without_flattening()->TestResult{
    let body="<hp:p id='1'><hp:run><hp:t>PRIVATE-MAIN</hp:t><hp:ctrl xmlns:x='http://www.hancom.co.kr/hwpml/2011/paragraph' xmlns:z='urn:outer'><x:footNote instId='101'><x:subList xmlns:z='urn:inner'><x:p id='22'><x:run><x:t>A &amp; 한글</x:t><z:future z:property='kept' z:value='opaque'><z:item/></z:future></x:run></x:p><p xmlns='http://www.hancom.co.kr/hwpml/2011/paragraph' id='23'><run><t>DEFAULT-NAMESPACE</t></run></p></x:subList></x:footNote></hp:ctrl></hp:run></hp:p>";
    let bytes=fixture::package(body)?;let forms=fixture::forms(&bytes,"namespace-source")?;
    let candidate=forms.body_structure().export_note_file_candidate(&bytes,Pick::Both,limits(),WriterLimits::default())?;
    let output=candidate.with_verified_bytes(<[u8]>::to_vec)?;
    let raw=expanded(&output)?.remove("Contents/section0.xml").ok_or("section")?;let xml=PreservingXmlDocument::parse(&raw)?;
    assert!(xml.elements().iter().any(|n|n.name().local_name()=="future"&&n.name().namespace()==Some("urn:inner")));
    assert!(xml.elements().iter().any(|n|n.name().local_name()=="p"&&n.name().prefix().is_none()&&n.name().namespace()==Some("http://www.hancom.co.kr/hwpml/2011/paragraph")));
    let text=String::from_utf8(raw)?;assert!(text.contains("A &amp; 한글")&&text.contains("DEFAULT-NAMESPACE")&&text.contains("z:property='kept'"));
    assert!(!text.contains("PRIVATE-MAIN"));assert_eq!(candidate.receipt().output_body_elements,2);Ok(())
}
#[test]
fn empty_sections_are_removed_from_opf_spine_and_header_count_without_losing_other_metadata()->TestResult{
    let mut parts=expanded(&source()?)?;
    let opf=parts.get_mut("Contents/content.hpf").ok_or("opf")?;
    *opf=String::from_utf8(opf.clone())?.replace("</o:manifest>","<o:item id='s1' href='Contents/section1.xml' media-type='application/xml'/></o:manifest>")
        .replace("</o:spine>","<o:itemref idref='s1'/></o:spine>").into_bytes();
    parts.insert("Contents/section1.xml".into(),b"<hs:sec xmlns:hs='http://www.hancom.co.kr/hwpml/2011/section' xmlns:hp='http://www.hancom.co.kr/hwpml/2011/paragraph'><hp:p id='1'><hp:run><hp:t>PRIVATE-EMPTY-SECTION</hp:t></hp:run></hp:p></hs:sec>".to_vec());
    parts.insert("Contents/header.xml".into(),b"<hh:head xmlns:hh='http://www.hancom.co.kr/hwpml/2011/head' secCnt='2'><hh:opaque value='KEEP-HEADER-METADATA'/></hh:head>".to_vec());
    let bytes=rebuild(parts)?;let forms=fixture::forms(&bytes,"two-sections")?;
    let candidate=forms.body_structure().export_note_file_candidate(&bytes,Pick::Both,limits(),WriterLimits::default())?;
    let out=candidate.with_verified_bytes(<[u8]>::to_vec)?;let expanded=expanded(&out)?;
    assert!(!expanded.contains_key("Contents/section1.xml"));
    assert!(!String::from_utf8(expanded["Contents/content.hpf"].clone())?.contains("section1.xml"));
    let head=String::from_utf8(expanded["Contents/header.xml"].clone())?;assert!(head.contains("secCnt='1'")&&head.contains("KEEP-HEADER-METADATA"));
    assert_eq!((candidate.receipt().output_body_sections,candidate.receipt().omitted_body_sections),(1,1));Ok(())
}
#[test]
fn source_preview_and_caret_are_invalidated_while_header_and_resource_bytes_are_preserved()->TestResult{
    let mut parts=expanded(&source()?)?;
    parts.insert("Preview/PrvText.txt".into(),b"PRIVATE-SOURCE-PREVIEW".to_vec());
    // A valid source preview is taken from the existing VS-0 builder, not fabricated pixels.
    let seed=hwpx_package::Hancom2020Vs0Builder::build("SEED")?.with_verified_bytes(<[u8]>::to_vec)?;
    let pixel=expanded(&seed)?.remove("Preview/PrvImage.png").ok_or("preview")?;
    parts.insert("Preview/PrvImage.png".into(),pixel);
    parts.insert("settings.xml".into(),b"<ha:HWPApplicationSetting xmlns:ha='http://www.hancom.co.kr/hwpml/2011/app'><ha:CaretPosition listIDRef='0' paraIDRef='1' pos='10'/><ha:other value='KEEP-SETTINGS'/></ha:HWPApplicationSetting>".to_vec());
    let opf=parts.get_mut("Contents/content.hpf").ok_or("opf")?;
    *opf=String::from_utf8(opf.clone())?.replace("</o:manifest>","<o:item id='settings' href='settings.xml' media-type='application/xml'/></o:manifest>").into_bytes();
    // The preview text is an admitted rootfile, exactly as in real HWPX packages.
    let container=parts.get_mut("META-INF/container.xml").ok_or("container")?;
    *container=String::from_utf8(container.clone())?.replace("</rootfiles>","<rootfile full-path='Preview/PrvText.txt' media-type='text/plain'/></rootfiles>").into_bytes();
    let bytes=rebuild(parts)?;let original=expanded(&bytes)?;let forms=fixture::forms(&bytes,"previews")?;
    let candidate=forms.body_structure().export_note_file_candidate(&bytes,Pick::Both,limits(),WriterLimits::default())?;
    let output=candidate.with_verified_bytes(<[u8]>::to_vec)?;let actual=expanded(&output)?;
    assert!(actual["Preview/PrvText.txt"].is_empty());assert_eq!(actual["Contents/header.xml"],original["Contents/header.xml"]);
    let settings=String::from_utf8(actual["settings.xml"].clone())?;assert!(!settings.contains("CaretPosition")&&settings.contains("KEEP-SETTINGS"));
    assert!(candidate.receipt().non_body_metadata_and_resources_may_contain_source_data);
    assert_eq!(forms.verify_source(&bytes)?,*forms.receipt());Ok(())
}
#[test]
fn passive_image_resource_reference_and_bytes_are_preserved_with_the_selected_body()->TestResult{
    let mut parts=expanded(&source()?)?;
    let seed=hwpx_package::Hancom2020Vs0Builder::build("SEED")?.with_verified_bytes(<[u8]>::to_vec)?;
    let pixel=expanded(&seed)?.remove("Preview/PrvImage.png").ok_or("pixel")?;
    parts.insert("BinData/image1.png".into(),pixel.clone());
    let opf=parts.get_mut("Contents/content.hpf").ok_or("opf")?;
    *opf=String::from_utf8(opf.clone())?.replace("</o:manifest>","<o:item id='image1' href='BinData/image1.png' media-type='image/png'/></o:manifest>").into_bytes();
    let section=parts.get_mut("Contents/section0.xml").ok_or("section")?;
    *section=String::from_utf8(section.clone())?.replace("<hp:t>FOOT-SECOND</hp:t>",
        "<hp:t>FOOT-SECOND</hp:t><hp:pic id='7' xmlns:hc='http://www.hancom.co.kr/hwpml/2011/core'><hc:img binaryItemIDRef='image1'/></hp:pic>").into_bytes();
    let bytes=rebuild(parts)?;let source=fixture::forms(&bytes,"image-source")?;
    let candidate=source.body_structure().export_note_file_candidate(&bytes,Pick::Footnotes,limits(),WriterLimits::default())?;
    let output=candidate.with_verified_bytes(<[u8]>::to_vec)?;let actual=expanded(&output)?;
    assert_eq!(actual["BinData/image1.png"],pixel);
    let body=String::from_utf8(actual["Contents/section0.xml"].clone())?;
    assert!(body.contains("binaryItemIDRef='image1'")&&body.contains("FOOT-SECOND"));
    assert!(!body.contains("END-FIRST")&&!body.contains("PRIVATE-MAIN"));Ok(())
}
#[test]
fn empty_selection_drift_protection_and_native_security_do_not_produce_output()->TestResult{
    let bytes=source()?;let f=fixture::forms(&bytes,"guards")?;
    let absent=fixture::package("<hp:p id='1'><hp:run><hp:t>NO NOTES</hp:t></hp:run></hp:p>")?;
    assert!(matches!(fixture::forms(&absent,"empty")?.body_structure().export_note_file_candidate(&absent,Pick::Both,limits(),WriterLimits::default()),Err(E::NoNotes)));
    assert!(matches!(f.body_structure().export_note_file_candidate(&absent,Pick::Both,limits(),WriterLimits::default()),Err(E::Source)));
    let locked=fixture::package(&format!("<hp:p id='1'><hp:run><hp:ctrl><hp:footNote instId='101'><hp:subList lock='1'><hp:p id='12'><hp:run><hp:t>LOCKED</hp:t></hp:run></hp:p></hp:subList></hp:footNote></hp:ctrl></hp:run></hp:p>"))?;
    assert!(matches!(fixture::forms(&locked,"locked")?.body_structure().export_note_file_candidate(&locked,Pick::Both,limits(),WriterLimits::default()),Err(E::Protection)));
    let mut parts=expanded(&bytes)?;parts.insert("META-INF/signatures.xml".into(),b"<Signature xmlns='http://www.w3.org/2000/09/xmldsig#'/>".to_vec());
    let signed=rebuild(parts)?;
    // The source importer or original trust chain may reject before our security gate.
    if let Ok(source)=fixture::forms(&signed,"signed") {assert!(source.body_structure().export_note_file_candidate(&signed,Pick::Both,limits(),WriterLimits::default()).is_err());}
    Ok(())
}
#[test]
fn finite_source_selection_payload_section_and_output_limits_are_enforced()->TestResult{
    let bytes=source()?;let f=fixture::forms(&bytes,"limits")?;
    for config in [NoteHwpxLimitConfig {notes:1,..Default::default()},NoteHwpxLimitConfig {elements:1,..Default::default()},
        NoteHwpxLimitConfig {section_bytes:1,..Default::default()},NoteHwpxLimitConfig {payload_bytes:1,..Default::default()},
        NoteHwpxLimitConfig {paragraphs:1,..Default::default()}] {
        assert!(matches!(f.body_structure().export_note_file_candidate(&bytes,Pick::Both,NoteHwpxLimits::new(config)?,WriterLimits::default()),Err(E::Limit)));
    }
    assert!(f.body_structure().export_note_file_candidate(&bytes,Pick::Both,limits(),WriterLimits::new(WriterLimitConfig {max_output_bytes:1})?).is_err());
    Ok(())
}
#[test]
fn nine_original_note_packages_export_six_and_reject_three_source_id_collisions_without_native_relabelling()->TestResult{
    let(mut exported,mut rejected)=(0usize,0usize);let mut lanes=[0usize;3];
    for input in historical::actual_inputs()? {
        lanes[match input.lane {"generated"=>0,"saved"=>1,"reopened"=>2,_=>return Err("lane".into())}]+=1;
        let source=fixture::forms(&input.bytes,"historical-export")?;
        let result=source.body_structure().export_note_file_candidate(&input.bytes,Pick::Both,limits(),WriterLimits::default());
        if input.expected_notes==2 {assert!(matches!(result,Err(E::Trust("id_index_validation_failed"))));rejected+=1;}
        else {let candidate=result?;let output=candidate.with_verified_bytes(<[u8]>::to_vec)?;assert!(fixture::forms(&output,"exported")?.notes().is_empty());exported+=1;}
        assert_eq!(source.verify_source(&input.bytes)?,*source.receipt());
    }
    assert_eq!((exported,rejected),(6,3));assert_eq!(lanes,[3,3,3]);Ok(())
}
#[test]
fn large_unselected_main_run_does_not_change_collected_file_or_copy_main_text_into_output()->TestResult{
    let small=source()?;let mut parts=expanded(&small)?;
    let raw=parts.get_mut("Contents/section0.xml").ok_or("section")?;
    *raw=String::from_utf8(raw.clone())?.replace("PRIVATE-MAIN-NOT-EXPORTED",&"UNSELECTED-LARGE-MAIN-".repeat(12_000)).into_bytes();
    let large=rebuild(parts)?;assert!(large.len()>240_000);
    let a=fixture::forms(&small,"small")?;let b=fixture::forms(&large,"large")?;
    let x=a.body_structure().export_note_file_candidate(&small,Pick::Both,limits(),WriterLimits::default())?;
    let y=b.body_structure().export_note_file_candidate(&large,Pick::Both,limits(),WriterLimits::default())?;
    // Rebuild normalizes archive entry order. Compare the same normalization of
    // the small source, not an accidental byte-order difference in the inputs.
    let normalized=rebuild(expanded(&small)?)?;let c=fixture::forms(&normalized,"normalized")?;
    let z=c.body_structure().export_note_file_candidate(&normalized,Pick::Both,limits(),WriterLimits::default())?;
    assert_eq!(y.with_verified_bytes(<[u8]>::to_vec)?,z.with_verified_bytes(<[u8]>::to_vec)?);
    assert_eq!(expanded(&x.with_verified_bytes(<[u8]>::to_vec)?)?,expanded(&y.with_verified_bytes(<[u8]>::to_vec)?)?);
    assert_ne!(y.receipt().request_sha256,z.receipt().request_sha256);assert_eq!(b.verify_source(&large)?,*b.receipt());Ok(())
}
#[test]
fn whole_form_proof_matches_direct_output_and_rejects_foreign_original_and_fresh_drift()->TestResult{
    use hwpx_package::document_import::structure::note_export::note_file_export_request_sha256;
    use sha2::{Digest as _,Sha256};
    let bytes=source()?;let original=fixture::forms(&bytes,"proof")?;let foreign=fixture::forms(&bytes,"proof")?;
    let proof=original.reconstruct_source_for_verification(&bytes)?;
    for (pick,tag) in [(Pick::Footnotes,0u8),(Pick::Endnotes,1),(Pick::Both,2)] {
        let direct=original.body_structure().export_note_file_candidate(&bytes,pick,limits(),WriterLimits::default())?;
        let joined=proof.export_note_file_candidate(&original,&bytes,pick,limits(),WriterLimits::default())?;
        assert_eq!(direct.receipt(),joined.receipt());assert_eq!(direct.with_verified_bytes(<[u8]>::to_vec)?,joined.with_verified_bytes(<[u8]>::to_vec)?);
        let source_sha:[u8;32]=Sha256::digest(&bytes).into();let mut digest=Sha256::new();
        digest.update(b"hwpx-agent.source-note-file-hwpx/v1\0");digest.update(source_sha);digest.update([tag]);
        let expected:[u8;32]=digest.finalize().into();assert_eq!(note_file_export_request_sha256(source_sha,pick),expected);
        assert_eq!(joined.receipt().request_sha256,expected);
        assert!(matches!(proof.export_note_file_candidate(&foreign,&bytes,pick,limits(),WriterLimits::default()),Err(E::Source)));
    }
    let mut changed=bytes.clone();changed.push(0);
    assert!(matches!(proof.export_note_file_candidate(&original,&changed,Pick::Both,limits(),WriterLimits::default()),Err(E::Source)));Ok(())
}
#[test]
fn spine_classified_body_named_settings_is_not_replaced_by_original_metadata_payload()->TestResult{
    let mut parts=expanded(&source()?)?;
    let section=parts.remove("Contents/section0.xml").ok_or("section")?;parts.insert("settings.xml".into(),section);
    let opf=parts.get_mut("Contents/content.hpf").ok_or("opf")?;
    *opf=String::from_utf8(opf.clone())?.replace("Contents/section0.xml","settings.xml").into_bytes();
    let bytes=rebuild(parts)?;let source=fixture::forms(&bytes,"body-settings")?;
    let candidate=source.body_structure().export_note_file_candidate(&bytes,Pick::Both,limits(),WriterLimits::default())?;
    let output=candidate.with_verified_bytes(<[u8]>::to_vec)?;
    let body=String::from_utf8(expanded(&output)?.remove("settings.xml").ok_or("output body")?)?;
    assert!(!body.contains("PRIVATE-MAIN"));assert!(body.contains("FOOT-SECOND")&&body.contains("END-FIRST")&&body.contains("END-THIRD"));
    assert!(fixture::forms(&output,"collected")?.notes().is_empty());Ok(())
}
