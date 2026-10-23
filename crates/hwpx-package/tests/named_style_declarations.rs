//! Original named declarations/resources only. No named CHAR body interpretation or mutations.
use hwpx_package::{PreservingXmlDocument,document_import::fields::{ImportedDocumentFields,semantics::{ImportedDocumentFieldSemantics,
    catalog::{ImportedDocumentCatalog,ImportedCatalogKind as CatalogKind,named_styles::{SourceNamedStyleNameQuery as Query,SourceNamedStyleKind as Kind,
        SourceNamedStyleNameAxis as Axis,SourceNamedStyleNameLimits as Limits,SourceNamedStyleNameError as E,SourceNamedStyleNameResolution as Resolution}}}}};
use std::error::Error;
use sha2::{Digest as _,Sha256};
#[path="support/document_import_field_fixture.rs"]#[allow(dead_code)]mod base;
#[path="support/search_definition_fixture.rs"]#[allow(dead_code)]mod fixture;
#[path="support/document_import_catalog_fixture.rs"]#[allow(dead_code)]mod archive;
type R=Result<(),Box<dyn Error>>;
fn package()->Result<Vec<u8>,Box<dyn Error>>{
    let raw=fixture::package("<hp:p id='1' styleIDRef='0' paraPrIDRef='0'><hp:run charPrIDRef='0'><hp:t>PRIVATE-BODY</hp:t></hp:run></hp:p>")?;
    archive::mutate_part(&raw,"Contents/header.xml",|text|{
        let xml=PreservingXmlDocument::parse(text.as_bytes())?;let mut edits=Vec::new();
        for n in xml.elements().iter().filter(|n|n.name().local_name()=="style"){
            let id=n.attributes().iter().find(|a|a.name().local_name()=="id").map(|a|&text[a.value_span().start()..a.value_span().end()]);
            let(kind,native,english)=match id{Some("0")=>("PARA","원본 문단 A","SRC First"),Some("1")=>("PARA","원본 문단 B","SRC Second"),Some("2")=>("PARA","대상 문단","DST"),
                Some("12")=>("CHAR","원본 문자 A","SRC First"),Some("13")=>("CHAR","원본 문자 B","SRC Second"),Some("14")=>("CHAR","대상 문자","DST"),_=>continue};
            for a in n.attributes(){let value=match a.name().local_name(){"type"=>Some(kind),"name"=>Some(native),"engName"=>Some(english),_=>None};
                if let Some(value)=value{edits.push((a.value_span().start(),a.value_span().end(),value));}}
        }edits.sort_by_key(|e|e.0);let mut out=text.to_owned();for(a,b,v)in edits.into_iter().rev(){out.replace_range(a..b,v);}Ok(out)
    })
}
fn attr(bytes:&[u8],id:u32,key:&str,value:&str)->Result<Vec<u8>,Box<dyn Error>>{
    archive::mutate_part(bytes,"Contents/header.xml",|text|{let xml=PreservingXmlDocument::parse(text.as_bytes())?;let id=id.to_string();
        let n=xml.elements().iter().find(|n|n.name().local_name()=="style"&&n.attributes().iter().any(|a|a.name().local_name()=="id"&&&text[a.value_span().start()..a.value_span().end()]==id)).ok_or("style")?;
        let a=n.attributes().iter().find(|a|a.name().local_name()==key).ok_or("attribute")?;let mut out=text.to_owned();out.replace_range(a.value_span().start()..a.value_span().end(),value);Ok(out)})
}
fn with_catalog<T>(bytes:&[u8],f:impl FnOnce(&ImportedDocumentCatalog<'_, '_, '_>)->T)->Result<T,Box<dyn Error>>{
    let forms=base::forms(bytes,"named-style-declarations")?;let fields=ImportedDocumentFields::import(&forms)?;let meanings=ImportedDocumentFieldSemantics::import(&fields)?;let catalog=ImportedDocumentCatalog::import(&meanings)?;Ok(f(&catalog))
}
fn q()->Query<'static>{Query{query:"SRC",replacement:"DST",regex:false,case_sensitive:true,whole_word:false,kind:Kind::Character,name_axis:Axis::EnglishName}}
fn resolve(bytes:&[u8],q:Query<'_>,limits:Limits)->Result<Resolution,Box<dyn Error>>{Ok(with_catalog(bytes,|c|c.resolve_named_style_replacements(q,limits))??)}
#[test]
fn character_style_ids_are_not_character_property_ids()->R{
    let out=resolve(&package()?,q(),Default::default())?;let from=out.from_declarations();assert_eq!(from.iter().map(|d|d.native_style_id).collect::<Vec<_>>(),vec![12,13]);
    assert_eq!(from.iter().map(|d|d.character_property.native_id).collect::<Vec<_>>(),vec![1,2]);assert_eq!(out.target_declaration().native_style_id,14);assert_eq!(out.target_declaration().character_property.native_id,3);
    assert!(from.iter().all(|d|d.native_style_id!=d.character_property.native_id));Ok(())
}
#[test]
fn paragraph_kind_is_explicit_even_when_same_names_exist_on_character_styles()->R{
    let out=resolve(&package()?,Query{kind:Kind::Paragraph,..q()},Default::default())?;
    assert_eq!(out.from_declarations().iter().map(|d|d.native_style_id).collect::<Vec<_>>(),vec![0,1]);assert_eq!(out.target_declaration().native_style_id,2);assert_eq!(out.receipt().kind,Kind::Paragraph);Ok(())
}
#[test]
fn target_in_other_kind_is_not_a_fallback_or_ambiguity()->R{
    let bytes=attr(&package()?,14,"engName","CHAR-TARGET")?;
    assert!(matches!(with_catalog(&bytes,|c|c.resolve_named_style_replacements(q(),Default::default()))?,Err(E::MissingTarget)));
    let out=resolve(&bytes,Query{replacement:"CHAR-TARGET",..q()},Default::default())?;assert_eq!(out.target_declaration().native_style_id,14);Ok(())
}
#[test]
fn native_and_english_name_axes_do_not_cross_match_or_infer_aliases()->R{
    let bytes=package()?;let query=Query{query:"원본 문자 A",replacement:"대상 문자",name_axis:Axis::NativeName,..q()};let out=resolve(&bytes,query,Default::default())?;
    assert_eq!(out.from_declarations()[0].native_style_id,12);assert!(matches!(with_catalog(&bytes,|c|c.resolve_named_style_replacements(Query{name_axis:Axis::EnglishName,..query},Default::default()))?,Err(E::NoMatches)));Ok(())
}
#[test]
fn regex_case_and_whole_word_match_original_decoded_names()->R{
    let bytes=package()?;for query in [Query{query:"src",case_sensitive:false,..q()},Query{query:r"^SRC (First|Second)$",regex:true,..q()},Query{query:"SRC",whole_word:true,..q()}]{assert_eq!(resolve(&bytes,query,Default::default())?.from_declarations().len(),2);}
    assert!(matches!(with_catalog(&bytes,|c|c.resolve_named_style_replacements(Query{query:"SR",whole_word:true,..q()},Default::default()))?,Err(E::NoMatches)));Ok(())
}
#[test]
fn exact_target_is_not_a_substring_or_raw_property_name()->R{
    let bytes=package()?;for replacement in ["DS","1","not declared"]{assert!(matches!(with_catalog(&bytes,|c|c.resolve_named_style_replacements(Query{replacement,..q()},Default::default()))?,Err(E::MissingTarget)));}
    assert!(matches!(with_catalog(&bytes,|c|c.resolve_named_style_replacements(Query{query:"DST",..q()},Default::default()))?,Err(E::NoChange)));Ok(())
}
#[test]
fn duplicate_target_in_same_kind_is_rejected_not_first_selected()->R{
    let bytes=attr(&package()?,13,"engName","DST")?;assert!(matches!(with_catalog(&bytes,|c|c.resolve_named_style_replacements(q(),Default::default()))?,Err(E::AmbiguousTarget)));Ok(())
}
#[test]
fn escaped_names_are_decoded_once_and_target_is_not_a_template()->R{
    let bytes=attr(&attr(&package()?,12,"engName","SRC &amp; One")?,14,"engName","DST &amp; $1")?;
    let out=resolve(&bytes,Query{query:"SRC & One",replacement:"DST & $1",..q()},Default::default())?;assert_eq!(out.from_declarations()[0].native_style_id,12);assert_eq!(out.target_declaration().native_style_id,14);Ok(())
}
#[test]
fn empty_control_malformed_and_zero_width_patterns_reject()->R{
    let bytes=package()?;for query in [Query{query:"",..q()},Query{replacement:"",..q()},Query{query:"SRC\n",..q()},Query{query:"[",regex:true,..q()},Query{query:"^",regex:true,..q()}]{
        assert!(matches!(with_catalog(&bytes,|c|c.resolve_named_style_replacements(query,Default::default()))?,Err(E::Pattern)));}Ok(())
}
#[test]
fn validated_limits_cannot_be_zero_or_exceed_fixed_ceilings()->R{
    for args in [(0,4096,1024,4096),(129,4096,1024,4096),(128,0,1024,4096),(128,4097,1024,4096),(128,4096,0,4096),(128,4096,1024*1024+1,4096),(128,4096,1024,0),(128,4096,1024,4*1024*1024+1)]{
        assert!(matches!(Limits::new(args.0,args.1,args.2,args.3),Err(E::Limit)));}Ok(())
}
#[test]
fn mapping_query_and_regex_budgets_fail_without_partial_resolution()->R{
    let bytes=package()?;let mappings=Limits::new(1,4096,1024*1024,4*1024*1024)?;let query=Limits::new(128,1,1024,4096)?;let regex=Limits::new(128,4096,1,4096)?;
    assert!(matches!(with_catalog(&bytes,|c|c.resolve_named_style_replacements(q(),mappings))?,Err(E::Limit)));
    assert!(matches!(with_catalog(&bytes,|c|c.resolve_named_style_replacements(q(),query))?,Err(E::Limit)));
    assert!(matches!(with_catalog(&bytes,|c|c.resolve_named_style_replacements(Query{query:"(?:A|B){1000}",regex:true,..q()},regex))?,Err(E::Pattern)));Ok(())
}
#[test]
fn entire_metadata_exact_byte_limit_and_one_byte_less_are_enforced()->R{
    let bytes=package()?;let baseline=resolve(&bytes,q(),Default::default())?;let count=baseline.canonical_json()?.len();
    let exact=resolve(&bytes,q(),Limits::new(128,4096,1024*1024,count)?)?;assert_eq!(exact.canonical_json()?.len(),count);
    let smaller=Limits::new(128,4096,1024*1024,count-1)?;assert!(matches!(with_catalog(&bytes,|c|c.resolve_named_style_replacements(q(),smaller))?,Err(E::Limit)));Ok(())
}
#[test]
fn shared_character_properties_do_not_merge_distinct_named_style_identities()->R{
    let bytes=attr(&package()?,13,"charPrIDRef","1")?;let out=resolve(&bytes,q(),Default::default())?;let from=out.from_declarations();assert_eq!(from.len(),2);assert_ne!(from[0].native_style_id,from[1].native_style_id);
    assert_eq!(from[0].character_property,from[1].character_property);assert_ne!(from[0].source_anchor,from[1].source_anchor);Ok(())
}
#[test]
fn next_style_is_preserved_relationship_not_based_on_or_inherited_resources()->R{
    let bytes=attr(&package()?,14,"nextStyleIDRef","12")?;let out=resolve(&bytes,q(),Default::default())?;assert_eq!(out.target_declaration().next_named_style.native_id,12);assert_eq!(out.target_declaration().character_property.native_id,3);
    assert_eq!(out.from_declarations()[0].next_named_style.native_id,0);Ok(())
}
#[test]
fn dangling_declared_resource_is_rejected_by_original_catalog_admission()->R{
    for(key,value)in [("charPrIDRef","999"),("paraPrIDRef","999"),("nextStyleIDRef","999")]{let bytes=attr(&package()?,12,key,value)?;assert!(with_catalog(&bytes,|c|c.resolve_named_style_replacements(q(),Default::default())).is_err());}Ok(())
}
#[test]
fn query_axis_and_original_source_bind_receipts_without_leaking_names_or_body()->R{
    let bytes=package()?;let a=resolve(&bytes,q(),Default::default())?;let b=resolve(&bytes,Query{query:"SRC First",..q()},Default::default())?;assert_ne!(a.receipt().request_sha256,b.receipt().request_sha256);
    let other=archive::mutate_part(&bytes,"Contents/section0.xml",|t|Ok(t.replace("PRIVATE-BODY","DIFFERENT-BODY")))?;let c=resolve(&other,q(),Default::default())?;
    assert_ne!(a.receipt().source_package_sha256,c.receipt().source_package_sha256);assert_ne!(a.receipt().request_sha256,c.receipt().request_sha256);
    for text in [format!("{:?}{a:?}{:?}",q(),a.receipt()),String::from_utf8(a.canonical_json()?)?]{assert!(!text.contains("PRIVATE-")&&!text.contains("SRC")&&!text.contains("DST")&&!text.contains("원본"));}Ok(())
}
#[test]
fn declaration_resolution_never_claims_body_occurrences_application_or_execution()->R{
    let bytes=package()?;let before: [u8;32]=Sha256::digest(&bytes).into();let out=resolve(&bytes,q(),Default::default())?;let receipt=out.receipt();assert!(receipt.all_original_declaration_resources_bound);
    assert!(!receipt.body_occurrences_or_target_semantics_qualified&&!receipt.current_access_execution_or_publication_authority);assert_eq!(receipt.changed_mappings,2);assert_eq!(receipt.source_package_sha256,before);assert_eq!(<[u8;32]>::from(Sha256::digest(&bytes)),before);Ok(())
}
#[test]
fn every_returned_resource_anchor_matches_original_typed_catalog_and_source_remains_verified()->R{
    let bytes=package()?;with_catalog(&bytes,|catalog|->R{
        let out=catalog.resolve_named_style_replacements(q(),Default::default())?;
        for d in out.from_declarations().iter().chain(std::iter::once(out.target_declaration())){
            for(kind,id,anchor)in [(CatalogKind::NamedStyle,d.native_style_id,&d.source_anchor),(CatalogKind::CharacterProperty,d.character_property.native_id,&d.character_property.source_anchor),
                (CatalogKind::ParagraphProperty,d.paragraph_property.native_id,&d.paragraph_property.source_anchor),(CatalogKind::NamedStyle,d.next_named_style.native_id,&d.next_named_style.source_anchor)]{
                let original=catalog.definitions().iter().find(|v|v.kind==kind&&v.native_id==id).ok_or("original resource")?;assert_eq!(&original.source_anchor,anchor);}}
        assert_eq!(catalog.verify_source(&bytes)?,*catalog.receipt());Ok(())
    })??;Ok(())
}
// Independent private hash input and public response budget boundary begins.
#[test]
fn long_valid_query_binding_has_separate_bound_from_exact_public_response_bytes()->R{
    let bytes=package()?;let pattern=format!("(?:{}|SRC)","Q".repeat(4000));let query=Query{query:&pattern,regex:true,..q()};
    let baseline=resolve(&bytes,query,Default::default())?;let length=baseline.canonical_json()?.len();
    let exact=resolve(&bytes,query,Limits::new(128,4096,1024*1024,length)?)?;assert_eq!(exact.canonical_json()?,baseline.canonical_json()?);
    let small=Limits::new(128,4096,1024*1024,length-1)?;assert!(matches!(with_catalog(&bytes,|c|c.resolve_named_style_replacements(query,small))?,Err(E::Limit)));Ok(())
}
// Independent private hash input and public response budget boundary ends.
