use hwpx_package::{BoundedZipReader,IdIndexLimits,IdRuleProfile,PackageGraph,PackageGraphLimits,PackageLimits,
    PatchIntent,PatchLimits,PatchLimitConfig,LeafTextRangeReplacement,TextAtomRangeReplacement as Range,PreservationRuleProfile,
    PreservingPatchEngine,PreservingWriter,PreservingXmlDocument,WriterLimits,XmlElementSelector,
    document_import::{ImportedSourcePackage,SourceImportLimits,forms::ImportedDocumentForms,
        search::{SourceSearchMode,SourceSearchQuery}}};
use domain_ir::DocumentId;
use sha2::{Digest as _,Sha256};
use std::{error::Error,io::Cursor};
#[allow(dead_code)] #[path="support/search_definition_fixture.rs"] mod fixture;
type TestResult=Result<(),Box<dyn Error>>;
type Spec<'a>=(usize,Vec<(u32,u32,u32,&'a str)>);
fn package(text:&str)->Result<Vec<u8>,Box<dyn Error>> {
    fixture::package(&format!("<hp:p id='1'><hp:run charPrIDRef='0'>{text}<hp:t>UNCHANGED&#38;TAIL</hp:t></hp:run></hp:p>"))
}
fn section(bytes:&[u8])->Result<String,Box<dyn Error>> {
    let mut r=BoundedZipReader::open(Cursor::new(bytes),PackageLimits::default())?;
    let i=r.entries().iter().position(|p|p.path.as_str()=="Contents/section0.xml").ok_or("part")?;
    Ok(String::from_utf8(r.read_entry(i)?)?)
}
fn apply(bytes:&[u8],specs:&[Spec<'_>],limits:PatchLimits,legacy:bool)->Result<Vec<u8>,Box<dyn Error>> {
    let mut r=BoundedZipReader::open(Cursor::new(bytes),PackageLimits::default())?;
    let graph=PackageGraph::build(&mut r,PackageGraphLimits::default())?;
    let i=r.entries().iter().position(|p|p.path.as_str()=="Contents/section0.xml").ok_or("part")?;
    let path=r.entries()[i].path.clone();let raw=r.read_entry(i)?;let xml=PreservingXmlDocument::parse(&raw)?;
    let leaves:Vec<_>=xml.elements().iter().enumerate().filter(|(_,n)|n.name().local_name()=="t").map(|(i,_)|i).collect();
    let mut intents=Vec::new();
    for (leaf,ranges) in specs {
        intents.push(PatchIntent::ReplaceTextAtomScalarRanges {target:XmlElementSelector::bind(&path,&xml,*leaves.get(*leaf).ok_or("leaf")?)?,
            ranges:ranges.iter().map(|(a,s,e,v)|Range::new(*a,*s,*e,v)).collect::<Result<Vec<_>,_>>()?});
    }
    if legacy {intents.push(PatchIntent::ReplaceLeafScalarRanges {target:XmlElementSelector::bind(&path,&xml,*leaves.last().ok_or("last")?)?,
        ranges:vec![LeafTextRangeReplacement::new(0,1,"&")?]});}
    let patch=PreservingPatchEngine::apply_with_limits_and_preservation_profile(&mut r,&graph,PackageGraphLimits::default(),
        IdRuleProfile::hwpml_2011_shape_v6(),IdIndexLimits::default(),limits,PreservationRuleProfile::Hangul2020PreviewTextV2,&intents)?;
    let artifact=PreservingWriter::build(&patch,PackageLimits::default(),PackageGraphLimits::default(),IdIndexLimits::default(),WriterLimits::default())?;
    let output=artifact.with_verified_bytes(<[u8]>::to_vec)?;
    let mut after=BoundedZipReader::open(Cursor::new(&output),PackageLimits::default())?;
    for index in 0..r.entries().len() {
        let original=&r.entries()[index].path;if original==&path{continue;}
        let j=after.entries().iter().position(|p|&p.path==original).ok_or("unchanged part")?;
        assert_eq!(r.read_entry(index)?,after.read_entry(j)?);
    }Ok(output)
}
fn rewrite(old:&str,new:&str,ranges:Vec<(u32,u32,u32,&str)>)->TestResult {
    let b=package(old)?;let before=section(&b)?;let digest:[u8;32]=Sha256::digest(&b).into();
    let out=apply(&b,&[(0,ranges)],Default::default(),false)?;
    assert_eq!(section(&out)?,before.replacen(old,new,1));assert_eq!(<[u8;32]>::from(Sha256::digest(&b)),digest);Ok(())
}
#[test]
fn atom_ranges_preserve_controls_entities_run_style_and_all_other_parts()->TestResult {
    // Keep the existing writer ID profile's rejection; no new charStyleIDRef rule is inferred.
    let unqualified=package("<hp:t charStyleIDRef='0'>ABC<hp:lineBreak/>DEF</hp:t>")?;
    assert!(apply(&unqualified,&[(0,vec![(0,0,1,"X")])],Default::default(),false).is_err());
    rewrite("<hp:t xmlns:k='urn:keep'>A&#x1F600;B<hp:tab width='8000' leader='0' type='0'/>C&#38;D<hp:lineBreak/>EF</hp:t>",
        "<hp:t xmlns:k='urn:keep'>A한&lt;&amp;<hp:tab width='8000' leader='0' type='0'/>C&#38;X<hp:lineBreak/>YF</hp:t>",
        vec![(0,1,3,"한<&"),(2,2,3,"X"),(4,0,1,"Y")])
}
#[test]
fn atom_ranges_leading_adjacent_and_trailing_controls_do_not_create_phantom_text_atoms()->TestResult {
    rewrite("<hp:t><hp:tab width='8000' leader='1' type='2'/><hp:lineBreak/>A&amp;B<hp:tab width='20' leader='0' type='0'/></hp:t>",
        "<hp:t><hp:tab width='8000' leader='1' type='2'/><hp:lineBreak/>AXY<hp:tab width='20' leader='0' type='0'/></hp:t>",
        vec![(2,1,2,"X"),(2,2,3,"Y")])
}
#[test]
fn atom_ranges_insert_at_text_boundaries_without_crossing_or_rewriting_control_tags()->TestResult {
    rewrite("<hp:t>AB<hp:lineBreak></hp:lineBreak>CD</hp:t>","<hp:t>XABY<hp:lineBreak></hp:lineBreak>ZCDQ</hp:t>",
        vec![(0,0,0,"X"),(0,2,2,"Y"),(2,0,0,"Z"),(2,2,2,"Q")])
}
#[test]
fn atom_ranges_delete_entire_text_atoms_but_keep_original_control_internal_whitespace()->TestResult {
    rewrite("<hp:t>A<hp:tab type='0' width='8000' leader='0'> </hp:tab>B<hp:lineBreak> </hp:lineBreak>C</hp:t>",
        "<hp:t><hp:tab type='0' width='8000' leader='0'> </hp:tab><hp:lineBreak> </hp:lineBreak></hp:t>",
        vec![(0,0,1,""),(2,0,1,""),(4,0,1,"")])
}
#[test]
fn atom_ranges_use_the_actual_search_pieces_original_atom_and_unicode_scalar_coordinates()->TestResult {
    let b=package("<hp:t>A&#x1F600;<hp:tab width='8000' leader='0' type='0'/>B&amp;C<hp:lineBreak/>Ω</hp:t>")?;
    let forms=ImportedDocumentForms::import(ImportedSourcePackage::import(&b,DocumentId::parse("atom-search")?,Sha256::digest(&b).into(),SourceImportLimits::default())?)?;
    let index=forms.body_structure().source_text_index(&b,Default::default())?;
    for (query,atom,start,end) in [("😀",0,1,2),("B&C",2,0,3),("Ω",4,0,1)] {
        let found=index.find(SourceSearchQuery {query,mode:SourceSearchMode::Literal,case_sensitive:true,whole_word:false,max_results:10})?;
        assert_eq!(found.matches().len(),1);assert_eq!(found.matches()[0].pieces.len(),1);
        let piece=&found.matches()[0].pieces[0];assert_eq!((piece.atom_index,piece.start_scalar,piece.end_scalar),(atom,start,end));
        let out=apply(&b,&[(0,vec![(piece.atom_index,piece.start_scalar,piece.end_scalar,"X")])],Default::default(),false)?;
        assert!(section(&out)?.contains("<hp:tab width='8000' leader='0' type='0'/>")&&section(&out)?.contains("<hp:lineBreak/>"));
    }Ok(())
}
#[test]
fn atom_ranges_reject_control_out_of_bounds_unsorted_overlap_empty_and_duplicate_requests_atomically()->TestResult {
    let b=package("<hp:t>ABC<hp:lineBreak/>DEF</hp:t>")?;
    for ranges in [vec![(1,0,1,"X")],vec![(0,0,99,"X")],vec![(9,0,0,"X")],vec![(2,0,1,"X"),(0,0,1,"Y")],
        vec![(0,0,2,"X"),(0,1,3,"Y")],vec![(0,1,1,"X"),(0,1,1,"Y")],vec![]] {
        assert!(apply(&b,&[(0,ranges)],Default::default(),false).is_err());
    }
    assert!(apply(&b,&[(0,vec![(0,0,1,"X")]),(0,vec![(2,0,1,"Y")])],Default::default(),false).is_err());
    assert!(apply(&b,&[(1,vec![(0,0,1,"X")])],Default::default(),true).is_err());
    assert!(Range::new(0,2,1,"X").is_err());assert!(section(&b)?.contains("ABC<hp:lineBreak/>DEF"));Ok(())
}
#[test]
fn atom_ranges_reuse_original_reader_to_reject_opaque_malformed_and_control_text_values()->TestResult {
    for leaf in ["<hp:t>A<!--KEEP-->B</hp:t>","<hp:t>A<u:future/>B</hp:t>","<hp:t>A<hp:tab/>B</hp:t>",
        "<hp:t>A<hp:tab width='1' leader='0' type='0' extra='1'/>B</hp:t>","<hp:t>A<hp:lineBreak x='1'/>B</hp:t>",
        "<hp:t>A<hp:lineBreak>TEXT</hp:lineBreak>B</hp:t>","<hp:t>A<hp:tab width='1' leader='0' type='0'><hp:lineBreak/></hp:tab>B</hp:t>",
        "<hp:t>A&#13;B</hp:t>","<hp:t>A\r\nB</hp:t>","<hp:t u:future='keep'>ABC</hp:t>"] {
        assert!(apply(&package(leaf)?,&[(0,vec![(0,0,1,"X")])],Default::default(),false).is_err());
    }
    for value in ["\t","\n","\r","\u{0}","\u{1fffe}"] {assert!(Range::new(0,0,1,value).is_err());}Ok(())
}
#[test]
fn atom_ranges_share_count_and_escaped_value_budgets_with_legacy_scalar_intents()->TestResult {
    let b=package("<hp:t>ABC<hp:lineBreak/>DEF</hp:t>")?;
    for cap in [PatchLimitConfig {max_intents:1,..Default::default()},PatchLimitConfig {max_total_output_growth:9,..Default::default()}] {
        assert!(apply(&b,&[(0,vec![(0,0,1,"&")])],PatchLimits::new(cap)?,true).is_err());
    }
    assert!(apply(&b,&[(0,vec![(0,0,1,"XX")])],PatchLimits::new(PatchLimitConfig {max_value_bytes:1,..Default::default()})?,false).is_err());
    let out=apply(&b,&[(0,vec![(0,0,1,"&")])],PatchLimits::new(PatchLimitConfig {max_intents:2,max_total_output_growth:10,..Default::default()})?,true)?;
    assert!(section(&out)?.contains("&amp;BC<hp:lineBreak/>DEF"));Ok(())
}
#[test]
fn atom_ranges_reject_stale_and_non_text_selectors_before_writer_publication()->TestResult {
    let b=package("<hp:t>ABC<hp:lineBreak/>DEF</hp:t>")?;
    let mut r=BoundedZipReader::open(Cursor::new(&b),PackageLimits::default())?;let graph=PackageGraph::build(&mut r,PackageGraphLimits::default())?;
    let i=r.entries().iter().position(|p|p.path.as_str()=="Contents/section0.xml").ok_or("part")?;let path=r.entries()[i].path.clone();
    let raw=r.read_entry(i)?;
    for (source,local) in [(String::from_utf8(raw.clone())?.replace("ABC","XYZ"),"t"),(String::from_utf8(raw)?,"run")] {
        let xml=PreservingXmlDocument::parse(source.as_bytes())?;let at=xml.elements().iter().position(|n|n.name().local_name()==local).ok_or("element")?;
        let intent=PatchIntent::ReplaceTextAtomScalarRanges {target:XmlElementSelector::bind(&path,&xml,at)?,ranges:vec![Range::new(0,0,1,"X")?]};
        assert!(PreservingPatchEngine::apply_with_limits_and_preservation_profile(&mut r,&graph,PackageGraphLimits::default(),IdRuleProfile::hwpml_2011_shape_v6(),
            IdIndexLimits::default(),Default::default(),PreservationRuleProfile::Hangul2020PreviewTextV2,&[intent]).is_err());
    }Ok(())
}
#[test]
fn atom_ranges_many_selections_share_one_target_and_preserve_private_values_and_controls()->TestResult {
    let text="A&#x1F600;&amp;<hp:lineBreak/>".repeat(100);let b=package(&format!("<hp:t>{text}</hp:t>"))?;
    let ranges:Vec<_>=(0..100).map(|i|(i*2,0,1,"PRIVATE-REPLACEMENT")).collect();let specs=vec![(0,ranges)];
    let first=apply(&b,&specs,Default::default(),false)?;assert_eq!(first,apply(&b,&specs,Default::default(),false)?);
    assert_eq!(section(&first)?.matches("PRIVATE-REPLACEMENT&#x1F600;&amp;<hp:lineBreak/>").count(),100);
    let range=Range::new(0,0,1,"PRIVATE-REPLACEMENT")?;assert!(!format!("{range:?}").contains("PRIVATE"));Ok(())
}
