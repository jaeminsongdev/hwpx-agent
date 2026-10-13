use hwpx_package::{
    BoundedZipReader, IdIndexLimits, IdRuleProfile, PackageGraph, PackageGraphLimits,
    PackageLimits, PatchIntent, PatchLimits, PatchText, PreservationRuleProfile,
    PreservingPatchEngine, PreservingWriter, PreservingXmlDocument, WriterLimits,
    XmlElementSelector,
};
use std::io::Cursor;
#[path = "support/document_import_field_fixture.rs"]
mod fixture;
type TestResult = Result<(), Box<dyn std::error::Error>>;
fn replace(leaf: &str, name: &str, value: &str) -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    let bytes = fixture::package(&format!(
        "<hp:p id='1'><hp:run>{leaf}<hp:t>UNCHANGED</hp:t></hp:run></hp:p>"
    ))?;
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    let index = reader
        .entries()
        .iter()
        .position(|p| p.path.as_str() == "Contents/section0.xml")
        .ok_or("part")?;
    let path = reader.entries()[index].path.clone();
    let old = reader.read_entry(index)?;
    let xml = PreservingXmlDocument::parse(&old)?;
    let index = xml
        .elements()
        .iter()
        .position(|n| n.name().local_name() == name)
        .ok_or("element")?;
    let intent = PatchIntent::ReplaceLeafText {
        target: XmlElementSelector::bind(&path, &xml, index)?,
        value: PatchText::new(value)?,
    };
    assert!(!format!("{intent:?}").contains("PRIVATE-VALUE"));
    let patch = PreservingPatchEngine::apply_with_limits_and_preservation_profile(
        &mut reader,
        &graph,
        PackageGraphLimits::default(),
        IdRuleProfile::current_hancom_2020_formula_v3(),
        IdIndexLimits::default(),
        PatchLimits::default(),
        PreservationRuleProfile::Hangul2020PreviewTextV2,
        &[intent],
    )?;
    let output = PreservingWriter::build(
        &patch,
        PackageLimits::default(),
        PackageGraphLimits::default(),
        IdIndexLimits::default(),
        WriterLimits::default(),
    )?;
    Ok(output.with_verified_bytes(<[u8]>::to_vec)?)
}
#[test]
fn empty_self_closing_entity_and_text_leaves_keep_original_names_attributes_and_siblings()
-> TestResult {
    fixture::forms(&fixture::captured()?, "patch-leaf")?;
    for (old, new) in [
        (
            "<hp:t u:flag='X' />",
            "<hp:t u:flag='X' >PRIVATE-VALUE &amp; &lt;X&gt;</hp:t>",
        ),
        (
            "<hp:t u:flag='X'></hp:t>",
            "<hp:t u:flag='X'>PRIVATE-VALUE &amp; &lt;X&gt;</hp:t>",
        ),
        (
            "<hp:t u:flag='X'>a&amp;b</hp:t>",
            "<hp:t u:flag='X'>PRIVATE-VALUE &amp; &lt;X&gt;</hp:t>",
        ),
    ] {
        let output = replace(old, "t", "PRIVATE-VALUE & <X>")?;
        let mut reader = BoundedZipReader::open(Cursor::new(output), PackageLimits::default())?;
        let i = reader
            .entries()
            .iter()
            .position(|p| p.path.as_str() == "Contents/section0.xml")
            .ok_or("part")?;
        let next = reader.read_entry(i)?;
        let mut original = BoundedZipReader::open(
            Cursor::new(fixture::package(&format!(
                "<hp:p id='1'><hp:run>{old}<hp:t>UNCHANGED</hp:t></hp:run></hp:p>"
            ))?),
            PackageLimits::default(),
        )?;
        assert_eq!(
            next,
            String::from_utf8(original.read_entry(i)?)?
                .replacen(old, new, 1)
                .as_bytes()
        );
    }
    Ok(())
}
#[test]
fn comments_child_elements_root_and_invalid_xml_values_cannot_be_erased_or_injected() -> TestResult
{
    for leaf in ["<hp:t><!--KEEP-->old</hp:t>", "<hp:t><hp:tab/></hp:t>"] {
        assert!(replace(leaf, "t", "new").is_err());
    }
    assert!(replace("<hp:t>old</hp:t>", "sec", "new").is_err());
    assert!(PatchText::new("bad\u{0000}").is_err());
    Ok(())
}
