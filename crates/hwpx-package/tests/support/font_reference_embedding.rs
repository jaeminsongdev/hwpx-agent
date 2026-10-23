//! Synthetic opaque binary evidence only; not a valid/installed/activated font or a Native fixture.
use super::*;
use hwpx_package::{IdIndex,IdIndexError,IdIndexLimits,IdIssueKind,IdRuleProfile,PackageGraph,PackageGraphLimits};
use std::io::Write;
use zip::{CompressionMethod,ZipWriter,write::SimpleFileOptions};
const BINARY_PATH:&str="BinData/p09-font-preservation.bin";
const PAYLOAD:&[u8]=b"\0\x01\0\0P09-OPAQUE-FONT-PRESERVATION-ONLY";
fn declaration_only()->Result<Vec<u8>,Box<dyn Error>> {
    let original=mutation::change_attribute(base()?,"Contents/header.xml","font","isEmbedded","1")?;
    mutation::mutate_part(&original,"Contents/header.xml",|text|{
        let xml=PreservingXmlDocument::parse(text.as_bytes())?;
        let node=xml.elements().iter().find(|n|n.name().local_name()=="font").ok_or("font")?;
        let mut t=text.to_owned();t.insert_str(node.start_name_span().end()," binaryItemIDRef=\"DECLARED-ONLY\"");Ok(t)
    })
}
fn with_payload(bytes:&[u8],payload:&[u8])->Result<Vec<u8>,Box<dyn Error>> {
    let mut input=BoundedZipReader::open(Cursor::new(bytes),PackageLimits::default())?;
    let entries:Vec<_>=input.entries().iter().map(|e|e.path.as_str().to_owned()).collect();
    let mut output=ZipWriter::new(Cursor::new(Vec::new()));
    let options=SimpleFileOptions::default().compression_method(CompressionMethod::Stored);
    for (i,path)in entries.into_iter().enumerate(){
        if path==BINARY_PATH{continue;}let bytes=input.read_entry(i)?;output.start_file(path,options)?;output.write_all(&bytes)?;
    }
    output.start_file(BINARY_PATH,options)?;output.write_all(payload)?;Ok(output.finish()?.into_inner())
}
pub(super) fn attach_binary_resource(original:&[u8])->Result<Vec<u8>,Box<dyn Error>> {
    let declared=mutation::mutate_part(original,"Contents/content.hpf",|text|{
        let xml=PreservingXmlDocument::parse(text.as_bytes())?;
        let node=xml.elements().iter().find(|n|n.name().local_name()=="manifest").ok_or("manifest")?;
        let namespace=node.name().namespace().ok_or("manifest namespace")?;
        let child=format!("<p09:item xmlns:p09=\"{namespace}\" id=\"DECLARED-ONLY\" href=\"../{BINARY_PATH}\" media-type=\"application/octet-stream\" isEmbeded=\"1\"/>");
        let mut result=text.to_owned();result.insert_str(node.end_tag_span().ok_or("manifest end")?.start(),&child);Ok(result)
    })?;
    with_payload(&declared,PAYLOAD)
}
fn with_substitute(bytes:&[u8])->Result<Vec<u8>,Box<dyn Error>> {
    mutation::mutate_part(bytes,"Contents/header.xml",|text|{
        let xml=PreservingXmlDocument::parse(text.as_bytes())?;
        let node=xml.elements().iter().find(|n|n.name().local_name()=="font").ok_or("font")?;
        let child="<p09:substFont xmlns:p09=\"http://www.hancom.co.kr/hwpml/2011/head\" face=\"P09-FALLBACK\" type=\"TTF\" binaryItemIDRef=\"DECLARED-ONLY\"/>";
        let mut result=text.to_owned();
        if node.is_empty(){
            let span=node.start_tag_span();let name=node.start_name_span();
            result.replace_range(span.end()-2..span.end(),&format!(">{child}</{}>",&text[name.start()..name.end()]));
        }else{
            // substFont precedes the existing typeInfo child in the unchanged typed reader.
            result.insert_str(node.start_tag_span().end(),child);
        }
        Ok(result)
    })
}
fn index(bytes:&[u8],profile:IdRuleProfile)->Result<Result<IdIndex,IdIndexError>,Box<dyn Error>> {
    let mut reader=BoundedZipReader::open(Cursor::new(bytes),PackageLimits::default())?;
    let graph=PackageGraph::build(&mut reader,PackageGraphLimits::default())?;
    Ok(IdIndex::build(&mut reader,&graph,profile,IdIndexLimits::default()))
}
fn issues(bytes:&[u8],profile:IdRuleProfile)->Result<Vec<IdIssueKind>,Box<dyn Error>> {
    let error=index(bytes,profile)?.err().ok_or("expected ID denial")?;
    Ok(error.validation().ok_or("expected validation issues")?.issues().iter().map(|i|i.kind()).collect())
}
#[test]
fn old_profile_unknown_and_new_profile_dangling_distinguish_both_original_causes()->R {
    let original=declaration_only()?;
    assert_eq!(issues(&original,IdRuleProfile::hwpml_2011_shape_v6())?,[IdIssueKind::UnknownIdLikeAttribute]);
    assert_eq!(issues(&original,IdRuleProfile::hwpml_2011_font_binary_v10())?,[IdIssueKind::DanglingReference]);Ok(())
}
#[test]
fn primary_and_substitute_binary_bindings_preserve_all_metadata_and_exact_payload()->R {
    let original=with_substitute(&attach_binary_resource(&declaration_only()?)?)?;
    assert!(index(&original,IdRuleProfile::hwpml_2011_font_binary_v10())?.is_ok());
    assert_eq!(issues(&original,IdRuleProfile::hwpml_2011_shape_v6())?,[IdIssueKind::UnknownIdLikeAttribute,IdIssueKind::UnknownIdLikeAttribute]);
    with_fonts(&original,|f|{assert!(f.definitions()[0].declared.substitute.is_some());Ok(())})?;
    let output=bytes(&candidate(&original,&all_mappings(&original)?,Limits::default())?)?;
    assert_preserved(&original,&output)?;assert_eq!(mutation::read_part(&output,BINARY_PATH)?,PAYLOAD);Ok(())
}
#[test]
fn missing_manifest_binding_still_rejects_instead_of_preserving_a_dangling_font()->R {
    let original=declaration_only()?;
    with_fonts(&original,|f|{let m=mapping(f,L::Hangul)?;
        assert_eq!(f.lower_reference_replacement_candidate(&original,&[m],Limits::default(),WriterLimits::default()).unwrap_err(),E::BinaryReference);Ok(())})?;Ok(())
}
#[test]
fn xml_manifest_target_is_not_accepted_as_a_binary_font_payload()->R {
    let original=attach_binary_resource(&declaration_only()?)?;
    let original=mutation::mutate_part(&original,"Contents/content.hpf",|text|{
        let xml=PreservingXmlDocument::parse(text.as_bytes())?;
        let id=xml.elements().iter().filter(|n|n.name().local_name()=="item").find_map(|n|{
            let value=|key:&str|n.attributes().iter().find(|a|a.name().local_name()==key).map(|a|{let span=a.value_span();&text[span.start()..span.end()]});
            let href=value("href")?;if href.ends_with("header.xml"){Some(value("id")?.to_owned())}else{None}
        }).ok_or("header manifest id")?;
        // Header reference is installed below, leaving the binary declaration itself unchanged.
        Ok(text.replace("id=\"DECLARED-ONLY\"",&format!("id=\"P09_UNUSED_{id}\"")))
    })?;
    let mut reader=BoundedZipReader::open(Cursor::new(&original),PackageLimits::default())?;
    let graph=PackageGraph::build(&mut reader,PackageGraphLimits::default())?;
    let header_id=graph.relationships.iter().find(|r|r.target.as_str()=="Contents/header.xml").ok_or("header link")?.id.clone();
    let original=mutation::change_attribute(&original,"Contents/header.xml","font","binaryItemIDRef",&header_id)?;
    assert!(index(&original,IdRuleProfile::hwpml_2011_font_binary_v10())?.is_ok());
    with_fonts(&original,|f|{let m=mapping(f,L::Hangul)?;
        assert_eq!(f.lower_reference_replacement_candidate(&original,&[m],Limits::default(),WriterLimits::default()).unwrap_err(),E::BinaryReference);Ok(())})?;Ok(())
}
#[test]
fn unknown_id_like_attributes_remain_denied_by_the_new_profile()->R {
    let original=mutation::mutate_part(base()?,"Contents/header.xml",|text|{
        let xml=PreservingXmlDocument::parse(text.as_bytes())?;
        let node=xml.elements().iter().find(|n|n.name().local_name()=="font").ok_or("font")?;
        let mut result=text.to_owned();result.insert_str(node.start_name_span().end()," unsupportedIDRef=\"0\"");Ok(result)
    })?;
    assert!(issues(&original,IdRuleProfile::hwpml_2011_font_binary_v10())?.contains(&IdIssueKind::UnknownIdLikeAttribute));Ok(())
}
#[test]
fn namespaced_font_reference_is_not_a_native_unqualified_attribute()->R {
    let original=mutation::mutate_part(base()?,"Contents/header.xml",|text|{
        let xml=PreservingXmlDocument::parse(text.as_bytes())?;
        let node=xml.elements().iter().find(|n|n.name().local_name()=="font").ok_or("font")?;
        let mut result=text.to_owned();result.insert_str(node.start_name_span().end()," xmlns:p09=\"urn:p09-foreign\" p09:binaryItemIDRef=\"DECLARED-ONLY\"");Ok(result)
    })?;
    assert!(issues(&original,IdRuleProfile::hwpml_2011_font_binary_v10())?.contains(&IdIssueKind::UnknownIdLikeAttribute));Ok(())
}
#[test]
fn font_binary_profile_does_not_silently_enable_the_text_style_axis()->R {
    let original=mutation::mutate_part(base()?,"Contents/section0.xml",|text|{
        let xml=PreservingXmlDocument::parse(text.as_bytes())?;
        let node=xml.elements().iter().find(|n|n.name().local_name()=="t").ok_or("text span")?;
        let mut result=text.to_owned();result.insert_str(node.start_name_span().end()," charStyleIDRef=\"0\"");Ok(result)
    })?;
    assert!(issues(&original,IdRuleProfile::hwpml_2011_font_binary_v10())?.contains(&IdIssueKind::UnknownIdLikeAttribute));
    assert_eq!(IdRuleProfile::hwpml_2011_shape_v6().version(),"hwpml-2011-shape-static/v6");
    assert_eq!(IdRuleProfile::hwpml_2011_text_style_v9().version(),"hwpml-2011-text-style-static/v9");Ok(())
}
#[test]
fn empty_font_binary_payload_is_rejected_without_loading_it()->R {
    let original=with_payload(&attach_binary_resource(&declaration_only()?)?,&[])?;
    with_fonts(&original,|f|{let m=mapping(f,L::Hangul)?;
        assert_eq!(f.lower_reference_replacement_candidate(&original,&[m],Limits::default(),WriterLimits::default()).unwrap_err(),E::BinaryReference);Ok(())})?;Ok(())
}
#[test]
fn duplicate_native_font_declarations_are_not_admitted_by_the_new_profile()->R {
    let original=mutation::mutate_part(base()?,"Contents/header.xml",|text|{
        let xml=PreservingXmlDocument::parse(text.as_bytes())?;
        let node=xml.elements().iter().filter(|n|n.name().local_name()=="font").nth(1).ok_or("second font")?;
        let span=node.attributes().iter().find(|a|a.name().local_name()=="id").ok_or("font id")?.value_span();
        let mut result=text.to_owned();result.replace_range(span.start()..span.end(),"0");Ok(result)
    })?;
    assert!(issues(&original,IdRuleProfile::hwpml_2011_font_binary_v10())?.contains(&IdIssueKind::DuplicateDeclaration));Ok(())
}
#[test]
fn changed_binary_bytes_cannot_reuse_the_original_font_import_binding()->R {
    let original=attach_binary_resource(&declaration_only()?)?;
    let changed=with_payload(&original,b"P09-CHANGED-OPAQUE-PAYLOAD")?;
    with_fonts(&original,|f|{let m=mapping(f,L::Hangul)?;
        assert_eq!(f.lower_reference_replacement_candidate(&changed,&[m],Limits::default(),WriterLimits::default()).unwrap_err(),E::Source);Ok(())})?;Ok(())
}
