use std::error::Error;
use std::io::{Cursor, Write};

use hwpx_package::{
    BoundedZipReader, IdDeclaration, IdIndex, IdIndexError, IdIndexLimitConfig, IdIndexLimits,
    IdIssueKind, IdKind, IdRuleProfile, IdValidationIssue, PackageGraph, PackageGraphLimits,
    PackageLimits,
};
use zip::write::SimpleFileOptions;
use zip::{CompressionMethod, ZipWriter};

type TestResult = Result<(), Box<dyn Error>>;
type TestReader = BoundedZipReader<Cursor<Vec<u8>>>;
type OpenedGraph = (TestReader, PackageGraph);

const CONTAINER: &str = r#"<?xml version="1.0" encoding="UTF-8"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">
  <rootfiles><rootfile full-path="Contents/content.hpf" media-type="application/oebps-package+xml"/></rootfiles>
</container>"#;

const HEADER: &str = r#"<h:head xmlns:h="http://www.hancom.co.kr/hwpml/2011/head">
  <h:fontface lang="HANGUL"><h:font id="1"/></h:fontface>
  <h:fontface lang="LATIN"><h:font id="1"/></h:fontface>
  <h:fontface lang="HANJA"><h:font id="1"/></h:fontface>
  <h:fontface lang="JAPANESE"><h:font id="1"/></h:fontface>
  <h:fontface lang="OTHER"><h:font id="1"/></h:fontface>
  <h:fontface lang="SYMBOL"><h:font id="1"/></h:fontface>
  <h:fontface lang="USER"><h:font id="1"/></h:fontface>
  <h:borderFill id="1"/>
  <h:charPr id="1" borderFillIDRef="01"><h:fontRef hangul="1" latin="1" hanja="1" japanese="1" other="1" symbol="1" user="1"/></h:charPr>
  <h:tabPr id="1"/>
  <h:numbering id="1"/>
  <h:bullet id="1"/>
  <h:paraPr id="1" tabPrIDRef="1"><h:heading type="OUTLINE" idRef="0"/><h:paraHead charPrIDRef="1"/></h:paraPr>
  <h:style id="1" charPrIDRef="1" paraPrIDRef="1" nextStyleIDRef="1"/>
  <h:memoShape id="1"/>
</h:head>"#;

const SECTION: &str = r#"<q:section xmlns:q="http://www.hancom.co.kr/hwpml/2011/paragraph">
  <q:secPr id="section-one" memoShapeIDRef="1" outlineShapeIDRef="1">
    <q:colPr id="column-one"/>
    <q:pageBorderFill borderFillIDRef="1"/>
  </q:secPr>
  <q:p id="0"/><q:p id="00"/>
  <q:p id="1" paraPrIDRef="1" styleIDRef="01"><q:run charPrIDRef="1"/></q:p>
</q:section>"#;

#[test]
fn current_2020_core_profile_indexes_typed_cross_part_references_without_value_leak() -> TestResult
{
    let bytes = valid_archive(Some(HEADER), SECTION, "PRIVATE-PACKAGE-ID")?;
    let (mut reader, mut graph) = open_graph(bytes)?;
    graph.parts.reverse();
    let index = IdIndex::build(
        &mut reader,
        &graph,
        IdRuleProfile::current_hancom_2020_core_v1(),
        IdIndexLimits::default(),
    )?;

    assert_eq!(index.profile_version(), "hancom-2020-hwpml-2011-core/v1");
    assert_eq!(index.parts_scanned(), 5);
    assert_eq!(index.declarations().len(), 21);
    assert_eq!(index.references().len(), 20);
    assert!(index.references().iter().all(|reference| {
        index
            .declaration_for(reference)
            .is_some_and(|declaration| declaration.kind() == reference.expected_kind())
    }));
    let cross_part = index
        .references()
        .iter()
        .filter(|reference| reference.location().part() != reference.target_part())
        .count();
    assert_eq!(cross_part, 6);
    let kinds_with_decimal_one = index
        .declarations()
        .iter()
        .filter(|declaration| declaration.location().part().as_str() == "Contents/header.xml")
        .map(IdDeclaration::kind)
        .collect::<std::collections::BTreeSet<_>>();
    assert!(kinds_with_decimal_one.contains(&IdKind::FontHangul));
    assert!(kinds_with_decimal_one.contains(&IdKind::FontLatin));
    assert!(kinds_with_decimal_one.contains(&IdKind::FontHanja));
    assert!(kinds_with_decimal_one.contains(&IdKind::FontJapanese));
    assert!(kinds_with_decimal_one.contains(&IdKind::FontOther));
    assert!(kinds_with_decimal_one.contains(&IdKind::FontSymbol));
    assert!(kinds_with_decimal_one.contains(&IdKind::FontUser));
    assert!(kinds_with_decimal_one.contains(&IdKind::CharacterProperties));
    assert!(kinds_with_decimal_one.contains(&IdKind::Style));

    let debug = format!("{index:?}");
    assert!(!debug.contains("PRIVATE-PACKAGE-ID"));
    assert!(!debug.contains("section-one"));

    let zero_sentinels = SECTION
        .replace("memoShapeIDRef=\"1\"", "memoShapeIDRef=\"0\"")
        .replace("outlineShapeIDRef=\"1\"", "outlineShapeIDRef=\"00\"");
    let (mut reader, graph) = open_graph(valid_archive(Some(HEADER), &zero_sentinels, "pkg")?)?;
    let sentinel_index = IdIndex::build(
        &mut reader,
        &graph,
        IdRuleProfile::current_hancom_2020_core_v1(),
        IdIndexLimits::default(),
    )?;
    assert_eq!(sentinel_index.references().len(), 18);

    let para_head_sentinel = HEADER.replace("charPrIDRef=\"1\"/>", "charPrIDRef=\"4294967295\"/>");
    let (mut reader, graph) =
        open_graph(valid_archive(Some(&para_head_sentinel), SECTION, "pkg")?)?;
    let sentinel_index = IdIndex::build(
        &mut reader,
        &graph,
        IdRuleProfile::current_hancom_2020_core_v1(),
        IdIndexLimits::default(),
    )?;
    assert_eq!(sentinel_index.references().len(), 19);

    let empty_metadata = SECTION
        .replace("id=\"section-one\"", "id=\"\"")
        .replace("id=\"column-one\"", "id=\"\"");
    let (mut reader, graph) = open_graph(valid_archive(Some(HEADER), &empty_metadata, "")?)?;
    let empty_index = IdIndex::build(
        &mut reader,
        &graph,
        IdRuleProfile::current_hancom_2020_core_v1(),
        IdIndexLimits::default(),
    )?;
    assert_eq!(empty_index.declarations().len(), 18);
    Ok(())
}

