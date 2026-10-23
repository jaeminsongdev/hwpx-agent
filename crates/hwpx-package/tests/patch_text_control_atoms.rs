use hwpx_package::{BoundedZipReader,IdRuleProfile,PackageGraph,PackagePath,PatchIntent,PatchError,PatchLimits,PatchLimitConfig,
    LeafTextRangeReplacement,TextAtomRangeReplacement,TextAtom,TextControlAtomReplacement as Replacement,TextControlKind as Kind,
    WhitespaceAtomRangeReplacement as WRange,WhitespaceOutputAtom as WAtom,WhitespaceText,
    PreservationRuleProfile,PreservingPatchEngine,PreservingWriter,PreservingXmlDocument,XmlElementSelector};
use sha2::{Digest as _,Sha256};
use std::{error::Error,io::Cursor};
#[allow(dead_code)] #[path="support/search_definition_fixture.rs"] mod fixture;
type TestResult=Result<(),Box<dyn Error>>;
type Spec=(usize,Vec<Replacement>);
const TAB:&str="<hp:tab width='1' leader='0' type='0'/>";
fn text(value:&str)->TextAtom{TextAtom::Text(value.to_owned())}
fn r(atom:u32,kind:Kind,output:Vec<TextAtom>)->Result<Replacement,Box<dyn Error>>{Ok(Replacement::new(atom,kind,output)?)}
fn package(leaf:&str)->Result<Vec<u8>,Box<dyn Error>>{fixture::package(&format!("<hp:p id='1' paraPrIDRef='0' styleIDRef='0'><hp:run charPrIDRef='1'>{leaf}</hp:run><hp:run charPrIDRef='0'><hp:t>  </hp:t><hp:t>A</hp:t><hp:t>B</hp:t></hp:run></hp:p>"))}
fn section(bytes:&[u8])->Result<String,Box<dyn Error>>{let mut reader=BoundedZipReader::open(Cursor::new(bytes),Default::default())?;
    let i=reader.entries().iter().position(|p|p.path.as_str()=="Contents/section0.xml").ok_or("section")?;Ok(String::from_utf8(reader.read_entry(i)?)?)}
fn run(bytes:&[u8],limits:PatchLimits,make:impl FnOnce(&PackagePath,&PreservingXmlDocument,&[usize])->Result<Vec<PatchIntent>,Box<dyn Error>>)->Result<Vec<u8>,Box<dyn Error>>{
    let mut reader=BoundedZipReader::open(Cursor::new(bytes),Default::default())?;let graph=PackageGraph::build(&mut reader,Default::default())?;
    let i=reader.entries().iter().position(|p|p.path.as_str()=="Contents/section0.xml").ok_or("section")?;let path=reader.entries()[i].path.clone();
    let raw=reader.read_entry(i)?;let xml=PreservingXmlDocument::parse(&raw)?;let leaves:Vec<_>=xml.elements().iter().enumerate().filter(|(_,n)|n.name().local_name()=="t").map(|(i,_)|i).collect();
    let intents=make(&path,&xml,&leaves)?;
    let patch=PreservingPatchEngine::apply_with_limits_and_preservation_profile(&mut reader,&graph,Default::default(),IdRuleProfile::hwpml_2011_text_style_v9(),Default::default(),limits,PreservationRuleProfile::Hangul2020PreviewTextV2,&intents)?;
    let artifact=PreservingWriter::build(&patch,Default::default(),Default::default(),Default::default(),Default::default())?;let out=artifact.with_verified_bytes(<[u8]>::to_vec)?;
    let mut after=BoundedZipReader::open(Cursor::new(&out),Default::default())?;assert_eq!(reader.entries().len(),after.entries().len());
    for i in 0..reader.entries().len(){let p=reader.entries()[i].path.clone();if p==path{continue;}let j=after.entries().iter().position(|e|e.path==p).ok_or("part")?;assert_eq!(reader.read_entry(i)?,after.read_entry(j)?);}Ok(out)
}
fn apply(bytes:&[u8],specs:&[Spec],limits:PatchLimits,legacy:u8)->Result<Vec<u8>,Box<dyn Error>>{
    run(bytes,limits,|path,xml,leaves|{let bind=|leaf:usize|XmlElementSelector::bind(path,xml,leaves[leaf]);let mut intents=Vec::new();
        for(leaf,replacements)in specs{intents.push(PatchIntent::ReplaceTextControlAtoms{target:bind(*leaf)?,replacements:replacements.clone()});}
        if legacy>0{let output=vec![WAtom::Text(WhitespaceText::new(" ")?)];let output=if legacy==4{vec![output[0].clone(),output[0].clone()]}else{output};
            intents.push(PatchIntent::ReplaceWhitespaceAtomRanges{target:bind(1)?,ranges:vec![WRange::text(0,0,1,output)?]});}
        if legacy==3{intents.push(PatchIntent::ReplaceTextAtomScalarRanges{target:bind(2)?,ranges:vec![TextAtomRangeReplacement::new(0,0,1,"&")?]});
            intents.push(PatchIntent::ReplaceLeafScalarRanges{target:bind(3)?,ranges:vec![LeafTextRangeReplacement::new(0,1,"&")?]});}Ok(intents)})
}
fn rewrite(old:&str,new:&str,replacements:Vec<Replacement>)->TestResult{let raw=package(old)?;let before=Sha256::digest(&raw);let out=apply(&raw,&[(0,replacements)],Default::default(),0)?;
    assert_eq!(section(&out)?,section(&raw)?.replacen(old,new,1));assert_eq!(Sha256::digest(&raw),before);Ok(())}
