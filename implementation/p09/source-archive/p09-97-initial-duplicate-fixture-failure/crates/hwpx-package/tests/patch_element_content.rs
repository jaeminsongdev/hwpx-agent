//! Original generic engine validates new content edits; no semantic/native acceptance claim.
use hwpx_package::{
    BoundedZipReader, IdIndexLimits, IdRuleProfile, PackageGraph, PackageGraphLimits,
    PackageLimits, PackagePath, PatchIntent, PatchLimitConfig, PatchLimits,
    PreservationRuleProfile, PreservingPatchEngine, PreservingWriter, PreservingXmlDocument,
    ValidatedXmlFragment, WriterLimits, XmlElementSelector,
};
use std::{error::Error, io::Cursor};
#[path = "support/document_import_field_fixture.rs"]
mod fixture;
type TestResult = Result<(), Box<dyn Error>>;
type Reader = BoundedZipReader<Cursor<Vec<u8>>>;
type Context = (
    Reader,
    PackageGraph,
    PackagePath,
    PreservingXmlDocument,
    usize,
);
fn opened() -> Result<Context, Box<dyn Error>> {
    let bytes = fixture::package(
        "<hp:p id='1'><hp:run><hp:hiddenComment><hp:subList u:flag='PRIVATE-ATTR'><hp:p id='2'><hp:run><hp:t>OLD</hp:t></hp:run></hp:p></hp:subList></hp:hiddenComment><hp:t>OUTSIDE</hp:t></hp:run></hp:p>",
    )?;
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    let index = reader
        .entries()
        .iter()
        .position(|e| e.path.as_str() == "Contents/section0.xml")
        .ok_or("part")?;
    let path = reader.entries()[index].path.clone();
    let xml = PreservingXmlDocument::parse(&reader.read_entry(index)?)?;
    let body = xml
        .elements()
        .iter()
        .position(|e| e.name().local_name() == "subList")
        .ok_or("body")?;
    Ok((reader, graph, path, xml, body))
}
fn child() -> Result<ValidatedXmlFragment, Box<dyn Error>> {
    Ok(ValidatedXmlFragment::parse(b"<hp:p xmlns:hp='http://www.hancom.co.kr/hwpml/2011/paragraph' id='9'><hp:run><hp:t>NEW-PRIVATE</hp:t></hp:run></hp:p>", PatchLimits::default())?)
}
fn apply(
    reader: &mut Reader,
    graph: &PackageGraph,
    intents: &[PatchIntent],
    limits: PatchLimits,
) -> Result<hwpx_package::PatchResult, hwpx_package::PatchError> {
    PreservingPatchEngine::apply_with_limits_and_preservation_profile(
        reader,
        graph,
        PackageGraphLimits::default(),
        IdRuleProfile::current_hancom_2020_formula_v3(),
        IdIndexLimits::default(),
        limits,
        PreservationRuleProfile::Hangul2020PreviewTextV2,
        intents,
    )
}
#[test]
fn content_only_edit_preserves_inherited_namespace_wrapper_unknown_attributes_and_all_other_bytes()
-> TestResult {
    let (mut reader, graph, path, xml, index) = opened()?;
    let source_index = reader
        .entries()
        .iter()
        .position(|e| e.path.as_str() == path.as_str())
        .ok_or("part")?;
    let original = reader.read_entry(source_index)?;
    let intent = PatchIntent::ReplaceElementContent {
        target: XmlElementSelector::bind(&path, &xml, index)?,
        children: vec![child()?, child()?],
    };
    assert!(!format!("{intent:?}").contains("NEW-PRIVATE"));
    let patch = apply(&mut reader, &graph, &[intent], PatchLimits::default())?;
    assert_eq!(patch.changed_parts(), 1);
    assert_eq!(patch.added_parts(), 0);
    let output = PreservingWriter::build(
        &patch,
        PackageLimits::default(),
        PackageGraphLimits::default(),
        IdIndexLimits::default(),
        WriterLimits::default(),
    )?;
    output.with_verified_bytes(|bytes| -> TestResult {
        let mut result = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
        let i = result
            .entries()
            .iter()
            .position(|e| e.path.as_str() == path.as_str())
            .ok_or("part")?;
        let part = result.read_entry(i)?;
        let next = PreservingXmlDocument::parse(&part)?;
        let body = next
            .elements()
            .iter()
            .find(|e| e.name().local_name() == "subList")
            .ok_or("body")?;
        let old = xml.elements()[index].content_span().ok_or("content")?;
        let new = body.content_span().ok_or("content")?;
        assert!(
            original[..old.start()] == part[..new.start()]
                && original[old.end()..] == part[new.end()..]
        );
        Ok(())
    })??;
    Ok(())
}
#[test]
fn content_children_and_aggregate_fragment_limits_are_checked_before_output_allocation()
-> TestResult {
    for config in [
        PatchLimitConfig {
            max_intents: 1,
            ..PatchLimitConfig::default()
        },
        PatchLimitConfig {
            max_fragment_bytes: 150,
            ..PatchLimitConfig::default()
        },
    ] {
        let (mut reader, graph, path, xml, index) = opened()?;
        let intent = PatchIntent::ReplaceElementContent {
            target: XmlElementSelector::bind(&path, &xml, index)?,
            children: vec![child()?, child()?],
        };
        assert!(apply(&mut reader, &graph, &[intent], PatchLimits::new(config)?).is_err());
    }
    Ok(())
}
#[test]
fn overlapping_content_and_descendant_edits_remain_atomic_conflicts() -> TestResult {
    let (mut reader, graph, path, xml, index) = opened()?;
    let descendant = xml.elements()[index].first_child().ok_or("child")?;
    let intents = [
        PatchIntent::ReplaceElementContent {
            target: XmlElementSelector::bind(&path, &xml, index)?,
            children: vec![child()?],
        },
        PatchIntent::DeleteSubtree {
            target: XmlElementSelector::bind(&path, &xml, descendant)?,
        },
    ];
    assert!(apply(&mut reader, &graph, &intents, PatchLimits::default()).is_err());
    Ok(())
}
#[test]
fn self_closing_content_target_and_dangling_output_style_are_rejected_by_original_guards()
-> TestResult {
    let captured = fixture::captured()?;
    let mut foreign = BoundedZipReader::open(Cursor::new(captured), PackageLimits::default())?;
    let i = foreign
        .entries()
        .iter()
        .position(|e| e.path.as_str() == "Contents/section0.xml")
        .ok_or("part")?;
    let path = foreign.entries()[i].path.clone();
    let xml = PreservingXmlDocument::parse(&foreign.read_entry(i)?)?;
    let stale = XmlElementSelector::bind(&path, &xml, xml.root_element())?;
    let (mut reader, graph, _, _, _) = opened()?;
    assert!(
        apply(
            &mut reader,
            &graph,
            &[PatchIntent::ReplaceElementContent {
                target: stale,
                children: vec![child()?]
            }],
            PatchLimits::default()
        )
        .is_err()
    );
    let (mut reader, graph, path, xml, _) = opened()?;
    let target = XmlElementSelector::bind(&path, &xml, xml.root_element())?;
    let bad = ValidatedXmlFragment::parse(
        b"<hp:p xmlns:hp='http://www.hancom.co.kr/hwpml/2011/paragraph' styleIDRef='987'/>",
        PatchLimits::default(),
    )?;
    assert!(
        apply(
            &mut reader,
            &graph,
            &[PatchIntent::ReplaceElementContent {
                target,
                children: vec![bad]
            }],
            PatchLimits::default()
        )
        .is_err()
    );
    let (mut reader, graph, _, _, _) = opened()?;
    let i = reader
        .entries()
        .iter()
        .position(|e| e.path.as_str() == "Contents/header.xml")
        .ok_or("header")?;
    let path = reader.entries()[i].path.clone();
    let xml = PreservingXmlDocument::parse(&reader.read_entry(i)?)?;
    let target = XmlElementSelector::bind(&path, &xml, xml.root_element())?;
    assert!(
        apply(
            &mut reader,
            &graph,
            &[PatchIntent::ReplaceElementContent {
                target,
                children: vec![child()?]
            }],
            PatchLimits::default()
        )
        .is_err()
    );
    Ok(())
}
