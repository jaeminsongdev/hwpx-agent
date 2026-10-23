use hwpx_package::{BoundedZipReader,IdIndexLimits,IdRuleProfile,PackageGraph,PackageGraphLimits,PackageLimits,
    PatchIntent,PatchLimits,PatchLimitConfig,LeafTextRangeReplacement as Range,PreservationRuleProfile,
    PreservingPatchEngine,PreservingWriter,PreservingXmlDocument,WriterLimits,XmlElementSelector,PatchError};
use std::{error::Error,io::Cursor};
use sha2::{Digest as _,Sha256};
#[allow(dead_code)]
#[path="support/document_import_field_fixture.rs"] mod fixture;
type TestResult=Result<(),Box<dyn Error>>;
type Spec<'a>=(usize,Vec<(u32,u32,&'a str)>);
fn package(leaves:&str)->Result<Vec<u8>,Box<dyn Error>> {fixture::package(&format!("<hp:p id='1'><hp:run>{leaves}<hp:t>UNCHANGED&#38;TAIL</hp:t></hp:run></hp:p>"))}
fn section(bytes:&[u8])->Result<Vec<u8>,Box<dyn Error>> {let mut r=BoundedZipReader::open(Cursor::new(bytes),PackageLimits::default())?;
    let i=r.entries().iter().position(|p|p.path.as_str()=="Contents/section0.xml").ok_or("part")?;Ok(r.read_entry(i)?)}
