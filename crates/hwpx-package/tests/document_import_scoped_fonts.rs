use hwpx_package::{PreservingXmlDocument,WriterLimits,document_import::{forms::ImportedDocumentForms,
    fields::{ImportedDocumentFields,semantics::{ImportedDocumentFieldSemantics,catalog::{ImportedDocumentCatalog,fonts::{ImportedDocumentFonts,ImportedFontLanguage as L,
        names::{FontNameReplacementQuery as Query,FontNameResolutionError as NameError}}}}},
    search::{SourceSearchLimits,SourceSearchLimitConfig,selector::{SourceIndexScopeSelector as Scope,SourceIndexBoundary as Boundary},
        reviews::SourceReviewTextPolicy as Policy,replacement::{SourceLiteralReplacementError as Compile,
            atoms::styles::fonts::{SourceFontStyleAxis as Axis,SourceFontReplacementError as E,SourceFontReplacementCandidate as Candidate}}}}};
use std::error::Error;
#[path="support/search_definition_fixture.rs"]#[allow(dead_code)]mod definition;
#[path="support/document_import_fonts_fixture.rs"]#[allow(dead_code)]mod original;
#[path="support/document_import_catalog_fixture.rs"]#[allow(dead_code)]mod archive;
type R=Result<(),Box<dyn Error>>;
const LANGS:[L;7]=[L::Hangul,L::Latin,L::Hanja,L::Japanese,L::Other,L::Symbol,L::User];
const TARGET:&str="P09-TARGET-FONT";
fn package(body:&str)->Result<Vec<u8>,Box<dyn Error>>{
    let bytes=definition::package(body)?;
    archive::mutate_part(&bytes,"Contents/header.xml",|text|{
        let xml=PreservingXmlDocument::parse(text.as_bytes())?;let mut edits=Vec::new();
        for(i,group)in xml.elements().iter().enumerate().filter(|(_,n)|n.name().local_name()=="fontface"){
            let children:Vec<_>=xml.elements().iter().filter(|n|n.parent()==Some(i)&&n.name().local_name()=="font").collect();
            let first=children.first().ok_or("font")?;let outer=first.outer_span().ok_or("font span")?;
            let mut copy=text[outer.start()..outer.end()].to_owned();let mut attrs=Vec::new();
            for a in first.attributes(){let value=match a.name().local_name(){"id"=>Some(children.len().to_string()),"face"=>Some(TARGET.to_owned()),_=>None};
                if let Some(value)=value{let s=a.value_span();attrs.push((s.start()-outer.start(),s.end()-outer.start(),value));}}
            attrs.sort_by_key(|e|e.0);for(a,b,v)in attrs.into_iter().rev(){copy.replace_range(a..b,&v);}
            let s=group.attributes().iter().find(|a|a.name().local_name()=="fontCnt").ok_or("count")?.value_span();
            edits.push((s.start(),s.end(),(children.len()+1).to_string()));
            let at=group.end_tag_span().ok_or("group end")?.start();edits.push((at,at,copy));
        }
        edits.sort_by_key(|e|e.0);let mut result=text.to_owned();for(a,b,v)in edits.into_iter().rev(){result.replace_range(a..b,&v);}Ok(result)
    })
}
fn plain(text:&str)->Result<Vec<u8>,Box<dyn Error>>{package(&format!("<hp:p id='1' paraPrIDRef='0' styleIDRef='0'><hp:run charPrIDRef='0'><hp:t>{text}</hp:t></hp:run></hp:p>"))}
fn with_fonts<T>(raw:&[u8],f:impl FnOnce(&ImportedDocumentFonts<'_, '_, '_, '_>)->Result<T,Box<dyn Error>>)->Result<T,Box<dyn Error>>{
    let forms=original::forms(raw,"scoped-font")?;let fields=ImportedDocumentFields::import(&forms)?;
    let meanings=ImportedDocumentFieldSemantics::import(&fields)?;let catalog=ImportedDocumentCatalog::import(&meanings)?;let fonts=ImportedDocumentFonts::import(&catalog)?;f(&fonts)
}
fn source_name(raw:&[u8])->Result<String,Box<dyn Error>>{with_fonts(raw,|fonts|Ok(fonts.definitions().iter().find(|d|d.language==L::Hangul&&d.declared.id==0).ok_or("source font")?.declared.face.clone()))}
fn style_name(raw:&[u8],style:u32)->Result<String,Box<dyn Error>>{
    let header=archive::read_part(raw,"Contents/header.xml")?;
    let catalog=hwpx_package::CharacterStyleCatalogReader::read(&header,Default::default())?;
    let native=catalog.styles.get(style as usize).filter(|s|s.id==style).ok_or("fixture character property")?.font_refs.hangul;
    with_fonts(raw,|fonts|Ok(fonts.definitions().iter().find(|d|d.language==L::Hangul&&d.declared.id==native).ok_or("actual style font")?.declared.face.clone()))
}
fn query(name:&str)->Query<'_>{Query{query:name,replacement:TARGET,regex:false,case_sensitive:true,whole_word:false,languages:&LANGS}}
fn policy()->Policy{Policy{include_hidden_explanations:false,include_memo_bodies:false}}
fn lower(forms:&ImportedDocumentForms,raw:&[u8],scope:Scope<'_>,axis:Axis)->Result<Candidate,Box<dyn Error>>{
    let values=scalar_styles(raw)?;let first=values.first().ok_or("fixture text")?;
    let style=match axis{Axis::RunProperty=>first.1,Axis::TextStyle=>first.2}.ok_or("fixture explicit axis")?;
    Ok(forms.lower_scoped_font_candidate(raw,query(&style_name(raw,style)?),scope,policy(),axis,Default::default(),Default::default())?)
}
fn bytes(out:&Candidate)->Result<Vec<u8>,Box<dyn Error>>{Ok(out.with_verified_bytes(<[u8]>::to_vec)?)}
fn scalar_styles(raw:&[u8])->Result<Vec<(char,Option<u32>,Option<u32>)>,Box<dyn Error>>{
    let raw=String::from_utf8(archive::read_part(raw,"Contents/section0.xml")?)?;let xml=PreservingXmlDocument::parse(raw.as_bytes())?;let mut values=Vec::new();
    for t in xml.tokens(){if !matches!(t.kind(),hwpx_package::XmlTokenKind::Text|hwpx_package::XmlTokenKind::Whitespace|hwpx_package::XmlTokenKind::Reference){continue;}
        let Some(i)=t.element_index()else{continue};let text=&xml.elements()[i];if text.name().local_name()!="t"{continue;}
        let run=&xml.elements()[text.parent().ok_or("run")?];let attr=|node:&hwpx_package::XmlElementToken,key:&str|->Result<Option<u32>,Box<dyn Error>>{
            node.attributes().iter().find(|a|a.name().local_name()==key).map(|a|{let s=a.value_span();Ok(raw[s.start()..s.end()].parse()?)}).transpose()
        };
        let run=attr(run,"charPrIDRef")?;let text=attr(text,"charStyleIDRef")?;let s=t.span();
        values.extend(quick_xml::escape::unescape(&raw[s.start()..s.end()])?.chars().map(|c|(c,run,text)));
    }Ok(values)
}
fn selection(forms:&ImportedDocumentForms,raw:&[u8],block:usize,a:usize,b:usize)->Result<([u8;32],Boundary,Boundary),Box<dyn Error>>{
    let inventory=forms.source_review_scope_index(raw,Default::default())?.scope_inventory()?;let item=&inventory.inventory.blocks[block];
    Ok((inventory.inventory.index.index_sha256,Boundary{paragraph_handle:item.paragraph_handle.clone(),block_index:block,normalized_scalar:a},
        Boundary{paragraph_handle:item.paragraph_handle.clone(),block_index:block,normalized_scalar:b}))
}
#[path="support/scoped_font_filter.rs"]mod filtered;
mod scoped{use super::*;
#[test]
fn partial_run_clones_shared_property_and_preserves_nonselected_scalars_and_entities()->R{
    let raw=plain("A&#x1F600;B&amp;C")?;let forms=original::forms(&raw,"scoped-font")?;
    let(hash,a,b)=selection(&forms,&raw,0,1,3)?;let out=lower(&forms,&raw,Scope::Selection{index_sha256:hash,start:&a,end:&b},Axis::RunProperty)?;
    let output=bytes(&out)?;let values=scalar_styles(&output)?;
    assert_eq!(values.iter().map(|v|v.0).collect::<String>(),"A😀B&C");
    assert_eq!(values[0].1,Some(0));assert_ne!(values[1].1,Some(0));assert_eq!(values[1].1,values[2].1);assert_eq!(values[3].1,Some(0));
    assert_eq!(out.receipt().changed_source_scalars,2);assert_eq!(out.receipt().cloned_character_properties,1);
    let before=with_fonts(&raw,|f|Ok(f.definitions().iter().map(|d|d.declared.clone()).collect::<Vec<_>>()))?;
    let after=with_fonts(&output,|f|Ok(f.definitions().iter().map(|d|d.declared.clone()).collect::<Vec<_>>()))?;assert_eq!(before,after);Ok(())
}
#[test]
fn two_paragraphs_share_original_style_but_only_selected_node_changes()->R{
    let raw=package("<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>ONE</hp:t></hp:run></hp:p><hp:p id='2'><hp:run charPrIDRef='0'><hp:t>TWO</hp:t></hp:run></hp:p>")?;
    let forms=original::forms(&raw,"scoped-font")?;let inventory=forms.source_review_scope_index(&raw,Default::default())?.scope_inventory()?;
    let node=inventory.inventory.nodes.iter().find(|n|n.source_handle==inventory.inventory.blocks[0].paragraph_handle).ok_or("node")?;
    let out=lower(&forms,&raw,Scope::NodeSet(std::slice::from_ref(&node.node_id)),Axis::RunProperty)?;let values=scalar_styles(&bytes(&out)?)?;
    assert!(values[..3].iter().all(|v|v.1!=Some(0)));assert!(values[3..].iter().all(|v|v.1==Some(0)));Ok(())
}
#[test]
fn explicit_text_style_splits_text_without_changing_run_or_unselected_text_axis()->R{
    let raw=package("<hp:p id='1'><hp:run charPrIDRef='0'><hp:t charStyleIDRef='1'>ABCD</hp:t></hp:run></hp:p>")?;
    let forms=original::forms(&raw,"scoped-font")?;let(hash,a,b)=selection(&forms,&raw,0,1,3)?;
    let out=lower(&forms,&raw,Scope::Selection{index_sha256:hash,start:&a,end:&b},Axis::TextStyle)?;let values=scalar_styles(&bytes(&out)?)?;
    assert!(values.iter().all(|v|v.1==Some(0)));assert_eq!(values[0].2,Some(1));assert_ne!(values[1].2,Some(1));assert_eq!(values[1].2,values[2].2);assert_eq!(values[3].2,Some(1));Ok(())
}
#[test]
fn document_and_section_scope_apply_once_and_reuse_one_clone_per_original_style()->R{
    let raw=plain("ABCD")?;let forms=original::forms(&raw,"scoped-font")?;let inventory=forms.source_review_scope_index(&raw,Default::default())?.scope_inventory()?;
    for scope in [Scope::Document,Scope::Section(&inventory.inventory.section_ids)]{let out=lower(&forms,&raw,scope,Axis::RunProperty)?;
        assert_eq!(out.receipt().cloned_character_properties,1);assert_eq!(out.receipt().changed_source_scalars,4);}
    Ok(())
}
#[test]
fn selected_nfc_scalar_keeps_all_original_hangul_contributors_and_outside_spelling()->R{
    let raw=plain("X각Y")?;let forms=original::forms(&raw,"scoped-font")?;let(hash,a,b)=selection(&forms,&raw,0,1,2)?;
    let out=lower(&forms,&raw,Scope::Selection{index_sha256:hash,start:&a,end:&b},Axis::RunProperty)?;
    let values=scalar_styles(&bytes(&out)?)?;assert_eq!(values.iter().map(|v|v.0).collect::<String>(),"X각Y");
    assert_eq!(values[0].1,Some(0));assert!(values[1..4].iter().all(|v|v.1!=Some(0)));assert_eq!(values[4].1,Some(0));Ok(())
}
#[test]
fn controls_retain_original_bytes_and_are_not_counted_as_changed_text()->R{
    let tab="<hp:tab width='1' leader='0' type='0'> </hp:tab>";let raw=plain(&format!("A{tab}B<hp:lineBreak> </hp:lineBreak>C"))?;
    let forms=original::forms(&raw,"scoped-font")?;let out=lower(&forms,&raw,Scope::Document,Axis::RunProperty)?;let output=bytes(&out)?;
    let text=String::from_utf8(archive::read_part(&output,"Contents/section0.xml")?)?;assert!(text.contains(tab)&&text.contains("<hp:lineBreak> </hp:lineBreak>"));
    assert_eq!(out.receipt().changed_source_scalars,3);Ok(())
}
#[test]
fn run_axis_rejects_unresolved_text_precedence_instead_of_guessing()->R{
    let raw=package("<hp:p id='1'><hp:run charPrIDRef='0'><hp:t charStyleIDRef='1'>ABC</hp:t></hp:run></hp:p>")?;
    let forms=original::forms(&raw,"scoped-font")?;
    assert!(matches!(forms.lower_scoped_font_candidate(&raw,query(&source_name(&raw)?),Scope::Document,policy(),Axis::RunProperty,Default::default(),Default::default()),Err(E::Compile(Compile::Selection))));Ok(())
}
#[test]
fn missing_requested_text_axis_rejects_without_named_style_or_run_fallback()->R{
    let raw=plain("ABC")?;let forms=original::forms(&raw,"scoped-font")?;
    assert!(matches!(forms.lower_scoped_font_candidate(&raw,query(&source_name(&raw)?),Scope::Document,policy(),Axis::TextStyle,Default::default(),Default::default()),Err(E::Compile(Compile::Selection))));Ok(())
}
#[test]
fn stale_whole_source_and_stale_selector_are_rejected()->R{
    let raw=plain("ABC")?;let forms=original::forms(&raw,"scoped-font")?;let changed=plain("ABD")?;
    assert!(matches!(forms.lower_scoped_font_candidate(&changed,query(&source_name(&raw)?),Scope::Document,policy(),Axis::RunProperty,Default::default(),Default::default()),Err(E::Source)));
    let(_,a,b)=selection(&forms,&raw,0,0,1)?;assert!(lower(&forms,&raw,Scope::Selection{index_sha256:[0;32],start:&a,end:&b},Axis::RunProperty).is_err());Ok(())
}
#[test]
fn finite_scalar_and_writer_limits_never_return_partial_candidates()->R{
    let raw=plain("ABC")?;let forms=original::forms(&raw,"scoped-font")?;
    let limits=SourceSearchLimits::new(SourceSearchLimitConfig{matches:1,..Default::default()})?;
    assert!(matches!(forms.lower_scoped_font_candidate(&raw,query(&style_name(&raw,0)?),Scope::Document,policy(),Axis::RunProperty,limits,Default::default()),Err(E::Compile(Compile::Limit))));
    let writer=WriterLimits::new(hwpx_package::WriterLimitConfig{max_output_bytes:1,..Default::default()})?;
    assert!(matches!(forms.lower_scoped_font_candidate(&raw,query(&style_name(&raw,0)?),Scope::Document,policy(),Axis::RunProperty,Default::default(),writer),Err(E::Compile(Compile::Writer))));Ok(())
}
#[test]
fn names_literal_regex_case_and_explicit_language_sets_are_bounded()->R{
    let raw=plain("ABC")?;with_fonts(&raw,|f|{
        let name=source_name(&raw)?;let exact=f.resolve_name_replacements(query(&name),128)?;assert_eq!(exact.mappings().len(),7);
        let q=Query{query:"p09-target",replacement:&name,case_sensitive:false,languages:&[L::Hangul],..query(&name)};
        assert_eq!(f.resolve_name_replacements(q,128)?.mappings().len(),1);
        let q=Query{query:"P09-.*-FONT",replacement:&name,regex:true,languages:&[L::Latin],..query(&name)};
        assert_eq!(f.resolve_name_replacements(q,128)?.mappings().len(),1);Ok(())
    })?;Ok(())
}
#[test]
fn name_target_absence_noop_and_no_match_are_distinct()->R{
    let raw=plain("ABC")?;with_fonts(&raw,|f|{let name=source_name(&raw)?;
        assert_eq!(f.resolve_name_replacements(Query{replacement:"P09-MISSING",..query(&name)},128).unwrap_err(),NameError::MissingTarget);
        assert_eq!(f.resolve_name_replacements(Query{replacement:&name,..query(&name)},128).unwrap_err(),NameError::NoChange);
        assert_eq!(f.resolve_name_replacements(query("P09-NO-SUCH-SOURCE"),128).unwrap_err(),NameError::NoMatches);Ok(())})?;Ok(())
}
#[test]
fn invalid_patterns_empty_names_duplicate_languages_and_mapping_limits_reject()->R{
    let raw=plain("ABC")?;with_fonts(&raw,|f|{let name=source_name(&raw)?;
        for q in [Query{query:"[",regex:true,..query(&name)},Query{query:"^",regex:true,..query(&name)},Query{query:"",..query(&name)},Query{replacement:"",..query(&name)}]{
            assert!(f.resolve_name_replacements(q,128).is_err());}
        assert_eq!(f.resolve_name_replacements(Query{languages:&[L::Hangul,L::Hangul],..query(&name)},128).unwrap_err(),NameError::Language);
        assert_eq!(f.resolve_name_replacements(query(&name),1).unwrap_err(),NameError::Limit);Ok(())})?;Ok(())
}
#[test]
fn request_binding_changes_with_language_set_and_names_are_not_disclosed()->R{
    let raw=plain("ABC")?;with_fonts(&raw,|f|{let name=source_name(&raw)?;let all=f.resolve_name_replacements(query(&name),128)?;
        let one=f.resolve_name_replacements(Query{languages:&[L::Hangul],..query(&name)},128)?;
        assert_ne!(all.receipt().request_sha256,one.receipt().request_sha256);
        assert!(!serde_json::to_string(all.receipt())?.contains(TARGET));assert!(!format!("{:?}",query(&name)).contains(&name));Ok(())})?;
    let forms=original::forms(&raw,"scoped-font")?;let out=lower(&forms,&raw,Scope::Document,Axis::RunProperty)?;
    assert!(!serde_json::to_string(out.receipt())?.contains(TARGET));assert!(!out.receipt().native_cascade_fallback_visibility_or_service_execution_qualified);
    assert!(!format!("{out:?}").contains(TARGET));Ok(())
}
#[test]
fn duplicate_target_faces_reject_instead_of_choosing_an_arbitrary_declaration()->R{
    let raw=archive::change_attribute(&plain("ABC")?,"Contents/header.xml","font","face",TARGET)?;
    with_fonts(&raw,|fonts|{assert_eq!(fonts.resolve_name_replacements(Query{languages:&[L::Hangul],..query(TARGET)},128).unwrap_err(),NameError::AmbiguousTarget);Ok(())})?;Ok(())
}
#[test]
fn language_order_is_canonical_and_whole_word_name_matching_is_explicit()->R{
    let raw=plain("ABC")?;with_fonts(&raw,|fonts|{let name=source_name(&raw)?;let mut languages=LANGS;languages.reverse();
        let a=fonts.resolve_name_replacements(query(&name),128)?;
        let b=fonts.resolve_name_replacements(Query{languages:&languages,..query(&name)},128)?;
        assert_eq!(a.receipt().request_sha256,b.receipt().request_sha256);
        let q=Query{query:"TARGET",replacement:&name,whole_word:true,languages:&[L::Hangul],..query(&name)};
        assert_eq!(fonts.resolve_name_replacements(q,128)?.mappings().len(),1);
        assert_eq!(fonts.resolve_name_replacements(Query{query:"TARGE",..q},128).unwrap_err(),NameError::NoMatches);Ok(())})?;Ok(())
}
#[test]
fn different_original_properties_get_separate_clones_with_nonfont_effects_preserved()->R{
    let raw=package("<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>A</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t>B</hp:t></hp:run></hp:p>")?;
    let forms=original::forms(&raw,"scoped-font")?;
    let request=Query{query:".+",regex:true,..query(TARGET)};
    let out=forms.lower_scoped_font_candidate(&raw,request,Scope::Document,policy(),Axis::RunProperty,Default::default(),Default::default())?;
    let output=bytes(&out)?;let values=scalar_styles(&output)?;assert_ne!(values[0].1,values[1].1);assert_eq!(out.receipt().cloned_character_properties,2);
    let read=|raw:&[u8]|->Result<hwpx_package::CharacterStyleCatalog,Box<dyn Error>>{
        let header=archive::read_part(raw,"Contents/header.xml")?;
        Ok(hwpx_package::CharacterStyleCatalogReader::read(&header,Default::default())?)
    };
    let before=read(&raw)?;let after=read(&output)?;assert_eq!(&before.styles, &after.styles[..before.styles.len()]);
    for(i,new)in values.iter().enumerate(){let mut expected=before.styles[i].clone();let actual=&after.styles[new.1.ok_or("new style")? as usize];
        expected.id=actual.id;expected.font_refs=actual.font_refs.clone();assert_eq!(&expected,actual);}
    Ok(())
}
#[test]
fn empty_selection_and_unmatched_selected_properties_do_not_publish_a_clone()->R{
    let raw=plain("ABC")?;let forms=original::forms(&raw,"scoped-font")?;let(hash,a,b)=selection(&forms,&raw,0,1,1)?;
    assert!(matches!(forms.lower_scoped_font_candidate(&raw,query(&source_name(&raw)?),Scope::Selection{index_sha256:hash,start:&a,end:&b},policy(),Axis::RunProperty,Default::default(),Default::default()),Err(E::Compile(Compile::NoMatches))));
    assert!(matches!(forms.lower_scoped_font_candidate(&raw,query(&source_name(&raw)?),Scope::Document,policy(),Axis::RunProperty,Default::default(),Default::default()),Err(E::Compile(Compile::NoMatches))));Ok(())
}
#[test]
fn a_verified_reconstruction_cannot_be_rebound_to_another_import_instance()->R{
    let raw=plain("ABC")?;let first=original::forms(&raw,"scoped-font")?;let second=original::forms(&raw,"scoped-font")?;
    let proof=first.reconstruct_source_for_verification(&raw)?;
    assert!(matches!(proof.lower_scoped_font_candidate(&second,query(&source_name(&raw)?),Scope::Document,policy(),Axis::RunProperty,Default::default(),Default::default()),Err(E::Source)));Ok(())
}
#[test]
fn invalid_name_query_rejects_before_importing_fresh_source_or_opening_a_writer()->R{
    let raw=plain("ABC")?;let forms=original::forms(&raw,"scoped-font")?;
    assert!(matches!(forms.lower_scoped_font_candidate(&[],query(""),Scope::Document,policy(),Axis::RunProperty,Default::default(),Default::default()),Err(E::Name(NameError::Pattern))));Ok(())
}
}
