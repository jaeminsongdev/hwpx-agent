use hwpx_package::{BoundedZipReader,IdRuleProfile,PackageGraph,
    PatchIntent,PatchLimits,PatchLimitConfig,LeafTextRangeReplacement,TextAtomRangeReplacement,PreservationRuleProfile,
    PreservingPatchEngine,PreservingWriter,PreservingXmlDocument,XmlElementSelector,
    WhitespaceText,WhitespaceOutputAtom as Atom,WhitespaceControlKind as Kind,WhitespaceAtomRangeReplacement as Range};
use sha2::{Digest as _,Sha256};
use std::{error::Error,io::Cursor};
#[allow(dead_code)] #[path="support/search_definition_fixture.rs"] mod fixture;
type TestResult=Result<(),Box<dyn Error>>;
type Spec=(usize,Vec<Range>);
fn text(value:&str)->Result<Atom,Box<dyn Error>>{Ok(Atom::Text(WhitespaceText::new(value)?))}
fn package(leaf:&str)->Result<Vec<u8>,Box<dyn Error>>{fixture::package(&format!("<hp:p id='1'><hp:run charPrIDRef='0'>{leaf}<hp:t>UNCHANGED&#38;TAIL</hp:t><hp:t>SECOND</hp:t></hp:run></hp:p>"))}
fn section(bytes:&[u8])->Result<String,Box<dyn Error>>{let mut r=BoundedZipReader::open(Cursor::new(bytes),Default::default())?;let i=r.entries().iter().position(|p|p.path.as_str()=="Contents/section0.xml").ok_or("part")?;Ok(String::from_utf8(r.read_entry(i)?)?)}
fn apply(bytes:&[u8],specs:&[Spec],limits:PatchLimits,legacy:u8)->Result<Vec<u8>,Box<dyn Error>>{
    let mut r=BoundedZipReader::open(Cursor::new(bytes),Default::default())?;let graph=PackageGraph::build(&mut r,Default::default())?;let i=r.entries().iter().position(|p|p.path.as_str()=="Contents/section0.xml").ok_or("part")?;
    let path=r.entries()[i].path.clone();let raw=r.read_entry(i)?;let xml=PreservingXmlDocument::parse(&raw)?;let leaves:Vec<_>=xml.elements().iter().enumerate().filter(|(_,n)|n.name().local_name()=="t").map(|(i,_)|i).collect();let mut intents=Vec::new();
    for(leaf,ranges)in specs{intents.push(PatchIntent::ReplaceWhitespaceAtomRanges{target:XmlElementSelector::bind(&path,&xml,*leaves.get(*leaf).ok_or("leaf")?)?,ranges:ranges.clone()});}
    if legacy==1||legacy==3{let index=if legacy==3{1}else{leaves.len()-1};intents.push(PatchIntent::ReplaceTextAtomScalarRanges{target:XmlElementSelector::bind(&path,&xml,leaves[index])?,ranges:vec![TextAtomRangeReplacement::new(0,0,1,"&")?]});}
    if legacy==2||legacy==3{intents.push(PatchIntent::ReplaceLeafScalarRanges{target:XmlElementSelector::bind(&path,&xml,*leaves.last().ok_or("tail")?)?,ranges:vec![LeafTextRangeReplacement::new(0,1,"&")?]});}
    let patch=PreservingPatchEngine::apply_with_limits_and_preservation_profile(&mut r,&graph,Default::default(),IdRuleProfile::hwpml_2011_text_style_v9(),Default::default(),limits,PreservationRuleProfile::Hangul2020PreviewTextV2,&intents)?;
    let artifact=PreservingWriter::build(&patch,Default::default(),Default::default(),Default::default(),Default::default())?;let out=artifact.with_verified_bytes(<[u8]>::to_vec)?;let mut after=BoundedZipReader::open(Cursor::new(&out),Default::default())?;
    assert_eq!(r.entries().len(),after.entries().len());for index in 0..r.entries().len(){let original=r.entries()[index].path.clone();if original==path{continue;}let j=after.entries().iter().position(|p|p.path==original).ok_or("part")?;assert_eq!(r.read_entry(index)?,after.read_entry(j)?);}Ok(out)
}
fn rewrite(old:&str,new:&str,ranges:Vec<Range>)->TestResult{let bytes=package(old)?;let digest=Sha256::digest(&bytes);let out=apply(&bytes,&[(0,ranges)],Default::default(),0)?;assert_eq!(section(&out)?,section(&bytes)?.replacen(old,new,1));assert_eq!(Sha256::digest(&bytes),digest);Ok(())}
#[test]
fn whitespace_text_ranges_collapse_spaces_without_touching_letters_entities_or_styles()->TestResult{
    rewrite("<hp:t charStyleIDRef='1'>A&#x1F600;  &#x2000;B&#38;C</hp:t>","<hp:t charStyleIDRef='1'>A&#x1F600; B&#38;C</hp:t>",vec![Range::text(0,2,5,vec![text(" ")?])?])
}
#[test]
fn whitespace_text_can_become_typed_tab_and_linebreak_without_raw_xml()->TestResult{
    rewrite("<hp:t>A  B</hp:t>","<hp:t>A<hp:tab width=\"8000\" leader=\"1\" type=\"2\"/><hp:lineBreak/>B</hp:t>",vec![Range::text(0,1,3,vec![Atom::Tab{width:8000,leader:1,tab_type:2},Atom::LineBreak])?])
}
#[test]
fn whitespace_qualified_controls_can_become_spaces_and_remove_paired_internal_whitespace()->TestResult{
    rewrite("<hp:t>A<hp:tab type='0' width='20' leader='0'> </hp:tab>B<hp:lineBreak> </hp:lineBreak>C</hp:t>","<hp:t>A  B C</hp:t>",vec![Range::control(1,Kind::Tab,vec![text("  ")?]),Range::control(3,Kind::LineBreak,vec![text(" ")?])])
}
#[test]
fn whitespace_control_removal_is_explicit_and_preserves_unselected_control_bytes()->TestResult{
    rewrite("<hp:t><hp:lineBreak/>A<hp:tab leader='0' type='0' width='1'> </hp:tab>B<hp:lineBreak/></hp:t>","<hp:t>A<hp:tab leader='0' type='0' width='1'> </hp:tab>B</hp:t>",vec![Range::control(0,Kind::LineBreak,vec![]),Range::control(4,Kind::LineBreak,vec![])])
}
#[test]
fn whitespace_text_and_control_edits_share_original_atom_coordinates()->TestResult{
    rewrite("<hp:t>A  <hp:lineBreak/> B</hp:t>","<hp:t>A <hp:tab width=\"0\" leader=\"0\" type=\"0\"/>B</hp:t>",vec![Range::text(0,1,3,vec![text(" ")?])?,Range::control(1,Kind::LineBreak,vec![Atom::Tab{width:0,leader:0,tab_type:0}]),Range::text(2,0,1,vec![])?])
}
#[test]
fn whitespace_all19_model_text_space_characters_are_accepted_and_replaced()->TestResult{
    let points=[0x20,0xa0,0x1680,0x2000,0x2001,0x2002,0x2003,0x2004,0x2005,0x2006,0x2007,0x2008,0x2009,0x200a,0x2028,0x2029,0x202f,0x205f,0x3000];
    let source: String=points.into_iter().map(|p|char::from_u32(p).ok_or("point")).collect::<Result<_,_>>()?;let atom=text(&source)?;assert!(!format!("{atom:?}").contains(&source));
    rewrite(&format!("<hp:t>A{source}B</hp:t>"),"<hp:t>A B</hp:t>",vec![Range::text(0,1,20,vec![text(" ")?])?])
}
#[test]
fn whitespace_text_constructor_rejects_controls_zero_width_letters_and_xml()->TestResult{
    for value in["","A","<hp:tab/>","&amp;","\t","\n","\r","\u{b}","\u{c}","\u{85}","\u{200b}","\u{feff}","\0"]{assert!(WhitespaceText::new(value).is_err());}
    assert!(WhitespaceText::new(&" ".repeat(1024*1024+1)).is_err());Ok(())
}
#[test]
fn whitespace_source_letter_deletion_or_replacement_is_rejected_atomically()->TestResult{
    let bytes=package("<hp:t>A  B</hp:t>")?;for range in[Range::text(0,0,1,vec![])?,Range::text(0,1,4,vec![text(" ")?])?]{assert!(apply(&bytes,&[(0,vec![range])],Default::default(),0).is_err());}assert!(section(&bytes)?.contains("A  B"));Ok(())
}
#[test]
fn whitespace_rejects_reverse_out_of_bounds_and_nonexistent_atom_ranges()->TestResult{
    assert!(Range::text(0,3,2,vec![]).is_err());assert!(Range::text(0,1,1,vec![]).is_err());assert!(Range::empty(vec![]).is_err());let bytes=package("<hp:t>A  B</hp:t>")?;
    for ranges in[vec![],vec![Range::text(0,1,99,vec![])?],vec![Range::text(3,0,1,vec![])?]]{assert!(apply(&bytes,&[(0,ranges)],Default::default(),0).is_err());}Ok(())
}
#[test]
fn whitespace_unsorted_overlapping_duplicate_and_ambiguous_insertions_are_rejected()->TestResult{
    let bytes=package("<hp:t>    </hp:t>")?;for ranges in[vec![Range::text(0,2,3,vec![])?,Range::text(0,0,1,vec![])?],vec![Range::text(0,0,3,vec![])?,Range::text(0,2,4,vec![])?],vec![Range::text(0,1,1,vec![text(" ")?])?,Range::text(0,1,1,vec![text(" ")?])?]]{assert!(apply(&bytes,&[(0,ranges)],Default::default(),0).is_err());}
    let r=Range::text(0,0,1,vec![text(" ")?])?;assert!(apply(&bytes,&[(0,vec![r.clone()]),(0,vec![r])],Default::default(),0).is_err());Ok(())
}
#[test]
fn whitespace_original_reader_rejects_opaque_malformed_and_unknown_control_shapes()->TestResult{
    for leaf in["<hp:t> <!--keep--> </hp:t>","<hp:t> <u:future/> </hp:t>","<hp:t> <hp:tab/> </hp:t>","<hp:t> <hp:tab width='1' leader='0' type='0' id='1'/> </hp:t>","<hp:t> <hp:lineBreak x='1'/> </hp:t>","<hp:t> <hp:lineBreak>TEXT</hp:lineBreak> </hp:t>","<hp:t> <hp:tab width='1' leader='0' type='0'><hp:lineBreak/></hp:tab> </hp:t>","<hp:t> &#13; </hp:t>"]{
        assert!(apply(&package(leaf)?,&[(0,vec![Range::text(0,0,1,vec![]) ?])],Default::default(),0).is_err());}Ok(())
}
#[test]
fn whitespace_control_kind_is_verified_and_text_coordinates_never_edit_controls()->TestResult{
    let bytes=package("<hp:t>A<hp:lineBreak/> B</hp:t>")?;for r in[Range::control(1,Kind::Tab,vec![]),Range::control(0,Kind::LineBreak,vec![]),Range::text(1,0,1,vec![text(" ")?])?]{assert!(apply(&bytes,&[(0,vec![r])],Default::default(),0).is_err());}Ok(())
}
#[test]
fn whitespace_stale_wrong_namespace_and_non_text_selectors_reject_before_publication()->TestResult{
    let bytes=package("<hp:t>  </hp:t>")?;let mut reader=BoundedZipReader::open(Cursor::new(&bytes),Default::default())?;let graph=PackageGraph::build(&mut reader,Default::default())?;let at=reader.entries().iter().position(|e|e.path.as_str()=="Contents/section0.xml").ok_or("part")?;let path=reader.entries()[at].path.clone();let original=String::from_utf8(reader.read_entry(at)?)?;
    for(source,local)in[(original.replace("<hp:t>  </hp:t>","<hp:t> \u{a0}</hp:t>"),"t"),(original.clone(),"run")]{let xml=PreservingXmlDocument::parse(source.as_bytes())?;let i=xml.elements().iter().position(|n|n.name().local_name()==local).ok_or("element")?;
        let intent=PatchIntent::ReplaceWhitespaceAtomRanges{target:XmlElementSelector::bind(&path,&xml,i)?,ranges:vec![Range::text(0,0,1,vec![])?]};assert!(PreservingPatchEngine::apply_with_limits_and_preservation_profile(&mut reader,&graph,Default::default(),IdRuleProfile::hwpml_2011_text_style_v9(),Default::default(),Default::default(),PreservationRuleProfile::Hangul2020PreviewTextV2,&[intent]).is_err());}
    assert!(apply(&package("<u:t> </u:t>")?,&[(0,vec![Range::text(0,0,1,vec![])?])],Default::default(),0).is_err());Ok(())
}
#[test]
fn whitespace_output_uses_actual_parent_prefix_and_default_namespace_not_hardcoded_hp()->TestResult{
    let ns="http://www.hancom.co.kr/hwpml/2011/paragraph";for(prefix,decl)in[("z:",format!("xmlns:z='{ns}' xmlns:hp='urn:shadow'")),("",format!("xmlns='{ns}'"))]{let old=format!("<{prefix}t {decl}> </{prefix}t>");let new=format!("<{prefix}t {decl}><{prefix}lineBreak/></{prefix}t>");rewrite(&old,&new,vec![Range::text(0,0,1,vec![Atom::LineBreak])?])?;}Ok(())
}
#[test]
fn whitespace_empty_self_closing_text_expands_only_its_closing_shell()->TestResult{
    rewrite("<hp:t charStyleIDRef='1' />","<hp:t charStyleIDRef='1' > <hp:lineBreak/></hp:t>",vec![Range::empty(vec![text(" ")?,Atom::LineBreak])?])
}
#[test]
fn whitespace_paired_empty_text_and_real_text_boundary_insertions_are_explicit()->TestResult{
    rewrite("<hp:t></hp:t>","<hp:t><hp:lineBreak/></hp:t>",vec![Range::empty(vec![Atom::LineBreak])?])?;
    rewrite("<hp:t>A</hp:t>","<hp:t> A<hp:lineBreak/></hp:t>",vec![Range::text(0,0,0,vec![text(" ")?])?,Range::text(0,1,1,vec![Atom::LineBreak])?])?;
    assert!(apply(&package("<hp:t/>")?,&[(0,vec![Range::text(0,0,0,vec![text(" ")?])?])],Default::default(),0).is_err());assert!(apply(&package("<hp:t> </hp:t>")?,&[(0,vec![Range::empty(vec![text(" ")?])?])],Default::default(),0).is_err());Ok(())
}
#[test]
fn whitespace_rendered_value_byte_caps_include_multibyte_text_and_control_markup()->TestResult{
    let bytes=package("<hp:t>  </hp:t>")?;let limits=PatchLimits::new(PatchLimitConfig{max_value_bytes:2,..Default::default()})?;
    assert!(apply(&bytes,&[(0,vec![Range::text(0,0,2,vec![text("　")?])?])],limits,0).is_err());assert!(apply(&bytes,&[(0,vec![Range::text(0,0,2,vec![Atom::LineBreak])?])],limits,0).is_err());Ok(())
}
#[test]
fn whitespace_fragment_and_empty_shell_caps_cannot_be_bypassed_by_small_payloads()->TestResult{
    let limits=PatchLimits::new(PatchLimitConfig{max_fragment_bytes:3,..Default::default()})?;assert!(apply(&package("<hp:t> </hp:t>")?,&[(0,vec![Range::text(0,0,1,vec![Atom::LineBreak])?])],limits,0).is_err());
    assert!(apply(&package("<hp:t/>")?,&[(0,vec![Range::empty(vec![text(" ")?])?])],limits,0).is_err());Ok(())
}
#[test]
fn whitespace_and_both_old_range_families_share_one_count_budget()->TestResult{
    let bytes=package("<hp:t>  </hp:t>")?;let specs=vec![(0,vec![Range::text(0,0,1,vec![])?,Range::text(0,1,2,vec![text(" ")?])?])];
    // Three top-level intents fit cap3, but their four scalar/atom ranges must not.
    assert!(apply(&bytes,&specs,PatchLimits::new(PatchLimitConfig{max_intents:3,..Default::default()})?,3).is_err());assert!(apply(&bytes,&specs,PatchLimits::new(PatchLimitConfig{max_intents:4,..Default::default()})?,3).is_ok());Ok(())
}
#[test]
fn whitespace_and_both_old_range_families_share_escaped_output_budget()->TestResult{
    let bytes=package("<hp:t>  </hp:t>")?;let specs=vec![(0,vec![Range::text(0,0,2,vec![text(" ")?])?])];assert!(apply(&bytes,&specs,PatchLimits::new(PatchLimitConfig{max_total_output_growth:10,..Default::default()})?,3).is_err());
    assert!(apply(&bytes,&specs,PatchLimits::new(PatchLimitConfig{max_total_output_growth:11,..Default::default()})?,3).is_ok());let empty=package("<hp:t/>")?;assert!(apply(&empty,&[(0,vec![Range::empty(vec![text(" ")?])?])],PatchLimits::new(PatchLimitConfig{max_total_output_growth:1,..Default::default()})?,0).is_err());Ok(())
}
#[test]
fn whitespace_output_atom_count_and_cross_family_duplicate_targets_are_bounded()->TestResult{
    let bytes=package("<hp:t> </hp:t>")?;assert!(apply(&bytes,&[(0,vec![Range::text(0,0,1,vec![Atom::LineBreak;3])?])],PatchLimits::new(PatchLimitConfig{max_intents:2,..Default::default()})?,0).is_err());
    // The old edit at0..1 and insertion at2 are byte-disjoint; shared target rejection is required.
    assert!(apply(&bytes,&[(1,vec![Range::text(0,2,2,vec![text(" ")?])?])],Default::default(),3).is_err());Ok(())
}
#[test]
fn whitespace_numeric_entities_and_non_bmp_offsets_are_original_scalar_boundaries()->TestResult{
    rewrite("<hp:t>A&#x1F600;&#x20;&#x2000;B&#38;</hp:t>","<hp:t>A&#x1F600;<hp:lineBreak/>B&#38;</hp:t>",vec![Range::text(0,2,4,vec![Atom::LineBreak])?])
}
#[test]
fn whitespace_many_disjoint_ranges_use_one_original_text_atom_and_keep_entities_exact()->TestResult{
    let source="A&#x1F600; ".repeat(2000);let old=format!("<hp:t>{source}</hp:t>");let new=format!("<hp:t>{}</hp:t>","A&#x1F600;　".repeat(2000));
    let ranges=(0..2000).map(|i|Range::text(0,i*3+2,i*3+3,vec![Atom::Text(WhitespaceText::new("　")?)] )).collect::<Result<Vec<_>,_>>()?;rewrite(&old,&new,ranges)
}
#[test]
fn whitespace_debug_redacts_payload_and_legacy_text_ranges_still_reject_control_strings()->TestResult{
    let r=Range::text(0,0,1,vec![text("\u{2000}")?])?;let bytes=package("<hp:t> </hp:t>")?;let a=apply(&bytes,&[(0,vec![r.clone()])],Default::default(),0)?;assert_eq!(a,apply(&bytes,&[(0,vec![r.clone()])],Default::default(),0)?);
    assert!(!format!("{r:?}").contains('\u{2000}'));for s in["\t","\n","\r"]{assert!(TextAtomRangeReplacement::new(0,0,1,s).is_err());}Ok(())
}
