use std::error::Error;
use std::io::{Cursor, Write};

use hwpx_agent_foundation::workdir::SecureWorkspace;
use hwpx_package::{
    AddedPart, AllocationHandle, AtomicPackagePublisher, BoundedZipReader, IdIndexLimits, IdKind,
    MetadataDisposition, NormalizedWriter, PackageGraph, PackageGraphLimits, PackageLimits,
    PatchAttributeValue, PatchError, PatchIntent, PatchLimitConfig, PatchLimits,
    PatchPartDisposition, PatchText, PreservingPatchEngine, PreservingWriter,
    PreservingXmlDocument, RelationshipAddition, RelationshipSpine, SiblingPosition,
    ValidatedXmlFragment, WriterLimitConfig, WriterLimits, WriterMode, XmlAttributeSelector,
    XmlElementSelector, XmlTextSelector, XmlTokenKind,
};
use sha2::{Digest as _, Sha256};
use tempfile::tempdir;
use zip::write::SimpleFileOptions;
use zip::{CompressionMethod, ZipWriter};

type TestResult = Result<(), Box<dyn Error>>;
type TestReader = BoundedZipReader<Cursor<Vec<u8>>>;
type OpenedGraph = (TestReader, PackageGraph);

const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";

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
  <h:charPr id="1" borderFillIDRef="1"><h:fontRef hangul="1" latin="1" hanja="1" japanese="1" other="1" symbol="1" user="1"/></h:charPr>
  <h:tabPr id="1"/>
  <h:numbering id="1"/>
  <h:bullet id="1"/>
  <h:paraPr id="1" tabPrIDRef="1"><h:heading type="OUTLINE" idRef="0"/><h:paraHead charPrIDRef="1"/></h:paraPr>
  <h:style id="1" charPrIDRef="1" paraPrIDRef="1" nextStyleIDRef="1"/>
  <h:memoShape id="1"/>
</h:head>"#;

const SECTION: &str = r#"<q:section xmlns:q="http://www.hancom.co.kr/hwpml/2011/paragraph">
  <q:p id="0"/>
  <q:p id="1" paraPrIDRef="1" styleIDRef="1"><q:run charPrIDRef="1"><q:t title="old">ORIGINAL</q:t><q:note>note</q:note><q:replace>replace</q:replace><q:delete>delete</q:delete></q:run></q:p>
</q:section>"#;