#[test]
fn duplicate_dangling_and_wrong_type_are_distinct_fail_closed_diagnostics() -> TestResult {
    let duplicate = HEADER.replace(
        "</h:head>",
        "<h:style id=\"1\" charPrIDRef=\"1\" paraPrIDRef=\"1\" nextStyleIDRef=\"1\"/></h:head>",
    );
    assert_issue(
        valid_archive(Some(&duplicate), SECTION, "pkg")?,
        IdIssueKind::DuplicateDeclaration,
    )?;

    let dangling = SECTION.replace("styleIDRef=\"01\"", "styleIDRef=\"99\"");
    assert_issue(
        valid_archive(Some(HEADER), &dangling, "pkg")?,
        IdIssueKind::DanglingReference,
    )?;

    let wrong_header = HEADER.replace(
        "</h:head>",
        "<h:charPr id=\"7\" borderFillIDRef=\"1\"/></h:head>",
    );
    let wrong_section = SECTION.replace("styleIDRef=\"01\"", "styleIDRef=\"7\"");
    let error = build_error(valid_archive(Some(&wrong_header), &wrong_section, "pkg")?)?;
    let issue = error
        .validation()
        .and_then(|report| {
            report
                .issues()
                .iter()
                .find(|issue| issue.kind() == IdIssueKind::WrongTypeReference)
        })
        .ok_or_else(|| std::io::Error::other("wrong-type issue missing"))?;
    assert_eq!(issue.expected_kind(), Some(IdKind::Style));
    assert_eq!(issue.actual_kind(), Some(IdKind::CharacterProperties));
    assert!(issue.related().is_some());
    Ok(())
}

#[test]
fn malformed_unknown_and_missing_target_never_produce_a_partial_index() -> TestResult {
    let malformed = HEADER.replacen("<h:font id=\"1\"/>", "<h:font id=\"not-decimal\"/>", 1);
    assert_issue(
        valid_archive(Some(&malformed), SECTION, "pkg")?,
        IdIssueKind::MalformedValue,
    )?;

    let unknown = SECTION.replace(
        "<q:p id=\"1\"",
        "<q:p id=\"1\" mysteryIDRef=\"SECRET-VALUE\"",
    );
    let error = build_error(valid_archive(Some(HEADER), &unknown, "pkg")?)?;
    assert!(validation_codes(&error).contains(&"id_index_unknown_id_like_attribute"));
    assert!(!format!("{error:?}").contains("SECRET-VALUE"));

    let unsupported_heading = HEADER.replace("idRef=\"0\"", "idRef=\"2\"");
    assert_issue(
        valid_archive(Some(&unsupported_heading), SECTION, "pkg")?,
        IdIssueKind::UnknownIdLikeAttribute,
    )?;

    assert_issue(
        valid_archive(None, SECTION, "pkg")?,
        IdIssueKind::TargetPartMissing,
    )?;
    Ok(())
}

