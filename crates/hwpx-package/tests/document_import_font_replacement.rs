use hwpx_package::{PreservingXmlDocument, WriterLimits, BoundedZipReader, PackageLimits,
    document_import::fields::{ImportedDocumentFields, semantics::{ImportedDocumentFieldSemantics,
        catalog::{ImportedDocumentCatalog, fonts::{ImportedDocumentFonts, ImportedFontLanguage as L,
            replacement::{FontReferenceMapping as M, FontReferenceReplacementLimits as Limits,
                FontReferenceReplacementError as E, FontReferenceReplacementCandidate as Candidate}}}}}};
use std::{error::Error, io::Cursor, sync::OnceLock};
#[path = "support/document_import_fonts_fixture.rs"] #[allow(dead_code)] mod fixture;
#[path = "support/document_import_catalog_fixture.rs"] #[allow(dead_code)] mod mutation;
type R = Result<(), Box<dyn Error>>;
const AXES: [L;7] = [L::Hangul,L::Latin,L::Hanja,L::Japanese,L::Other,L::Symbol,L::User];
static BASE: OnceLock<Result<Vec<u8>, String>> = OnceLock::new();
fn base() -> Result<&'static [u8], Box<dyn Error>> {
    BASE.get_or_init(|| make_base().map_err(|_| "font replacement fixture rejected".to_owned()))
        .as_ref().map(Vec::as_slice).map_err(|e| e.clone().into())
}
fn make_base() -> Result<Vec<u8>, Box<dyn Error>> {
    let bytes = mutation::actual_corpus()?.remove(0);
    // Derivative only. Add two distinct declarations per language without changing original IDs.
    mutation::mutate_part(&bytes, "Contents/header.xml", |text| {
        let xml = PreservingXmlDocument::parse(text.as_bytes())?;
        let mut edits = Vec::new();
        for (i, group) in xml.elements().iter().enumerate().filter(|(_,n)|n.name().local_name()=="fontface") {
            let fonts: Vec<_> = xml.elements().iter().filter(|n|n.parent()==Some(i)&&n.name().local_name()=="font").collect();
            let first = fonts.first().ok_or("font declaration")?;
            let native = |n: &hwpx_package::XmlElementToken| -> Result<u32,Box<dyn Error>> {
                let span=n.attributes().iter().find(|a|a.name().local_name()=="id").ok_or("font id")?.value_span();
                Ok(text[span.start()..span.end()].parse()?)
            };
            if !fonts.iter().enumerate().all(|(i,n)|native(n).is_ok_and(|id|id==i as u32)) {return Err("fixture original contiguous ids".into());}
            let outer=first.outer_span().ok_or("font span")?;
            let mut added=String::new();
            for (suffix,id) in [fonts.len(),fonts.len()+1].into_iter().enumerate() {
                let mut copy=text[outer.start()..outer.end()].to_owned();let mut attrs=Vec::new();
                for a in first.attributes() {
                    let value=match a.name().local_name(){"id"=>Some(id.to_string()),"face"=>Some(format!("P09-FONT-{}",if suffix==0{"A"}else{"B"})),_=>None};
                    if let Some(value)=value {let span=a.value_span();attrs.push((span.start()-outer.start(),span.end()-outer.start(),value));}
                }
                attrs.sort_by_key(|e|e.0);for(a,b,value)in attrs.into_iter().rev(){copy.replace_range(a..b,&value);}added.push_str(&copy);
            }
            let count=group.attributes().iter().find(|a|a.name().local_name()=="fontCnt").ok_or("font count")?.value_span();
            edits.push((count.start(),count.end(),(fonts.len()+2).to_string()));
            let end=group.end_tag_span().ok_or("font group end")?.start();edits.push((end,end,added));
        }
        edits.sort_by_key(|e|e.0);let mut result=text.to_owned();for(a,b,value)in edits.into_iter().rev(){result.replace_range(a..b,&value);}Ok(result)
    })
}
fn with_fonts<T>(bytes:&[u8], f: impl FnOnce(&ImportedDocumentFonts<'_, '_, '_, '_>)->Result<T,Box<dyn Error>>) -> Result<T,Box<dyn Error>> {
    let forms=fixture::forms(bytes,"source-font-replacement")?;
    let fields=ImportedDocumentFields::import(&forms)?;let meanings=ImportedDocumentFieldSemantics::import(&fields)?;
    let catalog=ImportedDocumentCatalog::import(&meanings)?;let fonts=ImportedDocumentFonts::import(&catalog)?;f(&fonts)
}
fn mapping(fonts:&ImportedDocumentFonts<'_, '_, '_, '_>,language:L)->Result<M,Box<dyn Error>> {
    let link=fonts.links().iter().find(|l|l.language==language).ok_or("font link")?;
    let old=fonts.definitions().iter().find(|d|d.font_id==link.font_id).ok_or("font target")?;
    let target=fonts.definitions().iter().find(|d|d.language==language&&d.declared.face=="P09-FONT-A").ok_or("declared replacement font")?;
    Ok(M{language,from_native_id:old.declared.id,to_native_id:target.declared.id})
}
fn spare(fonts:&ImportedDocumentFonts<'_, '_, '_, '_>,language:L)->Result<u32,Box<dyn Error>> {
    Ok(fonts.definitions().iter().find(|d|d.language==language&&d.declared.face=="P09-FONT-B").ok_or("declared spare font")?.declared.id)
}
fn candidate(bytes:&[u8],mappings:&[M],limits:Limits)->Result<Candidate,Box<dyn Error>> {
    with_fonts(bytes,|fonts|Ok(fonts.lower_reference_replacement_candidate(bytes,mappings,limits,WriterLimits::default())?))
}
fn bytes(c:&Candidate)->Result<Vec<u8>,Box<dyn Error>>{Ok(c.with_verified_bytes(<[u8]>::to_vec)?)}
fn all_mappings(data:&[u8])->Result<Vec<M>,Box<dyn Error>>{with_fonts(data,|fonts|AXES.into_iter().map(|l|mapping(fonts,l)).collect())}
fn assert_preserved(before:&[u8],after:&[u8])->R {
    let mut a=BoundedZipReader::open(Cursor::new(before),PackageLimits::default())?;
    let mut b=BoundedZipReader::open(Cursor::new(after),PackageLimits::default())?;
    let names:Vec<_>=a.entries().iter().map(|e|e.path.clone()).collect();
    assert_eq!(names,b.entries().iter().map(|e|e.path.clone()).collect::<Vec<_>>());
    for(i,path)in names.iter().enumerate(){if path.as_str()!="Contents/header.xml"{assert_eq!(a.read_entry(i)?,b.read_entry(i)?);}}
    with_fonts(before,|old|with_fonts(after,|new|{
        assert_eq!(old.definitions().len(),new.definitions().len());
        for(a,b)in old.definitions().iter().zip(new.definitions()){assert_eq!(a.language,b.language);assert_eq!(a.declared,b.declared);}
        Ok(())
    }))?;Ok(())
}
#[test]
fn all_seven_language_axes_read_back_and_other_package_members_exact()->R {
    let original=base()?;let mappings=all_mappings(original)?;
    let c=candidate(original,&mappings,Limits::default())?;let output=bytes(&c)?;
    assert!(c.receipt().changed_references>=7);assert!(c.receipt().outside_changed_attribute_values_exact);
    assert_preserved(original,&output)?;
    with_fonts(original,|before|with_fonts(&output,|fonts|{
        assert_eq!(before.links().len(),fonts.links().len());let mut changed=0;
        for (old,link) in before.links().iter().zip(fonts.links()){
            let source=before.definitions().iter().find(|d|d.font_id==old.font_id).ok_or("original target")?;
            let target=fonts.definitions().iter().find(|d|d.font_id==link.font_id).ok_or("output target")?;
            assert_eq!(old.language,link.language);
            let expected=if let Some(m)=mappings.iter().find(|m|m.language==old.language&&m.from_native_id==source.declared.id){changed+=1;m.to_native_id}else{source.declared.id};
            assert_eq!(target.declared.id,expected);
        }
        assert_eq!(changed,c.receipt().changed_references);
        Ok(())
    }))?;Ok(())
}
#[test]
fn one_language_never_aliases_same_numeric_id_in_other_languages()->R {
    let original=base()?;let m=all_mappings(original)?[0];let output=bytes(&candidate(original,&[m],Limits::default())?)?;
    with_fonts(original,|a|with_fonts(&output,|b|{
        for(x,y)in a.links().iter().zip(b.links()){
            let x=a.definitions().iter().find(|d|d.font_id==x.font_id).ok_or("old target")?;
            let y=b.definitions().iter().find(|d|d.font_id==y.font_id).ok_or("new target")?;
            assert_eq!(y.declared.id,if x.language==L::Hangul&&x.declared.id==m.from_native_id{m.to_native_id}else{x.declared.id});
        }Ok(())
    }))?;Ok(())
}
#[test]
fn mapping_chains_are_simultaneous_not_cascading()->R {
    let original=base()?;let m=all_mappings(original)?[0];
    let last=with_fonts(original,|f|spare(f,m.language))?;
    let c=candidate(original,&[m,M{language:m.language,from_native_id:m.to_native_id,to_native_id:last}],Limits::default())?;
    with_fonts(&bytes(&c)?,|f|{for link in f.links().iter().filter(|l|l.language==m.language){
        let d=f.definitions().iter().find(|d|d.font_id==link.font_id).ok_or("target")?;
        assert_ne!(d.declared.id,last);
    }Ok(())})?;Ok(())
}
#[test]
fn canonical_request_digest_is_order_independent_and_source_bound()->R {
    let original=base()?;let mut m=all_mappings(original)?;
    let a=candidate(original,&m,Limits::default())?;m.reverse();let b=candidate(original,&m,Limits::default())?;
    assert_eq!(a.receipt().canonical_mapping_sha256,b.receipt().canonical_mapping_sha256);
    let changed=mutation::change_attribute(original,"Contents/header.xml","font","face","P09-OTHER-SOURCE")?;
    let c=candidate(&changed,&m,Limits::default())?;
    assert_ne!(a.receipt().canonical_mapping_sha256,c.receipt().canonical_mapping_sha256);Ok(())
}
#[test]
fn embedded_declarations_and_binary_reference_remain_exact_without_activation()->R {
    let original=mutation::change_attribute(base()?,"Contents/header.xml","font","isEmbedded","1")?;
    let original=mutation::mutate_part(&original,"Contents/header.xml",|text|{
        let xml=PreservingXmlDocument::parse(text.as_bytes())?;
        let node=xml.elements().iter().find(|n|n.name().local_name()=="font").ok_or("font")?;
        let mut t=text.to_owned();t.insert_str(node.start_name_span().end()," binaryItemIDRef=\"DECLARED-ONLY\"");Ok(t)
    })?;
    let original=embedding_v1::attach_binary_resource(&original)?;
    let mappings=all_mappings(&original)?;let c=candidate(&original,&mappings,Limits::default())?;
    assert_preserved(&original,&bytes(&c)?)?;
    assert!(c.receipt().font_definitions_embedding_substitutes_and_type_info_preserved);Ok(())
}
#[test]
fn stale_original_bytes_are_rejected_without_rebinding()->R {
    let original=base()?;let changed=mutation::change_attribute(original,"Contents/header.xml","font","face","OTHER")?;
    with_fonts(original,|f|{let m=mapping(f,L::Hangul)?;
        assert_eq!(f.lower_reference_replacement_candidate(&changed,&[m],Limits::default(),WriterLimits::default()).unwrap_err(),E::Source);Ok(())})?;Ok(())
}
#[test]
fn missing_source_and_target_declarations_rejected()->R {
    let original=base()?;with_fonts(original,|f|{let mut m=mapping(f,L::Hangul)?;
        for from in [true,false]{if from{m.from_native_id=u32::MAX;}else{m=mapping(f,L::Hangul)?;m.to_native_id=u32::MAX;}
            assert_eq!(f.lower_reference_replacement_candidate(original,&[m],Limits::default(),WriterLimits::default()).unwrap_err(),E::Mapping);}
        Ok(())})?;Ok(())
}
#[test]
fn duplicate_and_conflicting_source_mappings_rejected()->R {
    let original=base()?;with_fonts(original,|f|{let m=mapping(f,L::Hangul)?;
        for target in [m.to_native_id,spare(f,m.language)?]{let second=M{to_native_id:target,..m};
            assert_eq!(f.lower_reference_replacement_candidate(original,&[m,second],Limits::default(),WriterLimits::default()).unwrap_err(),E::Mapping);}
        Ok(())})?;Ok(())
}
#[test]
fn explicit_noop_and_unreferenced_source_have_distinct_errors()->R {
    let original=base()?;with_fonts(original,|f|{let m=mapping(f,L::Hangul)?;
        let noop=M{to_native_id:m.from_native_id,..m};let unused=M{from_native_id:spare(f,m.language)?,..m};
        assert_eq!(f.lower_reference_replacement_candidate(original,&[noop],Limits::default(),WriterLimits::default()).unwrap_err(),E::NoChange);
        assert_eq!(f.lower_reference_replacement_candidate(original,&[unused],Limits::default(),WriterLimits::default()).unwrap_err(),E::NoMatches);Ok(())})?;Ok(())
}
#[test]
fn invalid_request_and_hard_mapping_limits_rejected_before_source_work()->R {
    let original=base()?;with_fonts(original,|f|{let m=mapping(f,L::Hangul)?;
        for limits in [Limits{maximum_mappings:0,..Limits::default()},Limits{maximum_mappings:129,..Limits::default()},
            Limits{maximum_reference_changes:0,..Limits::default()},Limits{maximum_reference_changes:4097,..Limits::default()}]{
            assert_eq!(f.lower_reference_replacement_candidate(&[],&[m],limits,WriterLimits::default()).unwrap_err(),E::Limit);}
        for mappings in [vec![],vec![m;129]]{assert_eq!(f.lower_reference_replacement_candidate(&[],&mappings,Limits::default(),WriterLimits::default()).unwrap_err(),E::Limit);}Ok(())})?;Ok(())
}
#[test]
fn reference_change_limit_rejects_whole_batch_instead_of_partial_candidate()->R {
    let original=base()?;with_fonts(original,|f|{let m=all_mappings(original)?;
        assert_eq!(f.lower_reference_replacement_candidate(original,&m,Limits{maximum_reference_changes:1,..Limits::default()},WriterLimits::default()).unwrap_err(),E::Limit);Ok(())})?;Ok(())
}
#[test]
fn observed_document_security_signal_rejects_global_reference_edit()->R {
    let original=mutation::mutate_part(base()?,"Contents/header.xml",|text|{
        let xml=PreservingXmlDocument::parse(text.as_bytes())?;let offset=xml.elements()[xml.root_element()].start_name_span().end();
        let mut t=text.to_owned();t.insert_str(offset," password=\"0\"");Ok(t)
    })?;
    with_fonts(&original,|f|{let m=mapping(f,L::Hangul)?;
        assert_eq!(f.lower_reference_replacement_candidate(&original,&[m],Limits::default(),WriterLimits::default()).unwrap_err(),E::Protection);Ok(())})?;Ok(())
}
#[test]
fn receipt_and_debug_do_not_expose_font_names_or_grant_authority()->R {
    let original=base()?;let c=candidate(original,&all_mappings(original)?,Limits::default())?;
    let receipt=serde_json::to_string(c.receipt())?;
    assert!(!receipt.contains("P09-FONT-"));assert!(!format!("{c:?}").contains("P09-FONT-"));
    assert!(!c.receipt().search_scope_name_matching_platform_fallback_or_execution_qualified);
    assert!(!c.receipt().full_protection_native_or_service_authority);Ok(())
}
#[test]
fn output_reimports_and_reapplying_original_mapping_is_no_matches()->R {
    let original=base()?;let m=all_mappings(original)?;let output=bytes(&candidate(original,&m,Limits::default())?)?;
    with_fonts(&output,|f|{assert_eq!(f.lower_reference_replacement_candidate(&output,&m,Limits::default(),WriterLimits::default()).unwrap_err(),E::NoMatches);Ok(())})?;Ok(())
}
#[path="support/font_reference_embedding.rs"] mod embedding_v1;