#[test]
fn five_xml_intents_are_surgical_and_keep_every_other_part_exact() -> TestResult {
    let bytes = valid_archive(SECTION)?;
    let (mut reader, graph) = open_graph(bytes.clone())?;
    let (path, document) = part_document(&mut reader, &graph, "Contents/section0.xml")?;
    let text_element = element(&document, "t", 0)?;
    let title = attribute(&document, text_element, "title")?;
    let text_token = text_token(&document, text_element)?;
    let note = element(&document, "note", 0)?;
    let replace = element(&document, "replace", 0)?;
    let delete = element(&document, "delete", 0)?;
    let insert = ValidatedXmlFragment::parse(
        format!(r#"<q:inserted xmlns:q="{PARAGRAPH_NS}">PRIVATE-INSERT</q:inserted>"#).as_bytes(),
        PatchLimits::default(),
    )?;
    let replacement = ValidatedXmlFragment::parse(
        format!(r#"<q:replaced xmlns:q="{PARAGRAPH_NS}">PRIVATE-REPLACE</q:replaced>"#).as_bytes(),
        PatchLimits::default(),
    )?;
    let intents = vec![
        PatchIntent::ReplaceAttribute {
            target: XmlAttributeSelector::bind(&path, &document, text_element, title)?,
            value: PatchAttributeValue::Text(PatchText::new("PRIVATE-ATTR-\"<&")?),
        },
        PatchIntent::ReplaceText {
            target: XmlTextSelector::bind(&path, &document, text_token)?,
            value: PatchText::new("PRIVATE-TEXT-<&>")?,
        },
        PatchIntent::InsertSibling {
            target: XmlElementSelector::bind(&path, &document, note)?,
            position: SiblingPosition::Before,
            fragment: insert,
        },
        PatchIntent::ReplaceSubtree {
            target: XmlElementSelector::bind(&path, &document, replace)?,
            fragment: replacement,
        },
        PatchIntent::DeleteSubtree {
            target: XmlElementSelector::bind(&path, &document, delete)?,
        },
    ];
    let result = PreservingPatchEngine::apply(&mut reader, &graph, &intents)?;

    result.verify_artifact_integrity()?;
    assert_eq!(result.intent_count(), 5);
    assert_eq!(result.changed_parts(), 1);
    assert_eq!(result.added_parts(), 0);
    assert_eq!(result.untouched_parts() + result.changed_parts(), 6);
    assert_eq!(
        part_disposition(&result, "Contents/section0.xml")?,
        PatchPartDisposition::Changed
    );
    assert!(result.parts().iter().all(|record| {
        record.disposition() != PatchPartDisposition::Untouched
            || record.source_sha256() == Some(record.output_sha256())
    }));
    let debug = format!("{intents:?} {result:?}");
    for secret in [
        "PRIVATE-ATTR",
        "PRIVATE-TEXT",
        "PRIVATE-INSERT",
        "PRIVATE-REPLACE",
    ] {
        assert!(!debug.contains(secret));
    }
    Ok(())
}

#[test]
fn overlap_stale_root_and_malicious_fragments_fail_before_publication() -> TestResult {
    let bytes = valid_archive(SECTION)?;
    let (mut reader, graph) = open_graph(bytes.clone())?;
    let (path, document) = part_document(&mut reader, &graph, "Contents/section0.xml")?;
    let run = element(&document, "run", 0)?;
    let text_element = element(&document, "t", 0)?;
    let token = text_token(&document, text_element)?;
    let conflicting = [
        PatchIntent::DeleteSubtree {
            target: XmlElementSelector::bind(&path, &document, run)?,
        },
        PatchIntent::ReplaceText {
            target: XmlTextSelector::bind(&path, &document, token)?,
            value: PatchText::new("nested")?,
        },
    ];
    assert_code(
        PreservingPatchEngine::apply(&mut reader, &graph, &conflicting),
        "patch_conflict",
    );

    let root = XmlElementSelector::bind(&path, &document, document.root_element())?;
    let root_delete = [PatchIntent::DeleteSubtree { target: root }];
    assert_code(
        PreservingPatchEngine::apply(&mut reader, &graph, &root_delete),
        "patch_root_mutation",
    );

    let drifted = SECTION.replace("ORIGINAL", "DRIFTED");
    let (mut drift_reader, drift_graph) = open_graph(valid_archive(&drifted)?)?;
    let stale = [PatchIntent::ReplaceText {
        target: XmlTextSelector::bind(&path, &document, token)?,
        value: PatchText::new("new")?,
    }];
    assert_code(
        PreservingPatchEngine::apply(&mut drift_reader, &drift_graph, &stale),
        "patch_selector_stale",
    );

    assert!(
        ValidatedXmlFragment::parse(
            b"<!DOCTYPE x [<!ENTITY e 'SECRET'>]><x/>",
            PatchLimits::default()
        )
        .is_err()
    );
    assert!(
        ValidatedXmlFragment::parse(b"<?xml version=\"1.0\"?><x/>", PatchLimits::default())
            .is_err()
    );
    assert!(ValidatedXmlFragment::parse(b" <x/>", PatchLimits::default()).is_err());
    assert!(PatchText::new("bad\u{1}value").is_err());
    let fragment = ValidatedXmlFragment::parse(b"<x/>", PatchLimits::default())?;
    let tight_fragment = PatchLimits::new(PatchLimitConfig {
        max_fragment_bytes: 1,
        ..PatchLimitConfig::default()
    })?;
    let limited = [PatchIntent::InsertSibling {
        target: XmlElementSelector::bind(&path, &document, run)?,
        position: SiblingPosition::Before,
        fragment,
    }];
    assert_code(
        PreservingPatchEngine::apply_with_limits(
            &mut reader,
            &graph,
            PackageGraphLimits::default(),
            hwpx_package::IdRuleProfile::current_hancom_2020_core_v1(),
            hwpx_package::IdIndexLimits::default(),
            tight_fragment,
            &limited,
        ),
        "patch_limit_exceeded",
    );
    let directory_part = AddedPart::xml(
        "Contents/new.xml/",
        "application/xml",
        b"<x/>",
        PackageLimits::default(),
        PackageGraphLimits::default(),
        PatchLimits::default(),
    );
    assert!(matches!(directory_part, Err(PatchError::PartPathInvalid)));
    Ok(())
}

#[test]
fn deterministic_id_reservation_rolls_back_on_post_validation_failure() -> TestResult {
    let bytes = valid_archive(SECTION)?;
    let (mut reader, graph) = open_graph(bytes.clone())?;
    let (path, document) = part_document(&mut reader, &graph, "Contents/section0.xml")?;
    let zero_paragraph = element(&document, "p", 0)?;
    let zero_id = attribute(&document, zero_paragraph, "id")?;
    let live_paragraph = element(&document, "p", 1)?;
    let style_reference = attribute(&document, live_paragraph, "styleIDRef")?;
    let handle = AllocationHandle::new(7);
    let allocate = PatchIntent::AllocateId {
        target: XmlAttributeSelector::bind(&path, &document, zero_paragraph, zero_id)?,
        kind: IdKind::Paragraph,
        handle,
    };

    let first = PreservingPatchEngine::apply(&mut reader, &graph, std::slice::from_ref(&allocate))?;
    assert_eq!(first.allocation_count(), 1);
    assert_eq!(first.changed_parts(), 1);
    let first_hash = part_output_hash(&first, "Contents/section0.xml")?;

    let (mut second_reader, second_graph) = open_graph(bytes.clone())?;
    let second = PreservingPatchEngine::apply(
        &mut second_reader,
        &second_graph,
        std::slice::from_ref(&allocate),
    )?;
    assert_eq!(
        first_hash,
        part_output_hash(&second, "Contents/section0.xml")?
    );

    let invalid = [
        allocate.clone(),
        PatchIntent::ReplaceAttribute {
            target: XmlAttributeSelector::bind(&path, &document, live_paragraph, style_reference)?,
            value: PatchAttributeValue::Allocated(handle),
        },
    ];
    let (mut failed_reader, failed_graph) = open_graph(bytes.clone())?;
    assert_code(
        PreservingPatchEngine::apply(&mut failed_reader, &failed_graph, &invalid),
        "id_index_validation_failed",
    );

    let (mut retry_reader, retry_graph) = open_graph(bytes)?;
    let retry = PreservingPatchEngine::apply(
        &mut retry_reader,
        &retry_graph,
        std::slice::from_ref(&allocate),
    )?;
    assert_eq!(
        first_hash,
        part_output_hash(&retry, "Contents/section0.xml")?
    );
    Ok(())
}

#[test]
fn add_relationship_and_part_are_atomic_closed_and_order_independent() -> TestResult {
    let bytes = valid_archive(SECTION)?;
    let new_xml = format!(
        r#"<q:section xmlns:q="{PARAGRAPH_NS}"><q:p id="1" paraPrIDRef="1" styleIDRef="1"><q:run charPrIDRef="1"><q:t>PRIVATE-NEW-PART</q:t></q:run></q:p></q:section>"#
    );
    let part = AddedPart::xml(
        "Contents/section1.xml",
        "application/xml",
        new_xml.as_bytes(),
        PackageLimits::default(),
        PackageGraphLimits::default(),
        PatchLimits::default(),
    )?;
    let relationship = RelationshipAddition::new(
        "PRIVATE-REL-ID",
        "Contents/section1.xml",
        "application/xml",
        RelationshipSpine::Linear,
        PackageLimits::default(),
        PackageGraphLimits::default(),
        PatchLimits::default(),
    )?;
    let forward = [
        PatchIntent::AddPart { part: part.clone() },
        PatchIntent::AddRelationship {
            relationship: relationship.clone(),
        },
    ];
    let reverse = [
        PatchIntent::AddRelationship { relationship },
        PatchIntent::AddPart { part },
    ];

    let (mut first_reader, first_graph) = open_graph(bytes.clone())?;
    let first = PreservingPatchEngine::apply(&mut first_reader, &first_graph, &forward)?;
    first.verify_artifact_integrity()?;
    assert_eq!(first.added_parts(), 1);
    assert_eq!(first.changed_parts(), 1);
    assert_eq!(first.relationship_count(), 1);
    assert_eq!(
        part_disposition(&first, "Contents/section1.xml")?,
        PatchPartDisposition::Added
    );
    let debug = format!("{forward:?} {first:?}");
    assert!(!debug.contains("PRIVATE-NEW-PART"));
    assert!(!debug.contains("PRIVATE-REL-ID"));

    let (mut second_reader, second_graph) = open_graph(bytes.clone())?;
    let second = PreservingPatchEngine::apply(&mut second_reader, &second_graph, &reverse)?;
    assert_eq!(
        part_output_hash(&first, "Contents/content.hpf")?,
        part_output_hash(&second, "Contents/content.hpf")?
    );
    assert_eq!(
        part_output_hash(&first, "Contents/section1.xml")?,
        part_output_hash(&second, "Contents/section1.xml")?
    );

    let (mut missing_reader, missing_graph) = open_graph(bytes)?;
    assert_code(
        PreservingPatchEngine::apply(&mut missing_reader, &missing_graph, &forward[..1]),
        "patch_part_relationship_mismatch",
    );
    Ok(())
}

#[test]
fn fixed_seed_random_sequences_are_deterministic_and_limits_fail_closed() -> TestResult {
    let bytes = valid_archive(SECTION)?;
    let (mut selector_reader, selector_graph) = open_graph(bytes.clone())?;
    let (path, document) = part_document(
        &mut selector_reader,
        &selector_graph,
        "Contents/section0.xml",
    )?;
    let text_element = element(&document, "t", 0)?;
    let title = attribute(&document, text_element, "title")?;
    let token = text_token(&document, text_element)?;
    let attribute_selector = XmlAttributeSelector::bind(&path, &document, text_element, title)?;
    let text_selector = XmlTextSelector::bind(&path, &document, token)?;
    let mut state = 0xC0DE_2020_u64;
    for round in 0..64 {
        state = state
            .wrapping_mul(6_364_136_223_846_793_005)
            .wrapping_add(1_442_695_040_888_963_407);
        let value = format!("r{round}-{state:016x}-<&");
        let mut intents = Vec::new();
        if state & 1 != 0 {
            intents.push(PatchIntent::ReplaceAttribute {
                target: attribute_selector.clone(),
                value: PatchAttributeValue::Text(PatchText::new(&value)?),
            });
        }
        if state & 2 != 0 || intents.is_empty() {
            intents.push(PatchIntent::ReplaceText {
                target: text_selector.clone(),
                value: PatchText::new(&value)?,
            });
        }
        let (mut left_reader, left_graph) = open_graph(bytes.clone())?;
        let left = PreservingPatchEngine::apply(&mut left_reader, &left_graph, &intents)?;
        let (mut right_reader, right_graph) = open_graph(bytes.clone())?;
        let right = PreservingPatchEngine::apply(&mut right_reader, &right_graph, &intents)?;
        assert_eq!(
            part_output_hash(&left, "Contents/section0.xml")?,
            part_output_hash(&right, "Contents/section0.xml")?
        );
    }

    assert!(
        PatchLimits::new(PatchLimitConfig {
            max_intents: 0,
            ..PatchLimitConfig::default()
        })
        .is_err()
    );
    let tight = PatchLimits::new(PatchLimitConfig {
        max_total_output_growth: 1,
        ..PatchLimitConfig::default()
    })?;
    let oversized = [PatchIntent::ReplaceText {
        target: text_selector,
        value: PatchText::new(&"X".repeat(1_024))?,
    }];
    let (mut reader, graph) = open_graph(bytes.clone())?;
    let error = PreservingPatchEngine::apply_with_limits(
        &mut reader,
        &graph,
        PackageGraphLimits::default(),
        hwpx_package::IdRuleProfile::current_hancom_2020_core_v1(),
        hwpx_package::IdIndexLimits::default(),
        tight,
        &oversized,
    );
    assert_code(error, "patch_limit_exceeded");
    assert_addition_part_limit(bytes)?;
    Ok(())
}

#[test]
fn separated_writers_are_deterministic_atomic_and_no_overwrite() -> TestResult {
    let bytes = valid_archive(SECTION)?;
    let (mut reader, graph) = open_graph(bytes)?;
    let patch = PreservingPatchEngine::apply(&mut reader, &graph, &[])?;
    let preserving = PreservingWriter::build(
        &patch,
        PackageLimits::default(),
        PackageGraphLimits::default(),
        IdIndexLimits::default(),
        WriterLimits::default(),
    )?;
    let preserving_repeat = PreservingWriter::build(
        &patch,
        PackageLimits::default(),
        PackageGraphLimits::default(),
        IdIndexLimits::default(),
        WriterLimits::default(),
    )?;
    let normalized = NormalizedWriter::build(
        &patch,
        PackageLimits::default(),
        PackageGraphLimits::default(),
        IdIndexLimits::default(),
        WriterLimits::default(),
    )?;
    let normalized_repeat = NormalizedWriter::build(
        &patch,
        PackageLimits::default(),
        PackageGraphLimits::default(),
        IdIndexLimits::default(),
        WriterLimits::default(),
    )?;
    preserving.verify()?;
    normalized.verify()?;
    assert_eq!(preserving.sha256(), preserving_repeat.sha256());
    assert_eq!(normalized.sha256(), normalized_repeat.sha256());
    assert_ne!(preserving.sha256(), normalized.sha256());
    assert_eq!(preserving.mode(), WriterMode::Preserving);
    assert_eq!(normalized.mode(), WriterMode::Normalized);
    assert_eq!(
        preserving.report().timestamp(),
        MetadataDisposition::NotPreservedUnavailable
    );
    assert_eq!(
        normalized.report().timestamp(),
        MetadataDisposition::Normalized
    );
    assert_eq!(
        preserving.report().raw_compressed_stream(),
        MetadataDisposition::NotPreservedUnavailable
    );
    assert!(preserving.report().entries().iter().all(|entry| {
        entry.disposition() == PatchPartDisposition::Untouched
            && entry.source_compression() == Some(entry.output_compression())
    }));
    assert_atomic_publication(&preserving, &normalized)?;
    let tiny = WriterLimits::new(WriterLimitConfig {
        max_output_bytes: 1,
    })?;
    let tiny_result = PreservingWriter::build(
        &patch,
        PackageLimits::default(),
        PackageGraphLimits::default(),
        IdIndexLimits::default(),
        tiny,
    );
    let Err(tiny_error) = tiny_result else {
        panic!("one-byte output limit unexpectedly returned an artifact");
    };
    assert_eq!(tiny_error.code(), "writer_output_limit_exceeded");
    Ok(())
}

fn assert_atomic_publication(
    preserving: &hwpx_package::PackageArtifact,
    normalized: &hwpx_package::PackageArtifact,
) -> TestResult {
    let temporary = tempdir()?;
    let workspace = SecureWorkspace::create(temporary.path().join("writer-work"))?;
    let receipt = AtomicPackagePublisher::publish(
        preserving,
        &workspace,
        std::path::Path::new("job-1/document.hwpx"),
        std::path::Path::new("documents/document.hwpx"),
    )?;
    assert!(receipt.staged_reopen_verified());
    assert!(receipt.published_reopen_verified());
    assert_eq!(receipt.sha256(), preserving.sha256());
    let published = temporary
        .path()
        .join("writer-work/output/documents/document.hwpx");
    let published_bytes = std::fs::read(&published)?;
    assert_eq!(
        <[u8; 32]>::from(Sha256::digest(&published_bytes)),
        preserving.sha256()
    );

    let duplicate = AtomicPackagePublisher::publish(
        normalized,
        &workspace,
        std::path::Path::new("job-2/document.hwpx"),
        std::path::Path::new("documents/document.hwpx"),
    );
    let Err(error) = duplicate else {
        panic!("no-overwrite publication unexpectedly succeeded");
    };
    assert_eq!(error.code(), "writer_output_exists");
    assert!(
        !temporary
            .path()
            .join("writer-work/staging/job-2/document.hwpx")
            .exists()
    );
    assert_eq!(
        <[u8; 32]>::from(Sha256::digest(std::fs::read(&published)?)),
        preserving.sha256()
    );

    let traversal = AtomicPackagePublisher::publish(
        normalized,
        &workspace,
        std::path::Path::new("job-3/document.hwpx"),
        std::path::Path::new("../escape.hwpx"),
    );
    assert!(traversal.is_err());
    assert!(
        !temporary
            .path()
            .join("writer-work/staging/job-3/document.hwpx")
            .exists()
    );
    assert!(!temporary.path().join("escape.hwpx").exists());

    Ok(())
}

fn assert_addition_part_limit(bytes: Vec<u8>) -> TestResult {
    let added_xml = format!(r#"<q:section xmlns:q="{PARAGRAPH_NS}"/>"#);
    let added = AddedPart::xml(
        "Contents/limited.xml",
        "application/xml",
        added_xml.as_bytes(),
        PackageLimits::default(),
        PackageGraphLimits::default(),
        PatchLimits::default(),
    )?;
    let relationship = RelationshipAddition::new(
        "limited",
        "Contents/limited.xml",
        "application/xml",
        RelationshipSpine::NotInSpine,
        PackageLimits::default(),
        PackageGraphLimits::default(),
        PatchLimits::default(),
    )?;
    let additions = [
        PatchIntent::AddPart { part: added },
        PatchIntent::AddRelationship { relationship },
    ];
    let tiny_added_part = PatchLimits::new(PatchLimitConfig {
        max_added_part_bytes: 1,
        ..PatchLimitConfig::default()
    })?;
    let (mut reader, graph) = open_graph(bytes.clone())?;
    let error = PreservingPatchEngine::apply_with_limits(
        &mut reader,
        &graph,
        PackageGraphLimits::default(),
        hwpx_package::IdRuleProfile::current_hancom_2020_core_v1(),
        hwpx_package::IdIndexLimits::default(),
        tiny_added_part,
        &additions,
    );
    assert_code(error, "patch_limit_exceeded");

    let one_changed_part = PatchLimits::new(PatchLimitConfig {
        max_changed_parts: 1,
        ..PatchLimitConfig::default()
    })?;
    let (mut reader, graph) = open_graph(bytes)?;
    let error = PreservingPatchEngine::apply_with_limits(
        &mut reader,
        &graph,
        PackageGraphLimits::default(),
        hwpx_package::IdRuleProfile::current_hancom_2020_core_v1(),
        hwpx_package::IdIndexLimits::default(),
        one_changed_part,
        &additions,
    );
    assert_code(error, "patch_limit_exceeded");
    Ok(())
}

fn assert_code(result: Result<hwpx_package::PatchResult, PatchError>, expected: &str) {
    let Err(error) = result else {
        panic!("invalid transaction unexpectedly succeeded");
    };
    assert_eq!(error.code(), expected, "{error:?}");
}

fn part_disposition(
    result: &hwpx_package::PatchResult,
    path: &str,
) -> Result<PatchPartDisposition, Box<dyn Error>> {
    result
        .parts()
        .iter()
        .find(|record| record.path().as_str() == path)
        .map(hwpx_package::PatchPartRecord::disposition)
        .ok_or_else(|| std::io::Error::other("part record missing").into())
}

fn part_output_hash(
    result: &hwpx_package::PatchResult,
    path: &str,
) -> Result<[u8; 32], Box<dyn Error>> {
    result
        .parts()
        .iter()
        .find(|record| record.path().as_str() == path)
        .map(hwpx_package::PatchPartRecord::output_sha256)
        .ok_or_else(|| std::io::Error::other("part record missing").into())
}

fn element(
    document: &PreservingXmlDocument,
    local_name: &str,
    occurrence: usize,
) -> Result<usize, Box<dyn Error>> {
    document
        .elements()
        .iter()
        .enumerate()
        .filter(|(_, element)| element.name().local_name() == local_name)
        .nth(occurrence)
        .map(|(index, _)| index)
        .ok_or_else(|| std::io::Error::other("element missing").into())
}

fn attribute(
    document: &PreservingXmlDocument,
    element_index: usize,
    local_name: &str,
) -> Result<usize, Box<dyn Error>> {
    document.elements()[element_index]
        .attributes()
        .iter()
        .position(|attribute| attribute.name().local_name() == local_name)
        .ok_or_else(|| std::io::Error::other("attribute missing").into())
}

fn text_token(
    document: &PreservingXmlDocument,
    element_index: usize,
) -> Result<usize, Box<dyn Error>> {
    document
        .tokens()
        .iter()
        .position(|token| {
            token.element_index() == Some(element_index) && token.kind() == XmlTokenKind::Text
        })
        .ok_or_else(|| std::io::Error::other("text token missing").into())
}

fn part_document(
    reader: &mut TestReader,
    graph: &PackageGraph,
    path: &str,
) -> Result<(hwpx_package::PackagePath, PreservingXmlDocument), Box<dyn Error>> {
    let graph_path = graph
        .parts
        .iter()
        .find(|part| part.path.as_str() == path)
        .ok_or_else(|| std::io::Error::other("graph part missing"))?
        .path
        .clone();
    let entry = reader
        .entries()
        .iter()
        .find(|entry| entry.path.as_str() == path)
        .ok_or_else(|| std::io::Error::other("entry missing"))?
        .index;
    let bytes = reader.read_entry(entry)?;
    Ok((graph_path, PreservingXmlDocument::parse(&bytes)?))
}

fn valid_archive(section: &str) -> Result<Vec<u8>, zip::result::ZipError> {
    let opf = r#"<?xml version="1.0" encoding="UTF-8"?>
<o:package xmlns:o="http://www.idpf.org/2007/opf/" id="pkg" version="2.0">
  <o:manifest>
    <o:item id="header" href="header.xml" media-type="application/xml"/>
    <o:item id="section0" href="section0.xml" media-type="application/xml"/>
  </o:manifest>
  <o:spine><o:itemref idref="section0" linear="yes"/></o:spine>
</o:package>"#;
    archive(vec![
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
        entry(
            "Contents/header.xml",
            HEADER.as_bytes(),
            CompressionMethod::Deflated,
        ),
        entry(
            "Contents/section0.xml",
            section.as_bytes(),
            CompressionMethod::Deflated,
        ),
    ])
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
        writer.start_file(
            name,
            SimpleFileOptions::default().compression_method(method),
        )?;
        writer.write_all(&bytes)?;
    }
    Ok(writer.finish()?.into_inner())
}

fn open_graph(bytes: Vec<u8>) -> Result<OpenedGraph, Box<dyn Error>> {
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    Ok((reader, graph))
}