fn apply(bytes:&[u8],specs:&[Spec<'_>],limits:PatchLimits)->Result<Vec<u8>,Box<dyn Error>> {
    let mut r=BoundedZipReader::open(Cursor::new(bytes),PackageLimits::default())?;let graph=PackageGraph::build(&mut r,PackageGraphLimits::default())?;
    let i=r.entries().iter().position(|p|p.path.as_str()=="Contents/section0.xml").ok_or("part")?;let path=r.entries()[i].path.clone();
    let raw=r.read_entry(i)?;let xml=PreservingXmlDocument::parse(&raw)?;
    let leaves:Vec<_>=xml.elements().iter().enumerate().filter(|(_,n)|n.name().local_name()=="t").map(|(i,_)|i).collect();let mut intents=Vec::new();
    for (leaf,ranges) in specs {intents.push(PatchIntent::ReplaceLeafScalarRanges {target:XmlElementSelector::bind(&path,&xml,*leaves.get(*leaf).ok_or("leaf")?)?,
        ranges:ranges.iter().map(|(s,e,v)|Range::new(*s,*e,v)).collect::<Result<Vec<_>,_>>()?});}
    let patch=PreservingPatchEngine::apply_with_limits_and_preservation_profile(&mut r,&graph,PackageGraphLimits::default(),
        IdRuleProfile::current_hancom_2020_formula_v3(),IdIndexLimits::default(),limits,PreservationRuleProfile::Hangul2020PreviewTextV2,&intents)?;
    let artifact=PreservingWriter::build(&patch,PackageLimits::default(),PackageGraphLimits::default(),IdIndexLimits::default(),WriterLimits::default())?;
    let output=artifact.with_verified_bytes(<[u8]>::to_vec)?;
    let mut after=BoundedZipReader::open(Cursor::new(&output),PackageLimits::default())?;
    for index in 0..r.entries().len() {let original=&r.entries()[index].path;
        if original==&path {continue;}let j=after.entries().iter().position(|p|&p.path==original).ok_or("unchanged part")?;
        assert_eq!(r.read_entry(index)?,after.read_entry(j)?);}
    Ok(output)
}
fn assert_rewrite(old:&str,new:&str,specs:&[Spec<'_>])->TestResult {
    let b=package(old)?;let before=section(&b)?;let digest:[u8;32]=Sha256::digest(&b).into();let out=apply(&b,specs,Default::default())?;
    assert_eq!(section(&out)?,String::from_utf8(before)?.replacen(old,new,1).as_bytes());assert_eq!(<[u8;32]>::from(Sha256::digest(&b)),digest);Ok(())
}
#[test]
fn scalar_ranges_preserve_unselected_entity_spellings_attributes_and_all_other_parts()->TestResult {
    assert_rewrite("<hp:t u:flag='keep'>A&#x1F600;B&amp;C&#13;D</hp:t>",
        "<hp:t u:flag='keep'>A한&lt;&amp;&#13;&amp;C&#13;D</hp:t>",&[(0,vec![(1,3,"한<&\r")])])
}
#[test]
fn scalar_ranges_apply_multiple_disjoint_and_adjacent_ranges_in_original_coordinates()->TestResult {
    assert_rewrite("<hp:t>abcdef</hp:t>","<hp:t>aXcdYf</hp:t>",&[(0,vec![(1,2,"X"),(4,5,"Y")])])?;
    assert_rewrite("<hp:t>abcdef</hp:t>","<hp:t>aXYdef</hp:t>",&[(0,vec![(1,2,"X"),(2,3,"Y")])])?;
    assert_rewrite("<hp:t>abc</hp:t><hp:t>def</hp:t>","<hp:t>aXc</hp:t><hp:t>Yef</hp:t>",&[(0,vec![(1,2,"X")]),(1,vec![(0,1,"Y")])])?;Ok(())
}
#[test]
fn scalar_ranges_follow_literal_crlf_normalization_but_reference_cr_is_a_distinct_scalar()->TestResult {
    assert_rewrite("<hp:t>A\r\nB\rC\nD</hp:t>","<hp:t>A\r\nX\rC\nD</hp:t>",&[(0,vec![(2,3,"X")])])?;
    assert_rewrite("<hp:t>A&#13;\nB</hp:t>","<hp:t>AX\nB</hp:t>",&[(0,vec![(1,2,"X")])])?;
    assert_rewrite("<hp:t>A&#xA;B</hp:t>","<hp:t>A&#xA;X</hp:t>",&[(0,vec![(2,3,"X")])])?;Ok(())
}
#[test]
fn scalar_ranges_insert_at_leaf_boundaries_expand_empty_tags_and_delete_without_changing_structure()->TestResult {
    assert_rewrite("<hp:t u:x='keep' />","<hp:t u:x='keep' >X&amp;</hp:t>",&[(0,vec![(0,0,"X&")])])?;
    assert_rewrite("<hp:t></hp:t>","<hp:t>X</hp:t>",&[(0,vec![(0,0,"X")])])?;
    assert_rewrite("<hp:t>abc</hp:t>","<hp:t>abcX</hp:t>",&[(0,vec![(3,3,"X")])])?;
    assert_rewrite("<hp:t>abc</hp:t>","<hp:t></hp:t>",&[(0,vec![(0,3,"")])])?;Ok(())
}
#[test]
fn scalar_ranges_reject_overlap_unsorted_duplicate_targets_empty_and_foreign_scalar_ranges_atomically()->TestResult {
    let b=package("<hp:t>abcdef</hp:t><hp:t>other</hp:t>")?;
    for specs in [vec![(0,vec![(0,3,"X"),(2,4,"Y")])],vec![(0,vec![(4,5,"X"),(0,1,"Y")])],
        vec![(0,vec![(1,1,"X"),(1,1,"Y")])],vec![(0,vec![])],vec![(0,vec![(0,99,"X")])],
        vec![(0,vec![(0,1,"X")]),(1,vec![(0,99,"Y")])],vec![(0,vec![(0,1,"X")]),(0,vec![(2,3,"Y")])]] {
        assert!(apply(&b,&specs,Default::default()).is_err());assert!(String::from_utf8(section(&b)?)?.contains("abcdef"));}
    assert!(Range::new(2,1,"X").is_err());assert!(Range::new(0,1,"\u{0000}").is_err());Ok(())
}
#[test]
fn scalar_ranges_reject_comments_children_and_stale_selectors_before_output()->TestResult {
    for leaf in ["<hp:t>a<!--KEEP-->b</hp:t>","<hp:t>a<hp:tab/>b</hp:t>"] {assert!(apply(&package(leaf)?,&[(0,vec![(0,1,"X")])],Default::default()).is_err());}
    let b=package("<hp:t>original</hp:t>")?;let mut reader=BoundedZipReader::open(Cursor::new(&b),PackageLimits::default())?;
    let graph=PackageGraph::build(&mut reader,PackageGraphLimits::default())?;let i=reader.entries().iter().position(|p|p.path.as_str()=="Contents/section0.xml").ok_or("part")?;
    let path=reader.entries()[i].path.clone();let changed=String::from_utf8(reader.read_entry(i)?)?.replace("original","changed");let xml=PreservingXmlDocument::parse(changed.as_bytes())?;
    let index=xml.elements().iter().position(|n|n.name().local_name()=="t").ok_or("leaf")?;
    let intent=PatchIntent::ReplaceLeafScalarRanges {target:XmlElementSelector::bind(&path,&xml,index)?,ranges:vec![Range::new(0,1,"X")?]};
    assert!(matches!(PreservingPatchEngine::apply_with_limits_and_preservation_profile(&mut reader,&graph,PackageGraphLimits::default(),
        IdRuleProfile::current_hancom_2020_formula_v3(),IdIndexLimits::default(),Default::default(),PreservationRuleProfile::Hangul2020PreviewTextV2,&[intent]),Err(PatchError::SelectorStale)));Ok(())
}
#[test]
fn scalar_ranges_global_count_value_and_escaped_output_budgets_reject_before_large_allocation()->TestResult {
    let b=package("<hp:t>abc</hp:t><hp:t>def</hp:t>")?;
    let cap=PatchLimits::new(PatchLimitConfig {max_intents:2,..Default::default()})?;
    assert!(apply(&b,&[(0,vec![(0,1,"X"),(1,2,"Y")]),(1,vec![(0,1,"Z")])],cap).is_err());
    let cap=PatchLimits::new(PatchLimitConfig {max_value_bytes:1,..Default::default()})?;
    assert!(apply(&b,&[(0,vec![(0,1,"XX")])],cap).is_err());
    let cap=PatchLimits::new(PatchLimitConfig {max_total_output_growth:4,..Default::default()})?;
    assert!(apply(&b,&[(0,vec![(0,1,"&")])],cap).is_err());
    let cap=PatchLimits::new(PatchLimitConfig {max_total_output_growth:6,..Default::default()})?;
    assert!(apply(&b,&[(0,vec![(0,1,"&")]),(1,vec![(0,1,"&")])],cap).is_err());Ok(())
}
#[test]
fn scalar_ranges_repeated_edits_are_deterministic_and_private_without_losing_unselected_text()->TestResult {
    let text="a😀&amp;".repeat(200);let b=package(&format!("<hp:t>{text}</hp:t>"))?;
    let ranges:Vec<_>=(0..200).map(|i|(i*3,i*3+1,"PRIVATE-REPLACEMENT")).collect();let specs=vec![(0,ranges)];
    let first=apply(&b,&specs,Default::default())?;assert_eq!(first,apply(&b,&specs,Default::default())?);
    let output=String::from_utf8(section(&first)?)?;assert_eq!(output.matches("PRIVATE-REPLACEMENT😀&amp;").count(),200);
    let range=Range::new(0,1,"PRIVATE-REPLACEMENT")?;assert!(!format!("{range:?}").contains("PRIVATE"));Ok(())
}
#[test]
fn scalar_ranges_collision_key_aliases_cannot_duplicate_one_leaf_scan()->TestResult {
    use std::io::Write as _;
    let b=package("<hp:t>abcdef</hp:t>")?;let mut reader=BoundedZipReader::open(Cursor::new(&b),PackageLimits::default())?;
    let graph=PackageGraph::build(&mut reader,PackageGraphLimits::default())?;let i=reader.entries().iter().position(|p|p.path.as_str()=="Contents/section0.xml").ok_or("part")?;
    let path=reader.entries()[i].path.clone();let raw=reader.read_entry(i)?;let xml=PreservingXmlDocument::parse(&raw)?;
    let index=xml.elements().iter().position(|n|n.name().local_name()=="t").ok_or("leaf")?;
    let mut zip=zip::ZipWriter::new(Cursor::new(Vec::new()));zip.start_file("contents/SECTION0.xml",zip::write::SimpleFileOptions::default())?;zip.write_all(&raw)?;
    let other=zip.finish()?.into_inner();let aliases=BoundedZipReader::open(Cursor::new(&other),PackageLimits::default())?;let alias=&aliases.entries()[0].path;
    assert_ne!(&path,alias);assert_eq!(path.as_str().to_ascii_lowercase(),alias.as_str().to_ascii_lowercase());
    let intents=[PatchIntent::ReplaceLeafScalarRanges {target:XmlElementSelector::bind(&path,&xml,index)?,ranges:vec![Range::new(0,1,"X")?]},
        PatchIntent::ReplaceLeafScalarRanges {target:XmlElementSelector::bind(alias,&xml,index)?,ranges:vec![Range::new(2,3,"Y")?]}];
    assert!(matches!(PreservingPatchEngine::apply_with_limits_and_preservation_profile(&mut reader,&graph,PackageGraphLimits::default(),
        IdRuleProfile::current_hancom_2020_formula_v3(),IdIndexLimits::default(),Default::default(),PreservationRuleProfile::Hangul2020PreviewTextV2,&intents),Err(PatchError::Conflict)));Ok(())
}