#[test]
fn control_tab_and_linebreak_become_escaped_arbitrary_unicode_text_not_xml()->TestResult{
    rewrite(&format!("<hp:t charStyleIDRef='1'>&#x1F600;A{TAB}B<hp:lineBreak/>C&#38;</hp:t>"),
        "<hp:t charStyleIDRef='1'>&#x1F600;A한글😀&amp;&lt;hp:tab/&gt;B'\"C&#38;</hp:t>",
        vec![r(1,Kind::Tab,vec![text("한글😀&<hp:tab/>")])?,r(3,Kind::LineBreak,vec![text("'\"")])?])
}
#[test]
fn control_can_expand_to_mixed_typed_text_tab_and_linebreak()->TestResult{
    rewrite(&format!("<hp:t>A{TAB}B</hp:t>"),"<hp:t>AX<hp:tab width=\"4294967295\" leader=\"2\" type=\"1\"/><hp:lineBreak/>YB</hp:t>",
        vec![r(1,Kind::Tab,vec![text("X"),TextAtom::Tab{width:u32::MAX,leader:2,tab_type:1},TextAtom::LineBreak,text("Y")])?])
}
#[test]
fn control_delete_uses_original_ordinals_and_keeps_nonselected_control_lexemes()->TestResult{
    let old=format!("<hp:t><hp:lineBreak/>A{TAB}B<hp:lineBreak> </hp:lineBreak>C</hp:t>");let new=format!("<hp:t>A{TAB}BC</hp:t>");
    rewrite(&old,&new,vec![r(0,Kind::LineBreak,vec![])?,r(4,Kind::LineBreak,vec![]) ?])
}
#[test]
fn control_paired_control_internal_whitespace_changes_only_when_selected()->TestResult{
    rewrite("<hp:t>A<hp:tab type='0' leader='0' width='1'> </hp:tab>B<hp:lineBreak> </hp:lineBreak>C</hp:t>",
        "<hp:t>AQB<hp:lineBreak> </hp:lineBreak>C</hp:t>",vec![r(1,Kind::Tab,vec![text("Q")])?])
}
#[test]
fn control_output_text_rejects_empty_raw_controls_noncharacters_and_oversize()->TestResult{
    for value in["","\t","\n","\r","\u{b}","\u{c}","\u{85}","\0","\u{ffff}"]{assert!(Replacement::new(0,Kind::Tab,vec![text(value)]).is_err());}
    assert!(Replacement::new(0,Kind::Tab,vec![text(&"x".repeat(1024*1024+1))]).is_err());
    assert!(Replacement::new(0,Kind::Tab,vec![TextAtom::LineBreak;4097]).is_err());Ok(())
}
#[test]
fn control_never_deletes_or_replaces_original_text_or_invents_empty_atoms()->TestResult{
    for leaf in["<hp:t>ABC</hp:t>","<hp:t/>","<hp:t></hp:t>"]{let raw=package(leaf)?;assert!(apply(&raw,&[(0,vec![r(0,Kind::Tab,vec![text("X")])?])],Default::default(),0).is_err());}
    let raw=package(&format!("<hp:t>A{TAB}B</hp:t>"))?;let error=apply(&raw,&[(0,vec![r(0,Kind::Tab,vec![]) ?])],Default::default(),0).expect_err("text is not control");
    assert!(matches!(error.downcast_ref::<PatchError>(),Some(PatchError::SelectorKind)));Ok(())
}
#[test]
fn control_expected_kind_missing_ordinal_duplicates_and_reverse_order_reject()->TestResult{
    let raw=package(&format!("<hp:t>A{TAB}B<hp:lineBreak/>C</hp:t>"))?;
    for replacements in[vec![r(1,Kind::LineBreak,vec![]) ?],vec![r(3,Kind::Tab,vec![]) ?],vec![r(10,Kind::Tab,vec![]) ?],
        vec![r(1,Kind::Tab,vec![]) ?,r(1,Kind::Tab,vec![text("X")])?],vec![r(3,Kind::LineBreak,vec![]) ?,r(1,Kind::Tab,vec![]) ?],vec![]]{
        assert!(apply(&raw,&[(0,replacements)],Default::default(),0).is_err());}Ok(())
}
#[test]
fn control_opaque_foreign_malformed_and_unknown_text_children_are_not_skipped()->TestResult{
    for extra in["<hp:titleMark/>","<!--opaque-->","<x:tab xmlns:x='urn:foreign'/>","&#13;"]{
        let raw=package(&format!("<hp:t>A{TAB}{extra}B</hp:t>"))?;assert!(apply(&raw,&[(0,vec![r(1,Kind::Tab,vec![text("X")])?])],Default::default(),0).is_err());}
    for tab in["<hp:tab width='1' leader='0'/>","<hp:tab width='X' leader='0' type='0'/>","<hp:tab width='1' leader='0' type='0' unknown='1'/>"]{
        let raw=package(&format!("<hp:t>{tab}</hp:t>"))?;assert!(apply(&raw,&[(0,vec![r(0,Kind::Tab,vec![]) ?])],Default::default(),0).is_err());}Ok(())
}
#[test]
fn control_namespace_alias_default_and_shadowed_hp_use_original_parent_prefix()->TestResult{
    for(old,new)in[("<q:t xmlns:q='http://www.hancom.co.kr/hwpml/2011/paragraph'>A<q:tab width='1' leader='0' type='0'/>B</q:t>","<q:t xmlns:q='http://www.hancom.co.kr/hwpml/2011/paragraph'>A<q:lineBreak/>B</q:t>"),
        ("<t xmlns='http://www.hancom.co.kr/hwpml/2011/paragraph'>A<tab width='1' leader='0' type='0'/>B</t>","<t xmlns='http://www.hancom.co.kr/hwpml/2011/paragraph'>A<lineBreak/>B</t>"),
        ("<q:t xmlns:q='http://www.hancom.co.kr/hwpml/2011/paragraph' xmlns:hp='urn:shadow'>A<q:tab width='1' leader='0' type='0'/>B</q:t>","<q:t xmlns:q='http://www.hancom.co.kr/hwpml/2011/paragraph' xmlns:hp='urn:shadow'>A<q:lineBreak/>B</q:t>")]{rewrite(old,new,vec![r(1,Kind::Tab,vec![TextAtom::LineBreak])?])?;}Ok(())
}
#[test]
fn control_stale_wrong_namespace_and_nontext_parent_selectors_reject()->TestResult{
    let raw=package(&format!("<hp:t>A{TAB}B</hp:t>"))?;
    for mode in 0..3{assert!(run(&raw,Default::default(),|path,xml,leaves|{
        let target=match mode{0=>{let changed=section(&raw)?.replace("A<","C<");let other=PreservingXmlDocument::parse(changed.as_bytes())?;XmlElementSelector::bind(path,&other,leaves[0])?},
            1=>XmlElementSelector::bind(path,xml,xml.elements()[leaves[0]].parent().ok_or("parent")?)?,_=>XmlElementSelector::bind(path,xml,leaves[0]+1)?};
        Ok(vec![PatchIntent::ReplaceTextControlAtoms{target,replacements:vec![r(1,Kind::Tab,vec![text("X")])?]}])}).is_err());}
    let raw=package("<x:t xmlns:x='urn:wrong'><x:tab/></x:t>")?;assert!(apply(&raw,&[(0,vec![r(0,Kind::Tab,vec![text("X")])?])],Default::default(),0).is_err());Ok(())
}
#[test]
fn control_escaped_unicode_encoded_value_and_fragment_caps_are_exact()->TestResult{
    let raw=package(&format!("<hp:t>A{TAB}B</hp:t>"))?;let spec=vec![(0,vec![r(1,Kind::Tab,vec![text("😀&<>")])?])];let n="😀&amp;&lt;&gt;".len();
    assert!(apply(&raw,&spec,PatchLimits::new(PatchLimitConfig{max_value_bytes:n-1,..Default::default()})?,0).is_err());
    assert!(apply(&raw,&spec,PatchLimits::new(PatchLimitConfig{max_value_bytes:n,..Default::default()})?,0).is_ok());
    let spec=vec![(0,vec![r(1,Kind::Tab,vec![text("X"),TextAtom::LineBreak])?])];let n="X<hp:lineBreak/>".len();
    assert!(apply(&raw,&spec,PatchLimits::new(PatchLimitConfig{max_fragment_bytes:n-1,..Default::default()})?,0).is_err());
    assert!(apply(&raw,&spec,PatchLimits::new(PatchLimitConfig{max_fragment_bytes:n,..Default::default()})?,0).is_ok());Ok(())
}
#[test]
fn control_and_all_three_old_range_families_share_internal_range_budget()->TestResult{
    let raw=package(&format!("<hp:t>A{TAB}B<hp:lineBreak/>C</hp:t>"))?;let spec=vec![(0,vec![r(1,Kind::Tab,vec![text("X")])?,r(3,Kind::LineBreak,vec![text("Y")])?])];
    assert!(apply(&raw,&spec,PatchLimits::new(PatchLimitConfig{max_intents:4,..Default::default()})?,3).is_err());
    assert!(apply(&raw,&spec,PatchLimits::new(PatchLimitConfig{max_intents:5,..Default::default()})?,3).is_ok());Ok(())
}
#[test]
fn control_whitespace_and_escaped_old_text_leaf_outputs_share_exact_byte_budget()->TestResult{
    let raw=package(&format!("<hp:t>A{TAB}B</hp:t>"))?;let spec=vec![(0,vec![r(1,Kind::Tab,vec![text("&")])?])];
    assert!(apply(&raw,&spec,PatchLimits::new(PatchLimitConfig{max_total_output_growth:15,..Default::default()})?,3).is_err());
    assert!(apply(&raw,&spec,PatchLimits::new(PatchLimitConfig{max_total_output_growth:16,..Default::default()})?,3).is_ok());Ok(())
}
#[test]
fn control_and_whitespace_share_output_atom_budget_without_top_level_count_confusion()->TestResult{
    let raw=package(&format!("<hp:t>A{TAB}B</hp:t>"))?;let spec=vec![(0,vec![r(1,Kind::Tab,vec![text("X"),text("Y")])?])];
    assert!(apply(&raw,&spec,PatchLimits::new(PatchLimitConfig{max_intents:3,..Default::default()})?,4).is_err());
    assert!(apply(&raw,&spec,PatchLimits::new(PatchLimitConfig{max_intents:4,..Default::default()})?,4).is_ok());Ok(())
}
#[test]
fn control_duplicate_target_rejects_even_byte_disjoint_edits_of_other_range_families()->TestResult{
    let raw=package(&format!("<hp:t> A{TAB}B</hp:t>"))?;
    for mode in 0..3{let error=run(&raw,Default::default(),|path,xml,leaves|{let target=XmlElementSelector::bind(path,xml,leaves[0])?;
        let other=match mode{0=>PatchIntent::ReplaceWhitespaceAtomRanges{target:target.clone(),ranges:vec![WRange::text(0,0,1,vec![]) ?]},
            1=>PatchIntent::ReplaceTextAtomScalarRanges{target:target.clone(),ranges:vec![TextAtomRangeReplacement::new(0,1,2,"X")?]},
            _=>PatchIntent::ReplaceLeafScalarRanges{target:target.clone(),ranges:vec![LeafTextRangeReplacement::new(0,1,"X")?]}};
        Ok(vec![PatchIntent::ReplaceTextControlAtoms{target,replacements:vec![r(1,Kind::Tab,vec![]) ?]},other])}).expect_err("duplicate target");
        assert!(matches!(error.downcast_ref::<PatchError>(),Some(PatchError::Conflict)));}Ok(())
}
#[test]
fn control_many_original_controls_use_one_cursor_without_renumbering()->TestResult{
    let old=format!("<hp:t>A{}B</hp:t>",TAB.repeat(2000));let new=format!("<hp:t>A{}B</hp:t>","x".repeat(2000));
    rewrite(&old,&new,(1..=2000).map(|i|r(i,Kind::Tab,vec![text("x")])).collect::<Result<_,_>>()?)
}
#[test]
fn control_streamed_escape_rejects_small_budget_without_mutating_original()->TestResult{
    let raw=package(&format!("<hp:t>A{TAB}B</hp:t>"))?;let before=Sha256::digest(&raw);
    let spec=vec![(0,vec![r(1,Kind::Tab,vec![text(&"&".repeat(200000))])?])];
    assert!(apply(&raw,&spec,PatchLimits::new(PatchLimitConfig{max_value_bytes:64,..Default::default()})?,0).is_err());assert_eq!(Sha256::digest(&raw),before);Ok(())
}
#[test]
fn control_debug_determinism_and_old_text_whitespace_rejections_are_preserved()->TestResult{
    let raw=package(&format!("<hp:t>A{TAB}B</hp:t>"))?;let value=r(1,Kind::Tab,vec![text("PRIVATE-TEXT<&")])?;assert!(!format!("{value:?}").contains("PRIVATE-TEXT"));
    let a=apply(&raw,&[(0,vec![value.clone()])],Default::default(),0)?;let b=apply(&raw,&[(0,vec![value])],Default::default(),0)?;assert_eq!(a,b);
    assert!(TextAtomRangeReplacement::new(0,0,1,"\t").is_err());assert!(WhitespaceText::new("general text").is_err());
    assert!(run(&raw,Default::default(),|path,xml,leaves|Ok(vec![PatchIntent::ReplaceWhitespaceAtomRanges{target:XmlElementSelector::bind(path,xml,leaves[0])?,ranges:vec![WRange::text(0,0,1,vec![]) ?]}])).is_err());Ok(())
}