#[test]
fn finite_limits_reject_zero_ceiling_and_runtime_overflow() -> TestResult {
    let invalid = IdIndexLimits::new(IdIndexLimitConfig {
        max_parts: 0,
        ..IdIndexLimitConfig::default()
    });
    let Err(error) = invalid else {
        panic!("zero limit was accepted");
    };
    assert_eq!(error.code(), "id_index_invalid_limit");

    let invalid = IdIndexLimits::new(IdIndexLimitConfig {
        max_references: IdIndexLimits::HARD_MAX_REFERENCES + 1,
        ..IdIndexLimitConfig::default()
    });
    let Err(error) = invalid else {
        panic!("over-ceiling limit was accepted");
    };
    assert_eq!(error.code(), "id_index_invalid_limit");

    let limits = IdIndexLimits::new(IdIndexLimitConfig {
        max_declarations: 1,
        ..IdIndexLimitConfig::default()
    })?;
    let bytes = valid_archive(Some(HEADER), SECTION, "pkg")?;
    let (mut reader, graph) = open_graph(bytes)?;
    let Err(error) = IdIndex::build(
        &mut reader,
        &graph,
        IdRuleProfile::current_hancom_2020_core_v1(),
        limits,
    ) else {
        panic!("declaration overflow was accepted");
    };
    assert_eq!(error.code(), "id_index_limit_exceeded");
    Ok(())
}

#[test]
fn rejected_preservation_part_blocks_indexing_before_semantic_downgrade() -> TestResult {
    let unsafe_header = "<!DOCTYPE head [<!ENTITY x 'value'>]><head/>";
    let bytes = valid_archive(Some(unsafe_header), SECTION, "pkg")?;
    let (mut reader, graph) = open_graph(bytes)?;
    let Err(error) = IdIndex::build(
        &mut reader,
        &graph,
        IdRuleProfile::current_hancom_2020_core_v1(),
        IdIndexLimits::default(),
    ) else {
        panic!("rejected XML was indexed");
    };
    assert_eq!(error.code(), "id_index_preservation_rejected");
    Ok(())
}

fn assert_issue(bytes: Vec<u8>, expected: IdIssueKind) -> TestResult {
    let error = build_error(bytes)?;
    let report = error
        .validation()
        .ok_or_else(|| std::io::Error::other("validation report missing"))?;
    assert!(report.issues().iter().any(|issue| issue.kind() == expected));
    Ok(())
}

fn validation_codes(error: &IdIndexError) -> Vec<&'static str> {
    error
        .validation()
        .map(|report| {
            report
                .issues()
                .iter()
                .map(IdValidationIssue::code)
                .collect()
        })
        .unwrap_or_default()
}

fn build_error(bytes: Vec<u8>) -> Result<IdIndexError, Box<dyn Error>> {
    let (mut reader, graph) = open_graph(bytes)?;
    let Err(error) = IdIndex::build(
        &mut reader,
        &graph,
        IdRuleProfile::current_hancom_2020_core_v1(),
        IdIndexLimits::default(),
    ) else {
        return Err(std::io::Error::other("invalid fixture produced an index").into());
    };
    Ok(error)
}

fn valid_archive(
    header: Option<&str>,
    section: &str,
    package_id: &str,
) -> Result<Vec<u8>, zip::result::ZipError> {
    let header_item = if header.is_some() {
        r#"<o:item id="header" href="header.xml" media-type="application/xml"/>"#
    } else {
        ""
    };
    let opf = format!(
        r#"<?xml version="1.0" encoding="UTF-8"?>
<o:package xmlns:o="http://www.idpf.org/2007/opf/" id="{package_id}" version="2.0">
  <o:manifest>
    {header_item}
    <o:item id="section0" href="section0.xml" media-type="application/xml"/>
  </o:manifest>
  <o:spine><o:itemref idref="section0" linear="yes"/></o:spine>
</o:package>"#
    );
    let mut entries = vec![
        entry(
            "mimetype",
            b"application/hwp+zip",
            CompressionMethod::Stored,
        ),
        entry("version.xml", b"<version/>", CompressionMethod::Stored),
        entry(
            "META-INF/container.xml",
            CONTAINER.as_bytes(),
            CompressionMethod::Deflated,
        ),
        entry(
            "Contents/content.hpf",
            opf.as_bytes(),
            CompressionMethod::Deflated,
        ),
    ];
    if let Some(header) = header {
        entries.push(entry(
            "Contents/header.xml",
            header.as_bytes(),
            CompressionMethod::Deflated,
        ));
    }
    entries.push(entry(
        "Contents/section0.xml",
        section.as_bytes(),
        CompressionMethod::Deflated,
    ));
    archive(entries)
}

fn entry(
    name: &str,
    bytes: &[u8],
    method: CompressionMethod,
) -> (String, Vec<u8>, CompressionMethod) {
    (name.to_owned(), bytes.to_vec(), method)
}

fn archive(
    entries: Vec<(String, Vec<u8>, CompressionMethod)>,
) -> Result<Vec<u8>, zip::result::ZipError> {
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    for (name, bytes, method) in entries {
        let options = SimpleFileOptions::default().compression_method(method);
        writer.start_file(name, options)?;
        writer.write_all(&bytes)?;
    }
    Ok(writer.finish()?.into_inner())
}

fn open_graph(bytes: Vec<u8>) -> Result<OpenedGraph, Box<dyn Error>> {
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    Ok((reader, graph))
}
